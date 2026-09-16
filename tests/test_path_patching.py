"""
Library-seam tests for `component_analysis/path_patching.py`.

The grid and the cost estimate: which (sender, receiver) cells exist, which
query heads a K or V receiver reaches, and how many forwards a run would make.
All of it is built from the Components alone, with no model, because `--dry-run`
prints the grid size and the cost estimate on the login node where there is no
GPU. So this module runs in both environments and imports no hook.

The two passes themselves are in `tests/test_path_patching_passes.py`, which
needs nnsight 0.7.0 and is skipped where it is not installed.
"""

from __future__ import annotations

import pytest

from component_analysis import path_patching as pp
from component_analysis.components import Component

HEADS_PER_GROUP = 2

#: "use the group the index implies", so that a test can pass `kv_group=None`
#: and mean it.
IMPLIED = object()


def head(layer, index, *, kv_group=IMPLIED):
    return Component(kind="head", layer=layer, index=index,
                     kv_group=index // HEADS_PER_GROUP if kv_group is IMPLIED
                     else kv_group,
                     head_gate_active=True, active_neuron_count=4)


def mlp(layer):
    return Component(kind="mlp", layer=layer, index=0, kv_group=None,
                     head_gate_active=True, active_neuron_count=4)


# ==============================================================================
# THE GRID
# ==============================================================================

def test_the_senders_are_the_circuit_components_plus_the_embedding():
    grid = pp.build_grid([head(0, 1), mlp(1)], heads_per_group=HEADS_PER_GROUP)

    assert grid.senders == [pp.EMBED_KEY, ("head", 0, 1), ("mlp", 1, 0)]


def test_the_receivers_are_q_per_head_k_and_v_per_group_mlp_inputs_and_the_readout():
    """K and V are addressed per KV group, so two heads of one group share one.

    Heads 0 and 1 of layer 1 are group 0 here; heads 2 and 3 would be group 1.
    Three heads over two groups therefore give three Q receivers but only two
    K receivers, which is the whole point of ADR-0001's GQA note.
    """
    components = [head(1, 0), head(1, 1), head(1, 2), mlp(1)]

    grid = pp.build_grid(components, heads_per_group=HEADS_PER_GROUP)

    assert [r.key for r in grid.receivers] == [
        ("q", 1, 0), ("q", 1, 1), ("q", 1, 2),
        ("k", 1, 0), ("v", 1, 0), ("k", 1, 1), ("v", 1, 1),
        ("mlp_in", 1, 0), pp.READOUT_KEY]


def test_a_k_receiver_records_the_heads_its_group_covers():
    """A K patch reaches every query head of the group, in the circuit or not.

    Group 1 covers heads 2 and 3; only head 2 is in this circuit. Reading the
    cell as "head 2's K" would hide that head 3 moved too.
    """
    grid = pp.build_grid([head(1, 2)], heads_per_group=HEADS_PER_GROUP)

    k = next(r for r in grid.receivers if r.key == ("k", 1, 1))
    assert k.covers_heads == (2, 3)
    assert k.circuit_heads == (2,)


def test_a_q_receiver_covers_only_its_own_head():
    grid = pp.build_grid([head(1, 2)], heads_per_group=HEADS_PER_GROUP)

    q = next(r for r in grid.receivers if r.key == ("q", 1, 2))
    assert q.covers_heads == (2,) and q.circuit_heads == (2,)


def test_a_head_never_sends_into_its_own_layers_queries_keys_or_values():
    """Q, K and V are read off the residual stream *before* the layer's
    attention writes to it, so a same-layer cell would be a path that does not
    exist."""
    grid = pp.build_grid([head(1, 0), head(1, 2)], heads_per_group=HEADS_PER_GROUP)

    same_layer = [cell for cell in grid.cells
                  if cell.sender[1] == 1 and cell.receiver[0] in ("q", "k", "v")
                  and cell.receiver[1] == 1]
    assert same_layer == []


def test_attention_reaches_the_mlp_of_its_own_layer():
    """The one exception to strict upstream ordering: the MLP block reads the
    residual stream after the layer's attention has written to it."""
    grid = pp.build_grid([head(1, 0), mlp(1)], heads_per_group=HEADS_PER_GROUP)

    assert pp.Cell(("head", 1, 0), ("mlp_in", 1, 0)) in grid.cells
    # ... but the MLP block does not send into its own input.
    assert pp.Cell(("mlp", 1, 0), ("mlp_in", 1, 0)) not in grid.cells


