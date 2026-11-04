# Review 04: independent recomputation of the R14 confirmation cell (FAR, size-500 D-only class)

**Verdict: CONFIRMED WITH NOTES.** Every headline number of the confirmation cell `confirm_k500-d3d842b` was
recomputed from `rows.jsonl` without the verdict script and matches the verdict to floating-point precision. The
largest difference is 0.0 on every fraction and 0.0 on every point. Every R14 bar is met under the twin and mean
references, on the whole seed-3 sample and on both halves. The notes concern reading the result, not arithmetic.

Reviewer: rev4 (Claude Opus, independent). Written Tue 3 Nov 2026. `WT` below means
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition`.

- **Not read before my numbers were saved.** The verdict script `scripts/neuron_partition_verdict.py`, the files in
  `verdict/confirm_k500-d3d842b/`, the `review3_tmp/` and `w8_tmp/` scripts, and hand-back 08 were not opened. My
  numbers were written to `WT/outputs/_analyses/neuron-partition/review4_tmp/recompute.json` first. The verdict
  script was never read.
- **Read for scope.** Spec rulings R2, R7, R8, R10 and R14, START item 10, section 2 of the reader brief, the
  `rows.jsonl` schema in hand-back 02, and `split_halves` and its caller in `scripts/neuron_partition_data.py`.
- **Called, not reimplemented.** `split_halves` from `scripts/neuron_partition_data.py`, and `ioi_rows` and
  `ioi_sentences_sha256` from `scripts/neuron_set_ablation.py`, which regenerate the IOI sentences on CPU.
- **Not used.** No GPU, Slurm or version control.

## Definitions used

- **Margin effect (R2).** For each id, every margin is averaged over the clean and corrupt streams. G is the mean
  over ids of the intact D margin minus the intact H-twin margin. The drop is the mean over ids of the intact D
  margin minus the ablated D margin. The fraction removed is the drop divided by G, a ratio of means.
- **The twin margin.** It was read from the D row's `twin_m_intact` field. It was checked equal to the intact margin
  of the H row with the same id, with a maximum difference of 0.0. The inversion effect uses I against N the same
  way.
- **G under both references.** It is the intact effect, so it is the same under twin and mean, with a difference of
  0.0.
- **Accuracy.** This is full-vocabulary argmax accuracy against `correct_token`, over every id and stream pair.
  IOI has one stream. The shift is ablated minus intact, in points.
- **Null p95.** `numpy.percentile(values, 95)` with its default linear interpolation, over the 20 null D-removed
  values of the same reference and subset.
- **Halves (R10).** `split_halves(D ids, pressure_id, seed=2)` was run on the 208 seed-3 D ids. Pressure ids came
  from the `far_v2` test split. H and F take D's half by id. All 166 I ids are D ids, so I and N take D's half by
  id, which is how W3's rank halves treat I. The split gives D 104 and 104, and I 78 and 88. IOI has no id in the
  seed-3 sample, so the IOI bar is read on all 1,000 rows only.

## Recomputed numbers beside the verdict

D and I removed are on the margin effect (R2). Collateral is read under the mean reference (R7). The verdict column
gives `verdict.json` rounded the same way; the full-precision values agree to the last printed digit.

| reference | subset | quantity | recomputed | verdict | difference |
|---|---|---|---|---|---|
| twin | whole | G of D, logits | 9.2979 | 9.2979 | 0.0 |
| twin | whole | G of I, logits | 14.1254 | 14.1254 | 0.0 |
| twin | whole | D removed | 0.8222 | 0.8222 | 0.0 |
| twin | whole | I removed | 0.1409 | 0.1409 | 0.0 |
| twin | whole | null p95 of D removed | 0.0134 | 0.0134 | 0.0 |
| twin | half A | D removed | 0.8242 | 0.8242 | 0.0 |
| twin | half A | I removed | 0.1448 | 0.1448 | 0.0 |
| twin | half A | null p95 of D removed | 0.0149 | 0.0149 | 0.0 |
| twin | half B | D removed | 0.8201 | 0.8201 | 0.0 |
| twin | half B | I removed | 0.1374 | 0.1374 | 0.0 |
| twin | half B | null p95 of D removed | 0.0120 | 0.0120 | 0.0 |
| mean | whole | D removed | 0.7476 | 0.7476 | 0.0 |
| mean | whole | I removed | 0.1538 | 0.1538 | 0.0 |
| mean | whole | null p95 of D removed | 0.0212 | 0.0212 | 0.0 |
| mean | half A | D removed | 0.7512 | 0.7512 | 0.0 |
| mean | half A | I removed | 0.1599 | 0.1599 | 0.0 |
| mean | half A | null p95 of D removed | 0.0227 | 0.0227 | 0.0 |
| mean | half B | D removed | 0.7439 | 0.7439 | 0.0 |
| mean | half B | I removed | 0.1483 | 0.1483 | 0.0 |
| mean | half B | null p95 of D removed | 0.0201 | 0.0201 | 0.0 |
| mean | whole | H accuracy, intact to ablated, points | 100.0 to 100.0, shift 0.0 | 0.0 | 0.0 |
| mean | whole | F accuracy, intact to ablated, points | 100.0 to 100.0, shift 0.0 | 0.0 | 0.0 |
| mean | whole | IOI accuracy, intact to ablated, points | 51.3 to 48.6, shift -2.7 | -2.7 | 0.0 |
| mean | halves A and B | H and F shift, points | 0.0 and 0.0 | 0.0 and 0.0 | 0.0 |
| mean | whole | null IOI shift, min and max, points | -1.3 and +2.2 | -1.3 and +2.2 (hand-back 08) | 0.0 |
| mean | whole | null H and F shift, every null, points | 0.0 | 0.0 | 0.0 |

The secondary rate measure at margin 0.7 also matches. The verdict's rate columns follow from these rates.

| reference | intact D rate | ablated D rate | intact I rate | ablated I rate | N rate, intact and ablated | I removed, rate |
|---|---|---|---|---|---|---|
| twin | 0.986 | 0.000 | 1.000 | 0.825 | 0.0 and 0.0 | 0.175 |
| mean | 0.986 | 0.000 | 1.000 | 0.874 | 0.0 and 0.0 | 0.127 |

The null D-removed values on the whole sample, in set order 0 to 19, are below.

```
twin: 0.0058 -0.0056 -0.0076 0.0187 0.0024 0.0053 -0.0130 0.0030 -0.0035 0.0092
      -0.0073 0.0099 0.0122 0.0131 -0.0155 -0.0114 -0.0055 0.0107 0.0092 0.0119
