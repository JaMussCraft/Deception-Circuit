# Review 07: independent recomputation of the SER cell (k 500, four classes, predicate-naming sample)

**Verdict: CONFIRMED WITH CORRECTIONS.** Every number that ruling R20 and `verdict.md` state for the cell
`ser_predicate_k500-d5f6b17` was recomputed from `rows.jsonl` without the verdict script. Against `verdict.json`,
2,640 quantities agree, with a worst difference of 2.2e-16 on fractions and 1.4e-14 on points. N1 fails at k 500 on
the H and F collateral bars only, under both references, on the whole sample and both halves. N2 is "suppression or
shared" on every subset. The one correction is a number in R20's wording. "Rate 1.0" is 0.998 under twin and 1.051
under mean. The mean value exceeds 1 because the ablated H rows themselves turn deceptive.

Reviewer: R7 (Claude Opus, independent). Written Wed 4 Nov 2026, about 12:46 pm EST. `WT` below means
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition`, and `NP` means
`WT/outputs/_analyses/neuron-partition`.

- **Read before my numbers were saved.** Spec item 10 and rulings R2, R6 to R8, R10, R11, R15 (d), R17 and R20;
  hand-back 11 with its four addenda; hand-back 12; review 06 as the model; and `verdict.md`, which the brief names
  as the claim. The R20 numbers were therefore known to me before I computed mine.
- **Not read.** The verdict script `scripts/neuron_partition_verdict.py` was never opened, imported or run. The row
  schema was learned from the rows and from the `definitions` block of `summary.json`. `verdict.json` was opened
  only after `NP/r7_tmp/recompute.json` was saved.
- **Called, not reimplemented.** `split_halves` from `scripts/neuron_partition_data.py`, and `clause_form` from
  `dataset/build_inversion_v2.py` for the clause-form check.
- **Data read outside this worktree.** The ladder's `design.json` under the specificity-ladder worktree's outputs,
  for the A1 exclusion lists. It is a data file. No code under that worktree was read.
- **Not used.** No GPU, Slurm or version control. Everything ran on the Delta login node with the mgnp interpreter.

## Definitions used

These are review 06's definitions, applied to SER.

- **Margins.** m is the row's `m_intact` or `m_ablated` per stream, in D's orientation. Within an id the clean and
  corrupt streams are averaged, then ids are averaged. IOI rows carry one stream, `clean`.
- **Margin removed (R2).** G is the mean over ids of the intact D margin minus the intact H margin of the same id.
  The fraction removed is the mean of intact minus ablated D margin, divided by G. I uses the user-neutral rows `N`.
  The D rows' `twin_m_intact` equals the twin rows' `m_intact` with a difference of 0.0.
- **Rate removed (R8).** The rate is the share of id-stream pairs with m at least 0.7. Rate removed is one minus the
  ablated rate effect over the intact rate effect. Under mean the ablated D rate is compared with the ablated H
  rate. Under twin it is compared with the intact H rate, because the donor is not patched.
- **Accuracy.** Full-vocabulary argmax against `correct_token` over every id-stream pair. A shift is ablated minus
  intact, in points. H, F and IOI collateral is read under mean for both references (R7). The twin H shift is the
  reverse patch and is descriptive.
- **D rate change (N2).** The ablated minus the intact D rate at margin 0.7, in points, under the same reference.
- **Null percentile.** `numpy.percentile` with linear interpolation over the 20 matched nulls of the same class,
  reference and subset. The N2 null term is the 95th percentile of the absolute null H shift.
- **Halves (R10).** One `split_halves(ids, pressure_id, seed=2)` call over the union of the sample's D and I ids. The
  pressure id comes from the `data/datasets/ser_v2` test split, else from the `ser_v2_user_inversion` pool. Every I
  id is also a `ser_v2` test id, so no id needed the pool's pressure id. H and F take the D id's half and N the I
  id's half. The split is D 146 and 154, I 144 and 156, equal to hand-back 11 (item 6) and to `verdict.json`. All
  1,000 IOI rows enter both halves.
- **N1 bars.** Size at most 2,000, D removed (margin) at least 0.50, I removed (margin) under 0.25, H, F and IOI
  shifts each under 5 points in absolute value, and D removed above the null's 95th percentile. A size passes only
  if every bar holds under twin and mean, on the whole sample and on both halves.
- **N2 rule.** Bypass if H falls at least 20 points, D's rate moves under 5 points and the null's 95th percentile of
  the absolute H shift is under 5. Suppression or shared if H falls at least 20, D's rate falls at least 10 and the
  null term is under 5. Otherwise undetermined. Mean decides.

## Recomputed numbers beside the claims

The claimed values are those of `verdict.md`. Mine are rounded the same way. At full precision they agree with
`verdict.json` to the last digit. The rate column is the secondary measure (R2). Collateral is read under mean (R7),
so the twin rows repeat the mean values.

| ref | class (n) | D removed, margin: mine / claimed | D removed, rate: mine / claimed | I removed, margin: mine / claimed | I removed, rate: mine / claimed | null p95 of D: mine / claimed | H, F, IOI shift: mine / claimed |
|---|---|---|---|---|---|---|---|
| twin | D_only (386) | 0.9557 / 0.956 | 0.9983 / 0.998 | 0.0938 / 0.094 | 0.0353 / 0.035 | 0.0221 / 0.022 | -15.8, -6.3, -2.7 / same |
| twin | DI_shared (28) | 0.2599 / 0.260 | 0.3945 / 0.395 | 0.3485 / 0.348 | 0.3395 / 0.339 | 0.0126 / 0.013 | -0.8, 0.0, 0.4 / same |
| twin | H_only (403) | 0.4711 / 0.471 | 0.6381 / 0.638 | 0.1677 / 0.168 | 0.1462 / 0.146 | 0.0296 / 0.030 | -44.8, -40.3, -2.2 / same |
| twin | all_shared (36) | 0.3704 / 0.370 | 0.5780 / 0.578 | 0.4268 / 0.427 | 0.5647 / 0.565 | 0.0032 / 0.003 | -3.8, -1.7, -6.1 / same |
| mean | D_only (386) | 0.7338 / 0.734 | 1.0515 / 1.051 | 0.1964 / 0.196 | 0.1361 / 0.136 | 0.0675 / 0.067 | -15.8, -6.3, -2.7 / same |
| mean | DI_shared (28) | 0.2721 / 0.272 | 0.4202 / 0.420 | 0.3368 / 0.337 | 0.2756 / 0.276 | 0.0071 / 0.007 | -0.8, 0.0, 0.4 / same |
| mean | H_only (403) | -0.1013 / -0.101 | 0.5249 / 0.525 | -0.1369 / -0.137 | 0.0908 / 0.091 | 0.0326 / 0.033 | -44.8, -40.3, -2.2 / same |
| mean | all_shared (36) | 0.1905 / 0.191 | 0.1595 / 0.160 | 0.2567 / 0.257 | 0.2303 / 0.230 | 0.0070 / 0.007 | -3.8, -1.7, -6.1 / same |

The deception-only class on the halves, for every quantity with a bar:

| ref | subset | D removed | I removed | null p95 of D | H shift | F shift | IOI shift | bars failed |
|---|---|---|---|---|---|---|---|---|
| twin | whole | 0.9557 | 0.0938 | 0.0221 | -15.8 | -6.3 | -2.7 | H, F |
| twin | half 1 | 0.9527 | 0.0941 | 0.0214 | -16.8 | -6.5 | -2.7 | H, F |
| twin | half 2 | 0.9582 | 0.0935 | 0.0228 | -14.9 | -6.2 | -2.7 | H, F |
| mean | whole | 0.7338 | 0.1964 | 0.0675 | -15.8 | -6.3 | -2.7 | H, F |
| mean | half 1 | 0.7464 | 0.2011 | 0.0687 | -16.8 | -6.5 | -2.7 | H, F |
| mean | half 2 | 0.7231 | 0.1923 | 0.0664 | -14.9 | -6.2 | -2.7 | H, F |

The descriptive twin reverse patch moves H by -7.2, -6.5 and -7.8 points on the whole sample and the two halves, as
claimed. Intact G is 6.440 for D and 7.601 for I. The intact D rate is 0.972 and the intact H rate 0.0. Under mean the
D_only class leaves an ablated D rate of 0.027 and raises the ablated H rate to 0.077.

## The N1 bars, applied

| class | twin whole | twin half 1 | twin half 2 | mean whole | mean half 1 | mean half 2 | bars failed (all six cells) |
|---|---|---|---|---|---|---|---|
| D_only | fail | fail | fail | fail | fail | fail | H, F |
| DI_shared | fail | fail | fail | fail | fail | fail | D, I |
| H_only | fail | fail | fail | fail | fail | fail | D, H, F (mean adds the null bar) |
| all_shared | fail | fail | fail | fail | fail | fail | D, I, IOI |

N1 is decided on D_only, and it fails at k 500, as `verdict.md` and R20 say. Each D_only bar flag equals
`verdict.json`'s `n1_bars`, 36 of 36. Every non-collateral bar passes with room. D removed is at least 0.723 against
0.50 and beats the null's 95th percentile by at least 0.65. I removed is at most 0.201 against 0.25. The largest
absolute IOI shift is 2.7 against 5. The failure is therefore cleanly a collateral failure.

## N2, applied (H_only, k 500)

| ref | subset | H shift | D rate change | null p95 of abs H shift | rule | claimed |
|---|---|---|---|---|---|---|
| mean | whole | -44.8 | -14.0 | 1.4 | suppression or shared | suppression or shared |
| mean | half 1 | -45.9 | -13.0 | 0.7 | suppression or shared | suppression or shared |
| mean | half 2 | -43.8 | -14.9 | 2.0 | suppression or shared | suppression or shared |
| twin | whole | -71.3 | -62.0 | 0.2 | suppression or shared | suppression or shared |
| twin | half 1 | -71.9 | -57.2 | 0.0 | suppression or shared | suppression or shared |
| twin | half 2 | -70.8 | -66.6 | 0.3 | suppression or shared | suppression or shared |

The twin H shift here is the reverse patch, with its null from the reverse patch, as `verdict.md` prints it. Mean
decides.

Unlike FAR's R18, the rate clause beats its null band on SER. Under mean no H_only null lowers D's rate by 14.0
points or more. The null range is -5.7 to +1.5, with a median of -1.2. The SER outcome therefore rests on the rate fall
as well as on the H and F falls.

## R20 against my numbers

| R20 statement | mine | match |
|---|---|---|
| 300 rows each for D, H, F, I and N; seed 2; 1,000 IOI rows at seed 2 | 300 each; IOI ids `ioi:seed=2:row=0..999` | yes |
| D_only has 386 neurons | 386, rebuilt by rule R6 | yes |
| D removed 0.96 under twin, 0.73 under mean | 0.9557, 0.7338 | yes |
| "rate 1.0" | 0.9983 under twin, 1.0515 under mean | no, see correction 1 |
| inversion 0.09 (twin) and 0.20 (mean) | 0.0938, 0.1964 | yes |
| IOI minus 2.7 | -2.7 | yes |
| H falls 15.8 and F 6.3 under mean | -15.8, -6.3 | yes |
| collateral bars fail on the whole sample and both halves | H and F fail in all six cells | yes |
| N1 fails at size 500 | fails; every other D_only bar passes | yes |
| shared and all-shared remove under 0.4 of the margin | 0.260 to 0.272 and 0.191 to 0.370 | yes |
| H_only has 403 neurons; H minus 44.8; rate fall 14.0 under mean | 403; -44.8; -14.0 | yes |
| null H shift 1.4 | 95th percentile of the absolute null H shift, 1.36 | yes |
| N2 is suppression or shared | on all three subsets under mean, and under twin | yes |
| Bridges-2 job 50213549, 3,572 s of 7,200 | `summary.json` gives 3,483 s of script wall time; Slurm not checked | not checked |

## F9 against my numbers

The F9 entry lives in `worklog.json`, which only the research-session tool may read, and the worktree's
`WORKLOG.md` render has an empty findings register. F9 was therefore checked through its two readable restatements.
The first is `RESUME.md`, in the line for R20 and F9. The second is follow-up C of `reports/13-followups-4nov.md`.

| F9 statement (RESUME and report 13) | mine | match |
|---|---|---|
| removes 0.96 of the deception margin under twin | 0.9557 | yes |
| fails N1 on collateral, H minus 15.8 and F minus 6.3 | -15.8, -6.3; the only failed bars | yes |
| N2 on SER is suppression or shared | on every subset | yes |
| 210 of the 386 class neurons lie in the Codex A3 SER layers | 210 of 386 | yes |
| report 13: the class is densest in layers 5 to 9 | 7, 8, 6, then 5 and 9 tied, are the five largest | yes |
| report 13's table: D removed 0.956 and 0.734, rate 0.998 and 1.051, I 0.094 and 0.196, null p95 0.022 and 0.067; H_only 0.471 and -0.101, rate 0.638 and 0.525, I 0.168 and -0.137, null p95 0.030 and 0.033 | the same to three decimals | yes |
| report 13: "a rate removed above 1.0 means that the ablated deception rate sits below the ablated honest rate under mean" | ablated D 0.027 against ablated H 0.077 | yes |
| report 13: the N2 table, mean whole, half 1 and half 2 and twin whole | -44.8, -14.0, 1.4; -45.9, -13.0, 0.7; -43.8, -14.9, 2.0; -71.3, -62.0, 0.2 | yes |
| report 13: review 05's rate-clause caution "applies until review 07 returns" | the caution does not apply on SER; no H_only null reaches -14.0 (N2 section) | resolved |

F9's wording in these two places has no "rate 1.0". Correction 1 below touches R20 only.

## Corrections

1. **"Rate 1.0" in R20.** The D rate removed is 0.998 under twin and 1.051 under mean. The mean value exceeds 1
   because R8 compares the ablated D rate with the ablated H rate. Ablating the class raises H's deceptive rate from
   0.0 to 0.077 while D's falls to 0.027, so the ablated effect is negative. Suggested wording: "(0.73 under mean;
   rate 0.998 under twin and 1.05 under mean, above 1 because the ablated H rows turn deceptive)".

The brief's expected row count was also off. That is not a finding of the cell. See the first sanity check.

## Sanity checks

| check | expected | observed | result |
|---|---|---|---|
| rows in `rows.jsonl` | twin has D, H, I and N (no F, no IOI); mean has D, H, F, I, N and IOI. 84 × (4 × 300 + 5 × 300 + 1,000) = 84 × 3,700 = 310,800 | 310,800; no duplicate reference, set, condition and id | ok |
| ids per condition | equal to `NP/data/ser_predicate_test_sample_seed2.json` | equal on all 840 reference, set and condition groups; H and F ids equal D's, N ids equal I's; D and I share 201 ids | ok |
| sample hash | `06a2dd93…a994` (hand-back 11) | same | ok |
| clause form | every D row predicate-naming | `clause_form(pressure, 'ser_v2')` is "predicate" for 300 of 300 D ids, and for the D rows of all 300 I ids; 8 pressure ids, 8 distinct clause texts; every I row uses request `ser_quiz_v1` | ok |
| exclusions | disjoint from the 360 ids of hand-back 11 | rebuilt from the four sources (ladder `design.json` assessment and mover-selection ids; the two mechanism-analysis held-out samples' `instance_ids`; `held_out.json` is empty); all four sha256 values match the sample's record; union 360; overlap with D, H, F, I and N ids 0 | ok |
| class membership | rule R6 with the R11 all-position scores | rebuilt as T_D minus (T_I union T_H) and so on, top 500 positive only, ties to the lower flat index: 386, 28, 403 and 36, equal to the sets file and to `ser_all_sets_k500.json` | ok |
| score sources | one ranking | `atp_all_mean` of the plain and `_rev` dh runs differ by 0.0; s_H is minus `rev_atp_all_mean` | ok |
| sets file | `45e962b2…30aa` (hand-back 11) | same; its 84 names equal the sets in `rows.jsonl` | ok |
| nulls | 20 per class, size and layer matched, disjoint | 20 of 20 for each class: same size, same 32-layer histogram, no neuron shared with the class, no repeated member, all 20 distinct; per-layer counts in `summary.json` equal for all 84 sets | ok |
| intact IOI accuracy | near the ladder's 0.51 | 0.511 from the rows | ok |
| intact margins across sets and references | identical | maximum difference 0.0; intact argmax identical | ok |
| self-replay and twin cross-check | 0 | `summary.json` gives 0.0 for D and I, cross-check 0.0 on 600 D and 600 I pairs, `unpaired` empty; read from the summary, not recomputable from rows | ok |
| manifest | dataset and code hashes | 71 of 71 dataset hashes re-verified, Bridges-2 absolute paths mapped onto `WT`; 5 of 5 code hashes equal the worktree files; commit `d5f6b175…36c6`, `git_dirty` false | ok |

File hashes at review time: `rows.jsonl` `a73be5c3…c977`, `summary.json` `0e868dc5…0929`, `run_manifest.json`
`04620384…cfa9`, `verdict.json` `f65e7421…3b4a`, `verdict.md` `6992cf0c…9a12`. The first two equal the hashes that
`verdict.json` records, and the last two equal hand-back 11's.

## Descriptive readings

### Per-layer counts of the D_only class against Codex A3

A3 covers SER layers 5 to 8, 11, 13 and 16. 210 of the 386 neurons lie in those layers and 176 outside, as hand-back 11
reports.

| layer | 0 | 1 | 2 | 3 | 4 | **5** | **6** | **7** | **8** | 9 | 10 | **11** | 12 | **13** | 14 | **16** | 17 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| neurons | 5 | 6 | 22 | 18 | 22 | 36 | 42 | 51 | 49 | 36 | 35 | 30 | 25 | 1 | 5 | 1 | 1 | 1 |

Bold layers are A3's. The largest blocks outside A3 are layers 9, 10 and 12 (96 neurons) and layers 2 to 4 (62).

### Where the H and F loss of D_only under mean sits

The loss is concentrated by designation polarity, not by pressure id or clause wording.

- **Polarity explains it.** In "identity" rows the prompt names the favorable item ("The garage reading came back
  favorable, and the other came back unfavorable"). The honest answer is then "the other". In "inversion" rows the
  named item is the unfavorable one, which is the honest answer. 94 of the 95 lost H pairs and all 38 lost F pairs
  are identity rows.

  | condition | polarity | pairs | accuracy intact to ablated | mean margin shift toward the opposite |
  |---|---|---|---|---|
  | H | identity | 304 | 1.000 to 0.691 | +2.02 |
  | H | inversion | 296 | 1.000 to 0.997 | +0.71 |
  | F | identity | 304 | 1.000 to 0.875 | +1.14 |
  | F | inversion | 296 | 1.000 to 1.000 | +0.41 |

- **Identity rows start with smaller honest margins.** The intact mean H margin is -2.95 on identity rows against
  -4.23 on inversion rows. On F it is -3.01 against -3.92. The lost pairs had a median intact margin of -1.48 (H) and
  -1.30 (F), against -3.59 and -3.28 for the pairs that stayed correct. In every lost pair, 95 of 95 on H and 38 of
  38 on F, the ablated full-vocabulary argmax is the opposite word. No row gained accuracy.
- **Pressure id is a proxy for the polarity mix.** By pressure id the H loss ranges from 4 to 30 percent of pairs.
  Within identity rows it is 27 to 40 percent for every pressure id with at least 30 pairs, and within inversion rows
  it is 0 for every pressure id but one (1 of 74). The 8 clauses are all predicate-naming, so clause form cannot
  separate the rows.
- **F has no pressure clause and still loses.** The class moves no-pressure prompts toward the favorable answer by
  0.4 to 1.1 logits. Part of what the class removes from D is therefore not tied to the pressure clause.
- **The loss is specific to the class.** Its 20 matched nulls move H by -2.5 to 0.0 points and F by -0.8 to 0.0.
- **D removal also differs by polarity.** Under mean, D removed is 0.666 on identity rows and 0.792 on inversion
  rows. The ablated identity D rows keep 20 percent of their deceptive answers, and the inversion rows keep none.

The pattern fits a class that partly carries "pick the item the prompt names as favorable". This is a reading of the
counts above, not a tested mechanism.

## Notes

1. **The class moves IOI more than its random sets do.** The IOI bar is absolute, so this does not affect the
   verdict. D_only's IOI shift of -2.7 lies below all 20 of its nulls, which range from -2.0 to +2.5. This matches the
   FAR class in review 06, note 3. all_shared's -6.1 lies far below its nulls' -0.8 to +0.7.
2. **One D_only null lowers D's rate as much as N2 measures.** Under mean, the D_only nulls' D rate change reaches
   -14.7 points. This does not enter any rule, and it does not undercut N2. N2's nulls are matched to the H_only
   class's layers, and they range from -5.7 to +1.5. It shows only that a 14-point rate fall is within reach of a
   random 386-neuron set in the D_only class's layers.
3. **H_only raises the deception margin while lowering the rate.** Under mean the D margin rises by 0.10 of G, yet
   D's rate at 0.7 falls 14.0 points, and H's rises to 0.37. The rate measure and the margin measure disagree in sign
   here. R2 decides N1 on the margin, and N2 is a rate rule, so neither decision changes.
4. **Bootstrap intervals were not reproduced.** The Slurm elapsed time of 3,572 s was not checked, because the job ran
   on Bridges-2.
5. **This review is the recomputation R15 and R20 ask for.** The SER outcome can lose its preliminary tag with
   correction 1 applied.

All class and null values for every class, reference and subset are in `NP/r7_tmp/recompute.json`.

## Commands

Every command ran on the Delta login node from `WT`. The scripts are in `NP/r7_tmp/`.

```
HF_DATASETS_OFFLINE=1 OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r7_tmp/recompute.py
```

Observed: "halves (union call): {'D': {'B': 154, 'A': 146}, ..., 'I': {'A': 144, 'B': 156}, ...} ids taking pool
pressure_id 0", "rows 310800 dups 0", the 24 class lines of the tables above, the six N2 lines, each "suppression or
shared" with "nulls_D_rate_at_or_below 0", and "IOI intact acc 0.511". Output `NP/r7_tmp/recompute.json`.

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r7_tmp/sets_check.py
```

