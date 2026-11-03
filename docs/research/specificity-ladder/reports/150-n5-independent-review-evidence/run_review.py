"""Root-submitted CPU only; exact immutable source/probe binding before and after."""
import pathlib,json,os,hashlib,subprocess,time,datetime,sys
E=pathlib.Path(__file__).resolve().parent;cfg=json.loads((E/'binding.json').read_text());B=pathlib.Path(cfg['runtime']);job=os.environ.get('SLURM_JOB_ID');assert job

def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def source_check():
 assert sha(cfg['snapshot'])==cfg['snapshot_sha256'];snapshot=json.loads(pathlib.Path(cfg['snapshot']).read_text());assert snapshot['source_commit']==cfg['source_commit']
 for name,value in snapshot['source_sha256'].items():
  p=B/name;assert p.is_file() and not p.is_symlink() and not p.stat().st_mode&0o222 and sha(p)==value,name
 for name,target in snapshot['input_links'].items():assert (B/name).is_symlink() and (B/name).resolve()==pathlib.Path(target).resolve()
 for name,value in json.loads((E/'probe-manifest.json').read_text()).items():assert sha(E/name)==value,name
source_check();raw=subprocess.run(['scontrol','show','job',job,'-o'],check=True,capture_output=True,text=True).stdout;facts=dict(x.split('=',1) for x in raw.split() if '=' in x);assert facts['JobState']=='RUNNING' and facts['Partition'].startswith('cpu') and 'gres/gpu' not in facts.get('AllocTRES','');(E/('allocation-'+job+'.txt')).write_text(raw)
base=E/('pytest-'+job);base.mkdir(exist_ok=False)
for name,python in [('mgnp','/u/swong2/.conda/envs/mgnp/bin/python'),('base','/sw/external/python/anaconda3/bin/python3.9')]:
 cmd=[python,'-m','pytest','-q','-p','no:cacheprovider','--basetemp='+str(base/name),str(E/'test_independent_n5.py')];env=dict(os.environ,PYTHONPATH=str(B),PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1');start=time.time()
 with (E/('pytest-'+name+'-'+job+'.log')).open('x') as f:r=subprocess.run(cmd,cwd=B,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=90)
 row=dict(command=cmd,cwd=str(B),started_utc=datetime.datetime.fromtimestamp(start,datetime.timezone.utc).isoformat(),elapsed_seconds=time.time()-start,exit_code=r.returncode,job_id=job,source_commit=cfg['source_commit'],source_and_probes_unchanged=True,software_fixtures_only=True,model_or_GPU=False);(E/('result-'+name+'-'+job+'.json')).write_text(json.dumps(row,indent=2)+'\n')
 if r.returncode:raise SystemExit(r.returncode)
source_check();(E/('COMPLETE-'+job+'.json')).write_text(json.dumps(dict(complete=True,source_commit=cfg['source_commit'],job_id=job,source_files=511,both_interpreters_passed=True,model_GPU_or_ledger_edits=False),indent=2)+'\n')
