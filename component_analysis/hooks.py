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

Four things live here: `load_analysis_model`, and the three shared forward
passes every analysis is built from — `capture_forward`, `replace_forward` and
`attention_weights` — plus the fp32 readout ADR-0001 requires for ranking
metrics. An analysis composes them; it does not open a second hook path, and it
never reaches through the nnsight wrapper itself (`device_and_dtype`,
`attention_implementation` and `describe` are here so that it does not have to).

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
                        hf_token: str = None, dtype=None):
    """The unmodified HF model, wrapped for nnsight tracing.

    Returns an `nnsight.LanguageModel` over `LlamaForCausalLM`. It is dispatched
    eagerly (`dispatch=True`) so the weights are on the device before the first
    trace, rather than on the first `.trace()` call inside a timed analysis.

    The model always loads under **SDPA**. ADR-0001 says eager attention is
    switched on only for pattern extraction, and `attention_weights` does that
    itself, for the length of one trace, restoring the previous implementation
    in a `finally`. A load-time override would have let a caller pay the
    `[batch, 32, seq, seq]` buffer per layer for every analysis, which is the
    cost the ADR is avoiding.

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

    kwargs = {"attn_implementation": SDPA}
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
# Three passes, and every component analysis is built from them: capture what
# the model writes and reads, run again with some of it replaced, and read
# attention rows. Tickets 07 and 08 compose `capture_forward` and
# `replace_forward` into interchange knockout and path patching rather than
# opening a second hook path.
#
# **Keys.** Everything a pass can touch is named `(kind, layer, index)` — a
# `Component` from `components.py`, or the plain tuple. Senders write into the
# residual stream; receivers read out of it, and path patching needs both.
#
#     ("embed", 0, 0)      EMBED_KEY    sender    the token embedding's output
#     ("head", layer, h)                sender    the `o_proj` input, head h's slice
#     ("mlp", layer, 0)                 sender    the MLP block's output
#     ("q", layer, h)                   receiver  `q_proj` output, head h's slice
#     ("k", layer, g)                   receiver  `k_proj` output, KV group g's slice
#     ("v", layer, g)                   receiver  `v_proj` output, KV group g's slice
#     ("mlp_in", layer, 0)              receiver  the MLP block's input
#     ("readout", 0, 0)    READOUT_KEY  receiver  the final norm's input
#
# Under grouped-query attention K and V are **per KV group**, not per head:
# Llama-3.1-8B has 8 KV groups of 4 query heads, so patching "head 7's K" would
# silently patch heads 4 to 7. `kv_group_of(model, head)` does the conversion
# and `heads_of_kv_group` inverts it.
#
# **`positions`.** The Readout position of each row: where the logits are read
# and where the residual stream is taken. It defaults to the last unpadded
# position, which is `prefix_length - 1` under the right padding every dataset
# in this repo uses. *Where a replacement is written* is a property of the
# replacement, not of the call, and rides on `Replacement.positions`.

from dataclasses import dataclass                                  # noqa: E402
from typing import Dict, List, Optional                            # noqa: E402

#: The token embedding, as a sender. Not a Component — it is neither a head nor
#: an MLP block and never appears in a head table — but it is the start of the
#: residual stream, so a pass that replaces "everything" must include it.
EMBED_KEY = ("embed", 0, 0)

#: The residual stream entering the final norm, as a receiver. The last thing
#: any sender can reach before the logits, and the receiver every direct effect
#: is measured at.
READOUT_KEY = ("readout", 0, 0)

#: Kinds sliced per attention head, and kinds sliced per KV group.
HEAD_KINDS = ("head", "q")
GROUP_KINDS = ("k", "v")
#: Kinds that are one whole tensor, indexed 0.
WHOLE_KINDS = ("mlp", "mlp_in", "embed", "readout")


@dataclass
class Replacement:
    """One key's value, and where to write it.

    `positions=None` writes at every position. Otherwise it is a boolean mask,
    either `[seq]` (the same positions for every row) or `[batch, seq]` (a
    per-instance span, which is what a Segment is), and the site's own value is
    kept everywhere else.
    """

    value: "torch.Tensor"
    positions: Optional["torch.Tensor"] = None


@dataclass
class Capture:
    """What one forward wrote and read, at the keys that were asked for."""

    #: `[batch, vocab]` at the Readout, in the model's own dtype. Ranking
    #: metrics go through `readout_logits` instead (ADR-0001: fp32).
    logits: "torch.Tensor"
    #: `{key: [batch, seq, dim]}`. `dim` is `head_dim` for a head or a Q slice,
    #: `head_dim` for a K or V group, and the hidden size for everything else.
    #: Full length, so one capture can be replayed at any subset of positions.
    outputs: Dict[tuple, "torch.Tensor"]
    #: `[batch, num_layers + 1, hidden]` at the Readout: the embedding output,
    #: then each decoder layer's. The logit lens reads this, and `[:, -1]` is
    #: the residual the final norm sees.
    residual: Optional["torch.Tensor"]
    #: `[batch]`, the Readout position each row was read at.
    readout: "torch.Tensor"


# ==============================================================================
# THE MODEL, WITHOUT REACHING THROUGH THE WRAPPER
# ==============================================================================

def _hf(model):
    """The HuggingFace model under an nnsight wrapper.

    `LanguageModel` (what `load_analysis_model` returns) and `NNsight` (what the
    tests wrap the tiny model in) both keep it on `_model`. That attribute is
    nnsight's, and private, so it is read here and nowhere else: ADR-0001's
    "a migration touches one file" is about this handle as much as about the
    imports.
    """
    return getattr(model, "_model", model)


def device_and_dtype(model) -> tuple:
    """`(device, dtype)` of the model's weights, for a caller that must assert
    it loaded where it meant to."""
    parameter = next(iter(_hf(model).parameters()))
    return parameter.device, parameter.dtype


def attention_implementation(model) -> str:
    """Which attention kernel the model is currently running, `sdpa` or `eager`."""
    return _hf(model).config._attn_implementation


def describe(model) -> str:
    """One line naming the wrapper, the model, where it is and how it runs."""
    device, dtype = device_and_dtype(model)
    return (f"{type(model).__name__} over {type(_hf(model)).__name__}, "
            f"{device}, {dtype}, attn {attention_implementation(model)}")


def geometry(model) -> dict:
    """The shapes every key depends on, read from the model's own config."""
    config = _hf(model).config
    num_heads = config.num_attention_heads
    head_dim = getattr(config, "head_dim", None) or config.hidden_size // num_heads
    num_kv_heads = getattr(config, "num_key_value_heads", None) or num_heads
    return {"num_layers": config.num_hidden_layers, "num_heads": num_heads,
            "head_dim": head_dim, "num_kv_heads": num_kv_heads,
            "heads_per_group": num_heads // num_kv_heads,
            "hidden_size": config.hidden_size}


