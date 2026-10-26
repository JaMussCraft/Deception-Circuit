#!/usr/bin/env python3
"""
p2_results.py -- the phase-2 results of the mechanism-analysis feature (ticket 04; spec sections 2.5-2.9, 4 phase 2).

Reads the fetched phase-2 cells under outputs/_analyses/mechanism-analysis-p2/<cell>/Up__leaf/<test set>/ (one job
per task, p2_jobs.py), the six atomic circuits' head sets, the per-task operand's provenance and the phase-1 S2p
sweeps, and writes

    reports/04-phase2-results.json       every number the reading quotes
    reports/04-phase2-results.md         the tables
    docs/research/mechanism-analysis/phase2/
        <t>_<cell>_head_table.csv        the cell's head table with the membership columns appended (R6)
        families.csv, segments.csv       the family knockouts and the segment-resolved knockout, long form
        roles/<t>_<cell>.json            the roles pass's roles.json per cell, copied
        p2_readings.json                 the readings block of the results JSON

Readings (pure functions, tested in tests/test_mechanism_analysis_p2.py):

    membership        U, S_k, C_t, core, excl_t, D_t-H_t, (D_t-H_t)-core, H_t-D_t, late H-D per Component, from the
                      six head sets and the operand's provenance, on CPU (spec section 4 phase 2)
    c_reads           the exclusives' top-Segment groups on their own D cell, Fisher exact over tasks x groups
                      (C-reads; a head-level test, not clustered)
    b_reader          the B2-signature heads (clause-mass drop >= floor and >= z SE, paired), the share in layers
                      8-17 against 10/32 by a one-sided binomial upper tail, and L13H5/H20/H21 (B-reader)
    c_honest          the late H-D heads' DLA on H and F (positive = honest there) and, on D, the honest-direction
                      DLA under pressure against the paired twin; suppressed = >= 50 % smaller (C-honest)
    i_vs_d            the B2 signature and the paired DLA on I against D per head of the deciding set (R-inv input)
    family_table      the composition-set family knockouts per cell, with R-cls at the family level from the
                      D/H/F item-swap cells (RQ-A's component part)
    segment_matrix    the segment-resolved neutral-twin knockout of the S2p top 20; pre_clause_check asserts the
                      pre-clause Segments exactly zero (R16: a sanity assertion, never a finding)
    ct_proposal       phase 3's C_t = core | excl_t | ((D_t-H_t)-core) | S_k heads | <= 10 MLPs (deciding first,
                      then S2p rank), with sizes

Statistics are hand-rolled (no scipy in the job environment): the Freeman-Halton exact test by enumeration of the
tables with the observed margins, and the exact binomial upper tail.

usage (from the repository root, after the cells are fetched and the roles pass has run):
    python outputs/_launch_mechanism_analysis/p2_results.py [--root DIR] [--reports DIR] [--curated DIR]
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
import shutil
import sys
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
for _p in (HERE, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import p1_readings as rd  # noqa: E402
import p2_jobs  # noqa: E402
import p2_operands  # noqa: E402
from component_analysis import roles  # noqa: E402

TASKS = ("far", "sdr", "ser")
ROOT = "outputs/_analyses/mechanism-analysis-p2"
REPORTS = "/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports"
CURATED = os.path.join(REPO, "docs", "research", "mechanism-analysis", "phase2")
HEAD_CELLS = ("d", "h", "f", "i")
FAMILY_CELLS = {"d": "D item-swap, all positions", "d_twinko": "D neutral twin, post-clause",
                "h": "H item-swap, all positions (honest margin)", "f": "F item-swap, all positions (honest margin)",
                "i": "I neutral twin, post-clause"}
MEMBERSHIP = ("U", "S_k", "C_t", "core", "excl_t", "DmH_t", "DmH_minus_core_t", "HmD_t", "late_HmD_t")
READ_GROUPS = ("designation", "item_mention", "pressure", "frame")
L13 = ("head.13.5", "head.13.20", "head.13.21")
BASE_RATE = 10 / 32
EPS = 1e-12

# the column names, taken from the roles pass so they cannot drift
TOP_SEGMENT, TOP_MASS = roles.TOP_SEGMENT, roles.TOP_MASS
TWIN_TOP_SEGMENT = roles.TWIN_TOP_SEGMENT
B2_DROP, B2_DROP_SE = roles.B2_DROP, roles.B2_DROP_SE
DLA, DLA_SE = roles.DLA, roles.DLA_SE
DLA_TWIN = "dla.neutral_twin_paired"
DLA_DIFF_TWIN, DLA_DIFF_TWIN_SE = "dla.differential_neutral_twin_paired", "dla.differential_neutral_twin_paired_se"


def label_of(key) -> str:
    return p2_operands.label_of(key)


def parse_label(label: str) -> tuple:
    return p2_operands.parse_label(label)


def key_of(row: dict) -> tuple:
    return (row["kind"], int(row["layer"]), int(row["index"]))


# ------------------------------------------------------------------ statistics

@lru_cache(maxsize=None)
def _lf(n: int) -> float:
    return math.lgamma(n + 1)


def fisher_exact_rxc(table) -> float:
    """Two-sided Freeman-Halton exact test: the probability mass of every table with the observed margins whose
    conditional probability is at most the observed table's. Empty rows and columns are dropped; fewer than two
    non-empty rows or columns means no test, p = 1."""
    rows = [list(map(int, r)) for r in table if sum(r) > 0]
    if len(rows) < 2:
        return 1.0
    keep = [j for j in range(len(rows[0])) if sum(r[j] for r in rows) > 0]
    rows = [[r[j] for j in keep] for r in rows]
    if len(keep) < 2:
        return 1.0
    row_sums = [sum(r) for r in rows]
    col_sums = [sum(r[j] for r in rows) for j in range(len(keep))]
    n = sum(row_sums)
    const = sum(_lf(s) for s in row_sums) + sum(_lf(s) for s in col_sums) - _lf(n)

    def logp(cells) -> float:
        return const - sum(_lf(c) for c in cells)

    observed = logp([c for r in rows for c in r])
    total = 0.0

    def rec(i, remaining_cols, acc):
        nonlocal total
        if i == len(rows) - 1:
            total_log = acc - sum(_lf(c) for c in remaining_cols) + const
            if total_log <= observed + 1e-9:
                total += math.exp(total_log)
            return
        # enumerate row i's cells summing to row_sums[i] within the remaining column capacities
        def fill(j, left, cur, cur_acc):
            if j == len(remaining_cols) - 1:
                if left <= remaining_cols[j]:
                    cur.append(left)
                    rem = [remaining_cols[k] - cur[k] for k in range(len(cur))]
                    rec(i + 1, rem, cur_acc - _lf(left))
                    cur.pop()
                return
            for c in range(min(left, remaining_cols[j]) + 1):
                cur.append(c)
                fill(j + 1, left - c, cur, cur_acc - _lf(c))
                cur.pop()
        fill(0, row_sums[i], [], acc)

    rec(0, col_sums, 0.0)
    return min(1.0, total)


def binomial_upper_tail(k: int, n: int, p: float) -> float:
    """P[X >= k] for X ~ Binomial(n, p); the one-sided test of a share above a base rate."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


