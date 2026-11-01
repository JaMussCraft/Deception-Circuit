# Zero-ablation interface audit — root fallback

Explorer worker failed at model capacity. Root inspected only the required dispatch and mask paths; no model execution.

`evaluate_selective_deception.build_context` hardcodes cli.ablation=interchange. More importantly, `selective_runner.generate_row` calls `gen_engine.generate` without a hook, so changing cli.ablation alone would not implement zero. The generator takes an explicit `hook` argument and installs it internally with `ablation_hook`; an outer hook can be overwritten. The new thin generation adapter must pass `evaluation.ablation.ZeroHook()` directly, preserving the existing native decode, EOS, placeholder-corrupt and quality parsing.

ZeroHook returns a broadcast scalar0 on the activation dtype/device for every gated site. `tests/test_evaluation.py::test_t4_empty_circuit_with_zero_ablation_is_embedding_only` verifies empty-zero logits equal the embedding-only path. `test_gen_engine.py::test_the_padded_path_holds_under_every_ablation_scheme` covers generation dispatch. Focused tiny-model tests in the new adapter must verify actual zero semantics, not merely a config string. All gates open plus ZeroHook should reproduce the prior baseline; the real run must complete and verify all32 intact token/EOS identities before any knockout, stopping on mismatch.

`selective_runner.resolve_masks` freezes core=(D&H)-m,43heads, and random_core_seed0 sampled withseed0/index0. `sample_random_masks` matches counts layer by layer and copies block allocation. `safe_knockout` produces keep masks and explicitly verifies retained MLP gates. No donor scores are appropriate here; no donors are used.

Actual frozen core/random supports each contain43heads and have identical layer allocations (layers7,8,9,10,11,12,13,14,17,24 counts4,7,4,4,4,5,4,4,2,5). Their overlap is 4heads. Both supports and full initialization provenance are already bound in transfer-v1 manifest; the new protocol pins their exact hashes.

Root-owned new wrapper is analysis/fixed_zero_transfer.sbatch, oneA100/onehour/no-requeue, guarded mgnp environment with APIkeys unset. Worker source must bind this wrapper. No job reservation or launch has yet occurred at this audit.
