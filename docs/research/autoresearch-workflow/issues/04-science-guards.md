# 04 — Science guards in Deception-Circuit code

**Status:** ready-for-agent
**Type:** task
**Blocked by:** nothing (runs in parallel with 01)
**Wave:** none; everything is in W and committed by the orchestrator.
**Estimated size:** reading about 90k tokens (spec §4.6, §6, R2, R16, R19; lane 1 §1b, §1d-1g; `W/CONTEXT.md`;
`W/run_io.py`; the relevant parts of `W/evaluate_circuit.py`, `W/evaluation/suite.py`,
`W/scripts/sdr_routing_pilot.py:327-404`), writing about 60k tokens.
**Hand-back:** `F/reports/04-handback.md`

## What to do

Record the DC test baseline, then add commit-stamped provenance to new training and evaluation runs, a grader
fingerprint, a number-resolution checker for reports, and the held-out policy with its registry. No GPU, no model
load.

## Facts to build on

- `W/run_io.py:172-187` `make_run_dir` creates the run directory and writes `config.json`. This is the one place
  every `train.py` run passes through.
- `W/evaluation/suite.py:74-80` `suite_root` and `:82-86` `cell_dir`; directories are created at `:93` (inside
  `write_json`), `:189` and `:315`. Find the seam where an evaluation cell starts and write the provenance there.
- `manifest.json` is already used with other meanings: `W/evaluate_native_sparse.py:334` and `:459`,
  `W/evaluation/generation_checkpoint.py:118`, and the SDR scripts. Hence `run_manifest.json` (R2).
- Field names to reuse: `W/scripts/sdr_routing_pilot.py:392-403` (`git_commit`, `dirty_diff_hash`, `code_sha256`,
  `software`, `model_revision`, `tokenizer_files`, `manifest_hash`), with a 10-second bound on git calls and
  `git_fingerprint_error` on failure.
- Grader code: `W/evaluation/benchmarks/{base,judge,judge_budget,liars_bench,mask_bench,sandbagging,sources,notebook}.py`
  and `W/evaluation/benchmark_eval.py`; `bench.judge_spec()` gives the judge per benchmark
  (`W/evaluate_circuit.py:627`, `:657` and `:916`). Field names `git_dirty`, `config_sha256`, `dataset_files` and
  `seed` are new in spec §4.6, not reused; keep them as specified.
- The checker's first real input: `W/docs/research/mechanism-analysis/synthesis.md` (326 lines, cites files for
  every number per lane 1 §0).

## Scope

In W:
- First, `F/reports/04-baseline-failures.md`: failing test names of the full suite in both envs before any edit.
- `W/run_manifest.py`: `build_run_manifest(...)` and `write_run_manifest(output_dir, ...)` per spec §4.6 and §6.1
  (refuse to overwrite different content; write `run_manifest.<n>.json` instead).
- `W/run_io.py`: call the writer from `make_run_dir` after `config.json`, with seed, data files and model from
  `args` (additive; existing behaviour byte-identical otherwise).
- `W/evaluation/suite.py` or the cell-start seam you find: write a per-cell `run_manifest.json`; include `grader`
  when benchmark evals are selected.
- `W/conftest.py`: set `DC_RUN_MANIFEST_GIT=0` for the suite (one additive line).
- `W/evaluation/grader_hash.py` (§6.3).
- `W/scripts/check_report_numbers.py` (§6.2).
- `W/docs/research/held-out.md` and `W/docs/research/held_out.json` with an empty `sets` list (§6.4, R19).
- Tests: `W/tests/test_run_manifest.py`, `W/tests/test_grader_hash.py`, `W/tests/test_check_report_numbers.py`.

## Acceptance criteria

- [ ] Baseline recorded in both envs before the first edit, with the exact commands used.
- [ ] `run_manifest` tests: all §4.6 fields present; `manifest_hash` verifies; git mocked for clean, dirty and
      unavailable cases; a second write with different content creates `run_manifest.1.json` and leaves the first
      untouched; `RESEARCH_DIRECTION` is recorded when set.
- [ ] The writer reads `DC_RUN_MANIFEST_GIT=0` to skip every git call (recording `git_fingerprint_error:
      "disabled"`), and `W/conftest.py` sets it for the suite, so existing tests that reach `make_run_dir` never shell
      out to git on Lustre. The `run_manifest` tests unset it and mock git explicitly.
- [ ] Full-suite wall time in each env is within 10% of the baseline run, or the difference is explained.
- [ ] A test drives `make_run_dir` with a minimal `args` and asserts `config.json` is unchanged in content and
      `run_manifest.json` exists.
- [ ] A test drives the evaluation cell seam with fakes and asserts a per-cell `run_manifest.json`, with `grader`
      present only when benchmarks are selected.
- [ ] `grader_hash` is stable across runs and changes when any listed file changes (temporary copies).
- [ ] `check_report_numbers.py` tests cover: resolved JSON leaf, resolved CSV cell, percent against a fraction,
      rounding tolerance, a derived number, each skipped category of §6.2, and `--strict` exit 1.
- [ ] `check_report_numbers.py --json W/docs/research/mechanism-analysis/synthesis.md` runs; the counts of
      numbers, resolved, derived and unresolved are pasted. No pass threshold applies to this legacy report.
- [ ] New tests pass in both envs. The full suite in both envs shows no failure name outside the baseline.
- [ ] `held-out.md` passes the lint from ticket 01 once that exists (or the hand-back says it was not yet available).

## Verification

Single test files first, then the full suite in the background in each env:
`/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/tests`
and the base command with the three thread variables from the brief.

## Comments
