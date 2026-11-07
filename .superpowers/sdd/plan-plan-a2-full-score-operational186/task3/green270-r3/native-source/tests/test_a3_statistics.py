"""Synthetic CPU contracts; no model, dataset, or assessment outcomes."""
import json
import inspect
import numpy as np
import pytest
from component_analysis import a3_statistics as stats
SEEDS=[42,1,123]
TASKS=('far_v2','ser_v2')


def panel(n_axes=33,split='validation',d=.75,i=0.,mmlu=True):
    result=dict(schema_version=1,kind='a3_direction_calibration' if split=='validation' else 'a3_direction_outcomes',
        split=split,seeds=SEEDS,axis_ids=['learned']+list(range(n_axes-1)),
        assessment_ids={t:['held-out'] for t in TASKS},assessment_utility_ids={'IOI':['held-out-ioi'],'MMLU':['held-out-mmlu']},tasks={})
    for task in TASKS:
        conditions={}
        for c in ('D','H','F','I','user_neutral'):
            intact=np.full((3,4,2),2. if c in ('D','I') else 0.)
            patched=np.repeat(intact[None],n_axes,axis=0)
            if c in ('D','I'):
                patched[0]-=2*(d if c=='D' else i);patched[1:]-=.2
            conditions[c]=dict(intact_margin=intact,patched_margin=patched,intact_correct=np.ones_like(intact),patched_correct=np.ones_like(patched))
        utilities={}
        for c,size in [('IOI',4)]+([('MMLU_zero',32),('MMLU_h_mean',32)] if mmlu else []):
            utilities[c]=dict(prompt_ids=[f'{c.split("_")[0]}-{j}' for j in range(size)],intact_correct=np.ones((3,size)),patched_correct=np.ones((n_axes,3,size)))
        result['tasks'][task]=dict(instance_ids=['a','b','c','d'],pressure_texts=['shared','shared','unique-'+task,'other-'+task],conditions=conditions,utilities=utilities,epsilon=1e-6)
    return result


def test_exact_triplet_strict_threshold_ties_and_failed_statistics():
    good=[dict(point_pass=True,D_fraction=x) for x in [.5,.75,1.]]
    assert stats.triplet_statistic(good)==.75
    assert stats.triplet_statistic([good[0],dict(point_pass=False,D_fraction=1),good[2]])==-np.inf
    result=stats.compare_triplets(.75,np.r_[np.full(189,-np.inf),np.full(10,.75)])
    assert result['null_95']==.75 and not result['strict_null_pass']
    assert result['p_value']==11/200 and result['failed_null_triplets']==189
    failed=stats.compare_triplets(-np.inf,np.full(199,-np.inf))
    assert failed['p_value']==1 and failed['failed_learned_triplet']
    assert failed['learned_statistic'] is None and failed['null_95'] is None
    json.dumps(failed,allow_nan=False)
    with pytest.raises(ValueError):stats.compare_triplets(.75,[0]*198)
    with pytest.raises(ValueError):stats.triplet_statistic(good[:2])


def test_holm_only_two_confirmatory_tasks_and_step_down():
    assert stats.holm_two({'far_v2':.025,'ser_v2':.05})=={'far_v2':True,'ser_v2':True}
    assert stats.holm_two({'far_v2':.03,'ser_v2':.04})=={'far_v2':False,'ser_v2':False}
    assert stats.holm_two({'far_v2':1.,'ser_v2':.005})=={'far_v2':False,'ser_v2':True}
    with pytest.raises(ValueError):stats.holm_two({'far_v2':.005,'ser_v2':.01,'sdr_v2':.01})


def test_incidence_draw_linkage_and_unequal_cluster_sizes():
    source={t:dict(instance_ids=['a','b','c','d'],pressure_texts=['shared-1','shared-1','shared-2','private-'+t]) for t in TASKS}
    draws=stats.draw_pressure_clusters(source,np.random.default_rng(4))
    for task in TASKS:
        assert len(draws[task]['cluster_occurrences'])==3
        shared=[(x['pressure_text'],x['occurrence']) for x in draws[task]['cluster_occurrences'] if x['pressure_text'].startswith('shared')]
        assert shared==[(x['pressure_text'],x['occurrence']) for x in draws[TASKS[0]]['cluster_occurrences'] if x['pressure_text'].startswith('shared')]
    assert len(draws['far_v2']['indices']) in (3,4,5)
    assert len(set(draws['far_v2']['occurrence_keys']))==3
    assert set(draws['far_v2']['occurrence_keys']) & set(draws['ser_v2']['occurrence_keys'])=={'1:0','1:1'}


