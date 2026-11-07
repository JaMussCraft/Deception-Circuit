from pathlib import Path
import json,time,resource
from collections import defaultdict
from component_analysis import a3_direction_runtime as r
p=Path('/tmp/report97-joined-final/test_complete_real_tiny_inject0/study')
d=r.ladder.read_artifact(p/'design.json');pr=r.ladder.read_artifact(p/'direction_protocol.json');sel,_=r.read_bundle(p/'selected')
source_hashes={k:r.common.file_hash(Path(k)) for k in ('component_analysis/a3_direction_runtime.py','component_analysis/a3_direction_workload.py')}
start=time.perf_counter();full_calls=[0];verified_bytes=[0];hash_calls=[0]
original=r.workload._packing_evidence;original_hash=r.common.file_hash

def validate(*args,**kw):full_calls[0]+=1;return original(*args,**kw)
def hashed(path,*args,**kw):
    verified_bytes[0]+=Path(path).stat().st_size;hash_calls[0]+=1
    return original_hash(path,*args,**kw)
r.workload._packing_evidence=validate;r.common.file_hash=hashed
proofs=[r._CompletedPackingProof(path) for path in sorted((p/'pilot-evidence'/'selected').iterdir())]
numeric_start=time.perf_counter();backing=r._numeric_backing_proof(p/'selected',r.pipeline._bundle_byte_reference(p/'selected'),proofs[0].proof._profile,injected=True);numeric_seconds=time.perf_counter()-numeric_start
validated=time.perf_counter();inventory=r.workload.build_inventory(d,pr,stage='remaining',selected=sel)
profiles=defaultdict(list)
for proof in proofs:profiles[r.workload.digest(proof.proof._profile)].append(proof)
checked=0;missing=[];check_start=time.perf_counter();before_bytes=verified_bytes[0]
reconciliation=r._PilotReconciliationPass(proofs,inventory,guard=lambda:None,injected=True,extra_witnesses=(backing['witness'],))
with reconciliation:
    inventory=reconciliation.inventory
    for req in inventory['requirements']:
        if req['operation'].startswith('capture_') or req['profile']['axis_tile_size']==1 or not req['timing_inputs']:continue
        keys={(x['source_task'],x['condition'],x['stream'],x['instance_id']) for x in req['timing_inputs']}
        candidates=[x for x in profiles[r.workload.digest(req['profile'])] if keys.issubset(x.proof._rows) and x.proof.covers_axes(req['axis_scope'])]
        if not candidates:missing.append(req['requirement_id']);continue
        reconciliation.check(candidates[0],req);checked+=1
        if checked%2000==0:print('CHECKED',checked,flush=True)
reconciliation.before_publication()
result=dict(injected=True,old_source_evidence=True,scientific_execution=False,model_calls=0,
    source_hashes=source_hashes,atomic_reconciliation=True,numeric_backing_cost_only=True,numeric_backing_files=len(list((p/'selected').rglob('*.npy')))+2,numeric_backing_validation_seconds=numeric_seconds,
    atomic_verified_bytes=reconciliation.verified_bytes,atomic_verification_seconds=reconciliation.verification_seconds,
    full_numeric_validations=full_calls[0],receipt_references=len(proofs),target_requirements_checked=checked,missing=missing,
    raw_rows=len(inventory['expected_keys']),retained_index_bytes=sum(x.retained_bytes for x in proofs),
    construction_seconds=validated-start,target_check_seconds=time.perf_counter()-check_start,
    total_seconds=time.perf_counter()-start,verified_bytes=verified_bytes[0],target_verified_bytes=verified_bytes[0]-before_bytes,
    file_hash_calls=hash_calls[0],peak_host_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
Path('/tmp/report97-proof-atomic-scaling.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
assert not missing and checked==23040 and len(proofs)==63 and full_calls[0]==63
