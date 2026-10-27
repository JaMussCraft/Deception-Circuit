#!/usr/bin/env python3
"""
p3_results.py -- the phase-3 results tables and curated copies (ticket 05; spec section 2.3, 2.6, 2.7 C3, R6, R11(g),
R14, R28). CPU only; reads the fetched phase-3 cells after p3_merge.py and p3_roles.py.

Per task (cells `outputs/_analyses/mechanism-analysis-p3/{d,d_is}/Ct__leaf/<t>_v2`):

- the A' adjudication of the deciding set (far, ser: pre-registered; sdr, reading B: descriptive), p3_logic.adjudicate
  with the S2p single effects (phase-1 S2p sweep, mean drop) as weights and phase 1C's routing share (c);
- B-selector: L17H24-27 and the core's L24 heads, category and the per-receiver totals (Q vs K+V, descriptive);
- where the pressure enters (B4): senders whose neutral-twin paths into C_t clear the floor, with their positions;
- completeness: the twin sweep's direct paths into the Readout, inside vs outside C_t;
- roles (roles.json of cell d after p3_roles.py) per task and per composition part (C3);
- checks: the twin sweep file exists, its sample is the grid's, no pre-clause top Segment, the Segment pass cost.

Writes reports/05-phase3-results.{md,json} under --reports and the curated copies under
docs/research/mechanism-analysis/phase3/ (head tables, categories, the readings JSON, roles).

usage (from the repository root):
    python outputs/_launch_mechanism_analysis/p3_results.py [--root DIR] [--p1-root DIR] [--reports DIR] [--curated DIR]
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
for _p in (HERE, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import p2_jobs  # noqa: E402
import p3_jobs  # noqa: E402
import p3_logic as L  # noqa: E402
import p3_merge  # noqa: E402
from component_analysis import head_table as ht  # noqa: E402
from component_analysis import path_patching as pp  # noqa: E402
from component_analysis.roles import ROLES_V2  # noqa: E402

TASKS = ("far", "sdr", "ser")
ROOT = p3_merge.P3_ROOT
REPORTS = "/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports"
CURATED = p3_jobs.PHASE3_DIR
P1C = p3_jobs.P1C_READINGS
PP = "path_patching"
PARTS = ("core", "excl", "DmH_minus_core", "S_k", "mlps")


def load_json(path: str):
    with open(path) as f:
        return json.load(f)


def maybe_json(path: str):
    return load_json(path) if os.path.isfile(path) else None


def require_convention(payload, path: str):
    """Signs are read natively (ADR-0002): refuse a path file without the current convention marker."""
    if payload is not None and pp.convention_of(payload.get("metric")) != pp.CONVENTION:
        raise ValueError(f"{path}: path-patching sign convention is {pp.convention_of(payload.get('metric'))!r}, "
                         f"not {pp.CONVENTION!r}; this builder reads signs natively")
    return payload


def label_of(row) -> str:
    return f"{row['kind']}.{int(row['layer'])}.{int(row['index'])}"


def s2p_weights(p1_root: str, t: str) -> dict:
    sweep = load_json(p2_jobs.sweep_path(p1_root, t, cell="s2p"))
    return {c["label"]: c["mean_drop"] for c in sweep["components"]}


def membership(t: str, ct: dict, label: str) -> dict:
    members = ct["tasks"][t]["members"]
    return {part: label in set(members[part]) for part in PARTS + ("C_t",)}


def part_of(t: str, ct: dict, label: str) -> str:
    """One composition part per Component for the C3 table, in this order: S_k, core, excl, (D-H)-core, MLP block;
    outside C_t: 'sweep-appended'."""
    m = membership(t, ct, label)
    for part in ("S_k", "core", "excl", "DmH_minus_core", "mlps"):
        if m[part]:
            return part
    return "outside_C_t"


def segment_pass_cost(seg: dict, agn: dict) -> dict:
    if not seg:
        return {}
    kv = sum(1 for c in agn.get("cells") or [] if c["receiver"].split(".")[0] in ("k", "v"))
    sel_kv = sum(1 for c in seg.get("cells") or [] if c.get("receiver_kind") in ("k", "v"))
    return {"threshold": seg.get("threshold"), "n_selected": seg.get("n_selected"),
            "n_cells": len(agn.get("cells") or []), "selected_share": (seg.get("n_selected") or 0) / max(
                len(agn.get("cells") or []), 1),
            "kv_selected": sel_kv, "kv_cells": kv, "kv_selected_share": sel_kv / max(kv, 1),
            "cost": seg.get("cost")}


def task_results(t: str, root: str, p1_root: str, ct: dict, readings: dict) -> dict:
    d = p3_merge.p3_cell(root, t, "d")
    dis = p3_merge.p3_cell(root, t, "d_is")
    sub = os.path.join(d, PP)
    agn = require_convention(load_json(os.path.join(sub, "agnostic_neutral_twin.json")), sub)
    # R25 (A): the twin Segment pass is part of the run; without it every K/V path would read `no_split`.
    seg = load_json(os.path.join(sub, "segments_neutral_twin.json"))
    cat = load_json(os.path.join(sub, "receiver_category_neutral_twin.json"))
    sweep = require_convention(maybe_json(os.path.join(sub, "sweep_neutral_twin.json")), sub)
    agn_is = require_convention(maybe_json(os.path.join(dis, PP, "agnostic.json")), dis)
    seg_is = maybe_json(os.path.join(dis, PP, "segments.json"))
    rows = ht.load_head_table(d)
    roles = maybe_json(os.path.join(d, "roles", "roles.json"))
    weights = s2p_weights(p1_root, t)
    tinfo = ct["tasks"][t]
    rab = readings["rab"][t]
    share_c = tinfo["routing_shares"]["c_all_outside_C"]

    cats = {f"head.{h['key'][1]}.{h['key'][2]}": h for h in cat["heads"]}
    deciding = tinfo["members"]["S_k"]
    adj = L.adjudicate(deciding, cats, weights, share_c)
    adj["status"] = "pre-registered (R-AB reading A')" if rab["reading"] == "A'" else \
        f"descriptive (R-AB reading {rab['reading']}; S_20 of the single selector)"
    adj["candidate"] = tinfo["candidate"]
    # Spec 2.3 names sub-readings for A' tasks only; on another reading the call is reported as its shape.
    adj["shape"] = adj["sub_reading"]
    if rab["reading"] != "A'":
        call = adj["weighted"]["call"]
        adj["sub_reading"] = f"descriptive: {call}-dominated" if call else "descriptive: mixed"
    for h in adj["heads"]:
        h.update(L.receiver_totals(agn, h["label"]))
        h["membership"] = [p for p in PARTS if membership(t, ct, h["label"])[p]]
    adj["robustness"] = L.robustness(adj["heads"])

    core_l24 = [x for x in tinfo["members"]["core"] if x.startswith("head.24.")]
    bsel_heads = {}
    for x in list(L.L17_HEADS) + core_l24:
        c = cats.get(x) or {}
        kv = L.strongest_kv(agn, x)
        bsel_heads[x] = {"category": c.get("category"), "path": c.get("path"), "support": c.get("support"),
                         "se": c.get("se"), "segment": c.get("segment"), **L.receiver_totals(agn, x),
                         "strongest_kv": None if kv is None else {"cell": kv["cell"], "mean": kv["mean"],
                                                                  "se": kv.get("se")},
                         "in_C_t": x in set(tinfo["members"]["C_t"])}

    entry = L.entry_points(agn, seg)
    comp = L.completeness(sweep, tinfo["members"]["C_t"]) if sweep else None

    by_cat = {}
    table = []
    for r in rows:
        lab = label_of(r)
        if not membership(t, ct, lab)["C_t"]:
            continue
        rc = cats.get(lab) or {}
        if r["kind"] == "head":
            by_cat[rc.get("category")] = by_cat.get(rc.get("category"), 0) + 1
        table.append({"task": t, "label": lab, "part": part_of(t, ct, lab),
                      "membership": "|".join(p for p in PARTS if membership(t, ct, lab)[p]),
                      "category": rc.get("category"), "path": rc.get("path"), "support": rc.get("support"),
                      "se": rc.get("se"), "segment": rc.get("segment"), "s2p_weight": weights.get(lab),
                      "role": r.get("roles.role_proposed"), "role_notes": r.get("roles.role_notes")})
    roles_by_part = {}
    for r in rows:
        lab = label_of(r)
        part = part_of(t, ct, lab)
        role = r.get("roles.role_proposed")
        roles_by_part.setdefault(part, {}).setdefault(role, 0)
        roles_by_part[part][role] += 1

    checks = {
        "sweep_file": sweep is not None,
        "sweep_counterfactual": (sweep or {}).get("counterfactual"),
        "sweep_same_as_grid": ((sweep or {}).get("sample") or {}).get("same_as_grid"),
        "pre_clause_top_segment": entry["pre_clause_bug"],
        "category_bang_notes": [h for h, v in cats.items() if (v.get("note") or "").startswith("!!")],
        "twin_n_instances": (agn.get("sample") or {}).get("n_instances"),
        "twin_excluded_by_gap": (agn.get("sample") or {}).get("n_excluded_by_gap"),
        "twin_gap": agn.get("gap"),
        "item_swap_cell": agn_is is not None,
        "item_swap_n_instances": ((agn_is or {}).get("sample") or {}).get("n_instances"),
        "roles_run": roles is not None,
        "rows_outside_C_t": [label_of(r) for r in rows if not membership(t, ct, label_of(r))["C_t"]],
    }
    cost = {"twin_agnostic": agn.get("cost"), "twin_segments": segment_pass_cost(seg, agn),
            "item_swap_agnostic": (agn_is or {}).get("cost"),
            "item_swap_segments": segment_pass_cost(seg_is, agn_is or {}),
            "sweep": (sweep or {}).get("cost")}
    return {"task": t, "reading": rab["reading"], "deciding": rab["deciding"], "routing": tinfo["routing_shares"],
            "a_prime": adj, "b_selector_heads": bsel_heads, "core_l24": core_l24,
            "category_counts_C_t_heads": by_cat, "category_counts_all_heads": cat.get("counts"),
            "entry": {"by_class": entry["by_class"], "n_cells": entry["n_cells"],
                      "senders": entry["senders"][:25], "pre_clause_bug": entry["pre_clause_bug"]},
            "entry_cells": entry["cells"],
            "completeness": comp, "roles": None if roles is None else {
                "counts": roles.get("counts"),
                # roles.json counts every row of the cell, the sweep-appended ones too: C_t's own counts here
                "counts_C_t": dict(collections.Counter(x["role"] for x in table)),
                "outside_C_t": [{"label": label_of(r), "role": r.get("roles.role_proposed")} for r in rows
                                if not membership(t, ct, label_of(r))["C_t"]],
                "flavour_counts": roles.get("flavour_counts"),
                "missing_views": roles.get("missing_views"), "merged_from": roles.get("merged_from")},
            "roles_by_part": roles_by_part, "table": table, "checks": checks, "cost": cost}


# ------------------------------------------------------------------ writers

def _f(x, nd=3):
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def write_csv(path: str, rows: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cols = []
    for r in rows:
        for c in r:
            if c not in cols:
                cols.append(c)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in cols})


def cross_task_roles(results: dict):
    """C3: each Component of some C_t lined up over the tasks (part, role, receiver category per task).

    Returns (rows, summary). `same_role` compares the roles of the tasks whose C_t holds the Component; a
    sweep-appended row (part outside_C_t) is listed but counts as not in C_t."""
    tasks = list(results["tasks"])
    by, inside_of = {}, {}
    for t in tasks:
        for r in results["tasks"][t]["table"]:
            e = by.setdefault(r["label"], {"label": r["label"]})
            inside = r.get("part") != "outside_C_t"
            e[f"part_{t}"] = r.get("part")
            e[f"role_{t}"] = r.get("role") if inside else None
            e[f"category_{t}"] = r.get("category") if inside else None
            if inside:
                inside_of.setdefault(r["label"], []).append(t)
    rows = []
    for lab, e in by.items():
        inside = inside_of.get(lab, [])
        for t in tasks:
            for k in ("part", "role", "category"):
                e.setdefault(f"{k}_{t}", None)
        roles = {e[f"role_{t}"] for t in inside}
        e["n_tasks_in_C_t"] = len(inside)
        # No proposed role (the pass did not run) is not comparable: never "the same role".
        e["same_role"] = (len(roles) == 1) if len(inside) >= 2 and None not in roles else None
        rows.append(e)
    kind_order = {"head": 0, "mlp": 1}
    rows.sort(key=lambda e: (-e["n_tasks_in_C_t"], int(e["label"].split(".")[1]),
                             kind_order.get(e["label"].split(".")[0], 2), int(e["label"].split(".")[2])))
    three = [e for e in rows if e["n_tasks_in_C_t"] == len(tasks)]
    summary = {"in_all_three": len(three), "same_role_all_three": sum(1 for e in three if e["same_role"]),
               "in_two_or_more": sum(1 for e in rows if e["n_tasks_in_C_t"] >= 2),
               "non_unknown_in_all_three": [e["label"] for e in three
                                            if any((e[f"role_{t}"] or "unknown") != "unknown" for t in tasks)]}
    return rows, summary


def write_curated(curated: str, root: str, results: dict) -> None:
    os.makedirs(os.path.join(curated, "roles"), exist_ok=True)
    cats, adj, bsel, entry, comp, c3 = [], [], [], [], [], []
    for t, r in results["tasks"].items():
        d = p3_merge.p3_cell(root, t, "d")
        shutil.copyfile(os.path.join(d, ht.CSV_NAME), os.path.join(curated, f"{t}_head_table.csv"))
        if os.path.isfile(os.path.join(d, "roles", "roles.json")):
            shutil.copyfile(os.path.join(d, "roles", "roles.json"), os.path.join(curated, "roles", f"{t}.json"))
        cats += [{k: v for k, v in row.items() if k != "role_notes"} for row in r["table"]]
        for h in r["a_prime"]["heads"]:
            adj.append({"task": t, "status": r["a_prime"]["status"], **{k: v for k, v in h.items()
                                                                       if k != "membership"},
                        "membership": "|".join(h["membership"])})
        for lab, h in r["b_selector_heads"].items():
            bsel.append({"task": t, "head": lab, **{k: v for k, v in h.items() if k != "strongest_kv"},
                         "strongest_kv": (h["strongest_kv"] or {}).get("cell"),
                         "strongest_kv_mean": (h["strongest_kv"] or {}).get("mean")})
        for c in r["entry_cells"]:
            entry.append({"task": t, **c})
        if r["completeness"]:
            comp.append({"task": t, **{k: v for k, v in r["completeness"].items()
                                       if not isinstance(v, (list, dict))}})
        for part, counts in r["roles_by_part"].items():
            for role, n in counts.items():
                c3.append({"task": t, "part": part, "role": role, "n": n})
    write_csv(os.path.join(curated, "categories.csv"), cats)
    write_csv(os.path.join(curated, "a_prime.csv"), adj)
    write_csv(os.path.join(curated, "b_selector.csv"), bsel)
    write_csv(os.path.join(curated, "entry_paths.csv"), entry)
    write_csv(os.path.join(curated, "completeness.csv"), comp)
    write_csv(os.path.join(curated, "roles_by_part.csv"), c3)
    write_csv(os.path.join(curated, "roles_cross_task.csv"), cross_task_roles(results)[0])
    slim = {"b_selector": results["b_selector"], "tasks": {}}
    for t, r in results["tasks"].items():
        slim["tasks"][t] = {k: v for k, v in r.items() if k not in ("table", "entry_cells")}
    with open(os.path.join(curated, "p3_readings.json"), "w") as f:
        json.dump(slim, f, indent=1, default=str)


def markdown(results: dict) -> str:
    sizes = sorted({r["checks"]["twin_n_instances"] for r in results["tasks"].values()}, key=str)
    out = ["# Phase-3 results (ticket 05): path patching on C_t", "",
           "Built by `outputs/_launch_mechanism_analysis/p3_results.py` from the cells "
           "`outputs/_analyses/mechanism-analysis-p3/{d,d_is}/Ct__leaf/<t>_v2` (Delta, fetched from Bridges-2). "
           "Path numbers are the normalized effect against the Neutral-Clause Twin unless a line says item swap: "
           "positive = the path helps the pressured (deceptive) answer. Floor 0.01 (docs/component-roles.md). "
           f"Causal sample: n = {' / '.join(str(n) for n in sizes)} (the cells' sample.n_instances; the default "
           "causal sample, seed 0, which is R-AB's selection sample).", ""]
    out += ["## A' adjudication (spec 2.3)", "",
            "| task | R-AB | deciding set | heads / MLPs | q | kv_clause | kv_post_clause | kv_unresolved | none | "
            "call (> 50 % weight) | routing (c) | sub-reading | status |", "|" + "---|" * 13]
    for t, r in results["tasks"].items():
        a = r["a_prime"]
        s = a["weighted"]["shares"]
        out.append(f"| {t} | {r['reading']} | {a['candidate']} | {a['n_heads']} / {a['n_mlps']} | "
                   + " | ".join(f"{s[c]:.2f} ({a['weighted']['counts'][c]})" for c in L.CATEGORIES)
                   + f" | {a['weighted']['call'] or 'none > 50 %'} | {r['routing']['c_all_outside_C']:.3f} | "
                     f"**{a['sub_reading'] or 'needs a researcher ruling'}** | {a['status']} |")
    out += ["", "Shares are of the summed S2p single effect (phase-1 S2p mean drop) over the deciding set's heads; "
            "counts in brackets. MLP members are listed, never called. A task not read A′ gets no sub-reading "
            "(spec 2.3); its call is given as a descriptive shape."]
    out += [f"- {t}: {r['a_prime']['weighted']['note']}" for t, r in results["tasks"].items()
            if r["a_prime"]["weighted"]["note"]]
    out.append("")
    for t, r in results["tasks"].items():
        a = r["a_prime"]
        out += [f"### {t}: per head of the deciding set ({a['status']})", "",
                f"MLP members ({a['n_mlps']}): {', '.join(a['mlp_members']) or 'none'}. "
                f"Negative S2p weights floored at 0: {a['weighted']['negative_weights_floored'] or 'none'}.", "",
                "| head | S2p weight | category | strongest path | support | SE | top Segment | Q n / abs | K+V n / abs | "
                "membership |", "|" + "---|" * 10]
        for h in sorted(a["heads"], key=lambda h: -(h["weight"] or 0)):
            out.append(f"| {h['label']} | {_f(h['weight'])} | {h['category']} | {h['path'] or '-'} | "
                       f"{_f(h['support'], 4)} | {_f(h['se'], 4)} | {h['segment'] or '-'} | "
                       f"{h['q_n']} / {_f(h['q_abs'])} | {h['kv_n']} / {_f(h['kv_abs'])} | "
                       f"{'+'.join(h['membership'])} |")
        out.append("")
    out += ["### Robustness of the call (EXPLORATORY, not pre-registered)", "",
            "The same cells re-read three ways: a head whose strongest path opposes the pressured answer counts as "
            "none; a head whose strongest path is under twice the floor (0.02) counts as none; each head placed by "
            "its larger Q or K+V total over the floor. K/V cells belong to a KV group, so the distinct groups behind "
            "the kv_clause heads are the independent tests.", "",
            "| task | pre-registered call | positive path only | floor x2 | Q vs K+V totals | "
            "kv_clause heads / KV groups |", "|" + "---|" * 6]

    def call_text(x):
        if not x:
            return "-"
        c = max(x["shares"], key=lambda k: x["shares"][k])
        return f"{x['call'] or 'mixed'} ({c} {x['shares'][c]:.2f})"
    for t, r in results["tasks"].items():
        a = r["a_prime"]
        rb = a.get("robustness") or {}
        out.append(f"| {t} | {call_text(a['weighted'])} | {call_text(rb.get('positive_path_only'))} | "
                   f"{call_text(rb.get('floor_x2'))} | {call_text(rb.get('totals'))} | "
                   f"{rb.get('kv_clause_heads', '-')} / {rb.get('kv_clause_groups', '-')} |")
    out.append("")
    b = results["b_selector"]
    out += ["## B-selector (spec 2.6)", "",
            f"- Clause 1, literal (one of L17H24-27 has category q on >= 2 tasks): **{b['clause1_literal']}**; "
            f"q tasks per head: {b['l17_q_tasks_per_head']}. Loose reading (some L17 head q, on >= 2 tasks): "
            f"{b['clause1_loose']} ({b['clause1_loose_tasks']}).",
            f"- Clause 2 (the core's L24 heads all kv_post_clause): on all tasks **{b['clause2_all_tasks']}**; "
            f"tasks where it holds: {b['clause2_tasks']}.", "",
            "| task | head | category | strongest path | support | SE | segment | Q n / signed / abs | "
            "K+V n / signed / abs | strongest K/V cell (mean) |", "|" + "---|" * 10]
    for t, r in results["tasks"].items():
        for lab, h in r["b_selector_heads"].items():
            kv = h["strongest_kv"] or {}
            out.append(f"| {t} | {lab} | {h['category']} | {h['path'] or '-'} | {_f(h['support'], 4)} | "
                       f"{_f(h['se'], 4)} | {h['segment'] or '-'} | {h['q_n']} / {_f(h['q_signed'])} / "
                       f"{_f(h['q_abs'])} | {h['kv_n']} / {_f(h['kv_signed'])} / {_f(h['kv_abs'])} | "
                       f"{kv.get('cell', '-')} ({_f(kv.get('mean'), 4)}) |")
    out += ["", "L17H24-27 share KV group 6: their K/V cells are one test (spec 7); the strongest K/V cell is the "
            "same row for the four heads.", ""]
    out += ["## Where the pressure enters (B4)", "",
            "Neutral-twin paths into C_t's receivers at or above the floor; K/V paths placed by their split's top "
            "Segment, Q / MLP / Readout paths at the query positions (the Readout): that column is the receiver "
            "type, not a measured arrival position. A K/V split whose top Segment is `unsegmented` is post-clause by "
            "construction (pre-clause positions are identical in D and its twin) and has its own column; the "
            "pre-registered receiver category still calls it kv_unresolved (R25).", "",
            "| task | paths >= floor | K/V clause (n / sum abs) | K/V post_clause | K/V post-clause unsegmented | "
            "K/V unresolved | K/V no split | Q / MLP / Readout receivers |", "|" + "---|" * 8]
    for t, r in results["tasks"].items():
        bc = r["entry"]["by_class"]

        def cell(k):
            v = bc.get(k)
            return f"{v['n']} / {v['abs']:.3f}" if v else "0"
        out.append(f"| {t} | {r['entry']['n_cells']} | {cell('clause')} | {cell('post_clause')} | "
                   f"{cell(L.POST_CLAUSE_UNSEGMENTED)} | {cell('unresolved')} | {cell('no_split')} | "
                   f"{cell('query_positions')} |")
    for t, r in results["tasks"].items():
        out += ["", f"{t}: strongest senders (summed |mean| over their paths >= floor):", "",
                "| sender | paths | sum abs | signed | K/V clause abs | K/V post-clause abs (incl. unsegmented) | "
                "Q / MLP / Readout abs |", "|" + "---|" * 7]
        for s in r["entry"]["senders"][:12]:
            w = s["abs_by_where"]
            post = w.get("post_clause", 0) + w.get(L.POST_CLAUSE_UNSEGMENTED, 0)
            out.append(f"| {s['sender']} | {s['n']} | {s['abs']:.3f} | {s['signed']:+.3f} | "
                       f"{w.get('clause', 0):.3f} | {post:.3f} | {w.get('query_positions', 0):.3f} |")
    out += ["", "## Completeness (neutral-twin sweep, direct paths into the Readout)", "",
            "Each sender's mean is already a share of the clean-minus-twin gap, so the signed sums are shares of the "
            "gap. They are sums of single direct effects and can cancel (compare the absolute sum).", "",
            "| task | C_t direct (share of twin gap) | outside C_t direct (share of twin gap) | outside abs | embed | "
            "unmeasured senders | flagged outside | top outside |", "|" + "---|" * 8]
    for t, r in results["tasks"].items():
        c = r["completeness"]
        if not c:
            out.append(f"| {t} | missing | | | | | | |")
            continue
        top_out = ", ".join(f"{x['sender']} {x['mean']:+.3f}" for x in c["top_outside"][:4])
        out.append(f"| {t} | {c['inside_signed']:+.3f} | {c['outside_signed']:+.3f} | {c['outside_abs']:.3f} | "
                   f"{_f(c['embed'])} | {len(c['unmeasured_inside']) + len(c['unmeasured_outside'])} | "
                   f"{len(c['flagged'])} | {top_out} |")
    role_names = [x for x in ROLES_V2 if x != "unknown"] + ["unknown"]
    out += ["", "## Roles (cell d with the merged views; Components of C_t only)", "", "| task | " + " | ".join(
        role_names) + " | rows outside C_t (role) | missing views |", "|" + "---|" * (len(role_names) + 3)]
    for t, r in results["tasks"].items():
        ro = r["roles"] or {}
        c = ro.get("counts_C_t") or {}
        outside = ", ".join(f"{x['label']} ({x['role']})" for x in ro.get("outside_C_t") or []) or "-"
        out.append(f"| {t} | " + " | ".join(str(c.get(k, 0)) for k in role_names)
                   + f" | {outside} | {ro.get('missing_views')} |")
    rows3, summ = cross_task_roles(results)
    tasks = list(results["tasks"])
    out += ["", "## Cross-task roles (C3)", "",
            f"{summ['in_two_or_more']} Components are in two or more C_t; {summ['in_all_three']} are in all "
            f"{len(tasks)}, and {summ['same_role_all_three']} of those have the same role on every task. Components "
            f"of every C_t with a role other than unknown on some task:", "",
            "| Component | " + " | ".join(f"{t} part / role / category" for t in tasks) + " |",
            "|" + "---|" * (1 + len(tasks))]
    for e in rows3:
        if e["label"] in summ["non_unknown_in_all_three"]:
            out.append(f"| {e['label']} | " + " | ".join(
                f"{e[f'part_{t}']} / {e[f'role_{t}']} / {e[f'category_{t}'] or '-'}" for t in tasks) + " |")
    out += ["", "The full table (every Component of some C_t) is `docs/research/mechanism-analysis/phase3/"
            "roles_cross_task.csv`."]
    out += ["", "## Checks and cost", "", "| task | twin sweep | same as grid | pre-clause top | twin n (gap-excl.) | "
            "twin Segment pass selected (K/V) | item-swap Segment selected (K/V) | rows outside C_t |",
            "|" + "---|" * 8]
    for t, r in results["tasks"].items():
        k, c = r["checks"], r["cost"]
        tw, it = c["twin_segments"] or {}, c["item_swap_segments"] or {}
        out.append(f"| {t} | {k['sweep_counterfactual']} | {k['sweep_same_as_grid']} | "
                   f"{len(k['pre_clause_top_segment'])} | {k['twin_n_instances']} ({k['twin_excluded_by_gap']}) | "
                   f"{tw.get('n_selected')} ({_f(tw.get('kv_selected_share'))}) | "
                   f"{it.get('n_selected')} ({_f(it.get('kv_selected_share'))}) | {len(k['rows_outside_C_t'])} |")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=os.path.join(REPO, ROOT))
    p.add_argument("--p1-root", default=os.path.join(REPO, p2_jobs.P1_ROOT))
    p.add_argument("--reports", default=REPORTS)
    p.add_argument("--curated", default=os.path.join(REPO, CURATED))
    p.add_argument("--tasks", default=",".join(TASKS))
    a = p.parse_args(argv)
    if sorted(a.tasks.split(",")) != sorted(TASKS):
        # B-selector, the cross-task roles and the curated tables are cross-task: a subset would overwrite them
        # with partial content and leave other tasks' copies stale.
        raise SystemExit("p3_results writes the cross-task report and curated tables: run it on all three tasks "
                         f"({','.join(TASKS)}), not {a.tasks!r}")
    ct = load_json(os.path.join(REPO, p3_jobs.PHASE3_DIR, "ct.json"))
    readings = load_json(os.path.join(REPO, P1C))
    tasks = {t: task_results(t, a.root, a.p1_root, ct, readings) for t in a.tasks.split(",")}
    by_task = {t: {lab: h["category"] for lab, h in r["b_selector_heads"].items()} for t, r in tasks.items()}
    results = {"b_selector": L.b_selector(by_task, {t: r["core_l24"] for t, r in tasks.items()}), "tasks": tasks}
    os.makedirs(a.reports, exist_ok=True)
    with open(os.path.join(a.reports, "05-phase3-results.json"), "w") as f:
        json.dump(results, f, indent=1, default=str)
    with open(os.path.join(a.reports, "05-phase3-results.md"), "w") as f:
        f.write(markdown(results))
    write_curated(a.curated, a.root, results)
    for t, r in tasks.items():
        print(t, r["a_prime"]["sub_reading"], r["category_counts_C_t_heads"], r["checks"]["sweep_counterfactual"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
