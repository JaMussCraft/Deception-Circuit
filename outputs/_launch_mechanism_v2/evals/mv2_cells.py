"""
mv2_cells.py -- the cells of the v2 coarse evaluation suite (ticket 06, spec 14.G14), as data.

Six coarse heads-only circuits: D (deceptive) and H (Honest Twin) for far_v2, sdr_v2 and ser_v2. Every cell
is one (circuit expression, test set) pair evaluated by `evaluate_circuit.py` with the coarse SDR wave's
two-cell design:

    sufficiency  the atomic circuit, or `(E) | m` for a composition: evals sanity, null, pressure
    knockout     `(E) - m`: evals knockout (heads-only knockout, every MLP kept)

`m` is the all-MLP, no-head operand. Compositions are at leaf granularity (head granularity ORs every MLP
unit back in; see outputs/_launch_format_control/README_suites.md). Interchange ablation, 20 random
circuits through both nulls.

Stages (G14):
    control  two drift-control cells: the v1 coarse SDR D heads-only knockout, already run twice on Delta
             (A40), each with that reference's own argv
    1        24 cells: suff + KO for the six circuits on their own test sets; per task D&H suff + KO,
             D-H KO, H-D KO on D's test set
    2        33 cells: cross-task D transfer (suff + KO on the other two D test sets), shared D core
             (suff + KO on all three), the exclusives D_t - D_u - D_v (KO on own test set), H on D's
             test set (suff + KO), D on <task>_nopressure (suff + KO), plus 6 conditional cells
             (D-H KO on the other two tasks), flagged `conditional`

All paths are relative to the repository root, so the same plan runs from any checkout (DC_REPO_ROOT).
`plan_cells` reads only the operands' head masks (for `expected_heads`); `jobs_for` and `job_args` are
pure functions of the cells.
"""

from __future__ import annotations

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
EVALS_DIR = "outputs/_launch_mechanism_v2/evals"
#: The canonical Delta checkout (read-only source of the drift-control run and its reference cells).
MAIN_CHECKOUT = "/projects/beto/swong2/Alignment/Deception-Circuit"
SUITE_JSON = os.path.join(HERE, "suite_v2.json")

TASKS = ("far", "sdr", "ser")
RUNS = {
    "far": {"D": "outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717",
            "H": "outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323"},
    "sdr": {"D": "outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323",
            "H": "outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323"},
    "ser": {"D": "outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101",
            "H": "outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323"},
}
#: The all-MLP, no-head operand, rebuilt from the far_v2 D run (build_operands.py).
ALLMLP = f"{EVALS_DIR}/operands/allmlp_nomb_v2"
#: Config-only task sources for the nopressure test sets (build_operands.py). Never bound as circuits.
STANDINS = {t: f"{EVALS_DIR}/standins/{t}_v2_nopressure" for t in TASKS}
#: Drift control: a copy of the v1 coarse SDR D run (not on this branch) and the format-control operand,
#: whose masks equal the main checkout's llama-8b-instruct_sdr_coarse/_allmlp_nomb (the SDR wave's `m`).
DRIFT_D = f"{EVALS_DIR}/drift_control/sdr_coarse_D_260922-092742"
DRIFT_M = "outputs/_launch_format_control/allmlp_nomb"
#: The two Delta reference cells, each reproduced with its own argv (paths and output dir aside).
DRIFT_CELLS = (
    {"job": "drift_sdr_coarse_D_hko", "label": "D_hko", "names": ("D", "m"),
     "reference_job": 22895982, "common_args": None},                       # fc coarse suite, 2026-10-15
    {"job": "drift_sdr_coarse_D_headsko", "label": "headsko", "names": ("c", "m"),
     "reference_job": 22316469, "common_args": ["--n-random", "20"]},      # submit_headsko.sh, 2026-09-22
)

SUITE_ROOT = "outputs/_suites/mechanism-v2-coarse"
SUFF_EVALS = ["sanity", "null", "pressure"]
KO_EVALS = ["knockout"]
#: Interchange only, 20 random circuits, all 20 through the knockout null (the format-control argv).
COMMON_ARGS = ["--ablation", "interchange", "--n-random", "20", "--knockout-null-count", "20"]
GRANULARITY = "leaf"
CONDITION_SUFFIX = {"deceptive": "", "honest": "_honest", "nopressure": "_nopressure"}

