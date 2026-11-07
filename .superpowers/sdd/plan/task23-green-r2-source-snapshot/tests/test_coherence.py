"""tests/test_coherence.py — the two open-generation coherence metrics.

These numbers exist to answer one question: when a knockout drops a benchmark's
deception rate, did the circuit carry the deception, or did the ablation break
the model's ability to write at all? They are only trustworthy if each is
computed over exactly the right tokens, so most of what is asserted here is
about *which positions are scored*, not about the arithmetic.

The arithmetic is checked against hand-computed values rather than against a
second implementation, since a second implementation written by the same hand
would share the same misunderstanding.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest
import torch

from evaluation import coherence
from tests.helpers import TINY, build_tiny_pair


class _RefCtx:
    """The two attributes `coherence` reads, backed by the tiny model.

    `reference_logits` mirrors `EvalContext.reference_logits` under
    `--reference shared`: single-stream, no corrupted ids, `use_cache=False`.
    """

    def __init__(self, attn_implementation="eager"):
        _, pruned = build_tiny_pair(attn_implementation=attn_implementation)
        pruned.set_final_circuit_mode(False)
        self.node_model = pruned
        self.device = "cpu"

    def reference_logits(self, input_ids, attention_mask):
        with torch.no_grad():
            return self.node_model(input_ids=input_ids,
                                   attention_mask=attention_mask,
                                   use_cache=False).logits


# ----------------------------------------------------------------------------
# completion_mask — where each row actually stopped
# ----------------------------------------------------------------------------

def test_the_first_eos_is_kept_and_everything_after_it_is_dropped():
    ids = torch.tensor([[7, 7, 1, 5, 5],       # eos at generated index 0
                        [7, 7, 4, 1, 5],       # eos at generated index 1
                        [7, 7, 4, 6, 8]])      # never stops
    prompt_mask = torch.ones(3, 2, dtype=torch.long)

    mask = coherence.completion_mask(ids, prompt_mask, gen_start=2,
                                     eos_ids=(1,))

    assert mask.tolist() == [[1, 1, 1, 0, 0],
                             [1, 1, 1, 1, 0],
                             [1, 1, 1, 1, 1]]


def test_the_eos_is_kept_even_when_it_is_also_the_pad_id():
    """The Llama-3.1-8B-Instruct case, and the reason `!= pad_id` is wrong.

    `models/__init__.py:75-77` sets `pad_token = eos_token` when loading a
    Llama tokenizer, so `pad_id` is `<|eot_id|>` — the usual stop token for an
    instruct chat turn. A mask built as `ids != pad_id` would drop the row's
    real stop token on essentially every stopped row, and that token was
    genuinely predicted.
    """
    pad_id = eos_id = 1
    ids = torch.tensor([[7, 7, 4, eos_id, pad_id, pad_id]])
    prompt_mask = torch.ones(1, 2, dtype=torch.long)

    mask = coherence.completion_mask(ids, prompt_mask, gen_start=2,
                                     eos_ids=(eos_id,))

    assert mask.tolist() == [[1, 1, 1, 1, 0, 0]]
    naive = (ids != pad_id).long()
    assert naive.tolist() != mask.tolist()      # the mistake this guards


def test_the_prompt_mask_is_carried_through_untouched():
    """Left padding in the prompt is the caller's, and stays the caller's."""
    ids = torch.tensor([[0, 0, 7, 4, 1, 9]])
    prompt_mask = torch.tensor([[0, 0, 1, 1]])

    mask = coherence.completion_mask(ids, prompt_mask, gen_start=4,
                                     eos_ids=(1,))

    assert mask.tolist() == [[0, 0, 1, 1, 1, 0]]


def test_with_no_eos_ids_the_whole_block_is_kept():
    ids = torch.tensor([[7, 4, 1, 9]])
    mask = coherence.completion_mask(ids, torch.ones(1, 1, dtype=torch.long),
                                     gen_start=1, eos_ids=())
    assert mask.tolist() == [[1, 1, 1, 1]]


# ----------------------------------------------------------------------------
# distinct_n
# ----------------------------------------------------------------------------

def test_distinct_n_on_hand_computed_cases():
    ids = torch.tensor([[5, 5, 5, 5],          # (5,5) x3, 1 unique -> 1/3
                        [5, 6, 9, 9]])         # masked to [5, 6]: 1/1 -> 1.0
    mask = torch.tensor([[1, 1, 1, 1],
                         [1, 1, 0, 0]])
    pooled, per_row, _ = coherence.distinct_n(ids, mask, n=2)

    assert per_row == [pytest.approx(1 / 3), pytest.approx(1.0)]
    # Token-weighted: (1 + 1) unique over (3 + 1) total. The row lengths differ,
    # which is the case where this parts company with the mean of the per-row
    # ratios — and row lengths always differ once rows stop at different points.
    assert pooled == pytest.approx(2 / 4)
    assert pooled != pytest.approx((1 / 3 + 1.0) / 2)


def test_a_row_too_short_for_an_ngram_is_None_not_zero_or_one():
    """Either sentinel would bias the aggregate in a direction that means nothing."""
    ids = torch.tensor([[5, 6]])
    mask = torch.tensor([[1, 0]])              # one real token
    pooled, per_row, _ = coherence.distinct_n(ids, mask, n=2)

    assert per_row == [None]
    assert pooled is None


def test_padding_is_excluded_before_the_ratio_is_taken():
    """A run of post-EOS pad would collapse the ratio for a row that behaved."""
    ids = torch.tensor([[5, 6, 7, 1, 1, 1, 1]])
    mask = torch.tensor([[1, 1, 1, 1, 0, 0, 0]])

    masked, _, _ = coherence.distinct_n(ids, mask, n=2)
    unmasked, _, _ = coherence.distinct_n(ids, n=2)

    assert masked == pytest.approx(1.0)        # (5,6) (6,7) (7,1)
    assert unmasked < masked                   # the pad run repeats (1,1)


# ----------------------------------------------------------------------------
# reference_cross_entropy
# ----------------------------------------------------------------------------

def _hand_nll(ctx, ids, mask, gen_start):
    """NLL computed position by position, no batching, no vectorisation."""
    with torch.no_grad():
        logits = ctx.reference_logits(ids, mask)
    total, count = 0.0, 0
    for row in range(ids.shape[0]):
        for t in range(gen_start, ids.shape[1]):
            if not mask[row, t]:
                continue
            logp = torch.log_softmax(logits[row, t - 1].float(), dim=-1)
            total += -float(logp[ids[row, t]])
            count += 1
    return total / count, count


def test_the_nll_matches_a_hand_computed_loop():
    ctx = _RefCtx()
    torch.manual_seed(5)
    ids = torch.randint(2, TINY["vocab"], (2, 9))
    mask = torch.ones(2, 9, dtype=torch.long)
    mask[0, -3:] = 0                           # the two rows stop differently
    mask[1, -1:] = 0
    gen_start = 4

    pooled, per_row, tokens = coherence.reference_cross_entropy(
        ctx, ids, mask, gen_start)
    expected, expected_count = _hand_nll(ctx, ids, mask, gen_start)

    assert sum(tokens) == expected_count
    assert pooled == pytest.approx(expected, abs=1e-5)


def test_the_pooled_nll_is_token_weighted_not_a_mean_of_row_means():
    """The two disagree whenever rows have unequal length, which is always."""
    ctx = _RefCtx()
    torch.manual_seed(6)
    ids = torch.randint(2, TINY["vocab"], (2, 10))
    mask = torch.ones(2, 10, dtype=torch.long)
    mask[1, -5:] = 0                           # row 1 scores 1 token, row 0 scores 6

    pooled, per_row, tokens = coherence.reference_cross_entropy(
        ctx, ids, mask, gen_start=4)

    assert tokens == [6, 1]
    weighted = sum(m * t for m, t in zip(per_row, tokens)) / sum(tokens)
    assert pooled == pytest.approx(weighted)
    assert pooled != pytest.approx(sum(per_row) / len(per_row))


@pytest.mark.parametrize("attn_impl", ("eager", "sdpa"))
def test_a_left_padded_batch_scores_the_same_as_its_rows_alone(attn_impl):
    """The padding check for this path.

    `ctx.reference_logits` runs `use_cache=False`, which on the *dual*-stream
    path would NaN a fully-padded query row. It is single-stream here, so it
    reaches HF's own mask construction and left padding is safe — asserted
    rather than assumed, because the two paths look identical at the call site.
    """
    ctx = _RefCtx(attn_implementation=attn_impl)
    torch.manual_seed(7)
    row_a = torch.randint(2, TINY["vocab"], (1, 8))
    row_b = torch.randint(2, TINY["vocab"], (1, 5))

    padded = torch.cat([torch.zeros(1, 3, dtype=torch.long), row_b], dim=1)
    ids = torch.cat([row_a, padded], dim=0)
    mask = torch.tensor([[1] * 8, [0, 0, 0, 1, 1, 1, 1, 1]])

    pooled, per_row, tokens = coherence.reference_cross_entropy(
        ctx, ids, mask, gen_start=4, batch_size=2)

    assert not any(math.isnan(v) for v in per_row)
    # Row b alone: same tokens, no padding, and its generated region starts at
    # the same *token*, which is one column earlier once the pad is gone.
    alone, _, alone_tokens = coherence.reference_cross_entropy(
        ctx, row_b, torch.ones(1, 5, dtype=torch.long), gen_start=1)
    assert tokens[1] == alone_tokens[0]
    assert per_row[1] == pytest.approx(alone, abs=1e-4)


def test_a_gen_start_of_zero_is_rejected():
    ctx = _RefCtx()
    ids = torch.randint(2, TINY["vocab"], (1, 4))
    with pytest.raises(ValueError, match="gen_start"):
        coherence.reference_cross_entropy(
            ctx, ids, torch.ones(1, 4, dtype=torch.long), gen_start=0)


# ----------------------------------------------------------------------------
# the pair, and why it is a pair
# ----------------------------------------------------------------------------

def test_looping_scores_a_good_nll_and_a_collapsed_distinct_2():
    """The reason distinct-2 is mandatory rather than supplementary.

    Degenerate repetition is highly *predictable*, so reference NLL rates it
    well — it is exactly the failure mode the NLL cannot see, and reporting NLL
    alone would let a collapsed knockout read as a healthy one.
    """
    ctx = _RefCtx()
    torch.manual_seed(8)
    prompt = torch.randint(2, TINY["vocab"], (1, 4))
    loop = torch.tensor([[9, 9, 9, 9, 9, 9]])
    scramble = torch.randint(2, TINY["vocab"], (1, 6))

    looping = torch.cat([prompt, loop], dim=1)
    scrambled = torch.cat([prompt, scramble], dim=1)
    prompt_mask = torch.ones(1, 4, dtype=torch.long)

    loop_metrics = coherence.coherence_metrics(ctx, looping, prompt_mask,
                                               gen_start=4)
    scr_metrics = coherence.coherence_metrics(ctx, scrambled, prompt_mask,
                                              gen_start=4)

    assert loop_metrics["ref_nll"] < scr_metrics["ref_nll"]
    assert loop_metrics["distinct_n"] < scr_metrics["distinct_n"]
    assert loop_metrics["distinct_n"] == pytest.approx(1 / 5)


def test_the_payload_carries_per_sample_values_and_a_token_count():
    ctx = _RefCtx()
    torch.manual_seed(9)
    ids = torch.randint(3, TINY["vocab"], (3, 9))
    ids[2, 6] = 2                              # row 2 stops after 3 tokens
    prompt_mask = torch.ones(3, 4, dtype=torch.long)

    out = coherence.coherence_metrics(ctx, ids, prompt_mask, gen_start=4,
                                      eos_ids=(2,))

    assert set(out) == {"ref_nll", "ref_ppl", "distinct_n",
                        "distinct_n_corpus", "n", "n_tokens", "per_sample"}
    assert out["n"] == 2
    assert out["n_tokens"] == 5 + 5 + 3
    assert out["ref_ppl"] == pytest.approx(math.exp(out["ref_nll"]), rel=1e-9)
    assert len(out["per_sample"]["ref_nll"]) == 3
    assert len(out["per_sample"]["distinct_n"]) == 3
    assert out["per_sample"]["n_tokens"] == [5, 5, 3]


# ----------------------------------------------------------------------------
# the fixes the block-C review asked for
# ----------------------------------------------------------------------------

class _FakeCtx:
    """A ctx whose reference logits are a fixed tensor in a chosen dtype.

    The tiny model is fp32, so nothing in this file exercises the dtype the
    harness actually loads. `models/__init__.py:66` sets
    `torch_dtype=torch.bfloat16` for Llama, and bf16 has 8 mantissa bits.
    """

    def __init__(self, logits, config=None):
        self._logits = logits
        self.device = "cpu"
        self.node_model = SimpleNamespace(
            config=config or SimpleNamespace(rope_scaling=None))

    def reference_logits(self, input_ids, attention_mask):
        return self._logits[:input_ids.shape[0], :input_ids.shape[1]]


def test_the_log_softmax_runs_in_fp32_even_when_the_logits_are_bf16():
    """Pins the `.float()` cast, which every other test here is blind to.

    Deleting it passes the whole rest of the file, because the tiny reference
    model is fp32 and the cast is a no-op there. `models/__init__.py:66` loads
    Llama with `torch_dtype=torch.bfloat16`, so on the model this harness
    actually targets the cast is the only thing between the report and a bf16
    log-softmax — a systematic bias in the number that ranks every circuit.

    Both sides of the comparison use the *same* bf16 logits, so what is
    measured is the softmax dtype alone rather than bf16 rounding of the
    logits themselves.
    """
    torch.manual_seed(3)
    vocab = 128256                             # the real Llama-3 vocabulary
    logits = (torch.randn(1, 6, vocab) * 8).bfloat16()
    ids = torch.randint(0, vocab, (1, 6))
    mask = torch.ones(1, 6, dtype=torch.long)
    gen_start = 3

    got, _, _ = coherence.reference_cross_entropy(
        _FakeCtx(logits), ids, mask, gen_start=gen_start)

    def hand(dtype):
        logp = torch.log_softmax(logits[:, gen_start - 1:-1].to(dtype), dim=-1)
        nll = -logp.gather(-1, ids[:, gen_start:].unsqueeze(-1)).squeeze(-1)
        return float(nll.double().mean())

    assert got == pytest.approx(hand(torch.float32), rel=1e-6)
    # And the cast is not cosmetic: dropping it moves the reported number.
    assert abs(hand(torch.bfloat16) - hand(torch.float32)) > 1e-3


def test_a_perplexity_that_does_not_fit_is_None_not_inf():
    """`json.dumps` writes inf as a bare `Infinity`, which is not valid JSON.

    The float32 tensor form this replaced saturated above an NLL of ~88.7, so
    an NLL of 200 — reachable only by a spectacularly broken ablation, but
    reachable — produced a report file that strict readers reject outright.
    float64 carries it to ~709 and returns None past that.
    """
    import json

    assert coherence._perplexity(1.5) == pytest.approx(math.exp(1.5))
    assert coherence._perplexity(None) is None
    # Where the old float32 exp saturated to inf, this is still a real number.
    assert math.isfinite(coherence._perplexity(200.0))
    assert coherence._perplexity(1000.0) is None
    payload = {"ref_ppl": coherence._perplexity(1000.0)}
    assert json.loads(json.dumps(payload)) == payload


def test_a_completion_mask_wider_than_the_prompt_is_rejected():
    """Advertised for direct use downstream, so it validates its own inputs."""
    ids = torch.randint(2, 50, (2, 6))
    with pytest.raises(ValueError, match="prompt_mask"):
        coherence.completion_mask(ids, torch.ones(2, 6, dtype=torch.long),
                                  gen_start=4, eos_ids=(1,))


def test_nothing_to_score_is_an_error_rather_than_an_empty_result():
    """`n_tokens == 0` on a non-empty batch is always a caller bug.

    Every row out of `gen_engine.generate` emits at least one token and
    `completion_mask` always keeps the position at `gen_start`, so a zero here
    means the mask did not come from it — which would otherwise be reported as
    a config that legitimately produced nothing.
    """
    ctx = _RefCtx()
    ids = torch.randint(2, TINY["vocab"], (2, 6))

    with pytest.raises(ValueError, match="nothing to score"):
        coherence.reference_cross_entropy(
            ctx, ids, torch.ones(2, 6, dtype=torch.long), gen_start=6)

    mask = torch.ones(2, 6, dtype=torch.long)
    mask[1, 4:] = 0                            # row 1 scores no generated token
    with pytest.raises(ValueError, match="no scored generated tokens"):
        coherence.reference_cross_entropy(ctx, ids, mask, gen_start=4)


def test_a_batch_dependent_rope_is_refused():
    """Left-padded rows are batched here on gen_engine's own argument."""
    logits = torch.randn(1, 6, 64)
    ctx = _FakeCtx(logits, config=SimpleNamespace(
        rope_scaling={"rope_type": "dynamic", "factor": 2.0}))
    with pytest.raises(ValueError, match="inv_freq"):
        coherence.reference_cross_entropy(
            ctx, torch.randint(0, 64, (1, 6)),
            torch.ones(1, 6, dtype=torch.long), gen_start=3)


