"""
component_analysis/dla.py — what each Component writes at the Readout.

Direct logit attribution asks, of every Circuit Component, how much of the
model's own preference for the deceptive answer that Component put there
directly: its output projected through the final norm and the unembedding onto

    logit(Target) - logit(Distractor)

at the Readout position. A head that pushes the other way — a **suppressor**,
in the role vocabulary — comes out negative, which is why the flag exists
rather than a ranking by magnitude alone. The logit lens is the same readout
applied to the *cumulative* residual stream layer by layer, so the layer where
the deceptive answer overtakes the honest one is visible as a sign flip.

**The metric always points the same way: logit(deceptive answer) minus
logit(honest answer).** Under pressure that is the dataset's own
`target` minus `distractor`. On the **Honest Twin** it is not:
`dataset.deception_common.harvest_honest_twins` swaps the two fields when it
harvests the honest split, so the twin's `target` is the honest answer. This
module negates that condition (`direction_sign`) and says so in `dla.json`'s
meta. Without it a mover would read as a suppressor on the honest twin and the
two columns could not be compared at all.

Conditions, and which instances each is measured over:

    pressure             the whole test split, the pressure prompts
    honest_instruction   the causal sample's paired Honest-Instruction
                         Counterfactual — only the instances that have one
    honest_twin          the whole test split of the `<task>_honest` dataset,
                         a different population, **descriptive not paired**
    differential         pressure minus honest_instruction, per instance, over
                         the paired rows only; `pressure_paired` is its left
                         term and is reported beside it so the difference is
                         never read against the full-split mean

## The fixed scale, and why the sum adds up

RMSNorm is not linear, so "each Component's contribution to the logits" is only
well defined once a scale is fixed. ADR-0001 fixes it the standard way: the
scale the final norm actually applied at that instance's Readout, computed from
the whole residual, in fp32. With that scale held fixed the readout *is* linear
in the residual, so the Components' contributions plus the embedding's sum
exactly to the model's logit difference — which is the invariant
`tests/test_dla.py` asserts, and the thing that catches a transposed projection
or a mis-sliced head.

`hooks.readout_logits(model, contribution, scale_from=residual)` is that fp32
readout: `scale_from` is the vector whose RMS sets the norm's scale, so one
Component's contribution is normalized by the whole residual's scale rather
than its own. See `fixed_scale_readout`.

The **logit lens** does not use the fixed scale: each layer's cumulative
residual is normalized by its own RMS, which is what a logit lens is — the
model's prediction if that layer's residual were the final one.

## What a head writes

`Capture.outputs[("head", l, h)]` is the input to `o_proj`, sliced to head h's
own `head_dim` columns. The residual stream receives `o_proj` of the whole
concatenation, and `o_proj` is a bias-free linear map, so head h's own
contribution is its slice times the matching *columns* of `o_proj.weight`. MLP
blocks and the embedding write their outputs into the residual stream directly.

`hooks.o_proj_weight(model, layer)` supplies that weight and asserts the
projection has no bias, so every model access in this analysis goes through the
one hook module ADR-0001 confines them to.
"""

from __future__ import annotations

import math
import os
from typing import Dict, List, Optional, Sequence

NAME = "dla"
SUBDIR = "dla"

#: The per-Component table and its figure.
JSON_NAME = "dla.json"
PNG_NAME = "dla.png"
#: The cumulative-residual lens and its figure.
LENS_JSON_NAME = "logit_lens.json"
LENS_PNG_NAME = "logit_lens.png"

SCHEMA_VERSION = 1

#: The three conditions, in the order they are measured and plotted.
PRESSURE = "pressure"
HONEST_INSTRUCTION = "honest_instruction"
HONEST_TWIN = "honest_twin"
CONDITIONS = (PRESSURE, HONEST_INSTRUCTION, HONEST_TWIN)

#: How far below zero a mean has to sit to be called suppression, in logits.
#: Read it against the two scales it sits between. The whole model's Readout
#: logit difference on SDR nls0.3 is about +1.75 and the clean-minus-corrupt
#: gap about +3.26 (ticket 02b), so 0.05 is a few percent of the effect. But a
#: single Component writes far less: on that circuit the largest direct
#: contribution is +0.18 and most are under 0.05, so this margin is not a small
#: fraction of a Component's own mass, and on a circuit whose Components each
#: write little it will flag nothing. That is deliberate — the flag exists to
#: name a Component that genuinely pushes the honest answer, not to rank the
#: noise — and it is a flag, `--dla-suppression-margin`, with the standard
#: error of every mean in `dla.json` for a reader who wants another rule.
DEFAULT_SUPPRESSION_MARGIN = 0.05

#: `--dla-split` levels, sharing ticket 03's vocabulary: the record fields a
#: condition's instances are grouped by before averaging.
SPLITS: Dict[str, tuple] = {
    "none": (),
    "designation": ("designation_polarity",),
    "item": ("item_polarity",),
    "both": ("designation_polarity", "item_polarity"),
}

#: The stratum every instance belongs to, whatever `--dla-split` says.
ALL = "all"


