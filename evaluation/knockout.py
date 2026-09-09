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

Four sections follow it:

* **The task-side null.** The same random circuits, put through the same
  complement and evaluated on the task test set under pressure. The wikitext
  null says what a random knockout of this size costs elsewhere; this one says
  whether knocking out *any* circuit of this size stops the deception just as
  well. A necessity claim needs both.

* **The flip audit.** Every test example is a behavioural-filter survivor, so
  the full model is deceptive on all of them. Per example the readout is the
  argmax token at the prediction position, which lands on the deceptive answer,
  the honest answer, or neither — so each example either stayed deceptive,
  flipped honest, or left the binary readout entirely. The counts go in the log
  and the full lists in `knockout.json`, for offline pattern analysis.

* **Prompt-variant knockouts.** The same three configurations re-run on the
  same prompts with the pressure clause replaced by an instruction to answer
  honestly, and then with the clause deleted outright. If the circuit is the
  deception mechanism, the behaviour should already be gone before the knockout
  touches it, and the knockout should have little left to take. Note that the
  labels are NOT rebuilt with the prompts — see evaluation/variants.py — so
  "accuracy" there means "still gives the deceptive answer" and the number you
  want is a low one.

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
from evaluation.metrics import (evaluate_task_metrics, summarize_metrics,
                                summarize_null)
from evaluation.wikitext import collateral_damage

# The all-open floor runs the identical harness with nothing ablated, so any
# non-zero KL is harness error, not collateral damage.
FLOOR_TOLERANCES = {"kl_per_token": 1e-4, "ppl_ratio_delta": 1e-4}

#: Prompt variants this evaluation re-runs, in render order.
VARIANTS = ("honest_instruction", "no_pressure")

VARIANT_TITLES = {
    "honest_instruction": "KNOCKOUT UNDER AN HONEST INSTRUCTION",
    "no_pressure": "KNOCKOUT WITH THE PRESSURE CLAUSE DELETED",
}

#: How much of a prompt the flip audit keeps. The pressure clause and the
#: question both live at the end, and 1000 full prompts would dwarf every other
#: number in knockout.json.
EXCERPT_CHARS = 200

#: Verbatim excerpts printed per group in the log. The rest live in the JSON.
LOG_EXCERPTS = 3


def resolve_null_count(cli, n_random: int) -> int:
    """How many random circuits the task-side null evaluates.

    `--knockout-null-count` defaults to "all of them" and is capped at the
    number actually drawn, so `--null-start` / `--null-count` sharding and
    `--n-random 0` both stay coherent without the caller checking.
    """
    requested = getattr(cli, "knockout_null_count", None)
    if requested is None:
        return n_random
    return max(0, min(int(requested), n_random))


def _choice(token_id, target_id, distractor_id) -> str:
    """Which of the two answers a token is: `deceptive`, `honest` or `other`.

    A None token means nothing was observed — there was no reference, so the
    full model's argmax is not known here. That is `unknown`, not `other`: the
    audit distinguishes "the model picked a third token" from "nobody looked",
    so an absent reference cannot be counted as evidence about the model.
    """
    if token_id is None:
        return "unknown"
    if token_id == target_id:
        return "deceptive"
    if token_id == distractor_id:
        return "honest"
    return "other"


