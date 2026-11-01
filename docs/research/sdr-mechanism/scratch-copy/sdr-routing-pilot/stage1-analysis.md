# Independent Stage 1 analysis: SDR routing pilot

2026-10-21 UTC. Raw source directory: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-routing-pilot/stage1-retry-f7cb49f-20261021T002501Z`. Sources used: `manifest.json`, `baseline.jsonl`, `comparisons.jsonl`, `gate.json`, `numerical_controls.json`. I independently selected `status=completed` comparison rows and recomputed directional effects, full-vocabulary truth flips, and 2,000-replicate story-cluster bootstrap intervals. I did not use the pooled reciprocal-direction summary to infer roles. Analysis seed20261021; each story receives equal weight after averaging its eligible rows. Intervals below are descriptive pointwise95% intervals without multiplicity adjustment or a power/significance claim. All effects are logit-margin changes unless stated otherwise.

**Provisional user message:** Shared32 can transfer either improved forced-choice truthfulness or impaired honesty depending on donor direction. Candidate6 also carries an instruction/context-sensitive effect that cannot be explained by copying the donor's emitted item alone. Selector2 depends more strongly on donor/recipient answer-content agreement. These observations support the approved focused pathway diagnostic; they do not identify pure pressure mediation, semantic roles, strategic intent, or external deception suppression.

## Integrity and achieved support

All480 baseline rows,6,528 available patches and384 explicitly excluded proposals are present. There are544 completed pairs per family/scope across48stories. Thirty-two frozen cross-story pairs lack a partner, each excluding6families×2scopes. The numerical controls report1,149 self/empty receipts with bitwise pass and valid mapping. Empty-family effects are exactly zero. All MLPs remain intact; the recipient remainder evolves freely under family patches. Readout is one semantic position; common adds mapped unchanged semantic positions. These are partial-position interventions, not whole-token ablations.

All96primary P variants (2truths×48stories) emit the false item. H truthfulness is74/96 (discovery33/48, confirmation41/48); N78/96 (38/48,40/48). No primary P/H/N full-vocabulary argmax is a non-item. All24stories per split have at least one accessible H and N variant; this does **not** mean all H/N variants are truthful. Alternative pressures add192P baseline rows but were not patched. The gate identifies32diagnostic stories (15discovery,17confirmation) and passes answer/content diagnostic support. Pure pressure mediation remains unidentified: designation changes populate answer cells but also change content. H adds an instruction, whereas N deletes pressure; these are different interventions.

Saved masks/candidate families were discovered on the same behaviorally filtered SDR test distribution. The prospective24/24story split prevents pilot split leakage but is not independent of historical candidate/data selection or OOD confirmation. No effect-size threshold determined viability.

## Direction matters: unchanged truth and story content

Common-scope change in recipient **truth-minus-other-item margin**. P←H means an H donor into a P recipient. Each cell has48rows/48stories. Positive improves recipient truth margin. Story/designation/truth are fixed and the clause/instruction changes. Donor emissions sometimes remain false, so these cells are not synonymous with donor copying.

| Family | P←H | H←P | P←N | N←P |
|---|---|---|---|---|
| candidate6 | +1.22 [1.00,1.42] | −1.07 [−1.26,−0.88] | +1.52 [1.19,1.84] | −1.34 [−1.63,−1.02] |
| selector2 | +1.50 [1.28,1.71] | −1.34 [−1.52,−1.14] | +1.47 [1.20,1.74] | −1.86 [−2.23,−1.49] |
| outsider2 | +1.33 [1.08,1.60] | −1.38 [−1.66,−1.12] | +1.31 [1.00,1.62] | −1.59 [−1.95,−1.20] |
| shared32 | +2.49 [2.11,2.85] | −2.47 [−2.83,−2.07] | +2.74 [2.20,3.26] | −2.88 [−3.45,−2.29] |
| outside-mask2 | −.002 [−.012,.009] | −.007 [−.018,.004] | −.003 [−.016,.010] | +.003 [−.010,.015] |

Shared32 has the largest effects in both directions. Its ability to improve P with an H/N donor coexists with severe harm when the pressure-conditioned state is injected into accessible H/N recipients. Reciprocal positive and negative effects must not be pooled into a claim of weak causal involvement.

Full-vocabulary outcomes in these same cells:

| Family | Truthful after P←H /48 false P | Truthful after P←N /48 | H truth lost after H←P /37 accessible | N truth lost after N←P /39 accessible |
|---|---:|---:|---:|---:|
| candidate6 | 9 | 25 | 10 | 5 |
| selector2 | 19 | 24 | 16 | 13 |
| outsider2 | 17 | 19 | 15 | 6 |
| shared32 | 34 | 38 | 36 | 35 |
| outside-mask2 | 0 | 0 | 0 | 0 |

These are forced item-response changes, not free-generation strategic-deception rates. Each cell has one selected truth variant per story; denominators differ from all96baseline H/N variants. A donor-conditioned state is not unconditional removal.

## Changed truth and actual emitted answers separate the families

Reversing donor designation/truth attenuates selector2 strongly. Candidate6 still improves P recipient truth even when H/N donors emit the recipient's false answer. These comparisons preserve the content-change label and do not isolate pressure.

| Family | P←H, changed truth (48stories) | P←N, changed truth (48stories) |
|---|---|---|
| candidate6 | +1.71 [1.34,2.10] | +2.12 [1.64,2.62] |
| selector2 | +.27 [.11,.41] | +.20 [.03,.40] |
| outsider2 | +.99 [.70,1.27] | +1.25 [.96,1.59] |
| shared32 | +1.04 [.69,1.39] | +.99 [.60,1.42] |
| outside-mask2 | −.007 [−.024,.009] | +.006 [−.006,.017] |

The strongest counterexample to simple emitted-item copying uses **only changed-truth H/N→P rows where the donor emits the same false item as the P recipient**:76rows/48stories, averaging one or two eligible rows within each story. Candidate6 increases recipient truth margin +1.71 [1.35,2.07]. Analogous selector2 effect is +.042 [−.059,.141]; outsider2 +.77 [.57,.95]; shared32 +.62 [.36,.89]. Candidate6 therefore alters recipient answer processing without merely imposing the donor's emitted item. Several context/routing computations could produce this; pressure-reader/truth-representation labels are not identified.

Conversely changed-truth P→H/P→N effects are candidate6 −.28/−1.00, selector2 +.22/+.17, outsider2 −.32/−.60, shared32 +.05/−.34. All cells have48rows/48stories. Here the pressure donor typically emits the recipient's truthful item, so candidate6's continuing negative effect again conflicts with a universal emitted-item-copy rule. Shared32 and selector2 are much closer to zero or slightly truth-favoring than under same-truth pressure donors. No single donor-truth or donor-emission rule explains all strata.

Same-pressure P0↔P1 swaps have changed truth/content and96rows/48stories. Both primary P baselines are false, so swapping designation also changes donor emitted answer relative to recipient truth. Common-scope truth-margin gains: candidate6 +2.40 [2.11,2.70], selector2 +1.79 [1.59,2.01], outsider2 +1.12 [1.00,1.23], shared32 +3.44 [3.05,3.84]. Outside controls ~0. These show truth/designation/answer-content sensitivity with pressure condition fixed; the correlated factors cannot be separated.

Cross-story N→N controls involve altered entity/content,64rows/32recipient stories. Truth-margin effects are candidate6 −.64 [−1.01,−.32], selector2 −.81 [−1.32,−.35], outsider2 −.33 [−.58,−.12], shared32 −1.57 [−2.56,−.66]; they lose6/52,6/52,4/52,19/52accessible row-level truths respectively. These are confounded donor-content controls, not clean pressure tests. Their story resampling treats recipient stories as units; frozen donor-story reuse can add dependence not captured by that simple bootstrap.

## Scope and split checks

On own-story unchanged-truth P↔H/P↔N rows, sign-align effects toward the donor's actual emitted item **before** averaging reciprocal directions. The paired common-minus-readout differences are candidate6 +.431 [.352,.507], selector2 +.039 [.030,.049], outsider2 +.080 [.068,.093], shared32 +.413 [.339,.486], each192pairs/48stories. Candidate6 and shared32 depend more strongly on the added common positions. This motivates focused paths but does not prove indirect mediation or exclude readout-only effects.

Leading unchanged-truth directional findings keep their signs in both frozen splits. P←H common cells below have24rows/24stories per split:

| Family | Discovery | Confirmation |
|---|---|---|
| candidate6 | +1.16 [.85,1.45] | +1.28 [1.00,1.56] |
| selector2 | +1.46 [1.13,1.77] | +1.54 [1.24,1.83] |
| outsider2 | +1.16 [.81,1.50] | +1.50 [1.14,1.86] |
| shared32 | +2.38 [1.80,2.92] | +2.60 [2.13,3.07] |

Candidate6 changed-truth P←H is +1.94 [1.36,2.49] discovery and +1.49 [1.01,2.00] confirmation; P←N +1.90 [1.16,2.62] and +2.34 [1.67,2.98]. Selector2 changed-truth P←H is smaller and uncertain on confirmation (+.13 [−.09,.36]). These are descriptive checks within the historically selected distribution. No new families or favorable donor replacements were selected.

## What the approved fixed Stage 2 can resolve

Continue only within approved answer/content diagnostic scope and remaining1reservedH200hour. The fixed39attention/readout direct-path cells can ask whether candidate6 outputs reach selector2 through Q versus grouped K/V, versus direct readout contribution. Intermediate freezing is needed to interpret direct paths. Discovery-selected≤3semantic-position followups must report all confirmation outcomes and can investigate the common/readout distinction. Preserve raw margin effects and donor/truth strata; Stage1 does not justify selector/mover role labels.

Approved candidate6/selector2/outsider2 interactions and fixed .5shared32 dose can distinguish conditional dependence from approximately independent contributions away from saturated margins. A nonadditive loss near a floor/ceiling is not evidence of redundancy. Stage2 still cannot identify pure pressure mediation, exclude MLP routes, establish completeness, or validate external suppression. No larger grid, head search, v2evaluation, training, or external judges is warranted.

Operator-reported accounting:124actualGPU-seconds,3,600reserved of7,200authorizedGPU-seconds, zero paid APIs. Budget is reservation-based. Lead context compactions were0 at this Stage1 checkpoint; current count:1 (first compaction occurred after the Stage2 audit completed). This analysis launches no jobs and changes no code, memory, or selection rules.