# ------------------------------------------------------------------ cost model
#: Minutes per cell on an A40 without the model load, from sacct of past coarse cells
#: (reports/06-recon-evals-and-bridges2.md A1/A3): KO 29-30 min and suff 28.6-33.4 min per job including
#: a ~3.5 min load; on a nopressure test set suff 10.5-12.9 and KO 15.0-15.6 min per job.
A40_CELL_MIN = {"sufficiency": 27.0, "knockout": 26.0,
                "sufficiency_nopressure": 8.0, "knockout_nopressure": 11.5}
#: Cell-time speed-up over an A40. A100 from 22879998/22881288 (15 min per KO job), H200 from 22945674
#: (3 KO exprs in 18 min). H100 from the Bridges-2 drift control (2026-10-24): one coarse SDR KO cell took
#: 401 s (49774554) and 367 s (49774563), i.e. 26 / 6.4 = 4.0x. Sufficiency cells on an H100 are not
#: measured yet and are assumed to scale the same way.
SPEEDUP = {"A40": 1.0, "L40S": 1.0, "A100": 2.26, "H200": 5.4, "H100": 4.0}
#: Model load and start-up per job (job start to suite created). H100: 10.4 min cold from /ocean (49774554);
#: 0.4 min when the node's page cache was warm (49774563, same node w010 right after). Cold is used.
LOAD_MIN = {"A40": 3.5, "L40S": 3.5, "A100": 3.5, "H200": 3.5, "H100": 10.5}
#: Walltime = estimate x 1.5, rounded up to a quarter hour, at least one hour (fc_cells' rule; orchestrator
#: ruling 2026-10-24: 01:00:00 for the drift control and the first stage-1 wave, tighten from measured
#: times with gen_cells.py --walltime-floor afterwards).
WALLTIME_FACTOR, WALLTIME_FLOOR_MIN = 1.5, 60


def cost_key(cell) -> str:
    return cell["kind"] + ("_nopressure" if cell["condition"] == "nopressure" else "")


def job_minutes(job, gpu: str) -> float:
    """Estimated elapsed minutes of one job on one GPU of class `gpu`."""
    return LOAD_MIN[gpu] + sum(A40_CELL_MIN[cost_key(c)] for c in job["cells"]) / SPEEDUP[gpu]


def walltime(minutes: float, floor_min: int = WALLTIME_FLOOR_MIN) -> str:
    m = max(floor_min, int(math.ceil(round(minutes * WALLTIME_FACTOR, 6) / 15.0)) * 15)
    return f"{m // 60:02d}:{m % 60:02d}:00"


def walltime_hours(text: str) -> float:
    h, m, s = (int(x) for x in text.split(":"))
    return h + m / 60 + s / 3600


# ------------------------------------------------------------------ head sets

def live_heads(run_dir: str, repo: str = REPO) -> frozenset:
    """(layer, head) pairs open in a saved mask, heads in closed attention blocks excluded.

    Read straight from the JSON (the coarse file when present), independently of evaluation.algebra,
    so the checker can hold the evaluator's leaf composition against it.
    """
    base = os.path.join(repo, run_dir)
    path = os.path.join(base, "active_nodes.coarse.json")
    if not os.path.exists(path):
        path = os.path.join(base, "active_nodes.json")
    with open(path) as f:
        masks = json.load(f)["masks"]
    blocks = masks["attention_blocks"]
    return frozenset((int(layer), h) for layer, row in masks["attention_heads"].items()
                     for h, on in enumerate(row) if on and blocks[int(layer)])


# ------------------------------------------------------------------ the plan

def _dataset(task: str, condition: str) -> str:
    return f"{task}_v2{CONDITION_SUFFIX[condition]}"


