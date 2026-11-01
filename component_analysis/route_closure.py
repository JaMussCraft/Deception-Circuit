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
`tq_all` (T prompt, quartet outputs from D).

## T1: the outside senders' direct effects (ticket 5, plan sections 1.2 to 1.5)

"Outside" is every head and MLP block not in the grid C_t and not in the quartet; the
embedding is never a sender here. For an arm X (base D) and outside sender s:

    drop_s,i(X) = m_i(D) - m_i(D with s's Readout write taken from X, all else frozen at D)
    e_s(X)      = mean_i drop_s,i(X) / mean_i G_i          (ratio of means, normalized by G)
    O_X         = sum of e_s(X) over the outside senders the arm does not itself write

**Normalized by G, never by the arm's gap** (plan 1.2's trap): `sweep_streams` builds the
`path_patching.Streams` with `gap = G`, and `summarize_sweep` divides by mean G. O = O_T and
O_q = O_{dq_all}; M_q = O_q / O.

    estimator (a)  `forward_sweep`: one forward per sender per batch
                   (`path_patching.sweep_readout`), run on T and dq_all; the rule of record
    estimator (b)  `offline_direct_effects`: r' = r_D - c_s(D) + c_s(X), c from
                   `dla.component_contributions`, r_D D's captured final residual, read through
                   the real final norm in fp32; run on T, the dq arms and every control
    joint swap     every summed sender from X at once (the final norm makes the sum
                   non-additive): `forward_joint` and `offline_direct_effects(joint=...)`

T1 controls and reference (base D, estimator (b) only; `build_t1_arms`):

    c1_d<n>    C1: the T2 control draw n of layer-L heads (outside the quartet and C_t), from T
               at every position
    c2_d<n>    C2: 4 heads of layers `--route-c2-layers` (8-16) outside C_t, the deciding set
               and the quartet, from T at every position (`draw_c2_heads`, seeded)
    c3_push    C3: D with delta_i * u_i added to mlp.L's output at the Readout; u_i the unit
               g * (W_U[target] - W_U[distractor]); delta_i solved in closed form so the
               fixed-scale layer-L lens margin (scale: D's layer-L residual) moves exactly as
               under dq_all (`solve_push`, `direction_push_bank`)
    s_k        S_k: the deciding set (`--route-deciding-set`) from T post-clause

An arm's own written sites (the quartet, a draw's heads, the deciding set, and mlp.L for the
C3 push) are left out of its O (`intervened`), so O_X measures what the arm does to the other
outside writers, as the quartet (in C_t) is left out of O_q.

