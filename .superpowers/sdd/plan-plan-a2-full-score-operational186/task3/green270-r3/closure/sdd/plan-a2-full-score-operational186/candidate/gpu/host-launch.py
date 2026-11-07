"""Python 3.6 host supervisor; actual reviewed allocation, protected mounts."""
from pathlib import Path
import datetime
import json
import math
import os
import signal
import socket
import subprocess
import time
from common import C, CONFIG, validate_config, require, sha, effective_deadlines, epoch


def seconds(value):
    days, clock = (value.split('-', 1) if '-' in value else ('0', value))
    parts = [int(x) for x in clock.split(':')]
    require(len(parts) in (2, 3), 'actual time limit required')
    return int(days) * 86400 + (parts[0] * 3600 + parts[1] * 60 + parts[2]
                                if len(parts) == 3 else parts[0] * 60 + parts[1])


def memory_bytes(value):
    factors = {'K': 1024, 'M': 1024 ** 2, 'G': 1024 ** 3, 'T': 1024 ** 4}
    number = float(value[:-1]) * factors[value[-1]] if value[-1] in factors else float(value)
    require(math.isfinite(number) and number > 0 and number == int(number), 'actual finite memory TRES')
    return int(number)


def validate_allocation(c, captured):
    facts = captured['fields']
    raw = captured['raw_scontrol']
    require(dict(x.split('=', 1) for x in raw.split() if '=' in x) == facts, 'actual raw/facts capture mismatch')
    require(0 <= time.time() - captured['captured_unix'] <= c['maximum_allocation_capture_age_seconds'], 'stale actual allocation')
    require(captured['actual_job_id'] == facts['JobId'] == c['actual_job_id'] == os.environ['SLURM_JOB_ID'], 'actual job identity')
    require(facts['JobState'] == 'RUNNING' and facts['Account'] == c['expected_account']
            and facts['Partition'] in c['allowed_partitions'] and facts['QOS'] == c['expected_qos'], 'actual RUNNING account/partition/QoS')
    require(facts['Requeue'] == '0' and facts['Restarts'] == '0', 'restart/requeue forbidden')
    host = socket.gethostname().split('.')[0]
    require(host == captured['host'].split('.')[0]
            and host in [x.split('.')[0] for x in captured['actual_hostnames']], 'own actual host')
    tres = dict(x.split('=', 1) for x in facts.get('AllocTRES', facts.get('TRES', '')).split(',') if '=' in x)
    require(tres.get('gres/gpu') == '1' and (tres.get('gres/gpu:h100-80') == '1'
            or facts.get('TresPerNode') == 'gres:gpu:h100-80:1'), 'exactly one typed H100 allocation')
    other_types = [k for k in tres if k.startswith('gres/gpu:') and k != 'gres/gpu:h100-80']
    require(not other_types, 'foreign typed GPU TRES')
    r = c['resources']
    require(r['GPU_count'] == 1 and int(facts['NumNodes']) == 1
            and int(facts['NumCPUs']) == r['CPUs'] and memory_bytes(tres['mem']) == r['RAM_bytes']
            and seconds(facts['TimeLimit']) == r['duration_seconds'], 'actual reviewed resource tuple')
    require(epoch(facts['EndTime']) > time.time(), 'allocation ended')
    return dict(job_id=c['actual_job_id'], hostname=socket.gethostname(), facts=facts, tres=tres,
                host_capture_unix=captured['captured_unix'])


def physical_path(c, virtual_path):
    virtual = Path(c['virtual_Alignment_root'])
    path = Path(virtual_path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute mapped namespace')
    try:
        return Path(c['physical_Alignment_root']) / path.relative_to(virtual)
    except ValueError:
        return path


def build_container_command(c, profile):
    main = physical_path(c, c['main_root'])
    require(main.is_dir() and not main.is_symlink(), 'actual MAIN mountpoint absent or linked')
    score = main / 'score'
    require(not score.exists() and not score.is_symlink(), 'existing score output')
    evidence = physical_path(c, c['evidence_root'])
    require(evidence != main and not str(evidence).startswith(str(main) + '/'), 'dedicated evidence mount')
    command = ['apptainer', 'exec', '--cleanenv', '--contain', '--no-home', '--writable-tmpfs', '--nv',
               '--pwd', c['runtime'], '--bind', c['physical_Alignment_root'] + ':' + c['virtual_Alignment_root'] + ':ro',
               '--bind', '/ocean:/ocean:ro', '--bind', c['physical_HF_cache'] + ':' + c['virtual_HF_cache'] + ':ro',
               '--bind', str(main) + ':' + c['main_root'] + ':rw']
    # Native publication needs MAIN/.score-*/ -> MAIN/score. Protect everything
    # already present, not the absent output leaf. Nested trees inherit RO.
    for leaf in sorted(main.iterdir()):
        require(not leaf.is_symlink() and not leaf.name.startswith('.score-'), 'unreviewed MAIN link/publication scratch')
        command += ['--bind', str(leaf) + ':' + c['main_root'] + '/' + leaf.name + ':ro']
    command += ['--bind', str(evidence) + ':' + c['evidence_root'] + ':rw']
    for key, value in sorted(profile.items()):
        command += ['--env', key + '=' + str(value)]
    packet = profile.get('A2_FULL_SCORE_PACKET', str(Path(__file__).resolve().parent))
    command += [c['image'], 'bash', packet + '/inner.sh']
    return command


def terminate_process_group(child):
    if child.poll() is not None:
        return
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=10)


