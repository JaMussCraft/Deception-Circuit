#!/usr/bin/env python3
"""
p1_readings.py -- the pre-registered phase-1 rules of the mechanism-analysis feature (ticket 03, spec section 2).

Pure functions over sweep numbers; the phase-1 results builder reads the fetched sweeps and calls them.

Effects (spec 2.2): for a Component c and test set X, d_c(X) = knockout drop / X's clean margin, signed, each in X's
own target direction (deceptive on D and I, honest on H and F); a positive d on H or F means "supports the honest
answer". Significance (docs/component-roles.md): |drop| >= 2 SE and >= 0.01 logits.
"""

from __future__ import annotations

MIN_DROP = 0.01          # logits
N_SE = 2.0
Z95 = 1.96
EPS = 1e-12


def significant_sign(e: dict) -> int:
    """+1 / -1 when the drop is significant in that direction, else 0. e = {"drop", "se"} in logits."""
    drop, se = e["drop"], e["se"]
    if abs(drop) + EPS >= N_SE * se and abs(drop) + EPS >= MIN_DROP:
        return 1 if drop > 0 else -1
    return 0


def d_of(e: dict) -> float:
    return e["drop"] / e["clean"]


def se_d(e: dict) -> float:
    return e["se"] / abs(e["clean"])


def rcls(D: dict, H: dict, F: dict) -> dict:
    """R-cls (spec 2.2, amended per R16), checked in order: opposes, shared, deception-leaning, honest-leaning, none.

    Each argument is {"drop", "se", "clean"} for the Component on that test set (S1 for D, S5 for H, S6 for F).
    """
    d = {"D": d_of(D), "H": d_of(H), "F": d_of(F)}
    sig = {"D": significant_sign(D), "H": significant_sign(H), "F": significant_sign(F)}
    m_hf = max(max(d["H"], 0.0), max(d["F"], 0.0))
    u_hf = max(max(d["H"] + Z95 * se_d(H), 0.0), max(d["F"] + Z95 * se_d(F), 0.0))
    hf_pos = sig["H"] > 0 or sig["F"] > 0
    out = {"d": d, "sig": sig, "m_HF": m_hf, "U_HF": u_hf, "reason": ""}
    if sig["D"] < 0:
        out["class"] = "opposes"
        return out
    if sig["D"] > 0 and hf_pos and m_hf > 0 and 0.5 - EPS <= d["D"] / m_hf <= 2.0 + EPS:
        out["class"] = "shared"
        return out
    if sig["D"] > 0 and d["D"] + EPS >= 2.0 * u_hf:
        out["class"] = "deception-leaning"
        return out
    if hf_pos and m_hf + EPS >= 2.0 * d["D"]:
        out["class"] = "honest-leaning"
        return out
    out["class"] = "none"
    if sig["D"] > 0 and hf_pos:
        out["reason"] = "D and H/F both significant, ratio outside [0.5, 2] and no factor-two dominance"
    elif sig["D"] > 0:
        out["reason"] = "D significant, H/F not significant but their upper 95% bound exceeds d(D) / 2"
    elif hf_pos:
        out["reason"] = "H/F significant but below twice d(D)"
    else:
        out["reason"] = "nothing significant"
    return out


# ------------------------------------------------------------------ clustered bootstrap (R12)

def _cluster_rate(clusters, rng, idx=None):
    """Instance-weighted rate over a resample of whole clusters. clusters = [(sum, count)]."""
    pick = [clusters[i] for i in (idx if idx is not None else rng.integers(0, len(clusters), len(clusters)))]
    s, n = sum(p[0] for p in pick), sum(p[1] for p in pick)
    return s / n


def cluster_bootstrap_diff(a, b, n_boot: int = 2000, seed: int = 0, alpha: float = 0.05) -> dict:
    """rate(a) - rate(b) with a percentile CI from resampling whole clusters within each side.

    a, b: [(cluster_id, value)] with value 0/1 (or any number); clusters are pressure_ids (spec R12).
    """
    import numpy as np

    def group(rows):
        acc = {}
        for cid, v in rows:
            s, n = acc.get(cid, (0.0, 0))
            acc[cid] = (s + float(v), n + 1)
        return list(acc.values())
    ca, cb = group(a), group(b)
    diff = sum(float(v) for _, v in a) / len(a) - sum(float(v) for _, v in b) / len(b)
    rng = np.random.default_rng(seed)
    boots = np.array([_cluster_rate(ca, rng) - _cluster_rate(cb, rng) for _ in range(n_boot)])
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return {"diff": diff, "ci": (float(lo), float(hi)), "n_boot": n_boot, "seed": seed,
            "n_clusters": (len(ca), len(cb)), "n": (len(a), len(b))}


# ------------------------------------------------------------------ C-own (spec 2.7)

def sign_test_p(k: int, n: int) -> float:
    """One-sided sign test: P(X >= k) for X ~ Binomial(n, 0.5)."""
    from math import comb
    return sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n


def holm(pvals: dict) -> dict:
    """Holm step-down adjusted p-values, monotone, capped at 1."""
    order = sorted(pvals, key=lambda k: pvals[k])
    m, running, out = len(order), 0.0, {}
    for i, key in enumerate(order):
        running = max(running, min(1.0, (m - i) * pvals[key]))
        out[key] = running
    return out


def c_own(task: str, d_by_head: dict) -> dict:
    """R-own: a head of excl_t is "own" when its d(D) on t's D (S1) exceeds the max of its d(D) on the other tasks'
    D. d_by_head = {head: {task: d}}. Returns the per-head call, k of n, and the one-sided sign-test p."""
    own = {}
    for head, d in d_by_head.items():
        others = [v for t, v in d.items() if t != task]
        own[head] = d[task] > max(others)
    k, n = sum(own.values()), len(own)
    return {"own": own, "k": k, "n": n, "p": sign_test_p(k, n) if n else None}
