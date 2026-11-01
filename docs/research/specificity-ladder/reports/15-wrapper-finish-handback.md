# A2 wrapper completion hand-back

Status: handed-back

`Task 2` implementation is complete for lead review. Resumed the existing checkpoint without rebuilding prior work. No worker git commands.

## What changed

- `scripts/twin_training.py` supports both direct-script and module launch by resolving the repository import path. It retains the frozen heads-plus-MLP command, identical D/I settings, explicit disabled fine/edge gates, deterministic matched prefixes, timing-only separation, and the allocation requirement.
- Prelaunch checks now authenticate the manifest's canonical build hash and compare both private D/I configurations for task, recipient condition, corruption kind, cohort readiness, source commit, maximum length, complete ordered split IDs, and original split counts. Both configuration file hashes enter the plan/receipt. Provisional builds check D only. Source model identities accept the registry alias or its actual canonical Hub identifier.
- Successful child exits must also produce complete epoch history, a periodic validation event, nonempty baseline/node evaluations with matching model/task/seed, valid model-range head/MLP indices, and a valid native manifest/config/dataset-configuration hash. Supplied orchestrator commit provenance is added only after those checks.
- `tests/test_twin_training_wrapper.py` adds assertion-level regression coverage, actual `train.py` parser/resolved-config integration without invoking training, actual materializer-output integration, and real short CPU child processes for artifact checks. `scripts/jobs/specificity_ladder_a2.json` retains the existing frozen settings unchanged.

## How verified

All commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder` using escalated execution because the default sandbox cannot initialize its temporary directory.

The direct-launch subprocess test first failed with `ModuleNotFoundError: No module named 'config'`; the module-entry and actual-parser tests passed. After the import fix, all selected entry/parser tests passed. Private-build consistency cases first failed because inconsistent builds were accepted; semantic-artifact cases first failed because incomplete outputs were accepted. Their implementations then passed the wrapper suite. Canonical Hub-model acceptance also had a failing test before its fix.

Final focused commands and exact observed summaries:

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_wrapper.py tests/test_twin_training.py -p no:cacheprovider -q
103 passed in 131.20s (0:02:11)

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training_wrapper.py tests/test_twin_training.py -p no:cacheprovider -q
103 passed, 2 warnings in 131.45s (0:02:11)
```

The base warnings were the existing pandas bottleneck-version warning and the `TRANSFORMERS_CACHE` deprecation warning. No failures. No broader suite was run: the task is an isolated wrapper and the assigned plan calls for focused checks unless a shared-behavior concern remains.

Separate actual dry-run commands against synthetic materializer output:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 scripts/twin_training.py --config scripts/jobs/specificity_ladder_a2.json --build-manifest /tmp/a2-wrapper-finish-check/materialized/build_manifest.json --task far_v2 --condition D --seed 42 --timing-epochs 20 --receipt /tmp/a2-wrapper-finish-check/receipt.json

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m scripts.twin_training --config scripts/jobs/specificity_ladder_a2.json --build-manifest /tmp/a2-wrapper-finish-check/materialized/build_manifest.json --task far_v2 --condition D --seed 42 --timing-epochs 20 --receipt /tmp/a2-wrapper-finish-check/receipt.json
```

Both exited successfully. Retained stdout plans are `/tmp/a2-wrapper-finish-check/direct-dry-run.json` and `/tmp/a2-wrapper-finish-check/module-dry-run.json`. A separate assertion compared their argv apart from the interpreter and their selected IDs, and checked that neither the requested receipt nor the planned training directory existed. Observed dry-run fields:

```json
{"purpose":"timing-only","fleet_ready":false,"counts":{"train":1,"validation":1,"test":1},"max_seq_length":30,"actual_epochs":20,"planned_epochs":500,"selected_ids":{"train":["train-1"],"validation":["validation-1"],"test":["test-1"]},"train_under_200_requires_lead_review":true}
```

The existing frozen configuration in `scripts/jobs/specificity_ladder_a2.json` sets the scientific settings; the smaller epoch count above applies only to the synthetic timing plan. Actual parser integration resolves the full command and compares it with the wrapper's expected persisted configuration. CPU subprocess dry-run tests cover both launch forms on each interpreter with an empty `PYTHONPATH`, assert no writes, and check that synthetic credentials do not appear in the plan.

## Execution evidence

No scientific or GPU run occurred. No job ID or cluster applies; allocation enforcement was exercised by the CPU test that removes the Slurm job ID and obtains a failed receipt before any child launch. No real allocation/hardware path was exercised.

The retained synthetic child receipt is `/tmp/a2-wrapper-receipt-check-p20jx12p/receipt.json`; its associated `run_manifest.json` is under the receipt's recorded output directory. Its observed fields were:

```json
{"status":"success","exit_code":0,"total_seconds":1200.0,"pruning_seconds":600.0,"test_runner_injected":true}
```

Those durations use an injected clock and printed fake timing; they are test values, never a pilot measurement or an allocation estimate. The synthetic private rows observed against expected were one per train/validation/test split, as shown in the dry-run fields above. The synthetic baseline and node evaluation values were `1.0` and `0.9`; no model baseline reproduction is claimed. The supplied source commit was the fixture value `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, explicitly synthetic provenance. Environment checks found only allowlisted keys in the receipt and neither of the synthetic credential values. Native manifest rehashing and supplied-commit injection were also asserted by the focused tests.

## What is NOT done

- No pilot, training/model load, GPU/API call, Slurm submission, notebook execution, or worker git operation.
- `Task 3` projection and its CLI stage are outside this assignment; the wrapper continues to accept only dry-run/run.
- No fleet reservation approval or scientific seed result. A timing mask remains timing-only, even on matched data.
- No independent external review yet. The lead should review the owned files before a real allocation.
- Prelaunch consistency checks inspect private configuration metadata, ordered IDs, and hashes; they do not reload Arrow rows or rerun tokenizer/behavioral admission. Those checks belong to the materializer. Native training provenance later records dataset-file hashes.
- An actual materializer run must receive the lead-supplied full source commit. The synthetic commit and tiny data used here must never be used as production provenance or timing coverage.

## Open questions

No blocking schema conflict remains. The current materializer schema is used directly without edits to its implementation. The lead owns independent review, full commit provenance, any allocation, and the separate projection task. Existing under-cap training cohorts remain prominently flagged for lead review before fleet launch.

Live usage at the completion checkpoint was `6%` spent with `94%` remaining and `should_pause:false`; reset is `2026-11-06T16:07:41+00:00`.
