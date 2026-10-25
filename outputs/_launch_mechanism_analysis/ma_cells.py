"""
ma_cells.py -- the evaluator cells of the mechanism-analysis feature, as data (ticket 01; run by ticket 03).

Phase 1A (spec section 4; rule R-A1, spec section 2.5). Per task t, heads-only knockout cells `(E) - m` at leaf on
D_t's own test set (`<t>_v2`), `--evals knockout`, 20 random circuits through both nulls, over the seven sets E
of RQ-A:

    1 D_t        2 H_t        3 core = D_far & D_sdr & D_ser        4 excl_t = D_t - D_u - D_v
    5 D_t - H_t  6 (D_t - H_t) - core                                7 D_t & H_t

under three ablation schemes:

    mean         sets 1-7. Task rows: the bank over D's test split. no_pressure variant rows: twice, under the
                 task bank and under the variant-matched bank (`--variant-mean-bank no_pressure`, R13, R19(2)),
                 which equals the bank over `<t>_v2_nopressure`'s test split
    zero         sets 3-6 (R-A1 decides the no-pressure column here)
    interchange  set 6 (the new set; sets 1-5 and 7 have ticket 06's interchange cells)

The spec lists 36 cells. R21 drops set 6 wherever it equals set 5 (D_t - H_t holds no core head): that is ser, so
33 cells; `dropped_cells` records the identity and, for interchange, ticket 06's cell of record. Labels of sets 1-5
and 7 are ticket 06's, so a phase-1A cell and its interchange cell of record share a name. One job per task chains
its schemes: a scheme is one evaluate_circuit.py process (one --ablation per process) with its own output dir and
suite name, and scripts/evaluate_chain.sbatch runs them in a row, so a job pays one cold model load and warm ones
after it.

The circuits, the all-MLP operand `m` and the measured cost rates are ticket 06's
(outputs/_launch_mechanism_v2/evals/mv2_cells.py), imported and never edited. All paths are relative to the
repository root (DC_REPO_ROOT). `plan_cells` reads only the operands' head masks; the rest are pure functions.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
LAUNCH_DIR = "outputs/_launch_mechanism_analysis"
SUITE_JSON = os.path.join(HERE, "suite_ma.json")


def _load_module(name: str, relpath: str):
    """A module of ticket 06's launcher (outputs/_launch_mechanism_v2/evals/), loaded once under `name`.

    Its own names (`gen_cells`, `check_cells`) are taken by the old launcher's tests, hence the explicit name.
    """
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V2_LAUNCH = "outputs/_launch_mechanism_v2/evals"
#: Ticket 06's plan module: the circuits of record, the `m` operand, the measured cost rates.
mv2 = _load_module("mv2_cells", f"{V2_LAUNCH}/mv2_cells.py")
TASKS = mv2.TASKS
RUNS = mv2.RUNS
ALLMLP = mv2.ALLMLP
live_heads = mv2.live_heads
GRANULARITY = "leaf"

SUITE_ROOT = "outputs/_suites/mechanism-analysis"
STAGE_DIR = {"1a": "phase1a"}
STAGE_NOTES = {
    "1a": "phase 1A (spec section 4, R21): 33 knockout cells (ser's set 6 equals its set 5 and is dropped), one "
          "job per task chaining mean, zero and interchange; ticket 03 submits it once ticket 01 has landed and "
          "the branch is pushed and synced (R3)",
}
#: The separator scripts/evaluate_chain.sbatch splits its arguments on.
CHAIN_SEP = ":::"
CHAIN_SCRIPT = "scripts/evaluate_chain.sbatch"

KO_EVALS = ["knockout"]
#: 20 random circuits, all 20 through the knockout null (ticket 06's argv).
NULL_ARGS = ["--n-random", "20", "--knockout-null-count", "20"]
#: Chain order inside a job. Each scheme is its own process, so nothing (no bank) carries over between them; mean
#: runs first only so the longest group starts right after the cold load.
SCHEMES = ("mean", "zero", "interchange")
SCHEME_ARGS = {
    "mean": ["--ablation", "mean", "--variant-mean-bank", "no_pressure"],
    "zero": ["--ablation", "zero"],
    "interchange": ["--ablation", "interchange"],
}
#: Which of the seven sets each scheme runs (spec section 4, phase 1A).
SCHEME_SETS = {"mean": (1, 2, 3, 4, 5, 6, 7), "zero": (3, 4, 5, 6), "interchange": (6,)}

# ------------------------------------------------------------------ cost model
#: Knockout cell, A40 minutes, and the GPU speed-ups and cold loads: ticket 06's measured rates (mv2_cells).
A40_KO_MIN = mv2.A40_CELL_MIN["knockout"]
SPEEDUP = mv2.SPEEDUP
LOAD_MIN = mv2.LOAD_MIN
#: Start-up of the 2nd and 3rd process of a chain job, from the node's warm page cache. H100: 0.4 min, measured
#: (49774563, the same node right after 49774554). Not measured on other GPUs, where the cold value is used.
WARM_LOAD_MIN = {"H100": 0.4}
#: One pass over the test set (or wikitext), A40 minutes. Not measured: derived from the KO cell (26 A40-min for
#: about 40 passes), so about 0.65.
A40_PASS_MIN = 0.65
#: One mean bank (two passes), A40 minutes, rounded up to 2.0. A mean group builds three, once per process: the
#: task bank, the no_pressure variant bank and the wikitext bank.
A40_BANK_MIN = 2.0
MEAN_BANKS_PER_GROUP = 3
#: The no_pressure rows again under their own bank, per mean cell (R19(2)): three configurations with a live
#: reference pass each, six passes, 3.9 A40-min, rounded up to 4.0. Derived, not measured.
A40_MATCHED_RUN_MIN = 4.0
#: Walltime = estimate x 1.5, rounded up to a quarter hour (agent-brief), at least the floor.
WALLTIME_FACTOR, WALLTIME_FLOOR_MIN = 1.5, 30


def group_minutes(group, gpu: str, first: bool) -> float:
    """Estimated minutes of one scheme group (one evaluate_circuit.py process) on one GPU of class `gpu`."""
    load = LOAD_MIN[gpu] if first else WARM_LOAD_MIN.get(gpu, LOAD_MIN[gpu])
    per_cell = A40_KO_MIN
    banks = 0.0
    if group["scheme"] == "mean":
        per_cell += A40_MATCHED_RUN_MIN
        banks = MEAN_BANKS_PER_GROUP * A40_BANK_MIN
    return load + (len(group["cells"]) * per_cell + banks) / SPEEDUP[gpu]


def job_minutes(job, gpu: str) -> float:
    """Estimated elapsed minutes of one chained job: one cold load, the later groups warm."""
    return sum(group_minutes(g, gpu, i == 0) for i, g in enumerate(job["groups"]))


def walltime(minutes: float, floor_min: int = WALLTIME_FLOOR_MIN) -> str:
    m = max(floor_min, int(math.ceil(round(minutes * WALLTIME_FACTOR, 6) / 15.0)) * 15)
    return f"{m // 60:02d}:{m % 60:02d}:00"


walltime_hours = mv2.walltime_hours


# ------------------------------------------------------------------ the plan

def _sets(t: str, S: dict) -> dict:
    """{set number: (label, expression, head set, operand names)} for task t (labels as in ticket 06)."""
    others = [u for u in TASKS if u != t]
    D, H = f"D_{t}", f"H_{t}"
    Ds = [f"D_{u}" for u in TASKS]
    core_expr = " & ".join(Ds)
    core = S[Ds[0]] & S[Ds[1]] & S[Ds[2]]
    return {
        1: (D, D, S[D], (D,)),
        2: (H, H, S[H], (H,)),
        3: ("D_core", core_expr, core, tuple(Ds)),
        4: (f"{D}_minus_" + "_minus_".join(f"D_{u}" for u in others),
            f"{D} - " + " - ".join(f"D_{u}" for u in others),
            S[D] - S[f"D_{others[0]}"] - S[f"D_{others[1]}"], (D, *(f"D_{u}" for u in others))),
        5: (f"{D}_minus_{H}", f"{D} - {H}", S[D] - S[H], (D, H)),
        6: (f"{D}_minus_{H}_minus_D_core", f"({D} - {H}) - ({core_expr})", (S[D] - S[H]) - core,
            (D, H, *Ds)),
        7: (f"{D}_and_{H}", f"{D} & {H}", S[D] & S[H], (D, H)),
    }


def _head_sets(repo: str) -> dict:
    names = {f"{r}_{t}": RUNS[t][r] for t in TASKS for r in ("D", "H")}
    return {n: live_heads(p, repo) for n, p in names.items()}


def _set6_is_set5(sets: dict) -> bool:
    """R21: set 6 is set 5 when D_t - H_t holds no core head; its cells would repeat set 5's."""
    return sets[6][2] == sets[5][2]


