"""Publish a NONAUTHORIZING draft envelope, never a root execution admission."""
from job_common import CFG,W,B,O,C,sha,write,utc,allocation
from component_analysis import a3_direction_runtime as authority,a3_direction_workload as dw,a3_mask_workload as mw
import time,json
assert sha(CFG['approved_policy_path'])==CFG['approved_policy_sha256'];approved=json.loads(open(CFG['approved_policy_path']).read())
policy=dw.mask_replacement_policy();assert policy['approved_policy_sha256']==CFG['approved_policy_sha256'] and policy['original_reservation']==approved['original_reservation']
prepared=authority.read_object(O/'mask/prepared');pilot=authority.read_object(O/'mask/inventory-pilot');mw.validate_inventory(pilot);assert pilot['identity']==prepared['identity']
ledger=authority.normalize_ledger(CFG['original_mapping'],identity=prepared['identity'],include_envelope=False,refresh_deadline=time.time())
active=authority.read_object(ledger['active_mapping_reference']['path'])
assert active.get('generation',0)>=CFG['minimum_completed_mapping_generation'] and len(active['expected_entry_ids'])>=CFG['minimum_mapped_RS_rows']
sums=dw._ledger(ledger,prepared['identity']);authority.validate_global_budgets(ledger['entries'],contingency_remaining=sums['contingency_remaining'])
assert sums['mask_retry_gpu_hours']==0,'An actual additional mask attempt already exists; no new draft/reservation authorized'
contract=dict(kind='a3_allocation_contract_v1',scheduler_work_dir=str(B),source_commit=C,cpus=4,memory_bytes=68719476736,gpus=1,gpu_type='h200')
draft=dict(kind='a3_root_pilot_admission_v1',id='a3-mask-N5-prospective-'+C[:12],identity=prepared['identity'],upper_inventory_sha256=pilot['inventory_sha256'],max_gpu_hours=.75,reservation_ids=[],mask_replacement_policy=policy,allocation_contract=contract,execution_authorized=False)
draft['admission_sha256']=dw.digest(draft)
check=dw.validate_mask_replacement_admission(draft,ledger['entries']);assert check==dict(execution_authorized=False,reservation_bound=False)
envelope=dict(kind='a3_mask_replacement_prospective_admission_v1',commit=C,created_utc=utc(),draft_admission=draft,policy_check=check,approved_policy_reference=dict(path=CFG['approved_policy_path'],sha256=CFG['approved_policy_sha256']),original_mapping_reference=ledger['original_mapping_reference'],completed_active_mapping_reference=ledger['active_mapping_reference'],completed_mapping_generation=active['generation'],completed_mapping_RS_rows=len(active['expected_entry_ids']),mapping_lineage_references=ledger['mapping_lineage_references'],actual_canonical_ledger_sha256=ledger['snapshot_sha256'],actual_ledger_entries=ledger['entries'],pilot_inventory_reference=authority.object_reference(O/'mask/inventory-pilot'),full_target_reference=authority.object_reference(O/'mask/inventory-full'),future_output=str(O/'mask-pilot-1'),planned_host_allowance_bytes=60129542144,requested_minutes_max=45,finish_reserve_seconds=300,minimum_shard_seconds=60,execution_authorized=False,actual_reservation_bound=False,root_owned_finalization_required=True)
assert envelope['kind'] not in authority.ROOT_ADMISSION_KINDS
assert 'reservation' not in envelope
authority.publish_object(O/'prospective-admission',envelope)
write(O/'evidence/prospective-admission-check.json',dict(check=check,envelope_reference=authority.object_reference(O/'prospective-admission'),original_mapping_reference=ledger['original_mapping_reference'],completed_active_mapping_reference=ledger['active_mapping_reference'],actual_canonical_ledger_sha256=ledger['snapshot_sha256'],original_charge_retained=next(e['reserved_gpu_hours'] for e in ledger['entries'] if e['id']=='r-031'),models_loaded=False,execution_authorized=False))
print('PROSPECTIVE_POLICY_DRAFT_ONLY_NO_EXECUTION_ADMISSION')
