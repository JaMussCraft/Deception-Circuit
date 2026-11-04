# Spec: neuron-partition (frozen exit criteria)

Frozen on Tue 3 Nov 2026 by session claude-5201d56c before the first GPU job. The exit criteria below are copied
verbatim from item 10 of `START.md`. Changes are dated rulings in the Rulings section; the frozen text is never edited.

## Exit criteria (item 10 of START.md, verbatim)

10. **Exit criteria.** Frozen before the first GPU job; changes are dated rulings in `spec.md`.
    - **Tasks.** FAR primary (act-naming clauses only), SER secondary, SDR out.
    - **Ids.** Rank on the train and validation splits; ablate on a fresh test sample of at least 300 rows per
      condition drawn with seed 2, excluding A1's 100 assessment ids and the mechanism-analysis held-out samples;
      record `dataset_files` in `run_manifest.json`.
    - **Ablation.** Three references. (1) Neutral-twin interchange at neuron level, the primary: for each instance the
      chosen neurons' activations in the D run are replaced by their values from the H-twin run of the same instance
      (and in the I run by the user-neutral twin's), extending the `neutral_twin` path of `component_analysis/knockout.py`
      to the `mlp_hidden` kind with tests on both interpreters. (2) Mean ablation from the no-pressure mean bank.
      (3) Zero ablation. Report disagreement among the three. The
      effect measures are the ladder's: the D effect is p(deceptive answer under D) minus p(deceptive answer under H),
      the I effect is the same for I against user-neutral, with the one-token readout at margin 0.7.
    - **Nulls.** At least 20 random neuron sets matched on size and per-layer count, scored on every metric
      including H, F and IOI accuracy.
    - **N1 pass (deception-specific).** A D-only set of at most 2,000 neurons removes at least 50 percent of the D
      effect, under 25 percent of the I effect, moves H, F and IOI accuracy by under 5 points each, and beats the 95th
      percentile of the matched null on D-effect removal, under neutral-twin interchange and under mean ablation, in
      both split halves. **Fail.** No set meets all of these: record a reviewed null "no deception-specific MLP neuron
      set at this granularity under the ladder rule, outside the A3 cell". Partial passes (one reference, one half)
      are recorded as leads, not passes. If the twin wiring never lands, the pass needs mean and zero instead, and the
      finding says so.
    - **N2 pass (honest bypass).** Ablating the H-only set drops H accuracy by at least 20 points while D's deceptive
      rate moves under 5 points and the matched null moves H accuracy under 5 points. **Suppression or shared.**
      D's deceptive rate also falls by at least 10 points. Anything else is "undetermined at this size".
    - **N3.** Report split-half Jaccard for every class against the same-condition ceiling and the IOI floor; a class is
      called stable only if its Jaccard is at least half the ceiling. The rotation test is descriptive.
    - **Done.** N1 and N2 have run on FAR with the twin interchange and mean ablation and the stability report exists;
      SER is a bonus.
      **Stop.** The 20 GPU-hour cap, or 36 wall-clock hours from launch, whichever comes first; hand back what exists.


## Grader

No benchmark grader is frozen for this direction: every readout is the one-token readout (target minus distractor
logit difference and the margin rule of the specificity ladder), and no EVAL 5 or judge run is planned. If a
benchmark run becomes necessary, the grader hash is frozen with `research-session freeze-grader` and recorded here
as a ruling before that run.

## Operational definitions (recorded Tue 3 Nov 2026, before the first GPU job)

- **Neuron.** One of the 32 by 14,336 inputs of the MLP down-projection after the SwiGLU gate (the `mlp_hidden`
  unit of the leaf gates in `models/llama_node.py`).
- **Conditions.** D is the `far_v2` pressured prompt; H is its neutral twin from `far_v2_honest`; F is
  `far_v2_nopressure`; I is the user-turn transparent inversion pool and its user-neutral twin from the ladder's A1
  control cell, read in place and recorded by path and sha256 in the manifest.
- **Effect sizes.** The D effect is p(deceptive answer under D) minus p(deceptive answer under H); the I effect is
  p(inverted answer under I) minus p(inverted answer under user-neutral). "Deceptive answer" is the one-token readout
  choosing the target over the distractor at margin 0.7, as the ladder defines it. "Removed" is the fraction of the
  intact effect that the ablation takes away.
- **Collateral.** H, F and IOI accuracy are the one-token accuracies on the fresh test sample (H and F) and on the
  project's IOI set.
- **Matched null.** Random neuron sets with the same size and the same per-layer counts as the tested set, at
  least 20 draws, seeded, scored on every metric.

## Rulings

- **R1 (Tue 3 Nov 2026).** The frozen text is item 10 of START.md as above; no change yet.
- **R2 (Tue 3 Nov 2026, before the first GPU job): effect measure.** Item 10 says "the effect measures are the
  ladder's" and paraphrases them as a rate difference at margin 0.7. The reader brief (reports/00-reader-brief.md,
  section 2) shows the ladder's measure is the margin effect: per row and stream, m = logit(opposite) minus
  logit(honest) in float32 at the readout token, in D's orientation; the intact effect is G = mean(m_intact minus
  m_intact of the twin), averaged over both streams within an id; the fraction removed is mean(m_intact minus
  m_patched) divided by G. Margin 0.7 is only the pool screen, so under the rate reading the intact effect is 1.0 by
  construction. Ruling: the pass bars of item 10 (50 percent of the D effect, 25 percent of the I effect, the null's
  95th percentile) are read on the ladder's margin effect, the primary measure. The rate difference at margin 0.7
  (p(deceptive under D) minus p(deceptive under H), and the same for I against user-neutral) is stored from the
  same logits and reported beside it as the secondary measure. The collateral bars (H, F and IOI accuracy under 5
  points) stay rate measures. Every result table shows both.
