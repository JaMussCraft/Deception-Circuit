"""Read actual Slurm CPU allocation facts; no allocation creation or env mutation."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,time
ENV_NAMES=('SLURM_JOB_ID','SLURM_JOBID','SLURM_STEP_ID','SLURM_STEPID','SLURM_CLUSTER_NAME','SLURM_JOB_ACCOUNT','SLURM_JOB_PARTITION','SLURM_JOB_NODELIST','SLURM_NODELIST','SLURM_CPUS_PER_TASK','SLURM_JOB_CPUS_PER_NODE','SLURM_CPUS_ON_NODE','SLURM_JOB_NUM_NODES','SLURM_NNODES','SLURM_NTASKS','SLURM_MEM_PER_NODE','SLURM_MEM_PER_CPU','SLURM_JOB_GPUS','SLURM_STEP_GPUS','SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK','CUDA_VISIBLE_DEVICES')
def environment():return {name:os.environ[name] for name in ENV_NAMES if name in os.environ}
def memory_bytes(value):
 match=re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)([KMGT]?)',value,re.I);assert match,'Unsupported Slurm memory representation: '+value
 return int(float(match[1])*1024**{'':2,'K':1,'M':2,'G':3,'T':4}[match[2].upper()])
def duration(value):
 days=0
 if '-' in value:day,value=value.split('-',1);days=int(day)
 parts=[int(p) for p in value.split(':')]
 if len(parts)==2:parts=[0]+parts
 assert len(parts)==3
 return days*86400+parts[0]*3600+parts[1]*60+parts[2]
def read_current(workdir,*,minimum_remaining_seconds=0):
 job=os.environ.get('SLURM_JOB_ID','');assert re.fullmatch(r'\d+',job),'Actual non-array Slurm job required; no login execution'
 env=environment();assert env.get('SLURM_CLUSTER_NAME')=='delta';assert os.environ.get('SLURM_CPUS_PER_TASK')=='4','Actual4CPU task required'
 raw=subprocess.run(['scontrol','-o','show','job',job],capture_output=True,text=True,check=True,timeout=15,env=dict(os.environ,TZ='UTC')).stdout
 fields=dict(word.split('=',1) for word in raw.split() if '=' in word);assert fields.get('JobId')==job and fields.get('JobState')=='RUNNING'
 assert re.search(r'\('+str(os.getuid())+r'\)',fields.get('UserId','')),'Allocation user differs'
 tres=dict(item.split('=',1) for item in fields.get('AllocTRES','').split(',') if '=' in item)
 assert int(tres.get('cpu','0'))==4 and int(fields.get('NumNodes','0'))==1
 assert not any(key.startswith('gres/gpu') and float(value)>0 for key,value in tres.items()),'GPU allocation forbidden'
 assert memory_bytes(tres['mem'])==32*1024**3,'Exact32GiB actual allocation required'
 for name in ('SLURM_JOB_GPUS','SLURM_STEP_GPUS'):assert not os.environ.get(name),'GPU-ID environment present; refuse rather than unset it'
 for name in ('SLURM_GPUS','SLURM_GPUS_ON_NODE','SLURM_GPUS_PER_NODE','SLURM_GPUS_PER_TASK'):assert os.environ.get(name,'') in ('','0'),'GPU-count environment present'
 assert fields.get('Account','').endswith('-cpu') and fields.get('Partition','').startswith('cpu')
 assert Path(fields['WorkDir']).resolve()==Path(workdir).resolve()
 hosts=subprocess.run(['scontrol','show','hostnames',fields['NodeList']],capture_output=True,text=True,check=True,timeout=15).stdout.split()
 host=os.uname().nodename;assert host.split('.')[0] in {h.split('.')[0] for h in hosts},'This process is not on allocated compute node'
 limit=duration(fields['TimeLimit']);assert limit==7500 and fields['Partition']=='cpu','This proposal requires exact125min normal CPU allocation'
 end=datetime.datetime.fromisoformat(fields['EndTime']).replace(tzinfo=datetime.timezone.utc).timestamp();assert end-time.time()>=minimum_remaining_seconds,'Insufficient actual allocation finish margin'
 return dict(kind='actual_slurm_cpu_fixture_provenance',job_id=job,step_id=env.get('SLURM_STEP_ID',env.get('SLURM_STEPID')),host=host,pid=os.getpid(),observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),slurm_environment=env,allocation_fields=fields,allocation_tres=tres,allocation_memory_bytes=memory_bytes(tres['mem']),time_limit_seconds=limit,end_time_unix=end,actual_GPU_count=0,raw_scontrol=raw,raw_scontrol_sha256=hashlib.sha256(raw.encode()).hexdigest(),cpu_model=next(line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),affinity_CPUs=sorted(os.sched_getaffinity(0)),process_cgroup=Path('/proc/self/cgroup').read_text(),scientific_execution=False,production_admission=False)

def cgroup_snapshot():
 """Capture the real memory-controller ancestry on cgroupv1 or v2."""
 memberships=[line.split(':',2) for line in Path('/proc/self/cgroup').read_text().splitlines()]
 unified=next((row[2] for row in memberships if row[0]=='0' and row[1]==''),None)
 legacy_memory=next((row[2] for row in memberships if 'memory' in row[1].split(',')),None)
 controller='v1' if legacy_memory is not None else 'v2'
 relative=legacy_memory if legacy_memory is not None else unified
 assert relative is not None,'Actual memory-controller membership required'
 mount=None
 for line in Path('/proc/self/mountinfo').read_text().splitlines():
  before,after=line.split(' - ',1);left=before.split();right=after.split()
  if controller=='v2' and right[0]=='cgroup2' or controller=='v1' and right[0]=='cgroup' and 'memory' in right[2].split(','):
   mount_root=Path(left[3]);mount=Path(left[4]);break
 assert mount is not None,'Actual memory-controller mount required'
 relpath=Path(relative)
 if relpath.is_relative_to(mount_root):suffix=relpath.relative_to(mount_root)
 else:suffix=Path(relative.lstrip('/'))
 p=mount/suffix;assert p.is_dir() and p.resolve().is_relative_to(mount.resolve())
 result=[]
 while True:
  item=dict(path=str(p),controller=controller)
  names=('memory.current','memory.max','memory.events','cpu.max','cpuset.cpus.effective') if controller=='v2' else ('memory.usage_in_bytes','memory.limit_in_bytes','memory.max_usage_in_bytes','memory.failcnt','memory.oom_control','memory.use_hierarchy')
  for name in names:
   file=p/name
   if file.exists():item[name]=file.read_text().strip()
  if controller=='v1':
   item['memory_event_semantics']='v1 raw failcnt/oom_control; not equivalent to v2 memory.events'
   if 'memory.usage_in_bytes' in item:item['memory.current']=item['memory.usage_in_bytes']
   if 'memory.limit_in_bytes' in item:item['memory.max']='max' if int(item['memory.limit_in_bytes'])>=2**60 else item['memory.limit_in_bytes']
  item['v2_memory_events_available']='memory.events' in item
  if item.get('memory.max','max')!='max':item['headroom_bytes']=int(item['memory.max'])-int(item.get('memory.current','0'))
  result.append(item)
  if p==mount:break
  p=p.parent
 return result
