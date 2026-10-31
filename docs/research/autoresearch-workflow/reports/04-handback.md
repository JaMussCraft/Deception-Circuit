# Ticket 04 hand-back: science guards in Deception-Circuit code

Status: resolved. The full-suite comparison under How verified shows no regression on either interpreter.

Nothing blocked the work. The orchestrator approved one file outside the ticket's named list, `W/tests/conftest.py`,
because the suite command never loads `W/conftest.py` (see Open questions). Between the drafts and the install, the
session paused while the mgnp baseline ran; no W code was edited before both baselines finished.

## What changed

Committed by the orchestrator from W (`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow`):

New files:

- `W/run_manifest.py` builds and writes `run_manifest.json` with every field of spec section 4.6. It never overwrites
  different content and writes `run_manifest.<n>.json` instead. It skips git when `DC_RUN_MANIFEST_GIT=0`.
- `W/evaluation/grader_hash.py` computes `grader_sha256` and the `grader` block, and has a small command line.
- `W/scripts/check_report_numbers.py` is the number-resolution checker of spec section 6.2. It uses the standard library
  only.
- `W/tests/test_run_manifest.py`, `W/tests/test_grader_hash.py` and `W/tests/test_check_report_numbers.py` hold the
  56 new tests (18, 8 and 30, counted with `pytest --co`).
- `W/tests/conftest.py` sets `DC_RUN_MANIFEST_GIT=0` and nothing else. The orchestrator approved it.
- `W/docs/research/held-out.md` states the policy, and `W/docs/research/held_out.json` is the registry with an empty
  `sets` list.
- `W/docs/research/autoresearch-workflow/reports/04-baseline-failures.md` and this hand-back.

Edited files, additive only:

- `W/run_io.py`: `make_run_dir` calls the new `write_run_provenance(args)` right after writing `config.json`. The
  config bytes are unchanged, and a failing writer prints a warning instead of stopping training.
- `W/evaluation/suite.py`: the new `write_cell_manifest(ctx)` runs at the top of `run_cell`, after the output
  directory exists. It writes `run_manifest.json` beside `summary.json` and fills `grader` only when `benchmarks` is
  among the selected evaluations.
- `W/conftest.py`: one line sets `DC_RUN_MANIFEST_GIT=0`.
- `W/docs/research/autoresearch-workflow/issues/04-science-guards.md`: Status line and Comments.

Staged in S: nothing. Ticket 04 has no wave and no op file.

Design decisions a reviewer should check:

- **Git fingerprint.** `git_commit` comes from `git rev-parse HEAD`. `git_dirty` is whether `git diff HEAD` is
  non-empty, so untracked files do not count. `dirty_diff_hash` is the sha256 of that diff, or null when clean. Each
  call has a 10-second bound. On failure the three fields are null and `git_fingerprint_error` says why.
- **Seed and config of an evaluation cell.** They come from the circuit's own run, `<run_dir>/config.json`, because
  that is what seed replication compares. `dataset_files` are the evaluated task's files.
- **Dataset files.** These are the data files under the task's dataset directory. Deception tasks use their
  `dataset_dir(args)`, STD uses `std_<variant>`, and the other tasks use `<data_dir>/<task>`. A joint run lists each
  subtask.
- **Model revision.** It is read from `refs/main` in the hub cache without loading the model. The lookup tries
  `HF_HUB_CACHE`, `HUGGINGFACE_HUB_CACHE`, `TRANSFORMERS_CACHE` and then `HF_HOME/hub`. On Delta both cache copies
  of Llama-3.1-8B-Instruct name the same revision.
- **Grader hash form.** The hash is the sha256 of one line per file, sorted by path, of the form
  `<relative path><tab><sha256><newline>`. For W today it is `866fd15dd30b695e46ffe955b09894fb831af92e2b9015eafbd7f0eee151d2f9`.
- **Checker categories beyond the spec list.** The checker also skips numbered labels (Table 3, phase 2, EVAL 5),
  paths and URLs, markdown list markers, and identifiers that glue letters to digits (A100, 8B, S_20). It counts every
  skip by category in its JSON output. A string cell or leaf that is wholly a number counts as numeric. A table row
  uses the citations of the paragraph just before its table and of the header row.

## How verified

Baseline, before any code edit. Both runs started together at about 12:54 pm CDT on 2026-10-31 through
`/u/swong2/.claude/jobs/b2cb53cd/tmp/04/run_suite.sh`. The commands, logs and name lists are in `04-baseline-failures.md`.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider -rfE <W>/tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider -rfE <W>/tests
```

```
mgnp: 19 failed, 3069 passed, 22 skipped, 2 warnings, 101 errors in 1634.52s
base: 19 failed, 2863 passed, 78 skipped, 4 warnings, 101 errors in 652.28s
```

Both interpreters fail the same 120 names.

New tests in W, single files first. These were run in W after the install, together with the two existing tests that
drive `train.main()` through `make_run_dir`:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 <python> -m pytest -q -p no:cacheprovider \
  W/tests/test_run_manifest.py W/tests/test_grader_hash.py W/tests/test_check_report_numbers.py \
  W/tests/test_nopressure_condition.py W/tests/test_format_control_launch.py
```

