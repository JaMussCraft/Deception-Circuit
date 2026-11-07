"""One real CPU allocation; no retry, source mutation, GPU or model admission."""
import os,sys,pathlib,json,shutil,time,subprocess,signal,resource,traceback
from job_common import CFG,P,W,B,O,C,sha,write,utc,allocation,environment,source_binding,packet_binding
from commands import commands
START=time.monotonic();DEADLINE=START+CFG['internal_deadline_seconds'];ACTIVE=None

def stop_child():
    global ACTIVE
    if ACTIVE is None or ACTIVE.poll() is not None:return
    os.killpg(ACTIVE.pid,signal.SIGTERM)
    try:ACTIVE.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(ACTIVE.pid,signal.SIGKILL);ACTIVE.wait(timeout=10)
def signal_stop(signum,frame):raise TimeoutError('job termination signal '+str(signum))
for signum in (signal.SIGTERM,signal.SIGINT):signal.signal(signum,signal_stop)

def ancestry():
    original=W/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819'
    basis=json.loads((original/'evidence/ancestry-before.json').read_text());result={}
    dynamic={str(root/'docs/research'/name) for root in (W,pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit')) for name in ('held_out.json','directions.json')}
    for name,expected in basis.items():
        p=pathlib.Path(name);value=dict(sha256=sha(p),bytes=p.stat().st_size)
        if name not in dynamic:assert value==expected,('original static ancestry bytes changed',name)
        result[name]=value
    return result

def initialize():
    packet=packet_binding();alloc=allocation()
    assert not O.exists(),'Fresh output root required; preserve any existing partial run'
    (O/'evidence').mkdir(parents=True)
    write(O/'evidence/cpu-release.json',packet['release']);write(O/'evidence/proposal-binding.json',packet)
    write(O/'evidence/allocation-start.json',alloc)
    before=source_binding();inputs=ancestry()
    write(O/'evidence/source-binding-before.json',before);write(O/'evidence/ancestry-before.json',inputs)
    snapshot=json.loads(pathlib.Path(CFG['snapshot']).read_text())
    write(O/'evidence/source-pointer.json',dict(source_commit=C,runtime_root=str(B),snapshot=CFG['snapshot'],cpu_preparation_only=True,execution_admitted=False))
    original=W/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819'
    for name in ('root-ruling.json','execution-settings.json'):
        shutil.copyfile(original/name,O/name);assert (original/name).read_bytes()==(O/name).read_bytes()
    write(O/'evidence/environment.json',{key:value for key,value in environment().items() if key in ('W','B','O','C','E','PYTHONPATH','PYTHONDONTWRITEBYTECODE','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','HF_HOME','HF_HUB_CACHE','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE','TOKENIZERS_PARALLELISM','DC_PYTHON','A3_REPO_ROOT','SPECIFICITY_A3_EDGE_REPO_ROOT','SPECIFICITY_A3_MASK_REPO_ROOT','A3_MASK_PYTHON','SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE','CUDA_VISIBLE_DEVICES') or key.startswith('SLURM_') and not any(secret in key.upper() for secret in ('TOKEN','SECRET','CREDENTIAL','JWT','AUTH'))})
    assert pathlib.Path('/work/nvme/beto/swong2/hub').is_dir(),'Original pinned offline cache must be accessible on compute node'
    return before,inputs

def run_step(name,command):
    global ACTIVE
    packet_binding();alloc=allocation();remaining=DEADLINE-time.monotonic();assert remaining>15,'CPU preparation internal deadline reached'
    cap=min(1200,remaining);record=dict(step=name,command=command,cwd=str(B),commit=C,started_utc=utc(),timeout_seconds=cap,allocation=alloc,execution_authorized=False,model_loaded=False)
    path=O/'evidence'/(name+'-command.json');write(path,dict(record,state='running'));started=time.monotonic()
    try:
        with (O/'evidence'/(name+'.log')).open('x') as log:
            ACTIVE=subprocess.Popen(command,cwd=B,env=environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:code=ACTIVE.wait(timeout=cap)
            except subprocess.TimeoutExpired:
                stop_child();code=124
        record.update(exit_code=code,state='completed',elapsed_seconds=time.monotonic()-started,finished_utc=utc(),log=str(O/'evidence'/(name+'.log')));write(path,record)
        assert code==0,(name,'failed; preserve evidence and stop')
    finally:stop_child();ACTIVE=None

def main():
    status=dict(kind='source_refresh_batch_real_cpu_preparation',commit=C,output=str(O),started_utc=utc(),execution_authorized=False,model_loaded=False,scientific_verdict=None)
    try:
        before,inputs=initialize()
        for name,command in commands():
            print('BEGIN '+name+' '+utc(),flush=True);run_step(name,command)
        after=source_binding();assert before['source_sha256']==after['source_sha256'] and before['input_links']==after['input_links']
        write(O/'evidence/source-binding-after.json',after);write(O/'evidence/final-input-binding.json',ancestry());write(O/'evidence/allocation-finish.json',allocation())
        artifacts={str(path.relative_to(O)):dict(sha256=sha(path),bytes=path.stat().st_size) for folder in ('canonical','mask','mask-source-settings','edge') for path in (O/folder).rglob('*') if path.is_file()}
        write(O/'evidence/complete-artifact-manifest.json',dict(commit=C,artifacts=artifacts,unchanged_source=True,execution_authorized=False))
        status.update(complete=True,exit_code=0)
    except BaseException as error:
        stop_child();status.update(complete=False,exit_code=1,error=repr(error),traceback=traceback.format_exc());raise
    finally:
        status.update(finished_utc=utc(),wall_seconds=time.monotonic()-START,actual_slurm_job_id=os.environ.get('SLURM_JOB_ID'),hostname=os.uname().nodename)
        if (O/'evidence').is_dir():write(O/'evidence/cpu-job-completion.json',status)
        print(json.dumps(status,indent=2),flush=True)
if __name__=='__main__':main()
