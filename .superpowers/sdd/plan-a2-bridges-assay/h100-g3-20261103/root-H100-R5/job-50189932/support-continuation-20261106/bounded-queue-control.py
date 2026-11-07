from pathlib import Path
import os,sys,json,hashlib,subprocess,time,datetime,signal,importlib.util
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103');Q=D/'root-H100-R5/job-50189932';O=Q/'support-continuation-20261106';R=D/'root-model-phase-release-helper/r5-r2';C=D/'root-Delta-model-preflight/job-23606524'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(R/'manifest.json')=='74f29f489229fe533ed6a7c6d07b13a24e3a2fb8c2c4555edda8b65b48b7f1e4'
assert sha(Q/'root-watch-phases-continuation-20261106.py')=='37934105f0ea56ba961eca8b2eb6b9de27f809c68be4c5b9feee6733a211e4c6'
assert sha(O/'actual-READY-continuation.json')=='71526670a4415f59a9e128c9f60a7a5173d8e541ab25237e58599b3987d4b463'
verdict=Path('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/160-host-split-operational-review-evidence/CPU-23606524-bounded-queue-control-ruling.json')
assert sha(verdict)=='cee85e88c69ddb8030b49d3c214ff3eb707595dd111b34185df8dc5c15a214d6'
sys.path.insert(0,str(R));spec=importlib.util.spec_from_file_location('release_helper',R/'helper.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
b,g,c=m.load_bindings(str(Q/'helper-bindings-continuation-20261106.json'),'c3eec41b5ca2331ebdb6fa387fa45159894fc8559d09df5e00202030387f09bd');m.verify_runtime_pins(b,g,c)
log=(O/'bounded-queue-events.jsonl').open('x',buffering=1)
def event(kind,**data):log.write(json.dumps(dict(kind=kind,utc_epoch=time.time(),monotonic=time.monotonic(),**data))+'\n')
def command(args,timeout=10):
 started=time.time()
 try:
  p=subprocess.run(args,text=True,capture_output=True,timeout=timeout,env=dict(os.environ,TZ='UTC'));event('command',argv=args,started=started,exit=p.returncode,stdout=p.stdout,stderr=p.stderr);p.check_returncode();return p.stdout
 except Exception as exc:event('command_error',argv=args,started=started,error=repr(exc));raise
fields=lambda raw:dict(x.split('=',1) for x in raw.split() if '=' in x)
def epoch(value):return datetime.datetime.strptime(value,'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp()
ready=json.loads((C/'evidence/READY.json').read_text());cpu=fields(command(['scontrol','-o','show','job','23606524']))
assert cpu['JobState']=='RUNNING' and cpu['NumCPUs']=='4' and cpu['Account'].endswith('-cpu') and ready['CPU_job_id']=='23606524' and ready['config_sha256']==sha(C/'config.json')
cutoff=min(ready['initial_end'],epoch(cpu['EndTime']))-60-1650-300
assert time.time()+180<cutoff
u=json.loads(command(['/u/swong2/.local/bin/codex-usage','--pause-at','80'],25));status=command(['research-session','status','--session',b['session']],25);projection=m.validate_usage(u,status,b['session']);event('fresh_usage',projection=projection)
ssh=b['ssh_argv']
def gpu():
 raw=command(ssh+['env','TZ=UTC','scontrol','-o','show','job','50189932']);f=fields(raw)
 assert f['JobId']=='50189932' and f['Account']=='cis260382p' and f['QOS']=='gpu' and f['Partition']=='GPU-shared' and f['Requeue']=='0' and f['Restarts']=='0' and f['NumCPUs']=='4' and f['TimeLimit'] in ('01:00:00','1:00:00')
 return raw,f
def accepted_running(raw,f):
 m.gpu_facts(raw,g);start=epoch(f['StartTime']);assert start<=cutoff and start<=time.time();return start
raw,f=gpu();assert f['JobState']=='PENDING' and f['Reason']=='JobHeldUser';assert not Path(b['state_directory']).exists()
assert time.time()+180<cutoff
watch_path=Q/'root-watch-phases-continuation-20261106.py';watch_log=(O/'phase-watcher.log').open('x')
watch=subprocess.Popen(['/u/swong2/.conda/envs/mgnp/bin/python','-u',str(watch_path)],stdout=watch_log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
(O/'phase-watcher-process.json').write_text(json.dumps({'pid':watch.pid,'watcher':str(watch_path),'watcher_sha256':sha(watch_path),'started_unix':time.time()},indent=2)+'\n')
event('explicit_conditional_execution_authorized',cutoff_UTC_epoch=cutoff,watcher_pid=watch.pid,maximum_queue_observation_seconds=120,reviewed_ruling_sha256=sha(verdict))
start_mono=time.monotonic();started_utc=time.time();disposition=None;reason=None
try:
 assert time.time()+180<cutoff
 command(ssh+['scontrol','release','50189932'])
 while time.monotonic()-start_mono<120 and time.time()<started_utc+120 and time.time()<cutoff:
  if watch.poll() is not None:raise RuntimeError('phase watcher exited before actual allocation')
  raw,f=gpu()
  if f['JobState']=='RUNNING':
   actual=accepted_running(raw,f);disposition='RUNNING_WITHIN_REVIEWED_START_WINDOW';event('running',actual_start_UTC_epoch=actual);break
  if f['JobState']!='PENDING':raise RuntimeError('unexpected GPU state '+f['JobState'])
  v=f.get('StartTime','Unknown')
  if v not in ('Unknown','N/A','(null)'):
   forecast=epoch(v)
   if forecast<time.time()-5:raise RuntimeError('inconsistent pending forecast in past')
   if forecast>cutoff:reason='actual pending forecast beyond safe support cutoff';break
  time.sleep(min(5,max(0,120-(time.monotonic()-start_mono))))
 if disposition is None:reason=reason or 'bounded placement observation expired without timely running allocation'
except Exception as exc:reason=repr(exc);event('observation_exception',error=reason)
finally:
 if disposition is None:
  try:
   raw,f=gpu()
   if f['JobState']=='RUNNING':accepted_running(raw,f);disposition='RUNNING_DURING_REHOLD_RACE_WITHIN_WINDOW'
   elif f['JobState']=='PENDING':
    try:command(ssh+['scontrol','hold','50189932'])
    except Exception:pass
    raw,f=gpu()
    if f['JobState']=='RUNNING':accepted_running(raw,f);disposition='RUNNING_DURING_REHOLD_RACE_WITHIN_WINDOW'
    else:assert f['JobState']=='PENDING' and f['Reason']=='JobHeldUser';disposition='CONFIRMED_UNSTARTED_REHOLD'
   else:disposition='TERMINAL_OR_UNEXPECTED_GPU_STATE_'+f['JobState']
  except Exception as exc:disposition='UNCERTAIN_STOP_PUBLICATION';event('rehold_uncertain',error=repr(exc))
 if not disposition.startswith('RUNNING_'):
  if watch.poll() is None:
   cmdline=Path('/proc/%d/cmdline'%watch.pid).read_bytes();assert str(watch_path).encode() in cmdline
   os.killpg(watch.pid,signal.SIGTERM)
   try:watch.wait(timeout=8)
   except subprocess.TimeoutExpired:os.killpg(watch.pid,signal.SIGKILL);watch.wait(timeout=5)
  event('watcher_stopped',returncode=watch.poll())
  if disposition=='CONFIRMED_UNSTARTED_REHOLD':
   assert not Path(b['state_directory']).exists(),'Unexpected helper invocation; inspect evidence'
   assert not list(Path(c['request_directory']).iterdir()),'Unexpected CPU phase request'
 result={'disposition':disposition,'reason':reason,'cutoff_UTC_epoch':cutoff,'finished_unix':time.time(),'watcher_pid':watch.pid,'watcher_running':watch.poll() is None,'same_GPU_job':'50189932','same_reservation':'r-041','no_retry_or_extension':True}
 (O/'bounded-queue-result.json').write_text(json.dumps(result,indent=2)+'\n');event('result',**result);print(json.dumps(result),flush=True)
