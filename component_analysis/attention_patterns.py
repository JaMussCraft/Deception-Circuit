"""
component_analysis/attention_patterns.py — what each Circuit Component head reads.

For every attention head in the circuit, the attention mass it places on each
**Segment** of the prompt, from a chosen query position (the **Readout** by
default), averaged over instances and split by designation polarity, item
polarity, both or neither. A head that reads the Designation Positions is doing
something different from one that reads the quoted option it is about to copy,
and this is the view that tells them apart.

Three conditions, chosen with `--attention-conditions`, and the difference
between them is the whole point of reading the table (CONTEXT.md; spec user
story 27):

    pressure             the task's own test split, under the Pressure Clause.
                         Descriptive, over every instance.
    honest_instruction   the *same* instances with the Pressure Clause replaced
                         by its Matched Honest Instruction. **Paired** and
                         causal: prompt and counterfactual align token for
                         token, so a difference is that instance's difference.
                         Only the instances that survived the clean-stream
                         honest filter have one (71 of the 100 sampled on SDR).
    honest_twin          the `<task>_honest` dataset: different instances,
                         answered honestly. **Unpaired, descriptive.** A
                         difference here is a difference between populations
                         and must never be read as a causal one, which is why
                         every column and every figure panel carries the label.

A fourth condition, `pressure_paired`, is derived rather than selectable: it is
the Pressure Clause on exactly the instances that have an Honest-Instruction
Counterfactual. It exists because `pressure` is the whole split, so the paired
honest column has nothing over the same instance ids to be read against without
it, and "paired" means the same instance ids on both sides.

Eager attention is on only inside `hooks.attention_weights`, which restores
SDPA in a `finally` (ADR-0001). This is the one analysis that pays the
`[batch, heads, seq, seq]` buffer per layer.

Every attention figure is drawn in `COLORMAP`, yellow through orange to dark
red, because the researcher reads these on a screen with a strong blue-light
filter, which dims and yellows blues and purples, so a map whose low end is
dark purple or blue (magma, viridis) collapses its bottom third to near-black
there, while this one carries its range in luminance and red-orange-yellow
hue. Each figure's JSON twin records the name under `colormap`, and the review
notebook draws its attention heatmaps in the same map.

What lands in the cell
----------------------
`attention/patterns.json`, which is the whole result and the twin of every
figure's numbers:

    analysis, schema_version, task, circuit, model
    split                  which factor the levels are, or "none"
    query_positions        the Segment names queried, in order
    column_query_position  the one the head-table columns were read at
    segments               every Segment name, in CONTEXT.md's order
    sum_tolerance          how far a row may be from one before `sums_to_one`
                           goes false
    components             [{key, name, label, layer, index, kv_group}], the
                           circuit's attention heads in head-table order
    conditions             one entry per condition that ran:
                             name, kind, paired, descriptive, dataset
                             instance_ids  which instances it was profiled
                                           over, in the order they were read.
                                           The two paired conditions carry the
                                           same list, which is what makes
                                           "paired" checkable in the file
                                           rather than only in the code
                             n_instances   what it was profiled over
                             n_loaded      what the loader held (they differ
                                           for the paired condition, where
                                           most of the sample has no
                                           counterpart)
                             batches
                             levels        [{level, n, n_by_query_position,
                                             n_absent_by_query_position,
                                             masses}]
                             checks        {max_abs_sum_minus_one, max_outside,
                                            n_batches, n_nan, sums_to_one}
                             notes         [str]
                             alignment     paired condition only: the token
                                           diff against the pressure prompts
    skipped                [{condition, reason}] — a condition that could not
                           run says so rather than going missing

`masses` is `{component key: {query Segment: {key Segment: mean mass}}}`, the
component key spelled `head.<layer>.<index>`.

Beside it: one heatmap PNG per split level (heads by Segment, one panel per
condition) with its JSON twin, and `top_heads.png` — a per-head bar chart for
the top-k heads by knockout rank when a knockout column already exists in the
cell's head table, and by layer when it does not.

Head-table columns, namespaced `attention_patterns.` by the CLI:

    query_position                          which query Segment the columns read
    pressure_top_segment / _top_mass        under the Pressure Clause, whole split
    pressure_paired_top_segment / _top_mass the paired subset's left term
    honest_instruction_paired_top_segment /
        _top_mass                           paired: the same instance ids, under
                                            the Matched Honest Instruction
    honest_twin_descriptive_top_segment /
        _top_mass                           the unpaired twin, labelled in the
                                            column name so a CSV reader cannot
                                            mistake it for a paired contrast

Both paired columns say `paired` in their names and the twin's says
`descriptive` (the researcher's 2026-10-13 decision; before it the paired honest
column was `honest_instruction_top_segment`, which `head_table.LEGACY_COLUMNS`
still translates). Every condition gets its columns whether or not it ran; a
condition with no data leaves them empty rather than absent, so head tables
from different cells still line up. Each column's instances are declared into
the head table's meta (`declare_coverage`): the whole split, the paired subset
or the twin's split, with n = 0 for a condition that did not run.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch

from component_analysis import head_table as ht

NAME = "attention_patterns"
SUBDIR = "attention"

#: The whole result, and the JSON twin of every figure's numbers.
PATTERNS_FILE = "patterns.json"
#: The honest twin's own segmentation, written for the same reason the cell's
#: `segmentation.json` is: no plot may be read against the wrong spans.
TWIN_SEGMENTATION_FILE = "honest_twin_segmentation.json"

SCHEMA_VERSION = 1

#: The default query position. The Readout is where the answer is produced, so
#: it is what a head reads "at the moment it matters" (spec user story 7).
DEFAULT_QUERY_POSITION = "readout"

#: The conditions `--attention-conditions` selects, in the order they are
#: measured and plotted. Named here rather than spelled at each use so that the
#: flag, the payload and the columns cannot drift apart.
PRESSURE = "pressure"
HONEST_INSTRUCTION = "honest_instruction"
HONEST_TWIN = "honest_twin"
CONDITIONS = (PRESSURE, HONEST_INSTRUCTION, HONEST_TWIN)

#: The paired condition's own left term: the *pressure* prompts of exactly the
#: instances that have an Honest-Instruction Counterfactual. Derived rather
#: than selectable, for the reason `dla.PRESSURE_PAIRED` is: "paired" means the
#: same instance ids on both sides, and `pressure` is profiled over the whole
#: test split. Comparing the paired honest column against the full-split
#: pressure column is a population contrast wearing a causal contrast's name,
#: which is what spec user story 27 exists to prevent, so the left term is
#: measured on its own rows and reported beside its right term.
PRESSURE_PAIRED = "pressure_paired"

#: `--split NAME` to the record fields whose levels the profiles are split by.
SPLITS: Dict[str, Tuple[str, ...]] = {
    "designation": ("designation_polarity",),
    "item": ("item_polarity",),
    "both": ("designation_polarity", "item_polarity"),
    "none": (),
}

#: The level every instance belongs to, present under every split. The
#: head-table columns and the unsplit heatmap are read off this one.
ALL_LEVEL = "all"

#: What a record says when it does not carry the factor being split on. Named
#: rather than dropped: an instance missing from a profile is invisible.
UNKNOWN_LEVEL = "unknown"

#: Seconds per eager forward at batch 8 x 128 tokens on an A40, measured by
#: ticket 02b's scaffold job (22106585). `estimate` scales it by the batch.
EAGER_SECONDS_PER_BATCH_OF_8 = 0.19

#: The colormap of every attention figure, and the name each JSON twin records
#: under `colormap` (the module docstring says why it is warm). Matplotlib and
#: plotly both know it by this name and agree on its ends, light yellow at zero
#: and dark red at the top, so the notebook takes it from the twin unchanged.
COLORMAP = "YlOrRd"

#: Where no value exists — a head with no profile — the axes show through as
#: grey hatching. A missing cell must not read as zero, and on this map zero is
#: the palest colour, so a blank white cell would.
MISSING_HATCH = "xx"
MISSING_HATCH_COLOUR = "#9a9a9a"

#: How far a row of attention may be from summing to one before the run says
#: so. HuggingFace's eager attention softmaxes in fp32 and casts the weights
#: back to the model's dtype, so on a bfloat16 model a row of 128 weights is
#: one only to about 1e-2; the tolerance is about the dtype, not about the
#: analysis.
SUM_TOLERANCE = 2e-2


# ==============================================================================
# READING THE FLAGS
# ==============================================================================

class UnknownCondition(ValueError, argparse.ArgumentTypeError):
    """A condition name that is not one of `CONDITIONS`.

    Both base classes on purpose. `argparse` reports the message of an
    `ArgumentTypeError` and replaces the message of a plain `ValueError` with
    "invalid parse_conditions value: 'honest'", which names the function
    instead of the flag and says nothing about what the valid names are. A
    caller that reaches `wanted_conditions` directly still catches a
    `ValueError`, as `dla.wanted_conditions` raises.
    """


def parse_conditions(value) -> List[str]:
    """`"a,b"` to `["a", "b"]`, refusing an unknown name.

    Wired as the flag's `type=`, so an unknown condition is refused by
    `argparse` at parse time — before the circuits resolve and long before an
    8B model is loaded onto a GPU. `registry.select` refuses an unknown
    `--analyses` name the same way up front, and a flag that costs a GPU load
    to reject a typo is a flag that gets typo'd on the cluster.
    """
    if not isinstance(value, str):
        return [one for one in CONDITIONS if one in value]
    wanted = [one.strip() for one in value.split(",") if one.strip()]
    unknown = [one for one in wanted if one not in CONDITIONS]
    if unknown:
        raise UnknownCondition(
            f"--attention-conditions names {', '.join(unknown)}, which "
            f"{'is' if len(unknown) == 1 else 'are'} not an attention "
            f"condition. Choose from {', '.join(CONDITIONS)}.")
    return [one for one in CONDITIONS if one in wanted]


def wanted_conditions(cli) -> List[str]:
    """The conditions this run profiles, in measurement order.

    The same semantics as `dla.wanted_conditions`, and deliberately the same
    shape: the two descriptive analyses are read side by side in one head
    table, and a flag that means one thing under `--dla-conditions` and
    another under `--attention-conditions` would be a trap. The one difference
    is when a typo is caught — here at parse time, there inside `run` — and it
    is recorded in ticket 06 rather than left for a reader to discover.
    """
    value = getattr(cli, "attention_conditions", None)
    if value is None:
        return list(CONDITIONS)
    return parse_conditions(value)


def add_arguments(group) -> None:
    group.add_argument("--attention-conditions", type=parse_conditions,
                       default=list(CONDITIONS), metavar="NAME[,NAME]",
                       help="Which conditions to profile: "
                            f"{', '.join(CONDITIONS)}. "
                            f"{HONEST_INSTRUCTION} is the paired "
                            "Honest-Instruction Counterfactual and brings its "
                            f"own left term, {PRESSURE_PAIRED}, with it. "
                            f"Dropping {PRESSURE} is allowed and leaves the "
                            "cell with no full-split column, which is a "
                            "smoke-run shape, not a reporting one. A condition "
                            "whose data this cell does not have is reported "
                            "under 'skipped' and left out.")
    group.add_argument("--query-positions", default=None,
                       metavar="SEGMENT[,SEGMENT]",
                       help="Which Segments to read attention from, by name "
                            f"(default: {DEFAULT_QUERY_POSITION}). A Segment "
                            "spanning several tokens is averaged over its "
                            "tokens, per instance.")
    group.add_argument("--split", default="designation", choices=sorted(SPLITS),
                       help="Split every profile by this factor. The unsplit "
                            f"{ALL_LEVEL!r} level is always computed as well, "
                            "and is what the head-table columns read.")
    group.add_argument("--attention-honest-twin", default="auto",
                       metavar="auto|off|DIR",
                       help="The unpaired honest-twin dataset for the "
                            "descriptive honest column. 'auto' looks for "
                            "<dataset dir>_honest beside the task's own "
                            "dataset and skips the condition, with a recorded "
                            "reason, when it is not there.")
    group.add_argument("--attention-top-k", type=int, default=8,
                       help="How many heads the per-head bar chart shows, "
                            "ranked by knockout when that column exists in the "
                            "cell's head table and by layer when it does not.")
    group.add_argument("--attention-rank-column", default=None, metavar="COLUMN",
                       help="Rank the bar chart's heads by this head-table "
                            "column instead (largest magnitude first).")
    group.add_argument("--attention-token-level", action="store_true",
                       help="Also render, per circuit head, the mean attention "
                            "from the query positions to every token of the "
                            "prompt (no Segment summing), one PNG per head "
                            f"under {SUBDIR}/{TOKEN_LEVEL_SUBDIR}/, grouped by "
                            "template variant. Read from the same forward "
                            "passes, so it adds no GPU pass. The per-head JSON "
                            "twins carry their values only while they total "
                            f"under {TOKEN_LEVEL_JSON_LIMIT_BYTES // 1_000_000} "
                            "MB per cell, and are meta-only above it.")


def parse_query_positions(value: Optional[str],
                          available: Sequence[str]) -> List[str]:
    """`--query-positions` as Segment names, refusing a name the task has not.

    Refused by name rather than ignored: a query position that silently does
    not exist would produce an empty profile, which reads as "this head attends
    to nothing".
    """
    if value is None:
        wanted = [DEFAULT_QUERY_POSITION]
    else:
        wanted = [one.strip() for one in value.split(",") if one.strip()]
    if not wanted:
        raise ValueError("--query-positions was given no Segment name")

    unknown = [one for one in wanted if one not in available]
    if unknown:
        raise ValueError(
            f"--query-positions names {', '.join(unknown)}, which "
            f"{'is' if len(unknown) == 1 else 'are'} not a Segment of this "
            f"task. Its Segments are: {', '.join(available)}")
    return wanted


def level_of(record: dict, split: str) -> str:
    """Which level of `--split` this instance belongs to."""
    factors = SPLITS[split]
    if not factors:
        return ALL_LEVEL
    values = []
    for factor in factors:
        value = record.get(factor)
        values.append(UNKNOWN_LEVEL if value is None else str(value))
    return "|".join(values)


# ==============================================================================
# SEGMENTS AS TENSORS
# ==============================================================================

def segment_ids(segmentation, names: Sequence[str],
                n_positions: int) -> torch.Tensor:
    """`[n_positions]`, the index into `names` of the Segment holding each token.

    `-1` where no Segment does, which on a padded batch is every position past
    the prompt. The default Segments partition the prompt, so inside it every
    token has exactly one owner; an override may overlap, and the last name in
    `names` order wins, which `validate_segmentation` has already reported.
    """
    ids = torch.full((n_positions,), -1, dtype=torch.long)
    for index, name in enumerate(names):
        segment = segmentation.segments.get(name)
        if segment is None:
            continue
        for start, end in segment.spans:
            if start < n_positions:
                ids[start:min(end, n_positions)] = index
    return ids


def segment_id_batch(segmentations: Sequence, names: Sequence[str],
                     n_positions: int) -> torch.Tensor:
    """`[batch, n_positions]` of `segment_ids`, one row per instance."""
    return torch.stack([segment_ids(one, names, n_positions)
                        for one in segmentations])


def query_slots(segmentations: Sequence, query_names: Sequence[str]):
    """`(positions [batch, K], valid [batch, K], slots)` for one batch.

    A query Segment is a span, and a span is a different width on different
    instances, so every query Segment gets as many columns as its widest
    instance in the batch and the narrower rows are padded with position 0 and
    marked invalid. `slots` names each column as `(Segment, k-th token)`, which
    is what the caller averages over.
    """
    per_name = []
    for name in query_names:
        tokens = [one.segments[name].token_indices()
                  if name in one.segments else [] for one in segmentations]
        per_name.append((name, tokens, max((len(t) for t in tokens), default=0)))

    slots = [(name, k) for name, _tokens, width in per_name
             for k in range(width)]
    positions = torch.zeros((len(segmentations), len(slots)), dtype=torch.long)
    valid = torch.zeros((len(segmentations), len(slots)), dtype=torch.bool)

    column = 0
    for _name, tokens, width in per_name:
        for k in range(width):
            for row, owned in enumerate(tokens):
                if k < len(owned):
                    positions[row, column] = owned[k]
                    valid[row, column] = True
            column += 1
    return positions, valid, slots


def masses_from_rows(rows: torch.Tensor, ids: torch.Tensor, *, n_segments: int):
    """`(masses [batch, heads, queries, n_segments], outside [batch, heads, queries])`.

    `rows` are attention rows over key positions and `ids` says which Segment
    each key position belongs to. Mass on a position no Segment claims — the
    padding past the prompt — is returned separately rather than folded into a
    Segment: pooled into one it would still sum to one and the profile would
    be wrong.
    """
    rows = rows.float()
    batch, heads, queries, keys = rows.shape
    if ids.shape != (batch, keys):
        raise ValueError(f"segment ids are {tuple(ids.shape)} for attention "
                         f"rows over {batch} instance(s) and {keys} key "
                         f"position(s)")

    # The sentinel bucket sits one past the last Segment, so scatter_add can do
    # the whole thing in one pass and "outside" is just its column.
    bucket = ids.masked_fill(ids < 0, n_segments)
    index = bucket.view(batch, 1, 1, keys).expand(batch, heads, queries, keys)
    out = torch.zeros((batch, heads, queries, n_segments + 1),
                      dtype=rows.dtype, device=rows.device)
    out.scatter_add_(-1, index.to(rows.device), rows)
    return out[..., :n_segments], out[..., n_segments]


# ==============================================================================
# ONE BATCH THROUGH THE MODEL
# ==============================================================================

def batch_masses(model, input_ids, attention_mask, *, heads_by_layer,
                 positions, ids, n_segments, rows_out: Optional[dict] = None):
    """`({(layer, head): [batch, queries, n_segments]}, checks)` for one batch.

    One `hooks.attention_weights` call per layer, carrying every circuit head
    of that layer and every query position at once: the call is a whole forward
    pass, so a call per head would multiply the cost of the analysis by the
    number of heads in the layer. Eager attention is switched on and SDPA
    restored inside that call, so it is the only thing here that knows about
    nnsight.

    `checks` reports how far a row was from summing to one and how much mass
    landed outside the segmentation. Both are written into the output: on a
    bfloat16 model a row sums to one only to about 1e-2, so a reader needs the
    number rather than a promise.

    `rows_out`, when given, receives each head's raw rows `[batch, queries,
    keys]` on the CPU: the token-level rendering is read from them, so it
    costs no forward pass of its own.
    """
    from component_analysis import hooks

    masses: Dict[Tuple[int, int], torch.Tensor] = {}
    worst_sum, worst_outside = 0.0, 0.0
    for layer in sorted(heads_by_layer):
        heads = sorted(heads_by_layer[layer])
        rows = hooks.attention_weights(model, input_ids, attention_mask,
                                       layer=layer, heads=heads,
                                       query_positions=positions)
        per_segment, outside = masses_from_rows(rows, ids.to(rows.device),
                                                n_segments=n_segments)
        total = per_segment.sum(-1) + outside
        worst_sum = max(worst_sum, float((total - 1.0).abs().max()))
        worst_outside = max(worst_outside, float(outside.max()))
        for column, head in enumerate(heads):
            masses[(layer, head)] = per_segment[:, column].cpu()
            if rows_out is not None:
                rows_out[(layer, head)] = rows[:, column].float().cpu()
    return masses, {"max_abs_sum_minus_one": worst_sum,
                    "max_outside": worst_outside}


def top_segment(profile: Dict[str, float]):
    """`(Segment, mass)` of the Segment holding the most mass, or `(None, None)`.

    Empty when no instance stood behind the profile — a condition that did not
    run, or a query Segment absent from every instance — which is a different
    thing from a head that attends nowhere and is spelled differently.
    """
    if not profile:
        return (None, None)
    name = max(profile, key=lambda one: profile[one])
    return (name, profile[name])


# ==============================================================================
# ACCUMULATING OVER A SPLIT
# ==============================================================================

def component_key_name(key) -> str:
    """A Component key as the string the JSON and the figures use."""
    kind, layer, index = key
    return f"{kind}.{layer}.{index}"


def head_label(key) -> str:
    """`L5H12`, which is how the researcher reads a head off a plot."""
    _kind, layer, index = key
    return f"L{layer}H{index}"


class Profiles:
    """Running mean attention mass per level, head, query Segment and Segment.

    Every instance contributes equally: a query Segment spanning several tokens
    is averaged within the instance first, then across instances. Pooling the
    tokens instead would weight an instance by how many tokens its Pressure
    Clause happens to take.
    """

    def __init__(self, head_keys, names, query_names):
        self.head_keys = list(head_keys)
        self.names = list(names)
        self.query_names = list(query_names)
        self._sums: Dict[tuple, torch.Tensor] = {}
        self._counts: Dict[tuple, int] = {}
        self._absent: Dict[tuple, int] = {}

    def add(self, masses, levels, positions_valid, slots):
        """One batch: `masses` is `{(layer, head): [batch, slots, segments]}`."""
        stacked = torch.stack([masses[(key[1], key[2])]
                               for key in self.head_keys], dim=1)
        for query in self.query_names:
            columns = [i for i, (name, _k) in enumerate(slots) if name == query]
            if not columns:
                # This Segment is absent from every instance of the batch, so
                # every instance counts as absent — but each level counts only
                # its own rows. Adding the whole batch to each would tell a
                # reader that `identity` and `inversion` each lost as many
                # instances as the two together.
                for level in {one for row in levels for one in row}:
                    self._absent[(level, query)] = (
                        self._absent.get((level, query), 0)
                        + sum(1 for row in levels if level in row))
                continue
            weight = positions_valid[:, columns].float()
            denominator = weight.sum(1)
            per_instance = (stacked[:, :, columns, :]
                            * weight[:, None, :, None]).sum(2)
            per_instance = per_instance / denominator[:, None, None].clamp(min=1)
            for row, row_levels in enumerate(levels):
                for level in row_levels:
                    key = (level, query)
                    if denominator[row] == 0:
                        self._absent[key] = self._absent.get(key, 0) + 1
                        continue
                    if key not in self._sums:
                        self._sums[key] = torch.zeros_like(per_instance[row])
                        self._counts[key] = 0
                    self._sums[key] += per_instance[row]
                    self._counts[key] += 1

    @property
    def levels(self) -> List[str]:
        """Every level seen, the unsplit one first."""
        seen = {level for level, _query in
                list(self._sums) + list(self._absent)}
        rest = sorted(seen - {ALL_LEVEL})
        return ([ALL_LEVEL] if ALL_LEVEL in seen else []) + rest

    def n(self, level: str) -> int:
        """Instances behind this level, counted at the first query Segment."""
        return max((self._counts.get((level, query), 0)
                    for query in self.query_names), default=0)

    def as_json(self) -> List[dict]:
        out = []
        for level in self.levels:
            masses: Dict[str, Dict[str, Dict[str, float]]] = {}
            for position, key in enumerate(self.head_keys):
                per_query = {}
                for query in self.query_names:
                    total = self._sums.get((level, query))
                    count = self._counts.get((level, query), 0)
                    if total is None or count == 0:
                        continue
                    mean = (total[position] / count).tolist()
                    per_query[query] = dict(zip(self.names, mean))
                masses[component_key_name(key)] = per_query
            out.append({
                "level": level,
                "n": self.n(level),
                "n_by_query_position": {
                    query: self._counts.get((level, query), 0)
                    for query in self.query_names},
                "n_absent_by_query_position": {
                    query: self._absent.get((level, query), 0)
                    for query in self.query_names},
                "masses": masses,
            })
        return out


# ==============================================================================
# THE THREE CONDITIONS
# ==============================================================================

@dataclass
class Slice:
    """The rows of one batch a condition actually reads, and their Segments.

    A dataclass for the same reason `dataloaders.Batch` is one: it carries
    aligned tensors and lists and nothing else, and every row of it belongs to
    the same instance at the same index.
    """

    input_ids: "torch.Tensor"
    attention_mask: "torch.Tensor"
    records: List[dict]
    segmentations: List

    def __len__(self) -> int:
        return len(self.records)


def by_record_id(segmentations) -> dict:
    return {one.record_id: one for one in segmentations}


def pressure_slices(batches, segmentations, missing: List[str]):
    """The whole split under the Pressure Clause, its Segments already resolved.

    An instance the loader has but the cell's `segmentation.json` does not is
    named in `missing` rather than skipped silently: it means the two were
    built from different views of the split (`--test-samples` shrinks one and
    not the other), which a reader of the n must know about.
    """
    known = by_record_id(segmentations)
    for batch in batches:
        rows = [row for row, one in enumerate(batch.ids) if one in known]
        missing.extend(one for one in batch.ids if one not in known)
        if not rows:
            continue
        yield Slice(batch.input_ids[rows], batch.attention_mask[rows],
                    [batch.records[row] for row in rows],
                    [known[batch.ids[row]] for row in rows])


def paired_rows(batch, known: dict) -> List[int]:
    """The rows of `batch` that have an Honest-Instruction Counterfactual *and*
    a resolved segmentation — the batch's share of the paired instance ids.

    Both paired conditions select their rows through this one function, so the
    left and the right term of the pair cannot drift onto different instances.
    That they do not is the whole meaning of "paired"; a helper is cheaper than
    a comment asking two loops to stay in step.
    """
    if batch.honest is None:
        return []
    return [row for row in batch.honest.rows if batch.ids[row] in known]


def pressure_paired_slices(batches, segmentations):
    """The *pressure* prompts of the instances that have an honest counterpart.

    The left term of the paired contrast. It exists for the reason
    `dla.PRESSURE_PAIRED` does: the `pressure` condition is profiled over the
    whole test split, so subtracting the paired honest profile from it would be
    a difference between two populations. This is the same instances, under the
    Pressure Clause, and it is what the paired honest column is read against.
    """
    known = by_record_id(segmentations)
    for batch in batches:
        rows = paired_rows(batch, known)
        if not rows:
            continue
        yield Slice(batch.input_ids[rows], batch.attention_mask[rows],
                    [batch.records[row] for row in rows],
                    [known[batch.ids[row]] for row in rows])


def honest_instruction_slices(batches, segmentations, report: dict):
    """The paired Honest-Instruction Counterfactual of the sampled instances.

    The honest prompt reuses its pressure prompt's Segments, which is sound
    exactly when the two differ only inside the Pressure Clause — that is what
    `assert_clause_aligned_pair` promised at build time and what is re-checked
    here, per instance, by diffing the token ids. An instance that fails is
    counted into the report rather than raising, so one drifted pool entry is a
    number in the output instead of a lost GPU job.
    """
    known = by_record_id(segmentations)
    for batch in batches:
        rows = paired_rows(batch, known)
        if not rows:
            continue
        keep = [batch.honest.rows.index(row) for row in rows]
        input_ids = batch.honest.input_ids[keep]
        resolved = [known[batch.ids[row]] for row in rows]
        differs = input_ids != batch.input_ids[rows]
        for position, one in enumerate(resolved):
            clause = set(one.segments["pressure_clause"].token_indices())
            changed = differs[position].nonzero().flatten().tolist()
            report["n_pairs"] += 1
            if not changed:
                report["n_identical_to_pressure"] += 1
            elif not set(changed) <= clause:
                report["n_differing_outside_the_clause"] += 1
                report["examples_outside_the_clause"] = (
                    report["examples_outside_the_clause"] + [one.record_id])[:5]
        yield Slice(input_ids, batch.honest.attention_mask[keep],
                    [batch.records[row] for row in rows], resolved)


def paired_batches(ctx) -> Tuple[Optional[object], Optional[str]]:
    """`(the causal sample, reason the paired condition cannot run)`.

    A sample whose instances have no Matched Honest Instruction is a skipped
    condition with a reason, not a condition whose every profile is empty: the
    two look the same in a plot and mean completely different things.
    """
    from component_analysis import dataloaders

    try:
        causal = ctx.causal_batches()
    except dataloaders.LoaderUnavailable as unavailable:
        return None, str(unavailable)
    report = causal.report
    if report["n_with_honest"]:
        return causal, None
    if report["honest_source"] == "absent":
        return None, (f"no Matched Honest survivors file beside the "
                      f"{report['task']} dataset, so no Honest-Instruction "
                      f"Counterfactual exists for this task")
    return None, (f"none of the {report['n_instances']} sampled instance(s) "
                  f"has a Matched Honest Instruction under the "
                  f"{report['honest_streams']} criterion")


def honest_twin_dir(ctx) -> Tuple[Optional[str], Optional[str]]:
    """`(directory, reason it cannot run)` for the unpaired honest twin."""
    from component_analysis import instances as ca_instances

    setting = getattr(ctx.cli, "attention_honest_twin", "auto")
    if setting == "off":
        return None, "--attention-honest-twin off"
    if setting != "auto":
        directory = setting
    else:
        directory = ca_instances.dataset_dir(ctx.task_spec) + "_honest"
    if not os.path.isdir(directory):
        return None, (f"no honest-twin dataset at {directory}; bind one with "
                      f"--attention-honest-twin DIR or pass 'off'")
    return directory, None


def twin_slices(batches, ctx, overrides, resolved_out: List):
    """The honest twin's own instances, with their own Segments.

    The twin is a *different* dataset, so its prompts get their own resolved
    and validated segmentation rather than borrowing the pressure split's, and
    that segmentation is written beside the results for the same reason the
    cell writes its own (spec user story 10).
    """
    from component_analysis import instances as ca_instances

    for batch in batches:
        segmentations, _report = ca_instances.resolve_split_segmentation(
            ctx.task_spec.name, batch.records, ctx.tokenizer,
            overrides=overrides, ids=batch.ids)
        resolved_out.extend(segmentations)
        yield Slice(batch.input_ids, batch.attention_mask, batch.records,
                    segmentations)


# ==============================================================================
# ONE CONDITION, END TO END
# ==============================================================================

def collect_condition(ctx, slices, *, head_keys, names, query_names, split,
                      heads_by_layer, tokens: Optional["TokenProfiles"] = None,
                      condition: Optional[str] = None) -> Tuple[Profiles, dict]:
    """Every batch of one condition through the model, into one `Profiles`.

    The ids of the instances actually profiled are collected alongside, into
    `checks["instance_ids"]`, as `dla.json` records them per condition. Without
    them a reader of `patterns.json` — and a test — can compare two conditions'
    instance *counts* but not their instance *ids*, so "paired" would be a
    property of the code path rather than of the file (spec user stories 28 and
    43).

    With `tokens`, the same rows also feed the token-level rendering under
    `condition`'s name.
    """
    from component_analysis import hooks

    device, _dtype = hooks.device_and_dtype(ctx.model)
    profiles = Profiles(head_keys, names, query_names)
    checks = {"max_abs_sum_minus_one": 0.0, "max_outside": 0.0, "n_batches": 0,
              "instance_ids": []}

    for one in slices:
        if not len(one):
            continue
        checks["instance_ids"].extend(
            segment.record_id for segment in one.segmentations)
        positions, valid, slots = query_slots(one.segmentations, query_names)
        ids = segment_id_batch(one.segmentations, names, one.input_ids.shape[1])
        rows = {} if tokens is not None else None
        masses, batch_checks = batch_masses(
            ctx.model, one.input_ids.to(device), one.attention_mask.to(device),
            heads_by_layer=heads_by_layer, positions=positions, ids=ids,
            n_segments=len(names), rows_out=rows)
        if tokens is not None:
            tokens.add(condition, one, rows, valid, slots)
        levels = []
        for record in one.records:
            row = [ALL_LEVEL]
            level = level_of(record, split)
            if level != ALL_LEVEL:
                row.append(level)
            levels.append(row)
        profiles.add(masses, levels, valid, slots)
        checks["max_abs_sum_minus_one"] = max(
            checks["max_abs_sum_minus_one"], batch_checks["max_abs_sum_minus_one"])
        checks["max_outside"] = max(checks["max_outside"],
                                    batch_checks["max_outside"])
        checks["n_batches"] += 1
    return profiles, checks


def count_nan(levels: List[dict]) -> int:
    return sum(1 for level in levels
               for per_query in level["masses"].values()
               for profile in per_query.values()
               for value in profile.values()
               if value is None or math.isnan(value))


# ==============================================================================
# FIGURES
# ==============================================================================

def colormap():
    """`COLORMAP` as a matplotlib colormap whose missing cells are transparent,
    so `show_missing_as_hatching` shows through them."""
    import matplotlib

    return matplotlib.colormaps[COLORMAP].with_extremes(bad=(0.0, 0.0, 0.0, 0.0))


def show_missing_as_hatching(axis) -> None:
    """Grey hatching behind an image, visible only where a cell is missing."""
    axis.patch.set_facecolor("white")
    axis.patch.set_hatch(MISSING_HATCH)
    axis.patch.set_edgecolor(MISSING_HATCH_COLOUR)


def bar_colour():
    """One colour from `COLORMAP` for bar charts: dark enough to read against
    white, and from the same warm family as every heatmap beside it."""
    import matplotlib

    return matplotlib.colormaps[COLORMAP](0.75)


def figure_name(stem: str, level: str) -> str:
    """A filename for one split level. `both` levels are `inversion|1`, and a
    pipe is a shell metacharacter, so it becomes a dash on disk."""
    return f"{stem}_{level.replace('|', '-')}"


def level_matrix(level: dict, component_names: Sequence[str],
                 segment_names: Sequence[str], query: str) -> List[List[float]]:
    """`[head][segment]` of one level's masses, NaN where a head has no profile."""
    rows = []
    for name in component_names:
        profile = level.get("masses", {}).get(name, {}).get(query) or {}
        rows.append([profile.get(one, float("nan")) for one in segment_names])
    return rows


def _levels_of(condition: dict) -> Dict[str, dict]:
    return {level["level"]: level for level in condition["levels"]}


def write_heatmaps(ctx, payload: dict) -> List[str]:
    """One heatmap per split level: heads by Segment, one panel per condition.

    The conditions share a level's figure rather than getting one each, because
    the question the researcher asks of them is a comparison — does this head
    read the same thing when the pressure is gone — and a comparison across
    files is a comparison nobody makes.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    segment_names = payload["segments"]
    component_names = [one["name"] for one in payload["components"]]
    labels = [one["label"] for one in payload["components"]]
    query = payload["column_query_position"]

    seen: List[str] = []
    for condition in payload["conditions"]:
        for level in condition["levels"]:
            if level["level"] not in seen:
                seen.append(level["level"])
    ordered = ([ALL_LEVEL] if ALL_LEVEL in seen else []) + sorted(
        one for one in seen if one != ALL_LEVEL)

    written = []
    for level_name in ordered:
        panels = [(condition, _levels_of(condition)[level_name])
                  for condition in payload["conditions"]
                  if level_name in _levels_of(condition)]
        if not panels:
            continue
        matrices = [level_matrix(level, component_names, segment_names, query)
                    for _condition, level in panels]
        figure, axes = plt.subplots(
            1, len(panels), squeeze=False, constrained_layout=True,
            figsize=(max(6.0, 0.55 * len(segment_names)) * len(panels),
                     max(3.0, 0.32 * len(labels)) + 2.4))
        for column, ((condition, level), matrix) in enumerate(zip(panels, matrices)):
            axis = axes[0][column]
            image = axis.imshow(matrix, aspect="auto", vmin=0.0, vmax=1.0,
                                cmap=colormap())
            show_missing_as_hatching(axis)
            axis.set_xticks(range(len(segment_names)))
            axis.set_xticklabels(segment_names, rotation=90, fontsize=7)
            axis.set_yticks(range(len(labels)))
            axis.set_yticklabels(labels, fontsize=7)
            axis.set_title(f"{condition['name']} ({condition['kind']})\n"
                           f"n={level['n']}", fontsize=9)
            figure.colorbar(image, ax=axis, fraction=0.03)
        figure.suptitle(
            f"Attention mass by Segment at {query} — {payload['circuit']} x "
            f"{payload['task']} — split {payload['split']}, level {level_name}",
            fontsize=10)
        stem = figure_name("patterns", level_name)
        path = os.path.join(ctx.subdir(SUBDIR), stem + ".png")
        figure.savefig(path, dpi=150)
        plt.close(figure)
        ctx.write_json(SUBDIR, stem + ".json", {
            "figure": stem + ".png",
            "shows": f"attention mass per Segment at {query}",
            "colormap": COLORMAP,
            "value_range": [0.0, 1.0],
            "level": level_name,
            "query_position": query,
            "rows": labels,
            "columns": segment_names,
            "panels": [{"condition": condition["name"],
                        "kind": condition["kind"],
                        "paired": condition["paired"],
                        "n": level["n"],
                        "matrix": matrix}
                       for (condition, level), matrix in zip(panels, matrices)],
        })
        written.append(path)
    return written


def rank_heads(ctx, payload: dict) -> Tuple[List[str], str]:
    """The heads the bar chart shows, most interesting first, and why.

    By knockout rank when the cell's head table already carries a knockout
    column (ticket 07 runs after this one, so that is a second run over the
    same cell), and by layer when it does not — which is the order the circuit
    itself is written in, not a ranking pretending to be one.
    """
    from component_analysis import head_table

    names = [one["name"] for one in payload["components"]]
    column = getattr(ctx.cli, "attention_rank_column", None)
    try:
        rows = head_table.load_head_table(ctx.cell_dir)
    except (OSError, ValueError):
        rows = []
    available = {name for row in rows for name in row}
    if column is None:
        knockout = sorted(one for one in available if one.startswith("knockout."))
        column = next((one for one in knockout if "rank" in one),
                      knockout[0] if knockout else None)
    if column is None or column not in available:
        return names, "layer order (no knockout column in this cell's head table)"

    ascending = "rank" in column
    by_name = {component_key_name(head_table.row_key(row)): row for row in rows}

    def sort_key(name):
        value = by_name.get(name, {}).get(column)
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return (1, 0.0)
        return (0, float(value) if ascending else -abs(float(value)))

    return sorted(names, key=sort_key), f"{column} ({'ascending' if ascending else 'largest magnitude first'})"


def write_top_heads(ctx, payload: dict) -> Optional[str]:
    """A per-head bar chart over Segments for the top-k heads."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not payload["conditions"]:
        return None
    condition = payload["conditions"][0]
    levels = _levels_of(condition)
    if ALL_LEVEL not in levels:
        return None
    level = levels[ALL_LEVEL]
    segment_names = payload["segments"]
    query = payload["column_query_position"]
    labels = {one["name"]: one["label"] for one in payload["components"]}

    ordered, how = rank_heads(ctx, payload)
    top_k = max(1, int(getattr(ctx.cli, "attention_top_k", 8) or 8))
    shown = ordered[:top_k]
    rows = level_matrix(level, shown, segment_names, query)

    figure, axes = plt.subplots(
        len(shown), 1, squeeze=False, constrained_layout=True,
        figsize=(max(6.0, 0.45 * len(segment_names)), 1.6 * len(shown) + 1.2))
    for position, (name, values) in enumerate(zip(shown, rows)):
        axis = axes[position][0]
        axis.bar(range(len(segment_names)), values, color=bar_colour())
        axis.set_ylim(0.0, 1.0)
        axis.set_ylabel(labels.get(name, name), fontsize=8)
        axis.tick_params(labelsize=7)
        if position == len(shown) - 1:
            axis.set_xticks(range(len(segment_names)))
            axis.set_xticklabels(segment_names, rotation=90, fontsize=7)
        else:
            axis.set_xticks([])
    figure.suptitle(f"{condition['name']} attention at {query}, top "
                    f"{len(shown)} head(s) by {how}", fontsize=10)
    path = os.path.join(ctx.subdir(SUBDIR), "top_heads.png")
    figure.savefig(path, dpi=150)
    plt.close(figure)
    ctx.write_json(SUBDIR, "top_heads.json", {
        "figure": "top_heads.png",
        "shows": f"{condition['name']} attention mass per Segment at {query}",
        "colormap": COLORMAP,
        "condition": condition["name"],
        "level": ALL_LEVEL,
        "query_position": query,
        "ranked_by": how,
        "rows": [labels.get(one, one) for one in shown],
        "columns": segment_names,
        "matrix": rows,
    })
    return path


# ==============================================================================
# TOKEN BY TOKEN
# ==============================================================================
#
# `--attention-token-level`: per circuit head, the mean attention from the
# query positions to every token of the prompt, with no Segment summing. It is
# read from the same attention rows as the Segment masses, so it costs no
# forward pass of its own.
#
# Prompts differ in length, so a mean over "position 37" would average
# different words. Instances are therefore grouped by Template Variant (and,
# within one, by the order of the Segment runs their tokens fall into, which on
# the saved SDR split is one order per variant), and a token's place is its
# run and its offset in that run, counted from whichever end of the run is
# nearer. A run that is the same width everywhere — the chat shell, the
# Designation Positions, the question, the stem — then lines up token for
# token; a run that varies (the intro around the entity name, the Pressure
# Clause) lines up at both ends and is ragged only in its middle. The Segments
# are used to line tokens up, never to sum them.
#
# Each slot's value is its summed attention divided by the group's instance
# count, so an instance with no token at a slot contributes nothing there,
# which is literally what it attended to. Every row then sums to one, and a
# Segment's tokens sum back to its mass in `patterns.json`.

#: Where the token-level files go, inside `attention/`.
TOKEN_LEVEL_SUBDIR = "token_level"
#: The cell's one token-level index: layout, labels, instance ids, colour scale.
TOKEN_LEVEL_INDEX = "token_level.json"
#: `<stem>_<head label>.png` and its JSON twin, one per circuit head.
TOKEN_LEVEL_STEM = "token_level"

#: The per-head JSON twins carry their values only while all of them together
#: stay under this many bytes per cell; above it every per-head twin is written
#: meta-only (shape, where the instance ids are, how to regenerate) and the
#: PNGs are the record. On SDR nls0.3 the full twins are about 1 MB.
TOKEN_LEVEL_JSON_LIMIT_BYTES = 5_000_000

#: The token-level colour scale: `COLORMAP` through a square-root norm on 0..1.
#: Most of a head's mass sits on a few tokens (on Llama, often the
#: `<|begin_of_text|>` sink) and the rest is spread thin over a hundred, so a
#: linear scale draws everything but the sink at the palest colour. The square
#: root keeps one fixed scale for every head and every cell, so two PNGs can be
#: compared by eye, while a mass of 0.01 is a tenth of the way up the map.
TOKEN_LEVEL_GAMMA = 0.5
TOKEN_LEVEL_SCALE = {"norm": "power", "gamma": TOKEN_LEVEL_GAMMA,
                     "vmin": 0.0, "vmax": 1.0}

#: Colour-bar ticks, so a reader of the square-root scale can read a mass off it.
TOKEN_LEVEL_TICKS = (0.0, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0)

#: How many of a row's largest tokens its twin names, largest first.
TOKEN_LEVEL_TOP = 8

#: The family of prompts a group's tokens come from. The three conditions on the
#: task's own prompts share groups and labels; the honest twin is a different
#: dataset and gets groups of its own.
PRESSURE_PROMPTS = "pressure"
TWIN_PROMPTS = "honest_twin"

#: The conditions whose prompts label the slots. Not the honest instruction:
#: its prompt is its pressure prompt with the clause replaced, so it reads the
#: pressure prompt's labels, and inside the Pressure Clause its own tokens are
#: the Matched Honest Instruction's rather than the label shown.
LABEL_CONDITIONS = (PRESSURE, PRESSURE_PAIRED, HONEST_TWIN)

#: Every condition, in the order rows are drawn.
TOKEN_LEVEL_ORDER = (PRESSURE, PRESSURE_PAIRED, HONEST_INSTRUCTION, HONEST_TWIN)

#: What a record says when it carries no `template_variant`.
NO_VARIANT = "-"

#: The run name of tokens no Segment claims. The default Segments partition the
#: prompt, so only an override that leaves gaps produces one.
UNCLAIMED_RUN = "unclaimed"


def segment_runs(segmentation, names: Sequence[str]) -> List[Tuple[str, int]]:
    """`[(Segment name, width)]`: the prompt as maximal runs of one Segment.

    Interleaved Segments (the intro around its two Item Mentions) are several
    runs, in prompt order. A token no Segment claims is a run named
    `UNCLAIMED_RUN`, which the default segmentation never produces.
    """
    ids = segment_ids(segmentation, names, segmentation.n_tokens).tolist()
    runs: List[List] = []
    for owner in ids:
        name = names[owner] if owner >= 0 else UNCLAIMED_RUN
        if runs and runs[-1][0] == name:
            runs[-1][1] += 1
        else:
            runs.append([name, 1])
    return [(name, width) for name, width in runs]


def run_slot_keys(runs: Sequence[Tuple[str, int]]) -> List[Tuple[int, str, int]]:
    """One slot key per token: `(run, side, offset)`, counted from the nearer end.

    The first half of a run of width w (rounded up) is `("L", k)` from its
    start and the rest `("R", k)` from its end, so two runs of different width
    agree on their first and last tokens and differ only in the middle.
    """
    keys = []
    for run, (_name, width) in enumerate(runs):
        left = (width + 1) // 2
        for k in range(width):
            keys.append((run, "L", k) if k < left
                        else (run, "R", width - 1 - k))
    return keys


#: Longest token label drawn on an axis; the twin keeps the whole string.
AXIS_LABEL_CHARS = 24


def axis_label(label: str) -> str:
    """A slot label cut to `AXIS_LABEL_CHARS`, so one long token cannot take
    the figure's height."""
    if len(label) <= AXIS_LABEL_CHARS:
        return label
    return label[:AXIS_LABEL_CHARS - 1] + "\u2026"


def display_token(text: str) -> str:
    """A token as an axis label: control characters visible, nothing else changed."""
    return text.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")


class TokenGroup:
    """Running sums for one group of prompts that share a token layout."""

    def __init__(self, family: str, variant: str, run_names: tuple, n_heads: int):
        self.family = family
        self.variant = variant
        self.run_names = run_names
        self.n_heads = n_heads
        self.widths = [[0, 0] for _ in run_names]          # [left, right] per run
        self.sums: Dict[tuple, Dict[tuple, "np.ndarray"]] = {}
        self.present: Dict[tuple, Dict[tuple, int]] = {}
        self.ids: Dict[tuple, List[str]] = {}
        self.tokens: Dict[tuple, Dict[int, int]] = {}
        self.labelled: set = set()

    def add(self, row_key, record_id, slot_keys, values, token_ids, *, label):
        """One instance: `values` is `[heads, n_tokens]` of this instance's mean
        attention from the query position, `token_ids` its prompt."""
        sums = self.sums.setdefault(row_key, {})
        present = self.present.setdefault(row_key, {})
        self.ids.setdefault(row_key, []).append(record_id)
        for position, key in enumerate(slot_keys):
            run, side, offset = key
            width = self.widths[run]
            column = 0 if side == "L" else 1
            width[column] = max(width[column], offset + 1)
            if key in sums:
                sums[key] = sums[key] + values[:, position]
            else:
                sums[key] = values[:, position].copy()
            present[key] = present.get(key, 0) + 1
        if label and record_id not in self.labelled:
            self.labelled.add(record_id)
            for position, key in enumerate(slot_keys):
                counts = self.tokens.setdefault(key, {})
                token = int(token_ids[position])
                counts[token] = counts.get(token, 0) + 1

    def slots(self) -> List[tuple]:
        """Every slot key in prompt order: a run's left half, then its right."""
        out = []
        for run, (left, right) in enumerate(self.widths):
            out += [(run, "L", k) for k in range(left)]
            out += [(run, "R", k) for k in reversed(range(right))]
        return out


class TokenProfiles:
    """Token-level means for every condition, grouped by token layout."""

    def __init__(self, head_keys, names, query_names):
        self.head_keys = list(head_keys)
        self.names = list(names)
        self.query_names = list(query_names)
        self.groups: Dict[tuple, TokenGroup] = {}

    def add(self, condition: str, one: "Slice", rows: dict, positions_valid,
            slots) -> None:
        """One batch of one condition. `rows` is `{(layer, head): [batch,
        query slots, keys]}`, the raw attention rows of this batch."""
        stacked = torch.stack([rows[(key[1], key[2])] for key in self.head_keys],
                              dim=1).float()          # [batch, heads, slots, keys]
        family = TWIN_PROMPTS if condition == HONEST_TWIN else PRESSURE_PROMPTS
        label = condition in LABEL_CONDITIONS
        for row, (record, segmentation) in enumerate(
                zip(one.records, one.segmentations)):
            n_tokens = segmentation.n_tokens
            runs = segment_runs(segmentation, self.names)
            variant = str(record.get("template_variant") or NO_VARIANT)
            names = tuple(name for name, _width in runs)
            group = self.groups.get((family, variant, names))
            if group is None:
                group = self.groups[(family, variant, names)] = TokenGroup(
                    family, variant, names, len(self.head_keys))
            keys = run_slot_keys(runs)
            token_ids = one.input_ids[row, :n_tokens].tolist()
            for query in self.query_names:
                columns = [i for i, (name, _k) in enumerate(slots)
                           if name == query and bool(positions_valid[row, i])]
                if not columns:
                    continue
                values = stacked[row][:, columns, :n_tokens].mean(1).numpy()
                group.add((condition, query), segmentation.record_id, keys,
                          values, token_ids, label=label)

    def ordered_groups(self) -> List[Tuple[str, TokenGroup]]:
        """`[(group id, group)]`: the task's prompts first, larger groups first.

        A group id is `<family>/<template variant>`, with `#2`, `#3` after it
        when one variant holds more than one token layout.
        """
        def size(group):
            return max((len(ids) for ids in group.ids.values()), default=0)

        out, seen = [], {}
        for family in (PRESSURE_PROMPTS, TWIN_PROMPTS):
            members = sorted((group for group in self.groups.values()
                              if group.family == family),
                             key=lambda group: (-size(group), group.variant))
            for group in members:
                base = f"{family}/{group.variant}"
                seen[base] = seen.get(base, 0) + 1
                out.append((base if seen[base] == 1 else f"{base}#{seen[base]}",
                            group))
        return out


def _row_keys(group: TokenGroup, query_names) -> List[tuple]:
    present = set(group.sums)
    return [(condition, query) for condition in TOKEN_LEVEL_ORDER
            for query in query_names if (condition, query) in present]


def _row_label(row_key, n: int, query_names) -> str:
    condition, query = row_key
    where = f" @ {query}" if len(query_names) > 1 else ""
    return f"{condition}{where} (n={n})"


def token_level_payloads(tokens: TokenProfiles, tokenizer, *, labels) -> Tuple[dict, dict]:
    """`(index, {head label: full twin})` — everything the figures are drawn from.

    The index holds what every head shares: each group's slots, their labels
    and Segments, and which instances stand behind each row. A head's twin
    holds its values and its largest tokens per row.
    """
    decoded: Dict[int, str] = {}

    def decode(token: int) -> str:
        if token not in decoded:
            decoded[token] = display_token(tokenizer.decode([token]))
        return decoded[token]

    index_groups, panels_by_head = [], {label: [] for label in labels}
    for group_id, group in tokens.ordered_groups():
        slots = group.slots()
        row_keys = _row_keys(group, tokens.query_names)
        slot_tokens, slot_share, slot_labels = [], [], []
        slot_segments = [group.run_names[key[0]] for key in slots]
        for key in slots:
            counts = group.tokens.get(key, {})
            total = sum(counts.values())
            if not counts:
                slot_tokens.append(None)
                slot_share.append(0.0)
                slot_labels.append("?")
                continue
            token, count = max(counts.items(), key=lambda item: (item[1], -item[0]))
            share = count / total
            slot_tokens.append(decode(token))
            slot_share.append(share)
            slot_labels.append(decode(token) if share == 1.0
                               else f"{decode(token)} ({share:.0%})")
        rows_meta = []
        for row_key in row_keys:
            n = len(group.ids[row_key])
            rows_meta.append({
                "condition": row_key[0], "query_position": row_key[1],
                "label": _row_label(row_key, n, tokens.query_names),
                "n_instances": n, "instance_ids": list(group.ids[row_key]),
                "n_present": [group.present[row_key].get(key, 0) for key in slots]})
        title = (f"{'honest-twin' if group.family == TWIN_PROMPTS else 'task'} "
                 f"prompts, template variant {group.variant}: averaged over "
                 + ", ".join(f"{meta['n_instances']} ({meta['condition']})"
                             for meta in rows_meta) + " instance(s)")
        index_groups.append({
            "group": group_id, "family": group.family,
            "template_variant": group.variant, "title": title,
            "n_slots": len(slots),
            "slot_labels": slot_labels, "slot_tokens": slot_tokens,
            "slot_token_share": slot_share,
            "slot_segments": slot_segments,
            "rows": rows_meta})
        for position, label in enumerate(labels):
            rows = []
            for row_key, meta in zip(row_keys, rows_meta):
                n = meta["n_instances"]
                sums = group.sums[row_key]
                values = [float(sums[key][position]) / n if key in sums else 0.0
                          for key in slots]
                top = sorted(range(len(values)), key=lambda i: -values[i])
                rows.append({
                    "condition": row_key[0], "query_position": row_key[1],
                    "label": meta["label"], "n_instances": n, "values": values,
                    "top_tokens": [{"slot": i, "token": slot_labels[i],
                                    "segment": slot_segments[i],
                                    "mass": values[i]}
                                   for i in top[:TOKEN_LEVEL_TOP]]})
            panels_by_head[label].append({"group": group_id, "title": title,
                                          "rows": rows})
    index = {"groups": index_groups}
    return index, panels_by_head


def plot_token_level(path: str, twin: dict, groups: Dict[str, dict]) -> None:
    """One head: a panel per group, a row per condition, a column per token."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import PowerNorm

    panels = twin["panels"]
    widest = max((groups[panel["group"]]["n_slots"] for panel in panels),
                 default=1)
    # Room under each panel for its rotated token labels, from the longest one:
    # about 0.6 of the font size per character, at 5.5 pt.
    labels_of = {panel["group"]: [axis_label(one) for one in
                                  groups[panel["group"]]["slot_labels"]]
                 for panel in panels}
    heights = [0.3 * max(1, len(panel["rows"])) + 0.9
               + max((len(one) for one in labels_of[panel["group"]]), default=1)
               * 5.5 * 0.6 / 72.0
               for panel in panels]
    figure, axes = plt.subplots(
        max(1, len(panels)), 1, squeeze=False, constrained_layout=True,
        figsize=(max(8.0, 0.12 * widest + 3.0), sum(heights) + 0.8),
        gridspec_kw={"height_ratios": heights or [1.0]})
    norm = PowerNorm(gamma=TOKEN_LEVEL_GAMMA, vmin=0.0, vmax=1.0)
    for axis, panel in zip(axes[:, 0], panels):
        group = groups[panel["group"]]
        matrix = [row["values"] for row in panel["rows"]]
        image = axis.imshow(matrix, aspect="auto", cmap=colormap(), norm=norm,
                            interpolation="nearest")
        show_missing_as_hatching(axis)
        axis.set_xticks(range(group["n_slots"]))
        axis.set_xticklabels(labels_of[panel["group"]], rotation=90,
                             fontsize=5.5)
        axis.set_yticks(range(len(panel["rows"])))
        axis.set_yticklabels([row["label"] for row in panel["rows"]], fontsize=7)
        axis.set_title(panel["title"], fontsize=8)
        figure.colorbar(image, ax=axis, fraction=0.02, pad=0.01,
                        ticks=TOKEN_LEVEL_TICKS)
    figure.suptitle(twin["title"], fontsize=9)
    figure.savefig(path, dpi=150)
    plt.close(figure)


