# Review 05: independent recomputation of the N2 fresh-data cell (FAR, size-2,000 H-only class)

**Verdict: CONFIRMED.** Every number that ruling R18 and finding F7 state for the cell
`confirm_h_only_k2000-3486f1a` was recomputed from `rows.jsonl` without the verdict script. Each matches to the
stated precision. Against `verdict.json`, 420 quantities agree with a worst difference of 6e-17 on fractions and
7e-15 on points. The item 10 N2 rule under the mean reference gives "suppression or shared" on the whole sample and
on both halves, and the twin rows give the same label. The notes below concern how F7 should read the label, not the
arithmetic. The largest note is that matched random sets lower D's deceptive rate about as much as the class does.

Reviewer: R5 (Claude Opus, independent). Written Wed 4 Nov 2026, about 11:30 am EST. `WT` below means
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition`.

- **Read before my numbers were saved.** Spec item 10 and rulings R2, R7, R8, R10, R14, R15 and R18; hand-back 09;
  review 04; `verdict.md`, which the brief names as the claim; the definitions in hand-back 05 and review 03; and
  section 2 of the reader brief. The R18 numbers were therefore known to me before I computed mine.
- **Not read.** The verdict script `scripts/neuron_partition_verdict.py` was never opened, imported or run. Its row
  schema was learned from the rows themselves. `verdict.json` was opened only after
  `WT/outputs/_analyses/neuron-partition/r5_tmp/recompute.json` was saved.
- **Called, not reimplemented.** `split_halves` from `scripts/neuron_partition_data.py`.
- **Not used.** No GPU, Slurm or version control. Everything ran on the Delta login node with the mgnp interpreter.

## Definitions used

- **Margins.** m is the row's `m_intact` or `m_ablated` per stream, in D's orientation (positive means the deceptive
  or inverted token). Within an id the clean and corrupt streams are averaged, then ids are averaged.
- **Margin removed (R2).** G is the mean over ids of the intact D margin minus the intact H margin of the same id. The
  fraction removed is the mean of intact minus ablated D margin, divided by G. I uses the user-neutral rows `N`. The
  H margin was taken from the H rows and checked equal to the D row's `twin_m_intact`, with a difference of 0.0.
- **Deceptive rate.** The share of id-stream pairs with m at least 0.7. D's deceptive-rate change for N2 is the
  ablated D rate minus the intact D rate, in points. This is item 10's literal "D's deceptive rate" and the default
  of hand-back 05. No ruling replaced it.
- **Rate removed (R8).** One minus the ablated rate effect over the intact rate effect. Under mean the ablated D rate
  is compared with the ablated H rate. Under twin it is compared with the intact H rate.
- **Accuracy.** Full-vocabulary argmax against `correct_token` over every id-stream pair. IOI has one stream. A shift
  is ablated minus intact, in points. H, F and IOI collateral is read under mean (R7). The twin H shift is the
  descriptive reverse patch.
- **Null percentile.** `numpy.percentile` with linear interpolation over the 20 matched nulls of the same reference
  and subset. The N2 null bar is the 95th percentile of the absolute null H shift, as hand-back 05 set it.
- **Halves (R10).** `split_halves(D ids, pressure_id, seed=2)` on the 208 seed-3 D ids, with pressure ids from the
  `far_v2` test split. Half 1 is A and half 2 is B. H and F take D's half by id. Every I id is a D id, so I and N take
  that id's half. The split is D 104 and 104, I 78 and 88, the same as review 04. IOI is not in the id sample, so
  all 1,000 IOI rows enter both halves.

## Recomputed numbers beside the claims

The claimed column quotes R18 and `verdict.md`. Mine are rounded the same way; full precision agrees with
`verdict.json` to the last digit.

| reference | subset | quantity | mine | claimed | match |
|---|---|---|---|---|---|
| mean | whole | H accuracy shift, points | -21.875 | -21.9 | yes |
| mean | whole | D deceptive rate, intact to ablated | 0.986 to 0.858 | | |
| mean | whole | D deceptive-rate change, points | -12.740 | -12.7 | yes |
| mean | half 1 | H shift and D rate change, points | -21.635 and -10.577 | 21.6 and 10.6 | yes |
| mean | half 2 | H shift and D rate change, points | -22.115 and -14.904 | 22.1 and 14.9 | yes |
| mean | whole, half 1, half 2 | null p95 of the absolute H shift, points | 0.0, 0.0, 0.0 | 0.0 | yes |
| mean | whole | D removed, margin | -0.6387 | -0.64 | yes |
| twin | whole | D removed, margin | -0.5279 | -0.53 | yes |
| mean | whole | F accuracy shift, points | -19.231 | -19.2 | yes |
| mean | whole | IOI accuracy shift, points, 1,000 rows | -2.400 (51.3 to 48.9) | -2.4 | yes |
| mean | whole | G of D and G of I, logits | 9.2979 and 14.1254 | | |
| mean | whole | I removed, margin | -0.1072 | -0.107 | yes |
| mean | whole | D and I removed, rate | 0.2195 and 0.2861 | 0.220 and 0.286 | yes |
| mean | whole | null p95 of D removed, margin | 0.0708 | 0.071 | yes |
| twin | whole | I removed, margin | -0.4583 | -0.458 | yes |
| twin | whole | D and I removed, rate | 0.1976 and 0.0241 | 0.198 and 0.024 | yes |
| twin | whole | null p95 of D removed, margin | 0.0607 | 0.061 | yes |
| twin | whole | H shift (reverse patch) and D rate change, points | -49.760 and -19.471 | -49.8 and -19.5 | yes |
| twin | half 1 | H shift and D rate change, points | -46.635 and -16.827 | -46.6 and -16.8 | yes |
| twin | half 2 | H shift and D rate change, points | -52.885 and -22.115 | -52.9 and -22.1 | yes |

The halves of the other measures, under mean, are below. F is -19.231 on each half by coincidence: 40 of 208 pairs
fail in each half.

| subset | D removed, margin | I removed, margin | D removed, rate | I removed, rate | F shift | null p95 of D removed |
|---|---|---|---|---|---|---|
| half 1 | -0.6510 | -0.0954 | 0.2059 | 0.3077 | -19.231 | 0.0721 |
| half 2 | -0.6263 | -0.1180 | 0.2330 | 0.2670 | -19.231 | 0.0695 |

## The N2 rule, applied

Item 10: bypass needs an H drop of at least 20 points, D's deceptive rate moving under 5 points and the null under
5 points. "Suppression or shared" needs the same H and null conditions with D's rate falling at least 10 points.

| reference | subset | H drop at least 20 | null p95 of absolute H shift under 5 | D rate change | label |
|---|---|---|---|---|---|
| mean | whole | 21.9, yes | 0.0, yes | -12.7, falls at least 10 | suppression or shared |
| mean | half 1 | 21.6, yes | 0.0, yes | -10.6, falls at least 10 | suppression or shared |
| mean | half 2 | 22.1, yes | 0.0, yes | -14.9, falls at least 10 | suppression or shared |
| twin | whole | 49.8, yes | 0.0, yes | -19.5, falls at least 10 | suppression or shared |
| twin | half 1 | 46.6, yes | 0.0, yes | -16.8, falls at least 10 | suppression or shared |
| twin | half 2 | 52.9, yes | 0.0, yes | -22.1, falls at least 10 | suppression or shared |

"Suppression or shared" holds on every row. Half 1 under mean clears the 10-point bar by 0.6 points.

## Sanity checks

| check | expected | observed | result |
|---|---|---|---|
| rows in `rows.jsonl` | 21 × (208 D + 208 H + 208 F + 166 I + 166 N + 1,000 IOI) plus twin D, H, I, N = 56,784 | 56,784, no duplicate reference, set, condition and id | ok |
| rows per set | twin D, H 208, I, N 166; mean D, H, F 208, I, N 166, IOI 1,000 | the same for all 21 sets | ok |
| ids per condition | equal to `data/far_test_sample_seed3.json` | equal on every reference, set and condition | ok |
| overlap with `data/far_test_sample_seed2.json` | none | 0 on D, H, F, I and N, against all 436 seed-2 ids | ok |
| overlap with the ranking ids `data/far_rank_ids.json` | none | 0 against 400 train and validation ids | ok |
| overlap with the 792 excluded ids of the sample file | none | 0 | ok |
| intact margins across sets and references | identical | maximum difference 0.0, argmax identical | ok |
| H twin margin | equal to the D row's `twin_m_intact` | maximum difference 0.0, both references, D and I | ok |
| IOI rows | `ioi:seed=2:row=0..999` | exactly those ids; intact margins and correct tokens equal to the R14 cell `confirm_k500-d3d842b`; sentence sha256 `906a93ed…ba86e0` in both summaries | ok |
| intact IOI accuracy | near the ladder's 0.51 | 0.513 | ok |
| self-replay error and twin cross-check | 0 | `summary.json` gives 0.0 for D and I; cross-check 0.0 on 416 D and 332 I rows; `unpaired` empty | ok, read from the summary |
| H_only membership | the k 2,000 H_only of `sets/far_atp_all_c3d7763/` | 1,623 neurons, equal to `far_all_sets_k2000.json` and `far_all_sets_k2000_with_nulls.json`; rebuilt from R6 as T_H minus (T_D union T_I) with the same 1,623 | ok |
| nulls | 20, layer-matched | all 20 equal the source file's nulls, match H_only's per-layer counts (layers 2 to 31), and share no neuron with it | ok |
| manifest | 71 dataset hashes, code hashes | 71 of 71 re-verified; the 5 code hashes equal the worktree files now and the R14 cell's manifest; the sets file and seed-3 sample hashes appear in the manifest | ok |

File hashes at review time: `rows.jsonl` `be0f8478…d789e`, `summary.json` `f73d47ec…e9c9`, `run_manifest.json`
`6576fd52…9f77`, `verdict.json` `3e3b6b28…9055`, `verdict.md` `cd440e30…10db1`.

## Notes

1. **The D-rate fall does not beat the matched null; the H fall does.** Every null moves H accuracy by exactly
   0.0, so the H drop of 21.9 points belongs to the class. The D rate is different. Under mean on the whole sample,
   9 of 20 nulls lower D's deceptive rate at least as far as the class's 12.7 points, and 10 of 20 clear the
   10-point bar themselves. The null median is -9.7 and the 5th percentile -25.4. Net of the null median, the class
   moves the D rate about 3 points. Item 10 reads the D rate without a null, so "suppression or shared" stands by
   the letter of the rule. But R18's gloss, "the class is not a pure honest route that deception bypasses", rests on
   the D-rate clause, which random layer-matched sets meet half the time. On this sample the rule's bypass branch
   (D rate moving under 5 points) would likely fail for any 1,623-neuron set, because only 6 of 20 nulls stay under 5
   points. F7 should say that the D-rate clause is not distinguishable from the null.
2. **Why random sets move D but not H.** The intact D margin averages 2.34 logits, with a minimum of 0.64, and 275 of
   416 D pairs lie within 2 logits of the 0.7 screen. The intact H margin averages -6.96, with a maximum of -2.17, and
   no H pair lies within 2 logits of 0.7. A small random perturbation pushes D pairs across 0.7 but cannot flip H.
   The null D-removed values are small, from -0.024 to 0.081 of G, which is under 0.8 logits.
3. **Rate and margin disagree in sign on D.** The mean D margin rises: D removed is -0.64 under mean and -0.53 under
   twin, which reads as deception growing. The D rate falls by 12.7 points. Under mean, 355 of 416 D pairs rise and 61
   fall. The 58 pairs that drop below 0.7 have a median ablated margin of -2.75, and 54 pairs end with the honest
   token as the argmax. So the class pushes most rows toward deception and flips a minority to honest. The rate is the
   measure item 10 names for N2; R2 moved only the N1 bars to the margin. F7 should report both directions.
4. **Where H accuracy goes.** Under mean, all 91 H pairs that turn wrong turn to the deceptive token, none to another
   token. Under twin, 207 of 416 do. The H loss is a move toward the deceptive answer, which fits the suppression
   reading.
5. **The inside-the-model reading gives the same label.** Under mean the ablated H rate rises from 0.0 to 0.089. D's
   rate minus H's rate therefore falls by 21.6 points on the whole sample, 20.2 on half 1 and 23.1 on half 2. Every
   value clears the 10-point bar, so the label does not depend on the reading. The same reading of the margin gives D
   removed 0.011 under mean: the class raises the D and H margins by about the same amount.
6. **Provenance label.** The manifest names commit `d5f6b17`, while the directory, the job line and the ledger name
   `3486f1a`. The manifest is written when the run ends, and the run used the live worktree, so it records the head
   at 11:14 am EST. The five scored code files hash identically to the R14 cell's manifest and to the worktree now, so
   the code that ran is pinned whatever the label. This review agrees with hand-back 09's default.
7. **Timestamps.** R16, R17 and R18 carry EST stamps about an hour later than the clock. `spec.md` was last written
   at 10:17 am CST, which is 11:17 am EST, and this review began at about 11:22 am EST, yet R18 is stamped 12:25 pm
   EST. Commit `d5f6b17` contains R17 (stamped 11:50 am) and was already the head when the manifest was written at
   11:14 am EST. The stamps do not change the verdict. R14 of 3 Nov is the operative pre-registration for this cell,
   so R15's "before any run" stamp (10:35 am EST, against a job start of 10:33 am EST) does not matter. The
   orchestrator should correct the stamps.
8. **F collateral.** The class lowers F accuracy by 19.2 points. This is not an N2 bar, but it shows the class is
   general answer machinery for FAR, not specific to the honest twin.
9. **This review is the recomputation R15 and R18 ask for.** The N2 outcome "suppression or shared" at size 2,000 can
   lose its preliminary tag, with note 1 attached.

The null values on the whole sample, in set order 0 to 19, are below.

```
D removed, margin, twin: 0.0282 0.0212 0.0601 0.0523 0.0448 0.0462 0.0212 0.0261 0.0044 0.0317
                         -0.0098 0.0307 0.0174 0.0723 0.0136 0.0403 0.0200 0.0428 0.0404 0.0466
