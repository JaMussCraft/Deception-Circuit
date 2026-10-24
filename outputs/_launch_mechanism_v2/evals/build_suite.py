#!/usr/bin/env python3
"""
build_suite.py -- write suite_v2.json, the definition of the v2 coarse evaluation suite (ticket 06).

The cells come from mv2_cells.plan_cells (every cell: expression, operands, test task / condition /
dataset, evals, block, conditional flag, expected head count). Per stage the packed jobs, with their
output and result directories and the cost estimate per GPU class. The drift-control block records the
Delta reference values of the cell it reproduces, copied from the main checkout's knockout.json files.

usage (from the repository root; needs build_operands.py to have run):
    python outputs/_launch_mechanism_v2/evals/build_suite.py [--main-checkout DIR]
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

MAIN_CHECKOUT = mc.MAIN_CHECKOUT
#: The Delta cells the drift control reproduces, one drift cell each (mv2_cells.DRIFT_CELLS). Both ran on
#: gpuA40x4 (sacct NodeList gpub029 / gpub049).
REFERENCES = (
    {"slurm_job": 22895982, "gpu": "A40", "role": "primary", "cell_job": "drift_sdr_coarse_D_hko",
     "why": "format-control coarse suite D_hko on sdr (--ablation interchange --knockout-null-count 20), "
            "the newer evaluator code; the yardstick for every row including the pressure variants",
     "path": "outputs/_suites/format-control-sdr-coarse-nls0.3/cells/D_hko__leaf/sdr/interchange/knockout.json"},
    {"slurm_job": 22316469, "gpu": "A40", "role": "secondary", "cell_job": "drift_sdr_coarse_D_headsko",
     "why": "the coarse SDR wave's heads-only KO cell (submit_headsko.sh argv, evaluations_headsko/); its "
            "pressure-variant rows predate an evaluator change and differ from the primary",
     "path": "outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742/"
             "evaluations_headsko/cells/headsko__leaf/sdr/interchange/knockout.json"},
)
STAGE_NOTES = {
    "control": "drift control (2 cells, one per Delta reference): run first on the remote cluster; stage 1 "
               "only after the orchestrator accepts the per-metric deltas",
    "1": "G14 stage 1 (24 cells); HARD STOP after it: results table to the orchestrator",
    "2": "G14 stage 2 (33 cells + 6 conditional); starts only after the user has seen stage 1",
}


def _created(knockout_path: str) -> str:
    with open(os.path.join(os.path.dirname(knockout_path), "summary.json")) as f:
        return json.load(f)["created"]


def drift_block(cells, main_checkout: str) -> dict:
    drift_cells = [c for c in cells if c["stage"] == "control"]
    jobs = {j["job"]: j for j in mc.jobs_for(drift_cells)}
    refs, metrics = [], []
    for ref in REFERENCES:
        path = os.path.join(main_checkout, ref["path"])
        with open(path) as f:
            m = drift.metrics_of(json.load(f))
        metrics.append(m)
        job = jobs[ref["cell_job"]]
        refs.append(dict(ref, source_checkout=main_checkout, created=_created(path),
                         result=f"{next(iter(job['results'].values()))}/knockout.json", metrics=m))
    floor = {k: r["delta"] for k, r in drift.compare(metrics[0], metrics[1]).items()}
    return {
        "cells": drift_cells,
        "references": refs,
        "between_references": floor,
        "reading": "Both references ran on A40s three weeks apart: task and wikitext rows agree exactly, so "
                   "on one GPU type the cell is bit-stable. The pressure-variant rows differ (no_pressure "
                   "full accuracy 0.169 vs 0.228) because of an evaluator change between 2026-09-22 and "
                   "2026-10-15, not the GPU; compare variants with the primary only. A cross-GPU run is not "
                   "expected to be bit-exact (bf16 kernels differ by architecture). Acceptance is the "
                   "orchestrator's call; no threshold is pre-registered.",
    }


def stage_block(cells, stage: str) -> dict:
    conditional = stage == "2"
    jobs = mc.jobs_for(mc.select(cells, stage, include_conditional=conditional))
    out = []
    for job in jobs:
        out.append({"job": job["job"], "output_dir": job["output_dir"], "task_from": job["task_from"],
                    "evals": job["evals"], "cells": [c["label"] for c in job["cells"]],
                    "conditional_cells": [c["label"] for c in job["cells"] if c["conditional"]],
                    "results": job["results"],
                    "est_min": {g: round(mc.job_minutes(job, g), 1) for g in ("A40", "H100")}})
    return {"note": STAGE_NOTES[stage], "n_cells": len(mc.select(cells, stage)),
            "n_conditional": sum(c["conditional"] for c in cells if c["stage"] == stage),
            "jobs_packed": out}


def build(main_checkout: str = MAIN_CHECKOUT) -> dict:
    cells = mc.plan_cells()
    return {
        "schema": 1,
        "suite": "mechanism-v2-coarse",
        "ticket": "06-evaluate-coarse-v2-circuits",
        "spec": "spec.md 14.G14",
        "generated_by": "outputs/_launch_mechanism_v2/evals/build_suite.py",
        "paths": "every path is relative to the repository root (DC_REPO_ROOT)",
        "runs": mc.RUNS,
        "operands": {"m": mc.ALLMLP, "standins": mc.STANDINS, "drift_D": mc.DRIFT_D, "drift_m": mc.DRIFT_M},
        "suite_root": mc.SUITE_ROOT,
        "compose_granularity": mc.GRANULARITY,
        "common_args": mc.COMMON_ARGS,
        "operand_rule": "The evaluator takes every test set from --task-from (the run's config.json: task, "
                        "deception_condition, data_dir); an operand's config is never read for the task. Every "
                        "job passes exactly one --task-from (checked by check_cells.py), so the far_v2 config "
                        "of m never names a test set, on any task.",
        "cost_model": {"a40_cell_min": mc.A40_CELL_MIN, "speedup_vs_a40": mc.SPEEDUP,
                       "load_min": mc.LOAD_MIN, "walltime_factor": mc.WALLTIME_FACTOR,
                       "walltime_floor_min": mc.WALLTIME_FLOOR_MIN,
                       "h100_note": "H100 cell time is assumed (0.85 x H200), not measured; the drift-control "
                                    "jobs measure it. H100 model load 458 s from /ocean (smoke job 49773269)"},
        "stages": {s: stage_block(cells, s) for s in mc.STAGE_DIR},
        "drift_control": drift_block(cells, main_checkout),
        "cells": cells,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--main-checkout", default=MAIN_CHECKOUT)
    a = p.parse_args(argv)
    suite = build(a.main_checkout)
    with open(mc.SUITE_JSON, "w") as f:
        json.dump(suite, f, indent=1)
        f.write("\n")
    for s, b in suite["stages"].items():
        print(f"stage {s}: {b['n_cells']} cells (+{b['n_conditional']} conditional), "
              f"{len(b['jobs_packed'])} packed jobs")
    print(mc.SUITE_JSON)


if __name__ == "__main__":
    main()
