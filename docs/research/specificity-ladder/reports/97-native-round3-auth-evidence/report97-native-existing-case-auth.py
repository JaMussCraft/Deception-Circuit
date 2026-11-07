from pathlib import Path
import faulthandler,functools,hashlib,json,resource,sys,time
root=Path(sys.argv[1]);out=Path(sys.argv[2]);began=time.perf_counter();attempts={'forwards':0,'pilot':0,'publication':0}
stack=(out/'fatal.log').open('w');faulthandler.enable(file=stack,all_threads=True)
def mark(event,**extra):
 print(json.dumps(dict(event=event,elapsed_seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,**extra)),flush=True)
def step(name,fn):
 mark('step_start',step=name);start=time.perf_counter();value=fn();mark('step_end',step=name,step_seconds=time.perf_counter()-start);return value
def forbidden(kind):
 def denied(*args,**kwargs):
  attempts[kind]+=1;raise RuntimeError('Read-only case authentication forbids '+kind)
 return denied
def tree(path):
 result={}
 for p in [path]+sorted(path.rglob('*')):
  assert not p.is_symlink()
  st=p.stat();item=dict(mode=st.st_mode,inode=st.st_ino,mtime_ns=st.st_mtime_ns)
  if p.is_file():item.update(bytes=st.st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
  else:item['directory']=True
  result[str(p.relative_to(path))]=item
 return result
mark('import_start')
from tests import a3_direction_native_scenario as s
from component_analysis import hooks
mark('import_end')
s.r._pilot_invocation=forbidden('pilot');s.pilot_cases=forbidden('pilot');hooks.capture_forward=forbidden('forwards')
s.r.publish_object=forbidden('publication');s.r.common.publish=forbidden('publication');s.r.common.write_json=forbidden('publication');s.r.artifacts._finish=forbidden('publication')
frozen=json.loads(Path('/tmp/report97-review111-round3-frozen-source.json').read_text())
def source_check():
 assert {name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in frozen}==frozen
step('frozen13_source_before',source_check)
case=root/'pilot-verification-cases/selected/4318f65b0a320e883897ca95ad472e2d1a0a11f53abea6ce1a848853d9fb57f1'
before=step('case_tree_before',lambda:tree(case));(out/'case-before.json').write_text(json.dumps(before,indent=2)+'\n')
original_record=json.loads((case/'case.json').read_text());original=dict(seconds=original_record['original_case_seconds'],forward_calls=original_record['original_case_forward_calls'])
assert original['forward_calls']==11100 and original['seconds']==102.63064642000245
assert not list((root/'pilot-scratch').iterdir())
design,protocol,model,plain=step('verify_expected_source_config_full_model',lambda:s.verify_scenario(root))
original_forward=plain.forward;plain.forward=forbidden('forwards');hook=plain.register_forward_pre_hook(forbidden('forwards'))
try:
 selected,_=step('read_completed_selected_bundle',lambda:s.r.read_bundle(root/'selected'))
 assert (root/'inventory/selected-pilot/COMPLETE.json').is_file()
 inv=step('independent_expected_inventory_rebuild_and_compare',lambda:s.inventory(root,design,protocol,'selected-pilot',selected=selected))
 invocations=step('validate_exact_expected_invocation_inventory',lambda:s._case_invocations(design,inv,'selected'))
 assert len(invocations)==63 and invocations[0]['invocation_id']==case.name
 invocation=invocations[0]
 binding=step('read_original_scenario_binding',lambda:s.r.read_object(root/'scenario'))
 assert s.model_identity(plain)==binding['model_identity']
 def wrap(owner,name):
  original=getattr(owner,name)
  @functools.wraps(original)
  def logged(*args,**kwargs):return step(name,lambda:original(*args,**kwargs))
  setattr(owner,name,logged)
 for owner,name in [(s.r,'_numeric_backing_proof'),(s.r._CompletedPackingProof,'__init__'),(s.r,'read_bundle'),(s.r,'load_selected_axes')]:wrap(owner,name)
 auth_start=time.perf_counter()
 result=step('original_read_pilot_case_full_authentication',lambda:s._read_pilot_case(case,model,design,protocol,inv,invocation,'selected',binding,root/'selected'))
 auth_seconds=time.perf_counter()-auth_start
 after=step('case_tree_after',lambda:tree(case));assert after==before
 (out/'case-after.json').write_text(json.dumps(after,indent=2)+'\n')
 step('frozen13_source_after',source_check)
 step('final_original_source_model_backing_verification',lambda:s.verify_scenario(root,load_model=False))
 assert s.model_identity(plain)==binding['model_identity']
 assert attempts=={'forwards':0,'pilot':0,'publication':0}
 mark('authentication_complete',authenticated_cases=1,full_selected_case_count=63,full_pilot_complete=False,new_numeric_forwards=0,attempted_forbidden_calls=attempts,authentication_seconds=auth_seconds,original_case=original,case_bytes_unchanged=True,case_path=str(case),returned_axis_count=result['axis_count'],source_unchanged=True)
finally:
 plain.forward=original_forward;hook.remove();faulthandler.disable();stack.close()
