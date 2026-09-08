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
from evaluation.benchmark_eval import SCREEN_MAX_FACTOR
from evaluation.benchmarks.base import DECEPTIVE
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
#: stream with the KV cache. Measured on an A40 in job 21880374 (the sandbagging
#: smoke test): one 8-row bucket decoded 1024 tokens in 126 s, i.e. 6.95 it/s
#: for the bucket. Per row that is 126 / (1024 * 8).
SEC_PER_GEN_TOKEN_ROW = 126.0 / (1024 * 8)

#: Seconds per scored token per row for the coherence forward. Also measured in
#: job 21880374: 2.91 s for one 8-row batch over ~1220 tokens. It is a single
#: teacher-forced forward rather than one per token, hence ~50x cheaper than
#: decoding -- but not free, and there is one per configuration, so leaving it
#: out understated a 9-config dataset by several minutes.
SEC_PER_COHERENCE_TOKEN_ROW = 2.91 / (1220 * 8)


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
    g.add_argument("--benchmark-coherence-batch-size", type=int, default=None,
                   help="Rows per coherence forward (default: a quarter of "
                        "--benchmark-gen-batch-size, min 1). Decoupled because "
                        "it is the tightest allocation in EVAL 5: the forward "
                        "materialises a float32 log_softmax over a 128k vocab, "
                        "so at batch 8 sandbagging's longest prompt needs "
                        "~15.6 GB on top of ~32 GB of weights under "
                        "--reference separate -- 47.6 of an A40's 48 GB.")
    g.add_argument("--benchmark-ref-pool", default="honest",
                   choices=["honest", "deceptive", "pooled"],
                   help="Which pool the corrupted stream is drawn from under "
                        "--ablation interchange.")
    g.add_argument("--benchmark-screen-seed", type=int, default=0,
                   help="Seed for the candidate shuffle the screen walks. "
                        "Screening in load order would make the evaluation set "
                        "a property of how the source file is sorted.")
    g.add_argument("--benchmark-screen-budget", type=int, default=0,
                   help="Stop screening after this many candidates even if the "
                        "reference pool is still short (0 = walk the pool, "
                        "which is what the plan asks for). A bound worth "
                        "setting on the large Liars' Bench scenarios, where "
                        "filling the honest bank can cost hours; a pool cut "
                        "short is reported, never silent.")
    g.add_argument("--benchmark-n-random", type=int, default=5,
                   help="Size-matched random circuits in EVAL 5's null. Far "
                        "below --n-random on purpose: generation is orders of "
                        "magnitude more expensive than a single-position "
                        "readout.")
    g.add_argument("--benchmark-screen-cache", default=None,
                   help="Directory holding cached screening passes (default: "
                        "outputs/_screens). The screen runs under all gates "
                        "open, so it does not depend on the circuit and never "
                        "has to be repaid -- at n=100 it is ~79%% of EVAL 5's "
                        "ceiling. The GPU is part of the cache key: `full` "
                        "reuses the screen's own tokens, so a screen made on "
                        "another device would put 'which GPU' inside the very "
                        "delta this evaluation measures. Cached screens are "
                        "pickles, loaded with weights_only=False, so point "
                        "this at a directory you control rather than at a "
                        "group-writable scratch space.")
    g.add_argument("--benchmark-refresh-screen", action="store_true",
                   help="Screen even if a cached screen matches, and overwrite "
                        "it.")
    g.add_argument("--no-benchmark-screen-cache", action="store_true",
                   help="Neither read nor write the screen cache.")
    g.add_argument("--no-kv-cache", action="store_true",
                   help="Debug: force the O(n^2) full-sequence re-forward "
                        "instead of the dual-stream KV cache.")
    g.add_argument("--judge-dry-run", action="store_true",
                   help="Print one judge prompt per selected benchmark and "
                        "exit. No model, no CUDA, no API key, no spend.")
    g.add_argument("--skip-judge-check", action="store_true",
                   help="Do not spend one judge call per judge verifying the "
                        "account works before the model loads. The check "
                        "exists because a key can be set and still be out of "
                        "credits, which is otherwise discovered an hour into "
                        "generation.")
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
    # The adapters read the first two through getattr(cli, ...), which returns
    # None for an undefined flag -- so before they were declared here, passing
    # one was a silent no-op rather than an error.
    #
    # --benchmark-belief-model is NOT one of them: `benchmarks/__init__.py`
    # constructs MaskSplit(split) without it, so `belief_model` is always
    # DEFAULT_BELIEF_MODEL and the flag parses and does nothing. Left declared
    # and documented as inert rather than quietly removed, since the MASK
    # metrics it would select are a real thing a reader may come looking for.
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
        stages.extend(benchmark_stages(cli, session.base_args.model))
    if cli.ablation == "mean":
        stages.append(("mean bank", 2 * test_pass))

    stages = scale_stages(stages, n_cells)
    stages.insert(0, ("model load", SEC_MODEL_LOAD, SEC_MODEL_LOAD))
    return {"stages": stages,
            "total_seconds": sum(s[1] for s in stages),
            "total_seconds_floor": sum(s[2] for s in stages),
            "cells": n_cells}


