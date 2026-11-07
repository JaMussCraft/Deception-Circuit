import copy
import pytest
from component_analysis.ladder_metrics import summarize_ladder


def rows(n=4, d_drop=1., i_drop=.1):
    out=[]
    for i in range(n):
        for c, base, drop in [('D', 3.+i, d_drop), ('H',1.+i,0), ('F',1.,0), ('I',2.,i_drop), ('user_neutral',1.,0), ('IOI',1.,0)]:
            for stream in (('clean',) if c=='IOI' else ('clean','corrupt')):
                out.append(dict(task='far_v2' if c!='IOI' else 'ioi',instance_id=str(i), pressure_id=str(i//2), condition=c,stream=stream,group='full',group_members=[['mlp',0,0]],operation='item_swap',intact_margin=base,patched_margin=base-drop,intact_correct=True,patched_correct=True,supported=True,gate_valid=True,self_replay_margin_error=0.))
    return out


def test_ratio_of_means_and_clustered_bootstrap():
    result=summarize_ladder(rows(), n_boot=100)
    cell=result['cells'][0]
    assert cell['D']['gap']==2
    assert cell['D']['fraction_removed']==.5
    assert cell['I']['fraction_removed']==pytest.approx(.1)
    assert cell['point_pass']
    assert cell['n_clusters']==2
    assert cell['D']['fraction_interval']==[.5,.5]
    assert result==summarize_ladder(rows(), n_boot=100)


@pytest.mark.parametrize('drop,pass_', [(1.,True),(.9999,False)])
def test_inclusive_d_gate(drop,pass_):
    assert summarize_ladder(rows(d_drop=drop), n_boot=10)['cells'][0]['point_pass']==pass_


def test_strict_i_gate_and_absolute_accuracy_gate():
    assert not summarize_ladder(rows(i_drop=.25),n_boot=10)['cells'][0]['point_pass']
    source=rows(n=20)
    for r in source:
        if r['condition']=='H' and r['instance_id']=='0':
            r['intact_correct']=False  # improvement is collateral too
    cell=summarize_ladder(source,n_boot=10)['cells'][0]
    assert cell['collateral']['H']['accuracy_shift']==pytest.approx(.05)
    assert not cell['point_pass']


def test_nonpositive_gap_or_single_stream_nonpositive_is_uninterpretable():
    source=rows()
    for r in source:
        if r['condition']=='D' and r['stream']=='clean': r['intact_margin']=0
    cell=summarize_ladder(source,n_boot=10)['cells'][0]
    assert not cell['interpretable']
    assert not cell['point_pass']


def test_missing_stream_and_required_unsupported_are_visible():
    source=rows()
    source.pop(0)
    with pytest.raises(ValueError,match='stream'): summarize_ladder(source,n_boot=10)
    source=rows(); source[0]['supported']=False
    cell=summarize_ladder(source,n_boot=10)['cells'][0]
    assert cell['coverage']['unsupported']==1
    assert not cell['point_pass']


def test_h_twin_degenerate_h_does_not_count_as_honesty():
    source=rows()
    for r in source:
        r['operation']='h_twin'
        if r['condition']=='H': r['gate_valid']=False; r['degenerate']=True
    cell=summarize_ladder(source,n_boot=10)['cells'][0]
    assert not cell['point_pass']
    assert not cell['collateral']['H']['nontrivial']


def test_native_tasks_remain_separate_and_ambiguous_task_rejected():
    source=rows()
    for r in source: r['task']='far_v2' if r['condition']!='IOI' else 'ioi'
    other=[dict(r,task='ser_v2',patched_margin=r['intact_margin']) for r in source if r['condition']!='IOI']
    result=summarize_ladder(source+other,n_boot=10)
    assert len(result['cells'])==2
    assert result['cells'][0]['D']['fraction_removed']==.5
    assert result['cells'][1]['D']['fraction_removed']==0
    source[0]['task']='unknown'
    with pytest.raises(ValueError,match='task'): summarize_ladder(source,n_boot=10)


def test_independent_seeds_average_within_recipient_and_outer_bootstrap():
    source=[]
    for seed,drop in ((101,0.),(102,1.),(103,2.)):
        source.extend(dict(r,operation='independent_resample',donor_seed=seed) for r in rows(d_drop=drop))
    result=summarize_ladder(source,n_boot=100)
    cell=result['cells'][0]
    assert cell['D']['fraction_removed']==.5
    assert cell['donor_seeds']==[101,102,103]
    assert cell['D']['fraction_interval'][0]<.5<cell['D']['fraction_interval'][1]
    assert not cell['strong']


def test_ratio_is_not_mean_of_row_ratios_and_streams_pair_within_id():
    source=rows(n=2)
    for r in source:
        if r['condition']=='D':
            r['intact_margin']=2. if r['instance_id']=='0' else 4.
            r['patched_margin']=r['intact_margin']-1
        if r['condition']=='H': r['intact_margin']=1.;r['patched_margin']=1.
    cell=summarize_ladder(source,n_boot=10)['cells'][0]
    assert cell['D']['fraction_removed']==.5  # 1/mean(1,3), not mean(1/1,1/3)


def test_mmlu_is_fixed_32_utility_rows_and_not_pressure_denominator():
    source=[dict(r,operation='zero') for r in rows()]
    for i in range(32):
        source.append(dict(source[-1],task='mmlu',condition='MMLU',instance_id=f'm{i}',intact_margin=1000.,patched_margin=-1000.,intact_correct=True,patched_correct=i!=0))
    cell=summarize_ladder(source,n_boot=10)['cells'][0]
    assert cell['MMLU']['pass']
    assert cell['MMLU']['additional_errors']==1
    assert len(cell['MMLU']['shift_interval'])==2
    assert len(cell['MMLU']['additional_errors_interval'])==2
    assert cell['D']['gap']==2
    source[-2]['patched_correct']=False
    assert not summarize_ladder(source,n_boot=10)['cells'][0]['point_pass']


def test_missing_independent_seed_is_rejected():
    source=[dict(r,operation='independent_resample',donor_seed=101) for r in rows()]
    with pytest.raises(ValueError,match='101.*102.*103'):
        summarize_ladder(source,n_boot=10)


def test_exact_five_percentage_point_decline_does_not_pass_by_roundoff():
    source=rows(n=20)
    for r in source:
        if r['condition']=='H':
            r['intact_correct']=r['instance_id']!='0'
            r['patched_correct']=r['instance_id'] not in ('0','1')
    cell=summarize_ladder(source,n_boot=10)['cells'][0]
    assert cell['collateral']['H']['accuracy_shift']==pytest.approx(-.05)
    assert not cell['point_pass']


def test_group_label_with_conflicting_memberships_is_rejected():
    source=rows()
    for r in source: r['group_members']=[['mlp',0,0]]
    source[0]['group_members']=[['head',0,1]]
    with pytest.raises(ValueError,match='membership'):summarize_ladder(source,n_boot=10)


def test_unsupported_f_twin_preserves_native_effects_without_certification():
    source=[dict(r,operation='h_twin') for r in rows()]
    for r in source:
        if r['condition']=='F':
            r['supported']=False
            for field in ('patched_margin','patched_correct'): r.pop(field)
        if r['condition']=='H': r.update(gate_valid=False,degenerate=True)
    cell=summarize_ladder(source,n_boot=10)['cells'][0]
    assert cell['D']['fraction_removed']==.5 and cell['I']['fraction_removed']==pytest.approx(.1)
    assert cell['coverage']['by_condition']['F']['unsupported']==8
    assert cell['collateral']['F']['accuracy_shift'] is None
    assert not cell['point_pass'] and not cell['strong']


def test_local_gate_and_complete_assay_readiness_are_distinct():
    source=rows()
    result=summarize_ladder(source,n_boot=10)
    assert result['cells'][0]['point_pass']
    assert not result['cells'][0]['complete_assay_ready']
    assert result['cells'][0]['assay_readiness']['MMLU']['missing_operations']==['zero','h_mean']
    source.extend(dict(r,operation=op) for op in ('zero','h_mean','h_twin') for r in rows() if r['condition']!='IOI')
    for op in ('zero','h_mean'):
        source.extend(dict(source[-1],task='mmlu',condition='MMLU',operation=op,
                           instance_id=f'm{i}',stream='clean') for i in range(32))
    cell=summarize_ladder(source,n_boot=10)['cells'][0]
    assert cell['complete_assay_ready']
    assert cell['assay_readiness']['MMLU']['complete']
    source[-1]['supported']=False
    assert not summarize_ladder(source,n_boot=10)['cells'][0]['complete_assay_ready']


def test_partial_independent_support_is_diagnostic_and_keeps_fixed_sample():
    source=[dict(r,operation='independent_resample',donor_seed=seed)
            for seed in (101,102,103) for r in rows()]
    source[0]['supported']=False
    source[0].pop('patched_margin'); source[0].pop('patched_correct')
    cell=summarize_ladder(source,n_boot=10)['cells'][0]
    assert cell['n_assessment_ids']==4
    assert cell['supported_subset']['ids']==['1','2','3']
    assert cell['supported_subset']['n_ids']==3
    assert cell['D']['fraction_removed']==.5
    assert not cell['point_pass'] and not cell['strong']
    assert cell['assessment_sample_changed'] is False


def test_mmlu_cannot_supply_an_invented_item_swap_gate():
    source=rows()
    source.append(dict(source[-1],task='mmlu',condition='MMLU',instance_id='m0'))
    with pytest.raises(ValueError,match='MMLU.*operation'):
        summarize_ladder(source,n_boot=10)


def test_readiness_allows_documented_f_twin_gap_but_never_changes_primary_gate():
    source=rows()
    for op in ('zero','h_mean','h_twin'):
        for r in rows():
            if r['condition']=='IOI': continue
            r=dict(r,operation=op)
            if op=='h_twin' and r['condition']=='F': r['supported']=False
            if op=='h_twin' and r['condition']=='H': r.update(gate_valid=False,degenerate=True)
            source.append(r)
    for op in ('zero','h_mean'):
        source.extend(dict(rows()[-1],task='mmlu',condition='MMLU',operation=op,
                           instance_id=f'm{i}',stream='clean') for i in range(32))
    cells=summarize_ladder(source,n_boot=10)['cells']
    twin=next(c for c in cells if c['operation']=='h_twin')
    primary=next(c for c in cells if c['operation']=='item_swap')
    assert primary['complete_assay_ready'] and primary['point_pass']
    assert not twin['point_pass'] and twin['D']['fraction_removed']==.5
    for r in source:
        if r['condition']=='IOI': r['operation']='zero'
    primary=next(c for c in summarize_ladder(source,n_boot=10)['cells'] if c['operation']=='item_swap')
    assert not primary['point_pass'] and not primary['complete_assay_ready']


def test_missing_independent_seed_for_one_pair_is_not_silent_subset_selection():
    source=[dict(r,operation='independent_resample',donor_seed=seed)
            for seed in (101,102,103) for r in rows()]
    source=[r for r in source if not (r['condition']=='D' and r['instance_id']=='0' and r['donor_seed']==101)]
    with pytest.raises(ValueError,match='paired ids|seed coverage'):
        summarize_ladder(source,n_boot=10)
