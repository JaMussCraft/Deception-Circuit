# Wrapper review fixes hand-back

Status: handed-back

Both blockers in `reports/19-wrapper-review-handback.md` are addressed in the assigned wrapper, frozen configuration, and tests. No materializer implementation or output-contract change was needed.

## What changed

- `scripts/jobs/specificity_ladder_a2.json` now freezes `deception_margin_loss: 0.7`; `scripts/twin_training.py` passes explicit `--deception-margin-loss 0.7`, converts it to a float in expected configuration, rejects a changed frozen value, and checks the persisted artifact value. Historical source screening thresholds are untouched.
- Before returning a run plan, the wrapper lazily loads the saved private Arrow datasets on CPU and compares complete split counts, complete ordered IDs, and the selected prefixes with the manifest. Both D and I are checked for matched builds; provisional data checks D.
- The wrapper authenticates the original recipient and donor sources using their recorded complete file maps, content hashes, and row hashes. It checks private source provenance against the manifest, then compares retained source rows with those authoritative rows. Training target/distractor and clean/reference prompts must match the actual original recipient/donor. Prompt hashes must agree with the private configuration's token proofs; orientation, corruption metadata, and donor identity must also agree. It does not rerun a tokenizer or behavioral filter.
- The tests use real Arrow datasets and current provenance shapes, while keeping source datasets independent from saved private rows. Stale-data regressions include changed ID, order outside the selected prefix, full count, clean prompt, reference prompt, target, distractor, forged retained labels, forged prompt proofs, and a changed authoritative source file. Existing launcher, receipt, allocation, and artifact tests remain covered.

## How verified

All commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder` with escalated execution because the default sandbox cannot initialize its temporary directory.

Test-first evidence: all margin regressions initially failed because the command omitted the override, the output mismatch was accepted, and a changed frozen value was accepted. After the margin fix, the actual parser/loss resolver resolved historical D/I screening values `0.7/0.5` to training values `0.7/0.7`; the historical values remained unchanged. The stale Arrow cases initially all failed because `plan_run` accepted changed data. Their failing output is retained at `/tmp/a2-wrapper-stale-red.log`; the targeted passing output is `/tmp/a2-wrapper-stale-green.log`.

Final affected-suite commands and exact summaries:

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_wrapper.py -p no:cacheprovider -q > /tmp/a2-wrapper-fix-mgnp.log 2>&1
49 passed in 60.73s (0:01:00)

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training_wrapper.py -p no:cacheprovider -q > /tmp/a2-wrapper-fix-base.log 2>&1
49 passed, 1 warning in 66.09s (0:01:06)
```

Both exited successfully. The base warning is the existing pandas bottleneck-version warning. The full materializer suite was not repeated, per the scoped review-fix assignment. The affected suite still exercises the actual materializer's D-only output contract and both subprocess entry points.

Repeated actual dry-run commands after the fixes:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 scripts/twin_training.py --config scripts/jobs/specificity_ladder_a2.json --build-manifest /tmp/a2-wrapper-finish-check/materialized/build_manifest.json --task far_v2 --condition D --seed 42 --timing-epochs 20 --receipt /tmp/a2-wrapper-finish-check/receipt.json > /tmp/a2-wrapper-finish-check/direct-fix-dry-run.json

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m scripts.twin_training --config scripts/jobs/specificity_ladder_a2.json --build-manifest /tmp/a2-wrapper-finish-check/materialized/build_manifest.json --task far_v2 --condition D --seed 42 --timing-epochs 20 --receipt /tmp/a2-wrapper-finish-check/receipt.json > /tmp/a2-wrapper-finish-check/module-fix-dry-run.json
```

Both exited successfully. An independent assertion compared their argv apart from the interpreter, checked the explicit margin, and checked that neither the requested receipt nor the planned training directory existed. The dry-run data remain synthetic, provisional, and timing-only.

The reviewer's exact preserved fixture `/tmp/a2-wrapper-review-stale-8hxss75s`, using the original build manifest and current frozen configuration, now raises:

```text
ValueError: stored split id/order mismatch: D/train
```

This directly closes the acceptance reproduced in `/tmp/a2-wrapper-review-stale-repro.log`.

Clock-injection follow-up: a custom clock initially failed the new regression because its failed allocation receipt had no test-evidence marker; explicit `time.monotonic` and the default clock passed. The wrapper now sets `test_runner_injected:true` for either an injected runner or a clock whose identity differs from `time.monotonic`, and additionally records `test_clock_injected`. These fields are set before allocation checks. Default and explicitly supplied `time.monotonic` remain ordinary execution. The existing projection rejection field is preserved. No real training or hardware call was needed.

Only the covering tests were rerun after this narrow change:

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_wrapper.py -k 'clock_only_injection or run_receipts_and_whole_process_clock' -p no:cacheprovider -q > /tmp/a2-wrapper-clock-mgnp.log 2>&1
8 passed, 44 deselected in 11.68s

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training_wrapper.py -k 'clock_only_injection or run_receipts_and_whole_process_clock' -p no:cacheprovider -q > /tmp/a2-wrapper-clock-base.log 2>&1
8 passed, 44 deselected, 1 warning in 13.91s
```

Both commands exited successfully; base emitted the existing bottleneck-version warning. The red output is `/tmp/a2-wrapper-clock-red.log`. The clock-only regression removes the allocation ID, obtains a failed receipt, and checks that a custom clock still sets both test-evidence flags. Existing injected-runner success/failure/missing-artifact/config-mismatch/stale-output clock tests also passed.

## Execution evidence

No scientific or GPU run occurred; job ID and cluster do not apply. Both focused test commands and both dry-run commands exited successfully. The suite completed `49/49` tests in each interpreter. The synthetic stored-row fixture contains `205/3/4` full train/validation/test rows and selects `200/3/4`; the order mutation swaps rows outside the selected training prefix, so the check covers the complete stored cohort. The actual dry-run materializer fixture contains the expected `1/1/1` rows and remains `fleet_ready:false`.

No model baseline reproduction is claimed. No new scientific `run_manifest.json` exists. Synthetic child receipt/artifact tests still pass, including rejection of a persisted training margin `0.5` when the command expects `0.7`. Fixture source commit `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` is deliberately synthetic and cannot serve as scientific provenance.

The live usage reading at hand-back was `7%` used, `93%` remaining, and `should_pause:false`, with reset `2026-11-06T16:07:41+00:00`.

## What is NOT done

No real training, model/tokenizer load, GPU/API use, Slurm submission, notebook execution, git command, or subagent. No materializer changes. The separate projection task remains outside this assignment. Source authentication and stored-row checks add CPU I/O to dry-run and prelaunch planning; they do not establish scientific performance or timing coverage.

The lead still owns independent review, full real commit provenance, actual allocation, and any future pilot or fleet decision.

## Open questions

No blocking schema conflict remains. The existing manifest source paths/hashes and private token proofs were sufficient; no compact output-proof extension was necessary. Default: review the three owned implementation/configuration/test files and this hand-back before authorizing a pilot.
