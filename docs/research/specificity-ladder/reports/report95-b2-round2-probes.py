import copy,runpy,json
from component_analysis import a3_direction_workload as w
n=runpy.run_path('tests/test_a3_direction_workload.py')
inv,ledger=n['postfit_lineage_fixture'](); receipts=n['receipts'](inv)
def cost(l): return w.project_cost(receipts,inv,l)
def reject(name,l):
 try: cost(l)
 except ValueError as exc: print('REJECT',name,str(exc)); return
 raise AssertionError('unexpected admission '+name)
a=cost(ledger); assert a['admitted'] and not a['execution_authorized'] and a['fit_validation_consumed_gpu_hours']==.1
print('ACCEPT valid_anchor',json.dumps(dict(reserved=a['existing_reserved_gpu_hours'],actual=a['existing_actual_gpu_hours'],envelope_consumed=a['fit_validation_consumed_gpu_hours'])))
for state in ('completed','failed','running','reserved'):
 for reference in ('same_id_wrong_hash','wrong_id_same_hash','consistent_omitted','consistent_included_over_cap'):
  bad=copy.deepcopy(ledger)
  entry=copy.deepcopy(bad['entries'][0]); entry.update(id='later-attempt',state=state,reserved_gpu_hours=.49,actual_gpu_hours=.001,inventory_sha256=inv['inventory_sha256'])
  line=entry['reservation_lineage']; line.update(reservation_id=entry['id'],reserved_gpu_hours=.49,inventory_sha256=entry['inventory_sha256'])
  if reference=='same_id_wrong_hash': line['admission_sha256']='f'*64
  if reference=='wrong_id_same_hash': line['admission_id']='another-admission'
  line['lineage_sha256']=w.digest({k:v for k,v in line.items() if k!='lineage_sha256'})
  bad['entries'].append(entry); bad['expected_entry_ids'].append(entry['id'])
  if reference=='consistent_included_over_cap':
   envelope=bad['fit_validation_envelope']; envelope['entry_ids'].append(entry['id']); envelope['envelope_sha256']=w.digest({k:v for k,v in envelope.items() if k!='envelope_sha256'})
  reject(state+'_'+reference,bad)
# A different admission with different ID AND digest remains independent and
# still contributes its reserved amount globally; no false match is introduced.
bad=copy.deepcopy(ledger); entry=copy.deepcopy(bad['entries'][0]); entry.update(id='unrelated-attempt',reserved_gpu_hours=.07,actual_gpu_hours=.001,inventory_sha256='b'*64)
line=entry['reservation_lineage']; line.update(reservation_id=entry['id'],admission_id='distinct-original',admission_sha256='f'*64,inventory_sha256=entry['inventory_sha256'],reserved_gpu_hours=.07)
line['lineage_sha256']=w.digest({k:v for k,v in line.items() if k!='lineage_sha256'}); bad['entries'].append(entry); bad['expected_entry_ids'].append(entry['id'])
a=cost(bad); assert a['admitted'] and abs(a['existing_reserved_gpu_hours']-.17)<1e-12 and a['fit_validation_consumed_gpu_hours']==.1
print('ACCEPT distinct_admission',json.dumps(dict(all_reserved=a['existing_reserved_gpu_hours'],envelope_consumed=a['fit_validation_consumed_gpu_hours'])))
# A legitimate current running reservation is charged exactly once.
bad=copy.deepcopy(ledger); initial=cost(bad); entry=copy.deepcopy(bad['entries'][0]); amount=initial['projected_gpu_hours']; entry.update(id='validation',state='running',reserved_gpu_hours=amount,inventory_sha256=inv['inventory_sha256'])
line=entry['reservation_lineage']; line.update(reservation_id=entry['id'],reserved_gpu_hours=amount,inventory_sha256=entry['inventory_sha256']); line['lineage_sha256']=w.digest({k:v for k,v in line.items() if k!='lineage_sha256'})
bad['entries'].append(entry); bad['expected_entry_ids'].append(entry['id']); envelope=bad['fit_validation_envelope']; envelope['entry_ids'].append(entry['id']); envelope['envelope_sha256']=w.digest({k:v for k,v in envelope.items() if k!='envelope_sha256'})
a=cost(bad); assert a['additional_gpu_hours']==0 and abs(a['fit_validation_consumed_gpu_hours']-(.1+amount))<1e-12
print('ACCEPT matching_running_charged_once',json.dumps(dict(additional=a['additional_gpu_hours'],envelope_consumed=a['fit_validation_consumed_gpu_hours'])))
print('PASS 16 rejection cases and 3 valid boundary cases')
