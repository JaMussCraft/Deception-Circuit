# Final standalone CPU audit code/spec review

2026-10-25. **PASS on both axes; no blocking or material correctness findings.** Review scope is the two new scratch files and their generated table contracts, not production integration or a new scientific confirmation.

Reviewed `code-review-package.md`, complete live source/tests, `spec.md`, `plan.md`, `implementation-brief.md`, `exploratory-role-addendum.md`, `implementation-report.md`, the frozen semantic contract/review, and selected final output structures. The package contains the exact live source text. Independently verified SHA256:

- `audit_native.py`: `86efc95da85042d15382ff4b44c8ebb49436a15c274f290007503626638e982f`
- `test_audit_native.py`: `658ae7a51e50f61e383b3047fc18b51f649437df4f7e29c93333b89ae5e7cdce`

Both match their entries in the final source manifest.

## Standards/code quality — PASS

The implementation is a standalone standard-library analysis with finite explicit inputs and no model imports, jobs, external APIs, notebook execution, or production changes. Validation is concentrated in named helpers; terminal-event interpretation, semantic prediction, aggregation, and the post-hoc extension have distinguishable responsibilities. Scratch-specific counts and source paths are appropriate to the bounded study. No consequential standards violation or refactor needed for correctness was found.

The 21 focused tests exercise plausible analytic errors rather than model behavior: false fixed-fact matches, stale prompt hashes, literal punctuation changes, candidate/lexical order differences, planned-versus-terminal events, duplicate events, missing donors, undefined semantic predictions, all-row denominators, margin-only changes, and role-versus-identity prediction coincidences. Root independently reports fresh 21-test and Ruff passes and a complete CPU rerun with byte-identical fixed audit, role, and support files. This reviewer inspected those tests and checked source/output contracts without redundantly running the model suite.

## Spec compliance — PASS

- **Exact matching and decoding:** `resolve_prompt`/`check_pair` (lines 57/132) preserve literal saved bytes and compare clause-removed prompts, named roles, orders, contracts, and token maps. `metadata_audit` (212) verifies every pilot unit and EOS pair before outcome interpretation. EOS membership comes from frozen input metadata; candidateA/B decoding uses each row's validated candidate list (150, 832).
- **Events and denominators:** `resolve_events` (165) constructs every frozen proposal, rejects duplicate events/terminals, and does not count planned/attempted events as measurements. The archive's 6,912 proposals remain 6,528 completed plus 384 excluded; patch aggregates retain proposal coverage (730). `rule_table` (520) uses matches + mismatches + undefined = all rows, with noncandidate coverage separately counted and within-story descriptive means.
- **Semantic contract and fixed tables:** `semantic_prediction` (445) matches the reviewed hash-pinned contract: problematic-to-damaging inference, positional-anchor consensus, ambiguity abstention, complement selection, and null H/N predictions. Endpoint tables, pair transitions, and missing support remain separate (620/647/692). Clause, pressure-ID, factual-contract, story, and archived-pair distinctions are independently derived; alias equality does not become a distinct-wording claim.
- **Input versus outcome predictors:** original input-rule matches are separate from copying/preservation diagnostics. Actual argmax changes, rather than margin-only shifts, define same-emission copy counterexamples. The exploratory role transport (769/784) is explicitly post hoc and outcome-derived, covers every completed patch, exposes predictor coincidences/disagreements, and separately reports the input-defined same-story named-truth-flip subset. Inspection confirmed all five role table collections satisfy their all-row rule denominators, with 3,456 completed truth-flip rows and all 12 family/scope cells represented.

This review does not independently re-establish every scientific aggregate; the separately assigned scientific checker owns that source-to-result replication. It finds no implementation correction needed before that review and final synthesis. No inference release or stronger identification claim follows from this PASS.

Findings: Standards 0; Spec 0.
