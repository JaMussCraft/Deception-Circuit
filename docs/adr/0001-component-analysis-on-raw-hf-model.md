# ADR-0001: Component analyses run on the raw HuggingFace model under nnsight, not on the prunable wrapper

Date: 2026-09-15
Status: accepted

## Context

Every circuit in this repo is discovered and evaluated through
`PrunableLlamaForCausalLM`, a wrapper that replaces attention and MLP modules
with gated versions and runs a dual clean/corrupt stream. The component-level
analyses (attention patterns, direct logit attribution, logit lens, per-head
knockout, path patching) need per-head outputs, per-head Q/K/V inputs, MLP
inputs and the unembedding, at chosen positions, in the *full* model
(decided in the 2026-09-14 grilling: measure in the full model first,
in-circuit only as a check).

## Decision

The analyses load the unmodified `LlamaForCausalLM` and reach every sender and
receiver through nnsight 0.7.0 at HuggingFace module boundaries
(`embed_tokens`, `o_proj` input, `q_proj`/`k_proj`/`v_proj`, `mlp`, `lm_head`).
Eager attention is switched on only for attention-pattern extraction; every
other analysis runs under SDPA. Ranking metrics are read through an fp32 final
norm and unembedding. Circuits enter as mask objects through the existing
binding and set-algebra layer and are coarsened to Components; the wrapper is
never instantiated.

## Alternatives

- Reuse the wrapper and its ablation hooks. Rejected: the wrapper only exposes
  gate sites (post-head output, MLP hidden/output), not Q/K/V inputs, and its
  dual-stream forward doubles the cost of every analysis that needs one stream.
- TransformerLens 3.9. Rejected: requires transformers >= 5.9, forces eager
  attention on every run, deprecates the API third-party patching utilities
  depend on, and changes DLA/logit-lens numerics in compatibility mode.

## Consequences

- Two model-loading paths now exist in the repo. Any change to how a circuit
  is *defined* (mask format, coarsening rule) must be mirrored in the analysis
  package's coarsening; the tests assert agreement with `evaluation/masks.py`.
- In-circuit analyses (complement ablated) cannot reuse the evaluator's hooks
  and must reimplement interchange ablation as nnsight interventions.
- GQA: Llama-3.1-8B has 8 KV heads, so K and V receivers are per KV group of
  four query heads, not per head. The head table records each head's group.
- nnsight 0.7.0 is pinned; its main branch is the 0.8 rewrite. The hook
  surface is confined to one module so a migration touches one file.