def flip_audit(rows, excerpts=None):
    """(per_example, flip_summary) from `evaluate_pred_position` rows.

    `rows` is the knockout pass's `per_example` list, whose `ref_argmax_id` is
    the FULL model's argmax on the same prompt (the reference cache holds the
    full model's logits; with no cache the evaluator takes a live full-model
    forward). So one pass carries both sides of the comparison.

    `n_other` is deliberately not split between the two interesting groups.
    `n_full_not_deceptive` and `n_full_unknown` say how much of it is the full
    model having been observed not to be deceptive here, and how much is a
    full-model choice that was never observed at all, rather than a knockout
    that left the A/B readout.
    """
    per_example, stayed, flipped = [], [], []
    n_other = n_full_not_deceptive = n_full_unknown = 0
    for row in rows:
        target_id, distractor_id = row["target_id"], row["distractor_id"]
        full = _choice(row["ref_argmax_id"], target_id, distractor_id)
        knocked = _choice(row["argmax_id"], target_id, distractor_id)
        if full == "deceptive" and knocked == "deceptive":
            status = "stayed_deceptive"
            stayed.append(row["index"])
        elif full == "deceptive" and knocked == "honest":
            status = "flipped_honest"
            flipped.append(row["index"])
        else:
            status = "other"
            n_other += 1
            n_full_unknown += int(full == "unknown")
            n_full_not_deceptive += int(full in ("honest", "other"))
        per_example.append({
            "example_id": row["index"],
            "prompt_excerpt": (excerpts[row["index"]]
                               if excerpts is not None else None),
            "full_choice": full,
            "knockout_choice": knocked,
            "full_token_id": row["ref_argmax_id"],
            "knockout_token_id": row["argmax_id"],
            "status": status,
        })

    summary = {
        "n_stayed_deceptive": len(stayed),
        "n_flipped_honest": len(flipped),
        "n_other": n_other,
        "n_full_not_deceptive": n_full_not_deceptive,
        "n_full_unknown": n_full_unknown,
        "stayed_ids": stayed,
        "flipped_ids": flipped,
    }
    return per_example, summary


