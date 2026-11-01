"""
component_analysis/route_closure.py — does the instructed route close at the quartet? (B1)

Direction `instructed-route`, phase B1 (`docs/research/instructed-route/plans/B1-plan.md`, frozen
rules in `spec.md`, ruling R1). Two questions about the layer-17 "quartet" `head.17.24..27`, which
is exactly KV group 6 of Llama-3.1-8B-Instruct:

  * **T1**, is the outside-grid share of the pressure effect mediated by the quartet's outputs?
  * **T2**, is the pressure carried to the quartet at the option-token **keys** or at the
    final-token **query**?

Every intervention is an interchange between two token-aligned streams of one instance:

    D   the `<task>_v2` pressure prompt (the cell's clean prompt)
    T   its Neutral-Clause Twin (`batch.neutral_twin`, same instance id), which differs from D
        only inside the `pressure_clause` Segment, has the same length and the same Readout,
        and is read with D's Target and Distractor

No mean or zero ablation is used anywhere (R1). The record field `neutral_prompt` is a different
control and is never read.

## The three primitives

    capture_pair(model, batch, segmentations) -> PairStreams
        D and T run whole, every sender (`hooks.all_component_keys`: the embedding, each head's
        `o_proj`-input slice, each MLP output) and every receiver (`hooks.all_receiver_keys`: each
        head's `q`, each KV group's `k` and `v`, each `mlp_in`, the Readout) captured at every
        position. The margin m = logit(Target) - logit(Distractor) is read in fp32 through
        `hooks.readout_logits`; the twin gap is G = m(D) - m(T). It also builds the position
        masks (below) and refuses a twin that is not token-aligned with D.
    restore_bank(source, keys, mask) -> {key: hooks.Replacement}
        `source` is a `Stream` or its outputs dict; `mask` is a `[batch, seq]` bool mask or None
        for every position.
    run_arm(model, pair, bank, capture_keys=(), base="D") -> ArmResult
        The `base` prompt with the bank written and every other site recomputed freely
        downstream; returns the fp32 margins (D's labels) and any captured outputs.

`q`, `k` and `v` are written at the `q_proj` / `k_proj` / `v_proj` outputs, which is before RoPE
(`hooks._traced_forward`); D and T are position-aligned, so the rotary phases match.

## Positions (scheme `mechanism_v2`, matched by Segment, never by string)

    readout                 the `readout` position (`batch.readout`, the last stem token)
    options                 item_1_question_pair + item_2_question_pair + item_1_question_option
                            + item_2_question_option; each must be present on every row
    preclause_mentions      item_1_intro + item_2_intro + designation_site (bit-identical in D
                            and T by causality, so any patch there is an exact-zero check)
    clause                  pressure_clause
    post_clause             after the last clause token, through the Readout (Readout included)
    post_clause_no_readout  the same without the Readout
    all                     every position (no mask)
    random_post_d<n>        control draw n: 4 tokens per instance drawn from post_clause_no_readout
                            minus options, seeded by (seed, draw, instance id)

## The arms

Restore direction (base D, values from T), T2 (plan section 2.2):

    q_readout        rule         q.L.h for the quartet heads, at the Readout
    k_options        rule         k.L.g (the quartet's KV group), at the options
    v_options, kv_options, qk (q at the Readout + k at the options), k_post_clause, k_clause,
    q_post_clause, out_readout (the quartet's outputs at the Readout)        descriptive
    kv_preclause_mentions   check   k and v at the pre-clause mentions (expected exactly m(D))
    ctrl_q_readout_d<n>     control q at the Readout of drawn non-quartet layer-L heads, outside
                                    C_t (the grid), one per draw
    ctrl_k_options_g<g>     control k.L.g at the options, every other KV group of layer L
    ctrl_k_random_post_d<n> control k.L.g (quartet group) at random_post_d<n>

Reverse direction (base T, values from D): `rev_q_readout`, `rev_k_options`.

T1 (plan section 1.1), the D_q arm and its descriptive variants: `dq_all` (the quartet's outputs
from T at every position; the primary run), `dq_readout`, `dq_post_clause_no_readout`; reverse
`tq_all` (T prompt, quartet outputs from D). T1's sweeps (the outside senders' direct effects
under T and D_q, the offline decomposition, C1 to C3, the S_k reference and the position-resolved
path patching) are ticket 5 and are not computed here.

Gates (always run): `g1_empty` (empty bank on D; must equal m(D) bit for bit) and
`g2_all_components` (every sender from T at every position on D; must reproduce m(T)).

## Output: `<cell>/route_closure/route_closure.json`

One file per task cell. Every per-instance list is in `instances.ids` order.

    schema              "route_closure/1"
    analysis, task, circuit
    model               `hooks.describe(model)`
    config              {route_tests, route_direction, route_sweep, route_control_draws,
                         route_control_seed, route_ct, route_deciding_set, route_pp_top,
                         route_max_batches, positions_per_draw}
    quartet             {layer, heads, kv_group}
    grid                {source: "<ct.json path>" or "cell circuit", n, keys: ["head.L.H", ...],
                         matches_cell: bool or null}
    deciding_set        {file, name, keys} or null (C2 reads it; ticket 5)
    instances           {ids, pressure_ids, without_twin}
    baseline            {m_D, m_T, G (per instance), mean_m_D, mean_m_T, mean_G,
                         P = mean_m_D - mean_m_T}
    gates               {g1_bit_identical: bool, g1_max_abs_diff, g2_max_abs_diff}
    arms_selected       [arm name, ...] in run order (gates first)
    arms                {name: {test: "t1"|"t2"|"gate", role: "rule"|"descriptive"|"check"|
                                "control"|"gate", direction: "restore"|"reverse"|"gate",
                                base: "D"|"T", source: "T"|"D",
                                writes: [{site: "q.17.24", positions: "<mask name>"}, ...]
                                        ("all components" for g2), meta: {...},
                                margins: [per instance], mean}}
    controls            {q_heads: [[h, ...] per draw], k_groups: [g, ...],
                         positions_per_draw: 4}
    positions           {first_batch: {ids, readout: [per row],
                                       masks: {name: {segments: [...], tokens: [[...] per row]}}}}
    t1                  {sweeps: {status: "not implemented: ticket 5", ...}}
    not_implemented     the ticket-5 parts, by name

A skipped cell (no instance has a twin, e.g. a v1 task or an H or F cell) writes the same file
with `skipped`, empty `arms` and `instances.without_twin` filled.

The readings (`scripts/route_closure_readings.py`, ticket 6) compute from this file:
r_a = (mean_m_D - arms[a].mean) / P for a restore arm (base D), and
r_a = (arms[a].mean - mean_m_T) / P for a reverse arm (base T), so both read as the share of the
pressure effect P the arm moves. This module computes no rule number.

Nothing here imports `hooks.py` or nnsight at module level (registry contract): `--dry-run` is a
login-node mode.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

NAME = "route_closure"
SUBDIR = "route_closure"
JSON_FILE = "route_closure.json"
SCHEMA = "route_closure/1"

#: The quartet on Llama-3.1-8B-Instruct (KV group 6); `--route-quartet` overrides it.
QUARTET_LAYER = 17
QUARTET_HEADS = (24, 25, 26, 27)
DEFAULT_QUARTET = f"{QUARTET_LAYER}:{','.join(str(h) for h in QUARTET_HEADS)}"
DEFAULT_CONTROL_DRAWS = 5
DEFAULT_CONTROL_SEED = 20261101
DEFAULT_PP_TOP = 20
#: How many random post-clause tokens one positional control draw writes.
POSITIONS_PER_DRAW = 4

T1, T2, BOTH = "t1", "t2", "both"
RESTORE, REVERSE = "restore", "reverse"
FORWARD, OFFLINE = "forward", "offline"

OPTION_SEGMENTS = ("item_1_question_pair", "item_2_question_pair",
                   "item_1_question_option", "item_2_question_option")
PRECLAUSE_MENTION_SEGMENTS = ("item_1_intro", "item_2_intro", "designation_site")
CLAUSE_SEGMENT = "pressure_clause"
READOUT_SEGMENT = "readout"
ALL = "all"

#: Mask name -> the Segments it is built from, for the JSON.
MASK_SEGMENTS = {
    "readout": [READOUT_SEGMENT],
    "options": list(OPTION_SEGMENTS),
    "preclause_mentions": list(PRECLAUSE_MENTION_SEGMENTS),
    "clause": [CLAUSE_SEGMENT],
    "post_clause": [f"after {CLAUSE_SEGMENT}", READOUT_SEGMENT],
    "post_clause_no_readout": [f"after {CLAUSE_SEGMENT}", f"not {READOUT_SEGMENT}"],
}

#: Ticket 5's parts, named in the JSON so a reader does not mistake them for zero.
NOT_IMPLEMENTED = (
    "t1.forward_sweep (O and O_q by path_patching.sweep_readout, normalized by G)",
    "t1.offline_direct_effects (fp32 decomposition through the real norm)",
    "t1.joint_swap of all outside senders",
    "t1.controls C1, C2 (offline estimator) and C3 (direction_push_bank)",
    "t1.S_k reference (deciding set restored post-clause)",
    "t1.position_resolved_path_patching (plan 1.5) and t2.path_patching (plan 2.3)",
)


# ==============================================================================
# FLAGS AND FILES
# ==============================================================================

def parse_quartet(text: str) -> Tuple[int, Tuple[int, ...]]:
    """`"17:24,25,26,27"` to `(17, (24, 25, 26, 27))`."""
    try:
        layer, heads = text.split(":")
        parsed = (int(layer), tuple(sorted(int(one) for one in heads.split(",")
                                           if one.strip())))
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"--route-quartet takes LAYER:H,H,..., got {text!r}") from None
    if not parsed[1]:
        raise argparse.ArgumentTypeError(f"--route-quartet {text!r} names no head")
    return parsed


def _quartet_arg(text: str) -> str:
    parse_quartet(text)
    return text


def _deciding_set_arg(text: str) -> Tuple[str, str]:
    path, sep, name = text.rpartition(":")
    if not sep or not path or not name:
        raise argparse.ArgumentTypeError(
            f"--route-deciding-set takes FILE:NAME, got {text!r}")
    return path, name


def add_arguments(group) -> None:
    group.add_argument("--route-tests", default=BOTH, choices=[T1, T2, BOTH],
                       help="Which B1 tests to run: t1 (the D_q arms; its sweeps are "
                            "ticket 5), t2 (the key-versus-query arms and controls), or "
                            "both. The G1 and G2 gate arms always run.")
    group.add_argument("--route-direction", default=BOTH, choices=[RESTORE, REVERSE, BOTH],
                       help="restore: the pressure prompt with sites set to their twin "
                            "values; reverse: the twin with sites set to their pressure "
                            "values (sufficiency); both.")
    group.add_argument("--route-sweep", default=BOTH, choices=[FORWARD, OFFLINE, BOTH],
                       help="T1's estimator of the outside senders' direct effects: the "
                            "forward sweep, the offline fp32 decomposition, or both. "
                            "Parsed and recorded; the sweeps are ticket 5.")
    group.add_argument("--route-control-draws", type=int, default=DEFAULT_CONTROL_DRAWS,
                       help="Seeded draws for the random-head and random-position "
                            f"controls. Default {DEFAULT_CONTROL_DRAWS}.")
    group.add_argument("--route-control-seed", type=int, default=DEFAULT_CONTROL_SEED,
                       help=f"Seed of every control draw. Default {DEFAULT_CONTROL_SEED}.")
    group.add_argument("--route-ct", default=None, metavar="FILE",
                       help="The grid C_t (mechanism-analysis phase3/ct.json); control heads "
                            "are drawn outside it. Default: the cell's own circuit.")
    group.add_argument("--route-deciding-set", type=_deciding_set_arg, default=None,
                       metavar="FILE:NAME",
                       help="The deciding set (e.g. phase1/groups/far_heldout_D.json:"
                            "greedy_k20), excluded from C2's draws and restored as the S_k "
                            "reference (ticket 5). Recorded here.")
    group.add_argument("--route-pp-top", type=int, default=DEFAULT_PP_TOP,
                       help="How many outside writers T1's path patching takes as "
                            f"receivers (ticket 5). Default {DEFAULT_PP_TOP}.")
    group.add_argument("--route-quartet", type=_quartet_arg, default=DEFAULT_QUARTET,
                       metavar="LAYER:H,H,...",
                       help="The decision heads; they must be exactly one KV group. "
                            f"Default {DEFAULT_QUARTET} (KV group 6 of Llama-3.1-8B).")
    group.add_argument("--route-max-batches", type=int, default=0,
                       help="Stop after this many batches (a smoke run). 0: all.")


def _parse_key(text: str) -> tuple:
    kind, layer, index = text.split(".")
    return (kind, int(layer), int(index))


def key_name(key) -> str:
    kind, layer, index = key
    return f"{kind}.{layer}.{index}"


def ct_task(task: str) -> str:
    """`far_v2` -> `far`: ct.json is keyed by the v1 task name."""
    return task[:-3] if task.endswith("_v2") else task


def load_ct(path: str, task: str) -> set:
    """The grid C_t of one task, as `(kind, layer, index)` keys."""
    with open(path) as handle:
        data = json.load(handle)
    tasks = data.get("tasks", {})
    name = ct_task(task)
    if name not in tasks:
        raise ValueError(f"{path} has no C_t for task {name!r}; it has "
                         f"{', '.join(sorted(tasks)) or '(none)'}")
    return {_parse_key(one) for one in tasks[name]["members"]["C_t"]}


def load_deciding_set(spec: Tuple[str, str]) -> List[tuple]:
    path, name = spec
    with open(path) as handle:
        data = json.load(handle)
    if name not in data:
        raise ValueError(f"{path} has no group {name!r}")
    return [(str(kind), int(layer), int(index)) for kind, layer, index in data[name]]


# ==============================================================================
# CONTROL DRAWS
# ==============================================================================

def draw_control_heads(*, num_heads: int, layer: int, quartet: Sequence[int],
                       excluded, n_draws: int, size: int, seed: int) -> List[List[int]]:
    """`n_draws` sorted sets of `size` layer-`layer` heads, none in the quartet or `excluded`.

    Seeded by a string (`random.Random` hashes it with SHA-512, so it is stable across
    processes, unlike the built-in `hash`).
    """
    pool = [h for h in range(num_heads)
            if h not in set(quartet) and ("head", layer, h) not in excluded]
    if len(pool) < size:
        raise ValueError(f"layer {layer} has only {len(pool)} head(s) outside the quartet "
                         f"and the grid, fewer than a control draw of {size}")
    rng = random.Random(f"{seed}:q_heads:{layer}")
    return [sorted(rng.sample(pool, size)) for _ in range(n_draws)]


def draw_control_positions(ids: Sequence[str], masks: Dict[str, "torch.Tensor"], *,
                           n_draws: int, size: int, seed: int) -> dict:
    """Per instance, `size` post-clause tokens that are neither options nor the Readout.

    Seeded per (seed, draw, instance id), so an instance gets the same tokens whatever batch
    it lands in. Returns `{"tokens": [draw][row] -> sorted list, "masks": [draw] -> [B, seq]}`.
    """
    import torch

    eligible = masks["post_clause_no_readout"] & ~masks["options"]
    tokens, out_masks = [], []
    for draw in range(n_draws):
        rows, mask = [], torch.zeros_like(eligible)
        for row, one in enumerate(ids):
            pool = eligible[row].nonzero().flatten().tolist()
            if len(pool) < size:
                raise ValueError(f"instance {one} has only {len(pool)} post-clause token(s) "
                                 f"that are neither options nor the Readout, fewer than "
                                 f"{size}")
            chosen = sorted(random.Random(f"{seed}:k_positions:{draw}:{one}").sample(pool, size))
            mask[row, chosen] = True
            rows.append(chosen)
        tokens.append(rows)
        out_masks.append(mask)
    return {"tokens": tokens, "masks": out_masks}


# ==============================================================================
# POSITION MASKS
# ==============================================================================

def _tokens(segmentation, name: str, *, required: bool) -> List[int]:
    segment = segmentation.segments.get(name)
    tokens = segment.token_indices() if segment is not None else []
    if required and not tokens:
        raise ValueError(f"instance {segmentation.record_id} has no Segment {name!r} "
                         f"(scheme {segmentation.scheme or 'unrecorded'}); route_closure "
                         f"needs it on every instance")
    return tokens


def position_masks(ids: Sequence[str], segmentations: Sequence, readout,
                   seq_len: int) -> Dict[str, "torch.Tensor"]:
    """`{mask name: [batch, seq] bool}` from each row's Segments (see the module docstring)."""
    import torch

    readout = [int(one) for one in torch.as_tensor(readout).tolist()]
    names = list(MASK_SEGMENTS)
    masks = {name: torch.zeros((len(ids), seq_len), dtype=torch.bool) for name in names}
    for row, (one, segmentation) in enumerate(zip(ids, segmentations)):
        if segmentation is None or segmentation.record_id != one:
            raise ValueError(f"instance {one} has no segmentation")
        last = readout[row]
        options = sorted(t for name in OPTION_SEGMENTS
                         for t in _tokens(segmentation, name, required=True))
        mentions = sorted(t for name in PRECLAUSE_MENTION_SEGMENTS
                          for t in _tokens(segmentation, name, required=False))
        clause = _tokens(segmentation, CLAUSE_SEGMENT, required=True)
        after = max(clause) + 1
        if set(options) & set(mentions):
            raise ValueError(f"instance {one}: option and pre-clause mention tokens overlap "
                             f"at {sorted(set(options) & set(mentions))}")
        if not all(after <= t < last for t in options):
            raise ValueError(f"instance {one}: option tokens {options} are not all after the "
                             f"Pressure Clause and before the Readout {last}")
        if any(t >= min(clause) for t in mentions):
            raise ValueError(f"instance {one}: pre-clause mention tokens {mentions} are not "
                             f"all before the Pressure Clause")
        masks["readout"][row, last] = True
        masks["options"][row, options] = True
        masks["preclause_mentions"][row, mentions] = True
        masks["clause"][row, clause] = True
        masks["post_clause"][row, after:last + 1] = True
        masks["post_clause_no_readout"][row, after:last] = True
    return masks


