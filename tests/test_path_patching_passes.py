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

import json
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
    normalized effect is +1 on every instance by construction: the clean
    metric minus the patched one is exactly the gap. Positive means the path
    carries the clean prompt's signal, the sign knockout's drop has.
    """
    receivers = [one.key for one in whole_model_grid.receivers]

    logits = pp.patched_readout(model, streams, senders=whole_model_grid.senders,
                                receivers=receivers)
    effect = pp.normalized_effect(streams, logits)

    assert tuple(effect.shape) == (BATCH,)
    assert torch.allclose(effect, torch.full((BATCH,), 1.0), atol=1e-3)


def batch_with_answers(batch, target, distractor):
    """The fixture's batch with the Target and Distractor of each row replaced."""
    items = [{
        "instance_id": batch.ids[row], "record": {},
        "input_ids": batch.input_ids[row],
        "attention_mask": batch.attention_mask[row],
        "corrupt_input_ids": batch.corrupt_input_ids[row],
        "corrupt_attention_mask": batch.corrupt_attention_mask[row],
        "target_token": int(target[row]),
        "distractor_token": int(distractor[row]),
        "readout": int(batch.readout[row]), "honest": None,
    } for row in range(len(batch.ids))]
    return next(iter(dataloaders.Batches(items, batch_size=len(items),
                                         report={})))