def scale_stages(stages, n_cells):
    """Multiply each stage by the cell count — except the ones that run once.

    A stage is `(label, seconds)`, `(label, seconds, floor)`, or
    `(label, seconds, floor, once)`. `once` marks work that happens once per
    process rather than once per cell: EVAL 5's screen, belief pass and
    reference pool are memoised by `Session.screen_for` and now cached to disk,
    so scaling them by the cell count claimed a 3x3 suite would screen nine
    times when it screens once — an overestimate of hours on exactly the suites
    that most need to be sized against a walltime.
    """
    scaled = []
    for stage in stages:
        label, rest = stage[0], list(stage[1:])
        ceiling = rest[0]
        floor = rest[1] if len(rest) > 1 else rest[0]
        mult = 1 if (len(rest) > 2 and rest[2]) else n_cells
        scaled.append((label, ceiling * mult, floor * mult))
    return scaled


def benchmark_stages(cli, model=None):
    """EVAL 5's rough cost, per dataset: the screen plus one pass per config.

    The screen's cost is a *worst case* — it walks the candidate pool until it
    finds `--benchmark-n-per-dataset` items the full model is deceptive on, and
    stops early when deception is common. There is no way to know which without
    generating, so this assumes the pool is exhausted and says so.
    """
    from evaluation.benchmarks import get_benchmark
    from evaluation import screen_cache

    n = cli.benchmark_n_per_dataset
    n_configs = 4 + cli.benchmark_n_random          # full/knockout/circuit/empty
    # The screen judges in chunks and stops when both pools fill; how many
    # candidates that takes is not knowable without generating, so this assumes
    # it runs to its own budget. Stated as the worst case rather than a guess,
    # because the failure this estimate exists to prevent is a job killed at
    # the walltime with nothing written.
    stages = []
    for dataset in expand(cli.benchmarks):
        bench = get_benchmark(dataset)
        tokens = bench.new_tokens or cli.benchmark_new_tokens
        # The screen stops at whichever comes first: its budget, or running out
        # of candidates. Estimating the budget for a 191-row benchmark claimed
        # five times the work that exists.
        pool = _pool_size(bench, cli)
        budget = cli.benchmark_screen_budget or pool or n * SCREEN_MAX_FACTOR
        screened = min(budget, pool) if pool else budget
        per_pass = n * tokens * SEC_PER_GEN_TOKEN_ROW

        # A cached screen makes the screen, the belief pass and the reference
        # pool free — they are circuit-independent and already on disk. This
        # cannot be asserted from a login node, which has no GPU and so cannot
        # build a key containing the device, so it is folded into the *floor*
        # and never the ceiling: the estimate exists to stop a job being killed
        # at the walltime, and a predicted hit that does not happen is exactly
        # the way it would fail at that job.
        cached = bool(model) and not cli.no_benchmark_screen_cache and \
            not cli.benchmark_refresh_screen and bool(
                screen_cache.cached_on_devices(
                    cli, dataset,
                    screen_cache.build_key(cli, dataset, bench,
                                           _items_for(bench, cli), model)))
        free = 0.0 if cached else None

        probes = _probe_count(bench, cli)
        if probes:
            # Belief runs over every *screened* candidate, not just survivors.
            belief_tokens = (tokens if probes == 1
                             else cli.benchmark_belief_tokens)
            stages.append(
                (f"eval 5 {dataset}: belief ({probes} probe(s))",
                 screened * probes * belief_tokens * SEC_PER_GEN_TOKEN_ROW,
                 free if free is not None
                 else n * probes * belief_tokens * SEC_PER_GEN_TOKEN_ROW,
                 True))
        # The screen stops as soon as it has `n` deceptive items -- and for a
        # prompt-kind benchmark that is the only thing it waits for, since its
        # honest bank comes from twins rather than screening bycatch. How fast
        # that happens is the full model's deception rate, which is exactly
        # what this evaluation is measuring, so it cannot be known here. Both
        # ends are printed rather than picking one and being wrong: the floor
        # assumes every candidate is deceptive, the ceiling assumes the walk
        # runs out of pool.
        stages.append((f"eval 5 {dataset}: screen ({n}-{screened} items)"
                       + (" [cached]" if cached else ""),
                       screened * tokens * SEC_PER_GEN_TOKEN_ROW,
                       free if free is not None
                       else n * tokens * SEC_PER_GEN_TOKEN_ROW,
                       True))
        stages.append((f"eval 5 {dataset}: reference pool", per_pass,
                       0.0 if cached else per_pass, True))
        # `full` reuses the screen's own tokens rather than generating again.
        stages.append((f"eval 5 {dataset}: {n_configs - 1} ablated configs",
                       (n_configs - 1) * per_pass))
        # One teacher-forced reference forward per config, over prompt +
        # generation. Cheaper than decoding by roughly the token count, since
        # it is a single forward rather than one per token.
        # ~1.3x `tokens` to stand for prompt + generation, which is what the
        # reference forward actually scores.
        stages.append((f"eval 5 {dataset}: coherence x {n_configs}",
                       n_configs * n * tokens * 1.3 *
                       SEC_PER_COHERENCE_TOKEN_ROW))
    return stages


