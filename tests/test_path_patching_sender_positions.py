"""
Sender position masks in `path_patching.receiver_inputs` (B1 plan, ticket 2).

`sender_positions` is one `[batch, seq]` boolean mask applied to every key in
`senders`: the sender carries its corrupt value at the masked positions and its
clean capture everywhere else. `None` keeps the old behaviour, the sender
corrupt at every position. Sections 1.5 and 2.3 of the B1 plan write one joint
sender (the quartet) at one mask per call, so one mask is the whole interface.

Same 2-layer random Llama and the same nnsight 0.7.0 gate as
`tests/test_path_patching_passes.py`, whose fixtures are reused.
"""

from __future__ import annotations

import pytest

nnsight = pytest.importorskip("nnsight")
PINNED = "0.7.0"
if nnsight.__version__ != PINNED:
    pytest.skip(f"nnsight {nnsight.__version__} is installed, not the pinned "
                f"{PINNED}; these are 0.7.0 behaviours.",
                allow_module_level=True)

import torch                                               # noqa: E402

from component_analysis import hooks                       # noqa: E402
from component_analysis import path_patching as pp         # noqa: E402
from tests.helpers import TINY                             # noqa: E402
from tests.test_path_patching_passes import (              # noqa: E402,F401
    batch, fp32_readout, model, streams, whole_model_grid)

LAST_MLP = ("mlp", TINY["layers"] - 1, 0)
EARLY_HEAD = ("head", 0, 1)


def two_pass(model, streams, senders, receivers, **kwargs):
    """`patched_readout`'s composition, with the new keyword passed to pass 1."""
    captured = pp.receiver_inputs(model, streams, senders=senders,
                                  receivers=receivers, **kwargs)
    return pp.readout_from_receivers(
        model, streams, {key: captured.outputs[key] for key in receivers})


def readout_only(streams):
    """`[batch, seq]` True only at each row's own Readout (row 1 is padded)."""
    mask = torch.zeros(streams.input_ids.shape, dtype=torch.bool)
    mask[torch.arange(mask.shape[0]), streams.positions.cpu()] = True
    return mask


def test_the_readout_mask_is_per_row(streams):
    """Row 1 is padded, so its Readout is not the last column; a mask built
    from -1 would put the patch on a pad token there."""
    mask = readout_only(streams)
    assert mask.sum().item() == mask.shape[0]
    assert streams.positions[0].item() != streams.positions[1].item()


@pytest.mark.parametrize("senders", [[EARLY_HEAD], [LAST_MLP],
                                     [EARLY_HEAD, ("head", 0, 2), LAST_MLP]])
def test_an_all_true_mask_is_bit_identical_to_none(model, streams, senders):
    receivers = [("q", 1, 0), ("k", 1, 1), ("mlp_in", 1, 0), pp.READOUT_KEY]
    every = torch.ones(streams.input_ids.shape, dtype=torch.bool)

    old = pp.receiver_inputs(model, streams, senders=senders,
                             receivers=receivers)
    new = pp.receiver_inputs(model, streams, senders=senders,
                             receivers=receivers, sender_positions=every)

    for key in receivers:
        assert torch.equal(new.outputs[key], old.outputs[key]), key
    assert torch.equal(new.logits, old.logits)


def test_none_is_the_default(model, streams):
    receivers = [pp.READOUT_KEY]
    old = pp.receiver_inputs(model, streams, senders=[EARLY_HEAD],
                             receivers=receivers)
    new = pp.receiver_inputs(model, streams, senders=[EARLY_HEAD],
                             receivers=receivers, sender_positions=None)
    assert torch.equal(new.outputs[pp.READOUT_KEY], old.outputs[pp.READOUT_KEY])


def test_an_all_false_mask_gives_zero_effect(model, streams):
    """Nothing is written corrupt, so the patch is the `senders=[]` patch,
    bit for bit, and that one already reproduces the clean Readout."""
    receivers = [("q", 1, 0), pp.READOUT_KEY]
    nowhere = torch.zeros(streams.input_ids.shape, dtype=torch.bool)

    got = two_pass(model, streams, [EARLY_HEAD, LAST_MLP], receivers,
                   sender_positions=nowhere)
    unpatched = two_pass(model, streams, [], receivers)

    assert torch.equal(got, unpatched)
    assert torch.allclose(got, streams.clean_readout, atol=1e-4)
    # ... while the same senders with no mask do move the Readout.
    moved = two_pass(model, streams, [EARLY_HEAD, LAST_MLP], receivers)
    assert not torch.allclose(moved, streams.clean_readout, atol=1e-3)


