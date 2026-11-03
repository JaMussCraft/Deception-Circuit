# Review 03: independent recomputation of the neuron-partition verdict (FAR, all-position ranking)

**Verdict: CONFIRMED WITH NOTES.** Every D_only number in the verdict was recomputed from `rows.jsonl` without the
verdict script and matches to floating-point precision. The largest difference is 1.1e-16 on a fraction and 0.0 on
a point. The notes are about reading the result, not about arithmetic. At size 500 the IOI bar is the only bar
that fails, by one row, and a sample of 100 IOI rows cannot place the true shift on either side of the 5-point bar.

Reviewer: rev3 (Opus, independent). The verdict script `scripts/neuron_partition_verdict.py` was not read. The
verdict files were opened only after the recomputed numbers were written to
`outputs/_analyses/neuron-partition/review3_tmp/recompute.json`. Scope: spec rulings R2, R7, R8 and R10, START item
10 (N1 and N2), reader brief section 2 and the `rows.jsonl` schema in hand-back 02. No git, GPU or Slurm was used.

## Definitions used

- **Rows.** Each `rows.jsonl` line holds one reference, set, condition and id. It carries `m_intact`, `m_ablated`,
  `argmax_intact`, `argmax_ablated` and `correct_token` per stream, and `twin_m_intact` on the paired conditions.
- **Margin effect (R2).** G is the mean over ids of the stream-averaged intact D margin minus the stream-averaged
  intact H-twin margin. The twin margin was taken from the H rows of the same reference and set, not from the D
  row's `twin_m_intact` field, and the two were checked equal. The drop is the mean over ids of intact minus
  ablated D margin. The fraction removed is the drop divided by G. I uses the user-neutral rows (condition `N`).
- **Ablated margin effect.** Under twin it is ablated D against the unpatched twin. Under mean and zero it is
  ablated D against ablated H (R8).
- **Rate at margin 0.7.** The share of id-stream pairs with m at least 0.7. The rate removed is one minus the
  ablated rate effect over the intact rate effect. Under twin the ablated D rate is compared with intact H. Under
  mean and zero it is compared with ablated H (R8).
- **Collateral.** Full-vocabulary argmax accuracy against `correct_token`, both streams, in points. The deciding
  collateral is read under the mean reference for every tested set (R7). IOI has one stream and 100 rows.
- **Null p95.** `numpy.percentile` with linear interpolation over the 20 matched nulls. The verdict uses the same
  method (`choices.null_percentile`).

## Recomputed numbers beside the verdict's

D_only, whole sample, 300 ids per condition. Sizes are 338, 714 and 1,442 neurons. The intact effects are the
same in every cell: G_D is 9.8337 and G_I is 14.7085 logits. The intact rates are 0.985 for D and 0.995 for I,
and 0.0 for H and user-neutral.

| k | reference | D removed, margin (mine / verdict) | I removed, margin | D removed, rate | I removed, rate | null p95 of D removed | null max of D removed |
|---|---|---|---|---|---|---|---|
| 500 | twin | 0.8126 / 0.8126 | 0.1452 / 0.1452 | 1.000 / 1.000 | 0.1859 / 0.1859 | 0.0123 / 0.0123 | 0.0207 / 0.0207 |
| 500 | mean | 0.7237 / 0.7237 | 0.1612 / 0.1612 | 0.9966 / 0.9966 | 0.1290 / 0.1290 | 0.0200 / 0.0200 | 0.0204 / 0.0204 |
| 500 | zero | 0.5504 / 0.5504 | 0.2204 / 0.2204 | 0.9797 / 0.9797 | 0.2044 / 0.2044 | 0.0246 / 0.0246 | 0.0248 / 0.0248 |
| 1000 | twin | 0.8505 / 0.8505 | 0.3398 / 0.3398 | 1.000 / 1.000 | 0.4807 / 0.4807 | 0.0253 / 0.0253 | 0.0491 / 0.0491 |
| 1000 | mean | 0.7680 / 0.7680 | 0.4136 / 0.4136 | 1.000 / 1.000 | 0.8576 / 0.8576 | 0.0445 / 0.0445 | 0.0599 / 0.0599 |
| 1000 | zero | 0.5829 / 0.5829 | 0.2865 / 0.2865 | 0.9594 / 0.9594 | 0.2328 / 0.2328 | 0.0726 / 0.0726 | 0.0946 / 0.0946 |
| 2000 | twin | 0.8468 / 0.8468 | 0.4949 / 0.4949 | 1.000 / 1.000 | 0.9682 / 0.9682 | 0.0277 / 0.0277 | 0.0388 / 0.0388 |
| 2000 | mean | 0.7829 / 0.7829 | 0.5727 / 0.5727 | 1.000 / 1.000 | 1.000 / 1.000 | 0.0249 / 0.0249 | 0.0286 / 0.0286 |
| 2000 | zero | 0.5520 / 0.5520 | 0.4032 / 0.4032 | 0.9577 / 0.9577 | 0.9112 / 0.9112 | 0.0372 / 0.0372 | 0.0372 / 0.0372 |

