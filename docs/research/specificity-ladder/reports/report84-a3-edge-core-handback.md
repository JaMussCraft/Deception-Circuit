# Hand-back report84: A3 edge core

Agent: Codex worker. Ticket: approved A3 Task 4b atop the reviewed native adapter. Status: handed-back for independent review.

## What changed

The orchestrator owns commits. Only these worktree files were written:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_edges.py`: frozen causal edge grid, local branch midpoint integrated gradients, exact simultaneous intact-delta clamps, and integration stability diagnostic.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_edges.py`: twenty-four CPU edge tests, including actual tiny random Llama gradients and a complete analytic toy.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report84-a3-edge-core-handback.md`: this report, mirrored to `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report84-a3-edge-core-handback.md`.

The module docstring defines the concrete schemas. `edge_grid` takes one task's frozen `edge_nodes` and HF dimensions plus explicit position-cell metadata. Each edge retains sender, receiver, position key, and its frozen position specification. The batch binds each key to that exact metadata and an integer position per row or ragged per-row token lists. Empty, unsupported, changed, or physically aliased cells fail before capture. There is no index interpolation, padding fallback, automatic candidate discovery, or D/I token splice.

Maps contain supported builder records with recipient and donor positions and explicit row, condition, and stream identities. Existing `recipient_id`, `donor_id`, `recipient_stream`, and `donor_stream` fields are accepted; shared `instance_id` and `stream` are twin shorthand. This permits a frozen clean-recipient/corrupt-donor IOI map without creating a new donor. MMLU donor construction is absent.

Attribution consumes `{batch, neutral, maps, weights?}` items. Caller-owned weights must sum to one across the complete iterable; implicit weights give equal row weights. The caller supplies canonical opposite/honest token labels. Each integration activates only one receiver leaf, keeps downstream branches live, and uses separate intact observations. Caches and gradients are detached and consumed per batch/receiver; vocabulary graphs do not escape. The primary within-cell attribution is a SUM over all verified mapped tokens; raw token count and mean tokens per row are reported. It is a local ranking, not necessity.

Exact patches use projected head or whole-MLP additive deltas from fixed intact and donor caches. Sorted sums group incoming edges into one residual per receiver branch and position mask. The native adapter merges disjoint Q/head and K/V/group slices. Returned clamps, masks, and actual native receiver outputs permit effective-tensor checks. Selected chains never consult changed live senders; a selected readout clamp retains its blocking effect. Endpoint recovery is promised only for the complete analytic toy.

Review follow-up: the stability helper now rejects nonfinite aggregate denominators, score-difference sums, and ratios even when individual input scores are finite. This prevents overflow from falsely declaring agreement. Ordinary arithmetic, the frozen overlap and normalized-L1 thresholds, zero-score behavior, and candidate ranking are unchanged. Three parameterized regression cases were added to the owned test file.

## How verified

All commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_edges.py tests/test_a3_native.py -p no:cacheprovider -q -rs
```

Observed final output: `42 passed, 1 warning in 9.01s`; exit zero. The warning is an external astor deprecated AST alias.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_edges.py tests/test_a3_native.py -p no:cacheprovider -q -rs
```

Observed final output: `41 passed, 1 skipped, 3 warnings in 17.33s`; exit zero. The existing native test `test_actual_nnsight_inference_parity` skips because base does not have pinned nnsight 0.7.0. Every new edge test and every actual native gradient test ran on both interpreters. Base warnings concern the transformers cache variable, TensorFlow ml_dtypes, and pandas bottleneck. The new single-receiver legacy two-pass agreement test ran on both interpreters.

```bash
/u/swong2/.local/bin/ruff format component_analysis/a3_edges.py tests/test_a3_edges.py
/u/swong2/.local/bin/ruff check component_analysis/a3_edges.py tests/test_a3_edges.py
```

Observed: two files reformatted; `All checks passed!`; exit zero.

Test-first evidence: the initial suite could not import the absent module. After implementation the first fourteen cases passed. Added token-count metadata failed with a missing field before its implementation; geometry alias and cross-bin physical alias tests each failed to raise before their fixes; the corrupt utility donor test failed with a row identity mismatch before explicit donor identity/stream support. Those same cases are included in both final passing runs.

Coverage includes causal order, same-layer attention to MLP, GQA receiver deduplication, two incoming edges, mixed Q/K/V branches, actual receiver tensor equality, edge permutation invariance, identity and empty-set replay, fixed-cache chains, readout blocking, ragged mapped token bins, unsupported and malformed maps, metadata aliases, distinct position effects, streamed row weights, native eight-versus-sixteen midpoint stability, exact stability threshold and nonfinite handling, and complete toy causal/dead-edge ranking and endpoint recovery.

Follow-up for the overflow identified by review report86: the targeted regression command below first produced `3 failed, 24 deselected in 11.44s`, because none of the overflow paths raised. The cases cover denominator overflow using twenty repeated `8e306` versus `1e307` scores, subtraction overflow, and ratio overflow. The implementation now raises an explicit `ValueError` for nonfinite aggregate arithmetic rather than emitting a misleading stability result.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_edges.py -k nonfinite_aggregate -p no:cacheprovider -q
```

