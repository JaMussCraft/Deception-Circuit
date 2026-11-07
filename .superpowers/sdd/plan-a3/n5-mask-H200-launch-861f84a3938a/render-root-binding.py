"""Read-only root binding PROPOSAL renderer. Never publishes authority/RS/jobs."""
import json,sys,os,hashlib,argparse,time,copy,base64
from pathlib import Path
G=Path(__file__).resolve().parent;cfg=json.loads((G/'launch-config.json').read_text());B=Path(cfg['runtime']);O=Path(cfg['output_root']);A=Path(cfg['authority_root'])
def check_held_request(facts,job_id,account):
    assert facts['JobId']==job_id and facts['JobState']=='PENDING' and facts['Reason']=='JobHeldUser'
    assert account==cfg['account'] and facts['Account']==account and set(facts['Partition'].split(','))<=set(cfg['allowed_partitions']) and Path(facts['WorkDir']).resolve()==B
    assert facts['RunTime']=='00:00:00' and int(facts['NumCPUs'])>=4 and facts['TimeLimit']=='00:45:00'
    assert facts.get('Requeue')=='0' and facts.get('Restarts')=='0'
    tres=dict(x.split('=',1) for x in facts.get('ReqTRES',facts.get('TRES','')).split(',') if '=' in x)
    assert tres.get('cpu')=='4' and authority._slurm_memory_bytes(tres.get('mem',''))==cfg['memory_bytes']
    assert tres.get('gres/gpu')=='1' and all(v=='1' for k,v in tres.items() if k.startswith('gres/gpu:'))
    assert Path(facts['Command']).resolve()==(G/'jobscript.sh').resolve()
    return True

p=argparse.ArgumentParser();p.add_argument('--job-id',required=True);p.add_argument('--reservation-id',required=True);p.add_argument('--account',required=True);p.add_argument('--held-job-record',required=True);args=p.parse_args()
sys.path.insert(0,str(B))
from component_analysis import a3_direction_runtime as authority,a3_direction_workload as dw,a3_mask_workload as mw
assert (O/'run_manifest.json').is_file() and json.loads((O/'run_manifest.json').read_text())['complete'] is True
prepared=authority.read_object(O/'mask/prepared');pilot=authority.read_object(O/'mask/inventory-pilot');mw.validate_inventory(pilot)
envelope=authority.read_object(O/'prospective-admission');assert envelope['kind']=='a3_mask_replacement_prospective_admission_v1' and envelope['execution_authorized'] is False
assert prepared['identity']==pilot['identity'] and prepared['identity']['commit']==cfg['commit']
prior,prior_path,chain=authority._mapping_chain(cfg['mapping_origin'])
ledger_path=Path(prior['ledger_path']);raw=ledger_path.read_bytes();ledger=json.loads(raw);rows={x['id']:x for x in ledger['reservations']}
assert set(rows)==set(prior['expected_entry_ids'])|{args.reservation_id}
for old in prior['entries']:
    assert all(rows[old['reservation_id']].get(k)==old['actual_entry'].get(k) for k in authority.RESERVATION_FIELDS)
new=rows[args.reservation_id];assert str(new['job_id'])==args.job_id and new['source_commit']==cfg['commit'] and new['output_dir']==cfg['model_output']
assert new['account']==args.account and new['partition']==cfg['partition'] and new['gpus']==1 and new['requested_minutes']==45 and new['reserved_gpu_hours']==.75
assert str(new['status']).lower() in ('pending','reserved') and new.get('actual_seconds') in (None,0)
facts=dict(s.split('=',1) for s in Path(args.held_job_record).read_text().split() if '=' in s)
assert check_held_request(facts,args.job_id,args.account)
# Pending request evidence is not live GPU admission; canonical loader rechecks RUNNING hardware/lease.
contract=dict(kind='a3_allocation_contract_v1',scheduler_work_dir=str(B),source_commit=cfg['commit'],cpus=4,memory_bytes=cfg['memory_bytes'],gpus=1,gpu_type='h200')
admission=dict(envelope['draft_admission'],id='a3-mask-N5-'+args.job_id,reservation_ids=[args.reservation_id],allocation_contract=contract,
    purpose='validation_timing',may_select_checkpoint=False,full_target_reference=envelope['full_target_reference'],minimum_shard_seconds=60,finish_reserve_seconds=300,
    prospective_envelope_reference=authority.object_reference(O/'prospective-admission'))
