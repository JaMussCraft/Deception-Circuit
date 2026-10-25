"""
component_analysis/knockout.py — every Component ranked by what its knockout costs.

The circuit evaluations rank *circuits* by what interchange-ablating them does
to the deceptive answer. This ranks the **Components** inside one circuit the
same way: knock out one head or one MLP block, in the full unmodified model,
and measure what happens to logit(Target) - logit(Distractor) at the Readout.

**The knockout is an interchange ablation.** The Component's output is replaced,
at every position, by the value it carried on the *item-swap corrupt* stream —
the same reference the gates were trained against, so a Component's number here
is comparable with the circuit-level knockout numbers the evaluator reports.
Mean and zero ablation are not built; `--knockout-scheme` exists so that they
can be added later without the interface changing, and refuses them by name
today.

**The sign convention, which is the one thing to get right when reading the
table.** The effect of a knockout is

    drop = clean logit difference - knocked-out logit difference

so it is **positive when the Component helps deception** (removing it moves the
model away from the deceptive answer) and negative for a Component that opposes
it — a suppressor's knockout *raises* the deceptive margin. The ranking sorts by
the signed drop, not by its magnitude, so rank 1 is the most deception-helping
Component and the suppressors are at the bottom where they can be read as such.
`knockout.json` carries the same sentence in its `metric` block.

**Accuracy** here is the two-way rate the metric implies: the share of the
sampled instances whose Target still outscores its Distractor. It is not a
full-vocabulary argmax, and on a deceptive-condition dataset the Target *is* the
deceptive answer, so this column is the deception rate under that knockout.

Everything is read through `hooks.readout_logits`, the fp32 final norm and
unembedding ADR-0001 requires: a head table is read as a ranking, and in
bfloat16 two Components can swap places on rounding alone.

No nnsight at module scope — `--dry-run` and the parser build run on the login
node, which has no 0.7.0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# The head table's own key coercion: a Component, a (kind, layer, index)
# tuple or a key read back out of JSON all become one tuple, so a row here
# and a row there cannot disagree about what names a Component.
from component_analysis.head_table import CAUSAL_SAMPLE, row_key
# One spelling of a Component for every sweep output: `head.17.25`, as the
# path-patching sweep writes it, so the two sweeps' lists compare by string.
from component_analysis.path_patching import label as component_label

NAME = "knockout"
SUBDIR = "knockout"

#: The four files this analysis writes. Each JSON is its PNG's twin: every
#: number a chart draws is in it, so an agent with no display loses nothing.
#: The per-Component pair is always written; the family pair only under
#: `--knockout-families` (see "Knockout by role family" below).
JSON_NAME = "knockout.json"
PNG_NAME = "knockout.png"

#: The default ablation scheme, and every scheme built (mechanism-analysis
#: 02a added mean and zero). `mean` has the evaluator's semantics
#: (`evaluation/ablation.py` `MeanCollector` / `MeanHook`): one mean per site
#: over every unpadded position of the cell's own test split, clean and corrupt
#: prompts pooled with equal token weight, accumulated in fp32, cast to the
#: model's dtype and written at every position the plan names. `zero` writes
#: zeros there.
SCHEME = "interchange"
SCHEMES = ("interchange", "mean", "zero")

#: Which stream an interchange knockout copies from. `item_swap` is the
#: dataset's corrupt prompt (the default, v1's only one); `neutral_twin` is
#: the v2 Neutral-Clause Twin's clean prompt, with the pressure prompt's labels
#: (`dataloaders.NeutralTwinPair`).
COUNTERFACTUAL = "item_swap"
COUNTERFACTUALS = ("item_swap", "neutral_twin")

#: Where a knockout writes: `all` (the default), `readout`, a Segment's name,
#: or the range form `after=<Segment>[,exclude=readout]` (R11(a)); the spec's
#: "post-clause" is `after=pressure_clause,exclude=readout`.
POSITIONS = "all"

#: Seconds per forward on an H100, extrapolated (not measured) from the H200
#: sweep of job 22899543 (0.0368 s) by the evaluator's H200/H100 ratio
#: 5.4 / 4.0. Ticket 02a's Bridges-2 smoke replaces it with a measurement.
SECONDS_PER_FORWARD_H100 = 0.0368 * 5.4 / 4.0

#: What of the loader's report belongs in this analysis's JSON. The
#: Honest-Instruction counts it also carries are the paired analyses' business:
#: a knockout runs on the item-swap pair alone, and printing "71 of 100 paired"
#: beside a knockout number would invite the reader to think it used them.
SAMPLE_FIELDS = ("task", "split", "batch_size", "max_length", "n_requested",
                 "n_instances", "missing_from_split", "dropped_by_tokenization")

#: Seconds per forward pass at batch 8 x 128 tokens on an A40, measured by the
#: block C scaffold check (ticket 02b). Only `--dry-run`'s estimate uses it.
SECONDS_PER_FORWARD = 0.19


class UnsupportedScheme(argparse.ArgumentTypeError, ValueError):
    """A knockout scheme, counterfactual or positions value that is not built.

    Two bases on purpose: argparse prints an `ArgumentTypeError` verbatim, so
    a bad flag fails on the login node with the sentence below rather than
    "invalid value", and a library caller still catches the `ValueError` it
    would expect.
    """


def resolve_scheme(value) -> str:
    """One of `SCHEMES`, or a refusal that names them."""
    scheme = str(value).strip().lower()
    if scheme in SCHEMES:
        return scheme
    raise UnsupportedScheme(
        f"knockout scheme {scheme!r} is not one of {', '.join(SCHEMES)}: "
        f"interchange copies the counterfactual stream's value, mean writes the "
        f"site's mean over the cell's test split, zero writes zeros")


def resolve_counterfactual(value) -> str:
    """One of `COUNTERFACTUALS`, or a refusal that names them."""
    counterfactual = str(value).strip().lower()
    if counterfactual in COUNTERFACTUALS:
        return counterfactual
    raise UnsupportedScheme(
        f"knockout counterfactual {counterfactual!r} is not one of "
        f"{', '.join(COUNTERFACTUALS)}")


_SEGMENT_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def parse_positions(value) -> dict:
    """`--knockout-positions`, parsed: `{"form", "segment"?, "exclude_readout"?, "text"}`.

    Wired as the flag's `type=`, so a malformed value is refused at parse time.
    Whether the named Segment exists is a property of the cell's segmentation
    and is checked by `position_mask` (and so by `--dry-run`).
    """
    text = str(value).strip()
    if text in ("all", "readout"):
        return {"form": text, "text": text}
    if _SEGMENT_NAME.fullmatch(text):
        return {"form": "segment", "segment": text, "text": text}
    if text.startswith("after="):
        parts = text[len("after="):].split(",")
        segment = parts[0]
        rest = parts[1:]
        if _SEGMENT_NAME.fullmatch(segment) and rest in ([], ["exclude=readout"]):
            return {"form": "after", "segment": segment,
                    "exclude_readout": bool(rest), "text": text}
    raise UnsupportedScheme(
        f"--knockout-positions {text!r} is not one of: all, readout, a Segment "
        f"name, or after=<Segment>[,exclude=readout]")


def positions_slug(parsed: dict) -> str:
    """The positions part of a column suffix; empty for every position."""
    form = parsed["form"]
    if form == "all":
        return ""
    if form == "readout":
        return "at_readout"
    if form == "segment":
        return f"at_{parsed['segment']}"
    return f"after_{parsed['segment']}" + ("_excl_readout"
                                           if parsed["exclude_readout"] else "")


@dataclass(frozen=True)
class KnockoutPlan:
    """Every choice a knockout makes, recorded in the JSON it writes.

    The default plan is v1's knockout (interchange from the item-swap corrupt
    stream, at every position) and writes v1's column names. Any other plan
    writes its head-table columns under a suffix that says what it measured,
    so a later reader of `knockout.logit_diff_drop` (the roles pass, say) can
    never take a neutral-twin or a mean-ablation drop for an item-swap one.
    """

    scheme: str = SCHEME
    counterfactual: str = COUNTERFACTUAL
    positions: str = POSITIONS

    def __post_init__(self):
        object.__setattr__(self, "scheme", resolve_scheme(self.scheme))
        object.__setattr__(self, "counterfactual",
                           resolve_counterfactual(self.counterfactual))
        object.__setattr__(self, "positions", parse_positions(self.positions)["text"])
        if self.scheme != "interchange" and self.counterfactual != COUNTERFACTUAL:
            raise ValueError(
                f"--knockout-counterfactual {self.counterfactual} names a stream "
                f"to copy from, which only interchange ablation reads; "
                f"{self.scheme} ablation takes none")

    @property
    def is_default(self) -> bool:
        return (self.scheme, self.counterfactual, self.positions) == \
            (SCHEME, COUNTERFACTUAL, POSITIONS)

    @property
    def parsed_positions(self) -> dict:
        return parse_positions(self.positions)

    @property
    def column_suffix(self) -> str:
        parts = []
        if self.scheme != SCHEME:
            parts.append(self.scheme)
        if self.counterfactual == "neutral_twin":
            parts.append("neutral_twin_paired")
        slug = positions_slug(self.parsed_positions)
        if slug:
            parts.append(slug)
        return "".join(f"_{part}" for part in parts)

    def describe(self) -> dict:
        return {"scheme": self.scheme,
                "counterfactual": (self.counterfactual if self.scheme == "interchange"
                                   else None),
                "positions": self.positions,
                "column_suffix": self.column_suffix}


def ablation_sentence(plan: KnockoutPlan) -> str:
    """What `metric.ablation` says, for this plan. v1's sentence for v1's plan."""
    if plan.is_default:
        return ("the Component's output at every position is replaced by the "
                "value it carried on the item-swap corrupt stream")
    where = {"all": "at every position", "readout": "at the Readout only",
             "segment": f"at the {plan.parsed_positions.get('segment')} Segment's tokens",
             "after": (f"at every token after the "
                       f"{plan.parsed_positions.get('segment')} Segment"
                       + (", the Readout excluded"
                          if plan.parsed_positions.get("exclude_readout") else ""))
             }[plan.parsed_positions["form"]]
    what = {"interchange": (
                "the value it carried on the item-swap corrupt stream"
                if plan.counterfactual == "item_swap" else
                "the value it carried on the instance's Neutral-Clause Twin "
                "(the clause replaced by a token-matched neutral sentence; the "
                "pressure prompt's labels)"),
            "mean": ("its mean over every unpadded position of the cell's test "
                     "split, clean and corrupt prompts pooled (fp32, the "
                     "evaluator's mean-ablation semantics)"),
            "zero": "zeros"}[plan.scheme]
    return f"the Component's output {where} is replaced by {what}"


def position_mask(parsed: dict, ids, segmentations, readout, seq_len: int):
    """`[batch, seq]` bool mask of where a knockout writes, or None for all.

    `segmentations` maps instance id to its `Segmentation` (spans over the
    clean prompt; the item-swap and twin streams are token-aligned with it).
    A Segment absent on a row is refused by name: a post-clause knockout on a
    prompt with no clause (the nopressure condition) is not a smaller
    knockout, it is a different question.
    """
    import torch

    form = parsed["form"]
    if form == "all":
        return None
    readout = torch.as_tensor(readout).long().tolist()
    mask = torch.zeros((len(ids), seq_len), dtype=torch.bool)
    for row, one in enumerate(ids):
        if form == "readout":
            mask[row, readout[row]] = True
            continue
        name = parsed["segment"]
        segmentation = segmentations.get(one) if segmentations else None
        if segmentation is None:
            raise ValueError(f"instance {one} has no segmentation, so "
                             f"--knockout-positions {parsed['text']} cannot be placed")
        if name not in segmentation.segments:
            raise ValueError(f"instance {one} has no Segment {name!r}; its "
                             f"Segments are {', '.join(segmentation.segments)}")
        tokens = segmentation.segments[name].token_indices()
        if not tokens:
            raise ValueError(f"Segment {name!r} is absent on instance {one}, so "
                             f"--knockout-positions {parsed['text']} has no tokens "
                             f"there")
        if form == "segment":
            mask[row, tokens] = True
            continue
        last = readout[row] if not parsed["exclude_readout"] else readout[row] - 1
        start = max(tokens) + 1
        if start <= last:
            mask[row, start:last + 1] = True
    return mask


# ==============================================================================
# WHAT ONE RUN MEASURED
# ==============================================================================

@dataclass
class Effects:
    """Per-instance logit differences: clean, and under each knockout.

    One list per knocked-out group, in the order the instances came out of the
    loader, so every summary statistic below is over the causal sample and
    nothing is averaged twice. A group is one Component for the per-Component
    pass, where `keys` holds Component keys, and every Component of one
    Component Role for the family pass, where `keys` holds role names.
    """

    ids: List[str]
    #: The label of each knocked-out group: a Component key, or a role name.
    keys: List

    clean_logit_difference: List[float]
    knocked_logit_difference: Dict[tuple, List[float]]
    scheme: str = SCHEME
    #: What the loader said about the sample it built; carried into the JSON.
    report: dict = field(default_factory=dict)
    #: The counterfactual stream's own full-model logit difference per
    #: instance, read with the CLEAN stream's labels (R19(1): the twin's margin
    #: is the denominator of R-AB's f_D). Empty under mean and zero, which run
    #: no counterfactual stream.
    counterfactual_logit_difference: List[float] = field(default_factory=list)
    #: `KnockoutPlan.describe()` of the run.
    plan: dict = field(default_factory=dict)
    #: Instances the loader gave but the plan could not run on (no twin).
    unpaired: List[str] = field(default_factory=list)
    #: R19(1): the Neutral-Clause Twin's own full-model logit difference per
    #: instance, in `ids` order and with the clean stream's labels, whenever
    #: the batches carry a twin (v2 D and I), whatever the plan; None for a
    #: row with no twin. Under a neutral-twin plan it is the counterfactual
    #: run itself. Empty when no batch carried a twin (v1, H, F).
    neutral_twin_logit_difference: List[Optional[float]] = field(default_factory=list)

    def drops(self, key) -> List[float]:
        """Clean minus knocked-out, per instance. Positive helps deception."""
        return [clean - knocked for clean, knocked
                in zip(self.clean_logit_difference, self.knocked_logit_difference[key])]

    def restrict(self, keys) -> "Effects":
        """The same run, read for `keys` only, in that order.

        How the completeness sweep hands the circuit's single knockouts to
        `knockout.json`: they were among the forwards the sweep ran, so they
        are read out of it rather than run again, and the two files cannot
        disagree.
        """
        keys = [row_key(one) for one in keys]
        absent = [one for one in keys if one not in self.knocked_logit_difference]
        if absent:
            raise ValueError(
                f"{len(absent)} Component(s) were not knocked out in this run, "
                f"the first being {absent[0]}; a restriction can only read "
                f"numbers the run measured")
        return Effects(ids=list(self.ids), keys=keys,
                       clean_logit_difference=list(self.clean_logit_difference),
                       knocked_logit_difference={
                           key: list(self.knocked_logit_difference[key])
                           for key in keys},
                       scheme=self.scheme, report=dict(self.report),
                       counterfactual_logit_difference=list(
                           self.counterfactual_logit_difference),
                       plan=dict(self.plan), unpaired=list(self.unpaired),
                       neutral_twin_logit_difference=list(
                           self.neutral_twin_logit_difference))


def _accuracy(values) -> Optional[float]:
    """Share of instances whose Target outscores its Distractor."""
    if not values:
        return None
    return sum(1 for one in values if one > 0) / len(values)


def _mean(values) -> Optional[float]:
    return sum(values) / len(values) if values else None


def _standard_error(values) -> Optional[float]:
    """Sample standard error of the mean, or None when n < 2.

    None rather than 0.0 on a single instance: zero would read as a measured
    and tiny spread rather than as a spread that was never measurable.
    """
    if len(values) < 2:
        return None
    mean = _mean(values)
    variance = sum((one - mean) ** 2 for one in values) / (len(values) - 1)
    return math.sqrt(variance) / math.sqrt(len(values))


def clean_run(effects: Effects) -> dict:
    """The un-knocked-out run every drop is measured against.

    Not called a baseline: CONTEXT.md reserves that word, because the
    random-circuit null is a baseline too.
    """
    return {
        "mean_logit_difference": _mean(effects.clean_logit_difference),
        "standard_error": _standard_error(effects.clean_logit_difference),
        "accuracy": _accuracy(effects.clean_logit_difference),
        "n_instances": len(effects.clean_logit_difference),
    }


def summarize(effects: Effects, components=None) -> List[dict]:
    """One ranked row per Component, strongest drop first.

    `components` is the Component list when there is one, so that a row can
    carry the head table's `kv_group` beside the numbers; the keys alone are
    enough without it. Ties keep the order the Components came in, which is
    head-table order, so a rerun never reshuffles equal rows.
    """
    by_key = {row_key(one): one for one in (components or [])}
    clean_accuracy = _accuracy(effects.clean_logit_difference)

    rows = []
    for key in effects.keys:
        knocked = effects.knocked_logit_difference[key]
        drops = effects.drops(key)
        accuracy = _accuracy(knocked)
        component = by_key.get(key)
        rows.append({
            "key": key,
            "kind": key[0], "layer": key[1], "index": key[2],
            "kv_group": None if component is None else component.kv_group,
            "n": len(drops),
            "mean_drop": _mean(drops),
            "standard_error": _standard_error(drops),
            "knocked_logit_difference": _mean(knocked),
            "accuracy": accuracy,
            "accuracy_drop": (None if accuracy is None or clean_accuracy is None
                              else clean_accuracy - accuracy),
        })

    # Signed, not absolute: a suppressor belongs at the bottom of the ranking
    # rather than beside the mover whose effect it mirrors. `sorted` is stable,
    # so ties keep head-table order.
    rows.sort(key=lambda row: -(row["mean_drop"] if row["mean_drop"] is not None
                                else float("-inf")))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


#: What the head table gains, before the CLI adds the `knockout` namespace.
#: Ticket 03 reads `knockout.rank` to order its per-head charts, so these
#: strings are an interface: rename one and the sibling analysis stops finding
#: the column rather than failing.
COLUMNS = ("logit_diff_drop", "rank", "standard_error", "accuracy")


#: The instance set every knockout column covers, by name, for the head table's
#: coverage meta: the causal sample, as far as the loader could tokenize it.
INSTANCE_SET = CAUSAL_SAMPLE


def columns(rows) -> dict:
    """The head-table update: `{component key: {column: value}}`.

    The CLI namespaces these under `knockout`, so they land as
    `knockout.logit_diff_drop`, `knockout.rank`, `knockout.standard_error` and
    `knockout.accuracy`.
    """
    return {row_key(row["key"]): {
        "logit_diff_drop": row["mean_drop"],
        "rank": row["rank"],
        "standard_error": row["standard_error"],
        "accuracy": row["accuracy"],
    } for row in rows}


def plan_of_effects(effects: Effects) -> "KnockoutPlan":
    """The plan an `Effects` was measured under (v1's when it does not say)."""
    plan = effects.plan or {}
    return KnockoutPlan(scheme=plan.get("scheme", effects.scheme),
                        counterfactual=plan.get("counterfactual") or COUNTERFACTUAL,
                        positions=plan.get("positions", POSITIONS))


#: The direction a cell's Target points, by the records' `condition`. On H and
#: F the Target is the honest item, so a positive drop there means the
#: Component supports the HONEST answer (ADR-0002 native sign; spec §2.2).
TARGET_DIRECTION = {"deceptive": "deceptive", "inversion": "deceptive",
                    "honest": "honest", "nopressure": "honest"}


def payload(effects: Effects, *, circuit: str, task: str, components=None,
            rows=None, target_direction: Optional[str] = None,
            extra: Optional[dict] = None, record_plan: bool = False) -> dict:
    """`knockout.json`: the ranked table, the clean run, and what it all means.

    `rows` is the ranking when the caller already has it, so that the table in
    the file and the table the head-table columns and the figure are built from
    are one object rather than three rankings that could disagree.

    `record_plan` (a v2 cell or a non-default plan, `records_more`) adds
    `plan`, `target_direction`, `counterfactual_run` and
    `unpaired_instance_ids` (mechanism-analysis 02a), states the sign in the
    cell's own target direction, and lets `extra` add a caller's own record
    (the mean bank, the per-instance sidecar's name). Without it the payload
    is the one v1 always wrote, key for key.
    """
    rows = summarize(effects, components) if rows is None else list(rows)
    plan = plan_of_effects(effects)
    recorded = {}
    if record_plan:
        recorded = {"plan": plan.describe(),
                    "target_direction": target_direction,
                    "counterfactual_run": counterfactual_run(effects),
                    "unpaired_instance_ids": list(effects.unpaired),
                    **(extra or {})}
    sign = ("drop = clean logit difference - knocked-out logit "
            "difference, so a positive drop means the Component helps "
            "deception and a negative one means it opposes it")
    if record_plan:
        sign = ("drop = clean logit difference - knocked-out logit "
                "difference, in the cell's own target direction "
                "(target_direction: deceptive on D and I, honest on H and F), "
                "so a positive drop means the Component supports the Target")
    return {
        "analysis": NAME,
        "circuit": circuit,
        "task": task,
        "scheme": effects.scheme,
        "metric": {
            "name": "logit(Target) - logit(Distractor) at the Readout",
            "readout": "fp32 final norm and unembedding (ADR-0001)",
            "sign": sign,
            "accuracy": ("share of sampled instances whose Target still "
                         "outscores its Distractor; not a full-vocabulary "
                         "argmax"),
            "ablation": ablation_sentence(plan),
            "figure": PNG_NAME,
        },
        "n_components": len(rows),
        "instances": effects.ids,
        "sample": {key: value for key, value in effects.report.items()
                   if key in SAMPLE_FIELDS},
        "clean_run": clean_run(effects),
        # JSON keys are strings, so a key is written as a list and read back
        # with `head_table.row_key`.
        "components": [{**row, "key": list(row["key"])} for row in rows],
        **recorded,
    }


# ==============================================================================
# THE FORWARD LOOP
# ==============================================================================

def knockout_effects(model, batches, components, *,
                     scheme=SCHEME, plan=None, segmentations=None,
                     mean_bank=None) -> Effects:
    """Knock out each Component alone, over every batch, and keep every number.

    Three kinds of forward per batch: one clean run to measure against, one
    corrupt run that captures what each Component carried there, and one run
    per Component with that capture written over the clean stream. So a batch
    costs `len(components) + 2` passes and nothing is recomputed per Component.

    The knocked-out run is `capture_forward` rather than `replace_forward`
    because only the capture hands back the residual the final norm sees, and
    the metric has to be read from it in fp32.
    """
    keys = [row_key(one) for one in components]
    return knock_out_groups(model, batches, [(key, [key]) for key in keys],
                            scheme=scheme, plan=plan, segmentations=segmentations,
                            mean_bank=mean_bank)


def _by_id(segmentations) -> Optional[dict]:
    """`{instance id: Segmentation}` from a list or a dict, or None."""
    if segmentations is None:
        return None
    if isinstance(segmentations, dict):
        return segmentations
    return {one.record_id: one for one in segmentations}


def _fill(key, *, scheme, mean_bank, n, seq, shape, dtype, device):
    """The `[n, seq, dim]` value a mean or zero knockout writes at `key`."""
    import torch

    dim = shape["head_dim"] if key[0] == "head" else shape["hidden_size"]
    if scheme == "zero":
        return torch.zeros((n, seq, dim), dtype=dtype, device=device)
    if key not in mean_bank:
        raise KeyError(f"the mean bank has no entry for {key}; collect it over "
                       f"every Component the run knocks out")
    mean = mean_bank[key]
    if mean.shape != (dim,):
        raise ValueError(f"the mean bank's {key} has shape {tuple(mean.shape)}, "
                         f"expected ({dim},)")
    return mean.to(dtype=dtype, device=device).reshape(1, 1, dim) \
        .expand(n, seq, dim).contiguous()


def knock_out_groups(model, batches, groups, *, scheme=SCHEME, plan=None,
                     segmentations=None, mean_bank=None) -> Effects:
    """Knock out each *group* of Components together, and keep every number.

    `groups` is `[(label, [component key, ...]), ...]`. A single-Component
    knockout is the case where every group has one member, which is how
    `knockout_effects` calls it, and a role family is the case where a group
    has several, which is how `family_effects` calls it. One loop, so the
    family numbers are the single numbers' own arithmetic rather than a second
    implementation of the same ablation.

    The two callers make **two calls**, not one, so a run that does both spends
    one extra clean and corrupt pass per batch (about five seconds of a
    two-minute job). Folding them into a single call would save that and would
    also mean splitting one `Effects` back into two afterwards, changing the
    signature ticket 07's tests and ticket 03's `knockout.rank` consumer read.
    The waste is deliberate and it is the cheaper of the two costs.

    A group is ablated by writing the corrupt stream's value over *every* one
    of its members in one forward, so a family's effect is the joint effect and
    not the sum of its members'.

    Per batch: one clean run, one corrupt run capturing every member of every
    group, and one run per group. `Effects.keys` holds the labels in the order
    they were given.

    `plan` (a `KnockoutPlan`; default: `scheme` alone, which is v1's
    knockout) picks the counterfactual stream, the scheme and the positions.
    Under `neutral_twin` only the rows with a twin run, and the others are
    listed in `Effects.unpaired`. A positions plan needs `segmentations`
    (`{id: Segmentation}` or the cell's list) and a mean plan a `mean_bank`
    (`collect_mean_bank`). With the default plan the forwards are exactly the
    ones this function always ran.
    """
    import torch

    from component_analysis import hooks

    plan = plan or KnockoutPlan(scheme=scheme)
    scheme = plan.scheme
    parsed = plan.parsed_positions
    by_id = _by_id(segmentations)
    if parsed["form"] != "all" and by_id is None:
        raise ValueError(f"--knockout-positions {plan.positions} needs the cell's "
                         f"segmentation")
    if scheme == "mean" and mean_bank is None:
        raise ValueError("a mean knockout needs a mean bank (collect_mean_bank)")
    twin = plan.counterfactual == "neutral_twin" and scheme == "interchange"
    groups = [(label, [row_key(one) for one in members])
              for label, members in groups]
    labels = [label for label, _members in groups]
    # Every Component any group ablates, captured once on the corrupt stream:
    # two families that share a member cost one capture, not two.
    keys = []
    for _label, members in groups:
        for key in members:
            if key not in keys:
                keys.append(key)
    # Where the weights actually are, which is not always what `--device` asked
    # for: the CLI seam test runs the tiny model on a CPU under `--device cuda`.
    device, _dtype = hooks.device_and_dtype(model)

    def logit_difference(capture, target, distractor):
        return hooks.target_minus_distractor(
            hooks.readout_logits(model, capture.residual[:, -1, :]),
            target, distractor).tolist()

    ids: List[str] = []
    clean_logit_difference: List[float] = []
    counterfactual_logit_difference: List[float] = []
    twin_margins: List[Optional[float]] = []
    unpaired: List[str] = []
    knocked: Dict[tuple, List[float]] = {label: [] for label in labels}
    shape = hooks.geometry(model) if scheme != "interchange" else None
    model_dtype = hooks.device_and_dtype(model)[1]

    for batch in batches:
        batch_ids = list(batch.ids)
        clean_ids, clean_mask = batch.input_ids, batch.attention_mask
        other_ids, other_mask = batch.corrupt_input_ids, batch.corrupt_attention_mask
        readout = batch.readout
        target, distractor = batch.target_token, batch.distractor_token
        if twin:
            pair = getattr(batch, "neutral_twin", None)
            rows = list(pair.rows) if pair is not None else []
            unpaired.extend(one for row, one in enumerate(batch_ids)
                            if row not in set(rows))
            if not rows:
                continue
            select = torch.tensor(rows, dtype=torch.long)
            batch_ids = [batch_ids[row] for row in rows]
            clean_ids, clean_mask = clean_ids[select], clean_mask[select]
            readout = readout[select]
            target, distractor = target[select], distractor[select]
            other_ids, other_mask = pair.input_ids, pair.attention_mask
            if not torch.equal(other_mask.sum(-1).long() - 1, readout):
                raise ValueError("a Neutral-Clause Twin does not end at its "
                                 "pressure prompt's Readout")
        mask = position_mask(parsed, batch_ids, by_id, readout, clean_ids.shape[1])

        clean_ids, clean_mask = clean_ids.to(device), clean_mask.to(device)
        readout = readout.to(device)
        # The clean stream's assignment on every run: which word is the Target
        # flips between the streams, and a drop measured against the flipped
        # one would be a difference of two different questions.
        target = target.to(device)
        distractor = distractor.to(device)

        with torch.no_grad():
            clean = hooks.capture_forward(model, clean_ids, clean_mask,
                                          components=[], positions=readout)
            if scheme == "interchange":
                corrupt = hooks.capture_forward(model, other_ids.to(device),
                                                other_mask.to(device),
                                                components=keys, positions=readout)
                values = corrupt.outputs
                counterfactual_logit_difference.extend(
                    logit_difference(corrupt, target, distractor))
            else:
                values = {key: _fill(key, scheme=scheme, mean_bank=mean_bank,
                                     n=clean_ids.shape[0], seq=clean_ids.shape[1],
                                     shape=shape, dtype=model_dtype, device=device)
                          for key in keys}
            ids.extend(batch_ids)
            clean_logit_difference.extend(logit_difference(clean, target, distractor))
            if twin:
                twin_margins.extend(counterfactual_logit_difference[-len(batch_ids):])
            elif getattr(batch, "neutral_twin", None) is not None:
                # R19(1): the twin's own margin beside every plan's numbers,
                # one forward per batch; rows without a twin read None.
                pair = batch.neutral_twin
                select = torch.tensor(list(pair.rows), dtype=torch.long,
                                      device=device)
                own = hooks.capture_forward(
                    model, pair.input_ids.to(device), pair.attention_mask.to(device),
                    components=[], positions=readout[select])
                by_row = dict(zip(pair.rows, logit_difference(
                    own, target[select], distractor[select])))
                twin_margins.extend(by_row.get(row) for row in range(len(batch_ids)))
            else:
                twin_margins.extend([None] * len(batch_ids))
            where = None if mask is None else mask.to(device)

            for label, members in groups:
                patched = hooks.capture_forward(
                    model, clean_ids, clean_mask, components=[],
                    positions=readout,
                    replacements={key: (values[key] if where is None else
                                        hooks.Replacement(values[key], positions=where))
                                  for key in members})
                knocked[label].extend(logit_difference(patched, target,
                                                       distractor))
    return Effects(ids=ids, keys=labels,
                   clean_logit_difference=clean_logit_difference,
                   knocked_logit_difference=knocked, scheme=scheme,
                   report=dict(getattr(batches, "report", {}) or {}),
                   counterfactual_logit_difference=counterfactual_logit_difference,
                   plan=plan.describe(), unpaired=unpaired,
                   neutral_twin_logit_difference=(
                       twin_margins if any(one is not None for one in twin_margins)
                       else []))


def collect_mean_bank(model, batches, keys) -> tuple:
    """`({key: [dim] fp32 mean}, info)`: every key's mean over a whole split.

    The evaluator's semantics (`evaluation/ablation.py` `collect_mean_bank`,
    source `pooled`): every unpadded position of every instance, the clean
    prompts and the corrupt prompts both, equal token weight, summed in fp32
    and divided by the token count. `batches` is the cell's descriptive loader
    (its whole test split), so the bank is the cell's own task bank.
    """
    import torch

    from component_analysis import hooks

    keys = [row_key(one) for one in keys]
    device, _dtype = hooks.device_and_dtype(model)
    sums: Dict[tuple, "torch.Tensor"] = {}
    tokens = 0.0
    instances = 0
    for batch in batches:
        instances += len(batch.ids)
        for stream_ids, stream_mask in ((batch.input_ids, batch.attention_mask),
                                        (batch.corrupt_input_ids,
                                         batch.corrupt_attention_mask)):
            stream_mask = stream_mask.to(device)
            with torch.no_grad():
                capture = hooks.capture_forward(model, stream_ids.to(device),
                                                stream_mask, components=keys)
            weight = stream_mask.float().unsqueeze(-1)
            tokens += float(stream_mask.sum())
            for key in keys:
                contribution = (capture.outputs[key].float() * weight).sum(dim=(0, 1))
                sums[key] = contribution if key not in sums else sums[key] + contribution
    if not tokens:
        raise ValueError("the mean bank saw no token; the split is empty")
    bank = {key: total / tokens for key, total in sums.items()}
    return bank, {"source": "pooled", "n_instances": instances,
                  "n_tokens": tokens, "n_keys": len(keys),
                  "semantics": ("per site, every unpadded position of the cell's "
                                "test split, clean and corrupt prompts pooled with "
                                "equal token weight, fp32 accumulation; written "
                                "in the model's dtype (evaluation/ablation.py)")}


# ==============================================================================
# ROLE FAMILIES
# ==============================================================================

#: The grouping column, in the order it is consulted. The researcher's
#: confirmed role wins wherever they have set one; the mechanical proposal
#: (ticket 10, `docs/component-roles.md`) fills in the rest.
ROLE_COLUMNS = ("role_confirmed", "roles.role_proposed")

FAMILY_JSON_NAME = "knockout_families.json"
FAMILY_PNG_NAME = "knockout_families.png"

#: The head-table columns the family pass adds, beside the single knockout's.
#: `role_family`, not `family`: CONTEXT.md already uses "family" for task
#: families and for the STD scenario families, and a bare `knockout.family`
#: holding the word "selector" would be ambiguous against both. The JSON keeps
#: its own key names, which ticket 11's notebook reads.
FAMILY_COLUMNS = ("role_family", "role_family_logit_diff_drop")


def role_of(row) -> Optional[str]:
    """This row's role: confirmed if the researcher set one, else proposed."""
    for column in ROLE_COLUMNS:
        value = row.get(column)
        if value not in (None, ""):
            return str(value)
    return None


def families_from_rows(rows) -> Dict[str, List[tuple]]:
    """`{role: [component key, ...]}` in head-table order.

    A Component with no role at all is left out rather than guessed into a
    family: the roles pass has not run on it, and a family whose membership is
    a default would be a knockout of something nobody named.
    """
    families: Dict[str, List[tuple]] = {}
    for row in rows:
        role = role_of(row)
        if role is None:
            continue
        families.setdefault(role, []).append(row_key(row))
    return families


def family_effects(model, batches, families, *, scheme=SCHEME, plan=None,
                   segmentations=None, mean_bank=None) -> Effects:
    """Ablate every Component of a role, together, one role at a time."""
    return knock_out_groups(model, batches, list(families.items()),
                            scheme=scheme, plan=plan, segmentations=segmentations,
                            mean_bank=mean_bank)


def summarize_families(effects: Effects, families) -> List[dict]:
    """One ranked row per role, strongest drop first, signed like the singles."""
    clean_accuracy = _accuracy(effects.clean_logit_difference)

    rows = []
    for role in effects.keys:
        knocked = effects.knocked_logit_difference[role]
        drops = effects.drops(role)
        accuracy = _accuracy(knocked)
        members = list(families.get(role, []))
        rows.append({
            "role": role,
            "n_components": len(members),
            "members": [list(one) for one in members],
            "n": len(drops),
            "mean_drop": _mean(drops),
            "standard_error": _standard_error(drops),
            "knocked_logit_difference": _mean(knocked),
            "accuracy": accuracy,
            "accuracy_drop": (None if accuracy is None or clean_accuracy is None
                              else clean_accuracy - accuracy),
        })

    rows.sort(key=lambda row: -(row["mean_drop"] if row["mean_drop"] is not None
                                else float("-inf")))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def family_columns(rows) -> dict:
    """`{component key: {role_family, role_family_logit_diff_drop}}` per member."""
    # `members` is written as a list, because a JSON key is not a tuple.
    return {row_key(tuple(member)): {"role_family": row["role"],
                                    "role_family_logit_diff_drop": row["mean_drop"]}
            for row in rows for member in row["members"]}


def family_payload(effects: Effects, families, *, circuit: str, task: str,
                   rows=None, roles_from: str = None, dropped=(),
                   target_direction: Optional[str] = None,
                   extra: Optional[dict] = None, record_plan: bool = False) -> dict:
    """`knockout_families.json`: the same shape and the same signs as the singles."""
    rows = summarize_families(effects, families) if rows is None else list(rows)
    single = payload(effects, circuit=circuit, task=task, rows=[],
                     target_direction=target_direction, extra=extra,
                     record_plan=record_plan)
    return {
        **{key: value for key, value in single.items()
           if key not in ("components", "n_components")},
        "analysis": f"{NAME}_families",
        "grouping": {
            "column": "role_confirmed, else roles.role_proposed",
            "criteria_doc": os.path.join("docs", "component-roles.md"),
            "read_from": roles_from,
            "n_components": sum(len(one) for one in families.values()),
            # Components that carried a role in the source cell but are not in
            # this circuit — the completeness sweep's rows, typically. They are
            # not ablated, and the count is here so the drop is visible.
            "n_outside_this_circuit": len(dropped),
            "outside_this_circuit": [list(one) for one in sorted(dropped)],
        },
        "metric": {**single["metric"],
                   "ablation": (("every Component of the role has its output at "
                                 "every position replaced by the value it "
                                 "carried on the item-swap corrupt stream, all "
                                 "in one forward, so the number is the family's "
                                 "joint effect and not the sum of its members'")
                                if plan_of_effects(effects).is_default else
                                (f"every Component of the role, jointly in one "
                                 f"forward: {ablation_sentence(plan_of_effects(effects))}")),
                   "figure": FAMILY_PNG_NAME},
        "n_families": len(rows),
        "families": rows,
    }


# ==============================================================================
# THE COMPLETENESS SWEEP
# ==============================================================================
#
# The single knockouts rank the circuit's own Components; a Component the
# pruning missed is invisible to them. `--knockout-completeness-sweep` knocks
# out every head and MLP block of the model, one at a time, with the same
# interchange ablation on the same causal sample, through the same
# `knock_out_groups` call — the circuit's singles are read out of the sweep's
# forwards (`Effects.restrict`), so `knockout.json` and `sweep.json` share one
# clean and one corrupt pass per batch and agree to the bit.

SWEEP_JSON_NAME = "sweep.json"
SWEEP_PNG_NAME = "sweep.png"

#: The head-table columns the sweep adds, for circuit Components only. Kept
#: apart from `COLUMNS`, which ticket 03 and the coverage tests pin.
SWEEP_COLUMNS = ("sweep_rank", "sweep_clears_threshold")

#: `--knockout-sweep-threshold`'s default, in **logits** of
#: logit(Target) - logit(Distractor), not a fraction of the clean-minus-corrupt
#: gap as `--path-sweep-threshold` is. Hand-tuned on SDR nls0.3 by the
#: researcher (2026-10-14); what it selects there is recorded in
#: docs/component-roles.md. It is a cut to read the list at, not a finding:
#: `sweep.json` always carries every Component ranked, and `THRESHOLD_LADDER`
#: counts what clears other cuts, so the cut can be moved without a rerun.
DEFAULT_SWEEP_THRESHOLD_LOGITS = 0.4
THRESHOLD_JUSTIFICATION = (
    f"{DEFAULT_SWEEP_THRESHOLD_LOGITS:g} logits, hand-tuned on SDR nls0.3 (the "
    "researcher's 2026-10-14 decision; docs/component-roles.md records what "
    "it selects there). Tune it by hand per run; the full ranked list is "
    "always written in components, so nothing below the cut is hidden")
THRESHOLD_LADDER = (0.02, 0.05, 0.1, 0.2, 0.4)

#: Components the sweep keeps, ranks and draws but never counts as something
#: the circuit missed: the researcher's 2026-10-14 decision on ticket 15's
#: finding that knocking out the layer 0 MLP reverses the margin on SDR
#: nls0.3 (drop +3.12 against a clean 1.66, knocked logit difference about
#: -1.46, accuracy 0.01). Left out of `flagged`,
#: `strongest_outside_circuit` and the ladder's outside count, the way the
#: embedding is left out of the sweep, and labelled on the figure.
POSITIVE_CONTROLS = (("mlp", 0, 0),)
POSITIVE_CONTROL_WHY = (
    "the layer 0 MLP acts as a second embedding: interchange-ablating it "
    "rewrites the corrupted token's representation, much as ablating the "
    "embedding (not swept) would run the corrupt prompt, so its large drop "
    "shows the knockout works rather than a Component the circuit missed")

#: How many Components the bar chart draws; the JSON carries all of them.
SWEEP_BAR_TOP = 40
#: How many of the strongest Components outside the circuit `sweep.json`
#: repeats in `strongest_outside_circuit`, for a reader who wants the answer
#: without walking all of `components`.
STRONGEST_OUTSIDE_TOP = 10


def sweep_size(geometry: dict) -> int:
    """How many Components the sweep knocks out: every head and MLP block."""
    return geometry["num_layers"] * (geometry["num_heads"] + 1)


def sweep_components(model) -> List[tuple]:
    """Every head and MLP block of the model, in run order.

    The model's own sender list less the embedding, which is not a Component:
    interchange-ablating it is running the corrupt prompt.
    """
    from component_analysis import hooks

    return [key for key in hooks.all_component_keys(model)
            if key[0] in ("head", "mlp")]


def sweep_effects(model, batches, *, scheme=SCHEME, plan=None, segmentations=None,
                  mean_bank=None) -> Effects:
    """Knock out every head and MLP block of the model, one at a time.

    `knock_out_groups` with one-member groups, as `knockout_effects` calls it:
    per batch one clean pass, one corrupt pass capturing every Component, and
    one pass per Component.
    """
    return knockout_effects(model, batches, sweep_components(model),
                            scheme=scheme, plan=plan, segmentations=segmentations,
                            mean_bank=mean_bank)


def parse_component_labels(value) -> List[tuple]:
    """`head.17.24,mlp.0.0` (the sweep's own spelling) as Component keys."""
    out = []
    for text in [one.strip() for one in str(value).split(",") if one.strip()]:
        parts = text.split(".")
        if len(parts) != 3 or parts[0] not in ("head", "mlp") or \
                not parts[1].isdigit() or not parts[2].isdigit():
            raise UnsupportedScheme(
                f"{text!r} is not a Component label; write head.<layer>.<index> "
                f"or mlp.<layer>.0, as sweep.json does")
        out.append((parts[0], int(parts[1]), int(parts[2])))
    return out


def summarize_sweep(effects: Effects, circuit_keys, *, threshold: float,
                    heads_per_group: Optional[int] = None,
                    exclude_from_ranking=()) -> List[dict]:
    """Every Component, ranked by the size of its drop, circuit marked.

    Ranked by **|drop|**, not by the signed drop `knockout.rank` uses: the
    sweep asks which Components matter that the circuit lacks, and a strong
    suppressor outside the circuit is one of those answers. The sign stays in
    `mean_drop` (positive helps deception) and `signed_rank` is knockout's own
    ranking of the same rows. `flagged` is a Component outside the circuit
    whose |drop| is at least `threshold` and that is not a positive control
    (`POSITIVE_CONTROLS`); a positive control stays ranked and is marked.

    `exclude_from_ranking` (R11(a): the layer-0 MLP of a neutral-twin sweep)
    keeps a Component's numbers and takes it out of the ranking: `rank` None,
    never flagged, `excluded_from_ranking` true. Without it the rows are the
    rows this function always wrote.
    """
    excluded = {row_key(one) for one in exclude_from_ranking}
    inside = {row_key(one) for one in circuit_keys}
    signed = summarize(effects)
    for row in signed:
        row["signed_rank"] = row.pop("rank")

    def strength(row):
        return abs(row["mean_drop"]) if row["mean_drop"] is not None else -1.0

    # `summarize` returns the signed order; re-sort from the run's own key
    # order so that ties keep model order rather than the signed order.
    by_key = {row["key"]: row for row in signed}
    rows = sorted((by_key[key] for key in effects.keys), key=strength,
                  reverse=True)
    if excluded:
        rows = ([row for row in rows if row["key"] not in excluded]
                + [row for row in rows if row["key"] in excluded])
    rank = 0
    for row in rows:
        key = row["key"]
        measured = row["mean_drop"] is not None
        ranked = measured and key not in excluded
        rank += 1 if ranked else 0
        se = row["standard_error"]
        row.update({
            "label": component_label(key),
            "rank": rank if ranked else None,
            "kv_group": (key[2] // heads_per_group
                         if heads_per_group and key[0] == "head" else None),
            "in_circuit": key in inside,
            "positive_control": key in POSITIVE_CONTROLS,
            "z": (row["mean_drop"] / se) if measured and se else None,
            "clears_threshold": measured and abs(row["mean_drop"]) >= threshold,
        })
        row["flagged"] = row["clears_threshold"] and counts_as_outsider(row)
        if excluded:
            row["excluded_from_ranking"] = key in excluded
            row["flagged"] = row["flagged"] and key not in excluded
    return rows


def counts_as_outsider(row) -> bool:
    """A Component outside the circuit that is not a positive control: what
    `flagged`, `strongest_outside_circuit` and the ladder's outside count
    are about."""
    return not row["in_circuit"] and not row["positive_control"]


def sweep_columns(rows) -> dict:
    """`{circuit Component key: {sweep_rank, sweep_clears_threshold}}`.

    Circuit Components only. A Component outside the circuit stays in
    `sweep.json`, flagged or not, and never becomes a head-table row: the
    table is the circuit's.
    """
    return {row_key(row["key"]): {"sweep_rank": row["rank"],
                                  "sweep_clears_threshold": row["clears_threshold"]}
            for row in rows if row["in_circuit"]}


def threshold_counts(rows, ladder=THRESHOLD_LADDER) -> List[dict]:
    """How many Components, inside and outside the circuit, clear each cut.

    A positive control is in neither count's outside half: it is not a
    Component the circuit missed.
    """
    out = []
    for cut in ladder:
        clearing = [row for row in rows if row["mean_drop"] is not None
                    and abs(row["mean_drop"]) >= cut]
        out.append({"threshold": cut,
                    "outside_circuit": sum(1 for row in clearing
                                           if counts_as_outsider(row)),
                    "in_circuit": sum(1 for row in clearing if row["in_circuit"])})
    return out


def sweep_payload(effects: Effects, rows, *, circuit: str, task: str,
                  threshold: float, cost: Optional[dict] = None,
                  target_direction: Optional[str] = None,
                  extra: Optional[dict] = None, record_plan: bool = False) -> dict:
    """`sweep.json`: every Component ranked, and the twin of `sweep.png`."""
    single = payload(effects, circuit=circuit, task=task, rows=[],
                     target_direction=target_direction, extra=extra,
                     record_plan=record_plan)
    rows = list(rows)
    shown = [row for row in rows if row["rank"] is not None][:SWEEP_BAR_TOP]
    as_json = [{**row, "key": list(row["key"])} for row in rows]
    return {
        **{key: value for key, value in single.items()
           if key not in ("components", "n_components")},
        "analysis": NAME,
        "pass": "completeness_sweep",
        "metric": {**single["metric"],
                   "ranking": ("rank is by |drop|, strongest first, so a "
                               "Component that opposes deception ranks beside "
                               "one that helps it; the sign is in mean_drop. "
                               "signed_rank is knockout's own ranking (rank 1 "
                               "helps deception most), the one knockout.rank "
                               "uses inside the circuit"),
                   "figure": SWEEP_PNG_NAME},
        "threshold": threshold,
        "threshold_units": ("logits of logit(Target) - logit(Distractor), not "
                            "a fraction of the clean-minus-corrupt gap"),
        "threshold_flag": "--knockout-sweep-threshold",
        "threshold_justification": THRESHOLD_JUSTIFICATION,
        "threshold_is_not_a_significance_test": (
            "a fixed cut on |mean_drop| over every Component; read each "
            "row's z (mean_drop / standard_error) beside it, and "
            "threshold_counts for other cuts"),
        "excludes": ("the embedding: interchange-ablating it is running the "
                     "corrupt prompt, so it is not a Component knockout. The "
                     "path-patching sweep counts it as a sender, which is why "
                     "that sweep has one more entry"),
        "head_table_columns": {
            "knockout.sweep_rank": ("this sweep's rank by |drop| among every "
                                    "Component of the model; circuit rows only"),
            "knockout.sweep_clears_threshold": ("|drop| >= threshold; circuit "
                                                "rows only"),
            "knockout.rank": ("for contrast: the signed rank among the "
                              "circuit's Components alone (rank 1 helps "
                              "deception most); signed_rank here is the same "
                              "rule over every Component"),
        },
        "flagged_means": ("outside the circuit, not a positive control, and "
                          "|mean_drop| >= threshold; listed here, never added "
                          "to the head table"),
        "positive_controls": {
            "components": [row["label"] for row in rows
                           if row["positive_control"]],
            "why": POSITIVE_CONTROL_WHY,
            "treatment": ("kept in components, ranked and drawn, marked "
                          "positive_control; left out of flagged, "
                          "strongest_outside_circuit and threshold_counts' "
                          "outside_circuit, as the embedding is left out of "
                          "the sweep"),
        },
        "n_components": len(rows),
        "n_in_circuit": sum(1 for row in rows if row["in_circuit"]),
        "flagged": [row["label"] for row in rows if row["flagged"]],
        "threshold_counts": threshold_counts(rows),
        "strongest_outside_circuit": [
            {**row, "key": list(row["key"])} for row in rows
            if counts_as_outsider(row)
            and row["rank"] is not None][:STRONGEST_OUTSIDE_TOP],
        "figure": {"file": SWEEP_PNG_NAME, "n_shown": len(shown),
                   "shows": f"the {len(shown)} strongest by |drop|, circuit "
                            f"Components highlighted, a positive control "
                            f"hatched and labelled"},
        "cost": cost or {},
        "components": as_json,
    }


# ==============================================================================
# NAMED GROUPS AND GREEDY SELECTION (mechanism-analysis 02a, R11, R16)
# ==============================================================================

GROUPS_JSON_NAME = "groups.json"
GREEDY_JSON_NAME = "greedy.json"

#: Per-instance sidecars (R19(1)), one per pass that writes them, so the
#: summary files keep their shapes: per instance the clean margin, the
#: knocked margin per group and the counterfactual stream's own margin.
INSTANCES_SUFFIX = "_instances.json"

#: Greedy defaults (spec §2.3): the top 50 of the S2p ranking, up to k = 20.
DEFAULT_GREEDY_POOL_SIZE = 50
DEFAULT_GREEDY_K_MAX = 20


def load_groups(path: str) -> List[tuple]:
    """`[(name, [key, ...]), ...]` from `{name: [[kind, layer, index], ...]}`.

    Keys are written in `head_table.row_key` order, (kind, layer, index), and
    each group is knocked out jointly. Refused by name: an empty group, a
    malformed key, a kind that is not a Component, a key named twice.
    """
    with open(path) as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{path}: a groups file is a non-empty JSON object "
                         f"{{name: [[kind, layer, index], ...]}}")
    out = []
    for name, members in raw.items():
        if not isinstance(members, list) or not members:
            raise ValueError(f"{path}: group {name!r} names no Component")
        keys = []
        for member in members:
            if not isinstance(member, list) or len(member) != 3:
                raise ValueError(f"{path}: group {name!r} has {member!r}; each "
                                 f"member is [kind, layer, index]")
            key = row_key(tuple(member))
            if key[0] not in ("head", "mlp"):
                raise ValueError(f"{path}: group {name!r} has {member!r}; a "
                                 f"Component is a head or mlp")
            if key in keys:
                raise ValueError(f"{path}: group {name!r} names {member!r} twice")
            keys.append(key)
        out.append((str(name), keys))
    return out


