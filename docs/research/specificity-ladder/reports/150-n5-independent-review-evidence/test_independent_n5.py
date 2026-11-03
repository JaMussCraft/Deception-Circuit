"""Independent approved-policy probes. Software fixtures only; no model authority."""
import copy,json,pathlib,os
import pytest
E=pathlib.Path(__file__).resolve().parent

def case(hours=.75,state='reserved'):
    from component_analysis import a3_direction_workload as w
    approved=json.loads((E/'approved-policy.json').read_text());old_admission=json.loads((E/'genuine-original-admission.json').read_text())
    policy=w.mask_replacement_policy();assert policy['original_reservation']==approved['original_reservation']
    original=dict(id='r-031',phase='M1',subphase='masks',state='failed',reserved_gpu_hours=.75,actual_gpu_hours=0,
        actual_entry=copy.deepcopy(approved['original_reservation']),reservation_lineage=dict(admission_id=old_admission['id'],admission_sha256=old_admission['admission_sha256'],upper_inventory_sha256=old_admission['upper_inventory_sha256'],max_gpu_hours=.75,reserved_gpu_hours=.75))
    # Assemble the real original admission schema, prospectively, with no new row.
    proposed=copy.deepcopy(old_admission);proposed.update(id='independent150-prospective-mask',identity=dict(commit='1'*40),upper_inventory_sha256='2'*64,reservation_ids=[],max_gpu_hours=.75,mask_replacement_policy=policy)
    proposed.update(full_target_inventory_sha256='6'*64,root_preflight_sha256='7'*64)
    proposed['allocation_contract']=dict(proposed['allocation_contract'],source_commit='1'*40)
    proposed['admission_sha256']=w.digest({k:v for k,v in proposed.items() if k!='admission_sha256'})
    actual=dict(id='independent150-new',job_id='99999999150',cluster='delta',account='software-only',partition='gpuH200x8',gpus=1,requested_minutes=hours*60,reserved_gpu_hours=hours,source_commit='1'*40,output_dir='/tmp/independent150-new-output',manifest_hash=None,status='RUNNING',actual_seconds=None)
    linked=copy.deepcopy(proposed);linked['reservation_ids']=[actual['id']];linked['admission_sha256']=w.digest({k:v for k,v in linked.items() if k!='admission_sha256'})
    new=dict(id=actual['id'],phase='M1',subphase='masks',state=state,reserved_gpu_hours=hours,actual_gpu_hours=None,actual_entry=actual,
        reservation_lineage=dict(admission_id=linked['id'],admission_sha256=linked['admission_sha256'],upper_inventory_sha256=linked['upper_inventory_sha256'],max_gpu_hours=.75,reserved_gpu_hours=hours,mask_replacement_policy_sha256=w.digest(policy)))
    return w,original,proposed,new,linked

def ledger(w,old,new,admission):
    return dict(kind='a3_root_ledger_snapshot_v1',root_supplied=True,snapshot_sha256='3'*64,current_snapshot_sha256='3'*64,age_seconds=0,max_age_seconds=900,expected_identity=admission['identity'],entries=[old]+([] if new is None else [new]),expected_entry_ids=[old['id']]+([] if new is None else [new['id']]),original_admissions=[] if new is None else [admission],contingency_gpu_hours=5.25)

def test_actual_approval_and_genuine_original_lineage_prospective_order(tmp_path):
    from component_analysis import a3_direction_runtime as r
    w,old,proposed,new,linked=case()
    result=w.validate_mask_replacement_admission(proposed,[old]);assert result==dict(execution_authorized=False,reservation_bound=False)
    # Completed prospective bytes can exist before a new actual RS row/mapping;
    # policy validation still cannot fabricate that row or grant execution.
    r.publish_object(tmp_path/'prospective',proposed);assert r.read_object(tmp_path/'prospective')==proposed
    assert w._ledger(ledger(w,old,None,proposed),proposed['identity'])['mask_retry_gpu_hours']==0
    assert w.mask_retry_gpu_hours([old,new],admissions=[linked])==.75
    assert w.validate_mask_replacement_admission(linked,[old,new])==dict(execution_authorized=False,reservation_bound=True)
    assert old['reserved_gpu_hours']==.75 and old['actual_entry']['status']=='CANCELLED'

@pytest.mark.parametrize('fault',['source','job','output','hours','actual_seconds','status','admission','inventory','phase','subphase','missing','duplicate'])
def test_original_anchor_cannot_be_reclaimed_or_relabelled(fault):
    w,old,proposed,new,linked=case()
    if fault=='source':old['actual_entry']['source_commit']='4'*40
    elif fault=='job':old['actual_entry']['job_id']='123'
    elif fault=='output':old['actual_entry']['output_dir']='/tmp/retargeted-original'
    elif fault=='hours':old['reserved_gpu_hours']=0
    elif fault=='actual_seconds':old['actual_entry']['actual_seconds']=1
    elif fault=='status':old['actual_entry']['status']='PENDING'
    elif fault=='admission':old['reservation_lineage']['admission_sha256']='4'*64
    elif fault=='inventory':old['reservation_lineage']['upper_inventory_sha256']='4'*64
    elif fault=='phase':old['phase']='M5'
    elif fault=='subphase':old['subphase']='edges'
    entries=[new] if fault=='missing' else [old,copy.deepcopy(old),new] if fault=='duplicate' else [old,new]
    if fault=='missing':
        assert w.mask_retry_gpu_hours(entries,admissions=[linked])==0
        with pytest.raises(ValueError):w.validate_mask_replacement_admission(linked,entries)
    else:
        with pytest.raises(ValueError):w.mask_retry_gpu_hours(entries,admissions=[linked])

