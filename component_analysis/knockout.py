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
import math
import os
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

#: The only ablation scheme that exists, and the two that do not yet.
SCHEME = "interchange"
FUTURE_SCHEMES = ("mean", "zero")

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
    """A knockout scheme that is not built.

    Two bases on purpose: argparse prints an `ArgumentTypeError` verbatim, so
    `--knockout-scheme zero` fails on the login node with the sentence below
    rather than "invalid value", and a library caller still catches the
    `ValueError` it would expect.
    """


def resolve_scheme(value) -> str:
    """`interchange`, or a refusal that says what is and is not built."""
    scheme = str(value).strip().lower()
    if scheme == SCHEME:
        return scheme
    later = " and ".join(FUTURE_SCHEMES)
    raise UnsupportedScheme(
        f"knockout scheme {scheme!r} is not implemented. {SCHEME!r} is the "
        f"only scheme built: it replaces the Component's output with the value "
        f"it carried on the item-swap corrupt stream. {later} ablation are "
        f"future work — the flag exists so they can be added without this "
        f"analysis's interface changing.")


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
                       scheme=self.scheme, report=dict(self.report))


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


def payload(effects: Effects, *, circuit: str, task: str, components=None,
            rows=None) -> dict:
    """`knockout.json`: the ranked table, the clean run, and what it all means.

    `rows` is the ranking when the caller already has it, so that the table in
    the file and the table the head-table columns and the figure are built from
    are one object rather than three rankings that could disagree.
    """
    rows = summarize(effects, components) if rows is None else list(rows)
    return {
        "analysis": NAME,
        "circuit": circuit,
        "task": task,
        "scheme": effects.scheme,
        "metric": {
            "name": "logit(Target) - logit(Distractor) at the Readout",
            "readout": "fp32 final norm and unembedding (ADR-0001)",
            "sign": ("drop = clean logit difference - knocked-out logit "
                     "difference, so a positive drop means the Component helps "
                     "deception and a negative one means it opposes it"),
            "accuracy": ("share of sampled instances whose Target still "
                         "outscores its Distractor; not a full-vocabulary "
                         "argmax"),
            "ablation": ("the Component's output at every position is replaced "
                         "by the value it carried on the item-swap corrupt "
                         "stream"),
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
    }


# ==============================================================================
# THE FORWARD LOOP
# ==============================================================================

def knockout_effects(model, batches, components, *,
                     scheme=SCHEME) -> Effects:
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
                            scheme=scheme)


