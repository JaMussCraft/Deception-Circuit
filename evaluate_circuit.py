"""
evaluate_circuit.py — evaluate a node-pruned circuit saved by train.py.

`train.py` discovers a circuit and evaluates it once, in-process, immediately
after pruning. Afterwards the circuit lives only in `<run_dir>/active_nodes.json`
under the "masks" key. This rebuilds it from there and asks three questions:

  1. sanity    does the saved mask reproduce the numbers the run reported?
  2. knockout  is the circuit *necessary* — does removing it stop the behaviour,
               and what does that cost on unrelated text?
  3. null      does a size-matched random circuit do just as well?

Usage:

    # everything, interchange ablation (the training-time reference)
    python evaluate_circuit.py outputs/llama-8b-instruct_std/nls0.7_noedge_260721-151636

    # reproduce the in-run numbers only
    python evaluate_circuit.py <run_dir> --evals sanity

    # check the conclusions against ablation-scheme sensitivity
    python evaluate_circuit.py <run_dir> --ablation mean

    # validate the circuit, the random set and the plan without a GPU
    python evaluate_circuit.py <run_dir> --dry-run

Results land in `<run_dir>/evaluations/<ablation>/`.
"""

import argparse
import json
import os
import sys
import time

from evaluation import get_evaluation, list_evaluations
from evaluation import report
from evaluation.ablation import ABLATION_SCHEMES
from evaluation.context import (SCHEMA_VERSION, baseline_numbers, build_context,
                                reference_numbers)
from evaluation.masks import ALGORITHM_VERSION, count_masks, save_packed_masks
from run_io import tee_stdout_stderr

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
        description="Evaluate a node-pruned circuit from a train.py run directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("run_dir", help="Run directory holding config.json and active_nodes.json.")

    g = p.add_argument_group("what to run")
    g.add_argument("--evals", nargs="+", default=list_evaluations(),
                   choices=list_evaluations(), help="Which evaluations to run.")
    g.add_argument("--ablation", default="interchange", choices=list(ABLATION_SCHEMES),
                   help="What fills an ablated node. Only 'interchange' can "
                        "reproduce the in-run numbers.")
    g.add_argument("--mean-source", default="pooled", choices=["pooled", "clean", "corrupt"],
                   help="Which prompt stream(s) enter the mean bank under --ablation mean.")
    g.add_argument("--knockout-granularity", default="finest", choices=["finest", "all"],
                   help="'finest' complements only the fine gates and leaves the "
                        "coarse ones open; 'all' complements every granularity.")
    g.add_argument("--dry-run", action="store_true",
                   help="Validate the circuit and the random set and estimate the "
                        "runtime, without loading a model or touching CUDA.")

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
                   help="Default: <run_dir>/evaluations.")
    g.add_argument("--verify", action=argparse.BooleanOptionalAction, default=True,
                   help="Round-trip the loaded masks against extract_node_masks.")
    g.add_argument("--strict", action="store_true",
                   help="Exit non-zero if any verification check fails.")
    return p


def resolve_cli(cli):
    if cli.device is None:
        import torch
        cli.device = "cuda" if torch.cuda.is_available() else "cpu"
    if cli.output_dir is None:
        cli.output_dir = os.path.join(cli.run_dir, "evaluations")
    if cli.ref_cache_device is None:
        cli.ref_cache_device = cli.device
    cli.evals = list(dict.fromkeys(cli.evals))
    return cli


# ==============================================================================
# DRY RUN
# ==============================================================================

def estimate_runtime(ctx) -> dict:
    cli = ctx.cli
    n_test = ctx.args.test_samples or 1000
    test_pass = SEC_PER_1000_TEST * n_test / 1000.0
    n_random = len(ctx.random_masks)

    stages = []
    if "sanity" in cli.evals:
        # full / discovered / repo-path / empty, plus the reference pass
        stages.append(("eval 1 (sanity)", 5 * test_pass))
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
    if cli.ablation == "mean":
        stages.append(("mean bank", 2 * test_pass))
    stages.insert(0, ("model load", SEC_MODEL_LOAD))

    total = sum(s for _, s in stages)
    return {"stages": stages, "total_seconds": total}


