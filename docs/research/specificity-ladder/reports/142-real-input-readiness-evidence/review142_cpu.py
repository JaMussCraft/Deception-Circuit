from pathlib import Path
import os,sys,json,subprocess,time,hashlib,datetime
E=Path(__file__).parent;W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');O=W/'outputs/_analyses/specificity-ladder/a3-source-cost-pilots-40fe57289405';R=W/'outputs/_analyses/specificity-ladder/a3-source-cost-runtime-40fe57289405/runtime';assert os.environ.get('SLURM_JOB_ID') and os.environ.get('CUDA_VISIBLE_DEVICES')==''
raw=subprocess.run(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o'],check=True,capture_output=True,text=True).stdout;f=dict(x.split('=',1) for x in raw.split() if '=' in x);assert f['JobState']=='RUNNING' and f['Partition'].startswith('cpu') and 'gres/gpu' not in f.get('AllocTRES','');(E/'actual-allocation.json').write_text(json.dumps({'job_id':os.environ['SLURM_JOB_ID'],'node':os.uname().nodename,'scontrol':raw,'gpus':0},indent=2))
commands=[]
for script,mode in [('check-science-and-inventories.py',m) for m in ('science','edge:fit-target','edge:pilot','mask:pilot','mask:full')]+[('check-copied-boundaries.py',o) for o in ('mask','edge')]:
 command=['/u/swong2/.conda/envs/mgnp/bin/python',str(E/script),mode];started=time.time()
 with (E/(script.replace('.py','')+'-'+mode.replace(':','-')+'.log')).open('x') as stream:r=subprocess.run(command,cwd=R,env=os.environ.copy(),stdout=stream,stderr=subprocess.STDOUT)
 commands.append({'command':command,'exit_code':r.returncode,'seconds':time.time()-started});(E/'cpu-review-commands.json').write_text(json.dumps(commands,indent=2));print(mode,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as file:
  for chunk in iter(lambda:file.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
m=json.loads((O/'evidence/complete-artifact-manifest.json').read_text());observed={}
for name,row in m['artifacts'].items():
 p=O/name;assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'];observed[name]=row
(E/'artifact-byte-check.json').write_text(json.dumps({'all_bytes_match':True,'files':len(observed),'artifacts':observed},indent=2))
assert sha(O/'run_manifest.json')=='2b6df60e22f5e2d60705ff549e7900c555a5c16797dc1c375481e764d8590258';(E/'CPU_REVIEW_COMPLETE.json').write_text(json.dumps({'job_id':os.environ['SLURM_JOB_ID'],'commit':'40fe57289405fd53a3fce02e5d4e47a0ebf78b64','all_commands_exit0':True,'artifact_bytes_match':True,'no_models_or_authority':True,'no_new_performance_benchmark':True},indent=2));print('INDEPENDENT142_CPU_REVIEW_COMPLETE',flush=True)
