"""Pure inventory and synthetic measured-receipt admission contracts."""
import copy
import math
import pytest
from component_analysis import a3_direction_workload as w


def fixture():
    tasks={}; access={}
    for task in ('far_v2','ser_v2','sdr_v2'):
        tasks[task]=dict(fit_ids=[task+'t0',task+'t1'],selection_ids=[task+'v0',task+'v1'],
            assessment_ids=[task+'a0',task+'a1'],direction_sites=[['head',17,24]])
        access[task]=[dict(instance_id=i,condition=c,split=split,streams={s:dict(tokens=[1,2,3],readout=2,prompt=i+c+s) for s in ('clean','corrupt')})
            for split,key in [('train','fit_ids'),('validation','selection_ids'),('test','assessment_ids')]
            for i in tasks[task][key] for c in ('D','H','F','I','user_neutral')]
    utility={task:[dict(instance_id=task+split+str(i),condition=task.upper(),split='test',streams={s:dict(tokens=[1,2],readout=1,prompt=task+split+str(i)+s) for s in ('clean','corrupt')}) for i in range(2)] for task in ('ioi','mmlu') for split in []}
    def util(task,split):
        return [dict(instance_id=task+split+str(i),condition=task.upper(),split='test',streams={s:dict(tokens=[1,2],readout=1,prompt=task+split+str(i)+s) for s in ('clean','corrupt')}) for i in range(2)]
    d=dict(tasks=tasks,access_rows=access,seeds=[42,1,123],injected=True,
           utility={t:util(t,'assessment') for t in ('ioi','mmlu')},ioi_validation=util('ioi','validation'),mmlu_validation=util('mmlu','validation'))
    p=dict(identity=dict(commit='a'*40,code_hashes={'source.py':'b'*64},model='m',model_revision='c'*40,tokenizer_revision='d'*40),
        workload=dict(microbatch_size=2,axis_tile_size=2,widths={t:{s:4 for s in ('train','validation','assessment')} for t in list(tasks)+['ioi','mmlu']},
            hardware={'gpu':'synthetic','count':1},head_width=2,hidden_size=8,dtype_bytes=2,
            finish_reserve_seconds=10,warmup_batches=1,serialization_batches=1,jobs=1,reuse_policy=copy.deepcopy(w.PROFILE_REUSE_POLICY)))
    def axis(name,i=0): return dict(axis_index=i,reference=name+str(i),sha256=w.digest([name,i]))
    selected=dict(selection_split='validation',blocked_task_seeds=[],identity=w._identity(d,p),selected_records=[dict(task=t,seed=s,site=['head',17,24],
        learned_axis=axis(t+str(s)+'learned'),assessment_axes=[axis(t+str(s)+'assessment',i) for i in range(199)],
        calibration_axes=[axis(t+str(s)+'calibration',i) for i in range(32)],
        nuisance=dict(status='fitted',axis=axis(t+str(s)+'nuisance'))) for t in tasks for s in (42,1,123)])
    return d,p,selected


def inventory(stage='fit-select'):
    d,p,s=fixture()
    if stage in ('remaining','selected-pilot'):
        p['workload']['axis_tile_size']=32
        s['identity']=w._identity(d,p)
    return w.build_inventory(d,p,stage=stage,selected=s if stage in ('remaining','selected-pilot') else None)


def packing_evidence(m):
    """Synthetic complete runner-v2 evidence; never a model measurement claim."""
    rows=[]
    for f in m['timing_inputs']:
        data=f['record']['streams'][f['stream']]; n=f['unpadded_length']; width=f['padded_width']
        rows.append(dict(tokens=data['tokens']+[0]*(width-n),mask=[1]*n+[0]*(width-n),readout=f['readout'],
            record=f['record'],task=f['source_task'],condition=f['condition'],stream=f['stream'],instance_id=f['instance_id'],
            expected_token=f['record'].get('expected_token',0),opposite_token=f['record'].get('opposite_token',0),
            honest_token=f['record'].get('honest_token',0),choice_tokens=f['record'].get('choice_tokens')))
    if not rows: return None
    p=m['profile']; bid=w.digest([w.digest(r) for r in rows]); specs=[]
    for c in m['axis_scope']:
        spec={k:copy.deepcopy(v) for k,v in c.items() if k!='axis_reference'}
        spec.setdefault('axis_sha256',w.digest([c.get('seed'),c.get('axis_index'),c.get('operation')]))
        specs.append(spec)
    while len(specs)<max(2,p['axis_tile_size']):
        specs.append(dict(site=p['sites'][0],seed=42,family='learned',axis_index=999+len(specs),
            operation='zero',axis_sha256=w.digest(['synthetic extra nonzero lane',len(specs)])))
    for spec in specs:
        spec['donors']=[]
        if spec['operation']=='interchange':
            spec['donors']=[dict(cached_donor_sha256='a'*64,mapping=dict(recipient_id=r['instance_id'],donor_id=r['instance_id'],
                donor_condition=r['condition'],donor_stream='corrupt' if r['task']=='ioi' or r['stream']=='clean' else 'clean')) for r in rows]
    recipients=[dict(source_task=r['task'],condition=r['condition'],stream=r['stream'],instance_id=r['instance_id']) for r in rows]
    scope=dict(profile=p,source_sha256=p['source_sha256'],batches={bid:specs},recipients={bid:recipients},dummy_cells={bid:[specs[0]]})
    comparisons=[]
    for spec in specs+[specs[0]]:
        for recipient in recipients:
            key=dict(recipient,**{k:spec[k] for k in ('site','seed','family','axis_index','operation')})
            side=dict(axis_hash=spec['axis_sha256'],intact_margin=1.,patched_margin=.5,intact_argmax=0,patched_argmax=1,
                head_norm=1.,replay_errors=dict(empty=0.,head_self=0.,zero_coefficient=0.))
            comparisons.append(dict(key=key,serial=side,packed=copy.deepcopy(side)))
    r=dict(kind='measured_direction_packing_v2',valid=True,scope=scope,scope_sha256=w.digest(scope),comparisons=comparisons,
        dummy_lanes_tested=True,distinct_axes=len(set(x['axis_sha256'] for x in specs)),nonzero_patches=len(comparisons))
    r['receipt_sha256']=w.digest(r)
    return dict(runner_receipt=r,snapshots={bid:rows})


def receipts(inv):
    measurements=[]; evidence={}
    for x in inv['requirements']:
        m=dict(profile=copy.deepcopy(x['profile']),operation=x['operation'],batch_seconds=[.01,.02],
            expected_keys=x['timing_keys'],observed_keys=x['timing_keys'],axis_ids=x['axis_ids'],axis_scope=copy.deepcopy(x['axis_scope']),
            source_split='validation',synchronized=True,timing_inputs=x['timing_inputs'],donor_convention=x['donor_convention'],
            axis_class=x['axis_class'],nonzero_axis_count=1,cache_fit=True,memory_capacity_bytes=2,cache_capacity_bytes=max(1,inv['storage_requirements']['tiers']['cache_disk']),
            cache_bytes=1,peak_allocated_bytes=1,peak_reserved_bytes=2)
        if m['operation']=='serialization':
            m['serialization_shape_ids']=[w.digest(s) for s in m['profile']['serialization_shapes']]
            m['batch_seconds']=[.02]*len(m['serialization_shape_ids'])
        if m['profile']['axis_tile_size']>1 and m['timing_inputs']:
            pid=w.digest([m['profile'],m['timing_inputs'],m['axis_scope']])
            if pid not in evidence: evidence[pid]=packing_evidence(m)
            m['packing_id']=pid
        measurements.append(m)
    return [dict(kind='a3_direction_timing_v1',status='completed',exit_code=0,identity=copy.deepcopy(inv['identity']),hardware=copy.deepcopy(inv['hardware']),
        startup_seconds=2,host_peak_bytes=1,inventory_sha256=inv['inventory_sha256'],measurements=measurements,packing_evidence=evidence,complete=True)]


def ledger(inv):
    return dict(kind='a3_root_ledger_snapshot_v1',root_supplied=True,snapshot_sha256='e'*64,
        current_snapshot_sha256='e'*64,age_seconds=0,max_age_seconds=60,
        entries=[],expected_entry_ids=[],contingency_gpu_hours=6,
        expected_identity=inv['identity'],storage_capacities={t:dict(pool=t,available_bytes=max(1,n)*2) for t,n in inv['storage_requirements']['tiers'].items()})


