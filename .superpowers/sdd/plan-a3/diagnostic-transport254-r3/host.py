#!/usr/bin/env python3
"""Unaccepted diagnostic transport; no admission or test result promotion."""
import argparse, ctypes, datetime, errno, hashlib, json, os, re, signal, socket, subprocess, time
from pathlib import Path
import transport229 as old

REL=Path('Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport254-r3')
DIAG=old.VIRT/'Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/green-timeout-diagnosis253'
RECIPE=DIAG/'root-diagnostic-recipe-r2.json'
PINS={'manifest.json':'d28cfe84647c1961a7c68520acf6dbedc10c8ace49eaa5f7ab029f932b485446','root-diagnostic-recipe-r2.json':'96c57370c5bbc3883eab47774d85d5c38d7c27c2ee5fa1586f246e2082f2c7fb','diagnostic253.py':'63568713bd1c40f143c43932a909f6faf7e831d3f217b6f311256b419c1f4bac','full-collected-nodeids.json':'c7db91d43948f91618dcb891486de6cf1135ee1f6d7d3d7aeecc0e1e4ad5f5eb','suspect-nodeids.json':'8b8e1d6e986219d614fc38ff5d6f57cc4977ffe6c7f3e28ff66b165abd5593cc','next-nodeid.json':'d241c971d92ce5ca2649175cb003003d95b7ed6ab86558a9011be3f0e893246d'}

def durable(path,value):
 with path.open('x') as f:
  json.dump(value,f,sort_keys=True,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())

