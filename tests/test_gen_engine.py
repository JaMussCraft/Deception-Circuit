"""tests/test_gen_engine.py — the shared greedy decoding loop.

`evaluation/gen_engine.py` is the only place in the harness that turns an
ablated model into text, and it is used at two very different scales: three
48-token wikitext samples on the uncached path, and hundreds of 512-token
benchmark generations on the cached, left-padded, length-bucketed one. The
second is where the failure modes live, and all of them are silent:

  * a padded batch that does not match the same rows generated alone (a mask
    that slices the wrong columns, or a RoPE that depends on the batch);
  * rows that come back in sort order rather than input order;
  * a row that emitted EOS and then went on contributing tokens.

The tiny random-weight model writes nonsense, which is fine — every assertion
here is mechanical. Comparisons are token-for-token, so `eager` is used
throughout: a random-init vocab-101 model has near-ties in its logits, and
holding the attention implementation fixed keeps the reduction order the same
on both sides of the comparison.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import torch
from transformers import LlamaConfig

from evaluation import gen_engine
from tests.helpers import TINY, build_tiny_pair

NEW_TOKENS = 5


def _ctx(seed=0, attn_implementation="eager"):
    """The three attributes `gen_engine` actually reads off an EvalContext."""
    _, pruned = build_tiny_pair(seed=seed,
                                attn_implementation=attn_implementation)
    pruned.set_final_circuit_mode(False)
    return SimpleNamespace(
        node_model=pruned,
        device="cpu",
        tokenizer=SimpleNamespace(pad_token_id=0, eos_token_id=1))


def _tokens(n, width, seed):
    g = torch.Generator().manual_seed(seed)
    # Away from 0 so real tokens are never confused with padding.
    return torch.randint(2, TINY["vocab"], (n, width), generator=g)


def _square_batch(n=3, width=7, new_tokens=NEW_TOKENS, seed=11):
    """An unpadded batch: clean (n, width), corrupt (n, width + new_tokens)."""
    clean = _tokens(n, width, seed)
    corrupt = _tokens(n, width + new_tokens, seed + 1)
    mask = torch.ones(n, width, dtype=torch.long)
    return clean, corrupt, mask


def _ragged_batch(lengths=(7, 4, 6), new_tokens=NEW_TOKENS, seed=21):
    """Left-padded rows of unequal length, corrupt aligned to the same columns.

    Both streams share one attention mask, so the corrupt sequence has to
    occupy exactly the non-pad positions of its clean partner — including the
    columns the generated tokens will land in.
    """
    n, width = len(lengths), max(lengths)
    pad = 0
    clean = torch.full((n, width), pad, dtype=torch.long)
    corrupt = torch.full((n, width + new_tokens), pad, dtype=torch.long)
    mask = torch.zeros(n, width, dtype=torch.long)
    for row, length in enumerate(lengths):
        cut = width - length
        clean[row, cut:] = _tokens(1, length, seed + row)[0]
        corrupt[row, cut:] = _tokens(1, length + new_tokens, seed + 100 + row)[0]
        mask[row, cut:] = 1
    return clean, corrupt, mask


# ----------------------------------------------------------------------------
# 1. the cached path agrees with the uncached one
# ----------------------------------------------------------------------------

@pytest.mark.parametrize("attn_impl", ("eager", "sdpa"))
def test_cached_generation_matches_the_uncached_loop(attn_impl):
    """The cache is an optimisation; it must not change a single token."""
    ctx = _ctx(attn_implementation=attn_impl)
    clean, corrupt, mask = _square_batch()

    slow = gen_engine.generate(ctx, clean_ids=clean, corrupt_ids=corrupt,
                               attention_mask=mask, new_tokens=NEW_TOKENS,
                               use_cache=False)
    fast = gen_engine.generate(ctx, clean_ids=clean, corrupt_ids=corrupt,
                               attention_mask=mask, new_tokens=NEW_TOKENS,
                               use_cache=True)

    assert slow.shape == (clean.shape[0], clean.shape[1] + NEW_TOKENS)
    assert torch.equal(slow, fast)
    # The prompt comes back untouched, so `out[:, W:]` is the generated block.
    assert torch.equal(fast[:, :clean.shape[1]], clean)


# ----------------------------------------------------------------------------
# 2. left padding and bucketing
# ----------------------------------------------------------------------------

def test_a_padded_batch_matches_the_same_rows_generated_alone():
    """The whole point of the left-padded path: batching changes nothing.

    Batch size 1 trims each row back to its own width, so the reference has no
    padding at all — which is what makes this a test of the padding rather than
    a comparison of two padded runs.
    """
    ctx = _ctx()
    clean, corrupt, mask = _ragged_batch()

    together = gen_engine.generate_bucketed(
        ctx, clean_ids=clean, corrupt_ids=corrupt, attention_mask=mask,
        new_tokens=NEW_TOKENS, batch_size=len(clean))
    alone = gen_engine.generate_bucketed(
        ctx, clean_ids=clean, corrupt_ids=corrupt, attention_mask=mask,
        new_tokens=NEW_TOKENS, batch_size=1)

    width = clean.shape[1]
    assert together.shape == (len(clean), width + NEW_TOKENS)
    assert not torch.isnan(together.float()).any()
    assert torch.equal(together[:, width:], alone[:, width:])
    # Row order is the input's, not the length-sorted one, and the prompts come
    # back exactly as they went in — padding included.
    assert torch.equal(together[:, :width], clean)


def test_bucketing_does_not_depend_on_the_bucket_size():
    ctx = _ctx()
    clean, corrupt, mask = _ragged_batch(lengths=(7, 4, 6, 5, 7))
    width = clean.shape[1]

    runs = [gen_engine.generate_bucketed(
        ctx, clean_ids=clean, corrupt_ids=corrupt, attention_mask=mask,
        new_tokens=NEW_TOKENS, batch_size=bs)[:, width:] for bs in (1, 2, 5)]

    assert torch.equal(runs[0], runs[1])
    assert torch.equal(runs[0], runs[2])


def test_permuting_the_input_permutes_the_output():
    """A sort/unsort bug that happens to be identity on one ordering."""
    ctx = _ctx()
    clean, corrupt, mask = _ragged_batch(lengths=(7, 4, 6, 5))
    width = clean.shape[1]
    perm = torch.tensor([2, 0, 3, 1])

    straight = gen_engine.generate_bucketed(
        ctx, clean_ids=clean, corrupt_ids=corrupt, attention_mask=mask,
        new_tokens=NEW_TOKENS, batch_size=2)
    shuffled = gen_engine.generate_bucketed(
        ctx, clean_ids=clean[perm], corrupt_ids=corrupt[perm],
        attention_mask=mask[perm], new_tokens=NEW_TOKENS, batch_size=2)

    assert torch.equal(shuffled[:, width:], straight[perm][:, width:])


# ----------------------------------------------------------------------------
# 3. per-row EOS
# ----------------------------------------------------------------------------

def _unique_generated_token(block):
    """A (row, step) whose token appears exactly once in the whole block.

    Uniqueness is what makes the assertion sharp: the id can only stop the one
    row, so every other row must come back byte-identical to the EOS-free run.
    """
    values, counts = torch.unique(block, return_counts=True)
    for value in values[counts == 1].tolist():
        hits = (block == value).nonzero()
        row, step = int(hits[0, 0]), int(hits[0, 1])
        if step < block.shape[1] - 1:      # leave room for a truncated tail
            return row, step, value
    pytest.skip("no uniquely-generated token in this sample")


def test_eos_stops_one_row_and_leaves_the_others_untouched():
    ctx = _ctx()
    clean, corrupt, mask = _square_batch(n=4, width=6, new_tokens=8, seed=31)
    width = clean.shape[1]
    kwargs = dict(clean_ids=clean, corrupt_ids=corrupt, attention_mask=mask,
                  new_tokens=8)

    free = gen_engine.generate(ctx, **kwargs)
    row, step, eos = _unique_generated_token(free[:, width:])

    stopped = gen_engine.generate(ctx, eos_ids=(eos,), **kwargs)

    pad = ctx.tokenizer.pad_token_id
    # The EOS itself is kept...
    assert torch.equal(stopped[row, :width + step + 1],
                       free[row, :width + step + 1])
    # ...and everything after it is padding, not more generation.
    assert (stopped[row, width + step + 1:] == pad).all()
    others = [r for r in range(clean.shape[0]) if r != row]
    assert torch.equal(stopped[others], free[others])


def test_the_output_is_full_width_even_when_every_row_stops_early():
    """Callers slice at a fixed offset, so an early break must still pad out."""
    ctx = _ctx()
    clean, corrupt, mask = _square_batch(n=3, width=6, new_tokens=8, seed=41)
    width = clean.shape[1]

    free = gen_engine.generate(ctx, clean_ids=clean, corrupt_ids=corrupt,
                               attention_mask=mask, new_tokens=8)
    # Every token any row generates first — so every row stops at step 0.
    eos_ids = tuple(free[:, width].tolist())
    stopped = gen_engine.generate(ctx, clean_ids=clean, corrupt_ids=corrupt,
                                  attention_mask=mask, new_tokens=8,
                                  eos_ids=eos_ids)

    assert stopped.shape == (3, width + 8)
    assert torch.equal(stopped[:, width], free[:, width])
    assert (stopped[:, width + 1:] == ctx.tokenizer.pad_token_id).all()


# ----------------------------------------------------------------------------
# 4. the guards
# ----------------------------------------------------------------------------

def test_an_uncached_padded_batch_is_rejected():
    """The manual mask NaNs a fully-padded query row; --no-kv-cache must not.

    This is a real limitation of the debug escape hatch, not a defensive
    assertion: only the `create_causal_mask` branch (which is the cache branch)
    is safe under left padding.
    """
    ctx = _ctx()
    clean, corrupt, mask = _ragged_batch()
    with pytest.raises(ValueError, match="padded batch"):
        gen_engine.generate(ctx, clean_ids=clean, corrupt_ids=corrupt,
                            attention_mask=mask, new_tokens=NEW_TOKENS,
                            use_cache=False)


def test_a_corrupt_stream_that_runs_out_is_rejected():
    """It is consumed one token per decode step, not just through the prompt."""
    ctx = _ctx()
    clean, corrupt, mask = _square_batch()
    with pytest.raises(ValueError, match="corrupt_ids"):
        gen_engine.generate(ctx, clean_ids=clean,
                            corrupt_ids=corrupt[:, :-1],
                            attention_mask=mask, new_tokens=NEW_TOKENS)


def test_a_mismatched_attention_mask_is_rejected():
    ctx = _ctx()
    clean, corrupt, mask = _square_batch()
    with pytest.raises(ValueError, match="attention_mask"):
        gen_engine.generate(ctx, clean_ids=clean, corrupt_ids=corrupt,
                            attention_mask=mask[:, :-1],
                            new_tokens=NEW_TOKENS)


@pytest.mark.parametrize("scaling,ok", [
    (None, True),
    ({"rope_type": "llama3", "factor": 8.0, "high_freq_factor": 4.0,
      "low_freq_factor": 1.0, "original_max_position_embeddings": 8192}, True),
    ({"rope_type": "linear", "factor": 2.0}, True),
    ({"rope_type": "dynamic", "factor": 2.0}, False),
])
def test_only_offset_invariant_rope_is_allowed(scaling, ok):
    """Left padding is a uniform position offset; RoPE only sees (i - j).

    That cancellation is what makes a padded batch equal to its rows run alone
    — but it needs a fixed `inv_freq`. "dynamic" rebuilds it from
    `position_ids.max()`, a batch-global quantity, and the equivalence is gone
    with no visible symptom.
    """
    config = LlamaConfig(hidden_size=TINY["hidden"],
                         num_attention_heads=TINY["heads"],
                         rope_scaling=scaling)
    if ok:
        gen_engine.assert_rope_is_offset_invariant(config)
    else:
        with pytest.raises(ValueError, match="inv_freq"):
            gen_engine.assert_rope_is_offset_invariant(config)


def test_the_pre_4_44_rope_spelling_is_still_read():
    """Configs on the hub still carry {"type": ...} rather than "rope_type"."""
    config = SimpleNamespace(rope_scaling={"type": "dynamic", "factor": 2.0})
    with pytest.raises(ValueError, match="inv_freq"):
        gen_engine.assert_rope_is_offset_invariant(config)


def test_the_pad_id_falls_back_to_eos_when_there_is_no_pad_token():
    assert gen_engine.resolve_pad_id(
        SimpleNamespace(pad_token_id=None, eos_token_id=7)) == 7
    assert gen_engine.resolve_pad_id(
        SimpleNamespace(pad_token_id=None, eos_token_id=None),
        eos_ids=(9, 4)) == 9
