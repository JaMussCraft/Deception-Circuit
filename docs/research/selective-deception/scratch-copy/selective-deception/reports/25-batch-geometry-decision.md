# Numerical extension: paired batch geometry and autograd floor

2026-10-18; narrow advice before fitting. Root reports Stage 1 full evaluation running, ticket 03 passed, and ticket 04 under CPU implementation. This review performed no real-model forwards, jobs, GPUs, APIs, code changes or git operations. It extends the prefit numerical contract without changing the scientific loss, data, candidates or four-rho design.

## Decision: one joint pair everywhere

Freeze **joint_pairs=1** for this pilot. Reference-cache construction, optimization and deterministic validation all receive the same ordered two-row batch `[D,H]`, with batch size two, the pair's exact unpadded length, identical position/attention-mask conventions and the same tensor layout. Do not build reference logits one row at a time while fitting or validating joint pairs. Do not pad unrelated lengths together or dynamically increase the batch size for validation. Use gradient accumulation for an effective batch larger than one pair, preserving the already specified D/H and capable-stratum denominators.

Reference baseline uses the validated dual-stream, all-open, self-donor path. Masked training/evaluation uses the frozen shared nonself-H donor twice, once for each recipient twin. All-open equivalence between those donor assignments is an explicit control, not an assumption. Capability flags are derived only from the corrected batch-two baseline. Old per-row caches are incompatible and must be rejected/rebuilt; do not reuse their flags merely because most labels agree.

Freeze and fingerprint ordering, batch size, per-row length, padding, position IDs, dtype, attention implementation, device/GPU/software identity and `use_cache=False` for readout scoring/training. Confirm attention and other relevant dropout probabilities are zero: `model.train()` must still enable the stochastic gate path, so global `model.eval()` is not a fix for a dropout discrepancy. Deterministic validation baseline and masked forward both run without gradients and with identical geometry. Record training-versus-validation module/gate modes explicitly.

## Minimal calibration addition

Yes: use the already planned root-submitted training/export calibration to measure an **all-open gradient-enabled numerical floor**, rather than adding a backend-selection framework or redesigning the gate primitive. Select fixed structural representatives of each observed length signature before outcomes (and record them); no favorable-row selection. For each representative use this ladder:

1. `N_self`: no-grad, dual-stream, self donor, all heads exactly open, batch `[D,H]`.
2. `N_nonself`: no-grad, the actual frozen nonself donor, all heads exactly open, otherwise identical.
3. `G_nonself`: gradients enabled, same actual donor and batch, gates forced to an all-open **forward value while retaining the existing STE/autograd dependency**.

The third case must exercise the graph that the real gate-trained model would have. Merely writing constant one gates that detach the clean path, toggling global eval, or inspecting gradients only after a no-grad forward does not test the suspected dispatch difference. Use existing test/calibration gate-control facilities; if none safely preserves the STE graph, report that missing calibration capability rather than claim the graph path was tested. This is a diagnostic override, never the training sampler or a new optimization mode. Save/restore RNG and gate state so calibration does not silently change the frozen fit initialization/sequence.

Compare N_self→N_nonself to isolate donor-path identity; compare N_nonself→G_nonself to isolate graph/dispatch effects. Report max/mean full-vocabulary absolute readout difference, changed entries, D/H label logits/probabilities, full-vocabulary argmax and truthful-capability changes, H NLL nondegradation and KL floor, and target-surrogate change. Compute diagnostic softmax/log/aggregate losses in fp32 from the actual logits, matching the training loss implementation; printing only rounded scalar loss hides the original BF16 discrepancy.

Include a same-path repeated no-grad baseline check on these representatives to distinguish dispatch effects from nondeterminism. The baseline cache must be constructed from the same paired function used by this check. During cache/validation construction, assert every batch really is one aligned D/H pair and that all expected IDs/readouts are present. Where all-open validation is already part of calibration, check the entire frozen validation set, rather than accepting a no-op on only one convenient example.

On the gradient-enabled all-open path, perform the existing one-backward calibration with actual nonself donors and the real objective. Confirm finite loss, finite candidate gradients, zero noncandidate gradients and no base-weight gradients; at least one candidate should receive a nonzero gradient when the chosen diagnostic loss has a nonzero signal. Do not require the KL-only gradient to be nonzero at exact identity. The all-open target loss can still drive gate gradients because changing a gate would introduce a different donor state. This check can share the existing tiny calibration workload rather than becoming another training run.

## Pass/fail interpretation — explicit prefit clarification

**The existing Stage 1 score tolerance is absolute 0.02 on the two semantic D/H label logits, not on the maximum over the full vocabulary.** Retain that scope. This clarification does not introduce a new full-vocabulary 0.02 cutoff or retrospectively describe one as frozen. Applying such a cutoff would be a distinct stricter amendment, and it is not recommended: a large error on a negligible-probability token can be irrelevant to both decisions and retention KL.

The calibration's enforced checks, for each comparison in the ladder and repeated no-grad identity, are:

- Maximum absolute difference over the D and H label logits on both recipient rows is **≤0.02**, with no relative-tolerance allowance. Compare float32-cast logits to the declared decimal threshold to avoid a BF16 representation of the threshold silently changing it.
- Full-vocabulary argmax and resulting truthful-capability flags are unchanged, using the same deterministic tie convention.
- Readout logits and computed diagnostic losses are finite; the gradient-enabled backward has finite candidate gradients, zero noncandidate gradients and no base gradients as specified above.

A violation blocks fitting for focused diagnosis. The previously observed 0.125 **label-logit** difference fails this rule. A 0.125 difference confined to another vocabulary token does not by itself fail it. Record exact equality where actually observed, but do not require bitwise full-vocabulary equality as an undisclosed condition. Backend, precision or graph-policy changes require an explicit config/fingerprint change and rerunning these same checks; no hidden tolerance widening or automatic fallback.

The following are **diagnostics without a newly invented pass/fail threshold**: full-vocabulary maximum/mean drift and count of changed entries; full-distribution H KL; D/H probability shifts; H truth-NLL nondegradation floor; and D target-surrogate floor. Compute them in fp32 using the same loss direction and formulas as training. Report both each representative and the aggregate. Do not call a large full-vocabulary max a failure of the 0.02 label contract, and do not say passing the label contract proves zero distributional drift.

The root receives the measured KL/NLL/target floors before releasing fitting; they are not discarded or subtracted from losses. A visibly consequential distributional discrepancy warrants a focused numerical diagnosis or a recorded configuration decision, not a claim that this gate certified KL fidelity. No new numerical KL cutoff is asserted here. If later retention or suppression effects are comparable to their corresponding measured floor, report those effects as numerically unresolved rather than claim a selective frontier gain. Compare like units (KL to KL, target-loss change to target-loss floor), not a raw logit maximum to a loss. Zero-removal/no-op results remain identity controls and cannot be presented as causal intervention benefit merely because a floating-point surrogate shifts.

Deterministic checkpoint comparisons continue to use matched no-grad geometry. This calibration establishes label/decision consistency plus a measured distributional floor; it does not establish universal equality between no-grad and graph-enabled forwards.

## Scope

The correction is small: share the paired batch constructor, invalidate incompatible caches, add shape/no-op tests and a fixed calibration report. Existing eligibility, losses and binary export stay unchanged. No production optimizer steps or batch launch are authorized by this review. Root alone controls calibration submission and charges it, including these checks, to the existing cumulative 20 GPU-hour ledger. Stage 1 behavioral validity and the frozen prefit capability/generation gates remain required; numerical consistency alone does not release training.