#: dataset -> loaded items, so --dry-run's plan table and its runtime estimate
#: read the adapters once between them rather than twice each.
_POOL_CACHE = {}


def _items_for(bench, cli):
    if bench.name not in _POOL_CACHE:
        try:
            _POOL_CACHE[bench.name] = bench.load(None, cli)
        except Exception:                                  # noqa: BLE001
            _POOL_CACHE[bench.name] = None
    return _POOL_CACHE[bench.name]


def _pool_size(bench, cli):
    """Screenable candidates: for a prompt-kind benchmark, the deceptive half."""
    items = _items_for(bench, cli)
    if items is None:
        return 0
    return len([i for i in items if bench.condition_kind != "prompt"
                or i.condition == DECEPTIVE])


def _probe_count(bench, cli):
    """How many belief probes an adapter asks per item, or 0 if it asks none.

    Read off a real item so it reflects the adapter rather than a guess; a
    dataset whose checkout is missing contributes 0 and the estimate omits the
    row rather than inventing one.
    """
    items = _items_for(bench, cli)
    if not items:
        return 0
    try:
        return len(bench.belief_request(items[0]) or [])
    except Exception:                                      # noqa: BLE001
        return 0


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
        if hasattr(bench, "bind"):
            # Without this the column prints the adapter's default judge even
            # under --mask-judge-model / --lb-judge-model, i.e. misreports
            # which model is about to be billed.
            bench.bind(cli)
        spec = bench.judge_spec()
        # The candidate pool, loaded for real: prompts are model-independent,
        # so this needs no GPU and no key. A dataset whose checkout is missing
        # reports that rather than taking the whole dry run down with it --
        # the point of --dry-run is to find out what is wrong, not to stop at
        # the first thing.
        # For a prompt-kind benchmark `load()` returns both conditions and the
        # screen walks only the deceptive half; counting both would roughly
        # double sandbagging's apparent pool and let the thin-cell warning use
        # a number no run can reach.
        if _items_for(bench, cli) is None:
            pool = "unavailable"
        else:
            pool = _pool_size(bench, cli)
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
    _screen_cache_plan(cli, datasets)


