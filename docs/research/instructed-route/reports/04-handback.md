# Hand-back 04: B1 ticket 1, a run_manifest.json in every analyze_components cell

Agent: Opus implementer (claude-opus-5-5). Ticket: B1 plan section 5 ticket 1, in
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B1-plan.md`.
Status: resolved.

## What changed

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/analyze_components.py`, new
  `write_cell_provenance` beside `write_cell`, called by `run()` once per cell after the head table; `run()` takes
  `argv=None` and `main()` passes its argv.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_analyze_components_manifest.py`,
  new, seven tests.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_analyze_components_registry.py`,
  one expectation line: the exact file list of a non-dry run now includes the cell's `run_manifest.json`. This file is
  outside the ticket's ownership list, and the edit was necessary because the test asserts every file a run writes.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_v1_snapshot_02b.py`,
  `snapshot()` skips `run_manifest*.json`. This file is outside the ownership list too, and the edit was necessary for
  the same reason. The fixture under `tests/fixtures/v1_snapshot_02b/` is unchanged.

`run_manifest.py` and `component_analysis/batch.py` are unchanged.

How it behaves:

- The manifest is written by `run()` only. `dry_run()` also calls `write_cell`, so the call sits beside `write_cell`
  rather than inside it, and a dry run writes no manifest.
- It reuses `run_manifest.write_run_manifest` as `run_io.write_run_provenance` and `evaluation/suite.py` do. The
  kwargs are `script` set to `analyze_components.py` itself, so `code_sha256` hashes it under pytest and batch too,
  plus `argv`, the task's `dataset_files_for_args(task_spec.args)`, `model=resolved.model` and `seed=cli.seed`.
  `config_path` is None because a cell has no config.json.
- An existing manifest with different content is kept and `run_manifest.1.json` is written beside it, which is the
  writer's existing convention. An identical rerun keeps the one file.
- A failure prints `!! run_manifest.json not written: ...` and the run goes on.
- Batch mode gets a manifest in every cell because each batch line calls `run()`. The recorded argv is the batch
  command line, because `batch.py` calls `run()` without `argv` (see Open questions).

## How verified

New test file before the code change, mgnp:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_analyze_components_manifest.py
```

Observed: 5 failed, 2 passed. The two dry-run tests pass trivially before the change.

After the change, the new file and the three existing `test_analyze_components_*.py` files, mgnp:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_analyze_components_manifest.py tests/test_analyze_components_end_to_end.py tests/test_analyze_components_registry.py tests/test_analyze_components_segmentation.py
```

Observed: 39 passed, 0 failed.

Same files, base 3.9:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_analyze_components_manifest.py tests/test_analyze_components_end_to_end.py tests/test_analyze_components_registry.py tests/test_analyze_components_segmentation.py
```

Observed: 39 passed, 0 failed.

Wider blast radius: every `tests/test_*.py` file that mentions `analyze_components` (30 files), because several assert
the exact file list of a cell. The baseline ran on mgnp before the code change:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider $(grep -rl analyze_components tests/ | grep '^tests/test_' | sort)
```

Observed before the change: 656 passed, 0 failed.

The same 30 files plus the new file after the change, base 3.9:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider -rfE tests/test_analyze_components_manifest.py $(grep -rl analyze_components tests/ | grep '^tests/test_' | sort)
```

Observed: 516 passed, 39 skipped, 0 failed. The skips are the tiny-Llama tests that need nnsight 0.7.0.

The same set after the change, mgnp:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider -rfE tests/test_analyze_components_manifest.py $(grep -rl analyze_components tests/ | grep '^tests/test_' | sort)
```

Observed: 668 passed, 1 failed. The failure was
`tests/test_v1_snapshot_02b.py::test_a_v1_attention_and_path_patching_cell_is_byte_identical_to_the_snapshot`, which
passed in the baseline, so it was a regression. The snapshot lists every file of the cell, and the cell now holds
`run_manifest.json`. The fix excludes `run_manifest*.json` from the snapshot. Like the wall-clock fields the test
already scrubs, it is provenance and not v1 output. The fixture was not regenerated. The pass count rose by more than
the seven new tests, most likely because other implementers edited files in this set while the runs were going.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider -rfE tests/test_v1_snapshot_02b.py
```

Observed after the fix on mgnp: 2 passed, 0 failed. On base 3.9 the module skips, because it needs nnsight 0.7.0.
The full 31-file set was not rerun on mgnp after this one-line test fix, because that run takes about 20 minutes.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- Batch lines record the batch command line as argv, not the line's own flags. Threading the line's argv needs a
  one-line change in `component_analysis/batch.py`, which this ticket does not own.
- The full repository suite was not run, only the 30 files that drive the analyze_components CLI plus the new file.

## Open questions

- Should batch manifests record each line's flags? It would take `cli_module.run(cli, resolved, model=model,
  argv=line)` in `batch.py`, plus the stub `run` lambda in `tests/test_component_analysis_v2_batch.py` taking
  `argv=None`. Default: leave it. Each cell still gets the 40-hex commit, the timings file names the line, and the
  `created` timestamp already makes a rerun write `run_manifest.<n>.json`.
- Are the test edits in `tests/test_analyze_components_registry.py` and `tests/test_v1_snapshot_02b.py` acceptable
  outside the ownership list? Default: accepted, because both only absorb the new provenance file.