Rates at margin 0.7 for D_only at size 500 (R8), mine and the verdict's equal:

| reference | D intact | D ablated | H used as comparison | rate effect intact | rate effect ablated |
|---|---|---|---|---|---|
| twin | 0.985 | 0.000 | intact H, 0.000 | 0.985 | 0.000 |
| mean | 0.985 | 0.0033 | ablated H, 0.000 | 0.985 | 0.0033 |
| zero | 0.985 | 0.020 | ablated H, 0.000 | 0.985 | 0.020 |

Ablated margin effect at size 500, from my recomputation (the verdict stores the drop, which matches):

| reference | D intact G | D ablated effect | I intact G | I ablated effect |
|---|---|---|---|---|
| twin | 9.834 | 1.843 | 14.709 | 12.573 |
| mean | 9.834 | 2.619 (2.717 against intact H) | 14.709 | 11.431 (12.337 against intact N) |
| zero | 9.834 | 1.680 (4.421 against intact H) | 14.709 | 7.729 (11.466 against intact N) |

Collateral for D_only, argmax accuracy shift in points. The mean column decides (R7). Every value equals the
verdict's.

| k | H, mean | F, mean | IOI, mean | H, twin reverse patch | H, zero | F, zero | IOI, zero |
|---|---|---|---|---|---|---|---|
| 500 | 0.0 | 0.0 | -6.0 | 0.0 | -1.5 | -1.8 | -17.0 |
| 1000 | -0.2 | 0.0 | -11.0 | 0.0 | -1.3 | -2.7 | -17.0 |
| 2000 | -0.8 | -0.2 | -13.0 | -1.0 | -2.8 | -5.7 | -19.0 |

Intact accuracy is 1.0 on H and F and 0.51 on IOI in every cell. IOI is not scored under twin, by design (R7).

Matched nulls for D_only, 20 draws each. The verdict's 20 null values match mine with a maximum difference of 0.0
for both D removed and the IOI shift.

| k | reference | null IOI shift, min | max | p95 of absolute shift (linear) |
|---|---|---|---|---|
| 500 | mean | -3 | +6 | 3.15 |
| 500 | zero | -2 | +5 | 2.15 |
| 1000 | mean | -9 | +6 | 6.15 |
| 2000 | mean | -8 | +8 | 8.0 |

The null H and F shifts are 0.0 in all 20 draws at every size, under mean and zero.

## The N1 bars at size 500

The verdict's bar flags agree with the numbers above. At size 500 every N1 bar passes except the IOI bar, under
twin and under mean, on the whole sample and in both halves:

| reference | subset | D removed | I removed | H shift | F shift | IOI shift | beats null p95 |
|---|---|---|---|---|---|---|---|
| twin | whole | 0.813 pass | 0.145 pass | 0.0 pass | 0.0 pass | -6.0 fail | pass |
| twin | half 1 | 0.811 pass | 0.146 pass | 0.0 pass | 0.0 pass | -6.0 fail | pass |
| twin | half 2 | 0.814 pass | 0.144 pass | 0.0 pass | 0.0 pass | -6.0 fail | pass |
| mean | whole | 0.724 pass | 0.161 pass | 0.0 pass | 0.0 pass | -6.0 fail | pass |
| mean | half 1 | 0.721 pass | 0.159 pass | 0.0 pass | 0.0 pass | -6.0 fail | pass |
| mean | half 2 | 0.726 pass | 0.163 pass | 0.0 pass | 0.0 pass | -6.0 fail | pass |

