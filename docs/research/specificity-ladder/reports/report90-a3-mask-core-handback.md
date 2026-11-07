# Hand-back report90: A3 constrained-mask numerical core

Agent: Codex worker. Ticket: approved A3 Task 5a numerical core. Status: handed-back for independent review.

## What changed

The orchestrator owns commits. Owned worktree files:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_mask.py`: exact full-cohort mask objective, native eligibility initialization, paired neutral-twin CPU-compatible forward, streamed optimizer update, checkpoint identity helpers and deterministic complement export.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_mask.py`: synthetic objective and tiny random native Llama contracts, including an independent retained-graph gradient/Adam oracle and native-hook removal parity.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report90-a3-mask-core-handback.md`: this report. Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report90-a3-mask-core-handback.md`.

No native model, closed selective-study, A1 runtime, A2 snapshot, pipeline or artifact module was edited. No git command was run.

The concrete public interface is:

- `configure_candidates(model, candidates)` accepts unique `(head, layer, query_head)` and `(mlp, layer, 0)` tuples, returns `MaskSupport`, freezes base weights and keeps the base in eval mode. Only candidate native gates train. Native eligibility forces every noncandidate entry, including finer attention/MLP gates and full-layer/block gates, exactly open. Whole MLP candidates use the decoder block gate. Candidate open probability initializes to the approved 0.95 through the unchanged native distribution formula. `support_for(model)` reconstructs support after copying a configured model. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a3.md`.
- `MaskChunk(ids, baseline_margin, baseline_logits, payload, token_counts, split='train')` binds ordered ids and both designation streams. Margins/token counts are shaped `[ids, 2]`; logits are `[ids, 2, vocabulary]`. D baseline logits can be absent. Non-train chunks, duplicate/mismatched ids, mismatched paired token counts and malformed targets fail. Task 5b must supply admitted immutable train membership; a split label alone cannot authenticate an external source.
- `native_chunk_forward(model, chunk)` consumes payload keys `input_ids`, `neutral_input_ids`, `attention_mask` shaped `[ids, 2, sequence]`, plus canonical `opposite_ids`/`honest_ids` shaped `[ids, 2]`. It flattens the paired streams into the actual dual-stream native wrapper using each condition's supplied neutral donor. It returns `margin`, differentiable FP32 analysis `logits`, and diagnostic `native_logits`, all at each row's final unpadded token. The established A3 differentiable readout supplies the FP32 norm and unembedding.
- `mask_objective` retains the planned full-cohort D suppression hinge, I preservation coefficient 4, intact-to-patched KL coefficient 1, and candidate-only removed-probability coefficient 0.01. All intact targets and the D/H baseline gap detach. The optional `constrained=False` removes only the I penalties. The algebraically identical D argument uses a difference-first FP64 reduction to preserve the exact zero subgradient at a chunk-independent kink. No denominator is clipped. `epsilon` defaults to the inherited A1 floor of 1e-6; Task 5b must supply the calibrated `max(1e-6, 10 * maximum self-replay error)`. Sources: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a3.md` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-ladder.md`.
- `streamed_update(model, support, optimizer, d_chunks, i_chunks, forward, *, g_d_fit, identity, constrained=True, epsilon=...)` performs exactly one update with the approved Adam learning rate 0.01 and native Adam defaults. It records CPU/all-available-CUDA RNG immediately before each first-pass D chunk, actual sampled gate values and margins, then replays unchanged parameters/chunks with immediate backward and graph disposal. It additionally asserts the post-chunk RNG path. It restores the post-first-D-pass RNG before fresh I draws, streams I backward, differentiates the candidate regularizer once, and steps once. Returned diagnostics include the full-cohort hinge, preservation/KL/removal values, CPU gradient tensors and D/I RNG/gate banks. Failed updates require checkpoint restoration; their state cannot be checkpointed as a completed boundary. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a3.md`.
- `make_checkpoint(..., identity, update)` returns an independent state dictionary for Task 5b to write atomically. `restore_checkpoint(...) -> completed_update` checks source identity, actual frozen base-weight bytes, ordered chunk boundaries/ids/token counts/payload/targets, native gate support/eligibility and update boundary. Checkpoints carry all gate state, Adam state, CPU/CUDA RNG and the frozen loss arm/gap/epsilon/source/chunk configuration. Changed configuration is rejected before the resumed next update.
- `export_removal_mask(model, provenance=...)` returns schema `a3-removal-mask-v1`, ordered `candidates`, binary `keep`, exact complementary `removed`, and copied `provenance`. It temporarily calls each candidate native gate in eval mode and restores its mode. It never calls a density/count helper or probability cutoff.

