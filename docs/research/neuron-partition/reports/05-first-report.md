# Report 05: First report on neuron-partition, for the week of Tue 3 Nov 2026 (presented Wed 4 Nov)

Report writer (Claude, Opus), item 8 of `../START.md`. Bare file names are in `reports/`; `../` is the direction.

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
   (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`, `02-w2-ablation-handback.md`). An
   exploratory, not pre-registered measurement on 1,000 IOI rows puts that cost at -3.7 points, interval -5.2 to
   -2.4: the point estimate is under the bar but the interval reaches it, so a 5-point shift is not excluded; the
   cost is well outside the null band of -2.3 to +1.1 (finding F5 in `../WORKLOG.md`). The decision stands (R13).
4. **N2.** The honest-only class is "undetermined at this size" at every size. At 2,000 it drops H accuracy by 23.5
   points while D's deceptive rate moves 5.2 points, just over the bar of 5
   (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).
5. **Comparison rankings.** At size 1,000 the readout-position deception-only class removes 0.291 of the deception
   margin and the activation-contrast class 0.039, with IOI shifts of -11.0 and -23.0 points
   (`outputs/_analyses/neuron-partition/verdict/far_atp_readout_c3d7763/verdict.md`,
   `outputs/_analyses/neuron-partition/verdict/far_contrast_66741d7/verdict.md`).
6. **Descriptive.** Every class is split-half stable on both rankings, and the all-position deception-only class sits
   0.62 to 0.65 in layers 0 to 9, unlike every other class (`04-w4-partition-handback.md`).
7. **Confirmation, pre-registered (R14).** On fresh ids and 1,000 fresh IOI rows the same 338-neuron class meets every
   N1 bar under twin and mean, whole and both halves: D removed 0.822 and 0.748, I removed 0.141 and 0.154, IOI -2.7
   points. N1 passes for this class there (F6, independent review pending); the ladder decision stays failed
   (`outputs/_analyses/neuron-partition/verdict/confirm_k500-d3d842b/verdict.md`, `08-w8-confirmation-handback.md`).

## What changed

### (a) The question and the three directions

Deception (D) is contrasted with its neutral twin (H), and a user-turn inversion (I) with its user-neutral twin (N).
N1 partitions neurons into D-only, D-and-I shared, H-only and all-shared classes and tests each by set ablation. N2
asks whether deception bypasses the H-only neurons; N3 measures split-half stability (`../START.md`, items 1 and 2).

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

**The partition (R6).** s_D scores D against H, s_I scores I against N, and s_H is the reverse run with H clean, sign
flipped. For k of 500, 1,000 and 2,000, T_D, T_I and T_H are the top k positive neurons of each. D-only = T_D minus
(T_I union T_H); D-and-I shared = (T_D and T_I) minus T_H; H-only = T_H minus (T_D union T_I); all-shared = all three.
Every class is ablated at every k, and k is never chosen on the test sample (`../spec.md`).

**Ablation and effects.** The twin interchange, primary, writes each instance's H values into the set at every
position of the D row, and N's into the I row; mean ablation uses F's train and validation splits (R3). The fraction
removed is mean(m_intact minus m_ablated) over the intact gap G, with the rate at margin 0.7 beside it; the bars read
the margin because the rate's intact effect is 1.0 by construction (R2). Collateral is read under mean, as F and IOI
have no twin (R7). Halves split by pressure cluster (R10), and each class has 20 matched random sets (`../spec.md`).

### (c) What is established

**The ranking baseline reproduces the dataset margins.** On the 400 D/H and 354 I/N ranking rows, every scored margin
correlates with the stored margin at 0.9985 or more, and the gaps are 9.61 and 14.61 against the Codex audit's 9.915
and 14.979. The all-position rerun reproduces every earlier key exactly (`01-w1-scorer-handback.md`).

**The all-position scores are wider, and deception overlaps inversion less there.** Over all positions, 13,987 of
458,752 neurons pass 0.01 and 105 pass 0.1 for D/H, against 1,477 and 46 at the readout. For I/N the counts are
24,998 and 206, against 6,338 and 114. The D/H and I/N maps correlate at 0.355 over all positions and at 0.775 at the
readout, and s_D and s_H correlate at 0.007 (`01-w1-scorer-handback.md`, addendum "all-position run").

**Class sizes and overlaps.** All-position rows are primary (R11), readout rows the comparison (`04-w4-partition-handback.md`).

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

**N3: every class is split-half stable on both rankings.** On all positions every class Jaccard lies between 0.73
and 0.83, against ceilings of 0.78 to 0.81. At the readout D-only is least stable, at 0.65 to 0.66 against ceilings of
0.79 to 0.82 (finding F1). The bar is half the ceiling, so "stable" means "not noise". The floor is a uniform random
set, 0.0001 to 0.002, in place of START's IOI floor, a change recorded only in `04-w4-partition-handback.md`.

### (d) The pre-registered pass bars, plainly

These restate item 10 of `../spec.md`. N1 passes if a D-only set of at most 2,000 neurons removes at least half of the
D effect, under a quarter of the I effect, moves H, F and IOI accuracy by under 5 points each, and beats the 95th
percentile of its matched null, under twin interchange and mean ablation, on the whole sample and on each half. One
reference or one half is a lead, not a pass. Otherwise the reviewed null reads "no deception-specific MLP neuron set
at this granularity under the ladder rule, outside the A3 cell".

N2 reads "bypass" if ablating H-only drops H accuracy at least 20 points while D's deceptive rate and the null's H
move under 5, "suppression or shared" if D's rate also falls at least 10, else "undetermined" (`../spec.md`).

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

**N1 verdict: fail at every k, with a near miss at 500.** No D-only set passes under twin and mean on the whole sample
and both halves, so the frozen text records the null for this ranking. At size 500 the 338-neuron class passes the
size, D, I, H, F and null bars on the whole sample and both halves under all three references. Under twin and mean it
removes 0.813 and 0.724 of the D margin, with rate effects 1.000 and 0.997, and 0.145 and 0.161 of the I margin,
against null 95th percentiles of 0.012 and 0.020. It fails only IOI: accuracy falls 6.0 points against the bar of 5,
that is 6 of 100 rows, and every subset fails because both halves share the 100 IOI rows
(`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.json` and
`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).