def knock_out_groups(model, batches, groups, *, scheme=SCHEME) -> Effects:
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
    """
    import torch

    from component_analysis import hooks

    scheme = resolve_scheme(scheme)
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
    knocked: Dict[tuple, List[float]] = {label: [] for label in labels}

    for batch in batches:
        clean_ids = batch.input_ids.to(device)
        clean_mask = batch.attention_mask.to(device)
        corrupt_ids = batch.corrupt_input_ids.to(device)
        corrupt_mask = batch.corrupt_attention_mask.to(device)
        readout = batch.readout.to(device)
        # The clean stream's assignment on every run: which word is the Target
        # flips between the streams, and a drop measured against the flipped
        # one would be a difference of two different questions.
        target = batch.target_token.to(device)
        distractor = batch.distractor_token.to(device)

        with torch.no_grad():
            clean = hooks.capture_forward(model, clean_ids, clean_mask,
                                          components=[], positions=readout)
            corrupt = hooks.capture_forward(model, corrupt_ids, corrupt_mask,
                                            components=keys, positions=readout)
            ids.extend(batch.ids)
            clean_logit_difference.extend(logit_difference(clean, target, distractor))

            for label, members in groups:
                patched = hooks.capture_forward(
                    model, clean_ids, clean_mask, components=[],
                    positions=readout,
                    replacements={key: corrupt.outputs[key] for key in members})
                knocked[label].extend(logit_difference(patched, target,
                                                       distractor))
    return Effects(ids=ids, keys=labels,
                   clean_logit_difference=clean_logit_difference,
                   knocked_logit_difference=knocked, scheme=scheme,
                   report=dict(getattr(batches, "report", {}) or {}))


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


def family_effects(model, batches, families, *, scheme=SCHEME) -> Effects:
    """Interchange-ablate every Component of a role, together, one role at a time."""
    return knock_out_groups(model, batches, list(families.items()),
                            scheme=scheme)


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
                   rows=None, roles_from: str = None, dropped=()) -> dict:
    """`knockout_families.json`: the same shape and the same signs as the singles."""
    rows = summarize_families(effects, families) if rows is None else list(rows)
    single = payload(effects, circuit=circuit, task=task, rows=[])
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
                   "ablation": ("every Component of the role has its output at "
                                "every position replaced by the value it "
                                "carried on the item-swap corrupt stream, all "
                                "in one forward, so the number is the family's "
                                "joint effect and not the sum of its members'"),
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
#: gap as `--path-sweep-threshold` is. Why 0.1 on SDR nls0.3 (ticket 07's
#: job 22110635): it is about twice the standard error of the strong circuit
#: Components (0.03 to 0.07), so a listed drop is not one standard error of
#: noise on a strong head; it is about 3% of the 3.26 clean-minus-corrupt gap;
#: and four of the circuit's eighteen clear it (L17H25 +0.45, L31 MLP +0.31,
#: L5H11 +0.15, L14H22 +0.11), so a flagged outsider is as strong as the
#: circuit's top four. The JSON also counts what clears `THRESHOLD_LADDER`,
#: so the cut can be moved without a rerun.
DEFAULT_SWEEP_THRESHOLD = 0.1
THRESHOLD_JUSTIFICATION = (
    "0.1 logits is about twice the standard error of the circuit's strong "
    "Components on SDR nls0.3 (0.03 to 0.07, ticket 07), about 3% of its "
    "3.26 clean-minus-corrupt gap, and cleared by four of the circuit's "
    "eighteen (L17H25, L31 MLP, L5H11, L14H22): a flagged Component outside "
    "the circuit is as strong as the circuit's top four. Calibrated on that "
    "circuit only")
THRESHOLD_LADDER = (0.02, 0.05, 0.1, 0.2)

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


def sweep_effects(model, batches, *, scheme=SCHEME) -> Effects:
    """Knock out every head and MLP block of the model, one at a time.

    `knock_out_groups` with one-member groups, as `knockout_effects` calls it:
    per batch one clean pass, one corrupt pass capturing every Component, and
    one pass per Component.
    """
    return knockout_effects(model, batches, sweep_components(model),
                            scheme=scheme)


def summarize_sweep(effects: Effects, circuit_keys, *, threshold: float,
                    heads_per_group: Optional[int] = None) -> List[dict]:
    """Every Component, ranked by the size of its drop, circuit marked.

    Ranked by **|drop|**, not by the signed drop `knockout.rank` uses: the
    sweep asks which Components matter that the circuit lacks, and a strong
    suppressor outside the circuit is one of those answers. The sign stays in
    `mean_drop` (positive helps deception) and `signed_rank` is knockout's own
    ranking of the same rows. `flagged` is a Component outside the circuit
    whose |drop| is at least `threshold`.
    """
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
    for rank, row in enumerate(rows, start=1):
        key = row["key"]
        measured = row["mean_drop"] is not None
        se = row["standard_error"]
        row.update({
            "label": component_label(key),
            "rank": rank if measured else None,
            "kv_group": (key[2] // heads_per_group
                         if heads_per_group and key[0] == "head" else None),
            "in_circuit": key in inside,
            "z": (row["mean_drop"] / se) if measured and se else None,
            "clears_threshold": measured and abs(row["mean_drop"]) >= threshold,
        })
        row["flagged"] = row["clears_threshold"] and not row["in_circuit"]
    return rows


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
    """How many Components, inside and outside the circuit, clear each cut."""
    out = []
    for cut in ladder:
        clearing = [row for row in rows if row["mean_drop"] is not None
                    and abs(row["mean_drop"]) >= cut]
        out.append({"threshold": cut,
                    "outside_circuit": sum(1 for row in clearing
                                           if not row["in_circuit"]),
                    "in_circuit": sum(1 for row in clearing if row["in_circuit"])})
    return out


def sweep_payload(effects: Effects, rows, *, circuit: str, task: str,
                  threshold: float, cost: Optional[dict] = None) -> dict:
    """`sweep.json`: every Component ranked, and the twin of `sweep.png`."""
    single = payload(effects, circuit=circuit, task=task, rows=[])
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
        "flagged_means": ("outside the circuit and |mean_drop| >= threshold; "
                          "listed here, never added to the head table"),
        "n_components": len(rows),
        "n_in_circuit": sum(1 for row in rows if row["in_circuit"]),
        "flagged": [row["label"] for row in rows if row["flagged"]],
        "threshold_counts": threshold_counts(rows),
        "strongest_outside_circuit": [
            {**row, "key": list(row["key"])} for row in rows
            if not row["in_circuit"] and row["rank"] is not None][:STRONGEST_OUTSIDE_TOP],
        "figure": {"file": SWEEP_PNG_NAME, "n_shown": len(shown),
                   "shows": f"the {len(shown)} strongest by |drop|, circuit "
                            f"Components highlighted"},
        "cost": cost or {},
        "components": as_json,
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


def write_sweep_figure(path: str, rows, *, threshold: float,
                       title: str = "") -> str:
    """The strongest `SWEEP_BAR_TOP` Components by |drop|, circuit highlighted.

    Horizontal bars in rank order, signed, so a Component that opposes
    deception sits left of zero; dotted lines at plus and minus the threshold.
    Every number drawn is a row of `sweep.json`.
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
    axes.barh(positions, [row["mean_drop"] for row in top],
              xerr=[row["standard_error"] or 0.0 for row in top],
              color=[SWEEP_CIRCUIT_COLOUR if row["in_circuit"]
                     else SWEEP_OTHER_COLOUR for row in top],
              edgecolor="none", height=0.7,
              error_kw={"ecolor": "#4a525a", "elinewidth": 0.9, "capsize": 2})
    axes.set_yticks(positions)
    axes.set_yticklabels([row["label"] for row in top], fontsize=8)
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
    axes.legend(handles=[Patch(color=SWEEP_CIRCUIT_COLOUR, label="in the circuit"),
                         Patch(color=SWEEP_OTHER_COLOUR, label="not in the circuit")],
                loc="lower right", fontsize=8, frameon=False)
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