def plan_cells(repo: str = REPO) -> list:
    """Every cell of the suite, in submission order."""
    names = {f"{r}_{t}": RUNS[t][r] for t in TASKS for r in ("D", "H")}
    S = {n: live_heads(p, repo) for n, p in names.items()}
    S["m"] = frozenset()
    cells = []

    def add(stage, job, label, expr, kind, heads, operands, *, home, test, condition, block,
            task_from, conditional=False, dataset=None, test_task=None):
        cells.append({
            "stage": stage, "job": job, "label": label, "expr": expr, "kind": kind,
            "cell_dir": label if kind == "sufficiency" and "(" not in expr else f"{label}__{GRANULARITY}",
            "block": block, "conditional": conditional, "home_task": home,
            "test_task": test_task or f"{test}_v2", "condition": condition,
            "dataset": dataset or _dataset(test, condition), "task_from": task_from,
            "evals": list(SUFF_EVALS if kind == "sufficiency" else KO_EVALS),
            "operands": dict(operands), "common_args": list(COMMON_ARGS),
            "expected_heads": len(heads)})

    def ops(*ns):
        table = dict(names, m=ALLMLP)
        return {n: table[n] for n in ns}

    def suff(stage, job, name, **kw):
        add(stage, job, name, name, "sufficiency", S[name], ops(name), **kw)

    def suff_c(stage, job, label, expr, heads, used, **kw):
        add(stage, job, f"{label}_suff", f"({expr}) | m", "sufficiency", heads, ops(*used, "m"), **kw)

    def ko(stage, job, label, expr, heads, used, **kw):
        add(stage, job, f"{label}_hko", f"({expr}) - m", "knockout", heads, ops(*used, "m"), **kw)

    # control: the v1 coarse SDR D heads-only KO, once per Delta reference, each with its own argv
    drift_heads = live_heads(DRIFT_D, repo)
    for d in DRIFT_CELLS:
        c, m = d["names"]
        expr = f"({c}) - m" if d["label"] == f"{c}_hko" else f"{c} - m"
        add("control", d["job"], d["label"], expr, "knockout", drift_heads, {c: DRIFT_D, m: DRIFT_M},
            home="sdr", test="sdr", condition="deceptive", block="drift_control", task_from=DRIFT_D,
            dataset="sdr", test_task="sdr")
        if d["common_args"] is not None:
            cells[-1]["common_args"] = list(d["common_args"])
        cells[-1]["reference_job"] = d["reference_job"]

    # stage 1
    for t in TASKS:
        D, H = f"D_{t}", f"H_{t}"
        dt = dict(home=f"{t}_v2", test=t, condition="deceptive", task_from=RUNS[t]["D"])
        ht = dict(home=f"{t}_v2", test=t, condition="honest", task_from=RUNS[t]["H"])
        suff("1", f"s1_{t}__D_suff", D, block="pair", **dt)
        suff_c("1", f"s1_{t}__D_suff", f"{D}_and_{H}", f"{D} & {H}", S[D] & S[H], (D, H),
               block="composition", **dt)
        ko("1", f"s1_{t}__D_ko", D, D, S[D], (D,), block="pair", **dt)
        ko("1", f"s1_{t}__D_ko", f"{D}_and_{H}", f"{D} & {H}", S[D] & S[H], (D, H), block="composition", **dt)
        ko("1", f"s1_{t}__D_ko", f"{D}_minus_{H}", f"{D} - {H}", S[D] - S[H], (D, H), block="composition", **dt)
        ko("1", f"s1_{t}__D_ko", f"{H}_minus_{D}", f"{H} - {D}", S[H] - S[D], (D, H), block="composition", **dt)
        suff("1", f"s1_{t}__H_suff", H, block="pair", **ht)
        ko("1", f"s1_{t}__H_ko", H, H, S[H], (H,), block="pair", **ht)

    # stage 2, one block of jobs per test task u
    Ds = [f"D_{t}" for t in TASKS]
    core = S[Ds[0]] & S[Ds[1]] & S[Ds[2]]
    core_expr = " & ".join(Ds)
    for u in TASKS:
        others = [t for t in TASKS if t != u]
        Du, Hu = f"D_{u}", f"H_{u}"
        dt = dict(test=u, condition="deceptive", task_from=RUNS[u]["D"])
        npt = dict(test=u, condition="nopressure", task_from=STANDINS[u])
        js, jk = f"s2_{u}__D_suff", f"s2_{u}__D_ko"
        for v in others:
            suff("2", js, f"D_{v}", home=f"{v}_v2", block="cross_task", **dt)
        suff_c("2", js, "D_core", core_expr, core, Ds, home="core", block="core", **dt)
        suff("2", js, Hu, home=f"{u}_v2", block="H_on_D_test_set", **dt)
        for v in others:
            ko("2", jk, f"D_{v}", f"D_{v}", S[f"D_{v}"], (f"D_{v}",), home=f"{v}_v2", block="cross_task", **dt)
        ko("2", jk, "D_core", core_expr, core, Ds, home="core", block="core", **dt)
        excl = f"{Du} - " + " - ".join(f"D_{v}" for v in others)
        label = f"{Du}_minus_" + "_minus_".join(f"D_{v}" for v in others)
        ko("2", jk, label, excl, S[Du] - S[f"D_{others[0]}"] - S[f"D_{others[1]}"], [Du] + [f"D_{v}" for v in others],
           home=f"{u}_v2", block="exclusive", **dt)
        ko("2", jk, Hu, Hu, S[Hu], (Hu,), home=f"{u}_v2", block="H_on_D_test_set", **dt)
        for v in others:
            Dv, Hv = f"D_{v}", f"H_{v}"
            ko("2", jk, f"{Dv}_minus_{Hv}", f"{Dv} - {Hv}", S[Dv] - S[Hv], (Dv, Hv), home=f"{v}_v2",
               block="conditional_D_minus_H_cross_task", conditional=True, **dt)
        suff("2", f"s2_{u}__np_suff", Du, home=f"{u}_v2", block="D_on_nopressure", **npt)
        ko("2", f"s2_{u}__np_ko", Du, Du, S[Du], (Du,), home=f"{u}_v2", block="D_on_nopressure", **npt)
    return cells


