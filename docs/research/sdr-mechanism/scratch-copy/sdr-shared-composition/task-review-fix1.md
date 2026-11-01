# Shared-composition scoped fix review

2026-10-26. **PASS — both P2 findings in task-review.md are resolved; no new must-fix defect found in the scoped changes.** Independent Codex Sol review of the frozen fix round1. This closes the task-review findings; the planned whole-change review, committed-source rebind and real-model calibration remain separate release steps.

## Reviewed identity and scope

Read `implementation/fix-round1/scoped-fix.diff` and its surrounding unchanged integration code, new regression tests and the final implementation report. Independently verified diff SHA256 `953c75dd039bc8c1fe34652853cea57dd834ee4515c9c11d03b3416211aaffdb`; all scoped snapshots and current worktree files match these fixed hashes:

- Runner: `d18c0ae989e386a1c637a4d7234b4a557d5083cf09bcbc9c080785244bd027b6`.
- Tests: `0c0da3ef07fe29e0ee35820bffea28f192261ae77a93e77eef96138b63d3126c`.
- Unchanged wrapper: `8239a864a4725c3bd4ab15f0d38e50eed22cd9afd931ffc6b801b4d5cf527c8a`.

Only the two requested numerical-evidence repairs and associated tests/accounting changed. No old source/helper, scientific arm/input, map, model setting, behavioral gate or calibration-resume policy was changed. No code/git/job/model/notebook operation or test rerun was performed by this reviewer.

## Finding1 resolved: failure evidence and attempt context

Runner lines213–227 now save the active control/step, row IDs, physical readouts, input/attention hashes and capture/replacement keys before model execution. Finite/geometry rejection retains actual/expected shape, dtype, finite flag, offending nonfinite physical slots and observed vector hashes in structured failure state.

Lines241–256 compute comparison diagnostics locally and append each receipt into the current attempt's sink before raising. The failed slot and earlier successful slots from the same control survive with row/physical slot/control/step, geometry/finite/bitwise/argmax/max-error fields and both vector hashes. The bounded raw exception remains separately retained by the existing failure publisher.

Current attempt state is initialized at line566 before setup/publication. Setup diagnostics use that state. A new group's setup failure therefore has the current batch context and empty decode rows rather than the preceding accepted arm's rows. The failure still raises ValueError, has resumable=false, produces no accepted terminal for the failed arm and fails hard-failure resume verification.

The new end-to-end fake-forward regressions exercise the actual run loop, setup, decoder and failure publisher: a late finite repeat mismatch after a token with successful prior-slot receipt; nonfinite and geometry rejection with exact active context; and a second-group setup failure after a preceding accepted group. These directly cover the original defect without requiring production model weights.

## Finding2 resolved: donor and U5 capture agreement

Runner lines272–280 retain the natural donor capture readout and freely evolving U5 receiver-capture readout, then compare each with its independent readout-only forward on identical B8/L224 IDs/attention masks. The U5 control uses the exact same mapped source-only U5 bank. This is the equivalent independent source-only control accepted in the original finding; it requires no receiver remapping or prolonged tensor lifetime across arm decoding.

Named `setup_donor_readout` and `setup_U5_readout` receipts use full FP32 vocabulary comparison, maximum error≤1e−5 and identical argmax, and persist in successful setup artifacts or current failure state before stopping. Existing recipient repeat/empty/self controls remain. Distinct regressions inject drift only on each capture path while ordinary readouts/repeats remain consistent; both stop with the correctly named failed full-vector receipt and no accepted arm. A matching-path regression verifies both controls and their vector hashes persist.

## Timing/accounting integration

Setup now executes five internal forwards: three natural captures plus two independent donor/U5 readouts. The three existing recipient repeat/empty/self forwards make **eight actual setup forwards per group**. The next-group guard charges **nine cold allowances**: eight setup calls plus one decoder cold allowance, alongside the unchanged67baseline/129patched warm decode-call budget. The new matching setup test verifies eight measured calls.

Added forwards, context hashing and comparison work are inside the measured forward/setup/decode elapsed paths. Setup runtime survives in accepted first-arm state, and `calibration_forecast` now includes the observed setup maximum when selecting its cold-forward bound. A regression checks a5.0second setup maximum is not lost behind a0.2second decoder maximum. No whole-panel worst-case stop was introduced. The earlier requirement to verify the guard's fixed10second nonforward allowance during real calibration remains an operational check, not a new code finding.

## Final evidence

Read the finalized implementation report and independently verified SHA256 `30e4f0052f4b7df3e9066ed5be64e97f59ee97d664f1eed69b84d58066015d2e`. Its exact-source results are:

- Base:31passed/1pinned-NNsight skip in15.25seconds.
- mgnp:32passed in28.63seconds, including the existing actual tiny Llama/NNsight natural-propagation test.
- Ruff F and shell syntax:PASS.

Already passed tests were not rerun. The report records red evidence against the prior implementation for the failure, setup-agreement and cold-bound regressions.

Independently verified v3 provisional freeze source hashes and equality of its entire scientific payload to v2. Scientific hash remains `1a29813fea112f713b66a673619afa25687a70527d832323159c92e9c4364412`;96inputs/192pairs/492batches are unchanged. V3 manifest hash is `67689e8ad232734d531ef484a5ae1b288c20030a65705d5c0543595bb025df72`.

Read the actual absolute-wrapper v3 CPU dry-run receipt `implementation/fix-round1/wrapper-cpu-dry-run.json` and independently verified SHA256 `2b33e2b1ddf137e7c201d0706279be9be5f897e6688642a295a2bb38f37d346b`:exit0, matching manifest,3,936science rows/492batches,180calibration rows/23batches, model_loaded=false, output_mutated=false, destination absent.

This PASS is for the two scoped repairs and resulting task-review readiness. The freeze remains UNCOMMITTED. Root's final commit binding/whole-change review/wrapper closure and the actual BF16/A100 numerical/runtime calibration are still required before scientific acquisition.