def test_inventory_explicitly_covers_all_cells():
    inv=inventory('remaining'); keys=inv['expected_keys']
    assert len(keys)==len(set(map(tuple,keys)))
    assert set(k[1] for k in keys)=={'far_v2','ser_v2','sdr_v2'}
    assert set(k[4] for k in keys)=={42,1,123}
    null=[k for k in keys if k[6]=='assessment_null']
    assert set(k[7] for k in null)==set(range(199))
    assert {k[8] for k in null if k[2]=='mmlu'}=={'zero','h_mean'}
    assert {k[8] for k in keys if k[6]=='steering_random'}=={'steer_positive','steer_negative'}
    assert {k[7] for k in keys if k[6]=='calibration_null'}==set(range(32))
    assert all(k[3]=='validation' for k in keys if k[0]=='calibration')
    assert sum(len(s['expected_keys']) for s in inv['shards'])==len(keys)
    assert inv['bytes']['transient_capture_peak']>inv['bytes']['readout_chunk_peak']


def test_exact_chunk_axis_tile_forward_counts():
    inv=inventory('fit-select')
    scoring=[x for x in inv['requirements'] if x['operation']=='patched']
    # Three seeds packed in two tiles, 10 mechanism batches plus IOI plus 2 floors.
    assert sum(x['batches'] for x in scoring)==3*(2*11+3)
    assert inv['forward_counts']['patched']==75
    for op in ('intact','empty','head_self','zero_coefficient'):
        assert inv['forward_counts'][op]==75
    # train D/I/H/user-neutral, two streams; one union-site capture per chunk.
    assert inv['forward_counts']['capture_train']==3*8
    assert inv['forward_counts']['positive_control']==3*12*2*3


def test_prefit_admission_excludes_assessment():
    inv=inventory(); assert set(k[3] for k in inv['expected_keys'])=={'validation'}
    assert inv['phase']=='M2' and inv['admission_scope']=='fit-validation-only'
    assert inv['pilot_part']=='prefit'


def test_failed_fits_are_explicit_not_missing_science():
    d,p,_=fixture()
    fits={'fit_records':[dict(task=t,site=['head',17,24],seed=s,dom_valid=(s!=42),reason='zero DOM') for t in d['tasks'] for s in (42,1,123)]}
    inv=w.build_inventory(d,p,stage='fit-select',fits=fits)
    assert len(inv['fit_failures'])==3 and len(inv['blockers'])==3
    assert 42 not in {k[4] for k in inv['expected_keys']}
    with pytest.raises(ValueError,match='blocked'):
        w.project_cost(receipts(inv),inv,ledger(inv))


@pytest.mark.parametrize('fault',['missing','nan','failed','short','hardware','source','axis','shape','unsynchronized'])
def test_receipt_faults_block(fault):
    inv=inventory(); r=receipts(inv); m=r[0]['measurements'][0]
    if fault=='missing': r[0]['measurements'].pop(0)
    if fault=='nan': m['batch_seconds']=[float('nan')]
    if fault=='failed': r[0]['exit_code']=1
    if fault=='short': m['observed_keys']=m['observed_keys'][:-1]
    if fault=='hardware': r[0]['hardware']={'gpu':'wrong','count':1}
    if fault=='source': r[0]['identity']['commit']='f'*40
    if fault=='axis': next(x for x in r[0]['measurements'] if x['axis_ids'])['axis_ids']=[]
    if fault=='shape': m['profile']['padded_width']=999
    if fault=='unsynchronized': m['synchronized']=False
    with pytest.raises(ValueError): w.project_cost(r,inv,ledger(inv))


def test_startup_and_shared_m1_charged_once():
    inv=inventory(); r=receipts(inv); l=ledger(inv)
    l['entries']=[dict(id='pilot',phase='M1',subphase='directions',state='completed',actual_gpu_hours=.1,reserved_gpu_hours=.2)]
    l['expected_entry_ids']=['pilot']
    result=w.project_cost(r,inv,l)
    assert result['existing_gpu_hours']==pytest.approx(.2)
    assert result['existing_actual_gpu_hours']==pytest.approx(.1)
    expected=2+1.25*sum(x['batches']*.02 for x in inv['requirements'])+10
    assert result['projected_seconds']==pytest.approx(expected)
    assert result['proposed_walltime_seconds']==math.ceil(expected)
    assert result['direction_m1_gpu_hours']==pytest.approx(.2)


@pytest.mark.parametrize('fault',['missing','stale','duplicate','forgotten','negative','contingency','M1','directionM1','M2','allA3'])
def test_no_fresh_ledger_or_reservation_blocks(fault):
    inv=inventory(); l=ledger(inv)
    if fault=='missing': l={}
    if fault=='stale': l['current_snapshot_sha256']='f'*64
    if fault in ('duplicate','forgotten','negative'):
        l['entries']=[dict(id='old',phase='M2',subphase='directions',state='failed',actual_gpu_hours=.1,reserved_gpu_hours=.2)]
        l['expected_entry_ids']=['old']
        if fault=='duplicate': l['entries']*=2
        if fault=='forgotten': l['expected_entry_ids'].append('omitted')
        if fault=='negative': l['entries'][0]['actual_gpu_hours']=-1
    if fault=='contingency': l['contingency_gpu_hours']=0
    if fault in ('M1','directionM1','M2','allA3'):
        phase,subphase,h={'M1':('M1','edges',2.1),'directionM1':('M1','directions',.51),'M2':('M2','directions',9),'allA3':('M4','edges',35)}[fault]
        l['entries']=[dict(id='prior',phase=phase,subphase=subphase,state='reserved',reserved_gpu_hours=h)]
        l['expected_entry_ids']=['prior']
    with pytest.raises(ValueError): w.project_cost(receipts(inv),inv,l)


def test_changed_workload_digest_rejects_optimistic_totals():
    inv=inventory(); inv['requirements'][0]['batches']=0
    with pytest.raises(ValueError,match='inventory'):
        w.project_cost(receipts(inv),inv,ledger(inv))


def test_selected_timing_requires_every_199_axis():
    inv=inventory('selected-pilot')
    assert set(c['axis_index'] for x in inv['requirements'] if x['operation']=='patched' for c in x['axis_scope'] if c['family']=='assessment_null')==set(range(199))
    assert all(k[3]=='validation' for k in inv['expected_keys'])
    d,p,s=fixture(); s['selected_records'][0]['assessment_axes'].pop()
    with pytest.raises(ValueError,match='199'): w.build_inventory(d,p,stage='remaining',selected=s)


def test_packing_reuse_is_explicit_unresolved_not_an_authorization_boolean():
    inv=inventory('remaining'); r=receipts(inv)
    result=w.project_cost(r,inv,ledger(inv))
    assert result['conditional_proposal'] and not result['execution_authorized']
    assert result['packed_execution_blocker']
    assert result['reuse_records'] and all(not x['target_rows_are_measured'] for x in result['reuse_records'])


def test_small_serial_inventory_can_be_admitted_without_packing_reuse():
    d,p,_=fixture(); p['workload']['axis_tile_size']=1
    inv=w.build_inventory(d,p,stage='fit-select')
    assert w.project_cost(receipts(inv),inv,ledger(inv))['admitted'] is True


def test_deadline_and_multigpu_arithmetic():
    inv=inventory(); l=ledger(inv); l['deadline_remaining_seconds']=1
    with pytest.raises(ValueError,match='deadline'): w.project_cost(receipts(inv),inv,l)


def test_rehashed_optimistic_inventory_still_fails_reconstruction():
    inv=inventory(); inv['requirements'][0]['batches']=1_000
    inv['inventory_sha256']=w.digest({k:v for k,v in inv.items() if k!='inventory_sha256'})
    with pytest.raises(ValueError,match='reconstruction'):
        w.project_cost(receipts(inv),inv,ledger(inv))


def test_policy_boolean_or_changed_assumption_is_not_frozen_policy():
    d,p,_=fixture(); p['workload']['reuse_policy']=True
    inv=w.build_inventory(d,p,stage='fit-select')
    with pytest.raises(ValueError,match='policy'): w.project_cost(receipts(inv),inv,ledger(inv))


