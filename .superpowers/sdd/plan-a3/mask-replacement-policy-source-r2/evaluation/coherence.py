"""
evaluation/coherence.py — is the ablated model still writing English?

A knockout that drops a benchmark's deception rate has two possible
explanations, and the interesting one is not the default. Either the circuit
carried the deception, or its removal broke the model's ability to produce
coherent text at all, and the judge is scoring rubble as honest. Two numbers
separate those, and **neither works alone**:

* **Reference cross-entropy** — the ablated model's own generation, teacher-
  forced through the *unablated* model. Scrambled output is surprising to a
  healthy model and scores a high NLL.
* **distinct-2** — unique bigrams over total bigrams. This is the mandatory
  companion, not a nice-to-have: degenerate looping ("the the the the") is
  extremely *predictable*, so it scores an excellent reference NLL while being
  exactly the failure the NLL was meant to catch.

    scrambled  =>  high NLL,  normal distinct-2
    looping    =>  low  NLL,  collapsed distinct-2

Read together they cover both. The floor for the NLL is not zero — it is the
**full model's own** greedy continuation scored by the same model, which is low
but finite, and it appears in the report as the `full` row rather than as a
constant here.

**The mask is the subtle part.** `gen_engine.generate` returns a fixed-width
block; where each row actually stopped is not in the tensor's shape. The
natural-looking reconstruction, `ids != pad_id`, is wrong on the model this
harness targets. `models/__init__.py:75-77` sets `pad_token = eos_token` when
loading a Llama tokenizer, so on Llama-3.1-8B-Instruct `pad_id` is 128009
`<|eot_id|>` — the usual stop token for an instruct chat turn. A `!= pad_id`
mask would therefore drop the real EOS on essentially every stopped row, and
that EOS is a token the model genuinely predicted. `completion_mask` below
does not read `pad_id` at all; it decides from `eos_ids`, which is correct
whatever the pad id happens to be.
"""

from __future__ import annotations

import math

import torch
from tqdm import tqdm


def completion_mask(ids, prompt_mask, gen_start, eos_ids=()) -> torch.Tensor:
    """The positions of `ids` that are real: prompt, plus generation to its EOS.

    The prompt region is `prompt_mask` unchanged (whatever padding the caller
    used). The generated region is 1 up to **and including** the first EOS and
    0 after it — the EOS is a real token and a real prediction. A model that
    stops somewhere sensible is behaving; one that never stops, or stops in the
    middle of a clause, is not, and scoring the stop token is how that shows up
    in the NLL.

    Rows that never emitted an EOS keep their whole generated block.

    Workstream D/E's benchmark callers need this too — it is the only way to
    recover per-row stop positions from what `gen_engine.generate` returns.
    """
    if prompt_mask.shape[1] != gen_start:
        raise ValueError(
            f"prompt_mask is {prompt_mask.shape[1]} wide but gen_start is "
            f"{gen_start}: it must cover the prompt and only the prompt. "
            f"(A full-width mask would produce a result wider than ids.)")
    generated = ids[:, gen_start:]
    if len(eos_ids):
        eos = torch.as_tensor(sorted({int(e) for e in eos_ids}),
                              dtype=ids.dtype, device=ids.device)
        is_eos = torch.isin(generated, eos)
        # cumsum is 0 before the first EOS and >= 1 from it onward; subtracting
        # the indicator puts the EOS position itself back at 0, so it is kept.
        keep = (is_eos.cumsum(dim=1) - is_eos.long()) == 0
    else:
        keep = torch.ones_like(generated, dtype=torch.bool)
    return torch.cat([prompt_mask.to(keep.device).bool(), keep], dim=1).long()


