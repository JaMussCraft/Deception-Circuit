#!/usr/bin/env python3
"""
p1a_results.py -- the phase-1A results of the mechanism-analysis feature (ticket 03, spec sections 2.5 and 4).

Reads the fetched 1A cells (paths from suite_ma.json), ticket 06's interchange cells of record (its results JSON in
the mechanism-datasets reports), the flip audits run on the mean and zero groups (`flip_audit_analysis.py`, one
JSON per group), and the fetched chain logs, and writes

    <reports>/03-1a-results.json    every number
    <reports>/03-1a-results.md      per-cell table, per-set table with R-A1, flip audit, job timings
    <curated>/p1a_cells.csv, p1a_sets.csv, p1a_readings.json   (R6 copy under docs/research/mechanism-analysis/)

Conventions (spec 2.5, R13, R19(2), R21):
  * accuracy counts the DECEPTIVE item on D's test set and on both prompt variants (labels unchanged), so the
    variant knockout accuracy is the KO deceptive rate;
  * R-A1 reads sets 3-6 from the D-test KO accuracy under MEAN and the no-pressure KO deceptive rate under ZERO;
    the mean no-pressure column is reported under both banks (task bank, variant-matched bank) as robustness;
  * sets 1, 2 and 7 are calibration rows with no reading;
  * ser's set 6 equals its set 5 (R21) and repeats it, marked;
  * interchange: set 6 from 1A (far, sdr), every other set from ticket 06.

usage (from the repository root):
    python outputs/_launch_mechanism_analysis/p1a_results.py [--flip-audit-dir DIR] [--logs-dir DIR]
        [--job-ids far=ID sdr=ID ser=ID] [--sacct FILE] [--reading FILE] [--reports DIR] [--curated DIR]
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ma_cells as mc  # noqa: E402

#: Ticket 06's separation rule (percentile <= 5 and z <= -2 per metric, of 4), reused, not restated.
drift = mc._load_module("mv2_drift", f"{mc.V2_LAUNCH}/drift.py")
METRICS = drift.METRICS

EPS = 1e-9
TASK_ORDER = ("far", "sdr", "ser")
#: R-A1 reads sets 3-6; sets 1, 2 and 7 are calibration rows (spec 2.5).
RA1_SETS = (3, 4, 5, 6)
SET_NAMES = {1: "D_t", 2: "H_t (on D's test set)", 3: "core", 4: "excl_t", 5: "D_t - H_t",
             6: "(D_t - H_t) - core", 7: "D_t & H_t"}
#: Spec 2.5: every mean/zero cell with D-test KO accuracy in this band gets the positional-default flip audit.
AUDIT_BAND = (0.25, 0.75)

MD_REPORTS = "/projects/beto/swong2/Alignment/.scratch/mechanism-datasets/reports"
TICKET06_RESULTS = (f"{MD_REPORTS}/06-stage1-results.json", f"{MD_REPORTS}/06-stage2-results.json")
REPORTS = "/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports"
CURATED = os.path.join(mc.REPO, "docs", "research", "mechanism-analysis", "phase1a")
FLIP_DIR = os.path.join(mc.REPO, mc.SUITE_ROOT, "phase1a", "flip_audit")
LOGS_DIR = os.path.join(mc.REPO, "logs", "bridges2")


# ------------------------------------------------------------------ the pre-registered reading

def ra1_reading(d_test_ko_acc_mean, np_rate_zero):
    """R-A1 (spec 2.5, R13): D-test KO accuracy under mean, no-pressure KO deceptive rate under zero.

    Checked in the table's order; band edges are inclusive. None when either column is missing.
    """
    if d_test_ko_acc_mean is None or np_rate_zero is None:
        return None
    d, z = d_test_ko_acc_mean, np_rate_zero
    if 0.25 - EPS <= d <= 0.75 + EPS and z >= 0.25 - EPS:
        return "answer machinery"
    if d <= 0.25 + EPS and z <= 0.10 + EPS:
        return "deception-specific"
    if d <= 0.25 + EPS and z >= 0.75 - EPS:
        return "item carrier"
    return "partial or none"


# ------------------------------------------------------------------ one cell

def _headline(section, key):
    return ((section or {}).get("headline") or {}).get(key)


def cell_numbers(ko: dict) -> dict:
    """One fetched knockout.json -> the numbers of the 1A table.

    Accuracy counts the deceptive item (`target`) on D's test set and on both prompt variants (labels unchanged),
    so the variant knockout accuracy is the KO deceptive rate. `variants.<v>` is ablated with the task bank;
    `variants_matched_bank.no_pressure` (mean cells under --variant-mean-bank only) with the rows' own bank.
    """
    task = ko["task"]
    stats = task["null"]["stats"]
    separated = sum(int(stats[m]["percentile"] <= drift.SEPARATION_PCT and stats[m]["z"] <= drift.SEPARATION_Z)
                    for m in METRICS)
    variants = ko.get("variants") or {}
    matched = (ko.get("variants_matched_bank") or {}).get("no_pressure")
    wt = ko.get("wikitext") or {}
    return {
        "ablation": ko.get("ablation"),
        "ko_accuracy": task["knockout"]["accuracy"],
        "ko_logit_diff": task["knockout"].get("logit_diff"),
        "ko_kl_div": task["knockout"].get("kl_div"),
        "n": task["knockout"].get("n"),
        "flipped_honest": (task.get("flip_summary") or {}).get("n_flipped_honest"),
        "stayed_deceptive": (task.get("flip_summary") or {}).get("n_stayed_deceptive"),
        "null_mean_accuracy": stats["accuracy"]["mean"],
        "null_accuracy_percentile": stats["accuracy"]["percentile"],
        "null_accuracy_z": stats["accuracy"]["z"],
        "separated": separated,
        "np_full_rate": _headline(variants.get("no_pressure"), "full_accuracy"),
        "np_ko_rate_task_bank": _headline(variants.get("no_pressure"), "knockout_accuracy"),
        "np_ko_rate_matched_bank": _headline(matched, "knockout_accuracy"),
        "matched_bank": (matched or {}).get("mean_bank"),
        "hi_full_rate": _headline(variants.get("honest_instruction"), "full_accuracy"),
        "hi_ko_rate_task_bank": _headline(variants.get("honest_instruction"), "knockout_accuracy"),
        "wikitext_kl_per_token": (wt.get("discovered") or {}).get("kl_per_token"),
        "wikitext_ppl_ratio": (wt.get("discovered") or {}).get("ppl_ratio"),
        "wikitext_null_mean_kl": (((wt.get("null") or {}).get("stats") or {}).get("kl_per_token") or {}).get("mean"),
    }


# ------------------------------------------------------------------ per set

def _get(d, key):
    return (d or {}).get(key)


def set_rows(numbers: dict, interchange_of_record: dict, aliases: dict) -> list:
    """Per (task, set): the three schemes side by side and the R-A1 reading.

    numbers: {(task, set, scheme): cell_numbers(...)} for the 1A cells that ran.
    interchange_of_record: {(task, set): {"ko_accuracy", "np_ko_rate_task_bank", "source", ...}} from ticket 06;
        a 1A interchange cell (set 6) takes precedence.
    aliases: {(task, set): twin_set} for sets dropped because they equal another (R21: ser's set 6 = set 5).

    R-A1 (sets 3-6 only): D-test KO accuracy under mean with the no-pressure KO deceptive rate under ZERO (R13).
    The same bands applied to the mean no-pressure column (task bank, matched bank) are robustness, not readings.
    """
    keys = {(t, s) for (t, s, _) in numbers} | set(aliases)
    rows = []
    for t, s in sorted(keys, key=lambda k: (TASK_ORDER.index(k[0]) if k[0] in TASK_ORDER else 99, k[0], k[1])):
        src = aliases.get((t, s), s)
        mean, zero = numbers.get((t, src, "mean")), numbers.get((t, src, "zero"))
        ic_1a = numbers.get((t, src, "interchange"))
        ic = ic_1a or interchange_of_record.get((t, src))
        d_mean, np_zero = _get(mean, "ko_accuracy"), _get(zero, "np_ko_rate_task_bank")
        decides = s in RA1_SETS
        rows.append({
            "task": t, "set": s, "set_name": SET_NAMES.get(s), "same_as_set": src if src != s else None,
            "calibration": not decides,
            "d_test_ko_acc": {"mean": d_mean, "zero": _get(zero, "ko_accuracy"), "interchange": _get(ic, "ko_accuracy")},
            "np_ko_rate": {"mean_task_bank": _get(mean, "np_ko_rate_task_bank"),
                           "mean_matched_bank": _get(mean, "np_ko_rate_matched_bank"),
                           "zero": np_zero, "interchange": _get(ic, "np_ko_rate_task_bank")},
            "ra1": ra1_reading(d_mean, np_zero) if decides else None,
            "ra1_robustness": ({"mean_task_bank": ra1_reading(d_mean, _get(mean, "np_ko_rate_task_bank")),
                                "mean_matched_bank": ra1_reading(d_mean, _get(mean, "np_ko_rate_matched_bank"))}
                               if decides else None),
            "interchange_source": ("phase 1A" if ic_1a else _get(ic, "source")),
            "cells": {"mean": mean, "zero": zero, "interchange": ic},
        })
    return rows


# ------------------------------------------------------------------ job timings

_CHAIN = re.compile(r"^=== evaluate_chain: group (\d+) of (\d+) (starts|exited (-?\d+)) (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)")


def chain_timings(text: str) -> list:
    """Per group of an evaluate_chain log: minutes from start to exit and the exit status (None if no exit line)."""
    starts, ends, total = {}, {}, {}
    for line in text.splitlines():
        m = _CHAIN.match(line)
        if not m:
            continue
        g, n = int(m.group(1)), int(m.group(2))
        total[g] = n
        ts = datetime.datetime.strptime(m.group(5), "%Y-%m-%d %H:%M:%S")
        if m.group(3) == "starts":
            starts[g] = ts
        else:
            ends[g] = (ts, int(m.group(4)))
    out = []
    for g in sorted(starts):
        end = ends.get(g)
        out.append({"group": g, "of": total[g],
                    "minutes": round((end[0] - starts[g]).total_seconds() / 60, 2) if end else None,
                    "exit": end[1] if end else None})
    return out


# ------------------------------------------------------------------ inputs

def _load(path):
    with open(path) as f:
        return json.load(f)


def suite_cells(suite: dict) -> list:
    """The 1A cells with their result dirs (repo-relative)."""
    out = []
    for job in mc.jobs_for(mc.select(suite["cells"], "1a")):
        for g in job["groups"]:
            for c in g["cells"]:
                out.append({**c, "job": job["job"], "group_name": g["group"],
                            "result_dir": g["results"][c["label"]]})
    return out


def collect_numbers(cells: list, root: str = mc.REPO) -> tuple:
    """({(task, set, scheme): numbers}, [missing result dirs])."""
    numbers, missing = {}, []
    for c in cells:
        path = os.path.join(root, c["result_dir"], "knockout.json")
        if not os.path.isfile(path):
            missing.append(c["result_dir"])
            continue
        n = cell_numbers(_load(path))
        n.update({"label": c["label"], "heads": c.get("expected_heads"), "result_dir": c["result_dir"],
                  "job": c["job"], "group": c["group_name"]})
        numbers[(c["home"], c["set"], c["scheme"])] = n
    return numbers, missing


def aliases_of(suite: dict) -> dict:
    """{(task, 6): 5} from suite_ma.json `dropped_cells` (R21's identity)."""
    out = {}
    for d in (suite.get("dropped_cells") or {}).get("cells", []):
        if "set_5" in (d.get("identity") or {}):
            out[(d["home"], d["set"])] = 5
    return out


def interchange_of_record(cells: list, paths=TICKET06_RESULTS) -> dict:
    """{(task, set): numbers} from ticket 06's knockout cells: same label, on D's own test set (`<t>_v2`)."""
    t06 = []
    for p in paths:
        for r in _load(p)["cells"]:
            if r.get("kind") == "knockout" and r.get("present"):
                t06.append((p, r))
    out = {}
    for c in cells:
        if c["scheme"] != "mean":            # mean covers every set that ran; one lookup per (task, set)
            continue
        for p, r in t06:
            if r["label"] == c["label"] and r["dataset"] == f"{c['home']}_v2":
                v = r.get("variants") or {}
                out[(c["home"], c["set"])] = {
                    "ko_accuracy": r["knockout"]["accuracy"], "separated": r["separated"],
                    "null_mean_accuracy": r["null_mean"]["accuracy"], "flipped_honest": r["flipped_honest"],
                    "n": r["n"], "np_ko_rate_task_bank": v.get("no_pressure.knockout_accuracy"),
                    "hi_ko_rate_task_bank": v.get("honest_instruction.knockout_accuracy"),
                    "wikitext_kl_per_token": r["wikitext"]["kl_per_token"],
                    "source": f"ticket 06 ({os.path.basename(p)}): {r['result_dir']}"}
                break
    return out


def flip_verdicts(flip_dir: str) -> dict:
    """{(group, label): positional summary} from flip_audit_analysis.py outputs `<flip_dir>/<group>.json`."""
    out = {}
    if not os.path.isdir(flip_dir):
        return out
    for name in sorted(os.listdir(flip_dir)):
        if not name.endswith(".json"):
            continue
        group = name[:-5]
        for c in _load(os.path.join(flip_dir, name)).get("cells", []):
            pos, head = c.get("positional") or {}, c.get("headline") or {}
            label = c["circuit"][:-len("__leaf")] if c["circuit"].endswith("__leaf") else c["circuit"]
            out[(group, label)] = {
                "verdict": pos.get("verdict"), "p_ko_item_2": pos.get("p_ko_item_2"),
                "p_target_item_2": pos.get("p_target_item_2"), "binom_p": pos.get("binom_p_vs_base"),
                "stay_gap": pos.get("stay_gap_2_minus_1"), "p_ko_neither": pos.get("p_ko_neither"),
                "stay_rate": head.get("stay_rate"), "separable": head.get("separable"),
                "rows_aligned": c.get("rows_aligned"), "source": os.path.join(flip_dir, name)}
    return out


def flip_rows(numbers: dict, verdicts: dict) -> list:
    rows = []
    for (t, s, scheme), n in sorted(numbers.items(), key=lambda kv: (TASK_ORDER.index(kv[0][0]), kv[0][1], kv[0][2])):
        if scheme not in ("mean", "zero"):
            continue
        acc = n["ko_accuracy"]
        required = AUDIT_BAND[0] - EPS <= acc <= AUDIT_BAND[1] + EPS
        v = verdicts.get((n["group"], n["label"]))
        rows.append({"task": t, "set": s, "scheme": scheme, "label": n["label"], "ko_accuracy": acc,
                     "audit_required": required, **({"audit": v} if v else {"audit": None})})
    return rows


def timings(job_ids: dict, logs_dir: str) -> dict:
    out = {}
    for job, jid in job_ids.items():
        path = os.path.join(logs_dir, f"evaluate_chain_{jid}.out")
        out[job] = {"job_id": jid, "log": path,
                    "groups": chain_timings(open(path, errors="replace").read()) if os.path.isfile(path) else None}
    return out


# ------------------------------------------------------------------ outputs

def _f(x, nd=3):
    if x is None:
        return "-"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def markdown(cell_list, numbers, srows, frows, tim, missing, reading="", sacct="") -> str:
    L = ["# Ticket 03 phase-1A results: mean / zero / interchange circuit knockouts (Bridges-2 H100)", "",
         "Generated by `outputs/_launch_mechanism_analysis/p1a_results.py` from the fetched cells under "
         "`outputs/_suites/mechanism-analysis/phase1a/` and ticket 06's interchange cells of record "
         "(mechanism-datasets `reports/06-stage1-results.json`, `06-stage2-results.json`). Heads-only `(E) - m` "
         "knockouts at leaf on D_t's own test set (`<t>_v2`, 1,000 items), 20 random head sets of the same size "
         "per null. Accuracy counts the DECEPTIVE item, on D's test set and on both prompt variants (labels "
         "unchanged), so a variant's KO accuracy is its KO deceptive rate; the full model's no-pressure rate is "
         "about 0.", ""]
    if missing:
        L += [f"**Missing cells ({len(missing)}):** " + ", ".join(f"`{m}`" for m in missing), ""]
    if reading:
        L += [reading.rstrip(), ""]

    L += ["## R-A1 per set and task", "",
          "Pre-registered (spec 2.5, R13): D-test KO accuracy under MEAN, no-pressure KO deceptive rate under "
          "ZERO. answer machinery: 0.25-0.75 and >= 0.25; deception-specific: <= 0.25 and <= 0.10; item carrier: "
          "<= 0.25 and >= 0.75; partial or none otherwise. Sets 1, 2 and 7 are calibration rows (no reading). "
          "The two robustness columns apply the same bands with the MEAN no-pressure column (task bank; "
          "variant-matched bank) in place of zero's; they never decide. Interchange: set 6 from 1A (far, sdr), "
          "the rest from ticket 06. ser's set 6 equals its set 5 (R21) and repeats it.", "",
          "| task | set | D-test KO acc: mean | zero | interchange | np KO dec. rate: mean, task bank "
          "| mean, np bank | zero | interchange | R-A1 | robustness (mean task bank / mean np bank) |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in srows:
        d, z = r["d_test_ko_acc"], r["np_ko_rate"]
        name = f"{r['set']} {r['set_name']}" + (f" (= set {r['same_as_set']})" if r["same_as_set"] else "")
        rob = r["ra1_robustness"]
        L.append(f"| {r['task']} | {name} | {_f(d['mean'])} | {_f(d['zero'])} | {_f(d['interchange'])} "
                 f"| {_f(z['mean_task_bank'])} | {_f(z['mean_matched_bank'])} | {_f(z['zero'])} "
                 f"| {_f(z['interchange'])} | {r['ra1'] or 'calibration'} "
                 f"| {(rob['mean_task_bank'] + ' / ' + rob['mean_matched_bank']) if rob and rob['mean_task_bank'] and rob['mean_matched_bank'] else '-'} |")
    L.append("")

    L += ["## Per cell", "",
          "Separated = metrics (of 4: accuracy, logit diff, KL, exact match) with percentile <= 5 and z <= -2 "
          "against the 20-set KO null (ticket 06's rule). np = no_pressure, hi = honest_instruction; both KO "
          "deceptive rates under the task bank, np also under its own bank on mean rows. Wikitext KL per token "
          "with its random-KO null mean.", "",
          "| task | set | scheme | cell | heads | KO acc | flipped / n | null mean acc | separated | np KO rate "
          "(task bank) | np KO rate (np bank) | hi KO rate | wikitext KL/tok (null mean) |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    order = {"mean": 0, "zero": 1, "interchange": 2}
    for (t, s, scheme), n in sorted(numbers.items(), key=lambda kv: (TASK_ORDER.index(kv[0][0]), order[kv[0][2]], kv[0][1])):
        L.append(f"| {t} | {s} | {scheme} | `{n['label']}` | {_f(n['heads'])} | {_f(n['ko_accuracy'])} "
                 f"| {_f(n['flipped_honest'])} / {_f(n['n'])} | {_f(n['null_mean_accuracy'])} | {n['separated']} "
                 f"| {_f(n['np_ko_rate_task_bank'])} | {_f(n['np_ko_rate_matched_bank'])} "
                 f"| {_f(n['hi_ko_rate_task_bank'])} | {_f(n['wikitext_kl_per_token'])} "
                 f"({_f(n['wikitext_null_mean_kl'])}) |")
    L.append("")

    L += ["## Flip audit: positional default", "",
          "`flip_audit_analysis.py` (R16) on every mean and zero group. Required (spec 2.5) where the D-test KO "
          "accuracy is in 0.25-0.75; run on every cell. Verdict 'positional default' when |P(KO item_2) - base| "
          ">= 0.15, binomial p < 0.01 and the stay-rate gap between target positions >= 0.3.", "",
          "| task | set | scheme | cell | KO acc | required | verdict | P(KO item_2) | base | binom p | stay gap "
          "| KO neither |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in frows:
        a = r["audit"] or {}
        L.append(f"| {r['task']} | {r['set']} | {r['scheme']} | `{r['label']}` | {_f(r['ko_accuracy'])} "
                 f"| {_f(r['audit_required'])} | {a.get('verdict') or 'not run'} | {_f(a.get('p_ko_item_2'))} "
                 f"| {_f(a.get('p_target_item_2'))} | {_f(a.get('binom_p'), 4)} | {_f(a.get('stay_gap'))} "
                 f"| {_f(a.get('p_ko_neither'))} |")
    L.append("")

    if tim:
        L += ["## Job timings (calibration)", "",
              "From the fetched chain logs (`=== evaluate_chain` stamps). Groups run mean, zero, interchange.", "",
              "| job | Slurm id | group | minutes | exit |", "| --- | --- | --- | --- | --- |"]
        for job, t in tim.items():
            for g in t["groups"] or []:
                L.append(f"| {job} | {t['job_id']} | {g['group']} of {g['of']} | {_f(g['minutes'], 1)} "
                         f"| {_f(g['exit'])} |")
        L.append("")
    if sacct:
        L += ["## Bridges-2 sacct", "", "```", sacct.rstrip(), "```", ""]
    return "\n".join(L)


def write_csvs(curated, numbers, srows):
    os.makedirs(curated, exist_ok=True)
    cols = ["task", "set", "scheme", "label", "heads", "ko_accuracy", "flipped_honest", "n", "null_mean_accuracy",
            "separated", "np_full_rate", "np_ko_rate_task_bank", "np_ko_rate_matched_bank", "hi_ko_rate_task_bank",
            "wikitext_kl_per_token", "wikitext_null_mean_kl", "result_dir"]
    with open(os.path.join(curated, "p1a_cells.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for (t, s, scheme), n in sorted(numbers.items(), key=lambda kv: (TASK_ORDER.index(kv[0][0]), kv[0][1], kv[0][2])):
            w.writerow([t, s, scheme] + [n.get(c) for c in cols[3:]])
    scols = ["task", "set", "set_name", "same_as_set", "d_test_mean", "d_test_zero", "d_test_interchange",
             "np_mean_task_bank", "np_mean_matched_bank", "np_zero", "np_interchange", "ra1",
             "robust_mean_task_bank", "robust_mean_matched_bank", "interchange_source"]
    with open(os.path.join(curated, "p1a_sets.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(scols)
        for r in srows:
            d, z, rob = r["d_test_ko_acc"], r["np_ko_rate"], r["ra1_robustness"] or {}
            w.writerow([r["task"], r["set"], r["set_name"], r["same_as_set"], d["mean"], d["zero"],
                        d["interchange"], z["mean_task_bank"], z["mean_matched_bank"], z["zero"], z["interchange"],
                        r["ra1"], rob.get("mean_task_bank"), rob.get("mean_matched_bank"), r["interchange_source"]])


def _key(k):
    return "/".join(str(x) for x in k)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--flip-audit-dir", default=FLIP_DIR)
    p.add_argument("--logs-dir", default=LOGS_DIR)
    p.add_argument("--job-ids", nargs="*", default=[], metavar="JOB=ID", help="e.g. p1a_far=49824695")
    p.add_argument("--sacct", default=None, help="a saved `b2.sh status` output to quote")
    p.add_argument("--reading", default=None, help="markdown inserted under the title (the hand-written reading)")
    p.add_argument("--reports", default=REPORTS)
    p.add_argument("--curated", default=CURATED)
    a = p.parse_args(argv)

    suite = _load(mc.SUITE_JSON)
    cells = suite_cells(suite)
    numbers, missing = collect_numbers(cells)
    ic = interchange_of_record(cells)
    srows = set_rows(numbers, ic, aliases_of(suite))
    frows = flip_rows(numbers, flip_verdicts(a.flip_audit_dir))
    tim = timings(dict(x.split("=", 1) for x in a.job_ids), a.logs_dir) if a.job_ids else {}
    reading = open(a.reading).read() if a.reading else ""
    sacct = open(a.sacct).read() if a.sacct else ""

    payload = {"generated_by": f"{mc.LAUNCH_DIR}/p1a_results.py", "spec": "spec.md 2.5, 4; R13, R19(2), R21",
               "n_cells_expected": len(cells), "n_cells_found": len(numbers), "missing": missing,
               "cells": {_key(k): v for k, v in numbers.items()}, "sets": srows, "flip_audit": frows,
               "interchange_of_record": {_key(k): v for k, v in ic.items()}, "timings": tim}
    os.makedirs(a.reports, exist_ok=True)
    with open(os.path.join(a.reports, "03-1a-results.json"), "w") as f:
        json.dump(payload, f, indent=1, sort_keys=False)
    with open(os.path.join(a.reports, "03-1a-results.md"), "w") as f:
        f.write(markdown(cells, numbers, srows, frows, tim, missing, reading, sacct))
    write_csvs(a.curated, numbers, srows)
    readings = {f"{r['task']}/set{r['set']}": {"set_name": r["set_name"], "ra1": r["ra1"],
                                               "robustness": r["ra1_robustness"], "same_as_set": r["same_as_set"]}
                for r in srows}
    with open(os.path.join(a.curated, "p1a_readings.json"), "w") as f:
        json.dump({"rule": "R-A1 (spec 2.5, R13): mean D-test KO acc x zero no-pressure KO deceptive rate",
                   "readings": readings, "flip_audit": frows}, f, indent=1)
    print(f"{len(numbers)} of {len(cells)} cells; missing {len(missing)}; wrote {a.reports}/03-1a-results.{{md,json}} "
          f"and {a.curated}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