def write_token_level(ctx, tokens: TokenProfiles, payload: dict) -> dict:
    """Every head's PNG and twin, and the index; returns what `patterns.json`
    says about them."""
    subdir = os.path.join(SUBDIR, TOKEN_LEVEL_SUBDIR)
    directory = ctx.subdir(subdir)
    components = payload["components"]
    labels = [one["label"] for one in components]
    index, panels_by_head = token_level_payloads(tokens, ctx.tokenizer,
                                                 labels=labels)
    groups = {group["group"]: group for group in index["groups"]}
    queries = ", ".join(tokens.query_names)

    twins = {}
    for component in components:
        label = component["label"]
        twins[label] = {
            "figure": f"{TOKEN_LEVEL_STEM}_{label}.png",
            "shows": (f"{label}'s mean attention from {queries} to every "
                      f"token of the prompt, no Segment summing"),
            "title": (f"{label}: attention from {queries} to every token, "
                      f"mean over instances (n per row); colour "
                      f"{COLORMAP}, square-root scale 0 to 1"),
            "head": component["key"], "label": label,
            "colormap": COLORMAP, "colour_scale": TOKEN_LEVEL_SCALE,
            "index": TOKEN_LEVEL_INDEX, "payload": "full",
            "panels": panels_by_head[label]}
    full_bytes = sum(len(json.dumps(twin, indent=2)) for twin in twins.values())
    full = full_bytes <= TOKEN_LEVEL_JSON_LIMIT_BYTES
    regenerate = (
        "Rerun analyze_components.py into this cell with the circuit bindings "
        "recorded in head_table.json's meta and --analyses attention_patterns "
        "--attention-token-level, after raising "
        "attention_patterns.TOKEN_LEVEL_JSON_LIMIT_BYTES above full_twins_bytes. "
        "The PNGs are complete either way.")

    heads = []
    for component in components:
        label = component["label"]
        twin = twins[label]
        plot_token_level(os.path.join(directory, twin["figure"]), twin, groups)
        if not full:
            twin = {key: value for key, value in twin.items() if key != "panels"}
            twin.update(
                payload="meta-only",
                shape=[{"group": panel["group"], "rows": len(panel["rows"]),
                        "slots": groups[panel["group"]]["n_slots"]}
                       for panel in panels_by_head[label]],
                instance_ids=(f"in {TOKEN_LEVEL_INDEX}, under "
                              f"groups[].rows[].instance_ids"),
                json_limit_bytes=TOKEN_LEVEL_JSON_LIMIT_BYTES,
                full_twins_bytes=full_bytes, regenerate=regenerate)
        name = f"{TOKEN_LEVEL_STEM}_{label}.json"
        ctx.write_json(subdir, name, twin)
        heads.append({"key": component["key"], "label": label,
                      "figure": twin["figure"], "twin": name})

    ctx.write_json(subdir, TOKEN_LEVEL_INDEX, {
        "analysis": NAME, "schema_version": SCHEMA_VERSION,
        "task": payload["task"], "circuit": payload["circuit"],
        "shows": (f"mean attention from {queries} to every token of the "
                  f"prompt, per circuit head; one PNG per head"),
        "colormap": COLORMAP, "colour_scale": TOKEN_LEVEL_SCALE,
        "query_positions": list(tokens.query_names),
        "level": ALL_LEVEL,
        "alignment": ("instances grouped by template variant and Segment-run "
                      "order; a token's slot is its run and its offset from "
                      "the nearer end of that run, so runs of varying width "
                      "are ragged only in the middle"),
        "values": ("summed attention over the group's instances divided by "
                   "the group's instance count, so every row sums to one and a "
                   "Segment's slots sum to its mass in patterns.json; "
                   "n_present says how many instances have a token at a slot"),
        "labels": ("the most common token at the slot among the group's "
                   "pressure-prompt (or honest-twin) instances, with the share "
                   "carrying it when it is not all of them; the "
                   "honest_instruction row reads the pressure labels, and "
                   "inside the Pressure Clause its own tokens are the Matched "
                   "Honest Instruction's"),
        "payload": "full" if full else "meta-only",
        "json_limit_bytes": TOKEN_LEVEL_JSON_LIMIT_BYTES,
        "full_twins_bytes": full_bytes,
        "regenerate": regenerate,
        "heads": heads, **index})
    return {"index": f"{TOKEN_LEVEL_SUBDIR}/{TOKEN_LEVEL_INDEX}",
            "payload": "full" if full else "meta-only",
            "full_twins_bytes": full_bytes,
            "json_limit_bytes": TOKEN_LEVEL_JSON_LIMIT_BYTES,
            "n_heads": len(heads)}


