"""
Path patching under the Neutral-Clause Twin (ticket 02b, spec R1, R16).

The twin is the v2 tasks' paired counterfactual: the same instance with its
Pressure Clause replaced by a token-matched neutral sentence, D's labels kept.
Through the same `counterfactual_pair` / `capture_streams` seam as the item
swap and the Matched Honest Instruction (user story 24), with its own column
suffix `_neutral_twin_paired`, its own files `*_neutral_twin.json`, and the
causal sample's paired-twin instance set in the coverage meta.

The pure tests run everywhere; the model tests need nnsight 0.7.0 and skip
otherwise, as `tests/test_attention_patterns.py` gates them.
"""

from __future__ import annotations

import argparse
import types
import json
import os

import pytest
import torch

from component_analysis import dataloaders
from component_analysis import path_patching as pp
from component_analysis.head_table import CAUSAL_SAMPLE_NEUTRAL_TWIN
from component_analysis.segmentation import Segment, Segmentation
from tests.helpers import TINY, tiny_config

SEQ = 12
BATCH = 3
CLAUSE = (5, 8)
HEADS_PER_GROUP = TINY["heads"] // TINY["kv_heads"]


def twin_batch(*, rows=(0, 1, 2), with_twin=True, twin_readout_shift=0):
    """A causal batch whose rows carry a Neutral-Clause Twin differing from
    the clean prompt inside `CLAUSE` only (hand-built, as the knockout model
    tests build theirs)."""
    torch.manual_seed(2)
    clean = torch.randint(2, TINY["vocab"], (BATCH, SEQ))
    corrupt = clean.clone()
    corrupt[:, 3] = (clean[:, 3] + 7) % TINY["vocab"]
    twin = clean.clone()
    twin[:, CLAUSE[0]:CLAUSE[1]] = (clean[:, CLAUSE[0]:CLAUSE[1]] + 11) % TINY["vocab"]
    mask = torch.ones_like(clean)
    mask[2, SEQ - 2:] = 0
    readout = mask.sum(-1) - 1
    pair = None
    if with_twin:
        rows = list(rows)
        twin_mask = mask[rows].clone()
        if twin_readout_shift:
            twin_mask[:, SEQ - twin_readout_shift:] = 0
        pair = dataloaders.NeutralTwinPair(
            rows=rows, input_ids=twin[rows], attention_mask=twin_mask,
            corrupt_input_ids=twin[rows].clone(), corrupt_attention_mask=twin_mask.clone(),
            clause_span=torch.tensor([list(CLAUSE)] * len(rows)))
    batch = dataloaders.Batch(
        ids=[f"tiny_{n}" for n in range(BATCH)], records=[{} for _ in range(BATCH)],
        input_ids=clean, attention_mask=mask, corrupt_input_ids=corrupt,
        corrupt_attention_mask=mask, target_token=torch.tensor([5, 6, 7]),
        distractor_token=torch.tensor([8, 9, 10]), readout=readout, honest=None,
        neutral_twin=pair)
    return batch, twin, mask


# ==============================================================================
# NAMES, SUFFIXES, SETS
# ==============================================================================

def test_the_neutral_twin_is_a_counterfactual_with_paired_columns():
    assert pp.NEUTRAL_TWIN == "neutral_twin"
    assert pp.NEUTRAL_TWIN in pp.COUNTERFACTUALS
    assert pp.COLUMN_SUFFIX[pp.NEUTRAL_TWIN] == "_neutral_twin_paired"
    assert pp.column_name("direct_support_se", pp.NEUTRAL_TWIN) == \
        "direct_support_neutral_twin_paired_se"
    assert pp.column_name("strongest_incoming", pp.NEUTRAL_TWIN) == \
        "strongest_incoming_neutral_twin_paired"
    assert pp.INSTANCE_SETS[pp.NEUTRAL_TWIN] == CAUSAL_SAMPLE_NEUTRAL_TWIN
    assert pp.output_name(pp.AGNOSTIC_STEM, pp.NEUTRAL_TWIN, "json") == \
        "agnostic_neutral_twin.json"


