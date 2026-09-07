"""
evaluation/gen_engine.py — the one greedy decoding loop in the harness.

Every open generation this harness produces comes through here: the three
wikitext coherence samples (`evaluation/generation.py`) and, at three orders of
magnitude more tokens, the benchmark knockout runs. They differ only in their
arguments, so they share a loop rather than owning one each.

Two facts about the dual-stream model shape everything below.

* **Both streams share one attention mask.** `PrunableLlamaForCausalLM.forward`
  accepts no `corrupted_attention_mask` — it would land in `**kwargs` and be
  silently dropped. So a corrupt sequence must occupy *exactly* the same
  non-pad positions as the clean sequence it is paired with, and the caller is
  responsible for building it that way.

* **The corrupt stream advances one token per decode step.** Under an
  interchange ablation the ablated units are filled from the corrupt stream, so
  it has to keep pace with the clean stream forever, not just through the
  prompt. `corrupt_ids` must therefore be at least `prompt_width + new_tokens`
  wide; `evaluation/generation.py` tiles a wikitext block to get there.

**Padding side.** Batched generation requires *left* padding: the next token is
read from the last column, which for a right-padded row is a pad. Left padding
is only safe on the cached path — see `use_cache` below.
"""

from __future__ import annotations

import torch
from tqdm import tqdm
from transformers.cache_utils import DynamicCache

from evaluation.ablation import ablation_hook

#: RoPE variants whose `inv_freq` is recomputed from `position_ids.max()`, i.e.
#: from a property of the *batch* rather than of the row. Under those a
#: left-padded batch is not equivalent to its rows run one at a time, and the
#: bucketing below would silently change the numbers. Llama-3.1/3.2 use
#: "llama3", a static per-frequency rescale, so this never fires in practice —
#: it is here because the failure is invisible if it ever does.
_BATCH_DEPENDENT_ROPE = ("dynamic", "longrope")


def _rope_types(config) -> set:
    """Every rope_type declared anywhere in the config's rope settings."""
    found = set()
    for attr in ("rope_scaling", "rope_parameters"):
        value = getattr(config, attr, None)
        if not isinstance(value, dict):
            continue
        # Either a flat {"rope_type": ...} or, on newer transformers, one such
        # dict per attention type: {"full_attention": {"rope_type": ...}, ...}.
        candidates = [value] + [v for v in value.values() if isinstance(v, dict)]
        for entry in candidates:
            # "type" is the pre-4.44 spelling and is still what some configs
            # on the hub carry.
            name = entry.get("rope_type", entry.get("type"))
            if isinstance(name, str):
                found.add(name)
    return found or {"default"}


def assert_rope_is_offset_invariant(config) -> None:
    """Refuse to batch under a RoPE whose frequencies depend on the batch.

    Left padding gives every row a uniform position offset. RoPE enters the
    attention score only through the *difference* (i - j), so a uniform offset
    cancels out of every score and a left-padded batch is exactly its rows run
    at batch size 1 — but only while `inv_freq` is fixed. The variants in
    `_BATCH_DEPENDENT_ROPE` rebuild it from `position_ids.max()`, which is a
    batch-global quantity, and the invariance is gone.
    """
    bad = sorted(t for t in _rope_types(config)
                 if any(b in t for b in _BATCH_DEPENDENT_ROPE))
    if bad:
        raise ValueError(
            f"rope_type={bad} recomputes inv_freq from position_ids.max(), so "
            f"a left-padded batch is not equivalent to the same rows run one "
            f"at a time. Batched generation is not safe under this config.")


def resolve_pad_id(tokenizer, eos_ids=()) -> int:
    """The filler for positions no row is meant to be read at.

    It only ever occupies columns the caller discards — leading prompt padding
    and the tail of a row that already emitted EOS — so any id in range will
    do. Preferring EOS over 0 when there is no pad token keeps a decoded
    sequence readable rather than seeding it with token 0.
    """
    pad = getattr(tokenizer, "pad_token_id", None)
    if pad is not None:
        return int(pad)
    if eos_ids:
        return int(next(iter(eos_ids)))
    eos = getattr(tokenizer, "eos_token_id", None)
    return int(eos) if eos is not None else 0


