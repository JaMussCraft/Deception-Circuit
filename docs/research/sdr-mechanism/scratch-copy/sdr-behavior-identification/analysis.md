# Original-native SDR evidence audit

2026-10-25. **Standalone code/spec review PASS; independent quantitative/source review PASS.** The independently written direct-source checker reproduces the scientific counts below with 5,193 output-comparison assertions and no discrepancies. Root reports 21 focused tests, Ruff and a complete CPU rerun with byte-identical fixed audit, role and support artifacts. [Code review](code-review.md); [scientific review](scientific-review.md). These reviews validate the stated finite analysis, not independent behavioral confirmation. Old reports, saved evidence and failed gates remain unchanged.

## Evidence and reproducibility

The [fixed spec](spec.md) and [design review](design-review.md) define the original input-rule analysis. The [post-hoc addendum](exploratory-role-addendum.md) separately authorizes the outcome-derived factual-role comparison after preliminary copying exceptions were known; it is neither an original-library test nor independent confirmation.

| Artifact | Contents |
|---|---|
| [audit.json](results/final/audit.json) | All original fixed-rule counts, disagreements, categories, factor margins, story means, transitions, patch coverage and structural strata |
| [role-transport.json](results/final/role-transport.json) | Separate post-hoc literal/role/preservation/damaging predictions, all pairwise agreements/disagreements and structural strata |
| [source-manifest.json](results/final/source-manifest.json) | Exact resolved source paths, byte counts and SHA256 values; semantic artifact included |
| [structural.json](results/final/structural.json), [support.json](results/final/support.json) | Exact matching, exposures, overlap and missing condition×answer cells |
| [pilot-outcomes.jsonl](results/final/pilot-outcomes.jsonl), [eos-outcomes.jsonl](results/final/eos-outcomes.jsonl), [patch-outcomes.jsonl](results/final/patch-outcomes.jsonl), [baseline-pairs.jsonl](results/final/baseline-pairs.jsonl) | Reversible row-level joins, terminal outcomes, exclusions and paired transitions |
| [independent-results.json](independent-results.json), [independent_check.py](independent_check.py) | Independent recomputation directly from archived sources without importing the implementation |
| [results-summary.md](results/final/results-summary.md) | Compact machine-produced audit tables |

Final bound SHA256 values: `audit.json` = `c1469a81d12e9e9c9e3526a10efe0eae710333dae70186bd4cb51dc76e9922b1`; `role-transport.json` = `f9fb914a7fabce4788aa5a45e27692cc663b4f5e756643e44ebbe899477c68fd`; `independent-results.json` = `6d7864ab5b97db7c91efd107f8ee8d81dd52544725e2d5eb574b5772c4bf0e2b`. Source, test, checker and remaining artifact hashes are in the reviews/manifests.

Let `W = /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot`. The finite input sources are:

| Source relative to W | Verified denominator |
|---|---|
| `dataset/deception_pools/{pressure_sdr,pressure_shared,matched_honest_sdr}.json` | 20 SDR + 5 shared clauses, with exact matched honest instructions |
| `outputs/_analyses/sdr-routing-pilot/stage1-retry-f7cb49f-20261021T002501Z/{manifest.json,baseline.jsonl,comparisons.jsonl,gate.json}` | 480 first-token variants / 48 stories / 96 fixed-fact units; 576 directed pair proposals × 6 families × 2 scopes = 6,912 patch proposals |
| `outputs/_analyses/sdr-completion-diagnostic/labels-pre-adjudication-23099381/{joined.jsonl,source.json,summary.json}` and referenced archived input manifest | 256 native EOS responses / 32 stories / 128 exact P/N pairs; 1,024 synthetic responses excluded |

Exactly 6,528 patches have completed terminals and 384 have explicit missing-partner exclusions. Every family/scope has 544 measured and 32 excluded proposals, with no missing/failed terminal. The event history also contains 7,520 planned records and 6,528 attempted records; these are not extra measurements. All saved baseline and patched emitted IDs agree with their archived full-vocabulary argmax. Recorded effects equal patched minus baseline truth margin.

Within each pilot unit and EOS pair, exact facts/order/contract match and literal clause deletion leaves byte-identical prompts. EOS candidateA/B labels are decoded through each row's named candidates, independently agreeing with archived correctness. Candidate lexical order is not assumed to equal record order. Pilot and EOS have **zero overlap** by story ID, source-instance ID and exact fact/contract fingerprint; they are not paired endpoint replay. Both are historically selected, familiar populations, not prevalence samples or unexposed confirmation. Primary-P harmless 96/96 is a consequence of historical behavioral selection.