def prompt_excerpts(loader, chars: int = EXCERPT_CHARS):
    """The tail of each example's clean prompt, in loader order, or None.

    Only the tail: the pressure clause and the question live at the end, which
    is what an offline reader of `flipped_ids` wants to look at. Returns None
    when the dataset does not carry `processed_data`, and an entry is None when
    a record has no `clean_prompt` (the synthetic task in the end-to-end test
    has the former and not the latter), so the audit degrades to bare example
    ids rather than failing.
    """
    dataset = getattr(loader, "dataset", None)
    indices = None
    # --test-samples does NOT produce a Subset — it truncates the record list
    # while loading (dataset/std_llama.py:load_std_dataset), so loader position
    # i is dataset position i. This branch is here for any future loader that
    # does wrap a Subset, where position i is dataset position indices[i].
    if dataset is not None and hasattr(dataset, "indices") and hasattr(dataset, "dataset"):
        dataset, indices = dataset.dataset, list(dataset.indices)
    records = getattr(dataset, "processed_data", None)
    if records is None:
        return None
    if indices is None:
        indices = range(len(records))
    out = []
    for i in indices:
        prompt = records[i].get("clean_prompt")
        out.append(None if prompt is None else prompt[-chars:])
    return out


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
        payload["variants"] = {variant: self._variant_side(ctx, variant)
                               for variant in VARIANTS}
        # Kept as an alias: knockout.json readers written against the
        # honest-only layout still find their section where it was. The
        # per-example lists are dropped from the copy — they can be a thousand
        # rows each, and they already live once under `variants`.
        payload["honest"] = {
            k: v for k, v in payload["variants"]["honest_instruction"].items()
            if k not in ("per_example", "flip_summary")}
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
            knocked = evaluate_task_metrics(ctx, loader, desc="knockout",
                                            collect_per_example=ctx.has_pred_spec,
                                            **common)

        per_example, flip_summary, reason = self._flip_audit(ctx, loader, knocked)
        return {
            "circuit": intact,
            "knockout": knocked,
            "per_example": per_example,
            "flip_summary": flip_summary,
            "flip_audit_reason": reason,
            "null": self._task_null(ctx, loader, hook, ref_cache, knocked),
        }

    def _flip_audit(self, ctx, loader, knocked):
        """(per_example, flip_summary, reason) for one knockout pass.

        The rows are popped off the metrics dict: they are a payload section of
        their own, and leaving them inside `knockout` would write the whole list
        into knockout.json twice.
        """
        rows = knocked.pop("per_example", None)
        if rows is None:
            return None, None, (f"{ctx.task.name} does not implement pred_spec, "
                                f"so there is no per-example argmax readout")
        return (*flip_audit(rows, prompt_excerpts(loader)), "")

    def _task_null(self, ctx, loader, hook, ref_cache, knocked):
        """The wikitext null's twin: the same random knockouts, on the task.

        Deliberately cheap — no argmax histogram and no per-example rows, since
        nothing reads them for the null. `verify` is off for the same reason it
        is in eval 3: the masks came from the same sampler the null already
        size-checks.
        """
        count = resolve_null_count(ctx.cli, len(ctx.random_masks))
        rows = []
        for i in range(count):
            index, masks = ctx.random_indices[i], ctx.random_masks[i]
            with ctx.circuit(knockout_masks(masks,
                                            ctx.cli.knockout_granularity)):
                metrics = evaluate_task_metrics(
                    ctx, loader, hook=hook, ref_cache=ref_cache,
                    desc=f"random knockout {i + 1}/{count}")
            rows.append({"index": index,
                         **{k: metrics[k] for k, _ in ctx.task.metric_columns
                            if k in metrics}})

        stats = (summarize_metrics(rows, knocked, ctx.task.metric_columns,
                                   ctx.task.metric_better) if rows else {})
        return {"n": len(rows), "granularity": ctx.cli.knockout_granularity,
                "rows": rows, "stats": stats}

    def _variant_side(self, ctx, variant):
        """The same three configurations on one prompt variant's prompts."""
        loader, reason = ctx.variant_loader(variant)
        if loader is None:
            print(f"\n  {variant} knockout skipped: {reason}")
            return {"variant": variant, "skipped": reason}

        # ref_cache is deliberately NOT ctx.ensure_ref_cache(): that cache holds
        # the full model's logits on the WITH-PRESSURE prompts. Passing None
        # makes evaluate_pred_position take a live full-model forward on this
        # batch, which is the only reference the KL column here can mean — and
        # it is also what makes `ref_argmax_id` the full model's choice on the
        # variant prompt, so the flip audit works here unchanged.
        common = dict(hook=ctx.hook_for("task"), ref_cache=None,
                      collect_argmax=True)
        with ctx.all_gates_open():
            full = evaluate_task_metrics(ctx, loader,
                                         desc=f"{variant}: full model", **common)
        circuit = evaluate_task_metrics(ctx, loader, desc=f"{variant}: circuit",
                                        **common)
        with ctx.circuit(ctx.knockout_masks, verify=ctx.cli.verify):
            knocked = evaluate_task_metrics(ctx, loader,
                                            desc=f"{variant}: knockout",
                                            collect_per_example=ctx.has_pred_spec,
                                            **common)

        per_example, flip_summary, flip_reason = self._flip_audit(
            ctx, loader, knocked)
        return {
            "variant": variant,
            "description": variants.VARIANT_DESCRIPTIONS[variant],
            "label_convention": variants.LABEL_CONVENTION,
            "rows": {"full": full, "circuit": circuit, "knockout": knocked},
            "per_example": per_example,
            "flip_summary": flip_summary,
            "flip_audit_reason": flip_reason,
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

        self._report_flip_audit(task, "FLIP AUDIT — UNDER PRESSURE")
        self._report_wikitext(payload, ctx)
        self._report_task_null(payload, ctx)
        for variant in VARIANTS:
            self._report_variant(payload, ctx, variant)
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

    def _report_task_null(self, payload, ctx) -> None:
        null = payload["task"]["null"]
        if not null["stats"]:
            return
        report.stats_table(
            null["stats"], ctx.task.metric_columns, null["n"],
            title=f"VERSUS SIZE-MATCHED RANDOM KNOCKOUTS — TASK "
                  f"({null['granularity']})")
        print("\n  READ EVERY COLUMN BACKWARDS HERE. `pct` and `z` follow "
              "Task.metric_better,\n  which is written for a circuit that "
              "should REPRODUCE the full model. This\n  knockout is meant to "
              "BREAK it, so on all four metrics the necessity result is\n  a "
              "LOW percentile:\n"
              "    accuracy, logit diff   low pct = less deceptive behaviour "
              "survives the\n"
              "                           circuit's knockout than a random "
              "one's\n"
              "    KL div, exact match    low pct = the circuit's knockout "
              "moved the prediction\n"
              "                           further from the full model's than a "
              "random one did\n"
              "  A high percentile on any of them says a random circuit of this "
              "size would have\n  done the job as well, or better.")

    def _report_flip_audit(self, section, title, note="") -> None:
        summary = section.get("flip_summary")
        if summary is None:
            reason = section.get("flip_audit_reason") or "no per-example readout"
            print(f"\n  Flip audit skipped: {reason}.")
            return

        report.banner(title, "-")
        print(f"\n  stayed deceptive  {summary['n_stayed_deceptive']:>6}")
        print(f"  flipped honest    {summary['n_flipped_honest']:>6}")
        print(f"  other             {summary['n_other']:>6}   "
              f"(of which {summary['n_full_not_deceptive']} the full model was "
              f"observed not to be\n"
              f"                             deceptive on, and "
              f"{summary['n_full_unknown']} where it was never read)")
        print("\n  'other' is every example that left the two-way readout: the "
              "argmax token is\n  neither the deceptive nor the honest answer. "
              "It is reported separately so it\n  cannot inflate either group.")
        if note:
            print(f"\n  {note}")

        excerpts = self._excerpts_by_status(section)
        for status, label in (("stayed_deceptive", "STAYED DECEPTIVE"),
                              ("flipped_honest", "FLIPPED HONEST")):
            shown = excerpts[status][:LOG_EXCERPTS]
            if not shown:
                continue
            print(f"\n  {label} (first {len(shown)} of "
                  f"{len(excerpts[status])}; the full lists are in "
                  f"knockout.json)")
            for example_id, excerpt in shown:
                print(f"    [{example_id}] {excerpt}")

    @staticmethod
    def _excerpts_by_status(section):
        out = {"stayed_deceptive": [], "flipped_honest": []}
        for row in section.get("per_example") or []:
            if row["status"] in out and row["prompt_excerpt"]:
                out[row["status"]].append(
                    (row["example_id"], " ".join(row["prompt_excerpt"].split())))
        return out

    def _report_variant(self, payload, ctx, variant) -> None:
        section = (payload.get("variants") or {}).get(variant)
        if section is None:
            return
        if "skipped" in section:
            print(f"\n  {variant} knockout skipped: {section['skipped']}")
            return

        rows = section["rows"]
        report.metric_table(
            [("full model (all gates open)", rows["full"]),
             ("discovered circuit", rows["circuit"]),
             (f"knockout ({payload['granularity']})", rows["knockout"])],
            ctx.task.metric_columns,
            title=VARIANT_TITLES[variant])

        print(f"\n  Prompts: {section['description']}.")
        print("\n  Labels are NOT rebuilt with the prompts: 'accuracy' is the "
              "rate at which the\n  model still gives the DECEPTIVE answer, so "
              "here a LOW number is the good one\n  and the knockout has less "
              "left to take away than it did under pressure.")
        print("\n  KL is against a LIVE full-model forward on these same "
              "prompts, not the cached\n  with-pressure reference, so the "
              "all-gates-open row must come out at KL 0 and\n  exact match 1.")

        head = section["headline"]
        print(f"\n  HEADLINE  deceptive-answer rate under '{variant}': "
              f"full model {head['full_accuracy']:.4f}, "
              f"knockout {head['knockout_accuracy']:.4f}  "
              f"(drop {head['full_minus_knockout']:+.4f})")

        if "argmax" in rows["knockout"]:
            report.argmax_table(
                rows["knockout"]["argmax"],
                title=f"ARGMAX DISTRIBUTION — {variant.upper()} / KNOCKOUT")

        self._report_flip_audit(
            section, f"FLIP AUDIT — {variant.upper()}",
            note=("'full model' here is the full model on THESE variant "
                  "prompts, not on the\n  with-pressure ones, so a large "
                  "'other' count with most of it in\n  n_full_not_deceptive is "
                  "the variant already having removed the behaviour."))

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