admission.pop('admission_sha256',None);admission['admission_sha256']=dw.digest(admission)
line=dict(admission_id=admission['id'],admission_sha256=admission['admission_sha256'],upper_inventory_sha256=pilot['inventory_sha256'],max_gpu_hours=.75,reserved_gpu_hours=.75,mask_replacement_policy_sha256=dw.digest(admission['mask_replacement_policy']))
newmap=dict(reservation_id=args.reservation_id,experiment='A3',phase='M1',subphase='masks',inventory_sha256=pilot['inventory_sha256'],original_reserved_gpu_hours=.75,actual_entry={k:new.get(k) for k in authority.RESERVATION_FIELDS},reservation_lineage=line)
normalized=[]
for row in prior['entries']+[newmap]:
    if row['experiment']!='A3':continue
    actual=rows[row['reservation_id']];state=str(actual['status']).lower();state={'pending':'reserved','cancelled':'failed','timeout':'failed','out_of_memory':'failed'}.get(state,state)
    normalized.append(dict(id=row['reservation_id'],phase=row['phase'],subphase=row['subphase'],state=state,reserved_gpu_hours=row['original_reserved_gpu_hours'],actual_gpu_hours=None if actual.get('actual_seconds') is None else actual['actual_seconds']*actual['gpus']/3600,actual_entry=actual,reservation_lineage=row['reservation_lineage']))
assert dw.mask_retry_gpu_hours(normalized,admissions=[admission])==.75
assert dw.validate_mask_replacement_admission(admission,normalized)['reservation_bound'] is True
authority.validate_global_budgets(normalized,contingency_remaining=5.25)
st=os.statvfs(O);free=st.f_bavail*st.f_frsize;pool='projects-device-'+str(O.stat().st_dev)
capacities={t:dict(pool=pool,available_bytes=free,path=str(O)) for t in ['cache_disk','output_disk','scratch_disk']};capacities['host_ram']=dict(pool='reserved-slurm-host',available_bytes=cfg['host_allowance_bytes'],basis='64GiB requested contract less8GiB allowance; actualallocationnotverified')
assert hashlib.sha256((O/'evidence/mask-validation.json').read_bytes()).hexdigest()==cfg['expected_mask_validation_sha256']
assert hashlib.sha256((O/'evidence/complete-artifact-manifest.json').read_bytes()).hexdigest()==cfg['expected_artifact_manifest_sha256']
validated=json.loads((O/'evidence/mask-validation.json').read_text());required={}
for tier,n in validated['inventories']['full']['storage_requirements']['tiers'].items():required[capacities[tier]['pool']]=required.get(capacities[tier]['pool'],0)+n
assert all(min(v['available_bytes'] for v in capacities.values() if v['pool']==pool)>=n for pool,n in required.items())
successor=copy.deepcopy(prior);successor.update(generation=prior.get('generation',0)+1,predecessor_reference=authority.object_reference(prior_path),ledger_snapshot_path=str(A/'ledger-after-new-reservation.json'),ledger_sha256=hashlib.sha256(raw).hexdigest(),expected_entry_ids=[r['id'] for r in ledger['reservations']],contingency_gpu_hours=5.25,storage_capacities=capacities)
successor['entries'].append(newmap);successor['original_admission_paths'].append(str(A/'admission'))
# Final admission reference depends on its root publication; root must fill it with object_reference(A/admission).
successor['original_admission_references'][str(A/'admission')]='ROOT_FILL_AFTER_FINAL_ADMISSION_PUBLICATION'
reservation=dict(kind='a3_root_execution_reservation_v1',identity=pilot['identity'],inventory_sha256=pilot['inventory_sha256'],reservation_id=args.reservation_id,actual_entry={k:new.get(k) for k in authority.RESERVATION_FIELDS},admission_path=str(A/'admission'),admission_reference='ROOT_FILL_AFTER_FINAL_ADMISSION_PUBLICATION',admission_sha256=admission['admission_sha256'],upper_inventory_path=str(O/'mask/inventory-pilot'),allocation_contract=contract,minimum_shard_seconds=60)
print(json.dumps(dict(kind='a3_mask_N5_root_binding_proposal_v1',execution_authorized=False,actual_allocation_verified=False,authority_publication_required=True,admission=admission,reservation=reservation,mapping_successor=successor,planned_successor_path=str(Path(prior['successor_directory'])/('mapping-%06d'%successor['generation'])),original_ledger_bytes_sha256=hashlib.sha256(raw).hexdigest(),ledger_snapshot_bytes_base64=base64.b64encode(raw).decode('ascii'),storage_pool_required=required,source_commit=cfg['commit']),indent=2))
