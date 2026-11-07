"""Root-run fixture RED observer, CPU-only; no native/scientific execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

PACKET = Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/red')
W = PACKET.parents[4]
TEST = W / '.superpowers/sdd/plan-a2-full-score-operational186/candidate/tests/test_full_score_cpu.py'
PYTHONS = ['/sw/external/python/anaconda3/bin/python3.9', '/u/swong2/.conda/envs/mgnp/bin/python']
MISSING = 'FULL_SCORE_CPU_IMPLEMENTATION_MISSING'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''): h.update(block)
    return h.hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def pins():
    value = json.loads((PACKET / 'pins.json').read_text())
    for path, wanted in value['files'].items():
        assert sha(path) == wanted, ('changed RED packet or source', path)
    for path in value['expected_absent']:
        assert not Path(path).exists(), ('implementation appeared before root RED observation', path)
    return value


def command(python, output, n):
    return [python, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--noconftest',
            '--confcutdir=' + str(TEST.parent), '--tb=short',
            '--junitxml=' + str(output / ('env%d.xml' % n)),
            '--basetemp=' + str(output / ('tmp-env%d' % n)), str(TEST)]


def bounded(command, env, stdout, stderr, seconds, cwd):
    child = subprocess.Popen(command, env=env, stdout=stdout, stderr=stderr,
                             cwd=str(cwd), start_new_session=True)
    try:
        return child.wait(timeout=seconds)
    except BaseException:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try: child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL); child.wait(timeout=5)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(); output = Path(args.output)
    assert output.is_absolute(), 'absolute fresh evidence directory required'
    expected = pins()
    commands = [command(p, output, n) for n, p in enumerate(PYTHONS, 1)]
    if args.dry_run:
        print(json.dumps(dict(packet=str(PACKET), test=str(TEST), commands=commands,
                              timeout_seconds_per_environment=90, no_native_import=True,
                              no_model=True, no_GPU=True), indent=2)); return 0
    assert os.environ.get('SLURM_JOB_ID'), 'root must dispatch fixture suite as Slurm CPU'
    assert os.environ.get('SLURM_CLUSTER_NAME') == 'delta'
    assert not any(os.environ.get(k) for k in ('SLURM_JOB_GPUS', 'SLURM_STEP_GPUS'))
    assert all(os.environ.get(k, '') in ('', '0') for k in (
        'SLURM_GPUS', 'SLURM_GPUS_ON_NODE', 'SLURM_GPUS_PER_NODE', 'SLURM_GPUS_PER_TASK'))
    assert int(os.environ.get('SLURM_CPUS_PER_TASK', '0')) >= 2
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1',
               CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1')
    allocation = subprocess.check_output(['scontrol', 'show', 'job', os.environ['SLURM_JOB_ID'], '-o'],
                                         universal_newlines=True, timeout=15)
    fields = dict(x.split('=', 1) for x in allocation.split() if '=' in x)
    assert fields['JobId'] == os.environ['SLURM_JOB_ID'] and fields['JobState'] == 'RUNNING'
    assert fields['Partition'] in ('cpu', 'cpu-interactive') and fields['Account'].endswith('-cpu')
    assert fields['NumNodes'] == '1' and not any(x.startswith('gres/gpu') for x in fields.get('AllocTRES', '').split(','))
    write(output / 'allocation.json', dict(actual_job_id=os.environ['SLURM_JOB_ID'],
                                         cluster=os.environ['SLURM_CLUSTER_NAME'], host=socket.gethostname(),
                                         scontrol_job=allocation, fields=fields))
    observations = []
    for n, (python, cmd) in enumerate(zip(PYTHONS, commands), 1):
        info = json.loads(subprocess.check_output([python, '-c',
            'import json,sys,pytest; print(json.dumps({"python":list(sys.version_info[:3]),"executable":sys.executable,"pytest":pytest.__version__}))'],
            env=env, universal_newlines=True, timeout=15))
        assert info['python'][:2] == ([3, 9] if n == 1 else [3, 12]), info
        with (output / ('env%d.stdout' % n)).open('x') as stdout, (output / ('env%d.stderr' % n)).open('x') as stderr:
            code = bounded(cmd, env, stdout, stderr, 90, TEST.parent)
        cases = list(ET.parse(str(output / ('env%d.xml' % n))).iter('testcase'))
        failures = [c for c in cases if c.find('failure') is not None]
        errors = [c for c in cases if c.find('error') is not None]
        observation = dict(environment=info, exit_code=code, tests=len(cases),
                           failures=len(failures), errors=len(errors), command=cmd,
                           test_names=[c.attrib['name'] for c in cases])
        write(output / ('env%d-result.json' % n), observation)
        assert code == 1 and cases and not errors, ('not attributable case RED', observation)
        assert len(cases) == len(failures) == expected['expected_cases'], observation
        for case in failures:
            assert MISSING in ''.join(case.find('failure').itertext()), case.attrib
        observations.append(observation)
    assert observations[0]['test_names'] == observations[1]['test_names']
    pins()  # mutation during observation invalidates RED receipt
    value = dict(status='TASK2_RED_OBSERVED_NO_IMPLEMENTATION_AUTHORITY', actual_job_id=os.environ['SLURM_JOB_ID'],
                 cluster='delta', host=socket.gethostname(), observations=observations,
                 pins_sha256=sha(PACKET / 'pins.json'), elapsed_seconds=time.time() - started,
                 no_native_import=True, no_model=True, no_GPU=True, source_commit=expected['source_commit'])
    write(output / 'RESULT.json', value); print(json.dumps(value, indent=2)); return 0


if __name__ == '__main__':
    sys.exit(main())
