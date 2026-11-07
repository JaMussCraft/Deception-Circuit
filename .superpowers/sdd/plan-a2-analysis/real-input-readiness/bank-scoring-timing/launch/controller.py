"""One bounded original-bank/prefix4 attempt. No source patch/model injection/retry."""
import os,sys,json,pathlib,time,subprocess,signal,traceback,math,shutil
from common import C,L,B,MAIN,PILOT,sha,write,utc,packet,source,budget,allocation,gpu_release,environment
ACTIVE=None;START=time.time()
def terminate():
    if ACTIVE is None or ACTIVE.poll() is not None:return
    os.killpg(ACTIVE.pid,signal.SIGTERM)
    try:ACTIVE.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(ACTIVE.pid,signal.SIGKILL);ACTIVE.wait(timeout=10)
def interrupted(signum,frame):raise TimeoutError('termination signal '+str(signum))
for signum in (signal.SIGTERM,signal.SIGINT):signal.signal(signum,interrupted)
OUT=pathlib.Path(os.environ['A2_TIMING_EXECUTION_OUTPUT']);assert not OUT.exists();OUT.mkdir(parents=True)
def end_epoch(facts):
    if os.environ.get('SLURM_JOB_END_TIME'):return min(START+1500,int(os.environ['SLURM_JOB_END_TIME']))
    return min(START+1500,time.mktime(time.strptime(facts['EndTime'],'%Y-%m-%dT%H:%M:%S')))
def run(name,command,deadline,env):
    global ACTIVE
    left=deadline-time.time();assert left>0,(name,'no remaining work lease')
    started=time.time();record=dict(command=command,cwd=str(B),started_utc=utc(),timeout_seconds=left)
    try:
        with (OUT/(name+'.stdout')).open('x') as stdout,(OUT/(name+'.stderr')).open('x') as stderr:
            ACTIVE=subprocess.Popen(command,cwd=B,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            try:code=ACTIVE.wait(timeout=left)
            except subprocess.TimeoutExpired:terminate();code=124
        record.update(exit_code=code,elapsed_seconds=time.time()-started,finished_utc=utc());write(OUT/(name+'-command.json'),record)
        assert code==0,(name,'failed; preserve partial; no automatic retry')
    finally:terminate();ACTIVE=None

def probe(name,deadline,env):
    target=OUT/(name+'.json');run(name,[C['python'],str(L/'gpu-probe.py')],deadline,dict(env,A2_GPU_PROBE_OUTPUT=str(target)));return json.loads(target.read_text())
try:
    packet();release=gpu_release();alloc=allocation(gpu=True,release=release);lease_end=end_epoch(alloc['facts']);work_end=lease_end-C['finish_reserve_seconds'];assert work_end>time.time()
    write(OUT/'allocation.json',alloc);write(OUT/'root-release.json',release)
    before=source();write(OUT/'source-before.json',before);write(OUT/'budget-before-bank.json',budget(prospective=False,release=release))
    assert not ((MAIN/'bank').exists() or (MAIN/'bank').is_symlink()) and not ((MAIN/'score').exists() or (MAIN/'score').is_symlink()) and not (PILOT.exists() or PILOT.is_symlink()),'fresh bank/pilot required'
    env=environment();initial=probe('gpu-before-bank',work_end,env)
    run('bank',C['bank_command'],work_end,env)
    bank_manifest_path=MAIN/'bank/run_manifest.json';bank_manifest=json.loads(bank_manifest_path.read_text());execution=bank_manifest['execution']
    assert execution['gpu_name']==initial['gpu_name'] and execution['dtype']==C['dtype'] and str(execution['slurm_job_id'])==os.environ['SLURM_JOB_ID']
    binding=dict(source_commit=C['commit'],groups_file_sha256=C['groups_file_sha256'],bank_file=str(MAIN/'bank/banks.json'),bank_file_sha256=sha(MAIN/'bank/banks.json'),bank_manifest_sha256=sha(bank_manifest_path),gpu_uuid=initial['gpu_uuid'],gpu_name=initial['gpu_name'],dtype=execution['dtype'],device=execution['device'],bank_execution=execution)
    write(OUT/'completed-bank-binding.json',binding)
    alloc2=allocation(gpu=True,release=release);lease_end=min(lease_end,end_epoch(alloc2['facts']));work_end=lease_end-C['finish_reserve_seconds'];remaining=lease_end-time.time()
    if remaining<C['score_lease_floor_seconds']:
        write(OUT/'BANK_ONLY.json',dict(complete_bank=True,prefix_score_started=False,remaining_seconds=remaining,required_orientation_floor_seconds=C['score_lease_floor_seconds'],H200_completion_forecast=False,automatic_retry=False));raise SystemExit(0)
    write(OUT/'budget-before-score.json',budget(prospective=False,release=release));source()
    second=probe('gpu-before-score',work_end,env)
    assert all(second[key]==initial[key] for key in ('gpu_uuid','gpu_name','device','visible_devices','total_memory_bytes','compute_capability')),'bank/score device changed'
    PILOT.mkdir(parents=True,exist_ok=False)
    with (PILOT/'groups.json').open('xb') as stream:stream.write(pathlib.Path(C['groups']).read_bytes())
    assert sha(PILOT/'groups.json')==C['groups_file_sha256'];(PILOT/'bank').symlink_to(MAIN/'bank',target_is_directory=True)
    assert (PILOT/'bank').resolve()==(MAIN/'bank').resolve() and not (MAIN/'score').exists()
    # The original CLI re-runs full A1 and A2 checks; after tokenizer identity/layout
    # it calls _validate_live immediately before the ORIGINAL model loader.
    # No model_loader callback is supplied (that would mark the artifact injected).
    last=allocation(gpu=True,release=release);lease_end=min(lease_end,end_epoch(last['facts']));work_end=lease_end-C['finish_reserve_seconds']
    if lease_end-time.time()<C['score_lease_floor_seconds']:
        write(OUT/'BANK_ONLY.json',dict(complete_bank=True,prefix_score_started=False,reason='lease fell below prospectively fixed eligibility floor during staging',partial_pilot_namespace_preserved=True,automatic_retry=False));raise SystemExit(0)
    run('score-prefix4',C['score_command'],work_end,env)
    score_path=PILOT/'score/run_manifest.json';score=json.loads(score_path.read_text());counts=score['counts'];e=score['execution']
    assert counts['rows']==counts['expected']==2484 and counts['positive_controls']==144
    assert e['gpu_name']==initial['gpu_name'] and e['dtype']==C['dtype'] and str(e['slurm_job_id'])==os.environ['SLURM_JOB_ID']
    assert sha(MAIN/'bank/banks.json')==binding['bank_file_sha256'] and sha(bank_manifest_path)==binding['bank_manifest_sha256'] and not (MAIN/'score').exists()
    after=source();write(OUT/'source-after.json',after)
    write(OUT/'COMPLETE.json',dict(scope='one measured original-H bank + prefix4 scoring only',complete=True,full_scoring_admitted=False,source_commit=C['commit'],gpu_uuid=initial['gpu_uuid'],gpu_name=initial['gpu_name'],bank_binding=binding,score_manifest_sha256=sha(score_path),score_execution=e,counts=counts,job_id=os.environ['SLURM_JOB_ID'],wall_seconds=time.time()-START,assessment_effects_inspected=False,automatic_retry=False))
except SystemExit:raise
except BaseException as error:
    terminate();write(OUT/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),wall_seconds=time.time()-START,partial_preserved=True,automatic_retry=False));raise
