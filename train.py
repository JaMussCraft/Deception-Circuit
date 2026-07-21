"""
train.py — unified entry point for two-phase circuit discovery.

One command runs node pruning and (optionally) edge pruning for any supported
model and task:

    python train.py --model gpt2     --task ioi
    python train.py --model llama-1b --task gp  --no-edge-pruning
    python train.py --model gpt2-xl  --task gt  --lambda-attention-heads 0.5

Models : gpt2, gpt2-xl, llama-1b, llama-8b, llama-8b-instruct
Tasks  : ioi, gp, gt, std     (gt is GPT-2 only; std is Llama-only, built for
                               llama-8b-instruct via dataset/build_std_dataset.py)

Edge pruning, the prunable granularities, and every sparsity coefficient
(`lambda_*`) are controlled by flags; see `python train.py --help`.
"""

import argparse
import json
import os
import sys

import torch

from config import (NodePruningConfig, EdgeConfig, GRANULARITIES,
                    default_node_config, default_hyperparams,
                    DEFAULT_NODE_LAMBDA_SPARSITY, DEFAULT_EDGE_LAMBDA_SPARSITY)
from models import ModelAdapter, MODEL_REGISTRY, list_models
from tasks import get_task, list_tasks
from pruning import GPUMemoryTracker, run_node_pruning, run_edge_pruning
from analysis import (extract_active_nodes, extract_node_masks, save_active_nodes,
                      load_active_nodes, count_dense_edges, analyze_edge_circuit)
from run_io import (make_run_dir, tee_stdout_stderr, save_history,
                    plot_phase_history)


# ==============================================================================
# CLI
# ==============================================================================

