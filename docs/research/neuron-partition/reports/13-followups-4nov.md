# Report 13: Results of the four pre-registered follow-ups, Wed 4 Nov 2026

Report writer W11, Claude Sonnet 5.5. Written Wed 4 Nov 2026, 12:47 PM EST, as the companion to `05-first-report.md`. Bare file names are in `reports/`. The path `../` is the direction. The definitions of the N1 and N2 bars, the twin and mean references and the ladder margin ratio are in the method and pass-bar sections of `05-first-report.md` and are not repeated here.

## Headline

1. The finer ladder passes N1 at every size from 250 to 750 on the seed-3 sample, so the size-500 pass is not a tuned point. Review 06 confirmed it by independent recomputation, with wording corrections.
2. N2 on FAR reads suppression or shared at size 2,000 on fresh data, not bypass. Review 05 confirmed it and qualified that the deceptive-rate clause lies inside the null band, so only the honest-accuracy fall beats the nulls.
3. On SER at size 500 the deception-only class removes the deception effect but fails N1 on honest and no-pressure collateral, and N2 on SER also reads suppression or shared. Both SER results are pending independent recomputation.
4. The one-neuron check shows that the attribution ranking predicts the sign and the order of single-neuron interchange effects at the top of the ranking, which is pending independent recomputation.
5. The first report's two decisions stand: the original ladder stays failed under its frozen bars, and the size-500 class stays confirmed on fresh data.

## What was run

All four follow-ups used the fixed all-position ranking and rule R6, with nothing re-ranked, as ruling R15 in `../spec.md` fixes. SER needed the ranking cell first, so five jobs ran. The jobs used 5.75 reserved GPU-hours after the user raised the cap in R16.

| Follow-up | Job id | Cluster and node | Reserved | Actual | State | Commit in job name | Commit in manifest | Output directory |
|---|---|---|---|---|---|---|---|---|
| N2 on fresh data, honest-only size 2,000 | 23519165 | Delta, A40, gpub007 | 60 min | 2,480 s | COMPLETED | 3486f1a | d5f6b17 | `outputs/_analyses/neuron-partition/ablation/confirm_h_only_k2000-3486f1a` |
| Finer ladder, sizes 250 to 750 | 50212883 | Bridges-2, H100 | 90 min | 3,041 s | COMPLETED | 92fc6fb | d5f6b17 | `outputs/_analyses/neuron-partition/ablation/ladder-92fc6fb` |
| One-neuron check | 23520193 | Delta, H200, gpub059 | 45 min | 1,447 s | COMPLETED | 92fc6fb | 800c903 | `outputs/_analyses/neuron-partition/ablation/one_neuron-92fc6fb` |
| SER ranking | 23520107 | Delta, A40, gpub090 | 30 min | 360 s | COMPLETED | a41752a | d5f6b17 | `outputs/_analyses/neuron-partition/attribution/ser_v2_dh_train+validation_predicate_a41752a` |
| SER ablation, size 500 | 50213549 | Bridges-2, H100, w008 | 120 min | 3,572 s | COMPLETED | d5f6b17 | d5f6b17 | `outputs/_analyses/neuron-partition/ablation/ser_predicate_k500-d5f6b17` |

Row counts match the expected counts in every cell, and self-replay error is 0.0 where a cell scores it, as `09-runner-handback.md` and `12-runner2-handback.md` record.

| Cell | Rows observed and expected | Intact IOI accuracy against the reference of 0.51 |
|---|---|---|
| N2 on fresh data | 56,784 and 56,784 | not stated in the hand-back |
| Finer ladder | 227,136 and 227,136 | 0.511 |
| One-neuron check | 24,000 and 24,000 | not applicable, IOI was off |
| SER ablation | 310,800 and 310,800 | 0.511 |

The SER ranking cell passed row-count and tensor checks in all ten directories.

## Follow-up A: N2 on fresh data, FAR, honest-only class at size 2,000

**Review 05: CONFIRMED, with one qualification.** An independent recomputation from the rows matches every number of ruling R18, with 420 quantities and a worst difference of 7e-15 on points, in `../reviews/05-n2-fresh-data-recompute.md`. Finding F7 is reviewed.

