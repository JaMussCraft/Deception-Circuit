#!/usr/bin/env python3
"""One finite full_score owning CPU request, one child, immutable evidence."""
import argparse
import copy
import datetime
import hashlib
import json
import importlib.util
import math
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import time
import traceback

SOURCE = '50e947bb852613e3a270082651f2bd1b7bb0c525'
P = Path(__file__).resolve().parent
A = '/projects/beto/swong2/Alignment/Deception-Circuit'
W = A + '/.claude/worktrees/specificity-ladder'
CATALOGUES = tuple(root + '/docs/research/' + name for root in (A,W)
                   for name in ('held_out.json','directions.json'))


def require(ok,message):
    if not ok: raise ValueError(message)


def number(value,positive=True):
    require(type(value) in (int,float) and math.isfinite(value)
            and (value > 0 if positive else value >= 0), 'finite reviewed number required')
    return value


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''): h.update(block)
    return h.hexdigest()


def unique_pairs(pairs):
    value = {}
    for key,item in pairs:
        require(key not in value,'duplicate JSON key: ' + key); value[key] = item
    return value


def decode(raw):
    return json.loads(raw,object_pairs_hook=unique_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def bound(ref):
    path = Path(ref['path']); require(path.is_absolute() and not path.is_symlink(),'ordinary absolute bound reference')
    raw = path.read_bytes(); require(hashlib.sha256(raw).hexdigest() == ref['sha256'],'bound file changed: ' + str(path))
    return decode(raw)


def write(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False); stream.write('\n')


def validate_request(c,r,waiting,now=None):
    now = time.time() if now is None else number(now)
    require(c['phase'] == r['phase'] == waiting['phase'] == 'full_score', 'full_score only')
    require(c['source_commit'] == SOURCE, 'accepted source50e only')
    for request_key,config_key in (
        ('standing_CPU_job_id','standing_CPU_job_id'),('standing_packet_manifest_sha256','packet_manifest_sha256'),
        ('accepted_source_commit','source_commit'),('frozen_G3_sha256','frozen_G3_sha256'),
        ('bank_file_sha256','bank_file_sha256'),('bank_manifest_sha256','bank_manifest_sha256'),
        ('GPU_packet_manifest_sha256','GPU_packet_manifest_sha256')):
        require(r[request_key] == c[config_key], 'request binding: ' + request_key)
    for request_key,waiting_key in (
        ('actual_future_GPU_job_id','job_id'),('accepted_source_commit','source_commit'),
        ('final_GPU_bound_config_sha256','bound_config_sha256'),('GPU_packet_manifest_sha256','launch_packet_manifest_sha256'),
        ('frozen_G3_sha256','groups_file_sha256'),('bank_file_sha256','bank_file_sha256'),
        ('bank_manifest_sha256','bank_manifest_sha256'),('GPU_WAITING_requested_at','requested_at')):
        require(r[request_key] == waiting[waiting_key], 'WAITING binding: ' + waiting_key)
    require(re.fullmatch('[0-9]+',r['actual_future_GPU_job_id']) is not None,'actual GPU job identity')
    for key in ('final_GPU_bound_config_sha256','GPU_packet_manifest_sha256'):
        require(re.fullmatch('[0-9a-f]{64}',r[key]) is not None,'GPU hash identity')
    issued = number(r['root_trigger_issued_at']); requested = number(waiting['requested_at'])
    require(0 <= now-issued <= 15 and requested <= issued, 'fresh root trigger at most15 seconds')
    end = number(waiting['publication_deadline'])
    require(0 < end-requested <= 300 and requested <= now < end,'fixed nonrenewable GPU WAITING window')
    return copy.deepcopy(r)


def child_deadline(c,waiting,initial_end,current_end,now=None):
    now = time.time() if now is None else number(now)
    require(c['phase'] == waiting['phase'] == 'full_score','full_score window only')
    requested = number(waiting['requested_at']); end = number(waiting['publication_deadline'])
    require(0 < end-requested <= 300 and requested <= now < end,'invalid fixed GPU window')
    cap = number(c['child_cap_seconds'])
    finish = number(c['CPU_finish_margin_seconds']); publication = number(c['publication_margin_seconds'])
    deadline = min(now+cap, number(initial_end)-finish, number(current_end)-finish, end-publication)
    if deadline <= now: raise TimeoutError('CPU/publication window already missed; no renewal')
    return deadline


def verify_request_files(request,request_sha256,marker,marker_sha256):
    acquired = []
    for path,want in ((request,request_sha256),(marker,marker_sha256)):
        path = Path(path)
        require(not path.is_symlink(), 'ordinary request/WAITING required')
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == want and not path.is_symlink() and sha(path) == want,
                'request or actual WAITING bytes changed')
        acquired.append(raw)
    # Decode only these authenticated buffers; never reopen to obtain authority.
    return dict(request_sha256=request_sha256,marker_sha256=marker_sha256,
                request_bytes=acquired[0],marker_bytes=acquired[1])