# ==============================================================================
# HEAD-TABLE COLUMNS
# ==============================================================================

#: Each condition's head-table column prefix, in column order.
#:
#: The honest-twin columns carry `descriptive` in their own names and the two
#: paired ones carry `paired`, so a reader who sees only a CSV header cannot
#: mistake an unpaired population contrast for a causal one (block C's rule,
#: extended by the researcher's 2026-10-13 decision). `pressure_paired` is here
#: so that the paired honest column has a left term over the same instance ids;
#: `pressure` is the whole split and is not one.
COLUMN_PREFIXES = {
    PRESSURE: "pressure",
    PRESSURE_PAIRED: "pressure_paired",
    HONEST_INSTRUCTION: "honest_instruction_paired",
    HONEST_TWIN: "honest_twin_descriptive",
}

#: The instance set each condition's columns are read over, by name, for the
#: head table's coverage meta. The paired pair shares one: the same ids.
INSTANCE_SETS = {
    PRESSURE: ht.TEST_SPLIT,
    PRESSURE_PAIRED: ht.PAIRED_HONEST_INSTRUCTION,
    HONEST_INSTRUCTION: ht.PAIRED_HONEST_INSTRUCTION,
    HONEST_TWIN: ht.HONEST_TWIN_SPLIT,
}


