#!/usr/bin/env python3
"""Flip-audit analysis: which examples survive a circuit knockout, and why?

Copied from outputs/_suites/_launch_260922/flip_audit_analysis.py for the
format-control suites. Changes: `is_delta` reads the circuit's operands from
suite.json (so D&F is a delta and the coarse `(X) - m` knockout is not), and
cell task labels are test-set directory names (`far_honest`,
`sdr_nopressure`), as `merge_shards.py` files them, so `load_task_data`
reads the right test set. On `*_honest` / `*_nopressure` cells the target is
the honest answer: "stayed_deceptive" there means "stayed on the trained
(target) answer", and the positional check (P(item_2) under knockout versus
the base rate) reads the same way.

Reads every cells/<circuit>/<task>/<ablation>/knockout.json under a suite root
(the layout evaluate_circuit.py and merge_shards.py write) and asks whether the
examples that STAYED deceptive under the knockout share a pattern.

usage:
    python flip_audit_analysis.py <suite_root> [--ablation interchange]
        [--control <other_suite_root>] [--data-dir data/datasets]
        [--out-json PATH] [--out-md PATH]

Defaults write <suite_root>/flip_audit.json and <suite_root>/flip_audit.md.
Stdlib + numpy + datasets only (scipy is not assumed). Never loads a model.
Run from the repo root so the default --data-dir resolves.

Semantics this script relies on (evaluation/knockout.py):

* task.per_example[i].example_id is loader position i, and the evaluation
  loader is unshuffled and not subsampled, so it is test-set row i. The script
  CHECKS this per cell: prompt_excerpt must equal clean_prompt[-200:] of row i.
  When the match rate is low, the field cuts are skipped for that cell.
* status: stayed_deceptive = full model deceptive AND knockout deceptive;
  flipped_honest = full deceptive AND knockout honest; other = anything else
  (knockout left the A/B readout, or the full model was not deceptive).
* variants.<v>.per_example: `_variant_side` evaluates with ref_cache=None,
  "which ... is also what makes `ref_argmax_id` the full model's choice on the
  variant prompt". So full_choice there is the FULL model on the variant
  prompt, knockout_choice the knockout on the variant prompt.
* task.null.stats.accuracy is summarize_null() output with better='higher':
  percentile = % of random knockouts the discovered knockout's accuracy beats,
  z = (discovered - mean)/std. Separable = pct <= 5 and z <= -2, or a strict
  difference when the null has ~zero spread (write_evaluation_summary.py).
* instance_id is a hash of the task-independent instance key, but the three
  tasks' TEST splits barely share instances (behavioral filters differ), so
  cross-task per-instance overlap is reported with its shared-id count and
  backed up by correlating per-level stay-rates on factors the tasks share.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
from collections import Counter, defaultdict

import numpy as np

# ----------------------------------------------------------------------------
# constants
# ----------------------------------------------------------------------------
NULL_PCT = 95.0           # separable(): pct <= 100 - NULL_PCT
NULL_Z = -2.0             # separable(): z <= NULL_Z
SD_EPS = 1e-6             # separable(): zero-spread null
EXCERPT_CHARS = 200       # knockout.EXCERPT_CHARS
MIN_ALIGN = 0.95          # excerpt match rate needed to trust row alignment
LEVEL_MIN_N = 20          # a level is flaggable only with n >= this
LEVEL_MARGIN = 0.15       # ... and |stay-rate - overall| >= this
ALPHA = 0.05
N_PERM = 2000             # permutation test draws
SEED = 0
CAT_FIELDS = ("pressure_slot", "template_variant", "item_pair", "domain",
              "entity", "item_polarity", "designation_polarity", "answer_item")
NUM_FIELDS = ("prompt_chars", "target_is_item_2", "prior_margin",
              "clean_margin", "corrupt_margin")
SHARED_FIELDS = ("item_pair", "domain", "entity")   # comparable across tasks
POS_MARGIN = 0.15         # positional default: |P(KO picks item_2) - base rate| >= this
POS_P = 0.01              # ... with an exact binomial p below this
POS_GAP = 0.30            # ... and |stay-rate(target=item_2) - stay-rate(target=item_1)| >= this


# ----------------------------------------------------------------------------
# statistics (no scipy)
# ----------------------------------------------------------------------------
def _gammainc_upper_reg(a, x):
    """Q(a, x), the regularized upper incomplete gamma function."""
    if x <= 0:
        return 1.0
    if x < a + 1:           # series for P, then 1 - P
        term = s = 1.0 / a
        ap = a
        for _ in range(10000):
            ap += 1
            term *= x / ap
            s += term
            if abs(term) < abs(s) * 1e-15:
                break
        p = s * math.exp(-x + a * math.log(x) - math.lgamma(a))
        return max(0.0, 1.0 - p)
    tiny = 1e-300           # modified Lentz continued fraction for Q
    b = x + 1 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return min(1.0, h * math.exp(-x + a * math.log(x) - math.lgamma(a)))


def chi2_sf(x, k):
    if k <= 0 or x is None or not math.isfinite(x):
        return float("nan")
    return _gammainc_upper_reg(k / 2.0, x / 2.0)


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def chi2_2xk(stay, flip):
    """Pearson chi-square and G on a 2 x k table (rows stay/flip, cols levels).

    Levels with zero total are dropped first. Cramér's V with two outcome rows
    is sqrt(chi2 / n).
    """
    stay = np.asarray(stay, float)
    flip = np.asarray(flip, float)
    keep = (stay + flip) > 0
    stay, flip = stay[keep], flip[keep]
    k = len(stay)
    n = stay.sum() + flip.sum()
    if k < 2 or stay.sum() == 0 or flip.sum() == 0:
        return None
    obs = np.vstack([stay, flip])
    exp = obs.sum(1, keepdims=True) * obs.sum(0, keepdims=True) / n
    chi2 = float(((obs - exp) ** 2 / exp).sum())
    with np.errstate(divide="ignore", invalid="ignore"):
        g = float(2 * np.where(obs > 0, obs * np.log(np.where(obs > 0, obs, 1) / exp), 0).sum())
    dof = k - 1
    return {"chi2": chi2, "g": g, "dof": dof,
            "p_chi2": chi2_sf(chi2, dof), "p_g": chi2_sf(g, dof),
            "cramers_v": math.sqrt(chi2 / n),
            "cramers_v_corrected": _bergsma_v(chi2, n, k),
            "frac_expected_lt5": float((exp < 5).mean())}


def _bergsma_v(chi2, n, k, r=2):
    """Bias-corrected Cramér's V (Bergsma 2013); plain V is inflated for many levels."""
    if n <= 1:
        return float("nan")
    phi2 = max(0.0, chi2 / n - (k - 1) * (r - 1) / (n - 1))
    kc = k - (k - 1) ** 2 / (n - 1)
    rc = r - (r - 1) ** 2 / (n - 1)
    den = min(kc - 1, rc - 1)
    return math.sqrt(phi2 / den) if den > 0 else float("nan")


def perm_p_chi2(codes, y, n_levels, observed, rng, n_perm=N_PERM):
    """Permutation p-value for the 2 x k chi-square (robust to sparse levels)."""
    tot = np.bincount(codes, minlength=n_levels).astype(float)
    p1 = y.mean()
    e1, e0 = tot * p1, tot * (1 - p1)
    ok = tot > 0
    count = 0
    yf = y.astype(float)
    for _ in range(n_perm):
        yp = rng.permutation(yf)
        s = np.bincount(codes, weights=yp, minlength=n_levels)
        f = tot - s
        c = (((s - e1) ** 2)[ok] / e1[ok]).sum() + (((f - e0) ** 2)[ok] / e0[ok]).sum()
        count += c >= observed - 1e-9
    return (count + 1) / (n_perm + 1)