def test_an_mlp_block_sends_into_a_later_layers_receivers_only():
    grid = pp.build_grid([mlp(0), head(1, 0), mlp(1)],
                         heads_per_group=HEADS_PER_GROUP)

    assert pp.Cell(("mlp", 0, 0), ("q", 1, 0)) in grid.cells
    assert pp.Cell(("mlp", 0, 0), ("mlp_in", 1, 0)) in grid.cells
    assert pp.Cell(("mlp", 1, 0), ("q", 1, 0)) not in grid.cells


def test_the_embedding_reaches_every_receiver_and_every_sender_reaches_the_readout():
    components = [head(0, 0), head(1, 2), mlp(1)]

    grid = pp.build_grid(components, heads_per_group=HEADS_PER_GROUP)

    embedded = [cell.receiver for cell in grid.cells if cell.sender == pp.EMBED_KEY]
    assert embedded == [r.key for r in grid.receivers]
    assert all(pp.Cell(sender, pp.READOUT_KEY) in grid.cells
               for sender in grid.senders)


def test_a_head_with_no_kv_group_is_refused_by_name():
    """Without `--num-kv-heads` a K receiver would be addressed as if the head
    index were the group index, which under GQA patches other heads."""
    with pytest.raises(ValueError, match="--num-kv-heads"):
        pp.build_grid([head(0, 1, kv_group=None)], heads_per_group=HEADS_PER_GROUP)


def test_the_grid_reports_its_own_size():
    grid = pp.build_grid([head(0, 0), head(1, 2), mlp(1)],
                         heads_per_group=HEADS_PER_GROUP)

    assert grid.size == {"senders": len(grid.senders),
                         "receivers": len(grid.receivers),
                         "cells": len(grid.cells)}


def test_a_key_is_labelled_the_same_way_everywhere():
    """One string form for JSON keys, plot labels and head-table cells."""
    assert pp.label(("head", 5, 12)) == "head.5.12"
    assert pp.label(("k", 14, 3)) == "k.14.3"
    assert pp.label(pp.EMBED_KEY) == "embed"
    assert pp.label(pp.READOUT_KEY) == "readout"


# ==============================================================================
# THE COST ESTIMATE
# ==============================================================================

def test_the_cost_estimate_counts_every_forward_the_run_would_make():
    """Two per batch for the two streams, one per sender for its patched
    forward, and one per cell to read the receiver back."""
    grid = pp.build_grid([head(0, 0), mlp(1)], heads_per_group=HEADS_PER_GROUP)

    cost = pp.cost(grid, n_batches=13, batch_size=8)

    senders_with_cells = len({cell.sender for cell in grid.cells})
    assert cost["forwards"] == 13 * (2 + senders_with_cells + len(grid.cells))
    assert cost["seconds"] == pytest.approx(
        cost["forwards"] * pp.seconds_per_forward(8))
    assert cost["minutes"] == pytest.approx(cost["seconds"] / 60)


def test_a_forward_costs_what_02b_measured_per_instance():
    """02b measured 0.1845 s per forward at batch 8 x 128 tokens on an A40,
    which is 0.0231 s per instance and already compute-bound, so the estimate
    scales with instances rather than with batches."""
    assert pp.seconds_per_forward(8) == pytest.approx(0.1848, abs=1e-3)
    assert pp.seconds_per_forward(16) == pytest.approx(2 * pp.seconds_per_forward(8))


# ==============================================================================
# PER-CELL STATISTICS
# ==============================================================================

def test_a_cell_reports_the_mean_and_the_standard_error_of_its_instances():
    """Worked by hand: mean 2, sample standard deviation 1, so the standard
    error over three instances is 1/sqrt(3)."""
    assert pp.summarize([1.0, 2.0, 3.0]) == {
        "mean": pytest.approx(2.0), "se": pytest.approx(0.5773502692, abs=1e-9),
        "n": 3, "n_excluded": 0}


def test_an_instance_the_corruption_did_not_move_is_excluded_and_counted():
    """Its effect came back non-finite because its clean-minus-corrupt gap was
    too small to divide by, and averaging it in would be a spike."""
    summary = pp.summarize([1.0, float("nan"), 3.0])

    assert summary == {"mean": pytest.approx(2.0), "se": pytest.approx(1.0),
                       "n": 2, "n_excluded": 1}


def test_a_cell_with_no_usable_instance_has_a_null_mean_not_a_nan():
    """NaN is not valid JSON, and the twin files exist to be read."""
    assert pp.summarize([float("nan")]) == {"mean": None, "se": None, "n": 0,
                                            "n_excluded": 1}
    assert pp.strongest([{"mean": None}, {"mean": -0.5}], 5) == [{"mean": -0.5}]


