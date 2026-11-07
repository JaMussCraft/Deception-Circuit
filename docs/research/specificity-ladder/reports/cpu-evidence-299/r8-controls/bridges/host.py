#!/usr/bin/env python3
"""Bounded sharded validation transport, adapted from reviewed diagnostic254-r3.

Host is Python3.6 compatible. Actual config/binding and accounting belong to root.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import supervisor
import transport229 as old

PACKET_REL = Path('Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r8-sharded')

def durable(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())

def allocation(c, timeout=15):
    e = os.environ; job = e['SLURM_JOB_ID']; assert re.fullmatch('[0-9]+', job)
    raw = subprocess.check_output(['scontrol', 'show', 'job', job, '-o'], universal_newlines=True,
        timeout=timeout, env=dict(e, TZ='UTC'))
    f = dict(x.split('=', 1) for x in raw.split() if '=' in x)
    t = dict(x.split('=', 1) for x in f.get('AllocTRES', f.get('TRES', '')).split(',') if '=' in x)
    cpus = str(c['cpus'])
    assert f['JobId'] == c['job_id'] == job and f['JobState'] == 'RUNNING'
    assert re.search(r'\(' + str(os.getuid()) + r'\)', f['UserId'])
    assert f['Account'] == c['account'] and f['Partition'] == c['partition'] and f['QOS'] == c['qos']
    assert f['NumNodes'] == f['NumTasks'] == '1' and f['NumCPUs'] == f['CPUs/Task'] == t['cpu'] == cpus
    assert t['mem'] in ('32G', '32768M') and f['TimeLimit'] in ('01:20:00', '1:20:00', '80:00')
    assert f['Requeue'] == f['Restarts'] == '0' and f['BatchHost'].split('.')[0] == socket.gethostname().split('.')[0]
    assert e.get('SLURM_CLUSTER_NAME') == c['cluster'] and e.get('SLURM_CPUS_PER_TASK') == cpus and e.get('SLURM_NTASKS') == '1'
    assert not any(k.startswith('gres/gpu') and float(v) > 0 for k, v in t.items())
    assert all(not e.get(k) for k in ('SLURM_JOB_GPUS', 'SLURM_STEP_GPUS', 'CUDA_VISIBLE_DEVICES'))
    assert all(e.get(k, '') in ('', '0') for k in ('SLURM_GPUS', 'SLURM_GPUS_ON_NODE', 'SLURM_GPUS_PER_NODE', 'SLURM_GPUS_PER_TASK'))
    return f, datetime.datetime.strptime(f['EndTime'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp()

def check_source(c):
    assert c['status'] == 'ROOT_BOUND_A3_SHARDED_VALIDATION'
    assert c['environment'] in ('base', 'mgnp') and c['shard'] in (0, 1)
    assert c['cluster'] == ('delta' if c['environment'] == 'base' else 'bridges2')
    assert c['cpus'] == (2 if c['environment'] == 'base' else 18) and c['memory_gib'] == 32 and c['allocation_seconds'] == 4800
    assert c['account'] and c['partition'] and c['qos'] and c['job_id'] and c['output']
    if c['environment'] == 'mgnp':
        assert c['account'] == 'cis260361p' and c['partition'] == 'RM-shared' and c['qos'] == 'rm'
        physical = Path(c['physical_root'])
        assert physical.is_absolute() and str(physical).startswith('/ocean/projects/cis260361p/swong2/')
        assert physical.resolve() == physical and all(not x.is_symlink() for x in [physical] + list(physical.parents))
        old.PHYS = physical
    inventory = json.loads((HERE.parent/'transport-inventory.json').read_text())
    assert [{k: x[k] for k in ('virtual', 'sha256', 'bytes')} for x in c['files']] == inventory['files']
    assert [{k: x[k] for k in ('virtual', 'literal_target')} for x in c['aliases']] == inventory['aliases']
    assert len(c['aliases']) == 8
    assert c['observer_virtual'] == str(old.VIRT/PACKET_REL/'run_packet.py')
    if c['environment'] == 'mgnp':
        base = dict(c, status='ROOT_BOUND_A3_GREEN_MGNP_TRANSPORT', expected_cases=223, expected_file_count=len(c['files']))
        old.check_config(base)
    else:
        assert all(x['physical'] == x['virtual'] for x in c['files'] + c['aliases'])
        old.check_records(c['files'], c['aliases'])

def job_layout(output, job_id):
    out = Path(output)
    assert out.is_absolute() and '..' not in out.parts and str(out) == output, 'canonical absolute output required'
    child = out.parent; root = child.parent
    assert out.name == 'execution' and child.name == 'child' and root.name == 'job-'+job_id, 'private child output layout required'
    return root, child, out

def command(c, stage, kind, deadline):
    _, child, out = job_layout(c['output'], c['job_id']); packet = old.VIRT/PACKET_REL
    env = {k: v for k, v in os.environ.items() if k.startswith('SLURM_')}
    env.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
        MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', DC_RUN_MANIFEST_GIT='0',
        A3_HOST_BOUND='1', A3_STAGE_DEADLINE=str(deadline), A3_STAGE_NAME=stage)
    py = '/sw/external/python/anaconda3/bin/python3.9' if c['environment'] == 'base' else old.PY
    argv = [py, '-B', str(packet/'run_packet.py'), '--environment', c['environment'], '--shard', str(c['shard']),
        '--stage', stage, '--output', str(out)]
    if c['environment'] == 'base':
        return argv, dict(os.environ, **env)
    assert kind in ('v1', 'v2')
    cg = '/sys/fs/cgroup:/sys/fs/cgroup:ro'
    if kind == 'v1':
        cg += ',/sys/fs/cgroup/memory:/sys/fs/cgroup/memory:ro'
    physical = old.virtual_to_physical(str(out.parent))
    # Host receipts stay at the job root, outside this child-only writable bind.
    cmd = ['apptainer', 'exec', '--cleanenv', '--contain', '--no-home', '--writable-tmpfs', '--pwd', str(packet),
        '--bind', str(old.PHYS)+':'+str(old.VIRT)+':ro', '--bind', '/ocean:/ocean:ro',
        '--bind', '/ocean/projects/cis260361p/swong2/hf/hub:/work/nvme/beto/swong2:ro',
        '--bind', old.ENV_PATH+':/u/swong2/.conda/envs/mgnp:ro', '--bind', physical+':'+str(out.parent)+':rw', '--bind', cg]
    env['HF_HUB_CACHE'] = '/work/nvme/beto/swong2'
    for k, v in sorted(env.items()):
        cmd.extend(['--env', k+'='+v])
    return cmd + [old.IMAGE, old.PY, '-B', str(packet/'bridges/inner.py'), kind, str(out.parent)] + argv, None

def execute_stage(c, stage, kind, root, initial_end, end):
    _, current = allocation(c); end = min(end, current)
    started = time.time(); started_mono = time.monotonic()
    deadline = supervisor.stage_bound(started, initial_end, end, supervisor.CAPS[stage])
    monotonic_deadline = started_mono + max(0, deadline - started)
    # All preparation consumes these original bounds, including source/image
    # validation, command construction, durable receipts and opening logs.
    check_source(c)
    if c['environment'] == 'mgnp':
        assert old.sha(old.IMAGE) == old.IMAGE_SHA
    argv, env = command(c, stage, kind, deadline)
    durable(root/(stage+'-command.json'), dict(argv=argv, deadline=deadline, monotonic_deadline=monotonic_deadline))
    with (root/(stage+'.stdout')).open('xb') as stdout, (root/(stage+'.stderr')).open('xb') as stderr:
        result = supervisor.execute(argv, stdout, stderr, supervisor.CAPS[stage], initial_end,
            lambda timeout=15: allocation(c, timeout), env=env,
            wall_deadline=deadline, monotonic_deadline=monotonic_deadline)
    durable(root/(stage+'-terminal.json'), result)
    virtual_root, _, _ = job_layout(c['output'], c['job_id'])
    terminal_ref = dict(path=str(virtual_root/(stage+'-terminal.json')), sha256=old.sha(root/(stage+'-terminal.json')))
    return result, end, terminal_ref

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config'); ap.add_argument('--config-sha256'); ap.add_argument('--manifest-sha256')
    ap.add_argument('--dry-run', action='store_true'); a = ap.parse_args()
    if a.dry_run:
        print(json.dumps(dict(status='UNBOUND_NOT_RUNNABLE', stages=supervisor.CAPS, allocation_seconds=4800,
            final_reserve=120, shared_failure_cleanup_seconds=20, overhead_seconds=360,
            actual_job=None, actual_config=None, scheduler_calls=0, execution_authorized=False), sort_keys=True)); return
    assert a.config and a.config_sha256 and a.manifest_sha256
    path = Path(a.config)
    assert path.is_absolute() and path.resolve() == path and all(not x.is_symlink() for x in [path]+list(path.parents))
    assert re.fullmatch('[0-9a-f]{64}', a.config_sha256) and old.sha(path) == a.config_sha256
    assert re.fullmatch('[0-9a-f]{64}', a.manifest_sha256) and old.sha(HERE/'manifest.json') == a.manifest_sha256
    manifest = json.loads((HERE/'manifest.json').read_text())
    for n, h in manifest.items():
        assert old.sha(HERE/n) == h
    c = json.loads(path.read_text()); check_source(c)
    f, end = allocation(c); initial_end = end
    virtual_out = Path(c['output']); physical_out = Path(old.virtual_to_physical(str(virtual_out))) if c['environment'] == 'mgnp' else virtual_out
    _, _, _ = job_layout(c['output'], c['job_id'])
    root = physical_out.parent.parent
    assert root.is_dir() and root.stat().st_uid == os.getuid() and root.resolve() == root and all(not p.is_symlink() for p in [root]+list(root.parents))
    assert not list(root.iterdir())
    physical_out.parent.mkdir(mode=0o700)
    kind = old.actual_controller(c['job_id']); supervisor.enable_subreaper()
    durable(root/'host-before.json', dict(allocation=f, end_bound=end, config_sha256=a.config_sha256, cgroup_kind=kind))
    error = None; stage_refs = {}
    try:
        for stage in ('baseline', 'oracle', 'suite'):
            result, end, terminal_ref = execute_stage(c, stage, kind, root, initial_end, end)
            stage_refs[stage] = terminal_ref
            assert result['normal_completion'] is True, result
    except BaseException as ex:
        error = repr(ex)
    finally:
        posterror = None
        try:
            check_source(c); assert old.sha(path) == a.config_sha256 and old.sha(HERE/'manifest.json') == a.manifest_sha256
            for n, h in manifest.items():
                assert old.sha(HERE/n) == h
            f, current = allocation(c); end = min(end, current)
            assert time.time() < end
        except BaseException as ex:
            posterror = repr(ex)
        durable(root/'host-after.json', dict(status='HOST_COMPLETE' if not error and not posterror else 'FAILED',
            normal_completion=not error and not posterror, exit_code=0 if not error and not posterror else 1,
            job_id=c['job_id'], cluster=c['cluster'], output=c['output'], source_checks_complete=not posterror,
            allocation_checks_complete=not posterror, config_sha256=a.config_sha256,
            stages=stage_refs, error=error, postcheck_error=posterror, allocation=f, end_bound=end, execution_authorized=False))
    if error or posterror:
        raise RuntimeError(str(error)+'; final '+str(posterror))

if __name__ == '__main__': main()
