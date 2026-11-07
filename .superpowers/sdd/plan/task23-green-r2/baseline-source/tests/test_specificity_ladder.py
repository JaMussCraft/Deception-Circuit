import pytest
import torch
from component_analysis.specificity_ladder import LadderBatch, validate_batch, mapped_replacement, collect_h_mean_bank


def batch():
    return LadderBatch(ids=['a','b'], condition='D', stream='clean',input_ids=torch.tensor([[1,2,3],[4,5,0]]),attention_mask=torch.tensor([[1,1,1],[1,1,0]]),readout=torch.tensor([2,1]),opposite_token=torch.tensor([6,7]),honest_token=torch.tensor([8,9]),expected_token=torch.tensor([6,7]),records=[{'split':'test'},{'split':'test'}])


def test_right_padding_and_explicit_readout():
    b=batch(); validate_batch(b)
    b.readout[1]=2
    with pytest.raises(ValueError,match='readout'): validate_batch(b)
    b=batch(); b.attention_mask[1]=torch.tensor([1,0,1])
    with pytest.raises(ValueError,match='right'): validate_batch(b)


def test_mapped_write_gathers_each_donor_without_writing_padding():
    recipient=torch.zeros(2,3,2)
    donor=torch.arange(16).reshape(2,4,2).float()
    maps=[{'recipient_positions':[0,1,2],'donor_positions':[1,2,3]}, {'recipient_positions':[0,1],'donor_positions':[2,3]}]
    r=mapped_replacement(recipient,donor,maps,torch.tensor([[1,1,1],[1,1,0]]),torch.ones(2,4))
    assert torch.equal(r.value[0],donor[0,1:])
    assert torch.equal(r.value[1,:2],donor[1,2:])
    assert not r.positions[1,2]
    maps[1]['recipient_positions']=[0,2]
    with pytest.raises(ValueError,match='unpadded'): mapped_replacement(recipient,donor,maps,torch.tensor([[1,1,1],[1,1,0]]),torch.ones(2,4))


def test_mean_bank_rejects_recipient_or_missing_provenance():
    b=batch()
    with pytest.raises(ValueError,match='original H'): collect_h_mean_bank(None,[b],[])


def test_reject_position_map_duplicate_and_donor_padding():
    m=[dict(recipient_positions=[0,0],donor_positions=[0,1])]
    with pytest.raises(ValueError,match='duplicate'):
        mapped_replacement(torch.zeros(1,2,2),torch.zeros(1,2,2),m,torch.ones(1,2),torch.ones(1,2))
    m=[dict(recipient_positions=[0,1],donor_positions=[0,1])]
    with pytest.raises(ValueError,match='donor.*unpadded'):
        mapped_replacement(torch.zeros(1,2,2),torch.zeros(1,2,2),m,torch.ones(1,2),torch.tensor([[1,0]]))


def test_noop_fails_closed_on_argmax_even_when_binary_margin_equal():
    from component_analysis.specificity_ladder import _noop_error
    b=batch(); base=torch.zeros(2,20); other=base.clone()
    base[:,10]=3;other[:,11]=3
    with pytest.raises(ValueError,match='assay invalid'):_noop_error(base,other,b)


def test_noop_fails_closed_when_margin_drifts_without_argmax_change():
    from component_analysis.specificity_ladder import _noop_error
    b=batch(); base=torch.zeros(2,20); base[:,10]=3; other=base.clone(); other[:,6]=.01
    with pytest.raises(ValueError,match='assay invalid'): _noop_error(base,other,b)


def test_explicit_twin_and_independent_donor_identity_rules():
    from component_analysis.specificity_ladder import _check_map
    b=batch()
    d=batch(); d.condition='H'; d.records=[dict(split='train'),dict(split='train')]
    # One row is enough to validate the semantic donor identity check before layout.
    from component_analysis.specificity_ladder import _rows
    b=next(_rows(b));d=next(_rows(d))
    plan=dict(supported=True,recipient_positions=[0,1,2],donor_positions=[0,1,2],covered_positions=3)
    with pytest.raises(ValueError,match='different-instance'):_check_map(b,d,plan,'independent_resample')
    d.stream='corrupt'
    with pytest.raises(ValueError,match='same-instance same-stream'):_check_map(b,d,plan,'h_twin')