# ==============================================================================
# THE PAIR
# ==============================================================================

@dataclass
class Stream:
    """One prompt of the pair, run whole."""

    name: str                                   # "D" or "T"
    input_ids: "torch.Tensor"
    attention_mask: "torch.Tensor"
    #: `{key: [batch, seq, dim]}` at every captured site, every position.
    outputs: Dict[tuple, "torch.Tensor"]
    #: `[batch]` fp32 logit(Target) - logit(Distractor), D's labels.
    margin: "torch.Tensor"


@dataclass
class PairStreams:
    """D and its Neutral-Clause Twin for the rows of one batch that have a twin."""

    d: Stream
    t: Stream
    gap: "torch.Tensor"                         # [batch] fp32, m(D) - m(T)
    ids: List[str]
    rows: List[int]
    pressure_ids: List
    readout: "torch.Tensor"                     # [batch]
    target: "torch.Tensor"
    distractor: "torch.Tensor"
    segmentations: List
    #: `{mask name: [batch, seq] bool}` on the model's device.
    masks: Dict[str, "torch.Tensor"] = field(default_factory=dict)

    def stream(self, name: str) -> Stream:
        return {"D": self.d, "T": self.t}[name]


@dataclass
class ArmResult:
    margins: "torch.Tensor"                     # [batch] fp32
    outputs: Dict[tuple, "torch.Tensor"] = field(default_factory=dict)