def test_point_thresholds_stream_denominators_both_mmlu_floors():
    p=panel(200,'assessment',d=.5,i=.25)
    assert not stats.summarize_direction_outcomes(p,n_boot=3)['tasks']['far_v2']['seeds'][0]['point_pass']
    p['tasks']['far_v2']['conditions']['I']['patched_margin'][0]=1.6
    assert stats.summarize_direction_outcomes(p,n_boot=3)['tasks']['far_v2']['seeds'][0]['point_pass']
    p['tasks']['far_v2']['utilities']['MMLU_h_mean']['patched_correct'][0,:,0:2]=0
    assert not stats.summarize_direction_outcomes(p,n_boot=3)['tasks']['far_v2']['seeds'][0]['point_pass']
    p['tasks']['far_v2']['conditions']['D']['intact_margin'][:,:,0]=-1
    result=stats.summarize_direction_outcomes(p,n_boot=3)
    assert not result['tasks']['far_v2']['seeds'][0]['denominator_valid']
    json.dumps(result,allow_nan=False)


def test_assessment_paired_intervals_and_separate_gates():
    p=panel(200,'assessment')
    for task in TASKS:
        p['tasks'][task]['pressure_texts']=['x','x','y','z']
        p['tasks'][task]['conditions']['D']['patched_margin'][0]=np.array([.1,.1,.9,.9])[None,:,None]
    result=stats.summarize_direction_outcomes(p,n_boot=31)
    a=result['tasks']['far_v2']['intervals']
    assert a==result['tasks']['ser_v2']['intervals']
    assert a['D_fraction'][0]==a['D_fraction'][1]==a['D_fraction'][2]
    assert result['bootstrap']['seed']==9001
    assert result['tasks']['far_v2']['holm_reject']
    assert result['tasks']['far_v2']['comparison']['strict_null_pass']


def test_zero_noise_power_threshold_asymmetry_json_and_defaults():
    result=stats.simulate_conditional_power(panel(),n_rep=3,seed=18)
    assert len(result['scenarios'])==60
    assert result['null_approximation']['calibration_axes']==32
    def cell(mode,d,i=0,loss=0):
        return next(c for c in result['scenarios'] if (c['mode'],c['D_fraction'],c['I_fraction'],c['collateral_loss'])==(mode,d,i,loss))
    assert cell('shared',.25)['rejections']['far_v2']['probability']==0
    assert cell('shared',.5)['rejections']['far_v2']['probability']==1
    assert cell('FAR_only',.75)['any_rejection']['probability']==1
    assert cell('FAR_only',.75)['both_rejections']['probability']==0
    assert cell('SER_only',.75)['rejections']['ser_v2']['probability']==1
    assert result['detectability'][0]['bracket']==[.25,.5]
    assert inspect.signature(stats.simulate_conditional_power).parameters['n_rep'].default==2000
    json.dumps(result,allow_nan=False)


def test_calibration_only_input_and_exclusion_overlap():
    with pytest.raises(ValueError,match='validation'):stats.simulate_conditional_power(panel(33,'assessment'),n_rep=1)
    p=panel();p['assessment_ids']['far_v2']=['a']
    with pytest.raises(ValueError,match='overlap'):stats.simulate_conditional_power(p,n_rep=1)
    p=panel();p['assessment_utility_ids']['MMLU']=['MMLU-0']
    with pytest.raises(ValueError,match='overlap'):stats.simulate_conditional_power(p,n_rep=1)
    p=panel();del p['assessment_ids']
    with pytest.raises(ValueError,match='assessment_ids'):stats.simulate_conditional_power(p,n_rep=1)
    p=panel();p['assessment_outcomes']=[]
    with pytest.raises(ValueError,match='unexpected'):stats.simulate_conditional_power(p,n_rep=1)


def test_invalid_original_denominator_and_conditional_mmlu():
    p=panel(mmlu=False);p['tasks']['far_v2']['conditions']['D']['intact_margin'][:]=0
    result=stats.simulate_conditional_power(p,n_rep=2)
    assert result['conditional_on_mmlu_guard']
    first=result['scenarios'][0]
    assert not first['original_denominator_valid']['far_v2']
    assert first['rejections']['far_v2']['probability'] is None
    assert first['both_rejections']['probability'] is None and first['any_rejection']['probability'] is None
    assert first['rejections']['ser_v2']['probability']==0


def test_bernoulli_loss_edges_infeasible_and_correlated_thresholds():
    intact=np.array([[1.,0.,1.,0.]]*3);u=np.array([0.,.1,.6,.9])
    assert np.array_equal(stats.inject_correctness_loss(intact,u,loss=0),intact)
    assert np.array_equal(stats.inject_correctness_loss(intact,u,loss=.5),np.zeros_like(intact))
    assert np.array_equal(stats.inject_correctness_loss(np.zeros_like(intact),u,loss=0),np.zeros_like(intact))
    with pytest.raises(ValueError,match='infeasible'):stats.inject_correctness_loss(intact,u,loss=.6)
    assert stats.inject_correctness_loss(np.ones_like(intact),u,loss=.2)[0,1]==0
    assert stats.inject_correctness_loss(intact,u,loss=.2)[0,2]==1


