#!/usr/bin/env python3
"""Bounded transport of an unchanged, source-pinned mgnp observer."""
import argparse,datetime,hashlib,json,os,re,signal,socket,subprocess,sys,time
from pathlib import Path
PHYS=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment')
VIRT=Path('/projects/beto/swong2/Alignment')
REL=Path('Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/a3-green-bridges-transport229')
IMAGE='/ocean/projects/cis260361p/swong2/specificity-ladder-20261102/containers/ubuntu2204.sif'
IMAGE_SHA='f50c8e39dd5e2ac1c1a4bdfd443351cb970513fdb10a572725eb53d7396f8697'
ENV_PATH='/ocean/projects/cis260361p/swong2/envs/mgnp'
PY='/u/swong2/.conda/envs/mgnp/bin/python'

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def virtual_to_physical(value):
 p=Path(value);assert p.is_absolute() and '..' not in p.parts and str(p)==value
 return str(PHYS/p.relative_to(VIRT))
def check_records(files,aliases):
 for x in files:
  p=Path(x['physical']);assert p.is_file() and p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
 for x in aliases:
  p=Path(x['physical']);assert p.is_symlink() and os.readlink(str(p))==x['literal_target']
def check_config(c):
 assert c['status']=='ROOT_BOUND_A3_GREEN_MGNP_TRANSPORT' and type(c['expected_cases']) is int and c['expected_cases']>0
 files=c['files'];aliases=c['aliases'];assert type(files) is list and files and type(c['expected_file_count']) is int and len(files)==c['expected_file_count'] and type(aliases) is list and len(aliases)==4
 for rows in (files,aliases):
  assert len({x['virtual'] for x in rows})==len(rows) and len({x['physical'] for x in rows})==len(rows)
  for x in rows:assert x['physical']==virtual_to_physical(x['virtual'])
 assert c['observer_virtual'] in {x['virtual'] for x in files} and c['observer_virtual'].endswith('/run_packet.py')
 assert all(re.fullmatch('[0-9a-f]{64}',x['sha256']) and type(x['bytes']) is int and x['bytes']>=0 for x in files)
 check_records(files,aliases)
def child_deadline(now,end):
 assert end-now>=3430,'insufficient allocation for 610+90+2700 and 30s reserve'
 return min(now+3450,end-30)
def timely(code,terminated,finished,deadline):return code==0 and not terminated and finished<deadline
def normal_manifest(m,job,count):
 try:
  r=m['results']['mgnp']
  return (m['status']=='GREEN_EXPECTED' and m['normal_completion'] is True and m['exit_code']==0 and m['model_loaded'] is False and m['execution_authorized'] is False and m['job_id']==job and m['cluster']=='bridges2' and set(m['results'])=={'mgnp'} and r['python']==PY and r['status']=='GREEN_EXPECTED' and r['normal_completion'] is True and r['pytest_exit_code']==0 and r['observed_cases']==count and r['expected_cases']==count and r['failures']==r['errors']==r['skipped']==0 and r['source_pins_before_after_equal'] is True and r['baseline_red']['exit_code']==0 and r['baseline_red']['manifest']['status']=='CORRECTION_RED_EXPECTED' and r['baseline_red']['manifest']['normal_completion'] is True and r['oracle_preflight']['exit_code']==0 and r['oracle']['complete'] is True)
 except (KeyError,TypeError):return False
def container_command(c,out,kind,env):
 assert kind in ('v1','v2');cg='/sys/fs/cgroup:/sys/fs/cgroup:ro'
 if kind=='v1':cg+=',/sys/fs/cgroup/memory:/sys/fs/cgroup/memory:ro'
 physical_out=virtual_to_physical(str(out));cmd=['apptainer','exec','--cleanenv','--contain','--no-home','--writable-tmpfs','--pwd',str(Path(c['observer_virtual']).parent),'--bind',str(PHYS)+':'+str(VIRT)+':ro','--bind','/ocean:/ocean:ro','--bind','/ocean/projects/cis260361p/swong2/hf/hub:/work/nvme/beto/swong2:ro','--bind',ENV_PATH+':/u/swong2/.conda/envs/mgnp:ro','--bind',str(Path(physical_out).parent)+':'+str(out.parent)+':rw','--bind',cg]
 profile={k:v for k,v in env.items() if k.startswith('SLURM_')};profile.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_CACHE='/work/nvme/beto/swong2',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 for k,v in sorted(profile.items()):cmd.extend(['--env',k+'='+v])
 return cmd+[IMAGE,PY,'-B',c['observer_virtual'],'--mode=GREEN','--environment=mgnp','--output='+str(out)]