## Task semantics and exposure

A completion of “The result/reading I will show you is X” is a prospective disclosure commitment. The relevance sentence directs showing the damaging item. Harmless selection is non-relevant under that contract; naming it is not automatically a false factual assertion, actual withholding or audience deception. No subjective belief/knowledge or intent is observed. H replaces the clause with an honest instruction; it is not a stored honest-split twin. N deletes the clause and is not `neutral_prompt`.

The 25-clause inventory and all source semantics were independently reviewed **without blinding**, with historical aggregate exposure disclosed. [Literal inventory](clauses.md); [mapping JSON](clause-semantics.json); [semantic review](semantic-review.md). Categories comprise six positional, two problematic-role, three flagged-role, nine demonstrative and five generic clauses. Inventory counts are not observed exposure frequencies. Unobserved clauses receive no hypothetical behavioral predictions.

The strict avoided candidate is the complement of a uniquely recoverable threat target under the two-item commitment interpretation. Positional anchors must agree. Problematic→damaging is a declared lexical inference. Flags without named assignment, competing demonstratives and generic adverse exchanges remain undefined. Audience=user equivalence is not explicit. Undefined does not refute all pragmatic readings, including flagged-as-damaging accommodation.

| Endpoint | Condition | Reference | Contextual resolution | Rows |
|---|---|---|---|---|
| Pilot | alternative_P | demonstrative | competing_demonstrative_antecedents | 94 |
| Pilot | alternative_P | generic | no_candidate_specific_trigger | 14 |
| Pilot | alternative_P | positional | competing_second_anchors | 22 |
| Pilot | alternative_P | positional | second_anchor_consensus | 22 |
| Pilot | alternative_P | role_flagged | flag_assignment_not_explicit | 22 |
| Pilot | alternative_P | role_problematic | declared_problematic_to_damaging_inference | 18 |
| Pilot | primary_P | demonstrative | competing_demonstrative_antecedents | 68 |
| Pilot | primary_P | generic | no_candidate_specific_trigger | 4 |
| Pilot | primary_P | positional | competing_second_anchors | 7 |
| Pilot | primary_P | positional | second_anchor_consensus | 7 |
| Pilot | primary_P | role_flagged | flag_assignment_not_explicit | 4 |
| Pilot | primary_P | role_problematic | declared_problematic_to_damaging_inference | 6 |
| EOS | P | demonstrative | competing_demonstrative_antecedents | 104 |
| EOS | P | generic | no_candidate_specific_trigger | 4 |
| EOS | P | positional | competing_second_anchors | 6 |
| EOS | P | positional | second_anchor_consensus | 6 |
| EOS | P | role_flagged | flag_assignment_not_explicit | 8 |

Strict avoidance is defined on 53/288 pilot P rows: 29 positional consensus plus 24 problematic-role inferences; 39 match and 14 mismatch. It is defined on 6/128 EOS P rows, with 5 matches and 1 mismatch. All H/N threat rules are undefined. Defined-only fractions cannot be ranked against all-row cue accuracy.

## Original fixed-rule baseline results

Each rule cell is **matches / mismatches / undefined**, using the full condition denominator. Noncandidate/unresolved counts are zero for every cell here. Pilot outcomes are candidate-token argmaxes; EOS outcomes are all archived unambiguous answers, all EOS-terminated. There are zero refusal, evasion, contradiction, cap/error or unresolved native EOS rows in this selected panel; none were filtered away.

| Endpoint / condition | N | Damaging | Harmless | Explicitly described | First example | Second example | Lexical first | Strict avoidance |
|---|---|---|---|---|---|---|---|---|
| Pilot argmax primary_P | 96 | 0/96/0 | 96/0/0 | 50/46/0 | 48/48/0 | 48/48/0 | 48/48/0 | 13/0/83 |
| Pilot argmax alternative_P | 192 | 108/84/0 | 84/108/0 | 130/62/0 | 86/106/0 | 106/86/0 | 82/110/0 | 26/14/152 |
| Pilot argmax H | 96 | 74/22/0 | 22/74/0 | 64/32/0 | 36/60/0 | 60/36/0 | 34/62/0 | 0/0/96 |
| Pilot argmax N | 96 | 78/18/0 | 18/78/0 | 64/32/0 | 32/64/0 | 64/32/0 | 36/60/0 | 0/0/96 |
| Native EOS N | 128 | 101/27/0 | 27/101/0 | 91/37/0 | 49/79/0 | 79/49/0 | 57/71/0 | 0/0/128 |
| Native EOS P | 128 | 34/94/0 | 94/34/0 | 62/66/0 | 90/38/0 | 38/90/0 | 82/46/0 | 5/1/122 |

