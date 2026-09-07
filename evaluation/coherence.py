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
harness targets: Llama-3.1-8B-Instruct's tokenizer has no pad token, so
`resolve_pad_id` falls back to `<|eot_id|>` — which is also the first EOS. Every
stopped row then ends `... <|eot_id|> <|eot_id|> <|eot_id|>`, and a `!= pad_id`
mask silently drops the real EOS, which is a scored token. `completion_mask`
below decides it from `eos_ids` instead, which is correct whatever `pad_id` is.
"""

from __future__ import annotations

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
    """
    per_row, uniq_total, gram_total = [], 0, 0
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
    pooled = (uniq_total / gram_total) if gram_total else None
    return pooled, per_row


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
        row_nll.extend(((nll * keep).sum(dim=1)).cpu().tolist())
        row_tokens.extend(counts.cpu().tolist())

    total_tokens = sum(row_tokens)
    pooled = (sum(row_nll) / total_tokens) if total_tokens else None
    means = [(s / c) if c else None for s, c in zip(row_nll, row_tokens)]
    return pooled, means, row_tokens


def coherence_metrics(ctx, ids, attention_mask, gen_start, *, n: int = 2,
                      batch_size: int = 1, desc: str = "") -> dict:
    """`{ref_nll, ref_ppl, distinct_2, n_tokens}` plus the per-sample values.

    `n_tokens` is the total number of scored generated tokens across all rows,
    which is what the pooled `ref_nll` is weighted by — a config whose rows all
    stopped after two tokens has a small `n_tokens`, and the report should say
    so rather than presenting its NLL as comparable.
    """
    pooled_nll, per_row_nll, per_row_tokens = reference_cross_entropy(
        ctx, ids, attention_mask, gen_start, batch_size=batch_size, desc=desc)
    pooled_distinct, per_row_distinct = distinct_n(
        ids[:, gen_start:], attention_mask[:, gen_start:], n=n)
    return {
        "ref_nll": pooled_nll,
        "ref_ppl": None if pooled_nll is None else float(torch.exp(
            torch.tensor(pooled_nll))),
        f"distinct_{n}": pooled_distinct,
        "n_tokens": int(sum(per_row_tokens)),
        "per_sample": {
            "ref_nll": per_row_nll,
            f"distinct_{n}": per_row_distinct,
            "n_tokens": [int(t) for t in per_row_tokens],
        },
    }
