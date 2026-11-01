# A2 preflight review handback

Agent: Codex independent reviewer. Status: handed-back.

## What changed

Verdict: hold the new launcher until the abbreviated-stage override is fixed. No other blocking issue was found in the reviewed delta.

Review scope: the root-provided delta `/tmp/specificity-a2-preflight-review.diff` against commit `9835e17`, the current wrapper/projection modules and focused tests, the new launcher, and the approved plan/ruling. The author report was not read. This review changed only these handback files:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/44-a2-preflight-review-handback.md`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/44-a2-preflight-review-handback.md`.

**Blocking finding: abbreviated stage options bypass the launcher dry-run guard.** The launcher rejects only `--stage` and `--stage=*`, while both argument parsers in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/twin_training.py` accept argparse abbreviations. Consequently `--dry-run --sta run` changes the selected Python stage to run. The shell has already skipped its allocation guard because its own stage is dry-run. The Python allocation and hardware guards still prevent training on a login node, but inside an allocation with a supplied execution commit the nominal dry-run can launch training. This violates the launcher’s explicit prohibition on stage override.

Reproduction below deliberately omits the execution commit, guaranteeing that the wrapper refuses before reading the dataset or launching a training child. Observed stderr ends with `ValueError: full execution commit required for run`, proving run-stage dispatch rather than dry-run dispatch. Evidence: `/tmp/a2-review-launcher-o7dmvqv0/abbreviated-stage.stderr.log`.

```bash
DC_PYTHON=/sw/external/python/anaconda3/bin/python3.9 bash scripts/jobs/specificity_twin_training.sh --dry-run --sta run --config scripts/jobs/specificity_ladder_a2.json --build-manifest outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json --task far_v2 --condition D --seed 42 --receipt /tmp/a2-review-unused-abbrev.json
```

Recommended correction: disable abbreviations in both the stage pre-parser and main parser, or reject all stage aliases before dispatch; add launcher regression cases for abbreviated stage options. Disabling abbreviations in the pre-parser alone is insufficient if the main parser still accepts them. Do not supply a commit to the unsafe reproduction.

The other reviewed requirements are satisfied by the inspected implementation and CPU tests:

- The explicit ruling binds the exact build hash, ordered selected-ID digest, complete integer count map, matched status, condition order, scope, and selection rule. No ruling keeps the cohort review hold; malformed, mismatching, stale, and missing ruling paths fail closed. The ruling clears only cohort review and preserves timing, budget, coverage, receipt, and hardware gates. Its digest remains visible with the under-size status. This validates an explicitly supplied ruling; it does not authenticate its author.
- Wrapper `--stage project` delegates to the standalone projection parser, preserving ruling and execution-revision behavior. Execution commit is separately required for real execution and recorded independently from the data build source commit. Native manifest augmentation retains native fields, adds both revisions, and updates its hash. Projection rejects missing, foreign, or mixed execution revisions.
- Both primary and worktree protected registries are read during planning and again immediately before the training child. Missing/malformed registries, invalid protected IDs, path escape, missing referenced files, bad hashes/counts, and relevant ID overlap refuse. The refreshed registry byte hashes are retained. Task-scoped nonoverlapping sets remain permitted.
- Actual default Delta environment activation succeeded through the new shell launcher. The launcher exports offline model/dataset settings, disables native git collection, and pins host math threads. A missing allocation refuses before environment activation; an exact stage override refuses too. The abbreviated option remains the exception described above.

## How verified

Both focused commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -B -m pytest -p no:cacheprovider -q tests/test_twin_training_projection.py tests/test_twin_training_wrapper.py
```

Observed: 157 passed, exit 0. The base environment emitted its pandas/bottleneck version warning. Count evidence: `/tmp/a2-review-launcher-o7dmvqv0/review-evidence.json`.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -p no:cacheprovider -q tests/test_twin_training_projection.py tests/test_twin_training_wrapper.py
```

Observed: 157 passed, exit 0. Count evidence: `/tmp/a2-review-launcher-o7dmvqv0/review-evidence.json`.

```bash
bash -n scripts/jobs/specificity_twin_training.sh
```

Observed: syntax check passed.

```bash
env -u SLURM_JOB_ID bash scripts/jobs/specificity_twin_training.sh
```

Observed: allocation refusal, exit 1. Count evidence: `/tmp/a2-review-launcher-o7dmvqv0/review-evidence.json`.

```bash
bash scripts/jobs/specificity_twin_training.sh --dry-run --stage run
```

Observed: explicit stage override refused, exit 2. Count evidence: `/tmp/a2-review-launcher-o7dmvqv0/review-evidence.json`.

```bash
env -u DC_PYTHON -u SLURM_JOB_ID bash scripts/jobs/specificity_twin_training.sh --dry-run --config scripts/jobs/specificity_ladder_a2.json --build-manifest outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json --task far_v2 --condition D --seed 42 --receipt /tmp/a2-review-unused-receipt.json
```

Observed: default environment activation and actual cohort preflight passed; exit 0; no receipt was written. Actual captured dry-run output: `/tmp/a2-review-launcher-o7dmvqv0/actual-dry-run.stdout.log`. The independently checked ruling digest is `343bff33ea69a9e40ba9fade582f7e038f508e4bfe333c3328b93eeb14784605`. Its count map and ordered-ID binding match the actual build at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json`. Count evidence: `/tmp/a2-review-launcher-o7dmvqv0/review-evidence.json`.

## Execution evidence

Local CPU tests and dry-run preflight only; commands and exit statuses are above. No model, scientific training, GPU, API, Slurm submission, notebook, or git command was executed. Scientific row counts, baseline reproduction, and scientific run manifest are not applicable. No scientific result is claimed.

Weekly usage at handback was 13 percent spent, 87 percent remaining, below the 80 percent cap. Reset reported as 2026-11-06T16:07:41+00:00. Evidence: `/tmp/a2-review-launcher-o7dmvqv0/review-evidence.json`.

## What is NOT done

The blocking launcher issue is reported but not fixed, per review-only ownership. No production child was launched. No timing measurement, reservation permission, or scientific gate passage is claimed. No review of an implementation after the reported abbreviation fix has occurred.

## Open questions

None for the user. Default: the orchestrator fixes abbreviated stage handling, adds the launcher regression, reruns focused checks and actual safe dry-run, then resumes preflight planning. Keep the launcher on hold until that correction is reviewed.
