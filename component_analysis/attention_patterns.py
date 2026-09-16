"""
component_analysis/attention_patterns.py — what each Circuit Component head reads.

For every attention head in the circuit, the attention mass it places on each
**Segment** of the prompt, from a chosen query position (the **Readout** by
default), averaged over instances and split by designation polarity, item
polarity, both or neither. A head that reads the Designation Positions is doing
something different from one that reads the quoted option it is about to copy,
and this is the view that tells them apart.

Three conditions, and the difference between them is the whole point of reading
the table (CONTEXT.md; spec user story 27):

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

Eager attention is on only inside `hooks.attention_weights`, which restores
SDPA in a `finally` (ADR-0001). This is the one analysis that pays the
`[batch, heads, seq, seq]` buffer per layer.

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
    pressure_top_segment / _top_mass        under the Pressure Clause
    honest_twin_descriptive_top_segment /
        _top_mass                           the unpaired twin, labelled in the
                                            column name so a CSV reader cannot
                                            mistake it for a paired contrast

The paired honest-instruction condition is computed and written into
`patterns.json`, but its head-table column belongs to ticket 06, which owns the
paired columns across the descriptive analyses.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import torch

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

#: How far a row of attention may be from summing to one before the run says
#: so. HuggingFace's eager attention softmaxes in fp32 and casts the weights
#: back to the model's dtype, so on a bfloat16 model a row of 128 weights is
#: one only to about 1e-2; the tolerance is about the dtype, not about the
#: analysis.
SUM_TOLERANCE = 2e-2


# ==============================================================================
# READING THE FLAGS
# ==============================================================================

def add_arguments(group) -> None:
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
                 positions, ids, n_segments):
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
        if batch.honest is None:
            continue
        rows = [row for row in batch.honest.rows if batch.ids[row] in known]
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
                      heads_by_layer) -> Tuple[Profiles, dict]:
    """Every batch of one condition through the model, into one `Profiles`."""
    from component_analysis import hooks

    device, _dtype = hooks.device_and_dtype(ctx.model)
    profiles = Profiles(head_keys, names, query_names)
    checks = {"max_abs_sum_minus_one": 0.0, "max_outside": 0.0, "n_batches": 0}

    for one in slices:
        if not len(one):
            continue
        positions, valid, slots = query_slots(one.segmentations, query_names)
        ids = segment_id_batch(one.segmentations, names, one.input_ids.shape[1])
        masses, batch_checks = batch_masses(
            ctx.model, one.input_ids.to(device), one.attention_mask.to(device),
            heads_by_layer=heads_by_layer, positions=positions, ids=ids,
            n_segments=len(names))
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
                                cmap="magma")
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
        axis.bar(range(len(segment_names)), values, color="#4c72b0")
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
# HEAD-TABLE COLUMNS
# ==============================================================================

def columns(payload: dict) -> dict:
    """`{component key: {column: value}}` — the top Segment per head.

    The honest-twin columns carry `descriptive` in their own names: the CSV is
    read column by column, and a reader who sees only the header must not be
    able to mistake an unpaired population contrast for a paired one.
    """
    query = payload["column_query_position"]
    wanted = {"pressure": "pressure", "honest_twin": "honest_twin_descriptive"}
    by_condition = {condition["name"]: condition
                    for condition in payload["conditions"]}

    updates: Dict[tuple, Dict[str, object]] = {}
    for component in payload["components"]:
        key = tuple(component["key"])
        cells: Dict[str, object] = {"query_position": query}
        for condition_name, prefix in wanted.items():
            condition = by_condition.get(condition_name)
            level = _levels_of(condition).get(ALL_LEVEL) if condition else None
            profile = (level or {}).get("masses", {}).get(
                component["name"], {}).get(query) or {}
            name, mass = top_segment(profile)
            cells[f"{prefix}_top_segment"] = name
            cells[f"{prefix}_top_mass"] = mass
        updates[key] = cells
    return updates


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

    batch_size = getattr(ctx.cli, "batch_size", dataloaders.DEFAULT_BATCH_SIZE)
    layers = len(heads_by_layer)
    parts = [f"{len(heads)} head(s) over {layers} layer(s), "
             f"{len(query)} query position(s) ({', '.join(query)}), "
             f"{len(names)} Segment(s), split by {split}"]
    total = 0.0

    def line(label, n_batches, n_instances):
        nonlocal total
        forwards, seconds = _cost(n_batches, layers, batch_size)
        total += seconds
        return (f"{label} {n_instances} instance(s) in {n_batches} batch(es), "
                f"{forwards} eager forward(s) ~{_duration(seconds)}")

    pressure = ctx.descriptive_batches()
    parts.append(line("pressure:", len(pressure), pressure.n_instances))

    causal, reason = paired_batches(ctx)
    if reason:
        parts.append(f"honest-instruction (paired): none — {reason}")
    else:
        parts.append(line("honest-instruction (paired):", len(causal),
                          causal.report["n_with_honest"]))

    directory, reason = honest_twin_dir(ctx)
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
        "components": [{"key": list(one.key), "name": component_key_name(one.key),
                        "label": head_label(one.key), "layer": one.layer,
                        "index": one.index, "kv_group": one.kv_group}
                       for one in heads],
        "conditions": [],
        "skipped": [],
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

    # --- pressure, over the whole test split --------------------------------
    missing: List[str] = []
    batches = ctx.descriptive_batches()
    profiles, checks = collect_condition(
        ctx, pressure_slices(batches, ctx.segmentations, missing), **shared)
    notes = []
    if missing:
        notes.append(f"{len(missing)} instance(s) of the loader's split have no "
                     f"resolved segmentation and were not profiled: "
                     f"{', '.join(missing[:3])}")
    payload["conditions"].append(_condition_json(
        "pressure", "pressure", False, batches, profiles, checks, notes))

    # --- the paired Honest-Instruction Counterfactual ------------------------
    causal, reason = paired_batches(ctx)
    if reason:
        payload["skipped"].append({"condition": "honest_instruction",
                                   "reason": reason})
    else:
        report = {"n_pairs": 0, "n_identical_to_pressure": 0,
                  "n_differing_outside_the_clause": 0,
                  "examples_outside_the_clause": []}
        profiles, checks = collect_condition(
            ctx, honest_instruction_slices(causal, ctx.segmentations, report),
            **shared)
        notes = [f"paired with the pressure condition, instance by instance; "
                 f"{causal.report['n_with_honest']} of "
                 f"{causal.report['n_instances']} sampled instances have a "
                 f"Matched Honest Instruction",
                 "the honest prompt reuses its pressure prompt's Segments, "
                 "which the token-level diff below re-checks per instance"]
        if report["n_differing_outside_the_clause"]:
            notes.append(
                f"!! {report['n_differing_outside_the_clause']} pair(s) differ "
                f"outside the Pressure Clause, so their Segments are not the "
                f"pressure prompt's: {', '.join(report['examples_outside_the_clause'])}")
        payload["conditions"].append(_condition_json(
            "honest_instruction", "honest instruction", True, causal, profiles,
            checks, notes, extra={"alignment": report},
            n_instances=causal.report["n_with_honest"]))

    # --- the unpaired honest twin -------------------------------------------
    directory, reason = honest_twin_dir(ctx)
    if reason:
        payload["skipped"].append({"condition": "honest_twin", "reason": reason})
    else:
        twin = dataloaders.descriptive_batches(
            directory, ctx.tokenizer, task=ctx.task_spec.name,
            batch_size=getattr(ctx.cli, "batch_size",
                               dataloaders.DEFAULT_BATCH_SIZE))
        overrides = segs.parse_segment_overrides(getattr(ctx.cli, "segment", None))
        resolved: List = []
        profiles, checks = collect_condition(
            ctx, twin_slices(twin, ctx, overrides, resolved), **shared)
        _write_twin_segmentation(ctx, resolved, directory, overrides)
        payload["conditions"].append(_condition_json(
            "honest_twin", "honest twin", False, twin, profiles, checks,
            ["UNPAIRED and descriptive: different instances from the pressure "
             "condition, so a difference here is a difference between "
             "populations and is not a causal contrast",
             f"segmentation resolved over {directory} and written to "
             f"{TWIN_SEGMENTATION_FILE}"],
            dataset=directory))

    ctx.write_json(SUBDIR, PATTERNS_FILE, payload)
    write_heatmaps(ctx, payload)
    write_top_heads(ctx, payload)
    return columns(payload)


def _condition_json(name, kind, paired, batches, profiles, checks, notes, *,
                    dataset=None, extra=None, n_instances=None) -> dict:
    levels = profiles.as_json()
    return {
        "name": name,
        "kind": kind,
        "paired": paired,
        "descriptive": not paired,
        "dataset": dataset,
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
