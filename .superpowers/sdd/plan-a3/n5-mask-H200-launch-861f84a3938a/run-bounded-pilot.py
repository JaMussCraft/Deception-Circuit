"""Single root-authorized allocation only; bounded child, no RS/job mutation."""
import os,sys,json,time,hashlib,subprocess,signal,datetime
from pathlib import Path
G=Path(__file__).resolve().parent;cfg=json.loads((G/'launch-config.json').read_text());O=Path(cfg['output_root']);A=Path(cfg['authority_root'])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def deadlines(initial_end,current_end):
    end=min(float(initial_end),float(current_end));return end-360,end-300
def completed_receipt(path,release):
    path=Path(path);assert {p.name for p in path.iterdir()}=={'payload.json','COMPLETE.json'}
    marker=json.loads((path/'COMPLETE.json').read_text());assert marker['kind']=='a3_complete' and set(marker['files'])=={'payload.json'}
    entry=marker['files']['payload.json'];assert entry['sha256']==sha(path/'payload.json') and entry['bytes']==(path/'payload.json').stat().st_size
    receipt=json.loads((path/'payload.json').read_text())
    assert receipt['kind']=='a3_mask_pilot_v2' and receipt['complete'] is True and receipt['exit_code']==0 and receipt['injected'] is False
    assert receipt['identity']['commit']==cfg['commit'] and receipt['reservation_id']==release['reservation_id'] and str(receipt['allocation_job_id'])==str(release['job_id'])
    assert receipt['pilot_inventory_sha256']==release['pilot_inventory_sha256'] and receipt['target_inventory_sha256']==release['full_target_inventory_sha256']
    assert receipt['purpose']=='validation_timing' and receipt['timing_only'] is True and receipt['final'] is False and receipt['may_select_checkpoint'] is False
    assert receipt['arms']==['constrained','unconstrained'] and 'H200' in receipt['hardware']
    assert [a['arm'] for a in receipt['arm_measurements']]==receipt['arms'] and all(a['source_split']=='validation' and a['purpose']=='validation_timing' for a in receipt['arm_measurements'])
    classes={'base_proof','targets','update','validation','binary_parity','checkpoint','selection','guard_initial','guard'}|{k+':'+task for task in ['far_v2','sdr_v2','ser_v2'] for k in ['H_bank','assessment']}
    assert classes<=set(receipt['measurements']) and receipt['measurements']['guard'][0]['scope']['refreshes']==1185
    return receipt

release_path=Path(cfg['root_execution_release']);release=json.loads(release_path.read_text());job=os.environ.get('SLURM_JOB_ID')
assert job and release['job_id']==job and release['source_commit']==cfg['commit'] and release['output_dir']==cfg['model_output']
assert int(os.environ.get('SLURM_RESTART_COUNT','0'))==0
assert release['account']==cfg['account'] and release['allowed_partitions']==cfg['allowed_partitions']
assert release['model_execution_authorized'] is True and release['independent_input_review_accepted'] is True
assert release['launch_config_sha256']==sha(G/'launch-config.json') and release['launcher_sha256']==sha(__file__)
assert release['jobscript_sha256']==sha(G/'jobscript.sh')
assert release['complete_artifact_manifest_sha256']==cfg['expected_artifact_manifest_sha256']==sha(O/'evidence/complete-artifact-manifest.json')
assert release['CPU_run_manifest_sha256']==cfg['expected_CPU_run_manifest_sha256']==sha(O/'run_manifest.json')
for name in ['source_review_reference','input_review_reference']:
    ref=release[name];assert sha(ref['path'])==ref['sha256']
for rootname in ['admission','reservation']:
    ref=release[rootname+'_reference'];assert Path(ref['path']).resolve()==(A/rootname).resolve()
    for f,body in ref['files'].items():assert sha(A/rootname/f)==body['sha256']
assert not (O/'mask-pilot-1').exists(),'Fresh one-attempt output required; no automatic resume/retry'
logs=A/'launch-logs';logs.mkdir(exist_ok=False)
def event(value):
    with (logs/'events.jsonl').open('a') as f:f.write(json.dumps(dict(at=time.time(),**value))+'\n')
def current_end():
    p=subprocess.run(['scontrol','-o','show','job',job],capture_output=True,text=True,check=True,timeout=15,env=dict(os.environ,TZ='UTC'))
    facts=dict(x.split('=',1) for x in p.stdout.split() if '=' in x)
    assert facts['Account']==cfg['account'] and facts['Partition'] in cfg['allowed_partitions']
    assert facts.get('Requeue')=='0' and facts.get('Restarts')=='0' and facts['TimeLimit']=='00:45:00'
    assert facts['JobState']=='RUNNING' and facts['JobId']==job and Path(facts['WorkDir']).resolve()==Path(cfg['runtime'])
    end=datetime.datetime.strptime(facts['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp()
    return end
def stop_requested(signum,frame):raise RuntimeError('allocation termination signal '+str(signum))
for signum in [signal.SIGTERM,signal.SIGINT]:signal.signal(signum,stop_requested)
child=None;reason=None;initial=current_end();soft,hard=deadlines(initial,initial)
assert time.time()<soft,'Insufficient actual lease for bounded pilot entry'
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=cfg['runtime'],SPECIFICITY_A3_MASK_REPO_ROOT=cfg['runtime'],A3_MASK_PYTHON=cfg['python'],DC_CLUSTER='delta',DC_RUN_MANIFEST_GIT='0',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
try:
    event(dict(event='begin',soft=soft,hard=hard,source_commit=cfg['commit']))
    child=subprocess.Popen(cfg['args'],cwd=cfg['runtime'],env=env,start_new_session=True)
    while child.poll() is None:
        latest=current_end();soft,hard=deadlines(initial,latest)
        if time.time()>=soft:reason='fixed_finish_reserve';break
        time.sleep(min(5,max(.01,soft-time.time())))
    if reason:
        event(dict(event='TERM',reason=reason));os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=max(.01,hard-time.time()))
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=15)
        raise TimeoutError(reason+'; incompletepilot, noautomaticretry')
    assert child.returncode==0,('pilot child failed',child.returncode)
    assert time.time()<hard,'Pilot exited after protected finish boundary'
    receipt=completed_receipt(O/'mask-pilot-1/pilot-receipt',release)
    event(dict(event='child_success',exit_code=child.returncode,remaining=initial-time.time()))
except BaseException as ex:
    if child is not None and child.poll() is None:
        os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=15)
    event(dict(event='failed',error=repr(ex),partial_preserved=True));raise
