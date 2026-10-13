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

**The counterfactuals.** Two pairs, one code path. `item_swap` is the dataset's
own Corruption; `honest_instruction` replaces the Pressure Clause with its
Matched Honest Instruction (ticket 05) and exists only for the instances that
survived the honest filter, so its pass covers fewer rows and says which ones.
`counterfactual_pair` is the only function that knows which is which;
everything below it takes two aligned streams. Each counterfactual writes its
own JSON and figures and its own head-table columns, suffixed by name.

This module implements the **position-agnostic** pass of the spec — the
sender's value is written at every position and the receiver takes it at every
position — and, for the cells that clear `--path-position-threshold`, the
**position-specific** pass by Segment.

**The completeness sweep** (`--path-completeness-sweep`, off by default) asks
the one question the grid cannot: the grid only ever patches the circuit's own
Components, so a Component with a large direct effect that the pruning missed
is invisible to it. The sweep patches every head and MLP block of the whole
model into the Readout, ranks them, and flags the ones outside the circuit that
clear the threshold — those get a head-table row of their own.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from component_analysis.head_table import CAUSAL_SAMPLE, \
    PAIRED_HONEST_INSTRUCTION, row_key

#: The registration protocol (`component_analysis/registry.py`).
NAME = "path_patching"
SUBDIR = "path_patching"

#: The stem of every file this analysis writes. `output_name` turns a stem into
#: a filename for one counterfactual, so production and tests name a file the
#: same way and a renamed file cannot pass its own test.
AGNOSTIC_STEM = "agnostic"
SEGMENTS_STEM = "segments"
SWEEP_STEM = "sweep"
HEATMAP_STEM = "heatmap"
DIRECT_EFFECT_STEM = "direct_effect"
SEGMENTS_HEATMAP_STEM = "segments_heatmap"
SWEEP_BARS_STEM = "sweep_bars"

#: The item-swap spellings, which are ticket 08's and must not move: a head
#: table or a figure written before ticket 09 still resolves by these names.
AGNOSTIC_FILE = "agnostic.json"
SEGMENTS_FILE = "segments.json"
SWEEP_FILE = "sweep.json"
HEATMAP_PNG = "heatmap.png"
HEATMAP_JSON = "heatmap.json"
DIRECT_EFFECT_PNG = "direct_effect.png"
DIRECT_EFFECT_JSON = "direct_effect.json"
SEGMENTS_HEATMAP_PNG = "segments_heatmap.png"
SEGMENTS_HEATMAP_JSON = "segments_heatmap.json"
SWEEP_BARS_PNG = "sweep_bars.png"
SWEEP_BARS_JSON = "sweep_bars.json"

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

#: The two counterfactual pairs of `dataloaders.Batch`, and the `--path-
#: counterfactual` value that asks for both. `item_swap` is the dataset's own
#: Corruption (the Designation Site swapped); `honest_instruction` replaces the
#: Pressure Clause with its Matched Honest Instruction (ticket 05) and exists
#: only for the instances that survived the honest filter.
ITEM_SWAP = "item_swap"
HONEST_INSTRUCTION = "honest_instruction"
COUNTERFACTUALS = (ITEM_SWAP, HONEST_INSTRUCTION)
BOTH = "both"

#: What each counterfactual appends to a head-table column's bare name. The
#: item-swap columns keep the names ticket 08 wrote. The honest ones are spelled
#: out in full rather than as `_honest`, because `dla` has both a paired
#: honest-instruction column and an unpaired honest-twin one, and end in
#: `_paired` because they are computed over the same instance ids on both sides
#: (the researcher's 2026-10-13 decision). Before it they ended in
#: `_honest_instruction`, which `head_table.LEGACY_COLUMNS` translates.
COLUMN_SUFFIX = {ITEM_SWAP: "", HONEST_INSTRUCTION: "_honest_instruction_paired"}

#: The bare names this analysis writes per Component per counterfactual, before
#: the suffix and before the head table's own `path_patching.` namespace.
COLUMN_NAMES = ("strongest_incoming", "strongest_incoming_effect",
                "strongest_outgoing", "strongest_outgoing_effect",
                "direct_effect", "direct_effect_se")

#: The completeness sweep's bare names, suffixed the same way.
SWEEP_COLUMN_NAMES = ("sweep_direct_effect", "sweep_direct_effect_se",
                      "sweep_rank", "sweep_in_circuit", "sweep_flagged")

#: The instance set each counterfactual's columns cover, by name, for the head
#: table's coverage meta: the causal sample, or its paired subset.
INSTANCE_SETS = {ITEM_SWAP: CAUSAL_SAMPLE,
                 HONEST_INSTRUCTION: PAIRED_HONEST_INSTRUCTION}

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

#: Where a Q, MLP or Readout receiver takes its patch in the position-specific
#: pass: at the query positions, not per Segment (the spec's rule). Ticket 03
#: owns `--query-positions`; this is its default, spelled out here because an
#: analysis module may not import another analysis module. A test asserts the
#: two spellings equal wherever both are importable.
DEFAULT_QUERY_POSITION = "readout"
QUERY_ENTRY = "query_positions"

#: The entry name for the check that the Segments really do partition the
#: prompt: the receiver patched at every Segment at once must give back the
#: position-agnostic cell.
UNION_ENTRY = "union"

#: How many senders the completeness sweep's bar chart shows. The JSON twin
#: carries all of them; a thousand bars on one axis carries nothing.
SWEEP_BAR_TOP = 40

#: Receiver kinds whose position-specific pass is by Segment. The others take
#: one patch at the query positions.
SEGMENTED_KINDS = ("k", "v")

#: How far from zero a cell's position-agnostic effect must be to earn the
#: second, position-specific pass. Five percent of the clean-minus-
#: counterfactual gap, per the spec. Spelled once: `add_arguments` and the
#: reader take it from here, so a changed default cannot disagree with itself.
DEFAULT_POSITION_THRESHOLD = 0.05

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
    #: Instances of the sample with no counterpart under this counterfactual.
    unpaired: List[str] = field(default_factory=list)
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
    #: Which counterfactual the `corrupt_*` fields hold, one of `COUNTERFACTUALS`.
    counterfactual: str = ITEM_SWAP
    #: Which rows of the batch these streams cover. Every row under the item
    #: swap; only the rows with a Matched Honest survivor under the honest
    #: instruction.
    rows: Sequence[int] = ()

    @property
    def usable(self):
        """Instances whose Corruption moved the answer far enough to divide by.

        A gap of nearly zero means the item swap did not change the answer on
        that instance, so every cell would be a ratio of two small numbers.
        """
        return self.gap.abs() >= MIN_GAP