def terminate(child,grace=5):
    if child.poll() is None:
        os.killpg(child.pid,signal.SIGTERM)
        try: child.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL); child.wait(timeout=grace)
    else: child.wait()


def observe_child(child,deadline,recheck):
    started = time.time(); term = None
    try:
        while True:
            deadline = min(deadline, number(recheck()))
            code = child.poll()
            # A reaped zero exit does not bypass a missed deadline.
            now = time.time()
            if now >= deadline: raise TimeoutError('child observed at/after fixed deadline')
            if code is not None:
                code = child.wait()
                now = time.time()
                if now >= deadline: raise TimeoutError('child reaped at/after fixed deadline')
                require(code == 0,'native guard child failed')
                return dict(exit_code=code,term_sent_at=None,started_unix=started,
                            finished_unix=now,deadline_unix=deadline)
            time.sleep(min(0.25,deadline-now))
    except BaseException:
        if child.poll() is None: term = time.time()
        terminate(child)
        raise


def validate_child_completion(c,r,child,result,now=None):
    now = time.time() if now is None else number(now)
    require(child['exit_code'] == 0 and child['term_sent_at'] is None,'normal child terminal exit required')
    require(number(child['started_unix']) <= number(child['finished_unix']) < number(child['deadline_unix'])
            and now < child['deadline_unix'], 'late child or supervisor cannot promote')
    require(result['phase'] == c['phase'] == r['phase'] == 'full_score' and result['complete'] is False
            and result['status'] == 'GUARDS_PASSED_AWAIT_SUPERVISOR', 'exact complete guard child receipt')
    require(result['source_commit'] == c['source_commit'] == SOURCE
            and result['actual_CPU_job_id'] == c['standing_CPU_job_id'] == r['standing_CPU_job_id']
            and result['actual_future_GPU_job_id'] == r['actual_future_GPU_job_id']
            and result['request_sha256'] == child['request_sha256'], 'child request/source/job bindings')
    require(result['rows'] == result['reconstructed_rows'] == 59652
            and result['positive_controls'] == result['reconstructed_controls'] == 3396
            and result['full_domain_support_audit_complete'] is True
            and re.fullmatch('[0-9a-f]{64}',result['support_reason_mask_sha256']) is not None,
            'completed full-domain identities/support audit required')
    require(result['source_before'] == result['source_after'], 'child immutable identity drift')
    require(set(result['source_before']) == {'source','groups','bank','bank_manifest','input_manifest','aliases','catalogues'},
            'complete immutable identity closure')
    require(set(result['source_before']['catalogues']) == set(CATALOGUES),'complete four catalogue identity closure')
    require(all(result[key] is False for key in ('model_loaded','GPU_admitted','freeze_executed')),'CPU-only proof')
    require(re.fullmatch('[0-9a-f]{64}',child['guard_result_sha256']) is not None,'immutable guard receipt hash')
    value = copy.deepcopy(result)
    value.update(kind='Delta_actual_full_score_preflight',complete=True,status='PASS',
        standing_packet_manifest_sha256=c['packet_manifest_sha256'],
        final_GPU_bound_config_sha256=r['final_GPU_bound_config_sha256'],
        GPU_packet_manifest_sha256=c['GPU_packet_manifest_sha256'],
        guard_result_sha256=child['guard_result_sha256'],supervisor_finished_unix=now,
        deadline_unix=child['deadline_unix'],automatic_retry=False,
        timely_window=True,bank_file_sha256=c['bank_file_sha256'],bank_manifest_sha256=c['bank_manifest_sha256'],
        full_rows=result['rows'],full_controls=result['positive_controls'],
        full_domain_support_audit_complete=result['full_domain_support_audit_complete'],
        waiting_sha256=r['GPU_WAITING_marker_sha256'],bound_gpu_config_sha256=r['final_GPU_bound_config_sha256'],
        launch_packet_manifest_sha256=c['GPU_packet_manifest_sha256'])
    return value