def _margin(model, capture, target, distractor):
    """fp32 logit(Target) - logit(Distractor) of a capture that holds the Readout."""
    import torch

    from component_analysis import hooks

    rows = torch.arange(capture.logits.shape[0], device=capture.readout.device)
    residual = capture.outputs[hooks.READOUT_KEY][rows, capture.readout, :]
    logits = hooks.readout_logits(model, residual)
    return hooks.target_minus_distractor(logits, target, distractor)


def _by_id(segmentations) -> dict:
    if segmentations is None:
        return {}
    if isinstance(segmentations, dict):
        return segmentations
    return {one.record_id: one for one in segmentations}


def _check_alignment(ids, d_ids, t_ids, d_mask, t_mask, clause_span, segmentations):
    """Refuse a twin that is not D with only its Pressure Clause changed."""
    import torch

    if not torch.equal(d_mask.cpu(), t_mask.cpu()):
        raise ValueError("a Neutral-Clause Twin has a different length from its pressure "
                         "prompt, so the two streams are not token-aligned")
    differs = (d_ids.cpu() != t_ids.cpu()) & d_mask.cpu().bool()
    for row, one in enumerate(ids):
        allowed = set(range(int(clause_span[row][0]), int(clause_span[row][1])))
        allowed |= set(_tokens(segmentations[row], CLAUSE_SEGMENT, required=False))
        outside = sorted(set(differs[row].nonzero().flatten().tolist()) - allowed)
        if outside:
            raise ValueError(f"instance {one}: its twin differs from its pressure prompt "
                             f"outside the Pressure Clause, at token(s) {outside}")