# ==============================================================================
# THE RULES, WITHOUT A MODEL
# ==============================================================================

def direction_sign(condition: str) -> int:
    """+1, or -1 for a condition whose dataset labels the answers the other way.

    Every column is logit(deceptive answer) - logit(honest answer). The Honest
    Twin split is harvested by `harvest_honest_twins`, which swaps `target` and
    `distractor` because on those instances the model gave the honest answer.
    Reading its fields as they stand would negate the column, so a mover would
    look like a suppressor and the honest and pressure columns could not be
    compared.
    """
    if condition not in CONDITIONS:
        raise ValueError(f"{condition!r} is not one of {', '.join(CONDITIONS)}")
    return -1 if condition == HONEST_TWIN else 1


def mean_and_se(values: Sequence[float]) -> dict:
    """Mean and standard error of the mean over instances.

    One instance has a mean and no standard error rather than a zero one: a
    zero would read as "measured, and certain".
    """
    values = [float(one) for one in values]
    if not values:
        return {"mean": None, "se": None, "n": 0}
    n = len(values)
    mean = sum(values) / n
    if n == 1:
        return {"mean": mean, "se": None, "n": 1}
    variance = sum((one - mean) ** 2 for one in values) / (n - 1)
    return {"mean": mean, "se": math.sqrt(variance / n), "n": n}


def is_suppressing(mean: Optional[float], *, margin: float) -> Optional[bool]:
    """Whether a Component's mean DLA favours the Distractor beyond `margin`.

    None in, None out: a Component this condition did not measure is unflagged,
    which is not the same as measured and not suppressing.
    """
    if mean is None:
        return None
    return bool(mean < -abs(margin))


def sign_flip_layer(values: Sequence[Optional[float]]) -> Optional[int]:
    """The layer at which the lens takes its final sign and keeps it.

    `values` is the mean logit difference per row of the cumulative residual,
    row 0 being the embedding and row `l + 1` the output of layer `l`. The
    answer is the first row of the unbroken run that reaches the end, so a lens
    that crosses the axis twice reports the later crossing — the earlier one
    did not decide anything. None when the last row is already the sign of the
    first (nothing flipped) or the lens ends on exactly zero.
    """
    rows = [None if one is None else float(one) for one in values]
    if not rows or rows[-1] is None or rows[-1] == 0.0:
        return None
    final = 1 if rows[-1] > 0 else -1
    index = len(rows) - 1
    while index > 0:
        previous = rows[index - 1]
        if previous is None or (1 if previous > 0 else -1 if previous < 0 else 0) != final:
            return index
        index -= 1
    return None


def sign_changes(values: Sequence[Optional[float]]) -> List[int]:
    """Every row where the lens changes sign from the row before it.

    Reported beside `sign_flip_layer` because the one number cannot say how
    decisive the crossing was. On the SDR circuit the lens sits within a tenth
    of a logit of zero for the first eighteen rows and crosses once, very
    early, so "the flip is at row 1" is true and a reader who sees only that
    would think the deceptive answer led from the start.
    """
    rows = [None if one is None else float(one) for one in values]
    out = []
    for index in range(1, len(rows)):
        before, after = rows[index - 1], rows[index]
        if before is None or after is None:
            continue
        if (before > 0) != (after > 0) and before != 0 and after != 0:
            out.append(index)
    return out


def stratum_of(record: dict, factors: Sequence[str]) -> str:
    """The split level an instance belongs to, as one readable key.

    A factor the records do not carry is skipped rather than turning every
    instance into an "unknown" stratum: FAR and SER test splits are
    identity-only, and a split level with one level is still a level.
    """
    parts = [f"{factor}={record[factor]}" for factor in factors
             if record.get(factor) is not None]
    return "/".join(parts) if parts else ALL


# ==============================================================================
# WHAT EACH COMPONENT WRITES INTO THE RESIDUAL STREAM
# ==============================================================================

#: Components read through the fp32 readout at once. The readout materializes
#: `[batch, chunk, vocab]` in float32 — 78 MB at batch 8 and 16 Components on
#: Llama-3.1-8B's 128k vocabulary — so a completeness sweep over every head in
#: the model stays bounded instead of asking for 5 GB in one allocation.
READOUT_CHUNK = 16

#: The kinds that write into the residual stream. Q, K, V, the MLP input and
#: the Readout are receivers: they read the stream rather than adding to it, so
#: attributing logits to one would double-count whatever wrote it.
SENDER_KINDS = ("embed", "head", "mlp")


def component_contributions(model, capture, keys) -> "torch.Tensor":
    """`[batch, len(keys), hidden]`: what each key added to the residual stream.

    At the Readout position of each row. A head's output is its `o_proj` input
    slice mapped through that head's columns of `o_proj.weight`; an MLP block's
    and the embedding's outputs go into the stream as they are.
    """
    import torch

    rows = torch.arange(capture.readout.shape[0], device=capture.readout.device)
    out = []
    for key in keys:
        kind, layer, index = (key.key if hasattr(key, "key") else key)
        if kind not in SENDER_KINDS:
            raise ValueError(
                f"{kind!r} does not write into the residual stream, so it has "
                f"no direct logit attribution; expected one of "
                f"{', '.join(SENDER_KINDS)}")
        value = capture.outputs[(kind, int(layer), int(index))]
        value = value[rows, capture.readout, :].float()
        if kind == "head":
            head_dim = value.shape[-1]
            weight = hooks_module().o_proj_weight(model, int(layer)).float()
            span = slice(int(index) * head_dim, (int(index) + 1) * head_dim)
            value = value @ weight[:, span].T
        out.append(value)
    return torch.stack(out, dim=1)


