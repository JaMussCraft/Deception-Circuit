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


# ==============================================================================
# THE SHARED FORWARD PASSES
# ==============================================================================
#
# Three functions, and every component analysis is built from them: capture what
# the Components write, run again with some of it replaced, and read attention
# rows. Tickets 07 and 08 compose `capture_forward` and `replace_forward` into
# interchange knockout and path patching rather than opening a second hook path.
#
# Two conventions they share.
#
# **Component keys.** A key is `(kind, layer, index)` — a `Component` from
# `components.py`, or the plain tuple. The embedding is a sender too (path
# patching sends from it, and replacing every head and MLP block without it
# does not reproduce the other stream, because the residual stream still starts
# from the first prompt's tokens), so it has the reserved key `EMBED_KEY`.
#
# **`positions`.** The Readout position of each row: where the logits are read
# and where the residual stream is taken. It defaults to the last unpadded
# position, which is `prefix_length - 1` under the right padding every dataset
# in this repo uses. *Where a replacement is written* is a property of the
# replacement, not of the call, and rides on `Replacement.positions`.

from dataclasses import dataclass                                  # noqa: E402

#: The token embedding, as a sender. Not a Component — it is neither a head nor
#: an MLP block and never appears in a head table — but it is the start of the
#: residual stream, so a pass that replaces "everything" must include it.
EMBED_KEY = ("embed", 0, 0)


@dataclass
class Replacement:
    """One Component's output, and where to write it.

    `positions=None` writes at every position. Otherwise it is a boolean mask,
    either `[seq]` (the same positions for every row) or `[batch, seq]` (a
    per-instance span, which is what a Segment is), and the Component's own
    output is kept everywhere else.
    """

    value: object
    positions: object = None


@dataclass
class Capture:
    """What one forward wrote, for the Components that were asked for."""

    #: `[batch, vocab]` at the Readout.
    logits: object
    #: `{component key: [batch, seq, dim]}`. `dim` is `head_dim` for a head and
    #: the hidden size for an MLP block or the embedding. Full length, so a
    #: capture can be replayed at any subset of positions later.
    outputs: dict
    #: `[batch, num_layers + 1, hidden]` at the Readout: the embedding output
    #: first, then each decoder layer's output. The logit lens reads this.
    residual: object
    #: `[batch]`, the Readout position each row was read at.
    readout: object


def _hf(model):
    """The HuggingFace model under an nnsight wrapper.

    `LanguageModel` (what `load_analysis_model` returns) and `NNsight` (what the
    tests wrap the tiny model in) both keep it on `_model`.
    """
    return getattr(model, "_model", model)


def _geometry(model):
    """(num_layers, num_heads, head_dim), read from the model's own config."""
    config = _hf(model).config
    heads = config.num_attention_heads
    head_dim = getattr(config, "head_dim", None) or config.hidden_size // heads
    return config.num_hidden_layers, heads, head_dim


def all_component_keys(model) -> list:
    """Every head, every MLP block and the embedding, in execution order.

    The two "reproduces the other stream" invariants hold only for this set —
    a subset leaves part of the residual stream reading the first prompt — so
    the tests and the scaffold check name it rather than rebuilding it.
    """
    num_layers, num_heads, _head_dim = _geometry(model)
    keys = [EMBED_KEY]
    for layer in range(num_layers):
        keys.extend(("head", layer, index) for index in range(num_heads))
        keys.append(("mlp", layer, 0))
    return keys


def _key(component) -> tuple:
    """A `Component`, or a plain `(kind, layer, index)` tuple, as a tuple."""
    key = getattr(component, "key", component)
    kind, layer, index = key
    return (str(kind), int(layer), int(index))


def readout_positions(attention_mask, positions=None):
    """`[batch]` Readout positions: the last unpadded token of each row.

    The datasets pad on the right and predict the answer at `prefix_length - 1`
    (`DeceptionDatasetLlama`), so the last unpadded position *is* the Readout.
    `positions` overrides it — one index for every row, or one per row — which
    is how a caller that already knows `prefix_length` avoids re-deriving it.
    """
    import torch

    if positions is None:
        return attention_mask.sum(-1).long() - 1
    if isinstance(positions, int):
        return torch.full((attention_mask.shape[0],), positions,
                          dtype=torch.long, device=attention_mask.device)
    out = torch.as_tensor(positions, device=attention_mask.device).long()
    if out.ndim == 0:
        out = out.expand(attention_mask.shape[0])
    if out.shape != (attention_mask.shape[0],):
        raise ValueError(f"positions must be one Readout index per row, got "
                         f"{tuple(out.shape)} for batch {attention_mask.shape[0]}")
    return out