def test_a_path_that_helps_the_target_gives_a_positive_cell(model, batch):
    """The sign convention, on the one sender whose direct effect is its total.

    The last layer's MLP block has nothing downstream of it, so its cell into
    the Readout is what knocking it out by interchange does. The Target and
    Distractor of each instance are chosen so that the block's clean output
    favours the Target over its corrupt output, and so that the Corruption
    moves the answer away from the Target (a positive gap), which is the shape
    of every real instance. Knockout calls that block helpful with a positive
    drop; the cell must say the same, and be that drop over the gap.
    """
    sender = ("mlp", TINY["layers"] - 1, 0)
    first = pp.capture_streams(model, batch, senders=[sender])
    knocked = fp32_readout(model, first.input_ids, first.attention_mask,
                           first.positions,
                           replacements={sender: first.corrupt_outputs[sender]})
    helps = first.clean_readout - knocked           # [batch, vocab]
    swap = first.clean_readout - first.corrupt_readout
    target, distractor = [], []
    for row in range(BATCH):
        both = torch.minimum(helps[row][:, None] - helps[row][None, :],
                             swap[row][:, None] - swap[row][None, :])
        best = int(torch.argmax(both))
        target.append(best // both.shape[1])
        distractor.append(best % both.shape[1])
        assert float(both.flatten()[best]) > 0.05, "no such pair in the vocab"

    streams = pp.capture_streams(model, batch_with_answers(batch, target,
                                                           distractor),
                                 senders=[sender])
    effect = pp.normalized_effect(
        streams, pp.patched_readout(model, streams, senders=[sender],
                                    receivers=[pp.READOUT_KEY]))
    knocked_metric = hooks.target_minus_distractor(
        knocked, streams.target, streams.distractor)
    drop = streams.clean_metric - knocked_metric

    assert bool((streams.gap > 0).all())
    assert bool((drop > 0).all())
    assert bool((effect > 0).all()), effect
    assert torch.allclose(effect, drop / streams.gap, atol=1e-4)


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
    for column in ("strongest_incoming", "strongest_outgoing", "direct_support"):
        assert f"{pp.NAME}.{column}" in table["columns"]
    assert all(row[f"{pp.NAME}.direct_support"] is not None
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


# ==============================================================================
# THE HONEST-INSTRUCTION COUNTERFACTUAL
# ==============================================================================

def honest_batch(paired_rows):
    """A causal batch whose `paired_rows` carry an Honest-Instruction pair.

    The honest prompt is a third random token sequence over the same mask, so
    it is aligned token for token with the pressure prompt and ends at the same
    Readout — which is all the patching code asks of it. The clause span is a
    slice in the middle, standing in for the Pressure Clause.
    """
    torch.manual_seed(2)
    clean = torch.randint(0, TINY["vocab"], (BATCH, SEQ))
    corrupt = torch.randint(0, TINY["vocab"], (BATCH, SEQ))
    instructed = torch.randint(0, TINY["vocab"], (BATCH, SEQ))
    mask = torch.ones_like(clean)
    mask[1, SEQ - 2:] = 0
    readout = mask.sum(-1) - 1
    items = []
    for row in range(BATCH):
        pair = None
        if row in paired_rows:
            pair = {"input_ids": instructed[row], "attention_mask": mask[row],
                    "clause_span": [2, 5], "instruction": "Be honest."}
        items.append({
            "instance_id": f"tiny{row}", "record": {},
            "input_ids": clean[row], "attention_mask": mask[row],
            "corrupt_input_ids": corrupt[row], "corrupt_attention_mask": mask[row],
            "target_token": 3 + row, "distractor_token": 11 + row,
            "readout": int(readout[row]), "honest": pair})
    batch = next(iter(dataloaders.Batches(items, batch_size=BATCH, report={})))
    return batch, instructed, mask


def test_the_honest_counterfactual_reproduces_the_honest_logits_through_the_same_function(
        model, whole_model_grid):
    """User story 24: both counterfactuals go through one code path.

    The same invariant the item-swap pair is held to — patch every sender into
    every receiver and the clean run becomes the counterfactual run — asserted
    on the Honest-Instruction Counterfactual, through `capture_streams` and
    `patched_readout` with no second implementation underneath.
    """
    batch, instructed, mask = honest_batch({0, 1})
    receivers = [one.key for one in whole_model_grid.receivers]

    streams = pp.capture_streams(model, batch, senders=whole_model_grid.senders,
                                 counterfactual=pp.HONEST_INSTRUCTION)
    got = pp.patched_readout(model, streams, senders=whole_model_grid.senders,
                             receivers=receivers)

    assert streams.counterfactual == pp.HONEST_INSTRUCTION
    assert torch.allclose(got, fp32_readout(model, instructed, mask,
                                            streams.positions), atol=1e-4)
    assert not torch.allclose(got, streams.clean_readout, atol=1e-3)


def test_the_honest_counterfactual_covers_only_the_rows_that_have_a_pair(
        model, whole_model_grid):
    """An instance with no Matched Honest survivor is left out, not filled in.

    Most of a split has no counterpart, and a filler row would be averaged into
    every cell as a null effect.
    """
    batch, _instructed, _mask = honest_batch({1})

    streams = pp.capture_streams(model, batch, senders=whole_model_grid.senders,
                                 counterfactual=pp.HONEST_INSTRUCTION)

    assert list(streams.ids) == ["tiny1"]
    assert streams.input_ids.shape[0] == 1
    assert tuple(streams.gap.shape) == (1,)


def test_a_batch_with_no_honest_pair_at_all_yields_no_streams(
        model, batch, whole_model_grid):
    """`batch` is the item-swap fixture, whose rows have no counterpart."""
    assert pp.capture_streams(model, batch, senders=whole_model_grid.senders,
                              counterfactual=pp.HONEST_INSTRUCTION) is None


def test_the_item_swap_counterfactual_is_the_default_and_names_itself(
        model, streams):
    assert streams.counterfactual == pp.ITEM_SWAP


class StubContext:
    """The smallest `registry.AnalysisContext` an analysis pass really uses.

    `agnostic_pass` is called with the real CLI context on a GPU; here it is
    called with a stub so that the Honest-Instruction Counterfactual can be
    driven end to end on the tiny model. The CLI seam has no Matched Honest
    pool to build from (`tests/test_dla_model.py` has the same limitation), so
    this is where the honest pass's written output is asserted.
    """

    def __init__(self, model, cell_dir, batches):
        import argparse
        self.model = model
        self.cell_dir = str(cell_dir)
        self.cli = argparse.Namespace(path_top=5, path_counterfactual=pp.BOTH)
        self.circuit_spec = type("S", (), {"label": "tiny"})()
        self.task_spec = type("T", (), {"name": "sdr"})()
        self._batches = batches
        self.segmentations = None

    def causal_batches(self):
        return self._batches

    def subdir(self, analysis):
        name = analysis if isinstance(analysis, str) else analysis.SUBDIR
        path = os.path.join(self.cell_dir, name)
        os.makedirs(path, exist_ok=True)
        return path

    def write_json(self, analysis, filename, payload):
        import json
        path = os.path.join(self.subdir(analysis), filename)
        with open(path, "w") as handle:
            json.dump(payload, handle, indent=2)
        return path


def honest_batches(paired_rows):
    """A one-batch `Batches` whose `paired_rows` carry an honest pair."""
    batch, _instructed, _mask = honest_batch(paired_rows)
    items = [{"instance_id": batch.ids[row], "record": {},
              "input_ids": batch.input_ids[row],
              "attention_mask": batch.attention_mask[row],
              "corrupt_input_ids": batch.corrupt_input_ids[row],
              "corrupt_attention_mask": batch.corrupt_attention_mask[row],
              "target_token": int(batch.target_token[row]),
              "distractor_token": int(batch.distractor_token[row]),
              "readout": int(batch.readout[row]),
              "honest": None if batch.honest is None
                        or row not in set(batch.honest.rows)
                        else {"input_ids": batch.honest.input_ids[
                                  list(batch.honest.rows).index(row)],
                              "attention_mask": batch.honest.attention_mask[
                                  list(batch.honest.rows).index(row)],
                              "clause_span": [2, 5],
                              "instruction": "Be honest."}}
             for row in range(BATCH)]
    return dataloaders.Batches(items, batch_size=BATCH,
                               report={"batch_size": BATCH})


def test_the_honest_pass_writes_its_own_file_and_names_the_counterfactual(
        model, whole_model_grid, tmp_path):
    """Two counterfactuals, two files: the item-swap one keeps ticket 08's name
    and the honest one is written beside it, never over it."""
    ctx = StubContext(model, tmp_path, honest_batches({0, 1}))

    summaries, tally = pp.agnostic_pass(ctx, whole_model_grid, ctx.causal_batches(),
                                        pp.HONEST_INSTRUCTION)

    assert summaries is not None
    written = json.loads(open(os.path.join(str(tmp_path), pp.SUBDIR,
                                           pp.output_name(pp.AGNOSTIC_STEM, pp.HONEST_INSTRUCTION, "json"))).read())
    assert written["counterfactual"] == pp.HONEST_INSTRUCTION
    assert written["metric"]["counterfactual"] == pp.HONEST_INSTRUCTION
    assert written["metric"]["convention"] == pp.CONVENTION
    assert written["metric"]["sign"].startswith("positive")
    assert written["sample"]["n_instances"] == BATCH
    assert len(written["cells"]) == len(whole_model_grid.cells)
    assert not os.path.exists(os.path.join(str(tmp_path), pp.SUBDIR,
                                           pp.AGNOSTIC_FILE))
    assert list(tally.used_ids) == ["tiny0", "tiny1"]


def test_the_honest_pass_reports_the_instances_that_have_no_counterpart(
        model, whole_model_grid, tmp_path):
    """An instance with no Matched Honest survivor is named in the file, so a
    smaller n is explained rather than noticed."""
    ctx = StubContext(model, tmp_path, honest_batches({1}))

    pp.agnostic_pass(ctx, whole_model_grid, ctx.causal_batches(),
                     pp.HONEST_INSTRUCTION)

    written = json.loads(open(os.path.join(str(tmp_path), pp.SUBDIR,
                                           pp.output_name(pp.AGNOSTIC_STEM, pp.HONEST_INSTRUCTION, "json"))).read())
    assert written["sample"]["n_instances"] == 1
    assert written["sample"]["without_a_counterpart"] == ["tiny0"]


def test_a_counterfactual_with_no_instance_at_all_writes_a_skipped_file(
        model, whole_model_grid, tmp_path):
    ctx = StubContext(model, tmp_path, honest_batches(set()))

    summaries, _tally = pp.agnostic_pass(ctx, whole_model_grid,
                                         ctx.causal_batches(),
                                         pp.HONEST_INSTRUCTION)

    assert summaries is None
    written = json.loads(open(os.path.join(str(tmp_path), pp.SUBDIR,
                                           pp.output_name(pp.AGNOSTIC_STEM, pp.HONEST_INSTRUCTION, "json"))).read())
    assert pp.HONEST_INSTRUCTION in written["skipped"]
    assert written["without_a_counterpart"] == ["tiny0", "tiny1"]


def test_both_counterfactuals_give_the_head_table_one_column_set_each(
        sdr_run, monkeypatch):
    """The CLI seam for `--path-counterfactual both`.

    This fixture's dataset has no Matched Honest survivors file, so the honest
    pass is skipped — and the columns still appear, empty, because a missing
    column reads as an analysis that was never asked for.
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
        "--path-counterfactual", "both", "--device", "cpu",
        "--output-dir", str(out)]) == 0

    swap = read_json(out, *CELL, pp.SUBDIR, pp.AGNOSTIC_FILE)
    honest = read_json(out, *CELL, pp.SUBDIR, pp.output_name(pp.AGNOSTIC_STEM, pp.HONEST_INSTRUCTION, "json"))
    assert swap["counterfactual"] == pp.ITEM_SWAP
    assert pp.HONEST_INSTRUCTION in honest["skipped"]

    table = read_json(out, *CELL, "head_table.json")
    assert f"{pp.NAME}.direct_support" in table["columns"]
    assert f"{pp.NAME}.direct_support_honest_instruction_paired" in table["columns"]
    assert f"{pp.NAME}.direct_support_honest_instruction_paired_se" in \
        table["columns"]
    assert not any("direct_effect" in one for one in table["columns"])
    assert all(row[f"{pp.NAME}.direct_support"] is not None
               for row in table["rows"])
    assert all(row[f"{pp.NAME}.direct_support_honest_instruction_paired"] is None
               for row in table["rows"])

    # The coverage, per column, in the table's meta (ticket 13): the item swap
    # over the sample it ran on, the skipped honest pass over nothing.
    from component_analysis.head_table import coverage_of

    meta = table["meta"]
    for name in pp.COLUMN_NAMES:
        swap_entry = coverage_of(meta, f"{pp.NAME}.{name}")
        assert swap_entry["n"] == len(swap["sample"]["instance_ids"])
        assert swap_entry["instance_set"].startswith("causal_sample")
        honest_entry = coverage_of(
            meta, f"{pp.NAME}.{pp.column_name(name, pp.HONEST_INSTRUCTION)}")
        assert honest_entry["n"] == 0 and honest_entry["instance_set"] is None


# ==============================================================================
# THE POSITION-SPECIFIC PASS, BY SEGMENT
# ==============================================================================

def tiny_segmentations(ids, n_tokens=SEQ, readout=None):
    """Three Segments partitioning a tiny prompt, one Segmentation per id.

    The real segmenter needs a real prompt; what the position-specific pass
    needs of it is only the token spans, so these are written directly. The
    three Segments partition the prompt, which is what makes the union check
    below a statement about the whole pass rather than about three spans.
    """
    from component_analysis.segmentation import Segment, Segmentation

    spans = {"head_span": ((0, 3),), "middle_span": ((3, 6),),
             "tail_span": ((6, n_tokens),)}
    return [Segmentation(task="sdr", record_id=one, n_tokens=n_tokens,
                         readout=n_tokens - 1 if readout is None else readout,
                         segments={name: Segment(name=name, spans=span)
                                   for name, span in spans.items()})
            for one in ids]


def test_patching_every_segment_at_once_is_the_position_agnostic_cell(
        model, streams, whole_model_grid):
    """The invariant that makes the second pass a decomposition of the first.

    The Segments partition the prompt, so writing the receiver's patched input
    at the union of them must reproduce the cell the position-agnostic pass
    measured. If it did not, a Segment row and its own total would be measuring
    two different things.
    """
    sender, receiver = ("head", 0, 0), ("k", 1, 0)
    union = torch.zeros((len(streams.ids), SEQ), dtype=torch.bool)
    union[:, :] = True

    effects = pp.positioned_effects(model, streams, sender, receiver,
                                    [("agnostic", None), ("union", union)])

    assert torch.allclose(effects["agnostic"], effects["union"], atol=1e-5)


def test_one_segment_is_not_the_whole_cell_so_the_split_says_something(
        model, streams):
    """The other half: a single Segment must differ from the union, or the
    position-specific pass would be an expensive way to repeat the first one."""
    sender, receiver = ("head", 0, 0), ("k", 1, 0)
    middle = torch.zeros((len(streams.ids), SEQ), dtype=torch.bool)
    middle[:, 3:6] = True

    effects = pp.positioned_effects(model, streams, sender, receiver,
                                    [("agnostic", None), ("middle", middle)])

    assert not torch.allclose(effects["agnostic"], effects["middle"], atol=1e-4)


def test_the_segment_pass_writes_the_selected_cells_and_the_union_check(
        sdr_run, monkeypatch):
    """The CLI seam for the position-specific pass.

    A threshold of zero selects every cell that has a mean, which on this tiny
    circuit is all thirteen, so the file shows both receiver kinds: the K and V
    cells swept by Segment and the Q, MLP and Readout cells taking one patch at
    the query positions.
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
        "--path-position-threshold", "0", "--device", "cpu",
        "--output-dir", str(out)]) == 0

    written = read_json(out, *CELL, pp.SUBDIR, pp.SEGMENTS_FILE)
    assert written["pass"] == "position_specific"
    assert written["threshold"] == 0.0
    assert written["n_selected"] == 13
    assert written["query_positions"] == ["readout"]
    assert os.path.getsize(os.path.join(str(out), *CELL, pp.SUBDIR,
                                        pp.SEGMENTS_HEATMAP_PNG)) > 0

    by_kind = {}
    for cell in written["cells"]:
        by_kind.setdefault(cell["receiver_kind"], []).append(cell)

    for cell in by_kind["k"] + by_kind["v"]:
        assert cell["union"] == pytest.approx(cell["agnostic"], abs=1e-4), \
            f"{cell['cell']}: the Segments must partition the prompt"
        assert cell["top_segment"]["segment"] in written["segments"]
        assert len(cell["by_segment"]) == len(written["segments"]) + 1

    for cell in by_kind["q"] + by_kind["readout"]:
        assert list(cell["by_segment"]) == [pp.QUERY_ENTRY]
        assert cell["union"] is None


