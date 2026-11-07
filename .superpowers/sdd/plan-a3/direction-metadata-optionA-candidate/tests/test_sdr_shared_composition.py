"""CPU contracts for the original-SDR mixed-bank study; no cached model load."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'outputs/_analyses/sdr-routing-pilot/stage1-retry-f7cb49f-20261021T002501Z/manifest.json'

@pytest.fixture
def study():
    path = ROOT/'scripts/sdr_shared_composition.py'
    assert path.exists(), 'additive composition runner is missing'
    spec = importlib.util.spec_from_file_location('composition_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_input_panel_preserves_originals_both_truths_and_exact_maps(study):
    original = json.loads(PARENT.read_text())
    panel = study.input_panel(original)
    assert (len(panel['main']), len(panel['pairs']), len(panel['calibration']), len(panel['calibration_pairs'])) == (96,192,4,8)
    assert len({r['story_id'] for r in panel['main']}) == 24
    assert {r['split'] for r in panel['main']} == {'confirmation'}
    assert {r['story_id'] for r in panel['calibration']} == {min(g['story_id'] for g in original['groups'] if g['split']=='discovery')}
    old = {r['variant_id']:r for r in original['panel']}
    rows = {r['id']:r for r in panel['main']}
    for row in panel['main']:
        assert row['ids'] == old[row['id']]['ids'] and row['prompt'] == old[row['id']]['prompt']
        assert row['condition'] in ('P','N')
        assert row['condition']=='N' or row['pressure_id'] == row['primary_pressure_id']
    for pair in panel['pairs']:
        a,b = (rows[pair[k+'_id']] for k in ('recipient','donor'))
        assert a['story_id']==b['story_id']
        assert (a['truth']==b['truth']) != (a['condition']==b['condition'])
        assert pair['mapping'] == original['maps'][a['id']+'|'+b['id']]['common']
    bad = deepcopy(original); bad['maps'].pop(panel['pairs'][0]['recipient_id']+'|'+panel['pairs'][0]['donor_id'])
    with pytest.raises(ValueError): study.input_panel(bad)


def test_arms_disjoint_sources_and_group_footprints(study):
    arms = study.arms()
    assert len(arms)==20
    assert [(a['id'],a['source'],a['bank'],a['receiver']) for a in arms[8:11]] == [('09',None,'clean','QK'),('10','U5','clean','QK'),('11',None,'induced','QK')]
    assert study.U5 == [(12,6),(13,5),(13,20),(13,21),(14,24)]
    assert set(study.U5).isdisjoint(study.H26)
    assert study.receiver_keys('QK') == [('q',17,24),('k',17,6)]
    assert study.footprint(('k',17,6)) == [24,25,26,27]
    assert study.footprint(('q',17,24)) == [24]
    assert study.receiver_keys('quartet') == [('head',17,h) for h in (24,25,26,27)]


def rows():
    return [dict(id='r0', ids=[1,2,3],length=3,stem='S',truth_id=1,other_id=2),dict(id='r1',ids=[3,2],length=2,stem='T',truth_id=2,other_id=1)]


def test_mixed_bank_preserves_distinct_masks_and_rejects_generated(study):
    source=('head',12,6); receiver=('k',17,6)
    captured=SimpleNamespace(outputs={k:torch.arange(8*224*128).reshape(8,224,128).float() for k in (source,receiver)})
    clean=study.pack_bank(captured,[receiver],rows())
    transplant=study.pack_bank(captured,[source],rows(),maps=[[[0,1],[2,2]],[[1,0]]],donor_rows=rows())
    assert clean[receiver].positions[0].sum()==3 and transplant[source].positions[0].sum()==2
    assert transplant[source].value[0,0,0]==captured.outputs[source][0,1,0]
    assert not clean[receiver].positions[2:].any()
    assert not transplant[source].positions[:,3:].any()
    assert captured.outputs[source].data_ptr()!=transplant[source].value.data_ptr()
    with pytest.raises(ValueError):study.pack_bank(captured,[source],rows(),maps=[[[3,0]],[[1,0]]],donor_rows=rows())
    with pytest.raises(ValueError):study.pack_bank(captured,[('readout',0,0)],rows())
    result=study.compose_banks(transplant,clean)
    assert set(result)=={source,receiver}
    with pytest.raises(ValueError):study.compose_banks(clean,clean)


def test_norms_use_only_original_prefix_and_fp32(study):
    key=('q',17,24); base=torch.zeros(8,224,128,dtype=torch.bfloat16); induced=base.clone()
    induced[0,:3]=2; induced[1,:2]=3; induced[:,4:]=100
    from component_analysis.hooks import Replacement
    mask=study.cc.prefix_positions(rows(),'cpu')
    a={key:Replacement(base,mask)};b={key:Replacement(induced,mask)}
    got=study.bank_norms(a,b,rows())
    assert got[0]['prefix_rms_delta']==2 and got[1]['prefix_rms_delta']==3
    assert got[0]['prefix_coordinate_count']==384 and got[1]['prefix_coordinate_count']==256
    assert got[0]['readout_l2_delta']==pytest.approx(2*128**.5)
    assert got[0]['prefix_rms_clean']==0


@pytest.fixture
def fake(study,monkeypatch):
    from component_analysis import hooks
    calls=[]
    monkeypatch.setattr(hooks,'device_and_dtype',lambda model:(torch.device('cpu'),torch.float32))
    monkeypatch.setattr(hooks,'_hf',lambda model:model)
    def capture(model,ids,mask,*,components,replacements=None):
        calls.append((ids.clone(),mask.clone(),replacements))
        logits=torch.zeros(8,7)
        for i in range(8):logits[i,6 if mask[i].sum()>=3+i else 2]=1
        return SimpleNamespace(logits=logits,outputs={},readout=mask.sum(-1)-1)
    monkeypatch.setattr(hooks,'capture_forward',capture)
    monkeypatch.setattr(study.rp,'capture_logits',lambda model,capture:capture.logits)
    model=SimpleNamespace(config=SimpleNamespace(use_cache=True))
    p={'payload':{'vocab_size':7,'eos':[6]},'scientific_hash':'f'*64,'_tokenizer':SimpleNamespace(decode=lambda ids,**kw:','.join(map(str,ids)))}
    return model,p,calls


def test_decoder_full_vocab_firststep_and_independent_eos(study,fake):
    model,p,calls=fake
    result=study.decode_batch(model,rows(),p)
    assert [r['generated_ids'] for r in result['rows']]==[[6],[2,2,6]]
    assert [r['first_step']['argmax'] for r in result['rows']]==[6,2]
    assert all(r['first_step']['sha256']==r['decoder_first_sha256'] for r in result['rows'])
    assert model.config.use_cache is True
    assert all(tuple(ids.shape)==(8,224) for ids,_,_ in calls)


def test_decoder_bank_masks_fixed_through_forced64(study,fake):
    model,p,calls=fake
    from component_analysis.hooks import Replacement
    mask=study.cc.prefix_positions(rows(),'cpu'); partial=mask.clone();partial[:,1]=False
    bank={('head',12,6):Replacement(torch.ones(8,224,128),partial),('q',17,24):Replacement(torch.ones(8,224,128),mask)}
    result=study.decode_batch(model,rows(),p,bank=bank,stress=True)
    assert all(len(r['generated_ids'])==64 and r['finish']=='stress' for r in result['rows'])
    for ids,attention,replacements in calls:
        if replacements:
            assert not replacements[('q',17,24)].positions[:,3:].any()
            assert replacements[('head',12,6)].positions[0].sum()==2
    bad={('q',17,24):Replacement(torch.ones(8,224,128),torch.ones(8,224,dtype=torch.bool))}
    with pytest.raises(ValueError):study.decode_batch(model,rows(),p,bank=bad)


def test_decoder_numerical_failure_stops_and_restores_cache(study,fake,monkeypatch):
    model,p,calls=fake
    original=study.rp.capture_logits
    monkeypatch.setattr(study.rp,'capture_logits',lambda *args:original(*args)*float('nan'))
    with pytest.raises(ValueError,match='finite'):study.decode_batch(model,rows(),p)
    assert model.config.use_cache is True


def test_exact_contrasts_on_hand_values(study):
    y={f'{i:02d}':float(i) for i in range(1,21)}
    got=study.contrasts(0.,y)
    assert got['delta_U5']==1 and got['delta_H26']==2 and got['interaction_U5_H26']==0
    assert got['block_Q']==0 and got['block_K']==0 and got['block_QK']==0
    assert got['rescue_QK']==11 and got['rescue_quartet']==18
    assert got['interaction_QK_U5']==-3 and got['interaction_QK_clean']==-3 and got['interaction_QK_adjusted']==0


def test_deadline_uses_next_batch_not_whole_panel(study):
    assert study.batch_budget(.2,2,3)==pytest.approx(1.5*128*.2+2+3)
    study.admit(100., 50., now=40.)
    with pytest.raises(TimeoutError):study.admit(100.,61.,now=40.)


def small_protocol(study):
    source=rows()[0]
    return {'payload':{'main':[source],'pairs':[],'calibration':[],'calibration_pairs':[],'eos':[6],'vocab_size':7,
                       'batches':[dict(id='main-b-000',phase='main',arm='00',group=None,row_ids=['r0'])]},
            'scientific_hash':'f'*64,'manifest_hash':'e'*64}


def test_atomic_accept_and_exact_resume_binding(study,fake,tmp_path):
    model,decode_protocol,calls=fake
    result=study.decode_batch(model,rows()[:1],decode_protocol)
    p=small_protocol(study);batch=p['payload']['batches'][0]
    binding=dict(manifest_hash=p['manifest_hash'],hardware={'name':'CPU'})
    run_hash=study.digest(binding)
    study.publish(tmp_path/('run-'+run_hash+'.json'),binding)
    study.accept_batch(tmp_path,p,batch,result,run_hash)
    assert set(study.accepted_batches(tmp_path,p))=={'main-b-000'}
    before=(tmp_path/'main-b-000.accepted.json').read_bytes()
    with pytest.raises(ValueError):study.accept_batch(tmp_path,p,batch,result,run_hash)
    assert (tmp_path/'main-b-000.accepted.json').read_bytes()==before
    bad=deepcopy(p);bad['manifest_hash']='0'*64
    with pytest.raises(ValueError):study.accepted_batches(tmp_path,bad)
    terminal=json.loads(before);terminal['body']['result']['rows'][0]['generated_ids']=[2]
    (tmp_path/'main-b-000.accepted.json').write_text(json.dumps(terminal))
    with pytest.raises(ValueError):study.accepted_batches(tmp_path,p)


def test_publication_crash_before_accept_cannot_create_accepted(study,tmp_path,monkeypatch):
    monkeypatch.setattr(study.cc.os,'link',lambda *args:(_ for _ in ()).throw(OSError('crash')))
    with pytest.raises(OSError):study.publish(tmp_path/'accepted.json',{'science':'retained only on atomic accept'})
    assert not (tmp_path/'accepted.json').exists()


def test_accept_rejects_changed_first_token_and_clean_eos(study,fake):
    model,p,calls=fake;result=study.decode_batch(model,rows()[:1],p)
    protocol=small_protocol(study);batch=protocol['payload']['batches'][0]
    study.validate_result(protocol,batch,result)
    bad=deepcopy(result);bad['rows'][0]['first_step']['argmax']=2
    with pytest.raises(ValueError):study.validate_result(protocol,batch,bad)
    with pytest.raises(ValueError):study.clean_identity(result['rows'],{'r0':dict(generated_ids=[2,6],finish='eos')})


def test_natural_induced_capture_does_not_freeze_intermediate_components(study,monkeypatch):
    from component_analysis import hooks
    source=('head',0,0);receiver=('q',1,0)
    monkeypatch.setattr(study,'U5',[(0,0)])
    monkeypatch.setattr(hooks,'device_and_dtype',lambda m:(torch.device('cpu'),torch.float32))
    def capture(model,ids,mask,*,components,replacements=None):
        # An intervening computation doubles the sender and adds a natural term.
        natural=ids.float().unsqueeze(-1).expand(8,224,128)
        sender=natural.clone()
        if replacements and source in replacements:
            r=replacements[source];sender[r.positions]=r.value[r.positions]
        intermediate=sender*2+7
        outputs={source:sender,receiver:intermediate, hooks.READOUT_KEY:natural}
        return SimpleNamespace(outputs={k:outputs[k] for k in components},logits=torch.zeros(8,7),readout=mask.sum(-1)-1)
    monkeypatch.setattr(hooks,'capture_forward',capture)
    monkeypatch.setattr(study.rp,'capture_logits',lambda m,c:c.logits)
    p={'payload':{'vocab_size':7}}
    rr=rows()[:1];dd=[dict(rr[0],ids=[3,3,3])]
    banks=study.setup_banks(None,rr,dd,[[[0,0],[1,1],[2,2]]],p,[source],[receiver])
    assert banks['clean'][receiver].value[0,0,0]==9
    assert banks['induced'][receiver].value[0,0,0]==13
    assert banks['induced'][receiver].value[0,0,0]!=banks['clean'][receiver].value[0,0,0]
    assert banks['stats']['physical_forwards']==5


def test_schedule_covers_3936_and_calibration_excludes_main(study):
    panel=study.input_panel(json.loads(PARENT.read_text()))
    batches=study.make_batches(panel['main'],panel['pairs'])
    assert len(batches)==492 and sum(len(b['row_ids']) for b in batches)==3936
    assert len({k for b in batches for k in b['row_ids']})==3936
    assert not {r['id'] for r in panel['calibration']} & {r['id'] for r in panel['main']}


def test_export_deduplicates_only_complete_question_views(study):
    p=small_protocol(study);p['payload']['main'][0].update(user='Which will you show?',pair=['alpha','beta'])
    generations=[dict(id='r0',text='S alpha',finish='eos')]
    exported=study.export_views(p,{'rows':generations})
    view=exported['views'][0]
    assert set(view)=={'view_id','question','candidates','response','finish'}
    assert view['question']=='Which will you show?' and view['response']=='S alpha'
    assert exported['protocol_hash']=='e'*64


def test_resume_rejects_unverified_or_hard_failed_attempts(study,tmp_path):
    p=small_protocol(study)
    study.publish(tmp_path/'attempt-a.json',dict(id='a',batch_id='main-b-000',manifest_hash=p['manifest_hash']))
    with pytest.raises(ValueError):study.verify_attempts(tmp_path,p,{})
    receipt=dict(attempt_sha256=study.file_hash(tmp_path/'attempt-a.json'),state='PREEMPTED')
    study.publish(tmp_path/'receipt.json',receipt)
    study.verify_attempts(tmp_path,p,{},tmp_path/'receipt.json')
    study.verify_attempts(tmp_path,p,{})
    study.publish(tmp_path/'failure-b.json',dict(manifest_hash=p['manifest_hash'],attempt_id='b',resumable=False))
    with pytest.raises(ValueError):study.verify_attempts(tmp_path,p,{})


def test_actual_tiny_hooks_natural_induced_differs_from_full_freeze(study,monkeypatch):
    import importlib.metadata
    if importlib.metadata.version('nnsight')!='0.7.0':pytest.skip('pinned nnsight tiny integration runs in mgnp')
    from nnsight import NNsight
    from transformers import LlamaConfig, LlamaForCausalLM
    from component_analysis import hooks
    torch.manual_seed(54)
    model=NNsight(LlamaForCausalLM(LlamaConfig(vocab_size=31,hidden_size=512,intermediate_size=640,num_hidden_layers=2,
        num_attention_heads=4,num_key_value_heads=2,max_position_embeddings=224,attn_implementation='sdpa')).eval())
    monkeypatch.setattr(study,'U5',[(0,0)])
    rr=[dict(rows()[0],truth_id=1,other_id=2)];dd=[dict(rr[0],ids=[4,5,6])]
    protocol={'payload':{'vocab_size':31}}
    source=('head',0,0);receiver=('q',1,0)
    banks=study.setup_banks(model,rr,dd,[[[0,0],[1,1],[2,2]]],protocol,[source],[receiver])
    assert not torch.equal(banks['clean'][receiver].value[0,:3],banks['induced'][receiver].value[0,:3])
    ids,mask,_=study.n.make_batch(rr,batch_size=8,sequence_length=224,device='cpu')
    clean=hooks.capture_forward(model,ids,mask,components=[('mlp',0,0)])
    frozen={source:banks['source'][source],('mlp',0,0):hooks.Replacement(clean.outputs['mlp',0,0],banks['clean'][receiver].positions)}
    observed=hooks.capture_forward(model,ids,mask,components=[receiver],replacements=frozen)
    assert not torch.equal(observed.outputs[receiver][0,:3],banks['induced'][receiver].value[0,:3])
    # The induced bank is in recipient coordinates and equals a manual natural source-only pass.
    manual=hooks.capture_forward(model,ids,mask,components=[receiver],replacements={source:banks['source'][source]})
    assert torch.equal(manual.outputs[receiver],banks['induced'][receiver].value)


def test_freeze_binds_original_inputs_source_and_provisional_execution(study,monkeypatch,tmp_path):
    parent=json.loads(PARENT.read_text());by_prompt={r['prompt']:r['ids'] for r in parent['panel']}
    monkeypatch.setattr(study.n,'load_tokenizer',lambda cache:SimpleNamespace(encode=lambda text,**kw:by_prompt[text]))
    monkeypatch.setattr(study.n,'cache_hashes',lambda cache:{'fixture':'a'*64})
    monkeypatch.setattr(study.n,'software',lambda:{'cpu':'test'})
    monkeypatch.setattr(study,'source_hashes',lambda:{'fixture':'b'*64})
    for name in ('spec','rubric'):(tmp_path/(name+'.md')).write_text(name)
    p=study.build_protocol(PARENT,tmp_path/'spec.md',tmp_path/'rubric.md',study.CACHE,'UNCOMMITTED')
    assert len(p['payload']['batches'])==492
    study.verify_protocol(p)
    with pytest.raises(ValueError):study.verify_protocol(p,execution=True)
    (tmp_path/'spec.md').write_text('drift')
    with pytest.raises(ValueError):study.verify_protocol(p)


def test_forward_honors_actual_deadline_before_model_call(study,fake):
    model,p,calls=fake;p['_deadline']=0
    ids=torch.zeros(8,224,dtype=torch.long);mask=torch.ones_like(ids)
    with pytest.raises(TimeoutError):study.forward(model,ids,mask,p,[])
    assert not calls


def test_partial_decode_evidence_survives_numerical_interruption(study,fake,monkeypatch):
    model,p,calls=fake;state={};original=study.rp.capture_logits;count=[0]
    def fail_later(*args):
        count[0]+=1
        if count[0]>=5:raise TimeoutError('operational interruption')
        return original(*args)
    monkeypatch.setattr(study.rp,'capture_logits',fail_later)
    with pytest.raises(TimeoutError):study.decode_batch(model,rows(),p,state=state)
    assert state['rows'][0]['generated_ids']==[6]
    assert state['rows'][1]['generated_ids']==[2]
    assert model.config.use_cache is True


def test_guard_charges_cold_once_not_once_per_decode_token(study):
    assert study.next_batch_budget(.2,5.,setup_needed=False,shutdown=40.)==pytest.approx(1.5*(129*.2+5)+50)
    assert study.next_batch_budget(.2,5.,setup_needed=True,shutdown=40.)==pytest.approx(1.5*(129*.2+9*5)+50)


def test_terminal_audit_rejects_wrong_frozen_bank_scope(study,fake):
    model,decode_protocol,calls=fake
    from component_analysis.hooks import Replacement
    row=rows()[0];planned=dict(row,id='p0:01',recipient_id='r0')
    mask=torch.zeros(8,224,dtype=torch.bool);mask[0,[0,2]]=True
    bank={('head',12,6):Replacement(torch.ones(8,224,128),mask)}
    result=study.decode_batch(model,[planned],decode_protocol,bank=bank)
    p=small_protocol(study);p['payload'].update(pairs=[dict(id='p0',recipient_id='r0',donor_id='r0',mapping=[[0,0],[2,2]])],
        families={'U5':[[12,6]]},arms=study.arms(),dtype='float32')
    batch=dict(id='main-g-000-a-01',arm='01',phase='main',group='main-g-000',pair_ids=['p0'],row_ids=['p0:01'])
    study.validate_result(p,batch,result)
    bad=deepcopy(result);bad['bank_receipts'][0]['mask_counts'][0]=3
    with pytest.raises(ValueError):study.validate_result(p,batch,bad)


def test_full_panel_analysis_preserves_direction_and_story_balancing(study):
    panel=study.input_panel(json.loads(PARENT.read_text()));source={r['id']:r for r in panel['main']};normalized=[]
    for r in panel['main']:
        normalized.append(dict(id=r['id'],recipient_id=r['id'],pair_id=None,arm=0,margin=0.,candidate=r['truthful_item'],
            truth_name=r['truthful_item'],other_name=r['other_item'],kind='commitment',finish='eos',semantic=None,direction=None))
    for q in panel['pairs']:
        r=source[q['recipient_id']]
        for arm in range(1,21):
            normalized.append(dict(id=q['id']+f':{arm:02d}',recipient_id=r['id'],pair_id=q['id'],arm=arm,margin=float(arm),
                candidate=r['truthful_item'],truth_name=r['truthful_item'],other_name=r['other_item'],kind='commitment',finish='eos',semantic=None,direction=q['direction']))
    baseline={r['recipient_id']:r for r in normalized if r['arm']==0}
    cases=[q for q in panel['pairs'] if q['direction']=='P0<-N0'][:5]
    # Same/different committed identities, refusal/evasion, cap, and one-sided choice.
    baseline[cases[1]['donor_id']]['candidate']=baseline[cases[1]['donor_id']]['other_name']
    for identifier,kind,finish in [(cases[2]['recipient_id'],'explicit_refusal','eos'),
                                   (cases[2]['donor_id'],'coherent_evasion','eos'),
                                   (cases[3]['recipient_id'],'capped','capped'),
                                   (cases[4]['donor_id'],'explicit_refusal','eos')]:
        baseline[identifier].update(candidate=None,kind=kind,finish=finish)
    no_damaging_choice={cases[1]['donor_id'],cases[2]['recipient_id'],cases[2]['donor_id'],cases[3]['recipient_id'],cases[4]['donor_id']}
    analysis=study.analyze_panel({'payload':panel,'manifest_hash':'e'*64},normalized)
    assert len(analysis['pairs'])==192 and len(analysis['arm_counts'])==160
    selected=[r for r in analysis['summaries'] if r['endpoint']=='margin' and r['contrast']=='delta_U5']
    assert len(selected)==8 and all(r['mean']==1. and r['ci95']==[1.,1.] and r['n_stories']==24 for r in selected)
    by_pair={r['pair_id']:r for r in analysis['pairs']}
    assert [by_pair[q['id']]['baseline_agreement'] for q in cases]==[True,False,None,None,None]
    assert len(normalized)==3936 and len(baseline)==96
    for result in analysis['pairs']:
        expected_delta=1. if result['recipient_id'] in no_damaging_choice else 0.
        assert result['contrasts']['damaging']['delta_U5']==expected_delta
        assert result['contrasts']['damaging']['interaction_U5_H26']==-expected_delta


def test_cpu_runtime_pipeline_binds_receipts_and_calibration_costs(study,fake,monkeypatch,tmp_path):
    import time
    model,decode_protocol,calls=fake;p=small_protocol(study);batch=p['payload']['batches'][0]
    p['payload'].update(main=[],calibration=[rows()[0]],calibration_batches=[batch],forced_arms=[],families={},arms=study.arms())
    p['provenance']={'cache':'CPU'}
    monkeypatch.setattr(study,'verify_protocol',lambda *args,**kw:None)
    monkeypatch.setattr(study,'allocation_interval',lambda:dict(job_id='CPU',start=time.time()-2,end=time.time()+600))
    monkeypatch.setattr(study.clause,'hardware_identity',lambda:{'name':'CPU'})
    monkeypatch.setattr(study.clause,'load_runtime_model',lambda p:model)
    monkeypatch.setattr(study.n,'load_tokenizer',lambda cache:decode_protocol['_tokenizer'])
    monkeypatch.setattr(study.hooks,'geometry',lambda m:dict(num_layers=32,num_heads=32,head_dim=128,num_kv_heads=8,heads_per_group=4,hidden_size=4096))
    out=tmp_path/'run'
    result=study.run(p,out,calibration=True,initial_forward_seconds=.001,shutdown_seconds=0.)
    assert result['status']=='completed'
    assert len(study.accepted_batches(out,p,calibration=True))==1
    summary=study.read_json(out/'calibration.json')
    assert summary['startup_seconds']>=2
    assert summary['forecast']['publication_seconds']>0
    assert summary['forecast']['read_hash_seconds']>0


@pytest.fixture
def failure_run(study,monkeypatch,tmp_path):
    """Run the real journal/decoder with only the external model forward replaced."""
    import time
    from component_analysis import hooks
    sources=rows();baseline=dict(id='cal-b-000',phase='cal',arm='00',group=None,row_ids=['r0','r1'])
    pairs=[dict(id=f'p{i}',recipient_id=f'r{i%2}',donor_id=f'r{i%2}',mapping=[[j,j] for j in range(sources[i%2]['length'])]) for i in range(4)]
    groups=[dict(id=f'cal-g-{i:03d}-a-01',phase='cal',arm='01',group=f'cal-g-{i:03d}',pair_ids=[f'p{2*i}',f'p{2*i+1}'],row_ids=[f'p{2*i}:01',f'p{2*i+1}:01']) for i in range(2)]
    p=dict(payload=dict(main=[],calibration=sources,pairs=[],calibration_pairs=pairs,eos=[6],vocab_size=7,dtype='float32',
        batches=[],calibration_batches=[baseline,groups[0]],forced_arms=[],arms=study.arms(),families={'U5':[list(k) for k in study.U5],'S32':[list(k) for k in study.U5]}),
        scientific_hash='f'*64,manifest_hash='e'*64,provenance={'cache':'CPU'})
    model=SimpleNamespace(config=SimpleNamespace(use_cache=True))
    monkeypatch.setattr(study,'verify_protocol',lambda *args,**kw:None)
    monkeypatch.setattr(study,'allocation_interval',lambda:dict(job_id='CPU',start=time.time()-2,end=time.time()+600))
    monkeypatch.setattr(study.clause,'hardware_identity',lambda:{'name':'CPU'})
    monkeypatch.setattr(study.clause,'load_runtime_model',lambda p:model)
    monkeypatch.setattr(study.n,'load_tokenizer',lambda cache:SimpleNamespace(decode=lambda ids,**kw:','.join(map(str,ids))))
    monkeypatch.setattr(hooks,'device_and_dtype',lambda m:(torch.device('cpu'),torch.float32))
    monkeypatch.setattr(hooks,'_hf',lambda m:m)
    monkeypatch.setattr(hooks,'geometry',lambda m:dict(num_layers=32,num_heads=32,head_dim=128,num_kv_heads=8,heads_per_group=4,hidden_size=4096))
    def execute(mode):
        counts={'late':0,'clean_capture':0}
        source_keys=[('head',l,h) for l,h in study.U5]
        receivers=list(dict.fromkeys(k for name in ('QK','V','quartet','K0') for k in study.receiver_keys(name)))
        def capture(model,ids,mask,*,components,replacements=None):
            logits=torch.zeros(8,7)
            for i in range(8):logits[i,6 if mask[i].sum()>=3+i else 2]=1
            if components==list(dict.fromkeys(source_keys+receivers))+[hooks.READOUT_KEY]:
                counts['clean_capture']+=1
                if mode=='new_setup' and counts['clean_capture']==2:logits[1,0]=float('nan')
            if mode=='donor' and components==source_keys+[hooks.READOUT_KEY] and replacements is None:logits[1,0]+=.001
            if mode=='induced' and components==receivers+[hooks.READOUT_KEY] and replacements:logits[1,0]+=.001
            if mode in ('late','nan','geometry') and components==[hooks.READOUT_KEY] and replacements and set(replacements)==set(source_keys) and int(mask[1].sum())==3:
                counts['late']+=1
                if counts['late']==2:
                    if mode=='late':logits[1,0]+=.001
                    elif mode=='nan':logits[1,0]=float('nan')
                    else:logits=logits[:,:6]
            outputs={k:ids.float().unsqueeze(-1).expand(8,224,128).clone() for k in components}
            return SimpleNamespace(logits=logits,outputs=outputs,readout=mask.sum(-1)-1)
        monkeypatch.setattr(hooks,'capture_forward',capture)
        monkeypatch.setattr(study.rp,'capture_logits',lambda m,c:c.logits)
        if mode=='new_setup':p['payload']['calibration_batches'].append(groups[1])
        directory=tmp_path/mode
        return p,directory,lambda:study.run(p,directory,calibration=True,initial_forward_seconds=.001,shutdown_seconds=0.)
    return execute


def test_late_mismatch_publishes_failed_and_prior_slot_receipts(failure_run,study):
    p,directory,execute=failure_run('late')
    with pytest.raises(ValueError):execute()
    failure=study.read_json(next(directory.glob('failure-*.json')))
    assert failure['batch']['id']=='cal-g-000-a-01' and failure['resumable'] is False
    partial=failure['partial'];controls=partial['controls']
    failed=[c for c in controls if c['control']=='patched_repeat' and c['step']==1]
    assert [c['row_id'] for c in failed]==['p0:01','p1:01']
    assert failed[0]['pass'] is True
    assert failed[1]['physical_slot']==1 and failed[1]['pass'] is False and failed[1]['finite'] is True
    assert failed[1]['bitwise'] is False and failed[1]['identical_greedy'] is True and failed[1]['max_abs_error']>1e-5
    assert failed[1]['expected_sha256']!=failed[1]['observed_sha256']
    assert partial['rows'][1]['generated_ids']==[2] and failure['error'].startswith('ValueError:')
    assert not (directory/'cal-g-000-a-01.accepted.json').exists()
    with pytest.raises(ValueError,match='hard failure'):study.verify_attempts(directory,p,study.accepted_batches(directory,p,calibration=True))


@pytest.mark.parametrize('mode',['nan','geometry'])
def test_forward_rejection_persists_current_decode_context(failure_run,study,mode):
    p,directory,execute=failure_run(mode)
    with pytest.raises(ValueError):execute()
    failure=study.read_json(next(directory.glob('failure-*.json')))
    diagnostic=failure['partial']['forward_failures'][-1]
    assert diagnostic['control']=='patched_repeat' and diagnostic['step']==1
    assert diagnostic['row_ids']==['p0:01','p1:01'] and diagnostic['readouts'][:2]==[2,2]
    assert diagnostic['shape']==([8,6] if mode=='geometry' else [8,7])
    assert len(diagnostic['observed_sha256'])==8 and failure['resumable'] is False
    assert diagnostic['nonfinite_physical_slots']==([1] if mode=='nan' else [])
    assert failure['partial']['rows'][1]['generated_ids']==[2]
    assert not (directory/'cal-g-000-a-01.accepted.json').exists()


def test_new_setup_failure_never_borrows_preceding_accepted_rows(failure_run,study):
    p,directory,execute=failure_run('new_setup')
    with pytest.raises(ValueError):execute()
    assert (directory/'cal-g-000-a-01.accepted.json').exists()
    failure=study.read_json(next(directory.glob('failure-*.json')))
    assert failure['batch']['id']=='cal-g-001-a-01'
    assert failure['partial']['attempt_context']['batch_id']=='cal-g-001-a-01'
    assert failure['partial']['rows']==[]
    assert failure['partial']['forward_failures'][-1]['control']=='setup_recipient_capture'


@pytest.mark.parametrize('mode,control',[('donor','setup_donor_readout'),('induced','setup_U5_readout')])
def test_setup_specific_drift_hard_stops_with_persisted_full_vectors(failure_run,study,mode,control):
    p,directory,execute=failure_run(mode)
    with pytest.raises(ValueError):execute()
    failure=study.read_json(next(directory.glob('failure-*.json')))
    receipt=failure['partial']['setup']['controls'][-1]
    assert receipt['control']==control and receipt['row_id']=='r1' and receipt['physical_slot']==1
    assert receipt['pass'] is False and receipt['finite'] is True and receipt['max_abs_error']>1e-5
    assert receipt['expected_sha256']!=receipt['observed_sha256']
    assert failure['resumable'] is False and not (directory/'cal-g-000-a-01.accepted.json').exists()


def test_matching_setup_retains_donor_and_U5_full_vocab_controls(failure_run,study):
    p,directory,execute=failure_run('matching');assert execute()['status']=='completed'
    setup=study.read_json(next(directory.glob('setup-*.json')))
    for name in ('setup_donor_readout','setup_U5_readout'):
        receipts=[c for c in setup['controls'] if c['control']==name]
        assert len(receipts)==2 and all(c['pass'] and c['expected_sha256']==c['observed_sha256'] for c in receipts)
    assert setup['stats']['physical_forwards']==8


def test_calibration_cold_bound_includes_setup_capture_calls(study):
    protocol={'payload':{'calibration_batches':[{'id':'b0','arm':'00'}]}}
    accepted={'b0':dict(elapsed_seconds=1.,max_forward_seconds=.2,setup={'runtime':{'max_forward_seconds':5.}},
        timings={'decoder':dict(readout_only=True,count=2,warm_max_seconds=.2)})}
    forecast=study.calibration_forecast(protocol,accepted)
    assert forecast['max_forward_seconds']==5. and forecast['steady_forward_seconds']==.2
