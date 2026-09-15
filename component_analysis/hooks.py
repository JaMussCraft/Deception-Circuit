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
    package imports in the login-node environment, where nnsight cannot be
    installed (it needs Python >= 3.10);
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

    return LanguageModel(hf_id, device_map=device, dispatch=True, **kwargs)