def kv_group_of(model, head: int) -> int:
    """The KV group a query head reads its K and V from."""
    return head // geometry(model)["heads_per_group"]


def heads_of_kv_group(model, group: int) -> List[int]:
    """The query heads a K or V patch on this group reaches."""
    per_group = geometry(model)["heads_per_group"]
    return list(range(group * per_group, (group + 1) * per_group))


def all_component_keys(model) -> list:
    """Every sender: the embedding, every head, every MLP block, in run order.

    The two "reproduces the other stream" invariants hold only for this set —
    a subset leaves part of the residual stream reading the first prompt — so
    the tests and the scaffold check name it rather than rebuilding it.
    """
    shape = geometry(model)
    keys = [EMBED_KEY]
    for layer in range(shape["num_layers"]):
        keys.extend(("head", layer, head) for head in range(shape["num_heads"]))
        keys.append(("mlp", layer, 0))
    return keys


def all_receiver_keys(model) -> list:
    """Every receiver: each head's Q, each KV group's K and V, each MLP input,
    and the Readout. K and V are per group, as ADR-0001 requires under GQA."""
    shape = geometry(model)
    keys = []
    for layer in range(shape["num_layers"]):
        keys.extend(("q", layer, head) for head in range(shape["num_heads"]))
        keys.extend(("k", layer, group) for group in range(shape["num_kv_heads"]))
        keys.extend(("v", layer, group) for group in range(shape["num_kv_heads"]))
        keys.append(("mlp_in", layer, 0))
    keys.append(READOUT_KEY)
    return keys