def capture_pair(model, batch, segmentations, *, keys=None) -> Optional[PairStreams]:
    """D and T of the rows of `batch` that have a twin, captured whole; None when none has one.

    `keys` defaults to every sender and every receiver of the model.
    """
    import torch

    from component_analysis import hooks
    from component_analysis import path_patching as pp

    selected = pp.counterfactual_pair(batch, pp.NEUTRAL_TWIN)
    if selected is None:
        return None
    rows, t_ids, t_mask = selected
    selector = torch.tensor(rows, dtype=torch.long)
    ids = [batch.ids[row] for row in rows]
    by_id = _by_id(segmentations)
    missing = [one for one in ids if one not in by_id]
    if missing:
        raise ValueError(f"instance(s) {', '.join(missing)} have no segmentation")
    segs = [by_id[one] for one in ids]

    d_ids = batch.input_ids[selector]
    d_mask = batch.attention_mask[selector]
    _check_alignment(ids, d_ids, t_ids, d_mask, t_mask, batch.neutral_twin.clause_span,
                     segs)

    device, _dtype = hooks.device_and_dtype(model)
    if keys is None:
        keys = hooks.all_component_keys(model) + hooks.all_receiver_keys(model)
    keys = [tuple(one) for one in keys]
    if hooks.READOUT_KEY not in keys:
        keys.append(hooks.READOUT_KEY)
    readout = batch.readout[selector].to(device)
    target = batch.target_token[selector].to(device)
    distractor = batch.distractor_token[selector].to(device)

    streams = {}
    for name, input_ids in (("D", d_ids), ("T", t_ids)):
        input_ids, mask = input_ids.to(device), d_mask.to(device)
        capture = hooks.capture_forward(model, input_ids, mask, components=keys,
                                        positions=readout)
        streams[name] = Stream(name=name, input_ids=input_ids, attention_mask=mask,
                               outputs=dict(capture.outputs),
                               margin=_margin(model, capture, target, distractor))

    masks = position_masks(ids, segs, batch.readout[selector], d_ids.shape[1])
    records = getattr(batch, "records", None) or [{}] * len(batch.ids)
    return PairStreams(
        d=streams["D"], t=streams["T"], gap=streams["D"].margin - streams["T"].margin,
        ids=ids, rows=list(rows),
        pressure_ids=[(records[row] or {}).get("pressure_id") for row in rows],
        readout=readout, target=target, distractor=distractor, segmentations=segs,
        masks={name: mask.to(device) for name, mask in masks.items()})