@pytest.mark.parametrize('field,value',[('timing_inputs',[]),('donor_convention','other'),('nonzero_axis_count',0)])
def test_measured_input_donor_and_nonzero_class_faults(field,value):
    inv=inventory(); r=receipts(inv)
    next(m for m in r[0]['measurements'] if m['axis_ids'])[field]=value
    with pytest.raises(ValueError): w.project_cost(r,inv,ledger(inv))


def test_prefit_profiles_actual_train_width_without_train_inputs():
    d,p,_=fixture()
    for task in d['tasks']: p['workload']['widths'][task]['train']=9
    inv=w.build_inventory(d,p,stage='prefit')
    rows=[x for x in inv['requirements'] if x['operation']=='capture_train']
    assert rows and {x['profile']['padded_width'] for x in rows}=={9}
    assert all(v['analysis_split']=='validation' for x in rows for v in x['timing_inputs'])
    assert inv['forward_counts']['equivalence_serial_patched']>0
    assert inv['forward_counts']['equivalence_dummy_2_patched']>0


def test_long_source_cannot_be_truncated_to_pilot_width():
    d,p,_=fixture(); p['workload']['widths']['far_v2']['train']=1
    with pytest.raises(ValueError,match='truncat'): w.build_inventory(d,p,stage='fit-select')


@pytest.mark.parametrize('fault',['null_hash','null_duplicate','missing_learned','nuisance_axis','selected_source'])
def test_selected_axis_identity_not_just_index(fault):
    d,p,s=fixture(); r=s['selected_records'][0]
    if fault=='null_hash': r['assessment_axes'][0]['sha256']='wrong'
    if fault=='null_duplicate': r['assessment_axes'][1]=r['assessment_axes'][0]
    if fault=='missing_learned': r.pop('learned_axis')
    if fault=='nuisance_axis': r['nuisance'].pop('axis')
    if fault=='selected_source': s['identity']['commit']='f'*40
    with pytest.raises(ValueError): w.build_inventory(d,p,stage='remaining',selected=s)


def test_matching_existing_reservation_is_not_charged_twice():
    inv=inventory(); r=receipts(inv); l=ledger(inv)
    initial=w.project_cost(r,inv,l)
    l['entries']=[dict(id='already',phase='M2',subphase='directions',state='reserved',
        reserved_gpu_hours=initial['projected_gpu_hours'],inventory_sha256=inv['inventory_sha256'])]
    l['expected_entry_ids']=['already']
    result=w.project_cost(r,inv,l)
    assert result['additional_gpu_hours']==pytest.approx(0)
    assert result['direction_m2_gpu_hours']==pytest.approx(initial['projected_gpu_hours'])


def test_failed_attempt_charged_beside_current_reservation():
    inv=inventory(); l=ledger(inv)
    l['entries']=[dict(id='failed',phase='M2',subphase='directions',state='failed',actual_gpu_hours=.1,
        reserved_gpu_hours=.3,inventory_sha256=inv['inventory_sha256'])]
    l['expected_entry_ids']=['failed']
    result=w.project_cost(receipts(inv),inv,l)
    assert result['direction_m2_gpu_hours']==pytest.approx(.3+result['projected_gpu_hours'])


def test_nuisance_unfittable_retains_conditional_obligations():
    d,p,s=fixture(); p['workload']['axis_tile_size']=32; s['identity']=w._identity(d,p)
    s['selected_records'][0]['nuisance']=dict(status='unfitted',reason='zero variance',fit_receipt={'manifest_sha256':'a'*64})
    inv=w.build_inventory(d,p,stage='remaining',selected=s)
    assert not inv['blockers'] and len(inv['conditional_unavailable'])==1
    assert len(inv['conditional_unavailable'][0]['obligations'])==3
    assert not [k for k in inv['expected_keys'] if k[1]=='far_v2' and k[4]==42 and k[6] in ('nuisance','steering_nuisance')]


def test_cache_memory_or_axis_hash_faults_block():
    inv=inventory(); r=receipts(inv)
    r[0]['measurements'][0]['cache_fit']=False
    with pytest.raises(ValueError,match='cache'): w.project_cost(r,inv,ledger(inv))


def test_postfit_cost_cannot_expand_original_fit_reservation():
    d,p,_=fixture()
    fits={'fit_records':[dict(task=t,site=['head',17,24],seed=s,valid=True) for t in d['tasks'] for s in (42,1,123)]}
    inv=w.build_inventory(d,p,stage='fit-select',fits=fits)
    with pytest.raises(ValueError,match='original fit'): w.project_cost(receipts(inv),inv,ledger(inv))


def test_multigpu_and_multiple_startups_are_explicit():
    d,p,_=fixture(); p['workload']['hardware']['count']=2; p['workload']['jobs']=2
    inv=w.build_inventory(d,p,stage='fit-select'); result=w.project_cost(receipts(inv),inv,ledger(inv))
    assert result['required_job_count']==2
    expected=2*2+1.25*sum(x['batches']*.02 for x in inv['requirements'])+2*10
    assert result['projected_seconds']==pytest.approx(expected)
    assert result['projected_gpu_hours']==pytest.approx(expected*2/3600)


def test_utility_donor_longer_than_declared_profile_blocks():
    d,p,_=fixture(); d['ioi_validation'][0]['streams']['corrupt'].update(tokens=[1]*10,readout=9)
    with pytest.raises(ValueError,match='truncat'): w.build_inventory(d,p,stage='prefit')


def test_prefit_padded_training_profile_cannot_truncate_validation_prompt():
    d,p,_=fixture(); p['workload']['widths']['far_v2']['train']=2
    with pytest.raises(ValueError,match='truncat'): w.build_inventory(d,p,stage='prefit')


def test_prior_direction_pilot_failure_counts_toward_combined_m1():
    inv=inventory('prefit'); l=ledger(inv)
    l['entries']=[dict(id='failed-pilot',phase='M1',subphase='directions',state='failed',actual_gpu_hours=.5,reserved_gpu_hours=.5)]
    l['expected_entry_ids']=['failed-pilot']
    with pytest.raises(ValueError,match='M1'): w.project_cost(receipts(inv),inv,l)


def test_completed_capture_and_later_validation_share_admission_envelope_once():
    inv,l=postfit_lineage_fixture()
    assert inv['forward_counts'].get('capture_train',0)==0
    result=w.project_cost(receipts(inv),inv,l)
    assert result['direction_m2_gpu_hours']==pytest.approx(.1+result['projected_gpu_hours'])
    assert result['fit_validation_consumed_gpu_hours']==pytest.approx(.1)
    assert result['existing_actual_gpu_hours']==pytest.approx(.01)
    envelope=l['fit_validation_envelope']; envelope['max_gpu_hours']=.01
    envelope['envelope_sha256']=w.digest({k:v for k,v in envelope.items() if k!='envelope_sha256'})
    with pytest.raises(ValueError,match='envelope'): w.project_cost(receipts(inv),inv,l)


def test_packed_proposal_requires_complete_measured_equivalence_evidence():
    inv=inventory(); r=receipts(inv); r[0].pop('packing_evidence',None)
    with pytest.raises(ValueError,match='packing'): w.project_cost(r,inv,ledger(inv))


@pytest.mark.parametrize('fault',['missing_comparison','margin_disagreement','replay_nan','changed_frozen_tokens','axis_hash'])
def test_rehashed_packing_receipt_faults_still_block(fault):
    inv=inventory(); r=receipts(inv)
    m=next(x for x in r[0]['measurements'] if x.get('packing_id') and x['axis_scope'])
    e=r[0]['packing_evidence'][m['packing_id']]; rr=e['runner_receipt']; scope=rr['scope']
    if fault=='missing_comparison': rr['comparisons'].pop()
    if fault=='margin_disagreement': rr['comparisons'][0]['packed']['patched_margin']=999.
    if fault=='replay_nan': rr['comparisons'][0]['packed']['replay_errors']['empty']=float('nan')
    if fault=='axis_hash':
        m['axis_scope'][0]['axis_sha256']='f'*64  # demanded frozen axis differs from measured
    if fault=='changed_frozen_tokens':
        old=next(iter(e['snapshots'])); snapshots=e['snapshots'].pop(old)
        snapshots[0]=copy.deepcopy(snapshots[0]); snapshots[0]['tokens'][0]=999
        new=w.digest([w.digest(x) for x in snapshots]); e['snapshots'][new]=snapshots
        for key in ('batches','recipients','dummy_cells'): scope[key][new]=scope[key].pop(old)
    if fault=='replay_nan':
        # NaN is rejected during canonical JSON hashing, before cost use.
        with pytest.raises(ValueError): w.project_cost(r,inv,ledger(inv))
        return
    rr['scope_sha256']=w.digest(scope)
    rr['receipt_sha256']=w.digest({k:v for k,v in rr.items() if k!='receipt_sha256'})
    with pytest.raises(ValueError,match='packing'): w.project_cost(r,inv,ledger(inv))


