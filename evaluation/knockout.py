"""
evaluation/knockout.py — eval 2: is the circuit *necessary*?

Loads the circuit's complement: every gate the circuit uses is closed, and
(under the default `finest` granularity) everything else is open. If the circuit
is what makes the model lie, ablating exactly it should stop the behaviour.

Two things to keep straight while reading the output:

* The knockout model's residual stream is the **clean** stream everywhere. The
  reference only supplies replacement values for the ablated units. This is not
  "run the corrupted prompt".
* The finest-only knockout touches **1.5% of the fine units** (10,640 of
  721,984 on the reference run). If that barely dents behaviour, that is the
  finding — a circuit whose removal costs nothing was not doing the work.

The task-side headline is the argmax-token distribution at the prediction
position: accuracy alone cannot tell "the model now says the honest answer" from
"the model now emits punctuation".

The wikitext side asks what the intervention cost elsewhere, against two
anchors: the all-gates-open floor (which must come out at KL 0) and the same 50
random circuits eval 3 uses, put through the same complement, so the two nulls
are paired.

Two sections follow it:

* **Honest-instruction knockout.** The same knockout re-run on the same prompts
  with the pressure clause replaced by an instruction to answer honestly. If the
  circuit is the deception mechanism, the behaviour should already be gone
  before the knockout touches it, and the knockout should have little left to
  take. Note that the labels are NOT rebuilt with the prompts — see
  evaluation/variants.py — so "accuracy" there means "still gives the deceptive
  answer" and the number you want is a low one.

* **Open generation.** Three greedy wikitext continuations under the full model,
  the knockout, and the circuit alone. Per-token KL says how much the
  distribution moved; only reading the text says whether the model still writes
  English.
"""

from __future__ import annotations

import os

from evaluation import Evaluation
from evaluation import report
from evaluation import variants
from evaluation.masks import knockout_masks, ones_like
from evaluation.metrics import evaluate_task_metrics, summarize_null
from evaluation.wikitext import collateral_damage

# The all-open floor runs the identical harness with nothing ablated, so any
# non-zero KL is harness error, not collateral damage.
FLOOR_TOLERANCES = {"kl_per_token": 1e-4, "ppl_ratio_delta": 1e-4}


