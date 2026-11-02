"""Real native-hook patching on CPU random tiny Llama; no downloaded model."""
import pytest
nnsight=pytest.importorskip('nnsight')
if nnsight.__version__!='0.7.0':
    pytest.skip(f'nnsight {nnsight.__version__} installed; pinned 0.7.0 required',allow_module_level=True)
import torch
from component_analysis import hooks
from component_analysis.specificity_ladder import LadderBatch, score_cell, positive_control, collect_h_mean_bank
from tests.helpers import tiny_config, TINY

@pytest.fixture(scope='module')
def model():
    from nnsight import NNsight
    from transformers import LlamaForCausalLM
    torch.manual_seed(41)
    return NNsight(LlamaForCausalLM(tiny_config(attn_implementation='sdpa')).eval())


def make(condition='D',stream='clean',split='test',ids=None):
    tokens=torch.tensor([[1,2,3,4,5],[8,9,10,0,0]])
    if stream=='corrupt': tokens=torch.tensor([[6,7,9,3,2],[2,4,6,0,0]])
    mask=torch.tensor([[1,1,1,1,1],[1,1,1,0,0]])
    records=[dict(split=split,source_condition=condition,source_hash='test-source',
                  layout=dict(role_spans=[['user',0,length]],content_spans=[['text',0,length]])) for length in (5,3)]
    return LadderBatch(ids or ['a','b'],condition,stream,tokens,mask,torch.tensor([4,2]),
                       torch.tensor([11,12]),torch.tensor([13,14]),torch.tensor([11,12]),records,'far_v2')


def maps(batch,donor,operation='item_swap'):
    return [dict(operation=operation,recipient_id=rid,recipient_condition=batch.condition,recipient_stream=batch.stream,
                 donor_id=donor.ids[i],donor_condition=donor.condition,donor_stream=donor.stream,
                 recipient_positions=list(range(int(batch.attention_mask[i].sum()))),
                 donor_positions=list(range(int(donor.attention_mask[i].sum()))),covered_positions=int(batch.attention_mask[i].sum()),
                 supported=True,degenerate=False,gate_valid=True,seed=None) for i,rid in enumerate(batch.ids)]


def test_joint_mixed_group_matches_direct_joint_patch_and_subtraction(model):
    b=make(); d=make(stream='corrupt')
    keys=[('head',0,1),('mlp',1,0)]
    rows=score_cell(model,[b],groups=[('full',keys),('minus',[keys[1]])],operation='item_swap',donor_batches=[d],donor_maps=maps(b,d))
    assert len(rows)==4
    capture=hooks.capture_forward(model,b.input_ids,b.attention_mask,components=keys,positions=b.readout)
    donor=hooks.capture_forward(model,d.input_ids,d.attention_mask,components=keys,positions=d.readout)
    replacements={k:hooks.Replacement(donor.outputs[k],b.attention_mask.bool()) for k in keys}
    direct=hooks.capture_forward(model,b.input_ids,b.attention_mask,components=keys,positions=b.readout,replacements=replacements)
    logits=hooks.readout_logits(model,direct.residual[:,-1])
    expected=logits[torch.arange(2),b.opposite_token]-logits[torch.arange(2),b.honest_token]
    assert [r['patched_margin'] for r in rows if r['group']=='full']==pytest.approx(expected.tolist(),abs=1e-6)
    assert any(r['patched_margin']!=r['intact_margin'] for r in rows)
    assert all(r['self_replay_margin_error']<=1e-5 for r in rows)


def test_empty_self_and_nonidentity_h_twin(model):
    b=make('H'); keys=[('head',1,2),('mlp',0,0)]
    for operation in ('empty','self_replay'):
        rows=score_cell(model,[b],groups=[('g',keys)],operation=operation)
        assert all(r['intact_margin']==pytest.approx(r['patched_margin'],abs=1e-6) for r in rows)
        assert all(not r['gate_valid'] for r in rows)
    recipient=make('D'); donor=make('H'); donor.input_ids=make(stream='corrupt').input_ids
    plan=maps(recipient,donor,'h_twin')
    rows=score_cell(model,[recipient],groups=[('g',keys)],operation='h_twin',donor_batches=[donor],donor_maps=plan)
    assert any(abs(r['patched_margin']-r['intact_margin'])>1e-6 for r in rows)


