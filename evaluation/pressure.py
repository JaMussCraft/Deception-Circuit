"""
evaluation/pressure.py — eval 4: does the behaviour need the pressure clause?

The deception tasks lie because the system turn tells them to. That leaves an
obvious confound in every other evaluation: a "deception circuit" might just be
the circuit that reads the last clause of the system prompt. This evaluation
takes the same test set, swaps the pressure clause out, and re-reads the same
prediction position:

  with_pressure       the trained test set, unchanged — the anchor
  no_pressure         the clause deleted, nothing in its place
  honest_instruction  the clause replaced by "answer honestly ..."

Two configurations per variant: the full model (every gate open) and the intact
circuit. There is no knockout row — the question here is what the *behaviour*
does when the prompt stops asking for it, not what removing the circuit costs.

    THE METRICS READ BACKWARDS. Labels are not rebuilt with the prompts, so
    `target` is still the deceptive answer word. Accuracy means "still gives
    the deceptive answer", and the result you want is accuracy FALLING and
    logit_diff going NEGATIVE relative to the with_pressure anchor.

Only accuracy and logit_diff are reported. KL and exact-match are omitted on
purpose: both are defined against the full model on the *same* batch, and the
full model under a variant is a different distribution from the full model
under pressure, so a "KL" column here would invite exactly the cross-variant
comparison it cannot support. The argmax distribution is collected instead —
if accuracy falls it says whether the model switched to the honest answer or
simply stopped answering.

Under `--ablation mean` the mean bank is the one collected on the with-pressure
prompt distribution and is reused for the variants. The replacement values are
therefore slightly off-distribution for the variant rows; this is noted in the
report rather than fixed, because a per-variant bank would make the rows
incomparable to every other evaluation in the run.
"""

from __future__ import annotations

from evaluation import Evaluation
from evaluation import report
from evaluation import variants
from evaluation.metrics import evaluate_pred_position

#: with_pressure first: it is the anchor every other row is read against.
VARIANT_ORDER = ("with_pressure",) + variants.PROMPT_VARIANTS

#: The two metrics this evaluation defines. See the module docstring for why
#: KL and exact-match are not here.
METRIC_COLUMNS = (("accuracy", "accuracy"), ("logit_diff", "logit diff"))

CONFIG_LABELS = {"full": "full model (all gates open)",
                 "circuit": "discovered circuit"}


class PressureEvaluation(Evaluation):
    name = "pressure"
    display_name = "Pressure-clause ablation — does the behaviour need the clause?"
    requires = ("pred_spec", "prompt_variants")

    def run(self, ctx) -> dict:
        payload = {
            "ablation": ctx.cli.ablation,
            "label_convention": variants.LABEL_CONVENTION,
            "variant_descriptions": {v: variants.VARIANT_DESCRIPTIONS[v]
                                     for v in VARIANT_ORDER},
            "metrics": ["accuracy", "logit_diff"],
            "variants": {},
            "skipped": {},
        }

        hook = ctx.hook_for("task")
        for variant in VARIANT_ORDER:
            loader, reason = self._loader(ctx, variant)
            if loader is None:
                print(f"\n  Skipping variant '{variant}': {reason}")
                payload["skipped"][variant] = reason
                continue

            rows = {}
            # use_reference=False: no full-model forward is needed for accuracy
            # or logit_diff, and the cached reference logits belong to the
            # with-pressure prompts, so they would be wrong here anyway.
            common = dict(use_reference=False, collect_argmax=True)
            with ctx.all_gates_open():
                rows["full"] = evaluate_pred_position(
                    ctx, loader, desc=f"{variant}: full model", **common)
            rows["circuit"] = evaluate_pred_position(
                ctx, loader, hook=hook, desc=f"{variant}: circuit", **common)
            payload["variants"][variant] = rows

        payload["headline"] = self._headline(payload)
        return payload

    # ------------------------------------------------------------------
    def _loader(self, ctx, variant):
        """(loader, reason). The anchor is the ordinary test set."""
        if variant == "with_pressure":
            return ctx.fast_loader, ""
        return ctx.variant_loader(variant)

    def _headline(self, payload):
        """How far the intact circuit's logit diff moved under honesty."""
        got = payload["variants"]
        anchor = got.get("with_pressure", {}).get("circuit")
        honest = got.get("honest_instruction", {}).get("circuit")
        if anchor is None or honest is None:
            return {"circuit_logit_diff_with_pressure": None,
                    "circuit_logit_diff_honest_instruction": None,
                    "delta": None}
        return {
            "circuit_logit_diff_with_pressure": anchor["logit_diff"],
            "circuit_logit_diff_honest_instruction": honest["logit_diff"],
            "delta": honest["logit_diff"] - anchor["logit_diff"],
        }

    # ------------------------------------------------------------------
    def report(self, payload, ctx) -> None:
        rows = []
        for variant in VARIANT_ORDER:
            got = payload["variants"].get(variant)
            if got is None:
                rows.append((f"{variant} — skipped", None))
                continue
            for config in ("full", "circuit"):
                rows.append((f"{variant} / {CONFIG_LABELS[config]}", got[config]))
        report.metric_table(rows, METRIC_COLUMNS,
                            title="EVAL 4 — PRESSURE-CLAUSE ABLATION")

        print("\n  Labels are NOT rebuilt with the prompts: 'accuracy' is the "
              "rate at which the\n  model still gives the DECEPTIVE answer, and "
              "logit diff is logit(deceptive) -\n  logit(honest). Falling "
              "accuracy and a negative logit diff are the result you\n  want — a "
              "circuit whose numbers do not move when the pressure is removed "
              "was\n  not reading the pressure.")
        if payload["ablation"] == "mean":
            print("\n  --ablation mean: the mean bank was collected on the "
                  "with-pressure prompts and\n  reused for the variants, so the "
                  "variant rows' replacement values are slightly\n  "
                  "off-distribution.")

        for variant in VARIANT_ORDER:
            print(f"\n  {variant}: "
                  f"{payload['variant_descriptions'][variant]}")
            reason = payload["skipped"].get(variant)
            if reason:
                print(f"    skipped — {reason}")

        head = payload["headline"]
        if head["delta"] is not None:
            print(f"\n  HEADLINE  intact circuit logit diff: "
                  f"with pressure {head['circuit_logit_diff_with_pressure']:+.4f}"
                  f"  ->  honest instruction "
                  f"{head['circuit_logit_diff_honest_instruction']:+.4f}"
                  f"   (delta {head['delta']:+.4f})")

        for variant in VARIANT_ORDER:
            got = payload["variants"].get(variant)
            if got and "argmax" in got["circuit"]:
                report.argmax_table(
                    got["circuit"]["argmax"],
                    title=f"ARGMAX DISTRIBUTION — {variant.upper()} / CIRCUIT")
