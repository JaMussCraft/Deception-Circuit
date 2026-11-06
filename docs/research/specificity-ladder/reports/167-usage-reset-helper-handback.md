# Hand-back 167: usage reset helper successor

Agent: Terra worker. Status: handed-back. Independent review is required before any operational use.

## What changed

New successor directory: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/root-model-phase-release-helper/r5`. Its `manifest.json` SHA-256 is `67d7ff0345b268f508a75f636224c0bef9f8e109f2e7f87fbaad972e73174a89`; `helper.py` is `35959ca0f1d20b0140d2c2d18f080cc2b7283f26e7219e166fb1331db24c698c`. Manifest lists every file hash, including focused tests, ruling, and raw logs. The r5 ruling marks copied r4 documentation and static results as historical, not r5 acceptance.

Only `validate_usage` differs from predecessor helper. The new expired post-reset route requires a below-80 live reading, explicit expired state, positive integer reset epochs, ordered timezone-aware timestamps, and live observation at most 60 seconds old. Matching-reset behavior and projected checkpoint arithmetic are retained; unknown exception states fail closed. Receipt telemetry identifies route, epochs, timestamps, ages, counters and absence of exception authority. Live reset is never hardcoded.

## How verified

All commands below ran in the r5 directory. RED was captured before implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m unittest -v test_usage_reset > red-base.log 2>&1
```

Exit 1: one unittest with 37 matrix subcases, seven errors. Five are the expected predecessor reset-mismatch rejection of legitimate new-route cases; two are absent route telemetry on matching-route cases. There were no setup or import errors. `red-base.log` captures the original matrix-only test, before additional tests were added.

```bash
PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m unittest -v test_usage_reset test_helper test_cache_gate > green-base.log 2>&1
```

Exit 0: 46 tests, including the 37-case matrix and additional adversarial and mocked actual `usage()` call-order/raw-reading tests; 0.063 seconds.

```bash
PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m unittest -v test_usage_reset test_helper test_cache_gate > green-mgnp.log 2>&1
```

Exit 0: the same 46 tests; 0.079 seconds. Matrix cases use `subTest`, so the 37 cases are not included individually in the unittest count.

A Python byte-content comparison found the entire helper outside `validate_usage` identical to r4, and rehashed all nine r4 manifest members successfully. The original r4 manifest remains `959b5987ea6bc22bd3d6cedcd07bc15a56edf72838d79f320c9548e5c3f02efc`.

## Execution evidence

Local pure unit tests only; no Slurm job or scientific model run. The base RED exited 1; base and mgnp GREEN exited 0 as above. Scientific output rows and baseline reproduction are not applicable. Provenance is the r5 `manifest.json` named above, binding the approved design manifest `fcb21328f139b540de690c66c074283139c25489b6f249dfb3d375cb049dd5ce` and predecessor manifest; this new uncommitted operational helper has no source commit to report.

## What is NOT done

Independent source review, operational binding, live release, scheduler action, remote operation, git, private usage changes, and RS state writes were not performed. Fixture equivalence grants no model or release admission. The previous handback's statement that there were no runs was inaccurate: the RED local unittest did run, as documented here.

## Open questions

Root should obtain independent review of the exact r5 manifest and bind any future support continuation before use. Default: hold operational use pending that review and current usage, scheduler, and support gates.