The half rows were read from `verdict.json`, not recomputed, because the half assignment comes from
`scripts/neuron_partition_data.py`. The IOI rows are the same 100 rows in both halves (`choices.ioi_in_halves`), so
the halves add no independent IOI evidence. At 1,000 and 2,000 the I bar also fails under twin and mean, so IOI
decides N1 only at 500.

## IOI resolution

At size 500 under mean ablation, 51 of 100 IOI rows are correct intact and 45 are correct ablated. Six rows went
from correct to wrong and none went from wrong to correct.

| measure | value |
|---|---|
| Shift | -6 points (6 lost, 0 gained) |
| Exact McNemar test against no change, two-sided | p = 0.031 |
| Clopper-Pearson 95% interval on 6 of 100 rows lost | 2.2% to 12.6%, so a shift of about -2 to -13 points |
| Bootstrap 95% interval over the 100 rows, 20,000 resamples, seed 0 | -11 to -2 points |
| Bootstrap share of resamples at -5 or below | 0.72 |
| Matched null shifts at 500, mean, 20 draws | -3 to +6; p95 of the absolute shift 3.15 |

What the sample shows:

- **The shift is distinguishable from zero.** All six discordant rows moved the same way, and the exact test gives
  p = 0.031.
- **It sits below every signed null at this size.** The 20 nulls span -3 to +6, so -6 ranks first of 21, a
  one-sided empirical p of about 0.05. The nulls' discordant rows are mixed in direction. The D_only set's are not.
- **It does not exceed the null band on absolute shift.** One null moved +6 points (0 lost, 6 gained), so an
  absolute shift of 6 ties the null maximum.
- **The sample cannot place the true shift relative to the 5-point bar.** The point estimate fails the bar by one
  row. Both 95% intervals run from about -2 to -11 or -13, so they cover true shifts that pass the bar and true
  shifts that fail it by a wide margin. A true shift of 3 and a true shift of 10 are both consistent with the data.
- **The bar sits inside the sampling noise at the larger sizes.** Random matched sets already move IOI by -9 points
  at 1,000 and -8 points at 2,000 under mean ablation. With 100 rows at 51% intact accuracy, one row is one point,
  and single random sets cross the 5-point bar.

The bar is not changed by this review. As written, the IOI bar fails at 500, so N1 fails at 500, and the verdict's
"fail" is the correct reading of the frozen text. The review's statement is that the IOI fail at 500 is a one-row
fail that this sample cannot confirm or rule out. A larger IOI sample would be needed to resolve it either way.

## Notes

1. **Percentile convention.** The spec does not name a percentile method. With 20 draws, the twin D-removed null
   p95 at 500 is 0.012 under linear interpolation and 0.021 under the "higher" method. The verdict uses linear, as
   I did. No verdict depends on it, since the tested set removes 0.81.
2. **Self-replay error.** `summary.json` reports 0.0 for D and I in all three cells. `rows.jsonl` holds no
   self-replay set, so this value was not recomputed. What was verified from rows is the pairing identity: every
   twin-reference row's `twin_m_intact` equals its twin's `m_intact` on 201,600 stream pairs per cell, maximum
   difference 0.0.
3. **The zero table in verdict.md shows the mean-reference collateral.** Its header says so, consistent with R7.
   The zero reference's own collateral is larger (IOI -17 at 500, F -5.7 at 2,000) and lives in `verdict.json`
   under `own`. Item 10 asks for disagreement among the three references to be reported, so the finding should
   quote the zero collateral beside the mean collateral.
4. **No lead at 500.** Item 10 records a partial pass (one reference, one half) as a lead. At 500 no
   reference-and-half combination meets every bar, because IOI fails in all six. `n1.by_k.500.lead` is false, which
   is consistent with the text.
