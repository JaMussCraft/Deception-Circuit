"""
run_io.py — per-run output directories, logging, and PDF plots.

Layout (when --output-dir is left unset):

  outputs/<model>_<task>/<hp-slug>_<timestamp>/
    config.json
    train.log
    history.json
    plots/loss_{node,edge}.pdf
    plots/metrics_{node,edge}.pdf
    active_nodes.json
    results.json

The slug lists only hyperparameters that differ from (family, task) defaults,
so all-default runs land in .../default_<timestamp>/.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass

from config import (GRANULARITIES, NodePruningConfig,
                    default_hyperparams, DEFAULT_NODE_LAMBDA_SPARSITY,
                    DEFAULT_EDGE_LAMBDA_SPARSITY)


# Compact tokens for CLI/training fields that commonly vary.
_HP_ABBREV = {
    "node_epochs": "ne",
    "edge_epochs": "ee",
    "lr": "lr",
    "batch_size": "bs",
    "max_seq_length": "seq",
    "train_samples": "ntr",
    "val_samples": "nva",
    "test_samples": "nte",
    "node_lambda_sparsity": "nls",
    "edge_lambda_sparsity": "els",
    "seed": "seed",
}

_GRAN_ABBREV = {
    "attention_heads": "ah",
    "attention_neurons": "an",
    "attention_blocks": "ab",
    "mlp_hidden": "mh",
    "mlp_output": "mo",
    "mlp_blocks": "mb",
    "full_layers": "fl",
    "embedding": "emb",
}


def _fmt_num(v) -> str:
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return f"{v:.4g}".replace("+", "")
    return str(v)


def resolved_run_config(args, node_cfg, edge_cfg) -> dict:
    """Full resolved config for config.json (and slug comparison)."""
    return {
        "model": args.model,
        "task": args.task,
        "family": args.family,
        "edge_pruning": args.edge_pruning,
        "skip_node_pruning": args.skip_node_pruning,
        "seed": args.seed,
        "node_epochs": args.node_epochs,
        "edge_epochs": args.edge_epochs,
        "lr": args.lr,
        "batch_size": args.batch_size,
        "max_seq_length": args.max_seq_length,
        "train_samples": args.train_samples,
        "val_samples": args.val_samples,
        "test_samples": args.test_samples,
        "node_lambda_sparsity": args.node_lambda_sparsity,
        "edge_lambda_sparsity": args.edge_lambda_sparsity,
        "data_dir": args.data_dir,
        "node_config": asdict(node_cfg) if is_dataclass(node_cfg) else dict(node_cfg),
        "edge_config": asdict(edge_cfg) if is_dataclass(edge_cfg) else dict(edge_cfg),
    }


def build_run_slug(args, node_cfg, max_len: int = 90) -> str:
    """Compact slug from non-default hyperparameters + timestamp for uniqueness."""
    defaults = default_hyperparams(args.family, args.task)
    default_node = NodePruningConfig()
    parts = []

    for key, abbr in _HP_ABBREV.items():
        val = getattr(args, key)
        if key in defaults:
            if val != defaults[key]:
                parts.append(f"{abbr}{_fmt_num(val)}")
        elif key == "node_lambda_sparsity":
            if val != DEFAULT_NODE_LAMBDA_SPARSITY:
                parts.append(f"{abbr}{_fmt_num(val)}")
        elif key == "edge_lambda_sparsity":
            if val != DEFAULT_EDGE_LAMBDA_SPARSITY:
                parts.append(f"{abbr}{_fmt_num(val)}")
        elif key == "seed":
            if val != 42:
                parts.append(f"{abbr}{_fmt_num(val)}")

    if not args.edge_pruning:
        parts.append("noedge")
    if args.skip_node_pruning:
        parts.append("skipnode")

    for g in GRANULARITIES:
        abbr = _GRAN_ABBREV[g]
        prune_key, lam_key = f"prune_{g}", f"lambda_{g}"
        if getattr(node_cfg, prune_key) != getattr(default_node, prune_key):
            parts.append(("yes" if getattr(node_cfg, prune_key) else "no") + abbr)
        if getattr(node_cfg, lam_key) != getattr(default_node, lam_key):
            parts.append(f"l{abbr}{_fmt_num(getattr(node_cfg, lam_key))}")

    body = "_".join(parts) if parts else "default"
    stamp = time.strftime("%y%m%d-%H%M%S")
    if len(body) > max_len:
        digest = hashlib.sha1(body.encode()).hexdigest()[:8]
        body = body[: max_len - 9].rstrip("_") + "_" + digest
    return f"{body}_{stamp}"


def make_run_dir(args, node_cfg, edge_cfg) -> str:
    """Create the run directory; auto-slug under outputs/<model>_<task>/ when unset."""
    if args.output_dir is None:
        slug = build_run_slug(args, node_cfg)
        args.output_dir = os.path.join("outputs", f"{args.model}_{args.task}", slug)
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(os.path.join(args.output_dir, "plots"), exist_ok=True)

    cfg = resolved_run_config(args, node_cfg, edge_cfg)
    with open(os.path.join(args.output_dir, "config.json"), "w") as f:
        json.dump(cfg, f, indent=2, default=str)

    if args.node_checkpoint is None:
        args.node_checkpoint = os.path.join(args.output_dir, "active_nodes.json")
    return args.output_dir


class _Tee:
    """Write to multiple text streams (e.g. terminal + train.log)."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()

    def flush(self):
        for s in self.streams:
            s.flush()

    def isatty(self):
        return any(getattr(s, "isatty", lambda: False)() for s in self.streams)