Position-resolved path patching (descriptive, `--route-path-patching on`, a second pass over the
batches): plan 1.5 writes the quartet with its T values only at `readout`,
`post_clause_no_readout` or `post_clause`, into the receivers of the `--route-pp-top` outside
writers by |e_s(T)| (`writer_receivers`: mlp_in at the Readout; a head's q at the Readout and its
KV group's k and v post-clause); plan 2.3 writes each `--route-pp-feeders` key and each layer below
L (as one group) from T into the quartet's q at the Readout and k.L.g at the options.

Gates (always run): `g1_empty` (empty bank on D; must equal m(D) bit for bit) and
`g2_all_components` (every sender from T at every position on D; must reproduce m(T)).

## Output: `<cell>/route_closure/route_closure.json`

One file per task cell. Every per-instance list is in `instances.ids` order.

    schema              "route_closure/1"
    analysis, task, circuit
    model               `hooks.describe(model)`
    config              {route_tests, route_direction, route_sweep, route_control_draws,
                         route_control_seed, route_ct, route_deciding_set, route_pp_top,
                         route_max_batches, positions_per_draw,
                         route_path_patching, route_pp_feeders, route_c2_layers}  (ticket 5)
    quartet             {layer, heads, kv_group}
    grid                {source: "<ct.json path>" or "cell circuit", n, keys: ["head.L.H", ...],
                         matches_cell: bool or null}
    deciding_set        {file, name, keys} or null (C2 reads it; ticket 5)
    instances           {ids, pressure_ids, without_twin}
    baseline            {m_D, m_T, G (per instance), mean_m_D, mean_m_T, mean_G,
                         P = mean_m_D - mean_m_T}
    gates               {g1_bit_identical: bool, g1_max_abs_diff, g2_max_abs_diff,
                         g3 (ticket 5, when T1 runs): {passed: bool or null (needs both
                             estimators), max_sender_diff, worst_sender, max_sum_diff,
                             max_joint_diff, per_sender_tolerance 0.01, sum_tolerance 0.02,
                             arms ["T", "dq_all"]}}
    arms_selected       [arm name, ...] in run order (gates first; T1 controls last)
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
    t1                  {sweeps, summary, path_patching}; when T1 is not selected,
                        sweeps.status and path_patching.status start "not selected"
    not_implemented     [] (kept; the ticket-5 parts are implemented)

`arms` also holds the T1 control arms (`c1_d<n>`, `c2_d<n>`, `c3_push`, `s_k`, test "t1", role
"control" or "reference") with their margins, when the offline estimator runs.

`t1.sweeps` (ticket 5):

    status "computed", estimators, normalized_by, drop (the drop's definition)
    outside             {n, keys: ["head.L.H", ...], excluded: {embedding, grid, quartet}}
    reported_rows       ["mlp.31.0", "mlp.30.0", "head.31.0"] (kept when the model has them)
    in_sum              how each arm's O is summed (outside minus its intervened sites)
    forward             {"T": Sweep, "dq_all": Sweep}, estimator (a); {} if not run
    offline             {"T", "dq_all", "dq_readout", "dq_post_clause_no_readout", "c1_d<n>",
                         "c2_d<n>", "c3_push", "s_k": Sweep}, estimator (b); {} if not run
    controls_status     whether C1 to S_k were computed (they need the offline estimator)
    c1_draws [[h, ...]], c2_draws [["head.L.H", ...]], c2_layers [lo, hi], c2_status
    c3                  {delta, target_change, achieved_change, lens_D (per instance), site,
                         positions "readout", scale, direction, max_abs_miss}

    Sweep = {n_instances, mean_G, O, O_pos, O_neg (split by the sign of e_s), O_joint,
             r_total = (mean_m_D - mean m_X) / mean_G, n_in_sum, intervened [names],
             rows {name: e_s}, senders {name: {mean_drop, e, se, in_sum}},
             per_instance {outside_sum, pos_sum, neg_sum, joint, margins (m_X),
                           rows {name: [drop]}}}           (per-instance values in logits)

    mean_i(per_instance.outside_sum) / mean_G = O, and likewise pos_sum, neg_sum and joint.

`t1.summary` (point numbers; the readings script recomputes them with medians and the bootstrap):

    {rule_estimator "forward" (or "offline" when only it ran), O, O_q, M_q, r_q, O_pos, O_neg,
     O_q_pos, O_q_neg, O_joint, O_q_joint, rows {name: {T, dq_all}}, selection_sample_O (0.803
     far, 0.774 ser; gate G4), M_q_offline, M_dq_readout, M_dq_post_clause_no_readout,
     M_C1 {arm: M}, M_C2 {arm: M}, M_C3, M_S}           M_X = O_X / O on the offline estimator

`t1.path_patching` (descriptive; status "computed" or "off (--route-path-patching off)"):

    counterfactual, normalized_by "mean G", same_instances (the second pass saw the first's ids),
    freeze
    plan_1_5   {ranked_by, top, sender [quartet keys], sender_masks {mask: segments},
                writers [{sender, e_T, e_Dq, reachable, receivers [{site, positions, reached}]}],
                effects {mask: {writers {name: Effect}, joint Effect, sum_writers}},
                O_q, O_q_top_writers}
    plan_2_3   {receivers {q_readout [...], k_options}, receiver_positions, senders
                [{name, keys}], skipped_senders [names], skipped_reasons {name: why},
                effects {sender: {q_readout: Effect, k_options: Effect}}}
    Effect = {e (mean drop / mean G), se, per_instance [drop, logits]}

A skipped cell (no instance has a twin, e.g. a v1 task or an H or F cell) writes the same file
with `skipped`, empty `arms` and `instances.without_twin` filled.

The readings (`scripts/route_closure_readings.py`, ticket 6) compute from this file:
r_a = (mean_m_D - arms[a].mean) / P for a restore arm (base D), and
r_a = (arms[a].mean - mean_m_T) / P for a reverse arm (base T), so both read as the share of the
pressure effect P the arm moves. They also recompute M_q and the controls' M from the
per-instance sums, with medians and the clustered bootstrap, and apply the verdict rules; this
module writes `t1.summary`'s point numbers only and applies no verdict.

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

#: Parts not computed by this module; empty since ticket 5. Kept so the field stays.
NOT_IMPLEMENTED: Tuple[str, ...] = ()

#: The rows plan section 1.2 names on Llama-3.1-8B; reported when the model has them.
REPORTED_ROWS = (("mlp", 31, 0), ("mlp", 30, 0), ("head", 31, 0))
#: Gate G3 (plan section 5): estimators (a) and (b) agree per sender and on the sum.
G3_PER_SENDER = 0.01
G3_SUM = 0.02
#: C2's layer range (plan 1.3), inclusive; `--route-c2-layers` overrides it.
DEFAULT_C2_LAYERS = (8, 16)
#: Plan 2.3's named senders: the phase-3 query feeders of the quartet (head.14.4,
#: head.15.8, mlp.13 to mlp.15). The strongest K feeder in `phase3/b_selector.csv` is
#: mlp.13.0 on far and mlp.14.0 on ser, both already in the list.
DEFAULT_PP_FEEDERS = "head.14.4,head.15.8,mlp.13.0,mlp.14.0,mlp.15.0"
#: Where plan 1.5 writes the quartet (one joint sender, T values): only at the Readout,
#: only post-clause without the Readout, and both (the union; pre-clause quartet values
#: are equal in D and T, so this is the quartet at every position, as `dq_all`).
PP_SENDER_MASKS = ("readout", "post_clause_no_readout", "post_clause")
#: The arms estimator (a), the forward sweep, is run on (plan 1.2: O and O_q).
FORWARD_ARMS = ("T", "dq_all")
#: The ticket-4 T1 arms estimator (b) also reads (besides "T" and the controls).
OFFLINE_DQ_ARMS = ("dq_all", "dq_readout", "dq_post_clause_no_readout")
#: Senders per chunk when the offline estimator reads residuals through the norm.
OFFLINE_CHUNK = 64
#: Held-out O is printed beside these (gate G4): E14's selection-sample signed sums.
SELECTION_SAMPLE_O = {"far": 0.803, "ser": 0.774}


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


def parse_keys(text: str) -> List[tuple]:
    """`"head.14.4,mlp.13.0"` to `[("head", 14, 4), ("mlp", 13, 0)]`."""
    try:
        return [_parse_key(one.strip()) for one in text.split(",") if one.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"expected comma-separated KIND.LAYER.INDEX keys, got {text!r}") from None


def _keys_arg(text: str) -> str:
    parse_keys(text)
    return text


def _layer_range_arg(text: str) -> Tuple[int, int]:
    try:
        low, high = (int(one) for one in text.split("-"))
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected LOW-HIGH layers, got {text!r}") from None
    if low < 0 or high < low:
        raise argparse.ArgumentTypeError(f"layer range {text!r} is empty or negative")
    return low, high


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
                       help="T1's estimator of the outside senders' direct effects: (a) the "
                            "forward sweep (O and O_q, the rule of record), (b) the offline "
                            "fp32 decomposition (every arm, the controls included), or both "
                            "(gate G3 compares them). The controls need offline.")
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
                            "greedy_k20), excluded from C2's draws and restored post-clause "
                            "as the S_k reference.")
    group.add_argument("--route-pp-top", type=int, default=DEFAULT_PP_TOP,
                       help="How many outside writers (by |e_s(T)|) T1's position-resolved "
                            f"path patching takes as receivers. Default {DEFAULT_PP_TOP}.")
    group.add_argument("--route-path-patching", default="on", choices=["on", "off"],
                       help="Run the position-resolved path patching of plan sections 1.5 "
                            "and 2.3 (descriptive; a second pass over the batches). "
                            "Default on.")
    group.add_argument("--route-pp-feeders", type=_keys_arg, default=DEFAULT_PP_FEEDERS,
                       metavar="KEYS",
                       help="Plan 2.3's named senders into the quartet's q and k, besides "
                            "the per-layer groups below the quartet. Keys the model lacks "
                            f"are skipped and listed. Default {DEFAULT_PP_FEEDERS}.")
    group.add_argument("--route-c2-layers", type=_layer_range_arg,
                       default=DEFAULT_C2_LAYERS, metavar="LOW-HIGH",
                       help="C2's layer range, inclusive (plan 1.3: 8-16). Layers the "
                            "model lacks are dropped; none left skips C2.")
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


def draw_c2_heads(*, num_heads: int, layers: Tuple[int, int], excluded, n_draws: int,
                  size: int, seed: int, num_layers: Optional[int] = None) -> List[List[tuple]]:
    """C2 (plan 1.3): `n_draws` sorted sets of `size` heads from layers `layers[0]` to
    `layers[1]` inclusive, none in `excluded` (the grid, the deciding set, the quartet).

    Layers at or above `num_layers` are dropped; when none is left the draw is empty (a
    model too shallow for the range, such as the tiny test model), which the JSON
    records rather than raising. A range the model has but whose pool is too small is
    refused by its range.
    """
    low, high = layers
    present = [layer for layer in range(low, high + 1)
               if num_layers is None or layer < num_layers]
    if not present:
        return []
    pool = [("head", layer, h) for layer in present for h in range(num_heads)
            if ("head", layer, h) not in excluded]
    if len(pool) < size:
        raise ValueError(f"layers {low}-{high} have only {len(pool)} head(s) outside the "
                         f"grid, the deciding set and the quartet, fewer than a C2 draw of "
                         f"{size}")
    rng = random.Random(f"{seed}:c2_heads:{low}-{high}")
    return [sorted(rng.sample(pool, size)) for _ in range(n_draws)]


def outside_senders(*, num_layers: int, num_heads: int, excluded) -> List[tuple]:
    """Every head and MLP block not in `excluded`, in run order; never the embedding.

    `excluded` is the grid C_t and the quartet. The quartet is in C_t on Llama-3.1-8B
    (`phase3/ct.json`), so excluding it again changes nothing there; it keeps the
    quartet's own direct write out of O when a test grid omits it.
    """
    keys = []
    for layer in range(num_layers):
        keys.extend(("head", layer, h) for h in range(num_heads))
        keys.append(("mlp", layer, 0))
    excluded = {tuple(one) for one in excluded}
    return [key for key in keys if key not in excluded]


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
    #: `[batch, num_layers + 1, hidden]` at the Readout (`Capture.residual`): row 0 the
    #: embedding, row l + 1 the residual after layer l. C3's lens reads row L + 1.
    residual: Optional["torch.Tensor"] = None


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
    #: `[batch, num_layers + 1, hidden]` at the Readout, as `Stream.residual`.
    residual: Optional["torch.Tensor"] = None


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
                               margin=_margin(model, capture, target, distractor),
                               residual=capture.residual)

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
                     outputs={key: capture.outputs[key] for key in keys},
                     residual=capture.residual)


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

    @property
    def intervened(self) -> Tuple[tuple, ...]:
        """The sites this arm writes, once each, in order."""
        return tuple(dict.fromkeys(key for key, _mask in self.writes))

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


