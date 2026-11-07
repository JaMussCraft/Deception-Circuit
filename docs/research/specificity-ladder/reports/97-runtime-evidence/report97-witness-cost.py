from pathlib import Path
import time,json,resource
from component_analysis import a3_direction_runtime as r
paths=[Path('/tmp/report97-final-delta-mgnp/test_genuine_completed_root_au0/upper'),Path('/tmp/report97-final-delta-mgnp/test_genuine_completed_root_au0/admission'),Path('/tmp/report97-joined-final/test_complete_real_tiny_inject0/study/inventory/upper')]
verified=[0];calls=[0];original=r.common.file_hash

def hashed(path,*a,**k):
    verified[0]+=Path(path).stat().st_size;calls[0]+=1;return original(path,*a,**k)
r.common.file_hash=hashed
for path in paths:r.read_object(path)
start=time.perf_counter();w=r._make_file_witness(paths);initial=time.perf_counter()-start
samples=[];before=verified[0]
for _ in range(10):
    start=time.perf_counter();r._check_file_witness(w);samples.append(time.perf_counter()-start)
result=dict(injected=True,scientific_execution=False,model_calls=0,paths=list(map(str,paths)),note='actual completed injected mask upper/original-root admission and old-source tiny direction upper; no production extrapolation',
    integrity_initialization_seconds=initial,guard_check_seconds=samples,verified_bytes=verified[0],guard_verified_bytes=verified[0]-before,
    hash_calls=calls[0],peak_host_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
Path('/tmp/report97-witness-cost.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
