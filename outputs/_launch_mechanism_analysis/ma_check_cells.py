#!/usr/bin/env python3
"""
ma_check_cells.py -- login-node check of every evaluate_circuit.py command the mechanism-analysis suite generates.

A job is one Slurm job (scripts/evaluate_chain.sbatch) running one evaluate_circuit.py process per scheme group.
For each group, on the CPU, without evaluating anything:

  1. evaluate_circuit.build_parser().parse_args(<the group's arguments>) accepts the command; every --evals name
     is known and none is `benchmarks`; exactly one --task-from; the evals are `knockout` only (never sanity,
     null or pressure); `--ablation` is given explicitly and is the group's scheme; a mean group carries the
     variant-matched no_pressure bank (`--variant-mean-bank no_pressure`, R13), other groups do not
  2. every path is relative to the repository root and resolves there (bound circuits have config.json and
     active_nodes.json, the task source has config.json); the output dir lies under
     outputs/_suites/mechanism-analysis/<stage dir>/
  3. ticket 06's checks (outputs/_launch_mechanism_v2/evals/check_cells.py, reused): evaluation.circuits
     composes every expression at leaf from the real masks with the cell's `expected_heads`, knockout cells keep
     no MLP unit, and resolve_tasks binds exactly one test set with the cell's task, condition and dataset
     directory, holding at least test_samples rows

Across the job: the chain arguments split on ':::' give back each group's arguments. Across all jobs: no two
groups share an output dir or a suite name.

Boundary: imports the evaluator's argparse and its circuit/task resolution only; never build_session, main() or
--dry-run; no model, no GPU.

usage (from anywhere):
    python outputs/_launch_mechanism_analysis/ma_check_cells.py [--stage 1a]
exit 0 when every job checks clean.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ma_cells as mc  # noqa: E402


#: Ticket 06's checker (circuit composition and task binding checks).
v2check = mc._load_module("mv2_check_cells", f"{mc.V2_LAUNCH}/check_cells.py")


def _option(argv, flag):
    """The values following `flag` up to the next option, or None when the flag is absent."""
    if flag not in argv:
        return None
    i = argv.index(flag) + 1
    out = []
    while i < len(argv) and not argv[i].startswith("--"):
        out.append(argv[i])
        i += 1
    return out


def _check_paths(group, repo, stage_root) -> list:
    problems = []
    for name, path in group["binds"].items():
        if os.path.isabs(path):
            problems.append(f"circuit {name}={path} is not relative to the repo root")
            continue
        for f in ("config.json", "active_nodes.json"):
            if not os.path.isfile(os.path.join(repo, path, f)):
                problems.append(f"circuit {name}: {path}/{f} not found")
    tf = group["task_from"]
    if os.path.isabs(tf):
        problems.append(f"--task-from {tf} is not relative to the repo root")
    elif not os.path.isfile(os.path.join(repo, tf, "config.json")):
        problems.append(f"--task-from {tf}/config.json not found")
    out = group["output_dir"]
    if os.path.isabs(out) or not os.path.normpath(out).startswith(stage_root + "/"):
        problems.append(f"--output-dir {out} must be relative and under {stage_root}/")
    return problems


def check_group(group, stage, parser, circuits, repo) -> list:
    argv = mc.group_args(group)
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            cli = parser.parse_args(argv)
    except SystemExit:
        return [f"argparse rejected the command: {err.getvalue().strip().splitlines()[-1:]}"]
    from evaluation import list_evaluations
    from evaluation.ablation import matched_variants
    problems = [f"unknown eval {e}" for e in cli.evals if e not in list_evaluations()]
    if len(cli.task_from or []) != 1:
        problems.append(f"{len(cli.task_from or [])} --task-from given, exactly 1 required")
    if "benchmarks" in cli.evals:
        problems.append("requests benchmarks (EVAL 5), which this suite never runs")
    if list(cli.evals) != mc.KO_EVALS:
        problems.append(f"evals {list(cli.evals)}: these groups run knockout only (never sanity, null or "
                        f"pressure)")
    scheme = _option(argv, "--ablation")
    if scheme != [group["scheme"]] or cli.ablation != group["scheme"]:
        problems.append(f"--ablation {scheme} given, the group's scheme is {group['scheme']} (pass it explicitly)")
    bank = matched_variants(cli)
    if group["scheme"] == "mean" and bank != ("no_pressure",):
        problems.append("mean group lacks the variant-matched no_pressure bank (--variant-mean-bank no_pressure, "
                        "R13)")
    if group["scheme"] != "mean" and bank:
        problems.append(f"{group['scheme']} group passes --variant-mean-bank, which only mean ablation reads")
    problems += _check_paths(group, repo, f"{mc.SUITE_ROOT}/{mc.STAGE_DIR[stage]}")
    if problems:
        return problems
    try:
        found, bindings, configs = v2check._check_circuits(group, cli, circuits)
        problems += found
        problems += v2check._check_tasks(group, cli, bindings, configs, circuits, repo)
    except Exception as e:  # resolution errors are findings, not crashes
        problems.append(f"resolution failed: {type(e).__name__}: {e}")
    return problems


def check_jobs(jobs, repo: str = mc.REPO) -> dict:
    """{job id: [problem, ...]} for every job; an empty list means the job checks clean."""
    repo = os.path.realpath(repo)
    if repo not in sys.path:
        sys.path.insert(0, repo)
    cwd = os.getcwd()
    os.chdir(repo)           # the evaluator resolves relative run dirs against the cwd, as in a job
    try:
        import evaluate_circuit
        from evaluation import circuits
        parser = evaluate_circuit.build_parser()
        out = {}
        for job in jobs:
            items = []
            for group in job["groups"]:
                items += [f"group {group['group']}: {p}"
                          for p in check_group(group, job["stage"], parser, circuits, repo)]
            parts, cur = [], []
            for a in mc.chain_args(job):
                if a == mc.CHAIN_SEP:
                    parts.append(cur)
                    cur = []
                else:
                    cur.append(a)
            parts.append(cur)
            if parts != [mc.group_args(g) for g in job["groups"]]:
                items.append("the chain arguments do not split back into the groups' arguments")
            out[job["job"]] = items
        groups = [(job["job"], g) for job in jobs for g in job["groups"]]
        for key in ("output_dir", "suite_name"):
            values = [g[key] for _, g in groups]
            for job_id, g in groups:
                if values.count(g[key]) > 1:
                    out[job_id].append(f"group {g['group']}: {key} {g[key]} shared with another group")
        return out
    finally:
        os.chdir(cwd)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stage", nargs="+", default=list(mc.STAGE_DIR), choices=list(mc.STAGE_DIR))
    a = p.parse_args(argv)
    cells = mc.load_suite()["cells"]
    jobs = []
    for s in a.stage:
        jobs += mc.jobs_for(mc.select(cells, s))
    problems = check_jobs(jobs)
    for job in jobs:
        items = problems[job["job"]]
        groups = "; ".join(f"{g['scheme']}: " + ", ".join(f"{c['label']}:{c['expected_heads']}h" for c in g["cells"])
                           for g in job["groups"])
        print(f"{'OK  ' if not items else 'FAIL'} {job['job']:10s} {groups}")
        for item in items:
            print(f"     - {item}")
    n = sum(len(v) for v in problems.values())
    print(f"\n{len(jobs)} job(s), {sum(len(j['groups']) for j in jobs)} group(s), "
          f"{sum(len(j['cells']) for j in jobs)} cell(s), {n} problem(s)")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