# ------------------------------------------------------------------ membership

def membership(t: str, sets: dict, operand_prov: dict) -> dict:
    """{key: {column: bool}} over U' = U | S_k heads | C_t MLP blocks."""
    comp = p2_jobs.composition_sets(t, sets)
    U = set().union(*(sets[k] for k in sets))
    sk = {parse_label(h) for h in operand_prov["heads"]}
    ct = {("mlp", int(l), 0) for l in operand_prov["mlp_layers"]}
    out = {}
    for layer, head in sorted(U | {(l, h) for _k, l, h in sk}):
        key = ("head", layer, head)
        pair = (layer, head)
        out[key] = {"U": pair in U, "S_k": key in sk, "C_t": False, "core": pair in comp["core"],
                    "excl_t": pair in comp[f"excl_{t}"], "DmH_t": pair in comp[f"DmH_{t}"],
                    "DmH_minus_core_t": pair in comp[f"DmH_minus_core_{t}"], "HmD_t": pair in comp[f"HmD_{t}"],
                    "late_HmD_t": pair in comp[f"late_HmD_{t}"]}
    for key in sorted(ct):
        out[key] = {c: False for c in MEMBERSHIP}
        out[key]["C_t"] = True
        out[key]["S_k"] = key in sk
    return out


# ------------------------------------------------------------------ readings

def _by_key(rows) -> dict:
    return {key_of(r): r for r in rows}


def read_group(segment) -> str:
    return roles.SEGMENT_GROUPS.get(segment, "unestablished") if segment else "unestablished"