def test_each_job_has_exact_requirement_partition_and_own_walltime():
    d,p,_=fixture(); p['workload']['jobs']=2
    inv=w.build_inventory(d,p,stage='fit-select'); result=w.project_cost(receipts(inv),inv,ledger(inv))
    assert sum(j['projected_seconds'] for j in result['jobs'])==pytest.approx(result['projected_seconds'])
    assert result['proposed_walltime_seconds']==max(j['walltime_seconds'] for j in result['jobs'])
    ids=[i for j in inv['jobs'] for i in j['requirement_ids']]
    assert len(ids)==len(inv['requirements']) and set(ids)=={r['requirement_id'] for r in inv['requirements']}


def test_pilot_measurement_invocations_are_realizable_by_reviewed_producer():
    inv=inventory('selected-pilot')
    assert inv['packing_invocations']
    assert all(len(x['cells'])>=x['profile']['axis_tile_size'] for x in inv['packing_invocations'])
    assert all({c['family'] for c in x['cells']} >= {'learned','assessment_null'}
               for x in inv['packing_invocations'] if x['panel']=='selected_pilot')
    pre=inventory('prefit')
    assert pre['forward_counts']['capture_intact']==72
    assert pre['forward_counts']['capture_donor']==6


def test_prefit_profiles_actual_short_training_chunk_shape():
    d,p,_=fixture(); task='far_v2'; old=d['tasks'][task]['fit_ids'][0]; new=task+'t2'
    d['tasks'][task]['fit_ids'].append(new)
    for row in list(d['access_rows'][task]):
        if row['instance_id']==old:
            clone=copy.deepcopy(row); clone['instance_id']=new; d['access_rows'][task].append(clone)
    inv=w.build_inventory(d,p,stage='prefit')
    assert {x['profile']['physical_batch_size'] for x in inv['requirements'] if x['operation']=='capture_train' and x['profile']['source_task']==task}=={1,2}


def test_timing_part_cannot_split_atomic_measurement_calls_between_jobs():
    d,p,_=fixture(); p['workload']['jobs']=2
    with pytest.raises(ValueError,match='atomic'): w.build_inventory(d,p,stage='prefit')


@pytest.mark.parametrize('fault',['split','blocked'])
def test_selected_validation_provenance_and_blocked_seed_gate(fault):
    d,p,s=fixture()
    if fault=='split': s['selection_split']='assessment'
    else: s['blocked_task_seeds']=[dict(task='far_v2',seed=42,reason='no finite DOM')]
    with pytest.raises(ValueError,match='selection|blocked'): w.build_inventory(d,p,stage='remaining',selected=s)


def test_serialization_count_is_derived_from_actual_payload_inventory():
    d,p,_=fixture(); p['workload']['serialization_batches']=0
    inv=w.build_inventory(d,p,stage='fit-select')
    required=len(inv['captures'])+len(inv['shards'])+len({c for s in inv['shards'] for c in s['control_ids']})+len(inv['jobs'])+sum(s['profile']['axis_tile_size']>1 for s in inv['shards'])
    assert inv['operation_counts']['serialization']==required
    assert 'serialization' not in inv['forward_counts']


# report95 review regressions; all capacity/lineage objects are injected fixtures.
def serial_inventory():
    d,p,_=fixture(); p['workload']['axis_tile_size']=1
    return w.build_inventory(d,p,stage='fit-select')


def postfit_lineage_fixture():
    upper=serial_inventory(); d=upper['frozen_inputs']['design']; p=upper['frozen_inputs']['protocol']
    fits={'fit_records':[dict(task=t,site=['head',17,24],seed=s,valid=True) for t in d['tasks'] for s in w.SEEDS]}
    inv=w.build_inventory(d,p,stage='fit-select',fits=fits); l=ledger(inv)
    admission=dict(kind='a3_root_fit_admission_v1',id='original-fit',identity=inv['identity'],
        upper_inventory_sha256=upper['inventory_sha256'],max_gpu_hours=.5,reservation_ids=['capture'])
    admission['admission_sha256']=w.digest(admission)
    l['original_admissions']=[copy.deepcopy(admission)]
    entry=dict(id='capture',phase='M2',subphase='directions',state='completed',
        actual_gpu_hours=.01,reserved_gpu_hours=.1,inventory_sha256=upper['inventory_sha256'])
    lineage=dict(kind='a3_reservation_lineage_v1',reservation_id='capture',admission_id=admission['id'],
        admission_sha256=admission['admission_sha256'],upper_inventory_sha256=upper['inventory_sha256'],
        inventory_sha256=entry['inventory_sha256'],identity=inv['identity'],max_gpu_hours=.5,reserved_gpu_hours=.1)
    lineage['lineage_sha256']=w.digest(lineage); entry['reservation_lineage']=lineage
    l['entries']=[entry]; l['expected_entry_ids']=['capture']
    envelope=dict(kind='a3_fit_validation_envelope_v1',identity=inv['identity'],upper_inventory=upper,
        max_gpu_hours=.5,entry_ids=['capture'],admission_id=admission['id'],admission_sha256=admission['admission_sha256'])
    envelope['envelope_sha256']=w.digest(envelope); l['fit_validation_envelope']=envelope
    return inv,l


@pytest.mark.parametrize('state',['completed','failed','running','reserved'])
def test_reserved_cap_never_refunded_by_low_actual(state):
    inv=serial_inventory(); l=ledger(inv)
    l['entries']=[dict(id='old',phase='M2',subphase='directions',state=state,
        reserved_gpu_hours=9,actual_gpu_hours=.001)]
    l['expected_entry_ids']=['old']
    with pytest.raises(ValueError,match='M2'): w.project_cost(receipts(inv),inv,l)


@pytest.mark.parametrize('tier',['host_ram','cache_disk','output_disk','scratch_disk'])
def test_full_target_storage_tier_underflow_blocks(tier):
    inv=serial_inventory(); l=ledger(inv)
    l['storage_capacities']={t:dict(pool=t,available_bytes=10**12) for t in ('host_ram','cache_disk','output_disk','scratch_disk')}
    l['storage_capacities'][tier]['available_bytes']=1
    with pytest.raises(ValueError,match='storage|capacity'): w.project_cost(receipts(inv),inv,l)


def test_full_target_storage_includes_sources_optional_summaries_and_projections():
    inv=serial_inventory(); required=inv['storage_requirements']
    assert required['components']['capture_source_records']>0
    assert required['components']['clause_summary_numeric']>0
    assert required['components']['projection_and_fit_arrays']>=inv['bytes']['projection_blocks']
    assert required['tiers']['cache_disk']>inv['bytes']['capture_disk']
    assert required['tiers']['output_disk']>inv['bytes']['row_keys_utf8']
    assert required['tiers']['host_ram']>inv['bytes']['readout_chunk_peak']


@pytest.mark.parametrize('fault',['empty','unrelated','ceiling','source','admission_missing','lineage_missing'])
def test_original_fit_envelope_requires_bound_root_lineage(fault):
    inv,l=postfit_lineage_fixture(); e=l['fit_validation_envelope']
    if fault=='empty': e['entry_ids']=[]
    if fault=='unrelated': l['entries'][0]['inventory_sha256']='f'*64
    if fault=='ceiling': e['max_gpu_hours']=8
    if fault=='source': l['entries'][0]['reservation_lineage']['identity']={'commit':'f'*40}
    if fault=='admission_missing': l.pop('original_admissions')
    if fault=='lineage_missing': l['entries'][0].pop('reservation_lineage')
    e['envelope_sha256']=w.digest({k:v for k,v in e.items() if k!='envelope_sha256'})
    with pytest.raises(ValueError,match='envelope|admission|lineage'): w.project_cost(receipts(inv),inv,l)