def distinct_n(ids, mask=None, n: int = 2):
    """Unique n-grams over total n-grams, per row and pooled.

    Computed over the *masked* tokens only. Post-EOS padding is a run of one
    repeated id, which would collapse the ratio toward zero and make a model
    that stopped early look degenerate.

    A row with fewer than `n` real tokens has no n-grams at all; its per-row
    value is `None` rather than 0.0 or 1.0, either of which would bias the
    aggregate in a direction that means nothing.

    The pooled figure is token-weighted — `sum(unique) / sum(total)` over rows,
    not the mean of the per-row ratios. The two disagree whenever rows have
    unequal length, which is always.

    Pooled is deliberately **within-row**: a bigram appearing in every row is
    counted once per row, so three identical rows pool to 1.0. That is the
    right reading for the failure this metric exists to catch, which is
    repetition inside one generation. It is blind to the other kind — an
    ablation that emits the same fluent sentence for all 200 prompts also
    scores 1.0 — so `corpus` is returned alongside it: the same ratio over the
    concatenation of every row's n-grams, which collapses under exactly that
    mode collapse. The report should show both.
    """
    per_row, uniq_total, gram_total = [], 0, 0
    corpus_grams, corpus_total = set(), 0
    for row in range(ids.shape[0]):
        tokens = ids[row]
        if mask is not None:
            tokens = tokens[mask[row].bool()]
        tokens = tokens.tolist()
        if len(tokens) < n:
            per_row.append(None)
            continue
        grams = [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
        per_row.append(len(set(grams)) / len(grams))
        uniq_total += len(set(grams))
        gram_total += len(grams)
        corpus_grams.update(grams)
        corpus_total += len(grams)
    pooled = (uniq_total / gram_total) if gram_total else None
    corpus = (len(corpus_grams) / corpus_total) if corpus_total else None
    return pooled, per_row, corpus


def reference_cross_entropy(ctx, ids, attention_mask, gen_start, *,
                            batch_size: int = 1, desc: str = ""):
    """Mean NLL per generated token under the **unablated** model.

    Teacher-forces the ablated model's own output: position `t` is scored from
    the logits at `t - 1`, for every `t >= gen_start` the mask keeps.

    The forward goes through `ctx.reference_logits`, which is single-stream —
    no `corrupted_input_ids`, so it lands in `super().forward` and uses HF's own
    causal-mask construction. Left padding is therefore safe here despite
    `use_cache=False`, unlike the dual-stream path in `evaluation/gen_engine.py`
    (verified directly: no NaN under eager or sdpa, and a padded row's logits
    match the same row run unpadded to ~2e-7). Do not add a guard against it.

    `attention_mask` must be a **completion mask** — the output of
    `completion_mask` above, not the mask the generation was run with extended
    with ones. Scoring the post-EOS padding as if the model had written it
    inflates `n_tokens` and collapses distinct-n toward the very "looping"
    signature these two metrics were paired to disambiguate. `coherence_metrics`
    builds it for you; prefer that entry point.

    Returns `(pooled_nll, per_row_nll, per_row_tokens)`. The pooled figure is
    **token-weighted** — total NLL over total scored tokens — not the mean of
    the row means.
    """
    if gen_start < 1:
        raise ValueError(
            "gen_start must be at least 1: position t is scored from the "
            "logits at t - 1, so there is nothing to score a sequence's first "
            "token against.")
    if attention_mask.shape != ids.shape:
        raise ValueError(
            f"attention_mask {tuple(attention_mask.shape)} must match ids "
            f"{tuple(ids.shape)}.")
    if ids.shape[0] and gen_start >= ids.shape[1]:
        raise ValueError(
            f"gen_start {gen_start} leaves nothing to score in a sequence of "
            f"{ids.shape[1]}. Every row out of gen_engine.generate has at "
            f"least one generated token, so this is a caller bug rather than "
            f"a config that produced nothing.")
    if ids.shape[0] and not bool(attention_mask[:, gen_start:].any(dim=1).all()):
        raise ValueError(
            "some row has no scored generated tokens. `completion_mask` always "
            "keeps at least the position at gen_start, so an all-zero "
            "generated mask means the mask was not built from it.")

    # Left-padded rows are batched here on the same offset-invariance argument
    # `evaluation/gen_engine.py` relies on, so it is asserted on the same
    # terms. Chunks are cut in input order rather than by length, which under a
    # batch-dependent RoPE would make the result depend on `batch_size`.
    from evaluation.gen_engine import assert_rope_is_offset_invariant
    assert_rope_is_offset_invariant(ctx.node_model.config)

    device = ctx.device
    row_nll, row_tokens = [], []
    chunks = range(0, ids.shape[0], batch_size)
    for start in tqdm(chunks, desc=desc, leave=False,
                      total=-(-ids.shape[0] // batch_size)):
        chunk = ids[start:start + batch_size].to(device)
        chunk_mask = attention_mask[start:start + batch_size].to(device)
        logits = ctx.reference_logits(chunk, chunk_mask)
        # Predict token t from position t - 1: drop the last position, which
        # predicts a token past the end of the sequence.
        logp = torch.log_softmax(logits[:, gen_start - 1:-1].float(), dim=-1)
        target = chunk[:, gen_start:]
        nll = -logp.gather(-1, target.unsqueeze(-1)).squeeze(-1)
        keep = chunk_mask[:, gen_start:].bool()
        counts = keep.sum(dim=1)
        # `where`, not `nll * keep`: a NaN at a masked-out position survives
        # multiplication by False and would poison the row's whole sum. Logits
        # are finite on this single-stream path even for a fully-padded row —
        # measured, not assumed — so this is defence in depth, and free.
        row_nll.extend(torch.where(keep, nll, torch.zeros_like(nll))
                       .sum(dim=1).cpu().tolist())
        row_tokens.extend(counts.cpu().tolist())

    total_tokens = sum(row_tokens)
    pooled = (sum(row_nll) / total_tokens) if total_tokens else None
    means = [(s / c) if c else None for s, c in zip(row_nll, row_tokens)]
    return pooled, means, row_tokens


def coherence_metrics(ctx, ids, prompt_mask, gen_start, *, eos_ids=(),
                      n: int = 2, batch_size: int = 1, desc: str = "") -> dict:
    """`{ref_nll, ref_ppl, distinct_n, n, n_tokens}` plus the per-sample values.

    Takes the **prompt** mask that generation was run with, plus `eos_ids`, and
    builds the completion mask itself. That is deliberate: the natural mistake
    for a caller is to reuse the generation mask extended with ones, which
    scores every post-EOS pad as if the model had written it — `n_tokens`
    inflates and distinct-n collapses toward the "looping" signature these two
    metrics exist to disambiguate. Making the correct mask the only reachable
    one is cheaper than documenting the trap.

    `n_tokens` is the total number of scored generated tokens across all rows,
    which is what the pooled `ref_nll` is weighted by — a config whose rows all
    stopped after two tokens has a small `n_tokens`, and the report should say
    so rather than presenting its NLL as comparable.

    The key is `distinct_n` with `n` reported alongside, not `distinct_2`. The
    plan names the latter, but a key that changes with a parameter makes a
    reader keyed on the literal string lose the column silently instead of
    failing.
    """
    mask = completion_mask(ids, prompt_mask, gen_start, eos_ids)
    pooled_nll, per_row_nll, per_row_tokens = reference_cross_entropy(
        ctx, ids, mask, gen_start, batch_size=batch_size, desc=desc)
    pooled_distinct, per_row_distinct, corpus_distinct = distinct_n(
        ids[:, gen_start:], mask[:, gen_start:], n=n)
    return {
        "ref_nll": pooled_nll,
        "ref_ppl": _perplexity(pooled_nll),
        "distinct_n": pooled_distinct,
        "distinct_n_corpus": corpus_distinct,
        "n": n,
        "n_tokens": int(sum(per_row_tokens)),
        "per_sample": {
            "ref_nll": per_row_nll,
            "distinct_n": per_row_distinct,
            "n_tokens": [int(t) for t in per_row_tokens],
        },
    }


def _perplexity(nll):
    """`exp(nll)`, or None where it does not fit.

    Computed in float64 via `math.exp` rather than a float32 tensor: the tensor
    form saturates to `inf` above an NLL of ~88.7, and `json.dumps` writes that
    as a bare `Infinity`, which is not valid JSON and is rejected by strict
    readers. An NLL that large means a spectacularly broken ablation, but the
    report should still be loadable when it happens.
    """
    if nll is None:
        return None
    try:
        return math.exp(nll)
    except OverflowError:
        return None