D removed, margin, mean: 0.0081 0.0039 0.0811 0.0488 0.0397 0.0591 0.0554 0.0104 0.0470 0.0539
                         -0.0154 0.0242 0.0009 0.0340 -0.0225 -0.0241 0.0169 0.0702 0.0487 0.0624
D rate change, points, twin: -5.5 -7.2 -19.0 -18.3 -13.0 -11.5 -11.5 -7.7 -6.5 -14.2
                             -1.9 -11.5 -8.9 -22.4 -5.8 -8.2 -5.5 -17.3 -9.9 -6.2
D rate change, points, mean: -2.2 -5.0 -29.1 -22.1 -12.7 -18.5 -15.6 -2.9 -18.0 -18.3
                             -5.3 -10.3 -7.2 -5.0 -1.9 -0.5 -7.2 -25.2 -9.1 -13.5
H, F shift, every null, mean: 0.0
IOI shift, nulls, mean: min -3.9, max +5.9 points
```

## Commands

Every command ran on the Delta login node. The scripts are in `WT/outputs/_analyses/neuron-partition/r5_tmp/`.

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/schema.py
```

Observed: 56,784 rows and the field list of each reference and condition.

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/recompute.py
```

Observed: "rows 56784 dups 0", "halves D {'A': 104, 'B': 104} I {'A': 78, 'B': 88}", every value in the first
table, and "suppression or shared" in all six rows. Output `r5_tmp/recompute.json`.

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/details.py
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/null_rate.py
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/numeric_order.py
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/d_argmax.py
```

