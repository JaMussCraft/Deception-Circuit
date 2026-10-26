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
                      DLA under pressure against the twin, both over the paired instances; suppressed (>= 50 %
                      smaller, same sign) and flipped (negative under pressure) counted apart (C-honest)
    i_vs_d            the B2 signature and the paired DLA on I against D per head of the deciding set (R-inv input)
    family_table      the composition-set family knockouts per cell (C3, RQ-A's component part), with the R-cls
                      bands applied to each family's joint drop (descriptive; the per-head R-cls is phase 1's)
    c2_reads          what the exclusives and the D-H heads read and write on D (C2)
    cell_check        scripts/check_cell.py's views per head cell (present / missing / BROKEN)
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
from component_analysis import dla, roles  # noqa: E402

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


def _twin_dla_column(name: str) -> str:
    """A twin DLA head-table column, `dla.<name>`, checked against the DLA analysis's own column list."""
    if name not in dla.TWIN_COLUMN_SOURCES:
        raise KeyError(f"{name!r} is not a twin DLA column; component_analysis/dla.py writes "
                       f"{sorted(dla.TWIN_COLUMN_SOURCES)}")
    return f"{dla.NAME}.{name}"


# the column names the roles pass reads come from roles.py; the two twin DLA columns the roles pass does not read
# (the twins' own DLA and the paired pressure DLA over the same instances) come from dla.py's column list
TOP_SEGMENT, TOP_MASS = roles.TOP_SEGMENT, roles.TOP_MASS
B2_DROP, B2_DROP_SE = roles.B2_DROP, roles.B2_DROP_SE
DLA, DLA_SE = roles.DLA, roles.DLA_SE
DLA_DIFF_TWIN, DLA_DIFF_TWIN_SE = roles.DLA_DIFFERENTIAL_TWIN, roles.DLA_DIFFERENTIAL_TWIN_SE
DLA_TWIN = _twin_dla_column("neutral_twin_paired")
DLA_PRESSURE_PAIRED = _twin_dla_column("pressure_neutral_twin_paired")
#: the readings beyond the ticket's list, written and labelled exploratory everywhere they appear
EXPLORATORY = ("families: d_twinko (D under the neutral twin, post-clause) and i (I under the twin)",
               "b_reader_I: the B2 signature on the I cell",
               "c_reads_top_prompt_segment: C-reads with the attention sink left out",
               "b_reader p_against_measured_share: the binomial against U''s own layer-8-17 share",
               "family-level R-cls: the R-cls bands applied to a family's joint drop")


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
    # the deciding set is its members (heads and MLP blocks); an older provenance carries the heads only
    sk = {parse_label(h) for h in operand_prov.get("members") or operand_prov["heads"]}
    ct = {("mlp", int(l), 0) for l in operand_prov["mlp_layers"]}
    out = {}
    for layer, head in sorted(U | {(l, h) for k, l, h in sk if k == "head"}):
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
    # `unestablished` is the absence of a read group (docs/component-roles.md), not a group: those heads are
    # counted beside the table and left out of the test
    groups = [g for g in READ_GROUPS if any(counts[t].get(g) for t in TASKS)]
    table = [[counts[t].get(g, 0) for g in groups] for t in TASKS]
    return {"groups": groups, "tasks": list(TASKS), "table": table, "counts": counts, "p": fisher_exact_rxc(table),
            "n_unestablished": {t: counts[t].get("unestablished", 0) for t in TASKS},
            "n_in_table": {t: sum(counts[t].get(g, 0) for g in groups) for t in TASKS},
            "heads": heads, "test": "Freeman-Halton exact, two-sided, head level (not clustered), over the four "
                                    "established read groups; unestablished reads (the attention sink) left out"}


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
    # the pre-registered base rate is 10 of 32 layers; U' holds heads in fewer layers, so the share of *measured*
    # heads that sit in layers 8-17 is reported beside it for the reader
    measured_in_band = sum(1 for row in rows if row.get("kind") == "head" and b2_signature(row, floor=floor, z=z) is not None
                           and 8 <= int(row["layer"]) <= 17)
    return {"floor": floor, "z": z, "n_measured": measured, "n_signature": len(sig), "n_in_8_17": k,
            "share_8_17": (k / len(sig)) if sig else None, "base_rate": BASE_RATE,
            "measured_share_8_17": (measured_in_band / measured) if measured else None,
            "p": binomial_upper_tail(k, len(sig), BASE_RATE) if sig else None,
            "p_against_measured_share": (binomial_upper_tail(k, len(sig), measured_in_band / measured)
                                         if sig and measured else None),
            "signature_heads": sig, "l13": l13,
            "test": "one-sided binomial upper tail of the layer-8-17 count among signature heads against 10/32 "
                    "(pre-registered); p_against_measured_share uses U''s own layer-band share as the base rate"}


