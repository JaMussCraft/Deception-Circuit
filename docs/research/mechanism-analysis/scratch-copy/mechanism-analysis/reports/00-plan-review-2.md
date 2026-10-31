# 00 plan review, re-check of the sync (review-00, 2026-10-25)

This is a read-only re-check of `spec.md` (R0-R18), `issues/01..08`, `agent-brief.md` and `reports/00-plan-draft.md`
against `reports/00-plan-review.md`. I read the sync hand-back's change list and spot-checked the code again where a
ticket depends on it.

**Verdict: approve, with four additions to tickets 01, 02a and 08.** The additions can go in as ticket comments while
those tickets run, and none stops them. Each needs to land before the work that consumes it.

## 1. Do B1-B6 land in the spec and in the tickets that implement them?

| blocker | spec | implementing ticket | landed |
| --- | --- | --- | --- |
| B1: null, held-out sample, CIs | §2.2 samples; §2.3 null, bootstrap, ratio of means; §7.10 | 02a (id exclusion), 03 (1C, null groups with a fixed seed) | yes, but see fix 1 |
| B2: post-clause ranking, layer-0 MLP excluded, greedy, B reworded | §2.1, §2.3, §2.9; §7.11 | 02a (range form, exclusion, greedy), 03 (S2p, greedy) | yes |
| B3: exhaustive A′ categories, quantifier, routing | §2.3 table, weighted majority, routing (a)-(c), R14 | 05 (adjudication, routing condition), 03 (routing groups) | yes |
| B4: no-pressure rows under mean | §2.5 decided under zero; §7.14 | 01 (variant-matched bank) | yes, but see fix 2 |
| B5: R-lens wording and clustering | §2.6 exploratory, clause table, clustered bootstrap; §7.6-8, §7.15 | 02a (clause-forms.csv), 03 | yes |
| B6: one gate rule, criteria rulings, sync | §5.4-5, R9, R10, §10 | all tickets, brief, draft | yes |

## 2. R9 phase gate

The gate paragraph is byte-identical, after whitespace normalization, in all 12 documents: the spec, the brief, the
draft and the nine tickets. I checked with a script, not by eye. No "user's go", "user says go" or "HARD STOP"
sentence is left; the only "hard stops" string is a question label in spec §10's table. The criteria-change rule
(R10) reads the same in spec §5.5 and agent-brief, lines 62-66.

## 3. Pile-2 defaults

All thirteen are in the tickets that need them:

- flip-audit paths: 03;
- groups JSON: 02a, 03;
- ratio of means: §2.3;
- signed R-cls: §2.2, 03;
- the `neutral_prompt` trap with a test: 02a;
- the drift H run in the manifest: 02a;
- C1 from the sweeps with U bound: §2.7, 03, 04;
- B-reader binomial: §2.6;
- C-own definition: §2.7, 03;
- ledger lock: brief, 03, 08;
- the cell move before worktree removal: §6, 06;
- Delta H200 for phases 2-3: §5.6;
- pre-clause segment sanity: §2.9, 02a, 04.

## 4. New gaps, and fixes for the tickets that are starting

**Fix 1 (02a): group knockouts must write per-instance values.**

- `knockout.json` today writes the instance ids and summary statistics only (`component_analysis/knockout.py`,
  payload around `:297`).
- R-AB (i) needs the twin's own margin per instance (the denominator of `f_D`), and the per-instance bootstrap needs
  the clean and knocked margins. R-inv's `f_I` needs the same.
- Add to 02a: for every group and sweep row, write per instance the clean margin, the knocked margin and the
  counterfactual stream's full-model margin, the last in the clean labels' direction. The twin's margin is already
  computed in the corrupt-capture forward, which has the Readout residual.

**Fix 2 (01): the variant-matched bank must be opt-in, and record both banks.**

- The ticket asks for v1 mean cells to stay byte-identical, but it does not say how the new bank is switched on.
- Ticket 03 also wants the mean rows reported under "task bank and variant-matched bank both stated".
- Default: a flag. With the flag set, the no-pressure variant side runs twice under mean: once as today, and once
  under a new key with the matched bank. Without the flag, output is unchanged.
- Collect the matched bank over the evaluator's own no-pressure variant loader. Alternatively, assert that those rows
  equal `<t>_v2_nopressure`'s test rows by id. Either way the bank matches exactly the rows it ablates.

**Fix 3 (02a, 03 and spec §2.4): R-inv must compare paired ids.**

- I is a behaviour-filtered subset of D's ids (at least 300 per task). A seed-1 draw from I with the exclusion
  option gives different instances from D's held-out sample, so `f_I` and `f_D` would not be paired.
- Add to 02a an id-inclusion option ("use exactly these ids"), so that 1C computes `f_D` and `f_I` on D's held-out
  ids that also survived I's filter, with n reported.
- Better: replace "the two 95% CIs do not overlap" with a paired bootstrap CI of `f_I - 0.5 f_D` that excludes 0.
  This is a small change to a pre-registered rule, so it needs a dated R-ruling before 1C runs.

**Fix 4 (08): match the inversion clause's form to D's clause.**

- The example I clause ("name the result that is NOT failing") is Predicate-naming. FAR's D clauses are all
  act-naming.
- If every I clause names the Predicate, then `f_I` vs `f_D` on FAR compares two wordings as well as deceptive vs
  transparent. That is the confound R12 moved R-lens to exploratory for.
- Add to 08: the pool has act-naming transparent forms too (for example, "The reviewer is quizzing you and asked
  for the wrong result on purpose."). Each I row uses the form of its D clause, per `clause-forms.csv`, and the
  retention table is split by form.
- This should be settled before 08 writes its pool.

**Non-blocking:**

- **Spec status line.** It still says "awaiting review-00's re-check", while R18 says "approved". Update it after
  this re-check.
- **Lens crossing summary (02a).** R-lens asks whether the margin is below -0.5 "before the final layer's margin
  turns positive". The 02a summary writes the first layer below -0.5 and the final sign, but not the layer of the
  last sign change. Add that layer, or the rule cannot be checked; R-lens is exploratory, so this is cheap to fix.
- **Clause-form rule.** The two clauses overlap: SDR's "keep the critical result hidden and show the wrong one" has
  a Predicate word and "wrong". State the precedence: Predicate-naming first, as the "iff" order implies.
- **1A split cost.** If 01 cannot chain the three schemes in one job, 1A costs about +1.5 reserve. That comes out of
  03's pooled 19.5 GPU-h and squeezes 1B and 1C, since the holdback is 0.75. A three-command sbatch wrapper avoids
  it.
- **Possible gate trigger.** "Instructed-inversion mediators" on two or more tasks would change the paper's headline
  from deception to instructed inversion. Consider adding it to R9's stop list. That is the orchestrator's call.