def _as_replacement(value) -> Replacement:
    return value if isinstance(value, Replacement) else Replacement(value)


def _write(current, replacement):
    """`current` with `replacement` written where its positions allow."""
    import torch

    value = replacement.value
    if replacement.positions is None:
        return value
    mask = torch.as_tensor(replacement.positions)
    if mask.dtype != torch.bool:
        raise TypeError("Replacement.positions must be a boolean mask over "
                        "token positions, not indices")
    if mask.ndim == 1:
        mask = mask.unsqueeze(0)
    return torch.where(mask.unsqueeze(-1).to(current.device), value, current)


def _plan(keys, num_layers):
    """Component keys grouped for one traced pass: (embed?, {layer: [head]},
    {layer: True}). Raises on a key no forward could reach."""
    embed = False
    heads, mlps = {}, {}
    for key in keys:
        kind, layer, index = key
        if key == EMBED_KEY:
            embed = True
        elif kind == "head":
            heads.setdefault(layer, []).append(index)
        elif kind == "mlp":
            mlps[layer] = True
        else:
            raise ValueError(
                f"{kind!r} is not a Component kind this pass can reach; "
                f"expected 'head', 'mlp' or the embedding key {EMBED_KEY}")
        if key != EMBED_KEY and not 0 <= layer < num_layers:
            raise ValueError(f"layer {layer} is outside the model's "
                             f"{num_layers} layers")
    return embed, heads, mlps


def _traced_forward(model, input_ids, attention_mask, *, capture=(),
                    replacements=None, positions=None, residual=False):
    """One forward: replace what was asked for, capture what was asked for.

    Both public passes go through here, so the interchange primitive and the
    capture it is fed from cannot drift apart. Capturing a Component that is
    also replaced returns the replaced value, which is what "what this
    Component wrote on this forward" means.

    Every envoy access below is written in **execution order** — embedding,
    then per layer the attention output, the MLP output and the layer's own
    output, then the logits. nnsight 0.7.0 resolves these lazily against the
    forward as it runs, so an access out of order ends the trace with
    `MissedProviderError` naming the module that came too late.
    """
    import torch

    replacements = {_key(k): _as_replacement(v)
                    for k, v in (replacements or {}).items()}
    capture = [_key(k) for k in capture]
    num_layers, _num_heads, head_dim = _geometry(model)
    wanted_embed, wanted_heads, wanted_mlps = _plan(capture, num_layers)
    _plan(replacements, num_layers)

    readout = readout_positions(attention_mask, positions)
    rows = torch.arange(input_ids.shape[0], device=readout.device)

    saved_heads, saved_mlps, saved_residual = {}, {}, []
    saved_embed = None
    with torch.no_grad():
        with model.trace(input_ids, attention_mask=attention_mask):
            embedded = model.model.embed_tokens.output
            if EMBED_KEY in replacements:
                embedded = _write(embedded, replacements[EMBED_KEY])
                model.model.embed_tokens.output = embedded
            if wanted_embed:
                saved_embed = embedded.save()
            if residual:
                saved_residual.append(embedded[rows, readout, :].save())

            for layer in range(num_layers):
                block = model.model.layers[layer]

                head_writes = [(index, replacements[("head", layer, index)])
                               for index in range(_num_heads)
                               if ("head", layer, index) in replacements]
                attention = block.self_attn.o_proj.input
                if head_writes:
                    attention = attention.clone()
                    for index, replacement in head_writes:
                        span = slice(index * head_dim, (index + 1) * head_dim)
                        attention[:, :, span] = _write(attention[:, :, span],
                                                       replacement)
                    block.self_attn.o_proj.input = attention
                if layer in wanted_heads:
                    saved_heads[layer] = attention.save()

                mlp = block.mlp.output
                if ("mlp", layer, 0) in replacements:
                    mlp = _write(mlp, replacements[("mlp", layer, 0)])
                    block.mlp.output = mlp
                if layer in wanted_mlps:
                    saved_mlps[layer] = mlp.save()

                if residual:
                    saved_residual.append(block.output[rows, readout, :].save())

            logits = model.output.logits[rows, readout, :].save()

    outputs = {}
    if wanted_embed:
        outputs[EMBED_KEY] = saved_embed.detach()
    for layer, indices in wanted_heads.items():
        for index in indices:
            span = slice(index * head_dim, (index + 1) * head_dim)
            outputs[("head", layer, index)] = saved_heads[layer][:, :, span].detach()
    for layer in wanted_mlps:
        outputs[("mlp", layer, 0)] = saved_mlps[layer].detach()

    stacked = torch.stack([one.detach() for one in saved_residual], dim=1) \
        if residual else None
    return Capture(logits=logits.detach(), outputs=outputs, residual=stacked,
                   readout=readout)


