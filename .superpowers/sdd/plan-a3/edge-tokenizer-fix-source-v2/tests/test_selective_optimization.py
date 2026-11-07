"""CPU contracts for the two prospective v4 initializations."""
import copy
import math
from unittest.mock import patch

import pytest
import torch

from evaluation import selective_mask as sm
from evaluation import selective_mask_runner as r
from tests.test_selective_extension import manifest as legacy_manifest, args_for
from tests.test_selective_mask_runner import tiny


def manifest(initial=1.):
    m=legacy_manifest(space='all')
    m['amendment'].update(policy='amendment-v4',max_updates=3072,initial_expected_removed=initial)
    m['manifest_hash']=r.sd.manifest_hash(m)
    return m


def plan(m, changes=None):
    args=args_for(m);args.initial_expected_removed=m['amendment'].get('initial_expected_removed',1.)
    for k,v in (changes or {}).items():setattr(args,k,v)
    with patch.object(r,'CANDIDATE_HASH',r.sd.content_hash(m['amendment']['union_heads'])), patch.object(r,'_wt_manifest',return_value={'manifest_hash':'wt'}):
        return r._amended_plan(args,m)


@pytest.mark.parametrize('initial',[1.,10.])
def test_v4_fixed_schedule_and_initial_identity(initial):
    p=plan(manifest(initial))
    assert p['updates']==3072 and p['validation_checkpoints']==48
    assert p['pair_presentations']==24576 and p['train_w_forwards']==3072
    assert p['settings']['initial_expected_removed']==initial


@pytest.mark.parametrize('changes',[{'initial_expected_removed':0.},{'initial_expected_removed':2.},
    {'initial_expected_removed':float('nan')},{'max_updates':1536},{'candidate_space':'union'},
    {'collateral_arm':'HW'},{'collateral_arm':'H'},{'checkpoint_every':32}])
def test_v4_rejects_unapproved_manifest(changes):
    m=manifest();m['amendment'].update(changes)
    with pytest.raises(ValueError):plan(m)


@pytest.mark.parametrize('changes',[{'initial_expected_removed':10.},{'rho':.01},{'seed':1},{'max_updates':1536},{'joint_pairs':2}])
def test_v4_rejects_cli_drift(changes):
    with pytest.raises(ValueError):plan(manifest(),changes)


@pytest.mark.parametrize('policy',['amendment-v2','amendment-v3'])
def test_legacy_rejects_changed_initialization(policy):
    m=legacy_manifest(policy)
    with pytest.raises(ValueError):plan(m,{'initial_expected_removed':10.})
    m['amendment']['initial_expected_removed']=10.
    with pytest.raises(ValueError):plan(m)


@pytest.mark.parametrize('initial',[1.,10.])
def test_v4_baseline_and_checkpoint_reject_identity_drift(tmp_path,initial):
    m=manifest(initial)
    identity=dict(policy='amendment-v4',manifest_hash=m['manifest_hash'],amendment=m['amendment'],
        source_files_hash='source',settings=plan(m)['settings'],receipt={})
    fp=r._baseline_fingerprint(identity)
    path=tmp_path/'cache.pt';r._save_tensor(path,dict(fingerprint=fp,baseline_path=r.BASELINE_PATH))
    model,heads,params=tiny();optimizer=r._optimizer(params)
    cp=tmp_path/'latest.pt';r._checkpoint(cp,model,optimizer,{'update':3},r.sd.content_hash(identity))
    assert r._restore(cp,model,optimizer,r.sd.content_hash(identity))['update']==3
    for key,value in [('policy','amendment-v3'),('source_files_hash','old'),('manifest_hash','other'),
                      ('amendment',dict(m['amendment'],initial_expected_removed=10. if initial==1 else 1.)),
                      ('amendment',dict(m['amendment'],max_updates=1536))]:
        changed=dict(identity,**{key:value})
        with pytest.raises(ValueError,match='fingerprint'):r._load_cache(path,r._baseline_fingerprint(changed))
        with pytest.raises(ValueError,match='fingerprint'):r._restore(cp,model,optimizer,r.sd.content_hash(changed))


def test_v4_receipt_requires_version_and_initialization():
    m=manifest(10.)
    rec=dict(version=4,policy='amendment-v4',initial_expected_removed=10.,manifest_hash=m['manifest_hash'],
        baseline_path=r.BASELINE_PATH,root_decision='approved',source_revision='source',source_files_hash='hash',
        model_revision='model',user_authorized_fit=True,prior_behavior={},wikitext_manifest_hash='wt',protocol_hash='protocol')
    assert r._amended_receipt(rec,m,'baseline')==rec
    for changes in ({'version':3},{'policy':'amendment-v3'},{'initial_expected_removed':1.},{'initial_expected_removed':None}):
        with pytest.raises(ValueError):r._amended_receipt(dict(rec,**changes),m,'baseline')


