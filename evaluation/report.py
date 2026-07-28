"""
evaluation/report.py — tables, banners, and figures for the circuit evaluator.

All printing goes through here so the log has one voice, and so an evaluation
module stays about what it measures rather than how it is formatted.
"""

from __future__ import annotations

import os

W = 84


def _pyplot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


# ==============================================================================
# BANNERS AND TABLES
# ==============================================================================

def banner(title: str, char: str = "=") -> None:
    print("\n" + char * W)
    print(f"  {title}")
    print(char * W)


def kv(label: str, value, width: int = 28) -> None:
    print(f"  {label:<{width}} {value}")


def ablation_banner(scheme: str) -> None:
    """Spell out what `--ablation` means, because it is not the same thing in
    every evaluation and the difference is a factor of ~140 in how much of the
    model is being replaced."""
    banner(f"ABLATION SCHEME: {scheme}")
    if scheme == "interchange":
        print("\n  Ablated nodes take their value from the corrupted stream — the "
              "\n  same reference the gates were trained against. This is the only "
              "\n  scheme that can reproduce the in-run numbers.")
        return

    verb = "zeroed" if scheme == "zero" else "replaced by their mean activation"
    print(f"\n  Ablated nodes are {verb}.")
    print("\n  Read the three evaluations differently under this scheme:")
    print("    sanity / null  fill the COMPLEMENT of a ~0.7%-of-model circuit, i.e.")
    print(f"                   they {scheme}-ablate ~99.3% of the model. That is the")
    print("                   standard (much harsher) faithfulness measure, and it")
    print("                   will not reproduce the in-run interchange numbers.")
    print("    knockout       fills the circuit itself — ~0.7% of the model.")


def counts_table(counts: dict, geometry: dict, title: str = "DISCOVERED CIRCUIT") -> None:
    banner(title)
    print(f"\n  {'Granularity':<20} {'Active':>12} {'Total':>12} {'Kept %':>9}")
    print("  " + "-" * 56)
    order = ["layers", "embedding", "attention_blocks", "mlp_blocks",
             "attention_heads", "attention_neurons", "mlp_hidden", "mlp_output"]
    for key in order + [k for k in counts if k not in order]:
        s = counts.get(key)
        if not s or not s["total"]:
            continue
        print(f"  {key:<20} {s['active']:>12,} {s['total']:>12,} "
              f"{s['active'] / s['total'] * 100:>8.3f}%")

    total_active = sum(s["active"] for s in counts.values())
    total_units = sum(s["total"] for s in counts.values())
    print("  " + "-" * 56)
    print(f"  {'TOTAL':<20} {total_active:>12,} {total_units:>12,} "
          f"{total_active / total_units * 100:>8.3f}%")
    print(f"\n  Geometry: {geometry.get('num_layers')} layers x "
          f"{geometry.get('num_heads')} heads x {geometry.get('head_dim')} dims, "
          f"hidden {geometry.get('hidden_size')}, "
          f"intermediate {geometry.get('intermediate_size')}")


def per_layer_table(counts: dict, keys=None, title: str = "PER-LAYER COUNTS") -> None:
    keys = keys or ["attention_heads", "attention_neurons", "mlp_hidden", "mlp_output"]
    keys = [k for k in keys if k in counts]
    layers = sorted({l for k in keys for l in counts[k]["per_layer"]}, key=int)
    if not layers:
        return
    banner(title, "-")
    header = f"  {'Layer':<8}" + "".join(f"{k:>20}" for k in keys)
    print("\n" + header)
    print("  " + "-" * (len(header) - 2))
    for l in layers:
        cells = "".join(f"{counts[k]['per_layer'].get(l, 0):>20,}" for k in keys)
        print(f"  {l:<8}{cells}")
    print("  " + "-" * (len(header) - 2))
    print(f"  {'TOTAL':<8}" + "".join(f"{counts[k]['active']:>20,}" for k in keys))


