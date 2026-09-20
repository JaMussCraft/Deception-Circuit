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
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# The head table's own key coercion: a Component, a (kind, layer, index)
# tuple or a key read back out of JSON all become one tuple, so a row here
# and a row there cannot disagree about what names a Component.
from component_analysis.head_table import row_key

NAME = "knockout"
SUBDIR = "knockout"

#: The files the researcher reads. The JSON is the PNG's twin: every number the
#: bar chart draws is in it, so an agent with no display loses nothing.
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
FAMILY_COLUMNS = ("family", "family_logit_diff_drop")


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
    """`{component key: {family, family_logit_diff_drop}}` for every member."""
    # `members` is written as a list, because a JSON key is not a tuple.
    return {row_key(tuple(member)): {"family": row["role"],
                              "family_logit_diff_drop": row["mean_drop"]}
            for row in rows for member in row["members"]}


def family_payload(effects: Effects, families, *, circuit: str, task: str,
                   rows=None, roles_from: str = None) -> dict:
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
# THE FIGURE
# ==============================================================================

def _label(row) -> str:
    """`L12 H7` for a head, `L12 MLP` for an MLP block."""
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
    axes.set_yticklabels([_label(row) for row in rows], fontsize=9)
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


# ==============================================================================
# THE ANALYSIS
# ==============================================================================

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
                            "where the roles pass has already run here. Give "
                            "this run its own --suite-name: an analysis run "
                            "rebuilds the head table from the intake's rows "
                            "and would drop the roles columns it just read.")


def roles_source(ctx) -> str:
    """The cell whose head table carries the roles: the flag, or this cell."""
    return getattr(ctx.cli, "knockout_roles_from", None) or ctx.cell_dir


def families_for(ctx) -> Dict[str, List[tuple]]:
    """The role families this run would ablate, read off a written head table.

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
    return families


def estimate(ctx) -> str:
    batches = ctx.causal_batches()
    passes = len(batches) * (len(ctx.components) + 2)
    line = (f"{len(ctx.components)} Component(s) x {len(batches)} batch(es) of "
            f"{batches.report['batch_size']} (+2 clean and corrupt passes per "
            f"batch) = {passes} forward pass(es), about "
            f"{passes * SECONDS_PER_FORWARD / 60:.1f} min on an A40, over "
            f"{batches.n_instances} instance(s); scheme "
            f"{resolve_scheme(getattr(ctx.cli, 'knockout_scheme', SCHEME))}")
    if not getattr(ctx.cli, "knockout_families", False):
        return line
    families = families_for(ctx)
    family_passes = len(batches) * (len(families) + 2)
    return (line + f"; plus {len(families)} role famil"
            f"{'y' if len(families) == 1 else 'ies'} "
            f"({', '.join(f'{role} x{len(members)}' for role, members in families.items())}) "
            f"from {roles_source(ctx)} = {family_passes} more forward pass(es), "
            f"about {family_passes * SECONDS_PER_FORWARD / 60:.1f} min")


def run(ctx) -> dict:
    """Knock out every Component, write the JSON and the PNG, return the columns."""
    scheme = resolve_scheme(getattr(ctx.cli, "knockout_scheme", SCHEME))
    # Read before the forwards, so a missing role column fails in seconds
    # rather than after the per-Component pass has already run.
    families = families_for(ctx) \
        if getattr(ctx.cli, "knockout_families", False) else None
    batches = ctx.causal_batches()
    effects = knockout_effects(ctx.model, batches, ctx.components, scheme=scheme)

    rows = summarize(effects, ctx.components)
    ctx.write_json(SUBDIR, JSON_NAME,
                   payload(effects, circuit=ctx.circuit_spec.label,
                           task=ctx.task_spec.name, rows=rows))
    write_figure(os.path.join(ctx.subdir(SUBDIR), PNG_NAME), rows,
                 title=f"{ctx.circuit_spec.label} x {ctx.task_spec.name}: "
                       f"per-Component {scheme} knockout")
    updates = columns(rows)
    if families is None:
        return updates

    grouped = family_effects(ctx.model, batches, families, scheme=scheme)
    family_rows = summarize_families(grouped, families)
    ctx.write_json(SUBDIR, FAMILY_JSON_NAME,
                   family_payload(grouped, families,
                                  circuit=ctx.circuit_spec.label,
                                  task=ctx.task_spec.name, rows=family_rows,
                                  roles_from=roles_source(ctx)))
    write_family_figure(os.path.join(ctx.subdir(SUBDIR), FAMILY_PNG_NAME),
                        family_rows,
                        title=f"{ctx.circuit_spec.label} x {ctx.task_spec.name}: "
                              f"{scheme} knockout by Component Role family")
    for key, values in family_columns(family_rows).items():
        updates.setdefault(key, {}).update(values)
    return updates