def fixed_scale_readout(model, contributions, residual) -> "torch.Tensor":
    """`[batch, k, vocab]` fp32 logits of each contribution at the *residual's* scale.

    RMSNorm is only linear once its scale is fixed, and the scale that makes
    the contributions add up to the model's own logits is the one the final
    norm actually applied: the whole residual's, at that instance's Readout.
    `hooks.readout_logits` takes it as `scale_from`, so every Component is
    normalized by the same number and the parts sum to the whole.

    The readout is chunked over Components because it materializes
    `[batch, chunk, vocab]` in float32 — a completeness sweep over every head
    in the model would otherwise ask for one allocation of several gigabytes.
    """
    import torch

    contributions = contributions.float()
    scale_from = residual.float().unsqueeze(1)
    chunks = [hooks_module().readout_logits(model, contributions[:, span],
                                            scale_from=scale_from)
              for span in (slice(start, start + READOUT_CHUNK) for start in
                           range(0, contributions.shape[1], READOUT_CHUNK))]
    return torch.cat(chunks, dim=1)


def hooks_module():
    """`component_analysis.hooks`, imported on use.

    Every analysis module is imported on the login node when the parser is
    built, and the login node has no nnsight 0.7.0. `hooks` imports nnsight
    inside its own functions, so importing it is in fact safe; importing it
    here keeps that from being something a reader has to check.
    """
    from component_analysis import hooks

    return hooks


def component_logit_difference(model, capture, keys, *, target, distractor
                               ) -> "torch.Tensor":
    """`[batch, len(keys)]`: each key's direct contribution to logit(T) - logit(D).

    In fp32, through the real final norm at the fixed scale. Summed over every
    head, every MLP block and the embedding, this equals the model's own logit
    difference at the Readout.
    """
    import torch

    contributions = component_contributions(model, capture, keys)
    logits = fixed_scale_readout(model, contributions,
                                 capture.residual[:, -1, :])
    return _difference_over_rows(logits, target, distractor)


def lens_logit_difference(model, capture, *, target, distractor) -> "torch.Tensor":
    """`[batch, num_layers + 1]`: the logit lens of the cumulative residual.

    Row 0 is the embedding's output, row `l + 1` the residual after layer `l`,
    each read through the final norm **at its own scale** — that is what a
    logit lens is, the prediction the model would make if this layer's residual
    were the last one. The fixed scale belongs to the per-Component
    attribution, where the parts have to add up; here each row is a whole
    residual in its own right.
    """
    logits = hooks_module().readout_logits(model, capture.residual)
    return _difference_over_rows(logits, target, distractor)


def _difference_over_rows(logits, target, distractor) -> "torch.Tensor":
    """`target_minus_distractor` over a `[batch, k, vocab]` stack.

    The hook takes one answer id per row of a `[batch, vocab]` tensor, so the
    stack is flattened and the ids repeated per row rather than broadcast —
    passing the stack straight in would index the Component axis by a token id
    and return a number for the wrong thing without raising.
    """
    batch, k, vocab = logits.shape
    target = target.to(logits.device).repeat_interleave(k)
    distractor = distractor.to(logits.device).repeat_interleave(k)
    flat = hooks_module().target_minus_distractor(
        logits.reshape(batch * k, vocab), target, distractor)
    return flat.reshape(batch, k)


# ==============================================================================
# TALLYING OVER INSTANCES
# ==============================================================================