@pytest.mark.parametrize("where", ["readout", "complement"])
def test_a_last_layer_mlp_into_the_readout_matches_a_direct_replace_forward(
        model, streams, where):
    """Nothing reads the last MLP block before the final norm, so its masked
    direct effect must equal a plain clean forward with that block replaced
    at the same positions (`hooks.Replacement`), with no freeze at all."""
    mask = readout_only(streams)
    if where == "complement":
        mask = ~mask

    got = two_pass(model, streams, [LAST_MLP], [pp.READOUT_KEY],
                   sender_positions=mask)
    direct = fp32_readout(
        model, streams.input_ids, streams.attention_mask, streams.positions,
        replacements={LAST_MLP: hooks.Replacement(
            streams.corrupt_outputs[LAST_MLP], positions=mask)})

    assert torch.allclose(got, direct, atol=1e-5)
    if where == "readout":
        # The MLP block is position-wise: the Readout row is the whole effect.
        assert not torch.allclose(got, streams.clean_readout, atol=1e-3)
    else:
        assert torch.allclose(got, streams.clean_readout, atol=1e-5)


@pytest.mark.parametrize("where", ["readout", "complement"])
def test_an_early_head_into_the_readout_matches_a_frozen_replace_forward(
        model, streams, where):
    """The truth is one `capture_forward` with every other Component frozen
    clean and the head written by a `hooks.Replacement` at the same positions.
    Every reader of the head is frozen, so its direct path into the Readout
    lives on the Readout row alone and the complement is exactly no effect."""
    mask = readout_only(streams)
    if where == "complement":
        mask = ~mask

    got = two_pass(model, streams, [EARLY_HEAD], [pp.READOUT_KEY],
                   sender_positions=mask)
    frozen = {key: value for key, value in streams.clean_outputs.items()
              if key != EARLY_HEAD}
    frozen[EARLY_HEAD] = hooks.Replacement(streams.corrupt_outputs[EARLY_HEAD],
                                           positions=mask)
    direct = fp32_readout(model, streams.input_ids, streams.attention_mask,
                          streams.positions, replacements=frozen)

    assert torch.allclose(got, direct, atol=1e-5)
    if where == "readout":
        assert not torch.allclose(got, streams.clean_readout, atol=1e-4)
    else:
        assert torch.allclose(got, streams.clean_readout, atol=1e-5)


@pytest.mark.parametrize("where", ["readout", "complement"])
def test_an_early_head_into_a_k_receiver_matches_a_frozen_replace_forward(
        model, streams, where):
    """A K receiver reads every position, so here the complement carries
    signal too, and the mask decides which part of it the receiver sees."""
    receiver = ("k", 1, 0)
    mask = readout_only(streams)
    if where == "complement":
        mask = ~mask

    got = pp.receiver_inputs(model, streams, senders=[EARLY_HEAD],
                             receivers=[receiver],
                             sender_positions=mask).outputs[receiver]
    frozen = {key: value for key, value in streams.clean_outputs.items()
              if key != EARLY_HEAD}
    frozen[EARLY_HEAD] = hooks.Replacement(streams.corrupt_outputs[EARLY_HEAD],
                                           positions=mask)
    direct = hooks.capture_forward(
        model, streams.input_ids, streams.attention_mask, components=[receiver],
        replacements=frozen, positions=streams.positions).outputs[receiver]
    clean = pp.receiver_inputs(model, streams, senders=[],
                               receivers=[receiver]).outputs[receiver]

    assert torch.allclose(got, direct, atol=1e-5)
    assert not torch.allclose(got, clean, atol=1e-4)


def test_a_seq_mask_is_the_same_mask_on_every_row(model, streams):
    receivers = [("k", 1, 0), pp.READOUT_KEY]
    generator = torch.Generator().manual_seed(3)
    one_row = torch.rand(streams.input_ids.shape[1], generator=generator) > 0.5

    short = pp.receiver_inputs(model, streams, senders=[EARLY_HEAD],
                               receivers=receivers, sender_positions=one_row)
    full = pp.receiver_inputs(
        model, streams, senders=[EARLY_HEAD], receivers=receivers,
        sender_positions=one_row.expand(streams.input_ids.shape[0], -1))

    for key in receivers:
        assert torch.equal(short.outputs[key], full.outputs[key]), key


def test_a_mask_of_the_wrong_shape_is_refused(model, streams):
    bad = torch.ones((streams.input_ids.shape[0] + 1,
                      streams.input_ids.shape[1]), dtype=torch.bool)
    with pytest.raises(ValueError, match="sender_positions"):
        pp.receiver_inputs(model, streams, senders=[EARLY_HEAD],
                           receivers=[pp.READOUT_KEY], sender_positions=bad)


def test_an_index_mask_is_refused(model, streams):
    indices = torch.zeros(streams.input_ids.shape, dtype=torch.long)
    with pytest.raises(TypeError, match="sender_positions"):
        pp.receiver_inputs(model, streams, senders=[EARLY_HEAD],
                           receivers=[pp.READOUT_KEY], sender_positions=indices)