def main():
    c = validate_config(C)
    require(sha(CONFIG) == os.environ['A2_FULL_SCORE_BOUND_CONFIG_SHA256'], 'host config changed')
    require(sha(c['image']) == c['image_sha256'], 'pinned SIF changed')
    evidence = physical_path(c, c['evidence_root'])
    require(not evidence.exists() and not evidence.is_symlink(), 'fresh evidence directory required')
    evidence.mkdir(parents=True)
    capture_file = evidence / 'allocation.json'
    def capture():
        observed_at = time.time()
        raw = subprocess.check_output(['scontrol', 'show', 'job', c['actual_job_id'], '-o'],
                                      universal_newlines=True, timeout=15, env=dict(os.environ, TZ='UTC'))
        facts = dict(x.split('=', 1) for x in raw.split() if '=' in x)
        hosts = subprocess.check_output(['scontrol', 'show', 'hostnames', facts['NodeList']],
                                        universal_newlines=True, timeout=15).split()
        data = dict(actual_job_id=c['actual_job_id'], host=socket.gethostname(), actual_hostnames=hosts,
                    raw_scontrol=raw, fields=facts, captured_unix=observed_at)
        validate_allocation(c, data)
        temporary = capture_file.with_name('allocation.pending-' + str(os.getpid()))
        with temporary.open('x') as stream: json.dump(data, stream, indent=2)
        os.replace(str(temporary), str(capture_file))
        return facts
    first = capture()
    initial_end = epoch(first['EndTime'])
    fixed_end = time.time() + c['resources']['duration_seconds']
    packet = Path(__file__).resolve().parent
    def to_virtual(path):
        return str(Path(c['virtual_Alignment_root']) / Path(path).relative_to(Path(c['physical_Alignment_root'])))
    profile = {k: v for k, v in os.environ.items() if k.startswith('SLURM_') or k == 'CUDA_VISIBLE_DEVICES'}
    profile.update(A2_FULL_SCORE_BOUND_CONFIG=to_virtual(CONFIG), A2_FULL_SCORE_BOUND_CONFIG_SHA256=sha(CONFIG),
                   A2_FULL_SCORE_PACKET=to_virtual(packet), A2_FULL_SCORE_RUNTIME=c['runtime'],
                   A2_FULL_SCORE_INITIAL_END_EPOCH=str(initial_end), A2_FULL_SCORE_FIXED_END_EPOCH=str(fixed_end),
                   A2_FULL_SCORE_EXECUTION_OUTPUT=c['evidence_root'], A2_FULL_SCORE_RELEASE_DIRECTORY=c['release_directory'],
                   DC_PYTHON=c['python'], PYTHONDONTWRITEBYTECODE='1')
    command = build_container_command(c, profile)
    with (evidence / 'host-launch.json').open('x') as stream:
        json.dump(dict(command=command, bound_config_sha256=sha(CONFIG), resources=c['resources'],
                       initial_end_epoch=initial_end, fixed_run_deadline=fixed_end,
                       host=socket.gethostname(), actual_job_id=c['actual_job_id']), stream, indent=2)
    child = None
    def interrupted(signum, frame):
        raise TimeoutError('host termination signal ' + str(signum))
    for signum in (signal.SIGINT, signal.SIGTERM): signal.signal(signum, interrupted)
    try:
        require(effective_deadlines(c, initial_end, initial_end, fixed_end, time.time())['remaining_work_seconds']
                >= c['resources']['minimum_entry_seconds'], 'host entry floor')
        child = subprocess.Popen(command, start_new_session=True)
        while True:
            current = capture()
            deadlines = effective_deadlines(c, initial_end, epoch(current['EndTime']), fixed_end, time.time())
            if time.time() >= deadlines['run_deadline']:
                raise TimeoutError('fixed initial/current/run deadline reached')
            code = child.poll()
            if code is not None:
                return code
            time.sleep(max(0, min(5, deadlines['run_deadline'] - time.time())))
    finally:
        if child is not None: terminate_process_group(child)


if __name__ == '__main__':
    raise SystemExit(main())
