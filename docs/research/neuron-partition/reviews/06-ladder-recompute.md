# Review 06: independent recomputation of the finer size ladder (FAR, D-only classes at sizes 250 to 750)

**Verdict: CONFIRMED WITH CORRECTIONS.** Every number that ruling R19 and `verdict.md` state for the cell
`ladder-92fc6fb` was recomputed from `rows.jsonl` without the verdict script. Each matches to the stated precision.
Against `verdict.json`, 1,128 quantities agree with a worst difference of 1.1e-16 on fractions and 0.0 on points. The
N1 pass holds at all four sizes, under both references, on the whole sample and both halves: 24 of 24 cells pass.
The one correction is to a sentence of R19, not to a number. "The deception effect flat and the inversion cost
rising with size" is true under the twin reference only. Under mean, D removed rises from 0.69 to 0.78 and I removed
is not monotone.

Reviewer: R6 (Claude Opus, independent). Written Wed 4 Nov 2026, about 12:21 pm EST. `WT` below means
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition`, and `NP` means
`WT/outputs/_analyses/neuron-partition`.

- **Read before my numbers were saved.** Spec item 10 and rulings R2, R6 to R8, R10, R11, R14, R15 and R19;
  hand-back 09 with its ladder addendum; hand-back 10, W9's set construction; review 05 as the model; and
  `verdict.md`, which the brief names as the claim. The R19 numbers were therefore known to me before I computed
  mine.
- **Not read.** The verdict script `scripts/neuron_partition_verdict.py` was never opened, imported or run. The row
  schema was learned from the rows themselves and from the `definitions` block of `summary.json`. `verdict.json` was
  opened only after `NP/r6_tmp/recompute.json` was saved. I did not read review 05's scripts.
- **Called, not reimplemented.** `split_halves` from `scripts/neuron_partition_data.py`.
- **Not used.** No GPU, Slurm or version control. Everything ran on the Delta login node with the mgnp interpreter.

## Definitions used

- **Margins.** m is the row's `m_intact` or `m_ablated` per stream, in D's orientation. Within an id the clean and
  corrupt streams are averaged, then ids are averaged.
- **Margin removed (R2).** G is the mean over ids of the intact D margin minus the intact H margin of the same id.
  The fraction removed is the mean of intact minus ablated D margin, divided by G. I uses the user-neutral rows `N`.
  The H margin came from the H rows and equals the D row's `twin_m_intact` with a difference of 0.0.
- **Rate removed (R8).** The rate is the share of id-stream pairs with m at least 0.7. Rate removed is one minus the
  ablated rate effect over the intact rate effect. Under mean the ablated D rate is compared with the ablated H
  rate. Under twin it is compared with the intact H rate, because the donor is not patched.
- **Accuracy.** Full-vocabulary argmax against `correct_token` over every id-stream pair. IOI has one stream. A shift
  is ablated minus intact, in points. H, F and IOI collateral is read under mean for both references (R7).
- **Null percentile.** `numpy.percentile` with linear interpolation over the 20 matched nulls of the same size,
  reference and subset.
- **Halves (R10).** `split_halves(D ids, pressure_id, seed=2)` on the 208 seed-3 D ids, with pressure ids from the
  `far_v2` test split. Half 1 is A and half 2 is B. H, F, I and N take the D id's half. Every I id is a D id, so the
  union of D and I ids that `verdict.json` names is the same list. The split is D 104 and 104, I 78 and 88, as in
  review 05 and `verdict.json`. All 1,000 IOI rows enter both halves.
- **Bars.** Size at most 2,000, D removed (margin) at least 0.50, I removed (margin) under 0.25, H, F and IOI shifts
  each under 5 points in absolute value, and D removed above the null's 95th percentile. A size passes only if every
  bar holds under twin and mean, on the whole sample and on both halves.

## Recomputed numbers beside the claims

The claimed values are those of `verdict.md`. Mine are rounded the same way, and at full precision they agree with
`verdict.json` to the last digit. The rate column is the secondary measure (R2). Collateral is read under mean (R7),
so the twin rows repeat the mean values.

| ref | size (n) | D removed, margin: mine / claimed | D removed, rate | I removed, margin: mine / claimed | I removed, rate: mine / claimed | null p95 of D: mine / claimed | H, F shift | IOI shift: mine / claimed |
|---|---|---|---|---|---|---|---|---|
| twin | 250 (152) | 0.8126 / 0.813 | 1.000 / 1.000 | 0.0090 / 0.009 | 0.0301 / 0.030 | 0.0131 / 0.013 | 0.0, 0.0 | -2.7 / -2.7 |
| twin | 375 (243) | 0.8220 / 0.822 | 1.000 / 1.000 | 0.0576 / 0.058 | 0.0994 / 0.099 | 0.0205 / 0.021 | 0.0, 0.0 | -3.2 / -3.2 |
| twin | 625 (424) | 0.8229 / 0.823 | 1.000 / 1.000 | 0.1936 / 0.194 | 0.2229 / 0.223 | 0.0216 / 0.022 | 0.0, 0.0 | -1.4 / -1.4 |
| twin | 750 (524) | 0.8207 / 0.821 | 1.000 / 1.000 | 0.2169 / 0.217 | 0.2560 / 0.256 | 0.0348 / 0.035 | 0.0, 0.0 | -0.9 / -0.9 |
| mean | 250 (152) | 0.6878 / 0.688 | 1.000 / 1.000 | 0.1476 / 0.148 | 0.0753 / 0.075 | 0.0182 / 0.018 | 0.0, 0.0 | -2.7 / -2.7 |
| mean | 375 (243) | 0.7284 / 0.728 | 1.000 / 1.000 | 0.1265 / 0.126 | 0.0904 / 0.090 | 0.0330 / 0.033 | 0.0, 0.0 | -3.2 / -3.2 |
| mean | 625 (424) | 0.7581 / 0.758 | 1.000 / 1.000 | 0.1754 / 0.175 | 0.1295 / 0.130 | 0.0304 / 0.030 | 0.0, 0.0 | -1.4 / -1.4 |
| mean | 750 (524) | 0.7769 / 0.777 | 1.000 / 1.000 | 0.1694 / 0.169 | 0.1175 / 0.117 | 0.0655 / 0.066 | 0.0, 0.0 | -0.9 / -0.9 |

The halves, for the four quantities with a bar that depends on the half:

| ref | size | half 1: D, I, null p95 | half 2: D, I, null p95 |
|---|---|---|---|
| twin | 250 | 0.8150, 0.0083, 0.0133 | 0.8103, 0.0095, 0.0130 |
| twin | 375 | 0.8254, 0.0588, 0.0194 | 0.8185, 0.0565, 0.0217 |
| twin | 625 | 0.8267, 0.1986, 0.0228 | 0.8191, 0.1890, 0.0204 |
| twin | 750 | 0.8236, 0.2227, 0.0354 | 0.8177, 0.2118, 0.0323 |
| mean | 250 | 0.6917, 0.1506, 0.0186 | 0.6840, 0.1449, 0.0184 |
| mean | 375 | 0.7336, 0.1308, 0.0352 | 0.7231, 0.1225, 0.0308 |
| mean | 625 | 0.7613, 0.1827, 0.0314 | 0.7548, 0.1688, 0.0290 |
| mean | 750 | 0.7792, 0.1775, 0.0654 | 0.7746, 0.1621, 0.0656 |

H and F shift 0.0 on both halves at every size. The rate removed is 1.000 on every half. Intact G is 9.312 for D and
14.132 for I on the whole sample. The intact D rate is 0.988 and the ablated D rate is 0.0 at every size and
reference.

## The N1 bars, applied

| size | twin whole | twin half 1 | twin half 2 | mean whole | mean half 1 | mean half 2 | verdict | claimed |
|---|---|---|---|---|---|---|---|---|
| 250 | pass | pass | pass | pass | pass | pass | PASS | PASS |
| 375 | pass | pass | pass | pass | pass | pass | PASS | PASS |
| 625 | pass | pass | pass | pass | pass | pass | PASS | PASS |
| 750 | pass | pass | pass | pass | pass | pass | PASS | PASS |

The closest bar is I removed under twin at size 750: 0.2227 on half 1 against the 0.25 bar. Every other bar clears
by a wide margin. D removed is at least 0.684 against 0.50, beats the null's 95th percentile by at least 0.666, and
the largest absolute IOI shift is 3.2 against 5.

## R19 against my numbers

| R19 statement | mine | match |
|---|---|---|
| sizes 152, 243, 424 and 524 neurons | 152, 243, 424, 524 | yes |
| D removed (margin) 0.81 to 0.82 under twin | 0.8126 to 0.8229 | yes |
| D removed (margin) 0.69 to 0.78 under mean | 0.6878 to 0.7769 | yes |
| rate 1.0 everywhere | 1.000 in all 24 cells | yes |
| I removed 0.01 to 0.22 under twin | 0.0090 to 0.2169 | yes |
| I removed 0.13 to 0.18 under mean | 0.1265 to 0.1754 | yes |
| null 95th percentile at most 0.066 | at most 0.0656, on mean half 2 at size 750 | yes |
| H and F shift 0.0 | 0.0 everywhere | yes |
| IOI shift minus 2.7, 3.2, 1.4 and 0.9 points | -2.7, -3.2, -1.4, -0.9 | yes |
| every N1 bar met under twin and mean, whole and both halves | 24 of 24 cells pass | yes |
| "the deception effect flat and the inversion cost rising with size" | twin only, see correction 1 | no |
| 3,041 s of 5,400 reserved | not checked; `summary.json` gives 2,786 s of script wall time | not checked |

## Corrections

1. **The trend sentence of R19 holds under twin only.** Under twin, D removed is flat at 0.81 to 0.82, and I removed
   rises at every step: 0.009, 0.058, 0.194, 0.217. Under mean, D removed rises at every step: 0.688, 0.728, 0.758,
   0.777. I removed under mean is not monotone: 0.148, 0.126, 0.175, 0.169. Suggested wording: "under the twin
   interchange the deception effect is flat and the inversion cost rises with size; under mean ablation the
   deception effect rises from 0.69 to 0.78 and the inversion cost stays between 0.13 and 0.18 with no trend."

## Sanity checks

| check | expected | observed | result |
|---|---|---|---|
| rows in `rows.jsonl` | 84 sets × 2,704 = 227,136 | 227,136, no duplicate reference, set, condition and id | ok |
| rows per set | twin D, H 208 and I, N 166; mean D, H, F 208, I, N 166 and IOI 1,000 | 2,704 for all 84 sets | ok |
| ids per condition | equal to `NP/data/far_test_sample_seed3.json` | equal on all 840 reference, set and condition groups | ok |
| the R14 confirmation sample | the same file | sha256 `bdd94ce2…87d6` in both manifests; the R14 cell `confirm_k500-d3d842b` holds the same ids in every group | ok |
| IOI rows | `ioi:seed=2:row=0..999`, the R14 draw | exactly those ids; sentence sha256 `906a93ed…ba86e0` in both summaries; `correct_token` equal on 1,000 of 1,000 rows | ok |
| intact IOI accuracy | near the ladder's 0.51 | 0.511, against 0.513 for the same rows in the R14 cell; see note 4 | ok |
| intact margins across sets and references | identical | maximum difference 0.0; argmax and correct token identical | ok |
| self-replay error and twin cross-check | 0 | `summary.json` gives 0.0 for D and I; cross-check 0.0 on 416 D and 332 I rows; `unpaired` empty; read from the summary, not recomputable from rows | ok |
| D_only membership | rule R6 with the R11 all-position scores of c3d7763 | rebuilt as T_D minus (T_I union T_H), top k positive only, ties to the lower flat index: 152, 243, 424 and 524 neurons, equal to `ladder_sets.json` and `NP/sets/far_atp_all_c3d7763_ladder/far_all_sets_k*.json`; T_D, T_I and T_H also equal | ok |
| the rule at size 500 | equal to F6's class | my rebuild gives 338, equal to `NP/sets/far_atp_all_c3d7763/far_all_sets_k500.json` | ok |
| score sources | one ranking | `atp_all_mean` of the plain and `_rev` dh runs differ by 0.0; same for the I runs; s_H is minus `rev_atp_all_mean` | ok |
| nulls | 20 per size, size and layer matched, disjoint | 20 of 20 at each size: same size, same 32-layer histogram, no neuron shared with the class, all distinct, equal to the `_with_nulls` files; per-layer counts in `summary.json` equal for all 84 sets | ok |
| nesting | not required | 144 of 152, 237 of 243, 325 of 338 and 415 of 424 members kept at each step, as hand-back 10 reports | ok |
| manifest | dataset and code hashes | 71 of 71 dataset hashes re-verified on Delta; 35 are recorded under Bridges-2 absolute paths and match the worktree files; 70 of 71 equal the R14 manifest, the exception being the sets file; the 5 code hashes equal the worktree now and the R14 manifest | ok |

File hashes at review time: `rows.jsonl` `c9e5730b…66f5a`, `summary.json` `a2cbb089…56a23`, `run_manifest.json`
`bf584c26…227cc`, `verdict.json` `548806ae…a4a69`, `verdict.md` `052b4668…4e81b`. The first two equal the hashes that
`verdict.json` records.

## Notes

1. **The tightest bar is the inversion cost under twin.** R15 (b) asks for the first bar to fail as the size grows.
   None fails between 250 and 750. The closest is I removed under twin, 0.217 of 0.25 at size 750 on the whole sample
   and 0.223 on half 1. On the secondary rate measure the same quantity is 0.256 at 750, over 0.25 on the whole
   sample and both halves (0.256 and 0.256). The pass stands because R2 reads the bars on the margin. The finding
   should name the inversion cost as the bar that would fail first, and say that the rate measure already crosses
   it at 750.
2. **The IOI shift of minus 2.7 at size 250 and at size 500 is a numerical coincidence, not a shared artefact.**
   The two values are built from different counts. At 250 in the ladder cell, 33 rows turn wrong and 6 turn right.
   At 500 in the R14 cell, 38 turn wrong and 11 turn right. The intact baselines also differ, 0.511 against 0.513.
   The ablated IOI margins differ between the two classes by 0.109 logits per row on average, so neither value is a
   cached or shared number. The underlying cost is partly shared, as expected. 141 of the 152 neurons at size 250 are
   in the 338-neuron class at 500. 24 of the 33 rows lost at 250 are also lost at 500. The per-row IOI margin changes
   correlate at 0.77.
3. **The class moves IOI more than its random sets do.** The IOI bar is absolute, so this does not affect the pass.
   But at sizes 250, 375 and 625 the class's IOI shift lies below every one of its 20 nulls. At 750 it lies inside
   the null range.

   | size | class IOI shift | null minimum | null maximum |
   |---|---|---|---|
   | 250 | -2.7 | -0.7 | +2.4 |
   | 375 | -3.2 | -0.9 | +1.5 |
   | 625 | -1.4 | -1.3 | +3.0 |
   | 750 | -0.9 | -1.7 | +2.5 |

   The R14 cell's nulls ranged from -1.3 to +2.2 against the class's -2.7. A small IOI cost specific to the class is
   therefore consistent across cells. It stays well under the 5-point bar.
4. **The same IOI rows give 0.511 here and 0.513 in the R14 cell.** 9 of 1,000 rows change their intact argmax. The
   ladder ran on a Bridges-2 H100 and the R14 cell on a Delta A40, so this is bf16 drift across hardware. Intact
   margins differ by at most 0.31 logits, with a median of 0.045. Each cell's shift uses its own intact baseline, so
   the shifts are internally consistent. Comparisons of IOI accuracy across cells carry about 0.2 points of hardware
   noise.
5. **H and F collateral is exactly 0.0 for the class and every null.** The intact H margins sit far below the 0.7
   screen and the argmax does not move. The H and F bars are therefore not discriminating at these sizes. The twin
   reverse patch, which is descriptive, moves H by -0.24 points at size 625 and 0.0 elsewhere.
6. **Provenance label.** The manifest names commit `d5f6b17` and the directory names `92fc6fb`, as hand-back 09
   reports. The manifest records the Bridges-2 clone's head. The five scored code files hash identically to the
   worktree and to the R14 cell, so the code that ran is pinned whatever the label.
7. **Not recomputed.** The bootstrap intervals in `verdict.md` were not reproduced. The Slurm elapsed time of 3,041 s
   was not checked, because the job ran on Bridges-2.
8. **This review is the recomputation R15 and R19 ask for.** The ladder outcome can lose its preliminary tag with
   correction 1 applied. The largest size meeting every bar is 750, the largest size tested. The class's specific
   size is therefore not bounded above by this ladder.

The class and null D-removed values on the whole sample, margin, nulls in set order 0 to 19 for size 250:

```
twin: 0.0109 0.0096 0.0130 -0.0010 0.0049 0.0002 0.0017 0.0072 0.0150 0.0080
      -0.0023 0.0010 0.0029 -0.0012 0.0015 0.0053 -0.0066 -0.0036 0.0040 0.0003