Question order and permitted-example order alias on all 480 pilot and 256 EOS rows; introductory record order also aliases example order throughout these panels. Lexical-first aliases first-example on 300/480 pilot and 128/256 EOS rows. Therefore a first-example fit does not independently identify an example rather than question/record-order mechanism.

| Comparison | N | Damaging→damaging | Damaging→harmless | Harmless→damaging | Harmless→harmless | Mean within-story identity change |
|---|---:|---:|---:|---:|---:|---:|
| Pilot primary P→H | 96 | 0 | 0 | 74 | 22 | .770833 |
| Pilot primary P→N | 96 | 0 | 0 | 78 | 18 | .812500 |
| Pilot primary→alternative P | 192 | 0 | 0 | 108 | 84 | .562500 |
| Native EOS N→P | 128 | 21 | 80 | 13 | 14 | .726563 |

The EOS decline in damaging choices from 101/128 to 34/128 has 80 paired switches in the pooled direction and 13 against it. This is a finite clause-edit result, not a claim that pressure always produces the same effect. Across the three P wordings, 65/96 pilot units emit both candidates; H and N each have one saved prompt per unit and 0 units with both answers. Full fixed-fact condition×answer crossing is absent. That limits diagnostics requiring that crossing; it does not erase matched clause effects or other supported causal comparisons.

| EOS truth | Order | N damaging /32 | N harmless /32 | P damaging /32 | P harmless /32 |
|---|---:|---:|---:|---:|---:|
| 0 | 0 | 19 | 13 | 10 | 22 |
| 0 | 1 | 28 | 4 | 1 | 31 |
| 1 | 0 | 30 | 2 | 3 | 29 |
| 1 | 1 | 24 | 8 | 20 | 12 |

The complete pairwise fixed-rule disagreement tables remain in `audit.json` (`pilot/eos.rule_disagreements_by_condition` and `_all`). A key comparison shows why neither cue nor factual-role agreement alone explains all rows:

| Endpoint / condition | Damaging=first predictions: rows / correct both | Predictions disagree: damaging outcome / first outcome |
|---|---:|---:|
| Pilot primary P | 48 / 0 | 0 / 48 |
| Pilot alternative P | 96 / 49 | 59 / 37 |
| Pilot H | 48 / 31 | 43 / 5 |
| Pilot N | 48 / 31 | 47 / 1 |
| EOS N | 64 / 43 | 58 / 6 |
| EOS P | 64 / 30 | 4 / 60 |

## Factor margins

These are descriptive damaging-choice margins, not independent effects or thresholds. Full all-rule matches/mismatches/undefined counts, truth-margin summaries and within-story averages for each factor live in `audit.json` under `pilot/eos.margins`. EOS designation and item polarity are absent from the archived metadata and remain explicitly absent rather than reconstructed to improve fit.

