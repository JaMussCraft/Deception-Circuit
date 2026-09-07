"""tests/test_kv_cache.py — the dual-stream KV cache.

`models/llama_node.py` runs two streams through one set of attention modules.
Giving the corrupted stream a cache is therefore not a one-line change: the two
streams need *distinct* Cache objects (a shared one would concatenate corrupt
K/V onto the clean entry under the same `layer_idx`), they have to stay in
lockstep (`cache_position` and the rotary embeddings are computed once and
shared), and the causal mask has to be built by transformers' own helper rather
than the manual construction, which is wrong the moment the cache is non-empty.

Three things are asserted here, and each one guards a specific way the change
could have gone wrong:

1. **cached == uncached.** Greedy decoding with the cache must produce the same
   tokens as the O(n^2) full-sequence re-forward, for every ablation scheme
   crossed with every circuit configuration. This is the correctness claim.
2. **`use_cache=False` is bit-identical to the pre-change implementation.**
   `tests/fixtures/prechange_logits.pt` was captured before the edit. Training
   and the four single-position evaluations all run on that path, so it must
   not move by a single ulp.
3. **Left padding does not produce NaN.** The manual mask builds
   `where(mask, 0.0, -inf)`; under left padding a fully-masked query row
   softmaxes to NaN and `0 * NaN = NaN` leaks into real positions at the next
   layer. The generation engine left-pads, so this is the failure the mask
   rewrite exists to prevent.

Everything runs on a tiny CPU model with `attn_implementation="eager"`: a
random-init vocab-101 model has near-ties in its logits, and eager attention
keeps the reduction order identical between the cached and uncached paths so a
token-for-token comparison is a real signal rather than a coin flip.
"""

from __future__ import annotations

import pytest
import torch
from transformers.cache_utils import DynamicCache

from tests.helpers import build_tiny_pair
from evaluation.ablation import ablation_hook, make_hook

ABLATIONS = ("interchange", "zero", "mean")
CONFIGS = ("full", "knockout", "circuit_only")


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------

def _tiny(seed=0):
    plain, pruned = build_tiny_pair(seed=seed, attn_implementation="eager")
    pruned.set_final_circuit_mode(False)
    return pruned


def _set_gates(model, config):
    """Open every gate, close every gate, or close half of them."""
    gates = [m for m in model.modules() if hasattr(m, "log_alpha")]
    for i, gate in enumerate(gates):
        with torch.no_grad():
            if config == "full":
                gate.log_alpha.fill_(10.0)
            elif config == "knockout":
                gate.log_alpha.fill_(-10.0)
            else:  # circuit_only — a mix, so both branches of every gate fire
                gate.log_alpha.fill_(10.0 if i % 2 else -10.0)


def _mean_bank(model, ids, corrupt, mask):
    """A bank collected the way evaluation/ablation.py collects one."""
    from evaluation.ablation import MeanCollector
    collector = MeanCollector()
    collector.set_mask(mask)
    with torch.no_grad(), ablation_hook(model, collector):
        model(input_ids=ids, corrupted_input_ids=corrupt,
              attention_mask=mask, use_cache=False)
    return collector.bank()


def _hook_for(model, ablation, ids, corrupt, mask):
    if ablation == "mean":
        return make_hook("mean", _mean_bank(model, ids, corrupt, mask), model)
    return make_hook(ablation)


def _generate_uncached(model, clean0, corrupt, new_tokens, hook):
    """The O(n^2) loop from evaluation/generation.py, verbatim in spirit."""
    clean = clean0.clone()
    with torch.no_grad(), ablation_hook(model, hook):
        for _ in range(new_tokens):
            length = clean.shape[1]
            logits = model(input_ids=clean,
                           corrupted_input_ids=corrupt[:, :length],
                           attention_mask=torch.ones_like(clean),
                           use_cache=False).logits
            nxt = logits[:, -1].float().argmax(dim=-1, keepdim=True)
            clean = torch.cat([clean, nxt], dim=1)
    return clean


