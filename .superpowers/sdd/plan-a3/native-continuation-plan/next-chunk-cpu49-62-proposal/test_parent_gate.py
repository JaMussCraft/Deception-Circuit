import copy, hashlib, importlib.util, json
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('conditional_parent_gate',Path(__file__).with_name('parent_gate.py'));gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return dict(path=str(path),sha256=digest(path))
@pytest.fixture
def lineage(tmp_path):
 w=tmp_path/'work';w.mkdir();root=w/'scenario';parent=root/'diagnostics/cpu-next-cases32-48-job23470779';parent.mkdir(parents=True)
 ids=[format(i,'064x') for i in range(63)];source=write(w/'source.py',{'frozen':True});catalog=write(w/'catalog.json',{'cases':ids});scenario=write(root/'scenario/payload.json',{'model_identity':'original-tiny-CPU'});driver=write(w/'drivers.json',{'original':True});submission=write(w/'submission.json',{'job_id':'23470779','driver_manifest_sha256':driver['sha256']})
 expected=dict(parent_job_id='23470779',parent_directory=str(parent),pinned_files=[source,catalog,scenario,driver,submission],source_hashes={'source.py':source['sha256']},catalog_sha256=catalog['sha256'],case_ids=ids,parent_start=32,parent_count=17,parent_driver_sha256=driver['sha256'])
 alloc=dict(job_id='23470779',actual_GPU_count=0,allocation_memory_bytes=34359738368,host='compute-node');allocation=write(parent/'coordinator-allocation.json',alloc)
 native=[];auth=[];records=[]
 for i in range(32,49):
  case=ids[i];path=root/'pilot-verification-cases/selected'/case;write(path/'case.json',{'original':i});write(path/'COMPLETE.json',{'complete':True});ref=dict(path=str(path),files={f.name:dict(sha256=digest(f),nbytes=f.stat().st_size) for f in path.iterdir()})
  n=dict(case_id=case,actual_forward_calls=i+1,native_seconds=1.0);a=dict(case_id=case,new_model_forwards=0,authentication_seconds=1.0);native.append(n);auth.append(a);records.append(dict(case_id=case,original_case_forward_calls=i+1,reference=ref));write(parent/('slurm-case-'+case+'.json'),dict(actual_job_id='23470779',actual_step_id='0',host='compute-node',allocation_reference=allocation,case_reference=ref,native=n,authentication=a,scientific_execution=False,production_admission=False))
 coor=dict(actual_job_id='23470779',actual_step_id='0',indices=list(range(32,49)),new_case_ids=ids[32:49],new_native_case_count=17,preserved_case_ids=ids[:32],preserved_case_references_unchanged=True,actual_new_forward_calls=sum(range(33,50)),forbidden_auth_model_forwards=0,native=native,authentication=auth,original_case_records=records,full_pilot_complete=False,aggregate_executed=False,scientific_execution=False,execution_authorized=False,slurm_allocation_reference=allocation)
 write(parent/'coordinator-result.json',coor);write(parent/'result.json',dict(exit_code=0,term_sent_at=None,actual_slurm_job_id='23470779',selected_case_start=32,selected_case_count=17,injected_fixture=True,scientific_execution=False,production_admission=False));write(parent/'driver-identity.json',dict(actual_job_id='23470779',driver_sha256=driver['sha256'],source_hashes=expected['source_hashes'],catalog_sha256=expected['catalog_sha256'],start=32,count=17,scientific_execution=False,execution_authorized=False))
 accounting='23470779|COMPLETED|0:0\n23470779.0|COMPLETED|0:0\n'
 return w,root,expected,accounting

def current_references(root,expected):
 return {name:dict(path=str(root/'pilot-verification-cases/selected'/name),files={f.name:dict(sha256=digest(f),nbytes=f.stat().st_size) for f in (root/'pilot-verification-cases/selected'/name).iterdir()}) for name in expected['case_ids'][32:49]}

def test_requires_parent_success_before_any_model_work(lineage):
 w,r,e,a=lineage
 with pytest.raises((ValueError,AssertionError),match='parent|COMPLETED|successful'):
  gate.check_parent(w,r,e,a.replace('COMPLETED','RUNNING'),current_references(r,e))

def test_complete_parent_accepts_only_exact_case_scope(lineage):
 w,r,e,a=lineage;result=gate.check_parent(w,r,e,a,current_references(r,e));assert result['authenticated_parent_case_ids']==e['case_ids'][32:49];assert result['new_model_forwards']==0

@pytest.mark.parametrize('change',['source','scenario','missing_result','nonzero_exit','case_bytes','missing_marker','missing_sidecar','case_order','forward_count','authority'])
def test_refuses_incomplete_or_changed_parent(lineage,change):
 w,r,e,a=lineage;p=Path(e['parent_directory'])
 if change in ('source','scenario'):
  path=w/'source.py' if change=='source' else r/'scenario/payload.json';path.write_text('changed')
 elif change=='missing_result':(p/'result.json').unlink()
 elif change=='nonzero_exit':
  x=json.loads((p/'result.json').read_text());x['exit_code']=1;write(p/'result.json',x)
 elif change=='case_bytes':(r/'pilot-verification-cases/selected'/e['case_ids'][32]/'case.json').write_text('changed')
 elif change=='missing_marker':(r/'pilot-verification-cases/selected'/e['case_ids'][32]/'COMPLETE.json').unlink()
 elif change=='missing_sidecar':(p/('slurm-case-'+e['case_ids'][32]+'.json')).unlink()
 else:
  x=json.loads((p/'coordinator-result.json').read_text())
  if change=='case_order':x['new_case_ids'].reverse()
  elif change=='forward_count':x['actual_new_forward_calls']+=1
  elif change=='authority':x['scientific_execution']=True
  write(p/'coordinator-result.json',x)
 with pytest.raises((ValueError,AssertionError,FileNotFoundError)):gate.check_parent(w,r,e,a,current_references(r,e))


def test_bounded_accounting_propagation_retains_actual_observations(lineage):
 from types import SimpleNamespace
 w,r,e,a=lineage;now=[0];calls=[]
 def runner(command,**kwargs):
  calls.append(command);return SimpleNamespace(returncode=0,stderr='',stdout='' if len(calls)==1 else a)
 result=gate.require_parent(w,r,e,current_references(r,e),runner=runner,clock=lambda:now[0],sleeper=lambda seconds:now.__setitem__(0,now[0]+seconds))
 assert len(result['accounting_observations'])==2 and result['gate_seconds']==2
 assert result['accounting_observations'][0]['stdout']==''

def test_accounting_propagation_deadline_refuses(lineage):
 from types import SimpleNamespace
 w,r,e,a=lineage;now=[0]
 with pytest.raises(ValueError,match='deadline'):
  gate.require_parent(w,r,e,current_references(r,e),runner=lambda *args,**kw:SimpleNamespace(returncode=0,stderr='',stdout=''),clock=lambda:now[0],sleeper=lambda seconds:now.__setitem__(0,now[0]+seconds),maximum_wait_seconds=3)
 assert now[0]==3

def test_failed_parent_never_waits_for_retry(lineage):
 from types import SimpleNamespace
 w,r,e,a=lineage
 with pytest.raises(ValueError,match='COMPLETED'):
  gate.require_parent(w,r,e,current_references(r,e),runner=lambda *args,**kw:SimpleNamespace(returncode=0,stderr='',stdout=a.replace('COMPLETED','FAILED')),sleeper=lambda seconds:pytest.fail('must not wait/retry failed parent'))