def packet(c):
    manifest = bound(c['packet_manifest'])
    require(c['packet_manifest']['sha256'] == c['packet_manifest_sha256'],'packet manifest identity')
    for path,wanted in manifest['files'].items():
        require(Path(path).is_absolute() and not Path(path).is_symlink() and sha(path) == wanted,'packet/source pin drift: ' + path)
    for name in ('supervisor.py','validate-phase.py','launch.sh','config.template.json','parameters.template.json','request.template.json'):
        require(str(P/name) in manifest['files'],'CPU member missing from packet')


def validate_config(c):
    template = decode((P/'config.template.json').read_bytes())
    require(set(c) == set(template),'closed CPU configuration')
    require(all(value is not None for value in c.values()),'unbound CPU configuration')
    require(c['phase'] == 'full_score' and c['source_commit'] == SOURCE and c['resource_review_accepted'] is True,
            'accepted full_score configuration/resources required')
    for key in ('child_cap_seconds','CPU_finish_margin_seconds','publication_margin_seconds','kill_grace_seconds','duration_seconds'):
        number(c[key])
    require(c['publication_margin_seconds'] >= c['kill_grace_seconds'] and c['CPU_finish_margin_seconds'] >= c['kill_grace_seconds'],
            'termination must fit reviewed margins')
    require(c['python'] == '/u/swong2/.conda/envs/mgnp/bin/python','real bank-matching mgnp environment')
    require(type(c['CPUs']) is int and c['CPUs'] > 0 and type(c['RAM_bytes']) is int and c['RAM_bytes'] > 0,'reviewed CPU resources')
    proof = bound(c['resource_proof'])
    require(proof['complete'] is True and proof['independent_review_accepted'] is True and proof['phase'] == 'full_score',
            'fresh accepted owning CPU resource decision required')
    for key in ('CPUs','RAM_bytes','duration_seconds','child_cap_seconds','CPU_finish_margin_seconds','publication_margin_seconds','kill_grace_seconds'):
        require(proof['resources'][key] == c[key],'reviewed CPU resource binding: ' + key)
    packet(c)


def duration_seconds(value):
    days,clock = value.split('-',1) if '-' in value else ('0',value)
    parts = [int(x) for x in clock.split(':')]
    require(len(parts) in (2,3),'Slurm duration format')
    if len(parts) == 2: parts.insert(0,0)
    return int(days)*86400+parts[0]*3600+parts[1]*60+parts[2]


def memory_bytes(value):
    match = re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)([KMGT]?)',value)
    require(match is not None,'Slurm memory format')
    return int(float(match.group(1))*1024**('KMGT'.index(match.group(2))+1 if match.group(2) else 0))


