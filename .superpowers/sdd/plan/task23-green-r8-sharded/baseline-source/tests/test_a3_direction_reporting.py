"""CPU-only raw panel normalization and descriptive inference contracts."""
import copy
import hashlib
import json

import numpy as np
import pytest

from component_analysis import a3_statistics as stats
from component_analysis import a3_direction_reporting as reporting


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def source(task, rid, condition, split):
    streams = ('clean',) if task in ('ioi', 'mmlu') else ('clean', 'corrupt')
    row = dict(task=task, instance_id=rid, source_id=rid, source_hash='source',
        split=split, condition=condition, prompt=rid, pressure_text='word '+rid[-1],
        expected_token=2, honest_token=1, opposite_token=2,
        streams={s:dict(tokens=[1, 2], readout=1, expected_token=2, honest_token=1,
                        opposite_token=2) for s in streams})
    if task == 'mmlu':
        row['choice_tokens'] = [1, 2, 3, 4]
    if split == 'validation':
        row['analysis_split'] = 'validation'
    return row


@pytest.fixture(scope='module')
def fixture():
    design = dict(seeds=[42, 1, 123], injected=True, tasks={}, access_rows={}, utility={},
                  selection_exclusion_ids=[])
    selected = dict(kind='a3_direction_selection', injected=True, selection_split='validation',
                    blocked_task_seeds=[], selected_records=[], axes={})
    for task in ('far_v2', 'ser_v2', 'sdr_v2'):
        design['tasks'][task] = dict(fit_ids=[task+'fit'], selection_ids=[task+'v0', task+'v1'],
            assessment_ids=[task+'a0', task+'a1'], direction_sites=[['head', 17, 24]])
        design['access_rows'][task] = [source(task, rid, c, split)
            for split, field in (('validation', 'selection_ids'), ('test', 'assessment_ids'))
            for c in stats.CONDITIONS for rid in design['tasks'][task][field]]
        for seed in stats.SEEDS:
            def axis(name, index=0):
                ref = f'{task}-{seed}-{name}-{index}'
                desc = dict(reference=ref, sha256=digest(ref), axis_index=index)
                selected['axes'][ref] = dict(sha256=desc['sha256'])
                return desc
            selected['selected_records'].append(dict(task=task, seed=seed, site=['head', 17, 24],
                learned_axis=axis('learned'), assessment_axes=[axis('assessment', i) for i in range(199)],
                calibration_axes=[axis('calibration', i) for i in range(32)]))
    for task, n in (('ioi', 2), ('mmlu', 32)):
        design['utility'][task] = [source(task, task+'a'+str(i), task.upper(), 'test') for i in range(n)]
        design[task+'_validation'] = [source(task, task+'v'+str(i), task.upper(), 'validation') for i in range(n)]
    panels = {}
    for split, family, axes in (('validation', 'calibration_null', 32), ('assessment', 'assessment_null', 199)):
        rows = []
        for rec in selected['selected_records']:
            t = rec['task']; ids = design['tasks'][t]['selection_ids' if split == 'validation' else 'assessment_ids']
            sources = [r for r in design['access_rows'][t] if r['instance_id'] in ids]
            sources += design['ioi_validation'] + design['mmlu_validation'] if split == 'validation' else design['utility']['ioi']+design['utility']['mmlu']
            for a in range(axes+1):
                desc = rec['learned_axis'] if a == 0 else rec['calibration_axes' if split == 'validation' else 'assessment_axes'][a-1]
                for src in sources:
                    task = src['task']; c = src['condition']
                    for op in (('zero', 'h_mean') if task == 'mmlu' else ('interchange',)):
                        for stream in src['streams']:
                            provenance = copy.deepcopy(src)
                            saved = src['streams'][stream]
                            if task not in ('ioi', 'mmlu'):
                                for k in ('expected_token', 'honest_token', 'opposite_token'):
                                    provenance[k] = saved[k]
                            provenance.update(tokens=saved['tokens'], layout=saved.get('layout'), utility_assessment=stream=='clean')
                            baseline = 2. if c in ('D', 'I') else 0.
                            drop = (1.2 if a == 0 else .2) if c == 'D' else (.2 if c == 'I' else 0.)
                            rows.append(dict(panel='calibration' if split=='validation' else split,
                                analysis_task=t, source_task=task, split=split, seed=rec['seed'], site=rec['site'],
                                family='learned' if a==0 else family, axis_index=0 if a==0 else a-1,
                                operation=op, instance_id=src['instance_id'], condition=c, stream=stream,
                                axis_hash=desc['sha256'], source_provenance=provenance,
                                expected_token=2, honest_token=1, opposite_token=2,
                                intact_margin=baseline, patched_margin=baseline-drop,
                                intact_correct=True, patched_correct=True, intact_argmax=2, patched_argmax=2,
                                epsilon=1e-6, supported=True, replay_valid=True, gate_valid=True,
                                replay_errors={'empty':0., 'head_self':0., 'zero_coefficient':0.},
                                positive_control={'valid':True}, head_norm=.1, residual_norm=.1))
        panels[split] = rows
    return design, selected, panels


