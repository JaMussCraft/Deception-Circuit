"""
evaluation/suite.py — run a grid of (circuit, task) cells and tabulate it.

One cell is exactly what `evaluate_circuit.py` used to be: a circuit, a task,
an ablation scheme, and the sanity / knockout / null / pressure evaluations
written as JSON next to a log. A suite is the cartesian product of the
resolved circuits and tasks, run in one process against one loaded model.

Layout
------
The single-circuit-on-its-own-task invocation is untouched — it still writes

    <run_dir>/evaluations/<ablation>/{sanity,knockout,null}.json
    <run_dir>/evaluations/index.json

Anything else (more than one circuit, any composed circuit, any task that is
not the circuit's own, or an explicit --suite-name) writes

    outputs/_suites/<suite-name>/
      suite.json    the spec and its provenance
      suite.log     tee'd stdout/stderr
      matrix.json   circuit x task x eval -> headline metrics
      matrix.csv    the same, one metric per row, for the 3x3 / 3x6 tables
      cells/<circuit-label>/<task-label>/<ablation>/
          sanity.json knockout.json null.json pressure.json summary.json plots/

The per-cell body is the same code in both cases, so a suite cell's JSON is
byte-comparable with a legacy run's.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time

from evaluation import get_evaluation, report
from evaluation.context import SCHEMA_VERSION, baseline_numbers, reference_numbers
from evaluation.masks import ALGORITHM_VERSION, count_masks, save_packed_masks
from run_io import tee_stdout_stderr

#: CLI flags that mean "this is a suite, not a single run".
SUITE_FLAGS = ("circuit", "expr", "xor", "all_pairs_delta", "task", "task_from",
               "suite_name")


# ==============================================================================
# LAYOUT
# ==============================================================================

def is_legacy(cli) -> bool:
    """True when the invocation is the historical one-run-one-task form.

    Deliberately decided from the *flags*, not from the resolved specs: a
    `--task-from` pointing at the circuit's own run still means the caller
    asked for a suite, and silently writing it into the run's own
    `evaluations/` would overwrite results with different provenance.
    """
    for flag in SUITE_FLAGS:
        value = getattr(cli, flag, None)
        if value:
            return False
    return bool(getattr(cli, "run_dir", None))


def default_suite_name() -> str:
    return time.strftime("suite_%y%m%d-%H%M%S")


def suite_root(cli, base_run_dir: str) -> str:
    """`outputs/_suites/<name>` — sibling of the run directories, or --output-dir."""
    if getattr(cli, "output_dir", None):
        return cli.output_dir
    outputs = os.path.dirname(os.path.dirname(os.path.abspath(base_run_dir)))
    return os.path.join(outputs, "_suites", cli.suite_name or default_suite_name())


def cell_dir(root: str, legacy: bool, circuit_spec, task_spec, ablation: str) -> str:
    if legacy:
        return os.path.join(root, ablation)
    return os.path.join(root, "cells", circuit_spec.label, task_spec.label, ablation)


# ==============================================================================
# JSON
# ==============================================================================

def write_json(path, payload):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    return path


def circuit_summary(ctx) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "run_dir": os.path.abspath(ctx.run_dir),
        "ablation": ctx.cli.ablation,
        "model": ctx.args.model,
        "task": ctx.args.task,
        "metric_columns": [list(c) for c in ctx.task.metric_columns],
        "metric_better": dict(ctx.task.metric_better),
        "geometry": ctx.geometry,
        "cli": {k: v for k, v in sorted(vars(ctx.cli).items())},
        "circuit": {"counts": ctx.counts},
        "sanity_circuit": {"granularity": ctx.sanity_granularity,
                           "counts": ctx.sanity_counts},
        "knockout": {"granularity": ctx.cli.knockout_granularity,
                     "counts": count_masks(ctx.knockout_masks)},
        "reference_numbers": {"source": "results.json:node_eval",
                              "node_eval": reference_numbers(ctx),
                              "baseline": baseline_numbers(ctx)},
    }


def random_circuits_record(ctx) -> dict:
    from evaluation.masks import check_feasibility
    return {
        "seed": ctx.cli.null_seed,
        "n": len(ctx.random_masks),
        "start": ctx.cli.null_start,
        "indices": ctx.random_indices,
        "alloc": ctx.cli.null_alloc,
        "algorithm_version": ALGORITHM_VERSION,
        "per_layer_counts": count_masks(ctx.random_masks[0]) if ctx.random_masks else {},
        "feasibility": check_feasibility(ctx.circuit_masks, ctx.geometry["num_heads"],
                                         ctx.geometry["head_dim"]),
        "note": "The masks themselves are not stored: they are exactly "
                "regenerable from (seed, indices, alloc, algorithm_version) via "
                "evaluation.masks.sample_random_mask_set.",
    }


def update_index(ctx, headlines: dict) -> str:
    path = os.path.join(ctx.cli.output_dir, "index.json")
    index = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                index = json.load(f)
        except (ValueError, OSError):
            index = {}
    index[ctx.cli.ablation] = {"last_run": time.strftime("%Y-%m-%dT%H:%M:%S"),
                              "evals": ctx.cli.evals, **headlines}
    return write_json(path, index)


# ==============================================================================
# ONE CELL
# ==============================================================================

def run_cell(ctx, *, legacy: bool) -> dict:
    """Run every requested evaluation for one (circuit, task) cell.

    Returns {"headlines": {...}, "skipped": {...}, "failures": [...]}.
    """
    cli = ctx.cli
    spec, task_spec = ctx.circuit_spec, ctx.task_spec

    os.makedirs(ctx.plots_dir, exist_ok=True)
    report.banner("CIRCUIT EVALUATION")
    report.kv("run dir", ctx.run_dir)
    report.kv("model / task", f"{ctx.args.model} / {ctx.args.task}")
    if not legacy:
        report.kv("circuit", f"{spec.label}  ({spec.kind}"
                             + (f", {spec.expr}" if spec.expr else "") + ")")
        report.kv("task cell", task_spec.label)
    report.kv("device", cli.device)
    report.kv("reference", cli.reference)
    report.kv("evaluations", ", ".join(cli.evals))
    report.kv("test samples", len(ctx.test_loader.dataset))
    report.kv("output dir", ctx.out_dir)

    report.ablation_banner(cli.ablation)
    report.counts_table(ctx.counts, ctx.geometry)
    report.per_layer_table(ctx.counts)

    # The cell's own circuit is what the model carries between evaluations;
    # every `ctx.circuit(...)` block restores back to it.
    ctx.apply_circuit(ctx.circuit_masks, verify=cli.verify)

    summary = circuit_summary(ctx)
    summary["verification"] = {"masks_roundtrip": bool(cli.verify)}
    if not legacy:
        summary["circuit_spec"] = spec.provenance()
        summary["task_spec"] = task_spec.provenance()
    headlines, skipped = {}, {}

    for name in cli.evals:
        evaluation = get_evaluation(name)
        ok, reason = ctx.requires_ok(evaluation)
        if not ok:
            print(f"\n  Skipping '{name}': {reason}")
            skipped[name] = reason
            continue

        started = time.time()
        payload = evaluation.run(ctx)
        payload["seconds"] = round(time.time() - started, 1)
        evaluation.report(payload, ctx)
        for path in evaluation.plots(payload, ctx):
            if path:
                print(f"  Wrote {path}")
        write_json(os.path.join(ctx.out_dir, f"{name}.json"), payload)
        headlines[name] = payload.get("headline", {})
        summary["verification"].update(payload.get("verification", {}))

    if "null" in cli.evals and ctx.random_masks:
        write_json(os.path.join(ctx.out_dir, "random_circuits.json"),
                   random_circuits_record(ctx))
        if cli.save_null_masks:
            save_packed_masks(os.path.join(ctx.out_dir, "random_circuits.npz"),
                              ctx.random_masks, ctx.random_indices)

    summary["failures"] = ctx.failures
    if skipped:
        summary["skipped"] = skipped
    write_json(os.path.join(ctx.out_dir, "summary.json"), summary)
    if legacy:
        update_index(ctx, headlines)

    report.banner("DONE")
    print(f"\n  Results in {ctx.out_dir}")
    if ctx.failures:
        print(f"\n  {len(ctx.failures)} check(s) FAILED:")
        for failure in ctx.failures:
            print(f"    - {failure}")
    return {"headlines": headlines, "skipped": skipped, "failures": ctx.failures}


# ==============================================================================
# THE GRID
# ==============================================================================

def suite_record(session, root: str) -> dict:
    import numpy

    cli = session.cli
    return {
        "schema_version": SCHEMA_VERSION,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "root": os.path.abspath(root),
        "argv": list(sys.argv),
        "ablation": cli.ablation,
        "evals": list(cli.evals),
        "model": session.base_args.model,
        "geometry": session.geometry,
        "compose_granularity": getattr(cli, "compose_granularity", "both"),
        "membership_convention": {
            "leaf": "attention_neurons / mlp_hidden / mlp_output",
            "head": "attention_heads + mlp_blocks",
            "embedding": "not a set member; the OR of the operands' gates",
            "coarse_gates": "re-derived bottom-up from the fine gates",
        },
        "circuits": [spec.provenance() for spec in session.circuits],
        "tasks": [spec.provenance() for spec in session.tasks],
        "cli": {k: v for k, v in sorted(vars(cli).items())},
        "versions": {"mask_algorithm": ALGORITHM_VERSION,
                     "numpy": numpy.__version__,
                     "python": sys.version.split()[0]},
    }


def write_matrix(root: str, cells: list) -> list:
    """matrix.json + matrix.csv — the 3x3 / 3x6 tables, unpivoted."""
    json_path = write_json(os.path.join(root, "matrix.json"),
                           {"created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "cells": cells})

    csv_path = os.path.join(root, "matrix.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["circuit", "circuit_kind", "expr", "task", "ablation",
                         "eval", "metric", "value"])
        for cell in cells:
            for eval_name, headline in sorted(cell["headlines"].items()):
                if not isinstance(headline, dict):
                    continue
                for metric, value in sorted(headline.items()):
                    writer.writerow([cell["circuit"], cell["circuit_kind"],
                                     cell["expr"] or "", cell["task"],
                                     cell["ablation"], eval_name, metric, value])
    return [json_path, csv_path]


def run(session) -> int:
    cli = session.cli
    legacy = cli.legacy
    root = (cli.output_dir if legacy else suite_root(cli, session.base_run_dir))
    os.makedirs(root, exist_ok=True)

    log_path = os.path.join(root, "evaluation.log" if legacy else "suite.log")
    if legacy:
        # The legacy log lives beside the ablation's results, not at the root.
        log_path = os.path.join(root, cli.ablation, "evaluation.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    cells, any_failure = [], False
    with tee_stdout_stderr(log_path, mode="a"):
        print("\n" + "#" * report.W)
        print(f"# {time.strftime('%Y-%m-%d %H:%M:%S')}  {' '.join(sys.argv)}")
        print("#" * report.W)

        if not legacy:
            write_json(os.path.join(root, "suite.json"), suite_record(session, root))
            report.banner("SUITE")
            report.kv("root", root)
            report.kv("circuits", ", ".join(s.label for s in session.circuits))
            report.kv("tasks", ", ".join(s.label for s in session.tasks))
            report.kv("cells", len(session.circuits) * len(session.tasks))

        # Task-outer / circuit-inner: one dataloader, mean bank and reference
        # cache per task, reused by every circuit evaluated against it.
        for task_spec in session.tasks:
            for circuit_spec in session.circuits:
                out_dir = cell_dir(root, legacy, circuit_spec, task_spec, cli.ablation)
                ctx = session.context_for(circuit_spec, task_spec, out_dir)
                result = run_cell(ctx, legacy=legacy)
                any_failure = any_failure or bool(result["failures"])
                cells.append({
                    "circuit": circuit_spec.label,
                    "circuit_kind": circuit_spec.kind,
                    "expr": circuit_spec.expr,
                    "task": task_spec.label,
                    "ablation": cli.ablation,
                    "out_dir": out_dir,
                    "counts": {k: v["active"] for k, v in circuit_spec.counts.items()},
                    "headlines": result["headlines"],
                    "skipped": result["skipped"],
                    "failures": result["failures"],
                })

        if not legacy:
            for path in write_matrix(root, cells):
                print(f"\n  Wrote {path}")
            report.banner("SUITE DONE")
            print(f"\n  {len(cells)} cell(s) under {root}")

    return 1 if (any_failure and cli.strict) else 0
