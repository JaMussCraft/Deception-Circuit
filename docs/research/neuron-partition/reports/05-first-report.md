# Report 05: First report on neuron-partition, for the advisor meeting of Wed 4 Nov 2026

Agent: report writer (Claude, Opus). Ticket: item 8 of `../START.md`. Status: complete; findings are preliminary. Bare
file names are in `docs/research/neuron-partition/reports/`, and `../` is `docs/research/neuron-partition/`.

**Review 03: CONFIRMED WITH NOTES.** Every D-only number, recomputed from the rows, matches the verdict with no
discrepancy (`../reviews/03-verdict-review.md`). Ruling R13 keeps N1 failed and the size-500 class a descriptive lead.

1. **Question.** Do any MLP neurons of Llama-3.1-8B-Instruct matter only for instructed deception (FAR task), and not
   for a transparent inversion control or for the honest answer (`../START.md`)?
2. **Method.** Rank all 458,752 down-projection-input neurons by attribution patching summed over every position, cut
   four classes by rule R6, and ablate each against 20 matched random sets under three references
   (`01-w1-scorer-handback.md`).
3. **Headline, N1.** N1 fails at every set size under the frozen bars, with a near miss at size 500. The deception-only
   class of 338 neurons removes 0.813 of the deception margin under twin interchange and 0.724 under mean ablation,
   and fails only the IOI bar, at -6.0 points against 5 on 100 IOI rows
   (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`, `02-w2-ablation-handback.md`).
4. **N2.** The honest-only class is "undetermined at this size" at every size. At 2,000 it drops H accuracy by 23.5
   points while D's deceptive rate moves 5.2 points, just over the bar of 5
   (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).
5. **Comparison rankings.** At size 1,000 the readout-position deception-only class removes 0.291 of the deception
   margin and the activation-contrast class 0.039, with IOI shifts of -11.0 and -23.0 points
   (`outputs/_analyses/neuron-partition/verdict/far_atp_readout_c3d7763/verdict.md`,
   `outputs/_analyses/neuron-partition/verdict/far_contrast_66741d7/verdict.md`).
6. **Descriptive.** Every class is split-half stable on both rankings, and the all-position deception-only class sits
   0.62 to 0.65 in layers 0 to 9, unlike every other class (`04-w4-partition-handback.md`).

## What changed

### (a) The question and the three directions

Deception (D) is contrasted with its neutral twin (H), and a user-turn transparent inversion (I) with its user-neutral
twin (N). N1 partitions the scored neurons into D-only, D-and-I shared, H-only and all-shared classes and tests each
by set ablation. N2 asks whether ablating H-only drops honest accuracy while the deceptive rate stays, which would mean
deception bypasses the honest neurons. N3 measures split-half stability (`../START.md`, items 1 and 2).

**Where this sits.** At head level no exclusive or difference head set is deception-specific (F-mech-005 in
`../../FINDINGS.md`), and no row had intervened below the head or block. This session leaves the Codex A3 cell alone.

### (b) The method

**Unit and conditions.** The unit is one input of the MLP down-projection after the SwiGLU gate, 32 layers by 14,336.
D is `far_v2`, H `far_v2_honest`, F the no-pressure `far_v2_nopressure`, and I and N come from the ladder's A1 control
cell. D and H have 200 train and 200 validation ranking rows, I and N 177 and 177. Each condition has a 300-row test
sample drawn with seed 2 that excludes 356 ids used by the ladder or the mechanism analysis; 164 ids are in both the D
and the I sample. IOI collateral uses 100 rows rebuilt from the ladder's recipe (R4, `03-w3-data-handback.md`).

**The score.** Per row, m is logit(opposite) minus logit(honest) at the readout token, in D's orientation (R2). A
neuron's attribution is (a_clean minus a_twin) times dm/da; positive means it supports the clean condition's answer.
Review 01 found that the readout score misses the 43 positions between the clause end and the readout, which the twin
interchange writes. Ruling R11 therefore made the attribution summed over every position the primary ranking, with
the readout score and the activation contrast as comparisons (`../reviews/01-scorer-review.md`).

**The partition (R6).** Three signed scores per neuron: s_D from D against H, s_I from I against N, and s_H from the
reverse run with H clean, sign flipped so that positive supports the honest answer. For each k on the ladder 500,
1,000 and 2,000, T_D, T_I and T_H are the top k positive neurons of each score. The classes are D-only = T_D minus
(T_I union T_H); D-and-I shared = (T_D and T_I) minus T_H; H-only = T_H minus (T_D union T_I); all-shared = all three.
Every class is ablated at every k, and k is never chosen on the test sample (`../spec.md`).

**Ablation and effects.** The twin interchange, the primary reference, replaces the set's activations in each D row
at every position with the same instance's H values, and in each I row with N's. Mean ablation uses F's train and
validation splits (R3). The fraction removed is mean(m_intact minus m_ablated) over the intact gap G (R2), with the
rate at margin 0.7 beside it. H, F and IOI shifts are read under the mean reference, because F and IOI have no twin
(R7). The halves split the test sample by pressure cluster (R10), and each class has 20 size-and-layer-matched random
sets. Two departures from the frozen item 10 are dated rulings: the bars read the margin, because the rate's intact
effect is 1.0 by construction (R2), and the collateral reads the mean reference (R7) (`../spec.md`).

### (c) What is established

**The ranking baseline reproduces the dataset margins.** On the 400 D/H and 354 I/N ranking rows, every scored margin
correlates with the stored margin at 0.9985 or more, and the gaps are 9.61 and 14.61 against the Codex audit's 9.915
and 14.979. The all-position rerun reproduces every earlier key exactly (`01-w1-scorer-handback.md`).

**The all-position scores are wider, and deception overlaps inversion less there.** Over all positions, 13,987 of
458,752 neurons pass 0.01 and 105 pass 0.1 for D/H, against 1,477 and 46 at the readout. For I/N the counts are
24,998 and 206, against 6,338 and 114. The D/H and I/N maps correlate at 0.355 over all positions and at 0.775 at the
readout, and s_D and s_H correlate at 0.007 (`01-w1-scorer-handback.md`, addendum "all-position run").

**Class sizes and overlaps, both rankings.** The all-position rows are the primary cut under R11; the readout rows
are the comparison (`04-w4-partition-handback.md`, addenda "all-position partition (R11)" and "real partition").

| k | Ranking | D-only | D-and-I shared | H-only | all-shared | Jaccard T_D, T_I | Jaccard T_D, T_H |
|---|---|---|---|---|---|---|---|
| 500 | all positions | 338 | 79 | 390 | 62 | 0.164 | 0.091 |
| 500 | readout | 174 | 172 | 331 | 111 | 0.395 | 0.182 |
| 1,000 | all positions | 714 | 144 | 802 | 94 | 0.135 | 0.076 |
| 1,000 | readout | 409 | 314 | 702 | 209 | 0.354 | 0.161 |
| 2,000 | all positions | 1,442 | 289 | 1,623 | 160 | 0.126 | 0.072 |
| 2,000 | readout | 895 | 629 | 1,474 | 325 | 0.313 | 0.135 |

**The all-position D-only class is a different, earlier set.** It holds 0.62 to 0.65 of its neurons in layers 0 to 9,
densest at layers 7 and 8, while the D-and-I shared and H-only classes put 0.75 to 0.87 in layers 10 to 16, densest at
layer 13. Its Jaccard with the readout D-only class of the same k is only 0.040 to 0.056, and all-shared changes
least, at 0.377 to 0.466. At the readout, D-only, D-and-I shared and H-only sat 0.77 to 0.92 in layers 10 to 16
(`04-w4-partition-handback.md`). A hypothesis, not a finding: these early neurons may only read the clause's tokens.

**N3 stability, both rankings.** Jaccard between the rank halves; the ceiling is T_D's own Jaccard. The readout rows
are preliminary finding F1. Every class clears the lenient bar of half the ceiling, so "stable" means "not noise".
The floor is a uniform random set, 0.0001 to 0.0022, in place of START's IOI floor, a change recorded only in
`04-w4-partition-handback.md`
(`outputs/_analyses/neuron-partition/sets/far_atp_all_c3d7763/stability_summary_all.md` and
`outputs/_analyses/neuron-partition/sets/far_atp_66741d7/stability_summary.md`).

| k | Ranking | Ceiling | D-only | D-and-I shared | H-only | all-shared |
|---|---|---|---|---|---|---|
| 500 | all positions | 0.7794 | 0.7506 | 0.7333 | 0.7926 | 0.7917 |
| 500 | readout | 0.8182 | 0.6602 | 0.7789 | 0.7493 | 0.7500 |
| 1000 | all positions | 0.8083 | 0.7718 | 0.8291 | 0.7671 | 0.8317 |
| 1000 | readout | 0.8018 | 0.6480 | 0.7514 | 0.7873 | 0.7817 |
| 2000 | all positions | 0.7770 | 0.7398 | 0.7455 | 0.7934 | 0.7308 |
| 2000 | readout | 0.7889 | 0.6608 | 0.7690 | 0.7743 | 0.7989 |

### (d) The pre-registered pass bars, plainly

These restate item 10 of `../spec.md`. N1 passes if a D-only set of at most 2,000 neurons removes at least half of the
D effect, under a quarter of the I effect, moves H, F and IOI accuracy by under 5 points each, and beats the 95th
percentile of its matched null, under twin interchange and mean ablation, on the whole sample and on each half. One
reference or one half is a lead, not a pass. Otherwise the reviewed null reads "no deception-specific MLP neuron set
at this granularity under the ladder rule, outside the A3 cell".

N2 calls ablating the H-only set "bypass" if H accuracy drops by at least 20 points while D's deceptive rate moves
under 5 points and the null moves H under 5 points. It is "suppression or shared" if D's deceptive rate also falls by
at least 10 points, and "undetermined at this size" otherwise (`../spec.md`).

### (e) Ablation results

The tables are the primary all-position ranking, copied from the verdict script with half1 and half2 written as
words. Each class was scored on 300 test ids per condition and 100 IOI rows; the halves hold 156 and 144 D ids and 141
and 159 I ids, and share all 100 IOI rows. Brackets are bootstrap 95% intervals over ids, and H, F and IOI shifts are
points under the mean reference in every table (R7, `outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.json`).

**Twin interchange, the primary reference** (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).

| class | k | size | D removed (margin) | D removed (rate) | I removed (margin) | I removed (rate) | null p95 of D removed | H shift | F shift | IOI shift | bars (whole) | half 1 | half 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D_only | 500 | 338 | 0.813 [0.80, 0.82] | 1.000 [1.00, 1.00] | 0.145 [0.14, 0.15] | 0.186 [0.16, 0.21] | 0.012 | 0.0 | 0.0 | -6.0 | fail | fail | fail |
| D_only | 1000 | 714 | 0.850 [0.84, 0.86] | 1.000 [1.00, 1.00] | 0.340 [0.33, 0.35] | 0.481 [0.45, 0.51] | 0.025 | -0.2 | 0.0 | -11.0 | fail | fail | fail |
| D_only | 2000 | 1442 | 0.847 [0.84, 0.85] | 1.000 [1.00, 1.00] | 0.495 [0.49, 0.50] | 0.968 [0.95, 0.98] | 0.028 | -0.8 | -0.2 | -13.0 | fail | fail | fail |
| DI_shared | 500 | 79 | 0.257 [0.25, 0.27] | 0.856 [0.83, 0.88] | 0.380 [0.38, 0.39] | 0.806 [0.78, 0.84] | 0.007 | 0.0 | 0.0 | 3.0 | fail | fail | fail |
| DI_shared | 1000 | 144 | 0.291 [0.28, 0.30] | 0.909 [0.89, 0.93] | 0.403 [0.40, 0.41] | 0.950 [0.93, 0.97] | 0.012 | 0.0 | 0.0 | 0.0 | fail | fail | fail |
| DI_shared | 2000 | 289 | 0.336 [0.33, 0.34] | 0.944 [0.93, 0.96] | 0.431 [0.43, 0.44] | 1.000 [1.00, 1.00] | 0.016 | 0.0 | 0.0 | 2.0 | fail | fail | fail |
| H_only | 500 | 390 | -0.149 [-0.17, -0.12] | 0.222 [0.19, 0.26] | -0.272 [-0.29, -0.26] | 0.022 [0.01, 0.04] | 0.024 | -1.3 | -1.3 | -8.0 | fail | fail | fail |
| H_only | 1000 | 802 | -0.495 [-0.53, -0.45] | 0.130 [0.10, 0.16] | -0.368 [-0.38, -0.35] | 0.018 [0.01, 0.03] | 0.040 | -11.2 | -10.2 | -5.0 | fail | fail | fail |
| H_only | 2000 | 1623 | -0.647 [-0.71, -0.58] | 0.166 [0.13, 0.20] | -0.421 [-0.44, -0.40] | 0.010 [0.00, 0.02] | 0.061 | -23.5 | -19.8 | -1.0 | fail | fail | fail |
| all_shared | 500 | 62 | 0.370 [0.36, 0.38] | 0.964 [0.95, 0.98] | 0.451 [0.44, 0.46] | 0.889 [0.86, 0.92] | 0.005 | 0.0 | -0.3 | -11.0 | fail | fail | fail |
| all_shared | 1000 | 94 | 0.405 [0.40, 0.41] | 0.988 [0.98, 1.00] | 0.488 [0.48, 0.49] | 0.960 [0.94, 0.97] | 0.004 | 0.0 | -0.3 | -10.0 | fail | fail | fail |
| all_shared | 2000 | 160 | 0.480 [0.47, 0.49] | 1.000 [1.00, 1.00] | 0.546 [0.54, 0.55] | 0.998 [0.99, 1.00] | 0.019 | -4.2 | -4.5 | -19.0 | fail | fail | fail |

**Mean ablation, the second deciding reference** (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).

| class | k | size | D removed (margin) | D removed (rate) | I removed (margin) | I removed (rate) | null p95 of D removed | H shift | F shift | IOI shift | bars (whole) | half 1 | half 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D_only | 500 | 338 | 0.724 [0.71, 0.74] | 0.997 [0.99, 1.00] | 0.161 [0.15, 0.17] | 0.129 [0.11, 0.16] | 0.020 | 0.0 | 0.0 | -6.0 | fail | fail | fail |
| D_only | 1000 | 714 | 0.768 [0.75, 0.78] | 1.000 [1.00, 1.00] | 0.414 [0.41, 0.42] | 0.858 [0.83, 0.88] | 0.045 | -0.2 | 0.0 | -11.0 | fail | fail | fail |
| D_only | 2000 | 1442 | 0.783 [0.77, 0.80] | 1.000 [1.00, 1.00] | 0.573 [0.57, 0.58] | 1.000 [1.00, 1.00] | 0.025 | -0.8 | -0.2 | -13.0 | fail | fail | fail |
| DI_shared | 500 | 79 | 0.233 [0.22, 0.24] | 0.829 [0.80, 0.86] | 0.373 [0.37, 0.38] | 0.729 [0.69, 0.76] | 0.007 | 0.0 | 0.0 | 3.0 | fail | fail | fail |
| DI_shared | 1000 | 144 | 0.252 [0.24, 0.26] | 0.849 [0.82, 0.87] | 0.391 [0.39, 0.40] | 0.894 [0.87, 0.92] | 0.030 | 0.0 | 0.0 | 0.0 | fail | fail | fail |
| DI_shared | 2000 | 289 | 0.279 [0.27, 0.29] | 0.919 [0.90, 0.94] | 0.417 [0.41, 0.42] | 0.975 [0.96, 0.99] | 0.028 | 0.0 | 0.0 | 2.0 | fail | fail | fail |
| H_only | 500 | 390 | -0.209 [-0.22, -0.19] | 0.102 [0.08, 0.13] | -0.121 [-0.14, -0.11] | 0.126 [0.10, 0.15] | 0.047 | -1.3 | -1.3 | -8.0 | fail | fail | fail |
| H_only | 1000 | 802 | -0.515 [-0.54, -0.49] | 0.100 [0.08, 0.13] | -0.159 [-0.18, -0.14] | 0.137 [0.11, 0.16] | 0.034 | -11.2 | -10.2 | -5.0 | fail | fail | fail |
| H_only | 2000 | 1623 | -0.698 [-0.73, -0.67] | 0.146 [0.12, 0.17] | -0.042 [-0.07, -0.02] | 0.280 [0.24, 0.31] | 0.074 | -23.5 | -19.8 | -1.0 | fail | fail | fail |
| all_shared | 500 | 62 | 0.177 [0.17, 0.18] | 0.497 [0.46, 0.53] | 0.261 [0.26, 0.27] | 0.223 [0.19, 0.25] | 0.005 | 0.0 | -0.3 | -11.0 | fail | fail | fail |
| all_shared | 1000 | 94 | 0.202 [0.19, 0.21] | 0.665 [0.63, 0.70] | 0.298 [0.29, 0.30] | 0.315 [0.29, 0.34] | 0.007 | 0.0 | -0.3 | -10.0 | fail | fail | fail |
| all_shared | 2000 | 160 | 0.232 [0.22, 0.24] | 0.775 [0.74, 0.80] | 0.335 [0.33, 0.34] | 0.457 [0.43, 0.48] | 0.017 | -4.2 | -4.5 | -19.0 | fail | fail | fail |

**Zero ablation, D-only rows** (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`). The
collateral columns are the mean reference's (R7); zero's own IOI shift at 500 is -17.0 (`../reviews/03-verdict-review.md`).