def test_the_strongest_cells_are_ranked_by_size_whatever_their_sign():
    """A Component that suppresses the deceptive answer is as interesting as
    one that promotes it, so the ranking is on the absolute effect."""
    cells = [{"mean": 0.2}, {"mean": -0.9}, {"mean": 0.5}]

    assert pp.strongest(cells, 2) == [{"mean": -0.9}, {"mean": 0.5}]


# ==============================================================================
# THE LOGIN NODE
# ==============================================================================

def test_this_module_imports_without_nnsight_and_without_the_hook_module():
    """`--dry-run` is a login-node mode and the login node has no nnsight 0.7.0.

    The analysis is imported when the parser is built, so that every analysis
    can register its own flags — before anyone knows whether this run wants a
    model. A fresh interpreter, because `sys.modules` is process-wide and an
    earlier test in the session may have imported nnsight already.
    """
    import os
    import subprocess
    import sys

    probe = ("import component_analysis.path_patching, sys; "
             "assert 'nnsight' not in sys.modules, 'nnsight'; "
             "assert 'component_analysis.hooks' not in sys.modules, 'hooks'")
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        capture_output=True, text=True)

    assert result.returncode == 0, result.stderr


# ==============================================================================
# THE COUNTERFACTUALS AND THE POSITION-SPECIFIC SELECTION
# ==============================================================================

def test_the_default_query_position_agrees_with_the_attention_analysis():
    """`--query-positions` belongs to ticket 03; this module may not import an
    analysis module, so it spells the default out and pins it here instead."""
    from component_analysis import attention_patterns

    assert pp.DEFAULT_QUERY_POSITION == attention_patterns.DEFAULT_QUERY_POSITION


def test_both_counterfactuals_are_run_when_the_flag_says_both():
    import argparse

    ctx = type("C", (), {"cli": argparse.Namespace(path_counterfactual=pp.BOTH)})()

    assert pp.selected_counterfactuals(ctx) == [pp.ITEM_SWAP,
                                                pp.HONEST_INSTRUCTION]


def test_a_counterfactual_the_module_does_not_know_is_refused_by_name():
    import argparse

    ctx = type("C", (), {"cli": argparse.Namespace(path_counterfactual="swap")})()

    with pytest.raises(ValueError, match="swap"):
        pp.selected_counterfactuals(ctx)


def test_the_item_swap_keeps_ticket_08s_filenames_and_the_other_pair_is_suffixed():
    """A head table and a figure from before this ticket still resolve."""
    assert pp.output_name("agnostic", pp.ITEM_SWAP, "json") == pp.AGNOSTIC_FILE
    assert pp.output_name("agnostic", pp.HONEST_INSTRUCTION, "json") == \
        "agnostic_honest_instruction.json"
    assert pp.output_name("segments", pp.ITEM_SWAP, "json") == pp.SEGMENTS_FILE


def test_only_the_cells_that_clear_the_threshold_are_selected_strongest_first():
    """By absolute effect, so a path that suppresses is selected too."""
    cells = {pp.Cell(("head", 0, 1), pp.READOUT_KEY): {"mean": -0.20},
             pp.Cell(("head", 0, 2), pp.READOUT_KEY): {"mean": 0.07},
             pp.Cell(("head", 0, 3), pp.READOUT_KEY): {"mean": 0.01},
             pp.Cell(("head", 0, 4), pp.READOUT_KEY): {"mean": None}}

    chosen = pp.selected_cells(cells, 0.05)

    assert [one.sender[2] for one in chosen] == [1, 2]


def test_a_segment_absent_from_an_instance_is_marked_rather_than_scored_zero():
    """An absent Segment patches nothing, so its effect would be exactly zero;
    counting that as data would pull the Segment's mean toward nothing."""
    from component_analysis.segmentation import Segment, Segmentation

    def one(record_id, spans):
        return Segmentation(task="sdr", record_id=record_id, n_tokens=8,
                            readout=7,
                            segments={"clause": Segment(name="clause",
                                                        spans=spans)})

    segmentations = {"a": one("a", ((2, 4),)), "b": one("b", ())}

    mask, present = pp.position_mask(segmentations, ["a", "b"], ["clause"], 8)

    assert mask[0].tolist() == [False, False, True, True, False, False, False,
                                False]
    assert present.tolist() == [True, False]


def test_an_instance_with_no_segmentation_at_all_masks_nothing():
    mask, present = pp.position_mask({}, ["a"], ["clause"], 4)

    assert not mask.any() and not present.any()
