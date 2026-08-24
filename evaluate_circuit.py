"""
evaluate_circuit.py — evaluate node-pruned circuits saved by train.py.

`train.py` discovers a circuit and evaluates it once, in-process, immediately
after pruning. Afterwards the circuit lives only in `<run_dir>/active_nodes.json`
under the "masks" key. This rebuilds it from there and asks:

  1. sanity    does the saved mask reproduce the numbers the run reported?
  2. knockout  is the circuit *necessary* — does removing it stop the behaviour,
               what does that cost on unrelated text, and does an honest
               instruction do the same thing the knockout does?
  3. null      does a size-matched random circuit do just as well?
  4. pressure  does the behaviour survive dropping the pressure clause?

Circuits and tasks are independent: any expression over saved circuits can be
evaluated against any number of tasks, in one process with one model load.

Usage:

    # everything, interchange ablation (the training-time reference)
    python evaluate_circuit.py outputs/llama-8b-instruct_std/nls0.7_noedge_260721-151636

    # reproduce the in-run numbers only
    python evaluate_circuit.py <run_dir> --evals sanity

    # the cross-task matrix: three circuits x three tasks
    python evaluate_circuit.py \
        --circuit far=<far_run> --circuit sdr=<sdr_run> --circuit ser=<ser_run> \
        --expr far --expr sdr --expr ser \
        --task-from <far_run> --task-from <sdr_run> --task-from <ser_run>

    # the specificity-asymmetry family, leaf and head granularity
    python evaluate_circuit.py --circuit far=... --circuit sdr=... --circuit ser=... \
        --xor far,sdr,ser --task-from <far_run>

    # validate every circuit, the algebra, the cell grid and the plan, no GPU
    python evaluate_circuit.py <run_dir> --dry-run

A single atomic circuit on its own task writes to `<run_dir>/evaluations/<ablation>/`
as it always has; anything else writes a suite under `outputs/_suites/<name>/`.
"""

import argparse
import os
import sys

from evaluation import list_evaluations
from evaluation import report
from evaluation import suite
from evaluation.ablation import ABLATION_SCHEMES
from evaluation.context import build_session
from evaluation.masks import count_masks

# Rough costs, calibrated on 1x A100 with Llama-3.1-8B-Instruct and 90-token STD
# prompts. Only used by --dry-run's estimate, which is there to catch "this will
# not fit in the walltime", not to be accurate.
SEC_MODEL_LOAD = 200.0
SEC_PER_1000_TEST = 55.0
SEC_PER_WIKITEXT_CONFIG = 13.0


# ==============================================================================
# CLI
# ==============================================================================