@pytest.mark.parametrize('initial',[1.,10.])
def test_all_head_initial_counts_and_non_candidates_exact_open(initial):
    from l0 import HardConcreteGate
    class Layer(torch.nn.Module):
        def __init__(self):
            super().__init__();self.attn=torch.nn.Module();self.attn.head_gates=HardConcreteGate(32)
    model=torch.nn.Module();model.model=torch.nn.Module();model.model.layers=torch.nn.ModuleList([Layer() for _ in range(32)])
    model.other_gate=HardConcreteGate(4)
    heads=[[l,h] for l in range(32) for h in range(32)]
    sm.configure_candidate_gates(model,heads,expected_initial_removed=initial)
    logits=r._candidate_logits(model)
    assert float(torch.sigmoid(-logits).sum().detach())==pytest.approx(initial,rel=1e-6)
    assert torch.allclose(logits,torch.full_like(logits,math.log((1024-initial)/initial)))
    model.train();assert torch.equal(model.other_gate(),torch.ones(4))
    model.eval();assert all(torch.equal(layer.attn.head_gates(),torch.ones(32)) for layer in model.model.layers)


def test_v4_cli_dry_run_never_loads_model(tmp_path,capsys):
    import json
    from train_selective_mask import main
    m=manifest(10.)
    with patch.object(r,'_read_manifest',return_value=m),patch.object(r,'_runtime',side_effect=AssertionError('model load')),\
         patch.object(r,'CANDIDATE_HASH',r.sd.content_hash(m['amendment']['union_heads'])),patch.object(r,'_wt_manifest',return_value={'manifest_hash':'wt'}):
        assert main(['--dry-run','--policy','amendment-v4','--manifest','m.json','--output-dir',str(tmp_path),
            '--wikitext-manifest','wt.json','--max-updates','3072','--candidate-space','all','--rho','0',
            '--seed','0','--joint-pairs','1','--collateral-arm','W','--initial-expected-removed','10'])==0
    assert json.loads(capsys.readouterr().out)['settings']['initial_expected_removed']==10.


@pytest.mark.parametrize('initial',[1.,10.])
def test_v4_calibration_evidence_rejects_wrong_init_or_horizon(tmp_path,initial):
    import json
    row=dict(candidate_space='all',collateral_arm='W',initial_expected_removed=initial,max_updates=3072,
        actual_nonself_candidate_gradient=True,export_equivalent=True)
    report=dict(policy='amendment-v4',numerical_gate_passed=True,source_files_hash='s',baseline_fingerprint='b',
        wikitext_cache_fingerprint='w',production_optimizer_steps=0,all_smoke_states_discarded=True,profile=[row])
    path=tmp_path/'calibration.json'
    def verify(content):
        path.write_text(json.dumps(content));digest=r._hash_file(path)
        receipt=dict(source_files_hash='s',baseline_fingerprint='b',wikitext_cache_fingerprint='w',
            numerical_evidence=dict(calibration_path=str(path),calibration_sha256=digest),measured_budget=dict(profile_sha256=digest))
        r._verify_amended_evidence(receipt,manifest(initial))
    verify(report)
    for changes in ({'initial_expected_removed':10. if initial==1 else 1.},{'max_updates':1536}):
        with pytest.raises(ValueError,match='profile'):verify(dict(report,profile=[dict(row,**changes)]))


def test_v4_numerical_gate_requires_exact_full_vocab_and_initial_count():
    comparison=dict(finite=True,changed_entries=0,max_abs_full_vocab=0.)
    checks=[dict(comparisons={'repeat':comparison,'self_nonself':comparison,'eval_grad':comparison},reference=comparison)]
    profile=[dict(initial_expected_removed=10.,initial_expected_removed_measured=10.,max_updates=3072)]
    assert r._v4_exact_calibration(checks,profile)
    altered=copy.deepcopy(checks);altered[0]['comparisons']['self_nonself']['changed_entries']=1
    assert not r._v4_exact_calibration(altered,profile)
    altered=copy.deepcopy(checks);altered[0]['reference']['max_abs_full_vocab']=1e-7
    assert not r._v4_exact_calibration(altered,profile)
    assert not r._v4_exact_calibration(checks,[dict(profile[0],initial_expected_removed_measured=1.)])