def c_reads(rows_by_task: dict, excl_by_task: dict, *, segment_col: str = TOP_SEGMENT, mass_col: str = TOP_MASS) -> dict:
    """C-reads: each task's exclusive heads' top-Segment group on the task's own cell; Fisher over tasks x groups."""
    heads, counts = {}, {}
    for t in TASKS:
        by = _by_key(rows_by_task.get(t, []))
        heads[t] = []
        for key in sorted(excl_by_task.get(t, ())):
            row = by.get(key, {})
            seg = row.get(segment_col)
            heads[t].append({"label": label_of(key), "segment": seg, "group": read_group(seg), "mass": row.get(mass_col)})
        counts[t] = {}
        for h in heads[t]:
            counts[t][h["group"]] = counts[t].get(h["group"], 0) + 1
    groups = [g for g in READ_GROUPS + ("unestablished",) if any(counts[t].get(g) for t in TASKS)]
    table = [[counts[t].get(g, 0) for g in groups] for t in TASKS]
    return {"groups": groups, "tasks": list(TASKS), "table": table, "counts": counts, "p": fisher_exact_rxc(table),
            "heads": heads, "test": "Freeman-Halton exact, two-sided, head level (not clustered)"}


def b2_signature(row: dict, *, floor: float, z: float):
    drop, se = row.get(B2_DROP), row.get(B2_DROP_SE)
    if drop is None or se is None:
        return None
    return bool(drop >= floor - EPS and drop >= z * se - EPS)


def b_reader(rows, *, floor: float = 0.05, z: float = 2.0) -> dict:
    """B-reader: signature heads, their share in layers 8-17 against 10/32 (one-sided), and L13H5/H20/H21."""
    sig, measured = [], 0
    l13 = {}
    for row in rows:
        if row.get("kind") != "head":
            continue
        s = b2_signature(row, floor=floor, z=z)
        label = label_of(key_of(row))
        if label in L13:
            l13[label] = {"drop": row.get(B2_DROP), "se": row.get(B2_DROP_SE), "signature": s}
        if s is None:
            continue
        measured += 1
        if s:
            sig.append({"label": label, "layer": int(row["layer"]), "drop": row[B2_DROP], "se": row[B2_DROP_SE]})
    k = sum(1 for h in sig if 8 <= h["layer"] <= 17)
    return {"floor": floor, "z": z, "n_measured": measured, "n_signature": len(sig), "n_in_8_17": k,
            "share_8_17": (k / len(sig)) if sig else None, "base_rate": BASE_RATE,
            "p": binomial_upper_tail(k, len(sig), BASE_RATE) if sig else None, "signature_heads": sig, "l13": l13,
            "test": "one-sided binomial upper tail of the layer-8-17 count among signature heads against 10/32"}


def c_honest(late_keys, rows_d, rows_h, rows_f) -> dict:
    """C-honest over the late H-D heads. On H and F the DLA is read in the cell's own (honest) direction; on D the
    metric is deceptive-positive, so the honest direction is the negation."""
    D, H, F = _by_key(rows_d), _by_key(rows_h), _by_key(rows_f)
    heads = {}
    for key in sorted(late_keys):
        h, f = H.get(key, {}).get(DLA), F.get(key, {}).get(DLA)
        dp, dt = D.get(key, {}).get(DLA), D.get(key, {}).get(DLA_TWIN)
        hp = -dp if dp is not None else None
        htw = -dt if dt is not None else None
        supp = (1.0 - hp / htw) if (hp is not None and htw is not None and htw > 0) else None
        heads[label_of(key)] = {"dla_H": h, "dla_F": f, "honest_dla_D_pressure": hp, "honest_dla_D_twin": htw,
                                "suppression": supp,
                                "writes_honest_on_H_and_F": bool(h is not None and f is not None and h > 0 and f > 0),
                                "suppressed": bool(supp is not None and supp >= 0.5)}
    return {"n": len(heads), "n_writes_honest": sum(v["writes_honest_on_H_and_F"] for v in heads.values()),
            "n_suppressed": sum(v["suppressed"] for v in heads.values()), "heads": heads,
            "rule": "writes honest = DLA > 0 on both H and F; suppressed = honest-direction DLA under pressure on D "
                    ">= 50 % smaller than on the paired twin (twin honest-direction DLA > 0)"}