def altered(rows, predicate, **changes):
    out = list(rows); i = next(i for i,r in enumerate(rows) if predicate(r))
    out[i] = dict(rows[i], **changes)
    return out


def test_pack_exact_strict_schema_and_scalar_oracle(fixture):
    d, s, p = fixture
    panel = reporting.pack_statistics_panel(d, s, p['validation'], split='validation')
    prepared, _, _ = stats._prepare(panel, power=True)
    assert set(panel['tasks']) == set(stats.TASKS)
    assert panel['axis_ids'] == ['learned']+list(range(32))
    task = prepared['far_v2']
    metrics = stats._evaluate(task, [0,1], {'IOI':['ioiv0','ioiv1'], 'MMLU':['mmluv'+str(i) for i in range(32)]})
    assert metrics['D_fraction'][0].tolist() == pytest.approx([.6]*3)
    assert metrics['I_fraction'][0].tolist() == pytest.approx([.1]*3)
    assert metrics['point_pass'][0].all()
    assert panel['tasks']['far_v2']['pressure_texts'] == ['word 0','word 1']
    assert np.asarray(panel['tasks']['far_v2']['conditions']['D']['patched_margin']).shape == (33,3,2,2)


@pytest.mark.parametrize('problem', ['missing','duplicate','axis','baseline','utility','label','validity','provenance','pilot','margin'])
def test_corrupt_or_incomplete_panel_rejected(fixture, problem):
    d,s,p = fixture; rows = p['validation']
    if problem == 'missing': rows = rows[1:]
    elif problem == 'duplicate': rows = rows+[rows[0]]
    elif problem == 'axis': rows = altered(rows, lambda r:True, axis_hash='0'*64)
    elif problem == 'baseline': rows = altered(rows, lambda r:r['family']=='calibration_null', intact_margin=99.)
    elif problem == 'utility': rows = [r for r in rows if r['source_task']!='mmlu']
    elif problem == 'label': rows = altered(rows, lambda r:True, expected_token=3)
    elif problem == 'validity': rows = altered(rows, lambda r:True, replay_valid=False)
    elif problem == 'provenance': rows = altered(rows, lambda r:True, source_provenance={})
    elif problem == 'pilot': rows = altered(rows, lambda r:True, panel='selected_pilot')
    elif problem == 'margin': rows = altered(rows, lambda r:True, patched_margin=float('nan'))
    with pytest.raises(ValueError): reporting.pack_statistics_panel(d,s,rows,split='validation')


def test_secondary_rows_do_not_replace_primary(fixture):
    d,s,p=fixture; rows=p['validation']
    extra=dict(rows[0],operation='zero',patched_margin=-999.)
    panel=reporting.pack_statistics_panel(d,s,rows+[extra],split='validation')
    assert np.asarray(panel['tasks']['far_v2']['conditions']['D']['patched_margin'])[0,0,0,0] == .8
    with pytest.raises(ValueError): reporting.pack_statistics_panel(d,s,rows[1:]+[extra],split='validation')


def test_validation_excludes_assessment_prompt_and_source_alias(fixture):
    d,s,p=fixture
    for key in ('source_id','prompt'):
        changed=copy.deepcopy(d)
        changed['ioi_validation'][0][key] = d['utility']['ioi'][0][key]
        with pytest.raises(ValueError): reporting.pack_statistics_panel(changed,s,p['validation'],split='validation')
    with pytest.raises(ValueError): reporting.pack_statistics_panel(d,s,p['assessment'],split='validation')


