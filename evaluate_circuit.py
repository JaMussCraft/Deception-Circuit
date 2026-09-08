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
  5. benchmarks  does knocking it out stop the model being deceptive on
               external benchmarks it was never pruned on? (opt in with
               --evals benchmarks; generates for hours and calls paid judges)

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

from evaluation import default_evaluations, list_evaluations
from evaluation import report
from evaluation import suite
from evaluation.ablation import ABLATION_SCHEMES
from evaluation.benchmarks import (DEFAULT_BENCHMARKS, GROUPS, expand,
                                   list_benchmarks, list_choices, required_keys)
from evaluation.context import build_session
from evaluation.masks import count_masks

# Rough costs, calibrated on 1x A100 with Llama-3.1-8B-Instruct and 90-token STD
# prompts. Only used by --dry-run's estimate, which is there to catch "this will
# not fit in the walltime", not to be accurate.
SEC_MODEL_LOAD = 200.0
SEC_PER_1000_TEST = 55.0
SEC_PER_WIKITEXT_CONFIG = 13.0
#: Seconds per generated token per row at --benchmark-gen-batch-size 8, dual
#: stream with the KV cache. EVAL 5 is dominated by this and nothing else.
SEC_PER_GEN_TOKEN_ROW = 0.0075


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
    g.add_argument("--evals", nargs="+", default=default_evaluations(),
                   choices=list_evaluations(),
                   help="Which evaluations to run. 'benchmarks' (EVAL 5) is a "
                        "choice but not a default: it generates for hours and "
                        "calls paid judge APIs, so it is asked for by name.")
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

    g = p.add_argument_group("deception benchmarks (EVAL 5)")
    g.add_argument("--benchmarks", nargs="+", default=list(DEFAULT_BENCHMARKS),
                   choices=list_choices(), metavar="NAME",
                   help="Datasets to run: %s. The group names %s expand to "
                        "their members."
                        % (", ".join(list_benchmarks()),
                           ", ".join(sorted(GROUPS))))
    g.add_argument("--benchmark-repo-root", default=None,
                   help="Directory holding the sibling benchmark checkouts "
                        "(mask/, liars-bench/). Default: this repo's parent.")
    g.add_argument("--benchmark-n-per-dataset", type=int, default=100,
                   help="Items per dataset the full model must be judged "
                        "deceptive on. Screening stops as soon as this many "
                        "are found.")
    g.add_argument("--benchmark-new-tokens", type=int, default=512,
                   help="Greedy tokens per generation. A benchmark whose "
                        "answer sits behind a CoT scaffold overrides this "
                        "(sandbagging asks for 1024).")
    g.add_argument("--benchmark-belief-tokens", type=int, default=128,
                   help="Greedy tokens per belief probe. Probes are "
                        "closed-form (a letter, a short claim), so spending "
                        "the full generation budget on them multiplies the "
                        "belief pass for nothing.")
    g.add_argument("--benchmark-gen-batch-size", type=int, default=8,
                   help="Rows per generation bucket. The plan's flag list says "
                        "32; its own A40 sizing paragraph assumes 8, and 8 is "
                        "what the arithmetic supports -- two KV caches at "
                        "256 KB/token/row plus ~32 GB of weights under "
                        "--reference separate leaves ~12 GB, which 32 rows x "
                        "1500 tokens exhausts.")
    g.add_argument("--benchmark-ref-pool", default="honest",
                   choices=["honest", "deceptive", "pooled"],
                   help="Which pool the corrupted stream is drawn from under "
                        "--ablation interchange.")
    g.add_argument("--benchmark-n-random", type=int, default=5,
                   help="Size-matched random circuits in EVAL 5's null. Far "
                        "below --n-random on purpose: generation is orders of "
                        "magnitude more expensive than a single-position "
                        "readout.")
    g.add_argument("--no-kv-cache", action="store_true",
                   help="Debug: force the O(n^2) full-sequence re-forward "
                        "instead of the dual-stream KV cache.")
    g.add_argument("--judge-dry-run", action="store_true",
                   help="Print one judge prompt per selected benchmark and "
                        "exit. No model, no CUDA, no API key, no spend.")
    g.add_argument("--judge-concurrency", type=int, default=8,
                   help="In-flight judge calls.")
    g.add_argument("--mask-judge-model", default=None,
                   help="Override MASK's binary judge (default: the model "
                        "mask/mask/evaluate.py uses).")
    g.add_argument("--mask-numeric-judge-model", default=None,
                   help="Override MASK's numerical-archetype judge.")
    g.add_argument("--lb-judge-model", default=None,
                   help="Override Liars' Bench's main judge.")
    g.add_argument("--lb-harm-judge-model", default=None,
                   help="Override Liars' Bench's harm-pressure claim judge.")
    # The adapters already read these three through getattr(cli, ...), which
    # returns None for an undefined flag -- so before they were declared here,
    # passing one was a silent no-op rather than an error.
    g.add_argument("--benchmark-pool-size", type=int, default=None,
                   help="Cap each condition pool at N items per benchmark, for "
                        "cheap smoke runs. The sandbagging deceptive pool is "
                        "drawn round-robin across WMDP bio/chem/cyber, so a "
                        "small cap stays topic-balanced.")
    g.add_argument("--benchmark-belief-model", default=None,
                   help="Model whose MASK metrics run supplies the belief "
                        "reference. Defaults to the model under evaluation; "
                        "set it explicitly to accept a deliberate mismatch.")
    g.add_argument("--lb-belief-templates", type=int, default=None,
                   help="Cap the number of Liars' Bench closed-form belief "
                        "probes per item (minimum 2, since belief is only "
                        "believed when the probes agree).")

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
    if "benchmarks" in cli.evals:
        stages.extend(benchmark_stages(cli))
    if cli.ablation == "mean":
        stages.append(("mean bank", 2 * test_pass))

    stages = [(label, seconds * n_cells) for label, seconds in stages]
    stages.insert(0, ("model load", SEC_MODEL_LOAD))
    return {"stages": stages, "total_seconds": sum(s for _, s in stages),
            "cells": n_cells}