def test_reserved_capture_exhausts_envelope_even_with_low_actual_use():
    inv,l=postfit_lineage_fixture(); entry=l['entries'][0]; entry['reserved_gpu_hours']=.5
    lineage=entry['reservation_lineage']; lineage['reserved_gpu_hours']=.5
    lineage['lineage_sha256']=w.digest({k:v for k,v in lineage.items() if k!='lineage_sha256'})
    with pytest.raises(ValueError,match='envelope'): w.project_cost(receipts(inv),inv,l)


@pytest.mark.parametrize('main_count',[2,3])
def test_dedicated_dummy_experiment_cannot_be_removed_and_rehashed(main_count):
    inv=inventory(); r=receipts(inv)
    m=copy.deepcopy(next(m for m in r[0]['measurements'] if m['axis_scope'] and m.get('packing_id')))
    m['axis_scope']=[dict(m['axis_scope'][0],seed=42+i) for i in range(main_count)]
    evidence=packing_evidence(m); rr=evidence['runner_receipt']; scope=rr['scope']
    assert len(next(iter(scope['batches'].values())))==main_count
    removed=sum(len(scope['recipients'][bid])*len(cells) for bid,cells in scope['dummy_cells'].items())
    rr['comparisons']=rr['comparisons'][:-removed]; scope['dummy_cells']={}
    rr['scope_sha256']=w.digest(scope); rr['receipt_sha256']=w.digest({k:v for k,v in rr.items() if k!='receipt_sha256'})
    with pytest.raises(ValueError,match='dummy'): w._packing_evidence(evidence,m)


def test_shared_storage_pool_cannot_spend_one_capacity_twice():
    inv=serial_inventory(); l=ledger(inv); tiers=inv['storage_requirements']['tiers']
    cap=max(tiers['cache_disk'],tiers['output_disk'])
    for tier in ('cache_disk','output_disk'):
        l['storage_capacities'][tier]=dict(pool='same-device',available_bytes=cap)
    with pytest.raises(ValueError,match='storage'): w.project_cost(receipts(inv),inv,l)


def test_target_storage_reconstruction_and_source_growth():
    inv=serial_inventory()
    assert w.derive_storage_requirements(inv)==inv['storage_requirements']
    d=copy.deepcopy(inv['frozen_inputs']['design']); p=inv['frozen_inputs']['protocol']
    for row in d['access_rows']['far_v2']:
        row['streams']['clean']['prompt']+='\U0001f600'*100
    larger=w.build_inventory(d,p,stage='fit-select')
    for tier in ('host_ram','cache_disk','output_disk'):
        assert larger['storage_requirements']['tiers'][tier]>inv['storage_requirements']['tiers'][tier]


def test_low_pilot_cache_capacity_cannot_admit_full_target():
    inv=serial_inventory(); r=receipts(inv)
    for m in r[0]['measurements']: m['cache_capacity_bytes']=1
    with pytest.raises(ValueError,match='target cache'): w.project_cost(r,inv,ledger(inv))


def test_target_host_retention_is_added_to_measured_host_peak():
    inv=serial_inventory(); l=ledger(inv); r=receipts(inv)
    r[0]['host_peak_bytes']=7
    l['storage_capacities']['host_ram']['available_bytes']=inv['storage_requirements']['tiers']['host_ram']+6
    with pytest.raises(ValueError,match='host|storage'): w.project_cost(r,inv,l)


def test_missing_measured_host_peak_blocks_storage_admission():
    inv=serial_inventory(); r=receipts(inv); r[0].pop('host_peak_bytes',None)
    with pytest.raises(ValueError,match='host'): w.project_cost(r,inv,ledger(inv))


def test_completed_capture_plus_active_validation_charges_reservations_once():
    inv,l=postfit_lineage_fixture(); r=receipts(inv); initial=w.project_cost(r,inv,l)
    reserve=initial['projected_gpu_hours']
    entry=dict(id='validation',phase='M2',subphase='directions',state='running',actual_gpu_hours=.001,
        reserved_gpu_hours=reserve,inventory_sha256=inv['inventory_sha256'])
    lineage=dict(l['entries'][0]['reservation_lineage'],reservation_id='validation',
        inventory_sha256=inv['inventory_sha256'],reserved_gpu_hours=reserve)
    lineage['lineage_sha256']=w.digest({k:v for k,v in lineage.items() if k!='lineage_sha256'})
    entry['reservation_lineage']=lineage; l['entries'].append(entry); l['expected_entry_ids'].append('validation')
    envelope=l['fit_validation_envelope']; envelope['entry_ids'].append('validation')
    envelope['envelope_sha256']=w.digest({k:v for k,v in envelope.items() if k!='envelope_sha256'})
    result=w.project_cost(r,inv,l)
    assert result['additional_gpu_hours']==0
    assert result['fit_validation_consumed_gpu_hours']==pytest.approx(.1+reserve)
    assert result['direction_m2_gpu_hours']==pytest.approx(.1+reserve)


def test_wrong_dedicated_dummy_cell_rejected_after_consistent_rehash():
    inv=inventory(); r=receipts(inv)
    m=next(m for m in r[0]['measurements'] if len(m['axis_scope'])==2 and m.get('packing_id'))
    evidence=packing_evidence(m); rr=evidence['runner_receipt']; scope=rr['scope']; bid=next(iter(scope['batches']))
    specs=scope['batches'][bid]; n=len(scope['recipients'][bid]); scope['dummy_cells'][bid]=[specs[1]]
    rr['comparisons']=rr['comparisons'][:-n]+copy.deepcopy(rr['comparisons'][n:2*n])
    rr['scope_sha256']=w.digest(scope); rr['receipt_sha256']=w.digest({k:v for k,v in rr.items() if k!='receipt_sha256'})
    with pytest.raises(ValueError,match='dummy'): w._packing_evidence(evidence,m)


@pytest.mark.parametrize('state',['completed','failed'])
@pytest.mark.parametrize('reference',['conflicting_digest','conflicting_id','consistent_omitted'])
def test_terminal_same_admission_lineage_cannot_hide_reserved_consumption(state,reference):
    inv,l=postfit_lineage_fixture()
    entry=dict(id='later-attempt',phase='M2',subphase='directions',state=state,
        reserved_gpu_hours=.49,actual_gpu_hours=.001,inventory_sha256=inv['inventory_sha256'])
    lineage=dict(l['entries'][0]['reservation_lineage'],reservation_id=entry['id'],
        inventory_sha256=entry['inventory_sha256'],reserved_gpu_hours=entry['reserved_gpu_hours'])
    if reference=='conflicting_digest': lineage['admission_sha256']='f'*64
    if reference=='conflicting_id': lineage['admission_id']='another-admission'
    lineage['lineage_sha256']=w.digest({k:v for k,v in lineage.items() if k!='lineage_sha256'})
    entry['reservation_lineage']=lineage
    l['entries'].append(entry); l['expected_entry_ids'].append(entry['id'])
    assert sum(e['reserved_gpu_hours'] for e in l['entries'])>.5
    assert entry['id'] not in l['fit_validation_envelope']['entry_ids']
    with pytest.raises(ValueError,match='admission|lineage|envelope'):
        w.project_cost(receipts(inv),inv,l)


def test_runtime_train_singletons_and_explicit_scoring_tail_geometry():
    d,p,s=fixture()
    # A third assessment row forces one execution-only tail alias in batch two.
    for task in d['tasks']:
        old=d['tasks'][task]['assessment_ids'][0]
        new=task+'a2'; d['tasks'][task]['assessment_ids'].append(new)
        d['access_rows'][task].extend(dict(copy.deepcopy(r),instance_id=new) for r in list(d['access_rows'][task]) if r['instance_id']==old)
    p['workload']['train_microbatch_size']=1
    p['workload']['pad_tail_batches']=True
    s['identity']=w.inventory_identity(d,p)
    inv=w.build_inventory(d,p,stage='remaining',selected=s)
    tail=next(x for x in inv['shards'] if x['split']=='assessment' and x['expected_keys'][0][2]=='far_v2' and len(x['instance_ids'])==1)
    assert tail['profile']['physical_batch_size']==p['workload']['microbatch_size']*p['workload']['axis_tile_size']
    assert len(tail['execution_ids'])==2 and len(tail['dummy_sources'])==1
    assert all('a3-dummy:' not in k[9] for k in inv['expected_keys'])
    assert tail['dummy_positive_forward_count']==3
    assert inv['bytes']['execution_dummy_rows']>0


