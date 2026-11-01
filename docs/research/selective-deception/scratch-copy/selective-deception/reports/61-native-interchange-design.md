# Bounded native donor-replay design

2026-10-19. Astra decision after report 60 and the corrected final assessment data. No model/job execution or source modification.

**Choose a thin donor-activation replay adapter, not a broad independent-mask model rewrite and not a silent zero-only substitute. Freeze these evaluation semantics before fitting; implementation and physical assessment can wait until finalist and runtime costs are known. Sparse fitting does not depend on this adapter's completion.** Limit ownership to a new evaluation helper, focused tests and its assessment caller. Existing training and historical evaluation paths stay immutable. Any engine callback must be a small backward-compatible addition in the new worktree, not a new generation framework.

## Fixed position policy

Each donor is an intact nonself native H prompt, independently executed with its own valid tokens, attention mask, positions and cache. Recipient D/H/recoding likewise keeps its exact native prompt and positions. Use the frozen balanced donor mapping from report 58, without output-based donor replacement.

Let `Lr` and `Ld` be the numbers of real recipient and donor prompt tokens. For real recipient prompt position `p`, set `q = Ld - Lr + p`.

- If `0 <= q < Ld`, a removed attention head receives the donor-bank activation at real donor prompt position `q`.
- If `q < 0`, the unmatched **early recipient prefix remains unmodified**. Do not repeat the donor's first activation, insert attended filler/pad tokens, or crop either model's actual input.
- For a shorter recipient, only a suffix of the fully contextualized donor prompt contributes replacement activations; the donor itself was still run on its entire native prompt.

This right-aligned intersection is an explicit engineering choice, not a unique or scientifically canonical cross-prompt correspondence. It aligns assistant-start boundaries and preserves valid positions. Prompt coverage differs by D/H/recoding length, especially the longer recoding instruction; report mapped/real prompt counts and the unmapped prefix length for every recipient. The effective native perturbation therefore differs from the equal-length all-position SDR training intervention even though it uses the same learned mask and interchange mixing family. Do not conceal that transfer limitation.

Recipient generation step `t=0` predicts its first answer token from its last prompt query and uses the donor's last prompt query. At step `t>=1`, the recipient query is on its own previous generated token; reference is the donor query on its previous generated token `y[t-1]`. Never use an activation for the donor token that is about to be predicted. Each donor query keeps its own RoPE/cache position, not the recipient's absolute position.

**After donor EOS, hold its last captured valid query activation**, namely the query that predicted EOS. Standard EOS-stopping does not forward the emitted EOS; do not invent an EOS query, pad query or continued donor sentence. If EOS is the first predicted token, the terminal reference is the last prompt query. Keep a separate termination flag for EOS versus cap. With the same 256-token cap, a cap-terminated donor has captured every query needed by a target through its 256th prediction; do not generate an extra donor token merely to fill a bank. Validate requested query bounds explicitly. Report how many target query steps use a terminal-held reference. Terminal holding is part of the intervention, not natural donor autoregression beyond EOS.

## Small adapter boundary

Conceptual interfaces can be implemented narrowly as `capture_donor(prompt, decode_spec, model_identity) -> bank`, `make_position_map(recipient_prompt, bank_metadata) -> map`, and `generate_with_replay(recipient, keep_mask, bank, map, decode_spec) -> result`. No general training abstraction is needed.

A donor bank stores the pre-output-projection attention-head reference at every relevant layer, for all real prompt queries and each actually forwarded continuation query. Capture all attention heads for this bounded first adapter rather than conditioning capture on observed outcomes. All non-head gates must be provably hard-open; no uncaptured MLP/block/layer reference may influence the recipient. Bank provenance includes the exact donor tokens/mask/positions, tokenizer/model/weights, dtype/backend/runtime, deterministic decode/EOS/cap, bank schema, mapping and terminal policy.

Capture must follow the **real donor autoregression**. One valid implementation is an all-open dual-stream donor loop feeding the same actual donor token into both streams at every step, so the existing reference hook observes a correctly positioned intact donor stream. Using a fixed placeholder corrupted stream during donor generation would capture the wrong activations. If capture instead follows a separate teacher-forced replay of an already generated donor completion, record and cost that additional forward pass and test equivalence; it is not free work just because it creates no new completion.