def _generate_cached(model, clean0, corrupt, new_tokens, hook):
    """Incremental decoding with one cache per stream."""
    clean = clean0.clone()
    clean_cache, corrupt_cache = DynamicCache(), DynamicCache()
    step_clean, step_corrupt = clean0, corrupt[:, :clean0.shape[1]]
    with torch.no_grad(), ablation_hook(model, hook):
        for step in range(new_tokens):
            total = clean.shape[1]
            out = model(input_ids=step_clean,
                        corrupted_input_ids=step_corrupt,
                        attention_mask=torch.ones(clean.shape[0], total,
                                                  dtype=torch.long),
                        past_key_values=clean_cache,
                        corrupted_past_key_values=corrupt_cache,
                        use_cache=True)
            nxt = out.logits[:, -1].float().argmax(dim=-1, keepdim=True)
            clean = torch.cat([clean, nxt], dim=1)
            step_clean = nxt
            # The corrupted stream is a fixed sequence, consumed one token per
            # step so both streams stay the same length.
            step_corrupt = corrupt[:, total:total + 1]
    return clean


# ----------------------------------------------------------------------------
# 1. cached generation == uncached generation
# ----------------------------------------------------------------------------

@pytest.mark.parametrize("ablation", ABLATIONS)
@pytest.mark.parametrize("config", CONFIGS)
def test_cached_generation_matches_uncached(ablation, config):
    model = _tiny()
    _set_gates(model, config)

    torch.manual_seed(3)
    B, P, N = 2, 6, 8
    clean0 = torch.randint(1, 101, (B, P))
    corrupt = torch.randint(1, 101, (B, P + N))

    hook = _hook_for(model, ablation, clean0, corrupt[:, :P],
                     torch.ones(B, P, dtype=torch.long))

    slow = _generate_uncached(model, clean0, corrupt, N, hook)
    fast = _generate_cached(model, clean0, corrupt, N, hook)

    assert torch.equal(slow, fast), (
        f"{ablation}/{config}: cached decode diverged from the full re-forward\n"
        f"  uncached {slow.tolist()}\n  cached   {fast.tolist()}")


def test_cached_prefill_logits_match_uncached():
    """Prefill alone — the allclose companion to the argmax comparison above."""
    model = _tiny()
    _set_gates(model, "circuit_only")

    torch.manual_seed(11)
    B, T = 2, 9
    ids = torch.randint(1, 101, (B, T))
    corrupt = torch.randint(1, 101, (B, T))
    mask = torch.ones(B, T, dtype=torch.long)

    with torch.no_grad():
        uncached = model(input_ids=ids, corrupted_input_ids=corrupt,
                         attention_mask=mask, use_cache=False).logits
        cached = model(input_ids=ids, corrupted_input_ids=corrupt,
                       attention_mask=mask,
                       past_key_values=DynamicCache(),
                       corrupted_past_key_values=DynamicCache(),
                       use_cache=True).logits

    assert torch.allclose(uncached, cached, atol=1e-5), \
        f"prefill max diff {(uncached - cached).abs().max().item():.3e}"


def test_the_two_caches_stay_separate():
    """A shared cache would concatenate corrupt K/V into the clean entry."""
    model = _tiny()
    _set_gates(model, "full")

    torch.manual_seed(5)
    ids = torch.randint(1, 101, (1, 4))
    corrupt = torch.randint(1, 101, (1, 4))
    clean_cache, corrupt_cache = DynamicCache(), DynamicCache()
    with torch.no_grad():
        model(input_ids=ids, corrupted_input_ids=corrupt,
              attention_mask=torch.ones(1, 4, dtype=torch.long),
              past_key_values=clean_cache,
              corrupted_past_key_values=corrupt_cache,
              use_cache=True)

    assert clean_cache.get_seq_length() == 4
    assert corrupt_cache.get_seq_length() == 4, \
        "the corrupted stream did not write to its own cache"

    shared = DynamicCache()
    with pytest.raises(ValueError, match="distinct Cache objects"):
        model(input_ids=ids, corrupted_input_ids=corrupt,
              attention_mask=torch.ones(1, 4, dtype=torch.long),
              past_key_values=shared, corrupted_past_key_values=shared,
              use_cache=True)


def test_out_of_step_caches_are_rejected():
    model = _tiny()
    _set_gates(model, "full")
    torch.manual_seed(5)
    ids = torch.randint(1, 101, (1, 4))
    corrupt = torch.randint(1, 101, (1, 4))
    clean_cache, corrupt_cache = DynamicCache(), DynamicCache()
    with torch.no_grad():
        model(input_ids=ids, corrupted_input_ids=corrupt,
              attention_mask=torch.ones(1, 4, dtype=torch.long),
              past_key_values=clean_cache,
              corrupted_past_key_values=DynamicCache(),
              use_cache=True)
    # clean_cache now holds 4 tokens, corrupt_cache still holds 0.
    with pytest.raises(ValueError, match="out of step"):
        model(input_ids=ids[:, :1], corrupted_input_ids=corrupt[:, :1],
              attention_mask=torch.ones(1, 5, dtype=torch.long),
              past_key_values=clean_cache,
              corrupted_past_key_values=corrupt_cache,
              use_cache=True)


