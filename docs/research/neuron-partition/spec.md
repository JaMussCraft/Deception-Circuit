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
