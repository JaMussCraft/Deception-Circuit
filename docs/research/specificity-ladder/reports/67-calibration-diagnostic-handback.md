# Hand-back: Calibration geometry diagnostic (ticket 67)

Agent: Codex worker. Status: handed-back.

## What changed

Files for the orchestrator to commit from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/tools/67-calibration-diagnostic.py`: standalone diagnostic extending the production score CLI with `--result-dir`, `--job-stdout`, and `--job-stderr`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_calibration_diagnostic_67.py`: CPU geometry, finite evidence, injected failure, ordering and dry-run tests.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/67-calibration-diagnostic-handback.md`: this report.

No production hooks, runner or pipeline were changed. No frozen maps or data were changed. No git commands were run.

The script reuses production parent, selection sidecar, source/code/grader/registry validators, then revalidates the cached tokenizer against every prepared prompt. It requires the original task order, four-ID pilot limit, batch size eight, and full supplied production commit `0253f494af007f93b2a00cb1e63cb3cdf1a8b519`. It separately hashes its own source; no claim is made that this new diagnostic belongs to that production commit.

Its pair generator mirrors the production condition/stream/parent-batch/singleton order and the original readout-only positive-calibration maps. It captures all sender keys including embeddings, without a READOUT_KEY shortcut. The original recovery check retains `atol=rtol=1e-5`. At the first original donor-logit failure it stops scanning and compares that pair at a common maximum parent width and a common maximum unpadded width. Resizing retains unmasked tokens and absolute readouts, strips only masked suffixes and never truncates actual tokens.

Every completed pair reports fp32/native donor-logit errors, final and per-layer residual errors, exact padded tokens/masks/readouts, task/condition/ID/stream, and empty/self-replay controls on both inputs. The geometry comparisons additionally report donor and recipient fp32/native/residual drift against the original geometry. Control mismatches are data rather than an exception. JSON uses finite errors or nulls plus nonfinite counts. A pair-start event precedes GPU work; exceptions retain context and a traceback. Events are flushed and fsynced incrementally. Distinct `run_manifest.json`, `pairs.jsonl`, and `summary.json` files identify independent job stdout/stderr/result paths.

## How verified

From the worktree:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_calibration_diagnostic_67.py -q -p no:cacheprovider
```

Observed: five tests passed. Injected fake geometry drift fails the original donor-logit test and passes common-width replay; this is a plumbing test, not empirical evidence about the real model. The dry-run test forbids weight loading and JSON writes and checks that the requested result directory is absent.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_calibration_diagnostic_67.py -q -p no:cacheprovider
```

Observed: five tests passed; one existing pandas/bottleneck version warning. No tests skipped.

Real frozen-input CPU dry-run (stdout captured externally; the script wrote no artifacts):

```bash
HF_HOME=/work/nvme/beto/swong2 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python docs/research/specificity-ladder/tools/67-calibration-diagnostic.py --stage score --artifact-root /projects/beto/swong2/Alignment/Deception-Circuit --data-root data/datasets --user-control-root outputs/_analyses/specificity-ladder/a1-control-77b6487-m07 --work-dir outputs/_analyses/specificity-ladder/ladder-0253f49-pilot --design outputs/_analyses/specificity-ladder/ladder-0253f49/design.json --groups outputs/_analyses/specificity-ladder/ladder-0253f49/selected.json --tasks far_v2 sdr_v2 ser_v2 --commit 0253f494af007f93b2a00cb1e63cb3cdf1a8b519 --limit 4 --batch-size 8 --result-dir /tmp/calibration67-dry-no-write --job-stdout logs/lad-a1-diag67-JOBID.out --job-stderr logs/lad-a1-diag67-JOBID.err --dry-run > /tmp/calibration67-dry-run.json
```

Observed: exit zero; 120 pairs in `/tmp/calibration67-dry-run.json`; requested result directory absent. First pair is FAR D clean ID `0061d53229dc`: recipient padded width 98, donor corrupt padded width 101, both unpadded width 97 and readout 96, as recorded in `/tmp/calibration67-dry-run.json`. This is input-geometry evidence only. No logits were computed. The orchestrator accepted output-only dry-run path differences and will substitute the final result directory and real Slurm log paths. Diagnostic source SHA256 is `6e25e23a69a92a2bc9c8cbfedd20596fda15ce1b959b154258251c00e13ec016`.

## Execution evidence

No new GPU job was submitted or executed by this worker. The real-model geometry hypothesis is not yet verified; GPU evidence and baseline reproduction remain missing. Local CPU tests above use synthetic inputs, with the injected fake drift explicitly labeled in the tests. They do not create a scientific run manifest.

The reported production failure to reproduce is job `23415975` on Delta, recorded in `logs/lad-a1-pilot-23415975.err`, whose stderr ends in donor-logit recovery maximum error `0.041628360748291016`. That number is taken from the existing log, not reproduced by this worker. The orchestrator must check it against the diagnostic original-pair result and report both numbers, state/exit, actual pairs observed against inventory, and the new run manifest before drawing an empirical conclusion.

## What is NOT done

- No GPU submission, model-weight load on login, API call, notebook execution, or candidate scientific scoring.
- No production fix and no tolerance change.
- No claim that equal-width geometry resolves the real failure or that BF16 shape drift caused it.
- No utility calibration scans: the script diagnoses only the mechanism positive-calibration path where the supplied job failed.

## Open questions

The orchestrator owns the single bounded Slurm GPU run and its reservation. Reuse the original production score arguments, replace the entry point with this script, append independent result/stdout/stderr paths, and run `--dry-run` first. The script refuses real execution without a Slurm CUDA allocation. The script returns zero when it successfully diagnoses an original failure; inspect `summary.json.status` and the recovery/noop booleans rather than interpreting exit zero as a calibration pass.

If the original pair fails again, compare its fp32 maximum error against the supplied failure value, then inspect common-width donor residual recovery, fp32 logits, native logits and both no-op controls. Equal-width success would isolate a geometry dependency on this pair; it would still require a separately reviewed production fix and fresh scientific scoring. If no original pair fails, retain the complete inventory/results and investigate remaining environment differences instead of changing the tolerance.
