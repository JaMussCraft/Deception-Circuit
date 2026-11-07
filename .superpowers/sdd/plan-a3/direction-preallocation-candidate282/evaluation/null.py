"""
evaluation/null.py — eval 3: does a size-matched random circuit do just as well?

Draws `--n-random` circuits with exactly the discovered circuit's per-layer
counts at every granularity (blocks held fixed, heads and neurons redrawn) and
evaluates each on the task test set. The discovered circuit passes if its
faithfulness sits above the 95th percentile of that null.

Read the numbers with the two anchors in view. On STD the corrupted stream
carries the *opposite* answer token, so a random circuit inherits corrupt-ish
behaviour and lands near accuracy 0 rather than 0.5 — the pass bar can be met
trivially. That is why the effect size, the Monte-Carlo p-value and the single
best random circuit are reported next to the percentile, with the empty and
full-model rows to calibrate the scale.
"""

from __future__ import annotations

import os

from evaluation import Evaluation
from evaluation import report
from evaluation.masks import count_masks, zeros_like
from evaluation.metrics import evaluate_task_metrics, summarize_metrics

# The granularities ctx.gate_sums() reads back off the GPU.
_GATE_KEYS = ("attention_blocks", "mlp_blocks", "attention_heads",
              "attention_neurons", "mlp_hidden", "mlp_output")


def expected_gate_sums(masks) -> dict:
    counts = count_masks(masks)
    return {k: counts[k]["per_layer"] for k in _GATE_KEYS if k in counts}


class NullEvaluation(Evaluation):
    name = "null"
    display_name = "Random-circuit null"
    requires = ()

    def run(self, ctx) -> dict:
        loader = ctx.fast_loader
        hook = ctx.hook_for("task")
        ref_cache = ctx.ensure_ref_cache()
        common = dict(hook=hook, ref_cache=ref_cache)

        discovered = evaluate_task_metrics(
            ctx, loader, desc="discovered circuit", **common)

        anchors = {}
        with ctx.all_gates_open():
            anchors["full"] = evaluate_task_metrics(
                ctx, loader, desc="full model (all gates open)", **common)
        with ctx.circuit(zeros_like(ctx.circuit_masks)):
            anchors["empty"] = evaluate_task_metrics(
                ctx, loader, desc="empty circuit", **common)

        expected_sums = expected_gate_sums(ctx.circuit_masks)
        rows, size_mismatches = [], []
        for i, (index, masks) in enumerate(zip(ctx.random_indices, ctx.random_masks)):
            with ctx.circuit(masks):
                # The full mask round trip is ~722K comparisons; for the null
                # this cheap invariant (per-granularity per-layer live-gate
                # counts, straight off the GPU) is the thing that actually has
                # to hold, and it catches a mis-applied mask just as well.
                if ctx.gate_sums() != expected_sums:
                    size_mismatches.append(index)
                metrics = evaluate_task_metrics(
                    ctx, loader,
                    desc=f"random circuit {i + 1}/{len(ctx.random_masks)}",
                    **common)
            rows.append({"index": index,
                         **{k: metrics[k] for k, _ in ctx.task.metric_columns
                            if k in metrics}})

        ctx.check(not size_mismatches,
                  f"null: {len(size_mismatches)} random circuits did not load "
                  f"with the discovered circuit's gate counts")

        stats = summarize_metrics(rows, discovered, ctx.task.metric_columns,
                                  ctx.task.metric_better)
        return {
            "n": len(rows),
            "seed": ctx.cli.null_seed,
            "start": ctx.cli.null_start,
            "alloc": ctx.cli.null_alloc,
            "ablation": ctx.cli.ablation,
            "batch_size": loader.batch_size,
            "discovered": discovered,
            "anchors": anchors,
            "rows": rows,
            "stats": stats,
            "size_mismatches": size_mismatches,
            "headline": {k: (stats[k]["percentile"] if k in stats else None)
                         for k, _ in ctx.task.metric_columns},
            "verification": {"null_circuits_size_matched": not size_mismatches},
        }

    def report(self, payload, ctx) -> None:
        cols = ctx.task.metric_columns
        report.stats_table(payload["stats"], cols, payload["n"],
                           title=f"EVAL 3 — RANDOM-CIRCUIT NULL "
                                 f"(alloc {payload['alloc']}, seed {payload['seed']})")

        report.metric_table(
            [("full model (all gates open)", payload["anchors"]["full"]),
             ("discovered circuit", payload["discovered"]),
             ("empty circuit (all gates closed)", payload["anchors"]["empty"]),
             ("best random circuit", self._best_row(payload, ctx)),
             ("mean random circuit", self._mean_row(payload, ctx))],
            cols, title="ANCHORS")

        report.banner("VERDICT", "-")
        print()
        for key, label in cols:
            s = payload["stats"].get(key)
            if not s:
                continue
            verdict = "PASS" if s["passes_95th"] else "fail"
            print(f"  {label:<14} {verdict}  — discovered {s['discovered']:.4f} "
                  f"beats {s['percentile']:.1f}% of the null "
                  f"(best random {s['best']:.4f}, p={s['p_value']:.4f}, "
                  f"z={s['z']:+.2f})")
        print("\n  Pass bar: faithfulness above the 95th percentile of the null.")
        print("  Read it against the anchors above — if the empty circuit already")
        print("  scores near the null's mean, the bar is weak evidence on its own.")

        if payload["size_mismatches"]:
            print(f"\n  !! {len(payload['size_mismatches'])} random circuits did "
                  f"not load with the expected gate counts: "
                  f"{payload['size_mismatches'][:10]}")

        report.per_layer_table(ctx.counts, title="PER-LAYER COUNTS — DISCOVERED")
        if ctx.random_masks:
            report.per_layer_table(
                count_masks(ctx.random_masks[0]),
                title=f"PER-LAYER COUNTS — RANDOM CIRCUIT "
                      f"{ctx.random_indices[0]} (identical by construction)")

    def plots(self, payload, ctx) -> list:
        anchors = [("empty circuit", payload["anchors"]["empty"], "#8172B2"),
                   ("full model", payload["anchors"]["full"], "#4C72B0")]
        path = os.path.join(ctx.plots_dir, "null_distribution.pdf")
        return [report.plot_null_distribution(
            payload["stats"], payload["rows"], ctx.task.metric_columns, path,
            anchors=anchors,
            title=f"Random-circuit null ({payload['n']} circuits, "
                  f"{ctx.cli.ablation} ablation)")]

    # ------------------------------------------------------------------
    def _best_row(self, payload, ctx):
        return {k: payload["stats"][k]["best"] for k, _ in ctx.task.metric_columns
                if k in payload["stats"]}

    def _mean_row(self, payload, ctx):
        return {k: payload["stats"][k]["mean"] for k, _ in ctx.task.metric_columns
                if k in payload["stats"]}