def columns(payload: dict) -> dict:
    """`{component key: {column: value}}` — the top Segment per head.

    Every condition gets its columns whether or not it ran: a condition with no
    data leaves them empty rather than absent, because a head table whose
    columns differ from cell to cell cannot be concatenated and an absent
    column reads exactly like a head that attends nowhere.
    """
    query = payload["column_query_position"]
    by_condition = {condition["name"]: condition
                    for condition in payload["conditions"]}

    updates: Dict[tuple, Dict[str, object]] = {}
    for component in payload["components"]:
        key = tuple(component["key"])
        cells: Dict[str, object] = {"query_position": query}
        for condition_name, prefix in COLUMN_PREFIXES.items():
            condition = by_condition.get(condition_name)
            level = _levels_of(condition).get(ALL_LEVEL) if condition else None
            profile = (level or {}).get("masses", {}).get(
                component["name"], {}).get(query) or {}
            name, mass = top_segment(profile)
            cells[f"{prefix}_top_segment"] = name
            cells[f"{prefix}_top_mass"] = mass
        updates[key] = cells
    return updates


def declare_coverage(ctx, payload: dict) -> None:
    """Tell the head table which instances each condition's columns cover.

    Read off `patterns.json`'s own `instance_ids`, so the meta and the file
    cannot disagree. A condition that did not run declares its columns over
    nothing, which the table records as n = 0. `query_position` is a setting,
    not a measurement, and declares nothing.
    """
    by_condition = {condition["name"]: condition
                    for condition in payload["conditions"]}
    for condition_name, prefix in COLUMN_PREFIXES.items():
        condition = by_condition.get(condition_name) or {}
        ctx.declare_coverage(
            [f"{prefix}_top_segment", f"{prefix}_top_mass"],
            instance_ids=condition.get("instance_ids") or [],
            instance_set=INSTANCE_SETS[condition_name],
            dataset=condition.get("dataset"))


