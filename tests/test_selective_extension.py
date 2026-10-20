"""Prospective v3 duration/space contracts; no weights or GPU required."""
import copy
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from evaluation import selective_mask_runner as r
from tests.test_selective_amendment import _tiny_training_inputs


def manifest(policy='amendment-v3', space='union', arm='W'):
    union=[[i//32,i%32] for i in range(103)]
    original=dict(candidate_heads=union,candidate_heads_hash=r.sd.content_hash(union),source_metadata={})
    original['manifest_hash']=r.sd.manifest_hash(original)
    m=copy.deepcopy(original)
    m['amendment']=dict(policy=policy,original_manifest_hash=original['manifest_hash'],union_heads=union,
        candidate_space=space,collateral_arm=arm,wikitext_manifest_hash='wt',protocol_hash='protocol',
        max_updates=1536 if policy=='amendment-v3' else 512,checkpoint_every=64,pairs_per_update=8)
    if space=='all':m['candidate_heads']=[[l,h] for l in range(32) for h in range(32)]
    m['candidate_heads_hash']=r.sd.content_hash(m['candidate_heads']);m['manifest_hash']=r.sd.manifest_hash(m)
    return m


def args_for(m):
    a=m['amendment']
    return SimpleNamespace(policy=a['policy'],collateral_arm=a['collateral_arm'],candidate_space=a['candidate_space'],
        max_updates=a['max_updates'],checkpoint_every=64,seed=0,rho=0.,joint_pairs=1,resume=False)


@pytest.mark.parametrize('space,arm',[('union','W'),('all','W'),('union','HW'),('all','HW')])
def test_v3_plan_prices_entire_fixed_schedule(space,arm):
    m=manifest(space=space,arm=arm);args=args_for(m)
    with patch.object(r,'CANDIDATE_HASH',r.sd.content_hash(m['amendment']['union_heads'])),\
         patch.object(r,'_wt_manifest',return_value={'manifest_hash':'wt'}):
        plan=r._amended_plan(args,m)
    assert plan['policy']=='amendment-v3'
    assert plan['updates']==1536 and plan['pair_presentations']==12288
    assert (plan['full_sdr_cycles'],plan['additional_pairs'])==(103,31)
    assert plan['train_joint_forwards']==12288 and plan['train_w_forwards']==1536
    assert plan['validation_checkpoints']==24 and plan['validation_joint_forwards']==2856
    assert plan['validation_w_forwards']==384 and plan['w_block_cycles']==48
    assert plan['checkpoint_writes']==1561 and plan['max_checkpoints']==25
    schedule=r.amended_schedule(119,seed=0,updates=1536)
    assert len(schedule)==1536 and plan['row_schedule_hash']==r.sd.content_hash(schedule)
    assert schedule[:512]==r.amended_schedule(119,seed=0)


@pytest.mark.parametrize('policy,changes',[
    ('amendment-v2',{'max_updates':1536}),('amendment-v3',{'max_updates':512}),
    ('amendment-v3',{'collateral_arm':'H'}),('amendment-v3',{'checkpoint_every':32})])
def test_manifest_rejects_cross_policy_or_extra_axes(policy,changes):
    m=manifest(policy);m['amendment'].update(changes)
    with patch.object(r,'CANDIDATE_HASH',r.sd.content_hash(m['amendment']['union_heads'])),pytest.raises(ValueError):
        r._validate_amendment(m)


@pytest.mark.parametrize('changes',[{'rho':.01},{'max_updates':512},{'seed':1},{'joint_pairs':2},{'resume':True}])
def test_v3_cli_rejects_unapproved_settings_and_resume(changes):
    m=manifest();args=args_for(m)
    for k,v in changes.items():setattr(args,k,v)
    with patch.object(r,'CANDIDATE_HASH',r.sd.content_hash(m['amendment']['union_heads'])),\
         patch.object(r,'_wt_manifest',return_value={'manifest_hash':'wt'}),pytest.raises(ValueError):
        r._amended_plan(args,m)


def test_v2_plan_preserves_h_arm_rho_and_512_costs():
    m=manifest('amendment-v2',arm='H');args=args_for(m);args.rho=.01
    with patch.object(r,'CANDIDATE_HASH',r.sd.content_hash(m['amendment']['union_heads'])),\
         patch.object(r,'_wt_manifest',return_value={'manifest_hash':'wt'}):
        plan=r._amended_plan(args,m)
    assert plan['updates']==512 and plan['train_joint_forwards']==4096 and plan['train_w_forwards']==0
    assert plan['validation_checkpoints']==8 and plan['checkpoint_writes']==521
    assert (plan['full_sdr_cycles'],plan['additional_pairs'],plan['w_block_cycles'])==(34,50,16)


def test_v3_receipt_cannot_reuse_v2_authorization():
    m=manifest()
    rec=dict(version=3,policy='amendment-v3',manifest_hash=m['manifest_hash'],baseline_path=r.BASELINE_PATH,
        root_decision='fixed four fresh fits',source_revision='rev',source_files_hash='source',
        user_authorized_fit=True,prior_behavior={'stage1_behavior':'failed'},model_revision='model',
        wikitext_manifest_hash='wt',protocol_hash='protocol')
    assert r._amended_receipt(rec,m,'baseline')['prior_behavior']['stage1_behavior']=='failed'
    for changed in (dict(rec,version=2),dict(rec,policy='amendment-v2'),dict(rec,protocol_hash='old')):
        with pytest.raises(ValueError):r._amended_receipt(changed,m,'baseline')


def test_v3_cache_shares_only_arm_space_and_rejects_old_policy_or_source(tmp_path):
    identity=dict(policy='amendment-v3',original_manifest_hash='sdr',wikitext_manifest_hash='wt',source_files_hash='new',
        manifest_hash='union-W',amendment={'arm':'W'},receipt={},settings={})
    changed=dict(identity,manifest_hash='all-HW',amendment={'arm':'HW'},receipt={'a':1},settings={'a':2})
    fp=r._baseline_fingerprint(identity)
    assert fp==r._baseline_fingerprint(changed)
    path=tmp_path/'reference.pt';r._save_tensor(path,dict(fingerprint=fp,baseline_path=r.BASELINE_PATH))
    for stale in (dict(changed,policy='amendment-v2'),dict(changed,source_files_hash='old')):
        with pytest.raises(ValueError,match='fingerprint'):
            r._load_cache(path,r._baseline_fingerprint(stale))


def test_v3_training_rejects_resume_before_loading_any_checkpoint(tmp_path):
    model,m,cache,args=_tiny_training_inputs(tmp_path);args.policy='amendment-v3';args.resume=True
    with pytest.raises(ValueError,match='fresh'):
        r._train_amended(args,m,{},SimpleNamespace(node_model=model),cache,{},'wt')


@pytest.mark.parametrize('policy',['report18-v1','amendment-v2','amendment-v3'])
def test_user_waiver_does_not_bypass_cache_identity_or_change_original_gate(tmp_path,policy):
    identity=dict(policy=policy,source_files_hash='current',receipt={})
    fp=r._baseline_fingerprint(identity);path=tmp_path/'reference.pt'
    r._save_tensor(path,dict(fingerprint=fp,baseline_path=r.BASELINE_PATH,splits={'train':{'capability':{'usable':False}}}))
    identity['receipt'].update(baseline_fingerprint=fp,baseline_cache_sha256=r._hash_file(path))
    args=SimpleNamespace(reference_cache=path)
    if policy=='report18-v1':
        with pytest.raises(ValueError,match='unusable'):r._checked_cache(args,identity)
    else:
        assert not r._checked_cache(args,identity)['splits']['train']['capability']['usable']
    identity['source_files_hash']='stale'
    with pytest.raises(ValueError,match='fingerprint'):r._checked_cache(args,identity)


def test_v3_cli_dry_run_reports_frozen_duration(tmp_path,capsys):
    import json
    from train_selective_mask import main
    m=manifest()
    with patch.object(r,'_read_manifest',return_value=m),\
         patch.object(r,'CANDIDATE_HASH',r.sd.content_hash(m['amendment']['union_heads'])),\
         patch.object(r,'_wt_manifest',return_value={'manifest_hash':'wt'}):
        assert main(['--dry-run','--policy','amendment-v3','--manifest','m.json','--output-dir',str(tmp_path),
            '--wikitext-manifest','wt.json','--max-updates','1536','--checkpoint-every','64','--rho','0',
            '--seed','0','--joint-pairs','1','--collateral-arm','W'])==0
    assert json.loads(capsys.readouterr().out)['updates']==1536
