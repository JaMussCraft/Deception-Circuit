"""CPU-only runner contracts; no pretrained weights or network."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest
import torch

from tests.helpers import build_tiny_pair


def runner():
    from evaluation import selective_mask_runner as r
    return r


def tiny():
    from evaluation.selective_mask import configure_candidate_gates
    torch.manual_seed(12)
    from config import NodePruningConfig
    cfg=NodePruningConfig(prune_attention_neurons=False,prune_attention_blocks=False,prune_mlp_hidden=False,prune_mlp_output=False,prune_mlp_blocks=False)
    _, model = build_tiny_pair(node_cfg=cfg)
    heads = [[0, 0], [1, 1]]
    params = configure_candidate_gates(model, heads, expected_initial_removed=.5)
    return model, heads, params


def test_selection_requires_both_h_accuracy_gates_and_d_improvement():
    r = runner()
    baseline = dict(split='validation', h_correct=10, capable_correct=8, suppression=1.)
    good = dict(split='validation', h_correct=10, capable_correct=8, suppression=.8, removed=2, update=2)
    for mutation in ({'h_correct': 9}, {'capable_correct': 7}, {'suppression': 1.}):
        assert r.select_checkpoint([dict(good, **mutation)], baseline) is None
    assert r.select_checkpoint([good], baseline) == good
    with pytest.raises(ValueError, match='validation'):
        r.select_checkpoint([dict(good, split='test')], baseline)


def test_selection_ties_use_size_then_earliest_without_test_access():
    r = runner()
    b = dict(split='validation', h_correct=2, capable_correct=1, suppression=2.)
    rows = [dict(b, suppression=1., removed=n, update=u) for n, u in [(3, 1), (2, 5), (2, 3)]]
    assert r.select_checkpoint(rows, b)['update'] == 3


def test_joint_pairs_share_draw_and_accumulation_preserves_stratum_denominators():
    r = runner()
    from evaluation.selective_mask import pilot_loss
    model, heads, _ = tiny()
    a = r._candidate_logits(model)
    torch.manual_seed(0)
    d = torch.randn(3, 7, requires_grad=True)
    h = torch.randn(3, 7, requires_grad=True)
    base = torch.randn(3, 7)
    capable = torch.tensor([False, False, True])
    truth = torch.tensor([1, 2, 3]); deceptive = torch.tensor([[0], [0], [0]])
    whole = pilot_loss(d, deceptive, h, base, truth, capable, a, rho=.1).total
    parts = []
    for ix in [slice(0, 2), slice(2, 3)]:
        p = pilot_loss(d[ix], deceptive[ix], h[ix], base[ix], truth[ix], capable[ix], a, rho=0.)
        parts.append(r._weighted_loss(p, len(d[ix]), 3, 1))
    got = sum(parts) + .1 * torch.sigmoid(-a).sum()
    torch.testing.assert_close(got, whole)
    assert torch.autograd.grad(got, h, retain_graph=True)[0].equal(torch.autograd.grad(whole, h)[0])
    # Joint twin forward draws once per layer and uses the same donor for D/H.
    prompt = dict(input_ids=[1, 2, 3], attention_mask=[1, 1, 1])
    c = dict(cluster_id='a', labels={'D': {'token_id': 4}, 'H': {'token_id': 5}},
             prompts={'original': {'D': {'clean': prompt}, 'H': {'clean': prompt}}})
    donor = copy.deepcopy(c); donor['cluster_id'] = 'b'
    donor['prompts']['original']['H']['clean']['input_ids'] = [6, 7, 8]
    split = dict(clusters=[c, donor], donor_map={'a': 'b', 'b': 'a'})
    model.train()
    with patch('torch.rand_like', side_effect=lambda x: torch.full_like(x, .5)) as draws:
        out = r._joint_logits(model, split, [0])
    assert out[0].shape == out[1].shape == (1, model.config.vocab_size)
    assert draws.call_count == len(model.model.layers)


def test_only_candidate_logits_enter_optimizer_and_base_stays_fixed():
    r = runner(); model, heads, params = tiny()
    before = {n: p.clone() for n, p in model.named_parameters()}
    optimizer = r._optimizer(params)
    assert optimizer.param_groups[0]['weight_decay'] == 0
    torch.sigmoid(-r._candidate_logits(model)).sum().backward(); optimizer.step()
    for name, p in model.named_parameters():
        if not torch.equal(p, before[name]):
            assert name.endswith('head_gates.log_alpha')
            gate = model.get_submodule(name.rsplit('.', 1)[0])
            assert torch.equal(p[~gate.eligibility], before[name][~gate.eligibility])
            assert p.dtype == torch.float32


def test_reference_cache_is_readout_only_and_bound_to_validated_path(tmp_path):
    r = runner()
    value = {'fingerprint': 'a', 'baseline_path': r.BASELINE_PATH, 'splits': {
        'train': {'h_logits': torch.randn(3, 7), 'capable': torch.tensor([True, False, True])}}}
    r._save_tensor(tmp_path / 'cache.pt', value)
    got = r._load_tensor(tmp_path / 'cache.pt', 'a')
    assert got['splits']['train']['h_logits'].shape == (3, 7)
    assert got['splits']['train']['h_logits'].device.type == 'cpu'
    value['baseline_path'] = 'single_stream'
    r._save_tensor(tmp_path / 'cache.pt', value)
    with pytest.raises(ValueError, match='baseline'):
        r._load_cache(tmp_path / 'cache.pt', 'a')


def test_cache_rejects_changed_baseline_path_or_prompt(tmp_path):
    r = runner(); path = tmp_path / 'cache.pt'
    r._save_tensor(path, {'fingerprint': 'prompt-a', 'baseline_path': r.BASELINE_PATH})
    with pytest.raises(ValueError, match='fingerprint'):
        r._load_cache(path, 'prompt-b')


def test_capability_is_train_only_frozen_and_not_a_row_filter():
    r = runner()
    rows = [{'stratum': [d, p, 'audit']} for d, p in [('identity', 1), ('inversion', 2)]] * 60
    flags = torch.tensor([True] * 60 + [False] * 60)
    result = r._capability_report(rows, flags, floor=60)
    assert result['usable'] and result['n_total'] == 120 and result['n_capable'] == 60
    assert not r._capability_report(rows, torch.zeros(120, dtype=torch.bool), floor=60)['usable']


def test_exact_resume_matches_uninterrupted_tiny_fit(tmp_path):
    r = runner()
    model, heads, params = tiny(); optimizer = r._optimizer(params)
    def update():
        optimizer.zero_grad(); (r._candidate_logits(model) * torch.rand(2)).sum().backward(); optimizer.step()
    update()
    r._checkpoint(tmp_path / 'state.pt', model, optimizer, {'update': 1}, 'fixed')
    update(); expected = [p.clone() for p in params]; expected_rng = torch.rand(3)
    model, heads, params = tiny(); optimizer = r._optimizer(params)
    cursor = r._restore(tmp_path / 'state.pt', model, optimizer, 'fixed')
    assert cursor['update'] == 1
    update()
    for actual, wanted in zip(params, expected):
        assert torch.equal(actual, wanted)
    assert torch.equal(torch.rand(3), expected_rng)


@pytest.mark.parametrize('change', ['donor', 'tokenizer', 'source', 'hardware', 'rho', 'seed', 'batch', 'policy'])
def test_resume_rejects_any_behavior_input_change(tmp_path, change):
    r = runner(); model, heads, params = tiny(); optimizer = r._optimizer(params)
    r._checkpoint(tmp_path / 'c.pt', model, optimizer, {}, 'original')
    with pytest.raises(ValueError, match='fingerprint'):
        r._restore(tmp_path / 'c.pt', model, optimizer, change)


def test_generation_safety_slice_is_fixed_before_fit_and_never_test_selection():
    r = runner()
    clusters = [dict(cluster_id=str((d, p, t, i)), stratum=[d, p, t])
                for d in ['identity', 'inversion'] for p in [1, 2] for t in ['audit', 'lab'] for i in range(3)]
    a = r._safety_slice(clusters)
    assert len(a) == 16 and a == r._safety_slice(list(reversed(clusters)))
    with pytest.raises(ValueError, match='stratum'):
        r._safety_slice(clusters[:2])


def test_derived_manifest_preserves_old_source_and_binds_learned_mask():
    r = runner()
    from evaluation.selective_diagnostics import content_hash
    p = dict(cluster_id='x', source_id='x', input_ids=[1, 2], attention_mask=[1, 1])
    row = dict(row_id='old', kind='score', cluster_id='x', policy='D', view='original',
               condition='core', mask_label='core', recipient=p, donor=None,
               identity_sanity_check=False, labels={'D': {'token_id': 1}, 'H': {'token_id': 2}})
    parent = dict(manifest_hash='parent', rows=[row], donor_reference_rows=[], clusters=[] , config={})
    original = copy.deepcopy(parent)
    mask = {'export_hash': 'abc', 'removal_mask': {'mlp_blocks': [0]}}
    derived = r.make_evaluation_manifest(parent, {'rho0': mask}, purpose='validation_safety', frozen_slice=['x'], provenance={'checkpoint': 'new'})
    assert parent == original
    learned = [x for x in derived['rows'] if x['mask_label'].startswith('learned-')]
    assert learned and 'abc' in learned[0]['condition'] and learned[0]['row_id'] != 'old'
    changed = r.make_evaluation_manifest(parent, {'rho0': dict(mask, export_hash='def')}, purpose='validation_safety', frozen_slice=['x'], provenance={'checkpoint': 'new'})
    assert derived['manifest_hash'] != changed['manifest_hash']
    assert content_hash(derived['rows']) != content_hash(changed['rows'])


def test_reference_closure_and_cost_include_donor_completions():
    r = runner()
    p = dict(input_ids=[1, 2], attention_mask=[1, 1], reference_row_id='ref')
    m = dict(rows=[dict(kind='generation', donor=p)], donor_reference_rows=[dict(row_id='ref')])
    plan = r._generation_cost(m)
    assert plan['target_completions'] == 1 and plan['donor_completions'] == 1
    assert plan['max_new_tokens'] == 192
    with pytest.raises(ValueError, match='closure'):
        r._generation_cost(dict(m, donor_reference_rows=[]))


def test_knockout_export_has_zero_mlps():
    from evaluation.selective_mask import export_binary_masks
    from evaluation.selective_runner import safe_knockout
    model, heads, _ = tiny()
    out = export_binary_masks(model, heads, provenance={})
    safe_knockout(out['removal_mask'])
    assert all(not any(v) for v in out['removal_mask']['mlp_hidden'].values())


def test_no_candidate_ends_without_automatic_retrain():
    r = runner()
    assert r.select_checkpoint([], dict(split='validation', h_correct=0, capable_correct=0, suppression=1)) is None


def test_dry_run_never_loads_weights_or_uses_network(monkeypatch, tmp_path, capsys):
    import train_selective_mask as cli
    r = runner()
    m = dict(manifest_hash='fixture', candidate_heads=list(range(103)), splits={s: {'n_pairs':119, 'clusters': []} for s in ('train', 'validation')})
    monkeypatch.setattr(r, '_read_manifest', lambda _: m)
    monkeypatch.setattr(r, '_runtime', lambda *a: pytest.fail('loaded model'))
    assert cli.main(['--dry-run','--manifest',str(tmp_path/'m'), '--output-dir',str(tmp_path), '--rho','0','--seed','0','--epochs','2','--validate-every','1','--joint-pairs','1','--accumulation','2']) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan['updates'] == 120 and plan['validation_checkpoints'] == 2


def wrapper(tmp_path, fail=False):
    home = tmp_path / 'home'; home.mkdir()
    (home / '.bashrc').write_text('conda() { if [ "$1" = activate ]; then return '+('1' if fail else '0')+'; fi; }; export -f conda\nfalse\n')
    bindir = tmp_path/'bin'; bindir.mkdir()
    (bindir/'python').write_text('#!/bin/bash\nprintf "%s\\n" "$@"\n')
    (bindir/'python').chmod(0o755)
    env = dict(os.environ, HOME=str(home), PATH=str(bindir)+':'+os.environ['PATH'])
    return subprocess.run(['bash','scripts/selective_mask.sbatch','--dry-run','--manifest','missing'], env=env, capture_output=True, text=True)


def test_wrapper_tolerates_bashrc_test_failure_but_requires_conda(tmp_path):
    out = wrapper(tmp_path)
    assert out.returncode == 0, out.stderr


def test_wrapper_activation_failure_is_fatal(tmp_path):
    assert wrapper(tmp_path, fail=True).returncode != 0


def test_wrapper_dry_run_is_cpu_only(tmp_path):
    out = wrapper(tmp_path)
    assert out.returncode == 0 and '--dry-run' in out.stdout and 'train_selective_mask.py' in out.stdout


def test_wrapper_has_no_array_retry_requeue_or_a100_training():
    text = Path('scripts/selective_mask.sbatch').read_text()
    assert '#SBATCH --no-requeue' in text and 'gpuA40x4' in text
    assert '#SBATCH --array' not in text and 'gpuA100' not in text


def test_baseline_and_masked_noop_use_identical_joint_geometry():
    r = runner(); model, heads, _ = tiny(); model.eval()
    p = dict(input_ids=[1,2,3],attention_mask=[1,1,1])
    h = dict(input_ids=[4,5,6],attention_mask=[1,1,1])
    def cluster(cid, d, honest):
        return dict(cluster_id=cid, labels={'D':{'token_id':7},'H':{'token_id':8}},
                    prompts={'original':{'D':{'clean':d},'H':{'clean':honest}}})
    split=dict(clusters=[cluster('a',p,h),cluster('b',h,p)],donor_map={'a':'b','b':'a'})
    shapes=[]
    def observe(module,args,kwargs):
        shapes.append((tuple(kwargs['input_ids'].shape),kwargs['attention_mask'].clone(),kwargs['use_cache']))
    handle=model.register_forward_pre_hook(observe,with_kwargs=True)
    baseline=r._baseline_logits(model,split)
    ds,hs=[],[]
    with torch.no_grad():
        for i in range(2):
            d,honest=r._joint_logits(model,split,[i]); ds.append(d); hs.append(honest)
    handle.remove()
    assert len(shapes)==4 and all(s[0]==(2,3) and s[2] is False for s in shapes)
    assert all(torch.equal(s[1],shapes[0][1]) for s in shapes)
    assert torch.equal(torch.cat(ds),baseline['D']) and torch.equal(torch.cat(hs),baseline['H'])
    from evaluation.selective_mask import pilot_loss
    base=baseline['H']; truth=torch.tensor([8,8])
    loss=pilot_loss(torch.cat(ds),torch.tensor([[7],[7]]),torch.cat(hs),base,truth,
                    torch.tensor([True,True]),r._candidate_logits(model),rho=0.)
    assert abs(float(loss.capable_kl)) < 1e-6 and float(loss.truth_nondegradation)==0.


def test_derived_manifest_retains_frozen_nonself_h_donor_over_intact_template():
    r=runner()
    recipient=dict(cluster_id='a',source_id='a',input_ids=[1],attention_mask=[1],policy='D',stream='clean')
    donor=dict(cluster_id='b',source_id='b',input_ids=[2],attention_mask=[1],policy='H',stream='clean',reference_row_id='ref')
    row=dict(row_id='intact',kind='generation',cluster_id='a',view='free_response',policy='D',condition='intact',mask_label=None,recipient=recipient,donor=None)
    nonself=dict(row,row_id='nonself',condition='core_nonself',donor=donor)
    source=dict(manifest_hash='parent',rows=[row,nonself],clusters=[],config={},donor_reference_rows=[dict(row_id='ref',kind='donor_reference',prompt=copy.deepcopy(donor),decode={'max_new_tokens':96})])
    derived=r.make_evaluation_manifest(source,{'rho0':{'export_hash':'a','removal_mask':{}}},purpose='validation_safety',frozen_slice=['a'],provenance={})
    assert len(derived['rows'])==1
    actual=derived['rows'][0]['donor']
    assert {k:v for k,v in actual.items() if k!='reference_row_id'}=={k:v for k,v in donor.items() if k!='reference_row_id'}
    assert actual['reference_row_id']!='ref'
    assert len(derived['donor_reference_rows'])==1


def test_train_loop_resume_has_no_skipped_or_repeated_updates(tmp_path,monkeypatch):
    r=runner()
    from types import SimpleNamespace
    model,heads,_=tiny()
    prompts=[dict(input_ids=[i,i+1,i+2],attention_mask=[1,1,1]) for i in (1,4,7)]
    clusters=[dict(cluster_id=str(i),labels={'D':{'token_id':8},'H':{'token_id':9}},
                   prompts={'original':{'D':{'clean':p},'H':{'clean':p}}}) for i,p in enumerate(prompts)]
    split=dict(clusters=clusters,donor_map={'0':'1','1':'2','2':'0'})
    m=dict(candidate_heads=heads,splits={'train':split,'validation':split})
    base=r._baseline_logits(model,split); labels=r._labels(split); capable=torch.ones(3,dtype=torch.bool)
    metrics=r._metrics(base['D'],base['H'],base['H'],labels,capable,update=0,removed=0)
    # Selection is orthogonal here; exercise real forward/backward/accumulation/persistence.
    monkeypatch.setattr(r,'select_checkpoint',lambda *_:None)
    cache={'splits':{s:dict(h_logits=base['H'],capable=capable,metrics=metrics) for s in ('train','validation')}}
    identity=dict(receipt={'safety_cluster_ids':[]})
    args=SimpleNamespace(output_dir=tmp_path/'full',joint_pairs=1,accumulation=2,epochs=2,validate_every=1,seed=0,rho=.01,resume=False)
    args.output_dir.mkdir(); r._train(args,m,identity,SimpleNamespace(node_model=model),cache)
    expected=torch.load(args.output_dir/'latest.pt',weights_only=False)
    args.output_dir=tmp_path/'resumed'; args.output_dir.mkdir(); model,_,_=tiny()
    save=r._checkpoint
    class Interrupt(Exception): pass
    def interrupted(path,model,opt,cursor,fp):
        save(path,model,opt,cursor,fp)
        if Path(path).name=='latest.pt' and cursor['update']==1: raise Interrupt()
    monkeypatch.setattr(r,'_checkpoint',interrupted)
    with pytest.raises(Interrupt): r._train(args,m,identity,SimpleNamespace(node_model=model),cache)
    monkeypatch.setattr(r,'_checkpoint',save); args.resume=True
    model,_,_=tiny(); r._train(args,m,identity,SimpleNamespace(node_model=model),cache)
    actual=torch.load(args.output_dir/'latest.pt',weights_only=False)
    assert actual['cursor']['update']==expected['cursor']['update']==4
    assert actual['cursor']['loss_log']==expected['cursor']['loss_log']
    for name,tensor in expected['gates'].items(): assert torch.equal(actual['gates'][name],tensor)
    assert torch.equal(actual['rng']['torch'],expected['rng']['torch'])


def test_calibration_forced_open_has_no_optimizer_and_restores_rng(tmp_path,monkeypatch):
    r=runner()
    from types import SimpleNamespace
    model,heads,_=tiny()
    p=dict(input_ids=[1,2,3],attention_mask=[1,1,1]); q=dict(input_ids=[4,5,6],attention_mask=[1,1,1])
    clusters=[dict(cluster_id=str(i),labels={'D':{'token_id':7},'H':{'token_id':8}},prompts={'original':{'D':{'clean':x},'H':{'clean':x}}}) for i,x in enumerate((p,q))]
    split=dict(clusters=clusters,donor_map={'0':'1','1':'0'})
    m=dict(candidate_heads=heads,splits={'train':split})
    base=r._baseline_logits(model,split)
    cache={'splits':{'train':dict(h_logits=base['H'],capable=torch.tensor([True,True]))}}
    monkeypatch.setattr(torch.cuda,'synchronize',lambda:None)
    monkeypatch.setattr(torch.cuda,'max_memory_allocated',lambda:0)
    monkeypatch.setattr(r,'_optimizer',lambda *_:pytest.fail('calibration created optimizer'))
    before={n:p.clone() for n,p in model.named_parameters()}; rng=torch.get_rng_state().clone()
    r._calibrate(SimpleNamespace(output_dir=tmp_path,joint_pairs=1,rho=.01),m,{},SimpleNamespace(node_model=model),cache)
    result=json.loads((tmp_path/'calibration.json').read_text())
    assert result['optimizer_steps']==0 and len(result['numerical_checks'])==1
    assert torch.equal(rng,torch.get_rng_state())
    for name,p in model.named_parameters(): assert torch.equal(before[name],p)


def test_corrupt_completed_checkpoint_fails_closed(tmp_path):
    r=runner(); model,heads,params=tiny(); path=tmp_path/'c.pt'
    r._checkpoint(path,model,r._optimizer(params),{},'fp')
    value=torch.load(path,weights_only=False)
    key=next(k for k in value['gates'] if k.endswith('log_alpha'))
    value['gates'][key][0]+=1
    torch.save(value,path)
    with pytest.raises(ValueError,match='corrupt'):
        r._restore(path,model,r._optimizer(params),'fp')


def test_planned_receipt_allows_baseline_but_blocks_optimizer(tmp_path):
    r=runner()
    clusters=[dict(cluster_id=str((d,p,t,i)),stratum=[d,p,t]) for d in ('identity','inversion') for p in (1,2) for t in ('audit','lab') for i in range(2)]
    m=dict(manifest_hash='m',splits={'validation':dict(clusters=clusters)})
    receipt=dict(version=1,manifest_hash='m',baseline_path=r.BASELINE_PATH,root_decision='planned by root',source_revision='revision',
                 safety_cluster_ids=r._safety_slice(clusters),policy='report18-v1',donor_reference_dir=str(tmp_path/'donors'))
    path=tmp_path/'receipt.json';path.write_text(json.dumps(receipt))
    assert r._receipt(path,m,'baseline')==receipt
    with pytest.raises(ValueError,match='baseline gates'):
        r._receipt(path,m,'train')


def test_donor_generation_is_reused_only_with_equal_reference_fingerprint(tmp_path,monkeypatch):
    r=runner(); model,_,_=tiny()
    from types import SimpleNamespace
    prompt=lambda cid,ids:dict(cluster_id=cid,source_id=cid,policy='H',stream='clean',view='free_response',
        input_ids=ids,attention_mask=[1]*len(ids),text=str(ids),intended_label='H',intended_answer='truth')
    labels={'D':{'token_id':7,'text':'lie'},'H':{'token_id':8,'text':'truth'}}
    p=prompt('a',[1,2]); donor=prompt('b',[3,4]); donor['reference_row_id']='ref'
    row=dict(row_id='old',kind='generation',cluster_id='a',policy='D',view='free_response',condition='nonself',
             mask_label='core',recipient=p,donor=donor,labels=labels,identity_sanity_check=False)
    ref=dict(row_id='ref',kind='donor_reference',prompt=donor,decode={'max_new_tokens':96})
    source=dict(manifest_hash='parent',rows=[row],donor_reference_rows=[ref],frozen_donor_reference_rows=[ref],
                clusters=[dict(cluster_id=cid,labels=labels) for cid in ('a','b')],config={'max_new_tokens':96,'decode':{'max_new_tokens':96}})
    calls=[]
    def generate(ctx,row,masks,reference,**kwargs):
        calls.append('target' if 'condition' in row else 'reference')
        return dict(token_ids=[8],termination='eos',eos_token_id=2,text='truth',empty=False,cap_hit=False)
    monkeypatch.setattr(r.sr,'generate_row',generate)
    def score(*_):
        calls.append('donor_score'); return dict(argmax_category='H',argmax_token_id=8)
    monkeypatch.setattr(r.sr,'score_row',score)
    monkeypatch.setattr(r.sr,'export_blind',lambda *_:None)
    provenance={'receipt':{'donor_reference_dir':str(tmp_path/'references')},'model':'same'}
    for i in range(2):
        derived=r.make_evaluation_manifest(source,{'rho':{'export_hash':str(i),'removal_mask':{}}},
            purpose='validation_safety',frozen_slice=['a'],provenance={'mask':str(i)})
        # No actual mask needed for generation stub; ResultStore and dependency execution are real.
        r._execute_generation(derived,SimpleNamespace(node_model=model),tmp_path/str(i),provenance,{},False)
    assert calls.count('reference')==1 and calls.count('target')==2
    assert calls.count('donor_score')==1


def test_checkpoint_excludes_swiglu_gate_proj_and_bounds_bytes(tmp_path):
    r=runner(); model,heads,params=tiny(); path=tmp_path/'gate-only.pt'
    assert any('gate_proj.weight' in name for name in model.state_dict())
    r._checkpoint(path,model,r._optimizer(params),{},'fp')
    saved=torch.load(path,weights_only=False)
    assert not any('gate_proj' in name for name in saved['gates'])
    from l0 import HardConcreteGate
    expected={name+'.'+key for name,module in model.named_modules() if isinstance(module,HardConcreteGate) for key in module.state_dict()}
    assert set(saved['gates'])==expected
    assert path.stat().st_size<32768


def test_loader_content_changes_source_identity_and_refuses_stale_receipt(tmp_path,monkeypatch):
    r=runner()
    from types import SimpleNamespace
    import evaluate_selective_deception as stage1
    # A temporary source tree lets the regression change real file content without
    # editing Stage 1 or any concurrent worker's files.
    here=tmp_path/'repo'; (here/'evaluation').mkdir(parents=True)
    for name in ('train_selective_mask.py','l0.py','analysis.py','config.py',
                 'scripts/selective_mask.sbatch','evaluation/selective_mask_runner.py',
                 'evaluate_selective_deception.py'):
        path=here/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text('# original\n')
    monkeypatch.setattr(r,'__file__',str(here/'evaluation/selective_mask_runner.py'))
    loader=here/'evaluate_selective_deception.py'
    original=r._source_files()
    assert original['evaluate_selective_deception.py']==r._hash_file(loader)
    snapshot=tmp_path/'snapshot'; snapshot.mkdir(); (snapshot/'config.json').write_text('{}')
    monkeypatch.setattr(stage1,'cached_snapshot',lambda _:snapshot)
    monkeypatch.setattr(r.sr,'resolve_masks',lambda:({}, {}, (None,{'D':'fixed'},{'D':{}})))
    monkeypatch.setattr(torch.cuda,'get_device_name',lambda _: 'CPU fixture')
    monkeypatch.setattr(torch.cuda,'get_device_capability',lambda _: (0,0))
    args=SimpleNamespace(model_path=str(snapshot),model_revision='snapshot',device='cpu',rho=0.,
                         seed=0,epochs=1,validate_every=1,joint_pairs=1,accumulation=1)
    receipt=dict(model_revision='snapshot',source_revision='fixture',source_files_hash=r.sd.content_hash(original))
    identity=r._identity(args,{'manifest_hash':'fixture'},receipt)
    loader.write_text('# changed loader behavior\n')
    changed=r._source_files()
    assert r.sd.content_hash(changed)!=receipt['source_files_hash']
    with pytest.raises(ValueError,match='source content hash mismatch'):
        r._identity(args,{'manifest_hash':'fixture'},receipt)
    updated=dict(receipt,source_files_hash=r.sd.content_hash(changed))
    assert r.sd.content_hash(r._identity(args,{'manifest_hash':'fixture'},updated))!=r.sd.content_hash(identity)
