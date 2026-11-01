# Independent bounded native replay helper review

2026-10-19. **PASS for the bounded CPU helper implementation. No source blockers found.** This is a source/test review and additional tiny-model verification; physical native assessment, caller correctness, actual GPU memory/runtime and scientific efficacy remain unproven.

Reviewed `Deception-Circuit/.claude/worktrees/selective-native-replay/evaluation/native_interchange.py` and `tests/test_native_interchange.py` against reports 61 and 65. Helper SHA256: `483482914d1ff217c4bfcdc5b8f8f237a76a468f557314f03c5111bd392176d9`. Read supporting model/gate/fixture definitions to verify the hook contract. No source, test, historical generation path, training source or git state was changed. No real model, GPU, network or API was used. The existing 24 focused cases and affected historical regressions in both supported environments are documented in report 65; the reviewer did not repeat that suite.

## Confirmed implementation behavior

- Donor capture forwards its actual generated token to both streams on the next step, with separate lockstep caches, all-one masks and its own monotonically increasing positions. The hook reads intact corrupted-stream head outputs before `o_proj`; it does not alter the corrupted stream. Captured continuation query zero is the query on the first emitted token, not the query predicting that token.
- Prompt replay uses the exact right-aligned valid intersection. An unmatched earlier recipient prefix is causally untouched: all earlier positions are also unmatched, both input streams are identical, and every nonhead gate is hard-open. Existing tests check hidden-state equality through every layer and exact mapped bank values for both length orderings. Mapped suffix entries are indexed bank tensors rather than shadow references.
- The explicit generation loop selects the last donor prompt query at t=0 and query `Ld-1+t` at t>=1. Each prediction consumes the previous generated token in the recipient cache. First-token/early EOS stops capture without forwarding EOS; subsequent recipient steps hold the query that predicted donor EOS. Cap-terminated banks contain exactly `Ld+K-1` queries and reject insufficient requested coverage. Existing tests genuinely exercise recipients outliving the donor, rather than merely computing an unused hold index.
- The execution context validates exact binary head masks, hard-opens and verifies every existing nonhead HardConcrete gate, and restores gate/hook state on exceptions. Missing sites, incompatible shapes, invalid query indices, stale same-instance parameter versions, source/runtime/identity drift, inconsistent termination and mutated bank bytes fail closed. Bank replay is read-only, with CPU storage and trusted serialization covered by existing tests.
- Inference is already scoped safely: `_execution` yields inside `torch.no_grad()`. An initial review concern that this scope ended before the forward was an indentation misread and was withdrawn before any fix. Independent forward hooks observed `torch.is_grad_enabled()==False` and `logits.requires_grad==False` at every donor and recipient step.

## Additional independent, load-bearing verification

The reviewer wrote only `/tmp/native_replay_independent_review.py`. For eager and SDPA, it creates a random tiny plain Hugging Face Llama and its identical-weight wrapped counterpart with **all granularities enabled**, including full-layer and embedding gates. It captures a four-token donor bank through the helper, then independently executes the plain model without any cache or replay hooks over each complete actual donor prefix. A plain `o_proj` input hook provides the independent preprojection attention oracle. It compares every layer's complete prompt queries and each continuation query to the bank, and independently derives the greedy tokens. This goes beyond the existing oracle that reuses the helper's dual-stream execution context.

Both environments passed all comparisons with `rtol=1e-5, atol=1e-7`; token sequences agreed exactly. Maximum absolute activation differences:

| Environment | Eager | SDPA |
|---|---:|---:|
| Base Python / Transformers 4.57.3 | 2.9802322387695312e-08 | 4.470348358154297e-08 |
| mgnp / Transformers 5.13 | 2.9802322387695312e-08 | 2.9802322387695312e-08 |

The same script performs a fully closed-head replay on a longer recipient and records no-grad observations throughout both capture and replay. Both environments passed. Commands used `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`, the worktree as `PYTHONPATH`, and respectively `/sw/external/python/anaconda3/bin/python` and `/u/swong2/.conda/envs/mgnp/bin/python`, followed by `/tmp/native_replay_independent_review.py`.

## Remaining contract boundaries

The assessment caller must verify immutable model/weight/tokenizer artifact identities, enforce the frozen nonself statement mapping and donor balancing, preserve exact exported masks, report prompt mapping coverage and terminal reuse, and bind results to frozen source/data. Tensor equality alone cannot establish nonself semantic identity. Fresh-model serialized reuse deliberately trusts the verified external artifact identity; the helper does not hash every model weight. Ordinary same-instance parameter modifications are guarded, while unsafe `.data` mutation is outside that automatic guard, as report 65 explicitly states.

Real-model backend support, CPU-bank transfer/storage overhead, actual runtime and assessment budget still need measured validation before physical launch. This PASS does not approve a compute expansion, caller changes or native outcome selection. Interpretation remains nonself-H activation interchange under the declared boundary-aligned, terminal-held reference policy.