The cell ablates the 1,623-neuron honest-only class and its 20 nulls on the seed-3 sample of 208 D, H and F ids, with 1,000 fresh IOI rows. N2 is read under the mean reference by the item 10 rule.

| Reference | Subset | H shift, points | D deceptive-rate change, points | Null p95 of the absolute H shift | N2 verdict |
|---|---|---|---|---|---|
| mean | whole | -21.9 | -12.7 | 0.0 | suppression or shared |
| mean | half 1 | -21.6 | -10.6 | 0.0 | suppression or shared |
| mean | half 2 | -22.1 | -14.9 | 0.0 | suppression or shared |
| twin | whole | -49.8 | -19.5 | 0.0 | suppression or shared |

| Quantity, whole sample | Mean | Twin |
|---|---|---|
| D removed, margin | -0.639 | -0.528 |
| I removed, margin | -0.107 | -0.458 |
| F accuracy shift, points | -19.2 | -19.2 |
| IOI accuracy shift, points | -2.4 | -2.4 |

Ablating the honest-only class lowers honest accuracy by about 22 points and no-pressure accuracy by about 19 points. It also raises the deception margin, which is why D removed is negative. The class therefore behaves as task machinery that deception also uses, and it is not a route that deception goes around.

**What review 05 qualifies.** Under mean, 9 of the 20 matched nulls also lower D's deceptive rate by at least 12.7 points, and the null median is 9.7. The rate clause of the rule therefore sits inside the null band. The honest-accuracy fall beats every null, which move it by 0.0, so the shared reading rests on that fall, on the no-pressure fall and on the margin rise.

**For the first report.** Report 05 read N2 as undetermined at 2,000, because the seed-2 deceptive rate moved 5.2 points against a bar of under 5. On fresh data the same class reads suppression or shared, and neither sample reads bypass. N2 now has a confirmation cell, which the first report listed as not done. Decision R13 and decision R14 are unchanged, because N2 does not enter either.

## Follow-up B: the finer size ladder, FAR deception-only class at sizes 250 to 750

**Review 06: CONFIRMED WITH CORRECTIONS, wording only.** All 1,128 quantities match within 1e-16 and the N1 pass holds in all 24 cells, which are four sizes, two references and three subsets, in `../reviews/06-ladder-recompute.md`. Finding F8 is reviewed.

The sizes after set construction are 152, 243, 424 and 524 neurons. Each has 20 matched nulls and is scored on the seed-3 sample and the same 1,000-row IOI draw as the size-500 confirmation. Deceptive rate removed is 1.000 in every row. H and F shifts are 0.0 in every row, and the N1 verdict is pass on the whole sample and both halves in every row.

| Reference | k | Size | D removed, margin | I removed, margin | Null p95 of D removed | IOI shift, points |
|---|---|---|---|---|---|---|
| twin | 250 | 152 | 0.813 | 0.009 | 0.013 | -2.7 |
| twin | 375 | 243 | 0.822 | 0.058 | 0.021 | -3.2 |
| twin | 625 | 424 | 0.823 | 0.194 | 0.022 | -1.4 |
| twin | 750 | 524 | 0.821 | 0.217 | 0.035 | -0.9 |
| mean | 250 | 152 | 0.688 | 0.148 | 0.018 | -2.7 |
| mean | 375 | 243 | 0.728 | 0.126 | 0.033 | -3.2 |
| mean | 625 | 424 | 0.758 | 0.175 | 0.030 | -1.4 |
| mean | 750 | 524 | 0.777 | 0.169 | 0.066 | -0.9 |

Under twin the deception effect is flat and the inversion cost rises with size. Under mean the deception effect rises from 0.688 to 0.777 and the inversion cost has no trend, which is review 06's correction to the wording of R19. The tightest bar is inversion under twin at size 750, at 0.217 against 0.25. Size 750 is the largest size tested, so the ladder does not bound the class's size from above.

**For the first report.** Decision R13 stands, because the original ladder was scored on the seed-2 sample and failed its frozen bars. Decision R14 is strengthened as a characterisation but not as a second confirmation. The seed-3 sample and the IOI draw had already been scored for the size-500 class, as R15 disclosed. The smallest set of 152 neurons already removes 0.813 of the deception margin under twin with almost no inversion cost.

## Follow-up C: SER at size 500