def add_arguments(group) -> None:
    group.add_argument("--knockout-scheme", type=resolve_scheme, default=SCHEME,
                       help=f"How a Component is ablated. {SCHEME!r} is the "
                            f"only scheme built; {' and '.join(FUTURE_SCHEMES)} "
                            f"are future work and are refused by name.")
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
                       default=DEFAULT_SWEEP_THRESHOLD,
                       help="A Component outside the circuit whose |drop| "
                            "is at least this many logits is listed as "
                            "flagged in sweep.json (never added to the head "
                            "table). Logits of logit(Target) - "
                            "logit(Distractor), not a fraction of the gap "
                            "like --path-sweep-threshold. Default "
                            f"{DEFAULT_SWEEP_THRESHOLD}: about twice the "
                            "standard error of the circuit's strong "
                            "Components on SDR nls0.3, and 3%% of its "
                            "clean-minus-corrupt gap.")


def scheme_of(ctx) -> str:
    """The ablation scheme this run asked for, resolved."""
    return resolve_scheme(getattr(ctx.cli, "knockout_scheme", SCHEME))


def sweeping(ctx) -> bool:
    """Whether `--knockout-completeness-sweep` was given."""
    return bool(getattr(ctx.cli, "knockout_completeness_sweep", False))


def sweep_threshold(ctx) -> float:
    """Which Components outside the circuit the sweep flags, in logits.

    `--knockout-sweep-threshold`, defaulting to `DEFAULT_SWEEP_THRESHOLD`.
    """
    return float(getattr(ctx.cli, "knockout_sweep_threshold",
                         DEFAULT_SWEEP_THRESHOLD))


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


def estimate(ctx) -> str:
    batches = ctx.causal_batches()
    passes = len(batches) * (len(ctx.components) + 2)
    line = (f"{len(ctx.components)} Component(s) x {len(batches)} batch(es) of "
            f"{batches.report['batch_size']} (+2 clean and corrupt passes per "
            f"batch) = {passes} forward pass(es), about "
            f"{passes * SECONDS_PER_FORWARD / 60:.1f} min on an A40, over "
            f"{batches.n_instances} instance(s); scheme "
            f"{scheme_of(ctx)}")
    if sweeping(ctx):
        shape = ctx.intake.geometry
        n_swept = sweep_size(shape)
        swept = len(batches) * (n_swept + 2)
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
    if not getattr(ctx.cli, "knockout_families", False):
        return line
    families, dropped = families_for(ctx)
    family_passes = len(batches) * (len(families) + 2)
    return (line + f"; plus {len(families)} role famil"
            f"{'y' if len(families) == 1 else 'ies'} "
            f"({', '.join(f'{role} x{len(members)}' for role, members in families.items())}) "
            f"from {roles_source(ctx)} = {family_passes} more forward pass(es), "
            f"about {family_passes * SECONDS_PER_FORWARD / 60:.1f} min")