def capture_forward(model, input_ids, attention_mask, *, components,
                    positions=None, replacements=None) -> Capture:
    """One forward: the Readout logits, what each Component wrote, the residual.

    Head output is the **input to `o_proj`**, sliced to the head's own
    `head_dim` columns — the o_proj *output* is already summed over heads, so a
    slice of it is not a head. MLP output is the block's output. Both are
    returned at every position, so one capture serves a position-agnostic patch
    and a position-specific one.

    `replacements` runs the capture under an intervention, which is how ticket
    08 reads a receiver while a sender carries its corrupt value, and how a
    knockout is checked for leaking into the heads beside it.
    """
    return _traced_forward(model, input_ids, attention_mask,
                           capture=components, replacements=replacements,
                           positions=positions, residual=True)


def replace_forward(model, input_ids, attention_mask, *, replacements,
                    positions=None):
    """The Readout logits of one forward with those Component outputs replaced.

    This is *the* interchange primitive: feed it `capture_forward`'s outputs
    from the corrupt stream and the named Components carry corrupt values while
    everything else runs clean. Knockout replaces one Component, path patching
    replaces one sender and re-runs the receivers; neither re-implements it.

    Each replacement is a `[batch, seq, dim]` tensor (written at every
    position) or a `Replacement` carrying a boolean position mask.
    """
    return _traced_forward(model, input_ids, attention_mask,
                           replacements=replacements, positions=positions).logits


def attention_weights(model, input_ids, attention_mask, *, layer, heads,
                      query_positions):
    """Attention rows `[batch, len(heads), len(query_positions), seq]`.

    Eager attention is switched on for this call and the previous
    implementation restored in a `finally`, because under SDPA in transformers
    5.13 the weights come back as None and eager costs a
    `[batch, 32, seq, seq]` buffer per layer that no other analysis should pay
    for (ADR-0001).

    `query_positions` is either one sequence of positions for the whole batch
    or `[batch, k]`, one set per row — a Segment is a per-instance span, so the
    second form is the one ticket 03 wants.

    The saved value is the whole `self_attn.output` tuple: indexing `[1]`
    *inside* the trace never binds under SDPA, which surfaces as an
    `UnboundLocalError` rather than the None transformers documents.
    """
    import torch

    hf = _hf(model)
    previous = hf.config._attn_implementation
    try:
        hf.set_attn_implementation(EAGER)
        with torch.no_grad():
            with model.trace(input_ids, attention_mask=attention_mask):
                attention = model.model.layers[layer].self_attn.output.save()
    finally:
        hf.set_attn_implementation(previous)

    weights = attention[1]
    if weights is None:
        raise RuntimeError(
            f"attention weights came back None from layer {layer} under "
            f"{hf.config._attn_implementation!r}; eager attention did not take")

    selected = weights[:, torch.as_tensor(list(heads), dtype=torch.long)]
    positions = torch.as_tensor(query_positions, dtype=torch.long,
                                device=selected.device)
    if positions.ndim == 1:
        positions = positions.unsqueeze(0).expand(selected.shape[0], -1)
    index = positions.unsqueeze(1).unsqueeze(-1).expand(
        selected.shape[0], selected.shape[1], positions.shape[1],
        selected.shape[-1])
    return torch.gather(selected, 2, index).detach()
