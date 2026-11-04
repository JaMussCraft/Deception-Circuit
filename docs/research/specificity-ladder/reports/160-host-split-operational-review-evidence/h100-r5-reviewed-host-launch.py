"""Bridges host stdlib launch; no source or historical artifact edits."""
from pathlib import Path
import os,sys,json,hashlib,subprocess,datetime,time,socket,signal
config=Path(os.environ['A2_H100_BOUND_CONFIG']);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(config)==os.environ['A2_H100_BOUND_CONFIG_SHA256'];c=json.loads(config.read_text());assert c['independent160_accepted'] is True and c['actual_job_id']==os.environ['SLURM_JOB_ID']
assert sha(c['image'])==c['image_sha256']
virtual=Path(c['virtual_Alignment_root']);physical=Path(c['physical_Alignment_root'])
capture=physical/Path(c['allocation_capture']).relative_to(virtual);assert not capture.exists()
def actual_capture():
 raw=subprocess.check_output(['scontrol','show','job',c['actual_job_id'],'-o'],universal_newlines=True,timeout=15,env=dict(os.environ,TZ='UTC'));facts=dict(x.split('=',1) for x in raw.split() if '=' in x)
 assert facts['JobState']=='RUNNING' and facts['JobId']==c['actual_job_id'] and facts['Account']==c['expected_account'] and facts['Partition'] in c['allowed_partitions'] and facts['QOS']==c['expected_qos']
 assert facts['Requeue']=='0' and facts['Restarts']=='0' and facts['TimeLimit'] in ('01:00:00','1:00:00','60:00')
 hosts=subprocess.check_output(['scontrol','show','hostnames',facts['NodeList']],universal_newlines=True,timeout=15).split();assert socket.gethostname().split('.')[0] in [x.split('.')[0] for x in hosts]
 end=datetime.datetime.strptime(facts['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp()
 data=dict(actual_job_id=c['actual_job_id'],host=socket.gethostname(),actual_hostnames=hosts,raw_scontrol=raw,fields=facts,captured_unix=time.time(),end_epoch=end)
 temporary=capture.with_name(capture.name+'.pending-'+str(os.getpid()));temporary.write_text(json.dumps(data,indent=2)+'\n');os.replace(str(temporary),str(capture));return end
end=actual_capture();assert end>time.time();initial_end=end
virtual=Path(c['virtual_Alignment_root']);physical=Path(c['physical_Alignment_root']);packet=Path(__file__).resolve().parent
# Root binds the bound-config virtual path; never synthesize a Slurm identity.
profile={k:v for k,v in os.environ.items() if k.startswith('SLURM_') or k in ('CUDA_VISIBLE_DEVICES',)}
profile.update(A2_H100_BOUND_CONFIG=str(virtual/config.relative_to(physical)),A2_H100_BOUND_CONFIG_SHA256=sha(config),A2_H100_PACKET=str(virtual/packet.relative_to(physical)),A2_H100_RUNTIME=c['runtime'],A2_TIMING_EXECUTION_OUTPUT=os.environ['A2_TIMING_EXECUTION_OUTPUT'],A2_H100_RELEASE_DIRECTORY=os.environ['A2_H100_RELEASE_DIRECTORY'],A2_H100_INITIAL_END_EPOCH=str(end),PYTHONDONTWRITEBYTECODE='1',HF_HUB_CACHE='/work/nvme/beto/swong2',TRANSFORMERS_CACHE='/work/nvme/beto/swong2',DC_B2_ALLOC='cis260361p')
cmd=['apptainer','exec','--cleanenv','--contain','--no-home','--writable-tmpfs','--nv','--pwd',c['runtime'],'--bind',str(physical)+':'+str(virtual)+':rw','--bind','/ocean:/ocean:ro','--bind',c['physical_HF_cache']+':'+c['virtual_HF_cache']+':ro']
for key,value in sorted(profile.items()):cmd+=['--env',key+'='+value]
cmd += [c['image'],'bash',profile['A2_H100_PACKET']+'/inner.sh']
child=subprocess.Popen(cmd,start_new_session=True)
def terminate():
 if child.poll() is None:
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=15)
try:
 while child.poll() is None:
  current_end=actual_capture()
  if time.time()>=min(initial_end,current_end)-c['finish_reserve_seconds']:
   terminate();raise TimeoutError('fixed initial/current host work deadline; no extension')
  time.sleep(5)
 raise SystemExit(child.returncode)
finally:terminate()
