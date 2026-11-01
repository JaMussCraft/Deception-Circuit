"""Nulls and bootstrap for the B3 patching (plan B3 sections 2 and 3.2), ported, plus the R10 member exclusion.

Sources, both read-only and outside the package because they live under `outputs/`:

- `layer_matched_nulls`, `ALL`, `POSITIVE_CONTROL`, `N_NULL`, `NULL_SEED`: from
  `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_launch_mechanism_analysis/p1c_groups.py`
  (mechanism-analysis ticket 03, the phase-1C groups builder).
- `mediated_fraction`, `instance_boot`, `f_boot`, `ci`, `N_BOOT`: from
  `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_launch_mechanism_analysis/p1c_results.py`
  (the phase-1C results builder that produced the FAR held-out f_D of 0.893).

The bootstrap bodies are copied without change. `layer_matched_nulls` is the source body plus ruling R10 (spec.md,
Sun 1 Nov 2026): from J4 on, a null draw for a set excludes that set's own members, with the same seed and the same
(kind, layer) counts. Exclusion is on by default. `exclude_members=False` is the source draw exactly, which is how J3
was drawn (its results.json records `null_kind` "layer_matched" and has no `exclude_members` field).
`tests/test_b3_patching.py` loads the two source files and asserts that the `exclude_members=False` draws and the
bootstrap values equal the source's per seed. A (kind, layer) with fewer non-member candidates than members raises
`NullPoolError` naming the set and the layer; nothing is drawn short.

Ruling R10a (lead, Sun 1 Nov 2026, option (a)): Llama has one MLP block per layer, so an MLP member is the only
candidate at its layer. The exclusion therefore applies to heads only, and MLP members stay in every draw as
unavoidable (`keep_mlp_members=True`, the default; plan 3.2 already fixes the MLP part of every draw). A null draw for
an MLP-containing set thus shares the set's MLPs, and the comparison tests the set's heads against random heads given
the same MLPs. `keep_mlp_members=False` is strict exclusion, under which S_all, S_far and S_ser raise.

`heads_only_nulls`: the heads-only arm needs a null over the heads alone. It is `layer_matched_nulls` applied to the
set's heads, so it inherits the member exclusion and is the same under either MLP setting.

`kept_members(S, draw)`: the members of S that a draw contains, as `head.L.H` / `mlp.L.0` names, recorded per draw.

Pure Python and NumPy only, so it imports on both interpreters.
"""
from __future__ import annotations

import random

N_LAYERS, N_HEADS = 32, 32
ALL = [("head", l, h) for l in range(N_LAYERS) for h in range(N_HEADS)] + [("mlp", l, 0) for l in range(N_LAYERS)]
POSITIVE_CONTROL = ("mlp", 0, 0)
N_NULL = 20
NULL_SEED = 20261025
N_BOOT = 2000


# ------------------------------------------------------------------ from p1c_groups.py, plus the R10 exclusion

class NullPoolError(ValueError):
    """A (kind, layer) has fewer non-member candidates than the set has members there."""


def layer_matched_nulls(S, n=N_NULL, seed=NULL_SEED, *, exclude_members=True, keep_mlp_members=True, label=None):
    """n random sets with S's (kind, layer) counts, drawn without replacement within each (kind, layer).

    exclude_members (R10, default on): each (kind, layer) pool leaves out S's own members. False gives the p1c_groups
    source draw exactly (J3). keep_mlp_members (R10a, default on): MLP members stay in their pools, so only head
    members are excluded; False is strict exclusion. Raises NullPoolError, naming `label` and the layer, when a pool
    is smaller than the count it must supply.
    """
    rng = random.Random(seed)
    need = {}
    for kind, layer, _ in S:
        need[(kind, layer)] = need.get((kind, layer), 0) + 1
    members = {tuple(k) for k in S} if exclude_members else set()
    if keep_mlp_members:
        members = {k for k in members if k[0] != "mlp"}
    pools = {(kind, layer): [k for k in ALL if k[0] == kind and k[1] == layer and k != POSITIVE_CONTROL
                             and k not in members]
             for kind, layer in need}
    for (kind, layer), count in sorted(need.items()):
        have = len(pools[(kind, layer)])
        if have < count:
            raise NullPoolError(
                f"set {label or '<unnamed>'}: layer {layer} {kind} has {have} non-member candidate(s) for "
                f"{count} member(s); a member-excluded layer-matched null draw is impossible there"
                + (" (one MLP per layer, so the member is the only candidate)" if kind == "mlp" else ""))
    out = []
    for _ in range(n):
        draw = []
        for key in sorted(need):
            draw += rng.sample(pools[key], need[key])
        out.append(draw)
    return out


# ------------------------------------------------------------------ the heads-only variant (new)

def heads_only_nulls(S, n=N_NULL, seed=NULL_SEED, *, exclude_members=True, label=None):
    """`layer_matched_nulls` over S's heads only: the null of the heads-only arm (member exclusion as there)."""
    return layer_matched_nulls([k for k in S if k[0] == "head"], n=n, seed=seed, exclude_members=exclude_members,
                               label=label)


def kept_members(S, draw):
    """The members of S that `draw` contains, in S's order, as names: under R10a these are S's MLP members."""
    d = {tuple(k) for k in draw}
    return [f"{k[0]}.{k[1]}.{k[2]}" for k in S if tuple(k) in d]


# ------------------------------------------------------------------ from p1c_results.py (unchanged)

def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def mediated_fraction(clean, knocked, twin) -> float:
    c = _mean(clean)
    return (c - _mean(knocked)) / (c - _mean(twin))


def instance_boot(n, *, n_boot=N_BOOT, seed=0):
    import numpy as np
    return np.random.default_rng(seed).integers(0, n, (n_boot, n))


def f_boot(C, K, T, idx):
    """Bootstrap f values for index matrix idx (n_boot x n); C, K, T numpy arrays."""
    c = C[idx].mean(1)
    return (c - K[idx].mean(1)) / (c - T[idx].mean(1))


def ci(vals, alpha=0.05):
    import numpy as np
    lo, hi = np.quantile(np.asarray(vals, dtype=float), [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)