def test_rng_infeasibility_and_bootstrap_denominator_weakness():
    p=panel()
    for task in TASKS:
        for c in ('H','F'):p['tasks'][task]['conditions'][c]['intact_correct'][:]=0
    a=stats.simulate_conditional_power(p,n_rep=2,seed=3)
    assert a==stats.simulate_conditional_power(p,n_rep=2,seed=3)
    bad=next(c for c in a['scenarios'] if c['collateral_loss']==.04)
    assert bad['infeasible_tasks']==list(TASKS) and bad['rejections']['far_v2']['probability'] is None
    p=panel();p['tasks']['far_v2']['pressure_texts']=['a','b','c','d']
    for c in ('D','I'):p['tasks']['far_v2']['conditions'][c]['intact_margin'][:]=np.array([-1,-1,1,2])[None,:,None]
    b=stats.simulate_conditional_power(p,n_rep=30,seed=8)
    assert b['scenarios'][0]['bootstrapped_denominator_invalid']['far_v2']>0
    assert b['scenarios'][0]['rejections']['far_v2']['n_trials']==30


def test_malformed_schema_and_incomplete_assessment_mmlu():
    for mutate in [lambda p:p.update(seeds=[42,1]),lambda p:p.update(axis_ids=['learned']+list(range(31))),
        lambda p:p['tasks']['far_v2']['conditions']['D'].update(intact_margin=np.ones((3,4,1))),
        lambda p:p['tasks']['far_v2']['conditions']['H']['intact_correct'].fill(.5)]:
        p=panel();mutate(p)
        with pytest.raises(ValueError):stats.simulate_conditional_power(p,n_rep=1)
    result=stats.summarize_direction_outcomes(panel(200,'assessment',mmlu=False),n_boot=2)
    assert not result['tasks']['far_v2']['seeds'][0]['point_pass']


def test_each_seed_gate_required_and_exact_collateral_boundary():
    p=panel(200,'assessment')
    # Exactly 1/20 accuracy movement is a failure even with a finite null rank.
    for t in TASKS:
        for c in p['tasks'][t]['conditions'].values():
            for name in tuple(c):
                c[name]=np.repeat(c[name],5,axis=1 if name.startswith('intact') else 2)
        p['tasks'][t]['instance_ids']=[str(i) for i in range(20)]
        p['tasks'][t]['pressure_texts']=['same']*20
    p['tasks']['far_v2']['conditions']['H']['patched_correct'][0,1,0]=0
    r=stats.summarize_direction_outcomes(p,n_boot=2)
    assert not r['tasks']['far_v2']['seeds'][1]['point_pass']
    assert r['tasks']['far_v2']['comparison']['p_value']==1
    assert not r['tasks']['far_v2']['holm_reject']
    assert r['tasks']['ser_v2']['holm_reject']


def test_observed_null_outcomes_unchanged_by_synthetic_effects():
    p=panel()
    for t in TASKS:
        # Every observed calibration null passes with stronger removal than
        # the injected .75: it must defeat the learned scenario, not be shifted.
        p['tasks'][t]['conditions']['D']['patched_margin'][1:]=.2
        p['tasks'][t]['conditions']['I']['patched_margin'][1:]=2
    r=stats.simulate_conditional_power(p,n_rep=5)
    c=next(s for s in r['scenarios'] if (s['mode'],s['D_fraction'],s['I_fraction'],s['collateral_loss'])==('shared',.75,0,0))
    assert c['rejections']['far_v2']['probability']==0
    assert r['calibration_coverage']['far_v2']['failed_null_triplets']['total']==0


def test_occurrence_uniforms_share_stream_seed_and_task_but_not_repeat():
    # Distinct occurrence keys must allow two copies of one cluster to flip
    # differently while all three seeds and both designation streams agree.
    p=panel()
    for t in TASKS:p['tasks'][t]['pressure_texts']=['same']*4
    tasks,_,_=stats._prepare(p,power=True)
    utility={'IOI':tasks['far_v2']['utilities']['IOI']['prompt_ids'],
             'MMLU':tasks['far_v2']['utilities']['MMLU_zero']['prompt_ids']}
    u={'H':np.array([0,0,1,1]),'F':np.array([0,0,1,1]),'IOI':np.ones(4),'MMLU':np.ones(32)}
    a=stats._evaluate(tasks['far_v2'],[0,1,0,1],utility,synthetic=[(.75,0,.04)],uniforms=u,conditional_mmlu=True)
    b=stats._evaluate(tasks['ser_v2'],[0,1,0,1],utility,synthetic=[(.75,0,.04)],uniforms=u,conditional_mmlu=True)
    assert np.array_equal(a['collateral_shifts']['H'],b['collateral_shifts']['H'])
    assert np.array_equal(a['collateral_shifts']['H'],np.full((1,3),-.5))


