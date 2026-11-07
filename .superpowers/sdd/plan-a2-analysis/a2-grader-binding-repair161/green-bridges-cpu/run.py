import os,sys,json,pathlib,hashlib,time,socket
E=pathlib.Path(__file__).resolve().parent
O=pathlib.Path(sys.argv[1]); job=os.environ['SLURM_JOB_ID']
binding=json.loads((E/'expected-source.json').read_text()); C=pathlib.Path(binding['candidate'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 for name,value in binding['files'].items(): assert sha(C/name)==value,name
 for name,target in binding['input_links'].items(): assert (C/name).is_symlink() and os.readlink(C/name)==target,name
check()
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
a=json.loads((O/'allocation.json').read_text());assert a['job_id']==job
raw=a['scontrol_job']; facts=dict(v.split('=',1) for v in raw.split() if '=' in v)
assert facts['JobState']=='RUNNING' and int(facts['NumCPUs'])>=5
assert facts['Partition']=='RM-shared' and facts['Account']=='cis260361p' and facts['QOS']=='rm',facts
assert a['host'].split('.')[0]==socket.gethostname().split('.')[0]
assert socket.gethostname().split('.')[0] in [n.split('.')[0] for n in a['allocation_hosts']]
tres=dict(t.split('=',1) for t in facts.get('AllocTRES',facts.get('TRES','')).split(',') if '=' in t)
assert int(tres['cpu'])>=5 and not any(k.startswith('gres/gpu') and float(v)>0 for k,v in tres.items()),tres
mem=tres['mem']; assert mem.endswith('G') and float(mem[:-1])>=8 or mem.endswith('M') and float(mem[:-1])>=8192,mem
assert a['image_sha256']=='f50c8e39dd5e2ac1c1a4bdfd443351cb970513fdb10a572725eb53d7396f8697'
assert a['physical_alignment']=='/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment'
assert pathlib.Path(sys.executable).resolve()==pathlib.Path('/ocean/projects/cis260361p/swong2/envs/mgnp/bin/python').resolve()
sys.path.insert(0,str(C));os.chdir(C)
import pytest
reports=[]
class Reports:
 def pytest_runtest_logreport(self,report):
  if report.failed:reports.append(dict(nodeid=report.nodeid,when=report.when,text=str(report.longrepr)))
started=time.time(); tests=json.loads((E/'proposal.json').read_text())['tests']
code=pytest.main(['--confcutdir='+str(C),'--import-mode=importlib','-q','-p','no:cacheprovider','--basetemp='+str(O/('pytest-'+job+'-mgnp')),*[str(C/name) for name in tests]],plugins=[Reports()])
origins={n:m.__file__ for n,m in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','dataset','models','evaluation','tests','scripts') and getattr(m,'__file__',None)}
assert all(pathlib.Path(p).resolve().is_relative_to(C) for p in origins.values()),origins
check()
result=dict(kind='PROVISIONAL_BRIDGES_MGNP_ONLY_TEST_FEEDBACK',scientific_acceptance=False,delta_both_interpreters_still_required=True,job_id=job,cluster='bridges2',python=sys.executable,source_count=len(binding['files']),source_unchanged=True,allocation=a,pytest_exit=int(code),failed_reports=reports,module_origins=origins,elapsed_seconds=time.time()-started,models_or_tokenizers_loaded=False)
(O/('result-'+job+'-mgnp.json')).write_text(json.dumps(result,indent=2)+'\n')
assert int(code)==0,(code,reports)
print('PROVISIONAL_BRIDGES_MGNP_AFFECTED_A2_GREEN_ONLY',flush=True)
