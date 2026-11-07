"""Bridges CPU producer transport; reuse unchanged existing execute supervisor."""
import argparse,datetime,json,os,re,resource,socket,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import common as c
SUPERVISOR=P.parent.parent/'plan'/'task23-green-r8-sharded'/'supervisor.py'
ADAPTER=P.parent/'prepared-resource-runner278-r2'/'runner.py'
ENTRY_WALL=time.time();ENTRY_MONO=time.monotonic()

def physical(cfg,value):
 path=Path(value)
 for virtual,actual in ((cfg['virtual_alignment'],cfg['physical_alignment']),('/u/swong2/.conda/envs/mgnp',cfg['packed_env']),
  ('/work/nvme/beto/swong2/hub','/ocean/projects/cis260361p/swong2/hf/hub')):
  try:return str(Path(actual)/path.relative_to(virtual))
  except ValueError:pass
 assert str(path).startswith('/ocean/'),'unmapped original virtual path: '+str(path)
 return str(path)


def container_command(cfg,kind,env,wrapper_start,deadline=None):
 assert kind in ('v1','v2');root=Path(cfg['run_root']);child=root/'child'
 cg='/sys/fs/cgroup:/sys/fs/cgroup:ro'
 if kind=='v1':cg+=',/sys/fs/cgroup/memory:/sys/fs/cgroup/memory:ro'
 argv=['apptainer','exec','--cleanenv','--contain','--no-home','--writable-tmpfs','--pwd',cfg['export'],
  '--bind',cfg['physical_alignment']+':'+cfg['virtual_alignment']+':ro','--bind','/ocean:/ocean:ro',
  '--bind','/ocean/projects/cis260361p/swong2/hf/hub:/work/nvme/beto/swong2/hub:ro',
  '--bind',cfg['packed_env']+':/u/swong2/.conda/envs/mgnp:ro',
  '--bind',physical(cfg,str(child))+':'+str(child)+':rw','--bind',cg]
 profile={k:v for k,v in env.items() if k.startswith('SLURM_')}
 profile.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',
  HF_HUB_CACHE='/work/nvme/beto/swong2/hub',HF_HOME='/work/nvme/beto/swong2',
  OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
  DC_CLUSTER='bridges2',DC_PYTHON=cfg['python'],A3_REPO_ROOT=cfg['export'],
  A3_WRAPPER_START_SECONDS=str(wrapper_start),A3_PRODUCER_DEADLINE=str(deadline),A3_STAGE_NAME='candidate-producer')
 for key,value in sorted(profile.items()):argv+=['--env',key+'='+value]
 return argv+[cfg['image'],cfg['python'],'-B',str(P.parent.parent/'plan'/'task23-green-r8-sharded'/'bridges'/'inner.py'),kind,str(child),cfg['python'],'-B',str(P/'driver.py'),'--config',cfg.get('config_path',str(P/'config.template.json')),'--config-sha256',cfg.get('config_sha256','UNBOUND')]


def seconds(value):
 days=0
 if '-' in value:d,value=value.split('-',1);days=int(d)
 parts=[int(x) for x in value.split(':')]
 if len(parts)==2:parts.insert(0,0)
 assert len(parts)==3
 return days*86400+parts[0]*3600+parts[1]*60+parts[2]