def allocation(c):
    job = os.environ.get('SLURM_JOB_ID','')
    require(job == c['standing_CPU_job_id'] and re.fullmatch('[0-9]+',job)
            and os.environ.get('SLURM_CLUSTER_NAME') == 'delta','actual Delta owning job')
    require(os.environ.get('CUDA_VISIBLE_DEVICES','') == '' and not any(os.environ.get(k) for k in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS'))
            and all(os.environ.get(k,'') in ('','0') for k in ('SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK')),
            'CPU-only allocation environment')
    raw = subprocess.check_output(['scontrol','show','job',job,'-o'],universal_newlines=True,timeout=10,env=dict(os.environ,TZ='UTC'))
    f = dict(x.split('=',1) for x in raw.split() if '=' in x)
    require(f['JobId'] == job and f['JobState'] == 'RUNNING' and f['Account'] == c['expected_account']
            and f['Partition'] in c['allowed_partitions'] and f['Partition'] in ('cpu','cpu-interactive')
            and f['Account'].endswith('-cpu') and f['QOS'] == c['expected_qos'],'actual CPU identity/account/partition/QoS')
    require(re.search(r'\(' + str(os.getuid()) + r'\)',f['UserId']) and f['Requeue'] == '0'
            and f['Restarts'] == '0' and f['NumNodes'] == '1','own single-node nonrequeued job')
    tres = dict(x.split('=',1) for x in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in x)
    require(not any(k.startswith('gres/gpu') for k in tres) and int(f['NumCPUs']) == c['CPUs']
            and int(tres['cpu']) == c['CPUs'] and memory_bytes(tres['mem']) == c['RAM_bytes']
            and duration_seconds(f['TimeLimit']) == c['duration_seconds'],'actual reviewed CPU resource tuple')
    require(Path(f['WorkDir']).resolve() == Path(c['runtime']).resolve(),'original runtime working directory')
    hosts = subprocess.check_output(['scontrol','show','hostnames',f['NodeList']],universal_newlines=True,timeout=10).split()
    require(socket.gethostname().split('.')[0] in {x.split('.')[0] for x in hosts},'actual compute node')
    end = datetime.datetime.fromisoformat(f['EndTime']).replace(tzinfo=datetime.timezone.utc).timestamp()
    return dict(job_id=job,host=socket.gethostname(),scontrol_job=raw,fields=f,tres=tres,end_epoch=end,captured_unix=time.time())


def supervise_once(c,request_path,config_ref=None):
    require(config_ref is not None and bound(config_ref) == c, 'exact CPU config bytes required')
    validate_config(c)
    initial = allocation(c); initial_end = min(initial['end_epoch'],time.time()+c['duration_seconds'])
    evidence = Path(c['evidence_output']); evidence.mkdir(parents=True,exist_ok=False)
    child = None; record = None
    try:
        write(evidence/'READY.json',dict(phase='full_score',actual_CPU_job_id=initial['job_id'],allocation=initial,
            source_commit=SOURCE,packet_manifest_sha256=c['packet_manifest_sha256'],initial_end=initial_end,GPU_admitted=False))
        request_path = Path(request_path)
        while not request_path.exists():
            current = allocation(c)
            if time.time() >= min(initial_end,current['end_epoch'])-c['CPU_finish_margin_seconds']:
                raise TimeoutError('standing request window expired')
            time.sleep(0.5)
        require(not request_path.is_symlink(),'ordinary request required')
        raw = request_path.read_bytes(); request_sha = hashlib.sha256(raw).hexdigest(); r = decode(raw)
        require(set(r) == set(decode((P/'request.template.json').read_bytes())), 'closed request fields')
        marker = Path(r['GPU_WAITING_marker_path']); marker_sha = r['GPU_WAITING_marker_sha256']
        acquired = verify_request_files(request_path,request_sha,marker,marker_sha)
        require(decode(acquired['request_bytes']) == r, 'request parsed from authenticated buffer')
        waiting = decode(acquired['marker_bytes']); validate_request(c,r,waiting)
        current = allocation(c)
        deadline = child_deadline(c,waiting,initial_end,current['end_epoch'])
        write(evidence/'request.json',r); write(evidence/'WAITING.json',waiting); write(evidence/'allocation-before.json',current)
        base = bound(c['base_parameters'])
        require(set(base) == set(decode((P/'parameters.template.json').read_bytes())), 'closed base parameter fields')
        require(base['accepted_source_commit'] == SOURCE and base['phase'] == 'full_score'
                and base['accepted_runtime'] == c['runtime'] and base['new_g3_output'] == c['frozen_G3_root']
                and base['frozen_G3_sha256'] == c['frozen_G3_sha256']
                and base['bank_file_sha256'] == c['bank_file_sha256']
                and base['bank_manifest_sha256'] == c['bank_manifest_sha256'],'base parameters config identities')
        base.update(actual_CPU_job_id=initial['job_id'],actual_future_GPU_job_id=r['actual_future_GPU_job_id'],
            packet_manifest_sha256=c['packet_manifest_sha256'],phase_request_sha256=request_sha,
            phase_deadline_unix=deadline,evidence_output=str(evidence))
        parameters = evidence/'parameters.json'; write(parameters,base)
        env = dict(os.environ,CUDA_VISIBLE_DEVICES='',DC_CLUSTER='delta',DC_PYTHON=c['python'],DC_RUN_MANIFEST_GIT='0',
            PYTHONPATH=c['runtime'],PYTHONDONTWRITEBYTECODE='1',HF_HUB_CACHE='/work/nvme/beto/swong2',
            TRANSFORMERS_CACHE='/work/nvme/beto/swong2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
            HF_DATASETS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
        command = [c['python'],str(P/'validate-phase.py'),'--parameters',str(parameters),'--parameters-sha256',sha(parameters)]
        def recheck():
            require(bound(config_ref) == c, 'CPU config changed')
            packet(c); bound(c['base_parameters']); verify_request_files(request_path,request_sha,marker,marker_sha)
            return min(deadline,child_deadline(c,waiting,initial_end,allocation(c)['end_epoch']))
        # All mutable pre-entry identities checked again before the only child.
        recheck()
        with (evidence/'child.log').open('x') as log:
            verify_request_files(request_path,request_sha,marker,marker_sha)
            require(time.time() < deadline, 'fixed deadline elapsed before Popen')
            child = subprocess.Popen(command,cwd=c['runtime'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            record = observe_child(child,deadline,recheck)
        record.update(command=command,request_sha256=request_sha,guard_result_sha256=sha(evidence/'guard-result.json'))
        write(evidence/'child-execution.json',record)
        result = bound(dict(path=str(evidence/'guard-result.json'),sha256=record['guard_result_sha256']))
        recheck(); after = allocation(c); write(evidence/'allocation-after.json',after)
        record['deadline_unix'] = min(record['deadline_unix'],after['end_epoch']-c['CPU_finish_margin_seconds'])
        complete = validate_child_completion(c,r,record,result)
        spec = importlib.util.spec_from_file_location('a2_full_cpu_boundary',str(P/'validate-phase.py'))
        boundary = importlib.util.module_from_spec(spec); spec.loader.exec_module(boundary)
        require(boundary.capture_identities(base) == result['source_after'], 'independent supervisor boundary drift')
        require(sha(parameters) == command[-1], 'child parameters changed')
        captures = result['catalogue_capture_files']
        require(len(captures) == 4 and {x['virtual_path'] for x in captures} == set(CATALOGUES), 'exact catalogue snapshot closure')
        for item in captures:
            path = Path(item['captured_bytes_path'])
            require(path.parent == evidence and not path.is_symlink() and path.stat().st_size == item['bytes']
                and sha(path) == item['sha256'] == result['source_after']['catalogues'][item['virtual_path']],
                'immutable catalogue capture changed')
        complete['CPU_bound_config_sha256'] = config_ref['sha256']
        complete['parameters_sha256'] = command[-1]
        # Final hash checks precede one exclusive publication; original child bytes stay immutable.
        require(sha(evidence/'guard-result.json') == record['guard_result_sha256'],'guard changed before publication')
        recheck(); require(time.time() < record['deadline_unix'],'publication deadline missed')
        complete['child_execution_sha256'] = sha(evidence/'child-execution.json')
        write(evidence/'COMPLETE.pending.json',complete)
        recheck(); require(time.time() < record['deadline_unix'],'serialized publication deadline missed')
        os.link(str(evidence/'COMPLETE.pending.json'),str(evidence/'COMPLETE.json'))
        require(time.time() < record['deadline_unix'],'publication completed too late; FAILED supersedes COMPLETE')
        return complete
    except BaseException as error:
        if child is not None: terminate(child,c['kill_grace_seconds'])
        write(evidence/'FAILED.json',dict(complete=False,phase='full_score',error=repr(error),traceback=traceback.format_exc(),
            finished_unix=time.time(),automatic_retry=False,partial_preserved=True))
        raise
    finally:
        if child is not None: terminate(child,c['kill_grace_seconds'])


def main():
    def interrupted(signum,frame): raise TimeoutError('CPU supervisor termination signal ' + str(signum))
    for signum in (signal.SIGTERM,signal.SIGINT): signal.signal(signum,interrupted)
    ap = argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--config-sha256',required=True)
    args = ap.parse_args(); c = bound(dict(path=args.config,sha256=args.config_sha256))
    supervise_once(c,c['request_path'],dict(path=args.config,sha256=args.config_sha256))


if __name__ == '__main__': main()
