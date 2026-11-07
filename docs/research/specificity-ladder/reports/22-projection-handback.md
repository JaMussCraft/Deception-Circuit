# Projection gate hand-back

## What changed

Created `scripts/twin_training_projection.py` and `tests/test_twin_training_projection.py` in the specificity-ladder worktree. The pure `project_reserved` function and standalone module CLI consume receipts and return a conditional reservation recommendation without launching training or writing a ledger.

The gate freezes the complete task, condition and seed product. It estimates full-process duration as fixed startup/finalization plus epoch-scaled pruning, buffers each allocation, rounds upward to whole minutes, and adds explicit positive aggregate pilot reservations. The unbuffered single-mask trigger directs a separate heads-only measurement. Training margin and historical dataset screening thresholds are reported separately.

The lead explicitly allowed timing reuse across seeds of the same task and condition. Each projected cell names its source receipt and reuse status. The largest comparable measured duration is used. No timing is transferred between tasks, conditions, builds, shapes, hardware or granularities. D-only estimates remain provisional.

The input plan contains `config`, `build_manifest`, `hardware` and `source_hashes`, with optional `granularity`. Hardware specifies exact `gpu_devices`, `gpu_count` and `cluster`. The CLI infers that conditional hardware from an eligible receipt and computes expected source hashes from current local sources. The module imports only the wrapper's pure standard-library configuration parser and gate constants; it never calls execution helpers.

## How verified

The final focused suite produced 48 passes on each required interpreter, with both process exit codes zero. This count is derived from the pytest output observed in the agent transcript. Commands:

```bash
OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_projection.py -p no:cacheprovider -q
OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training_projection.py -p no:cacheprovider -q
```

Tests first failed when the module was absent. Additional tests exposed acceptance of changed resolved configuration, missing argv, omitted gate flags, zero pilot reservation, and a total just above the phase cap. Those cases now block. Other tests cover arithmetic, upward rounding, the exact cap, the exact single-mask boundary, missing conditions or planned seeds, invalid timing/buffer values, injected or failed receipts, missing hashes, shape/hardware changes, provisional data, seed-only reuse, and distinct heads-only measurements. The CLI test consumes synthetic fixture files and observes no file creation.

The worktree report passed research-session lint and the strict report-number check. Automatic approval review rejected copying the report into the primary checkout as outside delegated worktree ownership; the parent was asked to perform that copy and primary lint. No retry bypassed the rejection.

The parent requested only focused suites for this ownership scope; the full repository suite was not run. No existing wrapper, materializer, configuration or test files were edited.

## Execution evidence

This hand-back reports CPU software checks only. Job ID and cluster: not applicable. GPU training exit state: not applicable. Observed scientific rows against expected: not applicable. Baseline reproduction numbers: not applicable. Scientific `run_manifest.json` and full run commit: not applicable because no scientific run occurred. Every timing fixture is synthetic and is explicitly labeled as a test, never a measured pilot.

The live Codex usage command returned `weekly.used_percent: 8`, `weekly.remaining_percent: 92`, `should_pause: false`, and reset `2026-11-06T16:07:41+00:00` at the hand-back checkpoint. No GPU/API spend, job submission, notebook execution, git command or ledger mutation occurred.

## What is NOT done

No actual pilot has been measured, and no fleet reservation is approved by this hand-back. The synthetic arithmetic cannot size a scientific fleet. A conservative first pilot proposal is a single H200 allocation capped at one GPU-hour, running the wrapper's timing-only mode at full selected counts and the longest known common padded length. The lead must choose a built task/condition, inspect current ledger headroom, and authorize/submit it separately. A timeout or failed pilot still consumes its full reserved cost and supplies no timing estimate. A D-only pilot cannot cover I or any other task.

Explicit lead-recorded conservative bounds are unsupported. No tiny-row extrapolation, inter-task or inter-condition reuse, model/hardware migration, partial scientific seed promotion, scheduler integration, ledger reconciliation, artifact reloading, or automatic heads-only launch is implemented. Heads-only projection accepts only separately measured heads-only receipt coverage; the current wrapper's production of that distinct plan remains outside this task's files.

The pure function trusts the wrapper's success/artifact-check assertions after checking hashes, resolved argv and provenance. It does not independently reopen artifacts. Original receipt JSON and source files must be preserved. Missing/invalid plan provenance raises an input error; CLI input errors return a hold recommendation. Invalid supplied receipts are reported and conservatively prevent approval, even if other receipts cover the same cells; callers can select usable receipts while retaining all pilot costs in the explicit aggregate reservation input. Training cohorts below the preferred count require lead review and remain blocked here.

## Open questions

No schema question blocks the implementation. The lead should review the policy of blocking approval when any supplied receipt is invalid; failed costs remain charged even when unusable receipts are excluded from projection input. Before a future real pilot, ensure clock-only test injection receives the wrapper's injected-test marker as well as injected runners. Without that marker, the pure projection cannot discover an externally injected synthetic clock.

The first pilot's actual timings, complete comparable coverage, A1 matched build, and ledger reservation total remain required before fleet approval. The module exposes no bound override or under-count review override.