| class | k | size | D removed (margin) | D removed (rate) | I removed (margin) | I removed (rate) | null p95 of D removed | H shift | F shift | IOI shift | bars (whole) | half 1 | half 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D_only | 500 | 338 | 0.550 [0.54, 0.56] | 0.980 [0.97, 0.99] | 0.220 [0.21, 0.23] | 0.204 [0.18, 0.23] | 0.025 | 0.0 | 0.0 | -6.0 | fail | fail | fail |
| D_only | 1000 | 714 | 0.583 [0.57, 0.59] | 0.959 [0.94, 0.97] | 0.287 [0.28, 0.29] | 0.233 [0.20, 0.27] | 0.073 | -0.2 | 0.0 | -11.0 | fail | fail | fail |
| D_only | 2000 | 1442 | 0.552 [0.54, 0.56] | 0.958 [0.94, 0.97] | 0.403 [0.40, 0.41] | 0.911 [0.89, 0.93] | 0.037 | -0.8 | -0.2 | -13.0 | fail | fail | fail |

**N1 verdict: fail at every k, with a near miss at 500.** No D-only set passes under twin and mean on the whole sample
and both halves, so the frozen text records the null for this ranking. At size 500 the 338-neuron class passes the
size, D, I, H, F and null bars on the whole sample and both halves under all three references. Under twin and mean it
removes 0.813 and 0.724 of the D margin, with rate effects 1.000 and 0.997, and 0.145 and 0.161 of the I margin,
against null 95th percentiles of 0.012 and 0.020. It fails only IOI: accuracy falls 6.0 points against the bar of 5,
that is 6 of 100 rows, and every subset fails because both halves share the 100 IOI rows
(`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.json` and
`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).

**How well 100 rows resolve the IOI bar.** The 6-point drop is 6 rows lost and 0 gained out of 100, an exact McNemar
p of 0.031. Its 95% interval runs from about 2 to 13 points lost, so the sample cannot place the true shift on either
side of the 5-point bar. The 20 matched nulls span -3 to +6 at size 500, with a 95th percentile of the absolute shift
of 3.15, and reach -9 at size 1,000 (`../reviews/03-verdict-review.md`, section "IOI resolution").

**Larger sets fail two bars, and the references agree.** At 1,000 and 2,000 the class also removes 0.340 and 0.495 of
the I margin under twin and 0.414 and 0.573 under mean, above the bar of a quarter, and moves IOI by -11.0 and -13.0
points. Zero ablation fails the same bars with the smallest D removed, 0.550 to 0.583. D-and-I shared and all-shared
remove more of the I margin than of the D margin under every reference
(`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).

