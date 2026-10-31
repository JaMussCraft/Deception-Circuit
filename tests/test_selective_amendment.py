"""CPU contracts for explicitly authorized amendment-v2; no model downloads."""
import copy
import json
import math
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import torch

from evaluation import selective_mask as sm
from evaluation import selective_mask_runner as r
from tests.test_selective_mask_runner import tiny


def test_amended_loss_units_and_window_hinge():
    d = torch.tensor([[2., 0., -1.]], requires_grad=True)
    h = torch.tensor([[0., 2., 0.], [0., 0., 2.]], requires_grad=True)
    base = torch.zeros(2, 3, requires_grad=True)
    args = (d, torch.tensor([[0]]), h, base, torch.tensor([1, 1]), torch.tensor([False, True]), torch.tensor([0.]))
    p = sm.pilot_loss(*args, rho=0.)
    for arm, coefficient in [('H', .5), ('W', 0.), ('HW', .25)]:
        loss = sm.amended_objective(p, arm=arm, n_d=1, total_d=1, total_h=2, total_capable=1,
            **({} if arm=='H' else dict(w_kl_sum=d.sum()*0+4., w_nll_sum=d.sum()*0+2., w_base_nll_sum=4., w_tokens=2)))
        want = p.suppression + coefficient*(p.capable_kl+p.truth_nondegradation)
        if arm in ('W','HW'): want = want + (1. if arm=='W' else .5)*1.
        torch.testing.assert_close(loss, want)
    w = sm.amended_objective(p, arm='W', n_d=1, total_d=1, total_h=2, total_capable=1,
        w_kl_sum=d.sum()*0+4., w_nll_sum=d.sum()*0+2., w_base_nll_sum=4., w_tokens=2)
    assert torch.autograd.grad(w, h, allow_unused=True)[0] is None
    assert base.grad is None


def test_empty_capable_and_partition_normalization():
    torch.manual_seed(1)
    d,h,b = (torch.randn(3,5,requires_grad=True) for _ in range(3))
    a=torch.tensor([0.]); y=torch.tensor([1,2,3]); cap=torch.tensor([False,False,True])
    whole=sm.pilot_loss(d,y[:,None],h,b,y,cap,a,rho=0.)
    want=sm.amended_objective(whole,arm='H',n_d=3,total_d=3,total_h=3,total_capable=1)
    parts=[]
    for ids in ([0,1],[2]):
        p=sm.pilot_loss(d[ids],y[ids,None],h[ids],b[ids],y[ids],cap[ids],a,rho=0.)
        parts.append(sm.amended_objective(p,arm='H',n_d=len(ids),total_d=3,total_h=3,total_capable=1))
    torch.testing.assert_close(sum(parts),want)
    p=sm.pilot_loss(d,y[:,None],h,b,y,torch.zeros(3,dtype=torch.bool),a,rho=0.)
    assert torch.isfinite(sm.amended_objective(p,arm='H',n_d=3,total_d=3,total_h=3,total_capable=0))


def test_fixed_schedule_wraps_tail_and_wikitext_cycles():
    batches=r.amended_schedule(119,seed=0)
    assert len(batches)==512 and all(len(x)==8 for x in batches)
    flat=sum(batches,[])
    assert flat[:119]==flat[119:238]
    assert sorted(flat[:119])==list(range(119))
    assert flat[112:120][-1]==flat[0]
    assert [i%32 for i in range(512)].count(0)==16


def test_common_noise_recomputed_graphs_and_restored_hooks():
    model,heads,params=tiny(); model.train()
    gates=[x.attn.head_gates for x in model.model.layers]
    with r._shared_gate_noise(model):
        first=[g() for g in gates]
        for _ in range(9):
            later=[g() for g in gates]
            assert all(torch.equal(x,y) for x,y in zip(first,later))
            sum(x.sum() for x in later).backward()
        assert all(p.grad is not None for p in params)
    assert all(not g._forward_hooks for g in gates)


