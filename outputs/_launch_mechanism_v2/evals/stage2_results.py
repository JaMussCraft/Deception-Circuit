#!/usr/bin/env python3
"""
stage2_results.py -- the stage-2 results of the v2 coarse suite (ticket 06, spec 14.G14 / G16).

Reads every stage-2 cell (conditional cells included) with stage1_results' parsers and writes

    reports/06-stage2-results.json   every cell's numbers
    reports/06-stage2-results.md     tables per block (a hand-written reading is included when present)

Blocks: cross-task D transfer (each D on the other two D test sets; the home cell comes from stage 1), the
31-head shared D core on all three tasks, the exclusives D_t - D_u - D_v (the --xor family) on their own
test sets, H on D's test set, D on <task>_v2_nopressure, and the conditional D_t - H_t knockouts on the
other two tasks. Same conventions as stage 1: accuracy counts the `target` of the test set (the deceptive
item on <t>_v2, the honest item on <t>_v2_nopressure); separation = percentile <= 5 and z <= -2 per metric
against 20 random head sets.

usage (from the repository root):
    python outputs/_launch_mechanism_v2/evals/stage2_results.py [--reports DIR] [--sacct FILE] [--reading FILE]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import mv2_cells as mc  # noqa: E402
import stage1_results as s1  # noqa: E402

TASK_NAMES = [f"{t}_v2" for t in mc.TASKS]


def collect(cells, stage: str, root: str = mc.REPO, include_conditional: bool = False) -> list:
    rows = []
    for job in mc.jobs_for(mc.select(cells, stage, include_conditional)):
        for c in job["cells"]:
            d = os.path.join(root, job["results"][c["label"]])
            m = s1.suff_metrics(d) if c["kind"] == "sufficiency" else s1.ko_metrics(d)
            rows.append({"label": c["label"], "kind": c["kind"], "block": c["block"], "job": job["job"],
                         "home_task": c["home_task"], "test_task": c["test_task"], "dataset": c["dataset"],
                         "expr": c["expr"], "heads": c["expected_heads"], "conditional": c["conditional"],
                         "result_dir": job["results"][c["label"]], **m})
    return rows


def _f(x, nd=3):
    return s1._f(x, nd)


def _get(rows, label, dataset):
    for r in rows:
        if r["label"] == label and r["dataset"] == dataset and r.get("present"):
            return r
    return None


def transfer_matrix(rows_all, kind: str) -> list:
    """[(circuit, {test task: value})]: suff -> circuit accuracy, knockout -> KO accuracy (separated)."""
    out = []
    for t in mc.TASKS:
        label = f"D_{t}" if kind == "sufficiency" else f"D_{t}_hko"
        row = {}
        for u in mc.TASKS:
            r = _get(rows_all, label, f"{u}_v2")
            if r is None:
                row[f"{u}_v2"] = None
            elif kind == "sufficiency":
                row[f"{u}_v2"] = {"accuracy": r["circuit"]["accuracy"], "kl_div": r["circuit"]["kl_div"],
                                  "no_pressure": (r.get("pressure") or {}).get("no_pressure", {}).get(
                                      "circuit_accuracy")}
            else:
                row[f"{u}_v2"] = {"accuracy": r["knockout"]["accuracy"], "separated": r["separated"],
                                  "no_pressure": r["variants"].get("no_pressure.knockout_accuracy")}
        out.append((label, row))
    return out


def _ko_table(rows, title, note=""):
    out = [f"## {title}", ""] + ([note, ""] if note else []) + [
        "| cell | test set | heads | KO acc | KO EM | KO KL | null mean acc | separated (of 4) | flipped | "
        "wikitext KL/tok (null mean) | no_pressure acc (full / KO) | honest_instr acc (full / KO) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        if not r.get("present"):
            out.append(f"| {r['label']} | {r['dataset']} | {r['heads']} | missing |||||||||")
            continue
        k, v, w = r["knockout"], r["variants"], r["wikitext"]
        out.append(f"| {r['label']} | {r['dataset']} | {r['heads']} | {_f(k['accuracy'])} | {_f(k['exact_match'])} "
                   f"| {_f(k['kl_div'])} | {_f(r['null_mean']['accuracy'])} | {r['separated']} "
                   f"| {r['flipped_honest']} / {r['n']} | {_f(w['kl_per_token'])} ({_f(w['null_mean_kl'])}) "
                   f"| {_f(v.get('no_pressure.full_accuracy'))} / {_f(v.get('no_pressure.knockout_accuracy'))} "
                   f"| {_f(v.get('honest_instruction.full_accuracy'))} / "
                   f"{_f(v.get('honest_instruction.knockout_accuracy'))} |")
    return out + [""]


def _suff_table(rows, title, note=""):
    out = [f"## {title}", ""] + ([note, ""] if note else []) + [
        "| cell | test set | heads | acc | EM | LD | KL | full acc | null mean acc | beats null (of 4) "
        "| no_pressure acc (full / circuit) | honest_instr acc (full / circuit) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        if not r.get("present"):
            out.append(f"| {r['label']} | {r['dataset']} | {r['heads']} | missing |||||||||")
            continue
        c, pr = r["circuit"], r.get("pressure") or {}
        npv, hiv = pr.get("no_pressure", {}), pr.get("honest_instruction", {})
        out.append(f"| {r['label']} | {r['dataset']} | {r['heads']} | {_f(c['accuracy'])} | {_f(c['exact_match'])} "
                   f"| {_f(c['logit_diff'])} | {_f(c['kl_div'])} | {_f(r['full']['accuracy'])} "
                   f"| {_f(r['null_mean']['accuracy'])} | {r['null_beats_all']} "
                   f"| {_f(npv.get('full_accuracy'))} / {_f(npv.get('circuit_accuracy'))} "
                   f"| {_f(hiv.get('full_accuracy'))} / {_f(hiv.get('circuit_accuracy'))} |")
    return out + [""]


def markdown(rows, rows_s1, sacct_rows, reading="") -> str:
    allrows = rows_s1 + rows
    out = ["# Ticket 06 stage-2 results: cross-task, core, exclusives and controls (Bridges-2, H100)", "",
           "Generated by `outputs/_launch_mechanism_v2/evals/stage2_results.py` from "
           "`outputs/_suites/mechanism-v2-coarse/stage2/` (home-task cells from stage 1). Interchange ablation, "
           "1,000 test items, 20 random circuits per null, compositions at leaf. Accuracy counts the test set's "
           "`target`: the DECEPTIVE item on `<t>_v2`, the HONEST item on `<t>_v2_nopressure`.", ""]
    if reading:
        out += [reading.rstrip(), ""]
    missing = [f"{r['label']} ({r['dataset']})" for r in rows if not r.get("present")]
    if missing:
        out += [f"**Missing cells:** {', '.join(missing)}", ""]
    for kind, title in (("sufficiency", "Cross-task D transfer: circuit alone (accuracy / KL; no_pressure acc)"),
                        ("knockout", "Cross-task D transfer: heads-only knockout (KO acc, separated of 4; "
                                     "no_pressure KO acc)")):
        out += [f"## {title}", "", "| circuit \\ test set | " + " | ".join(TASK_NAMES) + " |",
                "| --- |" + " --- |" * len(TASK_NAMES)]
        for label, row in transfer_matrix(allrows, kind):
            cells = []
            for u in TASK_NAMES:
                v = row[u]
                if v is None:
                    cells.append("-")
                elif kind == "sufficiency":
                    cells.append(f"{_f(v['accuracy'])} / {_f(v['kl_div'])}; np {_f(v['no_pressure'])}")
                else:
                    cells.append(f"{_f(v['accuracy'])} ({v['separated']}); np {_f(v['no_pressure'])}")
            out.append(f"| {label} | " + " | ".join(cells) + " |")
        out.append("")
    by_block = {}
    for r in rows:
        by_block.setdefault((r["block"], r["kind"]), []).append(r)
    out += _suff_table(by_block.get(("cross_task", "sufficiency"), []), "Cross-task sufficiency cells")
    out += _ko_table(by_block.get(("cross_task", "knockout"), []), "Cross-task knockout cells")
    out += _suff_table(by_block.get(("core", "sufficiency"), []), "Shared D core (D_far & D_sdr & D_ser, 31 heads): "
                       "sufficiency")
    out += _ko_table(by_block.get(("core", "knockout"), []), "Shared D core: heads-only knockout")
    out += _ko_table(by_block.get(("exclusive", "knockout"), []), "Exclusives D_t - D_u - D_v (the --xor family), "
                     "own test set")
    out += _suff_table(by_block.get(("H_on_D_test_set", "sufficiency"), []), "H on D's test set: circuit alone",
                       "Does the Honest-Twin circuit alone produce the deceptive answer under pressure?")
    out += _ko_table(by_block.get(("H_on_D_test_set", "knockout"), []), "H on D's test set: heads-only knockout",
                     "Does removing H's heads remove the deception the way removing D's does?")
    out += _suff_table(by_block.get(("D_on_nopressure", "sufficiency"), []), "D on the nopressure test set: "
                       "circuit alone", "Accuracy here counts the HONEST item (nopressure labels).")
    out += _ko_table(by_block.get(("D_on_nopressure", "knockout"), []), "D on the nopressure test set: heads-only "
                     "knockout", "A falling accuracy means the knockout removes the honest answer (inverts it).")
    out += _ko_table(by_block.get(("conditional_D_minus_H_cross_task", "knockout"), []),
                     "Conditional: D_t - H_t knockout on the other two tasks (user go G16, all 6)",
                     "Home-task D-H cells (stage 1): far 0.191 (4/4), sdr 0.513 (1/4), ser 0.228 (4/4).")
    if sacct_rows:
        out += ["## Jobs (Bridges-2 sacct)", "", "| job | Slurm id | state | elapsed | node |",
                "| --- | --- | --- | --- | --- |"]
        out += [f"| {s['job']} | {s['id']} | {s['state']} | {s['elapsed']} | {s['node']} |" for s in sacct_rows]
    return "\n".join(out) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--reports", default=s1.REPORTS)
    p.add_argument("--sacct", default=None, help="JSON list of {job, id, state, elapsed, node}")
    p.add_argument("--reading", default=os.path.join(s1.REPORTS, "06-stage2-reading.md"))
    a = p.parse_args(argv)
    cells = mc.load_suite()["cells"]
    rows = collect(cells, "2", include_conditional=True)
    rows_s1 = collect(cells, "1")
    sacct_rows = s1._load(a.sacct) if a.sacct else []
    reading = open(a.reading).read() if a.reading and os.path.isfile(a.reading) else ""
    with open(os.path.join(a.reports, "06-stage2-results.json"), "w") as f:
        json.dump({"cells": rows, "transfer": {k: transfer_matrix(rows_s1 + rows, k)
                                               for k in ("sufficiency", "knockout")}, "jobs": sacct_rows},
                  f, indent=1)
    with open(os.path.join(a.reports, "06-stage2-results.md"), "w") as f:
        f.write(markdown(rows, rows_s1, sacct_rows, reading))
    print(f"{sum(bool(r.get('present')) for r in rows)} of {len(rows)} stage-2 cells present")


if __name__ == "__main__":
    main()
