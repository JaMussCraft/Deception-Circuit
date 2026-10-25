#!/usr/bin/env python3
"""
p1b_results.py -- the phase-1B results of the mechanism-analysis feature (ticket 03, spec sections 2.2, 2.5-2.7, R12, R16).

Reads the fetched 1B sweeps (outputs/_analyses/mechanism-analysis-p1/<cell>/U__leaf/<test set>/knockout/sweep.json)
and lens cells, and writes

    <reports>/03-1b-results.json, 03-1b-results.md
    <curated>/rcls.csv, c1_matrix.csv, c1_matrix.png, top20.csv, c_own.csv, p1b_readings.json

Effects are d = drop / clean margin of the sweep, in the test set's own target direction (deceptive on D, honest on H
and F: a positive d on H or F supports the honest answer). Significance: |drop| >= 2 SE and >= 0.01 logits.
Rankings for R-AB use sweep.json `signed_rank` (the signed order, as the greedy selector's pool does; 02a hand-back).

usage (from the repository root):
    python outputs/_launch_mechanism_analysis/p1b_results.py [--root DIR] [--reports DIR] [--curated DIR]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ma_cells as mc  # noqa: E402
import p1_readings as rd  # noqa: E402

TASKS = ("far", "sdr", "ser")
ROOT = "outputs/_analyses/mechanism-analysis-p1"
REPORTS = "/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports"
CURATED = os.path.join(mc.REPO, "docs", "research", "mechanism-analysis", "phase1")
CLAUSE_FORMS = os.path.join(mc.REPO, "docs", "research", "mechanism-analysis", "clause-forms.csv")
V1_SWEEP = "/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_analyses/sdr-dh-core-kosweep/dh_core__leaf/sdr/knockout/sweep.json"
#: cell -> (cell-dir suffix, what it is). analyze_components files a cell under the TASK label (`<t>_v2`) whatever
#: the condition, so H (S5) and F (S6) also sit in `<t>_v2`; each 1B cell has its own output dir, so none collide.
CELLS = {"s1": ("_v2", "D item-swap, all positions"), "s2": ("_v2", "D neutral twin, all positions"),
         "s2p": ("_v2", "D neutral twin, post-clause (R-AB ranking)"), "s3": ("_v2", "D neutral twin, Readout"),
         "s4": ("_v2", "D mean, all positions"), "s5": ("_v2", "H item-swap, all positions"),
         "s6": ("_v2", "F item-swap, all positions")}
C_V1_HEADS = ("head.5.8", "head.5.9", "head.5.11", "head.9.12")
CLASSES = ("opposes", "shared", "deception-leaning", "honest-leaning", "none")
TOP = 20


def _load(path):
    with open(path) as f:
        return json.load(f)


def sweep_path(root, cell, t):
    return os.path.join(root, cell, "U__leaf", f"{t}{CELLS[cell][0]}", "knockout", "sweep.json")


def load_sweeps(root):
    """{(task, cell): {"clean", "counterfactual", "plan", "n", "by_label": {label: component}}}; missing ones left out."""
    out, missing = {}, []
    for t in TASKS:
        for cell in CELLS:
            p = sweep_path(root, cell, t)
            if not os.path.isfile(p):
                missing.append(p)
                continue
            s = _load(p)
            out[(t, cell)] = {"path": p, "clean": s["clean_run"]["mean_logit_difference"],
                              "counterfactual": (s.get("counterfactual_run") or {}).get("mean_logit_difference"),
                              "plan": s.get("plan"), "n": s["clean_run"].get("n_instances"),
                              "excluded_from_ranking": s.get("excluded_from_ranking"),
                              "target_direction": s.get("target_direction"),
                              "by_label": {c["label"]: c for c in s["components"]}}
    return out, missing


def entry(sw, label):
    c = sw["by_label"][label]
    return {"drop": c["mean_drop"], "se": c["standard_error"], "clean": sw["clean"]}


# ------------------------------------------------------------------ composition sets

def membership():
    """{label: tags} for the 123 heads of U, and the named sets per task."""
    S = mc._head_sets(mc.REPO)
    lab = {k: {f"head.{l}.{h}" for (l, h) in v} for k, v in S.items()}
    core = lab["D_far"] & lab["D_sdr"] & lab["D_ser"]
    sets = {"core": core}
    for t in TASKS:
        u, v = [x for x in TASKS if x != t]
        D, H = lab[f"D_{t}"], lab[f"H_{t}"]
        sets[f"excl_{t}"] = D - lab[f"D_{u}"] - lab[f"D_{v}"]
        sets[f"D-H_{t}"] = D - H
        sets[f"(D-H)-core_{t}"] = (D - H) - core
        sets[f"H-D_{t}"] = H - D
    union = set().union(*lab.values())
    return lab, sets, union


def tags(label, lab, sets):
    return {"circuits": sorted(k for k, v in lab.items() if label in v),
            "sets": sorted(k for k, v in sets.items() if label in v)}


# ------------------------------------------------------------------ readings

def classify(sweeps, labels):
    """{task: {label: rcls(...)}} from S1 (D), S5 (H), S6 (F)."""
    out = {}
    for t in TASKS:
        if not all((t, c) in sweeps for c in ("s1", "s5", "s6")):
            continue
        out[t] = {lb: rd.rcls(D=entry(sweeps[(t, "s1")], lb), H=entry(sweeps[(t, "s5")], lb),
                              F=entry(sweeps[(t, "s6")], lb)) for lb in labels}
    return out


def class_counts(cls, sets, union, all_labels):
    """{task: {set name: {class: n}}} over core, excl_t, D-H_t, (D-H)-core_t, H-D_t and outside every circuit."""
    out = {}
    for t, by in cls.items():
        named = {"core": sets["core"], "excl": sets[f"excl_{t}"], "D-H": sets[f"D-H_{t}"],
                 "(D-H)-core": sets[f"(D-H)-core_{t}"], "H-D": sets[f"H-D_{t}"],
                 "outside every circuit": set(all_labels) - union}
        out[t] = {name: {c: sum(1 for lb in members if by[lb]["class"] == c) for c in CLASSES}
                  for name, members in named.items()}
        for name, members in named.items():
            out[t][name]["n"] = len(members)
    return out


def ranking(sw, k=TOP, exclude=("mlp.0.0",)):
    """Top k by signed_rank (descending signed drop), the excluded Components left out."""
    comps = [c for lb, c in sw["by_label"].items() if lb not in exclude]
    return sorted(comps, key=lambda c: c["signed_rank"])[:k]


def top_lists(sweeps, lab, sets):
    out = {}
    for cell in ("s2p", "s3", "s2"):
        out[cell] = {}
        for t in TASKS:
            if (t, cell) not in sweeps:
                continue
            sw = sweeps[(t, cell)]
            out[cell][t] = [{"rank": i + 1, "label": c["label"], "signed_rank": c["signed_rank"],
                             "drop": c["mean_drop"], "se": c["standard_error"], "d": c["mean_drop"] / sw["clean"],
                             "sig": rd.significant_sign({"drop": c["mean_drop"], "se": c["standard_error"]}),
                             **tags(c["label"], lab, sets)} for i, c in enumerate(ranking(sw))]
        present = [set(r["label"] for r in out[cell][t]) for t in TASKS if t in out[cell]]
        if len(present) == 3:
            a, b, c = present
            out[cell]["_overlap"] = {"far&sdr": sorted(a & b), "far&ser": sorted(a & c), "sdr&ser": sorted(b & c),
                                     "all three": sorted(a & b & c)}
    return out


def positive_control(sweeps):
    v1 = None
    if os.path.isfile(V1_SWEEP):
        s = _load(V1_SWEEP)
        c = next(x for x in s["components"] if x["label"] == "mlp.0.0")
        v1 = {"drop": c["mean_drop"], "clean": s["clean_run"]["mean_logit_difference"], "rank": c["rank"],
              "signed_rank": c["signed_rank"], "ko_accuracy": c["accuracy"], "source": V1_SWEEP}
    out = {"v1_sdr_dh_core_kosweep": v1}
    for t in TASKS:
        if (t, "s1") not in sweeps:
            continue
        sw = sweeps[(t, "s1")]
        c = sw["by_label"]["mlp.0.0"]
        out[t] = {"drop": c["mean_drop"], "se": c["standard_error"], "clean": sw["clean"],
                  "d": c["mean_drop"] / sw["clean"], "rank": c["rank"], "signed_rank": c["signed_rank"],
                  "ko_accuracy": c["accuracy"], "positive_control_flag": c.get("positive_control"),
                  "as_in_v1": c["signed_rank"] == 1 and c["accuracy"] <= 0.10}
    return out


def c_own(sweeps, sets):
    out, p = {}, {}
    for t in TASKS:
        if not all((u, "s1") in sweeps for u in TASKS):
            continue
        heads = sorted(sets[f"excl_{t}"])
        d = {h: {u: sweeps[(u, "s1")]["by_label"][h]["mean_drop"] / sweeps[(u, "s1")]["clean"] for u in TASKS}
             for h in heads}
        out[t] = {**rd.c_own(t, d), "d": d}
        p[t] = out[t]["p"]
    if p:
        adj = rd.holm(p)
        for t in out:
            out[t]["p_holm"] = adj[t]
            out[t]["holds"] = adj[t] < 0.05
    return out


def c_mlp(cls, sweeps):
    rows, falsifiers = [], []
    mlps = [f"mlp.{l}.0" for l in range(1, 32)]
    for lb in mlps:
        c = {t: cls[t][lb]["class"] for t in cls}
        dD = {t: cls[t][lb]["d"]["D"] for t in cls}
        dl = [t for t in cls if c[t] == "deception-leaning"]
        if len(dl) == 1 and dD[dl[0]] >= 0.1:
            falsifiers.append(lb)
        rows.append({"label": lb, "class": c, "dD": dD})
    late = {lb: {t: cls[t][lb]["class"] for t in cls} for lb in ("mlp.30.0", "mlp.31.0")}
    return {"rows": rows, "falsifiers": falsifiers, "late": late,
            "late_shared_all": all(v == "shared" for d in late.values() for v in d.values()),
            "holds": not falsifiers and all(v == "shared" for d in late.values() for v in d.values())}


def c_v1(cls):
    if "sdr" not in cls:
        return None
    per = {h: {t: cls[t][h]["class"] for t in cls} for h in C_V1_HEADS}
    ok = [h for h in C_V1_HEADS if per[h].get("sdr") == "deception-leaning"
          and all(per[h].get(t) != "deception-leaning" for t in ("far", "ser"))]
    return {"per_head": per, "meeting": ok, "holds": len(ok) >= 3}


def rqa_predictions(cls, sets):
    out = {}
    for t, by in cls.items():
        core = sets["core"]
        excl = sets[f"excl_{t}"]
        shared = sum(by[h]["class"] == "shared" for h in core)
        dl = sum(by[h]["class"] == "deception-leaning" for h in excl)
        out[t] = {"core_shared": shared, "core_n": len(core), "core_holds": shared * 3 >= 2 * len(core),
                  "excl_deception_leaning": dl, "excl_n": len(excl), "excl_holds": dl * 2 > len(excl)}
    return out


def c1_matrix(sweeps, cls, all_labels, lab, sets):
    cols = [(t, cell) for t in TASKS for cell in ("s1", "s5", "s6")] + [(t, c) for t in TASKS for c in ("s2", "s4")]
    rows = []
    for lb in all_labels:
        r = {"label": lb, **{f"{t}:{cell}": (sweeps[(t, cell)]["by_label"][lb]["mean_drop"] / sweeps[(t, cell)]["clean"]
                                             if (t, cell) in sweeps else None) for t, cell in cols},
             **{f"rcls:{t}": cls[t][lb]["class"] for t in cls}}
        tg = tags(lb, lab, sets)
        r["circuits"] = " ".join(tg["circuits"])
        r["sets"] = " ".join(tg["sets"])
        r["group"] = group_of(lb, sets, lab)
        rows.append(r)
    return cols, rows


GROUP_ORDER = ("core", "excl_far", "excl_sdr", "excl_ser", "other D", "H only", "MLP", "outside")


def row_order(r):
    """Group, then layer and index as numbers (head.9.x before head.10.x; mlp.2 before mlp.10)."""
    _, layer, index = r["label"].split(".")
    return GROUP_ORDER.index(r["group"]), int(layer), int(index)


def c1_summary(cols, rows):
    """Mean d per composition group and test set, and the group sizes (the figure in numbers)."""
    names = [f"{t}:{c}" for t, c in cols]
    out = {}
    for g in GROUP_ORDER:
        rs = [r for r in rows if r["group"] == g]
        if not rs:
            continue
        out[g] = {"n": len(rs), **{n: (sum(r[n] for r in rs if r[n] is not None) /
                                       max(1, sum(r[n] is not None for r in rs))) for n in names}}
    return {"columns": names, "groups": out}


def group_of(lb, sets, lab):
    if lb.startswith("mlp."):
        return "MLP"
    if lb in sets["core"]:
        return "core"
    for t in TASKS:
        if lb in sets[f"excl_{t}"]:
            return f"excl_{t}"
    if any(lb in lab[f"D_{t}"] for t in TASKS):
        return "other D"
    if any(lb in lab[f"H_{t}"] for t in TASKS):
        return "H only"
    return "outside"


def c1_figure(cols, rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    keep = [r for r in rows if r["group"] != "outside"]
    keep.sort(key=row_order)
    names = [f"{t}:{c}" for t, c in cols]
    M = np.array([[np.nan if r[n] is None else r[n] for n in names] for r in keep], dtype=float)
    fig, ax = plt.subplots(figsize=(9, max(6, 0.11 * len(keep))))
    lim = np.nanpercentile(np.abs(M), 99) if np.isfinite(M).any() else 1
    im = ax.imshow(M, aspect="auto", cmap="RdBu_r", vmin=-lim, vmax=lim, interpolation="nearest")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n.replace("s1", "D swap").replace("s5", "H swap").replace("s6", "F swap")
                        .replace("s2", "D twin").replace("s4", "D mean") for n in names], rotation=60, ha="right",
                       fontsize=7)
    ax.set_yticks(range(len(keep)))
    ax.set_yticklabels([r["label"] for r in keep], fontsize=4)
    last = None
    for i, r in enumerate(keep):
        if r["group"] != last:
            ax.axhline(i - 0.5, color="k", lw=0.6)
            ax.text(len(names) - 0.4, i, r["group"], fontsize=6, va="top")
            last = r["group"]
    fig.colorbar(im, ax=ax, label="d = drop / clean margin (own target direction)", shrink=0.4)
    ax.set_title("C1: U heads and MLPs on 9 item-swap test sets, plus D under neutral twin and mean")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ R-lens (exploratory, R12)

def lens(root):
    forms = {}
    if os.path.isfile(CLAUSE_FORMS):
        with open(CLAUSE_FORMS) as f:
            for r in csv.DictReader(f):
                forms[(r["task"], r["pressure_id"])] = r["form"]
    per, inst = {}, {}
    for t in TASKS:
        p = os.path.join(root, "lens", "U__leaf", f"{t}_v2", "dla", "logit_lens.json")
        if not os.path.isfile(p):
            continue
        cross = _load(p).get("crossing") or {}
        per[t] = {}
        for cond, v in (cross.get("conditions") or {}).items():
            rows = v.get("instances") or []
            per[t][cond] = {"n": v.get("n"), "rate_honest_first": v.get("rate_honest_first")}
            if cond == "pressure":
                inst[t] = [(r["pressure_id"], bool(r["honest_first"]), forms.get((f"{t}_v2", r["pressure_id"])))
                           for r in rows]
                by_form = {}
                for pid, hf, form in inst[t]:
                    by_form.setdefault(form, []).append(hf)
                per[t]["pressure_by_form"] = {f: {"n": len(v), "rate": sum(v) / len(v)} for f, v in by_form.items()}
    contrasts = {}
    if "far" in inst:
        far = [(pid, hf) for pid, hf, _ in inst["far"]]
        for t in ("sdr", "ser"):
            if t in inst:
                act = [(pid, hf) for pid, hf, form in inst[t] if form == "act-naming"]
                if act:
                    contrasts[f"far - {t} act-naming"] = rd.cluster_bootstrap_diff(far, act, n_boot=2000, seed=0)
    return {"status": "EXPLORATORY (R12): raw lens, uncalibrated; CIs clustered by pressure_id", "per_task": per,
            "contrasts": contrasts, "expected": "FAR's honest-first rate exceeds the act-naming subsets of SDR and "
                                               "SER by >= 0.2"}


# ------------------------------------------------------------------ outputs

def _f(x, nd=3):
    if x is None:
        return "-"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def markdown(res) -> str:
    L = ["# Ticket 03 phase-1B results: mask-independent sweeps, R-cls, C1, C-own, C-MLP, C-v1, R-lens", "",
         "Generated by `outputs/_launch_mechanism_analysis/p1b_results.py` from "
         "`outputs/_analyses/mechanism-analysis-p1/` (Bridges-2 H100). Selection sample: n = 100, seed 0. U = the "
         "123-head union of the six coarse v2 circuits minus m, at leaf. d = drop / clean margin, in each test set's "
         "own target direction (deceptive on D; honest on H and F, where a positive d supports the honest answer). "
         "Significance: |drop| >= 2 SE and >= 0.01 logits.", ""]
    if res["missing"]:
        L += ["**Missing sweeps:** " + ", ".join(f"`{m}`" for m in res["missing"]), ""]
    if res.get("reading"):
        L += [res["reading"].rstrip(), ""]
    L += ["## Sweeps", "", "| task | cell | what | clean margin | counterfactual margin | n |",
          "| --- | --- | --- | --- | --- | --- |"]
    for k, v in res["sweeps"].items():
        L.append(f"| {v['task']} | {v['cell']} | {CELLS[v['cell']][1]} | {_f(v['clean'])} | {_f(v['counterfactual'])} "
                 f"| {v['n']} |")
    L += ["", "## R-cls class counts (S1, S5, S6)", ""]
    for t, sets in res["class_counts"].items():
        L += [f"**{t}**", "", "| set | n | " + " | ".join(CLASSES) + " |", "| --- " * (len(CLASSES) + 2) + "|"]
        for name, c in sets.items():
            L.append(f"| {name} | {c['n']} | " + " | ".join(str(c[k]) for k in CLASSES) + " |")
        L.append("")
    L += ["## RQ-A predictions from R-cls", "", "| task | core shared | >= 2/3 | excl deception-leaning | majority |",
          "| --- | --- | --- | --- | --- |"]
    for t, r in res["rqa"].items():
        L.append(f"| {t} | {r['core_shared']} / {r['core_n']} | {_f(r['core_holds'])} | {r['excl_deception_leaning']} / "
                 f"{r['excl_n']} | {_f(r['excl_holds'])} |")
    pc = res["positive_control"]
    L += ["", "## Positive control (layer-0 MLP, S1)", "", "| task | drop | clean | d | signed rank | KO acc | as in v1 |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    v1 = pc.get("v1_sdr_dh_core_kosweep")
    if v1:
        L.append(f"| v1 sdr D&H core | {_f(v1['drop'])} | {_f(v1['clean'])} | {_f(v1['drop'] / v1['clean'])} "
                 f"| {v1['signed_rank']} | {_f(v1['ko_accuracy'])} | reference |")
    for t in TASKS:
        if t in pc:
            r = pc[t]
            L.append(f"| {t} | {_f(r['drop'])} | {_f(r['clean'])} | {_f(r['d'])} | {r['signed_rank']} "
                     f"| {_f(r['ko_accuracy'])} | {_f(r['as_in_v1'])} |")
    for cell, title in (("s2p", "S2p ranking (R-AB; layer-0 MLP excluded; signed)"), ("s3", "S3 ranking (Readout)"),
                        ("s2", "S2 ranking (all positions, descriptive)")):
        L += ["", f"## {title}: top {TOP}", ""]
        tl = res["top"].get(cell, {})
        for t in TASKS:
            if t not in tl:
                continue
            L += [f"**{t}**", "", "| # | Component | drop | SE | d | sig | circuits | sets |", "| --- " * 8 + "|"]
            for r in tl[t]:
                L.append(f"| {r['rank']} | {r['label']} | {_f(r['drop'])} | {_f(r['se'])} | {_f(r['d'])} | {r['sig']} "
                         f"| {' '.join(r['circuits']) or 'outside'} | {' '.join(r['sets']) or '-'} |")
            L.append("")
        if "_overlap" in tl:
            L += ["Overlap of the three top-20 lists: " + "; ".join(f"{k}: {len(v)} ({', '.join(v) or '-'})"
                                                                   for k, v in tl["_overlap"].items()), ""]
    c1 = res.get("c1")
    if c1:
        short = {"s1": "D swap", "s5": "H swap", "s6": "F swap", "s2": "D twin", "s4": "D mean"}
        heads = [f"{n.split(':')[0]} {short[n.split(':')[1]]}" for n in c1["columns"]]
        L += ["## C1: Components x 9 item-swap test sets, plus D under neutral twin and mean", "",
              "Full matrix with R-cls per task: `docs/research/mechanism-analysis/phase1/c1_matrix.csv`; figure "
              "`c1_matrix.png` (rows grouped by composition set, ordered by layer). Mean d per group:", "",
              "| group | n | " + " | ".join(heads) + " |", "| --- " * (len(heads) + 2) + "|"]
        for g, v in c1["groups"].items():
            L.append(f"| {g} | {v['n']} | " + " | ".join(_f(v[n], 2) for n in c1["columns"]) + " |")
        L.append("")
    co = res["c_own"]
    L += ["## C-own (R-own): one-sided sign test over each exclusive set, Holm over tasks", "",
          "| task | heads | own | p | p Holm | holds |", "| --- | --- | --- | --- | --- | --- |"]
    for t, r in co.items():
        L.append(f"| {t} | {r['n']} | {r['k']} | {_f(r['p'], 4)} | {_f(r.get('p_holm'), 4)} | {_f(r.get('holds'))} |")
    L += ["", "Per head (d on each task's D, S1):", "", "| task | head | far | sdr | ser | own |", "| --- " * 6 + "|"]
    for t, r in co.items():
        for h, d in r["d"].items():
            L.append(f"| {t} | {h} | {_f(d['far'])} | {_f(d['sdr'])} | {_f(d['ser'])} | {_f(r['own'][h])} |")
    cm = res["c_mlp"]
    L += ["", "## C-MLP", "", f"Falsifying MLPs (deception-leaning on exactly one task with d(D) >= 0.1): "
          f"{', '.join(cm['falsifiers']) or 'none'}. Late MLPs: "
          + "; ".join(f"{k}: " + ", ".join(f"{t} {c}" for t, c in v.items()) for k, v in cm["late"].items())
          + f". Prediction holds: {_f(cm['holds'])}.", "",
          "| MLP | " + " | ".join(f"{t} class | {t} d(D)" for t in TASKS) + " |", "| --- " * 7 + "|"]
    for r in cm["rows"]:
        L.append(f"| {r['label']} | " + " | ".join(f"{r['class'].get(t, '-')} | {_f(r['dD'].get(t))}" for t in TASKS)
                 + " |")
    cv = res["c_v1"]
    if cv:
        L += ["", "## C-v1", "", "| head | far | sdr | ser |", "| --- | --- | --- | --- |"]
        for h, d in cv["per_head"].items():
            L.append(f"| {h} | {d.get('far')} | {d.get('sdr')} | {d.get('ser')} |")
        L += ["", f"Heads meeting C-v1: {', '.join(cv['meeting']) or 'none'} ({len(cv['meeting'])} of 4; needs 3). "
                  f"Holds: {_f(cv['holds'])}.", ""]
    ln = res["lens"]
    L += ["## R-lens (EXPLORATORY, R12)", "", ln["status"] + ".", "", "| task | condition | n | honest-first rate |",
          "| --- | --- | --- | --- |"]
    for t, conds in ln["per_task"].items():
        for cond, v in conds.items():
            if cond == "pressure_by_form":
                for form, fv in v.items():
                    L.append(f"| {t} | pressure, {form} | {fv['n']} | {_f(fv['rate'])} |")
            else:
                L.append(f"| {t} | {cond} | {v['n']} | {_f(v['rate_honest_first'])} |")
    L += ["", "| contrast | diff | 95% CI (clustered by pressure_id) | clusters |", "| --- | --- | --- | --- |"]
    for k, v in ln["contrasts"].items():
        L.append(f"| {k} | {_f(v['diff'])} | [{_f(v['ci'][0])}, {_f(v['ci'][1])}] | {v['n_clusters']} |")
    L += ["", f"Expected direction (not gated): {ln['expected']}.", "",
          "The neutral twin's rate is 0 by construction: the rule needs a positive final margin (deceptive answer), "
          "and the full model answers the twin honestly. `pressure_neutral_twin_paired` repeats the pressure rows "
          "paired with a twin.", ""]
    return "\n".join(L)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=os.path.join(mc.REPO, ROOT))
    p.add_argument("--reports", default=REPORTS)
    p.add_argument("--curated", default=CURATED)
    p.add_argument("--reading", default=None)
    a = p.parse_args(argv)

    sweeps, missing = load_sweeps(a.root)
    lab, sets, union = membership()
    any_sw = next(iter(sweeps.values()), None)
    all_labels = sorted(any_sw["by_label"]) if any_sw else []
    cls = classify(sweeps, all_labels)
    res = {"generated_by": f"{mc.LAUNCH_DIR}/p1b_results.py", "root": a.root, "missing": missing,
           "sweeps": {f"{t}/{c}": {"task": t, "cell": c, "path": v["path"], "clean": v["clean"],
                                   "counterfactual": v["counterfactual"], "n": v["n"], "plan": v["plan"],
                                   "target_direction": v["target_direction"]} for (t, c), v in sweeps.items()},
           "class_counts": class_counts(cls, sets, union, all_labels), "rqa": rqa_predictions(cls, sets),
           "positive_control": positive_control(sweeps), "top": top_lists(sweeps, lab, sets),
           "c_own": c_own(sweeps, sets), "c_mlp": c_mlp(cls, sweeps) if cls else None, "c_v1": c_v1(cls),
           "lens": lens(a.root), "sets": {k: sorted(v) for k, v in sets.items()},
           "reading": open(a.reading).read() if a.reading else ""}
    cols, rows = c1_matrix(sweeps, cls, all_labels, lab, sets)
    res["c1"] = c1_summary(cols, rows)
    os.makedirs(a.reports, exist_ok=True)
    os.makedirs(a.curated, exist_ok=True)
    with open(os.path.join(a.reports, "03-1b-results.json"), "w") as f:
        json.dump({**res, "rcls": cls}, f, indent=1, default=list)
    with open(os.path.join(a.reports, "03-1b-results.md"), "w") as f:
        f.write(markdown(res))
    with open(os.path.join(a.curated, "c1_matrix.csv"), "w", newline="") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    with open(os.path.join(a.curated, "rcls.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "label", "class", "reason", "d_D", "d_H", "d_F", "sig_D", "sig_H", "sig_F", "m_HF", "U_HF",
                    "group"])
        for t, by in cls.items():
            for lb, r in by.items():
                w.writerow([t, lb, r["class"], r["reason"], r["d"]["D"], r["d"]["H"], r["d"]["F"], r["sig"]["D"],
                            r["sig"]["H"], r["sig"]["F"], r["m_HF"], r["U_HF"], group_of(lb, sets, lab)])
    with open(os.path.join(a.curated, "top20.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell", "task", "rank", "label", "signed_rank", "drop", "se", "d", "sig", "circuits", "sets"])
        for cell, by in res["top"].items():
            for t, rows_t in by.items():
                if t.startswith("_"):
                    continue
                for r in rows_t:
                    w.writerow([cell, t, r["rank"], r["label"], r["signed_rank"], r["drop"], r["se"], r["d"], r["sig"],
                                " ".join(r["circuits"]), " ".join(r["sets"])])
    with open(os.path.join(a.curated, "c_own.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "head", "d_far", "d_sdr", "d_ser", "own"])
        for t, r in res["c_own"].items():
            for h, d in r["d"].items():
                w.writerow([t, h, d["far"], d["sdr"], d["ser"], r["own"][h]])
    with open(os.path.join(a.curated, "p1b_readings.json"), "w") as f:
        json.dump({k: res[k] for k in ("class_counts", "rqa", "positive_control", "c_own", "c_v1", "lens")} |
                  {"c_mlp": {k: v for k, v in (res["c_mlp"] or {}).items() if k != "rows"}}, f, indent=1, default=list)
    if rows and len(sweeps) == len(TASKS) * len(CELLS):
        c1_figure(cols, rows, os.path.join(a.curated, "c1_matrix.png"))
    print(f"{len(sweeps)} of {len(TASKS) * len(CELLS)} sweeps; wrote {a.reports}/03-1b-results.{{md,json}} and {a.curated}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