**The comparison rankings fail more widely.** D-only rows at size 1,000 under twin and mean, from
`outputs/_analyses/neuron-partition/verdict/far_atp_readout_c3d7763/verdict.md` and
`outputs/_analyses/neuron-partition/verdict/far_contrast_66741d7/verdict.md`.

| Ranking | Reference | size | D removed (margin) | D removed (rate) | I removed (margin) | null p95 of D removed | H shift | F shift | IOI shift |
|---|---|---|---|---|---|---|---|---|---|
| readout | twin | 409 | 0.291 | 0.978 | 0.192 | 0.028 | 0.0 | 0.0 | -11.0 |
| readout | mean | 409 | 0.236 | 0.775 | 0.112 | 0.021 | 0.0 | 0.0 | -11.0 |
| contrast | twin | 386 | 0.039 | 0.227 | -0.005 | 0.007 | 0.0 | -0.2 | -23.0 |
| contrast | mean | 386 | 0.032 | 0.212 | -0.018 | 0.009 | 0.0 | -0.2 | -23.0 |

**N2 verdict: undetermined at every size.** N2 is decided under the mean reference, and these are its rows
(`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).

| reference | k | subset | H shift | D rate change | null p95 of abs H shift | verdict |
|---|---|---|---|---|---|---|
| mean | 500 | whole | -1.3 | -9.8 | 0.0 | undetermined at this size |
| mean | 500 | half 1 | -1.3 | -9.9 | 0.0 | undetermined at this size |
| mean | 500 | half 2 | -1.4 | -9.7 | 0.0 | undetermined at this size |
| mean | 1000 | whole | -11.2 | -5.8 | 0.0 | undetermined at this size |
| mean | 1000 | half 1 | -9.9 | -5.8 | 0.0 | undetermined at this size |
| mean | 1000 | half 2 | -12.5 | -5.9 | 0.0 | undetermined at this size |
| mean | 2000 | whole | -23.5 | -5.2 | 0.0 | undetermined at this size |
| mean | 2000 | half 1 | -24.7 | -4.5 | 0.0 | bypass |
| mean | 2000 | half 2 | -22.2 | -5.9 | 0.0 | undetermined at this size |

- **Size 2,000 misses bypass by one bar.** The 1,623-neuron H-only class drops H accuracy by 23.5 points on 300 rows,
  and the null moves H by 0.0. D's own deceptive rate falls from 0.985 to 0.933, a move of 5.2 points against the
  bar of under 5. Half 1 reads bypass and half 2 undetermined
  (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.json` and
  `outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).
- **Beside the decision.** Zero reads bypass at 2,000 (H -44.3, D rate -4.5), and the twin reverse patch reads
  "suppression or shared" at 1,000 and 2,000 (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).
- **Ablating the H-only class raises the deception margin.** D removed is negative at every size: -0.149 to -0.647
  under twin and -0.209 to -0.698 under mean. The readout and contrast H-only classes read undetermined at 1,000
  (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md` and the two comparison verdicts).