**Pending independent recomputation.** Review 07 does not exist yet, so finding F9 is preliminary. The numbers are copied from the verdict file `outputs/_analyses/neuron-partition/verdict/ser_predicate_k500-d5f6b17/verdict.md`.

The SER sample holds 300 ids per condition at seed 2, with predicate-naming rows only and 1,000 IOI rows at seed 2, as R17 sets. The deception-only class has 386 neurons and is densest in layers 5 to 9. The rows below are the deception-only class and the honest-only class.

| Class | Reference | Size | D removed, margin | D removed, rate | I removed, margin | Null p95 of D removed | H shift | F shift | IOI shift | N1 bars |
|---|---|---|---|---|---|---|---|---|---|---|
| D_only | twin | 386 | 0.956 | 0.998 | 0.094 | 0.022 | -15.8 | -6.3 | -2.7 | fail |
| D_only | mean | 386 | 0.734 | 1.051 | 0.196 | 0.067 | -15.8 | -6.3 | -2.7 | fail |
| H_only | twin | 403 | 0.471 | 0.638 | 0.168 | 0.030 | -44.8 | -40.3 | -2.2 | fail |
| H_only | mean | 403 | -0.101 | 0.525 | -0.137 | 0.033 | -44.8 | -40.3 | -2.2 | fail |

A rate removed above 1.0 means that the ablated deception rate sits below the ablated honest rate under mean. The D-and-I shared class of 28 neurons and the all-shared class of 36 neurons each remove under 0.4 of the deception margin and fail N1 as well.

**N1 on SER reads fail.** The deception-only class meets the size, D, I, null and IOI bars. It fails the H bar at 15.8 points and the F bar at 6.3 points against bars of under 5, on the whole sample and on both halves under both references. The deception effect transfers from FAR to SER, but the class cannot be separated from honest answering at this size.

| Reference | Subset | H shift, points | D deceptive-rate change, points | Null p95 of the absolute H shift | N2 verdict |
|---|---|---|---|---|---|
| mean | whole | -44.8 | -14.0 | 1.4 | suppression or shared |
| mean | half 1 | -45.9 | -13.0 | 0.7 | suppression or shared |
| mean | half 2 | -43.8 | -14.9 | 2.0 | suppression or shared |
| twin | whole | -71.3 | -62.0 | 0.2 | suppression or shared |

**N2 on SER reads suppression or shared.** This matches FAR in follow-up A. Review 05's rate-clause qualification was not recomputed for SER, so the same caution applies until review 07 returns.

**Against the Codex A3 cell.** Of the 386 deception-only neurons, 210 lie in the A3 cell's SER layers, which are 5 to 8, 11, 13 and 16, as `11-w10-ser-prep-handback.md` and R17 record. A reading of this class as new therefore overlaps A3 for more than half of its neurons. All SER classes are split-half stable at every size, with the deception-only Jaccard at 0.774 against a ceiling of 0.815 at size 500, in `outputs/_analyses/neuron-partition/sets/ser_predicate_atp_all_a41752a/stability_summary_all.md`.

**For the first report.** The first report listed SER as not run, and it now has one size. SER was a bonus under START, and the FAR decisions do not depend on it. The SER result bounds how far the FAR finding generalises. It does not change R13 or R14.

## Follow-up D: the one-neuron interchange check

**Pending independent recomputation.** Review 08 does not exist yet, so finding F10 is preliminary. The numbers are copied from `outputs/_analyses/neuron-partition/verdict/one_neuron-92fc6fb/one_neuron_report.md`.

The check patches one neuron at a time from its neutral twin under the twin interchange, on the seed-2 D and H rows. It covers the top 20 neurons by the deception score and the top 20 by the honest score, which is 36 distinct neurons because 4 appear in both lists. It answers the second major of review 01 and has no pass bars.

| View | Set | Neurons | Sign agreement, D | Sign agreement, H | Spearman, deception score | Spearman, honest score |
|---|---|---|---|---|---|---|
| both streams | all groups | 40 | 40 of 40 | 39 of 40 | 0.929 | 0.998 |
| both streams | distinct neurons | 36 | 36 of 36 | 35 of 36 | 0.938 | 0.997 |
| clean stream | all groups | 40 | 40 of 40 | 39 of 40 | 0.931 | 0.997 |
| clean stream | distinct neurons | 36 | 36 of 36 | 35 of 36 | 0.940 | 0.995 |