def perm_p_chi2_stratified(codes, y, n_levels, observed, strata, rng, n_perm=N_PERM):
    """Permutation p for the field's chi-square with y shuffled WITHIN strata.

    Holding the strongest field's levels fixed asks whether this field adds
    anything beyond it (a confounded field loses its signal here).
    """
    tot = np.bincount(codes, minlength=n_levels).astype(float)
    p1 = y.mean()
    e1, e0 = tot * p1, tot * (1 - p1)
    ok = tot > 0
    groups = [np.flatnonzero(strata == g) for g in np.unique(strata)]
    yp = y.astype(float).copy()
    count = 0
    for _ in range(n_perm):
        for g in groups:
            yp[g] = rng.permutation(yp[g])
        s = np.bincount(codes, weights=yp, minlength=n_levels)
        f = tot - s
        c = (((s - e1) ** 2)[ok] / e1[ok]).sum() + (((f - e0) ** 2)[ok] / e0[ok]).sum()
        count += c >= observed - 1e-9
    return (count + 1) / (n_perm + 1)


def two_prop_p(k1, n1, k2, n2):
    """Two-sided two-proportion z-test p-value."""
    if n1 == 0 or n2 == 0:
        return float("nan")
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    return 2 * norm_sf(abs(k1 / n1 - k2 / n2) / se)


def mann_whitney(x_pos, x_neg):
    """AUC = P(stayed value > flipped value), rank-biserial, normal-approx p."""
    x_pos = np.asarray(x_pos, float)
    x_neg = np.asarray(x_neg, float)
    n1, n2 = len(x_pos), len(x_neg)
    if n1 == 0 or n2 == 0:
        return None
    allv = np.concatenate([x_pos, x_neg])
    order = allv.argsort(kind="mergesort")
    ranks = np.empty(len(allv))
    sv = allv[order]
    i = 0
    tie_term = 0.0
    while i < len(sv):           # average ranks over ties
        j = i
        while j + 1 < len(sv) and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1
        t = j - i + 1
        tie_term += t ** 3 - t
        i = j + 1
    u = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    auc = u / (n1 * n2)
    n = n1 + n2
    var = n1 * n2 / 12.0 * ((n + 1) - tie_term / (n * (n - 1))) if n > 1 else 0
    p = 2 * norm_sf(abs(u - n1 * n2 / 2) / math.sqrt(var)) if var > 0 else 1.0
    return {"mean_stayed": float(x_pos.mean()), "mean_flipped": float(x_neg.mean()),
            "auc": float(auc), "rank_biserial": float(2 * auc - 1), "p": float(p)}


def binom_two_sided(k, n, p):
    """Exact two-sided binomial p-value: sum of P(X=i) over i with P(X=i) <= P(X=k)."""
    if n == 0 or p <= 0 or p >= 1:
        return float("nan")
    logp = [_logcomb(n, i) + i * math.log(p) + (n - i) * math.log(1 - p) for i in range(n + 1)]
    ref = logp[k] + 1e-9
    return float(min(1.0, sum(math.exp(v) for v in logp if v <= ref)))