# ==============================================================================
# THE ANALYSIS
# ==============================================================================

def _plan(ctx):
    """(Segment names, query Segments, split, circuit heads, heads by layer).

    Raises `LoaderUnavailable` on a task with no segmentation, which is the one
    failure `--dry-run` softens into a printed "not applicable": a task without
    Segments has no attention profile to report, and that is a property of the
    task rather than a bad configuration.
    """
    from component_analysis import dataloaders

    if not ctx.segmentations:
        raise dataloaders.LoaderUnavailable(
            f"task {ctx.task_spec.name!r} has no resolved segmentation, so "
            f"attention has no Segments to be aggregated over")
    names = list(ctx.segmentations[0].segments)
    query = parse_query_positions(getattr(ctx.cli, "query_positions", None),
                                  names)
    split = getattr(ctx.cli, "split", "designation")
    heads = [one for one in ctx.components if one.kind == "head"]
    heads_by_layer: Dict[int, List[int]] = {}
    for head in heads:
        heads_by_layer.setdefault(head.layer, []).append(head.index)
    return names, query, split, heads, heads_by_layer


def _cost(n_batches: int, n_layers: int, batch_size: int) -> Tuple[int, float]:
    """(eager forward passes, seconds) for one condition.

    One forward per layer that holds a circuit head, per batch: the attention
    rows of a layer come back from a whole forward, so every head of that layer
    is read in the same pass and no head costs anything extra. The per-forward
    second is ticket 02b's A40 measurement at batch 8, scaled by the batch.
    """
    forwards = n_batches * n_layers
    return forwards, forwards * EAGER_SECONDS_PER_BATCH_OF_8 * (batch_size / 8.0)