def test_duplicate_selected_or_missing_axes_rejected(fixture):
    d,s,p=fixture
    changed=dict(s, selected_records=s['selected_records']+[s['selected_records'][0]])
    with pytest.raises(ValueError): reporting.pack_statistics_panel(d,changed,p['validation'],split='validation')
    changed=copy.deepcopy(s); changed['selected_records'][0]['calibration_axes'].pop()
    with pytest.raises(ValueError): reporting.pack_statistics_panel(d,changed,p['validation'],split='validation')


def test_sdr_same_gates_rank_and_paired_intervals_no_holm(fixture):
    d,s,p=fixture
    result=reporting.summarize_descriptive_sdr(d,s,p['assessment'],n_boot=3,seed=9001)
    assert result['descriptive_only'] is True
    assert 'holm_reject' not in result
    assert result['comparison']['p_value']==.005
    assert result['comparison']['strict_null_pass'] is True
    assert all(r['point_pass'] for r in result['seeds'])
    assert result['intervals']['D_fraction']==pytest.approx(np.array([[.6,.6]]*3))


def test_summary_hash_links_and_injected_cannot_finalize(fixture):
    d,s,p=fixture
    refs={name:dict(sha256=digest(value),nbytes=len(json.dumps(value,sort_keys=True,separators=(',',':')).encode()))
          for name,value in [('design',d),('selected',s),('rows',p['assessment'])]}
    result=reporting.assemble_direction_summary(d,s,p['assessment'],input_references=refs,n_boot=2)
    assert set(result['confirmatory']['tasks'])==set(stats.TASKS)
    assert result['descriptive_sdr']['descriptive_only'] is True
    assert result['finalized'] is False
    assert result['input_references']==refs
    with pytest.raises(ValueError): reporting.assemble_direction_summary(d,s,p['assessment'],input_references=refs,final=True,n_boot=2)
    stale=copy.deepcopy(refs); stale['rows']['sha256']='0'*64
    with pytest.raises(ValueError): reporting.assemble_direction_summary(d,s,p['assessment'],input_references=stale,n_boot=2)


def test_scalar_runner_oracle_matches_normalization(fixture):
    from component_analysis.a3_direction_runner import direction_point_metrics
    d,s,p=fixture
    subset=[r for r in p['validation'] if r['analysis_task']=='far_v2' and r['seed']==42 and r['family']=='learned']
    scalar=direction_point_metrics(subset,seed=42)
    panel=reporting.pack_statistics_panel(d,s,p['validation'],split='validation')
    prepared,utility,_=stats._prepare(panel,power=True)
    rng=np.random.default_rng(1)
    metric=stats._evaluate(prepared['far_v2'],[0,1],stats._utility_draws(utility,rng,bootstrap=False))
    assert scalar['D_fraction']==pytest.approx(metric['D_fraction'][0,0])
    assert scalar['I_fraction']==pytest.approx(metric['I_fraction'][0,0])
    assert scalar['point_pass']==bool(metric['point_pass'][0,0])


def test_mixed_assessment_leakage_blocks_calibration(fixture):
    d,s,p=fixture
    with pytest.raises(ValueError):
        reporting.pack_statistics_panel(d,s,p['validation']+[p['assessment'][-1]],split='validation')


def test_invalid_denominator_remains_failed_unavailable(fixture):
    d,s,p=fixture
    rows=[dict(r,intact_margin=0.,patched_margin=0.) if r['analysis_task']=='sdr_v2' and r['condition']=='D' else r
          for r in p['assessment']]
    result=reporting.summarize_descriptive_sdr(d,s,rows,n_boot=2)
    assert result['comparison']['failed_learned_triplet'] is True
    assert result['comparison']['learned_statistic'] is None
    assert result['comparison']['p_value']==1.
    assert result['intervals']['D_fraction']==[None]*3
    assert all(r['D_fraction'] is None and not r['denominator_valid'] for r in result['seeds'])


def test_changed_selected_design_binding_rejected(fixture):
    d,s,p=fixture
    stale=dict(s,inventory_identity={'design_sha256':'0'*64})
    with pytest.raises(ValueError): reporting.pack_statistics_panel(d,stale,p['validation'],split='validation')