#: Where ticket 06 wrote a task's own-test-set interchange cell for a set-5 label (stage 1, D knockouts).
V2_INTERCHANGE_CELL = "outputs/_suites/mechanism-v2-coarse/stage1/s1_{t}__D_ko/cells/{label}__leaf/{t}_v2/interchange"


def dropped_cells(repo: str = REPO) -> list:
    """The spec's set-6 cells R21 drops, with the identity that makes them repeats and the cell of record."""
    S = _head_sets(repo)
    out = []
    for t in TASKS:
        sets = _sets(t, S)
        if not _set6_is_set5(sets):
            continue
        core = sets[3][2]
        for scheme in SCHEMES:
            if 6 not in SCHEME_SETS[scheme]:
                continue
            record = None
            if scheme == "interchange":
                record = V2_INTERCHANGE_CELL.format(t=t, label=f"{sets[5][0]}_hko")
            out.append({"home": t, "scheme": scheme, "set": 6, "label": f"{sets[6][0]}_hko",
                        "identity": {"set_5": sets[5][1], "set_6": sets[6][1], "heads_set_5": len(sets[5][2]),
                                     "heads_set_6": len(sets[6][2]), "core_heads_in_set_5": len(sets[5][2] & core)},
                        "repeats": f"p1a_{t}__{scheme}/{sets[5][0]}_hko" if scheme != "interchange" else None,
                        "cell_of_record": record})
    return out


