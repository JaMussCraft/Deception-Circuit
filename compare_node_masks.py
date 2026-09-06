"""
compare_node_masks.py — compare overlap and differences across saved node circuits.

Takes two or more run directories (or direct paths to active_nodes.json) and
reports how their binary gate masks agree or diverge.

Usage:

    python compare_node_masks.py \\
        outputs/llama-8b-instruct_far/nls0.7_noedge_260819-081750 \\
        outputs/llama-8b-instruct_std/nls0.7_noedge_260721-151636

    python compare_node_masks.py run_a run_b run_c --granularity finest --json overlap.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from evaluation import report
from evaluation.mask_compare import (GRANULARITY_GROUPS, build_report, default_label,
                                     resolve_active_nodes_path)
from evaluation.masks import ALL_KEYS


def build_parser():
    p = argparse.ArgumentParser(
        description="Compare node-pruned circuits saved in active_nodes.json.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("paths", nargs="+",
                   help="Run directories or paths to active_nodes.json (>=2).")
    p.add_argument("--labels", nargs="+", default=None,
                   help="Short names for each input (same order as paths).")
    p.add_argument("--filename", default="active_nodes.json",
                   help="Mask file name when a path is a run directory.")
    p.add_argument("--granularity", default="all",
                   choices=sorted(GRANULARITY_GROUPS),
                   help="Which mask granularities to compare.")
    p.add_argument("--json", dest="json_path", default=None,
                   help="Write the full comparison report to this JSON file.")
    p.add_argument("--plot-dir", default=None,
                   help="Write pairwise Jaccard heatmaps (one PDF per granularity group).")
    p.add_argument("--top-layers", type=int, default=10,
                   help="Per-layer head/neuron diffs to print for pairwise comparisons.")
    return p


def _pairwise_jaccard_matrix(labels, pairwise, key):
    n = len(labels)
    mat = [[1.0 if i == j else float("nan") for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            name = f"{labels[i]} vs {labels[j]}"
            alt = f"{labels[j]} vs {labels[i]}"
            comp = pairwise.get(name) or pairwise.get(alt)
            if not comp:
                continue
            entry = comp["granularities"].get(key)
            if entry and entry.get("compatible", True):
                mat[i][j] = mat[j][i] = entry["jaccard"]
    return mat


def _plot_heatmap(labels, matrix, path, title):
    plt = report._pyplot()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(4, len(labels) * 0.9), max(3.5, len(labels) * 0.8)))
    data = [[0.0 if v != v else v for v in row] for row in matrix]  # nan -> 0 for imshow
    im = ax.imshow(data, vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)
    for i in range(len(labels)):
        for j in range(len(labels)):
            v = matrix[i][j]
            if v == v:
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", color="white", fontsize=7)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Jaccard")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def print_counts(labels, counts):
    report.banner("CIRCUIT SIZES")
    rows = []
    for label in labels:
        c = counts[label]
        finest = sum(c[k]["active"] for k in ("attention_neurons", "mlp_hidden", "mlp_output")
                   if k in c)
        rows.append((label, {"finest_active": finest,
                             "total_active": sum(s["active"] for s in c.values())}))
    report.metric_table(
        [(label, m) for label, m in rows],
        [("finest_active", "finest"), ("total_active", "all gates")],
        title=None,
        label_width=40,
    )


def print_pairwise_summary(labels, pairwise, keys):
    report.banner("PAIRWISE OVERLAP (Jaccard)")
    header_keys = [k for k in keys if any(
        k in comp["granularities"]
        for comp in pairwise.values()
    )]
    rows = []
    for name, comp in sorted(pairwise.items()):
        row = {}
        for key in header_keys:
            entry = comp["granularities"].get(key)
            if entry and entry.get("compatible", True):
                row[key] = entry["jaccard"]
        rows.append((name, row))
    cols = [(k, k[:12]) for k in header_keys]
    report.metric_table(rows, cols, title=None, label_width=44)


def print_pairwise_details(pairwise, top_layers):
    report.banner("PAIRWISE DIFFERENCES")
    for name, comp in sorted(pairwise.items()):
        problems = comp.get("problems") or []
        if problems:
            print(f"\n  {name}")
            for p in problems:
                print(f"    ! {p}")
        for key, entry in sorted(comp["granularities"].items()):
            if not entry.get("compatible", True):
                continue
            if entry.get("identical"):
                continue
            print(f"\n  {name} — {key}")
            print(f"    active: {entry['active_a']:,} vs {entry['active_b']:,}   "
                  f"intersection: {entry['intersection']:,}   "
                  f"only A: {entry['only_a']:,}   only B: {entry['only_b']:,}   "
                  f"Jaccard: {entry['jaccard']:.4f}")
            if entry.get("kind") != "per_layer" or top_layers <= 0:
                continue
            ranked = sorted(
                ((layer, stats) for layer, stats in entry["per_layer"].items()
                 if stats.get("compatible") and stats.get("symmetric_diff", 0)),
                key=lambda kv: kv[1]["symmetric_diff"],
                reverse=True,
            )[:top_layers]
            if not ranked:
                continue
            print(f"    top differing layers (symmetric diff):")
            for layer, stats in ranked:
                print(f"      layer {layer:>3}: diff={stats['symmetric_diff']:,}  "
                      f"Jaccard={stats['jaccard']:.3f}  "
                      f"({stats['active_a']} vs {stats['active_b']} active)")


def print_multi_summary(labels, multi, keys):
    report.banner(f"MULTI-WAY OVERLAP ({len(labels)} circuits)")
    rows = []
    for key in keys:
        entry = multi["granularities"].get(key)
        if not entry or not entry.get("compatible", True):
            continue
        rows.append((key, {
            "all_active": entry.get("all_active", 0),
            "any_active": entry.get("any_active", 0),
            "jaccard": entry.get("jaccard_all_vs_any", float("nan")),
        }))
    report.metric_table(
        rows,
        [("all_active", "all agree"), ("any_active", "any active"), ("jaccard", "Jaccard")],
        title=None,
        label_width=24,
    )


def print_active_summaries(labels, summaries):
    report.banner("COARSE active_heads / active_mlps")
    head = summaries["attention_heads"]
    print("\n  attention heads (per-layer Jaccard averaged over layers with any active head):")
    layer_scores = [v["jaccard"] for v in head["per_layer"].values() if v["union"]]
    avg = sum(layer_scores) / len(layer_scores) if layer_scores else 1.0
    print(f"    mean layer Jaccard: {avg:.4f}")
    for label, n in zip(labels, head["total_active"]):
        print(f"    {label:<40} {n:>6,} active heads")

    mlp = summaries["active_mlps"]
    print(f"\n  active MLP layers: intersection={mlp['intersection']}  "
          f"union={mlp['union']}  Jaccard={mlp['jaccard']:.4f}")
    for label, n in zip(labels, mlp["active_counts"]):
        only = mlp["only_in"][labels.index(label)]
        extra = f"  (only here: {only})" if only else ""
        print(f"    {label:<40} {n:>6}{extra}")


def main(argv=None):
    args = build_parser().parse_args(argv)
    if len(args.paths) < 2:
        build_parser().error("provide at least two paths to compare")

    labels = args.labels or [default_label(p, args.filename) for p in args.paths]
    if len(labels) != len(args.paths):
        build_parser().error("--labels must match the number of paths")

    keys = [k for k in GRANULARITY_GROUPS[args.granularity] if k in ALL_KEYS]
    for path in args.paths:
        resolve_active_nodes_path(path, args.filename)

    report_data = build_report(labels, args.paths, keys=keys, filename=args.filename)

    report.banner("NODE MASK COMPARISON")
    for label, path in zip(labels, report_data["paths"]):
        report.kv(label, path, width=18)

    print_counts(labels, report_data["counts"])
    print_pairwise_summary(labels, report_data["pairwise"], keys)
    print_pairwise_details(report_data["pairwise"], args.top_layers)
    print_multi_summary(labels, report_data["multi"], keys)
    print_active_summaries(labels, report_data["active_summaries"])

    if args.plot_dir:
        os.makedirs(args.plot_dir, exist_ok=True)
        written = []
        for key in keys:
            mat = _pairwise_jaccard_matrix(labels, report_data["pairwise"], key)
            if all(all(v != v for v in row) for row in mat):
                continue
            out = os.path.join(args.plot_dir, f"jaccard_{key}.pdf")
            _plot_heatmap(labels, mat, out, f"Pairwise Jaccard — {key}")
            written.append(out)
        if written:
            report.banner("PLOTS")
            for path in written:
                print(f"  {path}")

    if args.json_path:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_path)) or ".", exist_ok=True)
        with open(args.json_path, "w") as f:
            json.dump(report_data, f, indent=2)
        print(f"\nWrote JSON report to {args.json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