@pytest.mark.parametrize('state',['reserved','running','completed','failed'])
@pytest.mark.parametrize('hours',[.01,.25,.75])
def test_every_first_attempt_consumes_only_additional_slot_even_small_or_failed(state,hours):
    w,old,proposed,new,linked=case(hours,state);new['actual_gpu_hours']=0
    assert w.mask_retry_gpu_hours([old,new],admissions=[linked])==hours
    duplicate=copy.deepcopy(new);duplicate['id']='independent150-third';duplicate['actual_entry']['id']=duplicate['id']
    with pytest.raises(ValueError):w.mask_retry_gpu_hours([old,new,duplicate],admissions=[linked])

@pytest.mark.parametrize('fault',['hours','minutes','gpus','source','job','output','policy','admission_hash','upper','ceiling','anchors'])
def test_replacement_cannot_change_resource_source_or_approval_binding(fault):
    w,old,proposed,new,linked=case()
    if fault=='hours':new['reserved_gpu_hours']=.7501
    elif fault=='minutes':new['actual_entry']['requested_minutes']=46
    elif fault=='gpus':new['actual_entry']['gpus']=2
    elif fault=='source':new['actual_entry']['source_commit']=old['actual_entry']['source_commit']
    elif fault=='job':new['actual_entry']['job_id']=old['actual_entry']['job_id']
    elif fault=='output':new['actual_entry']['output_dir']=old['actual_entry']['output_dir']
    elif fault=='policy':new['reservation_lineage']['mask_replacement_policy_sha256']='5'*64
    elif fault=='admission_hash':linked['admission_sha256']='5'*64
    elif fault=='upper':linked['upper_inventory_sha256']='5'*64
    elif fault=='ceiling':linked['max_gpu_hours']=.7501
    elif fault=='anchors':linked['reservation_ids'].append('third')
    with pytest.raises(ValueError):w.mask_retry_gpu_hours([old,new],admissions=[linked])

@pytest.mark.parametrize('fault',[None,'direction','edge','M1','M2','M3','M4','M5','contingency','all'])
def test_all_caps_have_exact_additive_boundary(fault):
    from component_analysis import a3_direction_runtime as r
    w,old,proposed,new,linked=case();entries=[old,new]
    for phase,sub,hours in [('M1','directions',.5),('M1','edges',.75),('M2','directions',9),('M3','neurons',4),('M4','edges',9),('M5','masks',10)]:entries.append(dict(id=phase+sub,phase=phase,subphase=sub,reserved_gpu_hours=hours,state='completed',actual_gpu_hours=0))
    contingency=5.25
    if fault in ('direction','edge'):
        next(e for e in entries if e['subphase']==('directions' if fault=='direction' else 'edges') and e['phase']=='M1')['reserved_gpu_hours']+=.01
    elif fault in ('M2','M3','M4','M5'):next(e for e in entries if e['phase']==fault)['reserved_gpu_hours']+=.01
    elif fault=='M1':entries.append(dict(id='unrelated',phase='M1',subphase='other',reserved_gpu_hours=.01,state='failed'))
    elif fault=='contingency':contingency=5.24
    elif fault=='all':contingency=5.26
    if fault is None:
        result=r.validate_global_budgets(entries,contingency_remaining=contingency);assert result['M1']==2.75 and result['all']+contingency==40
    else:
        with pytest.raises(ValueError):r.validate_global_budgets(entries,contingency_remaining=contingency)


def test_new_completed_pilot_is_required_for_full_cost_intake():
    # This original, unchanged small fixture is a numerical/schema control, not
    # a real completed measurement. No source prepared artifacts are rewritten.
    from tests.test_a3_mask_pipeline import cost_fixture
    from component_analysis import a3_mask_workload as mw
    w,old,proposed,new,linked=case();inventory,receipt,prior=cost_fixture()
    linked['identity']=copy.deepcopy(inventory['identity']);linked['upper_inventory_sha256']=receipt['pilot_inventory_sha256'];linked['admission_sha256']=w.digest({k:v for k,v in linked.items() if k!='admission_sha256'})
    new.update(state='completed',actual_gpu_hours=.01,inventory_sha256=receipt['pilot_inventory_sha256']);new['actual_entry']['source_commit']=inventory['identity']['commit'];new['reservation_lineage'].update(admission_sha256=linked['admission_sha256'],upper_inventory_sha256=linked['upper_inventory_sha256'])
    receipt.update(reservation_id=new['id'],allocation_job_id=new['actual_entry']['job_id'],output_dir=new['actual_entry']['output_dir']);prior.update(entries=[old,new],expected_entry_ids=[old['id'],new['id']],original_admissions=[linked],contingency_gpu_hours=5.25)
    assert mw.project_cost([receipt],inventory,prior)['execution_authorized'] is False
    for state in ('reserved','running','failed'):
        bad=copy.deepcopy(prior);bad['entries'][1]['state']=state
        with pytest.raises(ValueError):mw.project_cost([receipt],inventory,bad)
