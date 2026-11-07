"""CPU COMPONENT diagnosis only: never validates/mints execution authority."""
import os,sys,json,time,resource,subprocess,hashlib,gc
from pathlib import Path
D=Path(__file__).resolve().parent
B=json.loads((D/'source-and-budget-binding.json').read_text())
assert os.environ.get('SLURM_JOB_ID','').isdigit() and os.environ.get('CUDA_VISIBLE_DEVICES')==''
OUT=D/'execution'
OUT.mkdir(exist_ok=False)
R=Path(B['old_source']); C=Path(B['candidate_source']); A=Path(B['original_authority'])
for f,v in B['module_agreement'].items():
 assert v['same_bytes'] and hashlib.sha256((R/f).read_bytes()).hexdigest()==v['sha256']==hashlib.sha256((C/f).read_bytes()).hexdigest()
sys.path.insert(0,str(R));os.chdir(R)
from component_analysis import a3_direction_runtime as auth,a3_mask_workload as mw,a3_direction_workload as dw
assert all(Path(m.__file__).resolve().is_relative_to(R) for m in [auth,mw,dw])
records=[]
def run(name,fn,*,optional=False):
 start=time.perf_counter();cpu=time.process_time()
 try:
  result=fn();row={'name':name,'status':'PASS','wall_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu,'maxrss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
 except Exception as ex:
  row={'name':name,'status':'REFUSED','wall_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu,'error_type':type(ex).__name__,'error':str(ex)}
  records.append(row);(OUT/'components.json').write_text(json.dumps(records,indent=2)+'\n')
  if not optional:raise
  return None
 records.append(row);(OUT/'components.json').write_text(json.dumps(records,indent=2)+'\n');return result
# Real CPU scheduler evidence, not a GPU adapter or allocation authority.
for i in range(6):
 def query():
  p=subprocess.run(['scontrol','-o','show','job',os.environ['SLURM_JOB_ID']],capture_output=True,text=True,check=True,timeout=15,env=dict(os.environ,TZ='UTC'))
  (OUT/f'actual-cpu-scontrol-{i}.txt').write_text(p.stdout)
  fields=dict(x.split('=',1) for x in p.stdout.split() if '=' in x)
  assert fields['JobState']=='RUNNING' and fields['JobId']==os.environ['SLURM_JOB_ID']
  assert not any('gres/gpu=' in fields.get(k,'') for k in ['AllocTRES','TRES'])
  return fields
 facts=run(f'actual_CPU_scheduler_RPC_{i}',query)
reservation=run('read_original_reservation',lambda:auth.read_object(A/'reservation'))
admission=run('read_original_admission',lambda:auth.read_object(A/'admission'))
assert reservation['actual_entry']['id']=='r-031'
assert reservation['actual_entry']['source_commit']==B['old_source_commit']
assert reservation['identity']==admission['identity']
assert auth.object_reference(A/'admission')==reservation['admission_reference']
upper=run('read_original_upper_pilot_inventory',lambda:auth.read_object(reservation['upper_inventory_path']))
run('validate_original_upper_pilot_inventory',lambda:mw.validate_inventory(upper))
upper_keys=run('original_authority_key_hash_proof',lambda:frozenset(dw.digest(k) for k in upper['expected_keys']))
run('original_reservation_allocation_contract_STATIC_ONLY',lambda:auth.validate_allocation_contract(reservation['allocation_contract'],reservation['actual_entry'],upper,injected=False))
# Actual production mapping APIs; unknown/stale/missing live facts refuse, never patched.
chain=None
for i in range(3):
 got=run(f'genuine_mapping_chain_{i}',lambda:auth._mapping_chain(A/'mapping'))
 if chain is None:chain=got
for i in range(3):
 run(f'actual_canonical_normalize_ledger_{i}',lambda:auth.normalize_ledger(A/'mapping',identity=upper['identity'],include_envelope=False,refresh_deadline=time.time()),optional=True)
# Low-level static witness component with authentic roots, not a forged authority context.
origin=auth.read_object(A/'mapping');roots=[A/'reservation',reservation['admission_path'],reservation['upper_inventory_path'],A/'mapping',chain[0]['ledger_snapshot_path']]
roots.extend(x['path'] for x in chain[2]);roots.extend(origin['original_admission_paths'])
roots.append(reservation['upper_inventory_path']) # real context inventory_path occurrence, retained even if duplicate
witness=run('original_authority_static_witness_construction',lambda:auth._make_file_witness(roots))
for i in range(3):run(f'original_authority_static_witness_refresh_{i}',lambda:auth._check_file_witness(witness))
inventory_bytes=run('inventory_retained_and_walk_bytes',lambda:auth._retained_json_bytes(upper))
frozen=run('original_pilot_recursive_owned_freeze',lambda:auth._freeze_json(upper))
proof_bytes=run('representative_retained_proof_walk',lambda:auth._retained_json_bytes([upper_keys,reservation,dict(identity=upper['identity'],inventory_sha256=upper['inventory_sha256']),frozen]))
# Actual new full target proof used before model access in the repaired pilot.
target=run('new_full_target_read',lambda:auth.read_object(B['new_target_inventory']))
assert target['identity']['commit']==B['candidate_commit'] and target['stage']=='full'
run('new_full_target_complete_validator',lambda:mw.validate_inventory(target))
keys=run('new_full_target_recursive_frozenset_proof',lambda:frozenset(map(dw._freeze,target['expected_keys'])))
assert len(keys)==len(target['expected_keys'])
summary={'status':'COMPONENT_DIAGNOSIS_COMPLETE','job_id':os.environ['SLURM_JOB_ID'],'source_modules_byte_identical':True,'authority_source':str(R),'target_source':str(C),'original_upper_keys':len(upper_keys),'inventory_retained_and_walk_bytes':inventory_bytes,'representative_retained_and_walk_bytes':proof_bytes,'witness_roots':[str(p) for p in roots],'new_full_target_keys':len(keys),'components':records,'production_live_admission_succeeded':False,'production_authority_context_minted':False,'execution_authorized':False,'models_or_weights_loaded':False,'guards_disabled_or_mocked':False,'scope':'Disjoint genuine-input components and actual CPU scheduler queries; not a full valid GPU path, not additive total forecast. Optional normalize_ledger refusals are preserved.'}
(OUT/'component-diagnosis.json').write_text(json.dumps(summary,indent=2)+'\n')
print('COMPONENT_DIAGNOSIS_COMPLETE')
