# Review 06: the D2 follow-up result (honest-instructed control)

Independent Opus review, Tue 3 Nov 2026 (Eastern time), of the D2 follow-up read from Bridges-2 job 50161975 under
ruling R15. I ran no git, no Slurm job and no paid call. Every figure not in `readings.json` is marked as computed
by this review and is descriptive.

## Scope

I read ruling R15 and its implementation note (`spec.md:34`), `plans/D2-followup-plan.md` sections 1 to 5, review 04
(`reviews/04-d2-review.md`) and review 05. I also read all of `scripts/d2_followup.py` and the helpers it uses in
`scripts/d2_premise.py` (`cluster_bootstrap` at line 1065, `explains` at line 1138). On the outputs side I read
`readings.json`, `readings.md`, `drift_anchor.json`, the GPU timings, the nine feature manifests, the job log
`logs/bridges2/d2_followup_50161975.out` and the D2 `results/d2/readings_final.json`. I formed my view from these
before reading hand-back 10.

Recomputation, on the mgnp interpreter, with read-only scratch scripts in `/u/swong2/.claude/jobs/5b9b1c28/tmp/`:

- **Re-read.** I re-ran `read_task` on the stored features for all three tasks. Its output equals the stored
  `readings.json` except 10 non-coefficient floats that differ at the last bit.
- **Hashes.** I recomputed the D2 feature hashes, the pool, code and feature-file hashes against the manifests.
- **Logits.** I re-fitted `C_HI` with the read's own code and took the mean logit of every condition on the
  act-form ids (`logits.py`), then split them by I clause, D clause, frame family and lie word (`lexical.py`,
  `lieword.py`, `vardec.py`).
- **Intervals.** I computed clustered intervals for the raw D minus I logit shift and the interaction
  (`shiftci.py`), plus the joint reading's undefined-resample count and logit-space positions (`joint.py`).
- **Tests.** `tests/test_d2_followup.py` passes on mgnp, 43 of 43 in 38 s.

## Question 1

**R15 was applied as frozen.** The evidence follows; two small reporting gaps are in Errors found.

- **Per-task then direction labels.** `task_label` (`scripts/d2_followup.py:780`) returns (a) on a failed gate and
  (c) only on FAR or SDR with all eight conditions true; otherwise (b). `direction_label` (line 790) returns (c) only
  on a FAR (c), a suggestive (c) on SDR alone, (a) when every task is (a), and (b) otherwise. Labels are (b), (b),
  (b), direction (b).
- **Signed rule.** The gap is the mean of `1[D] - 1[I]`, signed (line 732). The 15-point test is on the signed gap
  (line 901), and the interval must lie above zero (line 902).
- **Spread, leave-one-cluster-out and refusal.** The 0.30 spread is D minus HI on the act-form ids (lines 862 and
  903). The leave-one-cluster-out loop drops each D clause cluster in turn (lines 864 to 868). The refusal control
  refits ablated D against ablated HI and reads the same act-form ids (lines 872 to 879). Its validity AUROC is on
  those ids (lines 884 and 905), with the all-ids AUROC beside it (line 886).
- **IH coding.** Per id, `(z_D - z_I) - (z_HI - z_IH)` on the `C_HI` logit (line 891). Its interval is clustered by
  D clause (line 895), and "holds" means the lower bound is above zero (line 907). This matches the R15
  implementation note exactly.
- **Gate.** Validation AUROC of D against HI on all 200 validation ids (lines 827 to 830). Gates: FAR 1.000, SDR
  0.999, SER 0.976.
- **Manifests.** All nine manifests carry `pre_registered: true` and an empty stack check. They record torch
  2.11.0+cu128, transformers 5.13.0, an NVIDIA H100 80GB HBM3, commit `54cd1eb` and the pinned direction sha256
  `3e03edcd…f0cf0`. The direction is checked before the model loads (lines 602 to 607), and a stack mismatch stops
  the stage (lines 609 to 611). Each feature file's sha256 equals its manifest's.
- **Fallback firings.** Zero. Every pick in every manifest is `mirror`, and the features stage refuses to run on any
  firing (lines 312 to 317 and 620 to 622).
- **Row counts.** Unablated 1,240, 1,185 and 1,147 plus the 600-row anchor give 4,172. Ablated 410, 450 and 449 give
  1,309. The total is 5,481, as pre-registered.