def i_vs_d(deciding_heads, rows_d, rows_i, *, floor: float = 0.05, z: float = 2.0) -> dict:
    """Per deciding-set head: the B2 signature and the paired DLA on I against D (descriptive, feeds R-inv)."""
    D, I = _by_key(rows_d), _by_key(rows_i)
    out = {}
    for key in deciding_heads:
        d, i = D.get(key, {}), I.get(key, {})
        out[label_of(key)] = {
            "D": {"b2_drop": d.get(B2_DROP), "b2_se": d.get(B2_DROP_SE), "b2_signature": b2_signature(d, floor=floor, z=z),
                  "dla_pressure": d.get(DLA), "dla_twin": d.get(DLA_TWIN), "dla_differential": d.get(DLA_DIFF_TWIN),
                  "dla_differential_se": d.get(DLA_DIFF_TWIN_SE), "top_segment": d.get(TOP_SEGMENT)},
            "I": {"b2_drop": i.get(B2_DROP), "b2_se": i.get(B2_DROP_SE), "b2_signature": b2_signature(i, floor=floor, z=z),
                  "dla_pressure": i.get(DLA), "dla_twin": i.get(DLA_TWIN), "dla_differential": i.get(DLA_DIFF_TWIN),
                  "dla_differential_se": i.get(DLA_DIFF_TWIN_SE), "top_segment": i.get(TOP_SEGMENT)}}
    both = [v for v in out.values() if v["D"]["b2_signature"] is not None and v["I"]["b2_signature"] is not None]
    return {"heads": out, "n": len(out),
            "n_signature_D": sum(1 for v in both if v["D"]["b2_signature"]),
            "n_signature_I": sum(1 for v in both if v["I"]["b2_signature"]),
            "n_signature_both": sum(1 for v in both if v["D"]["b2_signature"] and v["I"]["b2_signature"]),
            "note": "I's metric direction is the inverted answer (the I stand-in's target), D's is the deceptive one"}


def _entry(group: dict, clean: dict) -> dict:
    return {"drop": group["mean_drop"], "se": group["standard_error"], "clean": clean["mean_logit_difference"]}


def family_table(cells: dict) -> dict:
    """{family: {cell: {...}}} from each cell's groups.json, plus R-cls at family level from d/h/f (item swap)."""
    out = {}
    for cell, g in cells.items():
        clean = g["clean_run"]
        for grp in g["groups"]:
            out.setdefault(grp["name"], {})[cell] = {
                "mean_drop": grp["mean_drop"], "standard_error": grp["standard_error"], "n": grp["n"],
                "n_components": grp.get("n_components", len(grp.get("members", []))),
                "accuracy": grp.get("accuracy"), "accuracy_drop": grp.get("accuracy_drop"),
                "knocked_logit_difference": grp.get("knocked_logit_difference"),
                "clean_logit_difference": clean["mean_logit_difference"],
                "d": grp["mean_drop"] / clean["mean_logit_difference"] if clean["mean_logit_difference"] else None,
                "target_direction": g.get("target_direction")}
    for fam, by in out.items():
        if all(c in by for c in ("d", "h", "f")):
            by["rcls"] = rd.rcls(D=_entry({"mean_drop": by["d"]["mean_drop"], "standard_error": by["d"]["standard_error"]},
                                          {"mean_logit_difference": by["d"]["clean_logit_difference"]}),
                                 H=_entry({"mean_drop": by["h"]["mean_drop"], "standard_error": by["h"]["standard_error"]},
                                          {"mean_logit_difference": by["h"]["clean_logit_difference"]}),
                                 F=_entry({"mean_drop": by["f"]["mean_drop"], "standard_error": by["f"]["standard_error"]},
                                          {"mean_logit_difference": by["f"]["clean_logit_difference"]}))
    return out


def segment_matrix(seg_cells: dict) -> dict:
    """{label: {segment: {mean_drop, standard_error, accuracy_drop}}} from the seg_<segment> cells' groups.json."""
    out = {}
    for seg, g in seg_cells.items():
        for grp in g["groups"]:
            out.setdefault(grp["name"], {})[seg] = {"mean_drop": grp["mean_drop"], "standard_error": grp["standard_error"],
                                                    "accuracy_drop": grp.get("accuracy_drop")}
    return out


def pre_clause_check(matrix: dict, pre_clause) -> dict:
    """R16: every pre-clause Segment reads exactly zero by construction. Not a finding; a non-zero is a bug."""
    nonzero, worst = [], 0.0
    for label, by in matrix.items():
        for seg in pre_clause:
            if seg not in by:
                continue
            v = by[seg]["mean_drop"]
            worst = max(worst, abs(v))
            if v != 0.0:
                nonzero.append({"label": label, "segment": seg, "mean_drop": v})
    return {"ok": not nonzero, "max_abs_drop": worst, "nonzero": nonzero}