@pytest.mark.parametrize('missing', ['null','seed','stream'])
def test_complete_axis_seed_stream_inventory_required(fixture, missing):
    d,s,p=fixture
    def omit(r):
        return ((r['family']=='calibration_null' and r['axis_index']==31) if missing=='null' else
                r['seed']==123 if missing=='seed' else r['stream']=='corrupt')
    rows=[r for r in p['validation'] if not omit(r)]
    with pytest.raises(ValueError): reporting.pack_statistics_panel(d,s,rows,split='validation')


def test_production_row_requires_real_opposite_stream_map(fixture):
    d,s,p=fixture
    row=copy.deepcopy(p['validation'][0]); axis=s['selected_records'][0]['learned_axis']
    row['numeric_profile']={'model':'frozen','source_sha256':'a'*64}
    row['profile_id']=digest(row['numeric_profile'])
    row['positive_control']={'valid':True,'profile_id':row['profile_id'],'control_id':'b'*64,'recipient_sha256':'c'*64}
    with pytest.raises(ValueError):
        reporting._validate_row(row,row['source_provenance'],axis,injected=False)


def test_missing_diagnostics_are_explicit_and_not_ready(fixture):
    d,s,p=fixture
    result=reporting.summarize_direction_diagnostics(d,s,p['assessment'])
    assert result['complete'] is False
    assert result['probes']['status']=='incomplete'
    assert all(group['reason'] for group in result['groups'] if group['status']!='complete')
    assert any(g['family']=='steering_learned' and g['status']=='incomplete' for g in result['groups'])


def diagnostic_fixture(fixture):
    d,s,p=fixture; selected=copy.deepcopy(s); diagnostics=[]
    selected['fit_reference']={'completion_sha256':'a'*64}
    for rec in selected['selected_records']:
        descriptor=dict(reference=rec['learned_axis']['reference']+'-nuisance',sha256=digest(rec['learned_axis']['reference']+'-nuisance'))
        rec['nuisance']={'status':'fitted','axis':descriptor}
        selected['axes'][descriptor['reference']]={'sha256':descriptor['sha256']}
        primary=[r for r in p['assessment'] if r['analysis_task']==rec['task'] and r['seed']==rec['seed'] and r['family']=='learned']
        diagnostics += [dict(r,family='nuisance',axis_hash=descriptor['sha256']) for r in primary]
        for family,axis in (('learned',rec['learned_axis']),('nuisance',descriptor)):
            for op in ('zero','h_mean'):
                diagnostics += [dict(r,family=family,operation=op,axis_hash=axis['sha256']) for r in primary if r['source_task']!='mmlu']
        for family,axis in (('steering_learned',rec['learned_axis']),('steering_nuisance',descriptor),('steering_random',rec['assessment_axes'][0])):
            for op in ('steer_positive','steer_negative'):
                diagnostics += [dict(r,family=family,operation=op,axis_hash=axis['sha256']) for r in primary
                                if r['source_task']!='mmlu' or r['operation']=='zero']
    return d,selected,p['assessment']+diagnostics


def test_complete_diagnostic_groups_remain_separate_and_label_ambiguity(fixture):
    d,s,rows=diagnostic_fixture(fixture)
    result=reporting.summarize_direction_diagnostics(d,s,rows)
    assert all(g['status']=='complete' for g in result['groups'])
    assert all(g.get('role_framing_ambiguity') for g in result['groups'] if g['family']=='nuisance' and g['operation']=='primary')
    assert all('point_metrics' not in g for g in result['groups'] if g['family'].startswith('steering_'))
    assert all(g['descriptive_only'] is True for g in result['groups'])
    assert result['complete'] is False  # no completed probe results
    with pytest.raises(ValueError):
        reporting.summarize_direction_diagnostics(d,s,altered(rows,lambda r:r['family']=='nuisance',axis_hash='0'*64))


def test_probe_results_require_exact_train_fit_ancestry(fixture):
    d,s,p=fixture
    with pytest.raises(ValueError):
        reporting.summarize_direction_diagnostics(d,s,p['assessment'],probe_results={'kind':'a3_direction_probe_results','complete':True})


