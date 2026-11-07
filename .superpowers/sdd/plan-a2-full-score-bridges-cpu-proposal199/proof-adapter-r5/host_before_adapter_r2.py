#!/usr/bin/env python3
"""Bridges host allocation adapter; immutable proof worker executes inside SIF."""
import argparse,datetime,hashlib,json,os,re,signal,socket,subprocess,time
from pathlib import Path
PHYS=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment')
VIRT=Path('/projects/beto/swong2/Alignment')
REL=Path('Deception-Circuit/.claude/worktrees/specificity-ladder')
R=VIRT/REL/'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime'
IMAGE='/ocean/projects/cis260361p/swong2/specificity-ladder-20261102/containers/ubuntu2204.sif'
IMAGE_SHA='f50c8e39dd5e2ac1c1a4bdfd443351cb970513fdb10a572725eb53d7396f8697'
PY='/ocean/projects/cis260361p/swong2/envs/mgnp/bin/python'
HUB='/ocean/projects/cis260361p/swong2/hf/hub'
LABELS=dict(MODEL_LOADED=False,EFFECTS_READ=False,SYNTHETIC_SCHEMA_ONLY=True,NUMERICAL_CONTROLS_TESTED=False,GPU_ADMITTED=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def validate_allocation(f,e,uid,host,workdir,expected_minutes=45):
 t=dict(x.split('=',1) for x in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in x)
 assert re.fullmatch('[0-9]+',e['SLURM_JOB_ID']) and f['JobId']==e['SLURM_JOB_ID'] and f['JobState']=='RUNNING' and re.search(r'\('+str(uid)+r'\)',f['UserId'])
 assert f['Account']=='cis260361p' and f['QOS']=='rm' and f['Partition']=='RM-shared' and f['NumNodes']=='1' and f['NumCPUs']=='26' and f['CPUs/Task']=='26' and t['cpu']=='26'
 assert f['Requeue']=='0' and f['Restarts']=='0' and f['TimeLimit'] in ('00:%02d:00'%expected_minutes,'%02d:00'%expected_minutes) and t['mem'] in ('48G','49152M')
 assert not any(k.startswith('gres/gpu') and float(v)>0 for k,v in t.items()) and f['WorkDir']==workdir and f['BatchHost'].split('.')[0]==host.split('.')[0]
 assert e.get('SLURM_CLUSTER_NAME')=='bridges2' and e.get('SLURM_CPUS_PER_TASK')=='26' and e.get('CUDA_VISIBLE_DEVICES','')==''
 assert all(not e.get(k) for k in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS')) and all(e.get(k,'') in ('','0') for k in ('SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK'))
 return t
def allocation():
 raw=subprocess.check_output(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o'],universal_newlines=True,timeout=15,env=dict(os.environ,TZ='UTC'));f=dict(x.split('=',1) for x in raw.split() if '=' in x);work=str(PHYS/REL/'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime');t=validate_allocation(f,os.environ,os.getuid(),socket.gethostname(),work)
 end=datetime.datetime.strptime(f['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp();return dict(job=os.environ['SLURM_JOB_ID'],host=socket.gethostname(),raw=raw,fields=f,tres=t,end_epoch=end,captured_unix=time.time())
def write(p,obj):
 with Path(p).open('x') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')
def check_packet(p,digest):
 assert sha(p/'manifest.json')==digest
 for n,h in json.loads((p/'manifest.json').read_text()).items():assert not Path(n).is_absolute() and '..' not in Path(n).parts and sha(p/n)==h,n
def container_command(packet,output,manifest,deadline):
 virtual_packet=VIRT/packet.relative_to(PHYS);virtual_out=VIRT/output.relative_to(PHYS)
 env={k:v for k,v in os.environ.items() if k.startswith('SLURM_')};env.update(PYTHONPATH=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',HF_HUB_CACHE='/work/nvme/beto/swong2',TRANSFORMERS_CACHE='/work/nvme/beto/swong2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',DC_CLUSTER='bridges2',DC_B2_ALLOC='cis260361p')
 cmd=['apptainer','exec','--cleanenv','--contain','--no-home','--writable-tmpfs','--pwd',str(R),'--bind',str(PHYS)+':'+str(VIRT)+':ro','--bind','/ocean:/ocean:ro','--bind',HUB+':/work/nvme/beto/swong2:ro','--bind',str(output)+':'+str(virtual_out)+':rw']
 for k,v in sorted(env.items()):cmd.extend(['--env',k+'='+v])
 return cmd+[IMAGE,'bash',str(virtual_packet/'inner.sh'),'--output',str(virtual_out),'--manifest-sha256',manifest,'--deadline-monotonic',str(deadline)]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--manifest-sha256',required=True);a=ap.parse_args();packet=Path(__file__).resolve().parent;check_packet(packet,a.manifest_sha256)
 out=Path(a.output);assert out.is_absolute() and not out.exists();out.relative_to(PHYS/REL);out.mkdir(parents=True,exist_ok=False)
 first=allocation();assert first['end_epoch']-time.time()>=2520;write(out/'allocation-before.json',first);assert sha(IMAGE)==IMAGE_SHA
 deadline=min(time.monotonic()+2400,time.monotonic()+first['end_epoch']-time.time()-120);cmd=container_command(packet,out,a.manifest_sha256,deadline);write(out/'command.json',{'argv':cmd});started=time.time();term=None;child=None
 def terminate():
  if child is not None and child.poll() is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
 def interrupted(signum,frame):raise TimeoutError('supervisor signal '+str(signum))
 for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,interrupted)
 try:
  with (out/'child.log').open('x') as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   while child.poll() is None:
    current=allocation();deadline=min(deadline,time.monotonic()+current['end_epoch']-time.time()-120)
    if time.monotonic()>=deadline:term=time.time();terminate();break
    time.sleep(2)
  finished=time.monotonic();after=allocation();write(out/'allocation-after.json',after);report=json.loads((out/'CHILD-REPORT.json').read_text()) if (out/'CHILD-REPORT.json').is_file() else {}
  execution=dict(command=cmd,exit_code=child.returncode,term_sent_at=term,started_unix=started,finished_unix=time.time(),deadline_monotonic=deadline,timely=finished<=deadline,actual_CPU_job_id=first['job'],**LABELS);write(out/'child-execution.json',execution)
  assert child.returncode==0 and term is None and finished<=deadline and report.get('status')=='CHILD_NORMAL_POSTGUARDS_AWAIT_SUPERVISOR' and report.get('complete') is False and all(report.get(k) is v for k,v in LABELS.items())
  assert after['end_epoch']-time.time()>=90;check_packet(packet,a.manifest_sha256);last=allocation();assert min(first['end_epoch'],last['end_epoch'])-time.time()>=30 and time.time()-started<=2670;assert sha(IMAGE)==IMAGE_SHA;write(out/'allocation-final.json',last)
  result=dict(report,complete=True,status='COMPLETE_CPU_SCHEMA_RESOURCE_PROOF_ONLY',actual_CPU_job_id=first['job'],child_report_sha256=sha(out/'CHILD-REPORT.json'),child_execution_sha256=sha(out/'child-execution.json'),packet_sha256=a.manifest_sha256,GPU_ADMITTED=False);write(out/'COMPLETE-PROOF.json',result)
 except BaseException as e:
  terminate();write(out/'FAILED-supervisor.json',dict(complete=False,error=repr(e),**LABELS));raise
 finally:terminate()
if __name__=='__main__':main()