def build_t1_arms(*, layer: int, c1_draws: Sequence[Sequence[int]],
                  c2_draws: Sequence[Sequence[tuple]], deciding: Sequence[tuple]
                  ) -> List[ArmSpec]:
    """T1's matched controls and reference (plan 1.3), all base D with values from T.

    C1 and C2 restore their drawn heads at every position, as `dq_all` restores the
    quartet. C3 is a push, not a restore: its bank is `direction_push_bank`, and its
    `writes` only name the site and the mask. S_k restores the deciding set post-clause.
    """
    arms = []
    for draw, heads in enumerate(c1_draws):
        arms.append(ArmSpec(f"c1_d{draw}", T1, "control", RESTORE, "D",
                            tuple((("head", layer, h), ALL) for h in heads),
                            meta={"control": "C1", "draw": draw, "heads": list(heads)}))
    for draw, keys in enumerate(c2_draws):
        arms.append(ArmSpec(f"c2_d{draw}", T1, "control", RESTORE, "D",
                            tuple((tuple(key), ALL) for key in keys),
                            meta={"control": "C2", "draw": draw,
                                  "heads": [key_name(key) for key in keys]}))
    arms.append(ArmSpec("c3_push", T1, "control", RESTORE, "D",
                        ((("mlp", layer, 0), "readout"),),
                        meta={"control": "C3", "push": True}))
    if deciding:
        arms.append(ArmSpec("s_k", T1, "reference", RESTORE, "D",
                            tuple((tuple(key), "post_clause") for key in deciding),
                            meta={"reference": "S_k", "n": len(deciding)}))
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
# T1: THE TWO ESTIMATORS OF THE OUTSIDE SENDERS' DIRECT EFFECTS (ticket 5)
# ==============================================================================

def hooks_geometry(model) -> dict:
    from component_analysis import hooks

    return hooks.geometry(model)


def sweep_streams(model, pair: PairStreams, x_outputs) -> "pp.Streams":
    """`path_patching.Streams` with D as the clean stream and X's outputs as corrupt.

    **The gap is G = m(D) - m(T)**, carried from the pair, never m(D) - m(X): plan 1.2's
    trap, since `normalized_effect` divides by `streams.gap` and with X = D_q the arm's
    own gap is not the twin gap. `clean_outputs` holds the senders only
    (`hooks.all_component_keys`): `receiver_inputs` writes back every key in it, so a
    receiver key there (the norm input above all) would freeze the very site read.
    """
    from component_analysis import hooks
    from component_analysis import path_patching as pp

    frozen = hooks.all_component_keys(model)
    return pp.Streams(
        input_ids=pair.d.input_ids, attention_mask=pair.d.attention_mask,
        positions=pair.readout, target=pair.target, distractor=pair.distractor,
        clean_outputs={key: pair.d.outputs[key] for key in frozen},
        corrupt_outputs={key: x_outputs[key] for key in frozen if key in x_outputs},
        clean_readout=None, corrupt_readout=None,
        clean_metric=pair.d.margin, corrupt_metric=pair.d.margin - pair.gap, gap=pair.gap,
        ids=tuple(pair.ids), counterfactual=pp.NEUTRAL_TWIN, rows=tuple(pair.rows))


def forward_sweep(model, pair: PairStreams, x_outputs, senders) -> Dict[tuple, "torch.Tensor"]:
    """Estimator (a): `{sender: [batch] drop}`, the drop m(D) - m(patched) in logits.

    One forward per sender (`path_patching.sweep_readout`): s carries its X value at
    every position and every other sender is frozen at D. The drop is not normalized
    here; `summarize_sweep` divides the mean drop by the mean G.
    """
    from component_analysis import hooks
    from component_analysis import path_patching as pp

    streams = sweep_streams(model, pair, x_outputs)
    out = {}
    for sender in senders:
        logits = pp.sweep_readout(model, streams, tuple(sender))
        out[tuple(sender)] = pair.d.margin - hooks.target_minus_distractor(
            logits, pair.target, pair.distractor)
    return out


def forward_joint(model, pair: PairStreams, x_outputs, senders) -> "torch.Tensor":
    """`[batch]` drop with every sender in `senders` from X at once, the rest frozen at D.

    The final RMSNorm makes the per-sender drops non-additive, so the plan reports this
    joint swap beside their sum.
    """
    from component_analysis import hooks
    from component_analysis import path_patching as pp

    streams = sweep_streams(model, pair, x_outputs)
    capture = pp.receiver_inputs(model, streams, senders=[tuple(one) for one in senders],
                                 receivers=[hooks.READOUT_KEY])
    return pair.d.margin - _margin(model, capture, pair.target, pair.distractor)


class _ReadoutView:
    """What `dla.component_contributions` reads off a capture: outputs and the Readout."""

    def __init__(self, outputs, readout):
        self.outputs = outputs
        self.readout = readout


def residual_margins(model, residuals, target, distractor, *, scale_from=None
                     ) -> "torch.Tensor":
    """`[batch, k]` fp32 m = logit(Target) - logit(Distractor) of `[batch, k, hidden]`
    residuals, through the real final norm.

    Each residual is normalized at its own scale (the final norm the model would apply
    to it), or at `scale_from`'s (`[batch, hidden]`, a fixed scale: the lens of C3).
    Only the two unembedding rows are read, never the whole vocabulary, so a sweep over
    every sender of the 8B model stays `[batch, k, hidden]`. The arithmetic is
    `hooks.readout_logits` followed by `hooks.target_minus_distractor`.
    """
    import torch

    from component_analysis import hooks

    hf = hooks._hf(model)
    norm = hf.model.norm
    epsilon = getattr(norm, "variance_epsilon", None)
    if epsilon is None:
        epsilon = getattr(norm, "eps", 1e-5)
    with torch.no_grad():
        weight = hf.lm_head.weight.detach()
        target = target.to(weight.device)
        distractor = distractor.to(weight.device)
        direction = (weight[target].float() - weight[distractor].float())     # [batch, hidden]
        gain = norm.weight.detach().float()
        out = []
        for start in range(0, residuals.shape[1], OFFLINE_CHUNK):
            hidden = residuals[:, start:start + OFFLINE_CHUNK].detach().float()
            basis = hidden if scale_from is None else \
                scale_from.detach().float().unsqueeze(1)
            scaled = hidden * torch.rsqrt(basis.pow(2).mean(-1, keepdim=True) + epsilon)
            out.append(((scaled * gain) * direction.unsqueeze(1)).sum(-1))
        return torch.cat(out, dim=1)


@dataclass
class OfflineResult:
    keys: List[tuple]
    drops: "torch.Tensor"                       # [batch, len(keys)] fp32, logits
    joint: Optional["torch.Tensor"] = None      # [batch] fp32, logits


