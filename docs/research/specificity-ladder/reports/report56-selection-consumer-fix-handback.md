# Hand-back 56: selection completion-marker consumers

Agent: Codex implementation worker. Ticket: accepted P1 in independent report 54. Status: handed-back.

## What changed

Committed by the orchestrator from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_pipeline.py`: a shared `selection_manifest_core` defines writer and consumer fields; `read_selection` requires and validates the last-written `selection_run_manifest.json` completion marker. Score and summarize invoke it immediately after prepared-design validation, before tokenizer loading, model loading or reading assessment output for a summary. Checks cover schema and exact field set, selected file bytes and payload, prepared design, raw-DLA/group/bank hashes, counts, ordered IDs/head keys, recorded full group, bank IDs, supplied identity, input/code hashes, execution metadata and injected marking. Canonical value hashes avoid accepting booleans as integer count/schema replacements.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_specificity_ladder_cli.py`: main-dispatch reproductions and refusals for 24 missing/malformed/stale/link mutation states across score and summarize; completed valid paths; early dry-run refusal; and completion-reader acceptance inside the existing actual tiny native pipeline.

No staged apply-tool operations. The sidecar remains the final writer completion marker. Existing preparation directories and frozen artifacts were not rewritten. Selection, scoring, sampling and resource instrumentation algorithms are unchanged. No git, GPU, API, notebook or subagent execution occurred.

## How verified

Working directory: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_specificity_ladder_cli.py -q -p no:cacheprovider -k 'main_refuses_incomplete_selection and (missing or malformed or empty)'
```

Observed before implementation: six failures. Score reached `MODEL_LOADER_REACHED`; summarize reached `SUMMARY_REACHED` for missing, malformed `{partial`, and valid-JSON `{}` sidecars. The model loader and summary read were sentinels; no actual model loaded.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_specificity_ladder_cli.py -q -p no:cacheprovider -k 'main_refuses_incomplete_selection or main_accepts_completed_selection'
```

Observed after implementation: 50 passed, 28 deselected. All 48 damaged-marker consumer cases refused before either sentinel; two completed valid-path cases reached their intended next consumer.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_specificity_ladder_cli.py -q -p no:cacheprovider
```

Observed final suite: 80 passed, one deprecation warning. This includes two early dry-run refusals and the actual pinned tiny native selection-to-score integration reading its completed selection through the new reader.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_specificity_ladder_cli.py -q -p no:cacheprovider
```

Observed: 79 passed, one skipped, three warnings. Base lacks pinned NNsight 0.7.0, so only its native integration skipped. Actual native integration passed in mgnp above.

```bash
/u/swong2/.local/bin/codex-usage --pause-at 80
```

Observed at hand-back: 15 percent spent, 85 percent remaining; threshold not reached. Reset November 6, 2026 at 16:07:41 UTC.

## Execution evidence

- Job id and cluster: local CPU pytest commands above; no Slurm submission or production scoring.
- Exit code: final targeted and complete owned suites exited 0.
- Row counts: 24 damage states across two consumers yielded 48 refusal cases; two valid consumer paths and two dry-run paths were tested. The existing actual tiny native integration retained its exact 12 positive-control rows and independent expected score-row checks.
- Baseline reproduces: the six before-fix sentinel reaches became refusals after the fix. Saved raw DLA still reconstructs the native tiny selection screen exactly, and its completed sidecar still links to the unchanged prepared fixture. No scientific production baseline is claimed.
- Provenance file: temporary pytest `selection_run_manifest.json` artifacts only. No production selection or assessment artifact was created or certified.

## What is NOT done

- No empirical selection, production assessment, GPU reading, API call or notebook execution.
- No existing prepared artifact, including preparation `6bd8bf5`, was edited or scored. Root retains the new-commit/new-preparation and semantic comparison gates.
- No whole-directory replacement or artifact-layout migration: the sidecar is the final completion marker and consumers now fail closed when it is absent or invalid.
- Independent closure review and production authorization remain with root.

## Open questions

None. Default: preserve the unscored production state until root reviews and commits the consumer fix and completes fresh preparation.