def allocation(cfg,timeout=15):
 env=os.environ;job=env['SLURM_JOB_ID'];assert job==cfg['job_id'] and re.fullmatch('[0-9]+',job)
 raw=subprocess.check_output(['scontrol','show','job',job,'-o'],universal_newlines=True,timeout=timeout,env=dict(env,TZ='UTC'))
 f=dict(word.split('=',1) for word in raw.split() if '=' in word)
 t=dict(word.split('=',1) for word in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in word)
 assert f['JobId']==job and f['JobState']=='RUNNING' and re.search(r'\('+str(os.getuid())+r'\)',f['UserId'])
 assert (f['Account'],f['Partition'],f['QOS'])==(cfg['account'],cfg['partition'],cfg['qos'])
 assert f['NumNodes']==f['NumTasks']=='1' and int(f['NumCPUs'])==int(f['CPUs/Task'])==int(t['cpu'])==cfg['cpus']
 match=re.fullmatch(r'(\d+)([KMGT])',t['mem']);assert match
 assert int(match[1])*1024**dict(K=1,M=2,G=3,T=4)[match[2]]==cfg['memory_bytes']
 assert seconds(f['TimeLimit'])==cfg['allocation_seconds'] and f['Requeue']==f['Restarts']=='0'
 assert f['BatchHost'].split('.')[0]==socket.gethostname().split('.')[0]
 assert Path(f['WorkDir']).resolve()==Path.cwd().resolve()
 assert env.get('SLURM_CLUSTER_NAME')==cfg['cluster'] and env.get('SLURM_CPUS_PER_TASK')==str(cfg['cpus']) and env.get('SLURM_NTASKS')=='1'
 assert not any(k.startswith('gres/gpu') and float(v)>0 for k,v in t.items())
 assert all(not env.get(k) for k in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS','CUDA_VISIBLE_DEVICES'))
 assert all(env.get(k,'') in ('','0') for k in ('SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK'))
 f.update(raw_scontrol=raw,raw_scontrol_sha256=__import__('hashlib').sha256(raw.encode()).hexdigest(),affinity_CPUs=sorted(os.sched_getaffinity(0)))
 end=datetime.datetime.strptime(f['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp()
 return f,end


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--config');ap.add_argument('--config-sha256');ap.add_argument('--dry-run',action='store_true');a=ap.parse_args()
 if a.dry_run:
  print(json.dumps(dict(status='UNBOUND_CANDIDATE_ONLY',actual_job=None,candidate_source=None,actual_config=None,
   native_imports=False,scheduler_calls=0,execution_authorized=False,driver=str(P/'driver.py')),sort_keys=True));return
 if not a.config or not a.config_sha256:ap.error('unbound actual config')
 path=Path(a.config);assert c.sha(path)==a.config_sha256
 cfg=c.read(path)
 try:c.validate(cfg)
 except ValueError as error:ap.error(str(error))
 cfg['config_path']=str(path);cfg['config_sha256']=a.config_sha256
 f,initial_end=allocation(cfg)
 supervisor=c.load(SUPERVISOR,'candidate311_existing_supervisor')
 start=float(os.environ.get('A3_WRAPPER_START_SECONDS',ENTRY_WALL))
 deadline=supervisor.stage_bound(start,initial_end,initial_end,cfg['child_cap_seconds'])
 mono=ENTRY_MONO+max(0,deadline-ENTRY_WALL)
 root=Path(physical(cfg,cfg['run_root']))
 assert root.is_dir() and root.stat().st_uid==os.getuid() and root.resolve()==root
 assert all(not p.is_symlink() for p in [root]+list(root.parents)) and not list(root.iterdir())
 (root/'child').mkdir(mode=0o700)
 adapter=c.load(ADAPTER,'candidate311_existing_observer')
 c.durable(root/'host-before.json',dict(allocation=f,initial_end=initial_end,wrapper_start=start,deadline=deadline,monotonic_deadline=mono,process=adapter.process_snapshot()))
 result=None;failure=None;post=None
 try:
  mapper=lambda value:physical(cfg,value)
  c.check_packet(cfg,mapper);c.check_sources(cfg,mapper)
  assert c.sha(cfg['image'])==cfg['image_sha256']
  stats=os.statvfs(str(root));assert stats.f_bavail*stats.f_frsize>=cfg['storage_free_bytes_required']
  transport=c.load(P.parent.parent/'plan'/'task23-green-r8-sharded'/'bridges'/'transport229.py','candidate311_existing_transport')
  kind=transport.actual_controller(cfg['job_id'])
  command=container_command(cfg,kind,os.environ,start,deadline)
  c.durable(root/'command.json',dict(argv=command,config_sha256=a.config_sha256,deadline=deadline,monotonic_deadline=mono,cgroup_controller=kind))
  supervisor.enable_subreaper()
  with (root/'child.stdout').open('xb') as stdout,(root/'child.stderr').open('xb') as stderr:
   result=supervisor.execute(command,stdout,stderr,cfg['child_cap_seconds'],initial_end,
    lambda timeout=15:allocation(cfg,timeout),wall_deadline=deadline,monotonic_deadline=mono)
  c.durable(root/'supervisor-terminal.json',result)
  assert result['normal_completion'] is True,result
  child=c.read(root/'child'/'run_manifest.json')
  assert child['status']=='candidate_producer_completed' and child['candidate_commit']==cfg['candidate_commit'] and child['execution_authorized'] is False
 except BaseException as error:failure=repr(error)
 finally:
  try:
   c.check_packet(cfg,lambda value:physical(cfg,value));c.check_sources(cfg,lambda value:physical(cfg,value))
   assert c.sha(path)==a.config_sha256 and c.sha(cfg['image'])==cfg['image_sha256']
   f,current_end=allocation(cfg);assert time.time()<min(initial_end,current_end)
  except BaseException as error:post=repr(error)
  usage=resource.getrusage(resource.RUSAGE_CHILDREN)
  c.durable(root/'host-terminal.json',dict(kind='PROVISIONAL_CANDIDATE_CPU_PRODUCER_TERMINAL',candidate_only=True,
   normal_completion=not failure and not post,exit_code=0 if not failure and not post else 1,
   error=failure,postcheck_error=post,supervisor=result,actual_job_id=cfg['job_id'],actual_cluster=cfg['cluster'],allocation=f,
   wall_seconds=time.time()-start,process=adapter.process_snapshot(),reaped_children_user_seconds=usage.ru_utime,
   reaped_children_system_seconds=usage.ru_stime,reaped_children_peak_rss_bytes=usage.ru_maxrss*1024,
   reaped_children_scope='host lifetime children including container and scontrol; not isolated-child or per-step peak; no baseline subtraction',
   execution_authorized=False,source_publication=False,native_acceptance_granted=False))
 if failure or post:raise RuntimeError(str(failure)+'; postcheck '+str(post))

if __name__=='__main__':main()