def plan_cells(repo: str = REPO) -> list:
    """Every cell of the suite, in submission order."""
    names = {f"{r}_{t}": RUNS[t][r] for t in TASKS for r in ("D", "H")}
    S = _head_sets(repo)
    table = dict(names, m=ALLMLP)
    cells = []
    for t in TASKS:
        sets = _sets(t, S)
        for scheme in SCHEMES:
            for n in SCHEME_SETS[scheme]:
                if n == 6 and _set6_is_set5(sets):
                    continue
                base, expr, heads, used = sets[n]
                label = f"{base}_hko"
                group = f"p1a_{t}__{scheme}"
                cells.append({
                    "stage": "1a", "job": f"p1a_{t}", "group": group, "scheme": scheme, "set": n,
                    "cell_id": f"{group}/{label}", "label": label, "expr": f"({expr}) - m",
                    "kind": "knockout", "cell_dir": f"{label}__{GRANULARITY}", "home": t,
                    "test_task": f"{t}_v2", "condition": "deceptive", "dataset": f"{t}_v2",
                    "task_from": RUNS[t]["D"], "evals": list(KO_EVALS),
                    "operands": {k: table[k] for k in (*dict.fromkeys(used), "m")},
                    "common_args": [*SCHEME_ARGS[scheme], *NULL_ARGS],
                    "expected_heads": len(heads)})
    return cells


# ------------------------------------------------------------------ jobs

def select(cells, stage: str) -> list:
    if stage not in STAGE_DIR:
        raise ValueError(f"unknown stage {stage!r}; choose from {', '.join(STAGE_DIR)}")
    return [c for c in cells if c["stage"] == stage]


_bind_rank = mv2._bind_rank


def _group(key: str, members: list) -> dict:
    first = members[0]
    for field in ("stage", "job", "scheme", "task_from", "evals", "test_task", "condition", "common_args"):
        values = {json.dumps(m[field]) for m in members}
        if len(values) > 1:
            raise ValueError(f"group {key}: cells disagree on {field}: {sorted(values)}")
    binds = {}
    for m in members:
        for name, path in m["operands"].items():
            if binds.setdefault(name, path) != path:
                raise ValueError(f"group {key}: operand {name} bound to two paths")
    labels = [m["label"] for m in members]
    if len(set(labels)) != len(labels):
        raise ValueError(f"group {key}: duplicate cell labels {labels}")
    out = f"{SUITE_ROOT}/{STAGE_DIR[first['stage']]}/{key}"
    return {"group": key, "scheme": first["scheme"], "suite_name": key,
            "binds": dict(sorted(binds.items(), key=lambda kv: _bind_rank(kv[0]))),
            "exprs": [[m["label"], m["expr"]] for m in members],
            "task_from": first["task_from"], "evals": list(first["evals"]),
            "common_args": list(first["common_args"]), "output_dir": out, "cells": members,
            "results": {m["label"]: f"{out}/cells/{m['cell_dir']}/{first['test_task']}/{first['scheme']}"
                        for m in members}}


def jobs_for(cells) -> list:
    """Group cells into scheme groups (one evaluate_circuit.py process each) and groups into jobs (one Slurm
    job each, chained by scripts/evaluate_chain.sbatch), both in plan order."""
    jobs, by_job = [], {}
    for c in cells:
        job = by_job.get(c["job"])
        if job is None:
            job = by_job[c["job"]] = {"job": c["job"], "stage": c["stage"], "_groups": {}}
            jobs.append(job)
        job["_groups"].setdefault(c["group"], []).append(c)
    for job in jobs:
        job["groups"] = [_group(k, v) for k, v in job.pop("_groups").items()]
        job["cells"] = [c for g in job["groups"] for c in g["cells"]]
    return jobs


def group_args(group) -> list:
    """The exact evaluate_circuit.py arguments of one scheme group (paths relative to the repo root)."""
    args = []
    for name, path in group["binds"].items():
        args += ["--circuit", f"{name}={path}"]
    for label, expr in group["exprs"]:
        args += ["--expr", f"{label}={expr}"]
    args += ["--compose-granularity", GRANULARITY, "--task-from", group["task_from"],
             "--evals", *group["evals"], *group["common_args"],
             "--suite-name", group["suite_name"], "--output-dir", group["output_dir"]]
    return args


def chain_args(job) -> list:
    """scripts/evaluate_chain.sbatch's arguments: the groups' arguments joined by ':::'."""
    out = []
    for i, group in enumerate(job["groups"]):
        if i:
            out.append(CHAIN_SEP)
        out += group_args(group)
    return out


def load_suite(path: str = SUITE_JSON) -> dict:
    with open(path) as f:
        return json.load(f)
