# V4 independent preproduction review

October 21, 2026. **PASS for code freeze and the approved baseline/calibration stage. No blocking findings remain.** Production still requires root review of actual calibration, runtime estimates, frozen receipts and reservation evidence. This is a code/spec review, not a measured GPU result.

Reviewed proposal105, the v4 implementation plan and scheduling-only execution amendment; the trainer/CLI patch against8830e4d; new optimization_v4 launcher and pair scripts plus their sbatch wrappers/tests; and optimization_v4_summary with its tests. Read shared project guidance and relevant selective-deception memory. Applied the surgical-change and verifiable-success criteria from karpathy-guidelines. No pretrained models, notebooks, GPU jobs or submissions were used by this reviewer. No implementation files were edited.

## Scientific contract

The new policy restricts the contrast to all1024/W/rho0/seed0/3072updates/checkpoint64, with initial expected removals1 or10. Eight SDR pairs per update, row schedule, gate-noise seeding, constant AdamW lr.03, unit objective coefficients, hard stochastic straight-through training and binary exports are preserved. The original initialization primitive already implements the required log((N-k)/k), so it did not need modification. Legacy policy settings and cache-sharing behavior remain unchanged; legacy CLI initialization changes are rejected.

Initialization and horizon enter manifest/settings/optimizer identities and checkpoint fingerprints. V4 baseline fingerprints retain the manifest/amendment, forcing separate initialization-specific SDR/WT references. Baseline reports bind init, manifest and actual source hash before bootstrap can derive the disposable calibration receipt. Train/validation remain the only prepared reference splits. No historical native/test outcomes enter finalist selection.

Calibration profiles only the invocation's all/W initialization and3072 horizon. It checks measured initial expected count, finite/nonzero candidate gradients, export equivalence, state restoration and exact full-vocabulary/reference comparisons for v4. Actual evidence must pass separately for both initializations; passing these CPU tests does not establish that GPU calibration will pass or fit15minutes.

## Execution and analysis

The scheduling amendment preserves the fourGPUhour production ceiling through two manually separated twoGPU/60minute allocations. The pair launcher requires root stage authorization, currentHEAD/source/immutable-receipt bindings, exactly two arms, and single-use claims. Continuation additionally binds each latest checkpoint's path/SHA and a prior terminal-state claim; root must verify actual Slurm state. It never submits, retries or resumes automatically. Original training receipts remain unchanged.

The trainer atomically saves gates, optimizer, complete cursor and Python/NumPy/Torch/CUDA RNG after each completed update, using a flushed/fsynced temporary file and replacement. An interrupted unfinished update can replay from the previous completed checkpoint. Exact resume fingerprints prevent cross-policy/init/horizon/source migration. The corrected tiny-model test verifies uninterrupted versus resumed optimizer/RNG payload equality.

The analyzer requires both complete3072-update/48-validation runs before proposing any finalist. Partial/invalid grids have no proposal, including when one arm finishes. It audits source/model/cache/checkpoint identities, update coverage, binary mask reconstruction, paired H losses/gains and expected-removal consistency. Selection preserves prospective90/95 rungs, joint-H/WT and WT-only tiers, deterministic ties, mask deduplication and at most two proposals; all outputs remain provisional until root freeze. Expected stochastic removals are explicitly distinguished from realized sampled counts and deterministic exports. Reused validation supports exploratory optimization conclusions only.

## Verification and resolved finding

- Reviewer executed the new wrapper/pair/analyzer tests together in base: **61passed** (5.59s).
- Reviewer executed the new trainer test file in base: initially **28passed,1failed**. The newly added exact-resume fixture supplied an empty WT manifest, suppressing block construction and passing None to the W update. Reported immediately to the trainer/root. Worker corrected only the fixture to a truthy manifest; reviewed the fix and final logs: **29passed base** (22.04s), **29passed mgnp** (19.43s). No production-code defect was implicated.
- Worker evidence reviewed: selected pre-edit trainer baseline85passed; selected regression111passed in each environment before the final three tests; wrapper/pair35passed in each environment; analyzer26passed in each environment. Reports106–108 give commands and scope.
- Full base trainer suite:1556passed/77skipped/seven known unrelated failures, as recorded in report107. Full mgnp result was still pending at this review. Broad scratch collection is not clean: report106 records225passed/13failed/twoerrors from historical evaluation-module import collisions; focused new suites pass independently. No blanket full-suite-success claim is made.

## Remaining operational gates

Root must freeze runtime source and separately record scratch launcher/analyzer hashes, prepare the actual two manifests/receipts, execute actual wrapper dry-runs and scheduler preflight, and audit both numerical/runtime calibration results before production. Runtime source inventory intentionally covers repository runtime files rather than scratch orchestration. Root must audit checkpoints and actual terminal Slurm state before authorizing segment2; budget or walltime failure does not authorize automatic extra segments. Real-artifact analyzer execution remains necessary after both fits complete. These are planned execution gates, not unresolved implementation findings.