def ct_proposal(t: str, sets: dict, deciding: dict, sweep_rank, *, mlp_cap: int = 10) -> dict:
    """Phase 3's C_t: core | excl_t | ((D_t-H_t)-core) | the deciding S_k's heads | <= mlp_cap MLP blocks."""
    comp = p2_jobs.composition_sets(t, sets)
    sk_heads = {tuple(k) for k in deciding["heads"]}
    heads = ({("head", l, h) for l, h in comp["core"]} | {("head", l, h) for l, h in comp[f"excl_{t}"]}
             | {("head", l, h) for l, h in comp[f"DmH_minus_core_{t}"]} | sk_heads)
    mlps = [label_of(tuple(k)) for k in deciding["mlps"]]
    for lb in sweep_rank:
        if len(mlps) >= mlp_cap:
            break
        if lb.startswith("mlp.") and lb not in mlps and lb != "mlp.0.0":
            mlps.append(lb)
    mlps = mlps[:mlp_cap]
    return {"heads": sorted(label_of(k) for k in sorted(heads)), "mlps": mlps,
            "sizes": {"core": len(comp["core"]), "excl_t": len(comp[f"excl_{t}"]),
                      "DmH_minus_core_t": len(comp[f"DmH_minus_core_{t}"]), "S_k_heads": len(sk_heads),
                      "heads": len(heads), "mlps": len(mlps), "components": len(heads) + len(mlps)},
            "rule": "spec section 4 phase 3: core | excl_t | ((D_t-H_t)-core) | S_k heads | <= 10 MLP blocks "
                    "(the deciding set's MLPs first, then by S2p rank, the layer-0 MLP never)"}


# ------------------------------------------------------------------ loading the cells

def cell_dir(root: str, cell: str, t: str) -> str:
    """The task's test-set dir under <root>/<cell>/Up__leaf/: the three tasks share a cell root and the test set is
    named after the task (<t>_v2, <t>_v2_nopressure, <t>_v2_inversion)."""
    hits = [h for h in sorted(glob.glob(os.path.join(root, cell, "Up__leaf", f"{t}_*"))) if os.path.isdir(h)]
    if len(hits) != 1:
        raise FileNotFoundError(f"{cell}/{t}: expected one test-set dir under {root}/{cell}/Up__leaf/{t}_*, found {hits}")
    return hits[0]


def load_json(path: str):
    with open(path) as f:
        return json.load(f)


def load_rows(cdir: str) -> list:
    return load_json(os.path.join(cdir, "head_table.json"))["rows"]


def load_groups(cdir: str) -> dict:
    return load_json(os.path.join(cdir, "knockout", "groups.json"))


def load_roles(cdir: str):
    path = os.path.join(cdir, roles.SUBDIR, roles.JSON_NAME)
    return load_json(path) if os.path.exists(path) else None


def clause_mass_by_layer(cdir: str, condition: str = "pressure") -> dict:
    """Descriptive: mean Readout-query mass on the Pressure Clause per layer, over the heads measured."""
    path = os.path.join(cdir, "attention", "patterns.json")
    if not os.path.exists(path):
        return {}
    pay = load_json(path)
    cond = next((c for c in pay["conditions"] if c["name"] == condition), None)
    if not cond:
        return {}
    level = (cond.get("levels") or {}).get("all") or {}
    masses = level.get("masses") or {}
    query = pay["column_query_position"]
    by_layer = {}
    for comp in pay["components"]:
        kind, layer, _i = comp["key"]
        if kind != "head":
            continue
        prof = (masses.get(comp["name"]) or {}).get(query) or {}
        v = prof.get("pressure_clause")
        if v is None:
            continue
        by_layer.setdefault(int(layer), []).append(float(v))
    return {l: {"mean": sum(v) / len(v), "max": max(v), "n_heads": len(v)} for l, v in sorted(by_layer.items())}


def roles_summary(rj) -> dict:
    if not rj:
        return {"available": False}
    return {"available": True, "variant": rj.get("variant"), "counts": rj.get("counts"),
            "flavour_counts": rj.get("flavour_counts"), "missing_views": rj.get("missing_views"),
            "merged_from": rj.get("merged_from"), "n_components": rj.get("n_components")}