def counterfactual_pair(batch, counterfactual: str):
    """`(rows, input_ids, attention_mask)` of one counterfactual, or None.

    The item swap has a counterpart for every row of the batch. The Honest-
    Instruction Counterfactual has one only for the instances that survived the
    honest filter, and `HonestPair.rows` names them; a batch with none at all
    gives None, which a caller reports rather than averaging zeros in.

    This is the one function that knows which pair is which. Everything below
    it takes two aligned streams and does not care where they came from, which
    is user story 24's "same code path".
    """
    import torch

    if counterfactual not in COUNTERFACTUALS:
        raise ValueError(
            f"{counterfactual!r} is not a counterfactual; expected one of "
            f"{', '.join(COUNTERFACTUALS)}")
    if counterfactual == ITEM_SWAP:
        rows = list(range(len(batch.ids)))
        return rows, batch.corrupt_input_ids, batch.corrupt_attention_mask

    pair = batch.honest
    if pair is None or not pair.rows:
        return None
    rows = list(pair.rows)
    selector = torch.tensor(rows, dtype=torch.long)
    if not torch.equal(pair.attention_mask.sum(-1).long() - 1,
                       batch.readout[selector]):
        raise ValueError(
            "an Honest-Instruction Counterfactual does not end at the same "
            "position as its pressure prompt, so the two Readouts are not the "
            "same token; the pool has drifted from the dataset")
    return rows, pair.input_ids, pair.attention_mask


def stream_batches(ctx, batches, *, senders, counterfactual: str,
                   tally: "_Tally"):
    """Every batch of the loader as a `Streams`, with the tally kept.

    The three passes — position-agnostic, position-specific and the
    completeness sweep — each walk the loader the same way: capture the two
    streams, skip a batch that has no instance of this counterfactual, count
    the two forwards, and record which instances the pass really covered. That
    preamble is here once, so a pass that forgot to count a forward or to name
    an unpaired instance cannot differ from the pass beside it.
    """
    for batch in batches:
        streams = capture_streams(ctx.model, batch, senders=senders,
                                  counterfactual=counterfactual)
        if streams is None:
            tally.unpaired.extend(batch.ids)
            continue
        tally.forwards += 2
        tally.used_ids.extend(streams.ids)
        covered = set(streams.ids)
        tally.unpaired.extend(one for one in batch.ids if one not in covered)
        yield streams
        del streams


def capture_streams(model, batch, *, senders,
                    counterfactual: str = ITEM_SWAP):
    """The two forwards every cell of one batch is measured against.

    `batch` is a `dataloaders.Batch`. The clean stream is always the pressure
    prompt; the counterfactual stream is the item-swap corruption or the
    Matched Honest Instruction, and both are aligned to it token for token, so
    the Target and Distractor ids are read with the **clean** stream's
    assignment on both runs and the Readout position is shared.

    Returns None when this batch has no instance of the counterfactual, which
    on the Honest-Instruction Counterfactual is most batches of most splits.
    """
    import torch

    from component_analysis import hooks

    selected = counterfactual_pair(batch, counterfactual)
    if selected is None:
        return None
    rows, other_ids, other_mask = selected

    device, _dtype = hooks.device_and_dtype(model)
    keys = [row_key(one) for one in senders]
    frozen = hooks.all_component_keys(model)
    selector = torch.tensor(rows, dtype=torch.long)

    input_ids = batch.input_ids[selector].to(device)
    attention_mask = batch.attention_mask[selector].to(device)
    positions = batch.readout[selector].to(device)
    target = batch.target_token[selector].to(device)
    distractor = batch.distractor_token[selector].to(device)

    clean = hooks.capture_forward(model, input_ids, attention_mask,
                                  components=list(frozen) + [READOUT_KEY],
                                  positions=positions)
    corrupt = hooks.capture_forward(model, other_ids.to(device),
                                    other_mask.to(device),
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
        gap=clean_metric - corrupt_metric,
        ids=tuple(getattr(batch, "ids", ())[row] for row in rows),
        counterfactual=counterfactual, rows=tuple(rows))


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


def positioned_effects(model, streams: Streams, sender, receiver, entries):
    """`{entry name: [batch] normalized effect}` for one cell, by position.

    `entries` is `[(name, mask)]`, each mask a `[batch, seq]` boolean saying
    where the receiver takes the sender's corrupt value; `None` means every
    position, which is the position-agnostic cell. Pass 1 is run **once** and
    shared: what the receiver reads while the sender carries its corrupt value
    does not depend on where that value is later written in.

    This is the seam the position-specific pass is asserted at: the Segments
    partition the prompt, so the union of their masks must give back the
    position-agnostic cell.
    """
    from component_analysis import hooks

    captured = receiver_inputs(model, streams, senders=[sender],
                               receivers=[receiver]).outputs[receiver]
    out = {}
    for name, mask in entries:
        replacement = (captured if mask is None
                       else hooks.Replacement(captured,
                                              positions=mask.to(captured.device)))
        patched = readout_from_receivers(model, streams, {receiver: replacement})
        out[name] = normalized_effect(streams, patched)
    return out


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
    group.add_argument("--path-position-threshold", type=float,
                       default=DEFAULT_POSITION_THRESHOLD,
                       help="A (sender, receiver) cell whose position-agnostic "
                            "normalized effect is at least this far from zero "
                            "gets a second, position-specific pass by Segment, "
                            "and a Component outside the circuit that clears it "
                            "in the completeness sweep is flagged in the head "
                            "table. The default is five percent of the "
                            "clean-minus-counterfactual gap.")
    group.add_argument("--path-counterfactual", default=ITEM_SWAP,
                       choices=sorted(COUNTERFACTUALS) + [BOTH],
                       help="Which counterfactual pair the senders carry. "
                            f"{ITEM_SWAP!r} is the dataset's own Corruption; "
                            f"{HONEST_INSTRUCTION!r} replaces the Pressure "
                            "Clause with its Matched Honest Instruction and "
                            "covers only the instances that survived the "
                            f"honest filter; {BOTH!r} runs each in turn and "
                            "writes one file and one column set per pair.")
    group.add_argument("--path-sweep-threshold", type=float, default=None,
                       help="How strong a Component outside the circuit must "
                            "be in the completeness sweep to be flagged in the "
                            "head table. Defaults to --path-position-"
                            "threshold, so behaviour is unchanged unless it is "
                            "set. It is a separate flag because the two "
                            "questions are separate: a value chosen to widen "
                            "or narrow the Segment pass would otherwise move "
                            "which Components the sweep calls strong.")
    group.add_argument("--path-completeness-sweep", action="store_true",
                       help="Also patch every head and MLP block of the whole "
                            "model into the Readout, so that a Component with "
                            "a large direct effect that the pruning missed "
                            "becomes visible. Off by default: it is one "
                            "forward per Component per batch, which on an 8B "
                            "model is more work than the grid itself. "
                            "--dry-run prints what it would cost. It runs once, "
                            "on the item-swap pair when that is selected.")
    group.add_argument("--path-top", type=int, default=10,
                       help="How many of the strongest cells, by absolute "
                            "normalized effect, are listed in the JSON.")