class Tally:
    """Per-instance DLA values, kept until the means and standard errors are due.

    One list per (Component, split level) and one per (layer, split level) for
    the lens. The values are kept rather than summed because the standard error
    needs the spread, and 1000 instances of a 19-Component circuit is a few tens
    of thousands of floats.
    """

    def __init__(self, keys, *, factors=(), sign: int = 1):
        self.keys = [tuple(key) for key in keys]
        self.factors = tuple(factors)
        self.sign = sign
        self.components: Dict[tuple, Dict[str, list]] = {
            key: {} for key in self.keys}
        self.lens: Dict[str, list] = {}
        self.totals: Dict[str, Dict[str, list]] = {}
        self.ids: List[str] = []

    def add(self, records, ids, per_component, lens, total, circuit_sum,
            embedding) -> None:
        """One batch's per-instance values, already read out of the model."""
        for row, record in enumerate(records):
            strata = {ALL}
            if self.factors:
                strata.add(stratum_of(record, self.factors))
            for stratum in strata:
                for column, key in enumerate(self.keys):
                    self.components[key].setdefault(stratum, []).append(
                        self.sign * float(per_component[row, column]))
                self.lens.setdefault(stratum, []).append(
                    [self.sign * float(one) for one in lens[row]])
                bucket = self.totals.setdefault(stratum, {})
                bucket.setdefault("model_logit_difference", []).append(
                    self.sign * float(total[row]))
                bucket.setdefault("circuit_components_sum", []).append(
                    self.sign * float(circuit_sum[row]))
                bucket.setdefault("embedding", []).append(
                    self.sign * float(embedding[row]))
                bucket.setdefault("outside_circuit", []).append(
                    self.sign * float(total[row] - circuit_sum[row]
                                      - embedding[row]))
        self.ids.extend(ids)

    # -- reading it back ----------------------------------------------------

    @property
    def n_instances(self) -> int:
        return len(self.ids)

    def levels(self) -> List[str]:
        """Every split level seen, `all` first."""
        seen = {stratum for value in self.components.values() for stratum in value}
        seen.update(self.lens)
        return [ALL] + sorted(one for one in seen if one != ALL)

    def component_stats(self, key) -> Dict[str, dict]:
        return {stratum: mean_and_se(values)
                for stratum, values in self.components[tuple(key)].items()}

    def lens_stats(self) -> Dict[str, dict]:
        """Per split level: the mean lens per layer, its standard error, the flip."""
        out = {}
        for stratum, rows in self.lens.items():
            per_layer = list(zip(*rows)) if rows else []
            stats = [mean_and_se(one) for one in per_layer]
            out[stratum] = {
                "n": len(rows),
                "mean": [one["mean"] for one in stats],
                "se": [one["se"] for one in stats],
                "sign_flip_layer": sign_flip_layer([one["mean"] for one in stats]),
                "sign_changes": sign_changes([one["mean"] for one in stats]),
            }
        return out

    def total_stats(self) -> Dict[str, dict]:
        return {stratum: {name: mean_and_se(values)
                          for name, values in bucket.items()}
                for stratum, bucket in self.totals.items()}


def paired_difference(left: Tally, right: Tally) -> Tally:
    """A tally of `left - right`, instance by instance.

    Both must have been filled from the same rows in the same order, which is
    what makes the differential a paired contrast rather than a difference of
    two population means.
    """
    if left.ids != right.ids:
        raise ValueError(
            "the differential is paired, so both sides must cover the same "
            f"instances in the same order; got {len(left.ids)} and "
            f"{len(right.ids)}")
    out = Tally(left.keys, factors=left.factors)
    out.ids = list(left.ids)
    for key in out.keys:
        for stratum, values in left.components[key].items():
            other = right.components[key][stratum]
            out.components[key][stratum] = [a - b for a, b in zip(values, other)]
    for stratum, rows in left.lens.items():
        other = right.lens[stratum]
        out.lens[stratum] = [[a - b for a, b in zip(one, two)]
                             for one, two in zip(rows, other)]
    for stratum, bucket in left.totals.items():
        out.totals[stratum] = {
            name: [a - b for a, b in zip(values, right.totals[stratum][name])]
            for name, values in bucket.items()}
    return out


# ==============================================================================
# MEASURING A CONDITION
# ==============================================================================

def measure_batch(model, keys, input_ids, attention_mask, readout, target,
                  distractor):
    """One forward: per-key DLA, the lens, and the model's own logit difference."""
    hooks = hooks_module()
    capture = hooks.capture_forward(model, input_ids, attention_mask,
                                    components=keys, positions=readout)
    per_component = component_logit_difference(model, capture, keys,
                                               target=target,
                                               distractor=distractor)
    lens = lens_logit_difference(model, capture, target=target,
                                 distractor=distractor)
    # The lens's last row is this same number by construction. It is read
    # again, on its own, because it is what the per-Component sum is checked
    # against — a quantity that checks itself checks nothing — and one more
    # readout of a [batch, hidden] residual is the cheapest pass here.
    total = hooks.target_minus_distractor(
        hooks.readout_logits(model, capture.residual[:, -1, :]),
        target, distractor)
    return per_component, lens, total


def _to_device(model, *tensors):
    device = hooks_module().device_and_dtype(model)[0]
    return [one.to(device) for one in tensors]


def _add_batch(tally, records, ids, per_component, lens, total) -> None:
    """Split the per-key column block into circuit, embedding and remainder.

    The embedding is a sender and not a Component, so it is not part of the
    circuit's own sum; it is found by key rather than by position, so a caller
    that orders its keys differently still gets the right split.
    """
    import torch

    embed = tuple(hooks_module().EMBED_KEY)
    columns_of_circuit = [index for index, key in enumerate(tally.keys)
                          if key != embed]
    circuit_sum = per_component[:, columns_of_circuit].sum(dim=1)
    embedding = (per_component[:, tally.keys.index(embed)]
                 if embed in tally.keys
                 else torch.zeros_like(circuit_sum))
    tally.add(records, ids, per_component, lens, total, circuit_sum, embedding)


