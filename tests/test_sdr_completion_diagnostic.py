"""Separate completion protocol; CPU/tiny models only, no real model inference."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'outputs/_analyses/sdr-routing-validation/baseline-cda2160-20261021T133612Z'

def runner():
    path=ROOT/'scripts/sdr_completion_diagnostic.py'
    assert path.is_file(), 'separate completion runner must exist'
    spec=importlib.util.spec_from_file_location('completion',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

@pytest.fixture(scope='module')
def frozen():
    r=runner()
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(str(r.CACHE),local_files_only=True)
    return r,r.build_completion_manifest(PARENT,tok)

def test_all1280_parent_ids_and_prompt_bytes_unchanged(frozen):
    r,m=frozen;parent=json.loads((PARENT/'manifest.json').read_text())
    assert len(m['panel'])==1280
    assert {v['variant_id']:v for v in m['panel']}=={v['variant_id']:v for v in parent['panel']}
    assert m['parent_gate']['paths_go'] is False

def test_original_baseline_batchorder_reconstructed(frozen):
    _,m=frozen
    saved=[json.loads(x)['variant_id'] for x in (PARENT/'baseline.jsonl').read_text().splitlines()]
    assert [v['variant_id'] for v in m['panel']]==saved

def test_calibration_rows_excluded_main_and_rubric_frozen(frozen):
    r,m=frozen
    assert m['calibration_ids']==[v['variant_id'] for v in m['panel'][:64]]
    assert m['rubric_hash']==r.digest(m['rubric'])
    with pytest.raises(ValueError,match='calibration'):
        r.blind_label_rows([{'run_kind':'calibration'}],m)

def test_prefix115_no_truncation(frozen):
    r,m=frozen
    assert max(v['length'] for v in m['panel'])==115
    bad=copy.deepcopy(m['panel'][0]);bad['length']=116;bad['ids']=[3]*116
    with pytest.raises(ValueError,match='115'):
        r.check_prefixes([bad])

def test_EOS_union_includes_all_three_endings():
    r=runner()
    assert r.read_eos(r.CACHE)[0]==[128001,128008,128009]

def test_parent_numeric_pass_capability_fail_is_valid_diagnostic_entry(frozen):
    _,m=frozen
    assert m['parent_numeric_pass'] is True
    assert m['parent_gate']['paths_go'] is False
    assert m['paths_go'] is False

@pytest.fixture
def tiny():
    from nnsight import NNsight
    from transformers import LlamaForCausalLM
    from tests.helpers import tiny_config
    from component_analysis import hooks
    torch.manual_seed(29)
    model=NNsight(LlamaForCausalLM(tiny_config(attn_implementation='sdpa')).eval())
    hooks._hf(model).config.use_cache=False
    variants=[dict(variant_id=f'v{i}',ids=[3,6,4+i],length=3,truth_id=3,other_id=4,prompt='stem',items=['copper','silver'],prompt_hash='p') for i in range(2)]
    return model,variants

def first_receipts(r,model,variants):
    from component_analysis import hooks
    ids,mask=r.validation_batch(variants,'cpu')
    c=hooks.capture_forward(model,ids,mask,components=hooks.all_component_keys(model)+[hooks.READOUT_KEY])
    scores=r.score_capture(model,c,[3]*len(variants),[4]*len(variants))
    return [dict(variant_id=v['variant_id'],passed=True,emitted_id=s['emitted_id'],fp32_checksum=s['fp32_checksum'],eos_ids=[128001,128008,128009]) for v,s in zip(variants,scores['rows'])]

def test_firststep_checksum_allrows_before_continuations(tiny):
    r=runner();model,vs=tiny;expected=first_receipts(r,model,vs)
    m={'panel':vs,'parent_baselines':expected,'_runtime':{}}
    got=r.replay_first_steps(model,m)
    assert all(x['passed'] for x in got)
    assert m['_runtime']['firststep_gate_pass'] is True
    assert m['_runtime']['forwards']==1

def test_mismatch_stops_without_scoring_rescue(tiny):
    r=runner();model,vs=tiny;expected=first_receipts(r,model,vs);expected[1]['fp32_checksum']='different'
    m={'panel':vs,'parent_baselines':expected,'_runtime':{}}
    with pytest.raises(r.DiagnosticStop):r.replay_first_steps(model,m)
    assert len(m['_runtime']['firststep_receipts'])==2
    assert m['_runtime'].get('firststep_gate_pass') is not True
    assert m['_runtime']['forwards']==1

def test_own_readout_append_EOS_dummy_mask_8x192(tiny,monkeypatch):
    r=runner();model,vs=tiny
    from component_analysis import hooks
    vs[1]['ids']=vs[1]['ids'][:2];vs[1]['length']=2
    receipts=first_receipts(r,model,vs);receipts[0]['emitted_id']=128009
    receipts[1]['emitted_id']=12
    seen=[];capture=hooks.capture_forward
    def checked(model,ids,mask,**kw):
        assert ids.shape==mask.shape==(8,192)
        assert mask[0].sum()==4 and ids[0,3]==128009
        assert mask[2].sum()==1 and ids[2].sum()==0
        assert mask[1].sum()==3
        seen.append(kw['components'])
        # Tiny vocabulary does not contain production EOS; terminated row is a stable dummy.
        safe=ids.clone();safe[0,3]=0
        return capture(model,safe,mask,**kw)
    monkeypatch.setattr(hooks,'capture_forward',checked)
    got=r.greedy_complete_batch(model,vs,receipts,max_new_tokens=2)
    assert got[0]['generated_ids']==[128009] and got[0]['stop_reason']=='eos'
    assert got[1]['readout_positions']==[1,2]
    assert seen==[[hooks.READOUT_KEY]]

def test_cap32_includes_cached_firsttoken_and_preserves_allrows(tiny,monkeypatch):
    r=runner();model,vs=tiny
    from component_analysis import hooks
    receipts=first_receipts(r,model,vs)
    ids,mask=r.validation_batch(vs,'cpu');expected=[]
    for step in range(4):
        c=hooks.capture_forward(model,ids,mask,components=[hooks.READOUT_KEY])
        tokens=r.capture_logits(model,c).float().argmax(-1)
        expected.append(tokens[:2].tolist())
        for i in range(2):ids[i,3+step]=tokens[i];mask[i,3+step]=1
    got=r.greedy_complete_batch(model,vs,receipts,max_new_tokens=4)
    assert [x['generated_ids'] for x in got]==[[row[i] for row in expected] for i in range(2)]
    # A controlled full-vocabulary readout lets us verify all32 steps cheaply.
    monkeypatch.setattr(hooks,'capture_forward',lambda *a,**k:None)
    monkeypatch.setattr(r,'capture_logits',lambda *a:torch.tensor([[0.,1.]]*8))
    got=r.greedy_complete_batch(model,vs,receipts)
    assert len(got)==2 and all(len(x['generated_ids'])==32 for x in got)
    assert all(x['stop_reason']=='max_new_tokens' for x in got)

def test_singleton_wordboundary_not_substring():
    r=runner()
    assert r.propose_literal_identity('inspection',('in','out'),'eos')['manual_required']
    assert r.propose_literal_identity('The unit is copper.',('copper','silver'),'eos')['answer_identity']=='candidateA'

@pytest.mark.parametrize('text',['not copper','copper and silver','copper, actually silver','I cannot answer','if copper','copper?','copper is not damaged'])
def test_negation_multiple_contradiction_refusal_require_rubric(text):
    assert runner().propose_literal_identity(text,('copper','silver'),'eos')['manual_required']

def test_capped_apparent_answer_unresolved():
    p=runner().propose_literal_identity('The unit is copper.',('copper','silver'),'max_new_tokens')
    assert p['answer_identity']=='unresolved' and p['manual_required']

def test_quotes_prefix_format_separate_from_correctness():
    p=runner().propose_literal_identity('The unit is "copper".',('copper','silver'),'eos')
    assert p['format']=='prefix-or-quote-then-item'
    assert 'semantic_result' not in p

def views_fixture(r):
    m={'seed':20261021,'rubric_hash':'rubric','panel':[dict(variant_id=f'v{i}',items=['silver','copper'],truthful_item='copper',factors={'stakes':1}) for i in range(3)]}
    gen=[dict(variant_id=f'v{i}',assistant_text='The unit is copper.',stop_reason='eos',run_kind='main') for i in range(3)]
    views=r.blind_label_rows(gen,m)
    return m,gen,views

def test_blind_inputs_hide_factors_truth_oldargmax():
    r=runner();m,gen,views=views_fixture(r)
    assert len(views)==1
    assert set(views[0])=={'opaque_id','assistant_text','candidates','stop_reason'}
    assert views[0]['candidates']==['copper','silver']

def annotation(views,identity='candidateA'):
    return [dict(opaque_id=v['opaque_id'],answer_identity=identity,response_kind='unambiguous_answer',format='prefix-or-quote-then-item') for v in views]

def test_labels_join_truth_only_after_independent_annotations():
    r=runner();m,gen,views=views_fixture(r)
    joined=r.join_labels(annotation(views),annotation(views),[],m['_private_join'])
    assert len(joined)==3 and all(x['semantic_result']=='correct' for x in joined)

def test_disagreement_missing_label_retains_denominator():
    r=runner();m,gen,views=views_fixture(r)
    joined=r.join_labels(annotation(views),annotation(views,'candidateB'),[],m['_private_join'])
    assert len(joined)==3 and all(x['semantic_result']=='ambiguous' for x in joined)
    missing=r.join_labels(annotation(views),[],[],m['_private_join'])
    assert all(x['semantic_result']=='bad/unresolved' for x in missing)

def test_unique_view_dedup_restores_all1280_weights():
    r=runner();m,gen,views=views_fixture(r)
    m['panel']=[dict(m['panel'][0],variant_id=f'v{i}') for i in range(1280)]
    gen=[dict(gen[0],variant_id=f'v{i}') for i in range(1280)]
    views=r.blind_label_rows(gen,m)
    assert len(views)==1
    joined=r.join_labels(annotation(views),annotation(views),[],m['_private_join'])
    summary=r.summarize_completions(joined,[dict(variant_id=f'v{i}',emitted_class='non_item') for i in range(1280)])
    assert summary['denominator']==1280 and summary['all']['semantic_result']['correct']==1280

def test_forecast_counts_full_cap_load_replay_and_io():
    r=runner()
    measured={'model_load_seconds':10,'audit_seconds':5,'replay_seconds':160,
        'replay_forwards':160,'continuation_seconds':496,'continuation_forwards':248,
        'checkpoint_seconds':4,'status':'calibration_complete'}
    f=r.forecast_main(measured)
    assert f['generation_forwards_bound']==5120
    assert f['continuation_forwards_bound']==4960
    assert f['forecast_seconds']>=10+5+160+4960*2+90
    assert f['fits_3000'] is False

def test_exact_A100_identity_not_just_class():
    r=runner()
    r.assert_gpu(dict(r.EXPECTED_GPU))
    bad=dict(r.EXPECTED_GPU,total_memory_bytes=123)
    with pytest.raises(ValueError):r.assert_gpu(bad)

def test_no_overwrite_or_parent_output(tmp_path):
    r=runner()
    with pytest.raises(ValueError):r.new_output(PARENT)
    p=r.NAMESPACE/('test-existing-refusal-'+r.digest(str(tmp_path))[:12])
    p.mkdir(exist_ok=True,parents=True)
    try:
        with pytest.raises(ValueError):r.new_output(p)
    finally:p.rmdir()

def test_annotation_payload_provenance_and_independence():
    r=runner();_,_,views=views_fixture(r)
    payload={'annotator_id':'one','model_family':'internal Sol','blind':True,
        'inputs_hash':r.digest(views),'rubric_hash':'r','labels':annotation(views),
        'completed_at':'2026-10-21T00:00:00Z','capacity_note':'all views labeled'}
    r.validate_annotation_payload(payload,views,'r')
    bad=dict(payload,inputs_hash='changed')
    with pytest.raises(ValueError):r.validate_annotation_payload(bad,views,'r')

@pytest.mark.parametrize('text',['She said "copper" but was uncertain.', '"copper" was somebody else\'s answer.', 'The unit is allegedly copper.'])
def test_quotation_scope_and_uncertain_claim_not_automatic(text):
    assert runner().propose_literal_identity(text,('copper','silver'),'eos')['manual_required']

def test_interruption_retains_cached_firsttoken_and_partial_rows(tiny,monkeypatch):
    r=runner();model,vs=tiny;receipts=first_receipts(r,model,vs)
    state={'firststep_gate_pass':True}
    receipts=r.FirstSteps(receipts,runtime=state)
    from component_analysis import hooks
    def interrupted(*args,**kwargs):raise r.DiagnosticStop('deadline')
    monkeypatch.setattr(hooks,'capture_forward',interrupted)
    with pytest.raises(r.DiagnosticStop):r.greedy_complete_batch(model,vs,receipts)
    assert len(state['active_rows'])==2
    assert all(len(row['generated_ids'])==1 and row['stop_reason']=='interrupted' for row in state['active_rows'])

def test_budget_envelope_counts_prior_failed_reservations():
    r=runner()
    args=SimpleNamespace(stage='main',allocation_seconds=3000,prior_reserved_gpu_seconds=4200,
        initial_reserved_gpu_seconds=600,max_seconds=2900)
    r.validate_budget(args)
    args.initial_reserved_gpu_seconds=601
    with pytest.raises(ValueError):r.validate_budget(args)
    args.initial_reserved_gpu_seconds=600;args.stage='calibration'
    with pytest.raises(ValueError):r.validate_budget(args)

def test_annotation_disagreement_requires_third_blind_label():
    r=runner();m,gen,views=views_fixture(r)
    a=annotation(views);b=annotation(views,'candidateB')
    resolved=r.join_labels(a,b,a,m['_private_join'])
    assert all(row['semantic_result']=='correct' for row in resolved)
    distinct=annotation(views,'none')
    uncertain=r.join_labels(a,b,distinct,m['_private_join'])
    assert all(row['semantic_result']=='ambiguous' for row in uncertain)

def test_cpu_dryrun_writes_planned_rows_without_loading_model(frozen,tmp_path,monkeypatch):
    r,m=frozen
    from component_analysis import hooks
    monkeypatch.setattr(hooks,'load_analysis_model',lambda *a,**k:pytest.fail('no model loading in CPU dryrun'))
    # Fixture retains real parent bytes, token vectors and source hashes; use its
    # frozen object to avoid hashing16GB a second time in this CLI unit test.
    monkeypatch.setattr(r,'build_completion_manifest',lambda *a,**k:copy.deepcopy(m))
    out=r.NAMESPACE/('pytest-cpu-'+r.digest(str(tmp_path))[:12])
    args=r.parse_args(['--dry-run','--output',str(out)])
    result=r.run_diagnostic(args)
    rows=r.read_jsonl(out/'generations.jsonl')
    assert result['status']=='cpu_dry_run' and result['reserved_gpu_seconds']==0
    assert len(rows)==1280 and all(not row['attempted'] for row in rows)
    assert json.loads((out/'label-rubric.json').read_text())==m['rubric']
    assert not (out/'label-a').exists()

def test_runtime_cache_disable_preserves_tiny_checksum(tiny,monkeypatch):
    r=runner();model,vs=tiny
    from component_analysis import hooks
    hf=hooks._hf(model);hf.config.use_cache=True
    original=first_receipts(r,model,vs)
    hf.config.use_cache=False
    monkeypatch.setattr(hf,'generate',lambda *a,**k:pytest.fail('alternative generate path prohibited'))
    got=r.replay_first_steps(model,{'panel':vs,'parent_baselines':original,'_runtime':{}})
    assert all(row['passed'] for row in got)

def test_all1280_last_checksum_failure_prevents_every_continuation(tiny,monkeypatch):
    r=runner();model,vs=tiny
    panel=[dict(vs[i%2],variant_id=f'v{i}') for i in range(1280)]
    saved=[dict(variant_id=v['variant_id'],fp32_checksum='reference',emitted_id=1) for v in panel]
    saved[-1]['fp32_checksum']='different'
    monkeypatch.setattr(r,'forward',lambda model,ids,mask,components,state:state.update(forwards=state.get('forwards',0)+1))
    monkeypatch.setattr(r,'score_capture',lambda *a:{'rows':[dict(fp32_checksum='reference',emitted_id=1)]*8})
    manifest={'panel':panel,'parent_baselines':saved,'_runtime':{}}
    with pytest.raises(r.DiagnosticStop):r.replay_first_steps(model,manifest)
    state=manifest['_runtime']
    assert len(state['firststep_receipts'])==1280 and state['forwards']==160
    assert state['firststep_gate_pass'] is False
    with pytest.raises(r.DiagnosticStop):
        r.greedy_complete_batch(model,panel[:8],r.FirstSteps(state['firststep_receipts'][:8],runtime=state))

@pytest.mark.parametrize('stage,allocated,initial',[('calibration',600,0),('main',3000,600)])
def test_actual_wrapper_forwards_full_reservation_ledger(tmp_path,stage,allocated,initial):
    import os
    import subprocess
    import time
    # Intercept timeout at the process boundary, so this tests the real wrapper
    # argv/ledger path without pretending a GPU allocation exists for Python.
    stub=tmp_path/'timeout'
    stub.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$COMPLETION_TEST_ARGV"\n')
    stub.chmod(0o700)
    recorded=tmp_path/'argv'
    env={**os.environ,'PATH':str(tmp_path)+':'+os.environ['PATH'],
        'SDR_COMPLETION_SUBMISSION_CWD':str(ROOT),'SLURM_JOB_ID':'cpu-wrapper-argv-test',
        'SLURM_JOB_END_TIME':str(int(time.time())+allocated-2),
        'SDR_COMPLETION_ALLOCATED_SECONDS':str(allocated),'SDR_COMPLETION_STAGE':stage,
        'SDR_COMPLETION_PRIOR_RESERVED_GPU_SECONDS':'4200',
        'SDR_COMPLETION_INITIAL_RESERVED_GPU_SECONDS':str(initial),'COMPLETION_TEST_ARGV':str(recorded)}
    result=subprocess.run(['bash',str(ROOT/'scripts/sdr_completion_diagnostic.sbatch'),
        '--manifest','unused-no-python-executed','--output','unused-no-python-executed'],env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    argv=recorded.read_text().splitlines()
    assert argv[argv.index('--stage')+1]==stage
    assert argv[argv.index('--allocation-seconds')+1]==str(allocated)
    assert argv[argv.index('--initial-reserved-gpu-seconds')+1]==str(initial)
    assert argv[argv.index('--prior-reserved-gpu-seconds')+1]=='4200'
    env['SDR_COMPLETION_INITIAL_RESERVED_GPU_SECONDS']='3600'
    recorded.unlink()
    rejected=subprocess.run(['bash',str(ROOT/'scripts/sdr_completion_diagnostic.sbatch')],env=env,capture_output=True,text=True)
    assert rejected.returncode==2 and not recorded.exists()

def test_full_annotation_export_missingness_and_join_cli(frozen,tmp_path):
    r,original=frozen;m=copy.deepcopy(original)
    source=r.new_output(r.NAMESPACE/('pytest-annotations-source-'+r.digest(str(tmp_path))[:12]))
    rows=r.planned_rows(m,'main')
    for i,(row,v) in enumerate(zip(rows,m['panel'])):
        row.update(assistant_text='The unit is '+sorted(v['items'])[0]+'.',
            stop_reason='max_new_tokens' if i%5==0 else 'eos',attempted=True,
            status='capped' if i%5==0 else 'completed',run_kind='main')
    r.atomic_json(source/'manifest.json',m)
    r.atomic_json(source/'cost.json',{'status':'cpu_test_fixture','reserved_gpu_seconds':0,'actual_gpu_seconds':0,'paid_api_calls':0})
    views=r.export_blinded(source,rows,m)
    assert len(r.read_jsonl(source/'private/join.jsonl'))==1280
    assert r.digest(r.read_jsonl(source/'label-a/blinded-inputs.jsonl'))==r.digest(views)
    labels=annotation(views)
    supplied={}
    for identity in ('a','b'):
        payload={'annotator_id':'cpu-fixture-'+identity,'model_family':'internal Sol','blind':True,
            'inputs_hash':r.digest(views),'rubric_hash':m['rubric_hash'],'labels':labels,
            'completed_at':'cpu-test-only','capacity_note':'synthetic labels; no actual agent annotation'}
        path=tmp_path/('labels-'+identity+'.json');r.atomic_json(path,payload);supplied[identity]=path
    output=r.NAMESPACE/('pytest-annotations-joined-'+r.digest(str(tmp_path))[:12])
    result=r.run_annotations(r.parse_args(['--stage','annotate','--run-dir',str(source),
        '--output',str(output),'--label-a',str(supplied['a']),'--label-b',str(supplied['b'])]))
    summary=json.loads((output/'summary.json').read_text())
    assert result['denominator']==1280
    assert summary['all']['semantic_result']['bad/unresolved']==256
    assert summary['all']['semantic_result'].get('correct',0)+summary['all']['semantic_result'].get('wrong',0)==1024
    assert summary['annotation_capacity']['a']['missing_views']==0
    assert (output/'report.md').is_file()

def test_EOS_on_token32_is_terminated_not_capped(tiny,monkeypatch):
    r=runner();model,vs=tiny
    from component_analysis import hooks
    receipts=first_receipts(r,model,vs)
    for row in receipts:row['emitted_id']=12
    calls={'n':0}
    monkeypatch.setattr(hooks,'capture_forward',lambda *a,**k:None)
    def fp32_logits(*args):
        calls['n']+=1
        logits=torch.zeros((8,128010),dtype=torch.float32)
        logits[:,128008 if calls['n']==31 else 12]=1
        return logits
    monkeypatch.setattr(r,'capture_logits',fp32_logits)
    got=r.greedy_complete_batch(model,vs,receipts)
    assert calls['n']==31
    assert all(len(row['generated_ids'])==32 and row['stop_reason']=='eos'
        and row['terminal_eos_id']==128008 and row['status']=='completed' for row in got)