def restore_bank(source, keys, mask) -> dict:
    """`{key: Replacement(source value, mask)}`; `mask` None writes every position."""
    from component_analysis import hooks

    outputs = getattr(source, "outputs", source)
    return {tuple(key): hooks.Replacement(outputs[tuple(key)], mask) for key in keys}


def run_arm(model, pair: PairStreams, bank: dict, capture_keys=(), *,
            base: str = "D") -> ArmResult:
    """The `base` prompt with `bank` written and everything downstream free."""
    from component_analysis import hooks

    stream = pair.stream(base)
    keys = [tuple(one) for one in capture_keys]
    capture = hooks.capture_forward(model, stream.input_ids, stream.attention_mask,
                                    components=keys + [hooks.READOUT_KEY],
                                    positions=pair.readout, replacements=bank)
    return ArmResult(margins=_margin(model, capture, pair.target, pair.distractor),
                     outputs={key: capture.outputs[key] for key in keys})


# ==============================================================================
# THE ARMS
# ==============================================================================

@dataclass
class ArmSpec:
    name: str
    test: str                                   # "t1" | "t2" | "gate"
    role: str                                   # "rule" | "descriptive" | "check" | "control" | "gate"
    direction: str                              # "restore" | "reverse" | "gate"
    base: str                                   # "D" | "T"; the source is the other stream
    writes: Tuple[Tuple[tuple, str], ...] = ()  # ((site key, mask name), ...)
    #: Write every sender (`hooks.all_component_keys`) at every position (gate G2).
    everything: bool = False
    meta: dict = field(default_factory=dict)

    @property
    def source(self) -> str:
        return "T" if self.base == "D" else "D"

    def as_json(self) -> dict:
        return {"test": self.test, "role": self.role, "direction": self.direction,
                "base": self.base, "source": self.source,
                "writes": ("all components" if self.everything else
                           [{"site": key_name(key), "positions": mask}
                            for key, mask in self.writes]),
                "meta": dict(self.meta)}