def test_complete_probe_results_and_diagnostics_readiness(fixture):
    d,s,rows=diagnostic_fixture(fixture)
    records=[]
    for rec in s['selected_records']:
        for name in ('image_probe','metadata_probe'):
            rec[name]={'status':'fitted','bootstrap':{'seed':rec['seed']}}
            records.append(dict(task=rec['task'],seed=rec['seed'],site=rec['site'],probe=name,
                fit_receipt=rec[name],status='completed',instance_ids=d['tasks'][rec['task']]['assessment_ids'],
                conditions=['D','I'],streams=['clean','corrupt'],correct=[[[1,1],[1,1]],[[1,1],[1,1]]],balanced_accuracy=1.))
    probes=dict(kind='a3_direction_probe_results',complete=True,split='assessment',fit_reference=s['fit_reference'],records=records)
    result=reporting.summarize_direction_diagnostics(d,s,rows,probe_results=probes)
    assert result['complete'] is True
    assert result['probes']['fit_reference']==s['fit_reference']
    stale=copy.deepcopy(probes); stale['records'][0]['balanced_accuracy']=.5
    with pytest.raises(ValueError): reporting.summarize_direction_diagnostics(d,s,rows,probe_results=stale)
    stale=copy.deepcopy(probes); stale['fit_reference']={'completion_sha256':'0'*64}
    with pytest.raises(ValueError): reporting.summarize_direction_diagnostics(d,s,rows,probe_results=stale)


def test_incomplete_steering_and_secondary_does_not_pass(fixture):
    d,s,rows=diagnostic_fixture(fixture)
    rows=[r for r in rows if not (r['family']=='steering_random' and r['operation']=='steer_negative' and r['source_task']=='mmlu')]
    result=reporting.summarize_direction_diagnostics(d,s,rows)
    groups=[g for g in result['groups'] if g['family']=='steering_random' and g['operation']=='steer_negative']
    assert all(g['status']=='incomplete' and 'tables' not in g for g in groups)


def test_original_ioi_retains_generated_source_split(fixture):
    d,s,p=fixture
    actual=copy.deepcopy(d)
    for row in actual['utility']['ioi']: row['split']='generated'
    assert reporting._sources(actual,'ioi','assessment')==actual['utility']['ioi']
    for row in actual['ioi_validation']:
        row['split']='generated'; row['analysis_split']='validation'
    assert reporting._sources(actual,'ioi','validation')==actual['ioi_validation']
    for row in actual['ioi_validation']: row.pop('analysis_split')
    with pytest.raises(ValueError): reporting._sources(actual,'ioi','validation')


def test_diagnostic_tables_keep_mmlu_operations_distinct(fixture):
    d,s,rows=diagnostic_fixture(fixture)
    result=reporting.summarize_direction_diagnostics(d,s,rows)
    group=next(g for g in result['groups'] if g['family']=='nuisance' and g['operation']=='primary')
    assert {t['operation'] for t in group['tables'] if t['source_task']=='mmlu'}=={'zero','h_mean'}


@pytest.mark.parametrize('row_margin', [0.,2.])
def test_review99_batch_replay_relative_tolerance_is_preserved(fixture,row_margin):
    import torch
    d,s,p=fixture
    row=copy.deepcopy(p['validation'][0]); axis=s['selected_records'][0]['learned_axis']
    original=torch.tensor([0.,2.],dtype=torch.float64)
    replay=torch.tensor([0.,2.00002],dtype=torch.float64)
    assert torch.allclose(original,replay,atol=1e-5,rtol=1e-5)
    assert torch.equal(original.argmax(),replay.argmax())
    measured=float((original-replay).abs().max())
    assert measured>1e-5
    row.update(intact_margin=row_margin,replay_errors={k:measured for k in row['replay_errors']},epsilon=10*measured)
    # The stored maximum covers the whole matched batch; a zero-margin member
    # must not reinterpret that maximum using its own different relative scale.
    reporting._validate_row(row,row['source_provenance'],axis,injected=True)
    too_small=dict(row,epsilon=1e-6)
    with pytest.raises(ValueError): reporting._validate_row(too_small,row['source_provenance'],axis,injected=True)
    invalid=dict(row,replay_valid=False)
    with pytest.raises(ValueError): reporting._validate_row(invalid,row['source_provenance'],axis,injected=True)