def position_threshold(ctx) -> float:
    """Which cells earn the position-specific pass."""
    return float(getattr(ctx.cli, "path_position_threshold",
                         DEFAULT_POSITION_THRESHOLD))


def sweep_threshold(ctx) -> float:
    """Which sweep Components outside the circuit are flagged.

    Falls back to the position threshold when `--path-sweep-threshold` is not
    given, which is what it was before the two were split, so an old command
    line means what it used to.
    """
    given = getattr(ctx.cli, "path_sweep_threshold", None)
    return position_threshold(ctx) if given is None else float(given)


def selected_counterfactuals(ctx) -> List[str]:
    """The counterfactuals `--path-counterfactual` asks for, in a fixed order."""
    value = getattr(ctx.cli, "path_counterfactual", ITEM_SWAP) or ITEM_SWAP
    if value == BOTH:
        return list(COUNTERFACTUALS)
    if value not in COUNTERFACTUALS:
        raise ValueError(
            f"--path-counterfactual {value!r} is not one of "
            f"{', '.join(sorted(COUNTERFACTUALS) + [BOTH])}")
    return [value]


def output_name(stem: str, counterfactual: str, extension: str) -> str:
    """The file one pass writes, by counterfactual.

    `stem.ext` for the item swap, `stem_<counterfactual>.ext` otherwise.

    The item-swap files keep the names ticket 08 wrote, so the block C outputs
    of record and anything reading them still resolve; a second counterfactual
    writes beside them rather than over them.
    """
    if counterfactual == ITEM_SWAP:
        return f"{stem}.{extension}"
    return f"{stem}_{counterfactual}.{extension}"


def heads_per_group(ctx) -> int:
    """How many query heads share one K or V receiver, from the HF config."""
    from component_analysis import intake

    kv_heads = intake.num_key_value_heads(
        ctx.intake.model, hf_token=getattr(ctx.cli, "hf_token", None),
        override=getattr(ctx.cli, "num_kv_heads", None))
    return ctx.intake.geometry["num_heads"] // kv_heads


def grid_for(ctx) -> Grid:
    return build_grid(ctx.components, heads_per_group=heads_per_group(ctx))


def estimate(ctx) -> str:
    """One line for `--dry-run`: every pass this configuration would run.

    Each pass's re-capture of the two streams is counted, not only its patched
    forwards, because that is what ticket 08 verified the estimate against.
    """
    grid = grid_for(ctx)
    batches = ctx.causal_batches()
    n_batches, n_instances = len(batches), batches.n_instances
    budget = cost(grid, n_batches=n_batches,
                  batch_size=batches.report.get("batch_size") or 1)
    per_forward = seconds_per_forward(budget["batch_size"])
    chosen = selected_counterfactuals(ctx)
    paired = batches.report.get("n_with_honest") or 0

    segmentations = by_record_id(getattr(ctx, "segmentations", None))
    names = segment_names_of(segmentations)
    # The two names the position-specific table reserves are checked here as
    # well as in the pass, so a --segment override that collides fails on the
    # login node rather than an hour into a job.
    check_entry_names(names)
    if names:
        query_segment_names(ctx, names)

    def minutes(forwards):
        return forwards * per_forward / 60

    lines = [f"{budget['senders']} sender(s) x {budget['receivers']} receiver(s) "
             f"= {budget['cells']} cell(s) after upstream ordering; "
             f"{n_instances} instance(s) in {n_batches} batch(es) of "
             f"{budget['batch_size']}; {budget['forwards']} forward(s) per "
             f"counterfactual, about {budget['minutes']:.0f} min at ticket 02b's "
             f"A40 rate of {per_forward:.2f} s per forward",
             f"counterfactual(s): {', '.join(chosen)}"]

    kv = n_batches * (2 + len(names))
    other = n_batches * 2
    lines.append(
        f"position-specific pass: {other} forward(s) to re-capture the "
        f"streams, then {kv} per selected K or V cell ({len(names)} Segment(s) "
        f"plus the union check, about {minutes(kv):.1f} min) and {other} per "
        f"selected Q, MLP or Readout cell (about {minutes(other):.1f} min); how "
        f"many cells clear --path-position-threshold is not knowable until the "
        f"position-agnostic pass has run")

    if getattr(ctx.cli, "path_completeness_sweep", False):
        shape = ctx.intake.geometry
        n_senders = shape["num_layers"] * (shape["num_heads"] + 1) + 1
        forwards = n_batches * (2 + n_senders)
        lines.append(f"completeness sweep: {n_senders} sender(s) into the "
                     f"Readout, {forwards} forward(s), about "
                     f"{minutes(forwards):.0f} min, on "
                     f"{sweep_counterfactual(ctx)} only")

    if HONEST_INSTRUCTION in chosen:
        lines.append(f"{paired} of {n_instances} instance(s) have an "
                     f"Honest-Instruction counterpart, so that pass costs "
                     f"about {budget['minutes'] * paired / max(n_instances, 1):.0f} "
                     f"min")
    return "; ".join(lines)


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
    """Every selected counterfactual's position-agnostic pass, in turn.

    One pair of captures per batch, one patched forward per sender, and one
    forward per cell to read the receiver's new input back at the Readout. Each
    counterfactual writes its own JSON and figures and contributes its own
    head-table columns, and each is written as it finishes rather than at the
    end, so a job that runs out of wall clock leaves the passes that did finish
    on disk.
    """
    grid = grid_for(ctx)
    _check_kv_groups(ctx, ctx.model)
    batches = ctx.causal_batches()

    updates: Dict[tuple, dict] = {}
    for counterfactual in selected_counterfactuals(ctx):
        summaries, tally = agnostic_pass(ctx, grid, batches, counterfactual)
        if summaries is None:
            # The columns still appear, empty: a counterfactual that found no
            # instance is a data finding, and a missing column looks like an
            # analysis that was never asked for.
            _merge(updates, {key: dict.fromkeys(COLUMN_NAMES)
                             for key in grid.senders if key != EMBED_KEY},
                   counterfactual)
            _declare(ctx, COLUMN_NAMES, [], counterfactual)
            continue
        _merge(updates, head_table_columns(grid, summaries), counterfactual)
        _declare(ctx, COLUMN_NAMES, measured_ids(tally), counterfactual)
        segment_pass(ctx, grid, batches, counterfactual, summaries)

    # Last, and in its own loop over the batches, because it is the most
    # expensive pass and the least likely to fit: a job killed on the wall
    # clock during the sweep still leaves every pass above it written.
    if getattr(ctx.cli, "path_completeness_sweep", False):
        counterfactual = sweep_counterfactual(ctx)
        payload = completeness_sweep(ctx, grid, batches, counterfactual)
        _merge(updates, sweep_columns(payload), counterfactual)
        _declare(ctx, SWEEP_COLUMN_NAMES, payload["sample"]["instance_ids"],
                 counterfactual)
    return updates