def build_arms(*, layer: int, quartet: Sequence[int], kv_group: int, num_kv_heads: int,
               tests: Sequence[str], directions: Sequence[str],
               head_draws: Sequence[Sequence[int]], n_position_draws: int) -> List[ArmSpec]:
    """Every arm the flags select, gates first (plan sections 1.1 and 2.2)."""
    def q(mask, heads=quartet):
        return tuple((("q", layer, h), mask) for h in heads)

    def kv(kind, mask, group=kv_group):
        return (((kind, layer, group), mask),)

    def out(mask):
        return tuple((("head", layer, h), mask) for h in quartet)

    arms = [ArmSpec("g1_empty", "gate", "gate", "gate", "D"),
            ArmSpec("g2_all_components", "gate", "gate", "gate", "D", everything=True)]

    def add(name, test, role, direction, writes, **meta):
        arms.append(ArmSpec(name, test, role, direction,
                            "D" if direction == RESTORE else "T", tuple(writes), meta=meta))

    if T1 in tests and RESTORE in directions:
        add("dq_all", T1, "rule", RESTORE, out(ALL))
        add("dq_readout", T1, "descriptive", RESTORE, out("readout"))
        add("dq_post_clause_no_readout", T1, "descriptive", RESTORE,
            out("post_clause_no_readout"))
    if T1 in tests and REVERSE in directions:
        add("tq_all", T1, "descriptive", REVERSE, out(ALL))

    if T2 in tests and RESTORE in directions:
        add("q_readout", T2, "rule", RESTORE, q("readout"))
        add("k_options", T2, "rule", RESTORE, kv("k", "options"))
        add("v_options", T2, "descriptive", RESTORE, kv("v", "options"))
        add("kv_options", T2, "descriptive", RESTORE, kv("k", "options") + kv("v", "options"))
        add("qk", T2, "descriptive", RESTORE, q("readout") + kv("k", "options"))
        add("k_post_clause", T2, "descriptive", RESTORE, kv("k", "post_clause"))
        add("k_clause", T2, "descriptive", RESTORE, kv("k", "clause"))
        add("q_post_clause", T2, "descriptive", RESTORE, q("post_clause"))
        add("out_readout", T2, "descriptive", RESTORE, out("readout"))
        add("kv_preclause_mentions", T2, "check", RESTORE,
            kv("k", "preclause_mentions") + kv("v", "preclause_mentions"))
        for draw, heads in enumerate(head_draws):
            add(f"ctrl_q_readout_d{draw}", T2, "control", RESTORE, q("readout", heads),
                draw=draw, heads=list(heads))
        for group in range(num_kv_heads):
            if group != kv_group:
                add(f"ctrl_k_options_g{group}", T2, "control", RESTORE,
                    kv("k", "options", group), kv_group=group)
        for draw in range(n_position_draws):
            add(f"ctrl_k_random_post_d{draw}", T2, "control", RESTORE,
                kv("k", f"random_post_d{draw}"), draw=draw)
    if T2 in tests and REVERSE in directions:
        add("rev_q_readout", T2, "descriptive", REVERSE, q("readout"))
        add("rev_k_options", T2, "descriptive", REVERSE, kv("k", "options"))
    return arms


def bank_for(model, arm: ArmSpec, pair: PairStreams) -> dict:
    from component_analysis import hooks

    source = pair.stream(arm.source)
    if arm.everything:
        return restore_bank(source, hooks.all_component_keys(model), None)
    bank = {}
    for key, mask in arm.writes:
        bank.update(restore_bank(source, [key], None if mask == ALL else pair.masks[mask]))
    return bank


# ==============================================================================
# THE ANALYSIS
# ==============================================================================

def _selected(value: str, both: Sequence[str]) -> Tuple[str, ...]:
    return tuple(both) if value == BOTH else (value,)


def _cli(ctx, name, default=None):
    return getattr(ctx.cli, name, default)


def _quartet(ctx) -> Tuple[int, Tuple[int, ...]]:
    return parse_quartet(_cli(ctx, "route_quartet", DEFAULT_QUARTET))


def _grid(ctx) -> Tuple[set, dict]:
    cell = {tuple(getattr(one, "key", one)) for one in (ctx.components or [])}
    path = _cli(ctx, "route_ct")
    if path:
        keys = load_ct(path, ctx.task_spec.name)
        meta = {"source": path, "matches_cell": (keys == cell) if cell else None}
    else:
        keys, meta = cell, {"source": "cell circuit", "matches_cell": None}
    meta.update(n=len(keys), keys=sorted(key_name(one) for one in keys))
    return keys, meta


def _counts(ctx, n_kv: int) -> dict:
    """How many arms the flags select, without a model."""
    layer, quartet = _quartet(ctx)
    draws = int(_cli(ctx, "route_control_draws", DEFAULT_CONTROL_DRAWS))
    arms = build_arms(layer=layer, quartet=quartet, kv_group=0, num_kv_heads=n_kv,
                      tests=_selected(_cli(ctx, "route_tests", BOTH), (T1, T2)),
                      directions=_selected(_cli(ctx, "route_direction", BOTH),
                                           (RESTORE, REVERSE)),
                      head_draws=[quartet] * draws, n_position_draws=draws)
    return {"arms": len(arms)}


