# Stage 1 smoke score-identity numerical review

Reviewed frozen commit `ef8cc2a94b99fc15ef5d68ca00304274fbdb70ed` and `outputs/selective-sdr-stage1-r1/run/` after job 22994204. No source edits, pretrained weights, GPU/API/job execution, git mutations or subagents. Used systematic debugging and one tiny random CPU BF16 diagnostic (repeated once while collecting its asynchronous output). Root remains responsible for any follow-up GPU probe.

## Decision

**Keep the full-run numerical gate closed; do not widen 0.02 post hoc.** There is a confirmed implementation-level mismatch between intact and intervened scoring paths. A causal-mask/SDPA dispatch explanation is strongly supported, but the existing smoke does not contain the all-open dual-self control needed to prove it caused the A100 differences. The next action should be a small discriminating forward-only probe on the same A100/runtime, not a larger diagnostic run.

This does not invalidate the four exact generation identities: intact generation already uses dual-stream cached decoding. It also does not establish wrong mask composition. Saved masks remain core43, comparator33 and random43 with zero MLP hidden/output membership, and failing identity donor token sequences exactly equal their recipients.

## Quantified smoke evidence

All four original score identity comparisons keep the same full-vocabulary argmax token. All four generation identities pass exact token equality. Two of four score identities fail the frozen absolute0.02 logit criterion.

Cluster `31fc797e12eac00fa036eed46c7525b372d64c9f4f3f596e7e43041320d6a883`, prompt length113:

| recipient / self condition | quantity | intact | self intervention | self−intact |
|---|---|---:|---:|---:|
| D / core_deceptive_clean | D logit |25.625|25.5|−0.125|
| D / core_deceptive_clean | H logit |23|22.875|−0.125|
| D / core_deceptive_clean | D−H margin |2.625|2.625|0|
| D / core_deceptive_clean | P(D) |0.9311157465|0.9311751723|+0.0000594258|
| D / core_deceptive_clean | P(H) |0.0674498007|0.0674541071|+0.0000043064|
| H / core_honest_clean | D logit |22.25|22.375|+0.125|
| H / core_honest_clean | H logit |23.875|23.875|0|
| H / core_honest_clean | D−H margin |−1.625|−1.5|+0.125|
| H / core_honest_clean | P(D) |0.1637207121|0.1815628707|+0.0178421587|
| H / core_honest_clean | P(H) |0.8314424157|0.8137083650|−0.0177340508|

Argmax IDs remain18496 for D and10716 for H. BF16 spacing in the [16,32) bin is0.125, so each changed label logit moved by one representable BF16 step. That alone does not make the result ignorable: the H row's P(D) changes by **1.784 percentage points**, and its margin changes. D's common logit shift mostly cancels in the label ratio, while small other-vocabulary changes still affect normalization.

For cluster `10c5a0db67b79f57f6f146ad3e2441debfe9e9f86d2b044eb197c86ecfb71a90`, length116, both D/H label logits and margins match exactly. Full-vocabulary P(D) still changes by−0.0000066757 for D and−0.0000174344 for H, showing that passing a two-label logit check does not prove whole-logit-vector equality.

## Exact source path

1. `evaluation/selective_runner.py:216` supplies `corrupted_input_ids` only if the row has a donor. Intact target and donor-score diagnostics therefore omit it; self-mask rows supply it. Both call the evaluator with `use_cache=False` (`evaluation/metrics.py:121`).
2. `models/llama_node.py:574` selects `super().forward` when no corrupted input is present. The installed Transformers5.13 `LlamaModel.forward` calls `create_causal_mask` at `.../transformers/models/llama/modeling_llama.py:399`.
3. The custom uncached dual stream instead falls through to the manual BF16 4D triangular mask at `models/llama_node.py:727–752` (the installed model lacks `_update_causal_mask`). Cached generation uses `create_causal_mask` at line715, so it avoids this particular intact/intervention split.
4. In installed `.../transformers/integrations/sdpa_attention.py:29`, `use_gqa_in_sdpa` depends on whether the mask is None. At line78 `is_causal` also depends on mask absence. Thus equal mathematical causal support is passed through different SDPA arguments: implicit causal/GQA versus explicit additive mask/repeated KV.
5. Gate application itself uses binary masks, final-circuit mode and exact open/closed values (`analysis.py:690–761`). The single-stream attention bypasses gates; dual-stream attention gets pre-output-projection values and mixes them with the donor (`models/llama_node.py:239–281`). For identical finite streams and binary gates this should be an identity *within the same forward path*. Its comparison to a different path is the unresolved numerical confound.

## Tiny CPU BF16 discriminator

Used the existing random two-layer64-hidden/4query-head/2KV-head/vocab101 model, explicit `attn_implementation='sdpa'`, BF16, lengths113 and116, unpadded fixed token sequences, and the existing heads-only knockout. Instrumented the SDPA call in-process; no repository code changed.