Review follow-up to `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report93-a3-mask-review-handback.md`: the numerical core now authenticates the complete cohort before and after every callback and before Adam, including targets, payloads, token counts, ids, order and chunk boundaries. Changes are rejected immediately after the mutating D callback, before I consumes the changed target; failed-update checkpoints remain prohibited. Checkpoint identity now includes effective model/config/module runtime settings, normalization epsilon, attention implementation/dropout settings, non-gate buffers, public tensor attributes, implementation versions and precision/backend settings. In-update computation fingerprints catch mutations of these settings and tensors. Full frozen weight-byte hashing occurs only at checkpoint construction/restore, while existing parameter-version guards cover callbacks. Authenticated completed-boundary checks reject a source or target changed after a successful update. No objective, coefficient, RNG replay or export rule changed.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_a3_mask.py
```

Observed initial acceptance output: `24 passed in 7.62s`; exit zero, no skips.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_a3_mask.py
```

Observed initial acceptance output: `24 passed, 3 warnings in 15.13s`; exit zero, no skips. Warnings concern the external transformers cache variable, TensorFlow ml_dtypes alias and pandas bottleneck version.

```bash
/u/swong2/.local/bin/ruff format component_analysis/a3_mask.py tests/test_a3_mask.py
/u/swong2/.local/bin/ruff check component_analysis/a3_mask.py tests/test_a3_mask.py
```

Observed: two files reformatted, then `All checks passed!`; exit zero.

Test-first evidence: initial collection failed on the missing core module. The first implemented run had eight passing tests and two exact-kink failures caused by floating-point reduction; difference-first FP64 arithmetic and exact paired target construction resolved those failures. Later checkpoint-boundary, hidden-extra-RNG-draw, native-distribution-buffer mutation and resume-configuration tests each first failed to raise before their corresponding assertions were implemented. Final scoped tests include those regressions.

The retained-graph oracle compares every candidate gate tensor's gradient, next parameters and Adam step/first/second moments against streaming for active, inactive and exactly kinked full-cohort D hinges, both constrained and unconstrained arms, unequal final chunks and two designation streams. Opposing per-chunk hinge arguments catch an independent-minibatch-hinge substitution. Terminal CPU RNG states match. Direct native-margin gradients are nonzero without the regularizer, and all frozen source weights remain unchanged.

Independent native eval hooks capture fixed neutral-donor head slices and whole-MLP outputs. Their removed-node forwards match native dual-stream exports for D and I, all retained, single head, single MLP and all candidates removed. Supplying the other condition's neutral donor changes the outputs. Tests exercise the native probability/eval discrepancy interval, strict eval-cutoff tie, exact hard-open noncandidates under extreme logits, matched rows/tokens, frozen targets, support identity, source-byte changes, exact resumed next-update parameters/RNG, forbidden non-train chunks and parameter/distribution-buffer mutation between D passes. Parameter versions, gate-buffer versions and module train/eval states stay fixed through both D passes and I backward.

```bash
/u/swong2/.local/bin/research-session lint docs/research/specificity-ladder/reports/report90-a3-mask-core-handback.md
/u/swong2/.local/bin/research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report90-a3-mask-core-handback.md
/sw/external/python/anaconda3/bin/python3.9 scripts/check_report_numbers.py docs/research/specificity-ladder/reports/report90-a3-mask-core-handback.md --strict
```

Observed: both Markdown lints exited zero; numeric-source audit resolved every listed prose number with no unresolved entries. The primary report is byte-identical to the worktree report.

After the review fixes, the same scoped pytest commands above were rerun on both interpreters. Latest mgnp output: `43 passed in 15.69s`; latest base output: `43 passed, 3 warnings in 19.21s`. Both exited zero with no skips. The warnings remain the external dependencies identified above. Ruff formatted the two owned Python files and then reported `All checks passed!`.

Test-first follow-up: seventeen added cohort/effective-computation cases first produced `17 failed, 24 deselected in 7.46s`. Two additional stale completed-boundary cases first produced `2 failed, 41 deselected in 7.03s`. They all pass in the final scoped runs. The cases cover I margin/logit mutations, donor payload/tokens, ids/order/boundaries, final RMSNorm epsilon, attention dropout/backend, config, rotary buffers, immediate rejection before I/Adam, and prohibition on checkpointing a failed update. Source/settings changes at completed boundaries also fail before checkpoint construction.

