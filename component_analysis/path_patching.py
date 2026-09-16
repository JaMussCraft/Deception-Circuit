"""
component_analysis/path_patching.py — which Component feeds which, and how much.

Knockout says how much a Component matters. Direct logit attribution says what
it writes at the Readout. Neither says *who reads it*. Path patching does: for
one (sender, receiver) pair it asks what happens to the answer when that single
path — and only that path — carries the value it would have had under the
item-swap Corruption.

**The two passes.** One cell is two forwards over the clean prompt:

  1. the sender's output is replaced by its corrupt-stream capture, **every
     other Component is frozen at its clean capture**, and the receiver's input
     is read off that forward;
  2. a clean forward with that one receiver input written in, and the metric
     read at the Readout.

The freeze in step 1 is what makes the number a *path* effect. Without it the
sender's corrupt value would reach the receiver through every intermediate
Component as well, and the (sender, Readout) cell would be the sender's total
effect — which is per-Component knockout, measured twice. With everything else
held at clean, the receiver's input differs from its clean input by the
sender's own contribution and nothing else, so the cell is the direct path.

**The metric.** `logit(Target) - logit(Distractor)` at the Readout, read in
fp32 through `hooks.readout_logits`, as the change from the clean run divided
by that instance's clean-minus-corrupt gap:

    effect = (patched - clean) / (clean - corrupt)

So **a negative cell is a path that carries the Corruption**: -1 means patching
that one path alone moved the answer as far as corrupting the whole prompt, and
0 means the path carries nothing. Instances are normalized one by one and then
averaged, so a prompt with a wide gap does not outvote a narrow one.

**The grid.** Senders are the circuit's Components plus the token embedding.
Receivers are each circuit head's Q (per head) and K and V (per KV group, the
whole point of ADR-0001's GQA note), each circuit MLP block's input, and the
Readout. A cell exists only where the sender is strictly upstream of the
receiver, with one exception: attention writes to the residual stream before
the same layer's MLP reads it, so a head reaches its own layer's MLP input.

The grid is built from the Components alone, with no model, because `--dry-run`
prints its size and a cost estimate on the login node, where there is no GPU
and no nnsight 0.7.0.

This module implements the **position-agnostic** pass of the spec: the sender's
value is written at every position and the receiver takes it at every position.
The position-specific pass, by Segment, is ticket 09.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from component_analysis.head_table import row_key

#: The registration protocol (`component_analysis/registry.py`).
NAME = "path_patching"
SUBDIR = "path_patching"

#: The per-cell table, and the two figures with their JSON twins.
AGNOSTIC_FILE = "agnostic.json"
HEATMAP_PNG = "heatmap.png"
HEATMAP_JSON = "heatmap.json"
DIRECT_EFFECT_PNG = "direct_effect.png"
DIRECT_EFFECT_JSON = "direct_effect.json"

#: The two keys that are not Components: the start and the end of the residual
#: stream. Spelled out here rather than imported, because `registry.py` requires
#: an analysis module to import neither nnsight nor `hooks` at module scope —
#: it is imported on the login node when the parser is built. They are asserted
#: equal to the hook module's own in `tests/test_path_patching_passes.py`, so
#: the two spellings cannot drift.
EMBED_KEY = ("embed", 0, 0)
READOUT_KEY = ("readout", 0, 0)

#: Receiver kinds, in the order the heatmap groups them.
RECEIVER_KINDS = ("q", "k", "v", "mlp_in", "readout")

#: The heatmap's colour for a (sender, receiver) pair that is not a path, so
#: that "no cell" never reads as "an effect of zero".
MISSING_COLOUR = "#e8e8e8"

#: The heatmap's colour scale runs to this percentile of the absolute effects
#: rather than to the largest of them. One cell is usually an order of magnitude
#: above the rest — on SDR nls0.3 the last MLP block's direct effect is 0.094
#: against a second place of 0.019 — and a scale set by it washes the other 392
#: cells to white. Cells beyond the scale saturate, and the colour bar's arrows
#: say so; the JSON twin carries every unclipped number.
HEATMAP_PERCENTILE = 98.0

#: An instance whose clean-minus-corrupt gap is this small is not normalized by
#: it: the Corruption did not move the answer, so every cell would be a ratio of
#: two small numbers. Excluded and counted rather than returned as a spike.
MIN_GAP = 1e-3

#: Wall time per instance per forward, measured by ticket 02b on an A40 at
#: batch 8 x 128 tokens: 0.1845 s to capture and 0.1909 s to replace, which is
#: 0.0231 s per instance. At that batch an 8B model in bfloat16 is already
#: compute-bound, so the estimate scales with the instance count and a larger
#: batch buys fewer, longer forwards rather than less work. An A100 is roughly
#: twice an A40, so an estimate from these numbers is an upper bound on the
#: partition the brief prefers. Below batch 8 the linear term underestimates,
#: because the fixed tracing cost 02b did not measure separately starts to
#: dominate; no analysis run uses a batch that small.
SECONDS_PER_INSTANCE = 0.0231


# ==============================================================================
# KEYS
# ==============================================================================

def label(key) -> str:
    """One string form of a key, for JSON, plot labels and head-table cells.

    `("head", 5, 12)` is `head.5.12`; the embedding and the Readout are single
    sites and are named by their kind alone.
    """
    kind, layer, index = key
    if key == EMBED_KEY or key == READOUT_KEY:
        return kind
    return f"{kind}.{layer}.{index}"


# ==============================================================================
# THE GRID
# ==============================================================================

@dataclass(frozen=True)
class Receiver:
    """One receiver of the grid, and which query heads a patch there reaches.

    `covers_heads` is every query head the patch touches — for a K or V
    receiver that is the whole KV group, circuit member or not, which is the
    thing a reader of the cell has to know. `circuit_heads` is the subset that
    is in the circuit under study.
    """

    key: tuple
    covers_heads: tuple = ()
    circuit_heads: tuple = ()

    @property
    def kind(self) -> str:
        return self.key[0]

    @property
    def layer(self) -> int:
        return self.key[1]


@dataclass(frozen=True)
class Cell:
    """One (sender, receiver) pair of the grid."""

    sender: tuple
    receiver: tuple

    @property
    def name(self) -> str:
        return f"{label(self.sender)}->{label(self.receiver)}"


@dataclass
class Grid:
    senders: List[tuple]
    receivers: List[Receiver]
    cells: List[Cell]

    @property
    def size(self) -> dict:
        return {"senders": len(self.senders), "receivers": len(self.receivers),
                "cells": len(self.cells)}

    def cells_into(self, key) -> List[Cell]:
        return [cell for cell in self.cells if cell.receiver == key]

    def receivers_for(self, sender) -> List[tuple]:
        """The receivers this sender is upstream of, in grid order."""
        reachable = {cell.receiver for cell in self.cells if cell.sender == sender}
        return [one.key for one in self.receivers if one.key in reachable]


def _reaches(sender: tuple, receiver: tuple) -> bool:
    """Is `sender` strictly upstream of `receiver`?

    The embedding precedes everything and the Readout follows everything. In
    between, a sender at layer `s` reaches a Q, K or V receiver at layer `r`
    only when `s < r`, because those are read off the residual stream as the
    layer begins. The MLP input is read after the same layer's attention has
    written, so a head at layer `s` reaches the MLP input at layer `s` too —
    the one exception. An MLP block never reaches its own input.
    """
    if receiver == READOUT_KEY:
        return True
    if sender == EMBED_KEY:
        return True
    sender_kind, sender_layer, _index = sender
    receiver_kind, receiver_layer, _ = receiver
    if receiver_kind == "mlp_in" and sender_kind == "head":
        return sender_layer <= receiver_layer
    return sender_layer < receiver_layer


def build_grid(components, *, heads_per_group: int) -> Grid:
    """The sender-by-receiver grid of one circuit, with no model loaded.

    `components` are the circuit's Components in head-table order;
    `heads_per_group` is `num_heads // num_key_value_heads`, which decides how
    many query heads one K or V receiver reaches.
    """
    heads = [one for one in components if one.kind == "head"]
    mlps = [one for one in components if one.kind == "mlp"]

    missing = [one for one in heads if one.kv_group is None]
    if missing:
        raise ValueError(
            f"{len(missing)} circuit head(s) carry no KV group, the first being "
            f"layer {missing[0].layer} head {missing[0].index}. K and V "
            f"receivers are addressed per KV group, so without it a patch would "
            f"be applied to whichever heads share the head's index. Pass "
            f"--num-kv-heads.")

    senders = [EMBED_KEY] + [one.key for one in components]

    receivers: List[Receiver] = []
    for one in heads:
        receivers.append(Receiver(("q", one.layer, one.index),
                                  covers_heads=(one.index,),
                                  circuit_heads=(one.index,)))
    seen = set()
    for one in heads:
        if (one.layer, one.kv_group) in seen:
            continue
        seen.add((one.layer, one.kv_group))
        covers = tuple(range(one.kv_group * heads_per_group,
                             (one.kv_group + 1) * heads_per_group))
        members = tuple(other.index for other in heads
                        if other.layer == one.layer
                        and other.kv_group == one.kv_group)
        for kind in ("k", "v"):
            receivers.append(Receiver((kind, one.layer, one.kv_group),
                                      covers_heads=covers,
                                      circuit_heads=members))
    for one in mlps:
        receivers.append(Receiver(("mlp_in", one.layer, 0)))
    receivers.append(Receiver(READOUT_KEY))

    cells = [Cell(sender, one.key) for sender in senders for one in receivers
             if _reaches(sender, one.key)]
    return Grid(senders=senders, receivers=receivers, cells=cells)


# ==============================================================================
# THE COST ESTIMATE
# ==============================================================================

def seconds_per_forward(batch_size: int) -> float:
    """One forward's wall time, from ticket 02b's A40 measurement."""
    return SECONDS_PER_INSTANCE * batch_size


def cost(grid: Grid, *, n_batches: int, batch_size: int) -> dict:
    """How many forwards this grid costs, and how long they would take.

    Per batch: the clean capture and the corrupt capture, then one patched
    forward per sender that has any cell, then one forward per cell to read the
    receiver's patched input back at the Readout.
    """
    senders_with_cells = len({cell.sender for cell in grid.cells})
    forwards = n_batches * (2 + senders_with_cells + len(grid.cells))
    seconds = forwards * seconds_per_forward(batch_size)
    return {"forwards": forwards, "seconds": seconds, "minutes": seconds / 60,
            "seconds_per_forward": seconds_per_forward(batch_size),
            "n_batches": n_batches, "batch_size": batch_size,
            **grid.size}


# ==============================================================================
# THE TWO PASSES
# ==============================================================================

@dataclass
class _Tally:
    """What a run accumulates besides the cells: the instances it saw, the
    gaps it normalized by, and what it cost."""

    gaps: List[float] = field(default_factory=list)
    used_ids: List[str] = field(default_factory=list)
    excluded: List[str] = field(default_factory=list)
    forwards: int = 0
    wall_seconds: float = 0.0


@dataclass
class Streams:
    """Both streams of one batch, captured once and shared by every cell of it.

    The clean capture is the **freeze set**: every Component of the model, not
    only the circuit's, held at the value it took on the clean prompt. The
    corrupt capture holds the senders' values alone, because a sender is the
    only thing a cell ever writes from the corrupt stream.
    """

    input_ids: "torch.Tensor"
    attention_mask: "torch.Tensor"
    positions: "torch.Tensor"
    target: "torch.Tensor"
    distractor: "torch.Tensor"
    #: {key: [batch, seq, dim]} for every Component of the model, on the clean
    #: prompt. Written back at every site a cell does not patch.
    clean_outputs: Dict[tuple, "torch.Tensor"]
    #: {sender key: [batch, seq, dim]} on the corrupt prompt.
    corrupt_outputs: Dict[tuple, "torch.Tensor"]
    #: `[batch, vocab]` fp32 at the Readout, for each stream run whole.
    clean_readout: "torch.Tensor"
    corrupt_readout: "torch.Tensor"
    #: `[batch]` fp32 `logit(Target) - logit(Distractor)`, and their difference.
    clean_metric: "torch.Tensor"
    corrupt_metric: "torch.Tensor"
    gap: "torch.Tensor"
    ids: Sequence[str] = ()

    @property
    def usable(self):
        """Instances whose Corruption moved the answer far enough to divide by.

        A gap of nearly zero means the item swap did not change the answer on
        that instance, so every cell would be a ratio of two small numbers.
        """
        return self.gap.abs() >= MIN_GAP


def capture_streams(model, batch, *, senders) -> Streams:
    """The two forwards every cell of one batch is measured against.

    `batch` is a `dataloaders.Batch`: the clean and item-swap-corrupt prompts,
    the Target and Distractor token ids read with the **clean** stream's
    assignment on both runs, and the Readout position of each row.
    """
    from component_analysis import hooks

    device, _dtype = hooks.device_and_dtype(model)
    keys = [row_key(one) for one in senders]
    frozen = hooks.all_component_keys(model)

    input_ids = batch.input_ids.to(device)
    attention_mask = batch.attention_mask.to(device)
    positions = batch.readout.to(device)
    target = batch.target_token.to(device)
    distractor = batch.distractor_token.to(device)

    clean = hooks.capture_forward(model, input_ids, attention_mask,
                                  components=list(frozen) + [READOUT_KEY],
                                  positions=positions)
    corrupt = hooks.capture_forward(model, batch.corrupt_input_ids.to(device),
                                    batch.corrupt_attention_mask.to(device),
                                    components=keys + [READOUT_KEY],
                                    positions=positions)

    clean_readout = _readout_of(model, clean)
    corrupt_readout = _readout_of(model, corrupt)
    clean_metric = hooks.target_minus_distractor(clean_readout, target, distractor)
    corrupt_metric = hooks.target_minus_distractor(corrupt_readout, target,
                                                   distractor)
    return Streams(
        input_ids=input_ids, attention_mask=attention_mask, positions=positions,
        target=target, distractor=distractor,
        clean_outputs={key: clean.outputs[key] for key in frozen},
        corrupt_outputs={key: corrupt.outputs[key] for key in keys},
        clean_readout=clean_readout, corrupt_readout=corrupt_readout,
        clean_metric=clean_metric, corrupt_metric=corrupt_metric,
        gap=clean_metric - corrupt_metric, ids=tuple(getattr(batch, "ids", ())))


def _readout_of(model, capture):
    """The fp32 Readout logits of a capture that asked for `READOUT_KEY`.

    Read off the captured site rather than off `Capture.residual`, because the
    residual rows are taken from each decoder layer's output — before a
    replacement *at* the Readout receiver is written. Taking both from the same
    site is what lets the Readout be a receiver like any other.
    """
    import torch

    from component_analysis import hooks

    rows = torch.arange(capture.logits.shape[0], device=capture.readout.device)
    residual = capture.outputs[READOUT_KEY][rows, capture.readout, :]
    return hooks.readout_logits(model, residual)


def receiver_inputs(model, streams: Streams, *, senders, receivers):
    """Pass 1: what the receivers read when only `senders` carry corrupt values.

    Every other Component of the model is written back with its clean capture,
    so the sender's value reaches the receiver directly and by no other route.
    The receivers come back at every position, which is what makes this the
    position-agnostic pass.
    """
    from component_analysis import hooks

    patched = {row_key(one) for one in senders}
    replacements = {key: value for key, value in streams.clean_outputs.items()
                    if key not in patched}
    replacements.update({key: streams.corrupt_outputs[key] for key in patched})
    return hooks.capture_forward(model, streams.input_ids,
                                 streams.attention_mask,
                                 components=[row_key(one) for one in receivers],
                                 replacements=replacements,
                                 positions=streams.positions)


def readout_from_receivers(model, streams: Streams, replacements):
    """Pass 2: a clean forward with those receiver inputs written in.

    Nothing else in the forward is touched, so whatever the patched receiver
    does with its new input propagates exactly as the model would do it.
    """
    from component_analysis import hooks

    capture = hooks.capture_forward(model, streams.input_ids,
                                    streams.attention_mask,
                                    components=[READOUT_KEY],
                                    replacements=replacements,
                                    positions=streams.positions)
    return _readout_of(model, capture)


def patched_readout(model, streams: Streams, *, senders, receivers):
    """Both passes for one set of paths: `[batch, vocab]` fp32 at the Readout.

    A run does not call this — it shares one pass 1 across all of a sender's
    receivers — but every invariant is asserted through it, so the composition
    the run performs is the composition the tests check.
    """
    captured = receiver_inputs(model, streams, senders=senders,
                               receivers=receivers)
    return readout_from_receivers(
        model, streams, {row_key(one): captured.outputs[row_key(one)]
                         for one in receivers})


def normalized_effect(streams: Streams, patched):
    """`(patched - clean) / (clean - corrupt)` per instance, `[batch]` fp32.

    NaN where the Corruption did not move that instance's answer; those
    instances are counted in the output rather than averaged in.
    """
    import torch

    from component_analysis import hooks

    metric = hooks.target_minus_distractor(patched, streams.target,
                                           streams.distractor)
    effect = (metric - streams.clean_metric) / streams.gap
    return torch.where(streams.usable, effect,
                       torch.full_like(effect, float("nan")))


# ==============================================================================
# STATISTICS
# ==============================================================================

def summarize(values: Sequence[float]) -> dict:
    """Mean, standard error and counts over one cell's per-instance effects.

    A non-finite value is an instance whose Corruption did not move the answer
    (`MIN_GAP`), so it is counted in `n_excluded` rather than averaged in: a
    cell that lost half its sample says so instead of quietly reporting the
    other half. A cell with nothing left gets a **null** mean, not a NaN,
    because NaN is not valid JSON and the twin files exist to be read.
    """
    kept = [one for one in values if math.isfinite(one)]
    dropped = len(values) - len(kept)
    if not kept:
        return {"mean": None, "se": None, "n": 0, "n_excluded": dropped}
    mean = sum(kept) / len(kept)
    se = None
    if len(kept) > 1:
        variance = sum((one - mean) ** 2 for one in kept) / (len(kept) - 1)
        se = math.sqrt(variance / len(kept))
    return {"mean": mean, "se": se, "n": len(kept), "n_excluded": dropped}


def strongest(cells: Sequence[dict], limit: int) -> List[dict]:
    """The cells with the largest absolute mean effect, strongest first."""
    ranked = [one for one in cells if one["mean"] is not None]
    ranked.sort(key=lambda one: abs(one["mean"]), reverse=True)
    return ranked[:limit]


# ==============================================================================
# THE ANALYSIS
# ==============================================================================

def add_arguments(group) -> None:
    group.add_argument("--path-instances", type=int, default=0,
                       help="Cap the causal sample this analysis patches over. "
                            "0 uses all of it. The cap is rounded up to a whole "
                            "batch, and it is the lever when --dry-run's cost "
                            "estimate does not fit the job's wall clock.")
    group.add_argument("--path-top", type=int, default=10,
                       help="How many of the strongest cells, by absolute "
                            "normalized effect, are listed in the JSON.")


def heads_per_group(ctx) -> int:
    """How many query heads share one K or V receiver, from the HF config."""
    from component_analysis import intake

    kv_heads = intake.num_key_value_heads(
        ctx.intake.model, hf_token=getattr(ctx.cli, "hf_token", None),
        override=getattr(ctx.cli, "num_kv_heads", None))
    return ctx.intake.geometry["num_heads"] // kv_heads


def grid_for(ctx) -> Grid:
    return build_grid(ctx.components, heads_per_group=heads_per_group(ctx))


def _planned(ctx, batches) -> Tuple[int, int]:
    """(batches, instances) this run would use, after `--patch-instances`."""
    size = batches.report.get("batch_size") or 1
    wanted = int(getattr(ctx.cli, "path_instances", 0) or 0)
    if wanted <= 0 or wanted >= batches.n_instances:
        return len(batches), batches.n_instances
    n_batches = min(len(batches), -(-wanted // size))
    return n_batches, min(batches.n_instances, n_batches * size)


def estimate(ctx) -> str:
    grid = grid_for(ctx)
    batches = ctx.causal_batches()
    n_batches, n_instances = _planned(ctx, batches)
    budget = cost(grid, n_batches=n_batches,
                  batch_size=batches.report.get("batch_size") or 1)
    return (f"{budget['senders']} sender(s) x {budget['receivers']} receiver(s) "
            f"= {budget['cells']} cell(s) after upstream ordering; "
            f"{n_instances} instance(s) in {n_batches} batch(es) of "
            f"{budget['batch_size']}; {budget['forwards']} forward(s), about "
            f"{budget['minutes']:.0f} min at ticket 02b's A40 rate of "
            f"{budget['seconds_per_forward']:.2f} s per forward")


def _check_kv_groups(ctx, model) -> None:
    """The head table's KV groups must be the model's own.

    `--num-kv-heads` is an override, and a wrong one would send every K and V
    patch to a neighbouring group without any of the assertions noticing.
    """
    from component_analysis import hooks

    wrong = [one for one in ctx.components if one.kind == "head"
             and one.kv_group != hooks.kv_group_of(model, one.index)]
    if wrong:
        first = wrong[0]
        raise ValueError(
            f"{len(wrong)} head(s) carry a KV group the model disagrees with, "
            f"the first being layer {first.layer} head {first.index}: the head "
            f"table says group {first.kv_group}, the model says "
            f"{hooks.kv_group_of(model, first.index)}. Drop --num-kv-heads or "
            f"correct it; K and V receivers are addressed by group.")


def run(ctx) -> dict:
    """The position-agnostic pass over the causal sample.

    One pair of captures per batch, one patched forward per sender, and one
    forward per cell to read the receiver's new input back at the Readout.
    """
    grid = grid_for(ctx)
    _check_kv_groups(ctx, ctx.model)
    batches = ctx.causal_batches()
    n_batches, _planned_instances = _planned(ctx, batches)
    budget = cost(grid, n_batches=n_batches,
                  batch_size=batches.report.get("batch_size") or 1)

    values: Dict[Cell, List[float]] = {cell: [] for cell in grid.cells}
    tally = _Tally()
    started = time.perf_counter()

    for index, batch in enumerate(batches):
        if index >= n_batches:
            break
        streams = capture_streams(ctx.model, batch, senders=grid.senders)
        tally.forwards += 2
        tally.gaps.extend(streams.gap.tolist())
        tally.used_ids.extend(batch.ids)
        tally.excluded.extend(one for one, usable in zip(batch.ids,
                                                         streams.usable.tolist())
                              if not usable)

        for sender in grid.senders:
            receivers = grid.receivers_for(sender)
            if not receivers:
                continue
            captured = receiver_inputs(ctx.model, streams, senders=[sender],
                                       receivers=receivers)
            tally.forwards += 1
            for receiver in receivers:
                patched = readout_from_receivers(
                    ctx.model, streams, {receiver: captured.outputs[receiver]})
                tally.forwards += 1
                values[Cell(sender, receiver)].extend(
                    normalized_effect(streams, patched).tolist())
            del captured
        del streams

    tally.wall_seconds = time.perf_counter() - started
    summaries = {cell: {"sender": label(cell.sender),
                        "receiver": label(cell.receiver), "cell": cell.name,
                        **summarize(values[cell])}
                 for cell in grid.cells}
    payload = _payload(ctx, grid, summaries, budget=budget, tally=tally)
    ctx.write_json(SUBDIR, AGNOSTIC_FILE, payload)
    _figures(ctx, grid, summaries, payload)
    return head_table_columns(grid, summaries)


def _payload(ctx, grid, summaries, *, budget, tally: _Tally) -> dict:
    cells = list(summaries.values())
    direct = [summaries[Cell(sender, READOUT_KEY)] for sender in grid.senders]
    gaps = tally.gaps
    return {
        "analysis": NAME,
        "pass": "position_agnostic",
        "circuit": ctx.circuit_spec.label,
        "task": ctx.task_spec.name,
        "counterfactual": "item_swap",
        "metric": {
            "quantity": "logit(Target) - logit(Distractor) at the Readout, fp32",
            "effect": "(patched - clean) / (clean - corrupt), per instance",
            "sign": "negative means the path carries the Corruption; -1 is the "
                    "whole clean-minus-corrupt gap",
            "min_gap": MIN_GAP,
        },
        "grid": grid.size,
        "senders": [label(one) for one in grid.senders],
        "receivers": [{"key": label(one.key), "kind": one.kind,
                       "layer": one.layer, "index": one.key[2],
                       "covers_heads": list(one.covers_heads),
                       "circuit_heads": list(one.circuit_heads)}
                      for one in grid.receivers],
        "cells": cells,
        "strongest": strongest(cells, int(getattr(ctx.cli, "path_top", 10))),
        "direct_effect_on_readout": direct,
        "cells_without_a_mean": [one["cell"] for one in cells
                                 if one["mean"] is None],
        "sample": {
            "n_instances": len(tally.used_ids),
            "n_batches": budget["n_batches"],
            "batch_size": budget["batch_size"],
            "instance_ids": tally.used_ids,
            "n_excluded_by_gap": len(tally.excluded),
            "excluded_by_gap": tally.excluded,
        },
        "gap": {
            "mean": (sum(gaps) / len(gaps)) if gaps else None,
            "min": min(gaps) if gaps else None,
            "max": max(gaps) if gaps else None,
            "n_positive": sum(1 for one in gaps if one > 0),
        },
        "cost": {
            "estimated": budget,
            "forwards": tally.forwards,
            "wall_seconds": tally.wall_seconds,
            "seconds_per_forward": (tally.wall_seconds / tally.forwards
                                    if tally.forwards else None),
        },
    }


# ==============================================================================
# HEAD-TABLE COLUMNS
# ==============================================================================

def _receives(grid: Grid, key: tuple) -> List[tuple]:
    """The receiver keys at which a patch reaches this Component.

    A K or V receiver is a KV group, so a cell into it is incoming to **every**
    circuit head of that group, not only to the head whose index named it.
    """
    kind, layer, index = key
    if kind == "mlp":
        return [("mlp_in", layer, 0)]
    return [one.key for one in grid.receivers
            if one.layer == layer and index in one.circuit_heads]


def head_table_columns(grid: Grid, summaries: Dict[Cell, dict]) -> dict:
    """The three things the ticket asks of the head table, per Component.

    The strongest incoming and outgoing paths are by absolute mean effect, so a
    Component that suppresses the deceptive answer is as visible as one that
    promotes it; the sign is on the effect column beside the name. The columns
    carry no analysis prefix — the head table's namespace already says
    `path_patching`.
    """
    updates = {}
    for key in grid.senders:
        if key == EMBED_KEY:
            continue          # the embedding is a sender, never a head-table row
        incoming = [summaries[cell] for receiver in _receives(grid, key)
                    for cell in grid.cells_into(receiver)]
        outgoing = [summaries[cell] for cell in grid.cells if cell.sender == key]
        best_in = strongest(incoming, 1)
        best_out = strongest(outgoing, 1)
        direct = summaries[Cell(key, READOUT_KEY)]
        updates[key] = {
            "strongest_incoming": best_in[0]["cell"] if best_in else None,
            "strongest_incoming_effect": best_in[0]["mean"] if best_in else None,
            "strongest_outgoing": best_out[0]["cell"] if best_out else None,
            "strongest_outgoing_effect": best_out[0]["mean"] if best_out else None,
            "direct_effect": direct["mean"],
            "direct_effect_se": direct["se"],
        }
    return updates




# ==============================================================================
# FIGURES
# ==============================================================================

def heatmap_order(grid: Grid) -> List[Receiver]:
    """Receivers grouped by type, then by layer, then by head or group index.

    Grouping by type is what makes the heatmap readable: a column block of Q
    receivers beside a block of K receivers shows at a glance whether a sender
    is read as a query or as a key, which is the pre-registered question about
    the mid-layer heads.
    """
    return sorted(grid.receivers,
                  key=lambda one: (RECEIVER_KINDS.index(one.kind), one.layer,
                                   one.key[2]))


def _matrix(grid: Grid, summaries: Dict[Cell, dict]) -> Tuple[list, list, list]:
    """(row labels, ordered receivers, values) with None where no cell exists."""
    columns = heatmap_order(grid)
    rows = [label(one) for one in grid.senders]
    values = [[summaries[Cell(sender, one.key)]["mean"]
               if Cell(sender, one.key) in summaries else None
               for one in columns] for sender in grid.senders]
    return rows, columns, values


def _figures(ctx, grid: Grid, summaries: Dict[Cell, dict], payload: dict) -> None:
    """The two PNGs, each with the JSON twin an agent with no GUI reads."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    rows, columns, values = _matrix(grid, summaries)
    grid_values = np.array([[np.nan if one is None else one for one in row]
                            for row in values], dtype=float)
    finite = np.abs(grid_values[np.isfinite(grid_values)])
    extent = float(np.percentile(finite, HEATMAP_PERCENTILE)) if finite.size else 1.0
    clipped = int((finite > extent).sum()) if finite.size else 0
    # A grid whose effects are all zero, or whose 98th percentile is, still
    # needs a scale with a width; fall back to the largest effect, then to one.
    extent = extent or (float(finite.max()) if finite.size else 0.0) or 1.0

    ctx.write_json(SUBDIR, HEATMAP_JSON, {
        "title": "Position-agnostic path patching, normalized effect",
        "rows": rows,
        "columns": [{"key": label(one.key), "kind": one.kind,
                     "layer": one.layer, "index": one.key[2],
                     "covers_heads": list(one.covers_heads)}
                    for one in columns],
        "values": values,
        "missing": "null where the sender is not strictly upstream of the receiver",
        "colour_scale": {"percentile": HEATMAP_PERCENTILE, "extent": extent,
                         "cells_beyond_the_scale": clipped},
        "metric": payload["metric"],
    })

    figure, axes = plt.subplots(
        figsize=(max(6.0, 0.42 * len(columns) + 3.0),
                 max(3.5, 0.34 * len(rows) + 2.0)))
    # `with_extremes` rather than `set_bad`, which matplotlib 3.11 deprecates.
    colours = plt.get_cmap("coolwarm").with_extremes(bad=MISSING_COLOUR)
    image = axes.imshow(np.ma.masked_invalid(grid_values), cmap=colours,
                        vmin=-extent, vmax=extent, aspect="auto")
    axes.set_xticks(range(len(columns)))
    axes.set_xticklabels([label(one.key) for one in columns], rotation=90,
                         fontsize=6)
    axes.set_yticks(range(len(rows)))
    axes.set_yticklabels(rows, fontsize=6)
    for boundary in _kind_boundaries(columns):
        axes.axvline(boundary - 0.5, color="black", linewidth=0.8)
    axes.set_xlabel("receiver, grouped by type then layer")
    axes.set_ylabel("sender")
    axes.set_title(f"Path patching (position-agnostic) — "
                   f"{ctx.circuit_spec.label} x {ctx.task_spec.name}\n"
                   f"(patched - clean) / (clean - corrupt); grey = no path; "
                   f"scale to the {HEATMAP_PERCENTILE:g}th percentile, "
                   f"{clipped} cell(s) beyond it",
                   fontsize=9)
    figure.colorbar(image, ax=axes, fraction=0.03, pad=0.02, extend="both")
    figure.tight_layout()
    figure.savefig(os.path.join(ctx.subdir(SUBDIR), HEATMAP_PNG), dpi=200)
    plt.close(figure)

    direct = payload["direct_effect_on_readout"]
    ctx.write_json(SUBDIR, DIRECT_EFFECT_JSON, {
        "title": "Direct effect on the Readout, by sender",
        "receiver": label(READOUT_KEY), "senders": direct,
        "metric": payload["metric"],
    })
    figure, axes = plt.subplots(figsize=(max(5.0, 0.4 * len(direct) + 2.0), 3.6))
    heights = [one["mean"] or 0.0 for one in direct]
    errors = [one["se"] or 0.0 for one in direct]
    axes.bar(range(len(direct)), heights, yerr=errors, capsize=2,
             color=["#b2182b" if one < 0 else "#2166ac" for one in heights])
    axes.axhline(0.0, color="black", linewidth=0.8)
    axes.set_xticks(range(len(direct)))
    axes.set_xticklabels([one["sender"] for one in direct], rotation=90,
                         fontsize=6)
    axes.set_ylabel("normalized effect")
    axes.set_title(f"Direct effect on the Readout — {ctx.circuit_spec.label} x "
                   f"{ctx.task_spec.name}", fontsize=9)
    figure.tight_layout()
    figure.savefig(os.path.join(ctx.subdir(SUBDIR), DIRECT_EFFECT_PNG), dpi=200)
    plt.close(figure)


def _kind_boundaries(columns: Sequence[Receiver]) -> List[int]:
    """Column indices where the receiver type changes, for the separators."""
    return [index for index in range(1, len(columns))
            if columns[index].kind != columns[index - 1].kind]
