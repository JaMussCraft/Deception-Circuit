# Hand-back 04: B1 ticket 1, a run_manifest.json in every analyze_components cell

Agent: Opus implementer (claude-opus-5-5). Ticket: B1 plan section 5 ticket 1, in
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B1-plan.md`,
with the B2 plan's section 6 T1 requirements folded in at the team lead's request
(`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B2-plan.md`).
Status: resolved.

## What changed

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/analyze_components.py`, new
  `write_cell_provenance` beside `write_cell`, called by `run()` once per cell after the head table; `run()` takes
  `argv=None` and `main()` passes its argv.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/component_analysis/batch.py`,
  one line: each batch line calls `run(..., argv=line)`, so its cells record that line's flags.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_analyze_components_manifest.py`,
  new, ten tests.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_analyze_components_registry.py`,
  one expectation line: the exact file list of a non-dry run now includes the cell's `run_manifest.json`.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_v1_snapshot_02b.py`,
  `snapshot()` skips `run_manifest*.json`. The fixture under `tests/fixtures/v1_snapshot_02b/` is unchanged.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_component_analysis_v2_batch.py`,
  the monkeypatched `run` lambda accepts `argv=None`, because `batch.py` now passes it.

The last three test files are outside the original ownership list. Each edit only absorbs the new provenance file or
the new keyword. `run_manifest.py` is unchanged.

How it behaves:

- The manifest is written by `run()` only. `dry_run()` also calls `write_cell`, so the call sits beside `write_cell`
  rather than inside it, and a dry run writes no manifest, batch dry runs included.
- It reuses `run_manifest.write_run_manifest`, wrapped as in `run_io.write_run_provenance`. A failure prints
  `!! run_manifest.json not written: ...` and the run goes on.
- The kwargs are `script` set to `analyze_components.py` itself, so `code_sha256` hashes it under pytest and batch
  too. The others are `argv`, the task's `dataset_files_for_args(task_spec.args)`, `model=resolved.model` and
  `seed=cli.seed`. `config_path` is None because a cell has no config.json.
- The recorded argv is `analyze_components.py` followed by the invocation's flags, or by the batch line's flags.
- An existing manifest with different content is kept and `run_manifest.1.json` is written beside it, which is the
  writer's existing convention. An identical rerun keeps the one file. Because `created` is part of the content, a
  rerun at a later second also writes the next numbered file.
- With `DC_RUN_MANIFEST_GIT=0` the manifest records `git_fingerprint_error: "disabled"` and `git_commit: null`. This
  is the existing `run_manifest.git_fingerprint` behaviour, and a test now asserts it through the CLI.

## How verified

The first seven tests were written before the code change, mgnp:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_analyze_components_manifest.py
```

Observed: 5 failed, 2 passed. The two dry-run tests pass trivially before the change.

The three tests added for the B2 requirements, before the `batch.py` change, same command: 2 failed, 7 passed. The
two batch-argv tests failed as expected. The disabled-git test passed at once, because the writer already does this.

After all changes, the new file and the batch test file, mgnp:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_analyze_components_manifest.py tests/test_component_analysis_v2_batch.py
```

Observed: 16 passed, 0 failed.

Wider blast radius: every `tests/test_*.py` file that mentions `analyze_components` (30 files, including the batch
and v1 snapshot files), because several assert the exact file list of a cell. The baseline ran on mgnp before any
code change:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider $(grep -rl analyze_components tests/ | grep '^tests/test_' | sort)
```

Observed before the change: 656 passed, 0 failed.

The first run after the change found one regression on mgnp:
`tests/test_v1_snapshot_02b.py::test_a_v1_attention_and_path_patching_cell_is_byte_identical_to_the_snapshot`, with
668 passed and 1 failed. The snapshot lists every file of the cell, and the cell now holds `run_manifest.json`. The
fix excludes `run_manifest*.json` from the snapshot. Like the wall-clock fields the test already scrubs, the
manifest is provenance and not v1 output.

Final run, all 30 files plus the new file, after every change, mgnp:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider -rfE tests/test_analyze_components_manifest.py $(grep -rl analyze_components tests/ | grep '^tests/test_' | sort)
```

Observed: 671 passed, 0 failed.

Same set, base 3.9:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider -rfE tests/test_analyze_components_manifest.py $(grep -rl analyze_components tests/ | grep '^tests/test_' | sort)
```

Observed: 518 passed, 39 skipped, 0 failed. The skips are the tiny-Llama tests that need nnsight 0.7.0, the v1
snapshot among them.

The mgnp total rose by more than the new tests between the baseline and the final run. The likely cause is that
other implementers edited files in this set while the runs were going.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- The full repository suite was not run, only the 30 files that drive the analyze_components CLI plus the new file.
- The B2 plan names the test file `tests/test_analyze_components_run_manifest.py`. At the team lead's instruction the
  file is `tests/test_analyze_components_manifest.py`, so the B2 plan's file name is now stale.

## Open questions

- Are the test edits outside the original ownership list acceptable? They are in
  `tests/test_analyze_components_registry.py`, `tests/test_v1_snapshot_02b.py` and
  `tests/test_component_analysis_v2_batch.py`. Default: accepted, because each only absorbs the new file or keyword.
- Should the B2 plan's T1 paragraph be corrected to the actual test file name? Default: yes, the orchestrator fixes it
  when committing the plans.