def measured_ids(tally) -> List[str]:
    """The instances a pass's means are over: those it saw, less any whose
    clean-minus-counterfactual gap excluded them."""
    excluded = set(tally.excluded)
    return [one for one in tally.used_ids if one not in excluded]


def _declare(ctx, names, instance_ids, counterfactual: str) -> None:
    """One counterfactual's columns, declared over the instances they cover."""
    suffix = COLUMN_SUFFIX[counterfactual]
    ctx.declare_coverage([f"{name}{suffix}" for name in names],
                         instance_ids=instance_ids,
                         instance_set=INSTANCE_SETS[counterfactual])


def sweep_counterfactual(ctx) -> str:
    """Which pair the completeness sweep runs on: one, not both.

    The sweep asks whether pruning missed a Component of the circuit, which is
    a question about the circuit's own Corruption, and it costs more than the
    grid — so it runs on the item swap when that is selected and on the single
    selected pair otherwise, rather than twice.
    """
    chosen = selected_counterfactuals(ctx)
    return ITEM_SWAP if ITEM_SWAP in chosen else chosen[0]


def _merge(updates: Dict[tuple, dict], columns: Dict[tuple, dict],
           counterfactual: str) -> None:
    """Fold one counterfactual's columns in, suffixed by which pair they are."""
    suffix = COLUMN_SUFFIX[counterfactual]
    for key, values in columns.items():
        updates.setdefault(key, {}).update(
            {f"{name}{suffix}": value for name, value in values.items()})