The one honest-margin miss is a neuron whose honest score is about zero. The four duplicate groups agree exactly. No single neuron removes more than 0.05 of the deception margin, and the strongest single neurons sit in layers 8 to 19. The size-500 class is dense in layers 0 to 9, so its effect comes from many small early contributions and not from the largest single neurons.

**What this does and does not show.** The ranking is faithful at the top, in sign and in order. The check does not test neurons deep in the ranking, where most of each class lies. It also uses the twin reference only and has no IOI rows.

**For the first report.** The first report listed this check as not run. The result supports reading the ranked classes as carrying real single-neuron effects, and it does not change R13 or R14.

## Budget

The cap is 30 reserved GPU-hours after R16, and at most 3 concurrent GPU jobs still holds. There was no OpenRouter spend. The ledger is `ledger.json` in the direction directory.

| Quantity | Value |
|---|---|
| Reserved before this phase, GPU-hours | 15.8334 |
| Reserved in this phase, GPU-hours | 5.75 |
| Reserved in total, GPU-hours | 21.5834 |
| Cap, GPU-hours | 30 |
| Unreserved remainder, GPU-hours | 8.4166 |
| Actual GPU-seconds, whole session | 38,632 |
| Actual GPU-seconds, this phase | 10,900 |

| Phase reservation | GPU-hours |
|---|---|
| N2 cell | 1.0 |
| Finer ladder | 1.5 |
| One-neuron check | 0.75 |
| SER ranking | 0.5 |
| SER ablation | 2.0 |

## The user's options

The user decides which of these to take. Costs below use the reservations of this phase as a guide and are estimates, not ledger rows.

1. **A SER ladder at smaller sizes.** Cut the SER deception-only class at sizes below 500, as the FAR ladder did, and see whether the honest and no-pressure collateral shrinks before the deception effect does. A four-size ladder would reserve about 1.5 to 2.0 GPU-hours.
2. **An all-forms SER run.** R17 kept this as the stated alternative to the predicate-naming rows. Act-naming alone is infeasible, at 49 D and 42 I eligible rows, so this option mixes clause forms and loses the wording match.
3. **A FAR ladder above 750.** Size 750 passed and bounds nothing from above, and the tightest bar there is inversion under twin at 0.217. Sizes above 750 would locate where that bar first fails on the seed-3 sample. The size-1,000 class failed it on the seed-2 sample at 0.340.
4. **A clause-reading test of the early-layer neurons.** Report 05 raised the hypothesis that the size-500 class only reads the clause tokens. No run so far addresses it, and the one-neuron check suggests the class effect is spread across many small early contributions.
5. **Wrap-up.** Merge the branch to main under the user's wrap-up definition and report the two FAR decisions with the new follow-up results beside them. F7 and F8 are reviewed, and F9 and F10 would be reported as preliminary unless reviews 07 and 08 return first.

## Provenance notes

**Incident P1.** The N2 cell was submitted after later commits had landed, so its manifest names d5f6b17 while the job name, the ledger row and the output directory name 3486f1a. W10 verified the FAR sample outputs byte-identical across the two commits, and the ablation and verdict code are identical between them, so the result is unaffected. The ladder and the SER ranking show the same pattern, with manifests naming d5f6b17 against job names 92fc6fb and a41752a. The one-neuron manifest names 800c903 instead, and I have not verified that code is identical between 800c903 and the commit in its job name. The WORKLOG records the incident and keeps the output paths. The sources are `../WORKLOG.md`, `09-runner-handback.md` and `12-runner2-handback.md`.

**Incident P2.** The orchestrator wrote four inline times without reading the clock, and rulings R16 to R18 were corrected in `../spec.md` to 10:50 AM, 11:00 AM and 11:17 AM EST. The tool's own stamps are authoritative. One WORKLOG entry stamped 11:23 AM EST still carries an inline time of about 12:40 PM EST, and I report the stamp. The times in this report were read from the clock at writing.

**Review status.** Findings F7 and F8 are reviewed. Findings F9 and F10 are pending independent recomputation, and every number for them above is copied from the verdict files and not recomputed here.
