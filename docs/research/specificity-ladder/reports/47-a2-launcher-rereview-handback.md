# A2 launcher re-review handback

Agent: Codex independent reviewer. Status: handed-back.

## What changed

Verdict: the abbreviated-stage blocker from report `44-a2-preflight-review-handback.md` is resolved. No remaining blocker was found in this narrow re-review.

Both the wrapper stage pre-parser and its main parser now set `allow_abbrev=False`; the standalone projection parser does too. An abbreviated stage option is therefore left unconsumed and rejected instead of changing dispatch. The exact shell prohibition on explicit stage override remains effective.

The actual-launcher regression executes the shell script with a CPU-only interpreter shim. The shim stubs plan creation, execution, and projection, and records a marker if either execution or projection is reached. All eight abbreviated option forms reject before that marker is created, including split and equals forms targeting run and project. Three exact-stage tests preserve the intended dry-run, run, and project dispatch. The projection CLI cases retain matching ruling behavior through both entry points. Counts: `/tmp/a2-launcher-rereview-pvxif_0t/review-evidence.json`.

Only these report files were written:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/47-a2-launcher-rereview-handback.md`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/47-a2-launcher-rereview-handback.md`.

Reviewed code and test source hashes are recorded in `/tmp/a2-launcher-rereview-pvxif_0t/review-evidence.json`. The author handback was not read.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -B -m pytest -p no:cacheprovider -q tests/test_twin_training_wrapper.py tests/test_twin_training_projection.py -k 'actual_launcher_rejects_abbreviated_stage or exact_stage_names_keep_their_dispatch or cli_offline_json_gate'
```

Observed: 21 passed, 147 deselected; exit 0. Evidence: `/tmp/a2-launcher-rereview-pvxif_0t/review-evidence.json`.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -p no:cacheprovider -q tests/test_twin_training_wrapper.py tests/test_twin_training_projection.py -k 'actual_launcher_rejects_abbreviated_stage or exact_stage_names_keep_their_dispatch or cli_offline_json_gate'
```

Observed: 21 passed, 147 deselected; exit 0. Evidence: `/tmp/a2-launcher-rereview-pvxif_0t/review-evidence.json`.

```bash
env -u DC_PYTHON -u SLURM_JOB_ID bash scripts/jobs/specificity_twin_training.sh --dry-run --config scripts/jobs/specificity_ladder_a2.json --build-manifest outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json --task far_v2 --condition D --seed 42 --receipt /tmp/a2-launcher-rereview-pvxif_0t/unused-receipt.json
```

Observed: exact normal launcher dry-run passed after actual environment activation, exit 0, expected FAR cohort retained, no receipt created. Evidence: `/tmp/a2-launcher-rereview-pvxif_0t/normal-dry-run.stdout.log` and `/tmp/a2-launcher-rereview-pvxif_0t/review-evidence.json`. This tested the current parser with the real approved data and default activation path.

## Execution evidence

Local CPU tests and a dry-run preflight only; exit statuses and counts are above. Test dispatch uses stubs and creates no scientific training child. No model, GPU, paid API, Slurm submission, notebook, git command, or delegated agent was used. Scientific rows, baseline reproduction, and scientific run manifest are not applicable; no scientific result is claimed.

Live weekly usage was 13 percent spent and 87 percent remaining, below the 80 percent cap; reset reported as 2026-11-06T16:07:41+00:00. Evidence: `/tmp/a2-launcher-rereview-pvxif_0t/review-evidence.json`.

## What is NOT done

The full focused suites were not repeated because this review is limited to parser dispatch and launcher behavior. The source, cohort, registry, timing, and budget logic previously reviewed in report `44-a2-preflight-review-handback.md` was not re-audited. No production launch or reservation was performed or authorized by this review.

## Open questions

None blocking. Default: the orchestrator may proceed with the corrected launcher under the existing allocation, usage, timing, cohort, protected-set, and phase-budget gates.