# ----------------------------------------------------------------------------
# 2. the use_cache=False path has not moved
# ----------------------------------------------------------------------------

def test_uncached_logits_are_bit_identical_to_the_pre_change_fixture():
    """The regression guard on the causal-mask edit.

    `tests/fixtures/prechange_logits.pt` was captured from the implementation
    that had no corrupt cache and no `create_causal_mask` branch. Training and
    all four shipped evaluations run on this path, so it must not move at all.
    """
    ref = torch.load("tests/fixtures/prechange_logits.pt")
    inputs = ref["_inputs"]
    ids, corrupt = inputs["ids"], inputs["corrupt"]
    masks = dict(inputs["masks"])
    masks["none"] = None

    _, pruned = build_tiny_pair(seed=0)
    pruned.set_final_circuit_mode(False)
    gates = [m for m in pruned.modules() if hasattr(m, "log_alpha")]

    for name, alpha in (("open", None), ("closed_ish", -2.0)):
        if alpha is not None:
            for gate in gates:
                with torch.no_grad():
                    gate.log_alpha.fill_(alpha)
        for mask_name, mask in masks.items():
            with torch.no_grad():
                got = pruned(input_ids=ids, corrupted_input_ids=corrupt,
                             attention_mask=mask, use_cache=False).logits
            expected = ref[f"{name}/{mask_name}"]
            assert torch.equal(got, expected), (
                f"{name}/{mask_name} moved: max diff "
                f"{(got - expected).abs().max().item():.3e}")


# ----------------------------------------------------------------------------
# 3. left padding
# ----------------------------------------------------------------------------

def test_left_padded_batch_matches_batch_size_one_and_has_no_nan():
    """Left padding is what generation needs and what the old mask broke.

    Under the manual construction a fully-padded query row is all `-inf`,
    softmax returns NaN, and the `0 * NaN` in the gate mixture leaks that NaN
    into real positions one layer later. `create_causal_mask` is used for every
    cache-mode forward precisely so this batch is safe.
    """
    model = _tiny()
    _set_gates(model, "circuit_only")

    torch.manual_seed(17)
    short, long = 4, 7
    a = torch.randint(1, 101, (1, long))
    b = torch.randint(1, 101, (1, short))
    ca = torch.randint(1, 101, (1, long))
    cb = torch.randint(1, 101, (1, short))

    pad = 0
    batch_ids = torch.cat([a, torch.cat([torch.full((1, long - short), pad), b], 1)], 0)
    batch_corrupt = torch.cat([ca, torch.cat([torch.full((1, long - short), pad), cb], 1)], 0)
    batch_mask = torch.ones(2, long, dtype=torch.long)
    batch_mask[1, :long - short] = 0

    with torch.no_grad():
        batched = model(input_ids=batch_ids, corrupted_input_ids=batch_corrupt,
                        attention_mask=batch_mask,
                        past_key_values=DynamicCache(),
                        corrupted_past_key_values=DynamicCache(),
                        use_cache=True).logits

    assert not torch.isnan(batched).any(), \
        "left padding produced NaN — the causal mask is masking whole query rows"

    for row, (ids, corrupt) in enumerate(((a, ca), (b, cb))):
        with torch.no_grad():
            alone = model(input_ids=ids, corrupted_input_ids=corrupt,
                          attention_mask=torch.ones_like(ids),
                          past_key_values=DynamicCache(),
                          corrupted_past_key_values=DynamicCache(),
                          use_cache=True).logits
        # Only the last position is compared: it is the one generation reads,
        # and it is the only position whose full context is identical between
        # the padded and unpadded runs.
        assert torch.allclose(batched[row, -1], alone[0, -1], atol=1e-4), (
            f"row {row} last-position logits differ between the left-padded "
            f"batch and batch size 1 by "
            f"{(batched[row, -1] - alone[0, -1]).abs().max().item():.3e}")
