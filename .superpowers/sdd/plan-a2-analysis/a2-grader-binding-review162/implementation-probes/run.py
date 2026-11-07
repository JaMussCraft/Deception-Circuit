from pathlib import Path
import os,sys,json,hashlib,time,subprocess
E=Path(__file__).resolve().parent;frozen=json.loads((E/'expected-source.json').read_text());C=Path(frozen['candidate'])
def check():
 for n,digest in frozen['files'].items():assert hashlib.sha256((C/n).read_bytes()).hexdigest()==digest,n
 for n,target in frozen['input_links'].items():assert (C/n).is_symlink() and os.readlink(C/n)==target,n
check();job=os.environ['SLURM_JOB_ID'];raw=subprocess.check_output(['scontrol','show','job',job,'-o'],text=True);fields=dict(x.split('=',1) for x in raw.split() if '=' in x)
assert fields['JobState']=='RUNNING';tres=dict(x.split('=',1) for x in fields['AllocTRES'].split(',') if '=' in x);assert not any(k.startswith('gres/gpu') and float(v)>0 for k,v in tres.items())
hosts=subprocess.check_output(['scontrol','show','hostnames',fields['NodeList']],text=True).split();assert os.uname().nodename.split('.')[0] in [h.split('.')[0] for h in hosts]
sys.path.insert(0,str(C));os.chdir(E)
from component_analysis import a2_pipeline as a2
from component_analysis import ladder_pipeline as a1
# Check actual candidate catalogues as well as temporary adversarial fixtures.
provenance,binding=a2._observe_grader_catalogue()
import pytest
started=time.monotonic();code=pytest.main(['--confcutdir='+str(E),'--import-mode=importlib','-q','-p','no:cacheprovider','--basetemp='+str(E/('temp-'+job+'-'+sys.argv[1])),str(E/'test_independent.py')])
origins={n:str(Path(m.__file__).resolve()) for n,m in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','dataset','evaluation','models') and getattr(m,'__file__',None)}
assert all(Path(p).is_relative_to(C) for p in origins.values());check()
(E/('result-'+job+'-'+sys.argv[1]+'.json')).write_text(json.dumps(dict(job_id=job,allocation=raw,python=sys.executable,pytest_exit=int(code),elapsed_seconds=time.monotonic()-started,module_origins=origins,source_unchanged=True,actual_catalogue_routes=list(provenance),binding_kind=binding['kind'],models_requested=False),indent=2)+'\n');assert int(code)==0