@contextmanager
def tee_stdout_stderr(log_path: str):
    """Mirror stdout and stderr to a log file for the duration of the block."""
    log_f = open(log_path, "w", buffering=1)
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = _Tee(old_out, log_f)
    sys.stderr = _Tee(old_err, log_f)
    try:
        yield log_path
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
        log_f.close()


def save_history(history: dict, output_dir: str) -> str:
    path = os.path.join(output_dir, "history.json")
    with open(path, "w") as f:
        json.dump(history, f, indent=2, default=str)
    return path


# Display names for the usual fidelity / eval summary metrics.
METRIC_LABELS = {
    "accuracy": "Accuracy",
    "logit_diff": "Logit Difference",
    "kl_div": "Faithfulness",
    "exact_match": "Exact Match Rate",
    "prob_diff": "Prob Diff",
    "cutoff_sharpness": "Cutoff Sharpness",
}

# Preferred order for summary plots (IOI/GP); others appended after.
_SUMMARY_METRIC_ORDER = ("accuracy", "logit_diff", "kl_div", "exact_match")


def _metric_label(key: str) -> str:
    return METRIC_LABELS.get(key, key.replace("_", " ").title())


def _ordered_metric_keys(keys) -> list:
    ordered = [k for k in _SUMMARY_METRIC_ORDER if k in keys]
    for k in keys:
        if k not in ordered:
            ordered.append(k)
    return ordered