A recipient may use an equal-shaped internal shadow stream solely to satisfy the unchanged model API. Every mapped, closed-head reference must come from the nonself bank. Unmapped-prefix positions must implement **keep-clean**, not an approximate self-reference fallback. An identical-token shadow can implement this prefix only if tests establish the causal invariant: no earlier position in that prefix has been intervened on, hence its shadow and clean activations are identical through every layer. Otherwise add an explicit local per-position bypass. Never substitute the shadow for a missing mapped bank entry. During decoding all valid target queries are mapped or terminal-held, so no shadow value is a scientific reference. Assert missing site, shape, position or fingerprint errors rather than silently switching to zero/interchange/identity.

Keep recipient generation greedy, cached and EOS-stopped with its own clean positions. Bank step selection must follow an explicit prefill/decode position, not a heuristic count of arbitrary module-hook calls. The existing attention reference hook is sufficient for value substitution; whether the caller needs a tiny explicit step callback is an implementation detail subject to review.

## Required focused CPU tests

Use tiny synthetic models; no real-model smoke is needed merely to design this adapter. Test both supported environments and eager/SDPA where available:

1. Captured donor prompt/continuation references equal its own correct intact execution; the capture shadow follows generated donor tokens, not placeholders. Verify query/prediction off-by-one indices and original positions.
2. All-open replay reproduces intact recipient logits/tokens independently of donor content and length. Equal-length, closed-head replay agrees with the existing dual-stream interchange under an identical fixed continuation; changed donor content has a load-bearing effect when heads are closed.
3. Both length orderings implement exactly the frozen map, with no pad activation consumed. Unmatched early recipient prefixes equal the unmodified clean path through all layers; donor changes cannot affect those earlier causal positions. Mapped suffix references must equal the indexed donor bank, not the shadow.
4. First-token/early EOS, cap termination and longer target continuation follow the terminal policy exactly, with no invented EOS/pad queries. Wrong shapes, missing sites, invalid indices and stale fingerprints fail closed.
5. Reusing a donor bank across D/H/recoding and masks leaves bank bytes unchanged. Exact keep/removal export and all-MLP-open checks remain enforced. Preserve affected existing generation/cache regressions; do not rewrite their historical behavior to accommodate the new path.

Prefer individual unpadded generation for this small assessment; batching/left-padding optimization is unnecessary scope. If batching is introduced, pad-ID invariance and equivalence to individual runs become required tests.

## Physical budget and interpretation

The corrected final assessment remains 192 target completions for three union finalists plus intact, or 336 if six union/all-head finalists are frozen before native outcomes. At most 16 genuinely reusable H donors add 16 completions, for **208 or 352 total**, with **53,248 or 90,112 generated-token maxima** at cap 256. Donor capture overhead, any replay forward, CPU transfer/storage and the recipient's internal shadow computation must be included in measured runtime.

All-head BF16 attention banks are about 262,144 bytes per real donor query position across 32 layers; a roughly 500-position bank is about 125 MiB, or about 2 GiB for 16 donors before metadata. Keep banks on CPU/disk with bounded active transfers. Do not cache full-vocabulary logits or all model sites unnecessarily for this heads-only adapter.

No extra GPU reservation is authorized by this review. Root currently reports 4.5/20 hours reserved, with sparse calibration not yet priced. Fit adapter capture and assessment inside the existing measured evaluation allocation; freeze a concrete estimate before launch. If it cannot fit, keep primary native assessment pending and present the costed shortfall or a clearly labeled secondary zero-only report. Do not silently weaken semantics to save time. A bounded CPU implementation/review can proceed within authorization; no user permission is needed for it.

Report native results as **nonself-H activation interchange under the declared boundary-aligned, terminal-held reference policy**. The method preserves valid native donor context but does not make donor replacement neutral deletion, establish a uniquely correct token mapping, or explain the old tiled-reference EVAL5 intervention. H/recoding preservation, donor truth/coded-target relation, mapping coverage and terminal-reference reuse remain visible alongside D suppression. No native outcome selects a new donor map, checkpoint or mask.