def task_results(t: str, root: str, sets: dict, prov: dict, deciding: dict, sweep: dict) -> dict:
    cells = {}
    for cell in list(FAMILY_CELLS) + [f"seg_{s}" for s in p2_jobs.SEGMENTS]:
        try:
            cells[cell] = cell_dir(root, cell, t)
        except FileNotFoundError as exc:
            cells[cell] = None
            print("  missing:", exc)
    rows = {c: load_rows(cells[c]) for c in HEAD_CELLS if cells[c]}
    mem = membership(t, sets, prov)
    comp = p2_jobs.composition_sets(t, sets)
    fam_cells = {c: load_groups(cells[c]) for c in FAMILY_CELLS if cells[c] and os.path.exists(os.path.join(cells[c], "knockout", "groups.json"))}
    seg_cells = {s: load_groups(cells[f"seg_{s}"]) for s in p2_jobs.SEGMENTS if cells.get(f"seg_{s}")}
    seg = segment_matrix(seg_cells)
    late = {("head", l, h) for l, h in comp[f"late_HmD_{t}"]}
    rank = [r["label"] for r in sorted(sweep["components"], key=lambda r: r["signed_rank"])]
    out = {
        "task": t, "cells": {c: (os.path.relpath(p, REPO) if p else None) for c, p in cells.items()},
        "membership_counts": {c: sum(1 for v in mem.values() if v[c]) for c in MEMBERSHIP},
        "n_components": len(mem),
        "b_reader": b_reader(rows["d"]) if "d" in rows else None,
        "b_reader_I": b_reader(rows["i"]) if "i" in rows else None,
        "c_honest": c_honest(late, rows.get("d", []), rows.get("h", []), rows.get("f", [])),
        "i_vs_d": i_vs_d([tuple(k) for k in deciding["heads"]], rows.get("d", []), rows.get("i", [])),
        "families": family_table(fam_cells),
        "segments": {"matrix": seg, "pre_clause_check": pre_clause_check(seg, p2_jobs.PRE_CLAUSE),
                     "informative": list(p2_jobs.POST_CLAUSE)},
        "clause_mass_by_layer": {c: clause_mass_by_layer(cells[c]) for c in HEAD_CELLS if cells[c]},
        "roles": {c: roles_summary(load_roles(cells[c])) for c in HEAD_CELLS if cells[c]},
        "ct_proposal": ct_proposal(t, sets, deciding, rank),
    }
    return out, rows, mem, cells


# ------------------------------------------------------------------ writing

def _f(x, nd=3):
    if x is None:
        return "-"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return f"{x:.{nd}f}" if abs(x) >= 10 ** -nd or x == 0 else f"{x:.1e}"
    return str(x)


def write_curated(curated: str, t: str, rows: dict, mem: dict, cells: dict) -> None:
    os.makedirs(os.path.join(curated, "roles"), exist_ok=True)
    for cell, rs in rows.items():
        cols = list(rs[0].keys()) if rs else []
        path = os.path.join(curated, f"{t}_{cell}_head_table.csv")
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols + [f"membership.{c}" for c in MEMBERSHIP])
            for r in rs:
                m = mem.get(key_of(r), {})
                w.writerow([r.get(c) for c in cols] + [int(bool(m.get(c, False))) for c in MEMBERSHIP])
        rpath = os.path.join(cells[cell], roles.SUBDIR, roles.JSON_NAME)
        if os.path.exists(rpath):
            shutil.copyfile(rpath, os.path.join(curated, "roles", f"{t}_{cell}.json"))