def offline_direct_effects(model, pair: PairStreams, x_outputs, senders, *, joint=None,
                           d_contributions=None) -> OfflineResult:
    """Estimator (b): the drop when s's Readout contribution in D's final residual is
    replaced by its X contribution, read through the real final norm, in fp32.

    The base is D's **captured** final residual r_D, so r' = r_D - c_s(D) + c_s(X) with
    `c` from `dla.component_contributions`; m(r_D) - m(r') is the drop. `joint`, a
    subset of `senders`, is swapped all at once. `d_contributions` reuses c(D) across
    the arms of one batch.
    """
    import torch

    from component_analysis import dla, hooks

    senders = [tuple(one) for one in senders]
    rows = torch.arange(pair.readout.shape[0], device=pair.readout.device)
    r_d = pair.d.outputs[hooks.READOUT_KEY][rows, pair.readout, :].float()
    c_d = d_contributions if d_contributions is not None else \
        dla.component_contributions(model, _ReadoutView(pair.d.outputs, pair.readout),
                                    senders)
    c_x = dla.component_contributions(model, _ReadoutView(x_outputs, pair.readout), senders)
    delta = c_x - c_d                                                    # [batch, k, hidden]
    base = residual_margins(model, r_d.unsqueeze(1), pair.target, pair.distractor)[:, 0]
    drops = torch.cat([base.unsqueeze(1) - residual_margins(
        model, r_d.unsqueeze(1) + delta[:, start:start + OFFLINE_CHUNK],
        pair.target, pair.distractor)
        for start in range(0, len(senders), OFFLINE_CHUNK)], dim=1)
    joint_drop = None
    if joint is not None:
        index = [senders.index(tuple(one)) for one in joint]
        swapped = r_d + delta[:, index].sum(1) if index else r_d
        joint_drop = base - residual_margins(model, swapped.unsqueeze(1), pair.target,
                                             pair.distractor)[:, 0]
    return OfflineResult(keys=senders, drops=drops, joint=joint_drop)


def summarize_sweep(drops, keys, *, gap, include, joint=None, margins=None, m_d=None,
                    rows=()) -> dict:
    """One arm's sweep over the sample: plan 1.2's numbers, ratios of means.

    `drops` is `[N, K]` in logits (per instance, per sender), `gap` `[N]` the twin gap
    G. e_s = mean_i drop_s,i / mean_i G_i; O = the sum of e_s over the senders `include`
    marks. O_pos and O_neg split O by the sign of e_s; the per-instance sums use the
    same sign sets, so mean_i(pos_sum_i) / mean G = O_pos. `r_total` = (mean m_D -
    mean m_X) / mean G is the arm's total recovery.
    """
    import math

    import torch

    drops = torch.as_tensor(drops).double().cpu()
    gap = torch.as_tensor(gap).double().cpu()
    n = drops.shape[0]
    mean_g = gap.mean()
    mean_drop = drops.mean(0)
    e = mean_drop / mean_g
    se = (drops.std(0, unbiased=True) / math.sqrt(n) / mean_g) if n > 1 else None
    inc = torch.tensor([bool(one) for one in include], dtype=torch.bool)
    pos, neg = inc & (e > 0), inc & (e < 0)
    outside_sum = drops[:, inc].sum(1)
    pos_sum, neg_sum = drops[:, pos].sum(1), drops[:, neg].sum(1)
    names = [key_name(one) for one in keys]
    senders = {name: {"mean_drop": float(mean_drop[k]), "e": float(e[k]),
                      "se": float(se[k]) if se is not None else None,
                      "in_sum": bool(inc[k])}
               for k, name in enumerate(names)}
    row_names = [key_name(one) for one in rows if key_name(one) in senders]
    out = {
        "n_instances": n, "mean_G": float(mean_g),
        "O": float(outside_sum.mean() / mean_g), "O_pos": float(pos_sum.mean() / mean_g),
        "O_neg": float(neg_sum.mean() / mean_g),
        "O_joint": float(torch.as_tensor(joint).double().mean() / mean_g)
        if joint is not None else None,
        "r_total": (float((torch.as_tensor(m_d).double().mean()
                           - torch.as_tensor(margins).double().mean()) / mean_g)
                    if margins is not None and m_d is not None else None),
        "n_in_sum": int(inc.sum()),
        "rows": {name: senders[name]["e"] for name in row_names},
        "senders": senders,
        "per_instance": {
            "outside_sum": outside_sum.tolist(), "pos_sum": pos_sum.tolist(),
            "neg_sum": neg_sum.tolist(),
            "joint": torch.as_tensor(joint).double().tolist() if joint is not None else None,
            "margins": torch.as_tensor(margins).double().tolist()
            if margins is not None else None,
            "rows": {name: drops[:, names.index(name)].tolist() for name in row_names}},
    }
    return out


# ==============================================================================
# T1: C3, THE DIRECTION-MATCHED PUSH
# ==============================================================================

def lens_margin(model, residual, scale_from, target, distractor) -> "torch.Tensor":
    """`[batch]` fixed-scale lens margin of a `[batch, hidden]` residual, the scale
    taken from `scale_from` (C3 fixes it at D's layer-L residual, so the lens is linear)."""
    return residual_margins(model, residual.unsqueeze(1), target, distractor,
                            scale_from=scale_from)[:, 0]


@dataclass
class Push:
    delta: "torch.Tensor"                       # [batch] fp32
    direction: "torch.Tensor"                   # [batch, hidden] fp32, unit
    target_change: "torch.Tensor"               # [batch] fp32, the lens change under D_q
    before: "torch.Tensor"                      # [batch] fp32, the lens of D


def solve_push(model, pair: PairStreams, arm_residual, *, layer: int) -> Push:
    """C3's per-instance push (plan 1.3), in closed form.

    u_i is the unit fp32 vector g * (W_U[target_i] - W_U[distractor_i]), g the final
    norm's weight: the steepest ascent of the lens margin at a fixed scale. The scale
    s_i is D's own layer-L residual's at the Readout. At that scale the lens is linear,
    so adding delta_i * u_i moves it by delta_i * s_i * |g * (W_U[t] - W_U[d])|, and
    delta_i = (L(r_Dq) - L(r_D)) / (s_i * |g * (W_U[t] - W_U[d])|) moves it exactly as
    the quartet restoration did. `arm_residual` is the D_q arm's `residual`.
    """
    import torch

    from component_analysis import hooks

    hf = hooks._hf(model)
    norm = hf.model.norm
    epsilon = getattr(norm, "variance_epsilon", None)
    if epsilon is None:
        epsilon = getattr(norm, "eps", 1e-5)
    r_d = pair.d.residual[:, layer + 1].float()
    r_q = arm_residual[:, layer + 1].float().to(r_d.device)
    before = lens_margin(model, r_d, r_d, pair.target, pair.distractor)
    change = lens_margin(model, r_q, r_d, pair.target, pair.distractor) - before
    with torch.no_grad():
        weight = hf.lm_head.weight.detach()
        vector = norm.weight.detach().float() * (
            weight[pair.target.to(weight.device)].float()
            - weight[pair.distractor.to(weight.device)].float())
        length = vector.norm(dim=-1)
        scale = torch.rsqrt(r_d.pow(2).mean(-1) + epsilon)
        delta = change / (scale * length.to(r_d.device))
    return Push(delta=delta, direction=(vector / length.unsqueeze(-1)).to(r_d.device),
                target_change=change, before=before)


def direction_push_bank(pair: PairStreams, push: Push, *, layer: int) -> dict:
    """`{mlp.L: Replacement}`: D's `mlp.L` output with delta_i * u_i added at the Readout
    and nowhere else. Upstream of `mlp.L` the arm is D, so D's capture is the live value."""
    import torch

    from component_analysis import hooks

    key = ("mlp", layer, 0)
    base = pair.d.outputs[key]
    rows = torch.arange(base.shape[0], device=base.device)
    value = base.clone()
    pushed = base[rows, pair.readout.to(base.device)].float() + \
        push.delta.to(base.device).unsqueeze(-1) * push.direction.to(base.device)
    value[rows, pair.readout.to(base.device)] = pushed.to(base.dtype)
    return {key: hooks.Replacement(value, pair.masks["readout"])}