def agnostic_pass(ctx, grid: Grid, batches, counterfactual: str):
    """One counterfactual's position-agnostic pass: `(summaries, tally)`.

    `(None, tally)` when this counterfactual has no instance in the sample —
    on the Honest-Instruction Counterfactual that is a data finding, so it is
    written out as a skipped file rather than left as an absent one.
    """
    budget = cost(grid, n_batches=len(batches),
                  batch_size=batches.report.get("batch_size") or 1)
    values: Dict[Cell, List[float]] = {cell: [] for cell in grid.cells}
    tally = _Tally()
    started = time.perf_counter()

    for streams in stream_batches(ctx, batches, senders=grid.senders,
                                  counterfactual=counterfactual, tally=tally):
        tally.gaps.extend(streams.gap.tolist())
        tally.excluded.extend(one for one, usable in zip(streams.ids,
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

    tally.wall_seconds = time.perf_counter() - started
    if not tally.used_ids:
        ctx.write_json(SUBDIR, output_name(AGNOSTIC_STEM, counterfactual, "json"),
                       _skipped_payload(ctx, counterfactual, tally))
        return None, tally

    summaries = {cell: {"sender": label(cell.sender),
                        "receiver": label(cell.receiver), "cell": cell.name,
                        **summarize(values[cell])}
                 for cell in grid.cells}
    payload = _payload(ctx, grid, summaries, budget=budget, tally=tally,
                       counterfactual=counterfactual)
    ctx.write_json(SUBDIR, output_name(AGNOSTIC_STEM, counterfactual, "json"), payload)
    _figures(ctx, grid, summaries, payload, counterfactual)
    return summaries, tally


def _skipped_payload(ctx, counterfactual: str, tally: _Tally) -> dict:
    """What is written when a counterfactual has no instance in the sample.

    An absent file and an empty one are indistinguishable from a crash; this
    one says which counterfactual found nothing and how many instances it
    looked at, which on the Honest-Instruction Counterfactual is the answer to
    "has the Matched Honest build been run for this task".
    """
    return {
        "analysis": NAME, "pass": "position_agnostic",
        "circuit": ctx.circuit_spec.label, "task": ctx.task_spec.name,
        "counterfactual": counterfactual,
        "skipped": f"no instance of the causal sample has a {counterfactual} "
                   f"counterpart",
        "n_without_a_counterpart": len(tally.unpaired),
        "without_a_counterpart": tally.unpaired,
        "cells": [],
    }


def metric_meta(counterfactual: str) -> dict:
    """The metric block every JSON of this analysis carries.

    It states the sign convention in the file itself. Path patching reads
    **negative** where a path carries the counterfactual, which is the opposite
    of knockout's positive drop; the two are reconciled in the roles vocabulary
    (ticket 10) and until then every file says which one it is.
    """
    return {
        "quantity": "logit(Target) - logit(Distractor) at the Readout, fp32",
        "effect": "(patched - clean) / (clean - corrupt), per instance",
        "counterfactual": counterfactual,
        "sign": f"negative means the path carries the {counterfactual} "
                f"counterfactual; -1 is the whole clean-minus-counterfactual "
                f"gap. Knockout (ticket 07) uses the opposite sign.",
        "min_gap": MIN_GAP,
    }


def _payload(ctx, grid, summaries, *, budget, tally: _Tally,
             counterfactual: str) -> dict:
    cells = list(summaries.values())
    direct = [summaries[Cell(sender, READOUT_KEY)] for sender in grid.senders]
    gaps = tally.gaps
    return {
        "analysis": NAME,
        "pass": "position_agnostic",
        "circuit": ctx.circuit_spec.label,
        "task": ctx.task_spec.name,
        "counterfactual": counterfactual,
        "metric": metric_meta(counterfactual),
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
            "n_without_a_counterpart": len(tally.unpaired),
            "without_a_counterpart": tally.unpaired,
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
# THE COMPLETENESS SWEEP
# ==============================================================================

def sweep_readout(model, streams: Streams, sender):
    """One sender's direct effect at the Readout, in a single forward.

    The two-pass cell reads the receiver's input off the frozen forward and
    writes it into a clean one. For the **Readout** receiver those are the same
    number: `hooks._traced_forward` saves the final norm's input after any
    replacement at it, so pass 2 would write back exactly the value pass 1 read
    and nothing between the two can change it. A test asserts the two are
    bit-identical. The sweep patches every head and MLP block of the model, so
    this halving is what puts it inside the short-job budget.
    """
    return _readout_of(model, receiver_inputs(model, streams, senders=[sender],
                                              receivers=[READOUT_KEY]))


def sweep_senders(model) -> List[tuple]:
    """Every sender of the model: the embedding, every head, every MLP block.

    The embedding is included although the ticket asks for heads and MLP
    blocks, so that the sweep's ranked list is directly comparable with the
    grid's `direct_effect_on_readout`, which has a row for it. It is not a
    Component and never becomes a head-table row.
    """
    from component_analysis import hooks

    return list(hooks.all_component_keys(model))


def completeness_sweep(ctx, grid: Grid, batches, counterfactual: str) -> dict:
    """Every head and MLP block of the model, patched into the Readout.

    The grid only ever asks about the circuit's own Components, so a Component
    with a large direct effect that pruning missed is invisible to it. This
    sweep is the check: one number per Component of the whole model, ranked,
    with circuit membership marked.
    """
    senders = sweep_senders(ctx.model)
    in_circuit = {row_key(one) for one in ctx.components}
    threshold = sweep_threshold(ctx)

    values: Dict[tuple, List[float]] = {key: [] for key in senders}
    tally = _Tally()
    started = time.perf_counter()

    for streams in stream_batches(ctx, batches, senders=senders,
                                  counterfactual=counterfactual, tally=tally):
        for sender in senders:
            values[sender].extend(
                normalized_effect(streams,
                                  sweep_readout(ctx.model, streams,
                                                sender)).tolist())
            tally.forwards += 1

    tally.wall_seconds = time.perf_counter() - started
    scored = [{"sender": label(key), "kind": key[0], "layer": key[1],
               "index": key[2], "in_circuit": key in in_circuit,
               **summarize(values[key])}
              for key in senders]
    # Strongest first by absolute effect; a sender with no mean at all has no
    # rank rather than the last one, and sorts to the end.
    ranked = sorted([one for one in scored if one["mean"] is not None],
                    key=lambda one: abs(one["mean"]), reverse=True)
    for rank, one in enumerate(ranked, start=1):
        one["rank"] = rank
    unranked = [{**one, "rank": None} for one in scored if one["mean"] is None]
    ranked = ranked + unranked
    for one in ranked:
        one["clears_threshold"] = (one["mean"] is not None
                                   and abs(one["mean"]) >= threshold)
        one["flagged"] = one["clears_threshold"] and not one["in_circuit"]

    payload = {
        "analysis": NAME,
        "pass": "completeness_sweep",
        "circuit": ctx.circuit_spec.label,
        "task": ctx.task_spec.name,
        "counterfactual": counterfactual,
        "metric": metric_meta(counterfactual),
        "receiver": label(READOUT_KEY),
        "threshold": threshold,
        "threshold_flag": "--path-sweep-threshold, defaulting to "
                          "--path-position-threshold",
        "n_senders": len(senders),
        "n_in_circuit": sum(1 for one in ranked if one["in_circuit"]),
        "flagged": [one["sender"] for one in ranked if one["flagged"]],
        "senders": ranked,
        "strongest": ranked[:int(getattr(ctx.cli, "path_top", 10))],
        "sample": {"n_instances": len(tally.used_ids),
                   "instance_ids": tally.used_ids,
                   "n_without_a_counterpart": len(tally.unpaired)},
        "cost": {"forwards": tally.forwards,
                 "wall_seconds": tally.wall_seconds,
                 "note": "one forward per sender per batch; the Readout "
                         "receiver needs no second pass"},
    }
    ctx.write_json(SUBDIR, output_name(SWEEP_STEM, counterfactual, "json"), payload)
    _sweep_figure(ctx, counterfactual, payload)
    return payload


def sweep_columns(payload: dict) -> Dict[tuple, dict]:
    """The head-table columns the sweep contributes, keyed by Component.

    Every circuit Component gets its sweep number. A Component **outside** the
    circuit gets a row of its own only when it clears the threshold — that is
    the whole point of the sweep, and appending all thousand-odd of them would
    bury the circuit in its own table.
    """
    updates = {}
    for one in payload["senders"]:
        key = (one["kind"], one["layer"], one["index"])
        if key == EMBED_KEY:
            continue
        if not one["in_circuit"] and not one["flagged"]:
            continue
        updates[key] = {
            "sweep_direct_effect": one["mean"],
            "sweep_direct_effect_se": one["se"],
            "sweep_rank": one["rank"],
            "sweep_in_circuit": one["in_circuit"],
            "sweep_flagged": one["flagged"],
        }
    return updates


def _sweep_figure(ctx, counterfactual: str, payload: dict) -> None:
    """The strongest senders as a bar chart, circuit Components highlighted."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    top = [one for one in payload["senders"]
           if one["mean"] is not None][:SWEEP_BAR_TOP]

    ctx.write_json(SUBDIR, output_name(SWEEP_BARS_STEM, counterfactual, "json"), {
        "title": f"Completeness sweep: direct effect on the Readout "
                 f"({counterfactual})",
        "counterfactual": counterfactual,
        "n_shown": len(top), "n_senders": payload["n_senders"],
        "threshold": payload["threshold"],
        "senders": top, "metric": payload["metric"],
    })

    if not top:
        return

    figure, axes = plt.subplots(figsize=(max(6.0, 0.28 * len(top) + 2.0), 3.8))
    heights = [one["mean"] for one in top]
    errors = [one["se"] or 0.0 for one in top]
    axes.bar(range(len(top)), heights, yerr=errors, capsize=2,
             color=["#b2182b" if one["in_circuit"] else "#bdbdbd"
                    for one in top])
    axes.axhline(0.0, color="black", linewidth=0.8)
    for sign in (1, -1):
        axes.axhline(sign * payload["threshold"], color="black",
                     linewidth=0.6, linestyle=":")
    axes.set_xticks(range(len(top)))
    axes.set_xticklabels([one["sender"] for one in top], rotation=90, fontsize=6)
    axes.set_ylabel("normalized effect")
    axes.set_title(f"Completeness sweep ({counterfactual}) — "
                   f"{ctx.circuit_spec.label} x {ctx.task_spec.name}\n"
                   f"strongest {len(top)} of {payload['n_senders']} sender(s); "
                   f"red = in the circuit, dotted = threshold "
                   f"{payload['threshold']:g}", fontsize=9)
    figure.tight_layout()
    figure.savefig(os.path.join(ctx.subdir(SUBDIR),
                                output_name(SWEEP_BARS_STEM, counterfactual, "png")),
                   dpi=200)
    plt.close(figure)


# ==============================================================================
# THE POSITION-SPECIFIC PASS, BY SEGMENT
# ==============================================================================

def query_segment_names(ctx, available: Sequence[str]) -> List[str]:
    """The Segments a Q, MLP or Readout receiver takes its patch at.

    Ticket 03 owns `--query-positions`; this reads the same flag so the two
    passes are anchored at the same tokens, and refuses an unknown name the
    same way ticket 03 does. That refusal is the point: a Segment that does not
    exist gives an all-false mask, which patches nothing and comes back as a
    null mean on every row — indistinguishable from a path that carries
    nothing. And with `--analyses path_patching` alone, ticket 03's own
    validation never runs, so this is the only thing standing between a typo
    and a table of nulls.
    """
    value = getattr(ctx.cli, "query_positions", None)
    wanted = ([one.strip() for one in value.split(",") if one.strip()]
              if value else [DEFAULT_QUERY_POSITION])
    if not wanted:
        raise ValueError("--query-positions was given no Segment name")
    unknown = [one for one in wanted if one not in available]
    if unknown:
        raise ValueError(
            f"--query-positions names {', '.join(unknown)}, which "
            f"{'is' if len(unknown) == 1 else 'are'} not a Segment of this "
            f"task. Its Segments are: {', '.join(available)}")
    return wanted


def check_entry_names(names: Sequence[str]) -> None:
    """No Segment may be called `union` or `query_positions`.

    Those two are rows of the position-specific table that are not Segments —
    the partition check and the single entry a Q, MLP or Readout receiver
    takes — and a task whose segmentation used either name would overwrite one
    of them silently. A `--segment` override is the likely way in.
    """
    clash = [one for one in names if one in (UNION_ENTRY, QUERY_ENTRY)]
    if clash:
        raise ValueError(
            f"Segment name(s) {', '.join(clash)} collide with the "
            f"position-specific table's own row names ({UNION_ENTRY}, "
            f"{QUERY_ENTRY}); rename the Segment or the --segment override")


def selected_cells(summaries: Dict[Cell, dict], threshold: float) -> List[Cell]:
    """The cells whose position-agnostic effect clears the threshold.

    By absolute effect, so a path that suppresses the counterfactual answer is
    selected as readily as one that carries it; strongest first, because the
    second pass is the expensive one and a truncated run should have spent its
    time on the largest cells.
    """
    ranked = [(cell, one) for cell, one in summaries.items()
              if one["mean"] is not None and abs(one["mean"]) >= threshold]
    ranked.sort(key=lambda pair: abs(pair[1]["mean"]), reverse=True)
    return [cell for cell, _one in ranked]


def position_mask(segmentations: dict, ids, names: Sequence[str],
                  n_positions: int):
    """`([batch, n_positions] bool, [batch] bool)`: where, and for which rows.

    The second tensor is whether the instance has any of those Segments at all.
    A Segment can be legitimately absent — the saved FAR run predates the
    Designation Suffix — and an absent Segment patches nothing, so its effect
    would be exactly zero. Counting those zeros as data would pull the
    Segment's mean toward nothing; they are marked here and excluded instead.
    """
    import torch

    mask = torch.zeros((len(ids), n_positions), dtype=torch.bool)
    for row, one in enumerate(ids):
        segmentation = segmentations.get(one)
        if segmentation is None:
            continue
        for name in names:
            segment = segmentation.segments.get(name)
            if segment is None:
                continue
            for start, end in segment.spans:
                if start < n_positions:
                    mask[row, start:min(end, n_positions)] = True
    return mask, mask.any(-1)


def segment_entries(ctx, receiver: tuple, streams: Streams, segmentations: dict,
                    n_positions: int, names: Sequence[str]):
    """`[(name, mask, present)]` for one receiver, in the order they are run.

    K and V receivers take the patch at each Segment's key positions in turn,
    plus the union of them all as the check that the split is a decomposition.
    Q, MLP and Readout receivers take one patch at the configured query
    positions, which is the spec's rule rather than a saving: their input is
    read at the position the model answers from, so a Segment sweep over them
    would be a sweep over positions the receiver does not read.

    `names` is the whole cell's Segment list, fixed once by the caller, so
    every batch contributes to the same columns even if one batch happens to
    have no instance carrying some Segment.
    """
    ids = list(streams.ids)
    if receiver[0] not in SEGMENTED_KINDS:
        query = query_segment_names(ctx, names)
        mask, present = position_mask(segmentations, ids, query, n_positions)
        return [(QUERY_ENTRY, mask, present)]

    entries = []
    for name in names:
        mask, present = position_mask(segmentations, ids, [name], n_positions)
        entries.append((name, mask, present))
    union, present = position_mask(segmentations, ids, names, n_positions)
    entries.append((UNION_ENTRY, union, present))
    return entries


def segment_names_of(segmentations) -> List[str]:
    """Every Segment name the cell's segmentation carries, in prompt order.

    Read off the resolved segmentation rather than from the task's default
    list, so that a `--segment` override on the command line is swept too, and
    fixed once for the whole pass rather than per batch.
    """
    names: List[str] = []
    for segmentation in segmentations.values():
        for name in segmentation.segments:
            if name not in names:
                names.append(name)
    return names


def by_record_id(segmentations) -> dict:
    """The cell's resolved segmentation, keyed by the id the loaders join on.

    `Segmentation.record_id` and `Batch.ids` both come from
    `sampling.record_ids`, so this join is by instance id and never by split
    position.
    """
    return {one.record_id: one for one in (segmentations or [])}


def segment_pass(ctx, grid: Grid, batches, counterfactual: str,
                 summaries: Dict[Cell, dict]) -> dict:
    """The second pass over the cells that cleared `--path-position-threshold`.

    One pass 1 per (cell, batch), shared across every position entry of that
    cell, and one pass 2 per entry. The result says, for each selected cell,
    where in the prompt the path carries its effect.
    """
    import torch

    threshold = position_threshold(ctx)
    chosen = selected_cells(summaries, threshold)
    segmentations = by_record_id(getattr(ctx, "segmentations", None))
    names = segment_names_of(segmentations)
    check_entry_names(names)
    # Validated before the loop, not inside it: a typo must fail on the first
    # batch of a GPU job, not after the grid has been patched.
    query_segment_names(ctx, names)

    rows: Dict[Cell, Dict[str, List[float]]] = {
        cell: {} for cell in chosen}
    absent: Dict[Cell, Dict[str, int]] = {cell: {} for cell in chosen}
    tally = _Tally()
    started = time.perf_counter()
    missing_segmentation: List[str] = []

    if chosen:
        for streams in stream_batches(ctx, batches, senders=grid.senders,
                                      counterfactual=counterfactual,
                                      tally=tally):
            missing_segmentation.extend(one for one in streams.ids
                                        if one not in segmentations)
            n_positions = streams.input_ids.shape[1]
            for cell in chosen:
                entries = segment_entries(ctx, cell.receiver, streams,
                                          segmentations, n_positions, names)
                effects = positioned_effects(
                    ctx.model, streams, cell.sender, cell.receiver,
                    [(name, mask) for name, mask, _present in entries])
                tally.forwards += 1 + len(entries)
                for name, _mask, present in entries:
                    values = torch.where(present.to(effects[name].device),
                                         effects[name],
                                         torch.full_like(effects[name],
                                                         float("nan")))
                    rows[cell].setdefault(name, []).extend(values.tolist())
                    absent[cell][name] = absent[cell].get(name, 0) + int(
                        (~present).sum())

    tally.wall_seconds = time.perf_counter() - started
    payload = _segment_payload(ctx, counterfactual, chosen, rows, absent,
                               summaries, threshold=threshold, tally=tally,
                               names=names,
                               missing_segmentation=missing_segmentation)
    ctx.write_json(SUBDIR, output_name(SEGMENTS_STEM, counterfactual, "json"), payload)
    _segment_figure(ctx, counterfactual, payload)
    return payload


def _segment_payload(ctx, counterfactual, chosen, rows, absent, summaries, *,
                     threshold, tally, names, missing_segmentation):
    """The per-cell, per-Segment table, with the union check beside each cell.

    `agnostic` and `union` are the same quantity measured two ways, so a reader
    can see that the split is a decomposition. `sum_of_segments` is recorded
    beside them and is **not** expected to equal either: patching two Segments
    at once is not the sum of patching each, because the receiver's forward is
    not linear in its input. The check the spec asks for is the union one.
    """
    cells = []
    for cell in chosen:
        entries = {}
        for name, values in rows[cell].items():
            entries[name] = {**summarize(values),
                             "n_absent": absent[cell].get(name, 0)}
        segments = {name: one for name, one in entries.items()
                    if name not in (UNION_ENTRY, QUERY_ENTRY)}
        means = [one["mean"] for one in segments.values()
                 if one["mean"] is not None]
        agnostic = summaries[cell]["mean"]
        union = entries.get(UNION_ENTRY, {}).get("mean")
        cells.append({
            "cell": cell.name,
            "sender": label(cell.sender), "receiver": label(cell.receiver),
            "receiver_kind": cell.receiver[0],
            "by_segment": entries,
            "agnostic": agnostic,
            "union": union,
            "union_minus_agnostic": (None if union is None or agnostic is None
                                     else union - agnostic),
            "sum_of_segments": sum(means) if means else None,
            "top_segment": _top_segment(segments),
        })
    return {
        "analysis": NAME,
        "pass": "position_specific",
        "circuit": ctx.circuit_spec.label,
        "task": ctx.task_spec.name,
        "counterfactual": counterfactual,
        "metric": metric_meta(counterfactual),
        "threshold": threshold,
        "selection": f"cells whose position-agnostic |mean| is at least "
                     f"{threshold}",
        "n_selected": len(chosen),
        "query_positions": query_segment_names(ctx, names),
        "position_rule": (
            "K and V receivers take the patch at each Segment's key positions; "
            "Q, MLP and Readout receivers take it at the query positions"),
        "union_check": (
            "the Segments partition the prompt, so 'union' must reproduce "
            "'agnostic'; 'sum_of_segments' is recorded for information and is "
            "not expected to, because a receiver's forward is not linear in "
            "its input"),
        "segments": list(names),
        "spans": "the Segments are resolved on the pressure prompt; both "
                 "counterfactual streams are aligned to it token for token, so "
                 "the same spans address both",
        "cells": cells,
        "sample": {"n_instances": len(tally.used_ids),
                   "instance_ids": tally.used_ids,
                   "n_without_a_segmentation": len(missing_segmentation),
                   "without_a_segmentation": missing_segmentation},
        "cost": {"forwards": tally.forwards,
                 "wall_seconds": tally.wall_seconds},
    }


def _top_segment(segments: Dict[str, dict]):
    """The Segment carrying the most of a cell's effect, by absolute mean."""
    ranked = [(name, one["mean"]) for name, one in segments.items()
              if one["mean"] is not None]
    if not ranked:
        return {"segment": None, "mean": None}
    name, mean = max(ranked, key=lambda pair: abs(pair[1]))
    return {"segment": name, "mean": mean}


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


def _figures(ctx, grid: Grid, summaries: Dict[Cell, dict], payload: dict,
             counterfactual: str) -> None:
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

    ctx.write_json(SUBDIR, output_name(HEATMAP_STEM, counterfactual, "json"), {
        "title": f"Position-agnostic path patching, normalized effect "
                 f"({counterfactual})",
        "counterfactual": counterfactual,
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
    axes.set_title(f"Path patching (position-agnostic, {counterfactual}) — "
                   f"{ctx.circuit_spec.label} x {ctx.task_spec.name}\n"
                   f"(patched - clean) / (clean - corrupt); grey = no path; "
                   f"scale to the {HEATMAP_PERCENTILE:g}th percentile, "
                   f"{clipped} cell(s) beyond it",
                   fontsize=9)
    figure.colorbar(image, ax=axes, fraction=0.03, pad=0.02, extend="both")
    figure.tight_layout()
    figure.savefig(os.path.join(ctx.subdir(SUBDIR),
                                output_name(HEATMAP_STEM, counterfactual, "png")),
                   dpi=200)
    plt.close(figure)

    direct = payload["direct_effect_on_readout"]
    ctx.write_json(SUBDIR, output_name(DIRECT_EFFECT_STEM, counterfactual, "json"), {
        "title": f"Direct effect on the Readout, by sender ({counterfactual})",
        "counterfactual": counterfactual,
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
    axes.set_title(f"Direct effect on the Readout ({counterfactual}) — "
                   f"{ctx.circuit_spec.label} x {ctx.task_spec.name}",
                   fontsize=9)
    figure.tight_layout()
    figure.savefig(os.path.join(ctx.subdir(SUBDIR),
                                output_name(DIRECT_EFFECT_STEM, counterfactual, "png")),
                   dpi=200)
    plt.close(figure)


def _segment_figure(ctx, counterfactual: str, payload: dict) -> None:
    """One row per selected cell, one column per Segment, with its JSON twin.

    Q, MLP and Readout receivers have no Segment row — they take one patch at
    the query positions — so they occupy the trailing column and the Segment
    columns are grey for them, which is the same "no cell here" grey the
    position-agnostic heatmap uses.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    segments = list(payload["segments"])
    columns = segments + [QUERY_ENTRY]
    cells = payload["cells"]
    values = [[one["by_segment"].get(name, {}).get("mean") for name in columns]
              for one in cells]
    rows = [one["cell"] for one in cells]

    ctx.write_json(SUBDIR, output_name(SEGMENTS_HEATMAP_STEM, counterfactual, "json"), {
        "title": f"Position-specific path patching by Segment ({counterfactual})",
        "counterfactual": counterfactual,
        "rows": rows, "columns": columns, "values": values,
        "missing": "null where this receiver kind takes no patch at that "
                   "column; K and V receivers are swept by Segment, everything "
                   "else takes one patch at the query positions",
        "threshold": payload["threshold"],
        "metric": payload["metric"],
    })

    if not cells:
        return

    grid_values = np.array([[np.nan if one is None else one for one in row]
                            for row in values], dtype=float)
    finite = np.abs(grid_values[np.isfinite(grid_values)])
    extent = float(finite.max()) if finite.size else 1.0
    extent = extent or 1.0

    figure, axes = plt.subplots(
        figsize=(max(6.0, 0.55 * len(columns) + 3.0),
                 max(3.0, 0.4 * len(rows) + 2.0)))
    colours = plt.get_cmap("coolwarm").with_extremes(bad=MISSING_COLOUR)
    image = axes.imshow(np.ma.masked_invalid(grid_values), cmap=colours,
                        vmin=-extent, vmax=extent, aspect="auto")
    axes.set_xticks(range(len(columns)))
    axes.set_xticklabels(columns, rotation=90, fontsize=7)
    axes.set_yticks(range(len(rows)))
    axes.set_yticklabels(rows, fontsize=7)
    axes.axvline(len(segments) - 0.5, color="black", linewidth=0.8)
    axes.set_xlabel("Segment the patch is written at")
    axes.set_ylabel("sender -> receiver")
    axes.set_title(f"Path patching by Segment ({counterfactual}) — "
                   f"{ctx.circuit_spec.label} x {ctx.task_spec.name}\n"
                   f"cells with |position-agnostic effect| >= "
                   f"{payload['threshold']:g}; grey = not swept",
                   fontsize=9)
    figure.colorbar(image, ax=axes, fraction=0.03, pad=0.02)
    figure.tight_layout()
    figure.savefig(os.path.join(ctx.subdir(SUBDIR),
                                output_name(SEGMENTS_HEATMAP_STEM, counterfactual, "png")),
                   dpi=200)
    plt.close(figure)


def _kind_boundaries(columns: Sequence[Receiver]) -> List[int]:
    """Column indices where the receiver type changes, for the separators."""
    return [index for index in range(1, len(columns))
            if columns[index].kind != columns[index - 1].kind]