- **R3 (Tue 3 Nov 2026): mean bank.** The no-pressure mean bank for mean ablation is collected on the F train and
  validation splits (as the ladder built its bank), never on the test split that holds the excluded ids.
- **R4 (Tue 3 Nov 2026): IOI.** The IOI adapter exists only in the Codex worktree and is rebuilt from the recipe in
  the reader brief, section 4, with its intact accuracy checked against the brief's 0.51 on 100 rows before use.
- **R5 (Tue 3 Nov 2026): assessment ids.** A1's 100 assessment ids per task are read from the ladder's design file
  named in the reader brief, section 3, not from the a1-full directory that START names.
- **R6 (Tue 3 Nov 2026, before any ablation cell): partition rule.** Three signed scores per neuron, each the
  attribution-patching mean over the ranking rows at the readout position: s_D from the D-versus-H run with D as
  the clean stream (positive means the neuron supports the deceptive answer), s_I from the I-versus-user-neutral run
  with I clean (positive supports the inverted answer), and s_H from the reverse run with H as the clean stream and
  D as the twin, with its sign flipped so that positive means the neuron supports the honest answer. For a size k
  taken from the ladder 500, 1,000 and 2,000, T_D, T_I and T_H are the top-k neurons by each signed score (positive
  only). Classes: D-only = T_D minus (T_I union T_H); D-and-I shared = (T_D intersection T_I) minus T_H; H-only =
  T_H minus (T_D union T_I); all-shared = T_D intersection T_I intersection T_H. Every class is ablated at every k
  of the ladder on the seed-2 test sample with its own size-and-layer-matched null, and the pass bars of item 10
  are read at each k; the finding reports every k and never picks k on the test sample. The activation-contrast
  ranking is the comparison, built with the same rule from the contrast mean.
- **R7 (Tue 3 Nov 2026, before the first ablation cell): collateral under the twin reference.** F and IOI have no
  neutral twin, so the collateral bars of item 10 (H, F and IOI accuracy under 5 points) are read under the mean
  reference for every tested set; under the twin reference the H collateral is the reverse patch and is descriptive.
  The finding says so.
- **R8 (Tue 3 Nov 2026): the rate effect under mean and zero.** The ablated D rate is compared with the ablated H
  rate (the effect inside the ablated model); the comparison against intact H is written beside it and is
  descriptive.
- **R9 (Tue 3 Nov 2026): operational.** Ablation cells pass `--max-length 128` (lossless: any truncation raises);
  rows.jsonl stays in outputs and is never committed; the IOI rows follow the reader brief's recipe and are not shown
  to be the ladder's own 100 rows.
