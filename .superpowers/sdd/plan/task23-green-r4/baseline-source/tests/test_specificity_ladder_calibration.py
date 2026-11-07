"""Padding geometry contract of positive calibration; no scientific scoring."""
from dataclasses import replace
import pytest
import torch
from component_analysis import hooks, specificity_ladder as runner


def singleton(width, stream='clean'):
    ids = torch.zeros((1,width),dtype=torch.int32)
    ids[0,:128] = torch.arange(128,dtype=torch.int32) % 90 + 1
    if stream == 'corrupt':
        ids[0,0] = 2
    mask = torch.zeros_like(ids,dtype=torch.bool)
    mask[:,:128] = True
    return runner.LadderBatch(['boundary'], 'I', stream, ids, mask,
            torch.tensor([127]),torch.tensor([3]),torch.tensor([4]),torch.tensor([3]),
            [{'split':'test','source_condition':'I'}], 'ser_v2')


def plan():
    return dict(recipient_condition='I',recipient_id='boundary',recipient_stream='clean',
                donor_condition='I',donor_id='boundary',donor_stream='corrupt',
                recipient_positions=[127],donor_positions=[127],supported=True)


def test_positive_calibration_aligns_128_129_before_any_capture(monkeypatch):
    """Omitting alignment makes this synthetic shape-sensitive recovery fail."""
    keys = [hooks.EMBED_KEY]
    monkeypatch.setattr(hooks,'all_component_keys',lambda model:keys)
    seen = []
    def capture(model,batch,components,replacements=None):
        width = batch.input_ids.shape[1]
        seen.append((width,batch.input_ids.clone(),batch.attention_mask.clone(),batch.readout.clone()))
        value = float(batch.input_ids[0,0])
        outputs = {hooks.EMBED_KEY:torch.full((1,width,2),value)}
        if replacements:
            value = float(replacements[hooks.EMBED_KEY].value[0,127,0])
        residual = torch.full((1,2,2),value)
        logits = torch.tensor([[value,width*.01]])
        return hooks.Capture(logits,outputs,residual,batch.readout),logits
    monkeypatch.setattr(runner,'_capture',capture)
    recipient, donor = singleton(128), singleton(129,'corrupt')
    result = runner.positive_control(object(),[recipient],donor_batches=[donor],donor_maps=[plan()])
    assert result[0]['valid'] and result[0]['max_abs_logit_error']==0
    assert [width for width,*_ in seen] == [129,129,129]
    for _,ids,mask,readout in seen:
        assert ids.dtype==torch.int32 and mask.dtype==torch.bool
        assert ids.device==recipient.input_ids.device
        assert mask.sum()==128 and not mask[0,128] and ids[0,128]==0
        assert readout.tolist()==[127]
    assert recipient.input_ids.shape[1]==128  # no mutation of input views
    assert donor.input_ids.shape[1]==129


@pytest.mark.parametrize('mask_dtype',[torch.bool,torch.int64,torch.float32])
def test_calibration_padding_preserves_absolute_geometry(mask_dtype):
    original = singleton(128)
    original.attention_mask = original.attention_mask.to(mask_dtype)
    got = runner._pad_calibration_batch(original,129)
    assert torch.equal(got.input_ids[:,:128],original.input_ids)
    assert torch.equal(got.attention_mask[:,:128],original.attention_mask)
    assert got.input_ids.dtype==original.input_ids.dtype
    assert got.attention_mask.dtype==mask_dtype
    assert got.input_ids.device==original.input_ids.device
    assert got.attention_mask.device==original.attention_mask.device
    assert got.readout is original.readout and got.records is original.records
    assert got.opposite_token is original.opposite_token
    assert got.honest_token is original.honest_token
    assert got.expected_token is original.expected_token
    assert got.attention_mask[0,128]==0 and got.input_ids[0,128]==0
    assert runner._pad_calibration_batch(original,128) is original


@pytest.mark.parametrize('width',[127,0,-1,129.0,True])
def test_calibration_padding_refuses_truncation_and_invalid_width(width):
    with pytest.raises(ValueError):
        runner._pad_calibration_batch(singleton(128),width)


@pytest.mark.parametrize('invalid',['hole','padded_readout','float_readout','float_tokens','multiple_rows'])
def test_calibration_padding_rejects_invalid_input_geometry(invalid):
    batch=singleton(129)
    if invalid=='hole': batch.attention_mask[0,2]=False
    elif invalid=='padded_readout': batch.readout[0]=128
    elif invalid=='float_readout': batch.readout=batch.readout.float()
    elif invalid=='float_tokens': batch.input_ids=batch.input_ids.float()
    else:
        batch=replace(batch,ids=['a','b'],records=[{},{}],
                      input_ids=batch.input_ids.expand(2,-1),attention_mask=batch.attention_mask.expand(2,-1),
                      readout=batch.readout.expand(2),opposite_token=batch.opposite_token.expand(2),
                      honest_token=batch.honest_token.expand(2),expected_token=batch.expected_token.expand(2))
    with pytest.raises(ValueError):
        runner._pad_calibration_batch(batch,130)
