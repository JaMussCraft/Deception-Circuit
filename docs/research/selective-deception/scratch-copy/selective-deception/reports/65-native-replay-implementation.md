# Bounded native donor activation replay implementation

2026-10-19. CPU implementation only, following frozen reports 58/60/61. No real-model load, GPU, API, network, job submission, git mutation, or changes to the frozen sparse-training worktree. Sparse fitting does not depend on this helper's readiness. Scientific/native assessment remains unrun.

Implemented only new `evaluation/native_interchange.py` and `tests/test_native_interchange.py` in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/selective-native-replay`, whose root readiness marker verified checkout base `08c032f49b2cd83848105d0681c9636bb66174ff`. No engine/model API changes. A separate worker owns the assessment caller.

## API and fixed semantics

- `DecodeSpec(max_new_tokens, eos_token_ids=())`: deterministic greedy cached generation. Positive integer cap and exact EOS tuple.
- `capture_donor(model, prompt_ids, decode_spec, *, model_identity, tokenizer_identity) -> DonorBank`: accepts only one nonempty `[1,L]` long prompt with every token valid. Implied attention mask is all ones, real positions `range(L)`. Both actual streams receive the same actual greedy donor tokens at each cached step. Capture occurs during that autoregression, without a production teacher-forced replay pass. CPU bank stores all real prompt queries plus each actually forwarded continuation query for every layer and every head, pre-`o_proj` in `[queries, heads, head_dim]` tensors. EOS is emitted but never forwarded. A cap of K captures exactly L+K-1 queries.
- `make_position_map(recipient_prompt, bank) -> tuple`: `q = Ld-Lr+p` when nonnegative; otherwise `-1` means causally untouched keep-clean prefix. The donor's entire native prompt is always executed. No padding, cropping, filler or first-donor-query repetition.
- `generate_with_replay(model, prompt_ids, keep_mask, bank, decode_spec, *, model_identity, tokenizer_identity) -> ReplayResult`: exact binary keep mask `[layers, heads]`; cached recipient inputs/positions follow its own prompt and actual greedy continuation. The equal-shaped identical-token shadow satisfies the existing unchanged API; mapped references come exclusively from the indexed nonself bank. At prediction t=0 the reference is the final donor prompt query. At t>=1 it is the donor query on donor generated token y[t-1]. After EOS hold the last valid query that predicted EOS; reject any request exceeding a cap-terminated bank's coverage. No shadow fallback for a missing mapped site.

`ReplayResult` exposes generated tokens including emitted EOS (no pads), EOS/cap termination, full prompt mapping, unmapped-prefix count, last-query bank index for each prediction, terminal-held-step count, and only the final vocabulary logit vector on CPU. `DonorBank` exposes exact prompt/generated token tuples, termination, CPU activation tuple, query count, provenance and content digest. `torch.save(bank)` and trusted `torch.load(..., weights_only=False)` support disk reuse. Source hashes deliberately make banks stale after helper/model/compatibility/gate source changes.

The scoped execution context installs exact hard head keep values, provably opens every nonhead HardConcrete gate, then restores original gate values and pre-existing hooks even on exceptions. Model must already be in eval mode. No training state is silently changed. Unmatched early recipient positions retain identical-token shadow values only because no earlier causal position was intervened on; focused tests establish exact intact hidden-state equality through every layer.

## Binding and fail-closed behavior

Bank provenance contains exact donor prompt IDs, all-one attention mask, original positions, actual generated IDs, decode cap/EOS policy, schema/mapping/terminal policy, caller-verified immutable model/weight and tokenizer identities, full model config/class, dtype/backend/device type, Python/Torch/Transformers versions, deterministic-algorithm setting, and helper/model/compatibility/gate source hashes. Same-model-instance non-gate parameter object/version checks additionally reject subsequent ordinary weight edits. Persisted reuse in a fresh model instance intentionally relies on the caller verifying immutable source/weight/tokenizer identities; transient object IDs are not a portable disk identity. The assessment caller must enforce the frozen nonself donor statement mapping; the low-level helper receives tensors and does not infer statement identity from token equality.

Reuse checks reject identity/runtime/source drift, wrong/missing layer sites, wrong CPU shape/dtype, nonfinite bank values, invalid token/position metadata, inconsistent EOS/cap termination, nonbinary/wrong-shape masks, cap overflow and out-of-range query indices. A content digest detects bank tensor or metadata mutation; replay only reads bank bytes. Arbitrary edits via unsafe `.data` mutation are outside ordinary parameter-version detection, so external verified weight identity remains part of the contract rather than a claim of automatic full-weight hashing.

## Test evidence

Real random tiny CPU Llama models, two layers/four query heads/GQA, exercised both eager and SDPA attention. No downloaded model or real data. Tests were written first: initial missing-module RED, then source-binding and malformed-termination RED before the corresponding hardening.

Final helper SHA256: `483482914d1ff217c4bfcdc5b8f8f237a76a468f557314f03c5111bd392176d9`.
Final test SHA256: `db521b405e65ad6d52804bd00397e8e87aed8d75595f00b8a2e5e84345d64d93`.

Commands use `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`:

| Environment | Command suffix | Result |
|---|---|---|
| Base `/sw/external/python/anaconda3/bin/python`, Transformers 4.57.3 | `-m pytest tests/test_native_interchange.py tests/test_gen_engine.py tests/test_kv_cache.py tests/test_benchmark_eval.py -q` | **145 passed**, 33.42 s, 3 existing dependency warnings |
| Base, after final assertion-only strengthening | `-m pytest tests/test_native_interchange.py -q` | **24 passed**, 17.77 s, same 3 warnings |
| mgnp `/u/swong2/.conda/envs/mgnp/bin/python`, Transformers 5.13 | `-m pytest tests/test_gen_engine.py tests/test_kv_cache.py tests/test_benchmark_eval.py -q` | **121 passed**, 31.50 s, 1 existing dependency warning |
| mgnp, final focused assertions | `-m pytest tests/test_native_interchange.py -q` | **24 passed**, 12.80 s |

Focused checks cover actual donor token inputs and original positions; exact captured queries against separate intact cached execution; all-open invariance across donor contents/lengths and equality to the existing cached engine; closed-head load-bearing content; exact equality to dual-stream interchange under a fixed continuation; both length orderings and exact indexed replacement; unmapped-prefix causal equality through all hidden-state layers; t0/t>=1 off-by-one indices; first-token and early EOS without extra EOS/pad forward; target continuation genuinely outliving donor with terminal holding; cap overflow; immutable bank reuse across prompt lengths/masks; save/load and fresh identical-model reuse; stale weight and identity rejection; missing/wrong-shape bank entries; invalid mapping indices; inconsistent termination even after recomputing digest; and restoration of gate/hook state.

Affected historical generation/cache/benchmark tests passed unchanged. No full-repository suite was rerun for this isolated helper; root explicitly selected the focused plus affected regressions after the training suites had completed. No failing test remains in these scoped runs. Logs are `/tmp/native-replay-base-final.log`, `/tmp/native-replay-base-focused-final.log`, `/tmp/native-replay-mgnp-regressions.log`, `/tmp/native-replay-mgnp-focused-final.log`.

## Remaining boundary

Independent review and the separately owned caller still precede physical assessment. No native efficacy or GPU runtime claim is made. All-head CPU banks, CPU transfer/storage, donor capture overhead and the recipient's unchanged dual-stream shadow computation must be measured inside the existing evaluation allocation before any launch. This remains nonself-H activation interchange under the declared boundary-aligned, terminal-held policy, with prompt coverage and terminal reuse visible; it is not neutral deletion or a unique scientific token correspondence.