def allocation():
 e=os.environ;job=e['SLURM_JOB_ID'];assert re.fullmatch('[0-9]+',job)
 raw=subprocess.check_output(['scontrol','show','job',job,'-o'],universal_newlines=True,timeout=15,env=dict(e,TZ='UTC'));f=dict(x.split('=',1) for x in raw.split() if '=' in x);t=dict(x.split('=',1) for x in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in x)
 assert f['JobId']==job and f['JobState']=='RUNNING' and re.search(r'\('+str(os.getuid())+r'\)',f['UserId'])
 assert f['Account']=='cis260361p' and f['Partition']=='RM-shared' and f['QOS']=='rm' and f['NumNodes']=='1' and f['NumTasks']=='1' and f['NumCPUs']=='18' and f['CPUs/Task']=='18' and t['cpu']=='18' and t['mem'] in ('32G','32768M')
 assert f['TimeLimit'] in ('00:59:00','59:00') and f['Requeue']=='0' and f['Restarts']=='0' and f['BatchHost'].split('.')[0]==socket.gethostname().split('.')[0]
 assert e.get('SLURM_CLUSTER_NAME')=='bridges2' and e.get('SLURM_CPUS_PER_TASK')=='18' and e.get('SLURM_NTASKS')=='1'
 assert not any(k.startswith('gres/gpu') and float(v)>0 for k,v in t.items()) and all(not e.get(k) for k in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS','CUDA_VISIBLE_DEVICES')) and all(e.get(k,'') in ('','0') for k in ('SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK'))
 return f,datetime.datetime.strptime(f['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp()
def actual_controller(job):
 found=[]
 for line in Path('/proc/self/cgroup').read_text().splitlines():
  f=line.split(':',2)
  if len(f)!=3:continue
  kind='v1' if 'memory' in f[1].split(',') else ('v2' if f[0]=='0' else None)
  if not kind:continue
  membership=Path(f[2]);parts=[x for x in membership.parts if re.fullmatch(r'job_?[0-9]+',x)]
  if not parts or not all(x in ('job_'+job,'job'+job) for x in parts):continue
  base=Path('/sys/fs/cgroup')/('memory' if kind=='v1' else '')/str(membership).lstrip('/')
  names=('memory.max_usage_in_bytes','memory.failcnt','memory.oom_control') if kind=='v1' else ('memory.peak','memory.events')
  if all((base/n).is_file() for n in names):found.append(kind)
 assert len(found)==1,'exact own-job memory controller not visible';return found[0]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--config-sha256',required=True);ap.add_argument('--manifest-sha256',required=True);a=ap.parse_args();here=Path(__file__).resolve().parent
 assert re.fullmatch('[0-9a-f]{64}',a.manifest_sha256) and sha(here/'manifest.json')==a.manifest_sha256
 for n,h in json.loads((here/'manifest.json').read_text()).items():assert Path(n).name==n and sha(here/n)==h
 assert re.fullmatch('[0-9a-f]{64}',a.config_sha256) and not Path(a.config).is_symlink() and sha(a.config)==a.config_sha256
 c=json.loads(Path(a.config).read_text());check_config(c);job=os.environ['SLURM_JOB_ID'];f,end=allocation();root=PHYS/REL/'jobs'/('job-'+job)
 assert root.is_dir() and root.stat().st_uid==os.getuid() and not root.is_symlink() and root.resolve()==root and all(not p.is_symlink() for p in root.parents)
 output=root/'execution';assert all(not os.path.lexists(str(root/n)) for n in ('execution','command.json','observer.log','transport-result.json','transport-failure.json'));assert sha(IMAGE)==IMAGE_SHA;kind=actual_controller(job);f,end=allocation();deadline=child_deadline(time.time(),end);out=VIRT/REL/'jobs'/('job-'+job)/'execution';cmd=container_command(c,out,kind,os.environ)
 with (root/'command.json').open('x') as dest:json.dump({'argv':cmd,'allocation':f,'config_sha256':a.config_sha256,'manifest_sha256':a.manifest_sha256},dest,indent=2)
 child=None;terminated=False;mono_deadline=time.monotonic()+min(3450,deadline-time.time())
 def stop():
  if child is not None and child.poll() is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
 def interrupt(signum,frame):raise TimeoutError('signal %s'%signum)
 for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,interrupt)
 try:
  with (root/'observer.log').open('x') as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   while child.poll() is None:
    _,end=allocation();deadline=min(deadline,end-30)
    if time.time()>=deadline or time.monotonic()>=mono_deadline:terminated=True;stop();break
    time.sleep(2)
  finished=time.time();_,end=allocation();deadline=min(deadline,end-30);assert timely(child.returncode,terminated,finished,deadline) and time.monotonic()<mono_deadline,'child exit or deadline failed'
  manifest=json.loads((output/'run_manifest.json').read_text());assert normal_manifest(manifest,job,c['expected_cases']),'observer manifest not normal mgnp GREEN';check_config(c);assert sha(a.config)==a.config_sha256 and sha(here/'manifest.json')==a.manifest_sha256
  _,end=allocation();assert time.time()<end,'allocation ended before receipt'
  (root/'transport-result.json').write_text(json.dumps({'status':'OBSERVER_NORMAL','job':job,'child_exit':child.returncode,'expected_cases':c['expected_cases'],'observer_manifest_sha256':sha(output/'run_manifest.json'),'observer_reports_production_weights_loaded':False,'gpu_requested':False,'config_sha256':a.config_sha256,'transport_manifest_sha256':a.manifest_sha256},indent=2)+'\n')
 except BaseException as e:
  stop();(root/'transport-failure.json').write_text(json.dumps({'status':'FAILED','error':repr(e),'child_exit':None if child is None else child.returncode},indent=2)+'\n');raise
if __name__=='__main__':main()
