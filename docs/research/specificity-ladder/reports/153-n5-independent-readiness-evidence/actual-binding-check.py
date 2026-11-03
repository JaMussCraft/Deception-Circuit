from pathlib import Path
import json,hashlib,base64
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');G=W/'.superpowers/sdd/plan-a3/n5-mask-H200-launch-861f84a3938a';E=W/'docs/research/specificity-ladder/reports/153-n5-independent-readiness-evidence';P=G/'root-binding-proposal-23474289.json';x=json.loads(P.read_text());a=x['admission'];r=x['reservation'];m=x['mapping_successor'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();cfg=json.loads((G/'launch-config.json').read_text());O=Path(cfg['output_root'])
assert x['execution_authorized'] is False and x['actual_allocation_verified'] is False
assert a['id']=='a3-mask-N5-23474289' and a['reservation_ids']==['r-040'] and a['max_gpu_hours']==.75 and a['identity']['commit']==cfg['commit']
assert a['admission_sha256']==digest({k:v for k,v in a.items() if k!='admission_sha256'})
assert a['identity']==json.loads((O/'mask/prepared/payload.json').read_text())['identity']
assert a['upper_inventory_sha256']==json.loads((E/'review-detail-23473884.json').read_text())['inventories']['pilot']['inventory_sha256']
assert r['reservation_id']=='r-040' and r['admission_sha256']==a['admission_sha256'] and r['identity']==a['identity'] and r['allocation_contract']==a['allocation_contract']
assert m['generation']==4 and len(m['expected_entry_ids'])==40 and m['expected_entry_ids'][-1]=='r-040' and m['contingency_gpu_hours']==5.25
pred=m['predecessor_reference'];prior=json.loads((Path(pred['path'])/'payload.json').read_text());assert prior['generation']==3 and len(prior['expected_entry_ids'])==39
for n,v in pred['files'].items():assert sha(Path(pred['path'])/n)==v['sha256']
assert m['entries'][:-1]==prior['entries'] and m['original_admission_paths'][:-1]==prior['original_admission_paths'] and m['expected_entry_ids'][:-1]==prior['expected_entry_ids']
line=m['entries'][-1];assert line['reservation_id']=='r-040' and line['phase']=='M1' and line['subphase']=='masks' and line['original_reserved_gpu_hours']==.75
assert line['reservation_lineage']['admission_sha256']==a['admission_sha256'] and line['reservation_lineage']['mask_replacement_policy_sha256']==digest(a['mask_replacement_policy'])
raw=base64.b64decode(x['ledger_snapshot_bytes_base64']);assert hashlib.sha256(raw).hexdigest()==x['original_ledger_bytes_sha256']==m['ledger_sha256'];live=Path('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/ledger.json');assert raw==live.read_bytes()
rows={z['id']:z for z in json.loads(raw)['reservations']};new=rows['r-040'];assert str(new['job_id'])=='23474289' and new['account']=='beto-delta-gpu' and new['partition']=='gpuH200x8,gpuH200x8-interactive' and new['reserved_gpu_hours']==.75 and new['requested_minutes']==45 and new['source_commit']==cfg['commit'] and new['output_dir']==cfg['model_output']
assert all(new.get(k)==v for k,v in r['actual_entry'].items());assert all(rows['r-031'].get(k)==v for k,v in a['mask_replacement_policy']['original_reservation'].items())
held=dict(t.split('=',1) for t in (G/'held-job-23474289.txt').read_text().split() if '=' in t);assert held['JobId']=='23474289' and held['Reason']=='JobHeldUser' and held['JobState']=='PENDING' and held['Partition']=='gpuH200x8' and held['Requeue']=='0' and held['Restarts']=='0' and held['TimeLimit']=='00:45:00' and 'gres/gpu:h200=1' in held['ReqTRES']
v=dict(status='PASS_ACTUAL_HELD_BINDING_PROPOSAL',job_id='23474289',reservation_id='r-040',proposal_path=str(P),proposal_sha256=sha(P),held_record_sha256=sha(G/'held-job-23474289.txt'),source_commit=cfg['commit'],admission_sha256=a['admission_sha256'],generation=4,rows=40,prior39entries_exact=True,old_r031_full_charge_retained=True,actual_ledger_sha256=sha(live),final_real_object_references_and_root_release_still_required=True,no_execution_authority_granted=True,placeholder_refs_intentional=True)
(E/'actual-binding-verdict.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2));print('VERDICT_SHA',sha(E/'actual-binding-verdict.json'))