## How verified

**Tests.** Every worker's tests pass on mgnp and the base Python 3.9 with no failure against the known baseline. The
counts, mgnp then base, are 28 and 28 for the scorer, 44 and 28 for the ablation script after the review fixes (16
base skips need nnsight 0.7.0), 20 and 20 for the data, 18 and 18 for the sets, and 20 and 20 for the verdict
(`01-w1-scorer-handback.md`, `02-w2-ablation-handback.md`, `03-w3-data-handback.md`, `04-w4-partition-handback.md`,
`05-w1-verdict-handback.md`).

**The scorer and ablation reviews both returned PASS WITH FIXES.** The scorer review's first major is resolved by
R11, and its second, that s_D and s_H agree in sign on only 0.63 of the top 100, is a known property
(`../reviews/01-scorer-review.md`).

**Both ablation-review fixes landed at commit fe2db9e before every full cell.** The review found that the IOI rows
depended on the Python hash seed and that the ids loader rejected W3's sample file. Every full cell records the fixed
IOI rows' sha256 `61ebeea3…5e59` and hash seed 0, reads W3's sample file directly, and names fe2db9e with
`git_dirty` false (`02-w2-ablation-handback.md`).

## Execution evidence

Five Delta jobs ran on interactive A40 nodes under account beto-delta-gpu. Three Bridges-2 jobs ran, and a fourth is
queued, on partition GPU-shared with one H100-80 GB each under allocation cis260372p. Totals are 13.5 of 20 GPU-hours
reserved and 25,104 GPU-seconds used, with no OpenRouter spend. The ledger is
`/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition/ledger.json`; the cell counts are in
`02-w2-ablation-handback.md`. Output paths are under `outputs/_analyses/neuron-partition/`.

