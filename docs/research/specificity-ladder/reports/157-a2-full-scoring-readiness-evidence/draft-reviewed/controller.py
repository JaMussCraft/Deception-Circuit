"""One full scoring-only attempt; no bank rebuild, prefix, retry or finalization."""
import os,pathlib,json,time,subprocess,signal,traceback,datetime
from common import C,L,B,MAIN,sha,write,utc,packet,source,imports,budget,allocation,gpu_release,environment
ACTIVE=None;START=time.time();OUT=pathlib.Path(os.environ['A2_SCORE_EXECUTION_OUTPUT']);OUT.mkdir(parents=True,exist_ok=False)
def stop():
    if ACTIVE is None or ACTIVE.poll() is not None:return
    os.killpg(ACTIVE.pid,signal.SIGTERM)
    try:ACTIVE.wait(timeout=15)
    except subprocess.TimeoutExpired:os.killpg(ACTIVE.pid,signal.SIGKILL);ACTIVE.wait(timeout=15)
def interrupted(signum,frame):raise TimeoutError('allocation termination signal '+str(signum))
for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,interrupted)
def end(facts):return datetime.datetime.strptime(facts['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp()
try:
    packet();release=gpu_release();alloc=allocation(gpu=True,release=release);lease=min(START+C['maximum_minutes']*60,end(alloc['facts']));work_end=lease-C['finish_reserve_seconds']
    write(OUT/'allocation.json',alloc);write(OUT/'root-release.json',release);before=source();write(OUT/'source-before.json',before);write(OUT/'budget-before-score.json',budget(prospective=False,release=release))
    assert not ((MAIN/'score').exists() or (MAIN/'score').is_symlink()) and sha(MAIN/'bank/banks.json')==C['bank_file_sha256'] and sha(MAIN/'bank/run_manifest.json')==C['bank_manifest_sha256']
    env=environment();probe_path=OUT/'gpu-before-score.json'
    result=subprocess.run([C['python'],str(L/'gpu-probe.py')],cwd=B,env=dict(env,A2_GPU_PROBE_OUTPUT=str(probe_path)),timeout=max(1,work_end-time.time()),check=True)
    probe=json.loads(probe_path.read_text());assert probe['gpu_name']==C['expected_gpu_name'] and probe['device'].split(':')[0]=='cuda'
    # No physical UUID equality is required by the owning bank contract. Record actual new UUID; never rewrite bank provenance.
    write(OUT/'bank-reuse-binding.json',dict(bank_file_sha256=C['bank_file_sha256'],bank_manifest_sha256=C['bank_manifest_sha256'],new_allocation_gpu=probe,bank_gpu_name=C['expected_gpu_name'],bank_dtype=C['expected_bank_dtype'],physical_UUID_equality_claimed=False))
    source();budget(prospective=False,release=release)
    started=time.time()
    with (OUT/'score.stdout').open('x') as out,(OUT/'score.stderr').open('x') as err:
        ACTIVE=subprocess.Popen(C['score_command'],cwd=B,env=env,stdout=out,stderr=err,start_new_session=True)
        while ACTIVE.poll() is None:
            current=allocation(gpu=True,release=release);lease=min(lease,end(current['facts']));work_end=lease-C['finish_reserve_seconds']
            if time.time()>=work_end:raise TimeoutError('fixed finish boundary; partial retained, no automatic retry')
            time.sleep(min(15,max(.1,work_end-time.time())))
        assert ACTIVE.returncode==0,('score child failed',ACTIVE.returncode)
    write(OUT/'score-command.json',dict(command=C['score_command'],exit_code=0,elapsed_seconds=time.time()-started))
    assert sha(MAIN/'bank/banks.json')==C['bank_file_sha256'] and sha(MAIN/'bank/run_manifest.json')==C['bank_manifest_sha256']
    p,ar=imports();args=p.parser().parse_args(C['score_command'][2:]);prepared,selected,sidecar=p._load_context(args);receipt=p.a1.read_artifact(C['groups'])
    banks=p.read_stage(MAIN/'bank','banks.json','bank',args,receipt);p.validate_banks(receipt,prepared,banks)
    scored=p.read_stage(MAIN/'score','score.json','score',args,receipt)
    assert scored['kind']=='a2_scored' and scored['pilot'] is False and scored['limit']==0 and scored['injected'] is False
    assert scored['counts']['rows']==scored['counts']['expected']==len(scored['rows'])==59652
    p.validate_a2_scope(receipt,scored['rows'],limit=0,banks=banks,bank_path=MAIN/'bank/banks.json');p.a1.validate_positive_controls(scored['positive_controls'],p._prepared_domain(receipt),0)
    assert scored['execution_provenance']['gpu_name']==C['expected_gpu_name'] and scored['execution_provenance']['dtype']==C['dtype'] and str(scored['execution_provenance']['slurm_job_id'])==os.environ['SLURM_JOB_ID']
    after=source();write(OUT/'source-after.json',after)
    write(OUT/'COMPLETE.json',dict(complete=True,scope='all9groups full scoring only; no summary/finalization',source_commit=C['commit'],counts=scored['counts'],score_manifest_sha256=sha(MAIN/'score/run_manifest.json'),score_file_sha256=sha(MAIN/'score/score.json'),bank_unchanged=True,new_gpu_uuid=probe['gpu_uuid'],job_id=os.environ['SLURM_JOB_ID'],wall_seconds=time.time()-START,assessment_effects_interpreted=False,automatic_retry=False))
except BaseException as error:
    stop();write(OUT/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),partial_preserved=True,automatic_retry=False));raise
finally:stop()