def build_parser():
    p = argparse.ArgumentParser(
        description="Evaluate node-pruned circuits from train.py run directories.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("run_dir", nargs="?", default=None,
                   help="Run directory holding config.json and active_nodes.json. "
                        "Equivalent to --circuit self=<run_dir>.")

    g = p.add_argument_group("circuits")
    g.add_argument("--circuit", action="append", metavar="NAME=RUN_DIR",
                   help="Bind a saved circuit to a name that expressions can "
                        "refer to. Repeatable.")
    g.add_argument("--expr", action="append", metavar="[LABEL=]EXPR",
                   help="A circuit expression over the bound names: '|' union, "
                        "'&' intersection, '\\' (or '-') difference, parentheses. "
                        "Repeatable. Default: every bound circuit on its own.")
    g.add_argument("--xor", default=None, metavar="A,B,C",
                   help="Shorthand for the exclusive family A\\B\\C, B\\A\\C, C\\A\\B.")
    g.add_argument("--all-pairs-delta", action="store_true",
                   help="Shorthand for every ordered difference X\\Y.")
    g.add_argument("--compose-granularity", default="both",
                   choices=["leaf", "head", "both"],
                   help="What set membership means for composed circuits: 'leaf' "
                        "is the finest gates, 'head' is heads + MLP blocks. "
                        "'both' evaluates each composition twice, as separate cells.")

    g = p.add_argument_group("tasks")
    g.add_argument("--task", action="append", metavar="NAME",
                   help="Evaluate on this registered task, with its default "
                        "hyperparameters and the bound circuits' model/data-dir. "
                        "Repeatable.")
    g.add_argument("--task-from", action="append", metavar="RUN_DIR",
                   help="Evaluate on the task this run was trained on, inheriting "
                        "its dataset args. Repeatable. Default: each bound "
                        "circuit's own task.")

    g = p.add_argument_group("what to run")
    g.add_argument("--evals", nargs="+", default=list_evaluations(),
                   choices=list_evaluations(), help="Which evaluations to run.")
    g.add_argument("--ablation", default="interchange", choices=list(ABLATION_SCHEMES),
                   help="What fills an ablated node. Only 'interchange' can "
                        "reproduce the in-run numbers.")
    g.add_argument("--mean-source", default="pooled", choices=["pooled", "clean", "corrupt"],
                   help="Which prompt stream(s) enter the mean bank under --ablation mean.")
    g.add_argument("--sanity-granularity", default="all", choices=["all", "coarse"],
                   help="Which gates the sanity eval loads. 'all' is the "
                        "discovered circuit; 'coarse' loads only the block and "
                        "head gates and holds every fine gate (attention "
                        "neurons, MLP hidden/output) open.")
    g.add_argument("--knockout-granularity", default="finest", choices=["finest", "all"],
                   help="'finest' complements only the fine gates and leaves the "
                        "coarse ones open; 'all' complements every granularity.")
    g.add_argument("--gen-examples", type=int, default=3,
                   help="Open-generation examples on wikitext in eval 2 (0 disables).")
    g.add_argument("--gen-new-tokens", type=int, default=48,
                   help="Greedy tokens per generation example.")
    g.add_argument("--dry-run", action="store_true",
                   help="Validate every circuit, the algebra, the random set and "
                        "the cell grid, and estimate the runtime, without "
                        "loading a model or touching CUDA.")

    g = p.add_argument_group("random-circuit null")
    g.add_argument("--n-random", type=int, default=50,
                   help="Number of size-matched random circuits.")
    g.add_argument("--null-seed", type=int, default=0,
                   help="Base seed; sample k draws from (seed, k).")
    g.add_argument("--null-alloc", default="uniform", choices=["uniform", "perhead"],
                   help="'perhead' also preserves the per-head neuron count multiset.")
    g.add_argument("--null-start", type=int, default=0,
                   help="First sample index (shard an sbatch array with this).")
    g.add_argument("--null-count", type=int, default=None,
                   help="Samples in this shard (default: --n-random).")
    g.add_argument("--save-null-masks", action="store_true",
                   help="Also write the random circuits as a packed npz.")

    g = p.add_argument_group("wikitext reference stream")
    g.add_argument("--skip-wikitext", action="store_true")
    g.add_argument("--wikitext-blocks", type=int, default=64)
    g.add_argument("--wikitext-block-size", type=int, default=512)
    g.add_argument("--wikitext-batch-size", type=int, default=4)
    g.add_argument("--wikitext-seed", type=int, default=0,
                   help="Seed for the fixed block derangement (reused by every "
                        "configuration, so no pairing noise enters the null).")

    g = p.add_argument_group("models & data")
    g.add_argument("--reference", default="separate", choices=["separate", "shared"],
                   help="'shared' drops the second copy of the weights and uses the "
                        "prunable model's ungated single-stream path as the "
                        "reference (exact, and ~15 GB cheaper).")
    g.add_argument("--eval-batch-size", type=int, default=32,
                   help="Batch size for everything except the sanity eval, which "
                        "stays pinned to the run's own batch size.")
    g.add_argument("--test-samples", type=int, default=None,
                   help="Shrink the task test set.")
    g.add_argument("--data-dir", default=None, help="Override the recorded --data-dir.")
    g.add_argument("--std-variant", default=None, choices=["azaria", "neutral"],
                   help="Which STD dataset the run was trained on. Runs predating "
                        "the config.json fix do not record it.")
    g.add_argument("--hf-token", default=None)
    g.add_argument("--device", default=None, help="Default: cuda when available.")
    g.add_argument("--ref-cache-device", default=None, choices=["cuda", "cpu"],
                   help="Where to keep the [N, vocab] reference-logit cache.")

    g = p.add_argument_group("output & checking")
    g.add_argument("--output-dir", default=None,
                   help="Default: <run_dir>/evaluations for a single circuit on "
                        "its own task, otherwise outputs/_suites/<suite-name>.")
    g.add_argument("--suite-name", default=None,
                   help="Name the suite directory (default: a timestamp slug). "
                        "Passing it forces the suite layout.")
    g.add_argument("--verify", action=argparse.BooleanOptionalAction, default=True,
                   help="Round-trip the loaded masks against extract_node_masks.")
    g.add_argument("--strict", action="store_true",
                   help="Exit non-zero if any verification check fails.")
    return p