def _screen_cache_plan(cli, datasets) -> None:
    """What the screen cache already holds for this configuration.

    The screen is ~79% of EVAL 5's ceiling and is the one part that never has
    to be repaid, so "is it already on disk, and from which GPU" is the single
    most useful line in the dry run for deciding what to submit.
    """
    from evaluation.benchmarks import get_benchmark
    from evaluation import screen_cache

    print()
    if cli.no_benchmark_screen_cache:
        print("  Screen cache: disabled (--no-benchmark-screen-cache).")
        return
    if cli.benchmark_refresh_screen:
        print("  Screen cache: --benchmark-refresh-screen; every screen will "
              "be recomputed and overwritten.")
        return
    # No model name here: the plan runs before the session is built, and the
    # key would differ from the real one anyway. Report per dataset what is on
    # disk and let the caller match it against the GPU they intend to use.
    root = cli.benchmark_screen_cache or screen_cache.DEFAULT_CACHE_DIR
    print(f"  Screen cache: {root}")
    for dataset in datasets:
        # Screens that match THIS configuration in every field but the device,
        # not every file in the directory: "3 cached screen(s)" that are three
        # other configurations will all miss, and reporting them as cached is
        # worse than reporting nothing.
        bench = get_benchmark(dataset)
        if hasattr(bench, "bind"):
            bench.bind(cli)
        key = screen_cache.build_key(cli, dataset, bench,
                                     _items_for(bench, cli), None)
        devices = screen_cache.cached_on_devices(cli, dataset, key)
        print(f"    {dataset:<34} "
              + (", ".join(sorted(set(devices))) if devices
                 else "nothing cached for this configuration"))
    print("  The GPU is part of the key, because `full` reuses the screen's "
          "own tokens:\n  a screen made on another device would put 'which "
          "GPU' inside the delta this\n  evaluation measures. Switching "
          "hardware is a miss, and the screen is repaid.")


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
    ranged = est["total_seconds_floor"] != est["total_seconds"]
    for label, seconds, floor in est["stages"]:
        if floor != seconds:
            print(f"  {label:<40} {floor / 60:>8.1f} - {seconds / 60:.1f} min")
        else:
            print(f"  {label:<40} {seconds / 60:>8.1f} min")
    print("  " + "-" * 50)
    if ranged:
        print(f"  {'TOTAL':<40} {est['total_seconds_floor'] / 60:>8.1f} - "
              f"{est['total_seconds'] / 60:.1f} min ({est['cells']} cell(s))")
        print("\n  The range is the screen: it stops as soon as it has "
              "--benchmark-n-per-dataset\n  items the full model is deceptive "
              "on, so the floor assumes every candidate\n  is deceptive and "
              "the ceiling assumes it walks the whole pool. Which end you\n  "
              "land on IS the full model's deception rate, which is what this "
              "evaluation\n  measures — so size the job against the ceiling.")
    else:
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


