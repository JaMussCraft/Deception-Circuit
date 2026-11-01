# Scientific design review

2026-10-25. Reviewer: independent behavior-identification critic. Reviewed `spec.md`, `plan.md`, and `reusable-evidence.md`, plus literal pressure pools and the archived pilot's prompt/comparison construction and one completed event. No code or model execution, jobs, notebooks, APIs, git operations, source edits, or other-study changes.

**Status: PASS, no remaining blocking design findings.** Both narrow precision fixes and the inventory/exposure clarification below were incorporated by the designer and independently re-read in the final spec and plan. These fixes do not add a data population, evaluation, model call, or new study.

## Precision fixes verified

1. **Classify pressure identity independently of the archived pair label.** Archived `pressure_pair(a,b)` returns `P↔P′` whenever both conditions are P. The fixed patch plan includes primary-P clean/corrupt truth swaps using the same pressure clause, so this label does not mean a pressure wording changed. Join recipient/donor input rows and report same/changed exact clause text and pressure ID, separately from truth/fact changes. Preserve the raw label only as metadata/alias. Otherwise the central support table can manufacture a pressure-change comparison from a content-only intervention.
2. **Apply the same matching audit to the EOS pairs.** The spec explicitly builds 96 pilot fixed-fact keys, but also calls 128 EOS P/N pairs fixed. Verify named facts, item ordering, task/response contract, and exact expected clause-only change for each EOS pair before interpreting transitions. Decode candidateA/B through each row's `candidates`; do not equate these labels with item1/2. Report cross-panel overlap at story/source-ID and actual fact/contract levels, rather than treating an ID match as a paired endpoint replay.

A useful small clarification is to separate the 25-clause inventory from actual observed exposures. Unobserved inventory clauses cannot acquire an output match or context-specific target from a hypothetical rendering. Mark the contextual prediction unobserved/undefined unless a frozen prompt is available.

## Scientific assessment

The finite JSON-only scope is sufficient for this retrospective question. Mandatory Arrow reconstruction, fresh behavioral assays, broader causal grids, or a new capability gate would add cost without being necessary to identify the saved support. The audit can add concrete evidence: exact missing pressure/answer cells at fixed facts; corrected pressure-label aliases; rule disagreements and undefined coverage; source-clause exposure and ambiguity; endpoint-specific cue matches; and terminal-event coverage with outcome-derived copying separated from input-derived rules.

The design correctly avoids claiming independent confirmation or prevalence. Original deceptive rows were behavior-selected; constructed H means honest-instruction replacement, not a row from the original honest split; N is clause deletion, not `neutral_prompt`; pooled truth/story crossing is not full fixed-fact condition×answer support. Full completions and first-token argmax remain separate endpoints in separate populations, with overlap to be checked rather than assumed.

Denominators are appropriately explicit: 480 pilot variants, 96 units, 192 primary/alternative-P pairs, 6912 proposed family/scope rows with completed versus excluded results, and 256 native EOS responses/128 pairs. The implementation must reconstruct these counts from actual records rather than assert them as constants. Duplicate terminal events must fail linkage; planned/attempted copies are not repeated measurements. Undefined rules and noncandidate/unresolved outcomes remain in all-row accounting. No response relabeling, responsive-only filtering, or favorable-subgroup rescue is authorized.

The semantic limits are correct. Disclosure commitments are not automatically false factual assertions; literal threat referents require context; generic adverse clauses may not identify a candidate to avoid. Separate-prompt retrieval does not establish reporting-time belief. The design can refute specified deterministic accounts in this finite panel and identify observational equivalence or absent support. It cannot establish deceptive intent, pressure-specific natural mediation, circuit removal, selective suppression, or generalization.

## Release condition

The two precision edits above are incorporated and verified in the final spec/plan; the design is appropriate to release for scratch-only CPU implementation. This is a design review, not verification of future audit outputs and not a GPU release. Independent final review should check a few actual semantic contexts, one baseline join, an EOS identity/pair match, a mislabeled same-pressure P/P event, and the count/coverage tables; no giant recursive receipt framework is needed.
