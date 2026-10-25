#!/usr/bin/env python3
"""
ma_build_suite.py -- write suite_ma.json, the definition of the mechanism-analysis evaluator suite (ticket 01).

The cells come from ma_cells.plan_cells (expression, operands, test set, scheme, set number, expected head
count). Per stage: the chained jobs, each with its scheme groups (output dir, suite name, per-cell result dirs)
and the cost estimate per GPU class. A test fails when the file is stale.

usage (from the repository root):
    python outputs/_launch_mechanism_analysis/ma_build_suite.py
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ma_cells as mc  # noqa: E402

GPUS = ("A40", "H200", "H100")


def stage_block(cells, stage: str) -> dict:
    jobs = mc.jobs_for(mc.select(cells, stage))
    out = []
    for job in jobs:
        out.append({"job": job["job"], "cells": len(job["cells"]),
                    "groups": [{"group": g["group"], "scheme": g["scheme"], "output_dir": g["output_dir"],
                                "suite_name": g["suite_name"], "task_from": g["task_from"],
                                "cells": [c["label"] for c in g["cells"]], "results": g["results"]}
                               for g in job["groups"]],
                    "est_min": {g: round(mc.job_minutes(job, g), 1) for g in GPUS},
                    "walltime": {g: mc.walltime(mc.job_minutes(job, g)) for g in GPUS}})
    return {"note": mc.STAGE_NOTES[stage], "n_cells": len(mc.select(cells, stage)), "jobs": out}


def build() -> dict:
    cells = mc.plan_cells()
    return {
        "schema": 1,
        "suite": "mechanism-analysis",
        "ticket": "03-phase1-ablation-replication-and-sweeps",
        "built_by": "01-infra-bridges2-and-ablation-launcher",
        "spec": "spec.md section 4 (phase 1A), section 2.5 (R-A1), R13",
        "generated_by": f"{mc.LAUNCH_DIR}/ma_build_suite.py",
        "paths": "every path is relative to the repository root (DC_REPO_ROOT)",
        "runs": mc.RUNS,
        "operands": {"m": mc.ALLMLP},
        "suite_root": mc.SUITE_ROOT,
        "compose_granularity": mc.GRANULARITY,
        "chain_script": mc.CHAIN_SCRIPT,
        "scheme_args": mc.SCHEME_ARGS,
        "null_args": mc.NULL_ARGS,
        "scheme_sets": {k: list(v) for k, v in mc.SCHEME_SETS.items()},
        "cost_model": {"a40_ko_cell_min": mc.A40_KO_MIN, "speedup_vs_a40": mc.SPEEDUP,
                       "cold_load_min": mc.LOAD_MIN, "warm_load_min": mc.WARM_LOAD_MIN,
                       "a40_pass_min": mc.A40_PASS_MIN, "a40_bank_min": mc.A40_BANK_MIN,
                       "mean_banks_per_group": mc.MEAN_BANKS_PER_GROUP,
                       "a40_matched_run_min_per_mean_cell": mc.A40_MATCHED_RUN_MIN,
                       "walltime_factor": mc.WALLTIME_FACTOR, "walltime_floor_min": mc.WALLTIME_FLOOR_MIN,
                       "note": "KO cell rate, speed-ups and the H100 cold (10.5) and warm (0.4) loads are ticket "
                               "06's measurements; the pass, bank and matched-run costs are derived, not "
                               "measured"},
        "dropped_cells": {"ruling": "R21 (spec section 9): set 6 = (D_t - H_t) - core equals set 5 = D_t - H_t "
                                    "when D_t - H_t holds no core head, so its cells repeat set 5's (mean, zero) "
                                    "or ticket 06's interchange cell of record; they are dropped",
                          "cells": mc.dropped_cells()},
        "stages": {s: stage_block(cells, s) for s in mc.STAGE_DIR},
        "cells": cells,
    }


def main(argv=None):
    suite = build()
    with open(mc.SUITE_JSON, "w") as f:
        json.dump(suite, f, indent=1)
        f.write("\n")
    for s, b in suite["stages"].items():
        print(f"stage {s}: {b['n_cells']} cells, {len(b['jobs'])} chained jobs")
    print(mc.SUITE_JSON)


if __name__ == "__main__":
    main()