def estimate(ctx) -> str:
    """One line for `--dry-run`: forwards per batch and the files it reads."""
    from component_analysis import path_patching as pp

    layer, quartet = _quartet(ctx)
    batches = ctx.causal_batches()
    twins = batches.report.get("n_with_neutral_twin")
    if not _may_have_twins(ctx):
        return ("not applicable: no instance of the causal sample has a Neutral-Clause Twin "
                f"({batches.report.get('neutral_twin_source', 'no twin split')}); "
                "a skipped file is written")
    grid_keys, grid = _grid(ctx)
    if _cli(ctx, "route_deciding_set"):
        load_deciding_set(_cli(ctx, "route_deciding_set"))
    shape = getattr(getattr(ctx, "intake", None), "geometry", None) or {}
    assumed = ""
    try:
        n_kv = shape["num_heads"] // pp.heads_per_group(ctx)
    except Exception:                                                 # noqa: BLE001
        n_kv, assumed = 8, " (KV groups not readable here; 8 assumed, as on Llama-3.1-8B)"
    n_arms = _counts(ctx, n_kv)["arms"]
    n_batches = len(batches)
    limit = int(_cli(ctx, "route_max_batches", 0) or 0)
    if limit:
        n_batches = min(n_batches, limit)
    forwards = n_batches * (2 + n_arms)
    per = pp.seconds_per_forward(batches.report.get("batch_size") or 1)
    return (f"quartet layer {layer} heads {list(quartet)}; {n_arms} arm(s) "
            f"(tests {_cli(ctx, 'route_tests', BOTH)}, direction "
            f"{_cli(ctx, 'route_direction', BOTH)}) + 2 whole captures per batch over "
            f"{n_batches} batch(es) = {forwards} forward(s){assumed}, about "
            f"{forwards * per / 60:.1f} "
            f"min at the A40 rate (capture-all forwards are heavier; time the smoke); "
            f"{twins if twins is not None else '?'} instance(s) with a twin; grid "
            f"{grid['source']} ({len(grid_keys)} Component(s)); T1 sweeps not implemented "
            f"(ticket 5)")


def _mask_json(pair: PairStreams, name: str, segments) -> dict:
    mask = pair.masks[name].cpu()
    return {"segments": list(segments),
            "tokens": [mask[row].nonzero().flatten().tolist() for row in range(mask.shape[0])]}


def _mean(values: Sequence[float]) -> Optional[float]:
    return float(sum(values) / len(values)) if values else None


def _payload(ctx, model, *, quartet_meta, grid, deciding, arms, head_draws, k_groups,
             draws) -> dict:
    from component_analysis import hooks

    cli = ctx.cli
    return {
        "schema": SCHEMA, "analysis": NAME, "task": ctx.task_spec.name,
        "circuit": getattr(ctx.circuit_spec, "label", None),
        "model": hooks.describe(model) if model is not None else None,
        "config": {"route_tests": _cli(ctx, "route_tests", BOTH),
                   "route_direction": _cli(ctx, "route_direction", BOTH),
                   "route_sweep": _cli(ctx, "route_sweep", BOTH),
                   "route_control_draws": draws,
                   "route_control_seed": _cli(ctx, "route_control_seed", DEFAULT_CONTROL_SEED),
                   "route_ct": _cli(ctx, "route_ct"),
                   "route_deciding_set": (":".join(cli.route_deciding_set)
                                          if _cli(ctx, "route_deciding_set") else None),
                   "route_pp_top": _cli(ctx, "route_pp_top", DEFAULT_PP_TOP),
                   "route_max_batches": _cli(ctx, "route_max_batches", 0),
                   "positions_per_draw": POSITIONS_PER_DRAW},
        "quartet": quartet_meta, "grid": grid, "deciding_set": deciding,
        "controls": {"q_heads": [list(one) for one in head_draws], "k_groups": k_groups,
                     "positions_per_draw": POSITIONS_PER_DRAW},
        "arms_selected": [arm.name for arm in arms],
        "t1": {"sweeps": {"status": "not implemented: ticket 5",
                          "estimators": _cli(ctx, "route_sweep", BOTH)}},
        "not_implemented": list(NOT_IMPLEMENTED),
    }