def test_runtime_tail_measurement_inputs_include_actual_execution_aliases():
    d,p,s=fixture();p['workload']['pad_tail_batches']=True
    # Frozen microbatch two with one validation utility recipient.
    d['ioi_validation']=d['ioi_validation'][:1]
    s['identity']=w.inventory_identity(d,p)
    inv=w.build_inventory(d,p,stage='remaining',selected=s)
    requirement=next(x for x in inv['requirements'] if x['profile'].get('source_task')=='ioi'
        and x['operation']=='patched' and x['timing_inputs'])
    assert len(requirement['timing_inputs'])==2
    alias=next(x for x in requirement['timing_inputs'] if x['instance_id'].startswith('a3-dummy:'))
    assert alias['record']['execution_dummy']['duplicate_of']==d['ioi_validation'][0]['instance_id']
    assert alias['record']['streams']==d['ioi_validation'][0]['streams']


from tests.test_a3_direction_runner import fake


def test_intact_capture_lanes_have_separate_scope_bound_measurement(fake):
    from tests.test_a3_direction_runner import identity,batch,SITE
    from component_analysis import a3_direction_runtime as runtime
    from dataclasses import replace
    profile=identity(2)['numeric_profile'];b=replace(batch('corrupt'),task='ioi',condition='IOI')
    for i,row in enumerate(b.records):
        n=int(b.attention_mask[i].sum())
        row['streams']={'corrupt':dict(tokens=b.input_ids[i,:n].tolist(),readout=int(b.readout[i]))}
    chunks=[];run=runtime.runner._capture_readouts(object(),[b],sites=[SITE],sink=chunks.append,identity={'numeric_profile':profile},measuring=True)
    inputs=runtime._timing_inputs_from_batches([b],profile);m=dict(profile=profile,timing_inputs=inputs)
    evidence=runtime.capture_lane_evidence(run,chunks,[b],inputs)
    assert w._capture_lane_evidence(evidence,m)==w.digest(evidence)
    with pytest.raises(ValueError):w._packing_evidence(evidence,m)
    evidence['timing_inputs_sha256']='b'*64
    with pytest.raises(ValueError):w._capture_lane_evidence(evidence,m)


def test_completed_inventory_json_roundtrip_preserves_exact_reconstruction():
    import json
    inv=inventory('fit-select')
    restored=json.loads(json.dumps(inv))
    w._validate_inventory(restored)
    restored['requirements'][0]['batches']+=1
    with pytest.raises(ValueError):w._validate_inventory(restored)


def test_runtime_inventory_costs_live_guards_without_inventing_forwards():
    d,p,_=fixture();p['workload'].update(train_microbatch_size=1,pad_tail_batches=True,account_runtime_guards=True)
    inv=w.build_inventory(d,p,stage='fit-select')
    guards=[r for r in inv['requirements'] if r['operation']=='guard_refresh']
    assert len(guards)==1 and guards[0]['batches']>=5*len(inv['shards'])+len(inv['captures'])
    assert 'guard_refresh' not in inv['forward_counts']
    captures=[s for r in inv['requirements'] if r['operation']=='serialization' for s in r['profile']['serialization_shapes'] if s['kind']=='readout_capture']
    assert all(s['numeric_bytes']>=p['workload']['head_width']*p['workload']['hidden_size']*4 for s in captures)
    assert inv['storage_requirements']['components']['authority_key_proof_host_bytes']>0


def test_reference_proof_costs_are_nonauthorizing_and_conflicting_digest_rejects():
    inv=inventory();rr=receipts(inv);receipt=rr[0];proofs={};ref_entries={}
    for pid,evidence in receipt['packing_evidence'].items():
        m=next(x for x in receipt['measurements'] if x.get('packing_id')==pid)
        proof=w._validate_packing_proof(evidence,m)
        proofs[pid]=proof;ref_entries[pid]={'kind':'a3_packing_proof_reference_v1','evidence_sha256':proof.source_digest}
    receipt['packing_evidence']=ref_entries;sha=w.digest(receipt)
    table={(sha,pid):proof for pid,proof in proofs.items()}
    result=w.project_cost(rr,inv,ledger(inv),packing_proofs=table)
    assert result['execution_authorized'] is False
    pid=next(iter(ref_entries));receipt['packing_evidence'][pid]['evidence_sha256']='f'*64
    table={(w.digest(receipt),key):proof for key,proof in proofs.items()}
    with pytest.raises(ValueError,match='packing reference'):w.project_cost(rr,inv,ledger(inv),packing_proofs=table)
    with pytest.raises((TypeError,ValueError)):proofs[pid].source_digest='f'*64
    with pytest.raises(ValueError):w._PackingProof(None,{})


def test_legacy_same_packing_id_different_receipt_payload_is_independently_validated():
    inv=inventory();first=receipts(inv)[0];second=copy.deepcopy(first)
    m=next(x for x in second['measurements'] if x.get('packing_id'))
    evidence=second['packing_evidence'][m['packing_id']];raw=evidence['runner_receipt']
    raw['scope']['profile']=dict(raw['scope']['profile'])
    raw['scope']['profile']['backend']='other'
    raw['scope_sha256']=w.digest(raw['scope']);raw['receipt_sha256']=w.digest({k:v for k,v in raw.items() if k!='receipt_sha256'})
    with pytest.raises(ValueError,match='profile'):w.project_cost([first,second],inv,ledger(inv))


def test_packing_lookup_and_explicit_live_boundary_counts_are_priced_not_forwards():
    inv=inventory();lookups=[r for r in inv['requirements'] if r['operation']=='packing_lookup']
    assert sum(r['batches'] for r in lookups)==sum(s['profile']['axis_tile_size']>1 for s in inv['shards'])
    assert 'packing_lookup' not in inv['forward_counts']
    if any(r['operation']=='guard_refresh' for r in inv['requirements']):
        guard=next(r for r in inv['requirements'] if r['operation']=='guard_refresh')
        assert guard['batches']==10*len(inv['shards'])+3*len(inv['captures'])+2*len(inv['jobs'])


def _n5_fixture():
    from component_analysis import a3_direction_workload as w
    policy={'kind': 'a3_mask_replacement_policy_v1', 'approved_policy_sha256': 'e560adace32533895149742494de837dc6320cd6dcc129f3800e040db14e89f8', 'original_reservation': {'account': 'bimc-delta-gpu', 'actual_seconds': 0, 'cluster': 'delta', 'gpus': 1, 'id': 'r-031', 'job_id': '23444798', 'manifest_hash': None, 'output_dir': '/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819/mask-pilot-1', 'partition': 'gpuH200x8', 'requested_minutes': 45.0, 'reserved_gpu_hours': 0.75, 'source_commit': '74efb4d0481968a1d0138eb1a79b97f302fd3c3b', 'status': 'CANCELLED'}, 'original_admission_id': 'a3-mask-m1-23444798', 'original_admission_sha256': 'd5083712dc93eb6a0b8971fefff7d37ad65a7dcc2a3bbb909f30f39b578313a3', 'original_upper_inventory_sha256': 'ee8553504a386259e7ff575dc248f80521d139b0f520a55c5b8f14eb9a9c05d1', 'additional_reservations_max': 1, 'replacement_gpu_hours_max': 0.75}
    old=dict(id='r-031',phase='M1',subphase='masks',state='failed',reserved_gpu_hours=.75,actual_gpu_hours=0,
        actual_entry=copy.deepcopy(policy['original_reservation']),reservation_lineage=dict(admission_id=policy['original_admission_id'],
            admission_sha256=policy['original_admission_sha256'],upper_inventory_sha256=policy['original_upper_inventory_sha256'],reserved_gpu_hours=.75,max_gpu_hours=.75))
    admission=dict(kind='a3_root_pilot_admission_v1',id='n5-replacement',identity={'commit':'b'*40},max_gpu_hours=.75,
        upper_inventory_sha256='c'*64,reservation_ids=[],mask_replacement_policy=copy.deepcopy(policy))
    admission['admission_sha256']=w.digest(admission)
    return w,policy,old,admission