# ==============================================================================
# T1 AND T2: POSITION-RESOLVED PATH PATCHING (plan 1.5 and 2.3, descriptive)
# ==============================================================================

def writer_receivers(writer, kv_group_of) -> List[Tuple[tuple, str]]:
    """Plan 1.5's receivers of one outside writer, with the mask each is written at:
    an MLP's input at the Readout; a head's q at the Readout and its KV group's k and v
    post-clause (Readout included). `kv_group_of(head) -> group`."""
    kind, layer, index = writer
    if kind == "mlp":
        return [(("mlp_in", layer, 0), "readout")]
    group = int(kv_group_of(index))
    return [(("q", layer, index), "readout"), (("k", layer, group), "post_clause"),
            (("v", layer, group), "post_clause")]


def quartet_reaches(layer: int, receiver) -> bool:
    """Can the quartet (heads of layer `layer`) write into this receiver? A head's
    output reaches its own layer's MLP input and every later layer's q, k and v."""
    kind, receiver_layer, _index = receiver
    return receiver_layer >= layer if kind == "mlp_in" else receiver_layer > layer


def top_writers(senders_summary: dict, keys: Sequence[tuple], n: int) -> List[tuple]:
    """The `n` keys with the largest |e_s| in a `summarize_sweep` "senders" map."""
    scored = [(abs(senders_summary[key_name(key)]["e"]), key) for key in keys
              if key_name(key) in senders_summary]
    return [key for _score, key in sorted(scored, key=lambda one: -one[0])[:n]]


def _two_pass(model, streams, captured, sites, masks):
    """Pass 2 of path patching: D with these receiver inputs written at their masks."""
    from component_analysis import hooks
    from component_analysis import path_patching as pp

    replacements = {site: hooks.Replacement(captured.outputs[site], masks[mask])
                    for site, mask in sites}
    return pp.readout_from_receivers(model, streams, replacements)


def quartet_path_patching(model, pair: PairStreams, quartet_keys, writers, *, kv_group_of
                          ) -> dict:
    """Plan 1.5: the quartet, one joint sender with its T values, written only at the
    masks of `PP_SENDER_MASKS` (D elsewhere), into each reachable writer's receivers.

    Returns `{sender mask: {"writers": {name: [batch] drop}, "joint": [batch] drop}}`,
    drops in logits; "joint" writes every reachable writer's receivers at once. Pass 1
    freezes every other sender at D (`path_patching.receiver_inputs`); pass 2 runs D
    with the receivers written and everything downstream free.
    """
    import torch

    from component_analysis import hooks
    from component_analysis import path_patching as pp

    layer = quartet_keys[0][1]
    streams = sweep_streams(model, pair, pair.t.outputs)
    plans = {key_name(writer): [(site, mask) for site, mask
                                in writer_receivers(writer, kv_group_of)
                                if quartet_reaches(layer, site)]
             for writer in writers}
    plans = {name: sites for name, sites in plans.items() if sites}
    every = list(dict.fromkeys(site for sites in plans.values() for site in sites))
    out = {}
    for mask_name in PP_SENDER_MASKS:
        if not every:
            out[mask_name] = {"writers": {}, "joint": torch.zeros_like(pair.d.margin)}
            continue
        captured = pp.receiver_inputs(model, streams, senders=list(quartet_keys),
                                      receivers=list(dict.fromkeys(s for s, _ in every)),
                                      sender_positions=pair.masks[mask_name])
        drop = {}
        for name, sites in plans.items():
            logits = _two_pass(model, streams, captured, sites, pair.masks)
            drop[name] = pair.d.margin - hooks.target_minus_distractor(
                logits, pair.target, pair.distractor)
        logits = _two_pass(model, streams, captured, every, pair.masks)
        out[mask_name] = {"writers": drop, "joint": pair.d.margin - hooks.target_minus_distractor(
            logits, pair.target, pair.distractor)}
    return out


def feeder_groups(feeders, *, layer: int, num_layers: int, num_heads: int):
    """Plan 2.3's senders: each named feeder the model has below layer `layer`, then
    every layer below it as one group (its heads and its MLP). Returns
    `(groups [(name, keys)], skipped {name: reason})`."""
    groups, skipped = [], {}
    for key in feeders:
        kind, at, index = key
        if kind not in ("head", "mlp") or at >= num_layers or \
                (kind == "head" and index >= num_heads) or (kind == "mlp" and index != 0):
            skipped[key_name(key)] = "not a sender of this model"
        elif at >= layer:
            skipped[key_name(key)] = f"not below the quartet's layer {layer}"
        else:
            groups.append((key_name(key), [tuple(key)]))
    for at in range(layer):
        groups.append((f"layer.{at}", [("head", at, h) for h in range(num_heads)]
                       + [("mlp", at, 0)]))
    return groups, skipped


def feeder_path_patching(model, pair: PairStreams, groups, *, layer: int, quartet,
                         kv_group: int) -> dict:
    """Plan 2.3: each sender group from T (every position, the rest frozen at D) into
    the quartet's q at the Readout (the four jointly) and into `k.L.g` at the options.

    Returns `{group name: {"q_readout": [batch] drop, "k_options": [batch] drop}}`.
    """
    from component_analysis import hooks
    from component_analysis import path_patching as pp

    streams = sweep_streams(model, pair, pair.t.outputs)
    q_sites = [(("q", layer, h), "readout") for h in quartet]
    k_sites = [(("k", layer, kv_group), "options")]
    out = {}
    for name, keys in groups:
        captured = pp.receiver_inputs(model, streams, senders=keys,
                                      receivers=[site for site, _ in q_sites + k_sites])
        out[name] = {}
        for label, sites in (("q_readout", q_sites), ("k_options", k_sites)):
            logits = _two_pass(model, streams, captured, sites, pair.masks)
            out[name][label] = pair.d.margin - hooks.target_minus_distractor(
                logits, pair.target, pair.distractor)
    return out


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