# ------------------------------------------------------------------ jobs

STAGE_DIR = {"control": "control", "1": "stage1", "2": "stage2"}


def select(cells, stage: str, include_conditional: bool = False) -> list:
    if stage not in STAGE_DIR:
        raise ValueError(f"unknown stage {stage!r}; choose from {', '.join(STAGE_DIR)}")
    if include_conditional and stage != "2":
        raise ValueError("conditional cells exist only in stage 2")
    return [c for c in cells if c["stage"] == stage and (include_conditional or not c["conditional"])]


def _bind_rank(name: str):
    """Binding order on the command line: D_far, H_far, D_sdr, ..., other names, then m."""
    canon = [f"{r}_{t}" for t in TASKS for r in ("D", "H")]
    if name == "m":
        return (2, 0, name)
    return (0, canon.index(name), name) if name in canon else (1, 0, name)


def jobs_for(cells, pack: bool = True) -> list:
    """Group cells into jobs (one evaluate_circuit.py process each).

    Packed (the default), a job is every cell sharing a `job` key: same stage, test set and evals, so one
    model load serves them all. Unpacked, every cell is its own job `<job>__<label>`.
    """
    order, groups = [], {}
    for c in cells:
        key = c["job"] if pack else f"{c['job']}__{c['label']}"
        if key not in groups:
            order.append(key)
            groups[key] = []
        groups[key].append(c)
    jobs = []
    for key in order:
        members = groups[key]
        first = members[0]
        for field in ("stage", "task_from", "evals", "test_task", "condition", "common_args"):
            values = {json.dumps(m[field]) for m in members}
            if len(values) > 1:
                raise ValueError(f"job {key}: cells disagree on {field}: {sorted(values)}")
        binds = {}
        for m in members:
            for name, path in m["operands"].items():
                if binds.setdefault(name, path) != path:
                    raise ValueError(f"job {key}: operand {name} bound to two paths")
        binds = dict(sorted(binds.items(), key=lambda kv: _bind_rank(kv[0])))
        labels = [m["label"] for m in members]
        if len(set(labels)) != len(labels):
            raise ValueError(f"job {key}: duplicate cell labels {labels}")
        out = f"{SUITE_ROOT}/{STAGE_DIR[first['stage']]}/{key}"
        jobs.append({"job": key, "stage": first["stage"], "binds": binds,
                     "exprs": [[m["label"], m["expr"]] for m in members],
                     "task_from": first["task_from"], "evals": list(first["evals"]),
                     "common_args": list(first["common_args"]),
                     "output_dir": out, "cells": members,
                     "results": {m["label"]: f"{out}/cells/{m['cell_dir']}/{first['test_task']}/interchange"
                                 for m in members}})
    return jobs


def job_args(job) -> list:
    """The exact evaluate_circuit.py arguments of one job (paths relative to the repo root)."""
    args = []
    for name, path in job["binds"].items():
        args += ["--circuit", f"{name}={path}"]
    for label, expr in job["exprs"]:
        args += ["--expr", f"{label}={expr}"]
    args += ["--compose-granularity", GRANULARITY, "--task-from", job["task_from"],
             "--evals", *job["evals"], *job["common_args"],
             "--suite-name", job["job"], "--output-dir", job["output_dir"]]
    return args


def load_suite(path: str = SUITE_JSON) -> dict:
    with open(path) as f:
        return json.load(f)
