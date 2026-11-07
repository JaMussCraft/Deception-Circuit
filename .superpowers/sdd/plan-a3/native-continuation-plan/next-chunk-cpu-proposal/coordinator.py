"""UNEXECUTED Slurm CPU proposal: original cases5 through11, real allocation retained."""
from pathlib import Path
import argparse,hashlib,json,os,resource,time
START=5
COUNT=7
PRESERVED=5

def main():
 parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--root',required=True);parser.add_argument('--out',required=True);args=parser.parse_args()
 root=Path(args.root).resolve();out=Path(args.out).resolve();w=Path.cwd();began=time.perf_counter();phase='startup';forwards=[0];auth_active=[False];forbidden=[0];authenticated=[];native=[]
 catalog_path=Path(__file__).resolve().parents[1]/'source-and-cases.json';catalog=json.loads(catalog_path.read_text());assert root==Path(catalog['scenario_root']) and out.is_dir()
 from allocation_facts import read_current
 allocation=read_current(w,minimum_remaining_seconds=2475)
 expected=json.loads((out/'allocation-before.json').read_text());assert allocation['job_id']==expected['job_id'] and allocation['host']==expected['host'] and allocation['slurm_environment']==expected['slurm_environment']
 def write(name,value):
  with (out/name).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
 def mark(event,**extra):print(json.dumps(dict(event=event,elapsed_seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,observed_model_forward_calls=forwards[0],**extra)),flush=True)
 def step(name,fn):
  nonlocal phase
  phase=name;mark('step_start',step=name);start=time.perf_counter();value=fn();mark('step_end',step=name,step_seconds=time.perf_counter()-start);return value
 def sources():assert {name:hashlib.sha256((w/name).read_bytes()).hexdigest() for name in catalog['source_hashes']}==catalog['source_hashes']
 write('coordinator-allocation.json',allocation)
 allocation_ref=dict(path=str(out/'coordinator-allocation.json'),sha256=hashlib.sha256((out/'coordinator-allocation.json').read_bytes()).hexdigest())
 step('frozen_source_before',sources)
 write('driver-identity.json',dict(driver_path=str(Path(__file__).resolve()),driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),catalog_path=str(catalog_path),catalog_sha256=hashlib.sha256(catalog_path.read_bytes()).hexdigest(),source_hashes=catalog['source_hashes'],start=START,count=COUNT,slurm_allocation_reference=allocation_ref,actual_job_id=allocation['job_id'],actual_step_id=allocation['step_id'],execution_host=allocation['host'],scientific_execution=False,execution_authorized=False))
 mark('import_start')
 from tests import a3_direction_native_scenario as s
 from component_analysis import hooks
 mark('import_end')
 r=s.r;all_ids=[c['invocation_id'] for c in catalog['cases']];old_ids=all_ids[:PRESERVED];new_ids=all_ids[START:START+COUNT];assert START==PRESERVED and len(new_ids)==COUNT
 base=root/'pilot-verification-cases/selected';assert {p.name for p in base.iterdir()}==set(old_ids)
 assert not any((base/name).exists() for name in new_ids) and not list((root/'pilot-scratch').iterdir())
 old_refs=step('preserved_case_references',lambda:{name:r.object_reference(base/name) for name in old_ids})
 for name in ('scenario','tiny-model','selected','inventory/selected-pilot'):assert (root/name/'COMPLETE.json').is_file(),name
 design,protocol,model,plain=step('verify_scenario',lambda:s.verify_scenario(root))
 assert design['injected'] is True and s.model_identity(plain)['device']=='cpu'
 assert s.r.runtime_kernel_identity(model)['device_type']=='cpu'
 selected,_=step('read_selected',lambda:r.read_bundle(root/'selected'))
 inv=step('existing_inventory_canonical_rebuild_compare',lambda:s.inventory(root,design,protocol,'selected-pilot',selected=selected))
 invocations=inv['packing_invocations'] or r._serial_invocations(inv);assert [x['invocation_id'] for x in invocations]==all_ids and len(all_ids)==63
 binding=step('read_scenario_binding',lambda:r.read_object(root/'scenario'))
 assert not r._NUMERIC_BACKING_CACHE,'Fresh process-local numeric backing cache required'
 original_capture=hooks.capture_forward;original_invocation=r._pilot_invocation;original_read=s._read_pilot_case
 def counted(*a,**kw):
  if auth_active[0]:forbidden[0]+=1;raise RuntimeError('Unexpected model forward during original read-only case authentication')
  forwards[0]+=1;return original_capture(*a,**kw)
 def timed_invocation(_model,_design,_protocol,invocation,**kw):
  nonlocal phase
  assert not auth_active[0] and invocation['invocation_id']==new_ids[len(native)]
  phase='native:'+invocation['invocation_id'];before=forwards[0];start=time.perf_counter();mark('native_start',case_id=invocation['invocation_id'])
  value=original_invocation(_model,_design,_protocol,invocation,**kw)
  record=dict(case_id=invocation['invocation_id'],native_seconds=time.perf_counter()-start,actual_forward_calls=forwards[0]-before);native.append(record);mark('native_end',**record);return value
 def timed_read(path,*a,**kw):
  nonlocal phase
  name=Path(path).name;assert name==new_ids[len(authenticated)] and not auth_active[0]
  phase='authentication:'+name;before=forwards[0];start=time.perf_counter();cache_before=list(r._NUMERIC_BACKING_CACHE);auth_active[0]=True;mark('auth_start',case_id=name,numeric_backing_cache_roots=cache_before)
  try:value=original_read(path,*a,**kw)
  finally:auth_active[0]=False
  assert forwards[0]==before and forbidden[0]==0
  record=dict(case_id=name,authentication_seconds=time.perf_counter()-start,new_model_forwards=0,numeric_backing_cache_roots_before=cache_before,numeric_backing_cache_roots_after=list(r._NUMERIC_BACKING_CACHE));authenticated.append(record);mark('auth_end',**record)
  sidecar_start=time.perf_counter()
  write('slurm-case-'+name+'.json',dict(kind='actual_slurm_cpu_case_reference',actual_job_id=allocation['job_id'],actual_step_id=allocation['step_id'],host=allocation['host'],producer_pid=os.getpid(),allocation_reference=allocation_ref,case_reference=r.object_reference(path),authentication=record,native=next(x for x in native if x['case_id']==name),injected=True,scientific_execution=False,production_admission=False))
  mark('case_allocation_sidecar_published',case_id=name,actual_publication_and_reference_seconds=time.perf_counter()-sidecar_start)
  return value
 try:
  hooks.capture_forward=counted;r._pilot_invocation=timed_invocation;s._read_pilot_case=timed_read
  refs=step('original_pilot_cases_contiguous_chunk',lambda:s.pilot_cases(model,design,protocol,inv,root=root,part='selected',case_ids=new_ids,binding=binding,selected_path=root/'selected',resume=True))
  assert len(refs)==COUNT and [x['case_id'] for x in native]==new_ids==[x['case_id'] for x in authenticated]
  rows=[]
  for index,name in enumerate(new_ids):
   record=r.artifacts._strict_json(base/name/'case.json');assert record['original_case_forward_calls']==native[index]['actual_forward_calls']>0
   rows.append(dict(case_id=name,original_case_seconds=record['original_case_seconds'],original_case_forward_calls=record['original_case_forward_calls'],reference=r.object_reference(base/name)))
  assert sum(x['original_case_forward_calls'] for x in rows)==forwards[0] and forbidden[0]==0
  assert {name:r.object_reference(base/name) for name in old_ids}==old_refs
  assert {p.name for p in base.iterdir()}==set(old_ids+new_ids) and not list((root/'pilot-scratch').iterdir())
  assert s.model_identity(plain)==binding['model_identity']
  step('final_scenario_backing_check',lambda:s.verify_scenario(root,load_model=False));step('frozen_source_after',sources)
  write('coordinator-result.json',dict(kind='injected_native_slurm_cpu_chunk',actual_job_id=allocation['job_id'],actual_step_id=allocation['step_id'],execution_host=allocation['host'],slurm_allocation_reference=allocation_ref,prior_login_timings_are_planning_inputs_only=True,indices=list(range(START,START+COUNT)),new_native_case_count=COUNT,new_case_ids=new_ids,preserved_case_ids=old_ids,preserved_case_references_unchanged=True,actual_new_forward_calls=forwards[0],forbidden_auth_model_forwards=forbidden[0],native=native,authentication=authenticated,original_case_records=rows,full_pilot_complete=False,aggregate_executed=False,scientific_execution=False,execution_authorized=False,wall_seconds=time.perf_counter()-began));mark('coordinator_complete',case_ids=new_ids,full_pilot_complete=False)
 except BaseException as error:
  write('coordinator-failure.json',dict(phase=phase,error=repr(error),elapsed_seconds=time.perf_counter()-began,actual_observed_model_forward_calls=forwards[0],completed_full_authentication_ids=[x['case_id'] for x in authenticated],native=native,full_pilot_complete=False));raise
 finally:hooks.capture_forward=original_capture;r._pilot_invocation=original_invocation;s._read_pilot_case=original_read

if __name__=='__main__':main()