def measure_condition(model, batches, keys, *, factors=(), sign: int = 1,
                      max_batches: int = 0) -> Tally:
    """Every batch of one condition, tallied per Component and per split level."""
    tally = Tally(keys, factors=factors, sign=sign)
    for index, batch in enumerate(batches):
        if max_batches and index >= max_batches:
            break
        input_ids, attention_mask, readout, target, distractor = _to_device(
            model, batch.input_ids, batch.attention_mask, batch.readout,
            batch.target_token, batch.distractor_token)
        per_component, lens, total = measure_batch(
            model, keys, input_ids, attention_mask, readout, target, distractor)
        _add_batch(tally, batch.records, batch.ids, per_component, lens, total)
    return tally


def measure_paired(model, batches, keys, *, factors=(), max_batches: int = 0):
    """(pressure tally, honest-instruction tally, differential, unpaired ids).

    Both tallies are filled from the same rows in the same order — only the
    instances of the causal sample that have a Matched Honest survivor — so the
    differential is a per-instance paired contrast. The instances without a
    counterpart are named rather than dropped silently; they are the reason the
    paired columns have a smaller n than the pressure column.
    """
    import torch

    pressure = Tally(keys, factors=factors)
    honest = Tally(keys, factors=factors)
    unpaired: List[str] = []

    for index, batch in enumerate(batches):
        if max_batches and index >= max_batches:
            break
        pair = batch.honest
        if pair is None:
            unpaired.extend(batch.ids)
            continue
        rows = list(pair.rows)
        unpaired.extend(one for row, one in enumerate(batch.ids)
                        if row not in set(rows))
        selector = torch.tensor(rows, dtype=torch.long)
        readout = batch.readout[selector]
        if not torch.equal(pair.attention_mask.sum(-1).long() - 1, readout):
            raise ValueError(
                "an Honest-Instruction Counterfactual does not end at the same "
                "position as its pressure prompt, so the two Readouts are not "
                "the same token; the pool has drifted from the dataset")

        records = [batch.records[row] for row in rows]
        ids = [batch.ids[row] for row in rows]
        target, distractor = batch.target_token[selector], \
            batch.distractor_token[selector]

        clean_args = _to_device(model, batch.input_ids[selector],
                                batch.attention_mask[selector], readout,
                                target, distractor)
        _add_batch(pressure, records, ids,
                   *measure_batch(model, keys, *clean_args))

        honest_args = _to_device(model, pair.input_ids, pair.attention_mask,
                                 readout, target, distractor)
        _add_batch(honest, records, ids,
                   *measure_batch(model, keys, *honest_args))

    return pressure, honest, paired_difference(pressure, honest), unpaired


def sum_check(model, batch, keys) -> dict:
    """Does the invariant hold on the real model, at bfloat16, on one batch?

    The tiny-model test asserts that DLA over every head, every MLP block and
    the embedding equals the model's own logit difference. That test runs in
    fp32 on the CPU; this records the same quantity where the analysis actually
    runs, because bfloat16 captures summed in fp32 are not obliged to reproduce
    the residual the model built by adding them in bfloat16.
    """
    input_ids, attention_mask, readout, target, distractor = _to_device(
        model, batch.input_ids, batch.attention_mask, batch.readout,
        batch.target_token, batch.distractor_token)
    per_component, _lens, total = measure_batch(
        model, keys, input_ids, attention_mask, readout, target, distractor)
    error = (per_component.sum(dim=1) - total).abs()
    return {
        "n_senders": len(keys),
        "n_instances": int(input_ids.shape[0]),
        "max_abs_error": float(error.max()),
        "mean_abs_error": float(error.mean()),
        "mean_abs_logit_difference": float(total.abs().mean()),
    }


# ==============================================================================
# WHERE EACH CONDITION'S PROMPTS COME FROM
# ==============================================================================

def wanted_conditions(cli) -> List[str]:
    """`--dla-conditions`, validated by name."""
    raw = getattr(cli, "dla_conditions", None) or ",".join(CONDITIONS)
    wanted = [one.strip() for one in raw.split(",") if one.strip()]
    unknown = [one for one in wanted if one not in CONDITIONS]
    if unknown:
        raise ValueError(
            f"--dla-conditions names {', '.join(unknown)}, which "
            f"{'is' if len(unknown) == 1 else 'are'} not a DLA condition. "
            f"Choose from {', '.join(CONDITIONS)}.")
    return [one for one in CONDITIONS if one in wanted]


def honest_twin_dir(ctx) -> str:
    """Where the Honest Twin split lives: `<dataset>_honest`, or the flag.

    The twin is a second dataset directory rather than a flag on the loader —
    a different population of instances under the same Scaffold — which is
    exactly why its column is descriptive and not paired.
    """
    from component_analysis import instances

    override = getattr(ctx.cli, "dla_honest_twin_dir", None)
    if override:
        return override
    return instances.dataset_dir(ctx.task_spec) + "_honest"


def dataset_of(ctx, condition: str) -> str:
    """Which dataset directory a condition's prompts come from.

    Written into `dla.json` because "honest" names two different things here —
    the paired counterfactual built from the task's own split, and the Honest
    Twin's separate split — and a reader of the file should not have to infer
    which one a column came from.
    """
    from component_analysis import instances

    if condition == HONEST_TWIN:
        return honest_twin_dir(ctx)
    return instances.dataset_dir(ctx.task_spec)


