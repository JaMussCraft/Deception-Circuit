"""The version glue in `models/_compat.py`.

These tests carry the three `create_causal_mask` signatures and the two
`get_mask_sizes` signatures as *fakes*, so one environment can check the
dispatch for all of them. The signatures are transcribed from the installed
transformers in this cluster's conda envs:

    4.57.3  /sw/external/python/anaconda3   (login node; the tests and every
                                             published number ran here)
    5.5.0   ~/.conda/envs/bloom
    5.8.0   ~/.conda/envs/nnsight
    5.13.0  ~/.conda/envs/mgnp             (the env evaluate_circuit.sbatch
                                             activates)

`test_the_installed_signature_is_one_we_handle` is the tripwire: it runs
against whatever transformers is actually importable, so an upgrade that
changes these functions a third time fails here, in a two-second test, instead
of on the first cached decode step of a twelve-hour GPU job.
"""

from __future__ import annotations

import pytest
import torch

from models import _compat


# --------------------------------------------------------------------------
# create_causal_mask: three signatures, one call site
# --------------------------------------------------------------------------

def _recorder(fn):
    """Wrap a fake so the kwargs it was called with land in `fn.seen`."""
    fn.seen = None
    return fn


def fake_457(config, input_embeds, attention_mask, cache_position,
             past_key_values, position_ids=None, or_mask_function=None,
             and_mask_function=None):
    fake_457.seen = dict(config=config, input_embeds=input_embeds,
                         attention_mask=attention_mask,
                         cache_position=cache_position,
                         past_key_values=past_key_values,
                         position_ids=position_ids)
    return "457-mask"


def fake_58(config, inputs_embeds, attention_mask, cache_position=None, *,
            past_key_values, position_ids=None, or_mask_function=None,
            and_mask_function=None):
    fake_58.seen = dict(config=config, inputs_embeds=inputs_embeds,
                        attention_mask=attention_mask,
                        cache_position=cache_position,
                        past_key_values=past_key_values,
                        position_ids=position_ids)
    return "58-mask"


def fake_513(config, inputs_embeds, attention_mask, past_key_values,
             position_ids=None, or_mask_function=None, and_mask_function=None,
             block_sequence_ids=None):
    fake_513.seen = dict(config=config, inputs_embeds=inputs_embeds,
                         attention_mask=attention_mask,
                         past_key_values=past_key_values,
                         position_ids=position_ids)
    return "513-mask"


def _call(monkeypatch, fake, cache_position=None):
    monkeypatch.setattr(_compat, "_create_causal_mask", fake)
    _compat._MASK_PLAN.pop(fake, None)
    return _compat.create_causal_mask(
        config="CFG",
        inputs_embeds="EMB",
        attention_mask="AM",
        cache_position=torch.arange(3) if cache_position is None else cache_position,
        past_key_values="PKV",
        position_ids="PID",
    )


def test_the_457_signature_gets_the_old_embeds_name_and_cache_position(monkeypatch):
    assert _call(monkeypatch, fake_457) == "457-mask"
    seen = fake_457.seen
    assert seen["input_embeds"] == "EMB"
    assert torch.equal(seen["cache_position"], torch.arange(3))
    assert seen["past_key_values"] == "PKV"


def test_the_5_8_signature_gets_the_new_embeds_name_and_still_takes_cache_position(monkeypatch):
    # 5.5/5.8 accept `cache_position` (deprecated, ignored) and make
    # `past_key_values` keyword-only -- a positional call breaks here, so this
    # also pins that every argument goes by keyword.
    assert _call(monkeypatch, fake_58) == "58-mask"
    seen = fake_58.seen
    assert seen["inputs_embeds"] == "EMB"
    assert torch.equal(seen["cache_position"], torch.arange(3))


def test_the_5_13_signature_gets_no_cache_position_at_all(monkeypatch):
    # The parameter is gone in 5.13; passing it is a TypeError. The fake has no
    # **kwargs, so if the shim passed it this call would raise rather than
    # quietly ignoring it.
    assert _call(monkeypatch, fake_513) == "513-mask"
    seen = fake_513.seen
    assert seen["inputs_embeds"] == "EMB"
    assert "cache_position" not in seen
    assert seen["past_key_values"] == "PKV"


def test_the_plan_is_cached_per_callable_and_does_not_leak(monkeypatch):
    # Two signatures in one process: a plan cached under one must not be
    # reused for the other.
    _call(monkeypatch, fake_457)
    _call(monkeypatch, fake_513)
    _call(monkeypatch, fake_457)
    assert "cache_position" in fake_457.seen
    assert "cache_position" not in fake_513.seen


