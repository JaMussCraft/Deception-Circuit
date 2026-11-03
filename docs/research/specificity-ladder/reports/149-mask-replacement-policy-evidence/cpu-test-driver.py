import os,json,sys,time,subprocess,hashlib
from pathlib import Path
E=Path(__file__).resolve().parent
assert os.environ.get('SLURM_JOB_ID','').isdigit() and os.environ.get('CUDA_VISIBLE_DEVICES')==''
binding=json.loads((E/'candidate-binding.json').read_text());root=Path(binding['candidate'])
def verify():
    for f,h in binding['files_sha256'].items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h,f
    for f,target in binding['links'].items():assert os.readlink(root/f)==target,f
verify()
job=os.environ['SLURM_JOB_ID'];results=[]
(E/('actual-allocation-'+job+'.txt')).write_text(subprocess.check_output(['scontrol','-o','show','job',job],universal_newlines=True))
for tag,python in [('mgnp','/u/swong2/.conda/envs/mgnp/bin/python'),('base','/sw/external/python/anaconda3/bin/python3.9')]:
    env=dict(os.environ,PYTHONPATH=str(E)+':'+str(root),REVIEW149_CANDIDATE=str(root),REVIEW149_IMPORTS=str(E/(tag+'-imports.json')))
    cmd=[python,'-m','pytest','-q','-p','no:cacheprovider','-p','review149_imports','--basetemp',str(E/('pytest-'+job+'-'+tag))]+json.loads((E/'pytest-selectors.json').read_text())
    started=time.perf_counter()
    with (E/(tag+'-pytest.log')).open('w') as log:p=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
    results.append(dict(interpreter=python,tag=tag,command=cmd,exit_code=p.returncode,wall_seconds=time.perf_counter()-started))
    (E/'cpu-test-results.json').write_text(json.dumps(results,indent=2)+'\n')
verify()
(E/'cpu-test-completion.json').write_text(json.dumps(dict(job_id=job,all_pass=all(r['exit_code']==0 for r in results),source_unchanged=True,no_pretrained_or_production_model=True,tiny_injected_fixture_models_may_be_constructed=True,execution_authorized=False),indent=2)+'\n')
sys.exit(0 if all(r['exit_code']==0 for r in results) else 1)
