"""component_analysis/probe.py: pure pieces of the B2 P1 falsity probe (instructed-route ticket T7).

numpy and torch only: the mgnp environment has neither sklearn nor scipy. `scripts/falsity_probe.py` drives these
over a T6 capture directory.

- `standardise_fit` / `standardise_apply`: per-feature mean and population standard deviation on the fit rows; a
  feature whose deviation is under 1e-8 is divided by 1.
- `fit_logistic(X, y, C)`: L2 logistic regression in float64 torch with LBFGS (strong Wolfe line search). The
  objective is mean binary cross-entropy + ||w||^2 / (2 C n), which is sklearn's `C * sum(loss) + ||w||^2 / 2`
  divided by `C n`, so C means what it means in sklearn. The intercept is not penalised.
- `mass_mean(X, y)`: mean of the y = 1 rows minus mean of the y = 0 rows (descriptive).
- `auroc(pos, neg)`: the Mann-Whitney statistic with average ranks, so a tie counts one half. P(pos > neg).
- `cluster_bootstrap`: resamples whole clusters with replacement (numpy `default_rng(seed)`), so it is
  seed-deterministic; `percentile_ci` reads the 2.5 and 97.5 percentiles.
- `permutation_swaps`: a boolean [n_permutations, n_pairs] mask, each entry True with probability 1/2, saying
  which instance pairs have their D and H labels swapped.
- `band`, `anti_aligned`, `gate_fallback`, `ci_band_edges_crossed`, `r2_label`: the frozen rules of `spec.md`
  (B2 exit criteria and ruling R2) and plan section 1.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

#: The frozen bands on the SER rule number (spec.md, B2): at least 0.75 misleadingness, under 0.6 literal falsity.
MISLEADING_AT = 0.75
LITERAL_UNDER = 0.6
BAND_EDGES = (LITERAL_UNDER, MISLEADING_AT)
#: Plan section 1: a FAR gate AUROC under 0.75 makes P1 report the per-token DLA alone.
GATE_AT = 0.75
#: Ruling R2: the cells that must score under 0.6 against their twins for a clean misleadingness verdict.
R2_CELLS = ("far_I", "far_HI", "ser_HI")
R2_UNDER = 0.6
STD_FLOOR = 1e-8


# ==============================================================================
# STANDARDISATION, FIT, MASS-MEAN
# ==============================================================================

def standardise_fit(X) -> Tuple[np.ndarray, np.ndarray]:
    """-> (mean, std) over the rows of X, float64; a near-constant feature gets std 1."""
    X = np.asarray(X, dtype=np.float64)
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std = np.where(std < STD_FLOOR, 1.0, std)
    return mean, std


def standardise_apply(X, mean, std) -> np.ndarray:
    return (np.asarray(X, dtype=np.float64) - mean) / std


def fit_logistic(X, y, C: float, *, max_iter: int = 1000, tol: float = 1e-9) -> dict:
    """L2 logistic regression (float64 torch, LBFGS). -> {"w", "b", "converged", "grad_norm", "loss", "n_iter"}.

    Objective: mean BCE(X w + b, y) + ||w||^2 / (2 C n). `converged` means the gradient's max-norm fell under
    1e-5 (LBFGS stops earlier on `tol` changes, which counts as converged when the gradient is that small).
    """
    import torch

    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if X.ndim != 2 or y.shape != (X.shape[0],):
        raise ValueError(f"fit_logistic: X {X.shape} and y {y.shape} do not match")
    if not (np.isfinite(X).all() and np.isfinite(y).all()):
        raise ValueError("fit_logistic: non-finite input")
    n, d = X.shape
    Xt = torch.from_numpy(X)
    yt = torch.from_numpy(y)
    w = torch.zeros(d, dtype=torch.float64, requires_grad=True)
    b = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    penalty = 1.0 / (2.0 * float(C) * n)
    optimiser = torch.optim.LBFGS([w, b], lr=1.0, max_iter=max_iter, tolerance_grad=1e-10,
                                  tolerance_change=tol * 1e-3, history_size=20, line_search_fn="strong_wolfe")

    def objective():
        z = Xt @ w + b
        return torch.nn.functional.binary_cross_entropy_with_logits(z, yt) + penalty * (w @ w)

    def closure():
        optimiser.zero_grad()
        loss = objective()
        loss.backward()
        return loss

    optimiser.step(closure)
    optimiser.zero_grad()
    loss = objective()
    loss.backward()
    grad = max(float(w.grad.abs().max()), float(b.grad.abs().max()))
    state = optimiser.state[w]
    return {"w": w.detach().numpy().copy(), "b": float(b.detach()), "converged": grad < 1e-5,
            "grad_norm": grad, "loss": float(loss.detach()), "n_iter": int(state.get("n_iter", 0))}


def decision(X, w, b) -> np.ndarray:
    return np.asarray(X, dtype=np.float64) @ np.asarray(w, dtype=np.float64) + float(b)


def mass_mean(X, y) -> np.ndarray:
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y).astype(bool)
    return X[y].mean(axis=0) - X[~y].mean(axis=0)


# ==============================================================================
# AUROC
# ==============================================================================

def average_ranks(x) -> np.ndarray:
    """1-based ranks, ties sharing the mean of the ranks they span."""
    x = np.asarray(x, dtype=np.float64)
    _, inverse, counts = np.unique(x, return_inverse=True, return_counts=True)
    upper = np.cumsum(counts).astype(np.float64)
    mid = upper - (counts - 1) / 2.0
    return mid[np.asarray(inverse).reshape(-1)]


def auroc(pos, neg) -> float:
    """Mann-Whitney AUROC of `pos` (label 1) against `neg` (label 0): P(pos > neg) + P(pos = neg) / 2."""
    pos = np.asarray(pos, dtype=np.float64).reshape(-1)
    neg = np.asarray(neg, dtype=np.float64).reshape(-1)
    if pos.size == 0 or neg.size == 0:
        raise ValueError("auroc: an empty class")
    if not (np.isfinite(pos).all() and np.isfinite(neg).all()):
        raise ValueError("auroc: non-finite score")
    ranks = average_ranks(np.concatenate([pos, neg]))
    u = ranks[:pos.size].sum() - pos.size * (pos.size + 1) / 2.0
    return float(u / (pos.size * neg.size))


# ==============================================================================
# RESAMPLING
# ==============================================================================

def cluster_bootstrap(stat: Callable[[np.ndarray], float], clusters, *, n_resamples: int,
                      seed: int) -> np.ndarray:
    """Resample whole clusters with replacement; `stat(indices)` is evaluated on every draw's unit indices.

    `clusters` labels each unit (here an instance pair) with its cluster (here `pressure_id`). A draw picks as many
    clusters as there are, with replacement, and takes every unit of each picked cluster. -> [n_resamples].
    """
    clusters = np.asarray(clusters)
    labels = sorted(set(clusters.tolist()))
    members = [np.flatnonzero(clusters == label) for label in labels]
    rng = np.random.default_rng(seed)
    out = np.empty(n_resamples, dtype=np.float64)
    for i in range(n_resamples):
        picked = rng.integers(0, len(members), size=len(members))
        out[i] = stat(np.concatenate([members[j] for j in picked]))
    return out


def percentile_ci(draws, level: float = 0.95) -> Tuple[float, float]:
    draws = np.asarray(draws, dtype=np.float64)
    tail = (1.0 - level) / 2.0 * 100.0
    return float(np.percentile(draws, tail)), float(np.percentile(draws, 100.0 - tail))


def permutation_swaps(n_pairs: int, n_permutations: int, *, seed: int) -> np.ndarray:
    """[n_permutations, n_pairs] booleans: True swaps that pair's D and H labels in that refit."""
    rng = np.random.default_rng(seed)
    return rng.random((n_permutations, n_pairs)) < 0.5


