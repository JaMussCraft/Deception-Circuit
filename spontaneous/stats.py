"""Nulls and bootstrap for the B3 patching (plan B3 sections 2 and 3.2), ported unchanged.

Sources, both read-only and outside the package because they live under `outputs/`:

- `layer_matched_nulls`, `ALL`, `POSITIVE_CONTROL`, `N_NULL`, `NULL_SEED`: from
  `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_launch_mechanism_analysis/p1c_groups.py`
  (mechanism-analysis ticket 03, the phase-1C groups builder).
- `mediated_fraction`, `instance_boot`, `f_boot`, `ci`, `N_BOOT`: from
  `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_launch_mechanism_analysis/p1c_results.py`
  (the phase-1C results builder that produced the FAR held-out f_D of 0.893).

The bodies are copied without change; `tests/test_b3_patching.py` loads the two source files and asserts the ported
draws and bootstrap values equal the source's per seed. The one addition is `heads_only_nulls`: Llama has one MLP
block per layer, so a layer-matched draw of a set with MLPs always redraws the same MLPs, and the heads-only arm needs
a null over the heads alone. It is `layer_matched_nulls` applied to the set's heads, nothing more.

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


# ------------------------------------------------------------------ from p1c_groups.py (unchanged)

def layer_matched_nulls(S, n=N_NULL, seed=NULL_SEED):
    """n random sets with S's (kind, layer) counts, drawn without replacement within each (kind, layer)."""
    rng = random.Random(seed)
    need = {}
    for kind, layer, _ in S:
        need[(kind, layer)] = need.get((kind, layer), 0) + 1
    pools = {(kind, layer): [k for k in ALL if k[0] == kind and k[1] == layer and k != POSITIVE_CONTROL]
             for kind, layer in need}
    out = []
    for _ in range(n):
        draw = []
        for key in sorted(need):
            draw += rng.sample(pools[key], need[key])
        out.append(draw)
    return out


# ------------------------------------------------------------------ the heads-only variant (new)

def heads_only_nulls(S, n=N_NULL, seed=NULL_SEED):
    """`layer_matched_nulls` over S's heads only: the null of the heads-only arm."""
    return layer_matched_nulls([k for k in S if k[0] == "head"], n=n, seed=seed)


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