**100 rows cannot resolve the IOI bar.** The 6-point drop is 6 rows lost and 0 gained, exact McNemar p 0.031, with a
95% interval of about 2 to 13 points lost. The nulls span -3 to +6 at size 500 and reach -9 at size 1,000
(`../reviews/03-verdict-review.md`). Zero ablation's own IOI shift at size 500 is -17.0, beside the mean-reference
collateral the tables show (R7).

**On 1,000 IOI rows, exploratory, not pre-registered (R13).** The size-500 class shifts IOI by -3.7 points, interval
-5.2 to -2.4, 45 rows lost and 8 gained, at intact accuracy 0.554; its nulls move IOI by -2.3 to +1.1. The 100-row -6
was a noisy over-estimate of a real cost of about 4 points, under the bar at its point estimate and outside the null
band (finding F5; `02-w2-ablation-handback.md`).

**Larger sets fail two bars, and the references agree.** At 1,000 and 2,000 the class also removes 0.340 and 0.495 of
the I margin under twin and 0.414 and 0.573 under mean, above the bar of a quarter, and moves IOI by -11.0 and -13.0
points. Zero ablation fails the same bars: its D-only class removes 0.550, 0.583 and 0.552 of the D margin and 0.220,
0.287 and 0.403 of the I margin. D-and-I shared and all-shared remove more of the I margin than of the D margin
(`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).

**The comparison rankings fail more widely** (`outputs/_analyses/neuron-partition/verdict/far_atp_readout_c3d7763/verdict.md`,
`outputs/_analyses/neuron-partition/verdict/far_contrast_66741d7/verdict.md`).

| Ranking | Reference | size | D removed (margin) | D removed (rate) | I removed (margin) | null p95 of D removed | H shift | F shift | IOI shift |
|---|---|---|---|---|---|---|---|---|---|
| readout | twin | 409 | 0.291 | 0.978 | 0.192 | 0.028 | 0.0 | 0.0 | -11.0 |
| readout | mean | 409 | 0.236 | 0.775 | 0.112 | 0.021 | 0.0 | 0.0 | -11.0 |
| contrast | twin | 386 | 0.039 | 0.227 | -0.005 | 0.007 | 0.0 | -0.2 | -23.0 |
| contrast | mean | 386 | 0.032 | 0.212 | -0.018 | 0.009 | 0.0 | -0.2 | -23.0 |

**N2 verdict: undetermined at every size.** N2 is decided under the mean reference. At 500 and 1,000, H moves -1.3
and -11.2 points, short of the bypass drop; the rows at 2,000 follow
(`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).

| reference | k | subset | H shift | D rate change | null p95 of abs H shift | verdict |
|---|---|---|---|---|---|---|
| mean | 2000 | whole | -23.5 | -5.2 | 0.0 | undetermined at this size |
| mean | 2000 | half 1 | -24.7 | -4.5 | 0.0 | bypass |
| mean | 2000 | half 2 | -22.2 | -5.9 | 0.0 | undetermined at this size |

- **Size 2,000 misses bypass by one bar.** The 1,623-neuron H-only class drops H accuracy by 23.5 points on 300 rows,
  and the null moves H by 0.0. D's own deceptive rate falls from 0.985 to 0.933, a move of 5.2 points against the
  bar of under 5. Half 1 reads bypass and half 2 undetermined
  (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.json` and
  `outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).