def _duration(seconds: float) -> str:
    return f"{seconds / 60:.0f} min" if seconds >= 90 else f"{seconds:.0f} s"


def estimate(ctx) -> str:
    """One line for `--dry-run`. Touches no GPU and writes no file."""
    from component_analysis import dataloaders

    names, query, split, heads, heads_by_layer = _plan(ctx)
    if not heads:
        return ("no attention head in this circuit, so nothing to profile "
                f"({len(ctx.components)} Component(s), MLP blocks only)")

    wanted = wanted_conditions(ctx.cli)
    batch_size = getattr(ctx.cli, "batch_size", dataloaders.DEFAULT_BATCH_SIZE)
    layers = len(heads_by_layer)
    parts = [f"{len(heads)} head(s) over {layers} layer(s), "
             f"{len(query)} query position(s) ({', '.join(query)}), "
             f"{len(names)} Segment(s), split by {split}",
             f"conditions {', '.join(wanted)}"]
    total = 0.0

    def line(label, n_batches, n_instances, *, passes=1):
        """One condition's cost. `passes` is how many times each batch is read:
        the paired condition reads each of its batches twice, once for the
        pressure prompt and once for its counterfactual, and saying "26
        batches" instead would misreport the loader."""
        nonlocal total
        forwards, seconds = _cost(n_batches * passes, layers, batch_size)
        total += seconds
        over = f"{n_batches} batch(es)" if passes == 1 else \
            f"{n_batches} batch(es) read {passes}x"
        return (f"{label} {n_instances} instance(s) in {over}, "
                f"{forwards} eager forward(s) ~{_duration(seconds)}")

    if PRESSURE in wanted:
        pressure = ctx.descriptive_batches()
        parts.append(line("pressure:", len(pressure), pressure.n_instances))

    causal, reason = (None, "not in --attention-conditions") \
        if HONEST_INSTRUCTION not in wanted else paired_batches(ctx)
    if reason:
        parts.append(f"honest-instruction (paired): none — {reason}")
    else:
        parts.append(line("honest-instruction (paired), both sides:",
                          len(causal), causal.report["n_with_honest"],
                          passes=2))

    directory, reason = (None, "not in --attention-conditions") \
        if HONEST_TWIN not in wanted else honest_twin_dir(ctx)
    if reason:
        parts.append(f"honest twin (descriptive): none — {reason}")
    else:
        try:
            twin = dataloaders.descriptive_batches(
                directory, ctx.tokenizer, task=ctx.task_spec.name,
                batch_size=batch_size)
            parts.append(line("honest twin (descriptive):", len(twin),
                              twin.n_instances))
        except Exception as failure:                       # noqa: BLE001
            parts.append(f"honest twin (descriptive): none — {directory} "
                         f"could not be loaded ({failure})")

    if getattr(ctx.cli, "attention_token_level", False):
        parts.append(f"token-level: one PNG per head ({len(heads)}), read from "
                     f"the same forwards, no extra pass")
    parts.append(f"about {_duration(total)} on an A40 in total, plus the "
                 f"figures")
    return "; ".join(parts)