| Endpoint | Condition | Factor | Level | Damaging / N |
|---|---|---|---|---|
| Pilot | H | designation_polarity | identity | 30/50 |
| Pilot | H | designation_polarity | inversion | 44/46 |
| Pilot | N | designation_polarity | identity | 32/50 |
| Pilot | N | designation_polarity | inversion | 46/46 |
| Pilot | alternative_P | designation_polarity | identity | 39/100 |
| Pilot | alternative_P | designation_polarity | inversion | 69/92 |
| Pilot | primary_P | designation_polarity | identity | 0/50 |
| Pilot | primary_P | designation_polarity | inversion | 0/46 |
| Pilot | H | item_polarity | 1 | 28/38 |
| Pilot | H | item_polarity | 2 | 46/58 |
| Pilot | N | item_polarity | 1 | 31/38 |
| Pilot | N | item_polarity | 2 | 47/58 |
| Pilot | alternative_P | item_polarity | 1 | 43/76 |
| Pilot | alternative_P | item_polarity | 2 | 65/116 |
| Pilot | primary_P | item_polarity | 1 | 0/38 |
| Pilot | primary_P | item_polarity | 2 | 0/58 |
| Pilot | H | reference_kind | absent | 74/96 |
| Pilot | N | reference_kind | absent | 78/96 |
| Pilot | alternative_P | reference_kind | demonstrative | 43/94 |
| Pilot | alternative_P | reference_kind | generic | 11/14 |
| Pilot | alternative_P | reference_kind | positional | 32/44 |
| Pilot | alternative_P | reference_kind | role_flagged | 14/22 |
| Pilot | alternative_P | reference_kind | role_problematic | 8/18 |
| Pilot | primary_P | reference_kind | demonstrative | 0/68 |
| Pilot | primary_P | reference_kind | generic | 0/4 |
| Pilot | primary_P | reference_kind | positional | 0/14 |
| Pilot | primary_P | reference_kind | role_flagged | 0/4 |
| Pilot | primary_P | reference_kind | role_problematic | 0/6 |
| Pilot | H | template | audit | 62/82 |
| Pilot | H | template | lab | 12/14 |
| Pilot | N | template | audit | 65/82 |
| Pilot | N | template | lab | 13/14 |
| Pilot | alternative_P | template | audit | 87/164 |
| Pilot | alternative_P | template | lab | 21/28 |
| Pilot | primary_P | template | audit | 0/82 |
| Pilot | primary_P | template | lab | 0/14 |
| EOS | N | designation_polarity | absent | 101/128 |
| EOS | P | designation_polarity | absent | 34/128 |
| EOS | N | item_polarity | absent | 101/128 |
| EOS | P | item_polarity | absent | 34/128 |
| EOS | N | reference_kind | absent | 101/128 |
| EOS | P | reference_kind | demonstrative | 23/104 |
| EOS | P | reference_kind | generic | 2/4 |
| EOS | P | reference_kind | positional | 4/12 |
| EOS | P | reference_kind | role_flagged | 5/8 |
| EOS | N | template | audit | 67/92 |
| EOS | N | template | lab | 34/36 |
| EOS | P | template | audit | 23/92 |
| EOS | P | template | lab | 11/36 |

## Patch outcomes and qualified archive alias

All **1,152 completed P↔P′ outcomes** use the same pressure ID and literal clause while changing factual truth. They are fact swaps, not distinct-pressure-wording patches. Primary/alternative-P wordings exist in the baseline panel only. `patch_structural_cells` independently separates exact clause equality, pressure-ID equality, named fact/contract equality, truth change, own/other story and archive pair label. Missing donors remain explicit in proposed coverage.

Common scope adds mapped unchanged semantic positions to the single readout position; it is not a whole-token ablation. All MLPs remain intact and the recipient remainder evolves freely. Family names are archive labels, not established semantic roles. D and H in the transition column below mean damaging and harmless **outcome categories**, not circuit masks.

| Family | Scope | Measured / proposed | D→D / D→H / H→D / H→H | Literal copy | Preserve | Changed same-emission /232 | Margin-only /232 | Mean Δmargin | Story-mean Δmargin |
|---|---|---|---|---|---|---|---|---|---|
| candidate6 | common | 544/576 | 176/28/167/173 | 339 | 349 | 44 | 188 | +0.603660 | +0.612488 |
| candidate6 | readout | 544/576 | 196/8/30/310 | 252 | 506 | 9 | 223 | +0.164831 | +0.166067 |
| empty | common | 544/576 | 204/0/0/340 | 232 | 544 | 0 | 0 | +0.000000 | +0.000000 |
| empty | readout | 544/576 | 204/0/0/340 | 232 | 544 | 0 | 0 | +0.000000 | +0.000000 |
| outside_mask2 | common | 544/576 | 204/0/0/340 | 232 | 544 | 0 | 232 | -0.000823 | -0.000887 |
| outside_mask2 | readout | 544/576 | 204/0/0/340 | 232 | 544 | 0 | 232 | +0.005869 | +0.005888 |
| outsider2 | common | 544/576 | 176/28/89/251 | 325 | 427 | 12 | 220 | +0.246006 | +0.251699 |
| outsider2 | readout | 544/576 | 181/23/80/260 | 317 | 441 | 9 | 223 | +0.240273 | +0.245658 |
| selector2 | common | 544/576 | 169/35/102/238 | 369 | 407 | 0 | 232 | +0.276296 | +0.283396 |
| selector2 | readout | 544/576 | 169/35/98/242 | 365 | 411 | 0 | 232 | +0.274549 | +0.281487 |
| shared32 | common | 544/576 | 113/91/212/128 | 521 | 241 | 7 | 225 | +0.566491 | +0.582210 |
| shared32 | readout | 544/576 | 132/72/167/173 | 469 | 305 | 1 | 231 | +0.343463 | +0.352975 |