@pytest.mark.parametrize('initial',[1.,10.])
def test_v4_calibration_profiles_only_chosen_init_all_w(tmp_path,initial):
    import json
    from types import SimpleNamespace
    from analysis import open_all_gates
    from evaluation import selective_wikitext as wt
    from tests.helpers import build_tiny_pair
    from tests.test_selective_amendment import _tiny_training_inputs
    _,m,_,args=_tiny_training_inputs(tmp_path)
    _,model=build_tiny_pair(num_hidden_layers=4)
    heads=[[l,h] for l in range(4) for h in range(4)]
    sm.configure_candidate_gates(model,heads,expected_initial_removed=initial)
    # A small real model exercises profiling; production eligibility stays guarded at1024 elsewhere.
    m['candidate_heads']=heads
    m['amendment']=dict(policy='amendment-v4',candidate_space='all',initial_expected_removed=initial)
    args.policy='amendment-v4';args.candidate_space='all';args.collateral_arm='W';args.rho=0.
    args.initial_expected_removed=initial;args.max_updates=3072;args.checkpoint_every=64;args.profile_updates=3
    cache={'splits':{}}
    for name in ('train','validation'):
        split=m['splits'][name];ref=r._baseline_logits(model,split);labels=r._labels(split)
        capable=ref['H'].argmax(-1)==labels['H']
        cache['splits'][name]=dict(h_logits=ref['H'],capable=capable,
            metrics=r._metrics(ref['D'],ref['H'],ref['H'],labels,capable,update=0,removed=0))
    block=dict(block_id='train-000000',input_ids=torch.tensor([[1,2,3]]),corrupted_input_ids=torch.tensor([[4,5,6]]),
        attention_mask=torch.ones(1,3,dtype=torch.long),n_tokens=2)
    wfp='c'*64
    with r._preserve_gates(model),torch.no_grad():
        open_all_gates(model)
        wt.write_reference_block(args.wikitext_cache,fingerprint=wfp,block_id=block['block_id'],
            logits=r._wt_logits(model,block),input_ids=block['input_ids'])
    original={k:v.clone() for k,v in r._gate_state(model).items()};schedule=r.amended_schedule
    with patch.object(r,'amended_schedule',side_effect=lambda n,seed:schedule(2,seed=seed)),\
         patch.object(wt,'iter_blocks',side_effect=lambda manifest,split:iter([block]*32 if split=='train' else [block]*16)):
        r._amended_calibrate(args,m,{'source_files_hash':'s'},SimpleNamespace(node_model=model),cache,{},wfp,.1)
    report=json.loads((tmp_path/'calibration.json').read_text());assert len(report['profile'])==1
    row=report['profile'][0]
    assert (row['candidate_space'],row['collateral_arm'],row['initial_expected_removed'])==('all','W',initial)
    assert row['initial_expected_removed_measured']==pytest.approx(initial,rel=1e-6)
    assert row['estimated_3072_update_run_seconds']>0 and row['max_updates']==3072
    assert 'estimated_1536_update_run_seconds' not in row
    assert all(c['finite_loss_and_gradients'] for c in report['numerical_checks'])
    assert all(torch.equal(v,r._gate_state(model)[k]) for k,v in original.items())


def test_v4_same_identity_resume_replays_optimizer_and_rng_exactly(tmp_path):
    from types import SimpleNamespace
    from evaluation import selective_wikitext as wt
    from tests.test_selective_amendment import _tiny_training_inputs
    identity=dict(policy='amendment-v4',manifest_hash='v4-init1',source_files_hash='frozen',
        settings=dict(max_updates=3072,initial_expected_removed=1.,rho=0.,seed=0))
    fingerprint=r.sd.content_hash(identity)
    block=dict(block_id='train-000000',input_ids=torch.tensor([[1,2,3]]),corrupted_input_ids=torch.tensor([[4,5,6]]),
        attention_mask=torch.ones(1,3,dtype=torch.long),n_tokens=2)
    update=r._amended_update
    def run(directory,resume,steps):
        directory.mkdir(exist_ok=True);model,m,cache,args=_tiny_training_inputs(directory)
        args.policy='amendment-v4';args.max_updates=3072;args.checkpoint_every=64;args.collateral_arm='W'
        args.rho=0.;args.initial_expected_removed=1.;args.resume=resume
        if not resume:
            wt.write_reference_block(args.wikitext_cache,fingerprint='a'*64,block_id=block['block_id'],
                logits=r._wt_logits(model,block).detach(),input_ids=block['input_ids'])
        calls=0
        def bounded(*a,**kw):
            nonlocal calls
            if calls==steps:raise RuntimeError('bounded interruption')
            calls+=1;return update(*a,**kw)
        with patch.object(wt,'iter_blocks',side_effect=lambda manifest,split:iter([block])),\
             patch.object(r,'_amended_update',side_effect=bounded),pytest.raises(RuntimeError,match='bounded interruption'):
            r._train_amended(args,m,identity,SimpleNamespace(node_model=model),cache,{'fixture':True},'a'*64)
        return r._load_tensor(directory/'latest.pt',fingerprint)
    full=run(tmp_path/'full',False,4)
    assert run(tmp_path/'resumed',False,2)['cursor']['update']==2
    resumed=run(tmp_path/'resumed',True,2)
    assert resumed['cursor']['update']==4
    assert r._tensor_digest(full)==r._tensor_digest(resumed)