def condition_batches(ctx, condition: str):
    """The loader one condition runs over, or `LoaderUnavailable` with the reason."""
    from component_analysis import dataloaders

    reason = dataloaders.uncovered_reason(ctx.task_spec.name)
    if reason:
        raise dataloaders.LoaderUnavailable(reason)
    if ctx.tokenizer is None:
        raise dataloaders.LoaderUnavailable(
            f"task {ctx.task_spec.name!r} has no resolved tokenizer, so its "
            f"prompts cannot be encoded")

    if condition == PRESSURE:
        return ctx.descriptive_batches()
    if condition == HONEST_INSTRUCTION:
        batches = ctx.causal_batches()
        if not batches.report["n_with_honest"]:
            raise dataloaders.LoaderUnavailable(
                f"no instance of the causal sample has an Honest-Instruction "
                f"Counterfactual ({batches.report['honest_source']}), so there "
                f"is nothing to pair against")
        return batches

    directory = honest_twin_dir(ctx)
    if not os.path.isdir(directory):
        raise dataloaders.LoaderUnavailable(
            f"no Honest Twin dataset at {directory}; bind one with "
            f"--dla-honest-twin-dir")
    return dataloaders.descriptive_batches(
        directory, ctx.tokenizer, task=ctx.task_spec.name,
        batch_size=getattr(ctx.cli, "batch_size", dataloaders.DEFAULT_BATCH_SIZE))


# ==============================================================================
# THE ANALYSIS PROTOCOL
# ==============================================================================

def add_arguments(group) -> None:
    group.add_argument("--dla-conditions", default=",".join(CONDITIONS),
                       metavar="NAME[,NAME]",
                       help="Which conditions to measure: "
                            f"{', '.join(CONDITIONS)}. A condition whose data "
                            f"this cell does not have is reported and skipped.")
    group.add_argument("--dla-split", default="none", choices=sorted(SPLITS),
                       help="Group instances by this factor set before "
                            "averaging. The head-table columns are always the "
                            "ungrouped means; the levels are in dla.json.")
    group.add_argument("--dla-suppression-margin", type=float,
                       default=DEFAULT_SUPPRESSION_MARGIN,
                       help="How far below zero the mean pressure DLA must sit "
                            "for a Component to be flagged as suppressing, in "
                            "logits.")
    group.add_argument("--dla-honest-twin-dir", default=None,
                       help="The Honest Twin dataset for the descriptive "
                            "column. Default: the task's dataset directory "
                            "with '_honest' appended.")
    group.add_argument("--dla-max-batches", type=int, default=0,
                       help="Stop each condition after this many batches. 0 "
                            "runs all of them; a small number is a smoke run.")
    group.add_argument("--dla-sum-check", default="on", choices=["on", "off"],
                       help="Record, on one batch, whether DLA over every "
                            "sender in the model reproduces the Readout logit "
                            "difference. One extra forward pass.")


def estimate(ctx) -> str:
    """`--dry-run`: how many instances each condition would read, per condition."""
    from component_analysis import dataloaders

    parts = []
    for condition in wanted_conditions(ctx.cli):
        try:
            batches = condition_batches(ctx, condition)
        except dataloaders.LoaderUnavailable as unavailable:
            if condition == PRESSURE:
                raise
            parts.append(f"{condition} not applicable ({unavailable})")
            continue
        n_instances = batches.n_instances
        n_batches = len(batches)
        if condition == HONEST_INSTRUCTION:
            n_instances = batches.report["n_with_honest"]
            parts.append(f"{condition} {n_instances} paired instance(s) of "
                         f"{batches.n_instances} sampled, 2 forward passes each")
            continue
        parts.append(f"{condition} {n_instances} instance(s) in {n_batches} "
                     f"batch(es), 1 forward pass each")
    return (f"{len(ctx.components)} Component(s); " + "; ".join(parts)
            + f"; split by {getattr(ctx.cli, 'dla_split', 'none')}")


