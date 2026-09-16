"""
Library-seam tests for the two forward passes of
`component_analysis/path_patching.py`, on the 2-layer random Llama.

These are the invariants that make a cell trustworthy: patching every sender
into every receiver reproduces the corrupt run, patching none reproduces the
clean run, a K receiver reaches one KV group's heads and no others, and the
freeze that makes a direct effect direct is doing something rather than nothing.
A patching bug that survived these would be indistinguishable from a finding.

nnsight 0.7.0 only, gated exactly as `tests/test_component_hooks.py` is: the
login-node base environment carries an nnsight 0.5.12 for the parent Alignment
repo, so "nnsight imports" is not the question. The grid these tests patch over
is built in `tests/test_path_patching.py`, which needs no model.
"""

from __future__ import annotations

import os

import pytest

nnsight = pytest.importorskip("nnsight")
PINNED = "0.7.0"
if nnsight.__version__ != PINNED:
    pytest.skip(f"nnsight {nnsight.__version__} is installed, not the pinned "
                f"{PINNED}; these are 0.7.0 behaviours.",
                allow_module_level=True)

import torch                                               # noqa: E402

from component_analysis import dataloaders, hooks          # noqa: E402
from component_analysis import path_patching as pp         # noqa: E402
from tests.helpers import TINY, tiny_config                # noqa: E402
from tests.test_analyze_components_segmentation import (   # noqa: E402,F401
    sdr_run)
from tests.test_path_patching import head, mlp             # noqa: E402

SEQ = 10
BATCH = 2
TINY_HEADS_PER_GROUP = TINY["heads"] // TINY["kv_heads"]


def tiny_analysis_model(vocab_size=None):
    """The tiny model wrapped for nnsight, as `load_analysis_model` returns it.

    `vocab_size` widens the embedding for the CLI test, whose prompts are
    tokenized by `FakeWordTokenizer` over a 256-word vocabulary rather than the
    101 tokens the tiny model is otherwise built with.
    """
    from nnsight import NNsight
    from transformers import LlamaForCausalLM

    config = tiny_config(attn_implementation="sdpa")
    if vocab_size is not None:
        config.vocab_size = vocab_size
    torch.manual_seed(0)
    return NNsight(LlamaForCausalLM(config).eval())


@pytest.fixture(scope="module")
def model():
    return tiny_analysis_model()


@pytest.fixture(scope="module")
def batch():
    """One batch of the causal loader's own type, hand-built for the tiny model.

    The two streams differ at many positions including the Readout, as in
    `tests/test_component_hooks.py`: where they agree at the Readout token the
    "patch everything" invariant would hold without the embedding being a
    sender, and would therefore not test that it is one.
    """
    torch.manual_seed(1)
    clean = torch.randint(0, TINY["vocab"], (BATCH, SEQ))
    corrupt = torch.randint(0, TINY["vocab"], (BATCH, SEQ))
    mask = torch.ones_like(clean)
    mask[1, SEQ - 2:] = 0          # one padded row, so the Readout is not just -1
    readout = mask.sum(-1) - 1
    items = [{
        "instance_id": f"tiny{row}", "record": {},
        "input_ids": clean[row], "attention_mask": mask[row],
        "corrupt_input_ids": corrupt[row], "corrupt_attention_mask": mask[row],
        "target_token": 3 + row, "distractor_token": 11 + row,
        "readout": int(readout[row]), "honest": None,
    } for row in range(BATCH)]
    return next(iter(dataloaders.Batches(items, batch_size=BATCH, report={})))


