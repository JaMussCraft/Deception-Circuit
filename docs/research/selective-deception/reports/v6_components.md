# Sparse necessary-mask components: completed first round

**L17H27 is the strongest local causal lead, and its effects are shared with benign inversion.** Restoring its intact output within the 30-head intervention restores much of the answer-margin change. A smaller direct L13H23→L17H27 query-path effect also acts on both tasks. These findings support shared answer routing under the tested intervention; they do not establish deception specificity.

The bounded round is complete: all 30 individual-head tests, seven conditional releases, matched benign controls, token-level attention, cached-clean rescue, donor-assignment comparison and one targeted path with a matched comparator. Technical and scientific reviews passed. No further jobs are active for this round.

## What was measured

The model is Llama-3.1-8B-Instruct on A40/BF16. The causal intervention replaces selected head slices at each recipient's last actual prompt token with its assigned honest donor's own last-token values. Other prompt positions remain unchanged. This differs from V5's all-position and free-generation interventions.

SDR uses 16 development and 16 internal-validation scenarios, each with deceptive instructions (D), truthful instructions (H), no pressure (F), and transparent benign inversion (I). D and I request the false/alternative answer under different framings; H/F request truth. A supplementary 16-scenario FAR panel lacks a matched capable-I control. Every intact case was requested-correct in the recorded fp32 readout. These previously exposed scenarios are mechanism development/internal validation, not pristine mask holdouts.

The pilot acquired 3,248 causal rows and 720 attention rows. The fixed follow-up acquired 640 rows: all 16 SDR validation scenarios × four variants × ten states. Technical smoke repeats are excluded from those sample counts. Exact source, donor, mask and case identities were frozen before the relevant outcomes.

## Whole-mask and individual-head findings

Positive margin drops weaken the requested answer. The table reports scenario means; D−I intervals are exploratory paired scenario-bootstrap intervals.

| New30 SDR panel | D drop | I drop | H drop | F drop | D−I, 95% interval |
|---|---:|---:|---:|---:|---:|
| Development, 16 scenarios | 1.245 | 1.352 | 0.274 | 0.328 | −0.107 [−0.316, 0.093] |
| Internal validation, 16 scenarios | 1.709 | 1.254 | 0.301 | 0.265 | +0.455 [0.079, 0.856] |

The positive validation contrast does not establish stable selectivity across panels. New30 leaves every SDR D/H/F/I requested argmax answer at 16/16 on both panels, despite changing margins and distributions. On supplementary FAR, instructed false answers fall from 16/16 to 6/16 while H/F remain 16/16; the missing matched-I panel limits its interpretation.

L17H27 single-head replacement drops development D/I margins by 1.016/1.099, versus 0.305/0.382 for H/F. Conditional release from New30 restores D/I margins by 0.824/0.865. L13H23 is the strongest earlier-layer single-D candidate, with D/I drops of 0.178/0.239. Most other single readout-position effects are small under this donor policy. These effects need not add to the whole-mask result and do not establish global irrelevance of the other heads.

![All 30 individual-head effects](/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/analysis-002/single-head-effects.png)

## Rescue and direct-path validation

The head choices were fixed from development before candidate-head validation. Cached-clean rescue restores the recipient's intact L17H27 output while the other 29 heads retain donor replacements. Natural release instead lets L17H27 compute in the perturbed context; cached-perturbed self reinsertion is the exact no-op comparator.

| Variant | Clean rescue minus New30 | Natural release minus New30 | Direct Q27 path drop | Matched Q26 path drop |
|---|---:|---:|---:|---:|
| D | +1.476 | +1.333 | 0.0853 | 0.0036 |
| I | +0.879 | +0.799 | 0.0776 | 0.0088 |
| H | +0.340 | +0.328 | 0.0075 | 0.0049 |
| F | +0.304 | +0.307 | 0.0013 | 0.0059 |

