"""
evaluation/sanity.py — eval 1: does the saved mask reproduce the run?

Four rows on the task's test set, at the run's own batch size:

    full model (all gates open)     the anchor — must be the plain model
    discovered circuit              the generic prediction-position evaluator
    discovered circuit (repo path)  task.evaluate, i.e. the code the run used
    empty circuit                   all gates closed — calibrates eval 3's floor

Then a delta table against `results.json["node_eval"]`.

The generic-vs-repo cross-check is the load-bearing one: agreeing to 1e-4 on the
same circuit validates the mask loader, the generic evaluator, and the reference
cache in a single assertion. Everything downstream — 50 random circuits, 52
wikitext configurations — runs on that machinery and never gets checked again.
"""

from __future__ import annotations

from evaluation import Evaluation
from evaluation import report
from evaluation.ablation import ablation_hook
from evaluation.context import baseline_numbers, reference_numbers
from evaluation.masks import zeros_like
from evaluation.metrics import evaluate_pred_position

# bf16 kernel selection is not guaranteed stable across processes, so the
# reproduction is checked to a tolerance rather than for equality. Accuracy and
# exact match are integer counts over 1000 samples, hence the 0.002.
REPRODUCTION_TOLERANCES = {
    "accuracy": 0.002,
    "exact_match": 0.002,
    "logit_diff": 0.01,
    "kl_div": 0.005,
}

# Same circuit, same process, two implementations — this is much tighter.
CROSS_CHECK_TOLERANCES = {
    "accuracy": 1e-6,
    "exact_match": 1e-6,
    "logit_diff": 1e-4,
    "kl_div": 1e-4,
}

# What "all gates open == the full model" is allowed to look like in bf16.
ALL_OPEN_TOLERANCES = {"kl_div": 1e-4, "exact_match_min": 0.999}