def run(ctx) -> dict:
    """Measure every requested condition, write the files, return the columns."""
    from component_analysis import dataloaders

    hooks = hooks_module()
    factors = SPLITS[getattr(ctx.cli, "dla_split", "none")]
    margin = getattr(ctx.cli, "dla_suppression_margin",
                     DEFAULT_SUPPRESSION_MARGIN)
    max_batches = getattr(ctx.cli, "dla_max_batches", 0)
    keys = [tuple(component.key) for component in ctx.components] \
        + [hooks.EMBED_KEY]

    tallies: Dict[str, Tally] = {}
    sources: Dict[str, dict] = {}
    skipped: Dict[str, str] = {}
    unpaired: List[str] = []
    checked = None

    for condition in wanted_conditions(ctx.cli):
        try:
            batches = condition_batches(ctx, condition)
        except dataloaders.LoaderUnavailable as unavailable:
            skipped[condition] = str(unavailable)
            continue
        sources[condition] = dict(batches.report, dataset_dir=dataset_of(
            ctx, condition), paired=(condition == HONEST_INSTRUCTION))
        if condition == HONEST_INSTRUCTION:
            paired, honest, difference, unpaired = measure_paired(
                ctx.model, batches, keys, factors=factors,
                max_batches=max_batches)
            tallies[HONEST_INSTRUCTION] = honest
            tallies["pressure_paired"] = paired
            tallies["differential"] = difference
            continue
        tallies[condition] = measure_condition(
            ctx.model, batches, keys, factors=factors,
            sign=direction_sign(condition), max_batches=max_batches)
        if condition == PRESSURE and \
                getattr(ctx.cli, "dla_sum_check", "on") == "on":
            checked = sum_check(ctx.model, next(iter(batches)),
                                hooks.all_component_keys(ctx.model))

    payload = dla_payload(ctx, tallies, sources, skipped, keys, margin=margin,
                          factors=factors, unpaired=unpaired,
                          sum_check_result=checked)
    lens = lens_payload(ctx, tallies)
    ctx.write_json(SUBDIR, JSON_NAME, payload)
    ctx.write_json(SUBDIR, LENS_JSON_NAME, lens)
    directory = ctx.subdir(SUBDIR)
    plot_components(os.path.join(directory, PNG_NAME), payload)
    plot_lens(os.path.join(directory, LENS_PNG_NAME), lens)
    return columns(payload)


# ==============================================================================
# THE FILES
# ==============================================================================

#: What every number in both files means, written into each of them so a reader
#: who opens only the JSON never has to guess the sign.
METRIC = ("logit(deceptive answer) - logit(honest answer) at the Readout, in "
          "float32 through the model's own final RMSNorm and unembedding. The "
          "Honest Twin split labels its answers the other way round "
          "(harvest_honest_twins swaps target and distractor), so that "
          "condition is negated into the same direction as the others.")

FIXED_SCALE = ("Per-Component attribution holds the final-norm scale at the "
               "value the whole residual produced at that instance's Readout, "
               "so the contributions are linear and sum to the model's own "
               "logit difference. The logit lens instead normalizes each "
               "layer's cumulative residual by its own scale, which is what a "
               "lens is.")


def label_of(key) -> str:
    """`L17H3` for a head, `L17 MLP` for an MLP block, `embed` for the embedding."""
    kind, layer, index = tuple(key)
    if kind == "head":
        return f"L{layer}H{index}"
    if kind == "mlp":
        return f"L{layer} MLP"
    return kind


def _component_row(tally, key) -> dict:
    kind, layer, index = tuple(key)
    return {"key": [kind, layer, index], "kind": kind, "layer": layer,
            "index": index, "label": label_of(key),
            "levels": tally.component_stats(key)}


def dla_payload(ctx, tallies, sources, skipped, keys, *, margin, factors,
                unpaired, sum_check_result) -> dict:
    """`dla/dla.json`: every condition, every Component, every split level."""
    import time

    embed = hooks_module().EMBED_KEY
    components = [key for key in keys if tuple(key) != tuple(embed)]

    conditions = {}
    for name, tally in tallies.items():
        conditions[name] = {
            "n_instances": tally.n_instances,
            "instance_ids": tally.ids,
            "direction_sign": tally.sign,
            "levels": tally.levels(),
            "totals": tally.total_stats(),
            "components": [_component_row(tally, key) for key in components],
            "embedding": {"label": "embed",
                          "levels": tally.component_stats(embed)},
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "analysis": NAME,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "circuit": ctx.circuit_spec.label,
        "task": ctx.task_spec.name,
        "metric": METRIC,
        "fixed_scale": FIXED_SCALE,
        "suppression_margin": margin,
        "split": getattr(ctx.cli, "dla_split", "none"),
        "split_factors": list(factors),
        "n_components": len(components),
        "conditions": conditions,
        "sources": sources,
        "skipped": skipped,
        "unpaired_instance_ids": unpaired,
        "sum_check": sum_check_result,
    }


def lens_payload(ctx, tallies) -> dict:
    """`dla/logit_lens.json`: the cumulative residual's logit difference per layer.

    Row 0 is the embedding's output and row `l + 1` the residual after layer
    `l`, so a circuit of 32 layers has 33 rows and the last one is the model's
    own logit difference.
    """
    import time

    conditions = {}
    for name, tally in tallies.items():
        stats = tally.lens_stats()
        if not stats:
            continue
        conditions[name] = {
            "n_instances": tally.n_instances,
            "n_rows": len(stats[ALL]["mean"]) if ALL in stats else 0,
            "sign_flip_layer": stats.get(ALL, {}).get("sign_flip_layer"),
            "sign_changes": stats.get(ALL, {}).get("sign_changes", []),
            "levels": stats,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "analysis": NAME,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "circuit": ctx.circuit_spec.label,
        "task": ctx.task_spec.name,
        "metric": METRIC,
        "rows": "row 0 is the embedding's output; row l+1 is the residual "
                "stream after decoder layer l, read at the Readout",
        "conditions": conditions,
    }