def generate(ctx, *, clean_ids, corrupt_ids, attention_mask, position_ids=None,
             hook=None, new_tokens, eos_ids=(), use_cache=True,
             desc="") -> torch.LongTensor:
    """Greedy-decode `new_tokens` continuations for one already-padded batch.

    `clean_ids`, `attention_mask` and (optionally) `position_ids` are
    `(n, W)`; `corrupt_ids` is at least `(n, W + new_tokens)`. The return is
    `(n, W + new_tokens)` in input row order with the input's left padding
    preserved, so `out[:, W:]` is the generated block for every row.

    `eos_ids` is plural because Llama-3 instruct models stop on several ids
    (`<|eot_id|>`, `<|end_of_text|>`, ...); source it from the model's
    `generation_config`, not from `tokenizer.eos_token_id`. The first EOS is
    kept in the output and everything after it is `pad_id`.

    `use_cache=False` is the debug escape hatch: it re-forwards the whole
    sequence at every step, which is O(n^2) but exercises none of workstream
    A's cache machinery. It is **only valid on an unpadded batch**. The
    uncached path goes through `llama_node.py`'s manual mask construction,
    which builds `where(mask, 0.0, -inf)`; a fully-padded query row softmaxes
    to NaN there and `0 * NaN = NaN` leaks that row into real positions at the
    next layer. Only the `create_causal_mask` branch — which is the cache
    branch — is padding-safe. Hence the assertion below; do not relax it
    without fixing the manual mask.
    """
    model = ctx.node_model
    device = ctx.device
    n, width = clean_ids.shape

    if attention_mask.shape != clean_ids.shape:
        raise ValueError(
            f"attention_mask {tuple(attention_mask.shape)} must match "
            f"clean_ids {tuple(clean_ids.shape)}: both streams share it.")
    if corrupt_ids.shape[0] != n or corrupt_ids.shape[1] < width + new_tokens:
        raise ValueError(
            f"corrupt_ids is {tuple(corrupt_ids.shape)} but the corrupt "
            f"stream advances one token per decode step, so it must be at "
            f"least ({n}, {width + new_tokens}).")

    clean = clean_ids.to(device)
    corrupt = corrupt_ids.to(device)
    mask = attention_mask.to(device)
    pad_id = resolve_pad_id(ctx.tokenizer, eos_ids)
    eos = torch.as_tensor(sorted({int(e) for e in eos_ids}),
                          dtype=clean.dtype, device=device)

    if not use_cache:
        if not bool(mask.all()):
            raise ValueError(
                "use_cache=False cannot be used with a padded batch: the "
                "uncached path builds the manual causal mask, under which a "
                "fully-padded query row softmaxes to NaN and leaks into the "
                "real positions at the next layer. Generate padded batches "
                "with the cache, or one row at a time.")
        return _decode_uncached(ctx, model, clean, corrupt, new_tokens, hook,
                                eos, pad_id, desc)

    assert_rope_is_offset_invariant(model.config)
    if position_ids is None:
        # Left padding shifts every real token right by the row's pad count;
        # this puts the first real token of every row back at position 0.
        position_ids = (mask.cumsum(-1) - 1).clamp(min=0)
    return _decode_cached(ctx, model, clean, corrupt, mask,
                          position_ids.to(device), new_tokens, hook, eos,
                          pad_id, desc)


def _step(logits, finished, eos, pad_id):
    """Greedy pick, with finished rows held at `pad_id`."""
    nxt = logits[:, -1].float().argmax(dim=-1, keepdim=True)
    if eos.numel() == 0:
        return nxt, finished
    nxt = torch.where(finished.unsqueeze(1), torch.full_like(nxt, pad_id), nxt)
    # The update comes *after* the where, so the first EOS survives into the
    # output and only what follows it is padding.
    return nxt, finished | torch.isin(nxt.squeeze(1), eos)


def _decode_uncached(ctx, model, clean, corrupt, new_tokens, hook, eos, pad_id,
                     desc):
    """Re-forward the whole sequence at every step. No cache, no padding.

    `position_ids` is deliberately not passed: the mask is all ones here (the
    caller was checked), so the model's own `cache_position.unsqueeze(0)` is
    already the correct per-row value, and passing nothing keeps this path
    byte-for-byte the forward the harness has always run.
    """
    seq = clean
    finished = torch.zeros(clean.shape[0], dtype=torch.bool,
                           device=clean.device)
    with torch.no_grad(), ablation_hook(model, hook):
        for _ in tqdm(range(new_tokens), desc=desc, leave=False):
            length = seq.shape[1]
            logits = model(
                input_ids=seq,
                corrupted_input_ids=corrupt[:, :length],
                attention_mask=torch.ones_like(seq),
                use_cache=False).logits
            nxt, finished = _step(logits, finished, eos, pad_id)
            seq = torch.cat([seq, nxt], dim=1)
    return seq