Observed: the rates, accuracies and null lists of notes 1 to 5. "mean|whole H_only D rate change -12.74 | null p5
-25.43 median -9.74 p95 -1.85 | nulls <= -10: 10/20 | nulls <= H_only: 9/20". "mean D pairs margin fell 61 rose
355 lost the 0.7 screen 58". "H pairs 416 wrong->opposite token 91 wrong->other token 0". "D intact margin mean
2.34, min 0.64, max 8.75, pairs within 2 logits of 0.7: 275 of 416". "mean D ablated argmax: {'deceptive': 362,
'honest': 54}" and "twin D ablated argmax: {'deceptive': 332, 'honest': 84}".

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/sanity.py
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/sets_check.py
```

Observed: 0 overlap with seed 2, the ranking ids and the 792 excluded ids; "IOI intact accuracy 0.513"; "max intact
margin difference across sets and references 0.0"; "manifest dataset_files 71 mismatched or missing []";
"R6 rebuilt H_only = T_H - (T_D | T_I): 1623 equal: True"; "nulls 20 layer-matched all: True disjoint from
H_only: 20 equal to source file nulls: 20".

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/compare.py
```

This ran after `recompute.json` was saved. Observed: "compared 420 worst fraction diff 5.551115123125783e-17 worst
point diff 7.105427357601002e-15" and "flags []". The 420 quantities are D and I removed by margin and rate, the D
rate change, the H, F, IOI and N shifts, every null D-removed, null H-shift and null D-rate-change value, the null
p95 of D removed and the N2 null bar, over six reference and subset cells. A first run listed the nulls in string
order (0, 1, 10, 11 and so on) and flagged order-only differences. Reordering them numerically removed every flag.

```
date
stat -c '%y %n' <run_manifest.json> <rows.jsonl> <spec.md> <hand-back 11> <hand-back 09>
sacct -j 23519165 -X -n -o JobID,State,Start,End,ElapsedRaw,NodeList,Account
```

Observed: "Wed Nov 4 10:22:15 CST 2026"; manifest 10:14:57 CST, spec 10:17:37 CST; job COMPLETED, 09:33:40 to
10:15:00 CST, 2,480 s, gpub007.