class SanityEvaluation(Evaluation):
    name = "sanity"
    display_name = "Sanity check — reproduce the in-run numbers"
    requires = ("pred_spec",)

    def run(self, ctx) -> dict:
        loader = ctx.test_loader
        hook = ctx.hook_for("task")
        ref_cache = ctx.ensure_ref_cache()
        rows = {}

        with ctx.all_gates_open():
            rows["full_open"] = evaluate_pred_position(
                ctx, loader, hook=hook, ref_cache=ref_cache,
                desc="full model (all gates open)")

        rows["discovered"] = evaluate_pred_position(
            ctx, loader, hook=hook, ref_cache=ref_cache,
            collect_argmax=True, desc="discovered circuit")

        rows["discovered_repo"] = self._repo_path(ctx, loader, hook)

        with ctx.circuit(zeros_like(ctx.circuit_masks)):
            rows["empty"] = evaluate_pred_position(
                ctx, loader, hook=hook, ref_cache=ref_cache,
                collect_argmax=True, desc="empty circuit")

        payload = {
            "batch_size": loader.batch_size,
            "n": rows["discovered"]["n"],
            "ablation": ctx.cli.ablation,
            "rows": rows,
            "reference": {"node_eval": reference_numbers(ctx),
                          "baseline": baseline_numbers(ctx)},
        }
        payload["cross_check"] = self._cross_check(ctx, rows)
        payload["all_open"] = self._check_all_open(ctx, rows["full_open"])

        expected = payload["reference"]["node_eval"]
        payload["delta"] = report.compute_delta(
            rows["discovered"], expected, REPRODUCTION_TOLERANCES,
            ctx.task.metric_columns) if expected else None
        if payload["delta"] is not None:
            ctx.check(payload["delta"]["ok"],
                      "sanity: the reloaded circuit does not reproduce "
                      "results.json:node_eval within tolerance")

        payload["headline"] = {k: rows["discovered"].get(k)
                               for k, _ in ctx.task.metric_columns}
        payload["verification"] = {
            "masks_roundtrip": bool(ctx.cli.verify),
            "all_open_equals_full": payload["all_open"]["ok"],
            "generic_vs_task_evaluate_max_delta": payload["cross_check"].get("max_delta"),
            "reference_numbers": {
                "source": "results.json:node_eval",
                "expected": expected,
                "observed": payload["headline"],
                "max_delta": payload["delta"]["max_delta"] if payload["delta"] else None,
                "ok": payload["delta"]["ok"] if payload["delta"] else None,
            },
        }
        return payload

    # ------------------------------------------------------------------
    def _repo_path(self, ctx, loader, hook):
        """task.evaluate — the exact call train.py made after pruning."""
        if ctx.reference_model is None:
            print("\n  Skipping the repo-path row: --reference shared has no "
                  "separate full model to hand to task.evaluate, which would "
                  "make it report self-faithfulness (KL 0, exact match 1).")
            return None
        with ablation_hook(ctx.node_model, hook):
            result = ctx.task.evaluate(
                ctx.node_model, "Node-Pruned Circuit (repo path)",
                ctx.reference_model, loader, ctx.device, ctx.tokenizer, ctx.state)
        # `outputs` is a per-sample record list; it belongs in results.json, not
        # in an evaluation payload.
        return {k: v for k, v in result.items() if k != "outputs"}

    def _cross_check(self, ctx, rows):
        repo = rows.get("discovered_repo")
        if repo is None:
            return {"ran": False,
                    "reason": "no separate reference model (--reference shared)"}
        generic = rows["discovered"]
        per_metric, ok, worst = {}, True, 0.0
        for key, tol in CROSS_CHECK_TOLERANCES.items():
            if key not in repo or key not in generic:
                continue
            delta = abs(float(generic[key]) - float(repo[key]))
            passed = delta <= tol
            per_metric[key] = {"generic": generic[key], "repo": repo[key],
                               "delta": delta, "tolerance": tol, "pass": passed}
            ok = ok and passed
            worst = max(worst, delta)
        ctx.check(ok, "sanity: the generic evaluator disagrees with task.evaluate "
                      f"(max delta {worst:.2e})")
        return {"ran": True, "ok": ok, "max_delta": worst, "per_metric": per_metric}

    def _check_all_open(self, ctx, row):
        """All gates open should be the plain model: KL 0, exact match 1.

        Not bit-exact in practice — the dual-stream forward always builds an
        explicit causal mask while the reference model lets SDPA take its
        is_causal fast path, which differs at kernel round-off — so this is a
        tolerance, not an equality.
        """
        kl_ok = row["kl_div"] <= ALL_OPEN_TOLERANCES["kl_div"]
        em_ok = row["exact_match"] >= ALL_OPEN_TOLERANCES["exact_match_min"]
        ok = kl_ok and em_ok
        ctx.check(ok, f"sanity: all gates open is not the full model "
                      f"(KL {row['kl_div']:.2e}, exact match {row['exact_match']:.4f})")
        return {"ok": ok, "kl_div": row["kl_div"],
                "exact_match": row["exact_match"],
                "tolerances": ALL_OPEN_TOLERANCES}

    # ------------------------------------------------------------------
    def report(self, payload, ctx) -> None:
        cols = ctx.task.metric_columns
        rows = payload["rows"]
        report.metric_table(
            [("full model (all gates open)", rows["full_open"]),
             ("discovered circuit", rows["discovered"]),
             ("discovered circuit (repo path)", rows["discovered_repo"]),
             ("empty circuit (all gates closed)", rows["empty"])],
            cols, title=f"EVAL 1 — SANITY CHECK  (n={payload['n']}, "
                        f"batch size {payload['batch_size']})")

        baseline = payload["reference"]["baseline"]
        if baseline:
            print()
            report.metric_table([("in-run baseline (full model)", baseline)], cols)

        if payload["delta"] is not None:
            report.delta_table(payload["delta"])
        else:
            print("\n  results.json has no node_eval — nothing to reproduce "
                  "against (was the run --skip-node-pruning?).")

        cross = payload["cross_check"]
        report.banner("GENERIC EVALUATOR vs task.evaluate", "-")
        if not cross["ran"]:
            print(f"\n  not run: {cross['reason']}")
        else:
            print()
            for key, d in cross["per_metric"].items():
                print(f"  {key:<14} generic {d['generic']:>12.6f}   "
                      f"repo {d['repo']:>12.6f}   |delta| {d['delta']:.2e}   "
                      f"{'PASS' if d['pass'] else 'FAIL'}")
            print(f"\n  {'agreement confirmed' if cross['ok'] else 'DISAGREEMENT'} "
                  f"(max |delta| {cross['max_delta']:.2e})")

        allopen = payload["all_open"]
        print(f"\n  All gates open vs the full model: KL {allopen['kl_div']:.2e}, "
              f"exact match {allopen['exact_match']:.4f}  "
              f"{'PASS' if allopen['ok'] else 'FAIL'}")

        empty = rows["empty"]
        print(f"\n  Empty circuit: accuracy {empty['accuracy']:.4f}, "
              f"logit diff {empty['logit_diff']:+.4f}. This is NOT the corrupt "
              f"model —\n  there is no embedding gate, so the residual stream "
              f"still starts from the clean\n  prompt. It is the floor eval 3's "
              f"null distribution should be read against.")

        if "argmax" in empty:
            report.argmax_table(empty["argmax"],
                                title="ARGMAX DISTRIBUTION — EMPTY CIRCUIT")

    def plots(self, payload, ctx) -> list:
        return []