- **R10 (Tue 3 Nov 2026, before the first ablation cell): "in both split halves".** The N1 pass clause "in both
  split halves" is read on the seed-2 test sample: its ids are split into two halves with seed 2 (stratified the way
  W3's rank halves are), and a class must meet every bar on each half as well as on the whole sample. Ranking
  stability across the rank halves is N3's report and does not enter the N1 pass.
- **R11 (Tue 3 Nov 2026, before the first ablation cell, from review 01 major 1): ranking position.** The twin
  interchange writes every position, so the primary ranking score is the attribution summed over every position of
  the prompt (the "all-position" key), which estimates that ablation; the readout-position score of R6 becomes the
  comparison ranking beside the activation contrast. Everything else in R6 is unchanged. Review 01 major 2 (the
  deception and honest scores share the activation difference and agree in sign on only 63 of the top 100) is
  recorded as a known property; a direct one-neuron interchange check on the top neurons by each score is
  descriptive if run.
- **R12 (Tue 3 Nov 2026): the test sample also excludes the ladder's 100 selection ids.** W3's sample excluded
  the union of A1's assessment ids, the ladder's selection ids and the two mechanism-analysis held-out samples
  (356 ids), one list more than R5 names. The sample stands as drawn: the extra exclusion only removes ids the
  ladder tuned on, and 644 D and 566 I rows remain eligible.
- **R13 (Tue 3 Nov 2026, 6:30 pm EST, after the cells): the N1 decision stands as failed; the size-500 result is
  a descriptive lead.** The all-position deception-only class at size 500 met every N1 bar except IOI (minus 6.0
  points against 5, on 100 IOI rows where matched random sets moved IOI by minus 3 to plus 6). The bars are not
  changed. One exploratory, not pre-registered measurement is run: the same class and its 20 nulls on the largest
  IOI row set the recipe supports (up to 1,000 rows), IOI condition and mean reference only, to report what 100
  rows could resolve. Its result is descriptive and does not alter N1; a follow-up would need its own
  pre-registered bars.
- **R14 (Tue 3 Nov 2026, 8:30 pm EST, before any draw): pre-registered confirmation test of the size-500 lead.**
  Fixed, unchanged inputs: the all-position deception-only class at size 500 (338 neurons, from
  `sets/far_atp_all_c3d7763/far_all_sets_k500_with_nulls.json`) and its 20 matched nulls, as held in
  `outputs/_analyses/neuron-partition/ablation/ioi_resolution_sets.json`. Fresh data, drawn only after this ruling:
  a seed-3 test sample by W3's balanced sampler from the eligible test pools after removing the 356 excluded ids and
  every id of the seed-2 sample from every pool (fully fresh instances), taking every eligible id: 208 rows each for
  D, H and F and 166 each for I and N; and 1,000 fresh IOI rows drawn with IOI seed 2, any sentence shared with the
  seed-1 draw dropped and counted. The bars are those of item 10 N1, unchanged and read on the point estimate as the
  verdict script reads them: under the twin interchange and under the mean reference, each on the whole sample and
  on both seed-3 halves (R10), the class removes at least 0.50 of the deception margin effect (R2), removes under
  0.25 of the inversion margin effect, moves H, F and IOI accuracy by under 5 points (mean reference, R7; IOI on
  the 1,000 fresh rows), and removes more than the 95th percentile of its 20 nulls. The zero reference is not run.
  Outcome: every bar met is "the size-500 lead is confirmed on fresh data" and N1 is recorded as passed for that
  class on the confirmation sample (preliminary until an independent recomputation matches); any bar missed is
  "not confirmed", with the bars named, and R13 stands. Optional second cell, run only if the first is running on an
  H200: the honest-only class at size 2,000 and its 20 nulls on the same fresh sample under twin and mean, read by
  the N2 rule of item 10 under the mean reference (bypass if H accuracy falls at least 20 points while the
  deceptive rate moves under 5 and the nulls' 95th percentile of the H shift is under 5; suppression or shared if
  the deceptive rate also falls at least 10 points; otherwise undetermined). Budget: at most 2 GPU-hours reserved
  for both cells.