def c_honest(late_keys, rows_d, rows_h, rows_f, *, z: float = 2.0) -> dict:
    """C-honest over the late H-D heads. On H and F the DLA is read in the cell's own (honest) direction; on D the
    metric is deceptive-positive, so the honest direction is the negation."""
    D, H, F = _by_key(rows_d), _by_key(rows_h), _by_key(rows_f)
    heads = {}

    def positive(row):
        """DLA > 0, and >= z SE when the table carries the SE (sign-only otherwise, said in the output)."""
        v, se = row.get(DLA), row.get(DLA_SE)
        if v is None:
            return None, True
        if se is None:
            return v > 0, True
        return bool(v > 0 and v >= z * se), False

    for key in sorted(late_keys):
        h, f = H.get(key, {}).get(DLA), F.get(key, {}).get(DLA)
        h_pos, h_sign_only = positive(H.get(key, {}))
        f_pos, f_sign_only = positive(F.get(key, {}))
        # both sides of the D comparison come from the paired columns (the same instances): the pressure DLA over
        # the paired instances and the twins' own DLA
        dp, dt = D.get(key, {}).get(DLA_PRESSURE_PAIRED), D.get(key, {}).get(DLA_TWIN)
        hp = -dp if dp is not None else None
        htw = -dt if dt is not None else None
        supp = (1.0 - hp / htw) if (hp is not None and htw is not None and htw > 0) else None
        suppressed = bool(supp is not None and 0.5 <= supp <= 1.0)       # reduced by half or more, same sign
        flipped = bool(supp is not None and supp > 1.0)                  # writes the deceptive answer under pressure
        heads[label_of(key)] = {"dla_H": h, "dla_F": f, "honest_dla_D_pressure": hp, "honest_dla_D_twin": htw,
                                "suppression": supp,
                                "writes_honest_on_H_and_F": bool(h_pos and f_pos),
                                "suppressed": suppressed, "flipped": flipped,
                                "reduced_at_least_half": suppressed or flipped,
                                "holds": bool(h_pos and f_pos) and (suppressed or flipped)}
        if h_sign_only or f_sign_only:
            heads[label_of(key)]["sign_only"] = True
    return {"n": len(heads), "n_writes_honest": sum(v["writes_honest_on_H_and_F"] for v in heads.values()),
            "n_suppressed": sum(v["suppressed"] for v in heads.values()),
            "n_flipped": sum(v["flipped"] for v in heads.values()),
            "n_reduced_at_least_half": sum(v["reduced_at_least_half"] for v in heads.values()),
            "n_holds": sum(v["holds"] for v in heads.values()), "heads": heads,
            "rule": f"writes honest = DLA > 0 and >= {z} SE on both H and F (sign-only where the SE column is absent, "
                    "flagged sign_only); on D the honest-direction DLA is read over the paired instances "
                    "(dla.pressure_neutral_twin_paired against dla.neutral_twin_paired, negated); suppressed = "
                    "reduced by >= 50 % and still honest-signed (0.5 <= suppression <= 1); flipped = negative under "
                    "pressure (suppression > 1); the spec's '>= 50 % smaller' is suppressed or flipped; holds = "
                    "writes honest and >= 50 % smaller (both clauses of C-honest on one head)"}


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
    level = {lv["level"]: lv for lv in cond.get("levels") or []}.get("all") or {}
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


SINK = "unsegmented"


def top_segment_excluding(profile: dict, exclude=(SINK,)):
    """(segment, mass) with the largest mass among the Segments not in `exclude`; (None, None) on an empty profile.
    The attention sink (`unsegmented`, the BOS token) takes the top spot on many heads, so C-reads is also read on
    the top *prompt* Segment (exploratory, beside the pre-registered top-Segment read)."""
    best = None
    for seg, mass in profile.items():
        if seg in exclude or mass is None:
            continue
        if best is None or mass > best[1]:
            best = (seg, float(mass))
    return best or (None, None)


