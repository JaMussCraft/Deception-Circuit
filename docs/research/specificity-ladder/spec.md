# Specificity ladder specification

Authority: the user-approved START.md and subsequent session decisions. This document records implementation choices before scoring new controls. The original phase gates remain binding.

## Question and scope

Test whether a component, direction, or feature is necessary for pressured deception while dispensable for a user-requested transparent inversion, honest and no-pressure answers, and an unrelated task. The old system-turn inversion is a comparison arm only. Deception here is operator-instructed; do not relabel it motive-driven.

A1 builds the control and scores the ladder. A2 trains pressure-versus-neutral and transparent-inversion-versus-neutral masks. A3 begins only after A1 delivers a usable control. START records all stop rules; a null is a valid result, not permission to change thresholds.

## Controls and sampling

Preserve existing D, H and F prompts and labels. Construct user-turn I from the same instance with the neutral H system clause and an explicit transparent request in the actual user role. Construct its neutral-request twin with the same facts, question and assistant stem, matching the quiz and awareness frame and naming both predicates for SDR/SER. It asks to answer the question from the provided information, without an explicit honesty or inversion directive. Record the remaining wording contrast and measure baseline competence. Requests must be task-aware: FAR requests the wrong result; SDR and SER request harmless or favorable selection with transparent framing, without calling a literally true item false.

Prove token alignment for each I/neutral-request twin in both designation streams, or record an explicit position correspondence before interventions. Never bypass old clause-alignment assertions. Any padding must be semantically neutral and recorded. Keep the original H as its own collateral condition. No prompt may be silently truncated; the new-condition token cap is 256, with rejection and counts for overlength rows.

Keep source instance ids and split membership. No validation or test ids enter training. Build all available source splits so A2 does not recycle the historical test-only I condition. Screening requires the target to be full-vocabulary argmax and exceed the distractor by at least 0.7 in both designation streams. If FAR or SER has fewer than 300 test ids, apply 0.5 to the same saved scores; if still insufficient, construct the response-turn fallback and report both sizes. Freeze prompt choices before full scoring and retain every rejection reason.

Select the comparison sample with seed 1 and n=100, exclude component-selection ids, and use matched ids across D, H, F and new I. Keep pool construction separate from component selection. The protected-set registry must be checked immediately before every scoring job; its empty state at startup is not permanent authorization.

## Effects and gates

For each condition C, keep the raw signed target-minus-distractor margin, full-vocabulary argmax accuracy, and binary-choice accuracy. Let G_C be the mean intact margin minus its own intact neutral-twin margin on the same rows. Report fractional removal as the mean intact-minus-intervened margin divided by G_C. Report numerator and denominator separately; nonpositive or numerically negligible G_C makes a fractional gate uninterpretable, never a pass. Pair D with original H, and I with its neutral-request twin.

The START rule requires at least 50 percent removal of D pressure effect, under 25 percent removal of I effect, and under 5 percentage points absolute movement in H, F and unrelated-task accuracy. Full-vocabulary accuracy is the collateral gate; binary accuracy is a diagnostic. Interchange is primary; zero and H-mean interventions are secondary crossed controls. Match the baseline and intervention numerical computation path and include no-op patches.

The crossed design has zero, mean over H, same-item resample from H, and item swap, crossed with the full deciding set and the set minus answer-mover candidates. Mean banks must come from H rather than the recipient condition. Record donor instance, stream and position mapping. An H-to-itself identity patch is a no-op control, not evidence of specificity.

The FAR and SER deciding sets come directly from the recorded greedy_k20 lists in mechanism-analysis phase1/p1c_readings.json. SDR single_k20 is descriptive because it did not pass the earlier mediation criterion. No late-layer group is treated as validated answer movers: the earlier mover hypothesis failed. Freeze a selection-only answer-contribution criterion and the removed intersection before the crossed ladder; it is not yet fixed by this initial control specification.

## Subsequent phase commitments

A2 uses three seeds per task for D-neutral and I-neutral masks, heads plus MLP. The training hinge margin is explicitly 0.7 for both, independent of the historical screening threshold; source screening metadata remains unchanged. Pre-register MLPs 5 through 8 and 11 for FAR/SER clause reading, with 11, 13 and 16 on SER alone. Time one mask before reserving the phase; above 6 GPU-hours use the heads-only fallback. D-minus-I seed stability requires Jaccard at least 0.5 and the A1 rule. At least 90 percent D-head containment in I on every seed is a reportable null.

A3 uses three seeds for difference-of-means directions, random-direction nulls, neuron-range tests restricted to MLPs, and position-aware edge attribution without edge-pruning training. Pass requires the A1 rule and a direction exceeding the 95th percentile of the null. Preserve all START fallbacks and the twin-trained mask comparison.

## Resources and provenance

Total reserved GPU budget is 125 hours: A1 25, A2 60, A3 40. API cap is 10 dollars; concurrent job cap is 99. Train on A40, H200 or H100, never 40 GB A100. Dry-run actual wrappers and reserve observed runtime plus a reasonable buffer. RS owns all ledgers and job records in the primary checkout.

The weekly usage cap is 80 percent. The user applied a temporary 75-point checkpoint cadence until the observed weekly reset. Return to 25 through the human-only command after that reset; do not assume the predicted date is correct.

Current benchmark grader code fingerprint: `866fd15dd30b695e46ffe955b09894fb831af92e2b9015eafbd7f0eee151d2f9`. The independently reviewed formal registry command installed this fingerprint in both primary and worktree registries before benchmark scoring. Local ladder adapter, runner and metric source hashes must additionally be frozen in each run manifest because the shared fingerprint does not cover these new files. The existing hash omits external rubric files, so any benchmark plan must additionally capture those files. EVAL 5 still requires explicit user permission. MMLU sample size and scoring protocol must be fixed before its first run.

## Initial verification baseline

Before implementation, the inversion, matched-honest, contingency, deception-task and mechanism-analysis mean-bank CPU tests gave 205 passing and one failing on both supported interpreters. The failure is tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms (120 versus 128 sequence-length requirement). Logs are /tmp/specificity-baseline-mgnp.log and /tmp/specificity-baseline-base.log. No notebooks were executed.