def allocation(timeout=15):
 e=os.environ; job=e['SLURM_JOB_ID']; assert re.fullmatch('[0-9]+',job)
 raw=subprocess.check_output(['scontrol','show','job',job,'-o'],universal_newlines=True,timeout=timeout,env=dict(e,TZ='UTC'))
 f=dict(x.split('=',1) for x in raw.split() if '=' in x); t=dict(x.split('=',1) for x in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in x)
 assert f['JobId']==job and f['JobState']=='RUNNING' and re.search(r'\('+str(os.getuid())+r'\)',f['UserId'])
 assert f['Account']=='cis260361p' and f['Partition']=='RM-shared' and f['QOS']=='rm' and f['NumNodes']=='1' and f['NumTasks']=='1' and f['NumCPUs']=='18' and f['CPUs/Task']=='18' and t['cpu']=='18' and t['mem'] in ('32G','32768M')
 assert f['TimeLimit'] in ('00:25:00','25:00') and f['Requeue']=='0' and f['Restarts']=='0' and f['BatchHost'].split('.')[0]==socket.gethostname().split('.')[0]
 assert e.get('SLURM_CLUSTER_NAME')=='bridges2' and e.get('SLURM_CPUS_PER_TASK')=='18' and e.get('SLURM_NTASKS')=='1'
 assert not any(k.startswith('gres/gpu') and float(v)>0 for k,v in t.items()) and all(not e.get(k) for k in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS','CUDA_VISIBLE_DEVICES')) and all(e.get(k,'') in ('','0') for k in ('SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK'))
 return f,datetime.datetime.strptime(f['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp()

def source_check(c):
 assert c['status']=='ROOT_BOUND_A3_DIAGNOSTIC_PARTIAL'
 assert hashlib.sha256(json.dumps([c['files'],c['aliases']],sort_keys=True,separators=(',',':')).encode()).hexdigest()=='b5946b6cb6aff9c2fad0047f61affaacd0b5ec13e5b832c92e19a6fdd4f63af5'
 base=dict(c); base['status']='ROOT_BOUND_A3_GREEN_MGNP_TRANSPORT'; old.check_config(base)
 records={x['virtual']:x['sha256'] for x in c['files']}
 for name,h in PINS.items(): assert records[str(DIAG/name)]==h

def command(c,phase,kind,env,root):
 out=old.VIRT/REL/'jobs'/('job-'+env['SLURM_JOB_ID'])/phase['label']
 physical=Path(old.virtual_to_physical(str(out)))
 assert kind in ('v1','v2'); cg='/sys/fs/cgroup:/sys/fs/cgroup:ro'
 if kind=='v1':cg+=',/sys/fs/cgroup/memory:/sys/fs/cgroup/memory:ro'
 cmd=['apptainer','exec','--cleanenv','--contain','--no-home','--writable-tmpfs','--pwd',phase['cwd'],'--bind',str(old.PHYS)+':'+str(old.VIRT)+':ro','--bind','/ocean:/ocean:ro','--bind','/ocean/projects/cis260361p/swong2/hf/hub:/work/nvme/beto/swong2:ro','--bind',old.ENV_PATH+':/u/swong2/.conda/envs/mgnp:ro','--bind',str(physical)+':'+str(out)+':rw','--bind',cg]
 oldout=phase['prepare_fresh_output_directory']
 def replace(v):return v.replace(oldout,str(out))
 profile={k:v for k,v in env.items() if k.startswith('SLURM_')}; profile.update({k:replace(v) for k,v in phase['environment'].items()}); profile['HF_HUB_CACHE']='/work/nvme/beto/swong2'
 for k,v in sorted(profile.items()):cmd.extend(['--env',k+'='+v])
 return cmd+[old.IMAGE,old.PY,'-B',str(old.VIRT/REL/'inner.py'),kind,str(out)]+[replace(x) for x in phase['argv']]

def enable_subreaper():
 # Adopt orphaned descendants so the supervisor can reap its own process group.
 assert ctypes.CDLL(None, use_errno=True).prctl(36,1,0,0,0)==0

def cleanup_group(child):
 pgid=child.pid
 old.group_signal(pgid,signal.SIGTERM)
 started=time.monotonic(); deadline=started+15; final=started+20
 killed=False
 while True:
  leader_exit=child.poll()
  if leader_exit is not None:
   while True:
    try: pid,_=os.waitpid(-pgid,os.WNOHANG)
    except ChildProcessError: break
    if not pid: break
  if not old.group_exists(pgid):
   child.wait(timeout=max(0,final-time.monotonic())); return
  if time.monotonic()>=deadline:
   if killed: raise RuntimeError('process group not reaped after KILL')
   old.group_signal(pgid,signal.SIGKILL); killed=True; deadline=final
  time.sleep(.05)

def enough(now,end,remaining):
 # Per phase: 600 child seconds, 15 TERM, 5 KILL/reap; final reserve 120.
 return now+remaining*620+120<end

def execute_phase(c,p,index,kind,root,end):
 # All expensive preparation, including source validation and a fresh controller
 # read, precedes the last allocation check and Popen.
 source_check(c); assert old.sha(old.IMAGE)==old.IMAGE_SHA
 phase=root/p['label']; phase.mkdir(mode=0o700)
 cmd=command(c,p,kind,os.environ,root)
 durable(root/('command-%d.json'%index),{'status':'DIAGNOSTIC_PARTIAL','argv':cmd})
 f,current=allocation(); end=min(end,current); now=time.time()
 assert enough(now,end,2-index),'insufficient remaining allocation before launch'
 deadline=min(now+600,end-120-(1-index)*620-20); mono=time.monotonic()+min(600,deadline-now)
 child=None; timed_out=False; error=None; cleanup_error=None; cleanup_started=False
 try:
  with (phase/'pytest.stdout').open('xb') as stdout,(phase/'pytest.stderr').open('xb') as stderr:
   _,current=allocation(); end=min(end,current); now=time.time()
   deadline=min(deadline,end-120-(1-index)*620-20)
   if not enough(now,end,2-index) or now>=deadline or time.monotonic()>=mono:
    timed_out=True
   else:
    child=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,start_new_session=True)
   while child is not None and child.poll() is None:
    left=min(deadline-time.time(),mono-time.monotonic())
    if left<=0:timed_out=True;break
    try: _,current=allocation(timeout=min(15,left))
    except subprocess.TimeoutExpired:timed_out=True;break
    end=min(end,current); deadline=min(deadline,end-120-(1-index)*620-20)
    left=min(deadline-time.time(),mono-time.monotonic())
    if left<=0:timed_out=True;break
    time.sleep(min(1,left))
   # Immediately remove descendants, including after the leader has exited.
   if child is not None:
    cleanup_started=True; cleanup_group(child)
   finished=time.time(); _,current=allocation(); end=min(end,current); deadline=min(deadline,end-120-(1-index)*620-20)
   if finished>=deadline or time.time()>=deadline or time.monotonic()>=mono:timed_out=True
   stdout.flush(); os.fsync(stdout.fileno()); stderr.flush(); os.fsync(stderr.fileno())
 except BaseException as ex:
  error=repr(ex)
  if child is not None and not cleanup_started:
   try: cleanup_group(child)
   except BaseException as cleanup_ex: cleanup_error=repr(cleanup_ex)
 finally:
  durable(root/('phase-%d.json'%index),{'status':'DIAGNOSTIC_PARTIAL','label':p['label'],'acceptance':False,'timed_out':timed_out,'raw_returncode':None if child is None else child.returncode,'error':error,'cleanup_error':cleanup_error,'allocation_end_bound':end})
 if error or cleanup_error: raise RuntimeError(str(error)+'; cleanup '+str(cleanup_error))
 return end

def main():
 a=argparse.ArgumentParser();a.add_argument('--config',required=True);a.add_argument('--config-sha256',required=True);a.add_argument('--manifest-sha256',required=True); a=a.parse_args(); here=Path(__file__).resolve().parent
 assert Path(a.config).is_absolute() and Path(a.config).resolve()==Path(a.config) and not Path(a.config).is_symlink() and all(not x.is_symlink() for x in Path(a.config).parents) and re.fullmatch('[0-9a-f]{64}',a.config_sha256) and old.sha(a.config)==a.config_sha256
 assert re.fullmatch('[0-9a-f]{64}',a.manifest_sha256) and old.sha(here/'manifest.json')==a.manifest_sha256
 m=json.loads((here/'manifest.json').read_text()); assert set(m)=={'host.py','transport229.py','inner.py','launch.sh'}
 for n,h in m.items():assert old.sha(here/n)==h
 c=json.loads(Path(a.config).read_text());source_check(c)
 recipe=json.loads(Path(old.virtual_to_physical(str(RECIPE))).read_text()); phases=recipe['commands']; assert [x['label'] for x in phases]==['six-failure-traces','next-122'] and all(x['child_wall_limit_seconds']==600 and x['term_grace_seconds']==15 for x in phases)
 f,end=allocation(); job=os.environ['SLURM_JOB_ID'];root=old.PHYS/REL/'jobs'/('job-'+job)
 assert root.is_dir() and root.stat().st_uid==os.getuid() and not root.is_symlink() and root.resolve()==root and all(not p.is_symlink() for p in root.parents)
 assert not list(root.iterdir()); kind=old.actual_controller(job); enable_subreaper()
 durable(root/'host-before.json',{'status':'DIAGNOSTIC_PARTIAL','allocation':f,'end_bound':end,'config_sha256':a.config_sha256,'manifest_sha256':a.manifest_sha256,'cgroup_kind':kind,'hostname':socket.gethostname()})
 def interrupt(signum,frame):raise RuntimeError('host signal %d'%signum)
 for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,interrupt)
 error=None
 try:
  for i,p in enumerate(phases):end=execute_phase(c,p,i,kind,root,end)
 except BaseException as ex:error=repr(ex)
 finally:
  posterror=None
  try:
   source_check(c); assert old.sha(a.config)==a.config_sha256 and old.sha(here/'manifest.json')==a.manifest_sha256
   for n,h in m.items():assert old.sha(here/n)==h
   f,current=allocation();end=min(end,current)
  except BaseException as ex:posterror=repr(ex);f=None
  durable(root/'host-after.json',{'status':'DIAGNOSTIC_PARTIAL','acceptance':False,'error':error,'postcheck_error':posterror,'allocation':f,'end_bound':end})
 if error or posterror:raise RuntimeError('diagnostic partial: '+str(error)+'; postcheck '+str(posterror))
if __name__=='__main__':main()
