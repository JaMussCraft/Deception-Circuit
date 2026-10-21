"""Frozen SDR validation contracts; no pretrained model inference."""
import copy
import importlib.util
from pathlib import Path
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = Path('/projects/beto/swong2/Alignment/Deception-Circuit')

@pytest.fixture(scope='module')
def runner():
    path = ROOT/'scripts/sdr_routing_validation.py'
    assert path.is_file(), 'new validation runner missing'
    spec = importlib.util.spec_from_file_location('validation', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture(scope='module')
def tokenizer(runner):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(str(runner.CACHE), local_files_only=True)

@pytest.fixture(scope='module')
def manifest(runner, tokenizer):
    return runner.build_validation_manifest(tokenizer, primary_root=PRIMARY)


def test_complete_factorial_and_exact_donor_axes(manifest):
    rows = manifest['panel']; by = {v['variant_id']:v for v in rows}
    assert len(rows)==1280
    assert sum(v['population']=='fresh' for v in rows)==1024
    assert len(manifest['pairs'])==3584
    for pair in manifest['pairs']:
        r,d = by[pair['recipient_id']],by[pair['donor_id']]
        assert r['story_id']==d['story_id']
        assert [k for k in r['factors'] if r['factors'][k]!=d['factors'][k]]==[pair['factor']]
    assert manifest['grid']['scientific_rows']==45824


def test_stakes_and_task_precede_record(manifest):
    for v in manifest['panel']:
        if v['population']=='fresh':
            assert v['anchors']['task']['span'][1] <= v['anchors']['stakes']['span'][0]
            assert v['anchors']['stakes']['span'][1] <= v['anchors']['record']['span'][0]


def test_truth_flip_swaps_predicates_not_record_name_order(manifest):
    by={v['variant_id']:v for v in manifest['panel']}
    for p in manifest['pairs']:
        if p['axis']=='T' and by[p['recipient_id']]['population']=='fresh':
            r,d=by[p['recipient_id']],by[p['donor_id']]
            assert r['record_order']==d['record_order']
            assert r['truthful_item']!=d['truthful_item']
            assert r['anchors']['record']['text'].replace('damaged','STATUS').replace('intact','STATUS')==d['anchors']['record']['text'].replace('damaged','STATUS').replace('intact','STATUS')


def test_named_truth_favored_correct_answer_distinct_fields(manifest):
    for v in manifest['panel']:
        assert v['truth_id']==v['correct_answer_id']==v['report_target_id']
        assert all(k in v for k in ('favored_id','truthful_item','correct_answer_item','report_target_item'))
        assert v['truth_id']!=v['other_id']


def test_sources_use_real_sample_json_and_exclude_prior_stories(manifest):
    h=manifest['historical']
    assert len(h['component_sample_files'])==25
    assert len(h['component_source_ids'])==139
    assert len(h['selective_source_ids'])==64
    assert not set(h['native_excluded_story_ids']) & {g['story_id'] for g in manifest['groups'] if g['population']=='native'}
    assert not set(h['fresh_excluded_story_ids']) & {g['story_id'] for g in manifest['groups'] if g['population']=='fresh'}


def test_fresh_fixtures_are_compositional_not_population_holdout(manifest):
    assert manifest['population_claim']=='compositional fixtures; familiar entities/items/templates; native historically exposed'
    assert len(manifest['groups'])==96
    assert manifest['selection_exclusions']


def test_split_bundle_and_hash_domains_do_not_leak(manifest):
    fresh=[g for g in manifest['groups'] if g['population']=='fresh']
    assert len(set(manifest['hash_domains'].values()))==3
    for template in ('A','B'):
        for split in ('exploration','confirmation'):
            group=[g for g in fresh if g['template']==template and g['split']==split]
            assert len(group)==16
            assert sum(g['order'] for g in group)==8
    assert manifest['overlap']['fresh_item_pair_split_overlap']==[]


def test_primary_support_intersection_identical_across_donor_axes(manifest):
    grouped={}
    for p in manifest['pairs']:
        support={x for x,y in manifest['maps'][p['pair_id']]['common']}
        if p['recipient_id'] in grouped: assert support==grouped[p['recipient_id']]
        grouped[p['recipient_id']]=support


def test_primary_support_identical_between_report_and_retrieval(manifest):
    by={v['variant_id']:v for v in manifest['panel']}
    supports={}
    for p in manifest['pairs']:
        v=by[p['recipient_id']]
        if v['population']!='fresh':continue
        key=(v['story_id'],v['factors']['truth'],v['factors']['favored'],v['factors']['stakes'])
        roles=set(tuple(x) for x in v['primary_role_support'])
        if key in supports:assert roles==supports[key]
        supports[key]=roles


def test192_no_truncation_and_stem_token_injectivity(manifest):
    assert manifest['physical_shape']==[8,192]
    for v in manifest['panel']:
        assert v['valid'] and v['length']==len(v['ids'])<=192
        assert len(set(v['item_ids'].values()))==2


def test_changed_clauses_omitted_from_semantic_map(manifest):
    by={v['variant_id']:v for v in manifest['panel']}
    for p in manifest['pairs']:
        r,d=by[p['recipient_id']],by[p['donor_id']]
        mapping=manifest['maps'][p['pair_id']]['common']
        assert all(r['ids'][a]==d['ids'][b] for a,b in mapping)
        assert not {a for a,b in mapping}&set(r['segments'].get('stakes',[]))
        assert not {a for a,b in mapping}&set(r['segments'].get('favored',[]))


def test_native_neutral_deletes_only_pressure(manifest):
    by={v['variant_id']:v for v in manifest['panel']}
    from dataset.matched_honest import replace_clause
    for p in manifest['pairs']:
        r,d=by[p['recipient_id']],by[p['donor_id']]
        if p['axis']=='P' and r['factors']['pressure']:
            assert replace_clause(r['prompt'],r['pressure'],'')==d['prompt']


def test_native_order_truth_suffix_consistent(manifest):
    for v in manifest['panel']:
        if v['population']=='native':
            assert '.THE DAMAGING ONE' in v['prompt']
            assert v['truthful_item']==v['items'][v['factors']['truth']]


def test_dummy_padding_readout_positions_stable(runner):
    from component_analysis.hooks import readout_positions
    ids,mask=runner.validation_batch([{'ids':[7,8,9],'length':3}], 'cpu')
    assert tuple(ids.shape)==(8,192)
    assert mask.sum(1).tolist()==[3,1,1,1,1,1,1,1]
    assert readout_positions(mask).tolist()==[2,0,0,0,0,0,0,0]
    with pytest.raises(ValueError):runner.validation_batch([{'ids':[1]*193,'length':193}],'cpu')


def rows_for_gate(manifest):
    return [dict(variant_id=v['variant_id'],emitted_id=v['truth_id'],truth_margin=1.,p_truth=.9,p_other=.05,other_mass=.05,fp32_checksum='x') for v in manifest['panel']]


def controls_for_gate(manifest):
    receipt={'pass':True,'bitwise':True,'max_abs_error':0.,'explanation':'exact synthetic gate fixture'}
    return [{**receipt,'control':'all_component_self','variant_ids':[v['variant_id'] for v in manifest['panel']]}]+[
        {**receipt,'control':name} for name in ('empty_recapture','no_sender_two_pass_all192','self_sender_two_pass_all192')]


def test80percent_gate_is_per_template_truth_and_keeps_all_rows(runner,manifest):
    rows=rows_for_gate(manifest)
    assert runner.evaluate_validity(manifest,rows,controls_for_gate(manifest))['paths_go']
    by={v['variant_id']:v for v in manifest['panel']}
    for r in rows:
        v=by[r['variant_id']]
        if v['population']=='fresh' and v['template']=='A' and v['factors']['truth']==0 and v['factors']['task']=='retrieval' and v['factors']['stakes']==0:r['emitted_id']=v['other_id']
    gate=runner.evaluate_validity(manifest,rows,controls_for_gate(manifest))
    assert not gate['paths_go'] and gate['completed_baselines']==1280


def test_no_stakes_or_emission_threshold(runner,manifest):
    assert runner.evaluate_validity(manifest,rows_for_gate(manifest),controls_for_gate(manifest))['paths_go']


def test_nonitem_is_not_refusal(runner):
    assert runner.emission_class(99,{'truth_id':1,'other_id':2})=='non_item'


def test_failed_gate_does_not_resample_or_tune(runner,manifest):
    before=runner.digest(manifest)
    assert not runner.evaluate_validity(manifest,[],[])['paths_go']
    assert runner.digest(manifest)==before


def test_dryrun_does_not_load_model_or_cuda(runner,manifest,tmp_path,monkeypatch):
    from types import SimpleNamespace
    from component_analysis import hooks
    def forbidden(*a,**k):raise AssertionError('model/CUDA prohibited')
    monkeypatch.setattr(hooks,'load_analysis_model',forbidden)
    monkeypatch.setattr(torch.cuda,'is_available',forbidden)
    monkeypatch.setattr(runner,'build_validation_manifest',lambda *a,**k:copy.deepcopy(manifest))
    args=runner.parse_args(['--dry-run','--output',str(tmp_path)])
    monkeypatch.setattr(runner,'validated_output',lambda p:Path(p))
    assert runner.run_baselines(args)['status']=='cpu_dry_run'


def test_budget_failure_receipts_and_deadlines(runner,tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'validated_output',lambda p:Path(p))
    args=runner.parse_args(['--output',str(tmp_path),'--allocation-seconds','3601'])
    with pytest.raises(ValueError):runner.run_baselines(args)
    assert (tmp_path/'cost.json').is_file()


def test_rejects_bf16_step_and_manifest_mutation(runner,manifest):
    assert not runner.numerical_receipt(torch.zeros(1),torch.tensor([.125]))['pass']
    changed=copy.deepcopy(manifest);changed['panel'][0]['truth_id']=-1
    with pytest.raises(ValueError):runner.verify_validation_manifest(changed,check_files=False)


def test_tiny_physical192_same_path_controls_and_fp32_readout(runner):
    from nnsight import NNsight
    from transformers import LlamaForCausalLM
    from tests.helpers import tiny_config
    torch.manual_seed(531)
    model=NNsight(LlamaForCausalLM(tiny_config(attn_implementation='sdpa')).eval())
    variants=[{'variant_id':'tiny0','ids':[3,6,4,9,12],'length':5,'truth_id':3,'other_id':4},
              {'variant_id':'tiny1','ids':[4,7,8],'length':3,'truth_id':4,'other_id':3}]
    assert hasattr(runner,'capture_baseline_batch'), 'baseline same-path control function missing'
    metrics,controls,forwards=runner.capture_baseline_batch(model,variants,'cpu',two_pass=True,receiver=('q',1,1))
    assert forwards>=5
    assert metrics['logits'].shape==(8,101) and metrics['logits'].dtype==torch.float32
    assert len(metrics['rows'])==2
    assert {c['control'] for c in controls}=={'all_component_self','empty_recapture','no_sender_two_pass_all192','self_sender_two_pass_all192'}
    assert all(c['pass'] and c['bitwise'] for c in controls)


def test_resolved_honest_sample_sources_and_conservative_native_pool(manifest):
    h=manifest['historical']
    assert len(h['all_component_source_ids'])==239
    assert len(h['component_expanded_story_ids'])==227
    assert h['native_eligible_counts']=={'rows':394,'stories':318}


def test_all_model_shards_and_compatibility_dependencies_hashed(manifest):
    assert len([p for p in manifest['model_files'] if p.endswith('.safetensors')])==4
    assert any(p.endswith('models/_compat.py') for p in manifest['code_sha256'])
    assert all(len(h)==64 for h in manifest['model_files'].values())


def test_named_primary_role_support_is_exact_axis_and_task_intersection(runner,manifest):
    by={v['variant_id']:v for v in manifest['panel']};own={}
    for p in manifest['pairs']:
        r,d=by[p['recipient_id']],by[p['donor_id']]
        mapped=runner.validation_semantic_map(r,d,scope='common')
        roles={tuple(r['position_roles'][str(a)]) for a,b in mapped}
        own[r['variant_id']]=own.get(r['variant_id'],roles)&roles
    for r in manifest['panel']:
        expected=own[r['variant_id']]
        if r['population']=='fresh':
            partner=next(d for d in manifest['panel'] if d['story_id']==r['story_id'] and d['factors']!={**r['factors']} and all(d['factors'][k]==x for k,x in r['factors'].items() if k!='task'))
            expected=expected&own[partner['variant_id']]
        assert set(map(tuple,r['primary_role_support']))==expected


def test_gate_rejects_missing_numeric_kind_coverage_or_nonfinite_receipt(runner,manifest):
    rows=rows_for_gate(manifest)
    for controls in ([{'pass':True}],controls_for_gate(manifest)[:-1]):
        assert not runner.evaluate_validity(manifest,rows,controls)['paths_go']
    controls=controls_for_gate(manifest);controls[0]['variant_ids'].pop()
    assert not runner.evaluate_validity(manifest,rows,controls)['paths_go']
    controls=controls_for_gate(manifest);controls[0]['max_abs_error']=float('nan')
    assert not runner.evaluate_validity(manifest,rows,controls)['paths_go']


def test_calibration_requires_all_variants_of_first_eight_stories(runner,manifest):
    first8={g['story_id'] for g in manifest['groups'][:8]}
    expected=[{'variant_id':v['variant_id']} for v in manifest['panel'] if v['story_id'] in first8]
    assert len(expected)==128
    assert hasattr(runner,'complete_calibration_fixtures'), 'complete-fixture calibration predicate missing'
    assert not runner.complete_calibration_fixtures(manifest['panel'],first8,expected[:120])
    assert runner.complete_calibration_fixtures(manifest['panel'],first8,expected)


def test_neutral_reporting_truth_failure_is_visible_without_affecting_retrieval_gate(runner,manifest):
    rows=rows_for_gate(manifest);by={v['variant_id']:v for v in manifest['panel']};failed=0
    for r in rows:
        v=by[r['variant_id']]
        if v['population']=='fresh' and v['template']=='A' and v['factors']=={'truth':0,'favored':v['factors']['favored'],'stakes':0,'task':'report'}:
            r['emitted_id']=v['other_id'] if failed%2 else next(i for i in range(3) if i not in (v['truth_id'],v['other_id']))
            failed+=1
    gate=runner.evaluate_validity(manifest,rows,controls_for_gate(manifest))
    assert gate['paths_go']
    assert 'neutral_reporting_strata' in gate, 'neutral reporting truth-stratum display missing'
    assert gate['neutral_reporting_strata']['A:truth0']=={'correct':0,'total':64,'accuracy':0.,'non_item_count':32}
    assert gate['neutral_reporting_strata']['A:truth1']=={'correct':64,'total':64,'accuracy':1.,'non_item_count':0}
    assert all(s['pass'] for s in gate['neutral_retrieval_strata'].values())
