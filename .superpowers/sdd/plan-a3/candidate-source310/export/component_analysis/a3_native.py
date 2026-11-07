"""Prospective A3 native Llama branch adapter (no edge selection or estimator).

Caller supplies a separately loaded, revision/dtype/backend-pinned HF Llama in
fully frozen eval mode. This module never loads weights or changes model state.
Only receiver incoming-residual leaves enter autograd. Each invocation owns one
batch graph; consume its VJP and release it before forwarding the next batch.

Sites use hooks.py tuple keys; k/v indices name KV groups, never query heads.
``outputs`` are detached native boundaries (head = pre-o_proj slice, mlp_in =
post-norm input); ``incoming`` are detached pre-norm residuals. ``additive``
projects head slices into residual width. ``neuron_hidden`` captures down_proj
input. A ResidualPatch supplies a *fixed pre-norm residual*, not a live delta:
edge orchestration must construct it from intact caches. Separate branches may
use different residuals; unselected projection slices stay live. No recursively
changed sender is consulted here. Captures do not retain extra graphs.
"""
from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn.functional as F


@dataclass(frozen=True)
class ResidualPatch:
    """Full [batch, seq, hidden] incoming residual; optional boolean position mask.

    Padding is always excluded. With grad=True this value is detached into an
    independent leaf returned in ``leaves``; differentiate that leaf, not value.
    """
    value: torch.Tensor
    positions: Optional[torch.Tensor] = None


def receiver_sites(model):
    """Canonical deduplicated receivers, in execution order."""
    cfg = model.config
    return [site for layer in range(cfg.num_hidden_layers)
            for site in ([("q", layer, h) for h in range(cfg.num_attention_heads)]
                         + [(kind, layer, g) for kind in ("k", "v")
                            for g in range(cfg.num_key_value_heads)]
                         + [("mlp_in", layer, 0)])] + [("readout", 0, 0)]


def causally_upstream(sender, receiver, source_position, receiver_position):
    """Direct additive residual paths require same-token endpoints and run order.

    Attention later transports K/V information to other query positions; that is
    not a cross-token residual addition and must be enumerated by edge geometry.
    """
    sk, sl, _ = sender
    rk, rl, _ = receiver
    if sk not in ("embed", "head", "mlp") or rk not in ("q", "k", "v", "mlp_in", "readout"):
        raise ValueError("expected additive sender and receiver sites")
    if source_position != receiver_position:
        return False
    return (sk == "embed" or rk == "readout" or sl < rl
            or (sl == rl and sk == "head" and rk == "mlp_in"))


def _native_norm(norm, residual):
    """Llama RMSNorm value/Jacobian without re-entering installed module hooks."""
    hidden = residual.float()
    epsilon = getattr(norm, "variance_epsilon", getattr(norm, "eps", 1e-5))
    scaled = hidden * torch.rsqrt(hidden.square().mean(-1, keepdim=True) + epsilon)
    return norm.weight * scaled.to(residual.dtype)


def differentiable_readout(model, residual):
    """FP32 RMSNorm and unembedding, with full residual Jacobian."""
    norm = model.model.norm
    hidden = residual.float()
    epsilon = getattr(norm, "variance_epsilon", getattr(norm, "eps", 1e-5))
    scaled = hidden * torch.rsqrt(hidden.square().mean(-1, keepdim=True) + epsilon)
    return F.linear(scaled * norm.weight.detach().float(),
                    model.lm_head.weight.detach().float())