def _t1_forwards(ctx, *, n_outside: int, n_kv: int, num_layers: int, num_heads: int,
                 draws: int) -> Tuple[int, int]:
    """Per batch: (T1 sweep and control forwards, path-patching forwards), no model."""
    layer, quartet = _quartet(ctx)
    tests = _selected(_cli(ctx, "route_tests", BOTH), (T1, T2))
    directions = _selected(_cli(ctx, "route_direction", BOTH), (RESTORE, REVERSE))
    if T1 not in tests or RESTORE not in directions:
        return 0, 0
    modes = _selected(_cli(ctx, "route_sweep", BOTH), (FORWARD, OFFLINE))
    sweep = (2 * n_outside + 2) if FORWARD in modes else 0
    if OFFLINE in modes:
        present = [one for one in range(_cli(ctx, "route_c2_layers", DEFAULT_C2_LAYERS)[0],
                                        _cli(ctx, "route_c2_layers", DEFAULT_C2_LAYERS)[1] + 1)
                   if one < num_layers]
        sweep += draws + (draws if present else 0) + 1 + \
            (1 if _cli(ctx, "route_deciding_set") else 0)
    paths = 0
    if _cli(ctx, "route_path_patching", "on") == "on":
        top = min(int(_cli(ctx, "route_pp_top", DEFAULT_PP_TOP)), n_outside)
        groups, _skipped = feeder_groups(
            parse_keys(_cli(ctx, "route_pp_feeders", DEFAULT_PP_FEEDERS)), layer=layer,
            num_layers=num_layers, num_heads=num_heads)
        paths = 2 + len(PP_SENDER_MASKS) * (top + 2) + 3 * len(groups)
    return sweep, paths


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
    num_layers = shape.get("num_layers") or shape.get("layers")
    num_heads = shape.get("num_heads") or 32
    if not isinstance(num_layers, int):
        num_layers, assumed = 32, assumed + " (32 layers assumed, as on Llama-3.1-8B)"
    n_arms = _counts(ctx, n_kv)["arms"]
    n_batches = len(batches)
    limit = int(_cli(ctx, "route_max_batches", 0) or 0)
    if limit:
        n_batches = min(n_batches, limit)
    forwards = n_batches * (2 + n_arms)
    quartet_keys = {("head", layer, h) for h in quartet}
    n_outside = len(outside_senders(num_layers=num_layers, num_heads=num_heads,
                                    excluded=set(grid_keys) | quartet_keys))
    draws = int(_cli(ctx, "route_control_draws", DEFAULT_CONTROL_DRAWS))
    sweep, paths = _t1_forwards(ctx, n_outside=n_outside, n_kv=n_kv, num_layers=num_layers,
                                num_heads=num_heads, draws=draws)
    sweep, paths = n_batches * sweep, n_batches * paths
    per = pp.seconds_per_forward(batches.report.get("batch_size") or 1)
    return (f"quartet layer {layer} heads {list(quartet)}; {n_arms} arm(s) "
            f"(tests {_cli(ctx, 'route_tests', BOTH)}, direction "
            f"{_cli(ctx, 'route_direction', BOTH)}) + 2 whole captures per batch over "
            f"{n_batches} batch(es) = {forwards} forward(s){assumed}, plus {sweep} T1 "
            f"sweep and control forward(s) ({n_outside} outside sender(s), estimators "
            f"{_cli(ctx, 'route_sweep', BOTH)}) and {paths} path-patching forward(s); about "
            f"{(forwards + sweep + paths) * per / 60:.1f} "
            f"min at the A40 rate (capture-all forwards are heavier; time the smoke); "
            f"{twins if twins is not None else '?'} instance(s) with a twin; grid "
            f"{grid['source']} ({len(grid_keys)} Component(s))")


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
    c2_layers = _cli(ctx, "route_c2_layers", DEFAULT_C2_LAYERS)
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
                   "positions_per_draw": POSITIONS_PER_DRAW,
                   "route_path_patching": _cli(ctx, "route_path_patching", "on"),
                   "route_pp_feeders": _cli(ctx, "route_pp_feeders", DEFAULT_PP_FEEDERS),
                   "route_c2_layers": list(c2_layers)},
        "quartet": quartet_meta, "grid": grid, "deciding_set": deciding,
        "controls": {"q_heads": [list(one) for one in head_draws], "k_groups": k_groups,
                     "positions_per_draw": POSITIONS_PER_DRAW},
        "arms_selected": [arm.name for arm in arms],
        "t1": {"sweeps": {"status": "not selected (T1 needs --route-tests t1 or both and "
                                    "--route-direction restore or both)",
                          "estimators": _cli(ctx, "route_sweep", BOTH)},
               "summary": None,
               "path_patching": {"status": "not selected"}},
        "not_implemented": list(NOT_IMPLEMENTED),
    }


class _SweepTally:
    """One arm's per-batch sweep results, concatenated at the end (CPU, fp32)."""

    def __init__(self, keys, intervened=()):
        self.keys = [tuple(one) for one in keys]
        self.intervened = [tuple(one) for one in intervened]
        self.drops, self.joint, self.margins = [], [], []

    def add(self, drops, joint, margins) -> None:
        self.drops.append(drops.float().cpu())
        self.joint.append(joint.float().cpu())
        self.margins.append(margins.float().cpu())

    def summary(self, *, outside: set, gap, m_d) -> dict:
        import torch

        include = [key in outside and key not in self.intervened for key in self.keys]
        out = summarize_sweep(torch.cat(self.drops), self.keys, gap=gap, include=include,
                              joint=torch.cat(self.joint), margins=torch.cat(self.margins),
                              m_d=m_d, rows=REPORTED_ROWS)
        out["intervened"] = [key_name(one) for one in self.intervened]
        return out


def _ratio(numerator, denominator) -> Optional[float]:
    if numerator is None or denominator in (None, 0) or denominator == 0.0:
        return None
    return float(numerator) / float(denominator)


def _g3(forward: dict, offline: dict, outside_names) -> dict:
    """Gate G3: estimators (a) and (b) agree per outside sender and on the summed O."""
    gate = {"per_sender_tolerance": G3_PER_SENDER, "sum_tolerance": G3_SUM,
            "arms": list(FORWARD_ARMS)}
    if not forward or not offline:
        gate.update(passed=None, max_sender_diff=None, max_sum_diff=None,
                    note="needs --route-sweep both")
        return gate
    sender_diff, sum_diff, joint_diff, worst = 0.0, 0.0, 0.0, None
    for arm in FORWARD_ARMS:
        for name in outside_names:
            diff = abs(forward[arm]["senders"][name]["e"] - offline[arm]["senders"][name]["e"])
            if diff > sender_diff:
                sender_diff, worst = diff, f"{arm}:{name}"
        sum_diff = max(sum_diff, abs(forward[arm]["O"] - offline[arm]["O"]))
        joint_diff = max(joint_diff, abs(forward[arm]["O_joint"] - offline[arm]["O_joint"]))
    gate.update(passed=bool(sender_diff <= G3_PER_SENDER and sum_diff <= G3_SUM),
                max_sender_diff=sender_diff, worst_sender=worst, max_sum_diff=sum_diff,
                max_joint_diff=joint_diff)
    return gate


