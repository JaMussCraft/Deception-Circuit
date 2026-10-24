#!/usr/bin/env python3
"""
check_cells.py -- login-node check of every evaluate_circuit.py command the v2 suite generates (ticket 06).

For each job (as gen_cells.py would submit it), on the CPU, without evaluating anything:

  1. evaluate_circuit.build_parser().parse_args(<the job's arguments>) accepts the command;
     every --evals name is known and none is `benchmarks` (no EVAL 5 in this suite); exactly one
     --task-from (the test set never comes from an operand's config)
  2. every path is relative to the repository root and resolves there: bound circuits have config.json
     and active_nodes.json, the task source has config.json, the output dir lies under the suite root;
     a nopressure stand-in is never bound as a circuit
  3. evaluation.circuits.resolve_circuits composes every expression at leaf from the real masks, and each
     cell's head count equals `expected_heads` (computed from the masks independently in mv2_cells);
     knockout cells `(E) - m` keep no MLP unit, sufficiency cells keep every MLP unit
  4. evaluation.circuits.resolve_tasks binds exactly one test set whose task and deception condition are
     the cell's, and whose derived dataset directory data/datasets/<dataset> exists with a test split of
     at least test_samples rows; an atomic home-test-set cell's task source is its own run (so sanity runs)

Boundary: this imports the evaluator's argparse and its circuit/task resolution only. It never calls
build_session, main() or --dry-run, loads no model and touches no GPU.

usage (from anywhere):
    python outputs/_launch_mechanism_v2/evals/check_cells.py [--stage control 1 2] [--no-pack]
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
import mv2_cells as mc  # noqa: E402


def _active(counts: dict, key: str) -> int:
    return counts[key]["active"]


def _check_paths(job, repo) -> list:
    problems = []
    standins = set(mc.STANDINS.values())
    for name, path in job["binds"].items():
        if os.path.isabs(path):
            problems.append(f"circuit {name}={path} is not relative to the repo root")
            continue
        for f in ("config.json", "active_nodes.json"):
            if not os.path.isfile(os.path.join(repo, path, f)):
                problems.append(f"circuit {name}: {path}/{f} not found")
        if path in standins:
            problems.append(f"circuit {name} binds the config-only stand-in {path}")
    tf = job["task_from"]
    if os.path.isabs(tf):
        problems.append(f"--task-from {tf} is not relative to the repo root")
    elif not os.path.isfile(os.path.join(repo, tf, "config.json")):
        problems.append(f"--task-from {tf}/config.json not found")
    out = job["output_dir"]
    if os.path.isabs(out) or not os.path.normpath(out).startswith(mc.SUITE_ROOT + os.sep):
        problems.append(f"--output-dir {out} must be relative and under {mc.SUITE_ROOT}/")
    return problems


def _check_circuits(job, cli, circuits) -> tuple:
    problems = []
    specs, bindings, _, configs, _ = circuits.resolve_circuits(cli)
    by_label = {s.label: s for s in specs}
    if len(specs) != len(job["cells"]):
        problems.append(f"{len(specs)} circuit specs for {len(job['cells'])} cells")
    for cell in job["cells"]:
        spec = by_label.get(cell["cell_dir"])
        if spec is None:
            problems.append(f"cell {cell['label']}: no circuit spec labelled {cell['cell_dir']}")
            continue
        heads = _active(spec.counts, "attention_heads")
        if heads != cell["expected_heads"]:
            problems.append(f"cell {cell['label']}: {heads} heads composed, {cell['expected_heads']} expected")
        mlp = [(_active(spec.counts, k), spec.counts[k]["total"]) for k in ("mlp_hidden", "mlp_output")]
        if cell["kind"] == "knockout" and any(a for a, _ in mlp):
            problems.append(f"cell {cell['label']}: knockout keeps MLP units {mlp}")
        if cell["kind"] == "sufficiency" and any(a != t for a, t in mlp):
            problems.append(f"cell {cell['label']}: sufficiency circuit lacks MLP units {mlp}")
    return problems, bindings, configs


def _check_tasks(job, cli, bindings, configs, circuits, repo) -> list:
    from tasks import get_task
    problems = []
    specs = circuits.resolve_tasks(cli, bindings, configs)
    if len(specs) != 1:
        return [f"{len(specs)} test sets bound, expected 1"]
    args = specs[0].args
    cell = job["cells"][0]
    cond = circuits.condition_of(args)
    if args.task != cell["test_task"]:
        problems.append(f"test task {args.task}, cells expect {cell['test_task']}")
    if cond != cell["condition"]:
        problems.append(f"test-set condition {cond}, cells expect {cell['condition']}")
    ds = os.path.normpath(get_task(args.task).dataset_dir(args))
    want = os.path.join("data", "datasets", cell["dataset"])
    if ds != want:
        problems.append(f"dataset dir {ds}, cells expect {want}")
    test = os.path.join(repo, ds, "test")
    if not os.path.isdir(test):
        problems.append(f"{ds}/test not found")
    else:
        import datasets
        n = datasets.load_from_disk(test).num_rows
        if args.test_samples and n < args.test_samples:
            problems.append(f"{ds}/test has {n} rows < test_samples {args.test_samples}")
    for c in job["cells"]:
        if c["kind"] == "sufficiency" and c["block"] == "pair" and c["operands"][c["label"]] != job["task_from"]:
            problems.append(f"cell {c['label']}: home test set bound from {job['task_from']}, not its own run")
    return problems


def check_job(job, parser, circuits, repo) -> list:
    argv = mc.job_args(job)
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            cli = parser.parse_args(argv)
    except SystemExit:
        return [f"argparse rejected the command: {err.getvalue().strip().splitlines()[-1:]}"]
    from evaluation import list_evaluations
    problems = [f"unknown eval {e}" for e in cli.evals if e not in list_evaluations()]
    if len(cli.task_from or []) != 1:
        # without exactly one --task-from the evaluator would add every bound circuit's own task,
        # including the far_v2 config of the operand m
        problems.append(f"{len(cli.task_from or [])} --task-from given, exactly 1 required")
    if "benchmarks" in cli.evals:
        problems.append("requests benchmarks (EVAL 5), which this suite never runs")
    problems += _check_paths(job, repo)
    if problems:
        return problems
    try:
        found, bindings, configs = _check_circuits(job, cli, circuits)
        problems += found
        problems += _check_tasks(job, cli, bindings, configs, circuits, repo)
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
        out = {job["job"]: check_job(job, parser, circuits, repo) for job in jobs}
        dirs = [job["output_dir"] for job in jobs]
        for job in jobs:
            if dirs.count(job["output_dir"]) > 1:
                out[job["job"]].append(f"output dir {job['output_dir']} shared with another job")
        return out
    finally:
        os.chdir(cwd)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stage", nargs="+", default=list(mc.STAGE_DIR), choices=list(mc.STAGE_DIR))
    p.add_argument("--no-pack", action="store_true")
    a = p.parse_args(argv)
    cells = mc.load_suite()["cells"]
    jobs = []
    for s in a.stage:
        jobs += mc.jobs_for(mc.select(cells, s, include_conditional=(s == "2")), pack=not a.no_pack)
    problems = check_jobs(jobs)
    for job in jobs:
        items = problems[job["job"]]
        heads = ", ".join(f"{c['label']}:{c['expected_heads']}h" for c in job["cells"])
        print(f"{'OK  ' if not items else 'FAIL'} {job['job']:24s} {job['task_from'].split('/')[-1]:58s} {heads}")
        for item in items:
            print(f"     - {item}")
    n = sum(len(v) for v in problems.values())
    print(f"\n{len(jobs)} job(s), {sum(len(j['cells']) for j in jobs)} cell(s), {n} problem(s)")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