def write_long_tables(curated: str, results: dict) -> None:
    with open(os.path.join(curated, "families.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "family", "cell", "n_components", "mean_drop", "standard_error", "d", "accuracy",
                    "accuracy_drop", "clean_logit_difference", "target_direction", "rcls"])
        for t, res in results["tasks"].items():
            for fam, by in res["families"].items():
                cls = (by.get("rcls") or {}).get("class")
                for cell, v in by.items():
                    if cell == "rcls":
                        continue
                    w.writerow([t, fam, cell, v["n_components"], v["mean_drop"], v["standard_error"], v["d"],
                                v["accuracy"], v["accuracy_drop"], v["clean_logit_difference"], v["target_direction"], cls])
    with open(os.path.join(curated, "segments.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "label", "segment", "pre_clause", "mean_drop", "standard_error", "accuracy_drop"])
        for t, res in results["tasks"].items():
            for label, by in res["segments"]["matrix"].items():
                for seg in p2_jobs.SEGMENTS:
                    if seg in by:
                        v = by[seg]
                        w.writerow([t, label, seg, int(seg in p2_jobs.PRE_CLAUSE), v["mean_drop"], v["standard_error"],
                                    v["accuracy_drop"]])


def markdown(results: dict) -> str:
    L = ["# Phase-2 results (ticket 04)", "",
         f"Generated by `outputs/_launch_mechanism_analysis/p2_results.py` from `{results['root']}`. "
         "Sign conventions: on D and I cells a positive drop or DLA supports the cell's target (the deceptive answer "
         "on D, the inverted answer on I); on H and F cells positive supports the honest answer (ADR-0002). "
         "Statistics: Freeman-Halton exact test (two-sided, head level) and the exact one-sided binomial upper tail.", ""]
    for t, res in results["tasks"].items():
        L += [f"## {t}", "", "Components in U': " + ", ".join(f"{c} {n}" for c, n in res["membership_counts"].items())
              + f" (total {res['n_components']})", ""]
        chk = res["segments"]["pre_clause_check"]
        L += [f"**Pre-clause sanity assertion (R16):** {'PASS' if chk['ok'] else 'FAIL'}; max |drop| "
              f"{_f(chk['max_abs_drop'], 6)}; non-zero entries {len(chk['nonzero'])}.", ""]
        # families
        L += ["### Family knockouts", "", "| family | n | " + " | ".join(FAMILY_CELLS) + " | R-cls (d/h/f) |",
              "|---|---|" + "---|" * len(FAMILY_CELLS) + "---|"]
        for fam, by in res["families"].items():
            n = next((v["n_components"] for c, v in by.items() if c != "rcls"), "-")
            cells = [f"{_f(by[c]['mean_drop'])} ± {_f(by[c]['standard_error'])}" if c in by else "-" for c in FAMILY_CELLS]
            L.append(f"| {fam} | {n} | " + " | ".join(cells) + f" | {(by.get('rcls') or {}).get('class', '-')} |")
        L.append("")
        # segments
        L += ["### Segment-resolved neutral-twin knockout of the S2p top 20 (informative Segments)", ""]
        segs = [s for s in p2_jobs.POST_CLAUSE if any(s in by for by in res["segments"]["matrix"].values())]
        L += ["| Component | " + " | ".join(segs) + " |", "|---|" + "---|" * len(segs)]
        for label, by in res["segments"]["matrix"].items():
            L.append(f"| {label} | " + " | ".join(_f(by[s]["mean_drop"]) if s in by else "-" for s in segs) + " |")
        L.append("")
        # B-reader
        b = res["b_reader"]
        if b:
            L += ["### B-reader (D cell)", "",
                  f"Signature heads {b['n_signature']} of {b['n_measured']} measured; in layers 8-17: {b['n_in_8_17']} "
                  f"(share {_f(b['share_8_17'])} vs base rate {_f(BASE_RATE)}); one-sided binomial p = {_f(b['p'], 4)}.",
                  "", "| head | layer | clause-mass drop | SE |", "|---|---|---|---|"]
            L += [f"| {h['label']} | {h['layer']} | {_f(h['drop'])} | {_f(h['se'])} |" for h in b["signature_heads"]]
            L += ["", "L13 heads: " + "; ".join(f"{k}: drop {_f(v['drop'])} ± {_f(v['se'])}, signature {_f(v['signature'])}"
                                                for k, v in b["l13"].items()), ""]
        # C-honest
        ch = res["c_honest"]
        L += ["### C-honest (late H-D heads)", "",
              f"{ch['n']} heads; write honest on H and F: {ch['n_writes_honest']}; suppressed under pressure: "
              f"{ch['n_suppressed']}.", "",
              "| head | DLA H | DLA F | honest DLA D (pressure) | honest DLA D (twin) | suppression |",
              "|---|---|---|---|---|---|"]
        L += [f"| {k} | {_f(v['dla_H'])} | {_f(v['dla_F'])} | {_f(v['honest_dla_D_pressure'])} | "
              f"{_f(v['honest_dla_D_twin'])} | {_f(v['suppression'])} |" for k, v in ch["heads"].items()]
        L.append("")
        # I vs D
        iv = res["i_vs_d"]
        L += ["### I vs D per deciding-set head", "",
              f"{iv['n']} heads; B2 signature on D {iv['n_signature_D']}, on I {iv['n_signature_I']}, both "
              f"{iv['n_signature_both']}.", "",
              "| head | top seg D | top seg I | B2 drop D | B2 drop I | DLA diff D | DLA diff I |", "|---|---|---|---|---|---|---|"]
        L += [f"| {k} | {_f(v['D']['top_segment'])} | {_f(v['I']['top_segment'])} | {_f(v['D']['b2_drop'])} | "
              f"{_f(v['I']['b2_drop'])} | {_f(v['D']['dla_differential'])} | {_f(v['I']['dla_differential'])} |"
              for k, v in iv["heads"].items()]
        L.append("")
        # roles
        L += ["### Roles", ""]
        for c, r in res["roles"].items():
            if r.get("available"):
                L.append(f"- {c}: {r['counts']}; unknown flavours {r['flavour_counts']}; missing views {r['missing_views']}")
            else:
                L.append(f"- {c}: roles pass not run")
        L.append("")
        ct = res["ct_proposal"]
        L += ["### Proposed C_t for phase 3", "", f"Sizes: {ct['sizes']}", f"MLPs: {', '.join(ct['mlps'])}", ""]
    cr = results["c_reads"]
    L += ["## C-reads (exclusive sets' top-Segment groups, own D cell)", "",
          "| task | " + " | ".join(cr["groups"]) + " |", "|---|" + "---|" * len(cr["groups"])]
    L += [f"| {t} | " + " | ".join(str(x) for x in row) + " |" for t, row in zip(cr["tasks"], cr["table"])]
    L += ["", f"Fisher exact p = {_f(cr['p'], 4)} ({cr['test']}).", ""]
    for t in TASKS:
        L.append(f"- {t}: " + "; ".join(f"{h['label']} {h['segment']} ({_f(h['mass'])})" for h in cr["heads"][t]))
    L.append("")
    return "\n".join(L)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=os.path.join(REPO, ROOT))
    p.add_argument("--reports", default=REPORTS)
    p.add_argument("--curated", default=CURATED)
    p.add_argument("--p1-root", default=os.path.join(REPO, p2_jobs.P1_ROOT))
    p.add_argument("--readings", default=os.path.join(REPO, p2_operands.READINGS))
    p.add_argument("--tasks", default=",".join(TASKS))
    a = p.parse_args(argv)
    sets = p2_jobs.head_sets()
    deciding = p2_operands.deciding_sets(load_json(a.readings))
    results = {"root": os.path.relpath(a.root, REPO), "tasks": {}}
    rows_by_task = {}
    os.makedirs(a.curated, exist_ok=True)
    for t in a.tasks.split(","):
        prov = load_json(os.path.join(REPO, p2_jobs.OPERAND.format(t=t), "provenance.json"))
        sweep = load_json(p2_jobs.sweep_path(a.p1_root, t))
        res, rows, mem, cells = task_results(t, a.root, sets, prov, deciding[t], sweep)
        results["tasks"][t] = res
        rows_by_task[t] = rows.get("d", [])
        write_curated(a.curated, t, rows, mem, cells)
        print(t, "pre-clause", res["segments"]["pre_clause_check"]["ok"], "B-reader p", (res["b_reader"] or {}).get("p"))
    comp = {t: {("head", l, h) for l, h in p2_jobs.composition_sets(t, sets)[f"excl_{t}"]} for t in TASKS}
    results["c_reads"] = c_reads(rows_by_task, comp)
    results["c_reads_twin_paired_top_segment"] = c_reads(rows_by_task, comp, segment_col=TWIN_TOP_SEGMENT, mass_col=TOP_MASS)
    write_long_tables(a.curated, results)
    os.makedirs(a.reports, exist_ok=True)
    with open(os.path.join(a.reports, "04-phase2-results.json"), "w") as f:
        json.dump(results, f, indent=1, default=str)
    with open(os.path.join(a.reports, "04-phase2-results.md"), "w") as f:
        f.write(markdown(results))
    readings = {t: {k: v for k, v in res.items() if k in ("b_reader", "b_reader_I", "c_honest", "i_vs_d", "ct_proposal",
                                                          "membership_counts", "roles")}
                for t, res in results["tasks"].items()}
    readings["c_reads"] = results["c_reads"]
    with open(os.path.join(a.curated, "p2_readings.json"), "w") as f:
        json.dump(readings, f, indent=1, default=str)
    print("wrote", os.path.join(a.reports, "04-phase2-results.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