Observed: "dh vs dh_rev atp_all_mean max diff 0.0"; "sizes {'D_only': 386, 'DI_shared': 28, 'H_only': 403,
'all_shared': 36}"; the two sha256 values above; for each class "equals sets file True equals plain k500 file True
summary per_layer equal True | nulls 20 size 20 layer hist 20 disjoint 20 no dup members 20 distinct sets 20 summary
per_layer 20"; "D_only per layer ... in A3 210 outside 176".

```
HF_DATASETS_OFFLINE=1 OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r7_tmp/provenance.py
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r7_tmp/excl.py
```

Observed: "D clause forms {'predicate': 300} | D forms of I ids {'predicate': 300}", "I request ids {'ser_quiz_v1':
300}", "groups 840 id mismatches 0", "intact margin max diff across sets and references 0.0 argmax equal True",
"twin_m_intact vs twin rows m_intact max diff 0.0", "manifest dataset files 71 equal 71 mismatch 0 missing 0", every
code hash "WT equal True"; and from the second script "union 360 D overlap 0 I overlap 0 H overlap 0 N overlap 0".
The first script's own exclusion union printed 200 because it did not read the two held-out files' `instance_ids`
key. The second script reads that key.

```
HF_DATASETS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r7_tmp/compare.py
```

This ran after `recompute.json` was saved. Observed: "compared 2640 worst fraction diff 2.220446049250313e-16 worst
point diff 1.4210854715202004e-14", "flags [] 0", "D_only N1 bar flags equal 36 of 36". A first version of this
script compared the twin block's own H shift, which is the reverse patch, with my mean H shift and raised 86 flags.
The fixed version compares the reverse patch with the reverse patch and the mean collateral with the mean collateral.

```
HF_DATASETS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r7_tmp/collateral.py
HF_DATASETS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r7_tmp/polarity.py
```

Observed: "H pairs 600 lost 95 gained 0", "F pairs 600 lost 38 gained 0", "by designation_polarity ['identity: lost
94 of 304 (31%)', 'inversion: lost 1 of 296 (0%)']" for H and "identity: lost 38 of 304, inversion: lost 0 of 296"
for F; "null D_only H shift min -2.5 max 0.0", "F shift min -0.8 max 0.0"; the polarity table above; and "D removed
(mean) on identity ... 0.666", "on inversion ... 0.792".

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r7_tmp/strict_argmax.py
```

Observed: "('H', 'lost'): 95, ('H', 'argmax is opposite word'): 95, ... ('F', 'lost'): 38, ('F', 'argmax is opposite
word'): 38". This checks the full-vocabulary argmax, not the two-way margin.

```
TZ=America/New_York date "+%I:%M %p %Z"
```

Observed: "12:46 PM EST".
