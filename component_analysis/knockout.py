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

NAME = "knockout"
SUBDIR = "knockout"

#: The files the researcher reads. The JSON is the PNG's twin: every number the
#: bar chart draws is in it, so an agent with no display loses nothing.
JSON_NAME = "knockout.json"
PNG_NAME = "knockout.png"

#: The only ablation scheme that exists, and the two that do not yet.
SCHEME = "interchange"
FUTURE_SCHEMES = ("mean", "zero")

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
    """Per-instance logit differences: clean, and under each single knockout.

    One list per Component, in the order the instances came out of the loader,
    so every summary statistic below is over the causal sample and nothing is
    averaged twice.
    """

    ids: List[str]
    keys: List[tuple]
    clean_logit_diff: List[float]
    knocked_logit_diff: Dict[tuple, List[float]]
    scheme: str = SCHEME
    #: What the loader said about the sample it built; carried into the JSON.
    report: dict = field(default_factory=dict)

    def drops(self, key) -> List[float]:
        """Clean minus knocked-out, per instance. Positive helps deception."""
        return [clean - knocked for clean, knocked
                in zip(self.clean_logit_diff, self.knocked_logit_diff[key])]


def _key(component) -> tuple:
    """A `Component`, or a plain (kind, layer, index), as a tuple key."""
    key = getattr(component, "key", component)
    kind, layer, index = key
    return (str(kind), int(layer), int(index))


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


def baseline(effects: Effects) -> dict:
    """The un-knocked-out run every drop is measured against."""
    return {
        "mean_logit_difference": _mean(effects.clean_logit_diff),
        "standard_error": _standard_error(effects.clean_logit_diff),
        "accuracy": _accuracy(effects.clean_logit_diff),
        "n_instances": len(effects.clean_logit_diff),
    }


def summarize(effects: Effects, components=None) -> List[dict]:
    """One ranked row per Component, strongest drop first.

    `components` is the Component list when there is one, so that a row can
    carry the head table's `kv_group` beside the numbers; the keys alone are
    enough without it. Ties keep the order the Components came in, which is
    head-table order, so a rerun never reshuffles equal rows.
    """
    by_key = {_key(one): one for one in (components or [])}
    clean_accuracy = _accuracy(effects.clean_logit_diff)

    rows = []
    for key in effects.keys:
        knocked = effects.knocked_logit_diff[key]
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
            "knockout_logit_difference": _mean(knocked),
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


def columns(rows) -> dict:
    """The head-table update: `{component key: {column: value}}`.

    The CLI namespaces these under `knockout`, so they land as
    `knockout.knockout_logit_diff_drop` and `knockout.knockout_rank`.
    """
    return {_key(row["key"]): {
        "knockout_logit_diff_drop": row["mean_drop"],
        "knockout_rank": row["rank"],
        "knockout_standard_error": row["standard_error"],
        "knockout_accuracy": row["accuracy"],
    } for row in rows}


def payload(effects: Effects, *, circuit: str, task: str, components=None,
            rows=None) -> dict:
    """`knockout.json`: the ranked table, the baseline, and what it all means.

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
        "sample": effects.report,
        "baseline": baseline(effects),
        # JSON keys are strings, so a key is written as a list and read back
        # with `head_table.row_key`.
        "components": [{**row, "key": list(row["key"])} for row in rows],
    }


# ==============================================================================
# THE FORWARD LOOP
# ==============================================================================

def knockout_effects(model, batches, components, *, scheme=SCHEME,
                     device=None, log=None) -> Effects:
    """Knock out each Component alone, over every batch, and keep every number.

    Three kinds of forward per batch: one clean run for the baseline, one
    corrupt run that captures what each Component carried there, and one run
    per Component with that capture written over the clean stream. So a batch
    costs `len(components) + 2` passes and nothing is recomputed per Component.

    The knocked-out run is `capture_forward` rather than `replace_forward`
    because only the capture hands back the residual the final norm sees, and
    the metric has to be read from it in fp32.
    """
    import torch

    from component_analysis import hooks

    scheme = resolve_scheme(scheme)
    keys = [_key(one) for one in components]
    if device is None:
        device, _dtype = hooks.device_and_dtype(model)

    def logit_difference(capture, target, distractor):
        return hooks.target_minus_distractor(
            hooks.readout_logits(model, capture.residual[:, -1, :]),
            target, distractor).tolist()

    ids: List[str] = []
    clean_logit_diff: List[float] = []
    knocked: Dict[tuple, List[float]] = {key: [] for key in keys}

    for number, batch in enumerate(batches, start=1):
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
            clean_logit_diff.extend(logit_difference(clean, target, distractor))

            for key in keys:
                patched = hooks.capture_forward(
                    model, clean_ids, clean_mask, components=[],
                    positions=readout,
                    replacements={key: corrupt.outputs[key]})
                knocked[key].extend(logit_difference(patched, target,
                                                     distractor))
        if log is not None:
            log(f"      batch {number}: {len(batch)} instance(s), "
                f"{len(keys) + 2} forward pass(es)")

    return Effects(ids=ids, keys=keys, clean_logit_diff=clean_logit_diff,
                   knocked_logit_diff=knocked, scheme=scheme,
                   report=dict(getattr(batches, "report", {}) or {}))


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


# ==============================================================================
# THE ANALYSIS
# ==============================================================================

def add_arguments(group) -> None:
    group.add_argument("--knockout-scheme", type=resolve_scheme, default=SCHEME,
                       help=f"How a Component is ablated. {SCHEME!r} is the "
                            f"only scheme built; {' and '.join(FUTURE_SCHEMES)} "
                            f"are future work and are refused by name.")


def estimate(ctx) -> str:
    batches = ctx.causal_batches()
    passes = len(batches) * (len(ctx.components) + 2)
    return (f"{len(ctx.components)} Component(s) x {len(batches)} batch(es) of "
            f"{batches.report['batch_size']} (+2 baseline passes per batch) = "
            f"{passes} forward pass(es), about "
            f"{passes * SECONDS_PER_FORWARD / 60:.1f} min on an A40, over "
            f"{batches.n_instances} instance(s); scheme "
            f"{resolve_scheme(getattr(ctx.cli, 'knockout_scheme', SCHEME))}")


def run(ctx) -> dict:
    """Knock out every Component, write the JSON and the PNG, return the columns."""
    scheme = resolve_scheme(getattr(ctx.cli, "knockout_scheme", SCHEME))
    batches = ctx.causal_batches()
    # No `device=ctx.device`: that is what the CLI was *asked* for, and the
    # model is where the weights actually are.
    effects = knockout_effects(ctx.model, batches, ctx.components, scheme=scheme)

    rows = summarize(effects, ctx.components)
    ctx.write_json(SUBDIR, JSON_NAME,
                   payload(effects, circuit=ctx.circuit_spec.label,
                           task=ctx.task_spec.name, rows=rows))
    write_figure(os.path.join(ctx.subdir(SUBDIR), PNG_NAME), rows,
                 title=f"{ctx.circuit_spec.label} x {ctx.task_spec.name}: "
                       f"per-Component {scheme} knockout")
    return columns(rows)