The unchanged independent reviewer reproduction was run in each interpreter with the wrapper below, substituting the corresponding interpreter path from the scoped commands above. Its previous final line expected changed-epsilon acceptance, so the wrapper accepts only the newly required source-identity rejection. No reviewer source was edited.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python -u - <<'PYCODE'
import runpy
try:
    runpy.run_path('docs/research/specificity-ladder/reports/report93-mask-review-repro.py', run_name='__main__')
except ValueError as error:
    assert str(error) == 'checkpoint source/support/chunk identity differs', str(error)
    print('EXPECTED_CHANGED_NORM_EPSILON_REJECTION', str(error))
else:
    raise AssertionError('independent changed-epsilon reproduction was accepted')
PYCODE
```

Observed in each interpreter: the independent scalar-loss oracle passed all six active/inactive/kink by constrained/unconstrained cases, including gradients, next parameters, Adam state and CPU RNG. Maximum gradient error remained `2.9103830456733704e-11`. The data mutation printed `mutation_rejected RuntimeError cohort mutation during streamed update`; the failed checkpoint printed `FAILED_CHECKPOINT_REJECTED`; changed final norm epsilon printed `EXPECTED_CHANGED_NORM_EPSILON_REJECTION checkpoint source/support/chunk identity differs`. Both wrapper commands exited zero. The base wrapper also emitted external TensorFlow duplicate-factory and protobuf MessageFactory startup messages before the successful oracle checks; no GPU execution was performed.

## Execution evidence

- Job and cluster: the local CPU pytest commands above; no Slurm, GPU, production weight or real-data training run.
- Exit codes: both final scoped pytest commands and Ruff exited zero.
- Counts: twenty-four synthetic/tiny-model cases ran against twenty-four expected on each interpreter, with no skips.
- Baseline assertions: intact D mean 1 and H mean -1 give a gap of 2; patched D mean 0.5 incurs suppression 0.5, and mean 0 incurs zero. Intact D mean 3 and H mean 1 require patched mean at most 2. Native all-retained logits match independently copied intact native weights; all-candidate removal matches independent fixed-donor native hooks. Sources are the owned tests listed above. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_mask.py`.
- Provenance: no scientific `run_manifest.json` or execution commit was produced. Root owns source freeze, independent review and run admission. These CPU contract checks establish no scientific efficacy, timing, benchmark or replication result.

- Review-fix counts: forty-three observed cases against forty-three expected in each interpreter, with no skips; all six independent mathematical oracle cases passed in each interpreter. Maximum oracle gradient discrepancy and both requested rejection outcomes are reported above. This remains tiny local CPU implementation evidence without a scientific run manifest.

## What is NOT done

Task 5b retains full-data orchestration and `train_constrained`: immutable A1/A2 lineage admission, historical exclusion and protected/test-id source checks, full matched train/validation construction, intact D/H gap estimation and self-replay calibration, scientific seed scheduling, the complete planned 200 updates in both arms, validation every 20 updates, earliest accepted checkpoint selection with the unchanged collateral gates, atomic checkpoint files, controls/random subsets, New30 provenance/comparison, transfer assessment, Slurm stages and operational cost admission. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a3.md`.

Only caller-declared train split admission is implemented here; the numerical core cannot prove whether an externally relabeled id belongs to a protected assessment registry. CUDA RNG capture/restore paths exist but were not exercised on hardware. No production precision/backend parity, GPU memory/runtime claim or 200-update scientific result is made. No broad suite or notebook was run, as assigned. Source for the deferred update count: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a3.md`.

All numbers in this report are approved plan settings, inherited A1 numerical guards, tiny synthetic fixture expectations, schema dimensions or observed local test counts/timings. None is an empirical research-effect or compute-budget estimate.

## Open questions

Both report93 exactness blockers are addressed; independent acceptance remains with root. No blocking implementation question remains for Task 5a. Default: independently review the two owned code/test files, commit by explicit file list, then implement Task 5b only under root's frozen scientific scope and runtime admission. The driver must pass the calibrated denominator epsilon and full immutable source identity, supply condition-correct neutral donors, construct the fixed Adam optimizer from `MaskSupport.parameters()`, preserve paired chunk order and restore a completed checkpoint after an interrupted/failed update.
