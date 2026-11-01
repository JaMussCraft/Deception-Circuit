# Ticket 04 independent spec, correctness and resource review

Verdict: **REQUEST CHANGES before production receipt creation** for one important provenance defect. No critical objective, gate-state, resume, geometry, reference-reuse or export defect was found in the frozen implementation. This review owns only this report; no source edits, git operations, real weights/models, GPU work, submissions, APIs or notebooks were used.

## Important finding: runtime loader is absent from source fingerprint

`evaluation/selective_mask_runner.py:425-432` hashes the CLI, l0, analysis, config, wrapper and evaluation/models/dataset/tasks Python files, but omits `evaluate_selective_deception.py`. That omitted file is imported by `_identity` at line 436 (`cached_snapshot`) and `_runtime` at lines 460-471 (`build_context`). Its runtime behavior includes local snapshot selection, model/context construction, geometry and dropout disabling.

An edit to that file can therefore change actual execution while `_source_files`, the root source-content receipt, baseline/cache fingerprint, checkpoint fingerprint and result provenance remain unchanged. `source_revision` is copied from the receipt; it neither detects nor binds dirty content in this omitted dependency. This breaks the ticket's exact behavior-input resume contract. The worker independently disclosed the same issue after freezing source in report21; this review confirms it from the runtime import chain.

Required narrow correction: include this specific runtime dependency in `_source_files`; add a CPU regression proving its file digest contributes to source identity and changed loader content causes the old receipt/fingerprint to be rejected. Recompute source hashes/receipts after correction. No broad repository hashing framework is needed.

## Reviewed behavior

- The runner consumes the primitive `pilot_loss`, candidate configuration and export, keeps all pairs, uses one `[D,H]` pair with the same nonself H donor, and applies accumulation weights using complete-window D/H and capable counts. Sparsity is charged once per update. AdamW and clipping settings match the frozen design.
- `_gate_state` enumerates actual `HardConcreteGate` module states, excluding SwiGLU `gate_proj` and frozen base weights. Candidate eligibility masks isolate gradients; exports retain noncandidates and remove no MLPs.
- Reference caching and deterministic validation share `_joint_logits`, exact unpadded batch-two geometry, no-grad mode and `use_cache=False`; training keeps stochastic gates active. Calibration uses forced-open STE hooks with a live graph, fixed length representatives, repeated no-grad controls, label-only .02 decisions, full-vocabulary/loss-floor diagnostics, frozen-base checks and no optimizer step. Root must still inspect actual measured floors before fitting.
- Complete-update checkpoints persist gate/eligibility, optimizer, fixed ordering/cursor/history and Python/NumPy/Torch/CUDA RNG. Actual tiny loop interruption/resumption tests cover accumulation/update continuation. Completed payload corruption is rejected. Selection preserves all-H and capable-H accuracy, requires actual removal and lower D surrogate, then size/earliest tie breaks; selected export is restored and checked.
- Baseline, calibration, training and final evaluation have separate receipt gates. Learned manifests retain nonself clean-H endpoints instead of accidentally adopting intact templates, fresh mask/row/reference identities, and selected-checkpoint provenance. Final assessment remains a root-frozen decision.
- Shared donor reference store identity excludes rho/optimizer/receipt state while binding intact execution plus exact frozen reference manifest/decode. Baseline and all four safety finalists reuse the same frozen donor closure, bounded at 16 references; targets remain separately fingerprinted. Existing ResultStore enforces exact rows, complete-record integrity and incomplete-trailing-write recovery.
- Wrapper is one GPU, A40 default, 20 minutes, no-requeue, guarded shell/conda activation and offline CLI execution. No grid, retry or scheduler submission is embedded. No production budget is inferred from CPU tests.

## Independent verification

From the pilot worktree, with OMP/MKL/OpenBLAS threads pinned to one and HF/Transformers offline, independently ran:

`<python> -m pytest -q tests/test_selective_mask_runner.py`

- `/sw/external/python/anaconda3/bin/python`: **34 passed**, 3 existing dependency warnings, 19.78s.
- `/u/swong2/.conda/envs/mgnp/bin/python`: **34 passed**, 19.60s.

These include actual tiny optimization interruption/resume, accumulation-denominator equivalence, forced-open calibration state/RNG restoration, source-independent fingerprint refusal primitives, real shared ResultStore reference reuse, gate-only checkpoint size/ownership, derived donor plumbing and wrapper execution with stubs. The worker reports 130 focused tests in each environment and actual tokenizer-only prepare; those broader claims were read in report21 rather than redundantly rerun. No untouched/full repository suite was run.

After the narrow provenance correction and focused regression, this review has no other important implementation change request. Production remains subject to the root's behavioral, capability/headroom, numerical, measured-cost and ledger gates.

Root closure: worker scopedfix includes evaluate_selective_deception.py in explicit runtime-source list, plus regression changing only its bytes and exercising stale-receipt rejection through actual _identity. RED/GREEN archived reports/21-artifacts/pilot04-loader-*. Focused35passbothenvs; actualwrapperdryrun passed. Final integratedsuites inprogress; no productionrelease implied.