# ==============================================================================
# KEYS, POSITIONS AND WRITES
# ==============================================================================

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


def _plan(keys, shape) -> dict:
    """Keys grouped by site for one traced pass, in execution order.

    Raises on a key no forward could reach, because a silently ignored key
    looks exactly like a Component with no effect.
    """
    sites: Dict[str, dict] = {kind: {} for kind in
                              ("q", "k", "v", "head", "mlp_in", "mlp")}
    flags = {"embed": False, "readout": False}
    limits = {"q": shape["num_heads"], "head": shape["num_heads"],
              "k": shape["num_kv_heads"], "v": shape["num_kv_heads"],
              "mlp": 1, "mlp_in": 1}

    for key in keys:
        kind, layer, index = key
        if key == EMBED_KEY:
            flags["embed"] = True
            continue
        if key == READOUT_KEY:
            flags["readout"] = True
            continue
        if kind not in sites:
            raise ValueError(
                f"{kind!r} is not a kind this pass can reach; expected one of "
                f"{', '.join(sorted(sites))}, {EMBED_KEY} or {READOUT_KEY}")
        if not 0 <= layer < shape["num_layers"]:
            raise ValueError(f"layer {layer} is outside the model's "
                             f"{shape['num_layers']} layers")
        if not 0 <= index < limits[kind]:
            raise ValueError(
                f"{kind!r} index {index} is outside 0..{limits[kind] - 1}"
                + (f"; K and V are per KV group, not per head — "
                   f"kv_group_of() converts" if kind in GROUP_KINDS else ""))
        sites[kind].setdefault(layer, []).append(index)
    return {"sites": sites, **flags}


