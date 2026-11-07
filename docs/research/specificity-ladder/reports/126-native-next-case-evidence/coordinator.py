"""Proposed, NOT RUN: one frozen injected case then same-process read-only auth."""
from pathlib import Path
import argparse,hashlib,json,os,resource,sys,time

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--root',required=True);p.add_argument('--out',required=True);args=p.parse_args()
 root=Path(args.root).resolve();out=Path(args.out).resolve();w=Path.cwd();began=time.perf_counter();phase='startup';forwards=[0];denials=[0]
 def write(name,value):
  with (out/name).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
 def mark(event,**extra):print(json.dumps(dict(event=event,elapsed_seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,observed_model_forward_calls=forwards[0],**extra)),flush=True)
 def step(name,fn):
  nonlocal phase
  phase=name;mark('step_start',step=name);start=time.perf_counter();value=fn();mark('step_end',step=name,step_seconds=time.perf_counter()-start);return value
 frozen=json.loads(Path(__file__).with_name('source-and-cases.json').read_text())
 assert root==Path(frozen['scenario_root']) and out.is_dir()
 def sources():assert {name:hashlib.sha256((w/name).read_bytes()).hexdigest() for name in frozen['source_hashes']}==frozen['source_hashes']
 step('frozen_source_before',sources)
 write('driver-identity.json',dict(driver_path=str(Path(__file__).resolve()),driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_hashes=frozen['source_hashes'],case_index=1,new_case_count=1,scientific_execution=False,execution_authorized=False))
 mark('import_start')
 from tests import a3_direction_native_scenario as s
 from component_analysis import hooks
 mark('import_end')
 r=s.r;old_id=frozen['cases'][0]['invocation_id'];new_id=frozen['cases'][1]['invocation_id'];base=root/'pilot-verification-cases/selected';old_case=base/old_id;new_case=base/new_id
 assert {x.name for x in base.iterdir()}=={old_id} and not new_case.exists()
 assert not list((root/'pilot-scratch').iterdir())
 old_reference=step('preserved_old_case_byte_reference',lambda:r.object_reference(old_case))
 for path in ('scenario','tiny-model','selected','inventory/selected-pilot'):
  assert (root/path/'COMPLETE.json').is_file(),path
 design,protocol,model,plain=step('verify_scenario',lambda:s.verify_scenario(root))
 selected,_=step('read_selected',lambda:r.read_bundle(root/'selected'))
 inv=step('existing_inventory_canonical_rebuild_compare',lambda:s.inventory(root,design,protocol,'selected-pilot',selected=selected))
 invocations=inv['packing_invocations'] or r._serial_invocations(inv)
 assert [x['invocation_id'] for x in invocations]==[x['invocation_id'] for x in frozen['cases']] and len(invocations)==63
 binding=step('read_scenario_binding',lambda:r.read_object(root/'scenario'))
 original_capture=hooks.capture_forward;original_invocation=r._pilot_invocation;original_forward=plain.forward;hook=None
 def counted(*a,**kw):forwards[0]+=1;return original_capture(*a,**kw)
 def timed_invocation(*a,**kw):return step('actual_native_invocation',lambda:original_invocation(*a,**kw))
 def denied(*a,**kw):denials[0]+=1;raise RuntimeError('Read-only warm authentication forbids model forwards/pilot/publication')
 original_publish=r.publish_object;original_common_publish=r.common.publish;original_write=r.common.write_json;original_finish=r.artifacts._finish
 try:
  hooks.capture_forward=counted;r._pilot_invocation=timed_invocation
  mark('native_setup_context',numeric_backing_cache_roots=list(r._NUMERIC_BACKING_CACHE))
  refs=step('original_pilot_cases_one_new_case',lambda:s.pilot_cases(model,design,protocol,inv,root=root,part='selected',case_ids=[new_id],binding=binding,selected_path=root/'selected',resume=True))
  assert len(refs)==1
  native_record=r.artifacts._strict_json(new_case/'case.json');assert native_record['original_case_forward_calls']==forwards[0]>0
  new_reference=r.object_reference(new_case);cache_roots=list(r._NUMERIC_BACKING_CACHE)
  assert str((root/'selected').absolute()) in cache_roots
  write('new-native-case.json',dict(case_id=new_id,reference=new_reference,original_case_seconds=native_record['original_case_seconds'],original_case_forward_calls=native_record['original_case_forward_calls'],numeric_backing_cache_roots=cache_roots,full_pilot_complete=False))
  before_forwards=forwards[0];hooks.capture_forward=denied;r._pilot_invocation=denied;plain.forward=denied;hook=plain.register_forward_pre_hook(denied)
  r.publish_object=denied;r.common.publish=denied;r.common.write_json=denied;r.artifacts._finish=denied
  auth_start=time.perf_counter()
  step('same_process_original_full_read_only_reauth',lambda:s._read_pilot_case(new_case,model,design,protocol,inv,invocations[1],'selected',binding,root/'selected'))
  warm_seconds=time.perf_counter()-auth_start
  assert denials[0]==0 and forwards[0]==before_forwards
  assert r.object_reference(new_case)==new_reference and r.object_reference(old_case)==old_reference
  assert s.model_identity(plain)==binding['model_identity']
  step('final_scenario_backing_check',lambda:s.verify_scenario(root,load_model=False));step('frozen_source_after',sources)
  assert not list((root/'pilot-scratch').iterdir())
  write('coordinator-result.json',dict(kind='injected_native_operational_continuation',new_case_id=new_id,new_native_case_count=1,new_case_authenticated=True,same_process_reauth_complete=True,reauth_seconds=warm_seconds,reauth_new_model_forwards=0,forbidden_calls=denials[0],actual_new_native_forward_calls=forwards[0],original_new_case_seconds=native_record['original_case_seconds'],original_new_case_forwards=native_record['original_case_forward_calls'],preserved_case_reference_unchanged=True,new_case_reference_unchanged=True,numeric_backing_cache_roots=cache_roots,full_pilot_complete=False,aggregate_executed=False,scientific_execution=False,execution_authorized=False,wall_seconds=time.perf_counter()-began))
  mark('coordinator_complete',new_case_id=new_id,warm_auth_seconds=warm_seconds,full_pilot_complete=False)
 except BaseException as error:
  write('coordinator-failure.json',dict(phase=phase,error=repr(error),elapsed_seconds=time.perf_counter()-began,actual_observed_model_forward_calls=forwards[0],whole_pilot_complete=False));raise
 finally:
  hooks.capture_forward=original_capture;r._pilot_invocation=original_invocation;plain.forward=original_forward
  if hook is not None:hook.remove()
  r.publish_object=original_publish;r.common.publish=original_common_publish;r.common.write_json=original_write;r.artifacts._finish=original_finish

if __name__=='__main__':main()
