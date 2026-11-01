# Hand-back 33: IOI and MMLU task adapters

Agent: Codex worker. Ticket: `plan-ladder.md`, Task 3. Status: resolved; CPU preparation complete, scientific scoring remains gated.

## What changed

Files for the orchestrator to commit from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_tasks.py`: normalized model-independent IOI and local-cache-only MMLU rows, right-padded LadderBatch adapters, explicit IOI donor maps and optional independent task donors, MMLU readout calibration maps.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_ladder_tasks.py`: focused CPU tests for answer removal, boundaries, prefix preservation, deterministic deduplication, malformed choices, original source IDs, overlength rejection, cache miss, name-pool compatibility and donor support.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/33-ladder-task-adapters-sample.json`: prospective frozen CPU sample, original parquet IDs and hashes, exact prompt bytes, token IDs, all IOI item-swap maps and MMLU readout calibration maps; no scoring authorization.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/ioi_llama.py`: authorized optional keyword-only prevalidated `name_pool`; default historical loading/filtering path is unchanged.

The adapter sorts the upstream name vocabulary before filtering and passes this explicit pool, restoring Python RNG state afterward. No production monkeypatch is used. IOI assesses only clean recipients; corrupt rows are donors. MMLU's arbitrary opposite letter is diagnostic only, with all four contextual option IDs provided for option-margin scoring. MMLU has no full-sequence layout or native item-swap map; its calibration maps explicitly connect only readout positions of different questions, preferring different gold letters.

## How verified

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_ladder_tasks.py -q -p no:cacheprovider
```

Observed: ten tests passed. Initial missing-module collection failed before implementation; the name-pool regression subsequently failed before that source seam was added.

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_ladder_tasks.py -q -p no:cacheprovider
```

Observed: ten tests passed on the final source. Base final rerun also passed all ten tests.

CPU cached-tokenizer acceptance uses the existing `dataset.user_inversion_pipeline.load_tokenizer` helper. Its base-transformers workaround loads the pinned local snapshot to avoid the documented online Mistral heuristic, and records the actual path and config hash. Base acceptance produced one hundred IOI rows twice with exact equality and thirty-two MMLU rows. All IOI native donor maps were supported. The MMLU cache contained fourteen thousand forty-two eligible questions with no rejected rows at the configured cap.

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/ladder_tasks_acceptance.py
```

Observed: exit zero; final prospective sample artifact materialized. Both cached-tokenizer acceptance environments passed. No model was loaded. The final artifact contains one hundred IOI rows, thirty-two MMLU rows, and thirty-two supported MMLU calibration maps. MMLU revision is `c30699e8356da336a370243923dbaf21066bb9fe`. Its parquet hash is `74a41822ce7d3def56e1682f958469c04642a5336a5ce912fa375fdb90fb25d7`.

## Execution evidence

Not applicable: no runs.

The checks above are CPU implementation and data-preparation checks, not behavioral experiments. No GPU job, model forward, baseline accuracy, benchmark scoring or run manifest is claimed. Scientific behavior remains not yet verified.

## What is NOT done

- No model scoring, GPU/API work or full benchmark evaluation.
- Frozen grader registration remains the lead's prerequisite before any MMLU scoring; the prospective manifest explicitly carries an empty grader registry.
- Optional independent IOI donor construction is tested on synthetic fixtures; the full separate donor pools have not been materialized.
- No claim about general capability preservation or actual ladder utility gates.

## Open questions

None blocking adapter integration. The lead should freeze the returned rows, sample manifest and grader registry before scoring. Use `task_batches(rows)` for clean utility recipients, `task_batches(rows, stream='corrupt')` only for IOI donors, `ioi_item_swap_maps(rows)` for native IOI maps, and `mmlu_calibration_maps(rows)` only for readout calibration. Optional `ioi_task_resample` returns separate donors and maps marked `task_resample`; integration must preserve that own-task provenance rather than labeling it H resampling.