def resolve_cli(cli):
    if cli.device is None:
        import torch
        cli.device = "cuda" if torch.cuda.is_available() else "cpu"
    if cli.ref_cache_device is None:
        cli.ref_cache_device = cli.device
    cli.evals = list(dict.fromkeys(cli.evals))

    cli.legacy = suite.is_legacy(cli)
    if cli.legacy and cli.output_dir is None:
        cli.output_dir = os.path.join(cli.run_dir, "evaluations")
    if not cli.legacy and not cli.suite_name:
        cli.suite_name = suite.default_suite_name()
    return cli


# ==============================================================================
# DRY RUN
# ==============================================================================

def estimate_runtime(session, ctx) -> dict:
    cli = session.cli
    n_test = ctx.args.test_samples or 1000
    test_pass = SEC_PER_1000_TEST * n_test / 1000.0
    n_random = len(ctx.random_masks)
    n_cells = len(session.circuits) * len(session.tasks)

    # Sanity only runs where there is a run whose results.json to reproduce,
    # i.e. an atomic circuit on its home task; every other eval runs everywhere.
    n_sanity = sum(1 for c in session.circuits for t in session.tasks
                   if c.home_run_dir and c.home_run_dir == t.home_run_dir)

    stages = []
    if "sanity" in cli.evals and n_sanity:
        # full / discovered / repo-path / empty, plus the reference pass
        stages.append(("eval 1 (sanity)", 5 * test_pass * n_sanity / max(n_cells, 1)))
    if "null" in cli.evals:
        stages.append((f"eval 3 (null, {n_random} circuits)", n_random * test_pass))
    if "knockout" in cli.evals:
        stages.append(("eval 2 (task knockout)", 2 * test_pass))
        if not cli.skip_wikitext:
            n_configs = 2 + n_random
            stages.append((f"eval 2 (wikitext, {n_configs} configs)",
                           n_configs * SEC_PER_WIKITEXT_CONFIG *
                           (cli.wikitext_blocks / 64.0) *
                           (cli.wikitext_block_size / 512.0)))
        stages.append(("eval 2 (honest variant)", 3 * test_pass))
        if cli.gen_examples:
            stages.append((f"eval 2 ({cli.gen_examples} generation examples)",
                           3 * cli.gen_examples * cli.gen_new_tokens * 0.35))
    if "pressure" in cli.evals:
        stages.append(("eval 4 (pressure clause)", 6 * test_pass))
    if cli.ablation == "mean":
        stages.append(("mean bank", 2 * test_pass))

    stages = [(label, seconds * n_cells) for label, seconds in stages]
    stages.insert(0, ("model load", SEC_MODEL_LOAD))
    return {"stages": stages, "total_seconds": sum(s for _, s in stages),
            "cells": n_cells}


