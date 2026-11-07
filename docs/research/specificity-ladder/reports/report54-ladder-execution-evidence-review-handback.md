# Hand-back `54`: Selection and scoring execution evidence review

Agent: Codex independent reviewer. Ticket: narrow metadata additions after frozen code `6bd8bf5`. Status: handed-back.

## What changed

Production files were read only. The orchestrator may commit `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report54-ladder-execution-evidence-review-handback.md`. The same hand-back is mirrored in primary. No staged operations exist.

**Verdict: request the narrow sidecar-consumer validation fix before treating selection as complete.** The lead accepted this finding during review. The raw DLA and execution instrumentation otherwise meet the scoped metadata requirements. Review used current code, tests and the orchestrator-supplied comparison `/tmp/specificity-ladder-evidence-review.diff`; author report `51` was not read.

**P1: missing, partial or stale selection sidecar does not prevent scoring.** In the reviewed code, `write_selection` publishes the selected artifact and then writes `selection_run_manifest.json` last. This is a reasonable completion-marker arrangement, but the score/summarize consumer in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_pipeline.py:584` reads only `args.groups` and validates design/bank/group payload hashes. It never reads the sidecar. A crash after the selected artifact is written, a partial sidecar write, or a stale manifest therefore leaves an artifact that can still reach the score model loader and later finalization without the new execution evidence. An overwrite refusal in the select stage does not close this consumer gap.

Model-free reproduction through the real `main` dispatch reached an injected sentinel model loader for each of these sidecar states: missing, malformed JSON `{partial`, and empty object `{}`. Source and registry checks unrelated to the sidecar were mocked so the reproduction isolated this consumer path; no actual model was loaded.

Default fix: validate the completion sidecar before score model loading and before accepting a summary. Require valid schema/kind and exact links to selected artifact bytes and payload, prepared design, groups, bank, ordered raw DLA, source/selection input hashes, code identity, commit/model/tokenizer identity, execution block and counts. Test missing, partial, stale and modified sidecars at the consumer, not only the writer. The sidecar can remain the final completion marker; this finding does not require replacing existing artifact layouts or changing the already frozen preparation.

Other inspected properties:

- Raw DLA evidence saves the exact head-key subsequence of the recorded full component list, preserves the task's ordered selection IDs, and serializes clean and corrupt arrays in that order. The arrays are the same arrays passed to the unchanged screen. Evidence states both axes and the original-H correct-minus-other direction. Reapplying `choose_mover_candidates` reconstructs the complete published screen, including rankings, candidate membership and remaining group. The actual tiny native-hook integration test exercises this equality.
- The selected payload includes raw evidence, execution provenance and the existing design/group/bank joins. The writer emits full supplied commit, model and tokenizer identities, input/code hashes, selection/head/bank-instance counts, the raw evidence hash, selected payload hash, exact selected file hash, and resolved artifact location. Writer link tests pass. These recorded fields are useful, but require the consumer validation above to certify completed selection.
- Resource capture uses the model's actual device and dtype. On CUDA it synchronizes and resets peaks for that device, then records the actual GPU name and allocated/reserved peaks for the same device at completion. It explicitly labels the memory scope as compute after model loading, including the resident model; it does not claim load-time transient peaks. CPU records null GPU name and memory peaks and never calls CUDA resource methods.
- Both actual selection and scoring paths use the same model-load/compute timing wrapper. Each gets separately named compute duration, model-load duration and stage duration. Scope explicitly excludes artifact publication. Stage instrumentation covers the full local selection or scoring call, including bank work and validation; it is not presented as per-forward kernel timing.
- Runtime labels read only safe allowlisted scheduler/cluster fields, validate their format, and retain the source of the chosen cluster label. They do not dump environment contents. Invalid or absent labels become null.
- The supplied diff adds raw evidence, instrumentation, selection publication and tests; it does not change cohort construction, ordered selection IDs, DLA calculations, screening rules, H-bank construction, intervention operations, model logits, gate thresholds or summary interpretation. The prior SDR descriptive qualification and compact bank-reference behavior remain present. The lead will separately reprepare a distinct artifact root after commit and compare semantic fields; this review did not mutate or certify that future artifact.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_specificity_ladder_cli.py -k 'selection_manifest or selection_runtime or execution_resources or model_load_and_stage or tiny_native_select' -q
```

Observed: `8 passed, 20 deselected, 1 warning in 19.19s`; exit code `0`. This includes the actual tiny native-hook selection/scoring test, raw-screen reconstruction, selection manifest links, mocked CUDA resource calls and CPU null behavior.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_specificity_ladder_cli.py -k 'selection_manifest or selection_runtime or execution_resources or model_load_and_stage or tiny_native_select' -q
```

Observed: `7 passed, 1 skipped, 20 deselected, 3 warnings in 17.90s`; exit code `0`. Only the tiny native-hook integration test skips because base lacks the pinned NNsight version; mgnp supplies its applicable pass.

The sidecar reproduction constructed sealed temporary design/group fixtures with consistent payload joins, patched only unrelated prepared/registry validation, and invoked score through `main` with a loader that raises `MODEL_LOADER_REACHED`. Observed literal output:

```text
sidecar None result MODEL_LOADER_REACHED
sidecar '{partial' result MODEL_LOADER_REACHED
sidecar '{}' result MODEL_LOADER_REACHED
```

The reproduction command exited `0`; it did not call a real loader or scoring function.

## Execution evidence

Local CPU tests and model-free reproduction only. Observed scoped test counts were `8` passing against `8` selected in mgnp and `7` passing plus `1` expected skip against `8` selected in base, with `20` intentionally deselected in each. Both test commands and the reproduction exited `0`. No pretrained model, GPU, API, Slurm job, notebook, production behavioral baseline or production assessment output was run by this reviewer. No scientific run manifest is claimed, so real GPU resources and production assay behavior are not yet verified here.

## What is NOT done

No production edits or git commands. No consumer fix or its closure review; no broad rerun, full model execution, existing preparation rewrite, new preparation semantic comparison or unrelated runtime modification. Mocked CUDA assertions test device dispatch and field semantics, not real GPU measurements. The bounded real-model pilot and provenance checks remain necessary.

## Open questions

The lead accepted the sidecar consumer gap and will assign the smallest fix. Default: keep the final sidecar as the selection completion marker, reject incomplete evidence before model loading or summary certification, and independently check that closure before production selection/scoring proceeds.