- **D2 feature hashes.** The read verifies each D2 feature file against its D2 manifest before anything else
  (`verify_d2_files`, lines 1017 to 1030, called at line 1034). The six hashes in `readings.json` equal the files
  today.
- **Drift anchor.** It is computed first (lines 656 to 670; the job log prints it before any new row), and the read
  stops above the bar (lines 1041 to 1043). All 600 rows are bit-identical, maximum difference 0.0.

## Question 2

**Sign convention: confirmed.** The interaction equals `(z_D - z_HI) - (z_I - z_IH)`. Above zero, the one-word
lie-to-honest swap moves `C_HI` further in D's clause than in I's clause. In R15's words, I's D-likeness is not
carried by its frame words. On FAR the two shifts are D minus I 2.347 and HI minus IH -1.506
(`readings.json:263` and following), so 3.853 = 2.347 + 1.506.

**Mean `C_HI` logits on the act-form ids** (computed by this review, from the read's own fit):

| task, ids | D | I | HI | IH | H | DT | HT |
|---|---|---|---|---|---|---|---|
| FAR, 210 | 8.01 | 5.66 | -8.03 | -6.52 | -8.59 | 6.75 | -11.11 |
| SDR, 35 | 5.50 | 4.43 | -5.69 | -6.04 | -13.11 | 5.81 | -1.76 |

On FAR, the swap moves the score 16.03 logits in D's clause (D minus HI) and 12.18 in I's (I minus IH), a ratio of
0.76. On SDR the two are 11.19 and 10.48, a ratio of 0.94.

| reading, act-form ids | FAR | SDR |
|---|---|---|
| D minus I logit, interval by D clause | 2.35 [0.92, 4.34] | 1.06 [-0.98, 3.02] |
| D minus I logit, interval by I clause | 2.35 [0.38, 4.42] | 1.06 [-0.85, 3.38] |
| interaction, interval by I clause | 3.85 [1.78, 6.06] | 0.72 [-0.98, 2.52] |
| AUROC of D against I on the logit | 0.70 | 0.53 |

**The rate readout is saturated, and this is a real qualifier.** On FAR, D's lowest logit is 2.81 and I's mean is
5.66. Only 2 of 210 I rows fall below the threshold at 0. A shift of 2.35 logits, about 15 percent of the 16-logit
D-HI span, cannot register when both conditions sit 6 to 8 logits above the threshold. The FAR null is a null of the
pre-registered rate readout. It is not a null in score space. The score-space difference is not new to `C_HI`:
review 04 reported an AUROC of D against I of 0.711 under D2's `C_H` (`reviews/04-d2-review.md:91`).

**What the score difference is: mostly wording, by the evidence in this data.**

- **D is flat and I moves.** D's mean logit is 8.0, 8.0 and 8.5 in the "wrong", "falsely" and "incorrectly"
  groups, which hold 206 of the 210 ids. I clause identity explains 91 percent of
  the variance of I's logit and 73 percent of D minus I. D clause identity explains 64 and 58 percent.
- **The spread is wide inside every frame family.** Mean I logit per I clause runs from 1.69 to 7.24 (drill), 1.42
  to 8.68 (quiz) and 2.22 to 11.29 (game). Two I clauses (`invd_far_v2_act_14` and `act_08`) score above their own
  D rows. A listener-knowledge signal predicts a consistent attenuation across transparent frames. The data show
  attenuation in some I clauses and amplification in others.
- **The difference tracks word overlap.** Across ids, D minus I has a Spearman correlation of -0.70 with the Jaccard
  overlap of the D and I clauses' non-frame words. At the level of the 34 (D clause, I clause) pairs it is -0.78. The
  low-overlap third has D minus I 4.68, the high-overlap third -0.68.
- **It vanishes where the lie word matches.** On the 6 D clauses that use "wrong" like the I clauses (153 ids),
  D minus I is 1.19 [-0.20, 3.08] with AUROC 0.60. On the 4 D clauses that use "falsely" or "incorrectly" (53 ids)
  it is 5.8 to 6.3 with AUROC 1.000.
- **A confound limits that split.** Those 53 rows carry only I clauses `act_05`, `act_06` and `act_07`, because
  the inversion builder pairs clauses by token count. D's lie word and I's clause identity are nested here and cannot
  be separated.
- **The interaction holds partly for the reverse of its design intent.** IH sits 1.51 logits above HI: I's frame
  words make an honest clause more D-like. Subtracting that negative frame shift adds 1.51 to the 2.35. The control
  removes only the additive effect of the frame words. Template, verb and lie-word form still differ between D's
  and I's clauses, as plan section 5.2 already says.

My reading is that FAR has a descriptive D minus I difference in score space of about 2.4 logits. It is carried by
which I clause a row has, and it is best explained by clause wording. A small listener-knowledge component cannot be
excluded, but nothing here isolates one.

**SDR does not show the pattern.** Its act-form D minus I is 1.06 with an interval spanning zero, AUROC 0.53, and an
interaction interval spanning zero under both clusterings. All of SDR's act-form D clauses use "wrong", and its
value matches FAR's "wrong" subset (1.19). Where the lie word matches, D and I sit within about one logit on both
tasks, and that difference is not distinguishable from zero.

## Question 3

**Confirmed: these are positions, not rates.** The read computes `p_X = (rate_X - rate_HI) / (rate_D - rate_HI)`
(line 923), as plan section 5.4 defines it. The arithmetic follows:

- SDR p_H is (0.000 - 0.020) / 0.956 = -0.021, and p_DT is (0.980 - 0.020) / 0.956 = 1.004.
- SER p_H is (0.032 - 0.120) / 0.823 = -0.107.
- A negative p_H means the neutral sentence scores below the honest instruction. A p_DT above 1 means DT scores
  above D.

**They are not labelled as positions where a reader meets them.** The joint table in `readings.md` (lines 21 to 25)
heads its columns p_I, p_H, p_DT and p_HT with no definition. R15 itself uses p_X for rates ("rates p_D, p_I, p_H,
…" and "the signed act-form gap p_D minus p_I"). Hand-back 10 says rates are what "R15 writes … p_X", then uses p_X
for positions in its joint table. A reader coming from R15 will read p_H = -0.021 as a rate. This is a labelling
collision, not a numbers error.

**The cell follows from the pre-registered relabelling.** `_level` (line 765) uses the 2/3 and 1/3 thresholds, and
`joint_cell` (line 771) maps high and low to "instruction content". FAR (1.000, 0.000), SDR (1.004, 0.163) and SER
(0.961, 0.190) are all high and low. The R15 relabelling touched only the (low, low) and (high, high) cells, which
no task reaches. No bootstrap resample was dropped as undefined on any task (computed by this review). The
statistic's intervals exclude zero everywhere.

**Logit space adds one thing** (computed by this review, descriptive). Positions on the mean logits are shown below.

| task | position of DT | position of HT | difference | true answer moves D to DT | true answer moves HI to HT |
|---|---|---|---|---|---|
| FAR | 0.92 | -0.19 | 1.11 | -1.25 | -3.08 |
| SDR | 0.95 | 0.41 | 0.55 | -0.66 | +5.74 |
| SER | 0.91 | 0.37 | 0.54 | -0.76 | +3.05 |

On FAR, a true answer moves both rows down, which is the common truth shift the statistic cancels. On SDR and SER, a
true answer moves the honest-instruction row about 40 percent of the way toward D and barely moves D. That is not a
common shift, so it does not cancel. It looks like a compliance component: D and HT both obeyed their instruction.
The rate readout hides it, because most HT rows stay below the threshold. Instruction content dominates on all three
tasks, and SDR and SER also carry a secondary compliance-like component in score space.

## Question 4

**(b) holds regardless.** The SDR act-form gap is 0.114, under the 15-point bar (line 901), so the label does not
depend on the interval.

**The lower bound of exactly 0.000 is structural.** D is scored at 1 on all 35 ids, so each id's D minus I is 0 or 1,
and the gap cannot go negative. The 4 non-zero ids sit in clusters SDR 03 (3 ids) and SDR 02 (1 id). A resample of 7
clusters omits both with probability (5/7)^7, about 0.095, which is above 0.025. So the 2.5th percentile is exactly
0. FAR is the same case: its 2 non-zero ids sit in clusters 05 and 10, and (10/12)^12 is about 0.112.

**The few-cluster intervals cut differently on the two tasks.**

- **SDR is underpowered.** Its interval [0.000, 0.250] (I-clause interval [0.000, 0.269]) cannot exclude a 15-point
  gap. SDR's (b) means "not shown", not "shown absent".
- **FAR's rate null is tight.** Its upper bound of 0.028 (0.025 by I clause) excludes a 15-point gap by a wide margin,
  on 2 failures of 210. Percentile intervals over 12 uneven clusters (1 to 44 ids) are optimistic, but not by enough
  to matter here.
- **Leave-one-cluster-out.** On SDR every gap stays above zero, but dropping cluster 03 leaves a single non-zero
  id (0.037).

## Question 5

**Gap sizes.** The all-ids gaps under `C_HI` are larger than under `C_H`: SDR 0.340 against 0.160, and SER 0.530
against 0.145 (`readings_final.json`, classifier gap). By form, the mean `C_HI` logits are as follows (computed by
this review):

| task and D form | ids | D | I |
|---|---|---|---|
| SDR act | 35 | 5.50 | 4.43 |
| SDR predicate | 166 | 5.09 | 1.01 |
| SDR other | 49 | 6.91 | 0.47 |
| SER predicate | 148 | 4.08 | -0.07 |
| SER other | 100 | 3.75 | -2.12 |

`C_HI` is trained on one-word lie-to-honest swaps (34 of 50 pairs, all 13 FAR pairs), so its axis is the deceptive
wording of the system clause. Act-form I clauses carry that wording and score near D. Predicate and other I clauses
carry it less and fall about halfway to HI. DT scores with D (rates 1.000, 0.980 and 0.912) and HT near HI.

**"The classifier reads being told to lie, not having lied" is supported, at the level the 2x2 can resolve.** The
false answer under an honest instruction (HI) reads as not-D. The true answer under a lie instruction (DT) reads as
D. Three qualifiers apply:

1. The design cannot tell "told to lie" from "the clause has the lexical shape of D's lie instruction". `C_HI` is
   trained on exactly that one-word contrast.
2. On SDR and SER a compliance-like component sits beside instruction content in score space (Question 3).
3. "Having lied" here means a teacher-forced wrong first answer, not the model's own lie.

**"Predicate- and other-form I clauses look less like lie instructions than D's" is supported descriptively, but not
controlled.** IH exists only for act-form clauses, so frame words are not separated from content on the predicate
and other forms. Within a form, D and I clauses also differ in wording beyond the frame.

**D2's own classifier read different things on different tasks.** Under the frozen `C_H`, HI reads as D on SER
(0.956), partly on SDR (0.240) and not on FAR (0.005). The SER D2 classifier read instruction presence, and FAR's
read the lie word.

A tighter statement would be: "`C_HI` reads the deceptive wording of the system clause, largely whatever the stated
answer. I clauses whose wording departs from D's (predicate and other forms, and some act-form clauses on FAR) score
lower."

## Question 6

**No error changes a label, a rate, a gap, a rate interval or any number reported in `readings.json` or hand-back 10.**
My re-read matches the stored read to the last bit apart from floating-point rounding. Hand-back 10 counts 146 such
values, and I count 10 because I did not compare the classifier coefficients. The reporting gaps and interpretive
points are listed under Errors found.

## Verdict and qualifiers

**(a) The finding is fair under R15, with qualifiers.** I would accept "under R15 every task labels (b): D and I are
indistinguishable at the rate readout on form-matched act-form clauses (FAR 0.010, SDR 0.114), and the D2 route
closes U1". It needs these qualifiers:

1. **The readout is saturated.** On FAR, D and I sit 6 to 8 logits above the threshold. The null is a null of the
   pre-registered rate readout.
2. **FAR has a descriptive score-space difference.** D minus I is 2.35 logits [0.92, 4.34], about 15 percent of the
   D-HI span. The IH interaction is 3.85 [1.82, 6.21]. Both are descriptive and not part of the rule.
3. **That difference reads as wording.** It is carried by I-clause identity, tracks wording overlap, and falls to
   1.19 [-0.20, 3.08] where D's lie word matches I's. The interaction is enlarged by IH sitting above HI. SDR does
   not show the difference.
4. **The two nulls differ in strength.** SDR's null is underpowered (upper bound 0.25). FAR's rate null is tight
   (upper bound 0.028).
5. **"Closes U1" is a consequence of the ruling** (R15, R6 iv). It is not a demonstration that no listener-knowledge
   representation exists.
6. **"F8's SDR pass is clause-driven on every task" needs rewording.** F8 passed on SDR only, and SER has no matched
   act-form reading. Suggested text: "F8's SDR pass is attributed to clause wording. Where wording is form-matched
   (act-form FAR and SDR), D and I do not differ at the rate readout. On SER the attribution rests on descriptive
   by-form gaps."
7. **The joint reading** is "instruction content" on all three tasks. On SDR and SER, score space also shows a
   compliance-like component.

**(b) The residual FAR score-space signal is not worth a new pre-registration on the existing data.** The data
already explain it as wording and pairing. A score-space re-read of the same clauses would inherit the nesting of
I clauses within D-clause groups, and it would be chosen after seeing the logits.

A new pre-registration is worth it only with a wording-controlled I pool. Each I clause would be D's own clause plus
a transparency frame, for example "For this quiz, your task is to answer the reviewer's question falsely". IH would
be HI plus the same frame. Frame by honesty is then an exact 2x2, and the interaction isolates what the frame does to
the lie word. It needs a pre-registered logit statistic, intervals by D clause and by I clause, and a bar sized
against the D-HI span. Frame-prefixed clauses must pass the fit and token tests. The cost should be about that of
this job, near 0.5 GPU-hours with no judge.

This is a new dataset and needs a new ruling. Under R15 the D2 route is closed whatever it would show, so whether to
reopen it is the user's call under need N2.

## Errors found

No numerical or code error. These are the reporting gaps and interpretive overstatements:

1. **The undefined-resample count is not stored.** Plan section 5.4 says resamples with no spread are "dropped and
   counted". `ratio_bootstrap` returns the count, but the read keeps only `ci95` (line 926). I computed zero on all
   three tasks, so nothing depends on it.
2. **The p_X positions are unlabelled, and their name collides with R15's.** See Question 3. The joint table in
   `readings.md` should say "position on the HI-to-D axis".
3. **The interaction interval is clustered by D clause only.** The variance is dominated by I clause. My
   I-clause-clustered interval, [1.78, 6.06], agrees, so nothing changes.
4. **Hand-back 10's "The truth shift is small" holds on rates only.** On the logit, a true answer moves HT 5.7 (SDR)
   and 3.1 (SER) toward D (Question 3).
5. **SDR's refusal "explains" rests on an exact tie.** The ablated gap is exactly half the unablated one. It does not
   affect the label, and hand-back 10 already notes it.

## Recommendations

1. **Record the finding with the qualifiers of the Verdict.** Mark the logit figures descriptive and
   reviewer-computed.
2. **Define the joint p_X as positions** wherever the finding or `readings.md` shows them, and keep "rate" for
   shares at or above 0.5.
3. **Keep the logit table of Question 2 next to the finding.** A reader of the rate table alone would take FAR's
   D and I as identical in score space, which they are not.
4. **Do not pre-register a score-space readout on the existing clauses.** If the user wants to pursue listener
   knowledge, the frame-prefixed minimal-pair design in the Verdict is the one to rule on.
5. **Optional, in any later version of the read:** store the undefined-resample count and an I-clause-clustered
   interaction interval. Neither is needed for this result.

## Hand-back check

Hand-back 10's figures agree with `readings.json` and my recomputation. That covers labels, gates, rates, gaps and
both intervals, the leave-one-cluster-out ranges (0.005 to 0.012 and 0.037 to 0.143), the ablated readings, the IH
interaction, shifts and frame share, the joint table, the by-form, frame-family, frozen-`C_H` and B1 to B4 tables,
the drift anchor, row counts and timings. Its "208 of 210" and "4 of 35" are right.

Where I read it differently:

- **"`C_HI` follows what the system instruction says, not the truth of the stated answer or whether the model
  obeyed."** This holds on FAR. On SDR and SER, score space shows a compliance-like component (Question 3).
- **"The truth shift is small."** Rates only (Errors found, item 4).
- **"F8's SDR pass … is read as clause-driven on every task … not a listener-deception state."** The follow-up
  tests this only where wording is form-matched. Predicate and other forms are not frame-controlled, and SER has no
  matched reading. The wording in Verdict qualifier 6 is safer.
- **The FAR IH sign.** Its account ("the frames do not carry I's D-likeness") is accurate. My addition is that the
  interaction is enlarged by IH sitting above HI, and that the residual D minus I tracks I-clause identity and
  wording overlap. A finding note on the sign, its open question 2, is warranted.
- **Notation.** It says R15 writes rates as p_X, then uses p_X for positions in its joint table (Question 3).
- **Its open question 1.** I agree the test AUROC stays a scratch figure in the hand-back. Adding it to the read
  after the result is not worth a code change.