def columns(payload) -> dict:
    """The head-table columns, namespaced under `dla` by the CLI.

    The embedding is a sender but not a Component, so it stays in the JSON and
    never becomes a row here.
    """
    margin = payload["suppression_margin"]
    by_condition = {
        name: {tuple(row["key"]): row["levels"].get(ALL, {})
               for row in condition["components"]}
        for name, condition in payload["conditions"].items()}

    def value(condition, key, field="mean"):
        return by_condition.get(condition, {}).get(key, {}).get(field)

    ordered = []
    for condition in payload["conditions"].values():
        for row in condition["components"]:
            if tuple(row["key"]) not in ordered:
                ordered.append(tuple(row["key"]))

    out = {}
    for key in ordered:
        pressure = value(PRESSURE, key)
        out[key] = {
            "pressure": pressure,
            "pressure_se": value(PRESSURE, key, "se"),
            "honest_instruction": value(HONEST_INSTRUCTION, key),
            "pressure_paired": value("pressure_paired", key),
            "differential": value("differential", key),
            "differential_se": value("differential", key, "se"),
            "honest_twin": value(HONEST_TWIN, key),
            "suppression": is_suppressing(pressure, margin=margin),
        }
    return out


# ==============================================================================
# THE FIGURES
# ==============================================================================

def _pyplot():
    """Agg, as `evaluation/report.py` does it: these run on a headless node."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


#: One colour per condition, so the two figures read as one.
COLOURS = {PRESSURE: "#2c6fbb", HONEST_INSTRUCTION: "#e08a1e",
           HONEST_TWIN: "#7f8c8d", "pressure_paired": "#5fa2dd",
           "differential": "#8e44ad"}


def plot_components(path: str, payload: dict) -> str:
    """The DLA bar chart: Components ordered by layer, suppressors marked."""
    plt = _pyplot()

    series = [name for name in (PRESSURE, HONEST_INSTRUCTION, HONEST_TWIN)
              if name in payload["conditions"]]
    if not series:
        return path
    rows = sorted(payload["conditions"][series[0]]["components"],
                  key=lambda row: (row["layer"], row["kind"] == "mlp",
                                   row["index"]))
    labels = [row["label"] for row in rows]
    order = [tuple(row["key"]) for row in rows]

    figure, axes = plt.subplots(figsize=(max(6.0, 0.5 * len(rows) + 2.5), 4.8))
    width = 0.8 / len(series)
    positions = range(len(rows))
    for offset, name in enumerate(series):
        by_key = {tuple(row["key"]): row["levels"].get(ALL, {})
                  for row in payload["conditions"][name]["components"]}
        means = [(by_key.get(key, {}).get("mean") or 0.0) for key in order]
        errors = [(by_key.get(key, {}).get("se") or 0.0) for key in order]
        axes.bar([one + offset * width - 0.4 + width / 2 for one in positions],
                 means, width, yerr=errors, capsize=2, label=name,
                 color=COLOURS.get(name, "#333333"))

    flagged = {key for key, values in columns(payload).items()
               if values["suppression"]}
    for index, key in enumerate(order):
        if key in flagged:
            axes.annotate("suppressor", (index, 0), textcoords="offset points",
                          xytext=(0, -14), ha="center", rotation=90,
                          fontsize=6, color="#c0392b")

    axes.axhline(0.0, color="black", linewidth=0.8)
    axes.set_xticks(list(positions))
    axes.set_xticklabels(labels, rotation=90, fontsize=7)
    axes.set_ylabel("direct logit attribution\n(deceptive - honest)")
    axes.set_title(f"DLA at the Readout — {payload['circuit']} x "
                   f"{payload['task']}")
    axes.legend(fontsize=7)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_lens(path: str, payload: dict) -> str:
    """The logit lens, one line per condition, the sign flip marked."""
    plt = _pyplot()

    conditions = payload["conditions"]
    if not conditions:
        return path
    figure, axes = plt.subplots(figsize=(7.5, 4.6))
    for row, (name, condition) in enumerate(conditions.items()):
        level = condition["levels"].get(ALL)
        if not level:
            continue
        means = level["mean"]
        colour = COLOURS.get(name, "#333333")
        axes.plot(range(len(means)), means, marker="o", markersize=3,
                  label=name, color=colour)
        flip = level.get("sign_flip_layer")
        if flip is None:
            continue
        axes.axvline(flip, linestyle="--", linewidth=0.9, alpha=0.6,
                     color=colour)
        # Every condition crosses in the same narrow band of layers, so the
        # labels are stacked rather than each sitting on its own line.
        axes.annotate(f"{name} at row {flip}", (flip, 0.0),
                      textcoords="offset points",
                      xytext=(4, 10 + 11 * row), fontsize=7, color=colour)

    axes.axhline(0.0, color="black", linewidth=0.8)
    axes.set_xlabel("cumulative residual: row 0 is the embedding, "
                    "row l+1 is after layer l")
    axes.set_ylabel("logit difference\n(deceptive - honest)")
    axes.set_title(f"Logit lens at the Readout — {payload['circuit']} x "
                   f"{payload['task']}")
    axes.legend(fontsize=7)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path