def _decode_cached(ctx, model, clean, corrupt, mask, position_ids, new_tokens,
                   hook, eos, pad_id, desc):
    """Prefill once, then one token per forward through the dual caches."""
    n, width = clean.shape
    device = clean.device
    clean_cache, corrupt_cache = DynamicCache(), DynamicCache()

    out = clean
    step_clean = clean
    step_corrupt = corrupt[:, :width]
    step_pos = position_ids
    # The mask covers the whole key block — cache included — and grows one
    # column per step. `llama_node.py` rejects a mask of the wrong width rather
    # than letting the kernel slice the wrong columns, so it is not
    # pre-allocated at the final width.
    full_mask = mask
    finished = torch.zeros(n, dtype=torch.bool, device=device)

    with torch.no_grad(), ablation_hook(model, hook):
        for step in tqdm(range(new_tokens), desc=desc, leave=False):
            logits = model(
                input_ids=step_clean,
                corrupted_input_ids=step_corrupt,
                attention_mask=full_mask,
                position_ids=step_pos,
                past_key_values=clean_cache,
                corrupted_past_key_values=corrupt_cache,
                use_cache=True).logits
            nxt, finished = _step(logits, finished, eos, pad_id)
            out = torch.cat([out, nxt], dim=1)
            # `.all()` is a device->host sync, so it is only paid when there is
            # an EOS that could actually make it true.
            if eos.numel() and bool(finished.all()):
                break
            step_clean = nxt
            step_corrupt = corrupt[:, width + step:width + step + 1]
            step_pos = step_pos[:, -1:] + 1
            full_mask = torch.cat(
                [full_mask, torch.ones(n, 1, dtype=full_mask.dtype,
                                       device=device)], dim=1)

    return _pad_right(out, width + new_tokens, pad_id)


def _pad_right(ids, target, pad_id):
    """Every caller slices at a fixed offset, so the width has to be constant."""
    missing = target - ids.shape[1]
    if missing <= 0:
        return ids
    filler = torch.full((ids.shape[0], missing), pad_id, dtype=ids.dtype,
                        device=ids.device)
    return torch.cat([ids, filler], dim=1)


def _pad_left(ids, target, pad_id):
    missing = target - ids.shape[1]
    if missing <= 0:
        return ids
    filler = torch.full((ids.shape[0], missing), pad_id, dtype=ids.dtype,
                        device=ids.device)
    return torch.cat([filler, ids], dim=1)


def generate_bucketed(ctx, *, clean_ids, corrupt_ids, attention_mask,
                      hook=None, new_tokens, eos_ids=(), batch_size=8,
                      use_cache=True, desc="") -> torch.LongTensor:
    """`generate`, in length-sorted buckets, with the row order restored.

    A benchmark's prompts vary in length by an order of magnitude, and a batch
    padded to its longest member pays for that padding on every row and every
    step. Sorting by true length and re-trimming each bucket to its own width
    is most of the speedup; the sort is *descending* so that if a width is
    going to exhaust memory it does so on the first bucket rather than the
    twentieth.

    Shapes and semantics are `generate`'s: `(n, W)` in, `(n, W + new_tokens)`
    out, input row order, left padding preserved.
    """
    n, width = clean_ids.shape
    pad_id = resolve_pad_id(ctx.tokenizer, eos_ids)
    lengths = attention_mask.sum(dim=1)
    # `stable` so equal-length rows keep their input order, which makes the
    # bucket contents reproducible rather than sort-implementation-defined.
    order = torch.argsort(lengths, descending=True, stable=True)

    pieces = []
    buckets = range(0, n, batch_size)
    for start in tqdm(buckets, desc=desc, leave=False,
                      total=-(-n // batch_size)):
        rows = order[start:start + batch_size]
        keep = int(lengths[rows].max())
        cut = width - keep                      # leading pad columns to drop
        piece = generate(
            ctx,
            clean_ids=clean_ids[rows][:, cut:],
            # The same columns come off the corrupt stream, which keeps its
            # non-pad positions aligned with the clean stream's — they share
            # one attention mask.
            corrupt_ids=corrupt_ids[rows][:, cut:width + new_tokens],
            attention_mask=attention_mask[rows][:, cut:],
            hook=hook, new_tokens=new_tokens, eos_ids=eos_ids,
            use_cache=use_cache)
        pieces.append(_pad_left(piece, width + new_tokens, pad_id))

    out = torch.cat(pieces, dim=0)
    inverse = torch.empty_like(order)
    inverse[order] = torch.arange(n, device=order.device)
    return out[inverse.to(out.device)]
