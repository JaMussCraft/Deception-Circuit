# V5 independent adapter/core review — 2026-10-24

Verdict: PASS for mask/cohort adapters. Runtime cache enforcement findings are tracked separately in report151; this does not authorize execution. Reviewed report148, accepted plan, source and actual prepared JSON artifacts. No historical source was modified; no model weights/API/GPU/notebook/git used. Tiny randomly initialized CPU model only.

## Actual consumer and fixed masks

The historical coarse run's real `config.json['node_config']` enables attention blocks, heads, neurons, MLP hidden/output, and disables MLP blocks/full layers/embedding. The directory's `noan_nomh_nomo` name does not describe the current serialized gate layout. Independently built the tiny consumer with that exact node_config, applied a whole-head mask's finest complement through `analysis.apply_node_masks`, and compared every extracted gate against the intended mask: PASS. Selected attention-neuron leaves are zero; all MLP leaves and unselected head support remain open. The implementation's strict gate-layout application fails rather than silently dropping mismatched masks.

Frozen support binds old69/new23/new30 to the original receipt, source JSON/export and checkpoint byte hashes. Checkpoints are hashed, never deserialized. Old ungated `active_mlps` is deliberately ignored. Random30 is one fixed per-layer sample over all 32 query heads, with target overlap allowed, using seed20261024. Four removals plus intact are the runtime's five states.

## Actual cohort and lineage

Independently loaded every real dataset through `load_fixed_cohort` (including source-hash checks), and compared every retained recipient's donor to its original full-row partner mapping: **371 exact matches** across the retained cohort. Exact two corrected MASK D exclusions leave171 MASK, alongside150 LB and50 sandbagging, without replacement. Saved full labels/verdicts, generations, metadata/beliefs, row positions and reasons remain in the audit. New masked outputs do not affect eligibility.

Runtime inspection confirms fresh intact and used-donor generations with all gates open, preserving frozen recipient beliefs. Missing donor beliefs are not reconstructed or judged. Historical A40 selection and new execution are separate provenance fields; this is a historical cohort pilot with fresh intact baseline, not a pristine holdout or v4 donor-replay protocol. Unused original reference pools are explicitly unrecovered.

The two named cache sources preserve their hashes and originals. Import follows within-file last-write semantics, with differing cross-file keys excluded. Report148 accurately records52 differing LB duplicate occurrences and0 cross-source conflicts. Of323 original paid-request keys,81 imported hits/242 misses and80 different cached text strings demonstrate why this must not be described as recovery of a unique original judgment. Eligibility uses saved full-row verdicts; prospective reuse follows the frozen import policy.

## Independent verification and bindings

Mask/cohort/budget focused tests combined: **43 passed in mgnp and43 passed in base** (base has only the three documented environment warnings). Adapter-specific tests comprise31 of these43. Actual-source consumer/mapping checks above passed independently of synthetic fixtures.

Reviewed SHA256:

| File | SHA256 |
|---|---|
|evaluation/frozen_head_masks.py|7d808f4238528c7751d9bf511337142119ea51817f3bc634836cec36b2b03c3b|
|evaluation/fixed_benchmark_cohort.py|4730ed4f8314bdce94bc1450fdf0fee8e8dd948edcbdefe250e47f457b4b8b49|
|tests/test_frozen_head_masks.py|10a2c9bc598725d023978b732c3cdc069c70378cdc0ece088a917779c8e8ba58|
|tests/test_fixed_benchmark_cohort.py|6da1733d9ea6c2330b0e8eedf0ea327fe790d93e442e3c1f3b670d9d791ba661|
|fixed-cohort.json|f9d49fe6c014a8a07e29bc02e8b1bf2fd94a554c240d416a329c12242371b74f|
|frozen-masks.json|69999255f3d5bebf363ecc3d8659f9ebcc6f0bb3ad70cebda9d78925eac33fb6|

## Final cache receipt refresh

Importer now records and validates `imported_bytes` with the immutable byte-prefix SHA256, permitting appended runtime rows. Independent new prefix tests: **6 passed in each environment**. Actual regenerated cohort loader and runtime `validate_study_cache` both PASS against the real imported cache (5,982,474 bytes). Cohort content, counts, donor mapping and imported cache bytes are unchanged apart from the additional receipt/source binding. Final superseding SHA256: importer `25183765aa4dccb2f1a1226a662fe1b3a933a208e6eb11cdf862398b6fd8cd43`; cohort tests `a162b1c939eb6e69c42b7576bb2dd009ed5c171066d9793ad4b3c6d675b2aff9`; fixed-cohort.json `99add00302460c8df9775177d6d283c3ca10906a1af05d1334bf8cfca052f57e`; imported cache `c1a4c31f3113c029c77700c7f728d3398b32b32f9c2516eb5939b53e19acea42`. Final adapter verdict remains **PASS**.