def profiles(cdir: str, condition: str = "pressure") -> dict:
    """{key: {segment: mass}} at the column query position for one attention condition of a cell."""
    path = os.path.join(cdir, "attention", "patterns.json")
    if not os.path.exists(path):
        return {}
    pay = load_json(path)
    cond = next((c for c in pay["conditions"] if c["name"] == condition), None)
    if not cond:
        return {}
    level = {lv["level"]: lv for lv in cond.get("levels") or []}.get("all") or {}
    masses = level.get("masses") or {}
    query = pay["column_query_position"]
    return {tuple(c["key"]): ((masses.get(c["name"]) or {}).get(query) or {}) for c in pay["components"]}


def rows_with_top_prompt_segment(rows, profs: dict) -> list:
    """The rows with the top-Segment columns replaced by the top prompt Segment (sink excluded)."""
    out = []
    for r in rows:
        seg, mass = top_segment_excluding(profs.get(key_of(r), {}))
        out.append({**r, TOP_SEGMENT: seg, TOP_MASS: mass})
    return out


def cell_check(cdir: str, views=None) -> dict:
    """scripts/check_cell.py's views over one cell: present, missing (with the view's note) or BROKEN (a malformed
    file). `views` defaults to check_cell.VIEWS; the import is lazy so the readings stay importable without it."""
    if views is None:
        scripts = os.path.join(REPO, "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        import check_cell  # noqa: E402

        views = check_cell.VIEWS
    status, notes = {}, {}
    for label, view_of in views:
        try:
            view = view_of(cdir)
        except Exception as error:  # noqa: BLE001 -- a malformed file is a failure, not an absence (check_cell.py)
            status[label], notes[label] = "BROKEN", f"{type(error).__name__}: {error}"
            continue
        if view:
            status[label] = "present"
        else:
            status[label], notes[label] = "missing", getattr(view, "note", "")
    return {"views": status, "notes": notes, "broken": [k for k, v in status.items() if v == "BROKEN"]}


def roles_summary(rj) -> dict:
    if not rj:
        return {"available": False}
    return {"available": True, "variant": rj.get("variant"), "counts": rj.get("counts"),
            "flavour_counts": rj.get("flavour_counts"), "missing_views": rj.get("missing_views"),
            "merged_from": rj.get("merged_from"), "n_components": rj.get("n_components")}


def c2_reads(rows_d, profs: dict, mem: dict, families=("excl_t", "DmH_t")) -> dict:
    """C2: what the exclusives and the D-H heads read and write on D: top Segment at the Readout (pressure),
    the top prompt Segment (sink left out), DLA under pressure and on the paired twin."""
    D = _by_key(rows_d)
    out = {}
    for fam in families:
        rows = []
        for key, m in mem.items():
            if key[0] != "head" or not m.get(fam):
                continue
            r = D.get(key, {})
            seg, mass = top_segment_excluding(profs.get(key, {}))
            rows.append({"label": label_of(key), "layer": key[1], "top_segment": r.get(TOP_SEGMENT),
                         "top_mass": r.get(TOP_MASS), "top_prompt_segment": seg, "top_prompt_mass": mass,
                         "group": read_group(r.get(TOP_SEGMENT)), "prompt_group": read_group(seg),
                         "dla_pressure": r.get(DLA), "dla_pressure_se": r.get(DLA_SE),
                         "dla_pressure_paired": r.get(DLA_PRESSURE_PAIRED), "dla_twin": r.get(DLA_TWIN),
                         "b2_drop": r.get(B2_DROP), "core": bool(m.get("core"))})
        out[fam] = rows
    return out


def task_results(t: str, root: str, sets: dict, prov: dict, deciding: dict, sweep: dict) -> tuple:
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
        "c2_reads": c2_reads(rows.get("d", []), profiles(cells["d"]) if cells.get("d") else {}, mem),
        "roles": {c: roles_summary(load_roles(cells[c])) for c in HEAD_CELLS if cells[c]},
        "check_cell": {c: cell_check(os.path.abspath(cells[c])) for c in HEAD_CELLS if cells[c]},
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
         "Sign conventions: every drop and DLA is read in its cell's own target direction (`target_direction` in "
         "the cell's knockout/groups.json: `deceptive` on D and I, where I's target slot holds the inverted answer; "
         "`honest` on H and F): a positive value supports the cell's target. The DLA reads the same target and "
         "distractor fields, so its metric text, which always says 'deceptive', is honest-positive on H and F. "
         "Statistics: Freeman-Halton exact test (two-sided, head level) and the exact one-sided binomial upper tail. "
         "Columns marked exploratory were not pre-registered.", ""]
    if results.get("exploratory"):
        L += ["Exploratory (beyond the ticket's list; never decides a reading):", ""]
        L += [f"- {x}" for x in results["exploratory"]] + [""]
    p1 = results.get("phase1_rcls") or {}
    if p1.get("rqa"):
        L += [f"Pre-registered per-head R-cls (RQ-A), graded in phase 1 (`{p1['source']}`, rqa): "
              + "; ".join(f"{t} core shared {v['core_shared']}/{v['core_n']} ({'holds' if v['core_holds'] else 'fails'}),"
                          f" exclusives deception-leaning {v['excl_deception_leaning']}/{v['excl_n']} "
                          f"({'holds' if v['excl_holds'] else 'fails'})" for t, v in p1["rqa"].items()) + ".", ""]
    for t, res in results["tasks"].items():
        L += [f"## {t}", "", "Components in U': " + ", ".join(f"{c} {n}" for c, n in res["membership_counts"].items())
              + f" (total {res['n_components']})", ""]
        chk = res["segments"]["pre_clause_check"]
        L += [f"**Pre-clause sanity assertion (R16):** {'PASS' if chk['ok'] else 'FAIL'}; max |drop| "
              f"{_f(chk['max_abs_drop'], 6)}; non-zero entries {len(chk['nonzero'])}.", ""]
        cc = res.get("check_cell") or {}
        if cc:
            labels = list(next(iter(cc.values()))["views"])
            broken = [f"{c}: {v}" for c, r in cc.items() for v in r["broken"]]
            L += ["### scripts/check_cell.py on the head cells", "",
                  "Missing views are the analyses phase 2 does not run (single knockout, sweeps and path patching come "
                  "from phases 1 and 3; the family knockout here is the groups pass, `knockout/groups.json`, which "
                  "check_cell does not list; the dla paired scatter is the honest-instruction scatter, a condition "
                  "v2 cells do not run).", "",
                  "| cell | " + " | ".join(labels) + " |", "|---|" + "---|" * len(labels)]
            L += [f"| {c} | " + " | ".join(r["views"].get(v, "-") for v in labels) + " |" for c, r in cc.items()]
            L += ["", "BROKEN views: " + ("; ".join(broken) if broken else "none") + ".", ""]
        # families
        L += ["### Family knockouts", "",
              "Columns d, h, f are the spec's family knockouts; d_twinko and i are exploratory. The R-cls column "
              "applies the R-cls bands to the family's joint drop and is descriptive: the pre-registered per-head "
              "R-cls classes are phase 1's (reports/03-phase1-results.json, class_counts).", "",
              "| family | n | " + " | ".join(FAMILY_CELLS) + " | family-level R-cls (descriptive) |",
              "|---|---|" + "---|" * len(FAMILY_CELLS) + "---|"]
        for fam, by in res["families"].items():
            n = next((v["n_components"] for c, v in by.items() if c != "rcls"), "-")
            cells = [f"{_f(by[c]['mean_drop'])} ± {_f(by[c]['standard_error'])}" if c in by else "-" for c in FAMILY_CELLS]
            L.append(f"| {fam} | {n} | " + " | ".join(cells) + f" | {(by.get('rcls') or {}).get('class', '-')} |")
        L.append("")
        # per-layer clause mass (spec 2.9 descriptive)
        cm = res["clause_mass_by_layer"].get("d") or {}
        if cm:
            layers = sorted(cm)
            L += ["### Pressure-clause attention mass per layer (D cell, Readout query; descriptive, spec 2.9)", "",
                  "| layer | " + " | ".join(str(l) for l in layers) + " |", "|---|" + "---|" * len(layers),
                  "| mean over U' heads | " + " | ".join(_f(cm[l]["mean"]) for l in layers) + " |",
                  "| max head | " + " | ".join(_f(cm[l]["max"]) for l in layers) + " |",
                  "| heads | " + " | ".join(str(cm[l]["n_heads"]) for l in layers) + " |", ""]
        # C2: the exclusives' and the (D-H)-core heads' reads and writes
        for fam, title in (("excl_t", "the exclusives"), ("DmH_t", "the D-H heads (core column: in the core; the "
                                                                     "rest are (D-H)-core)")):
            rows_c2 = res["c2_reads"].get(fam) or []
            if not rows_c2:
                continue
            L += [f"### C2: what {title} read and write (D cell)", "",
                  "The top prompt Segment (sink left out) is exploratory. DLA is deceptive-positive on D.", "",
                  "| head | core | top Segment (mass) | top prompt Segment (mass; sink left out) | DLA pressure | "
                  "DLA pressure (paired) | DLA twin | B2 drop |", "|---|---|---|---|---|---|---|---|"]
            L += [f"| {r['label']} | {_f(r.get('core'))} | {r['top_segment']} ({_f(r['top_mass'])}) | "
                  f"{r['top_prompt_segment']} ({_f(r['top_prompt_mass'])}) | {_f(r['dla_pressure'])} | "
                  f"{_f(r['dla_pressure_paired'])} | {_f(r['dla_twin'])} | {_f(r['b2_drop'])} |" for r in rows_c2]
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
            named = b["l13"]
            L += ["### B-reader (D cell)", "",
                  "Two pre-registered clauses (spec 2.6): (i) the binomial on the layer-8-17 share; (ii) L13H5, "
                  "L13H20 and L13H21 show the signature. (ii): "
                  + "; ".join(f"{k} {'yes' if v['signature'] else 'no'}" for k, v in named.items()) + ".", "",
                  f"(i) Signature heads {b['n_signature']} of {b['n_measured']} measured; in layers 8-17: {b['n_in_8_17']} "
                  f"(share {_f(b['share_8_17'])} vs base rate {_f(BASE_RATE)}); one-sided binomial p = {_f(b['p'], 4)}; "
                  f"against U''s own layer-8-17 share of measured heads ({_f(b['measured_share_8_17'])}) p = "
                  f"{_f(b['p_against_measured_share'], 4)}.",
                  "", "| head | layer | clause-mass drop | SE |", "|---|---|---|---|"]
            L += [f"| {h['label']} | {h['layer']} | {_f(h['drop'])} | {_f(h['se'])} |" for h in b["signature_heads"]]
            L += ["", "L13 heads: " + "; ".join(f"{k}: drop {_f(v['drop'])} ± {_f(v['se'])}, signature {_f(v['signature'])}"
                                                for k, v in b["l13"].items()), ""]
        bi = res.get("b_reader_I")
        if bi:
            L += ["### B-reader on the I cell (exploratory; not a B-reader test)", "",
                  f"Signature heads {bi['n_signature']} of {bi['n_measured']} measured; in layers 8-17: "
                  f"{bi['n_in_8_17']} (share {_f(bi['share_8_17'])}); binomial p against 10/32 = {_f(bi['p'], 4)}. "
                  "L13 heads: " + ("; ".join(f"{k} {'yes' if v['signature'] else 'no'}" for k, v in bi["l13"].items())
                                   or "-") + ".", ""]
        # C-honest
        ch = res["c_honest"]
        L += ["### C-honest (late H-D heads)", "",
              f"{ch['n']} heads; write honest on H and F (DLA > 0, >= 2 SE): {ch['n_writes_honest']}; on D, honest-"
              f"direction DLA over the paired instances: suppressed (reduced >= 50 %, still honest-signed) "
              f"{ch['n_suppressed']}, flipped (negative under pressure) {ch['n_flipped']}; either, the spec's "
              f"'>= 50 % smaller': {ch['n_reduced_at_least_half']}; both clauses on one head (writes honest and "
              f">= 50 % smaller): {ch['n_holds']}. A dash in suppression means the twin DLA is not honest-signed.", "",
              "| head | DLA H | DLA F | honest DLA D (pressure, paired) | honest DLA D (twin) | suppression | state | "
              "writes honest on H and F | both clauses |",
              "|---|---|---|---|---|---|---|---|---|"]
        L += [f"| {k} | {_f(v['dla_H'])} | {_f(v['dla_F'])} | {_f(v['honest_dla_D_pressure'])} | "
              f"{_f(v['honest_dla_D_twin'])} | {_f(v['suppression'])} | "
              f"{'flipped' if v['flipped'] else 'suppressed' if v['suppressed'] else '-'} | "
              f"{_f(v['writes_honest_on_H_and_F'])} | {_f(v.get('holds'))} |"
              for k, v in ch["heads"].items()]
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
    for key, title in (("c_reads", "C-reads (exclusive sets' top-Segment groups, own D cell; pre-registered)"),
                       ("c_reads_top_prompt_segment", "C-reads on the top prompt Segment (attention sink left out; exploratory)")):
        cr = results.get(key)
        if not cr:
            continue
        L += [f"## {title}", "",
              "| task | " + " | ".join(cr["groups"]) + " |", "|---|" + "---|" * len(cr["groups"])]
        L += [f"| {t} | " + " | ".join(str(x) for x in row) + " |" for t, row in zip(cr["tasks"], cr["table"])]
        L += ["", f"Fisher exact p = {_f(cr['p'], 4)} ({cr['test']}). Heads in the table: "
              + ", ".join(f"{t} {cr['n_in_table'][t]}" for t in TASKS) + "; unestablished (left out): "
              + ", ".join(f"{t} {cr['n_unestablished'][t]}" for t in TASKS) + ".", ""]
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
    results = {"root": os.path.relpath(a.root, REPO), "tasks": {}, "exploratory": list(EXPLORATORY)}
    p1 = os.path.join(a.reports, "03-phase1-results.json")
    if os.path.exists(p1):
        # the pre-registered per-head R-cls grading is phase 1's (sweeps S1, S5, S6); quoted here, not recomputed
        results["phase1_rcls"] = {"source": os.path.basename(p1), "rqa": load_json(p1).get("rqa")}
    rows_by_task, prompt_rows_by_task = {}, {}
    os.makedirs(a.curated, exist_ok=True)
    for t in a.tasks.split(","):
        prov = load_json(os.path.join(REPO, p2_jobs.OPERAND.format(t=t), "provenance.json"))
        sweep = load_json(p2_jobs.sweep_path(a.p1_root, t))
        res, rows, mem, cells = task_results(t, a.root, sets, prov, deciding[t], sweep)
        results["tasks"][t] = res
        rows_by_task[t] = rows.get("d", [])
        prompt_rows_by_task[t] = rows_with_top_prompt_segment(rows.get("d", []), profiles(cells["d"])) if cells.get("d") else []
        write_curated(a.curated, t, rows, mem, cells)
        print(t, "pre-clause", res["segments"]["pre_clause_check"]["ok"], "B-reader p", (res["b_reader"] or {}).get("p"))
    comp = {t: {("head", l, h) for l, h in p2_jobs.composition_sets(t, sets)[f"excl_{t}"]} for t in TASKS}
    results["c_reads"] = c_reads(rows_by_task, comp)
    results["c_reads_top_prompt_segment"] = c_reads(prompt_rows_by_task, comp)
    results["c_reads_top_prompt_segment"]["note"] = ("exploratory: the top Segment with the attention sink " \
                                                      "(unsegmented) left out, from attention/patterns.json")
    write_long_tables(a.curated, results)
    os.makedirs(a.reports, exist_ok=True)
    with open(os.path.join(a.reports, "04-phase2-results.json"), "w") as f:
        json.dump(results, f, indent=1, default=str)
    with open(os.path.join(a.reports, "04-phase2-results.md"), "w") as f:
        f.write(markdown(results))
    readings = {t: {k: v for k, v in res.items() if k in ("b_reader", "b_reader_I", "c_honest", "i_vs_d", "ct_proposal",
                                                          "membership_counts", "roles", "check_cell")}
                for t, res in results["tasks"].items()}
    readings["c_reads"] = results["c_reads"]
    readings["exploratory"] = results["exploratory"]
    with open(os.path.join(a.curated, "p2_readings.json"), "w") as f:
        json.dump(readings, f, indent=1, default=str)
    print("wrote", os.path.join(a.reports, "04-phase2-results.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