def _traced_forward(model, input_ids, attention_mask, *, capture=(),
                    replacements=None, positions=None, residual=False):
    """One forward: replace what was asked for, capture what was asked for.

    Both public passes go through here, so the interchange primitive and the
    capture it is fed from cannot drift apart. Capturing a site that is also
    replaced returns the replaced value, which is what "what this site carried
    on this forward" means.

    Every envoy access below is written in **execution order** — embedding,
    then per layer q, k, v, the attention output, the MLP input, the MLP output
    and the layer's own output, then the final norm's input and the logits.
    nnsight 0.7.0 resolves these lazily against the forward as it runs, so an
    access out of order ends the trace with `MissedProviderError` naming the
    module that came too late.
    """
    import torch

    replacements = {_key(k): _as_replacement(v)
                    for k, v in (replacements or {}).items()}
    capture = [_key(k) for k in capture]
    shape = geometry(model)
    head_dim = shape["head_dim"]
    wanted = _plan(capture, shape)
    written = _plan(replacements, shape)

    readout = readout_positions(attention_mask, positions)
    rows = torch.arange(input_ids.shape[0], device=readout.device)
    saved: Dict[tuple, object] = {}
    saved_residual = []

    def site(kind, layer, value, width):
        """Apply this site's writes to `value` and save it if it was asked for.

        `width` is the slice width per index, or None when the site is one
        whole tensor. Returns the effective value; the caller assigns it back
        only when something was written, so an untouched forward stays exact.
        """
        writes = written["sites"][kind].get(layer, [])
        if writes:
            if width is None:
                value = _write(value, replacements[(kind, layer, writes[0])])
            else:
                value = value.clone()
                for index in writes:
                    span = slice(index * width, (index + 1) * width)
                    value[:, :, span] = _write(value[:, :, span],
                                               replacements[(kind, layer, index)])
        if layer in wanted["sites"][kind]:
            saved[(kind, layer)] = value.save()
        return value, bool(writes)

    with torch.no_grad():
        with model.trace(input_ids, attention_mask=attention_mask):
            embedded = model.model.embed_tokens.output
            if written["embed"]:
                embedded = _write(embedded, replacements[EMBED_KEY])
                model.model.embed_tokens.output = embedded
            if wanted["embed"]:
                saved[EMBED_KEY] = embedded.save()
            if residual:
                saved_residual.append(embedded[rows, readout, :].save())

            for layer in range(shape["num_layers"]):
                block = model.model.layers[layer]
                attention = block.self_attn

                for kind, module, width in (("q", attention.q_proj, head_dim),
                                            ("k", attention.k_proj, head_dim),
                                            ("v", attention.v_proj, head_dim)):
                    value, changed = site(kind, layer, module.output, width)
                    if changed:
                        module.output = value

                value, changed = site("head", layer, attention.o_proj.input,
                                      head_dim)
                if changed:
                    attention.o_proj.input = value

                value, changed = site("mlp_in", layer, block.mlp.input, None)
                if changed:
                    block.mlp.input = value

                value, changed = site("mlp", layer, block.mlp.output, None)
                if changed:
                    block.mlp.output = value

                if residual:
                    saved_residual.append(block.output[rows, readout, :].save())

            final = model.model.norm.input
            if written["readout"]:
                final = _write(final, replacements[READOUT_KEY])
                model.model.norm.input = final
            if wanted["readout"]:
                saved[READOUT_KEY] = final.save()

            logits = model.output.logits[rows, readout, :].save()

    outputs = {}
    for key in capture:
        kind, layer, index = key
        if key in (EMBED_KEY, READOUT_KEY):
            outputs[key] = saved[key].detach()
        elif kind in WHOLE_KINDS:
            outputs[key] = saved[(kind, layer)].detach()
        else:
            span = slice(index * head_dim, (index + 1) * head_dim)
            outputs[key] = saved[(kind, layer)][:, :, span].detach()

    stacked = torch.stack([one.detach() for one in saved_residual], dim=1) \
        if residual else None
    return Capture(logits=logits.detach(), outputs=outputs, residual=stacked,
                   readout=readout)


def capture_forward(model, input_ids, attention_mask, *, components,
                    positions=None, replacements=None) -> Capture:
    """One forward: the Readout logits, what each key carried, the residual.

    Head output is the **input to `o_proj`**, sliced to the head's own
    `head_dim` columns — the o_proj *output* is already summed over heads, so a
    slice of it is not a head. Receiver keys come back the same way: a Q slice
    per head, a K or V slice per KV group, the MLP block's input, the residual
    entering the final norm. Everything is returned at every position, so one
    capture serves a position-agnostic patch and a position-specific one.

    `replacements` runs the capture under an intervention, which is how ticket
    08 reads a receiver while a sender carries its corrupt value, and how a
    knockout is checked for leaking into the heads beside it.
    """
    return _traced_forward(model, input_ids, attention_mask,
                           capture=components, replacements=replacements,
                           positions=positions, residual=True)