def _write_sweep(ctx, swept: Effects, wall: float, *, scheme: str) -> dict:
    """Write `sweep.json` and `sweep.png`; return the circuit rows' columns."""
    from component_analysis import hooks

    threshold = sweep_threshold(ctx)
    per_group = hooks.geometry(ctx.model)["heads_per_group"]
    rows = summarize_sweep(swept, ctx.keys, threshold=threshold,
                           heads_per_group=per_group)
    n_batches = len(ctx.causal_batches())
    forwards = n_batches * (len(swept.keys) + 2)
    cost = {"forwards": forwards, "n_batches": n_batches,
            "wall_seconds": wall,
            "seconds_per_forward": wall / forwards if forwards else None,
            "estimate_seconds_per_forward": SECONDS_PER_FORWARD,
            "note": ("per batch one clean pass, one corrupt pass capturing "
                     "every Component, and one pass per Component; the "
                     "circuit's single knockouts are among them")}
    ctx.write_json(SUBDIR, SWEEP_JSON_NAME,
                   sweep_payload(swept, rows, circuit=ctx.circuit_spec.label,
                                 task=ctx.task_spec.name, threshold=threshold,
                                 cost=cost))
    write_sweep_figure(
        os.path.join(ctx.subdir(SUBDIR), SWEEP_PNG_NAME), rows,
        threshold=threshold,
        title=f"{ctx.circuit_spec.label} x {ctx.task_spec.name}: {scheme} "
              f"knockout of every Component of the model\nstrongest "
              f"{min(SWEEP_BAR_TOP, len(rows))} of {len(rows)} by |drop|")
    ctx.declare_coverage(SWEEP_COLUMNS, instance_ids=swept.ids,
                         instance_set=INSTANCE_SET)
    flagged = [row["label"] for row in rows if row["flagged"]]
    print(f"    knockout sweep: {len(rows)} Component(s) in {wall:.0f} s; "
          f"{len(flagged)} outside the circuit clear {threshold:g}"
          + (f": {', '.join(flagged[:10])}{' ...' if len(flagged) > 10 else ''}"
             if flagged else ""))
    return sweep_columns(rows)


def run(ctx) -> dict:
    """Knock out every Component, write the JSON and the PNG, return the columns."""
    scheme = scheme_of(ctx)
    # Read before the forwards, so a missing role column fails in seconds
    # rather than after the per-Component pass has already run.
    families, dropped = families_for(ctx) \
        if getattr(ctx.cli, "knockout_families", False) else (None, [])
    batches = ctx.causal_batches()
    swept = None
    if sweeping(ctx):
        # One loop over every Component of the model; the circuit's singles
        # are read out of it, so the two files share their clean and corrupt
        # passes and agree to the bit.
        started = time.perf_counter()
        swept = sweep_effects(ctx.model, batches, scheme=scheme)
        wall = time.perf_counter() - started
        effects = swept.restrict(ctx.keys)
    else:
        effects = knockout_effects(ctx.model, batches, ctx.components,
                                   scheme=scheme)

    rows = summarize(effects, ctx.components)
    ctx.write_json(SUBDIR, JSON_NAME,
                   payload(effects, circuit=ctx.circuit_spec.label,
                           task=ctx.task_spec.name, rows=rows))
    write_figure(os.path.join(ctx.subdir(SUBDIR), PNG_NAME), rows,
                 title=f"{ctx.circuit_spec.label} x {ctx.task_spec.name}: "
                       f"per-Component {scheme} knockout")
    updates = columns(rows)
    ctx.declare_coverage(COLUMNS, instance_ids=effects.ids,
                         instance_set=INSTANCE_SET)
    if swept is not None:
        for key, values in _write_sweep(ctx, swept, wall,
                                        scheme=scheme).items():
            updates.setdefault(key, {}).update(values)
    if families is None:
        return updates

    grouped = family_effects(ctx.model, batches, families, scheme=scheme)
    family_rows = summarize_families(grouped, families)
    ctx.write_json(SUBDIR, FAMILY_JSON_NAME,
                   family_payload(grouped, families,
                                  circuit=ctx.circuit_spec.label,
                                  task=ctx.task_spec.name, rows=family_rows,
                                  roles_from=roles_source(ctx),
                                  dropped=dropped))
    write_family_figure(os.path.join(ctx.subdir(SUBDIR), FAMILY_PNG_NAME),
                        family_rows,
                        title=f"{ctx.circuit_spec.label} x {ctx.task_spec.name}: "
                              f"{scheme} knockout by Component Role family")
    for key, values in family_columns(family_rows).items():
        updates.setdefault(key, {}).update(values)
    ctx.declare_coverage(FAMILY_COLUMNS, instance_ids=grouped.ids,
                         instance_set=INSTANCE_SET)
    return updates
