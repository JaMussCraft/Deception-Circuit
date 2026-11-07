"""CPU contract tests: structural selection, freeze gates, resumable replay."""
import copy
from collections import Counter
import pytest
import evaluate_native_sparse as n


def pairs(prefix, domains):
    rows=[]
    for i in range(16):
        r=dict(source_id=prefix+str(i),statement=prefix+' claim '+str(i),correct_option=i//8)
        for d in domains:
            r[d]=[dict(role='system',content=d),dict(role='user',content=r['statement'])]
        rows.append(r)
    return {'pairs':rows}


def receipt(tmp_path, expanded=False):
    entries=[]
    for space in (('union','all') if expanded else ('union',)):
        for arm in ('H','W','HW'):
            e=dict(arm=arm,space=space,status='failed_frontier')
            for kind in ('export','checkpoint','manifest','run_identity'):
                p=tmp_path/(space+arm+kind);p.write_text(kind)
                e[kind+'_path'],e[kind+'_sha256']=str(p),n.file_hash(p)
            entries.append(e)
    return dict(version=1,finalists_frozen=True,expansion_decision='all_heads_complete' if expanded else 'union_only',
                selection_basis='SDR_WikiText_validation_only',no_test_based_selection=True,finalists=entries)


def test_structural_mapping_ignores_response_fields_and_balances_cells():
    f,d=pairs('new','DHR'),pairs('old','H')
    rr,dd=n.structural_pairs(f,d);expected=n.donor_mapping(rr,dd)
    for row in f['pairs']+d['pairs']:
        row.update(response='false assertion',model_belief=False,deceptive=True)
    rr,dd=n.structural_pairs(f,d)
    assert n.donor_mapping(rr,dd)==expected
    assert len(set(expected.values()))==16
    truth={r['source_id']:r['correct_option'] for r in dd}
    assert Counter((r['correct_option'],truth[expected[r['source_id']]]) for r in rr)=={(0,0):4,(0,1):4,(1,0):4,(1,1):4}
    f['pairs'][0]['statement']='  ＯＬＤ claim 0.  '
    with pytest.raises(ValueError,match='overlaps'):n.structural_pairs(f,d)


def test_duplicates_and_unbalanced_truth_fail():
    f,d=pairs('new','DHR'),pairs('old','H')
    f['pairs'][1]['source_id']=f['pairs'][0]['source_id']
    with pytest.raises(ValueError,match='duplicate'):n.structural_pairs(f,d)
    f=pairs('new','DHR');f['pairs'][0]['correct_option']=1
    with pytest.raises(ValueError,match='balanced'):n.structural_pairs(f,d)


@pytest.mark.parametrize('expanded',[False,True])
def test_receipt_binds_complete_selection_artifacts_and_failed_frontier(tmp_path,expanded):
    r=receipt(tmp_path,expanded)
    assert len(n.check_receipt(r))==(6 if expanded else 3)
    bad=copy.deepcopy(r);bad['finalists'].pop()
    with pytest.raises(ValueError,match='all three/six'):n.check_receipt(bad)
    r['finalists'][0]['checkpoint_sha256']='stale'
    with pytest.raises(ValueError,match='receipt hash'):n.check_receipt(r)


def test_receipt_rejects_test_selection_and_unfrozen(tmp_path):
    r=receipt(tmp_path);r['no_test_based_selection']=False
    with pytest.raises(ValueError,match='freeze receipt'):n.check_receipt(r)
    r['no_test_based_selection'],r['finalists_frozen']=True,False
    with pytest.raises(ValueError,match='freeze receipt'):n.check_receipt(r)


def test_actual_trainer_export_and_mlp_guard():
    from evaluation import selective_mask as sm
    from tests.helpers import build_tiny_pair
    _,model=build_tiny_pair(seed=17)
    heads=[(l,h) for l in range(2) for h in range(4)]
    sm.configure_candidate_gates(model,heads)
    e=sm.export_binary_masks(model,heads,provenance={'test':True})
    c=model.config;geom=(c.num_hidden_layers,c.num_attention_heads,c.hidden_size,c.intermediate_size)
    n.check_export(e,*geom)
    bad=copy.deepcopy(e);bad['removal_mask']['mlp_blocks'][0]=1
    bad['export_hash']=n.digest({k:v for k,v in bad.items() if k!='export_hash'})
    with pytest.raises(ValueError,match='heads-only'):n.check_export(bad,*geom)
    e['K']['0'][0]=1-e['K']['0'][0]
    with pytest.raises(ValueError,match='export hash'):n.check_export(e,*geom)


def test_store_rejects_stale_fingerprint_and_tampered_output(tmp_path):
    s=n.Store(tmp_path,{'fingerprint':'a'});s.put('x',{'response':'text'})
    assert s.get('x')=={'response':'text'}
    with pytest.raises(ValueError,match='fingerprint'):n.Store(tmp_path,{'fingerprint':'b'})
    n.atomic(tmp_path/'x.json',dict(response='changed',fingerprint='a',record_hash='stale'))
    with pytest.raises(ValueError,match='corrupt'):s.get('x')


def test_structural_dryrun_needs_no_weights_tokenizer_or_receipt(tmp_path,capsys):
    f,d=tmp_path/'pairs.json',tmp_path/'prior.json'
    n.atomic(f,pairs('new','DHR'));n.atomic(d,pairs('old','H'))
    args=['--pairs',str(f),'--donors',str(d),'--output-dir',str(tmp_path/'out')]
    n.main(['--dry-run']+args)
    assert '"weights_loaded": false' in capsys.readouterr().out
    assert not (tmp_path/'out').exists()
    with pytest.raises(SystemExit):n.main(['--run']+args)


def test_tiny_helper_integration_one_bank_shared_domains_masks_and_resume(tmp_path):
    from tests.helpers import build_tiny_pair
    _,model=build_tiny_pair(seed=17,attn_implementation='eager')
    class Tokenizer:
        def decode(self,ids,**kw):return ','.join(map(str,ids))
    prompt={'ids':[3,4,5],'text':'native'}
    m=dict(fingerprint='tiny-caller',eos_token_ids=list(range(model.config.vocab_size)),model={'tiny':True},
           runtime={'tiny':True},source={'test':'sha'},tokenizer_identity='tiny-tokenizer',geometry=[2,4],
           recipients=[dict(source_id='r',correct_option=1,prompts={d:prompt for d in 'DHR'})],
           donors=[dict(source_id='d',correct_option=0,prompts={'H':prompt})],donor_mapping={'r':'d'},
           finalists=[dict(space='union',arm=a,keep_mask=[[0]*4]*2,status='failed_frontier') for a in ('H','W','HW')])
    n.execute(m,model,Tokenizer(),tmp_path)
    targets=list(tmp_path.glob('target-*.json'))
    assert len(targets)==12
    assert len(list(tmp_path.glob('donor-*.pt')))==1
    for p in targets:
        r=n.read(p)
        assert r['termination']=='eos' and r['mapped_prompt_queries']==3 and len(r['generated_tokens'])==1
        assert r['source_truth_agreement'] is False
        assert r['encoded_target_truth_value']==(0 if r['domain']=='R' else None)
    before={p.name:n.file_hash(p) for p in tmp_path.iterdir()}
    n.execute(m,model,Tokenizer(),tmp_path)
    assert before=={p.name:n.file_hash(p) for p in tmp_path.iterdir()}


def test_run_receipt_binds_source_data_and_budget():
    m={'fingerprint':'source-data-runtime-finalists','receipt_sha256':'selection-sha'}
    a=dict(assessment_authorized=True,manifest_fingerprint=m['fingerprint'],manifest_sha256='manifest-sha',
           finalist_receipt_sha256='selection-sha',estimated_gpu_seconds=30,reserved_gpu_seconds=60)
    n.check_run_receipt(a,m,'manifest-sha')
    a['manifest_fingerprint']='stale-source'
    with pytest.raises(ValueError,match='execution receipt'):n.check_run_receipt(a,m,'manifest-sha')
    a['manifest_fingerprint']=m['fingerprint'];a['reserved_gpu_seconds']=20
    with pytest.raises(ValueError,match='estimate'):n.check_run_receipt(a,m,'manifest-sha')


def test_preparation_freezes_actual_prompts_mapping_runtime_and_every_receipt_artifact(tmp_path,monkeypatch):
    from types import SimpleNamespace
    f,d=tmp_path/'pairs.json',tmp_path/'prior.json'
    n.atomic(f,pairs('new','DHR'));n.atomic(d,pairs('old','H'))
    model=tmp_path/'snapshot';model.mkdir()
    n.atomic(model/'config.json',dict(num_hidden_layers=1,num_attention_heads=2,hidden_size=4,intermediate_size=6))
    (model/'model.safetensors').write_bytes(b'fingerprint-only-never-loaded')
    receipt_data=receipt(tmp_path)
    export=dict(provenance={'amendment':{'protocol_hash':'protocol'}},K={'0':[1,0]},R={'0':[0,1]},removed_heads=[[0,1]],removal_mask=dict(
        attention_heads={'0':[0,1]},attention_blocks=[0],mlp_blocks=[0],attention_neurons={'0':[0,0,1,1]},
        mlp_hidden={'0':[0]*6},mlp_output={'0':[0]*4}))
    export['export_hash']=n.digest(export)
    for e in receipt_data['finalists']:
        n.atomic(e['export_path'],export);e['export_sha256']=n.file_hash(e['export_path'])
        n.atomic(e['run_identity_path'],export['provenance']);e['run_identity_sha256']=n.file_hash(e['run_identity_path'])
        n.atomic(e['manifest_path'],{});e['manifest_sha256']=n.file_hash(e['manifest_path'])
    rp=tmp_path/'receipt.json';n.atomic(rp,receipt_data)
    class Tokenizer:
        eos_token_id=2
        unk_token_id=0
        def encode(self,text,**kw):return [ord(c) for c in text]
        def convert_tokens_to_ids(self,text):return 3
    monkeypatch.setattr(n,'source_identity',lambda:{'caller':'source-sha'})
    monkeypatch.setattr(n,'runtime_identity',lambda backend:{'backend':backend,'dtype':'bfloat16'})
    # This test isolates preparation serialization; real checkpoint validation is tested below.
    monkeypatch.setattr(n,'check_finalist_identity',lambda *args:None)
    args=SimpleNamespace(pairs=f,donors=d,receipt=rp,model_path=model,backend='sdpa')
    m=n.build_manifest(args,Tokenizer())
    assert m['target_completions']==192 and m['donor_completions']==16
    assert m['max_generated_tokens']==53248
    for row in m['recipients']:
        assert set(row['prompts'])==set('DHR')
        assert row['prompts']['D']['text']==n.prompt_text(row['D'])
        assert row['prompts']['D']['ids']==[ord(c) for c in n.prompt_text(row['D'])]
    assert len(set(m['donor_mapping'].values()))==16
    args.backend='eager'
    assert n.build_manifest(args,Tokenizer())['fingerprint']!=m['fingerprint']
    (model/'model.safetensors').write_bytes(b'changed-weights')
    changed=n.build_manifest(args,Tokenizer())
    assert changed['model']!=m['model']
    n.Store(tmp_path/'out',m)
    with pytest.raises(ValueError,match='fingerprint'):n.Store(tmp_path/'out',changed)


def test_interrupted_generation_needs_budget_review_before_retry(tmp_path):
    store=n.Store(tmp_path,{'fingerprint':'bounded'})
    store.begin('donor-1')
    with pytest.raises(ValueError,match='budget review'):store.begin('donor-1')
    store.put('donor-1',{'generated_tokens':[2]})
    assert not (tmp_path/'donor-1.inflight').exists()


def test_checkpoint_identity_regression_rejects_wrong_arm_candidate_protocol_weights_and_gate(tmp_path,monkeypatch):
    import torch
    from evaluation import selective_mask as sm
    from evaluation.selective_mask_runner import _save_tensor, _gate_state
    from tests.helpers import build_tiny_pair
    _,model=build_tiny_pair(seed=17)
    heads=[[l,h] for l in range(2) for h in range(4)]
    sm.configure_candidate_gates(model,heads)
    monkeypatch.setattr(n,'frozen_protocol_identity',lambda:('protocol','wikitext'))
    amendment=dict(policy='amendment-v2',collateral_arm='H',candidate_space='union',protocol_hash='protocol',wikitext_manifest_hash='wikitext')
    manifest=dict(candidate_heads=heads,candidate_heads_hash=n.digest(heads),amendment=amendment)
    manifest['manifest_hash']=n.digest(manifest)
    snapshot={'path':'/snapshot','files':{'weights.safetensors':'weights','config.json':'config'}}
    identity=dict(wikitext_manifest_hash='wikitext',policy='amendment-v2',manifest_hash=manifest['manifest_hash'],amendment=amendment,
                  settings=dict(collateral_arm='H',candidate_space='union'),receipt={'protocol_hash':'protocol'},
                  model={'snapshot':'/snapshot','files':snapshot['files']},dtype='bfloat16')
    export=sm.export_binary_masks(model,heads,provenance=identity)
    cp=tmp_path/'checkpoint.pt'
    state={'fingerprint':n.digest(identity),'gates':_gate_state(model),'cursor':{'update':64}}
    _save_tensor(cp,state)
    e={'arm':'H','space':'union','checkpoint_path':str(cp)}
    n.check_finalist_identity(e,export,manifest,identity,snapshot)
    for mutation in ('arm','candidate','protocol','weights','unscheduled','gate'):
        bad=copy.deepcopy(manifest);ident=copy.deepcopy(identity);snap=copy.deepcopy(snapshot)
        if mutation=='arm':bad['amendment']['collateral_arm']='W'
        if mutation=='candidate':bad['candidate_heads']=bad['candidate_heads'][:-1]
        if mutation=='protocol':ident['receipt']['protocol_hash']='other'
        if mutation=='weights':snap['files']['weights.safetensors']='other'
        if mutation=='unscheduled':
            state['cursor']['update']=65;_save_tensor(cp,state)
        if mutation=='gate':
            state['cursor']['update']=64
            state['gates']['model.layers.0.attn.head_gates.log_alpha']=torch.full((4,),-10.)
            _save_tensor(cp,state)
        with pytest.raises(ValueError):n.check_finalist_identity(e,export,bad,ident,snap)


def test_output_writer_lock_is_exclusive_and_runtime_settings_are_enforced(tmp_path):
    import torch
    with n.writer_lock(tmp_path):
        with pytest.raises(ValueError,match='active writer'):
            with n.writer_lock(tmp_path):pass
    n.configure_runtime()
    assert torch.are_deterministic_algorithms_enabled()
    assert not torch.backends.cuda.matmul.allow_tf32 and not torch.backends.cudnn.allow_tf32
    assert 'numpy' in n.runtime_identity('eager')['packages']
