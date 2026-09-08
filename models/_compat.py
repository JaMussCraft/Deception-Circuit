"""Version glue for the two transformers internals the dual-stream models call.

`models/llama_node.py` and `models/gpt2_node.py` reach past the public API into
`create_causal_mask` and `Cache.get_mask_sizes`. Both changed shape across the
versions this project runs under -- 4.57.3 on the login node, where the tests
and every published number were produced, and 5.13 in the `mgnp` job
environment that `scripts/evaluate_circuit.sbatch` activates::

    create_causal_mask
      4.57    (config, input_embeds,  attention_mask, cache_position, past_key_values, position_ids=None, ...)
      5.5/5.8 (config, inputs_embeds, attention_mask, cache_position=None, *, past_key_values, position_ids=None, ...)
      5.13    (config, inputs_embeds, attention_mask, past_key_values, position_ids=None, ..., block_sequence_ids=None)

    Cache.get_mask_sizes
      4.57    (cache_position: Tensor, layer_idx) -> (int, int)
      5.x     (query_length:   int,    layer_idx) -> (int, int)

Three things make this worth a module rather than an inline branch.

The `input_embeds` -> `inputs_embeds` rename and the dropped `cache_position`
raise a clear `TypeError`, so they only cost an afternoon. **`get_mask_sizes`
does not.** Hand 4.57's tensor to 5.x and it does not raise -- it broadcasts,
and returns a kv_length *tensor* as wide as the query block. The caller's
mask-width guard then stops comparing widths and starts raising "Boolean value
of Tensor with more than one value is ambiguous" on the first cached decode
step, which is how this was found.

Second: 5.5/5.8 made `past_key_values` keyword-only, so every call here is
keyword-only too. A positional call that works on 4.57 breaks there.

Third, and the part that is deliberately *not* papered over: 5.13 derives the
query offset from `past_key_values.get_seq_length()` and ignores
`cache_position` entirely (its own docstring says "Deprecated and unused").
For a contiguous decode loop -- the only kind `evaluation/gen_engine.py` runs
-- that is the same number by construction, and the cached-vs-uncached
equivalence tests in `tests/test_kv_cache.py` are what hold it to that. No
attempt is made to reconstruct 4.57's offset semantics on 5.13.

None of this is reachable from `use_cache=False`, which is why all four of the
original evaluations ran clean on both versions and nothing noticed until open
generation needed the cache.
"""

from __future__ import annotations

import inspect

from transformers.masking_utils import create_causal_mask as _create_causal_mask

# Signature probing is per-callable and per-class, not per-call: `generate`
# runs this once per decode step per layer.
_MASK_PLAN: dict = {}
_MASK_SIZES_WANTS_LENGTH: dict = {}


def _mask_plan(fn):
    """(embeds keyword name, whether this version accepts cache_position)."""
    plan = _MASK_PLAN.get(fn)
    if plan is None:
        params = inspect.signature(fn).parameters
        # 4.57 spells it `input_embeds`; everything from 5.0 on spells it
        # `inputs_embeds`. Probe for the newer name so an unrecognised
        # signature falls back to the older, which fails loudly on a rename
        # rather than silently passing the wrong tensor.
        plan = ("inputs_embeds" if "inputs_embeds" in params else "input_embeds",
                "cache_position" in params)
        _MASK_PLAN[fn] = plan
    return plan


def create_causal_mask(*, config, inputs_embeds, attention_mask, cache_position,
                       past_key_values, position_ids=None):
    """`transformers.masking_utils.create_causal_mask`, spelled for this version.

    Keyword-only on purpose: 5.5 and 5.8 make `past_key_values` keyword-only,
    so a positional call that works on 4.57 is a `TypeError` there.

    `cache_position` is passed when the installed signature accepts it (4.57
    requires it; 5.5/5.8 accept and ignore it) and dropped when it does not
    (5.13 removed it). See the module docstring for why dropping it is safe.
    """
    embeds_kw, wants_cache_position = _mask_plan(_create_causal_mask)
    kwargs = {
        "config": config,
        embeds_kw: inputs_embeds,
        "attention_mask": attention_mask,
        "past_key_values": past_key_values,
        "position_ids": position_ids,
    }
    if wants_cache_position:
        kwargs["cache_position"] = cache_position
    return _create_causal_mask(**kwargs)


def cache_kv_length(cache, cache_position):
    """The key-block width this cache will report to `create_causal_mask`.

    Asking the cache is the point: `get_mask_sizes` is the very function
    `create_causal_mask` calls, so a guard built on it reproduces that answer
    by construction for every `Cache` subclass. A `DynamicCache` reports
    `get_seq_length() + len(cache_position)`, but a `StaticCache` reports
    `max_cache_len` regardless of fill level, and hard-coding the dynamic
    formula would invert the check there. It reads only host-side ints and
    shapes, so unlike `int(cache_position[-1])` it costs no device sync.
    """
    klass = type(cache)
    wants_length = _MASK_SIZES_WANTS_LENGTH.get(klass)
    if wants_length is None:
        params = inspect.signature(klass.get_mask_sizes).parameters
        wants_length = "query_length" in params
        _MASK_SIZES_WANTS_LENGTH[klass] = wants_length
    argument = cache_position.shape[0] if wants_length else cache_position
    kv_length, _ = cache.get_mask_sizes(argument, 0)
    # Both versions are documented to return ints. Coerce anyway, so that a
    # future signature change degrades to a wrong-but-loud comparison -- or to
    # "only one element tensors can be converted to Python scalars" -- rather
    # than to the ambiguous-tensor crash this module exists to prevent.
    return int(kv_length)
