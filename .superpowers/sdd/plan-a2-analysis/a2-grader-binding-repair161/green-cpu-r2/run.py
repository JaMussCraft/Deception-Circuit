import os,sys,json,pathlib,hashlib,time,subprocess
E=pathlib.Path(__file__).resolve().parent;binding=json.loads((E/'expected-source.json').read_text());C=pathlib.Path(binding['candidate']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 for name,value in binding['files'].items():assert sha(C/name)==value,name
 for name,value in binding['input_files'].items():assert sha(C/name)==value,name
 for name,target in binding['input_links'].items():assert (C/name).is_symlink() and os.readlink(C/name)==target,name
check();job=os.environ['SLURM_JOB_ID'];assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
raw=subprocess.check_output(['scontrol','show','job',job,'-o'],text=True);facts=dict(v.split('=',1) for v in raw.split() if '=' in v);assert facts['JobState']=='RUNNING' and int(facts['NumCPUs'])>=4
assert facts['Partition'] in ('cpu','cpu-interactive');tres=dict(t.split('=',1) for t in facts['AllocTRES'].split(',') if '=' in t);assert not any(k.startswith('gres/gpu') and float(v)>0 for k,v in tres.items())
hosts=subprocess.check_output(['scontrol','show','hostnames',facts['NodeList']],text=True).split();assert os.uname().nodename.split('.')[0] in [n.split('.')[0] for n in hosts]
sys.path.insert(0,str(C));os.chdir(C)
import pytest
reports=[]
class Reports:
 def pytest_runtest_logreport(self,report):
  if report.failed:reports.append(dict(nodeid=report.nodeid,when=report.when,text=str(report.longrepr)))
tests=json.loads((E/'proposal.json').read_text())['tests'];started=time.time()
code=pytest.main(['--confcutdir='+str(C),'--import-mode=importlib','-q','-p','no:cacheprovider','--basetemp='+str(E/('pytest-'+job+'-'+sys.argv[1])),*[str(C/name) for name in tests]],plugins=[Reports()])
origins={n:m.__file__ for n,m in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','dataset','models','evaluation','tests','scripts') and getattr(m,'__file__',None)}
assert all(pathlib.Path(p).resolve().is_relative_to(C) for p in origins.values()),origins
check();result=dict(job_id=job,python=sys.executable,source_count=len(binding['files']),source_unchanged=True,allocation=raw,pytest_exit=int(code),failed_reports=reports,module_origins=origins,elapsed_seconds=time.time()-started,models_or_tokenizers_loaded=False,production_edits=True)
(E/('result-'+job+'-'+sys.argv[1]+'.json')).write_text(json.dumps(result,indent=2)+'\n')
assert int(code)==0,(code,reports)
print('FULL_AFFECTED_A2_GREEN_CONFIRMED',flush=True)