def test_the_v1_names_did_not_move():
    assert pp.COLUMN_SUFFIX[pp.ITEM_SWAP] == ""
    assert pp.COLUMN_SUFFIX[pp.HONEST_INSTRUCTION] == "_honest_instruction_paired"
    assert pp.COUNTERFACTUALS[:2] == (pp.ITEM_SWAP, pp.HONEST_INSTRUCTION)


def test_the_metric_block_names_the_twin():
    meta = pp.metric_meta(pp.NEUTRAL_TWIN)
    assert meta["counterfactual"] == pp.NEUTRAL_TWIN
    assert "Neutral-Clause Twin" in meta["sign"]
    assert meta["convention"] == pp.CONVENTION
    # v1's two sentences are the ones the snapshot holds.
    assert "the item swap" in pp.metric_meta(pp.ITEM_SWAP)["sign"]
    assert "Matched Honest Instruction" in pp.metric_meta(pp.HONEST_INSTRUCTION)["sign"]


# ==============================================================================
# THE PAIR
# ==============================================================================

def test_the_twin_pair_is_the_twin_prompt_on_the_rows_that_have_one():
    batch, twin, mask = twin_batch(rows=(0, 2))
    rows, input_ids, attention_mask = pp.counterfactual_pair(batch, pp.NEUTRAL_TWIN)
    assert rows == [0, 2]
    assert torch.equal(input_ids, twin[[0, 2]])
    assert torch.equal(attention_mask, mask[[0, 2]])


def test_a_batch_without_a_twin_gives_no_pair():
    batch, _twin, _mask = twin_batch(with_twin=False)
    assert pp.counterfactual_pair(batch, pp.NEUTRAL_TWIN) is None


def test_a_twin_that_ends_elsewhere_than_its_pressure_prompt_is_refused():
    batch, _twin, _mask = twin_batch(twin_readout_shift=3)
    with pytest.raises(ValueError, match="Neutral-Clause Twin"):
        pp.counterfactual_pair(batch, pp.NEUTRAL_TWIN)


# ==============================================================================
# WHICH COUNTERFACTUALS A CELL RUNS
# ==============================================================================

def ctx_for(task: str, value: str):
    return argparse.Namespace(
        cli=argparse.Namespace(path_counterfactual=value),
        task_spec=type("T", (), {"name": task})())


def test_both_on_a_v1_task_is_item_swap_and_honest_instruction_as_before():
    assert pp.selected_counterfactuals(ctx_for("sdr", pp.BOTH)) == \
        [pp.ITEM_SWAP, pp.HONEST_INSTRUCTION]


def test_both_on_a_v2_task_is_item_swap_and_the_neutral_twin():
    for task in ("far_v2", "sdr_v2", "ser_v2"):
        assert pp.selected_counterfactuals(ctx_for(task, pp.BOTH)) == \
            [pp.ITEM_SWAP, pp.NEUTRAL_TWIN]


def test_the_twin_alone_is_selectable_on_any_task():
    assert pp.selected_counterfactuals(ctx_for("sdr", pp.NEUTRAL_TWIN)) == \
        [pp.NEUTRAL_TWIN]
    assert pp.selected_counterfactuals(ctx_for("sdr_v2", pp.NEUTRAL_TWIN)) == \
        [pp.NEUTRAL_TWIN]


def test_the_flag_accepts_the_twin():
    parser = argparse.ArgumentParser()
    pp.add_arguments(parser.add_argument_group("path"))
    assert parser.parse_args(["--path-counterfactual", "neutral_twin"]
                             ).path_counterfactual == pp.NEUTRAL_TWIN


# ==============================================================================
# THROUGH THE MODEL
# ==============================================================================

def nnsight_model():
    nnsight = pytest.importorskip("nnsight")
    if nnsight.__version__ != "0.7.0":
        pytest.skip("patched forwards are a nnsight 0.7.0 behaviour")
    from nnsight import NNsight
    from transformers import LlamaForCausalLM

    torch.manual_seed(0)
    return NNsight(LlamaForCausalLM(tiny_config(attn_implementation="sdpa")).eval())


@pytest.fixture(scope="module")
def model():
    return nnsight_model()