def test_own_arm_selection_reports_w_even_when_h_fails():
    b=dict(split='validation',suppression=1.,h_correct=10,capable_correct=8,w_nll=3.)
    row=dict(b,suppression=.8,h_correct=0,capable_correct=0,w_nll=3.01,w_kl=.01,removed=2,update=64,rho=.01)
    assert r.select_amended_checkpoint([row],b,'W')['admissible']
    assert not r.select_amended_checkpoint([row],b,'H')['admissible']
    assert not r.select_amended_checkpoint([dict(row,w_kl=.1)],b,'W')['admissible']
    assert r.compact_amended_finding(row,b,'W')
    with pytest.raises(ValueError,match='validation'):
        r.select_amended_checkpoint([dict(row,split='test')],b,'W')


def test_receipt_does_not_relabel_failed_behavior(tmp_path):
    m={'manifest_hash':'m','amendment':{'policy':'amendment-v2'}}
    rec=dict(version=2,policy='amendment-v2',manifest_hash='m',baseline_path=r.BASELINE_PATH,
        root_decision='authorized',source_revision='rev',source_files_hash='source',
        user_authorized_fit=True,prior_behavior={'stage1_behavior':'failed','generation_headroom':'failed'},
        model_revision='model',wikitext_manifest_hash='wt')
    path=tmp_path/'receipt.json';path.write_text(json.dumps(rec))
    got=r._receipt(path,m,'baseline')
    assert got['prior_behavior']['stage1_behavior']=='failed'
    with pytest.raises(ValueError): r._receipt(path,m,'train')
    rec['user_authorized_fit']=False;path.write_text(json.dumps(rec))
    with pytest.raises(ValueError): r._receipt(path,m,'baseline')


def _tiny_training_inputs(tmp_path):
    model,heads,_=tiny()
    clusters=[]
    for i in range(2):
        prompt=dict(input_ids=[1+i,3,4],attention_mask=[1,1,1])
        clusters.append(dict(cluster_id=str(i),labels={'D':{'token_id':5},'H':{'token_id':6}},
            prompts={'original':{'D':{'clean':prompt},'H':{'clean':prompt}}}))
    split=dict(clusters=clusters,donor_map={'0':'1','1':'0'})
    ref=r._baseline_logits(model,split);labels=r._labels(split);cap=ref['H'].argmax(-1)==labels['H']
    metrics=r._metrics(ref['D'],ref['H'],ref['H'],labels,cap,update=0,removed=0)
    cache={'splits':{k:dict(h_logits=ref['H'],capable=cap,metrics=metrics) for k in ('train','validation')}}
    m=dict(candidate_heads=heads,splits={'train':split,'validation':split})
    args=SimpleNamespace(output_dir=tmp_path,seed=0,rho=.01,max_updates=4,checkpoint_every=2,
        collateral_arm='H',resume=False,wikitext_cache=tmp_path/'wt')
    return model,m,cache,args


def test_tiny_training_exact_resume_and_bounded_checkpoint_schedule(tmp_path):
    model,m,cache,args=_tiny_training_inputs(tmp_path)
    def validation(model,m,cache,args,identity,wm,wfp,update):
        row,export=r._validation(model,m['splits']['validation'],cache['splits']['validation'],update,m['candidate_heads'],identity)
        return dict(row,w_kl=0.,w_nll=1.,rho=.01),export
    def run(model,args):
        with patch.object(r,'_amended_validation',side_effect=validation):
            return r._train_amended(args,m,{},SimpleNamespace(node_model=model),cache,{},'wt')
    run(model,args);expected={k:v.clone() for k,v in r._gate_state(model).items()}
    full_latest=r._load_tensor(tmp_path/'latest.pt',r.sd.content_hash({}))
    assert len(json.loads((tmp_path/'frontier.json').read_text())['history'])==2
    # Restart from an actual complete-update checkpoint at step2 and reproduce4.
    import shutil
    shutil.copyfile(tmp_path/'validation-000002.pt',tmp_path/'latest.pt')
    other,_,_,_=_tiny_training_inputs(tmp_path);args.resume=True;run(other,args)
    assert all(torch.equal(v,r._gate_state(other)[k]) for k,v in expected.items())
    resumed_latest=r._load_tensor(tmp_path/'latest.pt',r.sd.content_hash({}))
    assert r._tensor_digest(full_latest)==r._tensor_digest(resumed_latest)