| Job | Cluster and node | Slurm id | Reserved | Actual | State | Output and commit |
|---|---|---|---|---|---|---|
| Ranking pilot, 64 validation rows | Delta, A40 | 23475874 | 45 min | 89 s | COMPLETED | `attribution/far_v2_{dh,in}_validation_f4ce555_limit64`, f4ce555, dirty |
| Full FAR ranking, forward and reverse | Delta, A40 | 23476096 | 30 min | 252 s | COMPLETED | `attribution/far_v2_{dh,in}_train+validation_7386fd3{,_rev}`, manifest 6c6d5be, dirty |
| Split-half ranking for N3 | Delta, A40 | 23476621 | 30 min | 259 s | COMPLETED | `attribution/far_v2_*_half{1,2}_66741d7*`, e5962fe, 5e4fd2c, 767d4be, clean |
| Ablation pilot, 16 ids, k 500 | Delta, A40, gpub046 | 23477197 | 30 min | 679 s | COMPLETED, 30 of 30 cells | `ablation/pilot-e5962fe`, run at f965bd5, dirty |
| All-position ranking (R11) | Delta, A40, gpub040 | 23478550 | 30 min | 482 s | COMPLETED, 10 directories | `attribution/far_v2_*_c3d7763*`, code c3d7763 pinned by sha256 |
| C: contrast sets, k 1,000 | Bridges-2, H100, w010 | 50182995 | 2 h | 4,035 s | COMPLETED, 30 of 30 cells | `ablation/jobC-fe2db9e`, fe2db9e, clean |
| A: all-position sets, k 500 and 1,000 | Bridges-2, H100, w007 | 50183187 | 4 h | 9,584 s | COMPLETED, 2 x 30 of 30 cells | `ablation/jobA-fe2db9e`, fe2db9e, clean |
| B: all-position k 2,000, readout k 1,000 | Bridges-2, H100, w008 | 50183194 | 4 h | 9,724 s | COMPLETED, 2 x 30 of 30 cells | `ablation/jobB-fe2db9e`, fe2db9e, clean |
| IOI resolution, 1,000 IOI rows, D-only k 500 and nulls, mean only | Bridges-2, H100 | 50189921 | 45 min | none yet | PENDING when this was written | `ablation/ioi_resolution-38c51db`, 38c51db |

