"""One 75-minute actual Delta CPU allocation; one guard child per model phase."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,signal,socket,subprocess,time,traceback
SOURCE='50e947bb852613e3a270082651f2bd1b7bb0c525'
P=Path(__file__).resolve().parent
EVIDENCE=None
PHASE=None
def interrupted(signum,frame):raise TimeoutError('CPU supervisor termination signal '+str(signum))
for signum in (signal.SIGTERM,signal.SIGINT):signal.signal(signum,interrupted)
def terminate(child):
 if child.poll() is None:
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=15)

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for part in iter(lambda:f.read(1048576),b''):h.update(part)
 return h.hexdigest()
def write(path,value):
 with Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def allocation():
 job=os.environ['SLURM_JOB_ID'];assert re.fullmatch('[0-9]+',job) and os.environ['SLURM_CLUSTER_NAME']=='delta'
 raw=subprocess.check_output(['scontrol','show','job',job,'-o'],text=True,timeout=15,env=dict(os.environ,TZ='UTC'));f=dict(x.split('=',1) for x in raw.split() if '=' in x)
 assert f['JobId']==job and f['JobState']=='RUNNING' and f['Account'].endswith('-cpu') and f['Partition']=='cpu'
 assert f['Requeue']=='0' and f['Restarts']=='0' and f['NumNodes']=='1' and f['NumCPUs']=='4'
 assert f['TimeLimit'] in ('01:15:00','1:15:00')
 hosts=subprocess.check_output(['scontrol','show','hostnames',f['NodeList']],text=True,timeout=15).split();assert socket.gethostname().split('.')[0] in [h.split('.')[0] for h in hosts]
 tres=dict(x.split('=',1) for x in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in x);assert tres.get('mem') in ('16G','16384M') and not any(k.startswith('gres/gpu') for k in tres)
 end=datetime.datetime.fromisoformat(f['EndTime']).replace(tzinfo=datetime.timezone.utc).timestamp()
 return dict(job_id=job,host=socket.gethostname(),scontrol_job=raw,fields=f,tres=tres,end_epoch=end,captured_unix=time.time())
def main():
 global EVIDENCE,PHASE
 ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--config-sha256',required=True);a=ap.parse_args();assert sha(a.config)==a.config_sha256;c=json.loads(Path(a.config).read_text())
 assert c['source_commit']==SOURCE and c['total_seconds']==4500 and c['finish_reserve_seconds']==60 and c['child_cap_seconds']==720 and c['publication_margin_seconds']==30 and c['kill_grace_seconds']==15
 assert sha(P/'implementation-manifest.json')==c['packet_manifest_sha256']
 for name,digest in json.loads((P/'implementation-manifest.json').read_text()).items():assert sha(P/name)==digest,name
 assert sha(c['base_parameters'])==c['base_parameters_sha256'];assert c['frozen_G3_sha256'] and c['H100_packet_manifest_sha256']
 facts=allocation();initial_end=facts['end_epoch'];absolute_end=min(time.time()+4500,initial_end);assert facts['job_id']==c['standing_CPU_job_id']
 evidence=Path(c['evidence_output']);evidence.mkdir(parents=True,exist_ok=False);EVIDENCE=evidence;write(evidence/'READY.json',dict(CPU_job_id=facts['job_id'],source_commit=SOURCE,allocation=facts,config_sha256=a.config_sha256,packet_manifest_sha256=c['packet_manifest_sha256'],initial_end=initial_end,model_admitted=False));sticky_gpu=None;sticky_config=None
 for phase in ('bank','prefix4'):
  PHASE=phase
  request_path=Path(c['request_directory'])/(phase+'.json')
  while not request_path.exists():
   current=allocation();deadline=min(absolute_end,current['end_epoch'])-60
   if time.time()>=deadline:raise TimeoutError('standing CPU request window expired')
   time.sleep(5)
  raw=request_path.read_bytes();request=json.loads(raw);now=time.time();assert request['phase']==phase and request['standing_CPU_job_id']==facts['job_id'] and request['standing_packet_manifest_sha256']==c['packet_manifest_sha256']
  assert request['accepted_source_commit']==SOURCE and request['frozen_G3_sha256']==c['frozen_G3_sha256'] and isinstance(request['final_GPU_bound_config_sha256'],str) and re.fullmatch('[0-9a-f]{64}',request['final_GPU_bound_config_sha256']) and request['H100_packet_manifest_sha256']==c['H100_packet_manifest_sha256']
  assert 0<=now-request['root_trigger_issued_at']<=15
  gpu=request['actual_future_GPU_job_id'];assert isinstance(gpu,str) and re.fullmatch('[0-9]+',gpu)
  if sticky_gpu is None:sticky_gpu=gpu;sticky_config=request['final_GPU_bound_config_sha256']
  assert gpu==sticky_gpu and request['final_GPU_bound_config_sha256']==sticky_config
  marker=Path(request['GPU_WAITING_marker_path']);marker_raw=marker.read_bytes();assert hashlib.sha256(marker_raw).hexdigest()==request['GPU_WAITING_marker_sha256'];waiting=json.loads(marker_raw)
  assert waiting['phase']==phase and waiting['job_id']==gpu and waiting['source_commit']==SOURCE and waiting['bound_config_sha256']==sticky_config
  assert waiting['requested_at']==request['GPU_WAITING_requested_at'] and 0<=now-waiting['requested_at']<270 and waiting['requested_at']<=request['root_trigger_issued_at']
  current=allocation();deadline=min(now+720,absolute_end-60,current['end_epoch']-60,waiting['requested_at']+270);assert deadline>time.time()
  out=evidence/phase;out.mkdir();write(out/'immutable-identities.json',dict(actual_CPU_job_id=facts['job_id'],actual_GPU_job_id=sticky_gpu,final_GPU_bound_config_sha256=sticky_config,source_commit=SOURCE,frozen_G3_sha256=c['frozen_G3_sha256'],H100_packet_manifest_sha256=c['H100_packet_manifest_sha256']));write(out/'request.json',request);write(out/'allocation-before.json',current)
  base=json.loads(Path(c['base_parameters']).read_text());base.update(phase=phase,new_g3_output=c['frozen_G3_root'],frozen_G3_sha256=c['frozen_G3_sha256'],evidence_output=str(out),actual_future_GPU_job_id=gpu,phase_request_sha256=hashlib.sha256(raw).hexdigest(),phase_deadline_unix=deadline,current_cpu_allocation=dict(path=str(out/'allocation-before.json'),sha256=sha(out/'allocation-before.json')))
  parameters=out/'parameters.json';write(parameters,base)
  env=dict(os.environ,DC_CLUSTER='delta',DC_PYTHON=c['python'],DC_RUN_MANIFEST_GIT='0',PYTHONPATH=c['runtime'],PYTHONDONTWRITEBYTECODE='1',HF_HUB_CACHE='/work/nvme/beto/swong2',TRANSFORMERS_CACHE='/work/nvme/beto/swong2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
  cmd=[c['python'],str(P/'validate-phase.py'),'--parameters',str(parameters),'--parameters-sha256',sha(parameters)];began=time.time();term=None
  with (out/'child.log').open('x') as log:
   child=subprocess.Popen(cmd,cwd=c['runtime'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   try:
    while child.poll() is None:
     latest=allocation();deadline=min(deadline,latest['end_epoch']-60);assert request_path.read_bytes()==raw and marker.read_bytes()==marker_raw,'request or WAITING marker changed'
     if time.time()>=deadline:
      term=time.time();terminate(child)
      break
     time.sleep(1)
   finally:
    terminate(child)
  assert request_path.read_bytes()==raw and marker.read_bytes()==marker_raw,'request or WAITING marker changed after child'
  after=allocation();write(out/'allocation-after.json',after);timely=time.time()<=min(deadline,after['end_epoch']-60)
  write(out/'child-execution.json',dict(command=cmd,exit_code=child.returncode,started_unix=began,finished_unix=time.time(),deadline_unix=deadline,term_sent_at=term,timely=timely,actual_CPU_job_id=facts['job_id'],actual_future_GPU_job_id=gpu,phase=phase))
  if child.returncode!=0 or term is not None or not timely:
   write(out/'FAILED.json',dict(phase=phase,complete=False,window_missed=not timely,exit_code=child.returncode,automatic_retry=False));raise RuntimeError('phase owning guard failed or window missed; no retry')
  result=json.loads((out/'guard-result.json').read_text());assert result['status']=='GUARDS_PASSED_AWAIT_SUPERVISOR' and result['complete'] is False and result['source_commit']==SOURCE and result['actual_future_GPU_job_id']==gpu and result['groups_file_sha256']==c['frozen_G3_sha256']
  result.update(kind='Delta_actual_model_phase_preflight',status='PASS',complete=True,request_sha256=hashlib.sha256(raw).hexdigest(),standing_packet_manifest_sha256=c['packet_manifest_sha256'],final_GPU_bound_config_sha256=sticky_config,H100_packet_manifest_sha256=c['H100_packet_manifest_sha256'],guard_result_sha256=sha(out/'guard-result.json'),timely_window=True,supervisor_finished_unix=time.time(),deadline_unix=deadline)
  assert time.time()<=deadline
  write(out/'COMPLETE.json',result)
 write(evidence/'COMPLETE.json',dict(complete=True,phases=['bank','prefix4'],actual_CPU_job_id=facts['job_id'],actual_future_GPU_job_id=sticky_gpu,source_commit=SOURCE,GPU_admitted=False))
if __name__=='__main__':
 try:main()
 except BaseException as error:
  if EVIDENCE is not None:
   failure=EVIDENCE/('FAILED-'+str(PHASE)+'.json')
   if not failure.exists():write(failure,dict(complete=False,phase=PHASE,error=repr(error),traceback=traceback.format_exc(),finished_unix=time.time(),automatic_retry=False,window_missed=isinstance(error,TimeoutError)))
  raise
