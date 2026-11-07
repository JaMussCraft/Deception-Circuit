#!/usr/bin/env python3
"""Bridges host allocation adapter; immutable proof worker executes inside SIF."""
import argparse,datetime,hashlib,json,os,re,signal,socket,subprocess,time,traceback
from guards import cgroup_bind,fresh_output
from cgroup_probe import collect
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
def container_command(packet,output,manifest,deadline,cgroup_record):
 virtual_packet=VIRT/packet.relative_to(PHYS);virtual_out=VIRT/output.relative_to(PHYS)
 env={k:v for k,v in os.environ.items() if k.startswith('SLURM_')};env.update(PYTHONPATH=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',HF_HUB_CACHE='/work/nvme/beto/swong2',TRANSFORMERS_CACHE='/work/nvme/beto/swong2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',DC_CLUSTER='bridges2',DC_B2_ALLOC='cis260361p',DC_RUN_MANIFEST_GIT='0')
 cmd=['apptainer','exec','--cleanenv','--contain','--no-home','--writable-tmpfs','--pwd',str(R),'--bind',str(PHYS)+':'+str(VIRT)+':ro','--bind','/ocean:/ocean:ro','--bind',HUB+':/work/nvme/beto/swong2:ro','--bind',str(output)+':'+str(virtual_out)+':rw','--bind',cgroup_bind(cgroup_record['controller'])]
 for k,v in sorted(env.items()):cmd.extend(['--env',k+'='+v])
 return cmd+[IMAGE,'bash',str(virtual_packet/'inner.sh'),'--output',str(virtual_out),'--manifest-sha256',manifest,'--deadline-monotonic',str(deadline)]
PREFLIGHT_MANIFEST='4a096d2c1eb020da99853959a3c26e4948a9c240618958accea0b80e553997d5'
def read(p):return json.loads(Path(p).read_text())
def normal_child(code,term,finished,deadline,report):
 if not(code==0 and term is None and finished<deadline and report.get('status')=='CHILD_NORMAL_POSTGUARDS_AWAIT_SUPERVISOR' and report.get('complete') is False and all(report.get(k) is v for k,v in LABELS.items())):raise ValueError('partial/terminated/late/non-schema child cannot complete')
def observe_cgroup():
 errors={}
 try:proc=Path('/proc/self/cgroup').read_text()
 except OSError as e:proc='';errors['membership']=str(e)
 try:mount=Path('/proc/self/mountinfo').read_text()
 except OSError as e:mount='';errors['mountinfo']=str(e)
 value=collect(os.environ.get('SLURM_JOB_ID',''),proc,mountinfo=mount);value['read_errors']=errors
 for r in value['records']:
  try:
   st=Path(r['path']).stat();r['live_directory_stat']=[st.st_dev,st.st_ino,st.st_mode]
  except (KeyError,OSError) as e:r['stat_error']=str(e)
 return value

def select_cgroup(value,job):
 assert value['job']==job and value.get('required_194_counter_visible') is True
 valid=[]
 for r in value['records']:
  required=('memory.peak','memory.events') if r['controller']=='v2' else ('memory.max_usage_in_bytes','memory.failcnt','memory.oom_control')
  if r.get('job_scoped') and r.get('same_as_frozen_worker_path') and all(k in r['values'] for k in required) and 'live_directory_stat' in r:valid.append(r)
 assert len(valid)==1,'actual readable exact-job memory controller ambiguous/missing'
 return valid[0]

def load_bindings(path,digest):
 assert sha(path)==digest,'root binding bytes changed';b=read(path)
 assert b.get('status')=='ROOT_BOUND_FOR_ONE_CPU_PROOF' and b['actual_job_id']==os.environ['SLURM_JOB_ID']
 assert b['diagnostic_packet_manifest_sha256']==PREFLIGHT_MANIFEST and b['independent_review_accepted'] is True and b['transfer_closure_verified'] is True
 assert b['catalogues_are_snapshots_not_continuous_Delta'] is True
 for key in ('probe_result','probe_host','probe_container','probe_command','independent_review','transfer_attestation'):
  ref=b[key];assert ref['path'] and ref['sha256'] and sha(ref['path'])==ref['sha256'],key
 result=read(b['probe_result']['path']);host=read(b['probe_host']['path']);inner=read(b['probe_container']['path'])
 assert result.get('complete') is True and result.get('host_exit')==0 and result.get('container_exit')==0 and result.get('no_graph') is True and result.get('no_model') is True and result.get('proof_admitted') is False
 command=read(b['probe_command']['path']);assert any(str(v).endswith('/preflight-r3/inner.sh') for v in command['argv']),'probe command is not reviewed r3'
 review=read(b['independent_review']['path']);assert review.get('packet_manifest_sha256')==b['adapter_manifest_sha256'] and str(review.get('verdict','')).startswith(('ACCEPT','READY','CORRECTED')),'independent adapter review is not accepted for this packet'
 assert host.get('required_194_counter_visible') is True and inner.get('required_194_counter_visible') is True and host['job']==inner['job']
 transfer=read(b['transfer_attestation']['path']);assert transfer.get('adapter_manifest_sha256')==b['adapter_manifest_sha256'];assert transfer.get('complete') is True and transfer.get('source_files')==511 and transfer.get('ordinary_inputs')==422 and transfer.get('literal_source_links')==4
 assert b['output_physical'] and b['adapter_manifest_sha256']
 return b

def owned_output(value,b,uid):
 assert value==b['output_physical'];out=Path(value);allowed=PHYS/REL/'.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/root-genuine-proof-r2'
 out.parent.relative_to(allowed);return fresh_output(value,out.parent,uid)

def source_before_activation():
 runtime=PHYS/R.relative_to(VIRT);snapshot=runtime.parent/'snapshot.json'
 assert sha(snapshot)=='68cc15073e383d0943620cab4271a9ee859ae51203e69704b83cca8ac7770f77'
 s=read(snapshot);assert s['source_commit']=='50e947bb852613e3a270082651f2bd1b7bb0c525'
 files=set(str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file() and not p.is_symlink());links=set(str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_symlink())
 assert len(files)==511 and len(links)==4 and files==set(s['source_sha256']) and links==set(s['input_links'])
 for name,digest in s['source_sha256'].items():assert sha(runtime/name)==digest,name
 for name,target in s['input_links'].items():assert os.readlink(str(runtime/name))==target,name
 return dict(source_commit=s['source_commit'],source_files=511,literal_source_links=4,snapshot_sha256=sha(snapshot))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--bindings',required=True);ap.add_argument('--bindings-sha256',required=True);a=ap.parse_args();packet=Path(__file__).resolve().parent
 check_packet(packet,a.manifest_sha256);binding=load_bindings(a.bindings,a.bindings_sha256);assert binding.get('adapter_manifest_sha256',a.manifest_sha256)==a.manifest_sha256
 out=owned_output(a.output,binding,os.getuid());out.mkdir(parents=True,exist_ok=False);child=None;stage='bootstrap'
 def terminate():
  if child is not None and child.poll() is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
 def interrupted(signum,frame):raise TimeoutError('supervisor signal '+str(signum))
 for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,interrupted)
 try:
  first=allocation();assert first['job']==binding['actual_job_id'] and first['end_epoch']-time.time()>=2520;write(out/'allocation-before.json',first);assert sha(IMAGE)==IMAGE_SHA
  write(out/'source-before-activation.json',source_before_activation());stage='real-host-cgroup';observed=observe_cgroup();write(out/'host-cgroup-before.json',observed);selected=select_cgroup(observed,first['job'])
  deadline=min(time.monotonic()+2400,time.monotonic()+first['end_epoch']-time.time()-120);cmd=container_command(packet,out,a.manifest_sha256,deadline,selected);write(out/'command.json',{'argv':cmd,'actual_readonly_cgroup_bind':cgroup_bind(selected['controller'])});started=time.time();term=None;stage='immutable-worker'
  with (out/'child.log').open('x') as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   while child.poll() is None:
    current=allocation();deadline=min(deadline,time.monotonic()+current['end_epoch']-time.time()-120)
    if time.monotonic()>=deadline:term=time.time();terminate();break
    time.sleep(2)
  finished=time.monotonic();after=allocation();deadline=min(deadline,time.monotonic()+after['end_epoch']-time.time()-120);write(out/'allocation-after.json',after);report=read(out/'CHILD-REPORT.json') if (out/'CHILD-REPORT.json').is_file() else {}
  execution=dict(command=cmd,exit_code=child.returncode,term_sent_at=term,started_unix=started,finished_unix=time.time(),deadline_monotonic=deadline,timely=finished<deadline,actual_CPU_job_id=first['job'],actual_cluster='bridges2',**LABELS);write(out/'child-execution.json',execution)
  normal_child(child.returncode,term,finished,deadline,report);assert after['end_epoch']-time.time()>=90;stage='final-guards';check_packet(packet,a.manifest_sha256);assert sha(a.bindings)==a.bindings_sha256
  entry=read(out/'container-cgroup-entry.json');assert entry.get('worker_entry_permitted') is True and entry['job']==first['job'] and entry['packet_manifest_sha256']==a.manifest_sha256
  last=allocation();assert min(first['end_epoch'],last['end_epoch'])-time.time()>=30 and time.time()-started<=2670;assert sha(IMAGE)==IMAGE_SHA;write(out/'allocation-final.json',last)
  write(out/'source-after.json',source_before_activation());final_cgroup=observe_cgroup();write(out/'host-cgroup-after.json',final_cgroup);select_cgroup(final_cgroup,first['job']);last=allocation();assert min(first['end_epoch'],last['end_epoch'])-time.time()>=30,'late final CPU publication'
  result=dict(report,complete=True,status='COMPLETE_CPU_SCHEMA_RESOURCE_PROOF_ONLY',actual_CPU_job_id=first['job'],actual_cluster='bridges2',actual_host=first['host'],actual_allocation=first['fields'],physical_WorkDir=first['fields']['WorkDir'],virtual_runtime_cwd=str(R),child_report_sha256=sha(out/'CHILD-REPORT.json'),child_execution_sha256=sha(out/'child-execution.json'),packet_sha256=a.manifest_sha256,root_bindings_sha256=a.bindings_sha256,catalogues_are_snapshots_not_continuous_Delta=True,GPU_ADMITTED=False);write(out/'COMPLETE-PROOF.json',result)
 except BaseException as e:
  terminate();write(out/'FAILED-supervisor.json',dict(complete=False,stage=stage,error=repr(e),traceback=traceback.format_exc(),**LABELS));raise
 finally:terminate()
if __name__=='__main__':main()