def benchmark_stages(cli):
    """EVAL 5's rough cost, per dataset: the screen plus one pass per config.

    The screen's cost is a *worst case* — it walks the candidate pool until it
    finds `--benchmark-n-per-dataset` items the full model is deceptive on, and
    stops early when deception is common. There is no way to know which without
    generating, so this assumes the pool is exhausted and says so.
    """
    from evaluation.benchmarks import get_benchmark

    n = cli.benchmark_n_per_dataset
    n_configs = 4 + cli.benchmark_n_random          # full/knockout/circuit/empty
    stages = []
    for dataset in expand(cli.benchmarks):
        tokens = get_benchmark(dataset).new_tokens or cli.benchmark_new_tokens
        per_pass = n * tokens * SEC_PER_GEN_TOKEN_ROW
        # screen + reference pool, then every configuration but `full` (which
        # reuses the screen's own tokens rather than generating again).
        stages.append((f"eval 5 {dataset}: screen + reference", 2 * per_pass))
        stages.append((f"eval 5 {dataset}: {n_configs - 1} ablated configs",
                       (n_configs - 1) * per_pass))
    return stages


def benchmark_plan(cli) -> None:
    """The --dry-run benchmark section: what would run, and what it needs."""
    from evaluation.benchmarks import get_benchmark

    datasets = expand(cli.benchmarks)
    report.banner(f"DECEPTION BENCHMARKS (EVAL 5) — {len(datasets)} dataset(s)")
    print()
    print(f"  {'dataset':<34} {'condition':<9} {'tokens':>6} {'pool':>8}  judge")
    print("  " + "-" * 100)
    thin = []
    for dataset in datasets:
        bench = get_benchmark(dataset)
        spec = bench.judge_spec()
        # The candidate pool, loaded for real: prompts are model-independent,
        # so this needs no GPU and no key. A dataset whose checkout is missing
        # reports that rather than taking the whole dry run down with it --
        # the point of --dry-run is to find out what is wrong, not to stop at
        # the first thing.
        try:
            pool = len(bench.load(None, cli))
        except Exception as exc:                           # noqa: BLE001
            pool = f"! {type(exc).__name__}"
        else:
            if pool < cli.benchmark_n_per_dataset:
                thin.append((dataset, pool))
        print(f"  {dataset:<34} {bench.condition_kind:<9} "
              f"{bench.new_tokens or cli.benchmark_new_tokens:>6} {pool:>8}  "
              + (f"{spec['provider']}/{spec['model']}" if spec
                 else "local grader, no API call"))
    if thin:
        print()
        for dataset, pool in thin:
            print(f"  !! {dataset}: only {pool} candidates for a target of "
                  f"{cli.benchmark_n_per_dataset}, and the screen keeps only "
                  f"the ones\n     the full model is deceptive on — so this "
                  f"cell will be thinner still.")

    keys = required_keys(cli.benchmarks)
    print()
    if keys:
        for key, users in sorted(keys.items()):
            present = "set" if os.environ.get(key) else "NOT SET"
            print(f"  {key:<22} {present:<8} needed by {', '.join(users)}")
    else:
        print("  No API key needed: every selected dataset grades locally.")

    print(f"\n  Target {cli.benchmark_n_per_dataset} items per dataset, drawn "
          f"by screening the candidate pool\n  in load order until that many "
          f"come back judged deceptive under the FULL model. The pool\n  "
          f"column is therefore an upper bound: the exact post-screen count "
          f"and the\n  judge-call total are only known after the generation "
          f"pass.")
    print(f"\n  Corrupt reference: --benchmark-ref-pool "
          f"{cli.benchmark_ref_pool}. Random null: "
          f"{cli.benchmark_n_random} circuit(s).")


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

    if "benchmarks" in cli.evals:
        benchmark_plan(cli)

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

def check_benchmark_keys(cli) -> None:
    """Fail before the model loads if a selected benchmark cannot be judged.

    EVAL 5 judges inline, so the alternative is discovering a missing key after
    an hour of generation with nothing labelled and nothing to resume from. The
    check is deliberately here rather than in the evaluation: it has to run
    before `build_session`, which loads ~32 GB of weights.
    """
    missing = {key: users for key, users in required_keys(cli.benchmarks).items()
               if not os.environ.get(key)}
    if not missing:
        return
    lines = ["EVAL 5 needs API key(s) that are not set:"]
    for key, users in sorted(missing.items()):
        lines.append(f"  {key}  — required by {', '.join(users)}")
    lines.append("")
    lines.append("Set them, or drop those datasets with --benchmarks. "
                 "'--benchmarks sandbagging'")
    lines.append("grades locally and needs no key at all.")
    raise SystemExit("\n".join(lines))


def main():
    cli = resolve_cli(build_parser().parse_args())
    if "benchmarks" in cli.evals and not cli.judge_dry_run:
        # Before build_session: a missing key must cost zero GPU time.
        check_benchmark_keys(cli)
    session = build_session(cli)
    if cli.dry_run:
        return dry_run(session)
    if cli.judge_dry_run:
        from evaluation.benchmark_eval import judge_dry_run
        return judge_dry_run(session)
    return suite.run(session)


if __name__ == "__main__":
    sys.exit(main())