After the fix, the required scoped final commands were:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_edges.py -p no:cacheprovider -q
```

Observed: `27 passed, 1 warning in 8.87s`; exit zero. The warning remains external astor deprecation.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_edges.py -p no:cacheprovider -q
```

Observed: `27 passed, 3 warnings in 18.09s`; exit zero. There were no skips. The warnings are the same base dependencies described above. These runs include the existing exact normalized-L1 boundary regression and actual tiny native-gradient cases. The original combined edge/native results above describe initial acceptance; this follow-up ran only the authorized edge suite.

```bash
/u/swong2/.local/bin/ruff format component_analysis/a3_edges.py tests/test_a3_edges.py
/u/swong2/.local/bin/ruff check component_analysis/a3_edges.py tests/test_a3_edges.py
```

Observed after the follow-up: one file reformatted, one unchanged; `All checks passed!`; exit zero.

## Execution evidence

- Job and cluster: local CPU pytest commands above; no Slurm job or GPU execution.
- Exit codes: both final pytest invocations and Python lint exited zero.
- Counts: twenty-four new edge cases plus eighteen existing native cases were collected, as expected. mgnp ran all forty-two; base ran forty-one and explicitly skipped the inherited pinned-nnsight parity case.
- Baseline assertion: the complete linear toy's causal integrated score is 10 against expected 10, and its dead-edge score is 0 against expected 0. The sum equals the measured intact-minus-patched endpoint margin difference. Exact full-graph logits equal the separately executed donor endpoint. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_edges.py`.
- Follow-up counts: twenty-seven edge cases ran against twenty-seven expected, with zero skips, on each interpreter; both final scoped test commands exited zero. No scientific run was introduced.
- Provenance: no scientific `run_manifest.json` was produced. Root owns source freeze and run admission. These are CPU contract tests, not a model-study result, benchmark, replication, or scientific efficacy claim.

## What is NOT done

No native adapter, generic hooks, pipeline, research state, worklog, ledger, or other worker's files were changed. No git command, subagent, GPU, Slurm, external API, notebook execution, pretrained model load, download, or broad repository suite was used.

Validation budget selection from one/four/sixteen edges, separate D/I rankings, the nineteen matched-null families, cohort bootstrap orchestration, production geometry preparation, protected-registry refresh, fit/select/assessment publication, and all three-seed scientific runs remain deferred. No candidate sets or matched nulls were silently invented. Root owns source freeze, cost receipts, phase admission, and any scientific run. The inherited base nnsight-version skip remains visible; native differentiation itself has no skipped gate here.

No claim is made that an incomplete real graph reaches the donor endpoint, that stable quadrature proves attribution accuracy, or that an attribution ranking establishes necessity. Exact joint clamp effects must select and assess sets in the later runner.

## Open questions

Independent review is the next step. Default: retain the narrow CPU core and its schemas; do not admit scientific execution until root supplies the frozen position geometry, valid cohort/maps/weights, complete selection and null orchestration, and measured resource admission. The map records are trusted builder evidence supplied by the caller; this module validates their identity, support, injectivity, and bounds but does not reconstruct prompt-builder proofs.