def test_corpus_distinct_n_sees_the_mode_collapse_that_pooled_cannot():
    """Three identical fluent rows pool to 1.0; the corpus figure does not.

    Within-row distinct-n is the right measure for repetition inside one
    generation, which is what the looping failure mode looks like. An ablation
    that emits the same sentence for every prompt is the other kind, and is
    invisible to it.
    """
    row = torch.tensor([[5, 6, 7, 8]])
    ids = row.repeat(3, 1)

    pooled, per_row, corpus = coherence.distinct_n(ids, n=2)

    assert pooled == pytest.approx(1.0)
    assert per_row == [pytest.approx(1.0)] * 3
    assert corpus == pytest.approx(3 / 9)


def test_coherence_metrics_builds_the_completion_mask_itself():
    """The contract is enforced by the signature, not by a docstring.

    Passing the generation mask extended with ones — the natural mistake —
    scores the post-EOS padding as generated text, which inflates n_tokens and
    collapses distinct-n into the looping signature. There is no longer a way
    to express that call.
    """
    ctx = _RefCtx()
    torch.manual_seed(11)
    ids = torch.randint(3, TINY["vocab"], (1, 10))
    ids[0, 5] = 2
    ids[0, 6:] = 2                             # EOS then a pad run
    prompt_mask = torch.ones(1, 4, dtype=torch.long)

    out = coherence.coherence_metrics(ctx, ids, prompt_mask, gen_start=4,
                                      eos_ids=(2,))
    assert out["n_tokens"] == 2                # the token before EOS, and EOS

    naive = coherence.reference_cross_entropy(
        ctx, ids, torch.ones(1, 10, dtype=torch.long), gen_start=4)
    assert naive[2] == [6]                     # what the trap would have scored