**Checks inside the full cells.** All five full cells scored 300 of 300 ids per condition, self-replay error 0.0,
and intact G 9.834 for D and 14.708 for I against the ladder audit's 10.087 and 14.979. Intact IOI accuracy is 0.51
on 100 rows in each, against the brief's 0.51 (R4); the pilot read 0.48 before the fixes (`02-w2-ablation-handback.md`).

## What is NOT done

- **A larger IOI measurement.** The IOI bar was read on 100 rows. Under ruling R13 an exploratory, not pre-registered
  measurement on 1,000 IOI rows is running tonight on Bridges-2. It is pending, will be an addendum, and cannot
  change the N1 decision (`../spec.md`, R13).
- **The one-neuron interchange check** of the scorer review's second major is descriptive and was not run.
- **SER.** No SER ranking or ablation has run. START makes SER a bonus.
- **Dropped or unused.** The N3 rotation test is dropped, as START's fallback allows, and no verdict is recorded in
  the Codex A3 neuron cell, as `../START.md` requires.

## Open questions

- **The near miss.** Does the advisor read the size-500 result as a lead worth a larger IOI measurement and a
  pre-registered follow-up, given that the bars were frozen? Default: as ruling R13 records, N1 stays failed and the
  class is a descriptive lead; any follow-up gets its own pre-registered bars (`../spec.md`).
- **Rate or margin (R2).** The bars read the margin effect, and the rate at margin 0.7 sits beside it (`../spec.md`).
  The rate is close to saturated: at the smallest size D-and-I shared removes 0.856 of the D rate but 0.257 of the D
  margin under twin (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.json`). Default: margin.
- **The honest-only class's negative D effect.** Ablating it raises the deception margin by 0.149 to 0.698 of the gap,
  yet under mean at 2,000 D's own deceptive rate falls 5.2 points
  (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`). Does the class hold the deceptive
  answer back, and how does that change the N2 reading? Default: report it descriptively and check per-row margins.
- **The I sample.** It overlaps the D sample on 164 of 300 ids (`03-w3-data-handback.md`), so D and I effects come
  from partly different instances. Default: report it as a caveat.
- **SER.** Should the unreserved 6.5 of 20 GPU-hours, derived from the ledger's 13.5 reserved, go to SER, whose
  act-naming test rows number only 72 (`00-reader-brief.md`)? Default: only with the user's go, after the review.