mean: 0.0060 -0.0180 0.0128 0.0027 0.0154 -0.0142 0.0153 0.0111 -0.0079 -0.0020
      0.0235 -0.0241 -0.0063 0.0092 -0.0175 0.0090 0.0197 0.0211 -0.0062 0.0087
```

## R14 bar checks

R7 reads the H, F and IOI bars under the mean reference for every tested set. Under the twin reference the H patch is
the descriptive reverse patch, so twin cells are decided on the three effect bars. The verdict script fills the twin
cells' collateral from the mean reference; that gives the same pass.

| bar | needed | twin whole | twin A | twin B | mean whole | mean A | mean B |
|---|---|---|---|---|---|---|---|
| size | at most 2,000 | 338, pass | 338, pass | 338, pass | 338, pass | 338, pass | 338, pass |
| D removed | at least 0.50 | 0.822, pass | 0.824, pass | 0.820, pass | 0.748, pass | 0.751, pass | 0.744, pass |
| I removed | under 0.25 | 0.141, pass | 0.145, pass | 0.137, pass | 0.154, pass | 0.160, pass | 0.148, pass |
| D removed above null p95 | strictly greater | 0.822 vs 0.013, pass | 0.824 vs 0.015, pass | 0.820 vs 0.012, pass | 0.748 vs 0.021, pass | 0.751 vs 0.023, pass | 0.744 vs 0.020, pass |
| absolute H shift | under 5 points | (R7: mean) | (R7: mean) | (R7: mean) | 0.0, pass | 0.0, pass | 0.0, pass |
| absolute F shift | under 5 points | (R7: mean) | (R7: mean) | (R7: mean) | 0.0, pass | 0.0, pass | 0.0, pass |
| absolute IOI shift, 1,000 fresh rows | under 5 points | (R7: mean) | (R7: mean) | (R7: mean) | 2.7, pass | whole only | whole only |

Every bar is met in every cell. Under R14 this reads "the size-500 lead is confirmed on fresh data", and this review
is the independent recomputation that R14 asks for before the result stops being preliminary.

## Sanity checks

| check | expected | observed | result |
|---|---|---|---|
| rows in `rows.jsonl` | 21 sets × (twin 748 + mean 956 + IOI 1,000) = 56,784 | 56,784, no duplicate set, reference, condition and id | ok |
| rows per set | twin D, H 208, I, N 166; mean D, H, F 208, I, N 166, IOI 1,000 | the same for every set | ok |
| ids per condition | equal to the seed-3 sample's ids | equal on all nine reference and condition pairs | ok |
| overlap with `far_test_sample_seed2.json` | none | 0 on D, H, F, I and N, against any seed-2 condition | ok |
| overlap with the six exclusion lists | none | 0 of 792 excluded ids | ok |
| unpaired rows | none | `summary.unpaired` is empty, and no twin-reference D or I row lacks `twin_m_intact` | ok |
| intact margins across sets | identical | maximum difference 0.0, every reference and condition | ok |
| IOI rows | 1,000, seed 2 | 1,000 ids `ioi:seed=2:row=0..999`, the same as a fresh regeneration | ok |
| IOI sentences sha256, seed 2 | `906a93ed…` | regenerated `906a93edad3c76f5…ba86e0` | ok |
| IOI sentences sha256, seed 1 | `fec3aa49…` | regenerated `fec3aa4911b56032…c9a30e`, the same as `ioi_resolution-delta-e8dd8a8/summary.json` | ok |
| IOI sentences shared with seed 1 | dropped and counted | 0 shared sentences and 0 shared prefixes, so nothing was dropped | ok |
| intact IOI accuracy | near the ladder's 0.51 | 0.513 | ok |
| sets | the D-only class at size 500 and its 20 nulls from the k500 file | all 21 equal to `far_all_sets_k500_with_nulls.json`; 338 neurons each; every null has D-only's per-layer counts and no neuron in common with it | ok |
| manifest | commit d3d842b, clean | `d3d842b886971e196d0f7df139e2d32a1dc22a97`, `git_dirty` false; all 71 `dataset_files` hashes re-verified on disk | ok |
| self-replay and twin cross-check | 0 | 0.0 for D and I; cross-check 0.0 on 416 D and 332 I rows | ok |
| file hashes in hand-back 08 | as listed | `rows.jsonl`, `summary.json`, `run_manifest.json`, the seed-3 sample, `verdict.json` and `verdict.md` all match | ok |

## Notes

1. **The IOI cost is real, and the bar holds.** The class lowers IOI accuracy by 2.7 points on 1,000 fresh rows.
   38 rows go from correct to wrong and 11 from wrong to correct. The exact McNemar p is 0.00014. The shift lies
   outside the nulls' range of -1.3 to +2.2. This review reproduced hand-back 08's counts. The finding should report
   the cost beside the pass.
2. **I removed has less headroom under an inside-the-model reading.** R2's fraction compares ablated I with the
   intact user-neutral twin. Mean ablation also moves the user-neutral margin 1.08 logits toward the inverted answer.
   Read as 1 minus the ablated I-minus-N gap over the intact gap, the analogue of R8's rate rule, I removed is 0.230
   on the whole sample, 0.234 on half A and 0.227 on half B. This is still under 0.25, but by about 0.02. It is not a
   bar under R2, so it does not change the verdict. The same reading gives D removed 0.763.
3. **The rate measure saturates.** The D rate effect goes from 0.986 to 0.0 under both references, so D removed on
   the rate is 1.000 everywhere. The margin measure is the one that discriminates, as R2 says.
4. **I accuracy falls on the inversion rows.** I argmax accuracy drops 7.2 points under twin and 3.6 under mean.
   This is not an R14 bar, because I collateral is measured by I removed. It shows the class touches the inversion
   route a little, consistent with I removed of 0.14 to 0.16.
5. **The I sample is below item 10's floor of 300 rows.** R14 takes every eligible id after the exclusions, which
   gives 166 I and N rows and 208 D, H and F rows. The finding should state the sample sizes.
6. **IOI enters both halves whole.** The IOI rows are not part of the seed-3 id sample, so both halves read the
   same -2.7 points. This is how R14 states it ("IOI on the 1,000 fresh rows").
7. **W8's own check was not independent.** Hand-back 08 reran copies of the review-03 scripts. This review shares no
   code with those scripts or with the verdict script, so it meets R14's independent-recomputation clause.

## Commands

Every command was run from `WT` with the mgnp interpreter. The scripts are in
`WT/outputs/_analyses/neuron-partition/review4_tmp/`.

```
/u/swong2/.conda/envs/mgnp/bin/python WT/outputs/_analyses/neuron-partition/review4_tmp/recompute.py
```

Observed: "rows 56784 dups 0", the halves 104 and 104 for D and 78 and 88 for I, every value in the first table, and
"ALL BARS PASS True". The output is `review4_tmp/recompute.json`.

```
/u/swong2/.conda/envs/mgnp/bin/python WT/outputs/_analyses/neuron-partition/review4_tmp/sanity.py
```

Observed: 0 overlap with seed 2 on every condition, 0 overlap with the 792 excluded ids, `unpaired {}`, and the IOI
sentence hashes stored in both summaries.

```
PYTHONHASHSEED=0 /u/swong2/.conda/envs/mgnp/bin/python WT/outputs/_analyses/neuron-partition/review4_tmp/ioi_check.py
```

Observed: seed 2 regenerates `906a93ed…` and seed 1 regenerates `fec3aa49…`, with 1,000 rows each,
"shared_sentences": 0 and "seed2_ids_match_rows": true. The output is `review4_tmp/ioi_check.json`.

```
/u/swong2/.conda/envs/mgnp/bin/python WT/outputs/_analyses/neuron-partition/review4_tmp/sets_check.py
```

Observed: 71 manifest hashes re-verified; all 21 sets equal to the k500 source, 338 neurons each, layer-matched, and
disjoint from D-only.

```
/u/swong2/.conda/envs/mgnp/bin/python WT/outputs/_analyses/neuron-partition/review4_tmp/ioi_paired.py
/u/swong2/.conda/envs/mgnp/bin/python WT/outputs/_analyses/neuron-partition/review4_tmp/inside_effect.py
```

Observed: "correct->wrong 38 wrong->correct 11 exact McNemar p 0.000142"; the inside-the-model I removed is 0.2302
on the whole sample, 0.2337 on half A and 0.2271 on half B.

```
/u/swong2/.conda/envs/mgnp/bin/python WT/outputs/_analyses/neuron-partition/review4_tmp/compare.py
/u/swong2/.conda/envs/mgnp/bin/python WT/outputs/_analyses/neuron-partition/review4_tmp/diff.py
sha256sum <the cell, sample and verdict files>
```

These ran after my numbers were saved. Observed: "compared 188 worst fraction diff 0.0 worst point diff 0.0". The
188 quantities are D and I removed, both G values, the null p95, every null D-removed value, the H, F and IOI shifts
and every null IOI shift, over six cells. The pass flags agree in all six cells, and the file hashes equal those in
hand-back 08.