def test_paired_prompt_bootstrap_does_not_resample_utility_by_seed_or_task():
    p=panel(200,'assessment')
    for t in TASKS:
        p['tasks'][t]['utilities']['IOI']['patched_correct'][0,:,0]=0
    result=stats.summarize_direction_outcomes(p,n_boot=23)
    a=result['tasks']['far_v2']['intervals']['IOI_shift']
    assert a[0]==a[1]==a[2]
    assert a==result['tasks']['ser_v2']['intervals']['IOI_shift']


def test_weak_negative_nonfinite_denominators_never_clipped():
    for gap in [1e-9,-1,np.inf]:
        p=panel()
        p['tasks']['far_v2']['conditions']['D']['intact_margin'][:]=gap
        # Finite numerator prevents unrelated subtraction of two infinities.
        if not np.isfinite(gap):
            p['tasks']['far_v2']['conditions']['D']['patched_margin'][:]=0
        with np.errstate(invalid='ignore'):
            r=stats.simulate_conditional_power(p,n_rep=1)
        assert r['scenarios'][0]['rejections']['far_v2']['probability'] is None
        json.dumps(r,allow_nan=False)


def test_bootstrap_invalid_draw_counts_gate_failure_and_mc_intervals():
    p=panel();p['tasks']['far_v2']['pressure_texts']=['a','b','c','d']
    for c in ('D','I'):p['tasks']['far_v2']['conditions'][c]['intact_margin'][:]=np.array([-1,-1,1,2])[None,:,None]
    result=stats.simulate_conditional_power(p,n_rep=23,seed=8)
    cell=result['scenarios'][0]
    assert 0<cell['bootstrapped_denominator_invalid']['far_v2']<23
    assert cell['any_seed_gate_failure_frequency']['far_v2'] is not None
    assert 0<=cell['any_seed_gate_failure_frequency']['far_v2']<=1
    mc=cell['rejections']['ser_v2']
    assert mc['mc_interval'][0]<=mc['probability']<=mc['mc_interval'][1]


def test_duplicate_ids_missing_conditions_mismatched_utility_and_partial_axes():
    mutations=[lambda p:p['tasks']['far_v2'].update(instance_ids=['a','a','c','d']),
        lambda p:p['tasks']['far_v2']['conditions'].pop('F'),
        lambda p:p['tasks']['far_v2']['utilities']['MMLU_zero']['prompt_ids'].__setitem__(0,'other'),
        lambda p:p['tasks']['far_v2']['utilities'].pop('MMLU_zero'),
        lambda p:p['tasks']['far_v2']['conditions']['D'].update(patched_margin=np.zeros((32,3,4,2)))]
    for mutate in mutations:
        p=panel();mutate(p)
        with pytest.raises(ValueError):stats.simulate_conditional_power(p,n_rep=1)


def test_detectability_uses_smallest_detectable_tested_fraction():
    scenarios=stats._scenarios()
    for s in scenarios:
        p=1. if s['D_fraction'] in (0.,.5,.75,1.) else 0.
        s['rejections']={t:{'probability':p} for t in TASKS}
    assert stats._detectability(scenarios)[0]['bracket'] is None


def test_unequal_clusters_keep_id_weighting_in_raw_ratio_not_cluster_means():
    p=panel(200,'assessment')
    p['tasks']['far_v2']['conditions']['D']['patched_margin'][0]=np.array([0.,0.,2.,2.])[None,:,None]
    r=stats.summarize_direction_outcomes(p,n_boot=1)
    seed=r['tasks']['far_v2']['seeds'][0]
    assert seed['D_fraction']==.5
    assert seed['raw']['D']['intact_margin']==2.
    assert seed['raw']['D']['patched_margin']==1.
    # A cluster-mean estimator would average 1,0,0 and give 1/3.
    assert seed['D_fraction']!=pytest.approx(1/3)


def test_missing_fields_and_cross_kind_leakage_rejected():
    p=panel();p['tasks']['far_v2']['split']='assessment'
    with pytest.raises(ValueError,match='unexpected'):stats.simulate_conditional_power(p,n_rep=1)
    p=panel();p['tasks']['far_v2']['conditions']['D'].pop('intact_margin')
    with pytest.raises(ValueError):stats.simulate_conditional_power(p,n_rep=1)
