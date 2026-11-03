#!/usr/bin/env python
"""
scripts/neuron_partition_verdict.py — the item-10 N1 and N2 verdicts from neuron-set ablation cells (CPU only).

neuron-partition, `docs/research/neuron-partition/spec.md` item 10 with rulings R2 (margin effect primary, rate
secondary), R6 (classes and the k ladder), R7 (collateral under the mean reference), R8 (the rate under mean and zero
is ablated D against ablated H) and R10 (the halves are halves of the seed-2 test sample).

Input: one or more cells written by `scripts/neuron_set_ablation.py` (`--cell DIR`, repeatable, normally one per k).
Each holds `summary.json` and `rows.jsonl`: one line per (reference, set, condition, instance id) with both streams'
margins in D orientation (m = logit(opposite) - logit(honest)), the twin's intact margin read in D's batch, the
argmax tokens and the condition-correct token. Every number here is recomputed from those per-id lines, so the
halves and the bootstrap use exactly the whole-sample definitions, which mirror W2's functions (`stream_average`,
`share`, `ladder_ratio`, `removed_fraction`, `effect_metrics`, `condition_metrics`): streams are averaged within an
id, then ids are averaged.

Sets: tested sets are named by class (`D_only`, `DI_shared`, `H_only`, `all_shared`, or `<class>_<k>`); their
matched nulls are `null_<class>_<k>_<i>`. The k of a tested set comes from its nulls (else from a `_<k>` suffix).

Per set, reference and id subset (whole sample, half 1, half 2):

* D removed, margin (primary, R2): G = mean_ids(m_D intact - m_twin intact), removed = mean_ids(m_D intact -
  m_D ablated) / G; None unless G > epsilon = max(1e-6, 10 x the cell's self-replay error for D).
* D removed, rate (R8): twin reference, (e_int - e_abl) / e_int with e = p(m_D >= 0.7) - p(m_twin intact >= 0.7);
  mean and zero, e_int = p(D intact) - p(H intact), e_abl = p(D ablated) - p(H ablated) on ids D and H share.
* I removed, margin and rate, the same with I and the user-neutral twin N.
* H, F and IOI accuracy shift in points (full-vocabulary argmax on the condition-correct token, ablated minus intact).
  The collateral bars use the mean reference for every reference (R7); the twin reference's own H line is the
  reverse patch and is descriptive.
* The matched null: every metric over the set's `null_<class>_<k>_<i>` groups on the same ids, with its 5th, 50th
  and 95th percentile (numpy linear interpolation).

N1 (item 10), per class, k and reference, on each subset: size <= 2,000; D removed (margin) >= 0.50; I removed
(margin) < 0.25; |H|, |F| and |IOI| shift (mean reference) < 5 points; D removed (margin) above the null's 95th
percentile. The N1 pass is read on D_only: every bar under the twin and the mean reference, on the whole sample and
on both halves. A missing value fails its bar and says why. Any (reference, subset) that meets every bar without the
whole pass is a lead.

N2 (item 10), for H_only, per reference (mean decides; zero beside it; twin is the descriptive reverse patch):
bypass = H accuracy shift <= -20 points and |D's deceptive-rate change| < 5 points and the null's 95th percentile of
|H shift| < 5 points; suppression or shared = H shift <= -20 and D's rate change <= -10 points; else undetermined.

Halves (R10): the union of the sample's D and I ids is split by `scripts/neuron_partition_data.split_halves` (W3's
rank-half rule: stratified by pressure_id, seed 2, alternation within sorted clusters), with pressure_id read from
the far_v2 and I-pool test splits. H and F take their D id's half, N its I id's half. IOI is not in the sample, so all
IOI rows enter both halves. When the records cannot be read, the fallback is a seeded shuffle of the sorted ids,
alternated; the method used is recorded.

Bootstrap: 1,000 resamples of ids with replacement (seed 2), tested sets only, 2.5th and 97.5th percentiles, for D
and I removed (margin and rate).

Outputs in `--output-dir`: `verdict.json` and `verdict.md`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CLASSES = ("D_only", "DI_shared", "H_only", "all_shared")
REFERENCES = ("twin", "mean", "zero")
STREAMS = ("clean", "corrupt")
TWIN_OF = {"D": "H", "I": "N"}
IOI = "IOI"
MARGIN = 0.7
MAX_SIZE = 2000
D_BAR, I_BAR, COLLATERAL_BAR = 0.50, 0.25, 5.0
N2_H_DROP, N2_D_STILL, N2_D_FALL, N2_NULL_H = -20.0, 5.0, -10.0, 5.0
SEED = 2
N_BOOT = 1000
NULL_RE = re.compile(r"^null_(?P<cls>.+)_(?P<k>\d+)_(?P<i>\d+)$")
SUBSETS = ("whole", "half1", "half2")

DEFAULT_SAMPLE = os.path.join(ROOT, "outputs", "_analyses", "neuron-partition", "data", "far_test_sample_seed2.json")
DEFAULT_D_DIR = os.path.join(ROOT, "data", "datasets", "far_v2")
DEFAULT_I_DIR = os.path.join(ROOT, "outputs", "_analyses", "neuron-partition", "data", "pools",
                             "far_v2_user_inversion")


# ==============================================================================
# LOADING A CELL
# ==============================================================================

class Block:
    """One (reference, set, condition): per-id arrays [n_ids, n_streams], NaN where absent."""

    __slots__ = ("m_int", "m_abl", "twin", "ok_int", "ok_abl")

    def __init__(self, n: int, s: int):
        self.m_int = np.full((n, s), np.nan)
        self.m_abl = np.full((n, s), np.nan)
        self.twin = np.full((n, s), np.nan)
        self.ok_int = np.full((n, s), np.nan)
        self.ok_abl = np.full((n, s), np.nan)


class Cell:
    """Every line of one ablation cell, indexed by condition id order."""

    def __init__(self, directory: str):
        self.directory = os.path.abspath(directory)
        with open(os.path.join(directory, "summary.json")) as handle:
            self.summary = json.load(handle)
        lines = []
        ids: Dict[str, set] = {}
        streams: Dict[str, set] = {}
        with open(os.path.join(directory, "rows.jsonl")) as handle:
            for text in handle:
                if not text.strip():
                    continue
                line = json.loads(text)
                if line.get("header"):
                    continue
                lines.append(line)
                cond = line["condition"]
                ids.setdefault(cond, set()).add(line["instance_id"])
                streams.setdefault(cond, set()).update(line["m_intact"])
        self.ids = {c: sorted(v) for c, v in ids.items()}
        self.index = {c: {one: i for i, one in enumerate(v)} for c, v in self.ids.items()}
        self.streams = {c: [s for s in STREAMS if s in v] + sorted(v - set(STREAMS)) for c, v in streams.items()}
        self.blocks: Dict[Tuple[str, str, str], Block] = {}
        for line in lines:
            ref, name, cond = line["reference"], line["set"], line["condition"]
            key = (ref, name, cond)
            block = self.blocks.get(key)
            if block is None:
                block = self.blocks[key] = Block(len(self.ids[cond]), len(self.streams[cond]))
            row = self.index[cond][line["instance_id"]]
            for j, stream in enumerate(self.streams[cond]):
                if stream not in line["m_intact"]:
                    continue
                block.m_int[row, j] = _num(line["m_intact"].get(stream))
                block.m_abl[row, j] = _num(line["m_ablated"].get(stream))
                block.twin[row, j] = _num((line.get("twin_m_intact") or {}).get(stream))
                correct = (line.get("correct_token") or {}).get(stream)
                a_int = (line.get("argmax_intact") or {}).get(stream)
                a_abl = (line.get("argmax_ablated") or {}).get(stream)
                if correct is not None and a_int is not None:
                    block.ok_int[row, j] = float(a_int == correct)
                if correct is not None and a_abl is not None:
                    block.ok_abl[row, j] = float(a_abl == correct)
        self.sets = sorted({name for (_r, name, _c) in self.blocks})
        self.references = [r for r in REFERENCES if any(k[0] == r for k in self.blocks)]
        self.replay = self.summary.get("self_replay_error") or {}

    def epsilon(self, condition: str) -> float:
        return max(1e-6, 10.0 * float(self.replay.get(condition) or 0.0))

    def size(self, name: str) -> Optional[int]:
        entry = (self.summary.get("sets") or {}).get(name) or {}
        return entry.get("size")

    def block(self, ref, name, cond) -> Optional[Block]:
        return self.blocks.get((ref, name, cond))

    def rows_of(self, cond: str, keep: Optional[set]) -> np.ndarray:
        """Row indices of `cond` whose id is in `keep` (all rows when None)."""
        if cond not in self.ids:
            return np.zeros(0, dtype=int)
        if keep is None:
            return np.arange(len(self.ids[cond]))
        return np.array([i for i, one in enumerate(self.ids[cond]) if one in keep], dtype=int)


def _num(value):
    return np.nan if value is None else float(value)


def tested_sets(cell: Cell) -> Dict[str, dict]:
    """{tested set name: {class, k, nulls: [names]}}."""
    nulls: Dict[Tuple[str, int], List[str]] = {}
    for name in cell.sets:
        match = NULL_RE.match(name)
        if match:
            nulls.setdefault((match["cls"], int(match["k"])), []).append(name)
    out = {}
    for name in cell.sets:
        if NULL_RE.match(name):
            continue
        cls, k = name, None
        suffix = re.match(r"^(?P<cls>.+)_(?P<k>\d+)$", name)
        if suffix and suffix["cls"] in CLASSES:
            cls, k = suffix["cls"], int(suffix["k"])
        ks = sorted({kk for (c, kk) in nulls if c == cls})
        if k is None:
            if len(ks) > 1:
                raise SystemExit(f"{cell.directory}: set {name!r} has nulls at several k ({ks}); "
                                 f"name it <class>_<k>")
            k = ks[0] if ks else None
        out[name] = {"class": cls, "k": k,
                     "nulls": sorted(nulls.get((cls, k), []), key=lambda n: int(NULL_RE.match(n)["i"]))}
    return out


# ==============================================================================
# METRICS (W2's definitions, on arrays)
# ==============================================================================

def _row_mean(values: np.ndarray) -> np.ndarray:
    """Mean over streams that have a value; NaN when none."""
    with np.errstate(invalid="ignore"):
        counts = np.sum(~np.isnan(values), axis=1)
        totals = np.nansum(values, axis=1)
        return np.where(counts > 0, totals / np.maximum(counts, 1), np.nan)


def _complete(*arrays) -> np.ndarray:
    """Rows where every stream of every array has a value (W2's `common` ids)."""
    ok = np.ones(arrays[0].shape[0], dtype=bool)
    for a in arrays:
        ok &= ~np.isnan(a).any(axis=1)
    return ok


def _share(values: np.ndarray, rows: np.ndarray, threshold: float = MARGIN) -> Optional[float]:
    """W2's `share`: indicator per stream where present, averaged within an id, then over ids."""
    if rows.size == 0:
        return None
    v = values[rows]
    indicator = np.where(np.isnan(v), np.nan, (v >= threshold).astype(float))
    per_id = _row_mean(indicator)
    per_id = per_id[~np.isnan(per_id)]
    return float(per_id.mean()) if per_id.size else None


def _mean_of_rows(values: np.ndarray, rows: np.ndarray) -> Optional[float]:
    if rows.size == 0:
        return None
    per_id = _row_mean(values[rows])
    per_id = per_id[~np.isnan(per_id)]
    return float(per_id.mean()) if per_id.size else None


def _removed(intact, ablated, epsilon=1e-6):
    if intact is None or ablated is None or intact <= epsilon:
        return None
    return (intact - ablated) / intact


def effect(cell: Cell, ref: str, name: str, cond: str, keep: Optional[set]) -> dict:
    """D (or I) removed by the ladder margin ratio and by the rate, on the ids in `keep`."""
    block = cell.block(ref, name, cond)
    out = {"margin": None, "rate": None, "G": None, "mean_drop": None, "n_ids": 0, "reason": None}
    if block is None:
        out["reason"] = f"no {cond} rows under {ref}"
        return out
    rows = cell.rows_of(cond, keep)
    rows = rows[_complete(block.m_int[rows], block.m_abl[rows], block.twin[rows])] if rows.size else rows
    out["n_ids"] = int(rows.size)
    if rows.size == 0:
        out["reason"] = "no complete ids"
        return out
    gap = _row_mean(block.m_int[rows] - block.twin[rows])
    drop = _row_mean(block.m_int[rows] - block.m_abl[rows])
    g, d = float(gap.mean()), float(drop.mean())
    eps = cell.epsilon(cond)
    out.update({"G": g, "mean_drop": d, "epsilon": eps})
    if g <= eps:
        out["reason"] = f"G = {g:.4g} is not above epsilon {eps:.3g}"
    else:
        out["margin"] = d / g
    p_int, p_abl, p_tw = (_share(block.m_int, rows), _share(block.m_abl, rows), _share(block.twin, rows))
    out["p_intact"], out["p_ablated"], out["p_twin_intact"] = p_int, p_abl, p_tw
    if ref == "twin":
        e_int = None if p_int is None or p_tw is None else p_int - p_tw
        e_abl = None if p_abl is None or p_tw is None else p_abl - p_tw
        out.update({"rate_effect_intact": e_int, "rate_effect_ablated": e_abl, "rate": _removed(e_int, e_abl),
                    "rate_basis": "D ablated against the twin intact (the donor is not patched)"})
    else:
        twin_block = cell.block(ref, name, TWIN_OF[cond])
        if twin_block is None:
            out["rate_basis"] = f"no {TWIN_OF[cond]} rows under {ref}"
            return out
        twin_rows_all = cell.index.get(TWIN_OF[cond], {})
        own_ids = cell.ids[cond]
        pairs = [(r, twin_rows_all[own_ids[r]]) for r in rows if own_ids[r] in twin_rows_all]
        pairs = [(r, t) for r, t in pairs if not np.isnan(twin_block.m_int[t]).any()
                 and not np.isnan(twin_block.m_abl[t]).any()]
        if not pairs:
            out["rate_basis"] = "no shared ids with the twin condition"
            return out
        own = np.array([p[0] for p in pairs], dtype=int)
        tw = np.array([p[1] for p in pairs], dtype=int)
        pd_int, pd_abl = _share(block.m_int, own), _share(block.m_abl, own)
        ph_int, ph_abl = _share(twin_block.m_int, tw), _share(twin_block.m_abl, tw)
        e_int, e_abl = pd_int - ph_int, pd_abl - ph_abl
        out.update({"rate_effect_intact": e_int, "rate_effect_ablated": e_abl, "rate": _removed(e_int, e_abl),
                    "rate_effect_ablated_vs_twin_intact": pd_abl - ph_int,
                    "n_ids_with_twin_condition": int(own.size),
                    "rate_basis": f"{cond} ablated against {TWIN_OF[cond]} ablated (R8)"})
    return out


def accuracy_shift(cell: Cell, ref: str, name: str, cond: str, keep: Optional[set]) -> Optional[float]:
    """Argmax accuracy on the condition-correct token, ablated minus intact, in points (W2's condition_metrics)."""
    block = cell.block(ref, name, cond)
    if block is None:
        return None
    rows = cell.rows_of(cond, None if cond == IOI else keep)
    rows = rows[_complete(block.m_int[rows])] if rows.size else rows
    a_int, a_abl = _mean_of_rows(block.ok_int, rows), _mean_of_rows(block.ok_abl, rows)
    if a_int is None or a_abl is None:
        return None
    return 100.0 * (a_abl - a_int)


def rate_change(cell: Cell, ref: str, name: str, cond: str, keep: Optional[set]) -> Optional[float]:
    """p(m >= 0.7) ablated minus intact, in points, over the condition's ids (D's deceptive rate for N2)."""
    block = cell.block(ref, name, cond)
    if block is None:
        return None
    rows = cell.rows_of(cond, keep)
    rows = rows[_complete(block.m_int[rows], block.m_abl[rows])] if rows.size else rows
    p_int, p_abl = _share(block.m_int, rows), _share(block.m_abl, rows)
    return None if p_int is None or p_abl is None else 100.0 * (p_abl - p_int)


def metrics(cell: Cell, ref: str, name: str, keep_by_cond: Dict[str, Optional[set]]) -> dict:
    d = effect(cell, ref, name, "D", keep_by_cond.get("D"))
    i = effect(cell, ref, name, "I", keep_by_cond.get("I"))
    out = {"D_removed_margin": d["margin"], "D_removed_rate": d["rate"],
           "I_removed_margin": i["margin"], "I_removed_rate": i["rate"],
           "D_rate_change_points": rate_change(cell, ref, name, "D", keep_by_cond.get("D")),
           "detail": {"D": d, "I": i}}
    for cond in ("H", "F", IOI, "N"):
        out[f"{cond}_shift_points"] = accuracy_shift(cell, ref, name, cond, keep_by_cond.get(cond))
    return out


NULL_METRICS = ("D_removed_margin", "D_removed_rate", "I_removed_margin", "I_removed_rate", "H_shift_points",
                "F_shift_points", "IOI_shift_points", "N_shift_points", "D_rate_change_points")


def null_distribution(cell: Cell, ref: str, nulls: Sequence[str], keep_by_cond) -> dict:
    per = [metrics(cell, ref, name, keep_by_cond) for name in nulls]
    out = {"n_nulls": len(nulls)}
    for key in NULL_METRICS:
        values = [m[key] for m in per]
        present = np.array([v for v in values if v is not None], dtype=float)
        entry = {"values": values, "n": int(present.size)}
        if present.size:
            entry.update({"p5": float(np.percentile(present, 5)), "p50": float(np.percentile(present, 50)),
                          "p95": float(np.percentile(present, 95))})
            if key.endswith("_shift_points"):
                entry["p95_abs"] = float(np.percentile(np.abs(present), 95))
        out[key] = entry
    return out


# ==============================================================================
# BOOTSTRAP
# ==============================================================================

def bootstrap(cell: Cell, ref: str, name: str, cond: str, keep: Optional[set], *, n: int, seed: int) -> dict:
    """95% intervals of the margin and rate removed, resampling ids with replacement."""
    block = cell.block(ref, name, cond)
    out = {"n_resamples": n, "seed": seed}
    if block is None:
        return out
    rows = cell.rows_of(cond, keep)
    rows = rows[_complete(block.m_int[rows], block.m_abl[rows], block.twin[rows])] if rows.size else rows
    if rows.size == 0:
        return out
    rng = np.random.default_rng(seed)
    gap = _row_mean(block.m_int[rows] - block.twin[rows])
    drop = _row_mean(block.m_int[rows] - block.m_abl[rows])
    idx = rng.integers(0, rows.size, size=(n, rows.size))
    g, d = gap[idx].mean(1), drop[idx].mean(1)
    eps = cell.epsilon(cond)
    ratio = np.where(g > eps, d / np.where(g > eps, g, 1.0), np.nan)
    out["margin"] = _interval(ratio)

    def ind(values, r):
        v = values[r]
        return _row_mean(np.where(np.isnan(v), np.nan, (v >= MARGIN).astype(float)))

    if ref == "twin":
        i_int, i_abl, i_tw = ind(block.m_int, rows), ind(block.m_abl, rows), ind(block.twin, rows)
        e_int = i_int[idx].mean(1) - i_tw[idx].mean(1)
        e_abl = i_abl[idx].mean(1) - i_tw[idx].mean(1)
    else:
        twin_block = cell.block(ref, name, TWIN_OF[cond])
        if twin_block is None:
            return out
        twin_index = cell.index.get(TWIN_OF[cond], {})
        own_ids = cell.ids[cond]
        pairs = [(r, twin_index[own_ids[r]]) for r in rows if own_ids[r] in twin_index]
        pairs = [(r, t) for r, t in pairs if not np.isnan(twin_block.m_int[t]).any()
                 and not np.isnan(twin_block.m_abl[t]).any()]
        if not pairs:
            return out
        own = np.array([p[0] for p in pairs], dtype=int)
        tw = np.array([p[1] for p in pairs], dtype=int)
        j = rng.integers(0, own.size, size=(n, own.size))
        e_int = ind(block.m_int, own)[j].mean(1) - ind(twin_block.m_int, tw)[j].mean(1)
        e_abl = ind(block.m_abl, own)[j].mean(1) - ind(twin_block.m_abl, tw)[j].mean(1)
    rate = np.where(e_int > 1e-6, (e_int - e_abl) / np.where(e_int > 1e-6, e_int, 1.0), np.nan)
    out["rate"] = _interval(rate)
    return out


def _interval(values: np.ndarray) -> dict:
    ok = values[~np.isnan(values)]
    if ok.size == 0:
        return {"lo": None, "hi": None, "n_defined": 0}
    return {"lo": float(np.percentile(ok, 2.5)), "hi": float(np.percentile(ok, 97.5)), "n_defined": int(ok.size)}


# ==============================================================================
# HALVES (R10)
# ==============================================================================

def sample_halves(sample: dict, *, d_dir: str, i_dir: str, seed: int = SEED) -> Tuple[Dict[str, str], dict]:
    """({id: "A" or "B"} over the union of the sample's D and I ids, how it was made)."""
    ids_d = [str(x) for x in sample["ids"]["D"]]
    ids_i = [str(x) for x in sample["ids"]["I"]]
    union = sorted(set(ids_d) | set(ids_i))
    try:
        from scripts.neuron_partition_data import split_halves
        clusters = {}
        for directory in (d_dir, i_dir):
            from datasets import load_from_disk
            for record in load_from_disk(directory)["test"]:
                clusters.setdefault(str(record["instance_id"]), str(record["pressure_id"]))
        missing = [one for one in union if one not in clusters]
        if missing:
            raise KeyError(f"{len(missing)} sample ids have no pressure_id")
        halves = split_halves(union, [clusters[one] for one in union], seed=seed)
        method = {"method": "split_halves (scripts/neuron_partition_data.py), stratified by pressure_id",
                  "seed": seed, "over": "the union of the sample's D and I ids",
                  "clusters_from": [os.path.abspath(d_dir), os.path.abspath(i_dir)]}
    except Exception as error:                                       # noqa: BLE001 - recorded fallback
        order = list(union)
        random.Random(seed).shuffle(order)
        halves = {one: "AB"[i % 2] for i, one in enumerate(order)}
        method = {"method": "fallback: sorted ids, random.Random(seed).shuffle, alternated", "seed": seed,
                  "why": f"{type(error).__name__}: {error}"}
    method["counts"] = {c: {h: sum(1 for one in sample["ids"][c] if halves.get(str(one)) == h) for h in "AB"}
                        for c in sample["ids"]}
    return halves, method


def keep_maps(sample: Optional[dict], halves: Optional[Dict[str, str]]) -> Dict[str, Dict[str, Optional[set]]]:
    """{subset: {condition: id set or None}}; IOI is None (all rows) in every subset."""
    whole = {c: None for c in ("D", "H", "F", "I", "N", IOI)}
    out = {"whole": whole}
    if halves is None:
        return out
    for subset, half in (("half1", "A"), ("half2", "B")):
        out[subset] = {c: {one for one, h in halves.items() if h == half} for c in ("D", "H", "F", "I", "N")}
        out[subset][IOI] = None
    return out


# ==============================================================================
# VERDICTS
# ==============================================================================

def n1_bars(size, own: dict, collateral: dict, null: dict) -> dict:
    """Each item-10 N1 bar: {passed, value, reason}."""
    def bar(value, test, label):
        if value is None:
            return {"passed": False, "value": None, "reason": f"{label}: no value"}
        return {"passed": bool(test(value)), "value": value}

    p95 = (null.get("D_removed_margin") or {}).get("p95")
    bars = {
        "size_le_2000": bar(size, lambda v: v <= MAX_SIZE, "size"),
        "D_removed_ge_0.50": bar(own["D_removed_margin"], lambda v: v >= D_BAR, "D removed"),
        "I_removed_lt_0.25": bar(own["I_removed_margin"], lambda v: v < I_BAR, "I removed"),
        "H_shift_lt_5": bar(collateral.get("H_shift_points"), lambda v: abs(v) < COLLATERAL_BAR, "H shift"),
        "F_shift_lt_5": bar(collateral.get("F_shift_points"), lambda v: abs(v) < COLLATERAL_BAR, "F shift"),
        "IOI_shift_lt_5": bar(collateral.get("IOI_shift_points"), lambda v: abs(v) < COLLATERAL_BAR, "IOI shift"),
    }
    if p95 is None or own["D_removed_margin"] is None:
        bars["beats_null_p95"] = {"passed": False, "value": own["D_removed_margin"], "null_p95": p95,
                                  "reason": "no null 95th percentile or no D removed"}
    else:
        bars["beats_null_p95"] = {"passed": own["D_removed_margin"] > p95, "value": own["D_removed_margin"],
                                  "null_p95": p95}
    bars["all"] = all(b["passed"] for b in bars.values())
    return bars


def n2_verdict(own: dict, null: dict) -> dict:
    h, d = own.get("H_shift_points"), own.get("D_rate_change_points")
    null_h = (null.get("H_shift_points") or {}).get("p95_abs")
    out = {"H_shift_points": h, "D_rate_change_points": d, "null_H_shift_p95_abs": null_h}
    if h is None or d is None:
        out["verdict"] = "undetermined at this size"
        out["reason"] = "missing H or D readout"
    elif h <= N2_H_DROP and abs(d) < N2_D_STILL and null_h is not None and null_h < N2_NULL_H:
        out["verdict"] = "bypass"
    elif h <= N2_H_DROP and d <= N2_D_FALL:
        out["verdict"] = "suppression or shared"
    else:
        out["verdict"] = "undetermined at this size"
    return out


def analyse(cells: Sequence[Cell], subsets: Dict[str, Dict[str, Optional[set]]], *, n_boot: int, seed: int) -> dict:
    results: Dict[str, Dict[str, Dict[str, dict]]] = {}
    for cell in cells:
        for name, info in tested_sets(cell).items():
            cls, k = info["class"], info["k"]
            size = cell.size(name)
            for ref in cell.references:
                entry = {"set": name, "cell": cell.directory, "size": size, "nulls": info["nulls"],
                         "subsets": {}, "bootstrap": {}}
                for subset, keep in subsets.items():
                    own = metrics(cell, ref, name, keep)
                    null = null_distribution(cell, ref, info["nulls"], keep)
                    mean_own = metrics(cell, "mean", name, keep) if "mean" in cell.references else {}
                    collateral = {c: mean_own.get(c) for c in ("H_shift_points", "F_shift_points",
                                                               "IOI_shift_points")}
                    entry["subsets"][subset] = {
                        "own": own, "null": null, "collateral_from_mean": collateral,
                        "n1_bars": n1_bars(size, own, collateral, null)}
                    if cls == "H_only":
                        entry["subsets"][subset]["n2"] = n2_verdict(own, null)
                for cond in ("D", "I"):
                    entry["bootstrap"][cond] = bootstrap(cell, ref, name, cond, subsets["whole"].get(cond),
                                                         n=n_boot, seed=seed)
                results.setdefault(ref, {}).setdefault(cls, {})[str(k)] = entry
    return results


def n1_summary(results: dict) -> dict:
    """D_only per k: the pass needs every bar under the deciding references on every subset."""
    deciding = ["twin", "mean"] if "twin" in results else ["mean", "zero"]
    out = {"deciding_references": deciding, "by_k": {}}
    ks = sorted({k for ref in results.values() for k in ref.get("D_only", {})}, key=lambda v: int(v))
    for k in ks:
        grid = {}
        for ref in deciding:
            entry = results.get(ref, {}).get("D_only", {}).get(k)
            grid[ref] = {s: (entry["subsets"][s]["n1_bars"]["all"] if entry and s in entry["subsets"] else None)
                         for s in SUBSETS}
        flags = [v for r in grid.values() for v in r.values()]
        complete = all(v is not None for v in flags)
        passed = complete and all(flags)
        out["by_k"][k] = {"grid": grid, "pass": passed,
                          "lead": (not passed) and any(v for v in flags if v),
                          "complete": complete}
    out["n1_pass_any_k"] = any(v["pass"] for v in out["by_k"].values())
    return out


# ==============================================================================
# REPORT
# ==============================================================================

def _f(value, digits=3):
    return "n/a" if value is None else f"{value:.{digits}f}"


def _ci(boot, key):
    entry = (boot or {}).get(key) or {}
    if entry.get("lo") is None:
        return ""
    return f" [{entry['lo']:.2f}, {entry['hi']:.2f}]"


def render_markdown(verdict: dict) -> str:
    lines = ["# neuron-partition verdict (item 10, N1 and N2)", ""]
    lines.append(f"Cells: {', '.join(c['dir'] for c in verdict['inputs']['cells'])}.")
    lines.append(f"Halves: {verdict['choices']['halves']['method']}.")
    lines.append("D and I removed are the ladder margin ratio (R2, primary) and the rate at margin 0.7 (R8); "
                 "brackets are bootstrap 95% intervals over ids (whole sample). Collateral shifts are under the "
                 "mean reference (R7). Pass flags: every N1 bar on the subset.")
    lines.append("")
    for ref, by_class in verdict["results"].items():
        lines += [f"## Reference: {ref}", "",
                  "| class | k | size | D removed (margin) | D removed (rate) | I removed (margin) | I removed (rate) "
                  "| null p95 of D removed | H shift | F shift | IOI shift | bars (whole) | half 1 | half 2 |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for cls in CLASSES:
            for k, entry in sorted(by_class.get(cls, {}).items(), key=lambda kv: int(kv[0]) if kv[0] != "None" else 0):
                whole = entry["subsets"]["whole"]
                own, col, boot = whole["own"], whole["collateral_from_mean"], entry["bootstrap"]
                p95 = (whole["null"].get("D_removed_margin") or {}).get("p95")
                flag = {True: "pass", False: "fail", None: "n/a"}
                halves = [flag[entry["subsets"][s]["n1_bars"]["all"]] if s in entry["subsets"] else "n/a"
                          for s in ("half1", "half2")]
                lines.append(
                    f"| {cls} | {k} | {entry['size']} | {_f(own['D_removed_margin'])}{_ci(boot.get('D'), 'margin')} "
                    f"| {_f(own['D_removed_rate'])}{_ci(boot.get('D'), 'rate')} "
                    f"| {_f(own['I_removed_margin'])}{_ci(boot.get('I'), 'margin')} "
                    f"| {_f(own['I_removed_rate'])}{_ci(boot.get('I'), 'rate')} | {_f(p95)} "
                    f"| {_f(col['H_shift_points'], 1)} | {_f(col['F_shift_points'], 1)} "
                    f"| {_f(col['IOI_shift_points'], 1)} | {flag[whole['n1_bars']['all']]} | {halves[0]} "
                    f"| {halves[1]} |")
        lines.append("")
    n1 = verdict["n1"]
    lines += ["## N1 (D_only)", "",
              f"Deciding references: {', '.join(n1['deciding_references'])}. A pass needs every bar under each on the "
              "whole sample and both halves.", "",
              "| k | " + " | ".join(f"{r} {s}" for r in n1["deciding_references"] for s in SUBSETS) + " | verdict |",
              "|---|" + "---|" * (3 * len(n1["deciding_references"]) + 1)]
    for k, entry in n1["by_k"].items():
        cells = [{True: "pass", False: "fail", None: "n/a"}[entry["grid"][r][s]]
                 for r in n1["deciding_references"] for s in SUBSETS]
        verdict_k = "PASS" if entry["pass"] else ("lead" if entry["lead"] else "fail")
        lines.append(f"| {k} | " + " | ".join(cells) + f" | {verdict_k} |")
    lines += ["", f"N1 pass at any k: {n1['n1_pass_any_k']}.", "", "## N2 (H_only)", "",
              "| reference | k | subset | H shift | D rate change | null p95 of abs H shift | verdict |",
              "|---|---|---|---|---|---|---|"]
    for ref, by_class in verdict["results"].items():
        for k, entry in sorted(by_class.get("H_only", {}).items(), key=lambda kv: int(kv[0]) if kv[0] != "None" else 0):
            for subset, block in entry["subsets"].items():
                n2 = block.get("n2") or {}
                lines.append(f"| {ref} | {k} | {subset} | {_f(n2.get('H_shift_points'), 1)} "
                             f"| {_f(n2.get('D_rate_change_points'), 1)} | {_f(n2.get('null_H_shift_p95_abs'), 1)} "
                             f"| {n2.get('verdict', 'n/a')} |")
    lines += ["", "N2 is decided under the mean reference; zero is beside it and twin is the descriptive reverse "
              "patch.", ""]
    return "\n".join(lines)


# ==============================================================================
# CLI
# ==============================================================================

def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--cell", action="append", required=True, help="An ablation cell directory (repeatable).")
    p.add_argument("--sample", default=DEFAULT_SAMPLE, help="far_test_sample_seed2.json (for the halves).")
    p.add_argument("--d-dir", default=DEFAULT_D_DIR, help="far_v2 (pressure_id of the D ids).")
    p.add_argument("--i-dir", default=DEFAULT_I_DIR, help="user-turn I pool (pressure_id of the I ids).")
    p.add_argument("--halves-json", default=None, help="A precomputed {id: 'A' or 'B'} map instead of the rule.")
    p.add_argument("--no-halves", action="store_true", help="Whole sample only.")
    p.add_argument("--bootstrap", type=int, default=N_BOOT)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--output-dir", required=True)
    return p


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    cells = [Cell(path) for path in args.cell]
    sample, halves, halves_info = None, None, {"method": "none (--no-halves)"}
    if not args.no_halves:
        with open(args.sample) as handle:
            sample = json.load(handle)
        if args.halves_json:
            with open(args.halves_json) as handle:
                halves = {str(k): str(v) for k, v in json.load(handle).items()}
            halves_info = {"method": f"precomputed map {os.path.abspath(args.halves_json)}"}
        else:
            halves, halves_info = sample_halves(sample, d_dir=args.d_dir, i_dir=args.i_dir, seed=args.seed)
    subsets = keep_maps(sample, halves)
    results = analyse(cells, subsets, n_boot=args.bootstrap, seed=args.seed)
    verdict = {
        "analysis": "neuron_partition_verdict",
        "inputs": {"cells": [{"dir": c.directory, "summary_sha256": _sha(os.path.join(c.directory, "summary.json")),
                              "rows_sha256": _sha(os.path.join(c.directory, "rows.jsonl")),
                              "references": c.references, "conditions": sorted(c.ids),
                              "n_ids": {k: len(v) for k, v in c.ids.items()},
                              "self_replay_error": c.replay} for c in cells],
                   "sample": None if sample is None else {"path": os.path.abspath(args.sample),
                                                          "sha256": _sha(args.sample)}},
        "choices": {
            "halves": halves_info,
            "ioi_in_halves": "all IOI rows in both halves (IOI is not part of the seed-2 sample)",
            "decides": "D and I removed by the ladder margin ratio (R2); the rate at margin 0.7 is reported beside it",
            "collateral": "H, F and IOI argmax accuracy shifts under the mean reference, for every reference (R7)",
            "n1_pass": "D_only; every bar under twin and mean on the whole sample and both halves "
                       "(mean and zero if no twin cells)",
            "n2_null_rule": "the matched null moves H under 5 points: 95th percentile of |null H shift| < 5",
            "n2_reference": "mean decides; zero beside it; twin is the descriptive reverse patch",
            "null_percentile": "numpy.percentile, linear interpolation, over the defined null values",
            "bootstrap": f"{args.bootstrap} resamples of ids with replacement, seed {args.seed}, whole sample, "
                         "tested sets only; 2.5th and 97.5th percentiles",
        },
        "results": results,
    }
    verdict["n1"] = n1_summary(results)
    os.makedirs(args.output_dir, exist_ok=True)
    with open(os.path.join(args.output_dir, "verdict.json"), "w") as handle:
        json.dump(verdict, handle, indent=1)
        handle.write("\n")
    with open(os.path.join(args.output_dir, "verdict.md"), "w") as handle:
        handle.write(render_markdown(verdict))
    print(f"wrote {args.output_dir}/verdict.json and verdict.md; N1 pass at any k: {verdict['n1']['n1_pass_any_k']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