@pytest.fixture(scope="module")
def whole_model_grid():
    """The grid when the circuit is every head and every MLP block."""
    components = ([head(layer, index, kv_group=index // TINY_HEADS_PER_GROUP)
                   for layer in range(TINY["layers"])
                   for index in range(TINY["heads"])]
                  + [mlp(layer) for layer in range(TINY["layers"])])
    return pp.build_grid(components, heads_per_group=TINY_HEADS_PER_GROUP)


@pytest.fixture(scope="module")
def streams(model, batch, whole_model_grid):
    return pp.capture_streams(model, batch, senders=whole_model_grid.senders)


def fp32_readout(model, input_ids, attention_mask, positions, replacements=None):
    """The independent truth: one forward, read through the fp32 Readout."""
    capture = hooks.capture_forward(model, input_ids, attention_mask,
                                    components=[pp.READOUT_KEY],
                                    replacements=replacements,
                                    positions=positions)
    rows = torch.arange(input_ids.shape[0])
    residual = capture.outputs[pp.READOUT_KEY][rows, capture.readout, :]
    return hooks.readout_logits(model, residual)


def test_the_two_keys_that_are_not_components_agree_with_the_hook_module(model):
    """This module spells `EMBED_KEY` and `READOUT_KEY` out rather than
    importing `hooks` at module scope, because `registry.py` forbids that of an
    analysis. So the two spellings are asserted equal here, where nnsight is
    installed, and cannot drift apart unnoticed."""
    assert pp.EMBED_KEY == hooks.EMBED_KEY
    assert pp.READOUT_KEY == hooks.READOUT_KEY


def test_the_whole_model_circuit_covers_every_sender_and_receiver_of_the_model(
        model, whole_model_grid):
    """The two "reproduces the other stream" invariants below only hold for the
    whole model, so this says in one assertion that the grid really is it."""
    assert set(whole_model_grid.senders) == set(hooks.all_component_keys(model))
    assert set(one.key for one in whole_model_grid.receivers) == set(
        hooks.all_receiver_keys(model))


def test_patching_every_sender_into_every_receiver_reproduces_the_corrupt_logits(
        model, batch, streams, whole_model_grid):
    receivers = [one.key for one in whole_model_grid.receivers]

    got = pp.patched_readout(model, streams, senders=whole_model_grid.senders,
                             receivers=receivers)

    assert torch.allclose(got, fp32_readout(model, batch.corrupt_input_ids,
                                            batch.corrupt_attention_mask,
                                            streams.positions), atol=1e-4)
    assert not torch.allclose(got, streams.clean_readout, atol=1e-3)


def test_patching_no_sender_at_all_reproduces_the_clean_logits(
        model, streams, whole_model_grid):
    """Every Component frozen at its clean capture and none patched: the freeze
    itself must be a no-op, or every cell would carry its error."""
    receivers = [one.key for one in whole_model_grid.receivers]

    got = pp.patched_readout(model, streams, senders=[], receivers=receivers)

    assert torch.allclose(got, streams.clean_readout, atol=1e-4)


def test_patching_a_k_receiver_reaches_that_kv_groups_heads_and_no_others(
        model, streams, whole_model_grid):
    """Under GQA a K receiver is a group, not a head. The tiny model has 4
    query heads over 2 KV heads, so group 0 serves heads 0 and 1 and a patch
    there must leave heads 2 and 3 of the same layer exactly where they were.
    """
    receiver = ("k", 1, 0)
    inside = [("head", 1, index) for index in hooks.heads_of_kv_group(model, 0)]
    outside = [("head", 1, index) for index in hooks.heads_of_kv_group(model, 1)]

    patched = pp.receiver_inputs(model, streams, senders=[pp.EMBED_KEY],
                                 receivers=[receiver])
    under = hooks.capture_forward(
        model, streams.input_ids, streams.attention_mask,
        components=inside + outside, positions=streams.positions,
        replacements={receiver: patched.outputs[receiver]})
    clean = hooks.capture_forward(model, streams.input_ids,
                                  streams.attention_mask,
                                  components=inside + outside,
                                  positions=streams.positions)

    assert hooks.heads_of_kv_group(model, 0) == [0, 1]
    for key in inside:
        assert not torch.allclose(under.outputs[key], clean.outputs[key],
                                  atol=1e-4)
    for key in outside:
        assert torch.equal(under.outputs[key], clean.outputs[key])


def test_a_last_layer_mlp_has_nothing_downstream_so_its_direct_effect_is_its_total(
        model, streams):
    """The freeze is what makes a cell a path rather than a total effect.

    The last layer's MLP block writes to the residual stream and nothing reads
    it again before the final norm, so freezing the rest of the model changes
    nothing and the two-pass patch must agree exactly with simply replacing
    that Component on a clean forward.
    """
    sender = ("mlp", TINY["layers"] - 1, 0)

    direct = pp.patched_readout(model, streams, senders=[sender],
                                receivers=[pp.READOUT_KEY])
    total = fp32_readout(model, streams.input_ids, streams.attention_mask,
                         streams.positions,
                         replacements={sender: streams.corrupt_outputs[sender]})

    assert torch.allclose(direct, total, atol=1e-5)
    assert not torch.allclose(direct, streams.clean_readout, atol=1e-3)


def test_an_earlier_senders_direct_effect_differs_from_its_total_effect(
        model, streams):
    """The other half of the same point, and the reason the freeze cannot be
    dropped: a head in the last layer already has the same layer's MLP block
    downstream of it, so its total effect includes a path this cell excludes.
    """
    for sender in (("head", TINY["layers"] - 1, 0), ("head", 0, 0)):
        direct = pp.patched_readout(model, streams, senders=[sender],
                                    receivers=[pp.READOUT_KEY])
        total = fp32_readout(model, streams.input_ids, streams.attention_mask,
                             streams.positions,
                             replacements={sender:
                                           streams.corrupt_outputs[sender]})

        assert not torch.allclose(direct, total, atol=1e-4), sender


def test_the_gap_is_the_clean_minus_corrupt_logit_difference_of_each_instance(
        model, streams, batch):
    clean = hooks.target_minus_distractor(streams.clean_readout,
                                          batch.target_token,
                                          batch.distractor_token)

    assert tuple(streams.gap.shape) == (BATCH,)
    assert torch.allclose(streams.clean_metric, clean, atol=1e-5)
    assert torch.allclose(streams.gap,
                          streams.clean_metric - streams.corrupt_metric,
                          atol=1e-6)


def test_a_cell_is_the_change_in_the_metric_over_that_instances_gap(
        model, streams, whole_model_grid):
    """The normalization the spec defines, at the seam that returns numbers.

    Patching every sender into every receiver is the whole Corruption, so its
    normalized effect is -1 on every instance by construction: the change is
    exactly minus the gap.
    """
    receivers = [one.key for one in whole_model_grid.receivers]

    logits = pp.patched_readout(model, streams, senders=whole_model_grid.senders,
                                receivers=receivers)
    effect = pp.normalized_effect(streams, logits)

    assert tuple(effect.shape) == (BATCH,)
    assert torch.allclose(effect, torch.full((BATCH,), -1.0), atol=1e-3)


# ==============================================================================
# THE CLI SEAM
# ==============================================================================

def test_a_cli_run_writes_the_json_the_figures_and_the_head_table_columns(
        sdr_run, monkeypatch, tmp_path):
    """The whole analysis through the real CLI, on the tiny model.

    The circuit is heads 0 and 2 of layer 0 and the MLP block of layer 1, so
    the grid is 4 senders by 8 receivers and 13 cells survive upstream
    ordering. What the researcher gets is what is asserted: one JSON per
    figure, two PNGs, and three columns per Component in the head table.
    """
    import analyze_components
    from component_analysis import registry
    from tests.fakes import FAKE_VOCAB_SIZE
    from tests.test_analyze_components_segmentation import CELL, read_json

    run_dir, out, _records = sdr_run
    monkeypatch.setattr(registry, "ANALYSES", [pp])
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: tiny_analysis_model(FAKE_VOCAB_SIZE))

    assert analyze_components.main([
        str(run_dir), "--num-kv-heads", "2", "--n-causal", "16",
        "--device", "cpu", "--output-dir", str(out)]) == 0

    written = read_json(out, *CELL, pp.SUBDIR, pp.AGNOSTIC_FILE)
    assert written["grid"] == {"senders": 4, "receivers": 8, "cells": 13}
    assert len(written["cells"]) == 13
    assert written["sample"]["n_instances"] == 16
    assert len(written["direct_effect_on_readout"]) == 4
    assert written["cells_without_a_mean"] == []
    for name in (pp.HEATMAP_PNG, pp.DIRECT_EFFECT_PNG, pp.HEATMAP_JSON,
                 pp.DIRECT_EFFECT_JSON):
        assert os.path.getsize(
            os.path.join(str(out), *CELL, pp.SUBDIR, name)) > 0

    with open(os.path.join(str(out), *CELL, pp.SUBDIR, pp.AGNOSTIC_FILE)) as f:
        assert "NaN" not in f.read(), "the JSON twin must be strict JSON"

    table = read_json(out, *CELL, "head_table.json")
    for column in ("strongest_incoming", "strongest_outgoing", "direct_effect"):
        assert f"{pp.NAME}.{column}" in table["columns"]
    assert all(row[f"{pp.NAME}.direct_effect"] is not None
               for row in table["rows"])


def test_the_heatmap_twin_has_a_value_for_every_cell_and_null_for_every_non_path(
        sdr_run, monkeypatch):
    """The JSON twin is what an agent with no GUI reads, so it must be complete."""
    import analyze_components
    from component_analysis import registry
    from tests.fakes import FAKE_VOCAB_SIZE
    from tests.test_analyze_components_segmentation import CELL, read_json

    run_dir, out, _records = sdr_run
    monkeypatch.setattr(registry, "ANALYSES", [pp])
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: tiny_analysis_model(FAKE_VOCAB_SIZE))
    analyze_components.main([str(run_dir), "--num-kv-heads", "2", "--n-causal",
                             "16", "--device", "cpu", "--output-dir", str(out)])

    twin = read_json(out, *CELL, pp.SUBDIR, pp.HEATMAP_JSON)

    assert len(twin["rows"]) == 4 and len(twin["columns"]) == 8
    filled = sum(1 for row in twin["values"] for one in row if one is not None)
    assert filled == 13
    assert [one["kind"] for one in twin["columns"]] == [
        "q", "q", "k", "k", "v", "v", "mlp_in", "readout"]
