"""
fc_cells.py — the cells of the format-control evaluation suites, as data.

One suite per task family evaluates three circuits of one task:

    D  the deceptive circuit (the mechanism circuit)
    H  its Honest Twin
    F  the Format Circuit (pruned on the `nopressure` condition)

each on three test sets, the datasets those runs were pruned on
(`<task>`, `<task>_honest`, `<task>_nopressure`, bound with `--task-from` on the
D, H and F run directories), plus the delta circuits D-F, D&F, F-D and the
exclusive-or family of D, H, F as knockout cells on the D test set.

`plan_suite` turns a suite configuration into a list of jobs (one Slurm job =
one shard directory = one `evaluate_circuit.py` invocation) and `job_args`
renders a job's exact argument list. Both are pure functions of the
configuration: nothing here touches the filesystem, so the plan can be tested
and printed before any run directory exists.

Families
--------
fine    One job per (circuit, dataset) runs evals 1-4 (sanity, knockout, null,
        pressure): faithfulness and knockout in one model load, as the
        2026-09-22 cross-task rerun did. Delta jobs run eval 2 only, at
        `--compose-granularity both` (two cells per job: `<label>__leaf` and
        `<label>__head`; head is the primary reading).

coarse  Heads-only coarse circuits are stored expanded: every MLP unit is open,
        so a plain knockout removes every MLP and says nothing about the heads.
        Sufficiency therefore runs on the atomic circuit (evals sanity, null,
        pressure) and every knockout is the heads-only cell `(<expr>) - m`
        against the all-MLP, no-head operand `m`. That expression is composed
        at `leaf`: `head` granularity cannot remove MLPs from circuits that
        have no `mlp_blocks` gate (it ORs the operands' MLP units), and on
        these masks every live head has all its neurons open, so leaf set
        operations are head set operations. This is a deliberate deviation
        from the spec's literal "coarse at head" (orchestrator ruling,
        2026-10-13); summaries report these cells at head level.

Every planned cell carries `dataset` (the directory merge_shards.py files it
under) and `condition` (deceptive / honest / nopressure of its test set); the
manifest's per-suite `cells` index adds `job` and `path`, so a reader can find
a cell by (circuit, condition).
"""

from __future__ import annotations

import math
import re
from types import SimpleNamespace

#: The three circuits of a suite, in binding order, and the deception
#: condition each was pruned on (which is also its test set's condition).
ROLES = ("D", "H", "F")
ROLE_CONDITION = {"D": "deceptive", "H": "honest", "F": "nopressure"}

#: Delta circuits on the D test set: explicit differences, then the
#: exclusive-or family of `--xor D,H,F`.
DELTAS = (("D_minus_F", "D - F"), ("D_and_F", "D & F"), ("F_minus_D", "F - D"))
XOR = ("D", "H", "F")

FINE_ATOMIC_EVALS = ("sanity", "knockout", "null", "pressure")
COARSE_SUFFICIENCY_EVALS = ("sanity", "null", "pressure")
KNOCKOUT_EVALS = ("knockout",)

#: Interchange only, 20 random circuits, all 20 through the knockout null.
COMMON_ARGS = ("--ablation", "interchange", "--n-random", "20",
               "--knockout-null-count", "20")

#: The heads-only operand's binding name in coarse suites.
ALLMLP = "m"
HKO = "_hko"

SUITES_ROOT = "outputs/_suites"


def dataset_label(task: str, condition) -> str:
    """The test set's directory name: `<task>` or `<task>_<condition>`.

    Read from the task registry's own `dataset_dir`, so the label is exactly
    the directory `--task-from` loads.
    """
    from tasks import get_task
    args = SimpleNamespace(data_dir="", deception_condition=condition or "deceptive")
    return get_task(task).dataset_dir(args)


def xor_family(names=XOR):
    """[(label, expr)] of the exclusive-or family, written with ` - `.

    Labels are the evaluator's own `--xor` slugs (`D_minus_H_minus_F`); the
    expression uses `-` rather than `\\` so it survives any shell.
    """
    from evaluation.algebra import expand_xor
    return [(label, re.sub(r"\s*\\\s*", " - ", expr)) for label, expr in expand_xor(names)]


def _names_in(expr: str):
    used = set(re.findall(r"[A-Za-z0-9_]+", expr))
    return [r for r in ROLES if r in used]


def _job(suite, cfg, *, job_id, binds, exprs, granularity, task_role, evals, cells):
    runs = cfg["runs"]
    needed = list(binds) + ([task_role] if task_role not in binds else [])
    awaits = [r for r in ROLES if r in needed and not runs.get(r)]
    if exprs and cfg["family"] == "coarse" and not cfg.get("allmlp"):
        awaits.append(ALLMLP)
    return {"suite": suite, "job": job_id, "family": cfg["family"], "task": cfg["task"],
            "binds": {r: runs.get(r) for r in binds},
            "allmlp": cfg.get("allmlp") if cfg["family"] == "coarse" and exprs else None,
            "exprs": [list(e) for e in exprs] if exprs else [],
            "compose_granularity": granularity,
            "task_from_role": task_role, "task_from": runs.get(task_role),
            "evals": list(evals), "cells": cells, "awaits": awaits}