def _n5_actual(w,policy,admission,hours=.75):
    admission=copy.deepcopy(admission);admission['reservation_ids']=['r-new']
    admission['admission_sha256']=w.digest({k:v for k,v in admission.items() if k!='admission_sha256'})
    new=dict(id='r-new',phase='M1',subphase='masks',state='reserved',reserved_gpu_hours=hours,actual_gpu_hours=None,
        actual_entry=dict(id='r-new',job_id='999999',cluster='delta',account='new-account',partition='gpuH200x8',gpus=1,
            requested_minutes=hours*60,reserved_gpu_hours=hours,source_commit='b'*40,output_dir='/tmp/n5-replacement',manifest_hash=None),
        reservation_lineage=dict(admission_id=admission['id'],admission_sha256=admission['admission_sha256'],upper_inventory_sha256='c'*64,
            max_gpu_hours=.75,reserved_gpu_hours=hours,mask_replacement_policy_sha256=w.digest(policy)))
    return new,admission


def test_n5_real_construction_order_prospective_then_actual():
    w,policy,old,admission=_n5_fixture()
    assert w.mask_replacement_policy()==policy
    assert w.validate_mask_replacement_admission(admission,[old])['execution_authorized'] is False
    ledger=dict(kind='a3_root_ledger_snapshot_v1',root_supplied=True,snapshot_sha256='a'*64,current_snapshot_sha256='a'*64,
        age_seconds=0,max_age_seconds=900,expected_identity=admission['identity'],entries=[old],expected_entry_ids=['r-031'],
        contingency_gpu_hours=5.25,original_admissions=[])
    assert w._ledger(ledger,admission['identity'])['mask_retry_gpu_hours']==0
    new,completed_admission=_n5_actual(w,policy,admission)
    ledger.update(entries=[old,new],expected_entry_ids=['r-031','r-new'],original_admissions=[completed_admission])
    assert w._ledger(ledger,admission['identity'])['mask_retry_gpu_hours']==.75
    from component_analysis import a3_direction_runtime as r
    assert r.validate_global_budgets([old,new],contingency_remaining=5.25)['M1']==1.5


@pytest.mark.parametrize('fault',['second_small','old_source','old_output','old_hours','old_phase','old_job','old_admission','not_cancelled',
    'new_policy','new_source','new_output','new_hours','new_lineage','new_admission_policy','new_admission_source','new_admission_anchors','new_admission_hash'])
def test_n5_replacement_rejects_wrong_scope_or_lineage(fault):
    w,policy,old,admission=_n5_fixture();new,admission=_n5_actual(w,policy,admission,.25)
    entries=[old,new]
    if fault=='second_small':
        other=copy.deepcopy(new);other['id']='r-third';other['actual_entry']['id']='r-third';entries.append(other)
    elif fault=='old_source':old['actual_entry']['source_commit']='c'*40
    elif fault=='old_output':old['actual_entry']['output_dir']='/changed'
    elif fault=='old_hours':old['reserved_gpu_hours']=0
    elif fault=='old_phase':old['phase']='contingency'
    elif fault=='old_job':old['actual_entry']['job_id']='777'
    elif fault=='old_admission':old['reservation_lineage']['admission_sha256']='0'*64
    elif fault=='not_cancelled':old['actual_entry']['status']='PENDING'
    elif fault=='new_policy':new['reservation_lineage']['mask_replacement_policy_sha256']='0'*64
    elif fault=='new_source':new['actual_entry']['source_commit']=old['actual_entry']['source_commit']
    elif fault=='new_output':new['actual_entry']['output_dir']=old['actual_entry']['output_dir']
    elif fault=='new_hours':new['reserved_gpu_hours']=.8
    elif fault=='new_lineage':new['reservation_lineage']['admission_id']='unrelated'
    elif fault=='new_admission_policy':admission['mask_replacement_policy']['approved_policy_sha256']='0'*64
    elif fault=='new_admission_source':admission['identity']['commit']='d'*40
    elif fault=='new_admission_anchors':admission['reservation_ids']=['r-new','r-third']
    elif fault=='new_admission_hash':admission['admission_sha256']='0'*64
    with pytest.raises(ValueError):w.mask_retry_gpu_hours(entries,admissions=[admission])


@pytest.mark.parametrize('state',['reserved','running','completed','failed'])
def test_n5_new_reservation_always_consumes_one_attempt(state):
    w,policy,old,admission=_n5_fixture();new,admission=_n5_actual(w,policy,admission,.25);new['state']=state;new['actual_gpu_hours']=0
    assert w.mask_retry_gpu_hours([old,new],admissions=[admission])==.25
    third=copy.deepcopy(new);third['id']='r-third'
    with pytest.raises(ValueError):w.mask_retry_gpu_hours([old,new,third],admissions=[admission])



def test_n5_direction_cost_accepts_approved_aggregate_above_original_m1():
    w,policy,old,a=_n5_fixture();new,a=_n5_actual(w,policy,a)
    inv=inventory('prefit');l=ledger(inv)
    l.update(entries=[old,new,dict(id='edge',phase='M1',subphase='edges',state='completed',reserved_gpu_hours=.75)],
        expected_entry_ids=['r-031','r-new','edge'],contingency_gpu_hours=5.25,original_admissions=[a])
    assert w.project_cost(receipts(inv),inv,l)['execution_authorized'] is False