def test_readout_only_positive_control_includes_embeddings(model):
    b=make(); donor=make(stream='corrupt'); plan=maps(b,donor)
    for i,m in enumerate(plan):
        m['recipient_positions']=[int(b.readout[i])];m['donor_positions']=[int(donor.readout[i])]
    result=positive_control(model,[b],donor_batches=[donor],donor_maps=plan)
    assert all(r['valid'] and r['max_abs_logit_error']<1e-5 for r in result)
    assert all(list(hooks.EMBED_KEY) in r['sender_keys'] for r in result)


def test_h_mean_is_equal_token_pool_both_streams_and_casts(model):
    b=make('H',split='train',ids=['train-a','train-b']); d=make('H',stream='corrupt',split='train',ids=['train-a','train-b']); keys=[('head',0,1),('mlp',1,0)]
    bank=collect_h_mean_bank(model,[b,d],keys)
    assert bank['provenance']['n_tokens']==16
    for key in keys:
        total=0
        for one in (b,d):
            cap=hooks.capture_forward(model,one.input_ids,one.attention_mask,components=keys)
            total=total+(cap.outputs[key].float()*one.attention_mask[:,:,None]).sum((0,1))
        assert torch.allclose(bank['values'][key],total/16)
    rows=score_cell(model,[make()],groups=[('g',keys)],operation='h_mean',mean_bank=bank)
    assert all(r['mean_bank_provenance']['source_condition']=='H' for r in rows)


def test_full_vocabulary_accuracy_is_separate_from_binary_win(model):
    from component_analysis.specificity_ladder import _stats
    b=make(); logits=torch.zeros(2,TINY['vocab']); logits[:,20]=3
    logits[torch.arange(2),b.opposite_token]=2; logits[torch.arange(2),b.honest_token]=1
    stats=_stats(b,logits,logits)
    assert stats['binary_win'].all()
    assert not stats['correct'].any()
    b.choice_tokens=torch.tensor([[11,13,15,17],[12,14,16,18]])
    stats=_stats(b,logits,logits)
    assert stats['choice_correct'].all()
    assert stats['choice_margin'].tolist()==[1.,1.]


def test_forged_layout_and_identity_maps_fail_closed(model):
    b=make(); d=make(stream='corrupt'); p=maps(b,d)
    d.records[0]['layout']['content_spans']=[['invented',0,5]]
    with pytest.raises(ValueError,match='layout'):
        score_cell(model,[b],groups=[('g',[('mlp',0,0)])],operation='item_swap',donor_batches=[d],donor_maps=p)
    h=make('H'); p=maps(h,h,'h_twin')  # deliberately lies about identity
    rows=score_cell(model,[h],groups=[('g',[('mlp',0,0)])],operation='h_twin',donor_batches=[h],donor_maps=p)
    assert all(r['degenerate'] and not r['gate_valid'] for r in rows)


def test_recipient_ids_cannot_enter_h_mean_source(model):
    h=make('H',split='train'); hc=make('H',stream='corrupt',split='train')
    bank=collect_h_mean_bank(model,[h,hc],[('mlp',0,0)])
    with pytest.raises(ValueError,match='recipient'):
        score_cell(model,[make()],groups=[('g',[('mlp',0,0)])],operation='h_mean',mean_bank=bank)


def adapter_rows(monkeypatch, *, identity=False, unsupported=False, seed=1):
    from component_analysis import ladder_tasks as tasks
    from tests.test_ladder_tasks import Tokenizer, source
    class SmallTokenizer(Tokenizer):
        def encode(self, text, add_special_tokens=False):
            return [v % 90 + 2 for v in super().encode(text, add_special_tokens)]
    def generate(tok, count, donor_seed):
        item=source(stem=('Then, Bob and Alice met. Bob gave it to' if donor_seed==1
                          else 'Later Bob and Alice met. Bob gave it to'))
        if identity: item['corrupted_sentence']=item['sentence'][:-5]+'Bob'
        if unsupported: item['corrupted_sentence']='Short Bob'
        return [item]
    monkeypatch.setattr(tasks,'_generate_ioi',generate)
    tokenizer=SmallTokenizer()
    return tasks,tokenizer,tasks.ioi_rows(tokenizer,n=1,seed=seed)