def replace_forward(model, input_ids, attention_mask, *, replacements,
                    positions=None):
    """The Readout logits of one forward with those sites replaced.

    This is *the* interchange primitive: feed it `capture_forward`'s outputs
    from the corrupt stream and the named senders carry corrupt values while
    everything else runs clean. Knockout replaces one Component, path patching
    replaces one sender and re-runs the receivers; neither re-implements it.

    Each replacement is a `[batch, seq, dim]` tensor (written at every
    position) or a `Replacement` carrying a boolean position mask. Receiver
    keys are replaceable too, which is what makes a path patch a patch rather
    than an ablation: the sender's value reaches one receiver's input and
    nothing else in that receiver's forward changes.
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
            f"{attention_implementation(model)!r}; eager attention did not take")

    selected = weights[:, torch.as_tensor(list(heads), dtype=torch.long)]
    positions = torch.as_tensor(query_positions, dtype=torch.long,
                                device=selected.device)
    if positions.ndim == 1:
        positions = positions.unsqueeze(0).expand(selected.shape[0], -1)
    index = positions.unsqueeze(1).unsqueeze(-1).expand(
        selected.shape[0], selected.shape[1], positions.shape[1],
        selected.shape[-1])
    return torch.gather(selected, 2, index).detach()


# ==============================================================================
# THE FP32 READOUT
# ==============================================================================

def readout_logits(model, residual, *, scale_from=None):
    """Logits from a residual at the Readout, in fp32, through the real norm.

    ADR-0001: *"Ranking metrics are read through an fp32 final norm and
    unembedding."* The reason is ordering, not accuracy — in bfloat16 two
    Components whose contributions differ by less than the spacing of the
    floats around a logit can swap places in a ranking, and a head table is
    read as a ranking. So the final RMSNorm is recomputed here in fp32 with the
    **actual scale at this position** (RMSNorm's scale depends on the vector it
    is normalizing, so a per-Component contribution cannot be normalized with
    some other instance's scale) and the unembedding is an fp32 matmul.

    `residual` is `[..., hidden]` — `Capture.residual[:, -1]` for a whole
    forward, or one Component's contribution for direct logit attribution.
    Returns `[..., vocab]` in float32.

    `scale_from`, when given, is the `[..., hidden]` residual whose RMS sets
    the norm's scale instead of `residual`'s own. Direct logit attribution
    passes the full residual at the Readout here and one Component's
    contribution as `residual`, so every contribution is normalized with the
    same scale and the contributions sum to the readout of the full residual.
    """
    import torch

    hf = _hf(model)
    norm = hf.model.norm
    epsilon = getattr(norm, "variance_epsilon", None)
    if epsilon is None:
        epsilon = getattr(norm, "eps", 1e-5)

    with torch.no_grad():
        hidden = residual.detach().float()
        basis = hidden if scale_from is None else scale_from.detach().float()
        scaled = hidden * torch.rsqrt(basis.pow(2).mean(-1, keepdim=True)
                                      + epsilon)
        scaled = scaled * norm.weight.detach().float()
        return scaled @ hf.lm_head.weight.detach().float().T


def o_proj_weight(model, layer: int):
    """`[hidden, num_heads * head_dim]` output-projection weight of one layer.

    Direct logit attribution turns a head's `Capture.outputs` slice (its
    `o_proj` input) into a residual-stream contribution by multiplying with
    the matching `head_dim` columns of this weight. Llama's `o_proj` has no
    bias; that is asserted so a model with one cannot be attributed silently.
    """
    o_proj = _hf(model).model.layers[layer].self_attn.o_proj
    assert getattr(o_proj, "bias", None) is None, (
        "o_proj has a bias; per-head attribution would need to split it")
    return o_proj.weight.detach()


def target_minus_distractor(logits, target, distractor):
    """`logit(Target) - logit(Distractor)` per row, in fp32.

    Which word is the Target flips between the clean and corrupt streams, so a
    caller comparing two streams passes the *clean* stream's ids for both runs;
    otherwise the clean-minus-corrupt gap is a difference of two positive
    numbers rather than the drop every patching metric is normalized by.
    """
    import torch

    rows = torch.arange(logits.shape[0], device=logits.device)
    return logits[rows, target].float() - logits[rows, distractor].float()