def run(ctx) -> dict:
    """Every condition, then `patterns.json`, the figures and the columns."""
    from component_analysis import dataloaders
    from component_analysis import segmentation as segs

    names, query, split, heads, heads_by_layer = _plan(ctx)
    column_query = query[0] if DEFAULT_QUERY_POSITION not in query \
        else DEFAULT_QUERY_POSITION
    payload = {
        "analysis": NAME,
        "schema_version": SCHEMA_VERSION,
        "task": ctx.task_spec.name,
        "circuit": ctx.circuit_spec.label,
        "model": ctx.intake.model,
        "split": split,
        "query_positions": query,
        "column_query_position": column_query,
        "segments": names,
        "sum_tolerance": SUM_TOLERANCE,
        "colormap": COLORMAP,
        "components": [{"key": list(one.key), "name": component_key_name(one.key),
                        "label": head_label(one.key), "layer": one.layer,
                        "index": one.index, "kv_group": one.kv_group}
                       for one in heads],
        "conditions": [],
        "skipped": [],
        # What --attention-token-level wrote, or None when it was not asked for.
        "token_level": None,
    }

    if ctx.model is None:
        payload["skipped"].append(
            {"condition": "all", "reason": "no model was loaded, so no "
                                           "attention weights were read"})
        ctx.write_json(SUBDIR, PATTERNS_FILE, payload)
        return {}
    if not heads:
        payload["skipped"].append(
            {"condition": "all", "reason": "this circuit holds no attention "
                                           "head, only MLP blocks"})
        ctx.write_json(SUBDIR, PATTERNS_FILE, payload)
        return {}

    shared = {"head_keys": [one.key for one in heads], "names": names,
              "query_names": query, "split": split,
              "heads_by_layer": heads_by_layer}
    wanted = wanted_conditions(ctx.cli)
    tokens = (TokenProfiles(shared["head_keys"], names, query)
              if getattr(ctx.cli, "attention_token_level", False) else None)

    # --- pressure, over the whole test split --------------------------------
    if PRESSURE not in wanted:
        payload["skipped"].append(
            {"condition": PRESSURE,
             "reason": f"{PRESSURE} is not in --attention-conditions"})
    else:
        missing: List[str] = []
        batches = ctx.descriptive_batches()
        profiles, checks = collect_condition(
            ctx, pressure_slices(batches, ctx.segmentations, missing), **shared,
            tokens=tokens, condition=PRESSURE)
        notes = []
        if missing:
            notes.append(f"{len(missing)} instance(s) of the loader's split "
                         f"have no resolved segmentation and were not "
                         f"profiled: {', '.join(missing[:3])}")
        payload["conditions"].append(_condition_json(
            PRESSURE, "pressure", False, batches, profiles, checks, notes))

    # --- the paired Honest-Instruction Counterfactual ------------------------
    causal, reason = (None, f"{HONEST_INSTRUCTION} is not in "
                            f"--attention-conditions") \
        if HONEST_INSTRUCTION not in wanted else paired_batches(ctx)
    if reason:
        payload["skipped"].append({"condition": HONEST_INSTRUCTION,
                                   "reason": reason})
    else:
        n_paired = causal.report["n_with_honest"]

        # The left term first, over exactly the rows the honest side will read.
        left, left_checks = collect_condition(
            ctx, pressure_paired_slices(causal, ctx.segmentations), **shared,
            tokens=tokens, condition=PRESSURE_PAIRED)
        payload["conditions"].append(_condition_json(
            PRESSURE_PAIRED, "pressure (paired subset)", True, causal, left,
            left_checks,
            [f"the Pressure Clause on the {n_paired} instance(s) that have a "
             f"Matched Honest Instruction — the left term of the paired "
             f"contrast, and the column the {HONEST_INSTRUCTION} column is to "
             f"be read against",
             f"NOT the same as {PRESSURE}, which is the whole test split: the "
             f"paired instances are the survivors of the Matched Honest "
             f"filter and not a random subset of it"],
            n_instances=n_paired))

        report = {"n_pairs": 0, "n_identical_to_pressure": 0,
                  "n_differing_outside_the_clause": 0,
                  "examples_outside_the_clause": []}
        profiles, checks = collect_condition(
            ctx, honest_instruction_slices(causal, ctx.segmentations, report),
            **shared, tokens=tokens, condition=HONEST_INSTRUCTION)
        notes = [f"paired with the {PRESSURE_PAIRED} condition, instance by "
                 f"instance; {n_paired} of {causal.report['n_instances']} "
                 f"sampled instances have a Matched Honest Instruction",
                 "the honest prompt reuses its pressure prompt's Segments, "
                 "which the token-level diff below re-checks per instance"]
        if report["n_differing_outside_the_clause"]:
            notes.append(
                f"!! {report['n_differing_outside_the_clause']} pair(s) differ "
                f"outside the Pressure Clause, so their Segments are not the "
                f"pressure prompt's: {', '.join(report['examples_outside_the_clause'])}")
        payload["conditions"].append(_condition_json(
            HONEST_INSTRUCTION, "honest instruction", True, causal, profiles,
            checks, notes, extra={"alignment": report}, n_instances=n_paired))

    # --- the unpaired honest twin -------------------------------------------
    directory, reason = (None, f"{HONEST_TWIN} is not in "
                               f"--attention-conditions") \
        if HONEST_TWIN not in wanted else honest_twin_dir(ctx)
    if reason:
        payload["skipped"].append({"condition": HONEST_TWIN, "reason": reason})
    else:
        twin = dataloaders.descriptive_batches(
            directory, ctx.tokenizer, task=ctx.task_spec.name,
            batch_size=getattr(ctx.cli, "batch_size",
                               dataloaders.DEFAULT_BATCH_SIZE))
        overrides = segs.parse_segment_overrides(getattr(ctx.cli, "segment", None))
        resolved: List = []
        profiles, checks = collect_condition(
            ctx, twin_slices(twin, ctx, overrides, resolved), **shared,
            tokens=tokens, condition=HONEST_TWIN)
        _write_twin_segmentation(ctx, resolved, directory, overrides)
        payload["conditions"].append(_condition_json(
            "honest_twin", "honest twin", False, twin, profiles, checks,
            ["UNPAIRED and descriptive: different instances from the pressure "
             "condition, so a difference here is a difference between "
             "populations and is not a causal contrast",
             f"segmentation resolved over {directory} and written to "
             f"{TWIN_SEGMENTATION_FILE}"],
            dataset=directory))

    if tokens is not None and tokens.groups:
        payload["token_level"] = write_token_level(ctx, tokens, payload)
    elif tokens is not None:
        # Asked for, but every condition was skipped: say so rather than draw
        # a PNG per head with no row in it.
        payload["token_level"] = {
            "payload": "none",
            "reason": "no condition was profiled, so there are no tokens to "
                      "render; see 'skipped'"}
    ctx.write_json(SUBDIR, PATTERNS_FILE, payload)
    write_heatmaps(ctx, payload)
    write_top_heads(ctx, payload)
    declare_coverage(ctx, payload)
    return columns(payload)


