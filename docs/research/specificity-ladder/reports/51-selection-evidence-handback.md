# Hand-back 51: auditable selection evidence

Agent: Codex implementation worker. Ticket: root-requested selection evidence metadata. Status: handed-back.

## What changed

Committed by the orchestrator from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_pipeline.py`: retain each task's ordered selection IDs, head keys, raw clean/corrupt DLA arrays, axes and label orientation in the selected artifact. Record actual model device/dtype, supplied commit/model/revisions, allowlisted Slurm job/cluster labels, selection compute elapsed time and GPU peak allocated bytes when applicable. The CLI additionally records model-load and selection-stage elapsed time. Publish immutable sibling `selection_run_manifest.json` with exact selected-payload, selected-file, raw-DLA, design/group/bank/input/code hashes and execution metadata. An existing sidecar blocks selection before model loading.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_specificity_ladder_cli.py`: reconstruct candidate rankings from saved raw arrays; verify sidecar links to exact artifact bytes and unchanged prepared design; verify safe runtime labels and early sidecar refusal. The actual tiny native pipeline now publishes and checks the selection sidecar before its existing score integration.

Final instrumentation addition requested by root: shared selection/scoring resource capture now records actual GPU name and peak allocated/reserved bytes on the model CUDA device, with explicit null GPU fields on CPU. Both stages record compute elapsed time and use one model-load/stage timing wrapper. Peaks reset after model loading and include the resident model; stage timing explicitly excludes artifact publication. Selection, scoring and sampling algorithms are unchanged.

No staged apply-tool operations. No ranking, source, sampler, donor or intervention algorithm changed. No git was run. Root owns review and commit.

## How verified

Working directory: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_specificity_ladder_cli.py -q -p no:cacheprovider -k 'select_uses or selection_manifest'
```

Observed before implementation: two failures, for missing `selection_evidence` and missing `write_selection`. After implementation: two passed, 20 deselected.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_specificity_ladder_cli.py -q -p no:cacheprovider
```

Observed after final instrumentation addition: 28 passed, one deprecation warning. The actual pinned NNsight/tiny-Llama CPU test reconstructed identical mover rankings from saved arrays, checked manifest design/file/raw-DLA hashes, and completed the existing select-to-score integration with exactly 12 positive controls.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_specificity_ladder_cli.py -q -p no:cacheprovider
```

Observed after final instrumentation addition: 27 passed, one skipped, three warnings. Base lacks pinned NNsight 0.7.0; its native integration skipped. Actual native execution passed in mgnp above.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_specificity_ladder_cli.py -q -p no:cacheprovider -k 'execution_resources or model_load_and_stage'
```

Observed instrumentation TDD: four failures before helpers existed, then four passed and 24 deselected. Mocked CUDA assertions cover synchronized reset/readout on the actual reported model device, GPU name, allocated/reserved peaks, compute timing and memory scope. CPU assertions refuse any CUDA API access. Both CLI stage wrappers passed deterministic model-load and stage-time checks. The full native tiny integration separately passed with null GPU fields and measured CPU compute time on both stages.

```bash
/u/swong2/.local/bin/codex-usage --pause-at 80
```

Observed at final instrumentation hand-back: 15 percent spent, 85 percent remaining; threshold not reached. Reset November 6, 2026 at 16:07:41 UTC.

## Execution evidence

- Job id and cluster: local CPU pytest commands above; no Slurm submission or production model load.
- Exit code: final scoped suites exited 0.
- Row counts: tiny test selected one original-H ID and used a separate H bank ID. Its actual select-to-score integration retained exactly 12 positive-control rows; scored row count equaled the independently reconstructed expected scope.
- Baseline reproduces: saved raw clean/corrupt DLA arrays reconstructed exactly the selected artifact's original candidate screen. No scientific baseline or production specificity result is claimed.
- Provenance file: pytest temporary `selection_run_manifest.json`, checked against its temporary groups artifact and unchanged prepared fixture. No production selection manifest exists from this work.

## What is NOT done

- No empirical selection or assessment scoring; no GPU, API or notebook execution.
- The CUDA instrumentation branch passed scoped mocks; no real GPU readings or actual Slurm job were produced. Peak memory is explicitly scoped to selection/scoring compute after model loading, including the resident model. Actual tiny CPU metadata records null GPU name and peak allocated/reserved bytes.
- Existing immutable prepare `6bd8bf5` was neither edited nor scored. Root must commit the reviewed metadata change, prepare into a separate root, and compare semantic draw/data/utility fields before first empirical selection. The code-hash guard remains strict.
- Model-load and stage timer wrappers passed deterministic unit mocks for both stages. The actual tiny native integration exercises selection/scoring compute timers and actual CPU device/dtype. No production model-load or stage timing has been measured.
- Independent review and production authorization remain with root.

## Open questions

None. Default: retain the unscored production state until review, commit and fresh preparation finish.