# Option A: unchanged frozen source is the independent metadata oracle.
# These are CPU-only equivalence/work-count tests, never model admission.
def _option_a_original():
    import importlib.util
    import hashlib
    from pathlib import Path
    path = Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-runtime-861f84a3938a/runtime/component_analysis/a3_direction_workload.py')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == '1b0f6110a39b5d50342b95fe7ee2d6b643fce20feb2ae4448403c1bc8c52d1b3'
    spec = importlib.util.spec_from_file_location('option_a_original_workload_oracle', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _option_a_dump(value):
    import json
    return (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')


def _option_a_input(stage, padding=False):
    d, p, selected = fixture()
    p['workload']['pad_tail_batches'] = padding
    if stage in ('remaining', 'selected-pilot'):
        p['workload']['axis_tile_size'] = 32
        selected['identity'] = w.inventory_identity(d, p)
    return d, p, selected if stage in ('remaining', 'selected-pilot') else None


@pytest.mark.parametrize('stage', ['prefit', 'fit-select', 'selected-pilot', 'remaining'])
@pytest.mark.parametrize('padding', [False, True])
def test_option_a_whole_output_matches_original(stage, padding):
    d, p, selected = _option_a_input(stage, padding)
    original = _option_a_original().build_inventory(d, p, stage=stage, selected=selected)
    actual = w.build_inventory(d, p, stage=stage, selected=selected)
    assert _option_a_dump(actual) == _option_a_dump(original)
    assert actual['inventory_sha256'] == original['inventory_sha256']
    assert actual['storage_requirements'] == original['storage_requirements']
    assert actual['forward_counts'] == original['forward_counts']
    assert type(actual['expected_keys'][0]) is type(original['expected_keys'][0])
    assert type(actual['requirements'][0]['timing_inputs']) is list


def test_option_a_never_copies_target_only_rows_for_lengths(monkeypatch):
    d, p, _ = fixture()
    target_only = {id(row) for rows in d['access_rows'].values() for row in rows if row['split'] == 'train'}
    deepcopy = copy.deepcopy
    seen = []
    depth = [0]
    def observe(value, *args, **kwargs):
        if depth[0] == 0 and id(value) in target_only:
            seen.append(value['instance_id'])
        depth[0] += 1
        try:
            return deepcopy(value, *args, **kwargs)
        finally:
            depth[0] -= 1
    monkeypatch.setattr(w.copy, 'deepcopy', observe)
    result = w.build_inventory(d, p, stage='fit-select')
    assert result['capture_shards']
    assert seen == [], 'target-only source rows were deep-copied solely for discarded lengths'


def test_option_a_source_rows_scanned_at_most_three_times_per_group(monkeypatch):
    from collections import Counter
    d, p, _ = fixture()
    scans = Counter()
    original = w._source_rows
    def observe(design, task, split):
        scans[(task, split)] += 1
        return original(design, task, split)
    monkeypatch.setattr(w, '_source_rows', observe)
    result = w.build_inventory(d, p, stage='fit-select')
    assert result['expected_keys']
    assert max(scans.values()) <= 3, dict(scans)


def test_option_a_sender_constant_encoded_and_bounded_once(monkeypatch):
    d, p, _ = fixture()
    dumps = w.json.dumps
    host_bound = w._host_bound
    counts = dict(wire=0, host=0)
    def senders(value):
        return isinstance(value, list) and len(value) > 10 and all(isinstance(x, list) and len(x) == 3 and x[0] in ('head', 'mlp') for x in value)
    def observe_dump(value, *args, **kwargs):
        if senders(value):
            counts['wire'] += 1
        return dumps(value, *args, **kwargs)
    def observe_host(value, *args, **kwargs):
        if senders(value):
            counts['host'] += 1
        return host_bound(value, *args, **kwargs)
    monkeypatch.setattr(w.json, 'dumps', observe_dump)
    monkeypatch.setattr(w, '_host_bound', observe_host)
    result = w.build_inventory(d, p, stage='fit-select')
    assert result['storage_requirements']['components']['positive_evidence'] > 0
    assert counts == dict(wire=1, host=1), counts


def test_option_a_retained_timing_records_are_independent():
    d, p, _ = fixture()
    result = w.build_inventory(d, p, stage='fit-select')
    records = []
    for req in result['requirements']:
        for row in req['timing_inputs']:
            if row['source_task'] == 'far_v2' and row['condition'] == 'D' and row['stream'] == 'clean':
                records.append(row['record'])
    first = records[0]
    other = next(row for row in records[1:] if row['instance_id'] == first['instance_id'])
    assert first is not other
    assert first['streams']['clean']['tokens'] is not other['streams']['clean']['tokens']
    first['streams']['clean']['tokens'].append(99)
    assert other['streams']['clean']['tokens'] == [1, 2, 3]
    assert all(row['streams']['clean']['tokens'] == [1, 2, 3] for row in d['access_rows']['far_v2'])
    assert all(row['streams']['clean']['tokens'] == [1, 2, 3] for row in result['frozen_inputs']['design']['access_rows']['far_v2'])


def test_option_a_target_lengths_preserve_padding_and_deduplication():
    d, p, _ = fixture()
    p['workload']['microbatch_size'] = 3
    p['workload']['pad_tail_batches'] = True
    for widths in p['workload']['widths'].values():
        for split in widths:
            widths[split] = 6
    for row in d['access_rows']['far_v2']:
        if row['split'] == 'validation' and row['instance_id'].endswith('v1'):
            for stream in row['streams'].values():
                stream['tokens'] = [1, 2, 3, 4, 5]
                stream['readout'] = 4
    result = w.build_inventory(d, p, stage='fit-select')
    req = next(q for q in result['requirements'] if q['operation'] == 'patched' and q['profile']['source_task'] == 'far_v2')
    assert req['target_unmasked_lengths'] == [3, 5, 3]
    positive = next(q for q in result['requirements'] if q['operation'] == 'positive_control' and q['profile']['source_task'] == 'far_v2')
    assert positive['target_unmasked_lengths'] == [3]
    empty = [q for q in result['requirements'] if not q['target_keys']]
    assert empty and all(q['target_unmasked_lengths'] == [] for q in empty)


@pytest.mark.parametrize('fault', ['missing_source', 'duplicate_source', 'readout', 'width', 'utility_width'])
def test_option_a_invalid_sources_match_original_errors(fault):
    d, p, _ = fixture()
    if fault == 'missing_source':
        d['access_rows']['far_v2'].pop(0)
    elif fault == 'duplicate_source':
        d['access_rows']['far_v2'].append(copy.deepcopy(d['access_rows']['far_v2'][0]))
    elif fault == 'readout':
        d['access_rows']['far_v2'][0]['streams']['clean']['readout'] = 0
    elif fault == 'width':
        p['workload']['widths']['far_v2']['validation'] = 1
    else:
        p['workload']['widths']['ioi']['validation'] = 1
    original = _option_a_original()
    with pytest.raises(ValueError) as expected:
        original.build_inventory(d, p, stage='fit-select')
    with pytest.raises(type(expected.value)) as actual:
        w.build_inventory(d, p, stage='fit-select')
    assert str(actual.value) == str(expected.value)


def test_option_a_changed_input_between_calls_not_cached():
    d, p, _ = fixture()
    for widths in p['workload']['widths'].values():
        for split in widths:
            widths[split] = 6
    first = w.build_inventory(d, p, stage='fit-select')
    changed = copy.deepcopy(d)
    row = next(x for x in changed['access_rows']['far_v2'] if x['split'] == 'validation')
    row['streams']['clean']['tokens'] = [1, 2, 3, 4]
    row['streams']['clean']['readout'] = 3
    second = w.build_inventory(changed, p, stage='fit-select')
    original = _option_a_original().build_inventory(changed, p, stage='fit-select')
    assert first['inventory_sha256'] != second['inventory_sha256']
    assert _option_a_dump(second) == _option_a_dump(original)


@pytest.mark.parametrize('payload', [
    {'unicode': 'é漢🙂', 'float': [1.0, -0.0, 1e-16, 1e30, 1.7976931348623157e308]},
    {'nested': {'b': [True, False, None], 'a': (1, 'x\\ny', '\\ud800')}},
    {'empty': [], 'map': {}, 'text': 'quote"slash\\'},
])
def test_option_a_publisher_stream_defaults_match_untouched_writer(tmp_path, payload):
    import hashlib
    import json
    from pathlib import Path
    from component_analysis import a3_direction_runtime as runtime
    baseline = Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-runtime-861f84a3938a/runtime/component_analysis/a3_direction_runtime.py')
    assert hashlib.sha256(Path(runtime.__file__).read_bytes()).hexdigest() == hashlib.sha256(baseline.read_bytes()).hexdigest()
    runtime.publish_object(tmp_path/'original', payload)
    expected = (tmp_path/'original/payload.json').read_bytes()
    class Sink:
        def __init__(self): self.hash = hashlib.sha256(); self.bytes = 0
        def write(self, text):
            raw = text.encode('utf-8'); self.hash.update(raw); self.bytes += len(raw); return len(text)
    sink = Sink()
    json.dump(payload, sink, sort_keys=True, allow_nan=False)
    sink.write('\n')
    assert sink.bytes == len(expected)
    assert sink.hash.hexdigest() == hashlib.sha256(expected).hexdigest()
    assert expected.endswith(b'\n')
    assert b'\\u00e9' in expected if 'unicode' in payload else True


def test_option_a_publisher_stream_rejects_nonfinite_without_complete(tmp_path):
    import json
    from component_analysis import a3_direction_runtime as runtime
    with pytest.raises(ValueError):
        runtime.publish_object(tmp_path/'original', {'value': math.inf})
    assert not (tmp_path/'original').exists()
    class Sink:
        def write(self, text): return len(text)
    with pytest.raises(ValueError):
        json.dump({'value': math.inf}, Sink(), sort_keys=True, allow_nan=False)


@pytest.mark.parametrize('stage', ['prefit', 'fit-select'])
def test_option_a_capture_metadata_multi_dummy_donors_match_original(stage):
    d, p, _ = fixture()
    p['workload']['microbatch_size'] = 5
    p['workload']['pad_tail_batches'] = True
    untouched = copy.deepcopy(d)
    expected = _option_a_original().build_inventory(d, p, stage=stage)
    actual = w.build_inventory(d, p, stage=stage)
    assert _option_a_dump(actual) == _option_a_dump(expected)
    assert d == untouched
    for stream in ('clean', 'corrupt'):
        capture = next(x for x in actual['captures'] if x['source_task'] == 'ioi'
                       and x['stream'] == stream and x['profile']['axis_tile_size'] == 2)
        assert len(capture['execution_ids']) == 5
        assert len(capture['dummy_sources']) == 3
        assert set(capture['dummy_sources'].values()) == {capture['instance_ids'][0]}