def _t1_summary(ctx, forward: dict, offline: dict) -> dict:
    """The point numbers of plan 1.2 to 1.4 (the readings script recomputes them, with
    per-instance medians and the clustered bootstrap, from the per-instance sums)."""
    rule, name = (forward, FORWARD) if forward else (offline, OFFLINE)
    o, o_q = rule["T"]["O"], rule["dq_all"]["O"]
    task = ct_task(ctx.task_spec.name)
    out = {"rule_estimator": name, "O": o, "O_q": o_q, "M_q": _ratio(o_q, o),
           "r_q": rule["dq_all"]["r_total"],
           "O_pos": rule["T"]["O_pos"], "O_neg": rule["T"]["O_neg"],
           "O_q_pos": rule["dq_all"]["O_pos"], "O_q_neg": rule["dq_all"]["O_neg"],
           "O_joint": rule["T"]["O_joint"], "O_q_joint": rule["dq_all"]["O_joint"],
           "rows": {row: {"T": rule["T"]["rows"].get(row),
                          "dq_all": rule["dq_all"]["rows"].get(row)}
                    for row in sorted(set(rule["T"]["rows"]) | set(rule["dq_all"]["rows"]))},
           "selection_sample_O": SELECTION_SAMPLE_O.get(task),
           "M_C1": {}, "M_C2": {}, "M_C3": None, "M_S": None,
           "M_dq_readout": None, "M_dq_post_clause_no_readout": None, "M_q_offline": None}
    if offline:
        base = offline["T"]["O"]
        for arm, value in offline.items():
            ratio = _ratio(value["O"], base)
            if arm.startswith("c1_d"):
                out["M_C1"][arm] = ratio
            elif arm.startswith("c2_d"):
                out["M_C2"][arm] = ratio
            elif arm == "c3_push":
                out["M_C3"] = ratio
            elif arm == "s_k":
                out["M_S"] = ratio
            elif arm == "dq_all":
                out["M_q_offline"] = ratio
            elif arm in ("dq_readout", "dq_post_clause_no_readout"):
                out[f"M_{arm}"] = ratio
    return out


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
    deciding, deciding_keys = None, []
    if _cli(ctx, "route_deciding_set"):
        path, name = ctx.cli.route_deciding_set
        deciding_keys = load_deciding_set((path, name))
        deciding = {"file": path, "name": name,
                    "keys": [key_name(one) for one in deciding_keys]}

    controls = T2 in tests and RESTORE in directions
    head_draws = (draw_control_heads(num_heads=shape["num_heads"], layer=layer,
                                     quartet=quartet, excluded=grid_keys, n_draws=draws,
                                     size=len(quartet), seed=seed) if controls else [])
    arms = build_arms(layer=layer, quartet=quartet, kv_group=kv_group,
                      num_kv_heads=shape["num_kv_heads"], tests=tests, directions=directions,
                      head_draws=head_draws, n_position_draws=draws if controls else 0)

    # ---- T1 (ticket 5): the outside senders, the estimators, the controls -----------
    t1_on = T1 in tests and RESTORE in directions
    modes = _selected(_cli(ctx, "route_sweep", BOTH), (FORWARD, OFFLINE)) if t1_on else ()
    forward_on, offline_on = FORWARD in modes, OFFLINE in modes
    pp_on = t1_on and _cli(ctx, "route_path_patching", "on") == "on"
    quartet_keys = [("head", layer, h) for h in quartet]
    outside = outside_senders(num_layers=shape["num_layers"], num_heads=shape["num_heads"],
                              excluded=set(grid_keys) | set(quartet_keys))
    outside_set = set(outside)
    every = [key for key in hooks.all_component_keys(model) if key != hooks.EMBED_KEY]
    all_keys = hooks.all_component_keys(model)
    c1_draws, c2_draws, t1_arms = [], [], []
    c2_layers = tuple(_cli(ctx, "route_c2_layers", DEFAULT_C2_LAYERS))
    if t1_on and offline_on:
        c1_draws = draw_control_heads(num_heads=shape["num_heads"], layer=layer,
                                      quartet=quartet, excluded=grid_keys, n_draws=draws,
                                      size=len(quartet), seed=seed)
        c2_draws = draw_c2_heads(num_heads=shape["num_heads"], layers=c2_layers,
                                 excluded=set(grid_keys) | set(deciding_keys)
                                 | set(quartet_keys),
                                 n_draws=draws, size=len(quartet), seed=seed,
                                 num_layers=shape["num_layers"])
        t1_arms = build_t1_arms(layer=layer, c1_draws=c1_draws, c2_draws=c2_draws,
                                deciding=deciding_keys)

    k_groups = [arm.meta["kv_group"] for arm in arms if "kv_group" in arm.meta]
    payload = _payload(ctx, model, quartet_meta={"layer": layer, "heads": list(quartet),
                                                 "kv_group": kv_group},
                       grid=grid, deciding=deciding, arms=arms + t1_arms,
                       head_draws=head_draws, k_groups=k_groups, draws=draws)

    segmentations = _by_id(getattr(ctx, "segmentations", None))
    limit = int(_cli(ctx, "route_max_batches", 0) or 0)
    ids, pressure_ids, without = [], [], []
    m_d, m_t, gap = [], [], []
    margins = {arm.name: [] for arm in arms + t1_arms}
    g1_identical, g1_diff, g2_diff = True, 0.0, 0.0
    first = None
    by_arm = {arm.name: arm for arm in arms + t1_arms}
    forward_tally = {name: _SweepTally(outside, by_arm[name].intervened
                                       if name in by_arm else ())
                     for name in (FORWARD_ARMS if forward_on else ())}
    offline_names = (["T"] + [one for one in OFFLINE_DQ_ARMS if one in by_arm]
                     + [arm.name for arm in t1_arms]) if offline_on else []
    offline_tally = {name: _SweepTally(every, by_arm[name].intervened
                                       if name in by_arm else ())
                     for name in offline_names}
    c3 = {"delta": [], "target_change": [], "achieved_change": [], "lens_D": []}

    def offline_add(name, x_outputs, x_margins, c_d):
        tally = offline_tally[name]
        joint = [key for key in outside if key not in tally.intervened]
        result = offline_direct_effects(model, pair, x_outputs, every, joint=joint,
                                        d_contributions=c_d)
        tally.add(result.drops, result.joint, x_margins)

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
        c_d = None
        if offline_on:
            from component_analysis import dla
            c_d = dla.component_contributions(model, _ReadoutView(pair.d.outputs, pair.readout),
                                              every)
        dq = None
        for arm in arms:
            swept = t1_on and arm.name in OFFLINE_DQ_ARMS and (offline_on or arm.name == "dq_all")
            result = run_arm(model, pair, bank_for(model, arm, pair),
                             capture_keys=all_keys if swept else (), base=arm.base)
            margins[arm.name].extend(result.margins.float().cpu().tolist())
            if arm.name == "g1_empty":
                g1_identical &= bool(torch.equal(result.margins, pair.d.margin))
                g1_diff = max(g1_diff, float((result.margins - pair.d.margin).abs().max()))
            if arm.name == "g2_all_components":
                g2_diff = max(g2_diff, float((result.margins - pair.t.margin).abs().max()))
            if swept and offline_on:
                offline_add(arm.name, result.outputs, result.margins, c_d)
            if arm.name == "dq_all" and t1_on:
                dq = result
            del result
        if t1_on:
            if offline_on:
                offline_add("T", pair.t.outputs, pair.t.margin, c_d)
            if forward_on:
                for name, x in (("T", pair.t), ("dq_all", dq)):
                    x_outputs = x.outputs
                    x_margins = x.margin if name == "T" else x.margins
                    drops = forward_sweep(model, pair, x_outputs, outside)
                    forward_tally[name].add(torch.stack([drops[key] for key in outside], dim=1),
                                            forward_joint(model, pair, x_outputs, outside),
                                            x_margins)
            for arm in t1_arms:
                push = None
                if arm.meta.get("push"):
                    push = solve_push(model, pair, dq.residual, layer=layer)
                    bank = direction_push_bank(pair, push, layer=layer)
                else:
                    bank = bank_for(model, arm, pair)
                result = run_arm(model, pair, bank, capture_keys=all_keys)
                margins[arm.name].extend(result.margins.float().cpu().tolist())
                offline_add(arm.name, result.outputs, result.margins, c_d)
                if push is not None:
                    achieved = lens_margin(model, result.residual[:, layer + 1].float(),
                                           pair.d.residual[:, layer + 1].float(),
                                           pair.target, pair.distractor) - push.before
                    c3["delta"].extend(push.delta.cpu().tolist())
                    c3["target_change"].extend(push.target_change.cpu().tolist())
                    c3["achieved_change"].extend(achieved.cpu().tolist())
                    c3["lens_D"].extend(push.before.cpu().tolist())
                del result
        del dq
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
        del pair, c_d

    if not ids:
        return _skip(ctx, payload, without)
    payload["instances"] = {"ids": ids, "pressure_ids": pressure_ids, "without_twin": without}

    mean_d, mean_t = _mean(m_d), _mean(m_t)
    payload["baseline"] = {"m_D": m_d, "m_T": m_t, "G": gap, "mean_m_D": mean_d,
                           "mean_m_T": mean_t, "mean_G": _mean(gap), "P": mean_d - mean_t}
    payload["gates"] = {"g1_bit_identical": g1_identical, "g1_max_abs_diff": g1_diff,
                        "g2_max_abs_diff": g2_diff}
    payload["arms"] = {arm.name: {**arm.as_json(), "margins": margins[arm.name],
                                  "mean": _mean(margins[arm.name])} for arm in arms + t1_arms}
    payload["positions"] = {"first_batch": first}

    if t1_on:
        gap_t = torch.tensor(gap, dtype=torch.float64)
        m_d_t = torch.tensor(m_d, dtype=torch.float64)
        forward = {name: tally.summary(outside=outside_set, gap=gap_t, m_d=m_d_t)
                   for name, tally in forward_tally.items()}
        offline = {name: tally.summary(outside=outside_set, gap=gap_t, m_d=m_d_t)
                   for name, tally in offline_tally.items()}
        outside_names = [key_name(one) for one in outside]
        payload["gates"]["g3"] = _g3(forward, offline, outside_names)
        sweeps = {
            "status": "computed", "estimators": _cli(ctx, "route_sweep", BOTH),
            "normalized_by": "mean G, the D minus T twin gap (baseline.mean_G), never the "
                             "arm's own gap; e_s = mean_i drop_s,i / mean_i G_i",
            "drop": "m(D) - m(D with the sender's Readout write from the arm), logits",
            "outside": {"n": len(outside), "keys": outside_names,
                        "excluded": {"embedding": True, "grid": grid["n"],
                                     "quartet": [key_name(one) for one in quartet_keys]}},
            "reported_rows": [key_name(one) for one in REPORTED_ROWS],
            "in_sum": "outside senders minus the arm's own intervened sites "
                      "(`intervened`); the C3 push site mlp.L is the push itself",
            "forward": forward, "offline": offline,
            "controls_status": ("computed with the offline estimator" if offline_on else
                                "not computed: C1, C2, C3 and S_k are read with the offline "
                                "estimator; run --route-sweep offline or both"),
            "c1_draws": [list(one) for one in c1_draws],
            "c2_draws": [[key_name(key) for key in one] for one in c2_draws],
            "c2_layers": list(c2_layers),
            "c2_status": ("drawn" if c2_draws else
                          f"not drawn: the model has no layer in {c2_layers[0]}-"
                          f"{c2_layers[1]}" if offline_on else "not run"),
        }
        if c3["delta"]:
            miss = [abs(a - b) for a, b in zip(c3["achieved_change"], c3["target_change"])]
            sweeps["c3"] = {**c3, "site": f"mlp.{layer}.0", "positions": "readout",
                            "scale": f"D's layer-{layer} residual at the Readout (fixed)",
                            "direction": "unit g * (W_U[target] - W_U[distractor])",
                            "max_abs_miss": max(miss)}
        payload["t1"] = {"sweeps": sweeps, "summary": _t1_summary(ctx, forward, offline),
                         "path_patching": {"status": "off (--route-path-patching off)"}}
        if pp_on:
            ranked = forward.get("T") or offline.get("T")
            payload["t1"]["path_patching"] = _path_patching(
                ctx, model, segmentations=segmentations, limit=limit, ids=ids,
                layer=layer, quartet=quartet, kv_group=kv_group, outside=outside,
                ranked=ranked, dq_summary=(forward.get("dq_all") or offline.get("dq_all")),
                rule_estimator=FORWARD if forward else OFFLINE, shape=shape)

    ctx.write_json(SUBDIR, JSON_FILE, payload)
    _declare(ctx, ids)
    return {}