def _condition_json(name, kind, paired, batches, profiles, checks, notes, *,
                    dataset=None, extra=None, n_instances=None) -> dict:
    levels = profiles.as_json()
    checks = dict(checks)
    # The ids are the condition's own field rather than a check: they say which
    # instances the profile is of, which is what makes two paired conditions
    # comparable at the file rather than only in the code.
    instance_ids = checks.pop("instance_ids", [])
    return {
        "name": name,
        "kind": kind,
        "paired": paired,
        "descriptive": not paired,
        "dataset": dataset,
        "instance_ids": instance_ids,
        # What this condition was actually profiled over. It is the loader's
        # instance count except for the paired condition, where most of the
        # sample has no counterpart and the loader's 100 would read as an n.
        "n_instances": batches.n_instances if n_instances is None else n_instances,
        "n_loaded": batches.n_instances,
        "batches": len(batches),
        "levels": levels,
        "checks": {**checks, "n_nan": count_nan(levels),
                   "sums_to_one": checks["max_abs_sum_minus_one"] <= SUM_TOLERANCE},
        "notes": list(notes),
        **(extra or {}),
    }


def _write_twin_segmentation(ctx, segmentations, directory, overrides) -> str:
    """The honest twin's Segments, beside its numbers.

    The cell's own `segmentation.json` describes the pressure dataset; the twin
    is a different dataset with different prompts, and a plot of it read
    against the wrong spans is exactly what user story 10 exists to prevent.
    """
    names = list(segmentations[0].segments) if segmentations else []
    return ctx.write_json(SUBDIR, TWIN_SEGMENTATION_FILE, {
        "task": ctx.task_spec.name,
        "dataset": directory,
        "split": "test",
        "condition": "honest_twin",
        "n_instances": len(segmentations),
        "segment_names": names,
        "segment_sources": {name: segmentations[0].segments[name].source
                            for name in names},
        "overrides": dict(overrides),
        "spans": "as in the cell's segmentation.json, which documents them",
        "instances": [one.as_json() for one in segmentations],
    })
