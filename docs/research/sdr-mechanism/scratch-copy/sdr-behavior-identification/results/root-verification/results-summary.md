# Bounded native SDR audit results

Retrospective selected-population audit; endpoints remain separate.

| Endpoint/condition | N | Damaging | Harmless | First example | Lexical first | Avoidance matches / N; undefined |
|---|---:|---:|---:|---:|---:|---:|
| Pilot argmax H | 96 | 74 | 22 | 36 | 34 | 0 / 96; 96 undefined |
| Pilot argmax N | 96 | 78 | 18 | 32 | 36 | 0 / 96; 96 undefined |
| Pilot argmax alternative_P | 192 | 108 | 84 | 86 | 82 | 26 / 192; 152 undefined |
| Pilot argmax primary_P | 96 | 0 | 96 | 48 | 48 | 13 / 96; 83 undefined |
| Native EOS N | 128 | 101 | 27 | 49 | 57 | 0 / 128; 128 undefined |
| Native EOS P | 128 | 34 | 94 | 90 | 82 | 5 / 128; 122 undefined |

Support: {'both_answers_within_P': 65, 'both_answers_within_H': 0, 'both_answers_within_N': 0, 'full_condition_answer_crossing': 0}

Transitions: [{"comparison": "N_to_P", "endpoint": "native_EOS", "n": 21, "source_category": "damaging", "target_category": "damaging"}, {"comparison": "N_to_P", "endpoint": "native_EOS", "n": 80, "source_category": "damaging", "target_category": "harmless"}, {"comparison": "N_to_P", "endpoint": "native_EOS", "n": 13, "source_category": "harmless", "target_category": "damaging"}, {"comparison": "N_to_P", "endpoint": "native_EOS", "n": 14, "source_category": "harmless", "target_category": "harmless"}, {"comparison": "P_to_H", "endpoint": "pilot_argmax", "n": 74, "source_category": "harmless", "target_category": "damaging"}, {"comparison": "P_to_H", "endpoint": "pilot_argmax", "n": 22, "source_category": "harmless", "target_category": "harmless"}, {"comparison": "P_to_N", "endpoint": "pilot_argmax", "n": 78, "source_category": "harmless", "target_category": "damaging"}, {"comparison": "P_to_N", "endpoint": "pilot_argmax", "n": 18, "source_category": "harmless", "target_category": "harmless"}, {"comparison": "P_to_alternative_P", "endpoint": "pilot_argmax", "n": 108, "source_category": "harmless", "target_category": "damaging"}, {"comparison": "P_to_alternative_P", "endpoint": "pilot_argmax", "n": 84, "source_category": "harmless", "target_category": "harmless"}]

The 1,152 archived P↔P′ patch rows are same-clause/same-pressure-ID factual swaps. No distinct-pressure-wording effect is inferred.
Cross-panel overlap by story, source-instance ID, and exact fact/contract fingerprint: {'story_id': 0, 'source_instance_id': 0, 'fact_contract_hash': 0}.

| Family | Scope | Completed / proposed | Output changes | Same-output-input cases | Actual copy counterexamples | Same-output margin-only shifts | Mean truth-margin change |
|---|---|---:|---:|---:|---:|---:|---:|
| candidate6 | common | 544 / 576 | 195 | 232 | 44 | 188 | 0.603660 |
| candidate6 | readout | 544 / 576 | 38 | 232 | 9 | 223 | 0.164831 |
| empty | common | 544 / 576 | 0 | 232 | 0 | 0 | 0.000000 |
| empty | readout | 544 / 576 | 0 | 232 | 0 | 0 | 0.000000 |
| outside_mask2 | common | 544 / 576 | 0 | 232 | 0 | 232 | -0.000823 |
| outside_mask2 | readout | 544 / 576 | 0 | 232 | 0 | 232 | 0.005869 |
| outsider2 | common | 544 / 576 | 117 | 232 | 12 | 220 | 0.246006 |
| outsider2 | readout | 544 / 576 | 103 | 232 | 9 | 223 | 0.240273 |
| selector2 | common | 544 / 576 | 137 | 232 | 0 | 232 | 0.276296 |
| selector2 | readout | 544 / 576 | 133 | 232 | 0 | 232 | 0.274549 |
| shared32 | common | 544 / 576 | 303 | 232 | 7 | 225 | 0.566491 |
| shared32 | readout | 544 / 576 | 239 | 232 | 1 | 231 | 0.343463 |

Every proposal remains in coverage; excluded donors have no fabricated measurement. Rules use all-row matches/mismatches/undefined counts. `audit.json` contains rule disagreements, category/factor margins, within-story means, and patch cells split by exact clause/facts/ID/alias. Row-level joins and missing support are in adjacent JSONL/JSON files.

Retrospective historically behavior-selected populations, not prevalence or independent confirmation.
First-token argmax and EOS labels are separate endpoints in disjoint panels.
Prospective showing commitments do not establish false factual assertion, realized withholding, intent, audience belief, or reporting-time knowledge.
Undefined strict avoidance leaves pragmatic consequence-sensitive alternatives open.
Missing condition-answer crossing limits only diagnostics requiring that crossing.
Scheduled P↔P′ aliases all retain the identical pressure clause and change facts.
Patch copying/preservation are outcome-derived diagnostics; emitted-answer strata are descriptive.

## Exploratory post-hoc role transport

Root proposed after seeing preliminary same-emission counterexamples candidate6/common44/232 and shared32/common7/232, and literal-copy counts. Independent critic accepted this bounded diagnostic before aggregate computation. It is outcome-derived, not original-library or independent confirmation.

All 6,912 proposals remain visible: 6,528 completed, 384 excluded. The following table covers completed patches; the four predictors are literal donor identity, donor factual role mapped into recipient facts, recipient preservation, and always recipient damaging.

| Family | Scope | N | Literal donor | Donor factual role | Recipient preservation | Recipient damaging |
|---|---|---:|---:|---:|---:|---:|
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

The separately tabulated input-defined same-story named-truth-flip subset contains 3456 completed patches. `role-transport.json` includes all predictor mismatches/undefined counts, pairwise equivalences/disagreements, exact-clause/fact/story cells and within-story means. Agreement may coincide with recipient preservation or always-damaging; it does not uniquely identify role encoding.