def _logcomb(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def hypergeom_sf(k, n, a, b):
    """P(|A & B| >= k) for random A, B of sizes a, b in a population of n."""
    lo, hi = max(0, a + b - n), min(a, b)
    if k <= lo:
        return 1.0
    if k > hi:
        return 0.0
    denom = _logcomb(n, b)
    return float(min(1.0, sum(math.exp(_logcomb(a, i) + _logcomb(n - a, b - i) - denom)
                              for i in range(k, hi + 1))))


def overlap(a, b, n):
    a, b = set(a), set(b)
    inter, union = len(a & b), len(a | b)
    exp_inter = len(a) * len(b) / n if n else float("nan")
    exp_union = len(a) + len(b) - exp_inter
    return {"n_a": len(a), "n_b": len(b), "intersection": inter, "union": union,
            "jaccard": inter / union if union else float("nan"),
            "expected_intersection": exp_inter,
            "expected_jaccard": (exp_inter / exp_union) if exp_union else float("nan"),
            "p_overlap_ge": hypergeom_sf(inter, n, len(a), len(b)) if n else float("nan")}


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3:
        return float("nan")

    def rank(v):
        o = v.argsort(kind="mergesort")
        r = np.empty(len(v))
        sv = v[o]
        i = 0
        while i < len(sv):
            j = i
            while j + 1 < len(sv) and sv[j + 1] == sv[i]:
                j += 1
            r[o[i:j + 1]] = (i + j) / 2.0
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def holm(pvals):
    """Holm-adjusted p-values (dict name -> p); NaNs pass through."""
    items = sorted(((p, k) for k, p in pvals.items() if p == p), key=lambda t: t[0])
    m = len(items)
    out, running = {}, 0.0
    for i, (p, k) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    for k in pvals:
        out.setdefault(k, float("nan"))
    return out


# ----------------------------------------------------------------------------
# loading
# ----------------------------------------------------------------------------
def separable(st):
    """write_evaluation_summary.separable(): knockout measurably worse than null."""
    if not st:
        return None
    z, pct, std = st.get("z"), st.get("percentile"), st.get("std")
    if std is not None and abs(std) < SD_EPS:
        disc, mean = st.get("discovered"), st.get("mean")
        if disc is None or mean is None:
            return False
        return disc < mean if st.get("better") == "higher" else disc > mean
    return (pct is not None and pct <= 100 - NULL_PCT
            and z is not None and z <= NULL_Z)


def find_cells(root, ablation):
    paths = sorted(glob.glob(os.path.join(root, "cells", "*", "*", ablation, "knockout.json")))
    out = []
    for p in paths:
        parts = os.path.normpath(p).split(os.sep)
        out.append({"circuit": parts[-4], "task": parts[-3], "path": p})
    return out


def suite_exprs(root):
    """label -> {"expr", "operands"} from the suite's circuit provenance."""
    try:
        s = json.load(open(os.path.join(root, "suite.json")))
        return {c.get("label"): {"expr": c.get("expr"), "operands": list(c.get("operands") or {})}
                for c in s.get("circuits", [])}
    except Exception:       # noqa: BLE001
        return {}


#: Operands that are not circuits of the suite: the coarse heads-only knockout
#: subtracts the all-MLP, no-head operand `m` from every expression.
NON_CIRCUIT_OPERANDS = ("m",)


def is_delta(label, exprs):
    """A delta cell composes two or more of the suite's circuits.

    Format-control change: the cross-task version tested for '-' in the
    expression, which misses D&F and counts the coarse heads-only knockout of
    an atomic circuit, `(D) - m`, as a delta.
    """
    e = exprs.get(label) or {}
    if isinstance(e, str):              # older suite.json reader shape
        return label.startswith("delta") or "-" in e
    circuits = [n for n in e.get("operands", []) if n not in NON_CIRCUIT_OPERANDS]
    return label.startswith("delta") or len(circuits) >= 2


_DATA_CACHE = {}


def load_task_data(data_dir, task):
    """(records, note). Records carry the derived cut fields."""
    key = (data_dir, task)
    if key in _DATA_CACHE:
        return _DATA_CACHE[key]
    try:
        from datasets import load_from_disk
        ds = load_from_disk(os.path.join(data_dir, task, "test"))
        recs = []
        for r in ds:
            r = dict(r)
            t = str(r.get("target", "")).strip()
            i1, i2 = str(r.get("item_1", "")).strip(), str(r.get("item_2", "")).strip()
            r["answer_item"] = "item_1" if t == i1 else "item_2" if t == i2 else "neither"
            r["target_is_item_2"] = 1.0 if r["answer_item"] == "item_2" else 0.0
            r["prompt_chars"] = float(len(r.get("clean_prompt") or ""))
            for f in ("prior_margin", "clean_margin", "corrupt_margin"):
                try:
                    r[f] = float(r.get(f))
                except (TypeError, ValueError):
                    r[f] = float("nan")
            recs.append(r)
        res = (recs, "")
    except Exception as e:     # noqa: BLE001
        res = (None, f"could not load {data_dir}/{task}/test: {type(e).__name__}: {e}")
    _DATA_CACHE[key] = res
    return res


def status_sets(per_example):
    st = defaultdict(set)
    for r in per_example:
        st[r["status"]].add(r["example_id"])
    return st


# ----------------------------------------------------------------------------
# per-cell analysis
# ----------------------------------------------------------------------------
def picks_item_2(choice, target_is_2):
    """Which item a readout picked: 'deceptive' is the target item, 'honest' the distractor."""
    if choice == "deceptive":
        return target_is_2
    if choice == "honest":
        return not target_is_2
    return None     # 'other' / 'unknown': neither item


def positional(pe, recs, variants_pe):
    """Positional-default check: does the knockout just say item_2?

    A readout that always picks item_2 scores P(target = item_2) by construction,
    so a knockout accuracy near that base rate can be a position default rather
    than a content-driven flip.
    """
    rows = [r for r in pe if r["example_id"] < len(recs)
            and recs[r["example_id"]]["answer_item"] in ("item_1", "item_2")]
    n = len(rows)
    if not n:
        return None
    t2 = [recs[r["example_id"]]["answer_item"] == "item_2" for r in rows]
    ko2 = [picks_item_2(r["knockout_choice"], t) for r, t in zip(rows, t2)]
    base = sum(t2) / n
    k_ko2 = sum(1 for x in ko2 if x)
    p_ko2 = k_ko2 / n

    def cond(pos):
        sel = [x for x, t in zip(ko2, t2) if t == pos]
        return (sum(1 for x in sel if x) / len(sel)) if sel else float("nan")

    def stay(pos):
        st = [r["status"] for r, t in zip(rows, t2) if t == pos]
        k = st.count("stayed_deceptive")
        m = k + st.count("flipped_honest")
        return (k / m if m else float("nan")), m
    s1, n1 = stay(False)
    s2, n2 = stay(True)
    pval = binom_two_sided(k_ko2, n, base)
    gap = s2 - s1 if (s1 == s1 and s2 == s2) else float("nan")
    verdict = ("positional default" if abs(p_ko2 - base) >= POS_MARGIN and pval < POS_P
               and gap == gap and abs(gap) >= POS_GAP else "content-driven flip")
    out = {"n": n, "p_target_item_2": base, "always_item_2_accuracy": base,
           "p_ko_item_2": p_ko2, "p_ko_neither": sum(1 for x in ko2 if x is None) / n,
           "p_ko_item_2_given_target_1": cond(False), "p_ko_item_2_given_target_2": cond(True),
           "binom_p_vs_base": pval,
           "stay_rate_target_1": s1, "n_target_1": n1, "stay_rate_target_2": s2, "n_target_2": n2,
           "stay_gap_2_minus_1": gap, "verdict": verdict, "variants": {}}
    for vn, vpe in variants_pe.items():
        vr = [r for r in vpe if r["example_id"] < len(recs)
              and recs[r["example_id"]]["answer_item"] in ("item_1", "item_2")]
        if not vr:
            continue
        vt = [recs[r["example_id"]]["answer_item"] == "item_2" for r in vr]
        full2 = [picks_item_2(r["full_choice"], t) for r, t in zip(vr, vt)]
        ko2v = [picks_item_2(r["knockout_choice"], t) for r, t in zip(vr, vt)]

        def c2(xs, pos):
            sel = [x for x, t in zip(xs, vt) if t == pos]
            return (sum(1 for x in sel if x) / len(sel)) if sel else float("nan")
        kf = sum(1 for x in full2 if x)
        out["variants"][vn] = {
            "n": len(vr), "p_full_item_2": kf / len(vr),
            "binom_p_full_vs_base": binom_two_sided(kf, len(vr), sum(vt) / len(vr)),
            "p_full_item_2_given_target_1": c2(full2, False),
            "p_full_item_2_given_target_2": c2(full2, True),
            "p_ko_item_2": sum(1 for x in ko2v if x) / len(vr)}
    return out


def analyse_cell(cell, data_dir, rng):
    k = json.load(open(cell["path"]))
    task = k.get("task") or {}
    ko = task.get("knockout") or {}
    res = {"circuit": cell["circuit"], "task": cell["task"],
           "path": os.path.abspath(cell["path"]), "notes": []}

    # 1. headline + first-order null control ---------------------------------
    null_st = ((task.get("null") or {}).get("stats") or {}).get("accuracy")
    head = {"knockout_accuracy": ko.get("accuracy"),
            "circuit_accuracy": (task.get("circuit") or {}).get("accuracy"),
            "n": ko.get("n")}
    if null_st:
        head["null"] = {x: null_st.get(x) for x in
                        ("n", "mean", "std", "min", "max", "percentile", "z", "p_value", "discovered")}
        head["separable"] = separable(null_st)
    else:
        head["null"] = None
        head["separable"] = None
        res["notes"].append("no task-side null (task.null.stats.accuracy absent)")
    res["argmax_top"] = [{"token": t.get("token"), "id": t.get("id"), "count": t.get("count"),
                          "frac": t.get("frac")}
                         for t in ((ko.get("argmax") or {}).get("top") or [])]
    res["argmax_fracs"] = {x: (ko.get("argmax") or {}).get(x)
                           for x in ("target_frac", "distractor_frac", "other_frac")}
    res["headline"] = head
    pe = task.get("per_example")
    fs = task.get("flip_summary")
    if not pe:
        reason = task.get("flip_audit_reason") or "old-schema knockout.json (no task.per_example)"
        res["flip_audit"] = None
        res["notes"].append(f"no flip audit: {reason}")
        return res, None, None

    sets = status_sets(pe)
    stayed, flipped, other = sets["stayed_deceptive"], sets["flipped_honest"], sets["other"]
    head.update({"n_stayed": len(stayed), "n_flipped": len(flipped), "n_other": len(other),
                 "n_full_not_deceptive": (fs or {}).get("n_full_not_deceptive"),
                 "n_full_unknown": (fs or {}).get("n_full_unknown"),
                 "stay_rate": len(stayed) / max(1, len(stayed) + len(flipped))})
    if fs and (fs.get("n_stayed_deceptive") != len(stayed) or fs.get("n_flipped_honest") != len(flipped)):
        res["notes"].append("flip_summary counts disagree with per_example statuses; per_example used")
    res["flip_audit"] = True

    # 3. 'other' rows ----------------------------------------------------------
    oth = [r for r in pe if r["status"] == "other"]
    res["other"] = {
        "by_full_choice": dict(Counter(r["full_choice"] for r in oth)),
        "by_knockout_choice": dict(Counter(r["knockout_choice"] for r in oth)),
        "by_full_x_knockout": dict(Counter(f"{r['full_choice']}->{r['knockout_choice']}" for r in oth)),
    }

    # 4. prompt variants ---------------------------------------------------------
    res["variants"] = {}
    for vname, v in (k.get("variants") or {}).items():
        vpe = (v or {}).get("per_example")
        if not vpe:
            res["variants"][vname] = {"skipped": (v or {}).get("skipped")
                                      or (v or {}).get("flip_audit_reason") or "no per_example"}
            continue
        full_dec = {r["example_id"] for r in vpe if r["full_choice"] == "deceptive"}
        ko_dec = {r["example_id"] for r in vpe if r["knockout_choice"] == "deceptive"}
        n_all = len(vpe)

        def frac(group, s):
            return (len(group & s) / len(group)) if group else float("nan")
        res["variants"][vname] = {
            "n": n_all,
            "full_still_deceptive_rate_all": len(full_dec) / n_all,
            "full_still_deceptive_rate_stayed": frac(stayed, full_dec),
            "full_still_deceptive_rate_flipped": frac(flipped, full_dec),
            "p_stayed_vs_flipped": two_prop_p(len(stayed & full_dec), len(stayed),
                                              len(flipped & full_dec), len(flipped)),
            "knockout_deceptive_rate_stayed": frac(stayed, ko_dec),
            "knockout_deceptive_rate_flipped": frac(flipped, ko_dec),
            "overlap_stayed_vs_full_still_deceptive": overlap(stayed, full_dec, n_all),
            "headline": v.get("headline"),
        }

    # 2. field cuts ---------------------------------------------------------------
    hi_pe = ((k.get("variants") or {}).get("honest_instruction") or {}).get("per_example") or []
    priv = {"stayed": stayed, "flipped": flipped, "other": other,
            "excerpt": {r["example_id"]: r.get("prompt_excerpt") for r in pe},
            "hi_full_dec": {r["example_id"] for r in hi_pe if r["full_choice"] == "deceptive"}}
    recs, note = load_task_data(data_dir, cell["task"])
    res["fields"] = None
    res["rows_aligned"] = False
    if recs is None:
        res["notes"].append(f"field cuts skipped: {note}")
        return res, None, priv
    n_chk = sum(1 for r in pe if r.get("prompt_excerpt") is not None)
    n_ok = sum(1 for r in pe if r.get("prompt_excerpt") is not None and r["example_id"] < len(recs)
               and (recs[r["example_id"]].get("clean_prompt") or "")[-EXCERPT_CHARS:] == r["prompt_excerpt"])
    align = (n_ok / n_chk) if n_chk else None
    res["rows_aligned"] = align is None or align >= MIN_ALIGN
    res["alignment"] = {"n_rows": len(pe), "n_dataset": len(recs), "excerpt_match_rate": align}
    if len(pe) != len(recs):
        res["notes"].append(f"per_example has {len(pe)} rows but the {cell['task']} test set has {len(recs)}")
    if align is None:
        res["notes"].append("no prompt excerpts to check row alignment; assuming example_id == test row")
    elif align < MIN_ALIGN:
        res["notes"].append(f"field cuts skipped: only {align:.1%} of prompt excerpts match the "
                            f"{cell['task']} test set (dataset rebuilt since this cell ran?)")
        return res, None, priv
    res["positional"] = positional(
        pe, recs, {vn: (v or {}).get("per_example") for vn, v in (k.get("variants") or {}).items()
                   if (v or {}).get("per_example")})
    ids = [i for i in sorted(stayed | flipped) if i < len(recs)]
    y = np.array([1 if i in stayed else 0 for i in ids])
    overall = float(y.mean()) if len(y) else float("nan")
    res["overall_stay_rate"] = overall
    if not (len(y) and 0 < y.sum() < len(y)):
        res["notes"].append("field cuts not informative: the stayed or the flipped group is empty")
        return res, recs, priv
    fields, codes_by_field = {}, {}
    for f in CAT_FIELDS:
        vals = [str(recs[i].get(f)) for i in ids]
        levels = sorted(set(vals))
        code = {lv: j for j, lv in enumerate(levels)}
        codes = np.array([code[v] for v in vals])
        tot = np.bincount(codes, minlength=len(levels))
        s = np.bincount(codes, weights=y, minlength=len(levels))
        test = chi2_2xk(s, tot - s)
        if test:
            test["p_perm"] = perm_p_chi2(codes, y, len(levels), test["chi2"], rng)
        lv_rows = []
        for j, lv in enumerate(levels):
            n1, k1 = int(tot[j]), int(round(s[j]))
            rate = k1 / n1 if n1 else float("nan")
            flag = (n1 >= LEVEL_MIN_N and abs(rate - overall) >= LEVEL_MARGIN)
            lv_rows.append({"level": lv, "n": n1, "n_stayed": k1, "stay_rate": rate,
                            "p_vs_rest": two_prop_p(k1, n1, int(y.sum()) - k1, len(y) - n1),
                            "flag": bool(flag),
                            "direction": ("higher" if rate > overall else "lower") if flag else ""})
        fields[f] = {"n_levels": len(levels), "test": test, "levels": lv_rows}
        codes_by_field[f] = (codes, len(levels))
    hp = holm({f: ((fields[f]["test"] or {}).get("p_perm", float("nan"))) for f in fields})
    for f in fields:
        fields[f]["p_perm_holm"] = hp[f]
    # confound check: every other field, stratified on the strongest field
    ranked = sorted((f for f in fields if fields[f]["test"]),
                    key=lambda f: (fields[f]["test"]["p_perm"], fields[f]["test"]["p_chi2"]))
    res["strongest_field"] = ranked[0] if ranked else None
    if ranked:
        top = ranked[0]
        for f in ranked[1:]:
            codes, nl = codes_by_field[f]
            fields[f]["p_perm_given_strongest"] = perm_p_chi2_stratified(
                codes, y, nl, fields[f]["test"]["chi2"], codes_by_field[top][0], rng)
    nums = {}
    for f in NUM_FIELDS:
        xs = np.array([recs[i].get(f, float("nan")) for i in ids], float)
        ok = ~np.isnan(xs)
        nums[f] = mann_whitney(xs[ok & (y == 1)], xs[ok & (y == 0)])
    res["numeric"] = nums
    res["fields"] = fields
    return res, recs, priv


def analyse_suite(root, ablation, data_dir, rng):
    per_cell, privs, data = [], [], {}
    for cell in find_cells(root, ablation):
        res, recs, priv = analyse_cell(cell, data_dir, rng)
        per_cell.append(res)
        privs.append(priv)
        if recs is not None and res.get("rows_aligned"):
            data[cell["task"]] = recs
    return per_cell, privs, data


# ----------------------------------------------------------------------------
# cross-cell
# ----------------------------------------------------------------------------
def cross_cells(per_cell, privs, data):
    out = {"within_task": {}, "within_circuit": {}, "shared_field_rates": {}}
    by_task, by_circ = defaultdict(list), defaultdict(list)
    for c, p in zip(per_cell, privs):
        if p is not None:
            by_task[c["task"]].append((c, p))
            by_circ[c["circuit"]].append((c, p))
    # (a) same task, different circuits: example_id is the same test row
    for t, cs in by_task.items():
        n = cs[0][0]["headline"].get("n") or len(cs[0][1]["excerpt"])
        rows = [{"a": cs[i][0]["circuit"], "b": cs[j][0]["circuit"],
                 **overlap(cs[i][1]["stayed"], cs[j][1]["stayed"], n)}
                for i in range(len(cs)) for j in range(i + 1, len(cs))]
        allc = set.intersection(*[p["stayed"] for _, p in cs])
        out["within_task"][t] = {"pairs": rows, "n_stayed_in_all": len(allc), "n": n,
                                 "circuits": [c["circuit"] for c, _ in cs]}
    # (b) same circuit, different tasks: via instance_id
    for circ, cs in by_circ.items():
        rows = []
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                (ca, pa), (cb, pb) = cs[i], cs[j]
                ta, tb = ca["task"], cb["task"]
                da = data.get(ta) if ca.get("rows_aligned") else None
                db = data.get(tb) if cb.get("rows_aligned") else None
                if da is None or db is None:
                    rows.append({"a": ta, "b": tb, "skipped": "dataset not loaded or rows not aligned"})
                    continue
                ia = {da[x]["instance_id"]: x for x in range(len(da))}
                ib = {db[x]["instance_id"]: x for x in range(len(db))}
                shared = set(ia) & set(ib)
                sa = {iid for iid in shared if ia[iid] in pa["stayed"]}
                sb = {iid for iid in shared if ib[iid] in pb["stayed"]}
                row = {"a": ta, "b": tb, "n_shared_instances": len(shared)}
                if len(shared) >= 20:
                    row.update(overlap(sa, sb, len(shared)))
                else:
                    row["note"] = (f"only {len(shared)} instance_ids are shared by the {ta} and {tb} "
                                   f"test sets; per-instance overlap is not estimable")
                    row.update({"n_stayed_a_on_shared": len(sa), "n_stayed_b_on_shared": len(sb),
                                "n_both_stayed_on_shared": len(sa & sb)})
                rows.append(row)
        out["within_circuit"][circ] = rows
    # (b') same circuit, different tasks: through factor levels the tasks share
    for circ, cs in by_circ.items():
        per_field = {}
        for f in SHARED_FIELDS:
            rates = {}
            for c, _ in cs:
                fl = (c.get("fields") or {}).get(f)
                if fl:
                    rates[c["task"]] = {lv["level"]: (lv["stay_rate"], lv["n"]) for lv in fl["levels"]}
            tl = sorted(rates)
            pairs = []
            for i in range(len(tl)):
                for j in range(i + 1, len(tl)):
                    ra, rb = rates[tl[i]], rates[tl[j]]
                    common = [lv for lv in ra if lv in rb and ra[lv][1] >= 10 and rb[lv][1] >= 10]
                    pairs.append({"a": tl[i], "b": tl[j], "n_shared_levels": len(common),
                                  "spearman": spearman([ra[lv][0] for lv in common],
                                                       [rb[lv][0] for lv in common])})
            per_field[f] = pairs
        out["shared_field_rates"][circ] = per_field
    return out


def control_overlap(per_cell, privs, cper, cprivs):
    rows = []
    for c, p in zip(per_cell, privs):
        if p is None:
            continue
        for k, q in zip(cper, cprivs):
            if q is not None and k["task"] == c["task"]:
                n = c["headline"].get("n") or len(p["excerpt"])
                rows.append({"task": c["task"], "cell": c["circuit"], "control": k["circuit"],
                             **overlap(p["stayed"], q["stayed"], n)})
    return rows


def stubborn(per_cell, privs, data, exprs, top=10):
    out = {}
    by_task = defaultdict(list)
    for c, p in zip(per_cell, privs):
        if p is not None:
            by_task[c["task"]].append((c, p))
    for t, cs in by_task.items():
        delta = [(c, p) for c, p in cs if is_delta(c["circuit"], exprs)]
        basis = "delta cells" if delta else "cells (no delta cell identified, so all cells)"
        delta = delta or cs
        cnt, where, prior = Counter(), defaultdict(list), Counter()
        for c, p in delta:
            for i in p["stayed"]:
                cnt[i] += 1
                where[i].append(c["circuit"])
            for i in p.get("hi_full_dec", ()):
                prior[i] += 1
        aligned = all(c.get("rows_aligned") for c, _ in delta)
        recs = data.get(t) if aligned else None
        rows = []
        for i, m in sorted(cnt.items(), key=lambda kv: (-kv[1], -prior[kv[0]], kv[0]))[:top]:
            r = recs[i] if recs is not None and i < len(recs) else {}
            exc = r.get("clean_prompt") or next((p["excerpt"].get(i) for _, p in delta
                                                 if p["excerpt"].get(i)), "") or ""
            rows.append({"example_id": i, "n_cells_stayed": m, "of_cells": len(delta),
                         "n_cells_full_deceptive_under_honest_instruction": prior[i],
                         "pressure_id": r.get("pressure_id"), "pressure": r.get("pressure"),
                         "cells": where[i], "instance_id": r.get("instance_id"),
                         "pressure_slot": r.get("pressure_slot"),
                         "template_variant": r.get("template_variant"),
                         "item_pair": r.get("item_pair"), "answer_item": r.get("answer_item"),
                         "excerpt_tail": exc[-100:]})
        out[t] = {"basis": basis, "n_cells": len(delta),
                  "hist_n_cells_stayed": {str(x): v for x, v in sorted(Counter(cnt.values()).items())},
                  "top": rows}
    return out


# ----------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------
def f3(x, nd=3):
    if x is None:
        return "-"
    if isinstance(x, float):
        if x != x:
            return "nan"
        if math.isinf(x):
            return "inf" if x > 0 else "-inf"
        if 0 < abs(x) < 10 ** -nd:
            return f"{x:.1e}"
        return f"{x:.{nd}f}"
    return str(x)


def pfmt(p):
    if p is None or p != p:
        return "-"
    return f"{p:.1e}" if p < 1e-3 else f"{p:.3f}"


def cname(c):
    return f"{c['circuit']}/{c['task']}"


def sig_fields(c):
    """Fields that separate stayed from flipped: Holm perm p < ALPHA and V >= 0.1."""
    out = []
    for f, d in (c.get("fields") or {}).items():
        t = d.get("test")
        hp = d.get("p_perm_holm")
        if t and hp is not None and hp == hp and hp < ALPHA and t["cramers_v_corrected"] >= 0.1:
            out.append((f, d))
    return out


def positional_sentence(cells, label=""):
    pos = [c for c in cells if c.get("positional")]
    if not pos:
        return ("Positional default: not assessed (no cell has aligned test records).")
    pd = [c for c in pos if c["positional"]["verdict"] == "positional default"]
    def one(c):
        q = c["positional"]
        return (f"{cname(c)} picks item_2 {q['p_ko_item_2']:.2f} vs base {q['p_target_item_2']:.2f}, "
                f"stay-rate {q['stay_rate_target_1']:.2f}/{q['stay_rate_target_2']:.2f} for target "
                f"item_1/item_2")
    txt = (f"Positional default{label}: {len(pd)}/{len(pos)} cells collapse toward one answer position "
           f"regardless of content"
           + (f" ({'; '.join(one(c) for c in pd)})" if pd else ""))
    if pd:
        txt += (". In these cells the knockout's accuracy is largely a position artefact: an always-item_2 "
                "responder scores P(target = item_2) by construction, so a partial accuracy near that base "
                "rate is not evidence of partial necessity")
    rest = [c for c in pos if c["positional"]["verdict"] != "positional default"]
    if rest:
        txt += (f". The other {len(rest)} are content-driven flips by this test (|P(item_2) - base| < "
                f"{POS_MARGIN} or binomial p >= {POS_P}, or stay-rate gap < {POS_GAP})")
    return txt + "."


def summary_paragraph(per_cell, cross, ctrl_rows):
    s = []
    audited = [c for c in per_cell if c.get("flip_audit")]
    no_audit = [c for c in per_cell if not c.get("flip_audit")]
    if not per_cell:
        return "No cells were found under this suite root, so there is nothing to diagnose."
    if not audited:
        return (f"None of the {len(per_cell)} cells carries a per-example flip audit (old-schema "
                f"knockout.json), so stayed-vs-flipped composition cannot be analysed. Knockout "
                f"accuracies are listed below for reference.")
    s.append(f"{len(audited)} of {len(per_cell)} cells carry a flip audit"
             + (f" ({len(no_audit)} without one skipped: {', '.join(cname(c) for c in no_audit)})"
                if no_audit else "") + ".")
    s.append("Stayed deceptive, of stayed+flipped: " + ", ".join(
        f"{cname(c)} {c['headline']['n_stayed']}/{c['headline']['n_stayed'] + c['headline']['n_flipped']}"
        for c in audited) + ".")
    sep = [c for c in audited if c["headline"].get("separable")]
    nonsep = [c for c in audited if c["headline"].get("separable") is False]
    nonull = [c for c in audited if c["headline"].get("separable") is None]
    if sep or nonsep:
        s.append(f"First-order control: {len(sep)} knockout(s) are separable from a random knockout of the "
                 f"same size and {len(nonsep)} are not"
                 + (f" ({', '.join(cname(c) for c in nonsep)})" if nonsep else "")
                 + (". For the non-separable cells a random circuit of the same size removes the deception "
                    "about as well, so their stayed/flipped split may reflect knockout size rather than "
                    "this circuit; read their patterns with caution." if nonsep else "."))
    if nonull:
        s.append(f"{len(nonull)} cell(s) have no task-side null.")
    s.append(positional_sentence(audited))
    with_fields = [c for c in audited if c.get("fields")]
    if with_fields:
        hits = defaultdict(list)
        for c in with_fields:
            for f, d in sig_fields(c):
                hi = [lv["level"] for lv in sorted(d["levels"], key=lambda z: -z["stay_rate"])
                      if lv["flag"] and lv["direction"] == "higher"]
                hits[f].append((c, d, hi))
        if hits:
            parts = []
            for f, lst in sorted(hits.items(), key=lambda kv: -len(kv[1])):
                parts.append(f"{f} in {len(lst)}/{len(with_fields)} cells ("
                             + "; ".join(f"{cname(c)}: "
                                         + (f"stay-rate elevated in {','.join(hi[:5])}, " if hi else "")
                                         + f"Holm p={pfmt(d['p_perm_holm'])}, corrected V={d['test']['cramers_v_corrected']:.2f}"
                                         for c, d, hi in lst) + ")")
            s.append("Fields that separate stayed from flipped (Holm-adjusted permutation p < 0.05 and "
                     "bias-corrected Cramér's V >= 0.1): " + " | ".join(parts) + ".")
            conf = []
            for c in with_fields:
                for f, d in sig_fields(c):
                    pg = d.get("p_perm_given_strongest")
                    if pg is not None and pg >= ALPHA:
                        conf.append(f"{f} in {cname(c)} (p={pfmt(pg)} given {c['strongest_field']})")
            if conf:
                s.append("Some of these are explained by the strongest field of their cell: holding that "
                         "field's levels fixed, they no longer separate stayed from flipped: "
                         + "; ".join(conf) + ".")
            quiet = [c for c in with_fields if not sig_fields(c)]
            if quiet:
                s.append(f"No field passes that bar in {', '.join(cname(c) for c in quiet)}.")
        else:
            s.append(f"No categorical field separates stayed from flipped in any of the {len(with_fields)} "
                     f"cells with field cuts (all Holm-adjusted permutation p >= 0.05 or corrected V < 0.1).")
        num_hits = []
        for c in with_fields:
            for f, m in (c.get("numeric") or {}).items():
                if m and m["p"] < ALPHA / len(NUM_FIELDS) and abs(m["rank_biserial"]) >= 0.2:
                    num_hits.append(f"{f} in {cname(c)} (AUC={m['auc']:.2f}, p={pfmt(m['p'])})")
        s.append(("Numeric cuts with |rank-biserial| >= 0.2 and Bonferroni p < 0.05: " + "; ".join(num_hits) + ".")
                 if num_hits else "No numeric cut (prompt length, target position, prior/clean/corrupt "
                                  "margin) reaches |rank-biserial| >= 0.2 with Bonferroni p < 0.05.")
    skipped = [c for c in audited if not c.get("fields")]
    if skipped:
        s.append(f"Field cuts were skipped for {', '.join(cname(c) for c in skipped)}; see the cell notes.")
    for vname in ("honest_instruction", "no_pressure"):
        vv = [(c, c["variants"][vname]) for c in audited
              if vname in (c.get("variants") or {}) and "skipped" not in c["variants"][vname]
              and c["variants"][vname]["full_still_deceptive_rate_stayed"] == c["variants"][vname]["full_still_deceptive_rate_stayed"]
              and c["variants"][vname]["full_still_deceptive_rate_flipped"] == c["variants"][vname]["full_still_deceptive_rate_flipped"]]
        if not vv:
            continue
        pos = [c for c, v in vv if v["full_still_deceptive_rate_stayed"] > v["full_still_deceptive_rate_flipped"]
               and v["p_stayed_vs_flipped"] < ALPHA]
        s.append(f"Under {vname} the full model still answers deceptively on "
                 + ", ".join(f"{v['full_still_deceptive_rate_stayed']:.0%} of stayed vs "
                             f"{v['full_still_deceptive_rate_flipped']:.0%} of flipped ({cname(c)})" for c, v in vv)
                 + f"; the stayed group is significantly more often still deceptive under this variant (p < 0.05) in "
                   f"{len(pos)}/{len(vv)} cells"
                 + (", consistent with part of the stubbornness being a property of the example (a prior "
                    "toward the deceptive answer) rather than of the circuit." if 2 * len(pos) > len(vv) else
                    ", which is weak evidence at most that stubbornness is an example-level prior here." if pos else
                    ", so there is no evidence here that stubbornness is an example-level prior."))
    ov = []
    for t, d in cross.get("within_task", {}).items():
        for p in d["pairs"]:
            if p["union"]:
                ov.append(f"{t} {p['a']}~{p['b']} J={p['jaccard']:.2f} vs {p['expected_jaccard']:.2f} "
                          f"size-matched random (p={pfmt(p['p_overlap_ge'])})")
    if ov:
        s.append("Stayed sets across circuits on the same task: " + "; ".join(ov) + ".")
    tiny = sorted({(r["a"], r["b"], r["n_shared_instances"])
                   for rows in cross.get("within_circuit", {}).values() for r in rows if "note" in r})
    if tiny:
        s.append("Cross-task per-instance overlap is not estimable because the test sets share only "
                 + ", ".join(f"{a}/{b}: {n}" for a, b, n in tiny)
                 + " instance_ids; the per-level stay-rate correlations on shared factors stand in for it.")
    if ctrl_rows:
        mx = max(r["intersection"] for r in ctrl_rows)
        nctl = max(r["n_b"] for r in ctrl_rows)
        if nctl <= 20:
            s.append(f"The control suite's knockouts flip almost everything (at most {nctl} stayed per cell), "
                     f"so overlap with its stayed sets is near-empty by construction (max intersection {mx}).")
        else:
            s.append(f"Overlap with the control suite's stayed sets reaches at most {mx} examples; see the "
                     f"control table for size-matched expectations.")
    return " ".join(s)


def positional_table(cells):
    L = ["| circuit | task | P(target=item_2) = always-item_2 acc | KO acc | P(KO item_2) | binom p | "
         "P(KO item_2 given t=item_1) | P(KO item_2 given t=item_2) | KO neither | stay given t=item_1 (n) | "
         "stay given t=item_2 (n) | full item_2: honest_instr. | full item_2: no_pressure | verdict |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in cells:
        q = c.get("positional")
        if not q:
            why = "no flip audit" if not c.get("flip_audit") else "test records not loaded or not aligned"
            L.append(f"| {c['circuit']} | {c['task']} | - | {f3(c['headline'].get('knockout_accuracy'))} | "
                     f"- | - | - | - | - | - | - | - | - | n/a ({why}) |")
            continue
        v = q.get("variants", {})
        def vf(name):
            x = v.get(name)
            return (f"{f3(x['p_full_item_2'])} (p={pfmt(x['binom_p_full_vs_base'])})" if x else "-")
        L.append(f"| {c['circuit']} | {c['task']} | {f3(q['p_target_item_2'])} | "
                 f"{f3(c['headline'].get('knockout_accuracy'))} | {f3(q['p_ko_item_2'])} | {pfmt(q['binom_p_vs_base'])} | "
                 f"{f3(q['p_ko_item_2_given_target_1'])} | {f3(q['p_ko_item_2_given_target_2'])} | "
                 f"{f3(q['p_ko_neither'])} | {f3(q['stay_rate_target_1'])} ({q['n_target_1']}) | "
                 f"{f3(q['stay_rate_target_2'])} ({q['n_target_2']}) | {vf('honest_instruction')} | "
                 f"{vf('no_pressure')} | {q['verdict']} |")
    return L


POSITIONAL_NOTE = (
    "Item picked: knockout_choice 'deceptive' is the target item, 'honest' the distractor, 'other' neither "
    "(counted as not item_2). Target position is target == item_2 in the test record. An always-item_2 "
    "responder's accuracy equals P(target = item_2). binom p is the exact two-sided binomial test of "
    "P(KO item_2) against that base rate. Stay-rates are stayed / (stayed + flipped) within each target "
    "position. The full-model columns give P(full picks item_2) on the variant prompts, with its binomial p "
    "against the base rate, to show whether the model's own honest answer has a position bias. Verdict: "
    f"'positional default' when |P(KO item_2) - base| >= {POS_MARGIN}, binom p < {POS_P} and the stay-rate "
    f"gap between target positions is >= {POS_GAP}; otherwise 'content-driven flip'.\n")


def md_report(root, ablation, per_cell, cross, stub, ctrl, ctrl_rows, summary):
    L = ["## Flip audit diagnosis\n", summary + "\n"]
    L.append(f"Suite `{os.path.abspath(root)}`, ablation `{ablation}`. Stayed means the full model and the "
             f"knockout both pick the deceptive answer at the prediction-position argmax. Flipped means the "
             f"knockout picks the honest answer, and other means neither. Composition tests compare stayed "
             f"with flipped only. p_perm is a {N_PERM}-draw permutation chi-square p-value, which is robust to "
             f"sparse levels, Holm-adjusted across the {len(CAT_FIELDS)} fields of a cell. V is Cramér's V and "
             f"V corr. its bias-corrected form, which does not inflate with the number of levels (entity has 72). "
             f"A level is flagged when n >= {LEVEL_MIN_N} and its stay-rate differs from the cell's by >= "
             f"{LEVEL_MARGIN}. In the variant tables, full_choice is the FULL model's argmax on the variant "
             f"prompt, because knockout.py runs the variants with ref_cache=None.\n")

    L.append("### Headline and null control\n")
    L.append("| circuit | task | KO acc | stayed | flipped | other | full not dec. | stay-rate | "
             "null mean ± sd | pct | z | separable |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in per_cell:
        h = c["headline"]
        nl = h.get("null") or {}
        tail = (f"{f3(nl.get('mean'))} ± {f3(nl.get('std'))} | {f3(nl.get('percentile'), 1)} | "
                f"{f3(nl.get('z'), 2)} | {'yes' if h.get('separable') else 'no'} |") if nl else "- | - | - | n/a |"
        L.append(f"| {c['circuit']} | {c['task']} | {f3(h.get('knockout_accuracy'))} | {h.get('n_stayed', '-')} | "
                 f"{h.get('n_flipped', '-')} | {h.get('n_other', '-')} | {h.get('n_full_not_deceptive', '-')} | "
                 f"{f3(h.get('stay_rate'))} | " + tail)
    L.append("")
    L.append("### Positional default\n")
    L.append(POSITIONAL_NOTE)
    L.extend(positional_table(per_cell))
    L.append("")

    for c in per_cell:
        L.append(f"### {c['circuit']} / {c['task']}\n")
        for n in c.get("notes", []):
            L.append(f"- Note: {n}")
        if c.get("notes"):
            L.append("")
        top = c.get("argmax_top") or []
        if top:
            fr = c.get("argmax_fracs") or {}
            L.append(f"Knockout argmax fractions: target {f3(fr.get('target_frac'))}, distractor "
                     f"{f3(fr.get('distractor_frac'))}, other {f3(fr.get('other_frac'))}. Top tokens: "
                     + ", ".join(f"`{t['token']!s}` {t['count']}" for t in top[:8]) + ".\n")
        if not c.get("flip_audit"):
            continue
        o = c.get("other") or {}
        L.append(("'other' rows by full -> knockout choice: "
                  + ", ".join(f"{x} {v}" for x, v in sorted(o["by_full_x_knockout"].items())) + ".\n")
                 if o.get("by_full_x_knockout") else "No 'other' rows.\n")
        al = c.get("alignment")
        if al:
            L.append(f"Row alignment: {al['n_rows']} audit rows, {al['n_dataset']} test records, prompt-excerpt "
                     f"match rate {f3(al['excerpt_match_rate'])}.\n")
        if c.get("fields"):
            L.append(f"Overall stay-rate {f3(c.get('overall_stay_rate'))}. 'p given strongest' re-runs the "
                     f"permutation test with the stay labels shuffled only within levels of "
                     f"{c.get('strongest_field')}, the field with the smallest p; a field that loses its "
                     f"signal there is confounded with it.\n")
            L.append("| field | levels | chi2 | dof | p_chi2 | p_perm | p_perm Holm | p given strongest | V | V corr. | exp<5 | "
                     "flagged levels: stay-rate (n) |")
            L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
            for f, d in c["fields"].items():
                t = d["test"]
                fl = "; ".join(f"{lv['level']} {lv['stay_rate']:.2f} ({lv['n']})"
                               for lv in sorted(d["levels"], key=lambda z: -z["stay_rate"]) if lv["flag"])
                if t:
                    L.append(f"| {f} | {d['n_levels']} | {t['chi2']:.1f} | {t['dof']} | {pfmt(t['p_chi2'])} | "
                             f"{pfmt(t['p_perm'])} | {pfmt(d['p_perm_holm'])} | "
                             f"{'strongest' if f == c.get('strongest_field') else pfmt(d.get('p_perm_given_strongest'))} | "
                             f"{t['cramers_v']:.3f} | {f3(t['cramers_v_corrected'])} | "
                             f"{t['frac_expected_lt5']:.2f} | {fl or '-'} |")
                else:
                    L.append(f"| {f} | {d['n_levels']} | - | - | - | - | - | - | - | - | - | single level |")
            L.append("")
            L.append("| numeric cut | mean stayed | mean flipped | AUC | rank-biserial | p |")
            L.append("|---|---|---|---|---|---|")
            for f, m in (c.get("numeric") or {}).items():
                if m:
                    L.append(f"| {f} | {f3(m['mean_stayed'])} | {f3(m['mean_flipped'])} | {f3(m['auc'])} | "
                             f"{f3(m['rank_biserial'])} | {pfmt(m['p'])} |")
            L.append("")
        vv = c.get("variants") or {}
        if vv:
            L.append("| variant | full still dec.: all | stayed | flipped | p | KO dec.: stayed | flipped | "
                     "Jaccard(stayed, full still dec.) | random J | overlap p |")
            L.append("|---|---|---|---|---|---|---|---|---|---|")
            for vn, v in vv.items():
                if "skipped" in v:
                    L.append(f"| {vn} | skipped: {v['skipped']} | | | | | | | | |")
                    continue
                ov = v["overlap_stayed_vs_full_still_deceptive"]
                L.append(f"| {vn} | {f3(v['full_still_deceptive_rate_all'])} | "
                         f"{f3(v['full_still_deceptive_rate_stayed'])} | {f3(v['full_still_deceptive_rate_flipped'])} | "
                         f"{pfmt(v['p_stayed_vs_flipped'])} | {f3(v['knockout_deceptive_rate_stayed'])} | "
                         f"{f3(v['knockout_deceptive_rate_flipped'])} | {f3(ov['jaccard'])} | "
                         f"{f3(ov['expected_jaccard'])} | {pfmt(ov['p_overlap_ge'])} |")
            L.append("")

    L.append("### Cross-cell overlap\n")
    L.append("Stayed sets across circuits on the same task, matched by example_id. Random is the size-matched "
             "expectation |A||B|/n, and p is the hypergeometric P(intersection >= observed).\n")
    L.append("| task | A | B | size A | size B | A∩B | expected A∩B | Jaccard | random J | p |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for t, d in cross["within_task"].items():
        for p in d["pairs"]:
            L.append(f"| {t} | {p['a']} | {p['b']} | {p['n_a']} | {p['n_b']} | {p['intersection']} | "
                     f"{f3(p['expected_intersection'], 1)} | {f3(p['jaccard'])} | {f3(p['expected_jaccard'])} | "
                     f"{pfmt(p['p_overlap_ge'])} |")
        L.append(f"| {t} | stayed in all {len(d['circuits'])} | | | | {d['n_stayed_in_all']} | | | | |")
    L.append("")
    L.append("Same circuit across tasks, matched by instance_id.\n")
    L.append("| circuit | task A | task B | shared instances | result |")
    L.append("|---|---|---|---|---|")
    for circ, rows in cross["within_circuit"].items():
        for r in rows:
            if "skipped" in r:
                res = r["skipped"]
            elif "note" in r:
                res = (f"not estimable; on the shared ids stayed A={r['n_stayed_a_on_shared']}, "
                       f"B={r['n_stayed_b_on_shared']}, both={r['n_both_stayed_on_shared']}")
            else:
                res = (f"J={f3(r['jaccard'])} (random {f3(r['expected_jaccard'])}), A∩B={r['intersection']}, "
                       f"p={pfmt(r['p_overlap_ge'])}")
            L.append(f"| {circ} | {r['a']} | {r['b']} | {r.get('n_shared_instances', '-')} | {res} |")
    L.append("")
    L.append("Same circuit across tasks, through factor levels the tasks share: Spearman correlation of "
             "per-level stay-rates over levels with n >= 10 in both tasks.\n")
    L.append("| circuit | field | task A | task B | shared levels | Spearman |")
    L.append("|---|---|---|---|---|---|")
    for circ, per_f in cross["shared_field_rates"].items():
        for f, pairs in per_f.items():
            for p in pairs:
                L.append(f"| {circ} | {f} | {p['a']} | {p['b']} | {p['n_shared_levels']} | {f3(p['spearman'])} |")
    L.append("")

    if ctrl is not None:
        L.append(f"### Control suite\n\n`{os.path.abspath(ctrl['root'])}`\n")
        L.append("| circuit | task | KO acc | stayed | flipped | other | separable |")
        L.append("|---|---|---|---|---|---|---|")
        for c in ctrl["cells"]:
            h = c["headline"]
            L.append(f"| {c['circuit']} | {c['task']} | {f3(h.get('knockout_accuracy'))} | {h.get('n_stayed', '-')} | "
                     f"{h.get('n_flipped', '-')} | {h.get('n_other', '-')} | "
                     f"{'n/a' if h.get('separable') is None else 'yes' if h.get('separable') else 'no'} |")
        L.append("")
        L.append("Positional default in the control suite (same columns as above).\n")
        L.extend(positional_table(ctrl["cells"]))
        L.append("")
        L.append(positional_sentence(ctrl["cells"], " (control)") + "\n")
        if ctrl["cross"]["within_task"]:
            L.append("Control stayed-set overlap across circuits on the same task.\n")
            L.append("| task | A | B | A∩B | Jaccard | random J | p |")
            L.append("|---|---|---|---|---|---|---|")
            for t, d in ctrl["cross"]["within_task"].items():
                for p in d["pairs"]:
                    L.append(f"| {t} | {p['a']} | {p['b']} | {p['intersection']} | {f3(p['jaccard'])} | "
                             f"{f3(p['expected_jaccard'])} | {pfmt(p['p_overlap_ge'])} |")
            L.append("")
        L.append("Overlap of each cell's stayed set with the control's stayed set on the same task.\n")
        L.append("| task | cell | control | size cell | size control | ∩ | expected ∩ | Jaccard | p |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for r in ctrl_rows:
            L.append(f"| {r['task']} | {r['cell']} | {r['control']} | {r['n_a']} | {r['n_b']} | {r['intersection']} | "
                     f"{f3(r['expected_intersection'], 1)} | {f3(r['jaccard'])} | {pfmt(r['p_overlap_ge'])} |")
        if not ctrl_rows:
            L.append("| - | no control cell with a flip audit on a matching task | | | | | | | |")
        L.append("")

    L.append("### Most stubborn examples\n")
    if not stub:
        L.append("No cell has a flip audit.\n")
    for t, d in stub.items():
        L.append(f"**{t}**, counted over {d['n_cells']} {d['basis']}. Ties are broken by the number of those "
                 f"cells in which the full model still answers deceptively under honest_instruction. Number of "
                 f"examples by how many cells they stayed in: " + ", ".join(f"{x} cells: {v}" for x, v in d["hist_n_cells_stayed"].items())
                 + ".\n")
        L.append("| example | cells | full dec. under honest instr. | instance_id | pressure_slot | template | "
                 "item_pair | target position | pressure clause (60 chars) | prompt tail |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in d["top"]:
            tail = (r["excerpt_tail"] or "").replace("\n", "\\n").replace("|", "\\|").replace("`", "'")
            pr = (r.get("pressure") or "")[:60].replace("|", "\\|").replace("`", "'")
            L.append(f"| {r['example_id']} | {r['n_cells_stayed']}/{r['of_cells']} | "
                     f"{r['n_cells_full_deceptive_under_honest_instruction']}/{r['of_cells']} | {r['instance_id'] or '-'} | "
                     f"{r['pressure_slot'] or '-'} | {r['template_variant'] or '-'} | {r['item_pair'] or '-'} | "
                     f"{r['answer_item'] or '-'} | {pr or '-'} | `{tail}` |")
        L.append("")
    return "\n".join(L) + "\n"


def clean_json(x):
    if isinstance(x, dict):
        return {k: clean_json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean_json(v) for v in x]
    if isinstance(x, set):
        return sorted(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        x = float(x)
        return None if (x != x or math.isinf(x)) else x
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pattern analysis of knockout flip audits across a suite.")
    ap.add_argument("suite_root")
    ap.add_argument("--ablation", default="interchange")
    ap.add_argument("--control", default=None, help="another suite root, e.g. the atomic-circuit suite")
    ap.add_argument("--data-dir", default="data/datasets")
    ap.add_argument("--out-json", default=None)
    ap.add_argument("--out-md", default=None)
    a = ap.parse_args(argv)
    root = a.suite_root.rstrip("/")
    if not os.path.isdir(os.path.join(root, "cells")):
        sys.exit(f"{root}/cells does not exist. Run merge_shards.py first, or pass a suite root whose "
                 f"cells/<circuit>/<task>/{a.ablation}/knockout.json are in place.")
    rng = np.random.default_rng(SEED)
    exprs = suite_exprs(root)
    per_cell, privs, data = analyse_suite(root, a.ablation, a.data_dir, rng)
    if not per_cell:
        print(f"warning: no cells/*/*/{a.ablation}/knockout.json under {root}", file=sys.stderr)
    cross = cross_cells(per_cell, privs, data)
    stub = stubborn(per_cell, privs, data, exprs)
    ctrl, ctrl_rows = None, []
    if a.control:
        croot = a.control.rstrip("/")
        if not os.path.isdir(os.path.join(croot, "cells")):
            print(f"warning: control {croot} has no cells/; skipped", file=sys.stderr)
        else:
            cper, cprivs, cdata = analyse_suite(croot, a.ablation, a.data_dir, rng)
            ctrl = {"root": croot, "cells": cper, "cross": cross_cells(cper, cprivs, cdata)}
            ctrl_rows = control_overlap(per_cell, privs, cper, cprivs)
    summary = summary_paragraph(per_cell, cross, ctrl_rows)
    out_json = a.out_json or os.path.join(root, "flip_audit.json")
    out_md = a.out_md or os.path.join(root, "flip_audit.md")
    payload = {"suite_root": os.path.abspath(root), "ablation": a.ablation, "data_dir": a.data_dir,
               "control_root": os.path.abspath(a.control) if a.control else None,
               "settings": {"level_min_n": LEVEL_MIN_N, "level_margin": LEVEL_MARGIN, "n_perm": N_PERM,
                            "alpha": ALPHA, "min_excerpt_alignment": MIN_ALIGN,
                            "separable_rule": "pct <= 5 and z <= -2, or strict difference when sd < 1e-6"},
               "summary": summary, "cells": per_cell, "cross": cross, "stubborn": stub,
               "control": ctrl, "control_overlap": ctrl_rows}
    with open(out_json, "w") as fh:
        json.dump(clean_json(payload), fh, indent=1)
    with open(out_md, "w") as fh:
        fh.write(md_report(root, a.ablation, per_cell, cross, stub, ctrl, ctrl_rows, summary))
    print(f"wrote {out_json}\nwrote {out_md}")
    print(summary)


if __name__ == "__main__":
    main()
