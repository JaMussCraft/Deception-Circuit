from pathlib import Path
import json,hashlib,os,sys,subprocess,tempfile,time
E=Path(__file__).parent;R=Path(os.environ['REVIEW134_RUNTIME']);assert os.environ.get('SLURM_JOB_ID'),'substantial review tests require Slurm CPU job';snapshot=json.loads((R.parent/'snapshot.json').read_text());assert snapshot['source_commit']=='40fe57289405fd53a3fce02e5d4e47a0ebf78b64'
def bind():
 for name,value in snapshot['source_sha256'].items():
  p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_mode&0o222==0;assert hashlib.sha256(p.read_bytes()).hexdigest()==value
 return {'files':len(snapshot['source_sha256']),'source_sha256':snapshot['source_sha256']}
initial=bind();outcomes=[]
for label,python in [('mgnp','/u/swong2/.conda/envs/mgnp/bin/python'),('base','/sw/external/python/anaconda3/bin/python3.9')]:
 with tempfile.TemporaryDirectory(prefix='review134-'+os.environ['SLURM_JOB_ID']+'-'+label+'-') as temp:
  env=dict(os.environ,REVIEW134_BASETEMP=temp+'/pytest');command=[python,str(E/'pytest_child.py'),label];started=time.time();log=E/('pytest-'+label+'-'+os.environ['SLURM_JOB_ID']+'.log')
  with log.open('w') as stream:r=subprocess.run(command,cwd=R,env=env,stdout=stream,stderr=subprocess.STDOUT)
  outcomes.append({'label':label,'command':command,'exit_code':r.returncode,'wall_seconds':time.time()-started});(E/('execution-'+os.environ['SLURM_JOB_ID']+'.json')).write_text(json.dumps({'job_id':os.environ['SLURM_JOB_ID'],'source_commit':snapshot['source_commit'],'initial_binding':initial,'outcomes':outcomes,'node':os.uname().nodename,'no_GPU_or_real_input_preparation':True},indent=2))
  if r.returncode:raise SystemExit(r.returncode)
assert bind()==initial
print('INDEPENDENT134_DUAL_ENV_COMPLETE',flush=True)