class KnockoutEvaluation(Evaluation):
    name = "knockout"
    display_name = "Necessity — knock the circuit out"
    requires = ()

    def run(self, ctx) -> dict:
        fine_total = sum(ctx.counts[k]["total"] for k in
                         ("attention_neurons", "mlp_hidden", "mlp_output")
                         if k in ctx.counts)
        payload = {
            "granularity": ctx.cli.knockout_granularity,
            "ablation": ctx.cli.ablation,
            "counts": {"ablated_fine_units": self._ablated_units(ctx),
                       "total_fine_units": fine_total},
        }
        payload["task"] = self._task_side(ctx)
        payload["wikitext"] = (None if ctx.cli.skip_wikitext
                               else self._wikitext_side(ctx))
        payload["honest"] = self._honest_side(ctx)
        payload["generation"] = self._generation_side(ctx)
        payload["headline"] = {
            "task_accuracy": payload["task"]["knockout"]["accuracy"],
            "wikitext_kl": (payload["wikitext"] or {}).get("discovered", {}).get(
                "kl_per_token"),
            "honest_accuracy_drop": (payload["honest"] or {}).get(
                "headline", {}).get("full_minus_knockout"),
        }
        payload["verification"] = {
            "knockout_is_exact_complement": True,   # asserted in build_context
            "wikitext_floor_is_zero": (payload["wikitext"] or {}).get("floor_ok"),
        }
        return payload

    # ------------------------------------------------------------------
    def _ablated_units(self, ctx):
        return sum(ctx.counts[k]["active"] for k in
                   ("attention_neurons", "mlp_hidden", "mlp_output")
                   if k in ctx.counts)

    def _task_side(self, ctx):
        loader = ctx.fast_loader
        hook = ctx.hook_for("task")
        ref_cache = ctx.ensure_ref_cache()
        common = dict(hook=hook, ref_cache=ref_cache, collect_argmax=True)

        intact = evaluate_task_metrics(ctx, loader, desc="discovered circuit",
                                       **common)
        with ctx.circuit(ctx.knockout_masks, verify=ctx.cli.verify):
            knocked = evaluate_task_metrics(ctx, loader, desc="knockout", **common)
        return {"circuit": intact, "knockout": knocked}

    def _honest_side(self, ctx):
        """The same three configurations on the honest-instruction prompts."""
        loader, reason = ctx.variant_loader("honest_instruction")
        if loader is None:
            print(f"\n  Honest-instruction knockout skipped: {reason}")
            return {"skipped": reason}

        # ref_cache is deliberately NOT ctx.ensure_ref_cache(): that cache holds
        # the full model's logits on the WITH-PRESSURE prompts. Passing None
        # makes evaluate_pred_position take a live full-model forward on this
        # batch, which is the only reference the KL column here can mean.
        common = dict(hook=ctx.hook_for("task"), ref_cache=None,
                      collect_argmax=True)
        with ctx.all_gates_open():
            full = evaluate_task_metrics(ctx, loader, desc="honest: full model",
                                         **common)
        circuit = evaluate_task_metrics(ctx, loader, desc="honest: circuit",
                                        **common)
        with ctx.circuit(ctx.knockout_masks, verify=ctx.cli.verify):
            knocked = evaluate_task_metrics(ctx, loader, desc="honest: knockout",
                                            **common)

        return {
            "variant": "honest_instruction",
            "description": variants.VARIANT_DESCRIPTIONS["honest_instruction"],
            "label_convention": variants.LABEL_CONVENTION,
            "rows": {"full": full, "circuit": circuit, "knockout": knocked},
            "headline": {
                "full_accuracy": full["accuracy"],
                "knockout_accuracy": knocked["accuracy"],
                "full_minus_knockout": full["accuracy"] - knocked["accuracy"],
            },
        }

    def _generation_side(self, ctx):
        """Three wikitext continuations per configuration, or a skip reason."""
        n = getattr(ctx.cli, "gen_examples", 0)
        if not n:
            return None
        if ctx.cli.skip_wikitext:
            reason = "--skip-wikitext was passed, so there are no prompts to continue"
            print(f"\n  Generation examples skipped: {reason}")
            return {"skipped": reason}
        from evaluation.generation import generation_examples
        return generation_examples(ctx, n, ctx.cli.gen_new_tokens)

    def _wikitext_side(self, ctx):
        hook = ctx.hook_for("wikitext")

        # Configuration order does not matter (batches are the outer loop), but
        # keeping the floor first makes a failure obvious in the log.
        configs = [("floor", ones_like(ctx.circuit_masks)),
                   ("discovered", ctx.knockout_masks)]
        for index, masks in zip(ctx.random_indices, ctx.random_masks):
            configs.append((f"random-{index}",
                            knockout_masks(masks, ctx.cli.knockout_granularity)))

        results = collateral_damage(ctx, configs, hook=hook,
                                    desc="wikitext collateral damage")

        rows = [{"index": index, **results[f"random-{index}"]}
                for index in ctx.random_indices]
        discovered = results["discovered"]
        floor = results["floor"]

        floor_ok = (floor["kl_per_token"] <= FLOOR_TOLERANCES["kl_per_token"]
                    and abs(floor["ppl_ratio"] - 1.0)
                    <= FLOOR_TOLERANCES["ppl_ratio_delta"])
        ctx.check(floor_ok,
                  f"knockout: the all-gates-open wikitext floor is not zero "
                  f"(KL {floor['kl_per_token']:.3e}, "
                  f"ppl ratio {floor['ppl_ratio']:.6f})")

        stats = {}
        if rows:
            for key in ("kl_per_token", "ppl_ratio"):
                stats[key] = summarize_null([r[key] for r in rows],
                                            discovered[key], better="lower")

        return {
            "blocks": ctx.cli.wikitext_blocks,
            "block_size": ctx.cli.wikitext_block_size,
            "pairing_seed": ctx.cli.wikitext_seed,
            "discovered": discovered,
            "floor": floor,
            "floor_ok": floor_ok,
            "null": {"rows": rows, "stats": stats},
            "verification": {"wikitext_floor_is_zero": floor_ok},
        }

    # ------------------------------------------------------------------
    def report(self, payload, ctx) -> None:
        cols = ctx.task.metric_columns
        task = payload["task"]
        report.metric_table(
            [("discovered circuit", task["circuit"]),
             (f"knockout ({payload['granularity']})", task["knockout"])],
            cols, title=f"EVAL 2 — NECESSITY  "
                        f"({payload['counts']['ablated_fine_units']:,} fine units "
                        f"ablated)")

        share = (payload["counts"]["ablated_fine_units"]
                 / max(payload["counts"]["total_fine_units"], 1) * 100)
        print("\n  The knockout model's residual stream is the CLEAN stream "
              "everywhere; the\n  reference only supplies replacement values for "
              "the ablated units. It touches\n  "
              f"{share:.2f}% of the fine units — if that barely dents behaviour, "
              f"that is the\n  finding, not a bug.")

        if "argmax" in task["knockout"]:
            report.argmax_table(task["knockout"]["argmax"],
                                title="ARGMAX DISTRIBUTION — KNOCKOUT")

        self._report_wikitext(payload, ctx)
        self._report_honest(payload, ctx)
        self._report_generation(payload, ctx)

    # ------------------------------------------------------------------
    def _report_wikitext(self, payload, ctx) -> None:
        wiki = payload["wikitext"]
        if wiki is None:
            print("\n  Wikitext collateral damage skipped (--skip-wikitext).")
            return

        report.banner(f"COLLATERAL DAMAGE ON WIKITEXT "
                      f"({wiki['blocks']} x {wiki['block_size']} tokens)")
        header = (f"  {'Configuration':<26}{'KL/token':>12}{'± SEM':>10}"
                  f"{'ppl full':>11}{'ppl abl.':>11}{'ratio':>9}")
        print("\n" + header)
        print("  " + "-" * (len(header) - 2))
        for label, row in (("all gates open (floor)", wiki["floor"]),
                           ("circuit knockout", wiki["discovered"])):
            print(f"  {label:<26}{row['kl_per_token']:>12.5f}"
                  f"{row['kl_sem']:>10.5f}{row['ppl_full']:>11.3f}"
                  f"{row['ppl_ablated']:>11.3f}{row['ppl_ratio']:>9.4f}")

        stats = wiki["null"]["stats"]
        if stats:
            mean_row = {k: stats[k]["mean"] for k in stats}
            print(f"  {'random knockouts (mean)':<26}"
                  f"{mean_row.get('kl_per_token', float('nan')):>12.5f}"
                  f"{'—':>10}{'—':>11}{'—':>11}"
                  f"{mean_row.get('ppl_ratio', float('nan')):>9.4f}")
        print("  " + "-" * (len(header) - 2))
        print(f"  all-open floor: KL {wiki['floor']['kl_per_token']:.3e}, "
              f"ppl ratio {wiki['floor']['ppl_ratio']:.6f}  "
              f"{'PASS' if wiki['floor_ok'] else 'FAIL'}")
        print(f"  tokens scored: {wiki['discovered']['n_tokens']:,}")

        if stats:
            report.banner("VERSUS SIZE-MATCHED RANDOM KNOCKOUTS", "-")
            print()
            for key, label in (("kl_per_token", "KL per token"),
                               ("ppl_ratio", "perplexity ratio")):
                s = stats[key]
                print(f"  {label:<18} circuit {s['discovered']:>10.5f}   "
                      f"null {s['mean']:>10.5f} ± {s['std']:.5f}   "
                      f"pct {s['percentile']:>5.1f}   p {s['p_value']:.4f}   "
                      f"z {s['z']:+.2f}")
            print("\n  'better' here means LESS damage, so a low percentile means "
                  "the circuit's\n  knockout costs MORE than a random one of the "
                  "same size — which, for a\n  necessity claim, is the direction "
                  "you want.")

    def _report_honest(self, payload, ctx) -> None:
        honest = payload["honest"]
        if honest is None:
            return
        if "skipped" in honest:
            print(f"\n  Honest-instruction knockout skipped: {honest['skipped']}")
            return

        rows = honest["rows"]
        report.metric_table(
            [("full model (all gates open)", rows["full"]),
             ("discovered circuit", rows["circuit"]),
             (f"knockout ({payload['granularity']})", rows["knockout"])],
            ctx.task.metric_columns,
            title="KNOCKOUT UNDER AN HONEST INSTRUCTION")

        print(f"\n  Prompts: {honest['description']}.")
        print("\n  Labels are NOT rebuilt with the prompts: 'accuracy' is the "
              "rate at which the\n  model still gives the DECEPTIVE answer, so "
              "here a LOW number is the good one\n  and the knockout has less "
              "left to take away than it did under pressure.")
        print("\n  KL is against a LIVE full-model forward on these same "
              "prompts, not the cached\n  with-pressure reference, so the "
              "all-gates-open row must come out at KL 0 and\n  exact match 1.")

        head = honest["headline"]
        print(f"\n  HEADLINE  deceptive-answer rate under the honest "
              f"instruction: full model {head['full_accuracy']:.4f}, "
              f"knockout {head['knockout_accuracy']:.4f}  "
              f"(drop {head['full_minus_knockout']:+.4f})")

        if "argmax" in rows["knockout"]:
            report.argmax_table(rows["knockout"]["argmax"],
                                title="ARGMAX DISTRIBUTION — HONEST / KNOCKOUT")

    def _report_generation(self, payload, ctx) -> None:
        gen = payload["generation"]
        if gen is None:
            return
        if "skipped" in gen:
            print(f"\n  Generation examples skipped: {gen['skipped']}")
            return
        from evaluation.generation import report_generations
        report_generations(gen, report)

    def plots(self, payload, ctx) -> list:
        wiki = payload["wikitext"]
        if not wiki or not wiki["null"]["rows"]:
            return []
        path = os.path.join(ctx.plots_dir, "wikitext_null.pdf")
        return [report.plot_wikitext_null(
            {"discovered": wiki["discovered"], "floor": wiki["floor"],
             "null": wiki["null"]}, path,
            title=f"Wikitext collateral damage ({ctx.cli.ablation} ablation)")]