def test_the_installed_signature_is_one_we_handle():
    """Tripwire against the next transformers upgrade."""
    import inspect
    params = inspect.signature(_compat._create_causal_mask).parameters
    assert ("inputs_embeds" in params) != ("input_embeds" in params), (
        f"transformers spells the embeds argument something new: {list(params)}")
    embeds_kw, wants_cache_position = _compat._mask_plan(_compat._create_causal_mask)
    assert embeds_kw in params
    assert wants_cache_position == ("cache_position" in params)
    # Whatever the version, these five must be nameable.
    for required in ("config", "attention_mask", "past_key_values", "position_ids"):
        assert required in params, f"{required} missing from {list(params)}"


# --------------------------------------------------------------------------
# get_mask_sizes: the change that does not raise
# --------------------------------------------------------------------------

class Cache457:
    """4.57: takes the cache_position tensor, returns ints."""

    def __init__(self, seen_tokens=7):
        self.seen_tokens = seen_tokens

    def get_mask_sizes(self, cache_position, layer_idx):
        assert isinstance(cache_position, torch.Tensor), "4.57 wants the tensor"
        return self.seen_tokens + cache_position.shape[0], 0


class Cache5x:
    """5.x: takes an int query_length.

    Crucially this reproduces the silent failure -- handed 4.57's *tensor* it
    does not raise, it broadcasts and returns a tensor as wide as the query
    block. That tensor is what made the caller's mask-width guard die with
    "Boolean value of Tensor with more than one value is ambiguous".
    """

    def __init__(self, seen_tokens=7):
        self.seen_tokens = seen_tokens

    def get_mask_sizes(self, query_length, layer_idx):
        return self.seen_tokens + query_length, 0


def test_a_457_cache_is_handed_the_tensor():
    assert _compat.cache_kv_length(Cache457(seen_tokens=7), torch.arange(9, 12)) == 10


def test_a_5x_cache_is_handed_the_length_not_the_tensor():
    # The regression. Passing the tensor here returns tensor([10, 10, 10]);
    # the assertion is that we get the scalar 10.
    got = _compat.cache_kv_length(Cache5x(seen_tokens=7), torch.arange(9, 12))
    assert got == 10
    assert isinstance(got, int)


def test_the_broadcast_bug_is_what_this_guards_against():
    """Pins that the fake really does reproduce the historical failure.

    Without this, `test_a_5x_cache_is_handed_the_length_not_the_tensor` would
    still pass against a fake that had been written too forgivingly, and the
    suite would be testing nothing.
    """
    kv_length, _ = Cache5x(seen_tokens=7).get_mask_sizes(torch.arange(9, 12), 0)
    assert isinstance(kv_length, torch.Tensor) and kv_length.numel() == 3
    with pytest.raises(RuntimeError, match="ambiguous"):
        bool(kv_length != 10)


class CacheTensorLength:
    """A cache that reports its width as a 0-d tensor.

    `StaticCache` layers return tensors rather than ints to avoid graph breaks
    under compile, so the coercion in `cache_kv_length` is not hypothetical:
    without it a tensor width reaches the caller's mask-width comparison, which
    is the shape of the original bug.
    """

    def get_mask_sizes(self, query_length, layer_idx):
        return torch.tensor(7 + query_length), 0


def test_a_tensor_kv_length_is_coerced_to_an_int():
    got = _compat.cache_kv_length(CacheTensorLength(), torch.arange(3))
    assert got == 10
    assert isinstance(got, int), "a tensor width leaks into the mask-width guard"


def test_a_single_step_decode_is_dispatched_the_same_way():
    # The decode path calls this with one new token per step.
    assert _compat.cache_kv_length(Cache5x(seen_tokens=11), torch.arange(11, 12)) == 12
    assert _compat.cache_kv_length(Cache457(seen_tokens=11), torch.arange(11, 12)) == 12


def test_the_dispatch_is_cached_per_class_and_does_not_leak():
    for _ in range(2):
        assert _compat.cache_kv_length(Cache457(), torch.arange(3)) == 10
        assert _compat.cache_kv_length(Cache5x(), torch.arange(3)) == 10


def test_the_installed_cache_is_one_we_handle():
    """Tripwire: the real DynamicCache must agree with the real mask builder."""
    from transformers.cache_utils import DynamicCache
    cache = DynamicCache()
    assert _compat.cache_kv_length(cache, torch.arange(5)) == 5
