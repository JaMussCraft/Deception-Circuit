# Projection Unicode compatibility fix hand-back

## What changed

Added `build_digest` in `scripts/twin_training_projection.py` using the materializer's canonical JSON convention, including `ensure_ascii=False`. Only build-hash validation now calls that function. Existing wrapper and receipt digest conventions remain unchanged. No global hash migration occurred.

Added a regression in `tests/test_twin_training_projection.py` with an em dash in source metadata. It independently computes the materializer's build hash, demonstrates acceptance of the valid manifest and original wrapper receipt hash, and demonstrates rejection of a receipt hash incorrectly changed to the materializer convention.

## How verified

Before implementation, the new Unicode regression failed with `ValueError: build hash mismatch`; the existing tests passed. The captured red output is `/tmp/a2-projection-unicode-red.log`.

After implementation, each focused suite passed 49 tests with exit code zero. The count is supported by `/tmp/a2-projection-unicode-mgnp.log` and `/tmp/a2-projection-unicode-base.log`.

```bash
OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_projection.py -p no:cacheprovider -q
OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training_projection.py -p no:cacheprovider -q
```

Read the wrapper's final injected-clock interface. Custom clocks now set `test_runner_injected` as well as `test_clock_injected`; the existing projection rejection still applies. No wrapper edit was needed.

## Execution evidence

This task ran local CPU tests only. Job ID and cluster: not applicable. Training exit state: not applicable. Scientific rows against expected: not applicable. Scientific baseline reproduction: not applicable. Scientific `run_manifest.json` and commit provenance: not applicable because no scientific run occurred. Synthetic timing fixtures remain test data and provide no measured runtime evidence.

Both focused suite processes exited successfully. Their logs are cited above. No GPU/API use, notebooks, git, job submission, training execution or ledger mutation occurred.

## What is NOT done

No under-count lead-ruling override, conservative bound override, pilot measurement or fleet approval was added. The existing under-count limitation remains documented in `22-projection-handback.md`. No files outside the projection module, its owning test file and this worktree report were edited.

This follow-up report is written and linted in the worktree only. The orchestrator will mirror it to the primary research directory; this agent did not repeat the previously rejected cross-checkout copy.

## Open questions

No implementation blocker remains for the scoped Unicode finding. The orchestrator may request the reviewer's targeted rereview and mirror this report. A real pilot and matched complete measurement coverage remain prerequisites for any fleet recommendation.
