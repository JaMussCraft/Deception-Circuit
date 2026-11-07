import copy, runpy, json
from collections import Counter
from component_analysis import a3_direction_workload as w
ns=runpy.run_path('tests/test_a3_direction_workload.py')
d,p,s=ns['fixture'](); p['workload']['axis_tile_size']=1
inv=w.build_inventory(d,p,stage='fit-select'); rs=ns['receipts'](inv); ld=ns['ledger'](inv)
ans=w.project_cost(rs,inv,ld)
print('capacity_underflow',json.dumps(dict(admitted=ans['admitted'],target_capture_disk=inv['bytes']['capture_disk'],target_projection_bytes=inv['bytes']['projection_blocks'],reported_cache_capacity=1,reported_memory_capacity=2,max_forecast_transient=max(inv['bytes'].values()))))
# Original envelope has no actual reservation/capture entries and zero amount consumed.
fits={'fit_records':[dict(task=t,site=['head',17,24],seed=seed,valid=True) for t in d['tasks'] for seed in w.SEEDS]}
post=w.build_inventory(d,p,stage='fit-select',fits=fits); l=ns['ledger'](post)
env=dict(kind='a3_fit_validation_envelope_v1',identity=post['identity'],upper_inventory=inv,max_gpu_hours=8,entry_ids=[])
env['envelope_sha256']=w.digest(env); l['fit_validation_envelope']=env
ans=w.project_cost(ns['receipts'](post),post,l)
print('empty_unreserved_envelope',json.dumps(dict(admitted=ans['admitted'],consumed=ans['fit_validation_consumed_gpu_hours'],entries=l['entries'])))
# Receipt with actual full comparison set, but every dummy proof stripped and rehashed.
i=ns['inventory']('fit-select'); receipts=ns['receipts'](i)
changed=0
for e in receipts[0]['packing_evidence'].values():
 if e is None: continue
 r=e['runner_receipt']; scope=r['scope']; dummy=sum(len(scope['recipients'][bid])*len(specs) for bid,specs in scope['dummy_cells'].items())
 if dummy:
  r['comparisons']=r['comparisons'][:-dummy]; scope['dummy_cells']={}; changed+=1
 r['scope_sha256']=w.digest(scope); r['receipt_sha256']=w.digest({k:v for k,v in r.items() if k!='receipt_sha256'})
a=w.project_cost(receipts,i,ns['ledger'](i))
print('dummy_proof_removed',json.dumps(dict(admitted=a['admitted'],stripped_evidence=changed)))
for stage in w.STAGES:
 iv=ns['inventory'](stage)
 print('inventory_count',stage,json.dumps(dict(rows=len(iv['expected_keys']),shards=len(iv['shards']),captures=len(iv['captures']),forwards=sum(iv['forward_counts'].values()),operations=iv['operation_counts'])))
# Independent cell arithmetic, not inventory's own counts.
N=2; U=2; V=2; Q=10*N+U+2*V
expected_remaining=9*((1+199+1)*Q + 2*2*(10*N+U) + 3*2*(10*N+U+V) + 33*Q)
actual=ns['inventory']('remaining'); assert len(actual['expected_keys'])==expected_remaining==56844
expected_shards_per_seed=(2*11+3)+(11+1)+(7*11+13)+(11+1)+2*11+3*(11+1)
assert len(actual['shards'])==9*expected_shards_per_seed==1773
assert all(actual['forward_counts'][op]==1773 for op in w.REPLAYS)
assert actual['forward_counts']['positive_control']==3*3*2*(10*N+U+V)==432
print('independent_remaining_oracle',json.dumps(dict(rows=expected_remaining,scoring_tiles=9*expected_shards_per_seed,scoring_forwards=5*9*expected_shards_per_seed,positive_forwards=432)))
# Envelope accepts an unrelated ledger entry in place of a bound capture/reservation.
l=ns['ledger'](post); l['entries']=[dict(id='unrelated',phase='M2',subphase='directions',state='completed',actual_gpu_hours=.01,inventory_sha256='f'*64)]; l['expected_entry_ids']=['unrelated']
env=dict(kind='a3_fit_validation_envelope_v1',identity=post['identity'],upper_inventory=inv,max_gpu_hours=8,entry_ids=['unrelated']); env['envelope_sha256']=w.digest(env); l['fit_validation_envelope']=env
ans=w.project_cost(ns['receipts'](post),post,l)
print('unrelated_envelope_entry',json.dumps(dict(admitted=ans['admitted'],consumed=ans['fit_validation_consumed_gpu_hours'],unrelated_inventory=l['entries'][0]['inventory_sha256'])))