def test_the_segment_pass_selects_nothing_when_no_cell_clears_the_threshold(
        sdr_run, monkeypatch):
    """The default is five percent of the gap, and a tiny random circuit moves
    nothing near that far; the file is still written, saying so."""
    import analyze_components
    from component_analysis import registry
    from tests.fakes import FAKE_VOCAB_SIZE
    from tests.test_analyze_components_segmentation import CELL, read_json

    run_dir, out, _records = sdr_run
    monkeypatch.setattr(registry, "ANALYSES", [pp])
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: tiny_analysis_model(FAKE_VOCAB_SIZE))
    analyze_components.main([
        str(run_dir), "--num-kv-heads", "2", "--n-causal", "16",
        "--path-position-threshold", "1e9", "--device", "cpu",
        "--output-dir", str(out)])

    written = read_json(out, *CELL, pp.SUBDIR, pp.SEGMENTS_FILE)
    assert written["n_selected"] == 0 and written["cells"] == []


# ==============================================================================
# THE COMPLETENESS SWEEP
# ==============================================================================

def test_the_sweep_shortcut_is_the_same_number_as_the_two_pass_direct_effect(
        model, streams):
    """The sweep is one forward per sender, not two, and this says why it may be.

    A replacement at the Readout receiver is written into the final norm's
    input and then read straight back out; nothing between them can change it.
    So pass 2 rewrites exactly the value pass 1 already read, and the two-pass
    direct effect is the one-pass one. The sweep patches every head and MLP
    block of the model, so halving its cost is the difference between fitting
    the short-job budget and not.
    """
    for sender in (("head", 0, 1), ("mlp", 0, 0), ("head", 1, 3)):
        two_pass = pp.patched_readout(model, streams, senders=[sender],
                                      receivers=[pp.READOUT_KEY])

        assert torch.equal(pp.sweep_readout(model, streams, sender),
                           two_pass), sender