@pytest.fixture(scope="module")
def whole_model_grid():
    from tests.test_path_patching import head, mlp

    components = ([head(layer, index, kv_group=index // HEADS_PER_GROUP)
                   for layer in range(TINY["layers"])
                   for index in range(TINY["heads"])]
                  + [mlp(layer) for layer in range(TINY["layers"])])
    return pp.build_grid(components, heads_per_group=HEADS_PER_GROUP)


def fp32_readout(model, input_ids, attention_mask, positions):
    from component_analysis import hooks

    capture = hooks.capture_forward(model, input_ids, attention_mask,
                                    components=[pp.READOUT_KEY],
                                    positions=positions)
    rows = torch.arange(input_ids.shape[0])
    residual = capture.outputs[pp.READOUT_KEY][rows, capture.readout, :]
    return hooks.readout_logits(model, residual)


def test_patching_every_sender_reproduces_the_twin_logits_through_the_same_function(
        model, whole_model_grid):
    """User story 24 for the third counterfactual: the invariant the item swap
    and the honest instruction are held to, on the twin, through
    `capture_streams` and `patched_readout` with nothing new underneath."""
    batch, twin, mask = twin_batch(rows=(0, 1))
    receivers = [one.key for one in whole_model_grid.receivers]

    streams = pp.capture_streams(model, batch, senders=whole_model_grid.senders,
                                 counterfactual=pp.NEUTRAL_TWIN)
    got = pp.patched_readout(model, streams, senders=whole_model_grid.senders,
                             receivers=receivers)

    assert streams.counterfactual == pp.NEUTRAL_TWIN
    assert list(streams.ids) == ["tiny_0", "tiny_1"]
    assert torch.allclose(got, fp32_readout(model, twin[[0, 1]], mask[[0, 1]],
                                            streams.positions), atol=1e-4)
    assert not torch.allclose(got, streams.clean_readout, atol=1e-3)


def test_a_batch_with_no_twin_yields_no_streams(model, whole_model_grid):
    batch, _twin, _mask = twin_batch(with_twin=False)
    assert pp.capture_streams(model, batch, senders=whole_model_grid.senders,
                              counterfactual=pp.NEUTRAL_TWIN) is None


class StubContext:
    """The smallest context the passes read, on a v2 task, with Segments."""

    def __init__(self, model, cell_dir, batches, *, task="sdr_v2",
                 counterfactual=pp.NEUTRAL_TWIN, threshold=0.0):
        self.model = model
        self.cell_dir = str(cell_dir)
        self.cli = argparse.Namespace(path_top=5, path_counterfactual=counterfactual,
                                      path_position_threshold=threshold)
        self.circuit_spec = type("S", (), {"label": "tiny"})()
        self.task_spec = type("T", (), {"name": task})()
        self._batches = batches
        self.segmentations = None
        self.declared = []

    def causal_batches(self):
        return self._batches

    def subdir(self, analysis):
        name = analysis if isinstance(analysis, str) else analysis.SUBDIR
        path = os.path.join(self.cell_dir, name)
        os.makedirs(path, exist_ok=True)
        return path

    def write_json(self, analysis, filename, payload):
        path = os.path.join(self.subdir(analysis), filename)
        with open(path, "w") as handle:
            json.dump(payload, handle, indent=2)
        return path

    def declare_coverage(self, columns, *, instance_ids, instance_set, **extra):
        self.declared.append((list(columns), list(instance_ids), instance_set))


def segmentations_of(batch):
    out = []
    for row, one in enumerate(batch.ids):
        n = int(batch.attention_mask[row].sum())
        out.append(Segmentation(
            task="sdr_v2", record_id=one, n_tokens=n, readout=n - 1, segments={
                "intro": Segment("intro", ((0, CLAUSE[0]),)),
                "pressure_clause": Segment("pressure_clause", (CLAUSE,)),
                "question": Segment("question", ((CLAUSE[1], n - 1),)),
                "readout": Segment("readout", ((n - 1, n),))}))
    return out


def twin_batches(batch):
    items = [{"instance_id": batch.ids[row], "record": {},
              "input_ids": batch.input_ids[row],
              "attention_mask": batch.attention_mask[row],
              "corrupt_input_ids": batch.corrupt_input_ids[row],
              "corrupt_attention_mask": batch.corrupt_attention_mask[row],
              "target_token": int(batch.target_token[row]),
              "distractor_token": int(batch.distractor_token[row]),
              "readout": int(batch.readout[row]), "honest": None,
              "neutral_twin": None if batch.neutral_twin is None
              or row not in batch.neutral_twin.rows else {
                  "input_ids": batch.neutral_twin.input_ids[
                      batch.neutral_twin.rows.index(row)],
                  "attention_mask": batch.neutral_twin.attention_mask[
                      batch.neutral_twin.rows.index(row)],
                  "corrupt_input_ids": batch.neutral_twin.corrupt_input_ids[
                      batch.neutral_twin.rows.index(row)],
                  "corrupt_attention_mask": batch.neutral_twin.corrupt_attention_mask[
                      batch.neutral_twin.rows.index(row)],
                  "clause_span": list(CLAUSE)}}
             for row in range(BATCH)]
    return dataloaders.Batches(items, batch_size=BATCH,
                               report={"batch_size": BATCH, "n_with_neutral_twin":
                                       sum(1 for one in items if one["neutral_twin"])})


def test_the_twin_pass_writes_its_files_columns_and_coverage(model, whole_model_grid,
                                                              tmp_path, monkeypatch):
    """`run` on a v2 context with `--path-counterfactual neutral_twin`: the
    agnostic file and the position-specific file under the twin's name, every
    column under `_neutral_twin_paired`, and the coverage declared over the
    paired-twin instance set with exactly the rows that have a twin."""
    batch, _twin, _mask = twin_batch(rows=(0, 1))
    ctx = StubContext(model, tmp_path, twin_batches(batch))
    ctx.segmentations = segmentations_of(batch)
    updates = run_on(ctx, whole_model_grid, monkeypatch)

    agnostic = json.load(open(os.path.join(
        tmp_path, pp.SUBDIR, pp.output_name(pp.AGNOSTIC_STEM, pp.NEUTRAL_TWIN, "json"))))
    assert agnostic["counterfactual"] == pp.NEUTRAL_TWIN
    assert agnostic["sample"]["instance_ids"] == ["tiny_0", "tiny_1"]
    assert agnostic["sample"]["without_a_counterpart"] == ["tiny_2"]
    assert "Neutral-Clause Twin" in agnostic["metric"]["sign"]

    segments = json.load(open(os.path.join(
        tmp_path, pp.SUBDIR, pp.output_name(pp.SEGMENTS_STEM, pp.NEUTRAL_TWIN, "json"))))
    assert segments["counterfactual"] == pp.NEUTRAL_TWIN
    assert segments["segments"] == ["intro", "pressure_clause", "question", "readout"]
    kv_cells = [one for one in segments["cells"] if one["receiver_kind"] in ("k", "v")]
    assert kv_cells, "a K or V cell must have had its Segment split"
    for one in kv_cells:
        # Every pre-clause position is identical in D and its twin, so the
        # intro row of the split is exactly zero by construction.
        assert one["by_segment"]["intro"]["mean"] == pytest.approx(0.0, abs=1e-6)
        assert one["top_segment"]["segment"] in ("pressure_clause", "question", "readout")

    some_head = ("head", 1, 0)
    assert "direct_support_neutral_twin_paired" in updates[some_head]
    assert "direct_support_neutral_twin_paired_se" in updates[some_head]
    assert "strongest_incoming_neutral_twin_paired" in updates[some_head]
    assert not [one for one in updates[some_head] if one.endswith("_honest_instruction_paired")]
    assert not any(one in updates[some_head] for one in pp.COLUMN_NAMES), \
        "no bare item-swap column: the item swap was not selected"

    declared = [one for one in ctx.declared if one[2] == CAUSAL_SAMPLE_NEUTRAL_TWIN]
    assert len(declared) == 2
    columns, ids, _set = declared[0]
    assert ids == ["tiny_0", "tiny_1"]
    assert set(columns) == {pp.column_name(one, pp.NEUTRAL_TWIN) for one in pp.COLUMN_NAMES}

    # The receiver category (spec 2.3) rides on the twin pass: its JSON, its
    # five columns on every circuit head, its coverage over the same rows.
    from component_analysis import receiver_category as rc

    category = json.load(open(os.path.join(tmp_path, pp.SUBDIR, rc.JSON_NAME)))
    assert category["floor"] == rc.FLOOR
    assert category["sample"]["instance_ids"] == ["tiny_0", "tiny_1"]
    assert sum(category["counts"].values()) == TINY["layers"] * TINY["heads"]
    assert updates[some_head][rc.COLUMN] in rc.CATEGORIES
    assert set(rc.COLUMNS) <= set(updates[some_head])
    assert rc.COLUMN not in updates[("mlp", 1, 0)]
    columns, ids, _set = declared[1]
    assert ids == ["tiny_0", "tiny_1"] and set(columns) == set(rc.COLUMNS)
    # With every cell split (threshold 0), no K/V path is unresolved unless
    # its top Segment is one the category cannot place.
    for one in category["heads"]:
        if one["category"] == "kv_unresolved":
            assert one["segment"] is None or one["segment"] == "unsegmented"


def run_on(ctx, grid, monkeypatch):
    """`pp.run` with the grid handed in: the stub has no intake to build one
    from and no HF config for the KV-group check."""
    monkeypatch.setattr(pp, "grid_for", lambda ctx: grid)
    monkeypatch.setattr(pp, "_check_kv_groups", lambda ctx, model: None)
    return pp.run(ctx)


def test_a_v2_cell_without_a_twin_writes_the_skipped_file(model, whole_model_grid,
                                                          tmp_path, monkeypatch):
    """An H or F cell of a v2 task: the loader pairs nothing, and the pass says
    so in a file rather than crashing or writing an empty grid."""
    batch, _twin, _mask = twin_batch(with_twin=False)
    ctx = StubContext(model, tmp_path, twin_batches(batch))
    ctx.segmentations = segmentations_of(batch)
    updates = run_on(ctx, whole_model_grid, monkeypatch)

    skipped = json.load(open(os.path.join(
        tmp_path, pp.SUBDIR, pp.output_name(pp.AGNOSTIC_STEM, pp.NEUTRAL_TWIN, "json"))))
    assert pp.NEUTRAL_TWIN in skipped["skipped"]
    assert skipped["without_a_counterpart"] == ["tiny_0", "tiny_1", "tiny_2"]
    assert all(value is None for value in updates[("head", 1, 0)].values())
    declared = [one for one in ctx.declared if one[2] == CAUSAL_SAMPLE_NEUTRAL_TWIN]
    assert declared and declared[0][1] == []


# ==============================================================================
# THE TWIN'S OWN POSITION THRESHOLD (R25 A)
# ==============================================================================

def test_the_twin_position_threshold_is_its_own_flag_and_defaults_to_the_shared_one():
    """Phase 3 runs the neutral-twin Segment pass at the receiver category's floor (0.01) while the
    item-swap pass keeps the default 0.05: one flag for the twin, the shared one for the rest."""
    cli = argparse.Namespace(path_position_threshold=0.05, path_twin_position_threshold=None)
    ctx = types.SimpleNamespace(cli=cli)
    assert pp.position_threshold(ctx) == 0.05
    assert pp.position_threshold(ctx, pp.ITEM_SWAP) == 0.05
    assert pp.position_threshold(ctx, pp.NEUTRAL_TWIN) == 0.05
    cli.path_twin_position_threshold = 0.01
    assert pp.position_threshold(ctx, pp.NEUTRAL_TWIN) == 0.01
    assert pp.position_threshold(ctx, pp.ITEM_SWAP) == 0.05
    assert pp.position_threshold(ctx, pp.HONEST_INSTRUCTION) == 0.05
    # A v1-shaped cli without the attribute reads the shared flag for every counterfactual.
    old = types.SimpleNamespace(cli=argparse.Namespace(path_position_threshold=0.07))
    assert pp.position_threshold(old, pp.NEUTRAL_TWIN) == 0.07


def test_the_twin_position_threshold_flag_parses_and_is_off_by_default():
    parser = argparse.ArgumentParser()
    pp.add_arguments(parser.add_argument_group("path"))
    assert parser.parse_args([]).path_twin_position_threshold is None
    assert parser.parse_args(["--path-twin-position-threshold", "0.01"]).path_twin_position_threshold == 0.01