def dry_run(session) -> int:
    cli = session.cli
    report.banner("DRY RUN — no model loaded, no CUDA touched")
    report.kv("model", session.base_args.model)
    report.kv("ablation", cli.ablation)
    report.kv("evaluations", ", ".join(cli.evals))
    report.kv("layout", "legacy (<run_dir>/evaluations)" if cli.legacy
              else f"suite ({suite.suite_root(cli, session.base_run_dir)})")

    report.ablation_banner(cli.ablation)

    report.banner("CIRCUITS")
    print()
    for spec in session.circuits:
        fine = sum(spec.counts[k]["active"] for k in
                   ("attention_neurons", "mlp_hidden", "mlp_output")
                   if k in spec.counts)
        source = spec.expr or (spec.home_run_dir or "")
        print(f"  {spec.label:<34} {spec.kind:<7} {fine:>10,} fine units   {source}")
        warning = _emptiness(spec)
        if warning:
            print(warning)

    report.banner("TASKS")
    print()
    for spec in session.tasks:
        print(f"  {spec.label:<20} task={spec.name:<8} "
              f"n={spec.args.test_samples}  data={spec.args.data_dir}  "
              f"{spec.home_run_dir or '(defaults)'}")

    report.banner(f"CELL GRID ({len(session.circuits)} circuits x "
                  f"{len(session.tasks)} tasks)")
    print()
    for task_spec in session.tasks:
        for circuit_spec in session.circuits:
            root = (cli.output_dir if cli.legacy
                    else suite.suite_root(cli, session.base_run_dir))
            print("  " + suite.cell_dir(root, cli.legacy, circuit_spec, task_spec,
                                        cli.ablation))

    # Everything below is per-circuit; report it for the first cell, which is
    # what the single-circuit invocation is.
    ctx = session.context_for(session.circuits[0], session.tasks[0], "")
    report.counts_table(ctx.counts, ctx.geometry)
    report.per_layer_table(ctx.counts)

    if ctx.sanity_granularity == "coarse":
        report.counts_table(ctx.sanity_counts, ctx.geometry,
                            title="SANITY CIRCUIT — COARSE GATES ONLY")

    report.banner("KNOCKOUT (%s)" % cli.knockout_granularity)
    knock = count_masks(ctx.knockout_masks)
    ablated = sum(ctx.counts[k]["active"] for k in ("attention_neurons", "mlp_hidden",
                                                    "mlp_output") if k in ctx.counts)
    print("\n  complement verified: knockout ∧ circuit = 0, knockout ∪ circuit = 1")
    print(f"  fine units ablated: {ablated:,}")
    for key in ("attention_neurons", "mlp_hidden", "mlp_output"):
        if key in knock:
            print(f"    {key:<20} {knock[key]['active']:>10,} live "
                  f"({knock[key]['active'] / knock[key]['total'] * 100:.2f}%)")

    report.banner(f"RANDOM CIRCUITS ({len(ctx.random_masks)} sampled, "
                  f"seed {cli.null_seed}, alloc {cli.null_alloc})")
    print("\n  hierarchy validated on every sample "
          "(no empty drawn head, no orphaned neuron)")
    target = ctx.counts
    mismatches = [i for i, m in zip(ctx.random_indices, ctx.random_masks)
                  if count_masks(m) != target]
    if mismatches:
        print(f"  !! {len(mismatches)} samples are NOT size-matched: {mismatches[:10]}")
    else:
        print(f"  all {len(ctx.random_masks)} samples size-matched to the "
              f"discovered circuit at every granularity and layer")
    if ctx.random_masks:
        report.per_layer_table(count_masks(ctx.random_masks[0]),
                               title="PER-LAYER COUNTS — random circuit "
                                     f"{ctx.random_indices[0]} (must match above)")

    est = estimate_runtime(session, ctx)
    report.banner("ESTIMATED RUNTIME (1x A100, very rough)")
    print()
    for label, seconds in est["stages"]:
        print(f"  {label:<40} {seconds / 60:>8.1f} min")
    print("  " + "-" * 50)
    print(f"  {'TOTAL':<40} {est['total_seconds'] / 60:>8.1f} min "
          f"({est['cells']} cell(s))")
    print("\n  Nothing was written. Drop --dry-run to run it.")
    return 0


def _emptiness(spec) -> str:
    from evaluation.algebra import emptiness_warning
    if spec.is_atomic:
        return ""
    return emptiness_warning(spec.label, spec.masks)


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    cli = resolve_cli(build_parser().parse_args())
    session = build_session(cli)
    if cli.dry_run:
        return dry_run(session)
    return suite.run(session)


if __name__ == "__main__":
    sys.exit(main())