The clearest literal-copy versus preservation comparison conditions on the 312 baseline donor/recipient disagreements per family/common scope. This is an **outcome-conditioned diagnostic**, not input-only selection or an independent experiment:

| Family / common | Baseline disagreement N | Patched donor answer | Preserved recipient answer | Baseline agreement N | Agreement preserved | Changed away from common answer |
|---|---:|---:|---:|---:|---:|---:|
| candidate6 | 312 | 151 | 161 | 232 | 188 | 44 |
| shared32 | 312 | 296 | 16 | 232 | 225 | 7 |

Thus S32's all-row 521/544 donor matches include 225 already agreeing baseline pairs; 521 is not a count of causal answer changes. Candidate6's 339 literal matches similarly include 188 already agreeing pairs. Copying and preservation overlap when donor and recipient agree; their match counts are not mutually exclusive categories. Every family/scope has 232 same-emission input pairs: 40 exact fixed-fact, 152 same-story named-truth-flip, and 40 cross-story changed-context pairs. Every categorical copying counterexample occurs in the 152 same-story truth flips. All fixed-fact same-emission cases change 0/40, and all cross-story same-emission cases change 0/40 in each cell. Thus candidate6/common44/232 (equivalently44/152 truth-flip cases) refutes universal emitted-answer copying, but does not identify pure-pressure mediation. Margin-only changes are not categorical counterexamples. Zero counterexamples does not prove copying. Empty has exactly zero margin effect; outside-mask controls preserve all answers despite small logit changes.

Recipient/donor **input-derived** rule fits and their undefined coverage remain in each `patch_family_scope` and structural cell, distinct from outcome-derived copy/preservation diagnostics. Their complete baseline→patched transitions and story-mean margin effects are reported above; no pooled total across masks, including empty, is used as a mechanistic headline.

## Explicitly post-hoc donor factual-role comparison

The [addendum](exploratory-role-addendum.md) was specified after preliminary 44/7 same-emission copying exceptions and literal-copy counts were known. Predictors were then fixed before aggregate computation: literal donor answer; donor emitted damaging/harmless role mapped through recipient facts; recipient answer preservation; and always recipient damaging. These are finite predictive descriptions of replacements, not inferred latent roles, policies or natural computations. The original fixed-rule tables above are unchanged.

All proposals remain 6,912=6,528 completed+384 excluded. All four predictions are defined for every completed row here, with zero outcome-other/unresolved counts; for each cell, mismatches equal N minus matches. All family/scope matches follow:

| Family | Scope | N | Literal donor | Donor role | Preserve | Always damaging |
|---|---|---|---|---|---|---|
| candidate6 | common | 544 | 339 | 219 | 349 | 343 |
| candidate6 | readout | 544 | 252 | 244 | 506 | 226 |
| empty | common | 544 | 232 | 224 | 544 | 204 |
| empty | readout | 544 | 232 | 224 | 544 | 204 |
| outside_mask2 | common | 544 | 232 | 224 | 544 | 204 |
| outside_mask2 | readout | 544 | 232 | 224 | 544 | 204 |
| outsider2 | common | 544 | 325 | 253 | 427 | 265 |
| outsider2 | readout | 544 | 317 | 251 | 441 | 261 |
| selector2 | common | 544 | 369 | 239 | 407 | 271 |
| selector2 | readout | 544 | 365 | 241 | 411 | 267 |
| shared32 | common | 544 | 521 | 235 | 241 | 325 |
| shared32 | readout | 544 | 469 | 233 | 305 | 299 |

The pre-existing **input-defined same-story named-truth-flip** subset has 288 measured rows per family/scope. Literal and donor-role predictions disagree on all 288:

