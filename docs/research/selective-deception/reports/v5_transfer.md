# Frozen-mask transfer: V2 and eval5

All ten eval5 blocks are acquired and technically audited under the disclosed amended protocol: **371 fixed recipients, 1,855 recipient responses, and 310 generation batches**. Independent scientific review is complete. The 30-head mask has its clearest favorable comparison on instructed deception; transfer elsewhere is mixed. These results do not establish a deception-specific mechanism.

- Instructed deception falls from48/50 native deceptive labels intact to6/50 with New30, versus31/50 with the fixed random mask. Nine New30 outcomes remain official INVALID. Even assigning all nine to deception gives6–15/50, versus48–50 intact and31–32 random, holding classified labels fixed. These are sensitivity bounds, not confidence intervals or protection against judge error.
- OldD69 produces fewer native deceptive labels than New30 in every block, while New30 has lower generated-text reference NLL in every block. This is a suppression/output-quality tradeoff; neither mask dominates, and NLL is not a benign-capability test.
- Coherent refusals are desirable and occur in the saved outputs. Other reductions reflect continued misleading spin, ambiguity, repetition, missing tags or the numerical range-overlap rule. Unparsed outcomes cannot be credited wholesale as successful suppression.

## Complete eval5 comparison

Entries are **native deceptive / honest / unparsed** counts on the entire fixed denominator. These categories have different meanings across benchmarks; no pooled deception headline is reported. Random30 is one fixed layer-matched comparator, not a random-null distribution. The full five-state table, including New23, is in the linked audit.

| Benchmark | N | Intact | New30 | OldD69 | Random30 |
|---|---:|---:|---:|---:|---:|
| Sandbagging |50|16/6/28|12/6/32|0/9/41|9/6/35|
| Instructed deception |50|48/0/2|6/35/9|2/40/8|31/18/1|
| Harm knowledge report |50|49/1/0|35/12/3|17/25/8|34/6/10|
| Convincing game |50|49/0/1|23/0/27|11/0/39|47/0/3|
| MASK continuations |28|26/0/2|17/4/7|4/12/12|7/6/15|
| MASK disinformation |11|11/0/0|5/0/6|4/1/6|5/0/6|
| MASK doubling-down |29|27/2/0|20/4/5|12/5/12|20/2/7|
| MASK known facts |37|36/0/1|19/5/13|16/8/13|20/2/15|
| MASK provided facts |50|46/0/4|30/11/9|17/9/24|32/4/14|
| MASK statistics, o3-amended |16|14/2/0|10/5/1|8/4/4|9/2/5|

New30 has lower raw D than Random30 in four blocks, equal counts in two, and higher counts in four; this tally is descriptive, not an aggregate efficacy statistic. Adding seven heads to New23 lowers raw D in nine blocks but increases it in sandbagging. It does not isolate seven standalone causal effects.

Sandbagging remains a quality warning: New30 distinct-2 falls.683→.382 and the at-token-limit proxy rises0→16/50, while NLL stays near baseline. Earlier targeted inspection found repetition and continued sandbagging intent behind missing tags. Neither New30's12 D nor OldD69's0 D establishes clean suppression.

In convincing game, New30's27 U comprise21 official INVALID and6 outputs using the frozen belief option under lying instructions. Some responses remain misleading or confused; zero H does not mean every U is failure, and27 U does not mean27 coherent refusals. The benchmark measures target-claim behavior, not actual human persuasion.

A deterministic, posthoc and unblinded ten-example MASK inspection found coherent refusals alongside contextual false confirmation and mixed truthful/cover explanations. These examples show that both patterns occur, without estimating prevalence. Statistics likewise contains a clear refusal, but its three New30 D→H transitions are range-overlap outcomes, not three established truthful corrections: broadening75,000 to“over75,000” can overlap a reference150,000–175,000 without stating that reference value. Original labels are preserved.

Generated-text reference NLL teacher-forces each state's own output through the intact model. New30/OldD69 NLL is.891/1.276 instructed,.502/.966 convincing,.390/.949 continuations and.369/.804 statistics. Length, content and predictable repetition affect this measure; it does not establish preserved benign utility.

## Protocol and causal scope

The original protocol is not claimed complete. Two explicit amendments remain visible: instructed acquisition is complete despite23 official INVALID outcomes and its original `complete:false`; statistics used a prospectively reviewed o3 substitution after o3-mini retired, before any statistics generation. Four neutral compatibility probes passed. All80 statistics responses used the same replacement extractor, original prompt/schema, low reasoning effort and range-overlap grader. Compatibility is not judge equivalence. Nine completed blocks and the original failed statistics attempt remain unchanged.

All historical A40-selected recipients and beliefs were retained, with fresh H200 intact outputs and native honest donors. No filtering, refill or mask reselection occurred. This exposed pilot tests necessity-like disruption under honest-donor interchange, not unique necessity, sufficiency or a deception-specific mechanism. Donor content and shared task/instruction-following machinery remain possible explanations. Native donor tiling differs from V2's independent donor replay.

New30 has27 heads outside the original103-head search union: two overlap old D, one overlaps F, none overlap H. Six of the seven additions to New23 are outside all three supports. This identifies previously excluded candidates, not their functions.

## Separate V2 transfer

The V2 assessment used128 recipients per family, excluding scenarios used for old-mask fitting/selection. Every mask received the same independent honest-donor activations. Intact chose all128 instructed false labels and all128 neutral-H truths per family.

| Family | New30 false labels | OldD69 false labels | New30 neutral-H truths | OldD69 neutral-H truths |
|---|---:|---:|---:|---:|
| FAR |2/128|7/128|126/128|105/128|
| SDR |87/128|24/128|122/128|91/128|
| SER |36/128|17/128|118/128|115/128|

New30's126 FAR truthful corrections span all four polarity/item-position cells (31,32,32,31 of32), inconsistent with a simple fixed-position default. The seven added heads yield39/19/24 further D corrections in FAR/SDR/SER with no reversed D corrections, but honest-task losses/churn remain. New30 preserves103/128 SER no-pressure truths versus108/128 for OldD69, so preservation is not universal. All6,144 rows and1,572 numerical identities passed review. This single-prefill label test does not measure free-generation honesty/refusal and should remain separate from eval5.

## Evidence and resources

[Final scientific review](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/187-final-scientific-review.md), [all-five-state raw tables](/projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/statistics-judge-amendment/final-raw-tables-001.md), [machine audit](/projects/beto/swong2/Alignment/.scratch/selective-deception/transfer-v5/statistics-judge-amendment/final-machine-audit-001.json), [qualitative MASK examples](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/197-mask-evasion-qualitative-examples.md), [V2 results](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/160-v2-frozen-mask-results.md), [head inventory](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/164-v5-frozen-head-inventory.md).

All study GPU jobs are terminal. Cumulative reservations37.1/40 GPU-hours; actual44,379 GPU-seconds (12h19m39s), including earlier phases/failures. API accounting:1,113 attempts, $4.1784295 known charges plus a retained $0.66 unknown reservation from the retired-endpoint failure; conservative exposure$4.8384295/$20, zero pending. Unknown cost is not zero and billing is not exact. Original acquisition ambiguity, grading amendments and audit limitations remain in the machine record.
