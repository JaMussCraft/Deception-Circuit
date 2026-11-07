import copy,json,tempfile
from pathlib import Path
from component_analysis import a3_direction_runtime as r, a3_direction_workload as w
from tests.test_a3_direction_workload import fixture,receipts,ledger

d,p,s=fixture();d['injected']=False;p['task_order']=list(d['tasks'])
p['numeric_profile']=dict(dtype='bfloat16',backend='native');p['workload']['vocabulary_size']=8
for task,spec in d['tasks'].items():
    spec['assessment_ids']=[task+'a'+str(i) for i in range(100)]
for task,n in [('ioi',100),('mmlu',32)]:
    old=d['utility'][task];d['utility'][task]=[dict(copy.deepcopy(old[0]),instance_id=task+'a'+str(i)) for i in range(n)]
for task,n in [('ioi',100),('mmlu',32)]:
    old=d[task+'_validation'];d[task+'_validation']=[dict(copy.deepcopy(old[0]),instance_id=task+'v'+str(i)) for i in range(n)]
inv=w.build_inventory(d,p,stage='fit-select')
rr=receipts(inv);baseline=w.project_cost(copy.deepcopy(rr),inv,ledger(inv));bad=rr[0]
bad.update(injected=True,actual_execution=False,job_id='injected-cpu',part='wrong-stage',source_split='assessment',runtime={'device':'cpu'},pilot_inventory_sha256='0'*64)
for m in bad['measurements']:m['batch_seconds']=[1e-9]*len(m['batch_seconds'])
with tempfile.TemporaryDirectory(prefix='review111-cost-') as tmp:
    path=Path(tmp)/'receipt';r.publish_object(path,bad)
    completed=r.read_object(path)
    proofs=r._cost_packing_proofs([completed])
    result=w.project_cost([completed],inv,ledger(inv),packing_proofs=proofs)
    out=dict(baseline_projected_seconds=baseline['projected_seconds'],baseline_projected_gpu_hours=baseline['projected_gpu_hours'],target_injected=inv['injected'],receipt_injected=completed['injected'],receipt_actual_execution=completed['actual_execution'],receipt_job=completed['job_id'],receipt_source_split=completed['source_split'],receipt_part=completed['part'],resolved_numeric_proofs=len(proofs),accepted=result['admitted'],execution_authorized=result['execution_authorized'],projected_seconds=result['projected_seconds'],projected_gpu_hours=result['projected_gpu_hours'],note='Synthetic counterexample only; no model, scheduler or production evidence.')
    print(json.dumps(out,indent=2))