def _pyplot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def plot_phase_history(history: dict, output_dir: str, phase: str) -> list:
    """Write loss and (if present) metrics PDFs for one phase. Returns paths."""
    if not history or not history.get("epochs"):
        return []

    plt = _pyplot()
    plots_dir = os.path.join(output_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    written = []
    epochs = history["epochs"]
    phase_l = phase.lower()

    fig, ax = plt.subplots(figsize=(7, 4))
    for key, label in (("loss", "Total"), ("kl", "KL"),
                       ("task", "Task"), ("sparsity", "Sparsity")):
        if key in history and history[key]:
            ax.plot(epochs, history[key], label=label)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title(f"{phase} pruning — training losses")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    loss_path = os.path.join(plots_dir, f"loss_{phase_l}.pdf")
    fig.savefig(loss_path)
    plt.close(fig)
    written.append(loss_path)

    evals = history.get("evals") or []
    if evals:
        metric_keys = []
        for ev in evals:
            for k, v in ev.items():
                if k == "epoch":
                    continue
                if isinstance(v, (int, float)) and k not in metric_keys:
                    metric_keys.append(k)
        metric_keys = _ordered_metric_keys(metric_keys)
        if metric_keys:
            n = len(metric_keys)
            ncols = 2 if n > 1 else 1
            nrows = (n + ncols - 1) // ncols
            fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 3.5 * nrows),
                                     squeeze=False)
            ev_epochs = [ev["epoch"] for ev in evals]
            for i, k in enumerate(metric_keys):
                ax = axes[i // ncols][i % ncols]
                ys = [ev.get(k) for ev in evals]
                ax.plot(ev_epochs, ys, marker="o")
                ax.set_xlabel("Epoch")
                ax.set_ylabel(_metric_label(k))
                ax.set_title(_metric_label(k))
                ax.grid(True, alpha=0.3)
            for j in range(n, nrows * ncols):
                axes[j // ncols][j % ncols].set_visible(False)
            fig.suptitle(f"{phase} pruning — validation metrics", y=1.02)
            fig.tight_layout()
            metrics_path = os.path.join(plots_dir, f"metrics_{phase_l}.pdf")
            fig.savefig(metrics_path, bbox_inches="tight")
            plt.close(fig)
            written.append(metrics_path)

    return written


def plot_fidelity_summary(rows, output_dir: str, metric_columns=None) -> list:
    """Bar charts of final fidelity metrics (baseline / node / edge).

    `rows` is a list of (label, metrics_dict_or_None), matching the fidelity
    table in train.py. Writes plots/fidelity_summary.pdf.
    """
    rows = [(label, m) for label, m in rows if m]
    if not rows:
        return []

    if metric_columns:
        keys = [k for k, _ in metric_columns]
        labels = {k: lbl for k, lbl in metric_columns}
        # Prefer user-facing names for the common IOI/GP summary metrics.
        for k, nice in METRIC_LABELS.items():
            if k in labels and k in ("accuracy", "logit_diff", "kl_div", "exact_match"):
                labels[k] = nice
    else:
        keys = []
        for _, m in rows:
            for k, v in m.items():
                if isinstance(v, (int, float)) and k not in keys:
                    keys.append(k)
        keys = _ordered_metric_keys(keys)
        labels = {k: _metric_label(k) for k in keys}

    keys = [k for k in keys if any(
        isinstance(m.get(k), (int, float)) for _, m in rows)]
    if not keys:
        return []

    plt = _pyplot()
    plots_dir = os.path.join(output_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    n = len(keys)
    ncols = 2 if n > 1 else 1
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 3.5 * nrows),
                             squeeze=False)
    stage_labels = [label for label, _ in rows]
    x = range(len(stage_labels))

    for i, k in enumerate(keys):
        ax = axes[i // ncols][i % ncols]
        vals = [m.get(k) for _, m in rows]
        bars = ax.bar(x, vals, color=["#4C72B0", "#55A868", "#C44E52"][:len(vals)])
        ax.set_xticks(list(x))
        ax.set_xticklabels(stage_labels, rotation=15, ha="right")
        ax.set_ylabel(labels.get(k, _metric_label(k)))
        ax.set_title(labels.get(k, _metric_label(k)))
        ax.grid(True, axis="y", alpha=0.3)
        for bar, v in zip(bars, vals):
            if isinstance(v, (int, float)):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f"{v:.3f}", ha="center", va="bottom", fontsize=8)

    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].set_visible(False)

    fig.suptitle("Fidelity comparison", y=1.02)
    fig.tight_layout()
    path = os.path.join(plots_dir, "fidelity_summary.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return [path]