def metric_table(rows, metric_columns, title=None, label_width=34) -> None:
    """rows: [(label, metrics_dict_or_None)]."""
    if title:
        banner(title)
    header = f"  {'Model':<{label_width}}" + "".join(f"{lbl:>14}" for _, lbl in metric_columns)
    print("\n" + header)
    print("  " + "-" * (len(header) - 2))
    for label, m in rows:
        if m is None:
            print(f"  {label:<{label_width}}" + "".join(f"{'—':>14}" for _ in metric_columns))
            continue
        cells = ""
        for key, _ in metric_columns:
            v = m.get(key)
            cells += f"{v:>14.4f}" if isinstance(v, (int, float)) else f"{'—':>14}"
        print(f"  {label:<{label_width}}{cells}")


def compute_delta(observed: dict, expected: dict, tolerances: dict,
                  metric_columns) -> dict:
    """Compare two metric dicts. Returns {"ok", "max_delta", "rows"}."""
    rows, ok, max_delta = [], True, 0.0
    for key, label in metric_columns:
        if key not in expected or key not in observed:
            continue
        exp, obs = float(expected[key]), float(observed[key])
        delta = obs - exp
        tol = tolerances.get(key)
        passed = tol is None or abs(delta) <= tol
        ok = ok and passed
        max_delta = max(max_delta, abs(delta))
        rows.append({"metric": key, "label": label, "expected": exp,
                     "observed": obs, "delta": delta, "tolerance": tol,
                     "pass": bool(passed)})
    return {"ok": bool(ok), "max_delta": max_delta, "rows": rows}


def delta_table(delta: dict, title="VERSUS THE IN-RUN NODE EVALUATION") -> None:
    banner(title)
    print(f"\n  {'Metric':<20} {'expected':>12} {'observed':>12} "
          f"{'delta':>12} {'tol':>10}   status")
    print("  " + "-" * 74)
    for row in delta["rows"]:
        tol_s = f"{row['tolerance']:.4f}" if row["tolerance"] is not None else "—"
        print(f"  {row['label']:<20} {row['expected']:>12.4f} "
              f"{row['observed']:>12.4f} {row['delta']:>+12.4f} "
              f"{tol_s:>10}   {'PASS' if row['pass'] else 'FAIL'}")
    print("  " + "-" * 74)
    print(f"  {'ALL' if delta['ok'] else 'SOME'} metrics within tolerance "
          f"(max |delta| {delta['max_delta']:.4f})")


def argmax_table(argmax: dict, title="ARGMAX DISTRIBUTION AT THE PREDICTION POSITION") -> None:
    banner(title, "-")
    print(f"\n  distinct tokens: {argmax['n_distinct']}   "
          f"target {argmax['target_frac']:.3f} | "
          f"distractor {argmax['distractor_frac']:.3f} | "
          f"other {argmax['other_frac']:.3f}")
    print(f"\n  {'count':>8}  {'frac':>7}  token")
    print("  " + "-" * 50)
    for row in argmax["top"]:
        print(f"  {row['count']:>8,}  {row['frac']:>7.3f}  {row['token']!r}")


def stats_table(stats: dict, metric_columns, n: int,
                title="RANDOM-CIRCUIT NULL") -> None:
    banner(title)
    print(f"\n  {n} size-matched random circuits\n")
    header = (f"  {'Metric':<14}{'discovered':>12}{'mean':>10}{'std':>10}"
              f"{'min':>10}{'p50':>10}{'p95':>10}{'max':>10}"
              f"{'pct':>7}{'p':>8}{'z':>8}")
    print(header)
    print("  " + "-" * (len(header) - 2))
    for key, label in metric_columns:
        s = stats.get(key)
        if not s:
            continue
        print(f"  {label[:13]:<14}{s['discovered']:>12.4f}{s['mean']:>10.4f}"
              f"{s['std']:>10.4f}{s['min']:>10.4f}{s['p50']:>10.4f}"
              f"{s['p95']:>10.4f}{s['max']:>10.4f}"
              f"{s['percentile']:>6.1f}%{s['p_value']:>8.4f}{s['z']:>8.2f}")
    print("  " + "-" * (len(header) - 2))
    print("  pct = the discovered circuit's percentile in the null "
          "(direction-aware);\n  p = Monte-Carlo p-value (#random at least as "
          "good + 1) / (n + 1);\n  z = (discovered - mean) / std, signed so "
          "positive is better.")