def dry_run(ctx) -> int:
    cli = ctx.cli
    report.banner("DRY RUN — no model loaded, no CUDA touched")
    report.kv("run dir", ctx.run_dir)
    report.kv("model / task", f"{ctx.args.model} / {ctx.args.task}")
    report.kv("ablation", cli.ablation)
    report.kv("evaluations", ", ".join(cli.evals))
    report.kv("output dir", ctx.out_dir)

    report.ablation_banner(cli.ablation)
    report.counts_table(ctx.counts, ctx.geometry)
    report.per_layer_table(ctx.counts)

    report.banner("KNOCKOUT (%s)" % cli.knockout_granularity)
    knock = count_masks(ctx.knockout_masks)
    ablated = sum(ctx.counts[k]["active"] for k in ("attention_neurons", "mlp_hidden",
                                                    "mlp_output") if k in ctx.counts)
    print(f"\n  complement verified: knockout ∧ circuit = 0, knockout ∪ circuit = 1")
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
    report.per_layer_table(count_masks(ctx.random_masks[0]),
                           title="PER-LAYER COUNTS — random circuit "
                                 f"{ctx.random_indices[0]} (must match above)")

    est = estimate_runtime(ctx)
    report.banner("ESTIMATED RUNTIME (1x A100, very rough)")
    print()
    for label, seconds in est["stages"]:
        print(f"  {label:<40} {seconds / 60:>8.1f} min")
    print("  " + "-" * 50)
    print(f"  {'TOTAL':<40} {est['total_seconds'] / 60:>8.1f} min")
    print("\n  Nothing was written. Drop --dry-run to run it.")
    return 0


# ==============================================================================
# RUN
# ==============================================================================

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


def write_json(path, payload):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    return path


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


def run_evaluations(ctx) -> int:
    cli = ctx.cli
    report.banner("CIRCUIT EVALUATION")
    report.kv("run dir", ctx.run_dir)
    report.kv("model / task", f"{ctx.args.model} / {ctx.args.task}")
    report.kv("device", cli.device)
    report.kv("reference", cli.reference)
    report.kv("evaluations", ", ".join(cli.evals))
    report.kv("test samples", len(ctx.test_loader.dataset))
    report.kv("output dir", ctx.out_dir)

    report.ablation_banner(cli.ablation)
    report.counts_table(ctx.counts, ctx.geometry)
    report.per_layer_table(ctx.counts)

    summary = circuit_summary(ctx)
    summary["verification"] = {"masks_roundtrip": bool(cli.verify)}
    headlines = {}

    for name in cli.evals:
        evaluation = get_evaluation(name)
        ok, reason = ctx.requires_ok(evaluation)
        if not ok:
            print(f"\n  Skipping '{name}': {reason}")
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
    write_json(os.path.join(ctx.out_dir, "summary.json"), summary)
    update_index(ctx, headlines)

    report.banner("DONE")
    print(f"\n  Results in {ctx.out_dir}")
    if ctx.failures:
        print(f"\n  {len(ctx.failures)} check(s) FAILED:")
        for f in ctx.failures:
            print(f"    - {f}")
        if cli.strict:
            return 1
    return 0


def main():
    cli = resolve_cli(build_parser().parse_args())
    ctx = build_context(cli)

    if cli.dry_run:
        return dry_run(ctx)

    os.makedirs(ctx.plots_dir, exist_ok=True)
    log_path = os.path.join(ctx.out_dir, "evaluation.log")
    with tee_stdout_stderr(log_path, mode="a"):
        print("\n" + "#" * report.W)
        print(f"# {time.strftime('%Y-%m-%d %H:%M:%S')}  "
              f"{' '.join(sys.argv)}")
        print("#" * report.W)
        return run_evaluations(ctx)


if __name__ == "__main__":
    sys.exit(main())
