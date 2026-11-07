# Hand-back: Positive-calibration common-width padding (ticket 69)

Agent: Codex worker. Status: handed-back.

## What changed

Files for the orchestrator to commit from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/specificity_ladder.py`: positive-control singleton inputs now right-pad to the maximum of their original padded widths before any intact, donor or patched capture. Existing donor-logit `atol=rtol=1e-5` remains unchanged.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_specificity_ladder_calibration.py`: geometry-boundary regression, preservation checks and invalid-input rejection tests.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_specificity_ladder_model.py`: real CPU tiny-Llama test of common-width donor native/fp32 full-logit and final-residual recovery plus recipient/donor empty/self-replay controls.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/69-calibration-fix-handback.md`: this report, mirrored to the same relative path in the primary checkout.

The padding helper accepts only validated singleton geometry and integer token/readout tensors. It preserves existing tokens, padding, masks, dtypes, devices, absolute readouts, labels and provenance references. New right-padding consists of zero-valued tokens with zero attention mask. It refuses truncation, noninteger widths, malformed masks/readouts, unsupported token/readout tensor types and nonsingleton input. Original batches are not mutated.

No production pipeline, generic hooks, scientific `score_cell` geometry, frozen artifacts, scientific IDs or thresholds changed. No READOUT_KEY shortcut was added. Diagnostic source `67-calibration-diagnostic.py` remains at SHA256 `6e25e23a69a92a2bc9c8cbfedd20596fda15ce1b959b154258251c00e13ec016`. New runner source SHA256 is `93a22eb6b51cf6ea081b37dd354179cd56aa89def6bb50337b40fc2937b9170e`.

## How verified

Tests were written before the implementation. The synthetic boundary regression failed against the original production function with donor recovery error `0.009999990463256836`; the real tiny-Llama boundary test independently failed because the first recipient capture still had width `128` instead of `129`. These are regression-contract tests, not an attempt to reproduce the real BF16 GPU drift on CPU. Fail-first outputs are `/tmp/calibration69-red.log` and `/tmp/calibration69-tiny-red.log`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_specificity_ladder_calibration.py::test_positive_calibration_aligns_128_129_before_any_capture -q -p no:cacheprovider
```

Observed before implementation: one failed test, donor-logit recovery exception; see `/tmp/calibration69-red.log`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_specificity_ladder_model.py::test_positive_control_128_129_recovers_donor_and_noops_on_common_shape -q -p no:cacheprovider
```

Observed before implementation: one failed test, unexpected first-capture shape; see `/tmp/calibration69-tiny-red.log`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_specificity_ladder.py tests/test_specificity_ladder_calibration.py tests/test_specificity_ladder_model.py tests/test_specificity_ladder_cli.py tests/test_calibration_diagnostic_67.py -q -p no:cacheprovider
```

Observed after implementation: 118 passed, no skips or failures, exit zero; `/tmp/calibration69-scoped-mgnp.log`. This includes the real tiny-Llama test with native hooks, donor full-vocabulary readout recovery, final-residual recovery and all no-op checks. The earlier focused calibration/model run passed all tests too; `/tmp/calibration69-focused-mgnp.log`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_specificity_ladder.py tests/test_specificity_ladder_calibration.py tests/test_specificity_ladder_model.py tests/test_specificity_ladder_cli.py tests/test_calibration_diagnostic_67.py -q -rs -p no:cacheprovider
```

Observed after implementation: 105 passed, two dependency skips, exit zero; `/tmp/calibration69-scoped-base.log`. Explicit skip reasons are quoted below from that log.

```text
SKIPPED [1] tests/test_specificity_ladder_model.py:5: nnsight 0.5.12 installed; pinned 0.7.0 required
SKIPPED [1] tests/test_specificity_ladder_cli.py:182: pinned nnsight 0.7.0 required
```

## Execution evidence

This worker submitted no GPU job. The evidence motivating the fix is the orchestrator's completed diagnostic, inspected directly in its artifacts and Slurm accounting:

- Job and cluster: `23416716`, Delta, NVIDIA A100-SXM4-40GB, BF16. Accounting command `sacct -j 23416716 --format=JobID,State,ExitCode,ElapsedRaw,AllocTRES --parsable2 --noheader` returned `COMPLETED`, exit `0:0`, elapsed `254` seconds for the job and batch step.
- Pair counts: 105 original pairs observed against 120 planned; the script deliberately stopped at the first failure, ordinal 104, recorded in `outputs/_analyses/specificity-ladder/calibration-diagnostic-0253f49/summary.json`. This is not a complete pilot pass.
- Baseline reproduces: original diagnostic donor-logit maximum error `0.041628360748291016` against pilot error `0.041628360748291016` in `logs/lad-a1-pilot-23415975.err`. Exact equality is recorded in `outputs/_analyses/specificity-ladder/calibration-diagnostic-0253f49/pairs.jsonl` at the original event for the failed pair.
- Failed pair: SER, condition I, clean stream, ID `00b809b51070`; original recipient/donor padded widths `128/129`, identical unpadded lengths `128` and readouts `127`. Original native-logit error `0.0625` and final-residual error `0.25`; the common-parent-width `129/129` and common-unpadded-width `128/128` alternatives each have fp32/native/final-residual error `0.0`. All recipient/donor empty/self-replay checks pass in all geometries, recorded in `outputs/_analyses/specificity-ladder/calibration-diagnostic-0253f49/pairs.jsonl`.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/calibration-diagnostic-0253f49/run_manifest.json`, supplied production commit `0253f494af007f93b2a00cb1e63cb3cdf1a8b519`, plus separately recorded diagnostic source hash above. Raw logs are `logs/lad-caldiag-23416716.out` and `logs/lad-caldiag-23416716.err`.

These artifacts isolate a padding-geometry dependency for that one failing pair under the recorded environment. They do not establish the exact responsible GPU kernel or complete scientific scoring. The production fix itself has only CPU test evidence so far.

## What is NOT done

- No GPU submission, large-model load, API calls, git commands, notebooks or subagents by this worker.
- No candidate scientific scoring or full positive-calibration pilot under the modified production source.
- No production changes outside positive calibration. Broader repository suites were not run, following the orchestrator's explicit scoped verification instruction.
- No silent migration of frozen provenance. The source hash changed intentionally; existing prepared/selected artifacts must remain immutable and fail stale-code guards. The orchestrator owns explicit reprepare/reselection under a new full commit before real production scoring.
- No claim that every possible shape mismatch is repaired on every model/backend; only one real failed pair has been isolated.

## Open questions

The orchestrator should review and commit the narrow source/test changes, regenerate prepared and selected artifacts with fresh provenance under that commit, then run the bounded production pilot. Default: preserve original artifacts and diagnostic outputs, retain existing tolerances, and block scientific conclusions on any remaining calibration or no-op failure. No additional change to scientific scoring geometry is proposed.