| variant | SDPA mask | is_causal | enable_gqa | KV heads entering SDPA |
|---|---|---|---|---:|
| single, all open | None |True|True|2|
| dual self, all open |BF16 [1,1,L,L]|False|False|4|
| dual self, core-like knockout |BF16 [1,1,L,L]|False|False|4|
| single, all open, explicit same4D mask |BF16 [1,1,L,L]|False|False|4|

All four last-position logit vectors were bitwise equal for both CPU examples (max absolute difference0). This confirms the dispatch difference and the same-path identity in the tiny model; **it does not reproduce or prove the A100 rounding mechanism**. Actual CUDA kernel selection was not recorded in the smoke, so attributing the result to one named CUDA kernel would exceed the evidence. Raw trace copied beside this report as `10-smoke-numerics-tiny.log`.

## Minimal discriminating GPU probe

Root may reserve one15-minute/1GPU job (0.25GPUh) on the same A10040GB with mgnp/torch2.11.0+cu128/transformers5.13.0 and the frozen model snapshot. Load one model, no generations, no selection change, no new data, no paid calls. Use the two existing smoke clusters × D/H original recipients = four prompts.

For each prompt run these four variants, all uncached:

- **S:** ordinary intact single-stream, all gates open.
- **B:** dual stream with identical self input, all gates open.
- **C:** dual stream with identical self input and the actual core knockout; verify applied gate masks.
- **E:** ordinary single-stream all-open, but supply the same explicit BF16 [1,1,L,L]0/−inf causal mask used by the uncached dual path.

That is16 forwards. Repeat B and C once per prompt to check stability:24 forwards total. Save the complete last-position vocabulary logits, D/H logits/probabilities/margins/argmax, tensor dtype, finite checks, actual gate counts and first-layer SDPA arguments (`attn_mask` shape/dtype, `is_causal`, `enable_gqa`, KV shape). Match S/C against the saved smoke and report max-absolute/equality for B−C, B−E and S−B; record repeats independently. Place probe outputs outside the immutable run store.

Interpretation is predeclared:

- If B and C match exactly, E matches B, and S differs from B with the observed direction/magnitude, the attention-mask/dispatch path explains the failed cross-path score identity. Keep 0.02 unchanged; the appropriate identity test becomes same-path B versus C.
- If B differs from C, do not call it merely single/dual drift. Inspect exact binary gates and earliest divergent clean/corrupt layer, with repeated-run stability. Full-run gate stays closed.
- If B=C but E differs from B, the issue is broader than causal-mask dispatch; investigate the other single/dual arithmetic differences before changing production scoring.
- If the original S/C result does not reproduce, first account for runtime/hardware/model/attention configuration and repeat stability. Do not approve based only on a new passing pair.

## Conditional minimal correction

Only after the first probe outcome: make the runner's no-donor scoring baseline supply its own input as the corrupted stream under all-open gates, for both intact recipient and intact donor score rows. This keeps the existing intervention scoring path, labels, masks, prompts, decoding and thresholds intact, and compares interventions against the same numerical implementation. The probe retains the inherited single-stream result as an explicit equivalence diagnostic against the original scoring path.

Add a targeted regression asserting that no-donor score forwards receive identical clean/corrupt input, and a BF16 same-path self-mask test. Do not alter the shared training/dual-stream implementation merely to change its historic uncached mask behavior, and do not loosen the numerical threshold. Source changes require a new recorded source/run fingerprint and fresh validated outputs; preserve the existing smoke and its failed gate as evidence. Carry the exact frozen sample/prompt/donor assignments forward, with no outcome-driven reselection or filtering. Do not bypass ResultStore fingerprint protection to mix revised baselines into the old run.

## Evidence identities

Smoke manifest hash `29da71bd7cef5f03bec931e5a4231cb93b3bfb026ce3b00f1ea3367a6aab95a0`; run fingerprint `7cc1959473ba42178c6bb75e75863207930a29776e141dea8ada7988cf76c499`.

| artifact | SHA256 |
|---|---|
| run.json |`2785e09083c9d7d1cd3899f6da13f31100eb42f67841b8541ed2214e7966bb5c`|
| summary.json |`aad7ffe03cf04bb747dc87becb6398bba6fa35cecb1504797e3cf4ce2322c418`|
| results.jsonl |`1f3628e811aa506b57bade49922b56b67cdd164a72e00cdf81ec04dd746ecf23`|
| evaluation/selective_runner.py |`31f48bb84ac0c86c6588f53de2c189506ab12df6d2c6e540585d188607059b27`|
| evaluation/metrics.py |`a55b70d8e9261b821880b83f53b12bfa30968243f10988e18096ca40e021a710`|
| models/llama_node.py |`2c48ae2c3cd470436889f4d0420a4b027cd1eb3bcfafc277bf92142c5d9d4644`|
| evaluation/context.py |`8ebd56ceb638644e9c681d3e6650933ad28ab050b8910862856fd843527899d3`|