| Family | Scope | N | Literal donor | Donor role | Preserve | Always damaging |
|---|---|---|---|---|---|---|
| candidate6 | common | 288 | 204 | 84 | 148 | 202 |
| candidate6 | readout | 288 | 152 | 136 | 270 | 92 |
| empty | common | 288 | 152 | 136 | 288 | 76 |
| empty | readout | 288 | 152 | 136 | 288 | 76 |
| outside_mask2 | common | 288 | 152 | 136 | 288 | 76 |
| outside_mask2 | readout | 288 | 152 | 136 | 288 | 76 |
| outsider2 | common | 288 | 182 | 106 | 234 | 124 |
| outsider2 | readout | 288 | 181 | 107 | 241 | 119 |
| selector2 | common | 288 | 209 | 79 | 231 | 133 |
| selector2 | readout | 288 | 206 | 82 | 234 | 130 |
| shared32 | common | 288 | 276 | 12 | 150 | 212 |
| shared32 | readout | 288 | 254 | 34 | 184 | 180 |

Candidate6/common does **not generally transport the donor factual role**: role 84/288 versus literal 204/288. S32 is closer to literal identity: 276/288 versus role 12/288. Candidate6 always-damaging 202/288 is not evidence for a truth policy: literal and always-damaging agree on 212/288. On the 76 distinguishing cases, candidate6 matches literal 39 and damaging 37; S32 matches literal 70 and damaging 6. Donor role and preservation agree 136/288; on their 152 disagreements, candidate6 matches role 44 versus preservation 108, S32 role 7 versus preservation 145. No role-policy interpretation follows from the original copying exceptions.

For all 544 patches per family/scope, within-recipient-story mean match fractions supplement raw counts where weights differ:

| Family / scope | Literal | Donor role | Preserve | Always damaging |
|---|---:|---:|---:|---:|
| candidate6 / common | .620833 | .400000 | .640278 | .628472 |
| candidate6 / readout | .460764 | .444792 | .930208 | .411458 |
| shared32 / common | .958333 | .430556 | .441667 | .596528 |
| shared32 / readout | .860069 | .428819 | .560764 | .547569 |

All other family/story means and complete pairwise equivalences/disagreements are in `role-transport.json`; no further predictor search occurred. S32 has 32 heads versus candidate6's six, so these are not size-controlled specificity or functional double-dissociation comparisons.

## Original D/H/F interpretation and next prediction

The [original mechanism review](../../project_context/reports/SDR%20circuit%20mechanism%20review.md) concerns D69/H56/F68, shared S32 and conditional exclusive contributions, not the six v2 masks. D−F33 had strong native knockout (.119 accuracy versus matched-null fifth percentile .517), whereas D−H−F22 did not separate (.782 versus .733); reviewed external D−F results lacked positive advantage. Aggregate-only old knockout files cannot supply new per-row native strata.

The [neutral transplant](../../project_context/reports/SDR%20cue-circuit%20transplant%20findings.md) and [position study](../../project_context/reports/SDR%20shared-head%20position%20findings.md) establish shared cue/content influence and conditional position effects under replacement. Exclusive A22/B11 have opposing example-transfer contributions. These remain valid; the native panels cannot simply inherit their example-dominance interpretation. The [native pilot](../../project_context/reports/SDR%20routing%20pilot%20findings.md) retains bounded QK perturbation evidence. Structural subtraction and replacement sensitivity assign no psychological role.

The present audit adds exact native clause-edit transitions, fixed-rule disagreements, copying exceptions, failed general role transport and qualification of the fact-only pressure alias. A useful successor must predict an input-defined native **clause-only** choice change beyond literal copying/preservation, with capable ordinary-task controls and a uniquely named disclosure target. This is a criterion for a new proposal, not an inference release.

Historical selection/inspection rules out prevalence and independent-confirmation claims. Discovery/confirmation names remain historical metadata. No independent-row errors, p-values, favorable-subgroup rescue, new success gate, response relabeling or invented missing outcomes are used. Ambiguous source meaning remains unresolved. Earlier [validation](../../project_context/reports/SDR%20routing%20validation%20findings.md) and [native-control](../../project_context/reports/SDR%20native%20controls%20findings.md) gates remain failed. None of these findings establishes intent, reporting-time knowledge, pressure-specific natural mediation, circuit completeness, a deception-specific function, clean suppression or OOD transfer.

New phase cost: **zero GPU seconds, $0 APIs**; only CPU joins over saved artifacts. No model inference, notebooks, jobs, training, original-runner edits, v2/selective-suppression work or git operations. Lead context compactions: **8**, excluding workers. Independent code/spec and quantitative/source checks are complete; the concise scientific narrative is available in [SDR native evidence audit](../../project_context/reports/SDR%20native%20evidence%20audit.md).