def native_forward(model, batch, *, capture_sites, patches=None, grad=False):
    """One scoped native HF forward, returning native and FP32 readout logits.

    Batch is a mapping or object with input_ids/attention_mask; optional readout
    contains one unpadded index per row. No cache is created. ``grad=True``
    creates incoming-residual leaves for every requested/patched receiver, and
    only those branches are reconstructed through their real norm/projection.
    ``patches`` maps receiver tuples to ResidualPatch. Model parameters must be
    frozen before entry, so backward after hook cleanup cannot touch them.
    """
    if any(module.training for module in model.modules()):
        raise ValueError("native adapter requires eval mode")
    if any(p.requires_grad for p in model.parameters()):
        raise ValueError("native adapter requires all base parameters frozen")
    if model.config.model_type != "llama":
        raise ValueError("native adapter supports HF Llama only")
    get = batch.get if isinstance(batch, dict) else lambda k, d=None: getattr(batch, k, d)
    ids, mask = get("input_ids"), get("attention_mask")
    if ids.ndim != 2 or mask.shape != ids.shape or not ((mask == 0) | (mask == 1)).all():
        raise ValueError("input_ids and binary attention_mask must be [batch, seq]")
    valid = mask.bool()
    if not valid.any(-1).all():
        raise ValueError("every row requires an unpadded token")
    positions = get("readout")
    if positions is None:
        positions = torch.arange(ids.shape[1], device=ids.device).expand_as(ids).masked_fill(~valid, -1).max(-1).values
    positions = torch.as_tensor(positions, device=ids.device).long()
    if positions.shape != (ids.shape[0],) or (positions < 0).any() or (positions >= ids.shape[1]).any():
        raise ValueError("readout must give one valid position per row")
    rows = torch.arange(ids.shape[0], device=ids.device)
    if not valid[rows, positions].all():
        raise ValueError("readout cannot select padding")
    requested = set(capture_sites)
    patches = {} if patches is None else dict(patches)
    receivers = set(receiver_sites(model))
    cfg = model.config
    allowed = receivers | {("embed", 0, 0)}
    for layer in range(cfg.num_hidden_layers):
        allowed |= {("head", layer, h) for h in range(cfg.num_attention_heads)}
        allowed |= {(kind, layer, 0) for kind in ("mlp", "neuron_hidden")}
    if not requested <= allowed or not set(patches) <= receivers:
        raise ValueError("unknown site or nonreceiver patch; K/V indices are KV groups")
    if any(not isinstance(p, ResidualPatch) for p in patches.values()):
        raise TypeError("patches must contain ResidualPatch values")
    active = (requested & receivers if grad else set()) | set(patches)
    outputs, incoming, additive, leaves, handles = {}, {}, {}, {}, []
    current = {}
    readout_residual = None

    def capture(key, value):
        if key in requested:
            outputs[key] = value.detach().clone()

    def incoming_capture(keys, value):
        for key in keys:
            if key in requested or key in active:
                incoming[key] = value.detach().clone()

    def residual_for(key, live):
        patch = patches.get(key)
        value = live.detach() if patch is None else patch.value
        if value.shape != live.shape or value.device != live.device or value.dtype != live.dtype:
            raise ValueError("patch residual must match native shape, device and dtype")
        value = value.detach().clone().requires_grad_(grad)
        if grad:
            leaves[key] = value
        selected = valid
        if patch is not None and patch.positions is not None:
            pmask = torch.as_tensor(patch.positions, device=live.device)
            if pmask.dtype != torch.bool or pmask.shape not in (ids.shape, ids.shape[1:]):
                raise ValueError("positions must be a boolean [seq] or [batch, seq] mask")
            selected = selected & pmask
        return torch.where(selected[..., None], value, live)

    def pre(module, fn):
        handles.append(module.register_forward_pre_hook(fn))

    def post(module, fn):
        handles.append(module.register_forward_hook(fn))

    try:
        with torch.set_grad_enabled(grad):
            post(model.model.embed_tokens, lambda m, a, out: capture(("embed", 0, 0), out))
            for layer_index, layer in enumerate(model.model.layers):
                qkv = [(kind, layer_index, i) for kind, count in
                       (("q", cfg.num_attention_heads), ("k", cfg.num_key_value_heads), ("v", cfg.num_key_value_heads))
                       for i in range(count)]

                def attention_input(m, args, li=layer_index, keys=qkv):
                    current[("attention", li)] = args[0]
                    incoming_capture(keys, args[0])
                pre(layer.input_layernorm, attention_input)
                for kind in ("q", "k", "v"):
                    projection = getattr(layer.self_attn, kind + "_proj")
                    dim = getattr(layer.self_attn, "head_dim", cfg.hidden_size // cfg.num_attention_heads)
                    count = cfg.num_attention_heads if kind == "q" else cfg.num_key_value_heads

                    def project(m, args, out, k=kind, li=layer_index, n=count, d=dim, norm=layer.input_layernorm):
                        live = current[("attention", li)]
                        slices = []
                        for i in range(n):
                            key = (k, li, i)
                            value = out[..., i*d:(i+1)*d]
                            if key in active:
                                reconstructed = F.linear(
                                    _native_norm(norm, residual_for(key, live)), m.weight, m.bias)
                                value = reconstructed[..., i*d:(i+1)*d]
                            slices.append(value)
                            capture(key, value)
                        return torch.cat(slices, dim=-1)
                    post(projection, project)

                def head_capture(m, args, li=layer_index, d=dim):
                    for h in range(cfg.num_attention_heads):
                        key = ("head", li, h)
                        value = args[0][..., h*d:(h+1)*d]
                        capture(key, value)
                        if key in requested:
                            if m.bias is not None:
                                raise ValueError("head additive attribution requires bias-free o_proj")
                            additive[key] = F.linear(value.detach(), m.weight[:, h*d:(h+1)*d]).detach().clone()
                pre(layer.self_attn.o_proj, head_capture)

                def mlp_input(m, args, li=layer_index):
                    current[("mlp", li)] = args[0]
                    incoming_capture([("mlp_in", li, 0)], args[0])
                pre(layer.post_attention_layernorm, mlp_input)

                def mlp_norm(m, args, out, li=layer_index):
                    key = ("mlp_in", li, 0)
                    if key in active:
                        out = _native_norm(m, residual_for(key, current[("mlp", li)]))
                    capture(key, out)
                    return out
                post(layer.post_attention_layernorm, mlp_norm)

                def mlp_output(m, args, out, li=layer_index):
                    key = ("mlp", li, 0)
                    capture(key, out)
                    if key in requested:
                        additive[key] = out.detach().clone()
                post(layer.mlp, mlp_output)
                pre(layer.mlp.down_proj, lambda m, a, li=layer_index: capture(("neuron_hidden", li, 0), a[0]))

            def readout_input(m, args):
                nonlocal readout_residual
                key = ("readout", 0, 0)
                incoming_capture([key], args[0])
                readout_residual = residual_for(key, args[0]) if key in active else args[0]
                capture(key, readout_residual)
                return (readout_residual,) + args[1:]
            pre(model.model.norm, readout_input)
            result = model(input_ids=ids, attention_mask=mask, use_cache=False)
            fp32 = differentiable_readout(model, readout_residual[rows, positions])
            return {"logits": result.logits[rows, positions].detach(), "fp32_logits": fp32,
                    "outputs": outputs, "incoming": incoming, "additive": additive,
                    "leaves": leaves, "readout": positions.detach()}
    finally:
        for handle in reversed(handles):
            handle.remove()