def run(ctx) -> dict:
    """Every selected arm over the causal sample's twin rows; writes `route_closure.json`.

    Returns no head-table columns: the rule numbers are ratios over the whole sample, read
    by the CPU readings script (ticket 6), not per-Component values.
    """
    import torch

    from component_analysis import hooks

    model = ctx.model
    if not _may_have_twins(ctx):
        # A v1 cell (or one whose loader paired no twin): nothing to measure, and the
        # quartet need not exist on this model. Every invocation without --analyses
        # reaches this module, so this is the common case, not an error.
        batches = ctx.causal_batches()
        return _skip(ctx, {"schema": SCHEMA, "analysis": NAME, "task": ctx.task_spec.name,
                           "circuit": getattr(ctx.circuit_spec, "label", None)},
                     list(getattr(batches, "ids", None) or
                          [one for batch in batches for one in batch.ids]))
    layer, quartet = _quartet(ctx)
    groups = sorted({hooks.kv_group_of(model, h) for h in quartet})
    if len(groups) != 1 or tuple(hooks.heads_of_kv_group(model, groups[0])) != tuple(quartet):
        raise ValueError(f"the quartet {list(quartet)} of layer {layer} must be exactly one KV "
                         f"group, so that one k or v write reaches it and nothing else; it "
                         f"spans group(s) {groups}")
    kv_group = groups[0]
    shape = hooks.geometry(model)
    tests = _selected(_cli(ctx, "route_tests", BOTH), (T1, T2))
    directions = _selected(_cli(ctx, "route_direction", BOTH), (RESTORE, REVERSE))
    draws = int(_cli(ctx, "route_control_draws", DEFAULT_CONTROL_DRAWS))
    seed = int(_cli(ctx, "route_control_seed", DEFAULT_CONTROL_SEED))
    grid_keys, grid = _grid(ctx)
    deciding = None
    if _cli(ctx, "route_deciding_set"):
        path, name = ctx.cli.route_deciding_set
        deciding = {"file": path, "name": name,
                    "keys": [key_name(one) for one in load_deciding_set((path, name))]}

    controls = T2 in tests and RESTORE in directions
    head_draws = (draw_control_heads(num_heads=shape["num_heads"], layer=layer,
                                     quartet=quartet, excluded=grid_keys, n_draws=draws,
                                     size=len(quartet), seed=seed) if controls else [])
    arms = build_arms(layer=layer, quartet=quartet, kv_group=kv_group,
                      num_kv_heads=shape["num_kv_heads"], tests=tests, directions=directions,
                      head_draws=head_draws, n_position_draws=draws if controls else 0)
    k_groups = [arm.meta["kv_group"] for arm in arms if "kv_group" in arm.meta]
    payload = _payload(ctx, model, quartet_meta={"layer": layer, "heads": list(quartet),
                                                 "kv_group": kv_group},
                       grid=grid, deciding=deciding, arms=arms, head_draws=head_draws,
                       k_groups=k_groups, draws=draws)

    segmentations = _by_id(getattr(ctx, "segmentations", None))
    limit = int(_cli(ctx, "route_max_batches", 0) or 0)
    ids, pressure_ids, without = [], [], []
    m_d, m_t, gap = [], [], []
    margins = {arm.name: [] for arm in arms}
    g1_identical, g1_diff, g2_diff = True, 0.0, 0.0
    first = None
    for number, batch in enumerate(ctx.causal_batches()):
        if limit and number >= limit:
            break
        pair = capture_pair(model, batch, segmentations)
        if pair is None:
            without.extend(batch.ids)
            continue
        without.extend(one for one in batch.ids if one not in pair.ids)
        if controls and draws:
            drawn = draw_control_positions(pair.ids, {k: v.cpu() for k, v in pair.masks.items()},
                                           n_draws=draws, size=POSITIONS_PER_DRAW, seed=seed)
            for draw, mask in enumerate(drawn["masks"]):
                pair.masks[f"random_post_d{draw}"] = mask.to(pair.readout.device)
        for arm in arms:
            result = run_arm(model, pair, bank_for(model, arm, pair), base=arm.base)
            margins[arm.name].extend(result.margins.float().cpu().tolist())
            if arm.name == "g1_empty":
                g1_identical &= bool(torch.equal(result.margins, pair.d.margin))
                g1_diff = max(g1_diff, float((result.margins - pair.d.margin).abs().max()))
            if arm.name == "g2_all_components":
                g2_diff = max(g2_diff, float((result.margins - pair.t.margin).abs().max()))
        ids.extend(pair.ids)
        pressure_ids.extend(pair.pressure_ids)
        m_d.extend(pair.d.margin.cpu().tolist())
        m_t.extend(pair.t.margin.cpu().tolist())
        gap.extend(pair.gap.cpu().tolist())
        if first is None:
            first = {"ids": list(pair.ids), "readout": pair.readout.cpu().tolist(),
                     "masks": {name: _mask_json(pair, name, segments)
                               for name, segments in MASK_SEGMENTS.items()}}
            for draw in range(draws if controls else 0):
                first["masks"][f"random_post_d{draw}"] = _mask_json(
                    pair, f"random_post_d{draw}",
                    [f"random draw {draw} of post_clause_no_readout minus options"])
        del pair

    if not ids:
        return _skip(ctx, payload, without)
    payload["instances"] = {"ids": ids, "pressure_ids": pressure_ids, "without_twin": without}

    mean_d, mean_t = _mean(m_d), _mean(m_t)
    payload["baseline"] = {"m_D": m_d, "m_T": m_t, "G": gap, "mean_m_D": mean_d,
                           "mean_m_T": mean_t, "mean_G": _mean(gap), "P": mean_d - mean_t}
    payload["gates"] = {"g1_bit_identical": g1_identical, "g1_max_abs_diff": g1_diff,
                        "g2_max_abs_diff": g2_diff}
    payload["arms"] = {arm.name: {**arm.as_json(), "margins": margins[arm.name],
                                  "mean": _mean(margins[arm.name])} for arm in arms}
    payload["positions"] = {"first_batch": first}
    ctx.write_json(SUBDIR, JSON_FILE, payload)
    _declare(ctx, ids)
    return {}


def _declare(ctx, ids) -> None:
    from component_analysis.head_table import CAUSAL_SAMPLE_NEUTRAL_TWIN

    ctx.declare_coverage([], instance_ids=ids, instance_set=CAUSAL_SAMPLE_NEUTRAL_TWIN)


def _may_have_twins(ctx) -> bool:
    """False when the loader says no instance has a twin, or the task is not v2 and the
    loader did not pair twins at all."""
    from component_analysis.dataloaders import V2_TASKS

    report = getattr(ctx.causal_batches(), "report", None) or {}
    twins = report.get("n_with_neutral_twin")
    if twins is not None:
        return twins > 0
    return ctx.task_spec.name in V2_TASKS


def _skip(ctx, payload: dict, without: List[str]) -> dict:
    """The skipped file: same schema, no arms, every instance listed as without a twin."""
    payload.update(skipped="no instance of the causal sample has a Neutral-Clause Twin",
                   instances={"ids": [], "pressure_ids": [], "without_twin": list(without)},
                   arms={}, baseline=None, gates=None, positions=None)
    ctx.write_json(SUBDIR, JSON_FILE, payload)
    _declare(ctx, [])
    return {}