# ==============================================================================
# RULES
# ==============================================================================

def band(value: float) -> str:
    """The frozen B2 band of a SER AUROC point estimate. Under 0.5 stays literal falsity (see `anti_aligned`)."""
    if value >= MISLEADING_AT:
        return "misleadingness"
    if value < LITERAL_UNDER:
        return "literal_falsity"
    return "indeterminate"


def anti_aligned(value: float) -> bool:
    return value < 0.5


def gate_fallback(far_gate_auroc: float) -> bool:
    return far_gate_auroc < GATE_AT


def ci_band_edges_crossed(lo: float, hi: float) -> List[float]:
    """The band edges that fall in a different band from one CI end to the other."""
    return [edge for edge in BAND_EDGES if band(lo) != band(hi) and lo < edge <= hi]


def r2_label(rule_band: str, controls: Dict[str, float]) -> Optional[str]:
    """Ruling R2. None unless the rule number is in the misleadingness band; then "clean" when FAR I, FAR HI and
    SER HI all score under 0.6 against their twins, otherwise "instruction-confounded" (with SER D at 0.75 or more,
    a FAR I or HI cell at 0.6 or more is predicted only by the clause-or-instruction-detector column)."""
    values = [controls[cell] for cell in R2_CELLS]
    if rule_band != "misleadingness":
        return None
    return "clean" if all(value < R2_UNDER for value in values) else "instruction-confounded"


def summarise(values: Sequence[float]) -> dict:
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        return {"n": 0}
    return {"n": int(values.size), "mean": float(values.mean()), "sd": float(values.std()),
            "q05": float(np.percentile(values, 5)), "q95": float(np.percentile(values, 95)),
            "max": float(values.max()), "min": float(values.min())}