def check_judges_answer(cli) -> None:
    """Spend one judge call per distinct judge, before the model loads.

    `check_benchmark_keys` proves a key is *set*. It cannot prove the key still
    works, and the difference is not academic: job 21882184 ran for 1h39m,
    finished sandbagging entirely, and then discovered that the OpenAI account
    had no credits left -- every MASK judge call returning 429
    `credit_balance_exhausted`, all 132 candidates labelled `unparsed`, and the
    dataset raising "the full model was not judged deceptive on any of them".

    A few cents here buys back that hour. Failures that are clearly about the
    account rather than the network are fatal; anything else is a warning,
    because a transient blip at startup should not stop a job that retries.
    """
    from evaluation.benchmarks import get_benchmark
    from evaluation.benchmarks.base import JudgeRequest
    from evaluation.benchmarks.judge import JudgeClient

    seen, probes = set(), []
    for dataset in expand(cli.benchmarks):
        bench = get_benchmark(dataset)
        if hasattr(bench, "bind"):
            bench.bind(cli)
        spec = bench.judge_spec()
        if not spec or (spec["provider"], spec["model"]) in seen:
            continue
        seen.add((spec["provider"], spec["model"]))
        probes.append((dataset, JudgeRequest(
            spec["provider"], spec["model"],
            [{"role": "user", "content": "Reply with the single word: ok"}],
            # Generous on purpose. A reasoning model (MASK's numerical judge is
            # o3-mini) spends its budget thinking before it emits anything, so
            # a tight cap returns an empty completion and the probe reports a
            # dead judge that is in fact perfectly healthy. The probe is one
            # call; the tokens are worth less than the false alarm.
            kwargs={"max_completion_tokens": 256})))
    if not probes:
        return

    print("  Checking %d judge(s) answer before loading the model..."
          % len(probes))
    # No cache: a cached "ok" from an earlier run would defeat the point.
    client = JudgeClient(cache_path=None, concurrency=len(probes),
                         max_retries=1, verbose=False)
    results = client.run([p[1] for p in probes])
    # Fatal unless the failure looks like weather. The gate exists to refuse
    # GPU hours that cannot produce a label, so the default has to be "stop":
    # a false stop costs one resubmission, a false pass costs the hour and a
    # half that job 21882184 spent before finding the account empty. An
    # earlier version of this had it the other way round and classified a
    # client-construction TypeError -- an SDK that cannot make any call at all
    # -- as transient.
    TRANSIENT = ("timeout", "timed out", "connection", "econnreset",
                 "temporarily unavailable", "502", "503", "504",
                 "rate limit", "overloaded")
    dead = []
    for (dataset, request), result in zip(probes, results):
        if result is not None and result.ok:
            continue
        error = str(getattr(result, "error", "no response"))
        lowered = error.lower()
        transient = (any(word in lowered for word in TRANSIENT)
                     # A 429 is a rate limit unless it is really a bill.
                     and not any(word in lowered for word in
                                 ("quota", "credit", "billing")))
        if transient:
            print("  !! %s did not answer (%s). Continuing: this reads as a "
                  "transient condition, and the run retries."
                  % (request.model, error))
        else:
            dead.append("  %s (%s) — %s" % (request.model, dataset, error))
    if dead:
        raise SystemExit("\n".join(
            ["EVAL 5's judge(s) rejected a test call, so nothing would be "
             "labelled:"] + dead
            + ["", "Check the account's credit and the key's validity, and "
               "that the judge SDK works in this environment. Or run",
               "'--benchmarks sandbagging', which grades locally and needs "
               "no judge at all.",
               "--skip-judge-check bypasses this if you know better."]))


def main():
    cli = resolve_cli(build_parser().parse_args())
    if "benchmarks" in cli.evals and not (cli.judge_dry_run or cli.dry_run):
        # Before build_session: a missing key must cost zero GPU time. Neither
        # --dry-run nor --judge-dry-run spends anything, and --dry-run's whole
        # job is to be runnable on a login node where no key is exported --
        # it *prints* which keys are missing, which it cannot do if a missing
        # key is what stopped it.
        check_benchmark_keys(cli)
        if not cli.skip_judge_check:
            check_judges_answer(cli)
    session = build_session(cli)
    if cli.dry_run:
        return dry_run(session)
    if cli.judge_dry_run:
        from evaluation.benchmark_eval import judge_dry_run
        return judge_dry_run(session)
    return suite.run(session)


if __name__ == "__main__":
    sys.exit(main())