```
mgnp: 115 passed, 1 warning in 26.52s
base: 115 passed, 4 warnings in 26.16s
```

### Full-suite comparison

Written by the orchestrator on 2026-10-31 at 4:45 pm EDT from the agent's logs, after the implementer went idle
twice without filling this section in. The after runs used the same `run_suite.sh` commands as the baseline, from W
with every ticket 04 file in place. Logs: `suite-after-base.log` (finished 4:15 pm EDT) and `suite-after-mgnp.log`
(finished 4:30 pm EDT) in `/u/swong2/.claude/jobs/b2cb53cd/tmp/04/`.

```
base: 19 failed, 2919 passed, 78 skipped, 4 warnings, 101 errors in 624.32s
mgnp: 19 failed, 3125 passed, 22 skipped, 2 warnings, 101 errors in 1502.09s
```

Passed counts rose by 56 on each interpreter (2863 to 2919; 3069 to 3125), which is exactly the number of new tests.
Failing and erroring names, compared with `names.py`:

```
/sw/external/python/anaconda3/bin/python3.9 -I T/04/names.py T/04/suite-baseline-base.log T/04/suite-after-base.log
NEW (in after, not in before): 0
GONE (in before, not in after): 0
/sw/external/python/anaconda3/bin/python3.9 -I T/04/names.py T/04/suite-baseline-mgnp.log T/04/suite-after-mgnp.log
NEW (in after, not in before): 0
GONE (in before, not in after): 0
```

All 120 names in `04-baseline-failures.md` still fail for the same worktree reasons, and nothing else fails. No
regression.

Number checker on the legacy synthesis report. No pass threshold applies to it.

```
/sw/external/python/anaconda3/bin/python3.9 -I W/scripts/check_report_numbers.py --json W/docs/research/mechanism-analysis/synthesis.md
/sw/external/python/anaconda3/bin/python3.9 -I W/scripts/check_report_numbers.py --json --root /projects/beto/swong2/Alignment/.scratch/mechanism-analysis W/docs/research/mechanism-analysis/synthesis.md
```

| roots | numbers | resolved | derived | unresolved | cited files not found |
|---|---|---|---|---|---|
| default (report directory, W) | 607 | 299 | 39 | 269 | 14 |
| plus the reports directory the report names | 607 | 416 | 39 | 152 | 3 |

Skipped in both runs: code 166, component ids 234, dates 6, identifiers 159, labels 23, rulings 58, sections 78,
tickets 19, versions 21. The second run adds `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis`, because the
report says its `reports/...` paths live there. Those files were only read. A sample of 100 unresolved numbers was
read by hand. Most are prose that repeats a number without citing a file in the same unit, or spec section numbers
written in parentheses, such as "(2.3)", which the checker cannot tell from values. The sample exposed two checker bugs, a head range
read as a negative number and a split exponent. Both are fixed and covered by tests.

Lint from ticket 01's staged command line, which printed nothing and exited 0:

```
/sw/external/python/anaconda3/bin/python3.9 -B S/tree/projects/beto/swong2/Alignment/.agents/research_session/cli.py lint W/docs/research/held-out.md W/docs/research/autoresearch-workflow/reports/04-baseline-failures.md
```

## Execution evidence

Not applicable: no runs. No GPU job, no `sbatch` and no paid API call was made.

## What is NOT done

- No provenance backfill for old runs, by spec R16.
- No code guard against scoring held-out ids, by spec R19. The policy and the empty registry exist.
- `grader_sha256` covers only the files spec section 6.3 names. It does not cover the rubric files in the sibling
  MASK and Liars' Bench checkouts that the judge specs name as `source`.

## Open questions

1. **The root conftest is not loaded by the suite command.** No pytest ini file exists in W, DC or A. So
   `pytest W/tests` makes `W/tests` the root and confcutdir, and `W/conftest.py` is skipped. Its
   `torch.set_num_threads(1)` therefore never applies. This is the likely reason the mgnp suite took 1,635 seconds
   against base's 652, since base exports one thread through the environment. Per the orchestrator, this is a
   follow-up and not fixed here. Two options are to move the thread pin into `W/tests/conftest.py`, or to add a
   `pytest.ini` at W's root. Either may shift results by one ulp and needs its own baseline.
2. **External rubric files.** Should a later ticket fold the `rubric_sources` files of the MASK and Liars' Bench
   adapters into the grader hash? Today a change in those sibling checkouts does not change `grader_sha256`.
3. **Spec section numbers in parentheses.** Synthesis-style tables write spec sections as "(2.3)". If future reports
   keep that form, a "§" prefix would let the checker skip them.
