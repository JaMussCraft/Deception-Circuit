# Final-review scoped correction

2026-10-26. **PASS — the sole P2 in final-code-review.md is resolved. No new must-fix defect found in the scoped source correction.** Together with the preceding whole-feature review and task-review-fix1 PASS, this closes the code-review findings on the exact files below. Committed-source binding and actual-wrapper CPU verification remain required before root releases calibration.

## Reviewed identity

Read the complete `implementation/fix-round2/scoped-fix.diff`, the changed producer and actual full-panel regression, surrounding analysis code, snapshot checksums and the final implementation-report addition. Independently verified diff SHA256 `9d3c1aa8f606961e1094470fc08874b591263e4c3526da6c8973b2a9d5a19281`, report SHA256 `3188b71e816683c273a2707704c74b844d8d3b9b9679029a69d7a8706e6229a4`, and current source hashes:

- Runner: `9045b94d4b14c8fd57969ced6617a5541dac09ffbfe4e8f7ceb3ce3fcd33346a`.
- Tests: `1d1b2f073d2cdf85222f0a65bab05c1627bb68502a278b10f66170cc41276495`.
- Unchanged wrapper: `8239a864a4725c3bd4ab15f0d38e50eed22cd9afd931ffc6b801b4d5cf527c8a`.

All three live files also compare byte-for-byte equal to the fix-round2 snapshots. Only the analysis agreement producer and its existing regression changed from the previously reviewed source. No acquisition, intervention, input, protocol-construction or wrapper code changed.

## Resolution and regression

Runner lines685 and691 now require both recipient and donor baselines to be EOS commitments with literal candidates belonging to their respective original two-item sets. Eligible equal names yield true and eligible different names yield false. All other cases yield null. Noncommitments and caps can no longer enter either defined emitted-item agreement stratum merely through nullable equality. Pair rows, candidates, categories, contrasts and direction/story aggregation are retained.

The actual `analyze_panel` regression at test lines344–364 exercises equal commitments, distinct commitments, refusal versus evasion, a capped baseline and a one-sided commitment. It requires exactly `[True, False, None, None, None]`, retains3,936rows/96baselines/192pairs/160arm tables, retains the known raw-margin summaries and independently checks damaging-item source effects and interactions for every pair. This covers the reported defect and guards against converting undefined agreement to false or filtering noncommitments.

Accepted the report's recorded red failure on fix1 and exact fixed-source results: base31passed/1pinned-NNsight skip, mgnp32passed, lint PASS. Already passed suites were not rerun. No tests, git operations, jobs, model execution, notebook execution or production edits were performed by this reviewer.

A fresh search found no production truthiness consumer of this field. The tri-state contract is explicitly documented in the report; future consumers must distinguish `is True`, `is False` and null.

## Postprocessing handoff and remaining release steps

The separately updated independent oracle now requires `baseline_agreement` in its normalized row contract. The runner intentionally publishes the field in `analysis.pairs`, while `normalize` does not duplicate it onto each outcome row. The planned thin oracle adapter must join this pair field by pair_id onto intervention rows and set null for baseline rows before invoking the oracle. This handoff was sent to root; it is not a defect in this scoped two-line source repair or a request to broaden the acquisition patch. The independent oracle changes were not otherwise reviewed here.

Skipping another provisional cache freeze/wrapper repeat for this analysis-only correction is reasonable. Prior provisional manifests bind older source and cannot serve as the final execution freeze. Root must commit these exact reviewed bytes, rebind the unchanged scientific payload to committed source, obtain the independent binding audit and run the actual original wrapper's CPU checks before explicit calibration release. Real BF16/A100 numerical and timing checks remain calibration obligations. This code-review PASS is not itself a GPU release.