def production_diagnostic_fixture(fixture):
    d,s,_=fixture; d=copy.deepcopy(d); s=copy.deepcopy(s)
    d['injected']=False; d['tasks']={'far_v2':d['tasks']['far_v2']}; d['access_rows']={}
    d['tasks']['far_v2']['assessment_ids']=['fara'+str(j) for j in range(100)]
    d['access_rows']['far_v2']=[source('far_v2',rid,c,'test') for c in stats.CONDITIONS for rid in d['tasks']['far_v2']['assessment_ids']]
    d['utility']['ioi']=[source('ioi','ioia'+str(j),'IOI','generated') for j in range(100)]
    for src in d['utility']['ioi']: src['streams']['corrupt']=copy.deepcopy(src['streams']['clean'])
    d['direction_protocol']={}; s['injected']=False
    s['selected_records']=[r for r in s['selected_records'] if r['task']=='far_v2']; s['protocol']={}
    s['inventory_identity']=dict(design_sha256=digest(d),protocol_sha256=digest({}),model='GOOD',model_revision='REV',code_hashes={'source':'a'*64})
    profile=dict(model='GOOD',model_revision='REV',source_sha256=digest(s['inventory_identity']['code_hashes']))
    pid=digest(profile); rows=[]
    for rec in s['selected_records']:
        for task,sources in [('far_v2',d['access_rows']['far_v2']),('ioi',d['utility']['ioi']),('mmlu',d['utility']['mmlu'])]:
            for src in sources:
                for stream in (reporting.STREAMS if task=='far_v2' else ('clean',)):
                    for family in ('learned','steering_learned'):
                        for op in (('zero','h_mean') if task=='mmlu' and family=='learned' else ('interchange',) if family=='learned' else ('steer_positive',)):
                            row=dict(panel='assessment',analysis_task='far_v2',source_task=task,split='assessment',seed=rec['seed'],site=rec['site'],family=family,axis_index=0,operation=op,instance_id=src['instance_id'],condition=src['condition'],stream=stream,
                                source_provenance=reporting._source_record(src,stream,task),axis_hash=rec['learned_axis']['sha256'],numeric_profile=profile,profile_id=pid,
                                opposite_token=2,honest_token=1,expected_token=2,intact_correct=True,patched_correct=True,intact_argmax=2,patched_argmax=2,
                                intact_margin=2. if src['condition'] in ('D','I') else 0.,patched_margin=.8 if src['condition']=='D' else 1.8 if src['condition']=='I' else 0.,
                                replay_errors={'empty':0.,'head_self':0.,'zero_coefficient':0.},epsilon=1e-6,supported=True,replay_valid=True,gate_valid=True,
                                positive_control={'valid':True,'control_id':'c'*64,'profile_id':pid,'recipient_sha256':'d'*64},donor_mapping=None,head_norm=.1,residual_norm=.1)
                            if op=='interchange':
                                row['donor_mapping']=dict(supported=True,recipient_id=src['instance_id'],donor_id=src['instance_id'],recipient_condition=src['condition'],donor_condition=src['condition'],recipient_stream=stream,donor_stream='corrupt' if stream=='clean' else 'clean',recipient_positions=[1],donor_positions=[1],donor_source_hash='source',donor_profile_id=pid)
                            rows.append(row)
    return d,s,rows


@pytest.mark.parametrize('field,value',[('model','WRONG'),('model_revision','WRONG'),('source_sha256','b'*64)])
@pytest.mark.parametrize('target',['steering','reused_floor'])
def test_review99_diagnostic_profile_binds_frozen_selected_identity(fixture,field,value,target):
    d,s,rows=production_diagnostic_fixture(fixture)
    # Valid selected profile gives complete positive steering for all seeds.
    valid=reporting.summarize_direction_diagnostics(d,s,rows)
    assert all(g['status']=='complete' for g in valid['groups'] if g['family']=='steering_learned' and g['operation']=='steer_positive')
    index=next(i for i,r in enumerate(rows) if
        (r['family']=='steering_learned' if target=='steering' else r['family']=='learned' and r['source_task']=='mmlu'))
    wrong=copy.deepcopy(rows[index]); wrong['numeric_profile'][field]=value
    wrong['profile_id']=digest(wrong['numeric_profile']); wrong['positive_control']['profile_id']=wrong['profile_id']
    changed=list(rows); changed[index]=wrong
    with pytest.raises(ValueError,match='model/source profile'):
        reporting.summarize_direction_diagnostics(d,s,changed)
