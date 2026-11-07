#!/usr/bin/env python3
"""Two discarded interpreters for data timing; emits no operational authority."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import socket
import subprocess
import sys
import time
import traceback

P=Path(__file__).resolve().parent
CPU=P.parent/'plan-a2-full-score-operational186/candidate/cpu'
SOURCE='50e947bb852613e3a270082651f2bd1b7bb0c525'
RUNTIME='/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime'
POLICY=dict(CPUs=4,RAM_bytes=34359738368,duration_seconds=900,bootstrap_seconds=75,prime_cap_seconds=480,
            fresh_cap_seconds=240,publication_margin_seconds=45,CPU_finish_margin_seconds=60,kill_grace_seconds=15,fixed_GPU_window_seconds=300)


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def unique(pairs):
    result={}
    for k,v in pairs:
        require(k not in result,'duplicate JSON key');result[k]=v
    return result


def read_ref(ref):
    path=Path(ref['path']);require(path.is_absolute() and not path.is_symlink(),'ordinary absolute bound reference')
    raw=path.read_bytes();require(hashlib.sha256(raw).hexdigest()==ref['sha256'] and sha(path)==ref['sha256'],'bound bytes changed')
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))


def write(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,str(path));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def helpers(c):
    pins=json.loads((P/'native-helper-pins.json').read_text())
    for path,want in pins.items():require(sha(path)==want,'Task2 helper changed: '+path)
    return load_module('timing239_native',CPU/'validate-phase.py'),load_module('timing239_supervisor',CPU/'supervisor.py')


def packet(c):
    manifest=read_ref(c['packet_manifest'])
    for path,want in manifest['files'].items():require(sha(path)==want,'diagnostic packet/source changed: '+path)
    return c['packet_manifest']['sha256']


def ensure_nonoperational(value):
    require(value['kind']=='A2_DATA_TIMING_DIAGNOSTIC_V1' and value['diagnostic_only'] is True
            and value['operational_admission'] is False,'diagnostic schema only')
    forbidden={'complete','phase','actual_future_GPU_job_id','waiting_sha256','timely_window','bound_gpu_config_sha256',
               'full_domain_support_audit_complete','issued_at','expires_at','request_sha256'}
    require(not forbidden.intersection(value),'operational authority fields forbidden')


def diagnostic_deadline(stage,started,initial_end,current_end):
    require(stage in ('prime','fresh'),'diagnostic stage only')
    require(all(type(x) in (int,float) and math.isfinite(x) for x in (started,initial_end,current_end)),'finite deadlines')
    reserve=POLICY['CPU_finish_margin_seconds']
    if stage=='prime':reserve+=POLICY['fresh_cap_seconds']+POLICY['publication_margin_seconds']
    deadline=min(started+POLICY[stage+'_cap_seconds'],initial_end-reserve,current_end-reserve)
    if deadline<=started:raise TimeoutError('diagnostic fixed CPU envelope cannot fit; no extension')
    return deadline


def child_command(c,config_path,config_sha,stage,output,deadline):
    require(stage in ('prime','fresh'),'only discarded data interpreters')
    require(c['python']=='/u/swong2/.conda/envs/mgnp/bin/python','bank matching mgnp required')
    return [c['python'],'-B',str(P/'child.py'),'--config',str(config_path),'--config-sha256',config_sha,
            '--diagnostic-stage',stage,'--output',str(output),'--deadline',str(deadline)]


def distinct_normal_processes(prime,fresh,parent_pid):
    require(prime['pid']!=fresh['pid'] and parent_pid not in (prime['pid'],fresh['pid']),'fresh interpreter/process required')
    require(all(x['exit_code']==0 and x['term_sent_at'] is None for x in (prime,fresh)),'both processes must terminate normally')


def local_orientation(fresh_pipeline_seconds,publication_seconds):
    require(fresh_pipeline_seconds>=0 and publication_seconds>=0,'actual positive timing observations')
    return dict(fixed_GPU_window_seconds=300,proposed_publication_margin_seconds=45,
        local_component_headroom_seconds=300-fresh_pipeline_seconds-max(45,publication_seconds),
        fresh_CPU_cap_seconds=240,CPU_finish_margin_seconds=60,kill_grace_seconds=15,
        request_transfer_remote_publication_measured=False,operational_feasible=None,
        limitation='Local measurement only. Actual request acquisition/transfer/root GPU publication costs remain unmeasured; no execution admission.')


def metrics(pid=None):
    pid=os.getpid() if pid is None else pid
    value=dict(pid=pid,captured_unix=time.time(),host=socket.gethostname())
    for name in ('status','cgroup'):
        try:value[name]=(Path('/proc')/str(pid)/name).read_text()
        except OSError as error:value[name]=dict(unavailable=repr(error))
    if pid==os.getpid():
        r=resource.getrusage(resource.RUSAGE_SELF)
        value['process_usage']=dict(user_seconds=r.ru_utime,system_seconds=r.ru_stime,peak_RSS_bytes=r.ru_maxrss*1024)
    # Never label a process leaf as the job aggregate. Preserve both scopes.
    raw=value.get('cgroup','');value['cgroup_observations']=[]
    if isinstance(raw,str):
        for line in raw.splitlines():
            parts=line.split(':',2)
            if len(parts)!=3:continue
            root=Path('/sys/fs/cgroup')
            if parts[0]!='0':root=root/'memory'
            scope=root/parts[2].lstrip('/')
            candidates=[('process',scope)]
            job=os.environ.get('SLURM_JOB_ID','')
            for ancestor in (scope,)+tuple(scope.parents):
                if re.fullmatch('job[_-]'+re.escape(job),ancestor.name):candidates.append(('job',ancestor));break
            for label,path in candidates:
                observed=dict(scope=label,path=str(path),files={})
                for name in ('memory.current','memory.peak','memory.max','memory.events','memory.usage_in_bytes','memory.max_usage_in_bytes','memory.limit_in_bytes'):
                    try:observed['files'][name]=(path/name).read_text().strip()
                    except OSError:pass
                observed['available']=bool(observed['files']);value['cgroup_observations'].append(observed)
    return value


def allocation_config(c):
    return dict(standing_CPU_job_id=c['actual_CPU_job_id'],expected_account=c['expected_account'],expected_qos=c['expected_qos'],
        allowed_partitions=['cpu','cpu-interactive'],CPUs=4,RAM_bytes=34359738368,duration_seconds=900,runtime=RUNTIME)


def validate_config(c):
    template=json.loads((P/'config.template.json').read_text())
    require(set(c)==set(template),'closed diagnostic config')
    require(c['kind']=='A2_DATA_TIMING_DIAGNOSTIC_CONFIG_V1' and c['diagnostic_only'] is True,'separate diagnostic config')
    require(c['policy']==POLICY and c['python']=='/u/swong2/.conda/envs/mgnp/bin/python','fixed reviewed diagnostic proposal')
    require(isinstance(c['actual_CPU_job_id'],str) and re.fullmatch('[0-9]+',c['actual_CPU_job_id']),'actual CPU job binding required')
    require(c['expected_account'] and c['expected_qos'] and c['evidence_output'],'actual placement/output bindings required')
    packet(c)
    accepted=read_ref(c['Task2_source_acceptance'])
    require(accepted['Task2_GREEN_accepted'] is True and accepted['independent_source_review_accepted'] is True,
            'root must accept actual Task2 GREEN and source before this diagnostic')
    require(accepted['helper_source_sha256']==json.loads((P/'native-helper-pins.json').read_text()),'exact accepted helper bytes')
    fixture=read_ref(accepted['actual_fixture_result']);read_ref(accepted['independent_source_review'])
    require(fixture['complete'] is True and fixture['actual_job_id']==accepted['actual_fixture_job_id']
        and fixture['status']=='TASK2_R224_RED_THEN_GREEN_OBSERVED', 'actual Task2 completed GREEN receipt')
    green=[row for row in fixture['observations'] if row['mode']=='green']
    require(len(green)==2 and all(row['exit_code']==0 and row['tests']==226 and row['failures']==row['errors']==row['skips']==0 for row in green)
        and green[0]['test_names']==green[1]['test_names'], 'both actual Task2 GREEN environments')
    p=read_ref(c['data_parameters'])
    require(p['accepted_runtime']==RUNTIME and p['accepted_source_commit']==SOURCE and p['phase']=='full_score'
            and p['root_source_review_accepted'] is True,'same true native data scope')
    require(len(read_ref(p['input_manifest'])['namespace_aliases'])==11,'original complete eleven-alias manifest')
    return p


def parameters(c,output,deadline):
    value=read_ref(c['data_parameters'])
    forbidden={'actual_future_GPU_job_id','phase_request_sha256','phase_request','GPU_WAITING_marker_path'}
    require(not forbidden.intersection(value),'invented operational identity forbidden')
    value.update(actual_CPU_job_id=c['actual_CPU_job_id'],packet_manifest_sha256=c['packet_manifest']['sha256'],
                 phase_deadline_unix=deadline,evidence_output=str(output))
    return value


def run_stage(c,config_ref,stage,root,initial_end,v,s):
    started=time.time();start_mono=time.monotonic();start_usage=resource.getrusage(resource.RUSAGE_CHILDREN)
    start_parent_usage=resource.getrusage(resource.RUSAGE_SELF)
    before=s.allocation(allocation_config(c));deadline=diagnostic_deadline(stage,started,initial_end,before['end_epoch'])
    out=root/stage;out.mkdir();write(out/'allocation-before.json',before);write(out/'parent-before.json',metrics())
    params=parameters(c,out,deadline);write(out/'data-parameters.json',params)
    command=child_command(c,config_ref['path'],config_ref['sha256'],stage,out,deadline)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',DC_CLUSTER='delta',DC_RUN_MANIFEST_GIT='0',DC_PYTHON=c['python'],
        PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=RUNTIME,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',
        HF_HUB_CACHE='/work/nvme/beto/swong2',TRANSFORMERS_CACHE='/work/nvme/beto/swong2',
        OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    child=None;execution=None
    def recheck():
        require(read_ref(config_ref)==c,'diagnostic config changed');packet(c)
        current=s.allocation(allocation_config(c))
        return min(deadline,current['end_epoch']-60)
    try:
        recheck()
        with (out/'child.log').open('x') as stream:
            child=subprocess.Popen(command,cwd=RUNTIME,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            write(out/'child-entry-process.json',metrics(child.pid))
            execution=s.observe_child(child,deadline,recheck)
        observation_ref=dict(path=str(out/'child-observation.json'),sha256=sha(out/'child-observation.json'))
        record=read_ref(observation_ref);ensure_nonoperational(record)
        require(record['pid']==child.pid and record['parent_pid']==os.getpid() and record['diagnostic_stage']==stage,'actual child identity')
        # Independent supervisor data boundary and exact saved catalogue checks,
        # inside the same fresh240 envelope, after normal child exit.
        require(v.capture_identities(params)==record['source_after'],'independent supervisor source/input/catalogue/bank drift')
        for row in record['catalogue_capture_files']:
            path=Path(row['captured_bytes_path'])
            require(path.parent==out and not path.is_symlink() and path.stat().st_size==row['bytes']
                    and sha(path)==row['sha256']==record['source_after']['catalogues'][row['virtual_path']], 'immutable catalogue capture changed')
        require(len(record['catalogue_capture_files'])==4,'all four catalogue captures')
        require(sha(out/'child-observation.json')==observation_ref['sha256'],'child observation bytes changed')
        require(sha(out/'data-parameters.json')==record['data_parameters_sha256'],'child parameters changed')
        current_deadline=recheck();require(time.time()<current_deadline,'independent boundary observed too late')
        write(out/'allocation-after.json',s.allocation(allocation_config(c)));write(out/'parent-after.json',metrics())
        stop_usage=resource.getrusage(resource.RUSAGE_CHILDREN);stop_parent_usage=resource.getrusage(resource.RUSAGE_SELF)
        result=dict(pid=child.pid,exit_code=execution['exit_code'],term_sent_at=execution['term_sent_at'],
            started_unix=started,finished_unix=time.time(),wall_seconds=time.monotonic()-start_mono,deadline_unix=current_deadline,
            child_user_seconds=stop_usage.ru_utime-start_usage.ru_utime,child_system_seconds=stop_usage.ru_stime-start_usage.ru_stime,
            parent_user_seconds=stop_parent_usage.ru_utime-start_parent_usage.ru_utime,
            parent_system_seconds=stop_parent_usage.ru_stime-start_parent_usage.ru_stime,
            child_observation=observation_ref,command=command,diagnostic_stage=stage,operational_admission=False)
        write(out/'pipeline-observation.json',result)
        require(time.time()<current_deadline,'pipeline serialization observed too late')
        result['wall_seconds_through_evidence']=time.monotonic()-start_mono
        return result
    finally:
        if child is not None:s.terminate(child,15)
        if execution is None and child is not None:
            write(out/'failed-process.json',dict(pid=child.pid,exit_code=child.returncode,observed_unix=time.time(),no_retry=True))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--config-sha256',required=True)
    ap.add_argument('--dry-run',action='store_true');a=ap.parse_args()
    if a.dry_run:
        print(json.dumps(dict(diagnostic_only=True,policy=POLICY,new_interpreters=2,operational_admission=False,
            required_bindings_unset=True,commands=[child_command(dict(python='/u/swong2/.conda/envs/mgnp/bin/python'),a.config,a.config_sha256,x,'ABSENT/'+x,0) for x in ('prime','fresh')]),indent=2));return
    started=time.time();config_ref=dict(path=a.config,sha256=a.config_sha256);c=read_ref(config_ref);validate_config(c);v,s=helpers(c)
    before=s.allocation(allocation_config(c));initial_end=min(before['end_epoch'],started+900)
    require(time.time()-started<75,'bootstrap allowance missed')
    out=Path(c['evidence_output']);require(out.is_absolute(),'absolute fresh diagnostic output');out.mkdir(parents=True,exist_ok=False)
    def interrupted(signum,frame):raise TimeoutError('diagnostic interrupted '+str(signum))
    for signum in (signal.SIGTERM,signal.SIGINT):signal.signal(signum,interrupted)
    try:
        write(out/'diagnostic-entry.json',dict(kind='A2_DATA_TIMING_DIAGNOSTIC_V1',diagnostic_only=True,operational_admission=False,
            actual_CPU_job_id=c['actual_CPU_job_id'],allocation=before,process=metrics(),bootstrap_seconds=time.time()-started))
        prime=run_stage(c,config_ref,'prime',out,initial_end,v,s)
        fresh=run_stage(c,config_ref,'fresh',out,initial_end,v,s)
        distinct_normal_processes(prime,fresh,os.getpid())
        publication_started=time.monotonic();publication_end=min(time.time()+45,initial_end-60,s.allocation(allocation_config(c))['end_epoch']-60)
        payload=dict(kind='A2_DATA_TIMING_DIAGNOSTIC_V1',diagnostic_only=True,operational_admission=False,
            prime=prime,fresh=fresh,actual_CPU_job_id=c['actual_CPU_job_id'],publication_scope='local evidence only; remote transfer/request/release not measured')
        ensure_nonoperational(payload)
        pending=out/'local-publication.pending.json';write(pending,payload);wanted=sha(pending)
        require(read_ref(dict(path=str(pending),sha256=wanted))==payload,'local serialization/readback changed')
        packet(c);require(time.time()<publication_end,'local publication allowance missed')
        os.link(str(pending),str(out/'local-publication.json'))
        elapsed=time.monotonic()-publication_started
        require(time.time()<publication_end,'local publication completed too late')
        report=dict(payload,status='LOCAL_COMPONENTS_MEASURED_ONLY',local_publication_seconds=elapsed,
            orientation=local_orientation(fresh['wall_seconds_through_evidence'],elapsed),total_wall_seconds=time.time()-started,
            final_process=metrics(),final_allocation=s.allocation(allocation_config(c)))
        ensure_nonoperational(report);write(out/'DIAGNOSTIC-REPORT.json',report)
        require(time.time()<initial_end-60,'diagnostic finish margin missed')
    except BaseException as error:
        write(out/'DIAGNOSTIC-FAILURE.json',dict(kind='A2_DATA_TIMING_DIAGNOSTIC_V1',diagnostic_only=True,operational_admission=False,
            error=repr(error),traceback=traceback.format_exc(),no_retry=True,process=metrics()))
        raise


if __name__=='__main__':main()