def plan_suite(suite: str, cfg: dict) -> list:
    """Every job of one suite, in submission order.

    cfg = {"family": "fine"|"coarse", "task": "far"|"sdr",
           "runs": {"D": run_dir, "H": run_dir, "F": run_dir or None},
           "allmlp": run_dir (coarse only)}

    A job whose run directory is not configured yet carries `awaits` (e.g.
    ["F"]) and has no arguments; everything else about it is planned.
    """
    family, task = cfg["family"], cfg["task"]
    if family not in ("fine", "coarse"):
        raise ValueError(f"unknown family {family!r}")
    ds = {r: dataset_label(task, ROLE_CONDITION[r]) for r in ROLES}
    jobs = []

    def cell(circuit, data_role, roles):
        """One cell: where it lands (cells/<circuit>/<dataset>/) and the
        deception condition of its test set."""
        return {"circuit": circuit, "dataset": ds[data_role],
                "condition": ROLE_CONDITION[data_role], "roles": roles}

    # Atomic circuits on each test set.
    for circ in ROLES:
        for data in ROLES:
            if family == "fine":
                jobs.append(_job(
                    suite, cfg, job_id=f"{circ}__{ds[data]}", binds=[circ], exprs=None,
                    granularity=None, task_role=data, evals=FINE_ATOMIC_EVALS,
                    cells=[cell(circ, data, ["faithfulness", "knockout"])]))
            else:
                jobs.append(_job(
                    suite, cfg, job_id=f"{circ}__{ds[data]}", binds=[circ], exprs=None,
                    granularity=None, task_role=data, evals=COARSE_SUFFICIENCY_EVALS,
                    cells=[cell(circ, data, ["faithfulness"])]))
    if family == "coarse":
        for circ in ROLES:
            for data in ROLES:
                label = f"{circ}{HKO}"
                jobs.append(_job(
                    suite, cfg, job_id=f"{label}__{ds[data]}", binds=[circ],
                    exprs=[(label, f"({circ}) - {ALLMLP}")], granularity="leaf",
                    task_role=data, evals=KNOCKOUT_EVALS,
                    cells=[cell(f"{label}__leaf", data, ["knockout"])]))

    # Deltas on the D test set.
    for label, expr in list(DELTAS) + xor_family():
        binds = _names_in(expr)
        if family == "fine":
            exprs, gran = [(label, expr)], "both"
            cells = [cell(f"{label}__{g}", "D", ["delta"]) for g in ("leaf", "head")]
        else:
            label = f"{label}{HKO}"
            exprs, gran = [(label, f"({expr}) - {ALLMLP}")], "leaf"
            cells = [cell(f"{label}__leaf", "D", ["delta"])]
        jobs.append(_job(suite, cfg, job_id=f"{label}__{ds['D']}", binds=binds, exprs=exprs,
                         granularity=gran, task_role="D", evals=KNOCKOUT_EVALS, cells=cells))
    return jobs


def side_job_args(suite: str, cfg: dict, side: dict) -> list:
    """Arguments of a side job: one extra circuit (e.g. a retune of F) on one
    of the suite's test sets, written beside the suite (not under _shards/,
    so the merge never files it into cells/)."""
    return ["--circuit", f"{side['circuit']}={side['run']}",
            "--task-from", cfg["runs"][side["task_from_role"]],
            "--evals", *side["evals"], *COMMON_ARGS,
            "--suite-name", suite, "--output-dir", f"{SUITES_ROOT}/{suite}/{side['output_dir']}"]


def shard_dir(job: dict) -> str:
    return f"{SUITES_ROOT}/{job['suite']}/_shards/{job['job']}"


def job_args(job: dict) -> list:
    """The exact `evaluate_circuit.py` arguments of one job."""
    if job["awaits"]:
        raise ValueError(f"job {job['job']} awaits {', '.join(job['awaits'])} "
                         f"(run directory not configured)")
    args = []
    for name, run in job["binds"].items():
        args += ["--circuit", f"{name}={run}"]
    if job["allmlp"]:
        args += ["--circuit", f"{ALLMLP}={job['allmlp']}"]
    for label, expr in job["exprs"]:
        args += ["--expr", f"{label}={expr}"]
    if job["compose_granularity"]:
        args += ["--compose-granularity", job["compose_granularity"]]
    args += ["--task-from", job["task_from"], "--evals", *job["evals"], *COMMON_ARGS,
             "--suite-name", job["suite"], "--output-dir", shard_dir(job)]
    return args


# ==============================================================================
# DRY RUNS AND WALLTIME
# ==============================================================================

_TOTAL_RE = re.compile(r"^\s*TOTAL\s+([0-9.]+)\s+min", re.M)


def parse_dryrun_log(text: str):
    """(passed, estimated minutes) of an `evaluate_circuit.py --dry-run` log."""
    if "Traceback" in text or "Nothing was written" not in text:
        return False, None
    totals = _TOTAL_RE.findall(text)
    return True, (float(totals[-1]) if totals else None)


def walltime(estimate_min: float) -> str:
    """Slurm --time: the dry-run estimate x 1.5, rounded up to a quarter hour,
    at least one hour. No cap (job length is not limited)."""
    minutes = max(60, int(math.ceil(round(estimate_min * 1.5, 6) / 15.0)) * 15)
    return f"{minutes // 60:02d}:{minutes % 60:02d}:00"
