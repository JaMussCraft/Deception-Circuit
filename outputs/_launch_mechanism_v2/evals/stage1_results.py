#!/usr/bin/env python3
"""
stage1_results.py -- the stage-1 results table of the v2 coarse suite (ticket 06).

Reads every stage-1 cell's outputs (paths from suite_v2.json; fetched to the Delta worktree) and writes

    reports/06-stage1-results.json   every cell's numbers
    reports/06-stage1-results.md     the tables, and per task the D-H home-task knockout call

Sufficiency cells (atomic X or (E) | m; evals sanity null pressure):
    faithfulness   the circuit alone: accuracy, exact match, logit diff, KL to the full model (null.json
                   `discovered`), against the full and empty anchors
    null           size-matched random circuits: mean accuracy, and how many of the 4 metrics beat all of
                   them (null.json stats `passes_95th`)
    pressure       the circuit under no_pressure / honest_instruction prompts (labels unchanged: the
                   deceptive answer is `target`, so a falling accuracy is the wanted reading)
    sanity         atomic home-test-set cells only: reproduces results.json node_eval (`delta.ok`)
Knockout cells ((E) - m; eval knockout):
    the model with the heads removed: accuracy, exact match, logit diff, KL; the task-side KO null of 20
    random head sets of the same size with the separation count (percentile <= 5 and z <= -2 per metric,
    the coarse SDR wave's gate; 4/4 is the gate EVAL 5 later adopted); flips to honest; wikitext
    collateral (KL/token, ppl ratio, and its own random-KO null); pressure-variant headlines

D-H call (per task): the D-H heads-only knockout on D's home test set is STRONG when it separates from its
random-KO null on 4/4 metrics (the written gate). The table also gives the share of D's own knockout
effect it reproduces, (full - DmH_ko) / (full - D_ko) on accuracy. Strong D-H tasks are recommended for the
conditional stage-2 cells (D_t - H_t KO on the other two tasks).

usage (from the repository root):
    python outputs/_launch_mechanism_v2/evals/stage1_results.py [--reports DIR] [--jobs-sacct FILE]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import drift  # noqa: E402
import mv2_cells as mc  # noqa: E402

REPORTS = "/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports"
METRICS = drift.METRICS


def _load(path):
    with open(path) as f:
        return json.load(f)


def _row(d):
    return {m: d.get(m) for m in METRICS}


def suff_metrics(cell_dir: str) -> dict:
    out = {"present": os.path.isfile(os.path.join(cell_dir, "null.json"))}
    if not out["present"]:
        return out
    null = _load(os.path.join(cell_dir, "null.json"))
    out["circuit"] = _row(null["discovered"])
    out["full"] = _row(null["anchors"]["full"])
    out["empty"] = _row(null["anchors"]["empty"])
    out["null_mean"] = {m: null["stats"][m]["mean"] for m in METRICS}
    out["null_beats_all"] = sum(bool(null["stats"][m]["passes_95th"]) for m in METRICS)
    p = os.path.join(cell_dir, "pressure.json")
    if os.path.isfile(p):
        pr = _load(p)
        out["pressure"] = {v: {"full_accuracy": pr["variants"][v]["full"]["accuracy"],
                               "circuit_accuracy": pr["variants"][v]["circuit"]["accuracy"],
                               "circuit_logit_diff": pr["variants"][v]["circuit"]["logit_diff"]}
                           for v in pr["variants"]}
        out["pressure_headline"] = pr.get("headline")
    s = os.path.join(cell_dir, "sanity.json")
    if os.path.isfile(s):
        sa = _load(s)
        out["sanity"] = {"ok": bool(sa["delta"]["ok"]), "max_delta": sa["delta"]["max_delta"]}
    summary = _load(os.path.join(cell_dir, "summary.json"))
    out["skipped"] = summary.get("skipped") or {}
    return out


def ko_metrics(cell_dir: str) -> dict:
    path = os.path.join(cell_dir, "knockout.json")
    out = {"present": os.path.isfile(path)}
    if not out["present"]:
        return out
    ko = _load(path)
    flat = drift.metrics_of(ko)
    out["knockout"] = _row(ko["task"]["knockout"])
    out["null_mean"] = {m: ko["task"]["null"]["stats"][m]["mean"] for m in METRICS}
    out["null_percentile"] = {m: ko["task"]["null"]["stats"][m]["percentile"] for m in METRICS}
    out["null_z"] = {m: ko["task"]["null"]["stats"][m]["z"] for m in METRICS}
    out["separated"] = flat["task.null.separated"]
    out["flipped_honest"] = ko["task"]["flip_summary"]["n_flipped_honest"]
    out["n"] = ko["task"]["knockout"]["n"]
    out["wikitext"] = {"kl_per_token": flat["wikitext.kl_per_token"], "ppl_ratio": flat["wikitext.ppl_ratio"],
                       "null_mean_kl": flat["wikitext.null.kl_per_token.mean"],
                       "null_percentile": flat["wikitext.null.kl_per_token.percentile"]}
    out["variants"] = {k.split(".")[1] + "." + k.split(".")[2]: v for k, v in flat.items() if k.startswith("variants.")}
    out["headline"] = ko.get("headline")
    return out


def collect(cells, root: str = mc.REPO) -> list:
    jobs = mc.jobs_for(mc.select(cells, "1"))
    rows = []
    for job in jobs:
        for c in job["cells"]:
            d = os.path.join(root, job["results"][c["label"]])
            m = suff_metrics(d) if c["kind"] == "sufficiency" else ko_metrics(d)
            rows.append({"label": c["label"], "kind": c["kind"], "block": c["block"], "job": job["job"],
                         "home_task": c["home_task"], "dataset": c["dataset"], "expr": c["expr"],
                         "heads": c["expected_heads"], "result_dir": job["results"][c["label"]], **m})
    return rows


def dh_call(rows, task: str) -> dict:
    """The D-H home-task knockout call for one task (t = far|sdr|ser)."""
    by = {r["label"]: r for r in rows}
    D, H = f"D_{task}", f"H_{task}"
    dmh, dko, suff = by.get(f"{D}_minus_{H}_hko"), by.get(f"{D}_hko"), by.get(D)
    if not (dmh and dmh.get("present") and dko and dko.get("present")):
        return {"task": f"{task}_v2", "status": "missing"}
    full = (suff or {}).get("full", {}).get("accuracy") if suff and suff.get("present") else None
    share = None
    if full is not None and full != dko["knockout"]["accuracy"]:
        share = (full - dmh["knockout"]["accuracy"]) / (full - dko["knockout"]["accuracy"])
    strong = dmh["separated"] == 4
    return {"task": f"{task}_v2", "status": "ok", "heads": dmh["heads"], "full_accuracy": full,
            "D_ko_accuracy": dko["knockout"]["accuracy"], "DmH_ko_accuracy": dmh["knockout"]["accuracy"],
            "DmH_null_mean_accuracy": dmh["null_mean"]["accuracy"], "DmH_separated": dmh["separated"],
            "DmH_flipped_honest": dmh["flipped_honest"], "share_of_D_effect": share, "strong": strong,
            "recommend_conditional": strong}


def _f(x, nd=3):
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def _sanity_text(san) -> str:
    if not san:
        return "skipped"
    return f"{'ok' if san['ok'] else 'tolerance flag'} (max d {san['max_delta']:.1e})"


def markdown(rows, calls, sacct_rows, reading: str = "") -> str:
    out = ["# Ticket 06 stage-1 results: six coarse v2 circuits on Bridges-2 (H100)", "",
           "Generated by `outputs/_launch_mechanism_v2/evals/stage1_results.py` from the fetched cells "
           "(`outputs/_suites/mechanism-v2-coarse/stage1/`). Interchange ablation, 1,000 test items per cell, "
           "20 random circuits per null, compositions at leaf. Accuracy counts the DECEPTIVE answer "
           "(`target`), so on D's test set a knockout is wanted to push it down, and on the pressure variants "
           "a falling circuit accuracy is the wanted reading.", ""]
    if reading:
        out += [reading.rstrip(), ""]
    missing = [r["label"] + " (" + r["dataset"] + ")" for r in rows if not r.get("present")]
    if missing:
        out += [f"**Missing cells:** {', '.join(missing)}", ""]
    out += ["## Sufficiency cells", "",
            "| cell | test set | heads | acc | EM | LD | KL | full acc | empty acc | null mean acc | beats null (of 4) "
            "| no_pressure acc (full / circuit) | honest_instr acc (full / circuit) | sanity |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        if r["kind"] != "sufficiency" or not r.get("present"):
            continue
        c, pr = r["circuit"], r.get("pressure") or {}
        npv, hiv = pr.get("no_pressure", {}), pr.get("honest_instruction", {})
        san = r.get("sanity")
        out.append(f"| {r['label']} | {r['dataset']} | {r['heads']} | {_f(c['accuracy'])} | {_f(c['exact_match'])} "
                   f"| {_f(c['logit_diff'])} | {_f(c['kl_div'])} | {_f(r['full']['accuracy'])} "
                   f"| {_f(r['empty']['accuracy'])} | {_f(r['null_mean']['accuracy'])} | {r['null_beats_all']} "
                   f"| {_f(npv.get('full_accuracy'))} / {_f(npv.get('circuit_accuracy'))} "
                   f"| {_f(hiv.get('full_accuracy'))} / {_f(hiv.get('circuit_accuracy'))} "
                   f"| {_sanity_text(san)} |")
    out += ["", "## Heads-only knockout cells", "",
            "| cell | test set | heads | KO acc | KO EM | KO LD | KO KL | null mean acc | separated (of 4) | 4/4 "
            "| flipped honest | wikitext KL/tok (null mean, pct) | ppl ratio | no_pressure acc (full / KO) "
            "| honest_instr acc (full / KO) |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        if r["kind"] != "knockout" or not r.get("present"):
            continue
        k, v, w = r["knockout"], r["variants"], r["wikitext"]
        out.append(f"| {r['label']} | {r['dataset']} | {r['heads']} | {_f(k['accuracy'])} | {_f(k['exact_match'])} "
                   f"| {_f(k['logit_diff'])} | {_f(k['kl_div'])} | {_f(r['null_mean']['accuracy'])} | {r['separated']} "
                   f"| {'yes' if r['separated'] == 4 else 'no'} | {r['flipped_honest']} / {r['n']} "
                   f"| {_f(w['kl_per_token'])} ({_f(w['null_mean_kl'])}, {_f(w['null_percentile'], 0)}) "
                   f"| {_f(w['ppl_ratio'])} "
                   f"| {_f(v.get('no_pressure.full_accuracy'))} / {_f(v.get('no_pressure.knockout_accuracy'))} "
                   f"| {_f(v.get('honest_instruction.full_accuracy'))} / "
                   f"{_f(v.get('honest_instruction.knockout_accuracy'))} |")
    out += ["", "## D-H home-task knockout and the conditional stage-2 cells", "",
            "Strong = the `(D - H) - m` knockout separates from its 20 random-KO head sets on 4/4 metrics "
            "(percentile <= 5 and z <= -2; the coarse SDR wave's gate, 4/4 as EVAL 5 adopted it). Share = "
            "(full - D-H KO) / (full - D KO) on accuracy: how much of D's own knockout effect the D-only "
            "heads reproduce.", "",
            "| task | D-H heads | full acc | D KO acc | D-H KO acc | D-H null mean acc | D-H separated | flipped "
            "honest | share of D effect | strong | conditional cells |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for c in calls:
        if c["status"] != "ok":
            out.append(f"| {c['task']} | missing | | | | | | | | | |")
            continue
        out.append(f"| {c['task']} | {c['heads']} | {_f(c['full_accuracy'])} | {_f(c['D_ko_accuracy'])} "
                   f"| {_f(c['DmH_ko_accuracy'])} | {_f(c['DmH_null_mean_accuracy'])} | {c['DmH_separated']} "
                   f"| {c['DmH_flipped_honest']} | {_f(c['share_of_D_effect'])} | {'yes' if c['strong'] else 'no'} "
                   f"| {'recommend' if c['recommend_conditional'] else 'not recommended'} |")
    if sacct_rows:
        out += ["", "## Jobs (Bridges-2 sacct)", "", "| job | Slurm id | state | elapsed | node |",
                "| --- | --- | --- | --- | --- |"]
        out += [f"| {s['job']} | {s['id']} | {s['state']} | {s['elapsed']} | {s['node']} |" for s in sacct_rows]
    return "\n".join(out) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--reports", default=REPORTS)
    p.add_argument("--sacct", default=None, help="JSON list of {job, id, state, elapsed, node}")
    p.add_argument("--reading", default=os.path.join(REPORTS, "06-stage1-reading.md"),
                   help="hand-written reading included after the introduction (skipped when missing)")
    a = p.parse_args(argv)
    cells = mc.load_suite()["cells"]
    rows = collect(cells)
    calls = [dh_call(rows, t) for t in mc.TASKS]
    sacct_rows = _load(a.sacct) if a.sacct else []
    with open(os.path.join(a.reports, "06-stage1-results.json"), "w") as f:
        json.dump({"cells": rows, "dh_calls": calls, "jobs": sacct_rows}, f, indent=1)
    with open(os.path.join(a.reports, "06-stage1-results.md"), "w") as f:
        reading = open(a.reading).read() if a.reading and os.path.isfile(a.reading) else ""
        f.write(markdown(rows, calls, sacct_rows, reading))
    print(f"{sum(bool(r.get('present')) for r in rows)} of {len(rows)} cells present")
    for c in calls:
        print(c)


if __name__ == "__main__":
    main()
