#!/usr/bin/env python3
"""
p1c_results.py -- the phase-1C results builder (ticket 03; spec 2.3, 2.4, 2.7; R11, R15, R19(3)).

Reads the fetched 1C cells under outputs/_analyses/mechanism-analysis-p1/ (Delta) -- heldout_d, heldout_h, heldout_f,
rinv_d, rinv_i (groups.json + groups_instances.json), s7 and s2p (sweep.json), greedy (greedy.json) -- with the groups
meta (docs/research/mechanism-analysis/phase1/groups/meta.json), the 1B R-cls classes (reports/03-1b-results.json)
and the 1A readings (reports/03-1a-results.json), and writes:
    reports/03-1c-results.md + .json
    docs/research/mechanism-analysis/phase1/{rab_curves.csv, rinv.csv, routing.csv, s7_vs_s2p.csv,
                                             p1c_readings.json}

Rules (spec 2.3): f_D = (mean clean - mean KO) / (mean clean - mean twin), a ratio of means; two-way deceptive
accuracy = share of KO margins > 0. (i): accuracy <= 0.25, f_D >= 0.75 and f_D > every one of the 20 null draws at
that candidate. (ii): on H and F (item-swap, all positions) |clean acc - KO acc| <= 0.10 and |clean margin - KO
margin| <= 25% of the clean margin, on both. Reading per task, in order: A (some k <= 20 meets (i) and (ii)), A' (some
k <= 20 meets (i)), B. Deciding set = the smallest such S_k, the single selector's on a tie; for B the single S_20,
descriptive. CIs: per-instance bootstrap, 2,000 resamples. R-inv (R19(3)): paired on the same ids, clustered by D's
pressure_id; "instructed inversion machinery" when the 95% CI of f_I - 0.5 f_D lies above 0, "deception-specific"
when it lies below 0, else "undecided".

usage (repository root): python outputs/_launch_mechanism_analysis/p1c_results.py [--reading FILE] [--sacct FILE]
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

TASKS = ("far", "sdr", "ser")
N_BOOT = 2000
ACC_MAX, F_MIN = 0.25, 0.75
II_ACC, II_MARGIN = 0.10, 0.25
K_MAX_READING = 20
EPS = 1e-12


# ------------------------------------------------------------------ pure rules

def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def mediated_fraction(clean, knocked, twin) -> float:
    c = _mean(clean)
    return (c - _mean(knocked)) / (c - _mean(twin))


def two_way_accuracy(knocked) -> float:
    knocked = list(knocked)
    return sum(1 for x in knocked if x > 0) / len(knocked)


def test_i(*, acc, f, null_fs) -> bool:
    return acc <= ACC_MAX + EPS and f + EPS >= F_MIN and all(f > n for n in null_fs)


def test_ii_one(*, clean_acc, ko_acc, clean_margin, ko_margin) -> bool:
    return (abs(clean_acc - ko_acc) <= II_ACC + EPS
            and abs(clean_margin - ko_margin) <= II_MARGIN * abs(clean_margin) + EPS)


def reading(cands: dict) -> tuple:
    """cands = {name: {"selector", "k", "i", "ii"}} -> (reading, deciding candidate name)."""
    small = {n: c for n, c in cands.items()
             if c["k"] <= K_MAX_READING and c["selector"] in ("single", "greedy")}   # R24: the U-only arm never reads
    order = lambda n: (small[n]["k"], 0 if small[n]["selector"] == "single" else 1)   # noqa: E731
    both = sorted((n for n, c in small.items() if c["i"] and c["ii"]), key=order)
    if both:
        return "A", both[0]
    only_i = sorted((n for n, c in small.items() if c["i"]), key=order)
    if only_i:
        return "A'", only_i[0]
    return "B", f"single_k{K_MAX_READING}"


def rinv_label(ci) -> str:
    lo, hi = ci
    if lo > 0:
        return "instructed inversion machinery"
    if hi < 0:
        return "deception-specific"
    return "undecided"


def inversion_shared(*, d_D, sig_D, d_I, sig_I) -> bool:
    if not (sig_D and sig_I) or d_D == 0:
        return False
    return 0.5 - EPS <= d_I / d_D <= 2.0 + EPS


def shared_share(rows) -> float:
    """rows = [(label, signed drop, R-cls class)] over the S2p top 80: shared part of the summed positive effect."""
    pos = [(d, c) for _, d, c in rows if d > 0]
    total = sum(d for d, _ in pos)
    return sum(d for d, c in pos if c == "shared") / total if total else float("nan")


def paired_cluster_ci(clusters, stat, *, n_boot=N_BOOT, seed=0, alpha=0.05):
    """Percentile CI of stat(indices) over resamples of whole clusters (rows keep their pairing)."""
    import numpy as np
    by = {}
    for i, c in enumerate(clusters):
        by.setdefault(c, []).append(i)
    groups = list(by.values())
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(groups), len(groups))
        idx = [i for g in pick for i in groups[g]]
        vals.append(stat(idx))
    lo, hi = np.quantile(np.array(vals, dtype=float), [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


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


# ------------------------------------------------------------------ loading

def _load(p):
    with open(p) as f:
        return json.load(f)


def cell_dir(root, cell, t):
    return os.path.join(root, cell, "U__leaf", f"{t}_v2", "knockout")


def load_groups_cell(root, cell, t):
    """{"rows": {name: groups.json row}, "clean_run", "ids", "C", "T", "K": {name: [...]}} or None."""
    d = cell_dir(root, cell, t)
    gp, ip = os.path.join(d, "groups.json"), os.path.join(d, "groups_instances.json")
    if not (os.path.isfile(gp) and os.path.isfile(ip)):
        return None
    g, inst = _load(gp), _load(ip)
    twin = inst.get("neutral_twin_logit_difference") or inst.get("counterfactual_logit_difference") or []
    if twin and any(x is None for x in twin):
        twin = inst.get("counterfactual_logit_difference") or twin
    return {"rows": {r["name"]: r for r in g["groups"]}, "clean_run": g["clean_run"], "plan": g.get("plan"),
            "ids": inst["instance_ids"], "C": inst["clean_logit_difference"], "T": twin,
            "K": inst["knocked_logit_difference"], "unpaired": inst.get("unpaired_instance_ids", [])}


def dataset_rows(t, suffix=""):
    from datasets import load_from_disk
    import ma_cells as mc
    ds = load_from_disk(os.path.join(mc.REPO, "data", "datasets", f"{t}_v2{suffix}"))["test"]
    return {r["instance_id"]: r for r in ds}


# ------------------------------------------------------------------ per-task computations

def rab(t, D, H, F, meta_t, seed=0):
    """Test (i) with nulls and CIs, test (ii), mediation curves, the reading and the deciding set."""
    import numpy as np
    C, T = np.array(D["C"], float), np.array(D["T"], float)
    idx = instance_boot(len(C), seed=seed)
    cands = {}
    for name, info in meta_t["candidates"].items():
        if name not in D["K"]:
            continue
        K = np.array(D["K"][name], float)
        f = mediated_fraction(C, K, T)
        acc = two_way_accuracy(K)
        nulls = [n for n in D["K"] if n.startswith(f"null_{name}_d")]
        null_f = [mediated_fraction(C, np.array(D["K"][n], float), T) for n in nulls]
        null_acc = [two_way_accuracy(D["K"][n]) for n in nulls]
        fb = f_boot(C, K, T, idx)
        accb = (K[idx] > 0).mean(1)
        nfb = np.mean([f_boot(C, np.array(D["K"][n], float), T, idx) for n in nulls], axis=0) if nulls else None
        per_inst = ((C - K) / (C - T)).tolist()
        ii = {}
        for side, cell in (("H", H), ("F", F)):
            if cell is None or name not in cell["rows"]:
                ii[side] = None
                continue
            row, cr = cell["rows"][name], cell["clean_run"]
            ii[side] = {"clean_acc": cr["accuracy"], "ko_acc": row["accuracy"],
                        "clean_margin": cr["mean_logit_difference"], "ko_margin": row["knocked_logit_difference"],
                        "acc_move": cr["accuracy"] - row["accuracy"],
                        "margin_move_rel": (cr["mean_logit_difference"] - row["knocked_logit_difference"])
                        / abs(cr["mean_logit_difference"]),
                        "pass": test_ii_one(clean_acc=cr["accuracy"], ko_acc=row["accuracy"],
                                            clean_margin=cr["mean_logit_difference"],
                                            ko_margin=row["knocked_logit_difference"])}
        ii_pass = (ii["H"] is not None and ii["F"] is not None and ii["H"]["pass"] and ii["F"]["pass"])
        cands[name] = {"selector": name.split("_")[0], "k": info["k"], "members": info["members"],
                       "f": f, "f_ci": ci(fb), "acc": acc, "acc_ci": ci(accb),
                       "null_f_mean": float(np.mean(null_f)) if null_f else None,
                       "null_f_mean_ci": ci(nfb) if nfb is not None else None,
                       "null_f_max": max(null_f) if null_f else None,
                       "null_acc_mean": float(np.mean(null_acc)) if null_acc else None,
                       "n_null": len(null_f), "null_f": null_f,
                       "per_instance_f": per_inst,
                       "i": test_i(acc=acc, f=f, null_fs=null_f) if null_f else False,
                       "ii_detail": ii, "ii": ii_pass}
    rd_, deciding = reading(cands)
    return {"n": len(C), "clean_mean": float(C.mean()), "twin_mean": float(T.mean()),
            "gap": float(C.mean() - T.mean()), "candidates": cands, "reading": rd_, "deciding": deciding}


def named_groups(D, H, F):
    import numpy as np
    out = {}
    C, T = np.array(D["C"], float), np.array(D["T"], float)
    for name in D["K"]:
        if not name.startswith("named_"):
            continue
        K = np.array(D["K"][name], float)
        row = {"n_components": D["rows"][name]["n_components"], "f_D": mediated_fraction(C, K, T),
               "acc_D": two_way_accuracy(K)}
        for side, cell in (("H", H), ("F", F)):
            if cell is not None and name in cell["rows"]:
                r, cr = cell["rows"][name], cell["clean_run"]
                row[f"acc_move_{side}"] = cr["accuracy"] - r["accuracy"]
                row[f"margin_move_rel_{side}"] = ((cr["mean_logit_difference"] - r["knocked_logit_difference"])
                                                  / abs(cr["mean_logit_difference"]))
        out[name[len("named_"):]] = row
    return out


def routing(D, meta_t, cand):
    import numpy as np
    C, T = np.array(D["C"], float), np.array(D["T"], float)
    share = lambda g: mediated_fraction(C, np.array(D["K"][g], float), T) if g in D["K"] else None   # noqa: E731
    info = meta_t["candidates"].get(cand, {})
    return {"candidate": cand, "C_t_size": info.get("C_t_size"), "C_t_mlps": info.get("C_t_mlps"),
            "a_all_mlps": share("route_a_all_mlps"), "b_heads_outside_C": share(f"route_b_{cand}"),
            "c_all_outside_C": share(f"route_c_{cand}")}


def rinv(t, RD, RI, cand, clusters_of, subset=None, seed=0):
    """Paired f_D, f_I on the same ids; clustered bootstrap CI of f_I - 0.5 f_D. subset: ids to keep."""
    import numpy as np
    if RD is None or RI is None or cand not in RD["K"] or cand not in RI["K"]:
        return None
    pos_i = {i: n for n, i in enumerate(RI["ids"])}
    ids = [i for i in RD["ids"] if i in pos_i and (subset is None or i in subset)]
    if not ids:
        return {"n": 0}
    pd_ = {i: n for n, i in enumerate(RD["ids"])}
    take = lambda arr, pos: np.array([arr[pos[i]] for i in ids], float)   # noqa: E731
    CD, TD, KD = take(RD["C"], pd_), take(RD["T"], pd_), take(RD["K"][cand], pd_)
    CI_, TI, KI = take(RI["C"], pos_i), take(RI["T"], pos_i), take(RI["K"][cand], pos_i)
    fD, fI = mediated_fraction(CD, KD, TD), mediated_fraction(CI_, KI, TI)

    def stat(ix):
        ix = np.asarray(ix)
        return mediated_fraction(CI_[ix], KI[ix], TI[ix]) - 0.5 * mediated_fraction(CD[ix], KD[ix], TD[ix])
    cl = [clusters_of.get(i) for i in ids]
    c = paired_cluster_ci(cl, stat, seed=seed)
    return {"n": len(ids), "n_clusters": len(set(cl)), "f_D": fD, "f_I": fI, "diff": fI - 0.5 * fD, "diff_ci": c,
            "label": rinv_label(c), "gap_D": float(CD.mean() - TD.mean()), "gap_I": float(CI_.mean() - TI.mean())}


def s7_vs_s2p(root, t, top_labels):
    import p1_readings as rd
    p7 = os.path.join(root, "s7", "U__leaf", f"{t}_v2", "knockout", "sweep.json")
    p2 = os.path.join(root, "s2p", "U__leaf", f"{t}_v2", "knockout", "sweep.json")
    if not (os.path.isfile(p7) and os.path.isfile(p2)):
        return None
    s7, s2 = _load(p7), _load(p2)
    c7, c2 = s7["clean_run"]["mean_logit_difference"], s2["clean_run"]["mean_logit_difference"]
    by7 = {c["label"]: c for c in s7["components"]}
    rows = []
    for c in s2["components"]:
        lb = c["label"]
        if lb == "mlp.0.0" or lb not in by7 or c.get("mean_drop") is None or by7[lb].get("mean_drop") is None:
            continue
        eD = {"drop": c["mean_drop"], "se": c["standard_error"], "clean": c2}
        eI = {"drop": by7[lb]["mean_drop"], "se": by7[lb]["standard_error"], "clean": c7}
        sD, sI = rd.significant_sign(eD), rd.significant_sign(eI)
        dD, dI = rd.d_of(eD), rd.d_of(eI)
        rows.append({"label": lb, "d_D": dD, "d_I": dI, "sig_D": sD, "sig_I": sI,
                     "rank_D": c.get("signed_rank"), "rank_I": by7[lb].get("signed_rank"),
                     "inversion_shared": inversion_shared(d_D=dD, sig_D=sD > 0, d_I=dI, sig_I=sI > 0)})
    top = [r for r in rows if r["label"] in set(top_labels)]
    return {"clean_I": c7, "clean_D": c2, "n_I": s7["clean_run"].get("n_instances"),
            "twin_I": (s7.get("counterfactual_run") or {}).get("mean_logit_difference"),
            "n_both_positive": sum(1 for r in rows if r["sig_D"] > 0 and r["sig_I"] > 0),
            "n_D_positive": sum(1 for r in rows if r["sig_D"] > 0),
            "n_inversion_shared": sum(r["inversion_shared"] for r in rows),
            "top20_inversion_shared": sum(r["inversion_shared"] for r in top), "top20": top, "rows": rows}


def b_share(root, t, classes):
    p = os.path.join(root, "s2p", "U__leaf", f"{t}_v2", "knockout", "sweep.json")
    if not os.path.isfile(p):
        return None
    comps = [c for c in _load(p)["components"] if c["label"] != "mlp.0.0" and c.get("signed_rank") is not None]
    comps.sort(key=lambda c: c["signed_rank"])
    top = comps[:80]
    rows = [(c["label"], c["mean_drop"], (classes.get(c["label"]) or {}).get("class")) for c in top]
    return {"share": shared_share(rows), "n": len(rows)}


# ------------------------------------------------------------------ outputs

def _f(x, nd=3):
    if x is None:
        return "-"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def _ci(c, nd=3):
    return "-" if c is None else f"[{c[0]:.{nd}f}, {c[1]:.{nd}f}]"


def overall(readings: dict) -> str:
    from collections import Counter
    cnt = Counter(readings.values())
    top, n = cnt.most_common(1)[0] if cnt else (None, 0)
    if n >= 2:
        return top
    return "mixed (" + ", ".join(f"{t} {r}" for t, r in readings.items()) + ")"


def markdown(res) -> str:
    L = ["# Ticket 03 phase-1C results: R-AB, R-inv, routing, S7 vs S2p (Bridges-2 H100)", "",
         "Generated by `outputs/_launch_mechanism_analysis/p1c_results.py` from `outputs/_analyses/mechanism-analysis-p1/`"
         " (heldout_d, heldout_h, heldout_f, rinv_d, rinv_i, s7, s2p, greedy) and the groups meta under "
         "`docs/research/mechanism-analysis/phase1/groups/`. Held-out sample: n = 100, seed 1, the selection ids "
         "excluded. f = (mean clean - mean KO) / (mean clean - mean twin), a ratio of means; accuracy counts the "
         "deceptive item. CIs: per-instance bootstrap, 2,000 resamples (R-inv: clustered by D's pressure_id).", ""]
    if res.get("reading"):
        L += [res["reading"].rstrip(), ""]
    L += ["## R-AB readings", "",
          "| task | reading | deciding set | k | f_D [95% CI] | KO acc [95% CI] | null f max | (i) | (ii) H acc / margin move | (ii) F acc / margin move | (ii) |",
          "| --- " * 11 + "|"]
    for t, r in res["rab"].items():
        c = r["candidates"].get(r["deciding"], {})
        ii = c.get("ii_detail") or {}
        mv = lambda s: ("-" if not ii.get(s) else f"{ii[s]['acc_move']:+.3f} / {100 * ii[s]['margin_move_rel']:+.1f}%")  # noqa: E731
        L.append(f"| {t} | {r['reading']} | {r['deciding']} | {c.get('k', '-')} | {_f(c.get('f'))} {_ci(c.get('f_ci'))} "
                 f"| {_f(c.get('acc'))} {_ci(c.get('acc_ci'))} | {_f(c.get('null_f_max'))} | {_f(c.get('i'))} "
                 f"| {mv('H')} | {mv('F')} | {_f(c.get('ii'))} |")
    L += ["", f"Overall (shared by >= 2 tasks): **{res['overall']}**.", ""]
    for t, r in res["rab"].items():
        L += [f"### {t}: mediation curves (held-out D; clean {r['clean_mean']:.3f}, twin {r['twin_mean']:.3f}, "
              f"gap {r['gap']:.3f}, n = {r['n']})", "",
              "| selector | k | f_D [95% CI] | KO acc [95% CI] | null f mean [95% CI] | null f max | (i) | H acc / margin move | F acc / margin move | (ii) |",
              "| --- " * 10 + "|"]
        for name, c in sorted(((n, c) for n, c in r["candidates"].items() if c["selector"] != "uonly"),
                              key=lambda kv: (kv[1]["selector"] != "single", kv[1]["k"])):
            ii = c["ii_detail"] or {}
            mv = lambda s: ("-" if not ii.get(s) else f"{ii[s]['acc_move']:+.3f} / {100 * ii[s]['margin_move_rel']:+.1f}%")  # noqa: E731
            L.append(f"| {c['selector']} | {c['k']} | {_f(c['f'])} {_ci(c['f_ci'])} | {_f(c['acc'])} {_ci(c['acc_ci'])} "
                     f"| {_f(c['null_f_mean'])} {_ci(c['null_f_mean_ci'])} | {_f(c['null_f_max'])} | {_f(c['i'])} "
                     f"| {mv('H')} | {mv('F')} | {_f(c['ii'])} |")
        dec = r["candidates"].get(r["deciding"])
        if dec:
            L += ["", f"Deciding set `{r['deciding']}` ({r['reading']}" + (", descriptive" if r["reading"] == "B" else "")
                  + "):", "", "| member | circuits | sets | R-cls |", "| --- | --- | --- | --- |"]
            for m in res["members"][t]:
                L.append(f"| {m['label']} | {' '.join(m['circuits']) or 'outside'} | {' '.join(m['sets']) or '-'} "
                         f"| {m['class'] or '-'} |")
        if r["reading"] == "B" and res["b_share"].get(t):
            L += ["", f"B: shared-class share of the summed positive S2p effect over the top 80: "
                      f"{_f(res['b_share'][t]['share'])}."]
        L.append("")
    L += ["## U-only top-k arm (R24, descriptive)", "",
          "The single selector restricted to U's 123 heads (the six coarse v2 circuits' heads), same k grid, same "
          "20-draw layer-matched null on held-out D and the same H/F item-swap check for k <= 20. It never enters the "
          "R-AB reading; it compares the circuits' best heads with the model's best Components (the unrestricted "
          "single selector, shown beside it at the same k).", "",
          "| task | k | U-only f_D [95% CI] | U-only KO acc | null f max | meets (i) | H / F acc move | single f_D | single KO acc |",
          "| --- " * 9 + "|"]
    for t, r in res["rab"].items():
        for name, c in sorted(((n, c) for n, c in r["candidates"].items() if c["selector"] == "uonly"),
                              key=lambda kv: kv[1]["k"]):
            sg = r["candidates"].get(f"single_k{c['k']}", {})
            ii = c["ii_detail"] or {}
            hf = ("-" if not ii.get("H") or not ii.get("F")
                  else f"{ii['H']['acc_move']:+.3f} / {ii['F']['acc_move']:+.3f}")
            L.append(f"| {t} | {c['k']} | {_f(c['f'])} {_ci(c['f_ci'])} | {_f(c['acc'])} | {_f(c['null_f_max'])} | "
                     f"{_f(c['i'])} | {hf} | {_f(sg.get('f'))} | {_f(sg.get('acc'))} |")
    L += ["", "## Named groups on the held-out samples", "",
          "| task | group | heads | f_D | KO acc D | H acc / margin move | F acc / margin move |", "| --- " * 7 + "|"]
    for t, g in res["named"].items():
        for name, v in g.items():
            hm = (f"{v['acc_move_H']:+.3f} / {100 * v['margin_move_rel_H']:+.1f}%" if "acc_move_H" in v else "-")
            fm = (f"{v['acc_move_F']:+.3f} / {100 * v['margin_move_rel_F']:+.1f}%" if "acc_move_F" in v else "-")
            L.append(f"| {t} | {name} | {v['n_components']} | {_f(v['f_D'])} | {_f(v['acc_D'])} | {hm} | {fm} |")
    L += ["", "## Routing check (shares of the clean-minus-twin gap, deciding set's preliminary C_t)", "",
          "| task | candidate | C_t size | C_t MLPs | (a) all 32 MLPs | (b) heads outside C_t | (c) all outside C_t |",
          "| --- " * 7 + "|"]
    for t, v in res["routing"].items():
        L.append(f"| {t} | {v['candidate']} | {v['C_t_size']} | {' '.join(v['C_t_mlps'] or [])} | "
                 f"{_f(v['a_all_mlps'])} | {_f(v['b_heads_outside_C'])} | {_f(v['c_all_outside_C'])} |")
    L += ["", "## R-inv (paired; R19(3) as amended by R23)", "",
          "| task | set | ids | rows | clusters | f_D | f_I | f_I - 0.5 f_D [95% CI] | label |", "| --- " * 9 + "|"]
    names = (("option B (primary)", "all"), ("option B, inversion-polarity only", "inversion_polarity"),
             ("R19(3) subset (robustness)", "r19"))
    for t, v in res["rinv"].items():
        for rows_name, key in names:
            x = v.get(key)
            if not x or not x.get("n"):
                continue
            conf = t == "far" and key != "inversion_polarity"
            L.append(f"| {t} | {v['candidate']} | {rows_name} | {x['n']} | {x['n_clusters']} | {_f(x['f_D'])} | "
                     f"{_f(x['f_I'])} | {_f(x['diff'])} {_ci(x['diff_ci'])} | {x['label']}"
                     + (" (polarity-confounded)" if conf else "") + " |")
    L += ["", "| task | id set | n | designation polarity | item polarity | template |", "| --- " * 6 + "|"]
    for t, v in res["rinv"].items():
        for k, st in (v.get("strata") or {}).items():
            L.append(f"| {t} | {k} | {st.get('n')} | {st.get('designation_polarity')} | {st.get('item_polarity')} | "
                     f"{st.get('template_variant')} |")
    L += ["", "Both id sets condition on survival of I's filter (argmax = target and margin >= 0.7 in both streams), so "
              "R-inv speaks for the instances whose transparent inversion the model follows. Option B (R23) draws I's "
              "own held-out sample (seed 1, the S1 selection ids excluded) and runs D on the same ids; the S_k were "
              "chosen on D's selection sample only. FAR stays polarity-confounded (I keeps mostly inversion-polarity "
              "rows); its inversion-polarity row compares like with like.", ""]
    L += ["## S7 (I) vs S2p (D), per Component (descriptive)", "",
          "| task | I clean / twin | D-positive | both positive | inversion-shared | of the S2p top 20 |",
          "| --- " * 6 + "|"]
    for t, v in res["s7"].items():
        if v:
            L.append(f"| {t} | {_f(v['clean_I'])} / {_f(v['twin_I'])} | {v['n_D_positive']} | {v['n_both_positive']} | "
                     f"{v['n_inversion_shared']} | {v['top20_inversion_shared']} / {len(v['top20'])} |")
    L += ["", "\"inversion-shared\": significant positive on both and d(I) / d(D) in [0.5, 2].", ""]
    if res.get("c_confound"):
        cc = res["c_confound"]
        L += ["## C-confound (far)", "", cc["text"], ""]
    if res.get("sacct"):
        L += ["## Bridges-2 sacct", "", "```", res["sacct"].rstrip(), "```", ""]
    return "\n".join(L)


def c_confound(p1a_json, named, rcls_counts):
    sets = {}
    if p1a_json and os.path.isfile(p1a_json):
        for r in _load(p1a_json).get("sets", []):
            if r.get("task") == "far" and r.get("set") in (5, 6):
                sets[r["set"]] = r
    g = (named.get("far") or {}).get("DmH_minus_core_far")
    parts = []
    for s in (5, 6):
        r = sets.get(s)
        if r:
            acc, npr = r.get("d_test_ko_acc") or {}, r.get("np_ko_rate") or {}
            parts.append(f"set {s} ({r.get('set_name')}): R-A1 {r.get('ra1')}, D-test KO acc mean {_f(acc.get('mean'))} "
                         f"/ zero {_f(acc.get('zero'))} / interchange {_f(acc.get('interchange'))}, no-pressure zero "
                         f"{_f(npr.get('zero'))}")
    if rcls_counts:
        parts.append(f"R-cls deception-leaning: D-H {rcls_counts.get('D-H')}, (D-H)-core {rcls_counts.get('(D-H)-core')}")
    if g:
        parts.append(f"held-out neutral-twin post-clause f_D of (D-H)-core: {_f(g['f_D'])}")
    return {"text": "; ".join(parts) + "." if parts else "inputs missing", "sets": sets, "heldout": g}


def main(argv=None) -> int:
    import ma_cells as mc
    import p1b_results as pb
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=os.path.join(mc.REPO, pb.ROOT))
    p.add_argument("--groups-dir", default=os.path.join(mc.REPO, "docs/research/mechanism-analysis/phase1/groups"))
    p.add_argument("--reports", default=pb.REPORTS)
    p.add_argument("--curated", default=pb.CURATED)
    p.add_argument("--reading", default=None)
    p.add_argument("--sacct", default=None)
    a = p.parse_args(argv)
    meta = _load(os.path.join(a.groups_dir, "meta.json"))
    p1b = _load(os.path.join(a.reports, "03-1b-results.json"))
    classes = p1b.get("rcls", {})
    lab, sets, _ = pb.membership()
    res = {"rab": {}, "named": {}, "routing": {}, "rinv": {}, "s7": {}, "b_share": {}, "members": {},
           "reading": open(a.reading).read() if a.reading else "",
           "sacct": open(a.sacct).read() if a.sacct else "", "missing": []}
    for t in TASKS:
        D = load_groups_cell(a.root, "heldout_d", t)
        H = load_groups_cell(a.root, "heldout_h", t)
        F = load_groups_cell(a.root, "heldout_f", t)
        if D is None:
            res["missing"].append(f"heldout_d/{t}")
            continue
        mt = meta["tasks"][t]
        r = rab(t, D, H, F, mt)
        res["rab"][t] = r
        res["named"][t] = named_groups(D, H, F)
        res["routing"][t] = routing(D, mt, r["deciding"])
        dec = r["candidates"].get(r["deciding"], {})
        res["members"][t] = [{"label": m, **pb.tags(m, lab, sets),
                              "class": (classes.get(t, {}).get(m) or {}).get("class")}
                             for m in dec.get("members", [])]
        res["b_share"][t] = b_share(a.root, t, classes.get(t, {}))
        RD, RI = load_groups_cell(a.root, "rinv_d", t), load_groups_cell(a.root, "rinv_i", t)
        drows = dataset_rows(t)
        clusters = {i: drows[i]["pressure_id"] for i in drows}
        sets_ = mt.get("rinv_sets") or {}
        read_ids = lambda key: set(open(os.path.join(a.groups_dir, sets_[key]["file"])).read().split())   # noqa: E731
        ids_b = read_ids("optionB") if "optionB" in sets_ else None
        ids_r19 = read_ids("r19") if "r19" in sets_ else None
        inv = set((sets_.get("optionB") or {}).get("inversion_polarity_ids", []))
        res["rinv"][t] = {"candidate": r["deciding"], "rule": mt.get("rinv_rule"), "seed": mt.get("rinv_seed"),
                          "strata": {k: {x: v[x] for x in ("n", "designation_polarity", "item_polarity",
                                                           "template_variant")} for k, v in sets_.items()},
                          "all": rinv(t, RD, RI, r["deciding"], clusters, subset=ids_b),
                          "inversion_polarity": rinv(t, RD, RI, r["deciding"], clusters, subset=inv),
                          "r19": rinv(t, RD, RI, r["deciding"], clusters, subset=ids_r19),
                          "per_candidate": {n: rinv(t, RD, RI, n, clusters, subset=ids_b)
                                            for n in (RD or {}).get("K", {})}}
        top20 = [c["label"] for c in sorted((c for c in _load(os.path.join(a.root, "s2p", "U__leaf", f"{t}_v2",
                                                                            "knockout", "sweep.json"))["components"]
                                             if c["label"] != "mlp.0.0" and c.get("signed_rank") is not None),
                                            key=lambda c: c["signed_rank"])[:20]]
        res["s7"][t] = s7_vs_s2p(a.root, t, top20)
    res["overall"] = overall({t: r["reading"] for t, r in res["rab"].items()}) if res["rab"] else "-"
    far_counts = (p1b.get("class_counts") or {}).get("far", {})
    res["c_confound"] = c_confound(os.path.join(a.reports, "03-1a-results.json"), res["named"],
                                   {k: (far_counts.get(k) or {}).get("deception-leaning") for k in ("D-H", "(D-H)-core")})
    os.makedirs(a.curated, exist_ok=True)
    with open(os.path.join(a.reports, "03-1c-results.json"), "w") as f:
        json.dump(res, f, indent=1, default=list)
    with open(os.path.join(a.reports, "03-1c-results.md"), "w") as f:
        f.write(markdown(res))
    with open(os.path.join(a.curated, "rab_curves.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "candidate", "selector", "k", "f_D", "f_lo", "f_hi", "acc", "acc_lo", "acc_hi",
                    "null_f_mean", "null_f_max", "test_i", "test_ii", "H_acc_move", "H_margin_move_rel",
                    "F_acc_move", "F_margin_move_rel", "members"])
        for t, r in res["rab"].items():
            for n, c in r["candidates"].items():
                ii = c["ii_detail"] or {}
                g = lambda s, k: (ii.get(s) or {}).get(k)   # noqa: E731
                w.writerow([t, n, c["selector"], c["k"], c["f"], *c["f_ci"], c["acc"], *c["acc_ci"], c["null_f_mean"],
                            c["null_f_max"], c["i"], c["ii"], g("H", "acc_move"), g("H", "margin_move_rel"),
                            g("F", "acc_move"), g("F", "margin_move_rel"), " ".join(c["members"])])
    with open(os.path.join(a.curated, "rinv.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "candidate", "rows", "n", "n_clusters", "f_D", "f_I", "diff", "diff_lo", "diff_hi", "label"])
        for t, v in res["rinv"].items():
            for rows_name, x in (("optionB", v["all"]), ("optionB_inversion_polarity", v["inversion_polarity"]),
                                 ("r19_robustness", v.get("r19"))):
                if x and x.get("n"):
                    w.writerow([t, v["candidate"], rows_name, x["n"], x["n_clusters"], x["f_D"], x["f_I"], x["diff"],
                                *x["diff_ci"], x["label"]])
    with open(os.path.join(a.curated, "routing.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "candidate", "C_t_size", "a_all_mlps", "b_heads_outside_C", "c_all_outside_C"])
        for t, v in res["routing"].items():
            w.writerow([t, v["candidate"], v["C_t_size"], v["a_all_mlps"], v["b_heads_outside_C"], v["c_all_outside_C"]])
    with open(os.path.join(a.curated, "s7_vs_s2p.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "label", "d_D", "d_I", "sig_D", "sig_I", "rank_D", "rank_I", "inversion_shared"])
        for t, v in res["s7"].items():
            for row in (v or {}).get("rows", []):
                w.writerow([t, row["label"], row["d_D"], row["d_I"], row["sig_D"], row["sig_I"], row["rank_D"],
                            row["rank_I"], row["inversion_shared"]])
    slim = {"overall": res["overall"],
            "rab": {t: {"reading": r["reading"], "deciding": r["deciding"],
                        "deciding_numbers": {k: v for k, v in r["candidates"].get(r["deciding"], {}).items()
                                             if k not in ("per_instance_f", "null_f")}} for t, r in res["rab"].items()},
            "rinv": {t: {k: v.get(k) for k in ("candidate", "rule", "seed", "all", "inversion_polarity", "r19", "strata")}
                     for t, v in res["rinv"].items()},
            "routing": res["routing"], "named": res["named"], "c_confound": res["c_confound"]["text"],
            "s7": {t: {k: v[k] for k in ("n_D_positive", "n_both_positive", "n_inversion_shared",
                                         "top20_inversion_shared")} for t, v in res["s7"].items() if v}}
    with open(os.path.join(a.curated, "p1c_readings.json"), "w") as f:
        json.dump(slim, f, indent=1, default=list)
    print(f"tasks {sorted(res['rab'])}; missing {res['missing']}; wrote {a.reports}/03-1c-results.{{md,json}} and "
          f"{a.curated}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