def test_update_w_does_not_backpropagate_h_terms(tmp_path):
    model,m,cache,args=_tiny_training_inputs(tmp_path);args.collateral_arm='W'
    from evaluation import selective_wikitext as wt
    block=dict(block_id='train-000000',input_ids=torch.tensor([[1,2,3]]),
        corrupted_input_ids=torch.tensor([[4,5,6]]),attention_mask=torch.ones(1,3,dtype=torch.long),n_tokens=2)
    fingerprint='a'*64
    wt.write_reference_block(args.wikitext_cache,fingerprint=fingerprint,block_id=block['block_id'],
        logits=r._wt_logits(model,block).detach(),input_ids=block['input_ids'])
    raw=r._amended_update(model,m,cache,args,[0,1]*4,block,fingerprint,r._optimizer([p for p in model.parameters() if p.requires_grad]),measure_gradients=True)
    assert 'H_KL' not in raw['gradient_component_norms'] and 'H_NLL' not in raw['gradient_component_norms']
    assert raw['w_tokens']==2 and raw['n_d']==8 and raw['gradient_isolation']


def test_shared_noise_rng_independent_of_absent_collateral_forwards():
    model,_,_=tiny();model.train();gate=model.model.layers[0].attn.head_gates
    endings=[]
    for forwards in (8,9):
        torch.manual_seed(7)
        with r._shared_gate_noise(model):
            for _ in range(forwards):gate()
        endings.append(torch.get_rng_state())
    assert torch.equal(*endings)