def _effect(drops, gap) -> dict:
    import math

    import torch

    drops = torch.as_tensor(drops).double()
    gap = torch.as_tensor(gap).double()
    n = drops.shape[0]
    return {"e": float(drops.mean() / gap.mean()),
            "se": float(drops.std(unbiased=True) / math.sqrt(n) / gap.mean()) if n > 1 else None,
            "per_instance": drops.tolist()}


def _path_patching(ctx, model, *, segmentations, limit, ids, layer, quartet, kv_group, outside,
                   ranked, dq_summary, rule_estimator, shape) -> dict:
    """Plan 1.5 and 2.3, a second pass over the batches (the writers are chosen from the
    whole sample's e_s(T) first). Each batch's pair is captured again, senders only."""
    import torch

    from component_analysis import hooks

    top = int(_cli(ctx, "route_pp_top", DEFAULT_PP_TOP))
    writers = top_writers(ranked["senders"], outside, top)
    quartet_keys = [("head", layer, h) for h in quartet]
    groups, skipped = feeder_groups(
        parse_keys(_cli(ctx, "route_pp_feeders", DEFAULT_PP_FEEDERS)), layer=layer,
        num_layers=shape["num_layers"], num_heads=shape["num_heads"])
    keys = hooks.all_component_keys(model) + [hooks.READOUT_KEY]
    q15 = {mask: {"writers": {}, "joint": []} for mask in PP_SENDER_MASKS}
    f23 = {name: {"q_readout": [], "k_options": []} for name, _keys in groups}
    gaps, seen = [], []
    for number, batch in enumerate(ctx.causal_batches()):
        if limit and number >= limit:
            break
        pair = capture_pair(model, batch, segmentations, keys=keys)
        if pair is None:
            continue
        seen.extend(pair.ids)
        gaps.extend(pair.gap.cpu().tolist())
        quartet_out = quartet_path_patching(model, pair, quartet_keys, writers,
                                            kv_group_of=lambda h: hooks.kv_group_of(model, h))
        for mask, values in quartet_out.items():
            for name, drop in values["writers"].items():
                q15[mask]["writers"].setdefault(name, []).extend(drop.cpu().tolist())
            q15[mask]["joint"].extend(values["joint"].cpu().tolist())
        feeder_out = feeder_path_patching(model, pair, groups, layer=layer, quartet=quartet,
                                          kv_group=kv_group)
        for name, values in feeder_out.items():
            for label, drop in values.items():
                f23[name][label].extend(drop.cpu().tolist())
        del pair
    gap_t = torch.tensor(gaps, dtype=torch.float64)
    effects = {}
    for mask, values in q15.items():
        per = {name: _effect(drop, gap_t) for name, drop in values["writers"].items()}
        effects[mask] = {"writers": per, "joint": _effect(values["joint"], gap_t),
                         "sum_writers": sum(one["e"] for one in per.values())}
    writer_rows = []
    for writer in writers:
        name = key_name(writer)
        sites = writer_receivers(writer, lambda h: hooks.kv_group_of(model, h))
        writer_rows.append({
            "sender": name, "e_T": ranked["senders"][name]["e"],
            "e_Dq": dq_summary["senders"][name]["e"],
            "reachable": any(quartet_reaches(layer, site) for site, _mask in sites),
            "receivers": [{"site": key_name(site), "positions": mask,
                           "reached": quartet_reaches(layer, site)} for site, mask in sites]})
    return {
        "status": "computed", "counterfactual": "T (the Neutral-Clause Twin)",
        "normalized_by": "mean G", "same_instances": seen == list(ids),
        "freeze": "pass 1 freezes every other sender at D (L12 applies here only)",
        "plan_1_5": {
            "ranked_by": f"|e_s(T)|, {rule_estimator} estimator", "top": top,
            "sender": [key_name(one) for one in quartet_keys],
            "sender_masks": {mask: MASK_SEGMENTS[mask] for mask in PP_SENDER_MASKS},
            "writers": writer_rows, "effects": effects,
            "O_q": dq_summary["O"],
            "O_q_top_writers": sum(row["e_Dq"] for row in writer_rows)},
        "plan_2_3": {
            "receivers": {"q_readout": [f"q.{layer}.{h}" for h in quartet],
                          "k_options": f"k.{layer}.{kv_group}"},
            "receiver_positions": {"q_readout": "readout", "k_options": "options"},
            "senders": [{"name": name, "keys": [key_name(one) for one in keys_]}
                        for name, keys_ in groups],
            "skipped_senders": list(skipped), "skipped_reasons": skipped,
            "effects": {name: {label: _effect(drop, gap_t) for label, drop in values.items()}
                        for name, values in f23.items()}},
    }


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