5. **Cell layout.** Each cell has 84 sets (the four classes and 20 nulls for each), three references and 4,400
   rows per set, 369,600 lines. The "30 of 30 cells" in hand-back 02 are the 30 condition-stream passes in
   `summary.json`'s `timing` (8 twin, 11 mean, 11 zero), not 30 sets.

## Sanity checks

| check | k 500 | k 1,000 | k 2,000 |
|---|---|---|---|
| `rows.jsonl` lines | 369,600 | 369,600 | 369,600 |
| sets | 84 | 84 | 84 |
| ids per reference, set and condition | 300 (IOI 100), every combination | same | same |
| duplicate (reference, set, condition, id) | 0 | 0 | 0 |
| unpaired ids between D and H, and I and N (my join) | 0 | 0 | 0 |
| `summary.json` `unpaired` | empty | empty | empty |
| twin pairing, max of absolute `twin_m_intact` minus twin `m_intact` | 0.0 over 201,600 | 0.0 | 0.0 |
| same check on mean and zero D and I rows | 0.0 | 0.0 | 0.0 |
| intact margin equal across sets and references per condition, id and stream | max diff 0.0 | 0.0 | 0.0 |
| intact margin equal across the three cells (3,100 condition-id-stream keys) | reference | 0.0 | 0.0 |
| D and H rows share the opposite-answer token (D_only, all references) | 0 mismatches | 0 | 0 |
| `summary.json` `self_replay_error` (claim, not recomputed) | D 0.0, I 0.0 | same | same |
| `summary.json` `twin_crosscheck` | 0.0 on 600 per entry | same | same |
| IOI `sentences_sha256` | 61ebeea3...5e59 | same | same |
| hash of IOI ids and correct tokens (mine) | 8847f8e2...df57 | same | same |
| IOI intact accuracy | 0.51, the ladder's 0.51 | 0.51 | 0.51 |

## Commands and key output

All scripts are in `outputs/_analyses/neuron-partition/review3_tmp/`. `recompute.py` and `show.py` ran before any
verdict file was opened. `compare.py` ran after.

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review3_tmp/recompute.py /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review3_tmp/recompute.json
```

```
done 500
done 1000
done 2000
```

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review3_tmp/show.py /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review3_tmp/recompute.json
```

```
D_only:twin:D_ladder {"n": 300, "G": 9.8337, "drop": 7.9905, "frac": 0.8126, "G_ablated": 1.8432, ...}
D_only:twin:I_ladder {"n": 300, "G": 14.7085, "drop": 2.1356, "frac": 0.1452, "G_ablated": 12.5729, ...}
D_only:mean:D_ladder {"n": 300, "G": 9.8337, "drop": 7.1171, "frac": 0.7237, "G_ablated": 2.6189, ...}
D_only:mean:IOI_acc {"intact": 0.51, "ablated": 0.45, "shift_points": -6.0}
null:mean:IOI_shift {"values": [-2.0, 0.0, 3.0, 0.0, -1.0, -1.0, 2.0, 1.0, -1.0, 1.0, 2.0, -2.0, 0.0, 1.0, -3.0, 3.0, 6.0, -2.0, -1.0, -1.0], "min": -3.0, "max": 6.0, ...}
IOI_paired:mean {"n": 100, "intact_correct": 51, "ablated_correct": 45, "lost": 6, "gained": 0, "shift": -6.0, "mcnemar_exact_p": 0.0312, "ci95_bootstrap": [-11.0, -2.0], "boot_p_le_minus5": 0.7215, ...}
{"1000": {"n_common": 3100, ..., "max_diff": 0.0}, "2000": {"n_common": 3100, ..., "max_diff": 0.0}} True
```

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review3_tmp/compare.py
```

```
500 twin D removed margin | 0.8126 | 0.8126 | ok
500 mean IOI shift (mean, R7) | -6.0 | -6.0 | ok
500 mean null IOI shift max |diff| over 20 | 0.0 | 0.0 | ok
2000 mean I removed margin | 0.5727 | 0.5727 | ok
worst {'frac': 1.1102230246251565e-16, 'points': 0.0}
```

The Clopper-Pearson interval came from the same script's exact binomial code (mgnp has no scipy):

```
CP 6/100 (0.02233488607131634, 0.12602993458082296)
McNemar 6 vs 0 0.03125
```