def build_parser():
    p = argparse.ArgumentParser(
        description="Two-phase (node + edge) circuit discovery.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    g = p.add_argument_group("model & task")
    g.add_argument("--model", default="gpt2", choices=list_models())
    g.add_argument("--task", default="ioi", choices=list_tasks())
    g.add_argument("--edge-pruning", action=argparse.BooleanOptionalAction,
                   default=True, help="Run Phase 2 edge pruning after node pruning.")
    g.add_argument("--skip-node-pruning", action="store_true",
                   help="Load active nodes from --node-checkpoint instead of training them.")
    g.add_argument("--node-checkpoint", default=None,
                   help="Path to save/load the active-node spec "
                        "(default: <run-dir>/active_nodes.json).")

    g = p.add_argument_group("granularities (node pruning)")
    for name in GRANULARITIES:
        g.add_argument(f"--prune-{name.replace('_', '-')}", dest=f"prune_{name}",
                       action=argparse.BooleanOptionalAction, default=None,
                       help=f"Enable/disable pruning at the {name} granularity.")
        g.add_argument(f"--lambda-{name.replace('_', '-')}", dest=f"lambda_{name}",
                       type=float, default=None,
                       help=f"Sparsity coefficient for the {name} granularity.")

    g = p.add_argument_group("sparsity & optimisation")
    g.add_argument("--node-lambda-sparsity", type=float, default=DEFAULT_NODE_LAMBDA_SPARSITY,
                   help="Phase-1 sparsity-vs-fidelity trade-off (the node pruning lambda).")
    g.add_argument("--edge-lambda-sparsity", type=float, default=DEFAULT_EDGE_LAMBDA_SPARSITY,
                   help="Phase-2 sparsity-vs-fidelity trade-off (the edge pruning lambda).")
    g.add_argument("--node-epochs", type=int, default=None)
    g.add_argument("--edge-epochs", type=int, default=None)
    g.add_argument("--lr", type=float, default=None)
    g.add_argument("--batch-size", type=int, default=None)
    g.add_argument("--max-seq-length", type=int, default=None)

    g = p.add_argument_group("data & io")
    g.add_argument("--train-samples", type=int, default=None)
    g.add_argument("--val-samples", type=int, default=None)
    g.add_argument("--test-samples", type=int, default=None)
    g.add_argument("--data-dir", default="./data/datasets",
                   help="Root holding <task>/ subfolders (ioi, gp, gt).")
    g.add_argument("--output-dir", default=None,
                   help="Run directory for logs/plots/JSONs "
                        "(default: outputs/<model>_<task>/<hp-slug>_<timestamp>).")
    g.add_argument("--seed", type=int, default=42)
    g.add_argument("--hf-token", default=None,
                   help="HuggingFace token for gated Llama models "
                        "(falls back to ../hf_tokken.txt or HF_TOKEN env var).")

    g = p.add_argument_group("std task")
    g.add_argument("--std-variant", default="azaria", choices=["azaria", "neutral"],
                   help="Which prebuilt STD dataset to load "
                        "(<data-dir>/std_<variant>).")
    g.add_argument("--std-runtime-filter", action="store_true",
                   help="Re-filter STD val/test for deceptive behavior with the "
                        "current full model (splits are already prefiltered by "
                        "dataset/build_std_dataset.py).")
    g.add_argument("--std-margin-loss", type=float, default=None,
                   help="Margin for the STD task loss and runtime filter. "
                        "Default: the build-time margin_thresh stored in the "
                        "dataset's dataset_config.json.")
    return p


def resolve_args(args):
    """Fill in family-specific defaults and apply CLI overrides."""
    args.family = MODEL_REGISTRY[args.model][1]

    # Training hyperparameters: use the (family, task) defaults where unset.
    hp = default_hyperparams(args.family, args.task)
    for k, v in hp.items():
        if getattr(args, k, None) is None:
            setattr(args, k, v)

    # Node config: per-(family, task) lambdas, then CLI overrides.
    node_cfg = default_node_config(args.family, args.task)
    for name in GRANULARITIES:
        pv = getattr(args, f"prune_{name}")
        lv = getattr(args, f"lambda_{name}")
        if pv is not None:
            setattr(node_cfg, f"prune_{name}", pv)
        if lv is not None:
            setattr(node_cfg, f"lambda_{name}", lv)

    edge_cfg = EdgeConfig()
    return node_cfg, edge_cfg


def resolve_hf_token(args):
    if args.hf_token:
        return args.hf_token
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"]
    for cand in ("../hf_tokken.txt", "hf_tokken.txt"):
        if os.path.exists(cand):
            with open(cand) as f:
                tok = f.read().strip()
            if tok:
                print(f"Loaded HF token from {cand}")
                return tok
    return None


# ==============================================================================
# Reporting
# ==============================================================================

W = 84


def _print_node_report(node_stats):
    if not node_stats:
        return
    print("\n" + "=" * W)
    print("  NODE PRUNING — GRANULARITY SUMMARY")
    print("=" * W)
    gs = node_stats.get("granularity_stats", {})
    print(f"\n{'Granularity':<22} {'Active':>10} {'Total':>10} {'Pruned %':>10}")
    print("-" * 54)
    for key in ["full_layers" if "full_layers" in gs else "layer_level",
                "attention_blocks", "mlp_blocks", "attention_heads",
                "attention_neurons", "mlp_hidden", "mlp_output", "embedding"]:
        s = gs.get(key)
        if s and s["total"] > 0:
            pct = (s["total"] - s["active"]) / s["total"] * 100
            print(f"  {key:<20} {s['active']:>10,.0f} {s['total']:>10,} {pct:>9.1f}%")
    pc = node_stats.get("prunable_compression")
    if pc:
        print(f"\n  Prunable-parameter reduction: {pc['reduction_percentage']:.1f}% "
              f"({pc['compression_ratio']:.2f}x)")


def _print_dense_edges(dense):
    print("\n" + "=" * W)
    print("  DENSE EDGES (between surviving nodes, before edge pruning)")
    print("=" * W)
    full_e, dense_e = dense["full_total"], dense["dense_total"]
    print(f"\n  Full-model edges: {full_e:>10,}")
    print(f"  Dense edges:      {dense_e:>10,}  ({dense_e / full_e:.2%} of full)")
    print(f"  Categories — output {dense['dense_output']:,} | mlp {dense['dense_mlp']:,} | "
          f"q {dense['dense_q']:,} | k {dense['dense_k']:,} | v {dense['dense_v']:,}")
    return full_e, dense_e


def _print_edge_report(edge_stats, full_e):
    te, ae = edge_stats["total_edges"], edge_stats["active_edges"]
    print("\n" + "=" * W)
    print("  EDGE PRUNING — SUMMARY")
    print("=" * W)
    print(f"\n  {'Category':<16} {'Active':>10} {'Total':>10} {'Kept %':>9}")
    print("  " + "-" * 47)
    for cat, s in edge_stats["stats"].items():
        if s["total"] > 0:
            print(f"  {cat.replace('_', ' ').title():<16} {s['active']:>10,} "
                  f"{s['total']:>10,} {s['active'] / s['total'] * 100:>8.1f}%")
    print("  " + "-" * 47)
    if te > 0:
        print(f"  {'TOTAL':<16} {ae:>10,} {te:>10,} {ae / te * 100:>8.1f}%")
    if ae > 0:
        print(f"\n  Edge compression: {te / ae:.2f}x   "
              f"vs full model: {ae:,}/{full_e:,} ({ae / full_e:.2%})")
    return te, ae


def _print_fidelity(task, rows):
    """rows: list of (label, metrics_dict_or_None)."""
    print("\n" + "=" * W)
    print("  FIDELITY COMPARISON")
    print("=" * W)
    cols = task.metric_columns
    header = f"  {'Model':<26}" + "".join(f"{lbl:>14}" for _, lbl in cols)
    print("\n" + header)
    print("  " + "-" * (len(header) - 2))
    for label, m in rows:
        if m is None:
            continue
        cells = ""
        for key, _ in cols:
            v = m.get(key)
            cells += f"{v:>14.4f}" if isinstance(v, (int, float)) else f"{'—':>14}"
        print(f"  {label:<26}{cells}")


# ==============================================================================
# Main
# ==============================================================================

def main():
    args = build_parser().parse_args()

    # GT is not defined for Llama models — check before resolving any defaults.
    args.family = MODEL_REGISTRY[args.model][1]
    task = get_task(args.task)
    if not task.supports_family(args.family):
        print(f"\nTask '{args.task.upper()}' is not supported for "
              f"{args.family.upper()} models ({args.model}).")
        print("Greater-Than relies on GPT-2 single-token two-digit years; "
              "use --task ioi or --task gp for Llama, or a GPT-2 model for GT.")
        sys.exit(0)

    node_cfg, edge_cfg = resolve_args(args)
    make_run_dir(args, node_cfg, edge_cfg)

    with tee_stdout_stderr(os.path.join(args.output_dir, "train.log")):
        _run_training(args, task, node_cfg, edge_cfg)


def _run_training(args, task, node_cfg, edge_cfg):
    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tracker = GPUMemoryTracker()
    run_history = {}

    if torch.cuda.is_available():
        gpu = torch.cuda.get_device_properties(0)
        print(f"\nGPU: {gpu.name} | {gpu.total_memory / 1024 ** 3:.1f} GB")
    print(f"Model: {args.model} ({MODEL_REGISTRY[args.model][0]})  |  Task: {task.display_name}")
    print(f"Edge pruning: {'ON' if args.edge_pruning else 'OFF'}  |  seed: {args.seed}")
    print(f"Output dir: {args.output_dir}")

    adapter = ModelAdapter(args.model, hf_token=resolve_hf_token(args))
    args.shuffle_train = not adapter.cache_target_logits  # cached path needs stable order

    tokenizer = adapter.load_tokenizer()
    full_model = adapter.load_full_model(device)
    tracker.snap("Full model loaded")

    state = task.prepare(tokenizer, device)
    train_dl, val_dl, test_dl = task.build_dataloaders(
        tokenizer, args.family, full_model, device, args, state)

    print("\n--- Baseline evaluation (full model) ---")
    baseline = task.evaluate(full_model, "Full Model", None, test_dl, device, tokenizer, state)

    # ----- Phase 1: node pruning ------------------------------------------
    node_stats = None
    node_eval = None
    if args.skip_node_pruning and os.path.exists(args.node_checkpoint):
        active_heads, active_mlps = load_active_nodes(args.node_checkpoint)
    else:
        node_model, node_stats, node_hist = run_node_pruning(
            adapter, task, full_model, train_dl, val_dl, device, tokenizer,
            node_cfg, args, state, tracker)
        run_history["node"] = node_hist
        plot_phase_history(node_hist, args.output_dir, "Node")
        active_heads, active_mlps = extract_active_nodes(node_model)
        node_masks = extract_node_masks(node_model)
        save_active_nodes(active_heads, active_mlps, args.node_checkpoint,
                          masks=node_masks)

        node_model.eval()
        node_eval = task.evaluate(node_model, "Node-Pruned Circuit", full_model,
                                  test_dl, device, tokenizer, state)
        del node_model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        tracker.snap("Node model freed")

    n_heads = sum(len(v) for v in active_heads.values())
    print(f"\nActive nodes: {n_heads} heads + {len(active_mlps)} MLPs + 1 embedding")

    dense = count_dense_edges(
        active_heads, active_mlps,
        num_layers=adapter.num_layers(full_model),
        num_heads_per_layer=adapter.num_heads(full_model),
        num_key_value_groups=adapter.num_key_value_groups(full_model),
        verbose=False)

    # ----- Phase 2: edge pruning ------------------------------------------
    edge_stats = None
    edge_eval = None
    if args.edge_pruning:
        edge_model, edge_hist = run_edge_pruning(
            adapter, task, full_model, active_heads, active_mlps,
            train_dl, val_dl, device, tokenizer, edge_cfg, args, state, tracker)
        run_history["edge"] = edge_hist
        plot_phase_history(edge_hist, args.output_dir, "Edge")
        edge_stats = analyze_edge_circuit(edge_model, verbose=False)
        edge_model.eval()
        edge_eval = task.evaluate(edge_model, "Edge-Pruned Circuit", full_model,
                                  test_dl, device, tokenizer, state)

    if run_history:
        hist_path = save_history(run_history, args.output_dir)
        print(f"\nSaved training history to {hist_path}")

    # ----- Reports --------------------------------------------------------
    _print_node_report(node_stats)
    full_e, dense_e = _print_dense_edges(dense)
    te = ae = None
    if edge_stats is not None:
        te, ae = _print_edge_report(edge_stats, full_e)

    _print_fidelity(task, [
        ("Baseline (Full Model)", baseline),
        ("Node-Pruned Circuit", node_eval),
        ("Edge-Pruned Circuit", edge_eval),
    ])

    print("\n" + "=" * W)
    print("  END-TO-END EDGE COMPRESSION")
    print("=" * W)
    print(f"\n  Full model:        {full_e:>10,}  (100.0%)")
    print(f"  After node pruning:{dense_e:>10,}  ({dense_e / full_e:.1%})")
    if ae is not None:
        print(f"  After edge pruning:{ae:>10,}  ({ae / full_e:.1%})")
        if ae > 0:
            print(f"\n  Overall edge compression: {full_e / ae:.2f}x")

    # ----- Persist --------------------------------------------------------
    results = {
        "model": args.model, "task": args.task, "family": args.family,
        "edge_pruning": args.edge_pruning, "seed": args.seed,
        "baseline": baseline, "node_eval": node_eval, "edge_eval": edge_eval,
        "dense_edges": dense,
        "edge_stats": {k: edge_stats[k] for k in ("total_edges", "active_edges")}
        if edge_stats else None,
        "node_granularity": node_stats.get("granularity_stats") if node_stats else None,
    }
    results_path = os.path.join(args.output_dir, "results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved results to {results_path}")
    print(f"Run artifacts in {args.output_dir}")

    tracker.print_report()


if __name__ == "__main__":
    main()