# ==============================================================================
# FIGURES
# ==============================================================================

def plot_null_distribution(stats: dict, rows, metric_columns, path: str,
                           anchors=None, title="Random-circuit null") -> str:
    """One histogram panel per metric: the null, the discovered circuit, the
    95th-percentile region, and the empty / full anchors."""
    plt = _pyplot()
    keys = [(k, lbl) for k, lbl in metric_columns if k in stats]
    if not keys:
        return ""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    ncols = 2 if len(keys) > 1 else 1
    nrows = (len(keys) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 3.6 * nrows),
                             squeeze=False)

    for i, (key, label) in enumerate(keys):
        ax = axes[i // ncols][i % ncols]
        values = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
        s = stats[key]
        ax.hist(values, bins=min(20, max(5, len(values) // 2)),
                color="#B0B7C3", edgecolor="white", label="random circuits")

        better = s.get("better", "higher")
        edge = s["p95"] if better == "higher" else s["p5"]
        lo, hi = (edge, max(values + [s["discovered"]])) if better == "higher" \
            else (min(values + [s["discovered"]]), edge)
        ax.axvspan(lo, hi, color="#55A868", alpha=0.12,
                   label="better than 95% of the null")
        ax.axvline(s["discovered"], color="#C44E52", lw=2,
                   label=f"discovered ({s['discovered']:.4f})")

        for name, value, colour in (anchors or []):
            if isinstance(value, dict):
                value = value.get(key)
            if isinstance(value, (int, float)):
                ax.axvline(value, color=colour, ls="--", lw=1.2, label=name)

        ax.set_xlabel(label)
        ax.set_ylabel("circuits")
        ax.set_title(f"{label}  (pct {s['percentile']:.1f}, p {s['p_value']:.3f})")
        ax.grid(True, alpha=0.25)
        if i == 0:
            ax.legend(fontsize=7, loc="best")

    for j in range(len(keys), nrows * ncols):
        axes[j // ncols][j % ncols].set_visible(False)

    fig.suptitle(title, y=1.01)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_wikitext_null(payload: dict, path: str,
                       title="Wikitext collateral damage") -> str:
    """KL and perplexity ratio for the discovered knockout against the null."""
    plt = _pyplot()
    null_rows = (payload.get("null") or {}).get("rows") or []
    if not null_rows:
        return ""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8), squeeze=False)
    for ax, key, label in ((axes[0][0], "kl_per_token", "KL(full ‖ ablated) per token"),
                           (axes[0][1], "ppl_ratio", "perplexity ratio")):
        values = [r[key] for r in null_rows if isinstance(r.get(key), (int, float))]
        if not values:
            continue
        ax.hist(values, bins=min(20, max(5, len(values) // 2)),
                color="#B0B7C3", edgecolor="white", label="random knockouts")
        disc = (payload.get("discovered") or {}).get(key)
        if isinstance(disc, (int, float)):
            ax.axvline(disc, color="#C44E52", lw=2, label=f"circuit ({disc:.4g})")
        floor = (payload.get("floor") or {}).get(key)
        if isinstance(floor, (int, float)):
            ax.axvline(floor, color="#4C72B0", ls="--", lw=1.2,
                       label=f"all-open floor ({floor:.4g})")
        ax.set_xlabel(label)
        ax.set_ylabel("knockouts")
        ax.grid(True, alpha=0.25)
        ax.legend(fontsize=7)

    fig.suptitle(title, y=1.03)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path
