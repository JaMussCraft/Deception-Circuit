from pathlib import Path
import json,time,resource
from component_analysis import a3_direction_runtime as r
p=Path('/tmp/report97-joined-accepted/test_complete_real_tiny_inject0/study')
source={name:r.common.file_hash(name) for name in ('component_analysis/a3_direction_runtime.py','component_analysis/a3_direction_workload.py')}
start=time.perf_counter()
paths=sorted((p/'pilot-evidence'/'selected').iterdir())
proofs=[r._CompletedPackingProof(path) for path in paths]
validated=time.perf_counter()
backing=r._make_file_witness([p/'selected'])
index=r._PackingCandidateIndex(proofs,extra_witnesses=(backing,),startup_seconds=validated-start)
proof=proofs[47];scope=list(proof.proof._specs.values())[:2]
original=r._file_tree_identity;calls=[]
def counted(path):
    calls.append(str(path));return original(path)
r._file_tree_identity=counted
lookup_start=time.perf_counter()
for _ in range(100):
    assert proof in index.candidates(proof.proof._profile,scope,runtime_profile=proof.metadata.get('runtime_profile'))
lookup_seconds=time.perf_counter()-lookup_start
assert calls==[]
live=[];guard=r._DependencyGuard(lambda:live.append(1),index)
for _ in range(3):guard()
assert len(calls)==len(index.forest.paths)*3 and len(live)==guard.calls==index.forest.refreshes==3
result=dict(injected=True,scientific_execution=False,execution_authorized=False,model_calls=0,
 historical_input_only=True,source_hashes=source,proof_count=len(proofs),selected_files=sum(x[0]=='file' for x in backing.identities[0]),
 construction_seconds=validated-start,index_seconds=index.index_seconds,startup_seconds=index.startup_seconds,
 retained_index_bytes=index.retained_bytes,lookup_count=100,lookup_seconds=lookup_seconds,lookup_file_tree_calls=0,
 forest_roots=len(index.forest.paths),boundary_count=guard.calls,live_checks=len(live),tree_calls=len(calls),
 verified_bytes=index.forest.verified_bytes,boundary_seconds=guard.elapsed_seconds,
 peak_host_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,total_seconds=time.perf_counter()-start)
assert result['proof_count']==63 and result['selected_files']==8394
print(json.dumps(result,sort_keys=True),flush=True)