def test_the_sweep_ranks_every_component_of_the_model_and_marks_membership(
        sdr_run, monkeypatch):
    """The CLI seam for `--path-completeness-sweep`.

    The tiny model has 2 layers of 4 heads plus 2 MLP blocks, and the fixture's
    circuit is three of those, so the sweep must score eleven senders (the
    embedding included) and mark three of them as circuit members.
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
        "--path-completeness-sweep", "--path-position-threshold", "1e9",
        "--device", "cpu", "--output-dir", str(out)]) == 0

    written = read_json(out, *CELL, pp.SUBDIR, pp.SWEEP_FILE)
    assert written["pass"] == "completeness_sweep"
    assert written["counterfactual"] == pp.ITEM_SWAP
    assert written["n_senders"] == 11 and written["n_in_circuit"] == 3
    assert written["receiver"] == "readout"
    assert [one["rank"] for one in written["senders"]] == list(range(1, 12))
    assert written["flagged"] == []          # nothing clears a threshold of 1e9
    assert os.path.getsize(os.path.join(str(out), *CELL, pp.SUBDIR,
                                        pp.SWEEP_BARS_PNG)) > 0

    table = read_json(out, *CELL, "head_table.json")
    assert len(table["rows"]) == 3, \
        "no Component outside the circuit cleared the threshold, so no row is " \
        "appended"
    assert all(row[f"{pp.NAME}.sweep_in_circuit"] for row in table["rows"])


def test_a_strong_component_outside_the_circuit_gets_a_row_of_its_own(
        sdr_run, monkeypatch):
    """What the sweep is for: a Component the pruning missed becomes visible.

    With the threshold at zero every Component clears it, so all ten of the
    tiny model's Components land in the head table and the seven outside the
    circuit are flagged.
    """
    import analyze_components
    from component_analysis import registry
    from tests.fakes import FAKE_VOCAB_SIZE
    from tests.test_analyze_components_segmentation import CELL, read_json

    run_dir, out, _records = sdr_run
    monkeypatch.setattr(registry, "ANALYSES", [pp])
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: tiny_analysis_model(FAKE_VOCAB_SIZE))
    analyze_components.main([
        str(run_dir), "--num-kv-heads", "2", "--n-causal", "16",
        "--path-completeness-sweep", "--path-position-threshold", "0",
        "--device", "cpu", "--output-dir", str(out)])

    table = read_json(out, *CELL, "head_table.json")
    flagged = [row for row in table["rows"] if row[f"{pp.NAME}.sweep_flagged"]]

    assert len(table["rows"]) == 10
    assert len(flagged) == 7
    assert all(not row[f"{pp.NAME}.sweep_in_circuit"] for row in flagged)
    assert all(row[f"{pp.NAME}.sweep_rank"] is not None for row in table["rows"])

    from component_analysis.head_table import coverage_of

    sweep = read_json(out, *CELL, pp.SUBDIR, pp.SWEEP_FILE)
    entry = coverage_of(table["meta"], f"{pp.NAME}.sweep_direct_support")
    assert entry["n"] == sweep["sample"]["n_instances"] > 0
    assert set(entry["instance_ids"]) == set(sweep["sample"]["instance_ids"])


def test_the_sweep_runs_on_the_grids_own_sample_and_its_coverage_says_so(
        sdr_run, monkeypatch):
    """One draw for the whole analysis: the global `--n-causal`/`--seed`
    sample. The sweep's instances are the grid's, its head-table columns point
    at the same instance set in the coverage meta, and on a circuit Component
    its direct support is the grid's own Readout cell."""
    import analyze_components
    from component_analysis import registry
    from component_analysis.head_table import coverage_of
    from tests.fakes import FAKE_VOCAB_SIZE
    from tests.test_analyze_components_segmentation import CELL, read_json

    run_dir, out, _records = sdr_run
    monkeypatch.setattr(registry, "ANALYSES", [pp])
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: tiny_analysis_model(FAKE_VOCAB_SIZE))
    assert analyze_components.main([
        str(run_dir), "--num-kv-heads", "2", "--n-causal", "16",
        "--path-completeness-sweep", "--path-position-threshold", "1e9",
        "--device", "cpu", "--output-dir", str(out)]) == 0

    grid = read_json(out, *CELL, pp.SUBDIR, pp.AGNOSTIC_FILE)
    sweep = read_json(out, *CELL, pp.SUBDIR, pp.SWEEP_FILE)
    sample = read_json(out, *CELL, "sample.json")
    assert sweep["sample"]["instance_ids"] == grid["sample"]["instance_ids"]
    assert len(sweep["sample"]["instance_ids"]) == 16
    assert sweep["sample"]["same_as_grid"] is True
    assert set(sweep["sample"]["instance_ids"]) == set(
        sample["instance_ids"] if "instance_ids" in sample
        else [one["instance_id"] for one in sample["instances"]])

    table = read_json(out, *CELL, "head_table.json")
    grid_entry = coverage_of(table["meta"], f"{pp.NAME}.direct_support")
    sweep_entry = coverage_of(table["meta"], f"{pp.NAME}.sweep_direct_support")
    assert grid_entry["instance_set"] == sweep_entry["instance_set"]
    assert grid_entry["n"] == sweep_entry["n"] == 16
    for row in table["rows"]:
        assert row[f"{pp.NAME}.sweep_direct_support"] == \
            row[f"{pp.NAME}.direct_support"]


