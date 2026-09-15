"""
component_analysis/hooks.py — every nnsight call in this package, and nothing else.

ADR-0001 puts the component analyses on the unmodified HuggingFace
`LlamaForCausalLM` under nnsight 0.7.0, reaching senders and receivers at module
boundaries (`embed_tokens`, the `o_proj` input for per-head output,
`q_proj`/`k_proj`/`v_proj`, `mlp`, `lm_head`). The prunable wrapper is never
instantiated here.

nnsight 0.7.0 is pinned and its `main` branch is the 0.8 rewrite, so the hook
surface is confined to this one module: a 0.8 migration touches this file and
no other. Two rules keep that true:

  * every nnsight import happens *inside* a function, so the rest of the
    package imports in the login-node base environment. That env is Python 3.9
    and does carry an nnsight — 0.5.12, kept for the parent Alignment repo —
    but not the pinned 0.7.0, which needs Python >= 3.10. So the question is
    never "does nnsight import here" but "is it the pinned version", which is
    what `tests/test_nnsight_hooks.py` gates on;
  * no other module in this package imports nnsight, directly or indirectly.

Ticket 01 fills in only the model loading. The attention-profile, DLA,
path-patch and knockout functions land in the tickets that need them, each as a
small function on top of `load_analysis_model`.

Two nnsight 0.7.0 behaviours to build on, both established by
`scripts/smoke_nnsight.py` on the tiny model:

  * **Envoy accesses inside a trace must be in execution order.** They resolve
    lazily against the forward as it runs, so reading `o_proj.input` before
    `q_proj.output` ends the trace with
    `MissedProviderError: ... was not provided`, as though q_proj had never
    run. Write the accesses in the order the modules execute.
  * **Save the attention tuple, not its second element.** Under SDPA in
    transformers 5.13 `self_attn.output[1]` is None, and calling `.save()` on
    it never binds the name — an `UnboundLocalError` rather than the None the
    caller expected. Save `self_attn.output` and index afterwards.
"""

from __future__ import annotations

#: Attention implementation per analysis. Attention weights come back as None
#: under SDPA in transformers 5.13, so pattern extraction needs eager — and
#: eager costs a [batch, heads, seq, seq] buffer per layer, so nothing else
#: pays for it.
SDPA = "sdpa"
EAGER = "eager"


def load_analysis_model(model_name: str, *, device: str = "cuda",
                        hf_token: str = None, attn_implementation: str = SDPA,
                        dtype=None):
    """The unmodified HF model, wrapped for nnsight tracing.

    Returns an `nnsight.LanguageModel` over `LlamaForCausalLM`. It is dispatched
    eagerly (`dispatch=True`) so the weights are on the device before the first
    trace, rather than on the first `.trace()` call inside a timed analysis.

    `attn_implementation` stays a parameter rather than a constant because the
    same loaded model is switched to eager for attention patterns and back to
    SDPA for everything else (`set_attn_implementation` exists in transformers
    5.13); callers that only ever want one of the two can pass it here.

    `dispatch` is consumed by nnsight's own `MetaMixin.__init__` in 0.7.0
    (checked in the installed source, since the only mentions in the package
    are in docstrings); `device_map` and `dtype` pass through to
    `from_pretrained`, where `dtype` is transformers 5.x's spelling of what
    `models/__init__.py` still calls `torch_dtype` for the 4.57 login env.

    `tests/test_nnsight_hooks.py` exercises the CPU path with the three
    HuggingFace loaders faked, which pins where each kwarg lands. The GPU path
    — `device_map="cuda"` and the bfloat16 default that follows from it — has
    no test, so the first ticket to load a model on a GPU should treat a
    successful call as its own first assertion.
    """
    import torch
    from nnsight import LanguageModel

    from models import MODEL_REGISTRY

    if model_name in MODEL_REGISTRY:
        hf_id = MODEL_REGISTRY[model_name][0]
    else:
        hf_id = model_name

    kwargs = {"attn_implementation": attn_implementation}
    if dtype is not None:
        kwargs["dtype"] = dtype
    elif device != "cpu":
        kwargs["dtype"] = torch.bfloat16
    if hf_token:
        kwargs["token"] = hf_token
        # `LanguageModel._load` forwards **kwargs to the config and to the
        # model, but loads the tokenizer from a separate `tokenizer_kwargs`
        # that defaults to empty. Without this the weights of a gated repo load
        # and the tokenizer then 401s, naming the tokenizer rather than the
        # token. `models/__init__.py` passes it to both loaders for the same
        # reason.
        kwargs["tokenizer_kwargs"] = {"token": hf_token}

    return LanguageModel(hf_id, device_map=device, dispatch=True, **kwargs)