```

All null values for every size, reference and subset are in `NP/r6_tmp/recompute.json`.

## Commands

Every command ran on the Delta login node. The scripts are in `NP/r6_tmp/`.

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r6_tmp/schema.py
```

Observed: "rows 227136 dups 0", each reference and condition count, "sets 84 {2704}".

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r6_tmp/recompute.py
```

Observed: "halves {'D': {'B': 104, 'A': 104}, ... 'I': {'B': 88, 'A': 78}, ...}", the 24 lines of the tables above,
each ending "pass True", and "N1 verdict per k {250: True, 375: True, 625: True, 750: True}". Output
`NP/r6_tmp/recompute.json`.

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r6_tmp/sets_check.py
```

Observed: "dh vs dh_rev atp_all_mean max diff 0.0"; for each size "rebuilt D_only 152 equals sets file True T_D/T_I/T_H
equal True ... equals ladder_sets True" and "nulls: size 20/20 layer hist 20/20 disjoint 20/20 equal to with_nulls
file 20/20 distinct 20/20"; "k500: rebuilt D_only 338 equals sets file True".

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r6_tmp/provenance.py
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r6_tmp/abs_paths.py
```

Observed: "id mismatches vs seed-3 file 0 IOI id mismatches 0" for both cells; "intact margin max diff across 84
sets x 2 refs 0.0"; "IOI intact acc ladder 0.511 R14 0.513"; "argmax equal 991/1000"; "ladder 250: lost 33 gained
6 net -2.7"; "R14 500: lost 38 gained 11 net -2.7"; "overlap lost 250 & 500: 24"; "correlation ... 0.772";
"D_only_250 within the R14 D_only (500): 141 of 152"; every code hash "WT equal True R14 manifest equal True";
"absolute Bridges-2 paths mapped onto WT: equal 35 mismatched 0".

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r6_tmp/compare.py
```

This ran after `recompute.json` was saved. Observed: "compared 1128 worst fraction diff 1.1102230246251565e-16 worst
point diff 0.0", "flags [] 0", and the pass flag equal at all four sizes. The 1,128 quantities are D and I removed by
margin and rate, the null p95 of D removed, every null D and I removed value, and the H, F and IOI shifts, over the
24 reference, size and subset cells.

```
TZ=America/New_York date "+%I:%M %p %Z"
```

Observed: "12:21 PM EST".