def test_an_instance_the_gap_excludes_is_excluded_from_the_sweep_as_from_the_grid(
        model, whole_model_grid, tmp_path):
    """An instance whose Corruption does not move the answer is left out of
    every cell's mean, so the sweep's columns must not claim to cover it
    while the grid's say they do not."""
    torch.manual_seed(1)
    clean = torch.randint(0, TINY["vocab"], (BATCH, SEQ))
    corrupt = clean.clone()
    corrupt[0] = torch.randint(0, TINY["vocab"], (SEQ,))   # row 1 never moves
    mask = torch.ones_like(clean)
    items = [{"instance_id": f"tiny{row}", "record": {},
              "input_ids": clean[row], "attention_mask": mask[row],
              "corrupt_input_ids": corrupt[row],
              "corrupt_attention_mask": mask[row],
              "target_token": 3 + row, "distractor_token": 11 + row,
              "readout": SEQ - 1, "honest": None} for row in range(BATCH)]
    batches = dataloaders.Batches(items, batch_size=BATCH,
                                  report={"batch_size": BATCH})
    ctx = StubContext(model, tmp_path, batches)
    ctx.components = []

    _summaries, tally = pp.agnostic_pass(ctx, whole_model_grid, batches,
                                         pp.ITEM_SWAP)
    sweep = pp.completeness_sweep(ctx, whole_model_grid, batches, pp.ITEM_SWAP,
                                  grid_ids=tally.used_ids)

    assert tally.excluded == ["tiny1"]
    assert sweep["sample"]["excluded_by_gap"] == ["tiny1"]
    assert pp.sweep_measured_ids(sweep) == pp.measured_ids(tally) == ["tiny0"]