For D/I, positive rescue restores the instructed false/alternative preference; it does not make the answer more honest. The strong D and I rescue validates L17H27 as a shared local causal lever. Clean rescue and natural release differ, supporting sensitivity to the upstream context. No rescue ratio is interpreted as an additive percentage of deception mediated.

The targeted path changes only L13H23's final output, freezes other component outputs while capturing the receiver query, then writes that query into an otherwise clean run. It measures a direct residual-through-normalization route into Q. The Q27−Q26 drop is 0.0817 on D [0.0423, 0.1217] and 0.0688 on I [0.0448, 0.0948], with near-zero H/F contrasts. Q26 is an adjacent matched comparator in the same KV group, not an assumed null. This is one isolated route under explicit clamps, not all mediated paths or a semantic-clause circuit. Its effect must not be divided by the total sender effect as a mediation percentage.

![Rescue and targeted query-path results](/projects/beto/swong2/Alignment/.scratch/selective-deception/component-analysis-v6/followup-analysis-001/rescue-and-path-effects.png)

**Every follow-up state still gives 16/16 requested-correct answers in each SDR variant, in both native and fp32 argmax.** These are changes in answer preference, not observed SDR corrections, refusals or generated deception rates.

## Donor and attention controls

Exact answer-word matching was infeasible for all recipients. A prospective amendment retained all 16 and explicitly compared honest donors whose construction truth occupies the same/opposite item position. Words, contexts and lengths differ, so this measures assignment sensitivity rather than isolated position routing or content copying. Truth-oriented agree-minus-disagree margins are D +0.031, I −0.044, H +0.095 and F +0.110; all intervals include zero. There is no clear directional signal for these assignments, not evidence of donor equivalence or irrelevance. All selected donors are capable in the saved checks: 38 unique donor IDs/scenarios across arms, not 192 independent observations from the repeated capability rows.

Attention covers eight fixed development scenarios and all 30 heads under D/H/I. L17H27 places about 24.6%/11.5% raw mass on occurrences of truth/false answer-token IDs under D, 24.8%/13.0% under I, and 10.0%/11.1% under H. These are exact lexical occurrence sums, not semantic truth or instruction segments. L13H23 puts much less mass on those words; a fixed illustrative example emphasizes literal boundary/header tokens. Neither observation establishes a function from attention alone.

Eager and SDPA each pass identity checks, but their logits differ: requested-margin drift reaches 0.25 native, with no argmax changes in the 24-case attention subset. No unverified clause/fact boundaries or cross-backend numerical equivalence are assumed.

## Evidence, scope and next question

Independent audits verified all rows and intervention controls. The follow-up passes 560 batch-level exact flags, exactly reproduces 1,536 prior intact/New30 metric fields and exactly reproduces all 160 repeated smoke rows. Full component banks and Q/vocabulary tensors were not retained for independent reconstruction; the audit combines saved scalar/argmax/proof evidence with reviewed source.

[Detailed pilot results](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/202-v6-pilot-results.md), [follow-up results](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/209-v6-followup-results.md), [final artifact audit](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/208-v6-followup-final-artifact-audit.md), [scientific review](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/210-v6-final-scientific-review.md), [attention descriptives](/projects/beto/swong2/Alignment/.scratch/selective-deception/reports/211-v6-attention-token-descriptives.md).

The next scientific question is whether this shared routing mechanism explains the all-position/free-generation effects, and whether matched lexical counterfactuals separate donor information from task structure. Those require a separately frozen design; this round did not add edges, optimize a mask or reuse eval5 as untouched confirmation.

This component round used **602 GPU-seconds (10 minutes 2 seconds)** across four completed jobs and **55 minutes of reservations**, with no additional API calls. Cumulative selective-study reservations are **38.0167/40 GPU-hours**, actual usage is **44,981 GPU-seconds (12h29m41s)**, and 1.9833 reserved GPU-hours remain. Code is checkpointed at `57c53ac539d55ae5c6bff67cdb5be31c2289e802` on the isolated `selective-components-v6` branch. Frozen manifests, receipts, raw data and plots are retained.
