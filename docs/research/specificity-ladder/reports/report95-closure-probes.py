import copy, runpy, json
from component_analysis import a3_direction_workload as w
n=runpy.run_path('tests/test_a3_direction_workload.py')
def rejected(name,fn):
 try: fn()
 except ValueError as exc: print('REJECT',name,str(exc)); return
 raise AssertionError('admitted '+name)
inv=n['serial_inventory'](); baseline=w.project_cost(n['receipts'](inv),inv,n['ledger'](inv))
assert baseline['admitted'] and not baseline['execution_authorized']
print('BASELINE',json.dumps(inv['storage_requirements']['tiers'],sort_keys=True))
r=n['receipts'](inv)
for m in r[0]['measurements']: m['cache_capacity_bytes']=1
rejected('cachecapacity1',lambda:w.project_cost(r,inv,n['ledger'](inv)))
for tier in inv['storage_requirements']['tiers']:
 l=n['ledger'](inv); l['storage_capacities'][tier]['available_bytes']=1
 rejected('tier1_'+tier,lambda:w.project_cost(n['receipts'](inv),inv,l))
l=n['ledger'](inv); r=n['receipts'](inv); r[0]['host_peak_bytes']=17
for t,v in inv['storage_requirements']['tiers'].items(): l['storage_capacities'][t]['available_bytes']=v+(17 if t=='host_ram' else 0)
a=w.project_cost(r,inv,l); assert a['admitted']; print('ACCEPT','exact_tier_plus_host_peak')
l['storage_capacities']['host_ram']['available_bytes']-=1
rejected('one_byte_short_host_plus_peak',lambda:w.project_cost(r,inv,l))
l=n['ledger'](inv); tiers=inv['storage_requirements']['tiers']; need=tiers['cache_disk']+tiers['output_disk']+tiers['scratch_disk']
for t in ('cache_disk','output_disk','scratch_disk'): l['storage_capacities'][t]=dict(pool='one-disk',available_bytes=need)
assert w.project_cost(n['receipts'](inv),inv,l)['admitted']; print('ACCEPT','exact_shared_disk_pool')
for t in ('cache_disk','output_disk','scratch_disk'): l['storage_capacities'][t]['available_bytes']-=1
rejected('shared_disk_one_byte_short',lambda:w.project_cost(n['receipts'](inv),inv,l))
post,l=n['postfit_lineage_fixture'](); a=w.project_cost(n['receipts'](post),post,l); assert a['fit_validation_consumed_gpu_hours']==.1
print('ACCEPT','original_anchor_reserved0.1_actual0.01')
for field,value in [('entry_ids',[]),('max_gpu_hours',8),('admission_sha256','f'*64)]:
 bad=copy.deepcopy(l); e=bad['fit_validation_envelope']; e[field]=value; e['envelope_sha256']=w.digest({k:v for k,v in e.items() if k!='envelope_sha256'})
 rejected('envelope_'+field,lambda:w.project_cost(n['receipts'](post),post,bad))
# All state reservations remain charged; low actual is not cap credit.
for state in ('completed','failed','running','reserved'):
 ll=n['ledger'](inv); ll['entries']=[dict(id='old',phase='M2',subphase='directions',state=state,reserved_gpu_hours=9,actual_gpu_hours=.001)]; ll['expected_entry_ids']=['old']
 rejected('no_refund_'+state,lambda:w.project_cost(n['receipts'](inv),inv,ll))
# Additional linked attempts cannot be hidden from the original envelope.
for state in ('completed','failed','running','reserved'):
 bad=copy.deepcopy(l); entry=copy.deepcopy(bad['entries'][0]); entry.update(id='later',state=state,reserved_gpu_hours=.49,actual_gpu_hours=.001,inventory_sha256=post['inventory_sha256'])
 line=entry['reservation_lineage']; line.update(reservation_id='later',reserved_gpu_hours=.49,inventory_sha256=post['inventory_sha256']); line['lineage_sha256']=w.digest({k:v for k,v in line.items() if k!='lineage_sha256'})
 bad['entries'].append(entry); bad['expected_entry_ids'].append('later')
 rejected('omitted_linked_'+state,lambda:w.project_cost(n['receipts'](post),post,bad))
 # Corrupt linkage must not silently classify the same admission ID as unrelated.
 line['admission_sha256']='f'*64; line['lineage_sha256']=w.digest({k:v for k,v in line.items() if k!='lineage_sha256'})
 try:
  out=w.project_cost(n['receipts'](post),post,bad)
  print('ADMITTED_BAD_SAME_ADMISSION_ID',state,json.dumps(dict(envelope_consumed=out['fit_validation_consumed_gpu_hours'],all_reserved=out['existing_reserved_gpu_hours'])))
 except ValueError as exc: print('REJECT','wrong_hash_same_admission_id_'+state,str(exc))
# Preserve complete full-tile proof while removing every dummy experiment.
i=n['inventory'](); r=n['receipts'](i); changed=0
for evidence in r[0]['packing_evidence'].values():
 if evidence is None: continue
 rr=evidence['runner_receipt']; scope=rr['scope']; count=sum(len(scope['recipients'][b])*len(c) for b,c in scope['dummy_cells'].items())
 rr['comparisons']=rr['comparisons'][:-count]; scope['dummy_cells']={}; changed+=1
 rr['scope_sha256']=w.digest(scope); rr['receipt_sha256']=w.digest({k:v for k,v in rr.items() if k!='receipt_sha256'})
rejected('all_dummy_experiments_removed_'+str(changed),lambda:w.project_cost(r,i,n['ledger'](i)))