- **Beside the decision.** At the largest size zero reads bypass and the twin reverse patch "suppression or shared".
- **Ablating the H-only class raises the deception margin.** D removed is negative at every size: -0.149 to -0.647
  under twin and -0.209 to -0.698 under mean. The readout and contrast H-only classes read undetermined at 1,000
  (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md` and the two comparison verdicts).

## Confirmation test, pre-registered (R14)

**Review 04: CONFIRMED WITH NOTES.** An independent recomputation from the rows matches every number of this
section (188 quantities, worst difference 0.0), so finding F6 is reviewed (`../reviews/04-confirmation-review.md`).
Two notes from it: the inversion sample has 166 rows, under item 10's floor of 300 (the pool had no more fresh
ids); and under the mean reference the user-neutral margin also moves 1.08 logits toward the inverted answer, so a
second reading of the inversion effect (the ablated gap over the intact gap) is 0.230, under the 0.25 bar by 0.02,
where the registered reading (R2) is 0.154.

**Design, fixed before any draw.** Ruling R14 tested the fixed size-500 all-position D-only class (338 neurons) and
its 20 nulls on fresh data. The seed-3 sample holds 208 D, H and F ids and 166 I and N ids, disjoint from every seed-2
id (sha256 `bdd94ce2…`); its halves hold 104 and 104 D ids and 78 and 88 I ids. The 1,000 IOI rows were drawn with
IOI seed 2 and share 0 sentences with the seed-1 draw (sha256 `906a93ed…`). The N1 bars were unchanged, read under
twin and mean on the whole sample and both halves. Zero was not run, and the optional honest-only cell was skipped
because every H200 node was draining (`../spec.md`, R14; `08-w8-confirmation-handback.md`).

**Every bar is met.** H and F shift 0.0 and IOI -2.7 points under the mean reference, on 1,000 fresh rows with intact
accuracy 0.513 (`outputs/_analyses/neuron-partition/verdict/confirm_k500-d3d842b/verdict.md`,
`08-w8-confirmation-handback.md`).

| reference | subset | D removed (margin) | I removed (margin) | null p95 of D removed | bars |
|---|---|---|---|---|---|
| twin | whole | 0.822 | 0.141 | 0.013 | pass |
| twin | half 1 | 0.824 | 0.145 | 0.015 | pass |
| twin | half 2 | 0.820 | 0.137 | 0.012 | pass |
| mean | whole | 0.748 | 0.154 | 0.021 | pass |
| mean | half 1 | 0.751 | 0.160 | 0.023 | pass |
| mean | half 2 | 0.744 | 0.148 | 0.020 | pass |

The IOI cost is real but under the bar: exact McNemar p 0.00014, bootstrap interval -4.1 to -1.4 points, against
nulls of -1.3 to +2.2 (`08-w8-confirmation-handback.md`).

**Both decisions stand.** N1 passes for this class on the confirmation sample (finding F6, preliminary until the
independent review). The original ladder decision is unchanged: no D-only set passed on the seed-2 sample under its frozen bars, so N1
failed there (F3, R13). The class was carried forward after the seed-2 results were seen, which is why R14 required
fresh ids and fresh IOI rows (`../spec.md`).

## How verified

**Tests** pass on mgnp and base Python 3.9 with no failure against the baseline, mgnp then base: scorer 28 and 28,
ablation 44 and 28 (16 base skips need nnsight 0.7.0), data 20 and 20, sets 18 and 18, verdict 20 and 20 (hand-backs
`01-w1-scorer-handback.md` to `05-w1-verdict-handback.md`, with `02-w2-ablation-handback.md`, `03-w3-data-handback.md`
and `04-w4-partition-handback.md`).

**Reviews.** The scorer and ablation reviews returned PASS WITH FIXES. The scorer review's first major is resolved
by R11, and its second, sign agreement of s_D and s_H on only 0.63 of the top 100, is a known property. Both ablation
fixes, the hash-seed-dependent IOI rows and the ids loader, landed at fe2db9e before every full cell, and each cell
records IOI sha256 `61ebeea3…5e59` and `git_dirty` false (`../reviews/01-scorer-review.md`, `02-w2-ablation-handback.md`).

## Execution evidence

Delta jobs ran on interactive A40 nodes under account beto-delta-gpu, and Bridges-2 jobs on partition GPU-shared with
one H100-80 GB each under allocation cis260372p. Totals are 15.8334 of 20 GPU-hours reserved and 27,732 GPU-seconds
used, with no OpenRouter spend (`/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition/ledger.json`).
Cell and row counts are in `02-w2-ablation-handback.md` and `08-w8-confirmation-handback.md`; outputs are under
`outputs/_analyses/neuron-partition/`.

| Job | Cluster and node | Slurm id | Reserved | Actual | State | Output and commit |
|---|---|---|---|---|---|---|
| Rankings: pilot on 64 rows; full, forward and reverse; split halves for N3 | Delta, A40 | 23475874; 23476096; 23476621 | 45 min; 30 min; 30 min | 89 s; 252 s; 259 s | COMPLETED | `attribution/`, at f4ce555 (dirty), 7386fd3 (manifest 6c6d5be, dirty), 66741d7 (clean) |
| Ablation pilot, 16 ids, k 500 | Delta, A40, gpub046 | 23477197 | 30 min | 679 s | COMPLETED, 30 of 30 cells | `ablation/pilot-e5962fe`, run at f965bd5, dirty |
| All-position ranking (R11) | Delta, A40, gpub040 | 23478550 | 30 min | 482 s | COMPLETED, 10 directories | `attribution/far_v2_*_c3d7763*`, code c3d7763 pinned by sha256 |
| C: contrast sets, k 1,000 | Bridges-2, H100, w010 | 50182995 | 2 h | 4,035 s | COMPLETED, 30 of 30 cells | `ablation/jobC-fe2db9e`, fe2db9e, clean |
| A: all-position sets, k 500 and 1,000 | Bridges-2, H100, w007 | 50183187 | 4 h | 9,584 s | COMPLETED, 2 x 30 of 30 cells | `ablation/jobA-fe2db9e`, fe2db9e, clean |
| B: all-position k 2,000, readout k 1,000 | Bridges-2, H100, w008 | 50183194 | 4 h | 9,724 s | COMPLETED, 2 x 30 of 30 cells | `ablation/jobB-fe2db9e`, fe2db9e, clean |
| IOI resolution, exploratory, not pre-registered (R13): queued copy, first attempt | Bridges-2, H100; Delta, A40, gpub001 | 50189921; 23493221 | 45 min; 40 min | 0 s; 41 s | CANCELLED unstarted, no charge; FAILED at CUDA initialisation | none |
| IOI resolution, exploratory, not pre-registered (R13), 1,000 rows, D-only k 500 and nulls, mean only | Delta, A40, gpub002 | 23493280 | 40 min | 271 s | COMPLETED | `ablation/ioi_resolution-delta-e8dd8a8`, code e8dd8a8 by sha256, head 3c50669, dirty |
| Confirmation, pre-registered (R14): seed-3 sample, D-only k 500 and nulls, twin and mean | Delta, A40, gpub075 | 23494260 | 60 min | 2,316 s | COMPLETED, 56,784 of 56,784 rows | `ablation/confirm_k500-d3d842b`, d3d842b, clean |

**Checks.** All five full cells scored 300 of 300 ids per condition, self-replay error 0.0, intact G 9.834 for D and
14.708 for I (ladder audit 10.087 and 14.979), and IOI 0.51 on 100 rows against the brief's 0.51 (R4)
(`02-w2-ablation-handback.md`).

## What is NOT done

- **Confirmation scope.** R14 confirmed only the size-500 D-only class under twin and mean. Zero was not run, and the
  optional honest-only cell was skipped, so N2 has no confirmation (`08-w8-confirmation-handback.md`).
- **The one-neuron interchange check** of the scorer review's second major is descriptive and was not run.
- **SER.** No SER ranking or ablation has run. START makes SER a bonus.
- **Dropped or unused.** The N3 rotation test is dropped, as START's fallback allows, and no verdict is recorded in
  the Codex A3 neuron cell, as `../START.md` requires.

## Open questions

- **What the two decisions support.** The ladder failed under its frozen bars (R13), and the one class carried forward
  passed a pre-registered confirmation on fresh data (R14, F6). The user's options are to report the class as a
  deception-specific set by the N1 bars, to test it further first (SER, the one-neuron check, whether its early-layer
  neurons only read the clause), or both. Default: report both decisions side by side, F6 preliminary until reviewed.
- **Rate or margin (R2).** The bars read the margin effect, and the rate at margin 0.7 sits beside it (`../spec.md`).
  The rate is close to saturated: at the smallest size D-and-I shared removes 0.856 of the D rate but 0.257 of the D
  margin under twin (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.json`). Default: margin.
- **The honest-only class's negative D effect.** Ablating it raises the deception margin by 0.149 to 0.698 of the gap,
  yet under mean at 2,000 D's own deceptive rate falls 5.2 points (`outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.md`).
  Options: report it descriptively, or check per-row margins first. Default: describe it.
- **The I sample** overlaps the D sample on 164 of 300 ids, so D and I effects come from partly different instances
  (`03-w3-data-handback.md`). Default: a stated caveat.
- **SER.** The unreserved 4.17 of 20 GPU-hours, derived from the ledger's 15.83, could go to SER, whose act-naming
  test rows number only 72 (`00-reader-brief.md`). Default: only on the user's go.