def test_amendment_lineage_and_all_1024_candidate_binding():
    from evaluation import selective_diagnostics as sd
    union=[[i//32,i%32] for i in range(103)]
    original=dict(candidate_heads=union,candidate_heads_hash=sd.content_hash(union),source_metadata={})
    original['manifest_hash']=sd.manifest_hash(original)
    amended=copy.deepcopy(original)
    amended['amendment']=dict(policy='amendment-v2',original_manifest_hash=original['manifest_hash'],
        union_heads=original['candidate_heads'],candidate_space='all',collateral_arm='W',
        wikitext_manifest_hash='wt',protocol_hash='protocol',max_updates=512,checkpoint_every=64,pairs_per_update=8)
    amended['candidate_heads']=[[l,h] for l in range(32) for h in range(32)]
    amended['candidate_heads_hash']=sd.content_hash(amended['candidate_heads'])
    amended['manifest_hash']=sd.manifest_hash(amended)
    with patch.object(r,'CANDIDATE_HASH',original['candidate_heads_hash']):r._validate_amendment(amended)
    amended['candidate_heads'].pop()
    with pytest.raises(ValueError,match='1024'):r._validate_amendment(amended)
    amended['candidate_heads'].append([31,31]);amended['source_metadata']['forged']=True
    with patch.object(r,'CANDIDATE_HASH',original['candidate_heads_hash']),pytest.raises(ValueError,match='original SDR'):r._validate_amendment(amended)


def test_amended_baseline_fingerprint_shares_arm_space_but_not_wikitext():
    identity=dict(policy='amendment-v2',original_manifest_hash='sdr',wikitext_manifest_hash='wt',source_files_hash='source',
        manifest_hash='arm-H-union',amendment={'arm':'H'},receipt={},settings={})
    changed=dict(identity,manifest_hash='arm-W-all',amendment={'arm':'W'},settings={'rho':.01},receipt={'new':'receipt'})
    assert r._baseline_fingerprint(identity)==r._baseline_fingerprint(changed)
    assert r._baseline_fingerprint(identity)!=r._baseline_fingerprint(dict(changed,wikitext_manifest_hash='other'))


def test_calibration_profiles_both_spaces_all_arms_and_discards_smoke_states(tmp_path):
    model,m,cache,args=_tiny_training_inputs(tmp_path)
    args.profile_updates=3;args.candidate_space='union'
    m['amendment']=dict(candidate_space='union',union_heads=m['candidate_heads'])
    identity=dict(source_files_hash='s')
    from evaluation import selective_wikitext as wt
    block=dict(block_id='train-000000',input_ids=torch.tensor([[1,2,3]]),
        corrupted_input_ids=torch.tensor([[4,5,6]]),attention_mask=torch.ones(1,3,dtype=torch.long),n_tokens=2)
    wfp='c'*64
    with r._preserve_gates(model),torch.no_grad():
        from analysis import open_all_gates
        open_all_gates(model)
        wt.write_reference_block(args.wikitext_cache,fingerprint=wfp,block_id=block['block_id'],
            logits=r._wt_logits(model,block),input_ids=block['input_ids'])
    original={k:v.clone() for k,v in r._gate_state(model).items()}
    configure=sm.configure_candidate_gates;export=sm.export_binary_masks;schedule=r.amended_schedule
    def candidates(heads):return [[l,h] for l in range(2) for h in range(4)] if len(heads)==1024 else heads
    with patch.object(sm,'configure_candidate_gates',side_effect=lambda model,heads:configure(model,candidates(heads))),\
         patch.object(sm,'export_binary_masks',side_effect=lambda model,heads,provenance:export(model,candidates(heads),provenance=provenance)),\
         patch.object(r,'amended_schedule',side_effect=lambda n,seed:schedule(2,seed=seed)),\
         patch.object(wt,'iter_blocks',side_effect=lambda manifest,split:iter([block]*32 if split=='train' else [block]*16)):
        r._amended_calibrate(args,m,identity,SimpleNamespace(node_model=model),cache,{},wfp,.1)
    report=json.loads((tmp_path/'calibration.json').read_text())
    assert len(report['profile'])==6
    assert {(p['candidate_space'],p['collateral_arm']) for p in report['profile']}=={(s,a) for s in ('union','all') for a in ('H','W','HW')}
    assert report['production_optimizer_steps']==0 and report['all_smoke_states_discarded']
    assert all(p['export_equivalent'] and p['export_probe_removed_heads']>=1 for p in report['profile'])
    assert all(torch.equal(v,r._gate_state(model)[k]) for k,v in original.items())
    assert all(len(p['priced_update_seconds'])==2 and p['estimated_512_update_run_seconds']>0 for p in report['profile'])


def test_training_evidence_rejects_changed_measured_artifact(tmp_path):
    report=dict(policy='amendment-v2',numerical_gate_passed=True,source_files_hash='s',baseline_fingerprint='b',
        wikitext_cache_fingerprint='w',production_optimizer_steps=0,all_smoke_states_discarded=True,
        profile=[dict(candidate_space='union',collateral_arm='W',actual_nonself_candidate_gradient=True,export_equivalent=True)])
    path=tmp_path/'calibration.json';path.write_text(json.dumps(report));digest=r._hash_file(path)
    receipt=dict(source_files_hash='s',baseline_fingerprint='b',wikitext_cache_fingerprint='w',
        numerical_evidence=dict(calibration_path=str(path),calibration_sha256=digest),measured_budget=dict(profile_sha256=digest))
    m={'amendment':dict(candidate_space='union',collateral_arm='W')}
    r._verify_amended_evidence(receipt,m)
    path.write_text(json.dumps(dict(report,numerical_gate_passed=False)))
    with pytest.raises(ValueError,match='SHA'):r._verify_amended_evidence(receipt,m)


def test_compact_finding_scans_entire_frontier_even_when_finalist_is_larger():
    baseline=dict(split='validation',suppression=1.,h_correct=10,capable_correct=8,w_nll=3.)
    compact=dict(baseline,suppression=.89,removed=2,update=64,w_kl=.01)
    larger=dict(baseline,suppression=.7,removed=20,update=512,w_kl=.01)
    assert r.select_amended_checkpoint([compact,larger],baseline,'W')['removed']==20
    assert r.has_compact_amended_finding([compact,larger],baseline,'W')
