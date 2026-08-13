"""Shared statistics / reporting helpers for the dataset build scripts.

Extracted from build_std_dataset.py so the deception-mechanism builders
(FAR / SDR / SER) report in exactly the same shape as STD.
"""

import statistics
from collections import defaultdict


def percentile(values, q):
    vals = sorted(values)
    if not vals:
        return None
    idx = min(int(round(q / 100 * (len(vals) - 1))), len(vals) - 1)
    return vals[idx]


def print_token_length_stats(name, lengths):
    if not lengths:
        print(f"\nToken-length statistics — {name}: (no examples)")
        return
    print(f"\nToken-length statistics — {name} (n={len(lengths)}):")
    print(f"  min={min(lengths)}  mean={statistics.mean(lengths):.1f}  "
          f"median={statistics.median(lengths)}  p90={percentile(lengths, 90)}  "
          f"max={max(lengths)}")


def length_summary(lengths):
    """JSON-friendly version of print_token_length_stats.

    Empty input is a real possibility mid-build (a filter can drop an entire
    split), and crashing there would throw away every GPU hour spent so far —
    so it reports n=0 instead of raising.
    """
    if not lengths:
        return {"n": 0, "min": None, "mean": None, "median": None,
                "p90": None, "max": None}
    return {
        "n": len(lengths),
        "min": min(lengths),
        "mean": statistics.mean(lengths),
        "median": statistics.median(lengths),
        "p90": percentile(lengths, 90),
        "max": max(lengths),
    }


def histogram(values):
    """{value: count}, sorted by value — used for the prompt-length histograms."""
    counts = defaultdict(int)
    for v in values:
        counts[v] += 1
    return {k: counts[k] for k in sorted(counts)}


def margin_summary(margins):
    if not margins:
        return {"n": 0, "mean": None, "std": None,
                **{f"p{q}": None for q in (1, 5, 25, 50, 75, 95, 99)}}
    return {
        "n": len(margins),
        "mean": statistics.mean(margins),
        "std": statistics.pstdev(margins) if len(margins) > 1 else 0.0,
        **{f"p{q}": percentile(margins, q) for q in (1, 5, 25, 50, 75, 95, 99)},
    }


def pass_rate_by(records, behaviors, key_fn):
    """Pass-rate per group: {group: {"passed": int, "total": int, "rate": float}}."""
    grouped = defaultdict(lambda: [0, 0])
    for rec, b in zip(records, behaviors):
        g = grouped[key_fn(rec)]
        g[1] += 1
        g[0] += int(b["passed"])
    return {k: {"passed": p, "total": t, "rate": p / t}
            for k, (p, t) in sorted(grouped.items())}


def print_pass_rate_table(title, rates, max_rows=None):
    print(f"\nPass rate by {title}:")
    rows = sorted(rates.items(), key=lambda kv: kv[1]["rate"])
    if max_rows is not None and len(rows) > max_rows:
        shown = rows[:max_rows // 2] + rows[-(max_rows - max_rows // 2):]
        print(f"  (showing {max_rows} lowest/highest of {len(rows)} groups; "
              f"full table in filter_report.json)")
    else:
        shown = rows
    for k, v in shown:
        print(f"  {v['rate']*100:6.1f}%  ({v['passed']:>4}/{v['total']:<4})  {k}")


def plot_margin_distributions(split_behaviors, margin_thresh, out_path,
                              only_passed=False, task_label="STD"):
    """One PDF: a panel per split, overlaid clean/corrupt margin histograms with
    the margin threshold marked. Colors are fixed per stream across panels.
    only_passed=True restricts to examples that survived the behavioral filter."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    if only_passed:
        split_behaviors = {split: [b for b in behaviors if b.get("passed")]
                           for split, behaviors in split_behaviors.items()}

    streams = [("clean_margin", "clean", "#2a78d6"),
               ("corrupt_margin", "corrupt", "#008300")]
    all_margins = [b[k] for behaviors in split_behaviors.values()
                   for b in behaviors for k, _, _ in streams]
    if not all_margins:
        print(f"No {'passing ' if only_passed else ''}examples to plot — "
              f"skipping {out_path}")
        return
    bins = np.linspace(min(all_margins), max(all_margins), 41)

    # Shared bins/x-axis for shape comparison; per-panel y so small splits stay
    # readable next to the 5x-larger test split.
    fig, axes = plt.subplots(1, len(split_behaviors),
                             figsize=(4.5 * len(split_behaviors), 3.5),
                             sharex=True)
    for ax, (split, behaviors) in zip(np.atleast_1d(axes), split_behaviors.items()):
        for key, label, color in streams:
            ax.hist([b[key] for b in behaviors], bins=bins, histtype="stepfilled",
                    alpha=0.35, facecolor=color, edgecolor=color,
                    linewidth=1.5, label=label)
        ax.axvline(0, color="#888888", linewidth=1)
        ax.axvline(margin_thresh, color="#555555", linewidth=1, linestyle="--")
        ax.set_title(f"{split} (n={len(behaviors)})", fontsize=10)
        ax.set_xlabel("logit margin (target − distractor)")
        ax.grid(axis="y", alpha=0.25)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.set_ylabel("examples")
    np.atleast_1d(axes)[0].legend(frameon=False, fontsize=9)
    subset = "filter survivors only" if only_passed else "all generated examples"
    fig.suptitle(f"{task_label} margin distributions — {subset} "
                 f"(dashed line: margin_thresh={margin_thresh})", fontsize=11)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved margin distribution plot to {out_path}")