def check_groups(groups, geometry: dict) -> None:
    """Every member must be a Component of this model (layers, heads, MLP 0)."""
    for name, keys in groups:
        for kind, layer, index in keys:
            if not 0 <= layer < geometry["num_layers"]:
                raise ValueError(f"group {name!r}: layer {layer} is outside the "
                                 f"model's {geometry['num_layers']} layers")
            limit = geometry["num_heads"] if kind == "head" else 1
            if not 0 <= index < limit:
                raise ValueError(f"group {name!r}: {kind} index {index} is "
                                 f"outside 0..{limit - 1}")


def file_digest(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _model_order(key) -> tuple:
    return (key[1], 0 if key[0] == "head" else 1, key[2])


def greedy_pool(sweep_path: str, *, size: int) -> List[tuple]:
    """The top `size` Components of a sweep, by signed drop, strongest first.

    Signed, because R-AB looks for Components whose knockout REMOVES the
    deceptive margin (positive drop); a strong negative drop is not a
    mediator. The layer-0 MLP (the Positive Control) and any row the sweep
    excluded from ranking never enter. Ties go to model order.
    """
    with open(sweep_path) as handle:
        sweep = json.load(handle)
    rows = [row for row in sweep["components"]
            if row.get("mean_drop") is not None
            and not row.get("excluded_from_ranking")
            and row_key(tuple(row["key"])) not in POSITIVE_CONTROLS]
    rows.sort(key=lambda row: (-row["mean_drop"],
                               _model_order(row_key(tuple(row["key"])))))
    return [row_key(tuple(row["key"])) for row in rows[:size]]


def greedy_select(pool, evaluate, *, k_max: int) -> List[dict]:
    """Greedy joint selection: each step adds the Component with the largest
    joint drop together with the ones already chosen.

    `evaluate(groups)` takes a list of member lists and returns one
    `(joint drop, payload)` per group, in order; the payload of the chosen
    group is kept on its step (the real evaluator passes the run's per-instance
    numbers). Ties go to the earlier Component in `pool`. Stops at `k_max` or
    when the pool is spent.
    """
    pool = [row_key(one) for one in pool]
    chosen: List[tuple] = []
    steps = []
    while len(chosen) < min(k_max, len(pool)):
        remaining = [key for key in pool if key not in chosen]
        results = evaluate([chosen + [key] for key in remaining])
        best = max(range(len(remaining)), key=lambda i: (results[i][0], -i))
        chosen = chosen + [remaining[best]]
        steps.append({"k": len(chosen), "added": remaining[best],
                      "members": list(chosen), "joint_drop": results[best][0],
                      "payload": results[best][1],
                      "candidates": [{"key": key, "joint_drop": result[0]}
                                     for key, result in zip(remaining, results)]})
    return steps


def group_rows(effects: Effects, groups) -> List[dict]:
    """One row per named group: the single knockout's statistics, joint."""
    clean_accuracy = _accuracy(effects.clean_logit_difference)
    members = dict(groups)
    rows = []
    for label in effects.keys:
        drops = effects.drops(label)
        knocked = effects.knocked_logit_difference[label]
        accuracy = _accuracy(knocked)
        rows.append({
            "name": label, "n_components": len(members.get(label, [])),
            "members": [component_label(key) for key in members.get(label, [])],
            "n": len(drops), "mean_drop": _mean(drops),
            "standard_error": _standard_error(drops),
            "knocked_logit_difference": _mean(knocked), "accuracy": accuracy,
            "accuracy_drop": (None if accuracy is None or clean_accuracy is None
                              else clean_accuracy - accuracy)})
    return rows


def counterfactual_run(effects: Effects) -> dict:
    """The counterfactual stream's own margin, in the clean labels' direction."""
    values = effects.counterfactual_logit_difference
    return {"mean_logit_difference": _mean(values),
            "standard_error": _standard_error(values),
            "accuracy": _accuracy(values), "n_instances": len(values),
            "means": ("the full model on the counterfactual stream (item-swap "
                      "corrupt prompt, or the Neutral-Clause Twin) read with the "
                      "clean stream's Target and Distractor; empty under mean and "
                      "zero, which run no counterfactual stream")}


def instances_payload(effects: Effects, *, what: str, label=str) -> dict:
    """A per-instance sidecar: every number the summaries were computed from."""
    return {
        "analysis": NAME, "pass": what, "plan": effects.plan,
        "sign": ("drop = clean - knocked, in the cell's own target direction "
                 "(deceptive on D and I, honest on H and F)"),
        "instance_ids": list(effects.ids),
        "clean_logit_difference": list(effects.clean_logit_difference),
        "counterfactual_logit_difference": list(
            effects.counterfactual_logit_difference),
        "neutral_twin_logit_difference": list(effects.neutral_twin_logit_difference),
        "margins": ("every list is per instance in instance_ids order and reads "
                    "logit(Target) - logit(Distractor) with the clean stream's "
                    "labels: clean = the cell's own prompt; knocked = under each "
                    "knockout; counterfactual = the stream an interchange copies "
                    "from (empty under mean and zero); neutral_twin = the "
                    "Neutral-Clause Twin's own margin (R19(1); null for a row "
                    "with no twin, empty on a cell with none)"),
        "knocked_logit_difference": {label(key): list(values) for key, values
                                     in effects.knocked_logit_difference.items()},
        "unpaired_instance_ids": list(effects.unpaired),
    }


# ==============================================================================
# THE FIGURE
# ==============================================================================

def _short_label(row) -> str:
    """`L12 H7` for a head, `L12 MLP` for an MLP block: the per-Component
    and family charts' tick spelling. The sweep's chart and JSON use
    `component_label` (`head.12.7`) instead, so its PNG and its twin agree."""
    if row["kind"] == "mlp":
        return f"L{row['layer']} MLP"
    return f"L{row['layer']} H{row['index']}"


def write_figure(path: str, rows, *, title: str = "") -> str:
    """The ranked bar chart: one bar per Component, coloured by layer.

    Horizontal bars, because eighteen Components need readable names, ordered
    by the signed drop so the deception-helping Components are at the top and
    any suppressor is at the bottom on the other side of the zero line. The
    colour carries the layer, which is a magnitude, so it is one hue from light
    to dark with a colorbar rather than a categorical set — a rainbow here would
    invent a category boundary between layer 11 and layer 12. Error bars are
    the standard error over the causal sample.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = list(rows)
    if not rows:
        raise ValueError("no Component to plot; the knockout scored none")

    layers = [row["layer"] for row in rows]
    lowest, highest = min(layers), max(layers)
    span = (highest - lowest) or 1
    # One hue, light to dark, because the layer is a magnitude: a rainbow would
    # invent a category boundary between layer 11 and layer 12. A band of the
    # ramp, not the whole of it — below about a third of the way up the fill is
    # too pale to read against white — and the colorbar is drawn from the same
    # band, so the key and the bars are the same colours.
    ramp = plt.get_cmap("Blues")
    band = matplotlib.colors.LinearSegmentedColormap.from_list(
        "layers", [ramp(0.35 + 0.6 * step / 255) for step in range(256)])
    colors = [band((layer - lowest) / span) for layer in layers]

    height = max(2.5, 0.34 * len(rows) + 1.4)
    figure, axes = plt.subplots(figsize=(8.0, height))
    positions = range(len(rows))
    axes.barh(list(positions), [row["mean_drop"] for row in rows],
              xerr=[row["standard_error"] or 0.0 for row in rows],
              color=colors, edgecolor="none", height=0.68,
              error_kw={"ecolor": "#5b6670", "elinewidth": 1.0, "capsize": 2.5})
    axes.set_yticks(list(positions))
    axes.set_yticklabels([_short_label(row) for row in rows], fontsize=9)
    axes.invert_yaxis()                      # rank 1 at the top
    axes.axvline(0.0, color="#333a40", linewidth=1.0)
    axes.set_xlabel("drop in logit(Target) - logit(Distractor)\n"
                    "(positive: the Component helps deception)", fontsize=9)
    axes.set_title(title or "Per-Component interchange knockout", fontsize=11)
    axes.grid(axis="x", color="#d6dade", linewidth=0.6)
    axes.set_axisbelow(True)
    for edge in ("top", "right", "left"):
        axes.spines[edge].set_visible(False)
    axes.tick_params(axis="both", length=0, labelsize=9)

    normalizer = matplotlib.colors.Normalize(vmin=lowest, vmax=highest)
    bar = figure.colorbar(
        matplotlib.cm.ScalarMappable(norm=normalizer, cmap=band), ax=axes,
        fraction=0.035, pad=0.02)
    bar.set_label("layer", fontsize=9)
    bar.outline.set_visible(False)

    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path


def write_family_figure(path: str, rows, *, title: str = "") -> str:
    """The ranked bar chart of role families, on the singles' sign convention.

    One bar per role, ordered by the signed drop so a family that opposes
    deception sits at the bottom on the other side of the zero line, exactly as
    a suppressing Component does in the per-Component chart. The bar is
    labelled with the family's size, because "unknown, 16 Components" and
    "mover, 1" are not the same claim and the chart would otherwise invite the
    reader to compare them as if they were.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = list(rows)
    if not rows:
        raise ValueError("no family to plot; no Component carries a role")

    labels = [f"{row['role']}  ({row['n_components']})" for row in rows]
    height = max(2.2, 0.5 * len(rows) + 1.4)
    figure, axes = plt.subplots(figsize=(7.5, height))
    positions = range(len(rows))
    axes.barh(list(positions), [row["mean_drop"] for row in rows],
              xerr=[row["standard_error"] or 0.0 for row in rows],
              color="#4c72a8", edgecolor="none", height=0.6,
              error_kw={"ecolor": "#5b6670", "elinewidth": 1.0, "capsize": 2.5})
    axes.set_yticks(list(positions))
    axes.set_yticklabels(labels, fontsize=9)
    axes.invert_yaxis()
    axes.axvline(0.0, color="#333a40", linewidth=1.0)
    axes.set_xlabel("drop in logit(Target) - logit(Distractor)\n"
                    "(positive: the family helps deception)", fontsize=9)
    axes.set_title(title or "Interchange knockout by Component Role family",
                   fontsize=11)
    axes.grid(axis="x", color="#d6dade", linewidth=0.6)
    axes.set_axisbelow(True)
    for edge in ("top", "right", "left"):
        axes.spines[edge].set_visible(False)
    axes.tick_params(axis="both", length=0, labelsize=9)

    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path


#: Circuit bars and the rest. Told apart by lightness as well as hue, so the
#: highlight survives a blue-light filter and a greyscale print: a dark
#: burnt orange against a light grey, and the circuit's tick labels in bold.
SWEEP_CIRCUIT_COLOUR = "#b4471b"
SWEEP_OTHER_COLOUR = "#b9c0c7"
#: A positive control keeps its circuit or non-circuit fill and gains a hatch
#: and a label, so the mark survives the same filter and greyscale print.
SWEEP_CONTROL_HATCH = "////"
SWEEP_CONTROL_SUFFIX = " (positive control)"


def write_sweep_figure(path: str, rows, *, threshold: float,
                       title: str = "") -> str:
    """The strongest `SWEEP_BAR_TOP` Components by |drop|, circuit highlighted.

    Horizontal bars in rank order, signed, so a Component that opposes
    deception sits left of zero; dotted lines at plus and minus the threshold;
    a positive control hatched, with "(positive control)" on its tick. Every
    number drawn is a row of `sweep.json`.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    top = [row for row in rows if row["rank"] is not None][:SWEEP_BAR_TOP]
    if not top:
        raise ValueError("no Component to plot; the sweep scored none")

    height = max(2.5, 0.26 * len(top) + 1.6)
    figure, axes = plt.subplots(figsize=(8.0, height))
    positions = list(range(len(top)))
    bars = axes.barh(positions, [row["mean_drop"] for row in top],
                     xerr=[row["standard_error"] or 0.0 for row in top],
                     color=[SWEEP_CIRCUIT_COLOUR if row["in_circuit"]
                            else SWEEP_OTHER_COLOUR for row in top],
                     edgecolor="none", height=0.7,
                     error_kw={"ecolor": "#4a525a", "elinewidth": 0.9,
                               "capsize": 2})
    controls = [row["positive_control"] for row in top]
    for bar, control in zip(bars, controls):
        if control:
            bar.set_hatch(SWEEP_CONTROL_HATCH)
            bar.set_edgecolor("#4a525a")
    axes.set_yticks(positions)
    axes.set_yticklabels([row["label"] + (SWEEP_CONTROL_SUFFIX if control
                                          else "")
                          for row, control in zip(top, controls)], fontsize=8)
    for tick, row in zip(axes.get_yticklabels(), top):
        if row["in_circuit"]:
            tick.set_fontweight("bold")
    axes.invert_yaxis()
    axes.axvline(0.0, color="#333a40", linewidth=1.0)
    for sign in (1, -1):
        axes.axvline(sign * threshold, color="#333a40", linewidth=0.8,
                     linestyle=":")
    axes.set_xlabel("drop in logit(Target) - logit(Distractor)\n"
                    "(positive: the Component helps deception; dotted: "
                    f"threshold {threshold:g})", fontsize=9)
    axes.set_title(title or "Knockout completeness sweep", fontsize=10)
    handles = [Patch(color=SWEEP_CIRCUIT_COLOUR, label="in the circuit"),
               Patch(color=SWEEP_OTHER_COLOUR, label="not in the circuit")]
    if any(controls):
        handles.append(Patch(facecolor="white", edgecolor="#4a525a",
                             hatch=SWEEP_CONTROL_HATCH,
                             label="positive control, not counted as missed"))
    axes.legend(handles=handles, loc="lower right", fontsize=8, frameon=False)
    axes.grid(axis="x", color="#d6dade", linewidth=0.6)
    axes.set_axisbelow(True)
    for edge in ("top", "right", "left"):
        axes.spines[edge].set_visible(False)
    axes.tick_params(axis="both", length=0, labelsize=8)

    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path


# ==============================================================================
# THE ANALYSIS
# ==============================================================================

def _non_negative(value) -> float:
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError(
            f"--knockout-sweep-threshold is a size of drop and cannot be "
            f"negative; got {value}")
    return number


def _positive_int(value) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value}")
    return number


def add_arguments(group) -> None:
    group.add_argument("--knockout-scheme", type=resolve_scheme, default=SCHEME,
                       help="How a Component is ablated: interchange (copy the "
                            "counterfactual stream's value), mean (the site's "
                            "mean over the cell's test split, clean and corrupt "
                            "pooled; the evaluator's semantics) or zero.")
    group.add_argument("--knockout-counterfactual", type=resolve_counterfactual,
                       default=COUNTERFACTUAL,
                       help="The stream an interchange knockout copies from: "
                            "item_swap (the corrupt prompt) or neutral_twin "
                            "(the v2 Neutral-Clause Twin, D's labels kept; D "
                            "and I cells only).")
    group.add_argument("--knockout-positions", type=parse_positions,
                       default=parse_positions(POSITIONS),
                       metavar="all|readout|SEGMENT|after=SEGMENT[,exclude=readout]",
                       help="Where the knockout writes. 'after=pressure_clause,"
                            "exclude=readout' is the spec's post-clause range. "
                            "Applies to every pass of the run.")
    group.add_argument("--knockout-singles", choices=["on", "off"], default="on",
                       help="Run the per-Component pass over the circuit's "
                            "Components (knockout.json and the head-table "
                            "columns). 'off' for a run that only does --knockout-"
                            "groups or --knockout-greedy-pool; a sweep always "
                            "writes the singles, read from its own forwards.")
    group.add_argument("--knockout-families", action="store_true",
                       help="Also knock out every Component of a Component "
                            "Role together, one role at a time. Roles come "
                            "from role_confirmed where the researcher has set "
                            "one and from roles.role_proposed otherwise, so "
                            "`analyze_components.py roles` must have run on "
                            "the cell this reads them from.")
    group.add_argument("--knockout-roles-from", default=None, metavar="CELL_DIR",
                       help="Where the role columns are read from. Default: "
                            "this cell's own head table, which is the case "
                            "where the roles pass has already run here. Every "
                            "run rebuilds the head table from the intake's "
                            "rows, so the role columns this pass grouped by "
                            "are copied back into the table it writes; roles "
                            "for Components outside this circuit are dropped "
                            "and counted in knockout_families.json.")
    group.add_argument("--knockout-completeness-sweep", action="store_true",
                       help="Also knock out every head and MLP block of the "
                            "whole model, one at a time, on the same causal "
                            "sample, and write knockout/sweep.json and "
                            "sweep.png ranked by |drop| with circuit "
                            "membership marked. The circuit's own single "
                            "knockouts are read from the same forwards. One "
                            "forward per Component plus the shared clean and "
                            "corrupt passes per batch: 1056 + 2 = 1058 on "
                            "Llama-3.1-8B; --dry-run prints the cost.")
    group.add_argument("--knockout-sweep-threshold", type=_non_negative,
                       default=DEFAULT_SWEEP_THRESHOLD_LOGITS,
                       help="A Component outside the circuit whose |drop| "
                            "is at least this many logits is listed as "
                            "flagged in sweep.json (never added to the head "
                            "table). Logits of logit(Target) - "
                            "logit(Distractor), not a fraction of the gap "
                            "like --path-sweep-threshold. Default "
                            f"{DEFAULT_SWEEP_THRESHOLD_LOGITS:g}, hand-tuned on "
                            "SDR nls0.3; tune it by hand per run. The full "
                            "ranked list of "
                            "every Component is always written to sweep.json, "
                            "so the cut hides nothing.")
    group.add_argument("--knockout-sweep-exclude", type=parse_component_labels,
                       default=[], metavar="LABEL[,LABEL]",
                       help="Components the sweep measures but leaves out of its "
                            "ranking and its flags, e.g. mlp.0.0 (the Positive "
                            "Control, R11(a)). Their numbers stay in sweep.json.")
    group.add_argument("--knockout-groups", default=None, metavar="FILE",
                       help="Knock out each named set jointly: JSON "
                            "{name: [[kind, layer, index], ...]}. Writes "
                            "knockout/groups.json and a per-instance sidecar.")
    group.add_argument("--knockout-greedy-pool", default=None, metavar="SWEEP_JSON",
                       help="Greedy joint selection over the top of this "
                            "sweep.json (signed drop, layer-0 MLP and excluded "
                            "rows left out): each step adds the Component with "
                            "the largest joint drop. Writes knockout/greedy.json.")
    group.add_argument("--knockout-greedy-pool-size", type=_positive_int,
                       default=DEFAULT_GREEDY_POOL_SIZE,
                       help="How many of the sweep's top Components the greedy "
                            "search draws from.")
    group.add_argument("--knockout-greedy-k-max", type=_positive_int,
                       default=DEFAULT_GREEDY_K_MAX,
                       help="The largest set the greedy search builds.")
    group.add_argument("--knockout-per-instance", action="store_true",
                       help="Write the per-instance sidecar of the singles and "
                            "the sweep. Always on for a v2 cell and for any "
                            "non-default scheme, counterfactual or positions; "
                            "groups and greedy always write theirs.")


def plan_of(ctx) -> KnockoutPlan:
    """The scheme, counterfactual and positions this run asked for."""
    positions = getattr(ctx.cli, "knockout_positions", POSITIONS)
    if isinstance(positions, dict):
        positions = positions["text"]
    return KnockoutPlan(scheme=getattr(ctx.cli, "knockout_scheme", SCHEME),
                        counterfactual=getattr(ctx.cli, "knockout_counterfactual",
                                               COUNTERFACTUAL),
                        positions=positions)


def scheme_of(ctx) -> str:
    """The ablation scheme this run asked for, resolved."""
    return resolve_scheme(getattr(ctx.cli, "knockout_scheme", SCHEME))


def sweeping(ctx) -> bool:
    """Whether `--knockout-completeness-sweep` was given."""
    return bool(getattr(ctx.cli, "knockout_completeness_sweep", False))


def singles_on(ctx) -> bool:
    return getattr(ctx.cli, "knockout_singles", "on") == "on" or sweeping(ctx)


def sweep_threshold(ctx) -> float:
    """Which Components outside the circuit the sweep flags, in logits.

    `--knockout-sweep-threshold`, defaulting to `DEFAULT_SWEEP_THRESHOLD_LOGITS`.
    """
    return float(getattr(ctx.cli, "knockout_sweep_threshold",
                         DEFAULT_SWEEP_THRESHOLD_LOGITS))


def sweep_exclusions(ctx) -> List[tuple]:
    return list(getattr(ctx.cli, "knockout_sweep_exclude", None) or [])


def is_v2_cell(ctx) -> bool:
    from component_analysis.dataloaders import V2_TASKS

    return getattr(ctx.task_spec, "name", None) in V2_TASKS


def records_more(ctx, plan: KnockoutPlan) -> bool:
    """A v2 cell or a non-default plan: write the sidecars, the coverage
    details and the H100 estimate. A v1 cell under v1's plan writes exactly
    the files and the meta it always did."""
    return is_v2_cell(ctx) or not plan.is_default or \
        bool(getattr(ctx.cli, "knockout_per_instance", False))


def roles_source(ctx) -> str:
    """The cell whose head table carries the roles: the flag, or this cell."""
    return getattr(ctx.cli, "knockout_roles_from", None) or ctx.cell_dir


def families_for(ctx) -> tuple:
    """`(families, dropped)`: the role families this run ablates, off a head table.

    Refused by name rather than silently empty: a family knockout that quietly
    found no role would write a file saying nothing happened, which looks
    exactly like a circuit whose Components have no roles.
    """
    from component_analysis.head_table import JSON_NAME as TABLE_JSON
    from component_analysis.head_table import load_head_table

    source = roles_source(ctx)
    if not os.path.exists(os.path.join(source, TABLE_JSON)):
        raise SystemExit(
            f"--knockout-families needs a head table with a role column, and "
            f"{source!r} has no {TABLE_JSON}. Run "
            f"`python analyze_components.py roles <cell>` first, or point "
            f"--knockout-roles-from at a cell where it has run.")
    families = families_from_rows(load_head_table(source))
    if not families:
        raise SystemExit(
            f"no Component in {source!r} carries a role, so there is no family "
            f"to knock out. Run `python analyze_components.py roles` on that "
            f"cell first.")

    # A roles cell may hold rows this circuit does not: the completeness sweep
    # appends the Components it scored from outside the circuit, and the roles
    # pass gives every one of them a role (`unknown`, for want of any view).
    # Those are dropped rather than ablated, because a family knockout is a
    # statement about the circuit under study, and the count is recorded in
    # the JSON's `grouping` block so the drop is visible rather than silent.
    inside = set(ctx.keys)
    kept, dropped = {}, []
    for role, members in families.items():
        here = [one for one in members if one in inside]
        dropped.extend(one for one in members if one not in inside)
        if here:
            kept[role] = here
    if dropped:
        print(f"    knockout: {len(dropped)} Component(s) in {source} carry a "
              f"role but are not in this circuit and are not ablated: "
              f"{', '.join(str(one) for one in sorted(dropped)[:5])}"
              f"{' ...' if len(dropped) > 5 else ''}")
    if not kept:
        raise SystemExit(
            f"every Component with a role in {source!r} is outside this "
            f"circuit, so there is no family to knock out. Read the roles from "
            f"a cell of this circuit.")
    return kept, dropped


def groups_for(ctx) -> Optional[List[tuple]]:
    """The `--knockout-groups` file, parsed and checked against the model."""
    path = getattr(ctx.cli, "knockout_groups", None)
    if not path:
        return None
    groups = load_groups(path)
    check_groups(groups, ctx.intake.geometry)
    return groups


def check_plan(ctx, plan: KnockoutPlan, batches) -> None:
    """Refuse a plan this cell cannot run, before any forward.

    A neutral-twin knockout on a cell with no twin (H, F, v1), or one whose
    positions name a Segment some sampled row lacks (post-clause on F), is a
    misconfigured cell, not a smaller measurement.
    """
    if plan.scheme == "interchange" and plan.counterfactual == "neutral_twin":
        report = batches.report
        if not report.get("n_with_neutral_twin"):
            raise ValueError(
                f"--knockout-counterfactual neutral_twin on "
                f"{ctx.task_spec.name!r}: no instance of the causal sample has a "
                f"Neutral-Clause Twin ("
                f"{report.get('neutral_twin_source', 'not a v2 task')})")
        if report.get("without_neutral_twin"):
            print(f"    knockout: {len(report['without_neutral_twin'])} sampled "
                  f"instance(s) have no twin and are left out of the "
                  f"neutral-twin knockout")
    parsed = plan.parsed_positions
    if parsed["form"] != "all":
        by_id = _by_id(ctx.segmentations)
        for batch in batches:
            position_mask(parsed, list(batch.ids), by_id, batch.readout,
                          batch.input_ids.shape[1])


def target_direction_of(batches) -> Optional[str]:
    """`deceptive` or `honest`, from the records' `condition`."""
    for batch in batches:
        conditions = {record.get("condition") for record in batch.records}
        directions = {TARGET_DIRECTION.get(one) for one in conditions}
        return directions.pop() if len(directions) == 1 else None
    return None


def _greedy_settings(ctx) -> Optional[dict]:
    path = getattr(ctx.cli, "knockout_greedy_pool", None)
    if not path:
        return None
    return {"path": path,
            "size": int(getattr(ctx.cli, "knockout_greedy_pool_size",
                                DEFAULT_GREEDY_POOL_SIZE)),
            "k_max": int(getattr(ctx.cli, "knockout_greedy_k_max",
                                 DEFAULT_GREEDY_K_MAX))}


def _greedy_forwards(n_batches: int, pool_size: int, k_max: int) -> int:
    return sum(n_batches * (pool_size - step + 2)
               for step in range(min(k_max, pool_size)))


def estimate(ctx) -> str:
    batches = ctx.causal_batches()
    plan = plan_of(ctx)
    check_plan(ctx, plan, batches)
    passes = len(batches) * (len(ctx.components) + 2)
    line = (f"{len(ctx.components)} Component(s) x {len(batches)} batch(es) of "
            f"{batches.report['batch_size']} (+2 clean and corrupt passes per "
            f"batch) = {passes} forward pass(es), about "
            f"{passes * SECONDS_PER_FORWARD / 60:.1f} min on an A40, over "
            f"{batches.n_instances} instance(s); scheme "
            f"{scheme_of(ctx)}")
    total = passes if singles_on(ctx) else 0
    if not singles_on(ctx):
        line = "per-Component pass off (--knockout-singles off)"
    if sweeping(ctx):
        shape = ctx.intake.geometry
        n_swept = sweep_size(shape)
        swept = len(batches) * (n_swept + 2)
        total = swept
        line = (f"completeness sweep: {n_swept} Component(s) of the model "
                f"({shape['num_layers']} layers x ({shape['num_heads']} heads "
                f"+ 1 MLP block)) x {len(batches)} batch(es) of "
                f"{batches.report['batch_size']} (+2 shared clean and corrupt "
                f"passes per batch) = {swept} forward pass(es), about "
                f"{swept * SECONDS_PER_FORWARD / 60:.1f} min on an A40, over "
                f"{batches.n_instances} instance(s); the circuit's "
                f"{len(ctx.components)} single knockout(s) are read from the "
                f"same forwards, not added; the embedding is not a Component "
                f"and is not swept; flagged outside the circuit at "
                f"threshold {sweep_threshold(ctx):g} logits; scheme "
                f"{scheme_of(ctx)}")
        if sweep_exclusions(ctx):
            line += (f"; excluded from ranking: "
                     f"{', '.join(component_label(k) for k in sweep_exclusions(ctx))}")
    if getattr(ctx.cli, "knockout_families", False):
        families, dropped = families_for(ctx)
        family_passes = len(batches) * (len(families) + 2)
        total += family_passes
        line += (f"; plus {len(families)} role famil"
                 f"{'y' if len(families) == 1 else 'ies'} "
                 f"({', '.join(f'{role} x{len(members)}' for role, members in families.items())}) "
                 f"from {roles_source(ctx)} = {family_passes} more forward pass(es), "
                 f"about {family_passes * SECONDS_PER_FORWARD / 60:.1f} min")
    groups = groups_for(ctx)
    if groups is not None:
        group_passes = len(batches) * (len(groups) + 2)
        total += group_passes
        sizes = sorted({len(keys) for _name, keys in groups})
        line += (f"; plus {len(groups)} named group(s) from "
                 f"{ctx.cli.knockout_groups} (sizes {sizes[0]}-{sizes[-1]}) = "
                 f"{group_passes} more forward pass(es)")
    greedy = _greedy_settings(ctx)
    if greedy is not None:
        if os.path.exists(greedy["path"]):
            pool = greedy_pool(greedy["path"], size=greedy["size"])
            pool_note = (f"pool {len(pool)} from {greedy['path']} (top: "
                         f"{', '.join(component_label(k) for k in pool[:3])})")
            size = len(pool)
        else:
            pool_note = (f"!! pool file {greedy['path']} does not exist yet; "
                         f"costed at {greedy['size']}")
            size = greedy["size"]
        greedy_passes = _greedy_forwards(len(batches), size, greedy["k_max"])
        total += greedy_passes
        line += (f"; plus greedy to k={min(greedy['k_max'], size)} over a {pool_note}"
                 f" = {greedy_passes} more forward pass(es)")
    if plan.scheme == "mean":
        bank_passes = 2 * len(ctx.descriptive_batches())
        total += bank_passes
        line += (f"; plus the mean bank over the whole test split, both streams "
                 f"= {bank_passes} forward pass(es)")
    if records_more(ctx, plan):
        line += (f"; plan {plan.describe()}; in total {total} forward pass(es), "
                 f"about {total * SECONDS_PER_FORWARD_H100 / 60:.1f} min on an "
                 f"H100 (extrapolated)")
    return line


def _rename(updates: dict, suffix: str) -> dict:
    return {key: {f"{column}{suffix}": value for column, value in values.items()}
            for key, values in updates.items()}


def _declare(ctx, columns, plan, effects, *, details) -> None:
    from component_analysis.head_table import CAUSAL_SAMPLE_NEUTRAL_TWIN

    instance_set = (CAUSAL_SAMPLE_NEUTRAL_TWIN
                    if plan.counterfactual == "neutral_twin"
                    and plan.scheme == "interchange" else INSTANCE_SET)
    ctx.declare_coverage([f"{column}{plan.column_suffix}" for column in columns],
                         instance_ids=effects.ids, instance_set=instance_set,
                         **({"details": details} if details else {}))


def _coverage_details(ctx, plan) -> Optional[dict]:
    if not records_more(ctx, plan) or ctx.sample is None:
        return None
    return {"sample_seed": ctx.sample.seed,
            "id_filters": {name: {key: value for key, value in record.items()
                                  if key != "not_in_split"}
                           for name, record in ctx.sample.id_filters.items()},
            "plan": plan.describe()}


def _write_instances(ctx, name: str, effects: Effects, *, what: str,
                     label=component_label) -> str:
    filename = f"{name}{INSTANCES_SUFFIX}"
    ctx.write_json(SUBDIR, filename, instances_payload(effects, what=what,
                                                       label=label))
    return filename


def _write_sweep(ctx, swept: Effects, wall: float, *, scheme: str,
                 plan: KnockoutPlan, direction, extra: dict) -> dict:
    """Write `sweep.json` and `sweep.png`; return the circuit rows' columns."""
    from component_analysis import hooks

    threshold = sweep_threshold(ctx)
    per_group = hooks.geometry(ctx.model)["heads_per_group"]
    excluded = sweep_exclusions(ctx)
    rows = summarize_sweep(swept, ctx.keys, threshold=threshold,
                           heads_per_group=per_group,
                           exclude_from_ranking=excluded)
    n_batches = len(ctx.causal_batches())
    forwards = n_batches * (len(swept.keys) + 2)
    cost = {"forwards": forwards, "n_batches": n_batches,
            "wall_seconds": wall,
            "seconds_per_forward": wall / forwards if forwards else None,
            "estimate_seconds_per_forward": SECONDS_PER_FORWARD,
            "note": ("per batch one clean pass, one corrupt pass capturing "
                     "every Component, and one pass per Component; the "
                     "circuit's single knockouts are among them")}
    extra = dict(extra)
    if excluded:
        extra["excluded_from_ranking"] = [component_label(k) for k in excluded]
    if records_more(ctx, plan):
        extra["instances_file"] = _write_instances(ctx, "sweep", swept,
                                                   what="completeness_sweep")
    ctx.write_json(SUBDIR, SWEEP_JSON_NAME,
                   sweep_payload(swept, rows, circuit=ctx.circuit_spec.label,
                                 task=ctx.task_spec.name, threshold=threshold,
                                 cost=cost, target_direction=direction,
                                 extra=extra,
                                 record_plan=records_more(ctx, plan) or bool(excluded)))
    write_sweep_figure(
        os.path.join(ctx.subdir(SUBDIR), SWEEP_PNG_NAME), rows,
        threshold=threshold,
        title=f"{ctx.circuit_spec.label} x {ctx.task_spec.name}: {scheme} "
              f"knockout of every Component of the model\nstrongest "
              f"{min(SWEEP_BAR_TOP, len(rows))} of {len(rows)} by |drop|")
    _declare(ctx, SWEEP_COLUMNS, plan, swept, details=_coverage_details(ctx, plan))
    flagged = [row["label"] for row in rows if row["flagged"]]
    print(f"    knockout sweep: {len(rows)} Component(s) in {wall:.0f} s; "
          f"{len(flagged)} outside the circuit (positive controls aside) "
          f"clear {threshold:g}"
          + (f": {', '.join(flagged[:10])}{' ...' if len(flagged) > 10 else ''}"
             if flagged else ""))
    return _rename(sweep_columns(rows), plan.column_suffix)


def _metric_block(plan: KnockoutPlan, figure: Optional[str]) -> dict:
    return {"name": "logit(Target) - logit(Distractor) at the Readout",
            "readout": "fp32 final norm and unembedding (ADR-0001)",
            "sign": ("drop = clean logit difference - knocked-out logit "
                     "difference, in the cell's own target direction (see "
                     "target_direction): positive means the group supports the "
                     "Target"),
            "accuracy": ("share of sampled instances whose Target still "
                         "outscores its Distractor; not a full-vocabulary argmax"),
            "ablation": ablation_sentence(plan) + ", jointly for every member",
            "figure": figure}


def _write_groups(ctx, batches, groups, plan, common, direction) -> None:
    path = ctx.cli.knockout_groups
    started = time.perf_counter()
    grouped = knock_out_groups(ctx.model, batches, groups, **common)
    wall = time.perf_counter() - started
    instances = _write_instances(ctx, "groups", grouped, what="groups", label=str)
    forwards = len(batches) * (len(groups) + 2)
    ctx.write_json(SUBDIR, GROUPS_JSON_NAME, {
        "analysis": NAME, "pass": "groups", "circuit": ctx.circuit_spec.label,
        "task": ctx.task_spec.name, "plan": plan.describe(),
        "metric": _metric_block(plan, None), "target_direction": direction,
        "source": {"path": path, "sha256": file_digest(path)},
        "instances": grouped.ids, "instances_file": instances,
        "unpaired_instance_ids": list(grouped.unpaired),
        "clean_run": clean_run(grouped), "counterfactual_run": counterfactual_run(grouped),
        "n_groups": len(groups), "groups": group_rows(grouped, groups),
        "cost": {"forwards": forwards, "wall_seconds": wall,
                 "seconds_per_forward": wall / forwards if forwards else None,
                 "seconds_per_group": wall / len(groups) if groups else None},
    })
    print(f"    knockout groups: {len(groups)} group(s) in {wall:.0f} s")


def _write_greedy(ctx, batches, settings, plan, common, direction) -> None:
    pool = greedy_pool(settings["path"], size=settings["size"])
    if not pool:
        raise ValueError(f"{settings['path']} gives an empty greedy pool")
    with open(settings["path"]) as handle:
        source = json.load(handle)
    sweep_drop = {row_key(tuple(row["key"])): row.get("mean_drop")
                  for row in source.get("components", [])}
    started = time.perf_counter()
    forwards = [0]

    def evaluate(member_lists):
        labelled = [(f"candidate_{i}", members) for i, members in enumerate(member_lists)]
        effects = knock_out_groups(ctx.model, batches, labelled, **common)
        forwards[0] += len(batches) * (len(labelled) + 2)
        return [(_mean(effects.drops(label)), (effects, label))
                for label, _members in labelled]

    steps = greedy_select(pool, evaluate, k_max=settings["k_max"])
    wall = time.perf_counter() - started
    first = steps[0]["payload"][0]
    chosen = Effects(ids=list(first.ids), keys=[f"k={step['k']}" for step in steps],
                     clean_logit_difference=list(first.clean_logit_difference),
                     knocked_logit_difference={
                         f"k={step['k']}": list(step["payload"][0]
                                                .knocked_logit_difference[step["payload"][1]])
                         for step in steps},
                     counterfactual_logit_difference=list(
                         first.counterfactual_logit_difference),
                     plan=first.plan, unpaired=list(first.unpaired),
                     neutral_twin_logit_difference=list(
                         first.neutral_twin_logit_difference))
    instances = _write_instances(ctx, "greedy", chosen, what="greedy", label=str)
    out_steps = []
    for step in steps:
        effects, label = step["payload"]
        drops = effects.drops(label)
        knocked = effects.knocked_logit_difference[label]
        out_steps.append({
            "k": step["k"], "added": component_label(step["added"]),
            "members": [component_label(key) for key in step["members"]],
            "joint_drop": step["joint_drop"], "standard_error": _standard_error(drops),
            "knocked_logit_difference": _mean(knocked), "accuracy": _accuracy(knocked),
            "candidates": [{"label": component_label(one["key"]),
                            "joint_drop": one["joint_drop"]}
                           for one in step["candidates"]]})
    ctx.write_json(SUBDIR, GREEDY_JSON_NAME, {
        "analysis": NAME, "pass": "greedy", "circuit": ctx.circuit_spec.label,
        "task": ctx.task_spec.name, "plan": plan.describe(),
        "metric": _metric_block(plan, None), "target_direction": direction,
        "rule": ("start from the empty set; at each step add the pool Component "
                 "whose addition gives the largest mean joint drop on this "
                 "sample; ties to the earlier pool Component"),
        "pool_source": {"path": settings["path"], "sha256": file_digest(settings["path"]),
                        "plan": source.get("plan"), "task": source.get("task"),
                        "pool_rule": ("top by signed mean_drop, the layer-0 MLP "
                                      "and excluded rows left out, ties in model "
                                      "order")},
        "pool": [{"label": component_label(key), "sweep_drop": sweep_drop.get(key)}
                 for key in pool],
        "k_max": settings["k_max"], "instances": chosen.ids,
        "instances_file": instances, "clean_run": clean_run(chosen),
        "counterfactual_run": counterfactual_run(chosen), "steps": out_steps,
        "cost": {"forwards": forwards[0], "wall_seconds": wall,
                 "group_knockouts": sum(len(step["candidates"]) for step in steps),
                 "seconds_per_forward": wall / forwards[0] if forwards[0] else None},
    })
    print(f"    knockout greedy: k={len(steps)} from a pool of {len(pool)} in "
          f"{wall:.0f} s; order {', '.join(o['added'] for o in out_steps[:5])}"
          f"{' ...' if len(out_steps) > 5 else ''}")


def run(ctx) -> dict:
    """Knock out every Component, write the JSON and the PNG, return the columns."""
    plan = plan_of(ctx)
    scheme = plan.scheme
    # Read before the forwards, so a missing role column or a bad groups file
    # fails in seconds rather than after the per-Component pass has run.
    families, dropped = families_for(ctx) \
        if getattr(ctx.cli, "knockout_families", False) else (None, [])
    groups = groups_for(ctx)
    greedy = _greedy_settings(ctx)
    batches = ctx.causal_batches()
    check_plan(ctx, plan, batches)
    direction = target_direction_of(batches)

    extra = {}
    bank = None
    if scheme == "mean":
        started = time.perf_counter()
        bank, info = collect_mean_bank(ctx.model, ctx.descriptive_batches(),
                                       sweep_components(ctx.model))
        info["wall_seconds"] = time.perf_counter() - started
        extra["mean_bank"] = info
    common = {"plan": plan, "segmentations": ctx.segmentations, "mean_bank": bank}
    details = _coverage_details(ctx, plan)

    updates: dict = {}
    swept = None
    effects = None
    if sweeping(ctx):
        # One loop over every Component of the model; the circuit's singles
        # are read out of it, so the two files share their clean and corrupt
        # passes and agree to the bit.
        started = time.perf_counter()
        swept = sweep_effects(ctx.model, batches, **common)
        wall = time.perf_counter() - started
        effects = swept.restrict(ctx.keys)
    elif singles_on(ctx):
        effects = knockout_effects(ctx.model, batches, ctx.components, **common)

    if effects is not None:
        rows = summarize(effects, ctx.components)
        single_extra = dict(extra)
        if records_more(ctx, plan):
            single_extra["instances_file"] = _write_instances(
                ctx, "knockout", effects, what="singles")
        ctx.write_json(SUBDIR, JSON_NAME,
                       payload(effects, circuit=ctx.circuit_spec.label,
                               task=ctx.task_spec.name, rows=rows,
                               target_direction=direction, extra=single_extra,
                               record_plan=records_more(ctx, plan)))
        write_figure(os.path.join(ctx.subdir(SUBDIR), PNG_NAME), rows,
                     title=f"{ctx.circuit_spec.label} x {ctx.task_spec.name}: "
                           f"per-Component {scheme} knockout")
        updates = _rename(columns(rows), plan.column_suffix)
        _declare(ctx, COLUMNS, plan, effects, details=details)
    if swept is not None:
        for key, values in _write_sweep(ctx, swept, wall, scheme=scheme, plan=plan,
                                        direction=direction, extra=extra).items():
            updates.setdefault(key, {}).update(values)
    if families is not None:
        grouped = family_effects(ctx.model, batches, families, **common)
        family_rows = summarize_families(grouped, families)
        family_extra = dict(extra)
        if records_more(ctx, plan):
            # R19(1): every joint knockout keeps its per-instance rows.
            family_extra["instances_file"] = _write_instances(
                ctx, "knockout_families", grouped, what="families", label=str)
        ctx.write_json(SUBDIR, FAMILY_JSON_NAME,
                       family_payload(grouped, families,
                                      circuit=ctx.circuit_spec.label,
                                      task=ctx.task_spec.name, rows=family_rows,
                                      roles_from=roles_source(ctx),
                                      dropped=dropped, target_direction=direction,
                                      extra=family_extra,
                                      record_plan=records_more(ctx, plan)))
        write_family_figure(os.path.join(ctx.subdir(SUBDIR), FAMILY_PNG_NAME),
                            family_rows,
                            title=f"{ctx.circuit_spec.label} x {ctx.task_spec.name}: "
                                  f"{scheme} knockout by Component Role family")
        for key, values in _rename(family_columns(family_rows),
                                   plan.column_suffix).items():
            updates.setdefault(key, {}).update(values)
        _declare(ctx, FAMILY_COLUMNS, plan, grouped, details=details)
    if groups is not None:
        _write_groups(ctx, batches, groups, plan, common, direction)
    if greedy is not None:
        _write_greedy(ctx, batches, greedy, plan, common, direction)
    return updates