@pytest.mark.parametrize('kind',['supported','identity','unsupported'])
def test_actual_ioi_adapter_maps_run_on_tiny_model(model,monkeypatch,kind):
    tasks,_,rows=adapter_rows(monkeypatch,identity=kind=='identity',unsupported=kind=='unsupported')
    plan=tasks.ioi_item_swap_maps(rows)
    result=score_cell(model,tasks.task_batches(rows),groups=[('g',[('mlp',0,0)])],
                      operation='item_swap',donor_batches=tasks.task_batches(rows,stream='corrupt'),donor_maps=plan)[0]
    assert result['supported']==(kind!='unsupported')
    assert result['gate_valid']==(kind=='supported')
    assert plan[0]['requested_positions']==len(rows[0]['streams']['clean']['tokens'])
    assert plan[0]['covered_positions']==(0 if kind=='unsupported' else plan[0]['requested_positions'])
    if kind=='identity': assert result['degenerate']


def test_actual_ioi_task_resample_is_distinct_and_checks_sources(model,monkeypatch):
    tasks,tok,rows=adapter_rows(monkeypatch)
    donors,plan=tasks.ioi_task_resample(tok,rows,donor_seeds=(101,))
    kwargs=dict(groups=[('g',[('mlp',0,0)])],operation='task_resample',donor_maps=plan)
    result=score_cell(model,tasks.task_batches(rows),donor_batches=tasks.task_batches(donors),**kwargs)[0]
    assert result['supported'] and result['donor_seed']==101
    assert result['donor_provenance']['donor_source_hash']==donors[0]['source_hash']
    for field,value in [('source_hash','forged'),('split','test'),('a','Someone')]:
        bad=tasks.task_batches(donors)
        bad[0].records[0][field]=value
        with pytest.raises(ValueError,match='own-task'):
            score_cell(model,tasks.task_batches(rows),donor_batches=bad,**kwargs)
    with pytest.raises(ValueError,match='H-derived'):
        score_cell(model,tasks.task_batches(rows),donor_batches=tasks.task_batches(donors),
                   groups=kwargs['groups'],operation='independent_resample',
                   donor_maps=[dict(m,operation='independent_resample') for m in plan])


def test_positive_control_128_129_recovers_donor_and_noops_on_common_shape(model,monkeypatch):
    """Real native hooks audit calibration geometry, residual, logits and noops."""
    from component_analysis import specificity_ladder as runner
    from tests.test_specificity_ladder_calibration import singleton, plan
    recipient,donor=singleton(128),singleton(129,'corrupt')
    recipient.input_ids=recipient.input_ids.long()
    donor.input_ids=donor.input_ids.long()
    # Observe real captures: no replacement of the model or tracing machinery.
    original_capture=runner._capture
    captures=[]
    def observe(model,batch,keys,replacements=None):
        assert batch.input_ids.shape==(1,129)
        capture,logits=original_capture(model,batch,keys,replacements)
        captures.append((batch,capture,logits))
        return capture,logits
    monkeypatch.setattr(runner,'_capture',observe)
    result=runner.positive_control(model,[recipient],donor_batches=[donor],donor_maps=[plan()])
    assert len(result)==1 and result[0]['valid']
    assert list(hooks.EMBED_KEY) in result[0]['sender_keys']
    assert list(hooks.READOUT_KEY) not in result[0]['sender_keys']
    _,dc,dl=captures[1]
    _,patched,pl=captures[2]
    assert torch.allclose(pl,dl,atol=1e-5,rtol=1e-5)
    assert torch.allclose(patched.logits,dc.logits,atol=1e-5,rtol=1e-5)
    assert torch.allclose(patched.residual[:,-1],dc.residual[:,-1],atol=1e-5,rtol=1e-5)
    keys=hooks.all_component_keys(model)
    for batch,capture,logits in captures[:2]:
        for replacements in ({},{k:hooks.Replacement(capture.outputs[k],batch.attention_mask.bool()) for k in keys}):
            noop,nl=original_capture(model,batch,keys,replacements)
            runner._noop_error(logits,nl,batch)
            assert torch.allclose(nl,logits,atol=1e-5,rtol=1e-5)
            assert torch.allclose(noop.residual[:,-1],capture.residual[:,-1],atol=1e-5,rtol=1e-5)
    assert recipient.input_ids.shape==(1,128) and donor.input_ids.shape==(1,129)
