"""A3 Task5a numerical core, without dataset orchestration or scientific selection.

One update covers all matched ids and both designation streams. Callers supply
immutable train chunks and intact targets. Task5b owns provenance admission,
200-update scheduling, validation selection and atomic checkpoint files.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Sequence

import torch
import torch.nn.functional as F
from l0 import HardConcreteGate

GAP_EPSILON = 1e-6


def _gap(value, epsilon=GAP_EPSILON):
    if not isinstance(epsilon, (int, float)) or not GAP_EPSILON <= epsilon < float(
        "inf"
    ):
        raise ValueError("epsilon must be finite and at least the A1 floor")
    value = torch.as_tensor(value).detach()
    if value.numel() != 1 or not torch.isfinite(value).all() or value.item() <= epsilon:
        raise ValueError("G_D_fit must be finite and greater than epsilon")
    return value


def _paired(value, name):
    if (
        value.ndim != 2
        or value.shape[1] != 2
        or not value.shape[0]
        or not torch.isfinite(value).all()
    ):
        raise ValueError(name + " must contain finite [ids,2] paired streams")


def mask_objective(
    d_margin,
    d_base_margin,
    g_d_fit,
    i_margin,
    i_base_margin,
    i_logits,
    i_base_logits,
    removed_prob,
    *,
    constrained=True,
    epsilon=GAP_EPSILON,
):
    """Full-cohort objective; only patched values and removal probabilities differentiate."""
    gap = _gap(g_d_fit, epsilon)
    for name, value in [
        ("D", d_margin),
        ("D baseline", d_base_margin),
        ("I", i_margin),
        ("I baseline", i_base_margin),
    ]:
        _paired(value, name)
    if (
        d_margin.shape != d_base_margin.shape
        or i_margin.shape != i_base_margin.shape
        or d_margin.shape != i_margin.shape
    ):
        raise ValueError("matched D/I rows and streams required")
    if (
        i_logits.ndim != 3
        or i_logits.shape[:2] != i_margin.shape
        or i_logits.shape != i_base_logits.shape
    ):
        raise ValueError("I logits must match paired row/stream targets")
    if not torch.isfinite(i_logits).all() or not torch.isfinite(i_base_logits).all():
        raise ValueError("nonfinite I logits")
    if (
        removed_prob.ndim != 1
        or not removed_prob.numel()
        or not torch.isfinite(removed_prob).all()
    ):
        raise ValueError("candidate-only removed probabilities required")
    # Difference-first FP64 reduction preserves an exact hinge kink across chunks.
    argument = (
        d_margin.double() - d_base_margin.detach().double()
    ).mean() + 0.5 * gap.double()
    suppression = F.relu(argument)
    preservation = F.relu(i_base_margin.detach() - i_margin).mean()
    kl = (
        F.kl_div(
            F.log_softmax(i_logits, -1),
            F.softmax(i_base_logits.detach(), -1),
            reduction="none",
        )
        .sum(-1)
        .mean()
    )
    removal = removed_prob.mean()
    loss = suppression + (4 * preservation + kl if constrained else 0) + 0.01 * removal
    return dict(
        loss=loss,
        suppression=suppression,
        preservation=preservation,
        kl=kl,
        removal=removal,
        suppression_argument=argument,
    )


@dataclass
class MaskChunk:
    """One immutable cohort slice. Every row carries both designation streams.

    token_counts binds matched D/I target positions; payload is callback-owned.
    Native payload tensors are [ids,2,sequence] plus answer ids [ids,2].
    """

    ids: tuple[str, ...]
    baseline_margin: torch.Tensor
    baseline_logits: torch.Tensor | None
    payload: Any
    token_counts: torch.Tensor
    split: str = "train"


@dataclass
class MaskSupport:
    candidates: tuple[tuple[str, int, int], ...]
    gates: dict[str, HardConcreteGate]

    def parameters(self):
        return [gate.log_alpha for gate in self.gates.values()]

    def removed_probability(self):
        return torch.cat(
            [
                1
                - torch.sigmoid(
                    g.log_alpha[g.eligibility] - g.beta * torch.log(-g.gamma / g.zeta)
                )
                for g in self.gates.values()
            ]
        )


def _candidate_gate(model, key):
    kind, layer, index = key
    if layer < 0 or layer >= len(model.model.layers):
        raise ValueError("candidate layer outside native model")
    block = model.model.layers[layer]
    if kind == "head":
        name, gate = f"model.layers.{layer}.attn.head_gates", block.attn.head_gates
    elif kind == "mlp" and index == 0:
        name, gate = f"model.layers.{layer}.mlp_block_gate", block.mlp_block_gate
    else:
        raise ValueError("only query heads and whole MLP blocks are eligible")
    if gate is None or not 0 <= index < gate.log_alpha.numel():
        raise ValueError("candidate gate missing or index out of range")
    return name, gate


def support_for(model):
    candidates = tuple(getattr(model, "_a3_mask_candidates", ()))
    if not candidates:
        raise ValueError("configure A3 candidates first")
    gates = {}
    for key in candidates:
        name, gate = _candidate_gate(model, key)
        gates[name] = gate
    return MaskSupport(candidates, gates)


def configure_candidates(model, candidates: Sequence[tuple[str, int, int]]):
    """Freeze base; enable native eligibility only at frozen head/block support."""
    candidates = tuple(tuple(k) for k in candidates)
    if not candidates or len(set(candidates)) != len(candidates):
        raise ValueError("nonempty unique candidate support required")
    resolved = [_candidate_gate(model, key) for key in candidates]
    model.eval().requires_grad_(False)
    for gate in model.modules():
        if isinstance(gate, HardConcreteGate):
            gate.set_eligibility(torch.zeros_like(gate.log_alpha, dtype=torch.bool))
    for key, (_, gate) in zip(candidates, resolved):
        gate.eligibility[key[2]] = True
    for _, gate in resolved:
        gate.log_alpha.requires_grad_(True)
        gate.train()
        with torch.no_grad():
            gate.log_alpha[gate.eligibility] = torch.logit(
                torch.tensor(0.95, device=gate.log_alpha.device)
            ) + gate.beta * torch.log(-gate.gamma / gate.zeta)
    model._a3_mask_update_spec = None
    model._a3_mask_boundary = True
    model._a3_mask_candidates = candidates
    return support_for(model)


def native_chunk_forward(model, chunk):
    """Run condition-specific neutral donors through the native dual-stream path."""
    p = chunk.payload
    ids, neutral, mask = (
        p[k] for k in ["input_ids", "neutral_input_ids", "attention_mask"]
    )
    if (
        ids.ndim != 3
        or ids.shape[1] != 2
        or ids.shape != neutral.shape
        or ids.shape != mask.shape
    ):
        raise ValueError("native paired clean/neutral shapes must agree")
    n, streams, seq = ids.shape
    if n != len(chunk.ids) or not torch.equal(
        mask.sum(-1).cpu(), chunk.token_counts.cpu()
    ):
        raise ValueError("native token counts disagree")
    # Training numerical path is shared by both D passes, including readout dtype.
    residual = []
    handle = model.model.norm.register_forward_pre_hook(
        lambda module, args: residual.append(args[0])
    )
    try:
        native_logits = model(
            input_ids=ids.reshape(-1, seq),
            corrupted_input_ids=neutral.reshape(-1, seq),
            attention_mask=mask.reshape(-1, seq),
            use_cache=False,
        ).logits
    finally:
        handle.remove()
    positions = (
        torch.arange(seq, device=mask.device)
        .expand(n * streams, seq)
        .masked_fill(~mask.reshape(-1, seq).bool(), -1)
        .max(-1)
        .values
    )
    rows = torch.arange(n * streams, device=native_logits.device)
    from component_analysis.a3_native import differentiable_readout

    logits = differentiable_readout(model, residual[0][rows, positions]).reshape(
        n, streams, -1
    )
    native_logits = native_logits[rows, positions].reshape(n, streams, -1)
    opposite, honest = p["opposite_ids"], p["honest_ids"]
    margin = logits.gather(-1, opposite[..., None]).squeeze(-1) - logits.gather(
        -1, honest[..., None]
    ).squeeze(-1)
    return {"margin": margin, "logits": logits, "native_logits": native_logits}


def rng_state():
    return {
        "cpu": torch.get_rng_state().clone(),
        "cuda": [s.clone() for s in torch.cuda.get_rng_state_all()]
        if torch.cuda.is_available()
        else [],
    }


def restore_rng(state):
    torch.set_rng_state(state["cpu"])
    if state["cuda"]:
        if len(state["cuda"]) != torch.cuda.device_count():
            raise ValueError("CUDA RNG device count changed")
        torch.cuda.set_rng_state_all(state["cuda"])


def _fingerprint(value):
    """Bind payload bytes, not just a caller's source label."""
    h = hashlib.sha256()

    def add(x):
        if isinstance(x, torch.Tensor):
            x = x.detach().cpu().contiguous()
            h.update(str((str(x.dtype), tuple(x.shape))).encode())
            h.update(x.reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(x, dict):
            for k in sorted(x):
                add(str(k))
                add(x[k])
        elif isinstance(x, (list, tuple)):
            h.update(b"[")
            for item in x:
                add(item)
            h.update(b"]")
        elif x is None or isinstance(x, (str, int, float, bool)):
            h.update(json.dumps(x, sort_keys=True).encode() + b"\0")
        else:
            raise ValueError(
                "identity payload must be tensors or JSON-compatible values"
            )

    add(value)
    return h.hexdigest()


def _chunks_identity(ds, ins):
    return _fingerprint(
        [
            [
                {
                    "ids": c.ids,
                    "margin": c.baseline_margin,
                    "logits": c.baseline_logits,
                    "tokens": c.token_counts,
                    "payload": c.payload,
                    "split": c.split,
                }
                for c in chunks
            ]
            for chunks in (ds, ins)
        ]
    )


def _validate_chunks(ds, ins):
    if not ds or not ins:
        raise ValueError("complete D and I cohorts required")

    def validate(chunks):
        ids = []
        for c in chunks:
            if c.split != "train":
                raise ValueError("optimizer core accepts train split only")
            _paired(c.baseline_margin, "baseline")
            if (
                c.baseline_margin.shape[0] != len(c.ids)
                or c.token_counts.shape != c.baseline_margin.shape
            ):
                raise ValueError("row/token count mismatch")
            ids.extend(c.ids)
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate cohort id")
        return ids, torch.cat([c.token_counts.cpu() for c in chunks])

    dids, dtokens = validate(ds)
    iids, itokens = validate(ins)
    if dids != iids:
        raise ValueError("D/I ids/order must match")
    if not torch.equal(dtokens, itokens):
        raise ValueError("matched D/I token counts required")
    for c in ins:
        if (
            c.baseline_logits is None
            or c.baseline_logits.shape[:2] != c.baseline_margin.shape
        ):
            raise ValueError("paired I target logits required")
    return len(dids)


def _base_computation(model):
    """Effective native settings and non-gate tensors, excluding frozen weights.

    Native modules keep runtime norm/attention attributes outside config. Include
    those too; configuration alone cannot authenticate the actual computation.
    This is small for native Llama (principally rotary buffers), so per-callback
    authentication never copies the frozen multi-billion-parameter weight set.
    """

    def setting(value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (torch.dtype, torch.device)):
            return str(value)
        if isinstance(value, (list, tuple)):
            return [setting(v) for v in value]
        if isinstance(value, dict):
            return {str(k): setting(v) for k, v in value.items()}
        if hasattr(value, "to_dict"):
            result = setting(value.to_dict())
            # HF omits its effective attention selector from some to_dicts.
            result["effective_attention_implementation"] = getattr(
                value, "_attn_implementation", None
            )
            return result
        if hasattr(value, "__dataclass_fields__"):
            return setting(vars(value))
        if callable(value):
            return f"{getattr(value,'__module__',type(value).__module__)}.{getattr(value,'__qualname__',type(value).__qualname__)}"
        raise TypeError

    modules, tensors = {}, {}
    gate_prefixes = tuple(
        name + "."
        for name, mod in model.named_modules()
        if isinstance(mod, HardConcreteGate)
    )
    for name, module in model.named_modules():
        if isinstance(module, HardConcreteGate):
            continue
        attributes = {
            "module_type": f"{type(module).__module__}.{type(module).__qualname__}"
        }
        for key, value in vars(module).items():
            if key.startswith("_") and key not in (
                "_attn_implementation",
                "_flash_attn_uses_top_left_mask",
            ):
                continue
            if isinstance(value, torch.Tensor):
                tensors["attribute:" + name + "." + key] = value
            else:
                try:
                    attributes[key] = setting(value)
                except TypeError:
                    pass  # registered child modules/parameters are captured separately
        modules[name] = attributes
    for name, value in model.named_buffers():
        if not name.startswith(gate_prefixes):
            tensors["buffer:" + name] = value
    from transformers import __version__ as transformers_version

    runtime = {
        "torch": str(torch.__version__),
        "transformers": transformers_version,
        "devices": sorted({str(p.device) for p in model.parameters()}),
        "default_dtype": str(torch.get_default_dtype()),
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "cuda_matmul_tf32": torch.backends.cuda.matmul.allow_tf32,
        "cudnn_tf32": torch.backends.cudnn.allow_tf32,
    }
    return {"modules": modules, "tensors": tensors, "runtime": runtime}


def _computation_identity(model):
    return _fingerprint(_base_computation(model))


def _versions(model):
    parameters = tuple(
        (name, id(p), p._version) for name, p in model.named_parameters()
    )
    distributions = tuple(
        (name, key, id(value), value._version)
        for name, gate in model.named_modules()
        if isinstance(gate, HardConcreteGate)
        for key, value in gate.named_buffers()
        if value is not None
    )
    modes = tuple((name, module.training) for name, module in model.named_modules())
    return parameters, distributions, modes


def _check_support(model, support):
    expected = {}
    for key in support.candidates:
        name, gate = _candidate_gate(model, key)
        if name not in expected:
            expected[name] = torch.zeros_like(gate.log_alpha, dtype=torch.bool)
        expected[name][key[2]] = True
    for name, gate in model.named_modules():
        if isinstance(gate, HardConcreteGate):
            mask = expected.get(
                name, torch.zeros_like(gate.log_alpha, dtype=torch.bool)
            )
            if gate.eligibility is None or not torch.equal(gate.eligibility, mask):
                raise ValueError("native eligibility differs from candidate support")


def _check_modes(model, support, optimizer):
    _check_support(model, support)
    if not isinstance(optimizer, torch.optim.Adam) or any(
        group["lr"] != 0.01
        or group["weight_decay"] != 0
        or group.get("maximize", False)
        or group["betas"] != (0.9, 0.999)
        or group["eps"] != 1e-8
        or group["amsgrad"]
        for group in optimizer.param_groups
    ):
        raise ValueError("fixed Adam defaults with learning rate 0.01 required")
    allowed = {id(g) for g in support.gates.values()}
    if any(module.training and id(module) not in allowed for module in model.modules()):
        raise ValueError("base model must remain eval; only candidate gates train")
    if any(not g.training for g in support.gates.values()):
        raise ValueError("candidate gates must train during optimizer update")
    params = {id(p) for p in support.parameters()}
    if {id(p) for group in optimizer.param_groups for p in group["params"]} != params:
        raise ValueError("optimizer must own precisely candidate gate tensors")
    if any(p.requires_grad and id(p) not in params for p in model.parameters()):
        raise ValueError("base parameters must be frozen")


def streamed_update(
    model,
    support,
    optimizer,
    d_chunks,
    i_chunks,
    forward: Callable,
    *,
    g_d_fit,
    identity,
    constrained=True,
    epsilon=GAP_EPSILON,
):
    """One exact streamed full-cohort update. No parameters change until the step.

    Return CPU gate/RNG replay diagnostics and full gate-tensor gradients. D
    graphs are freed chunk by chunk. I graphs are also immediately discarded.
    """
    if getattr(model, "_a3_update_in_progress", False):
        raise RuntimeError("nested update is not an optimizer boundary")
    n = _validate_chunks(d_chunks, i_chunks)
    gap = _gap(g_d_fit, epsilon)
    _check_modes(model, support, optimizer)
    specification = {
        "identity": _fingerprint(identity),
        "chunks": _chunks_identity(d_chunks, i_chunks),
        "gap": gap.item(),
        "epsilon": epsilon,
        "constrained": bool(constrained),
        "computation": _computation_identity(model),
    }
    previous = getattr(model, "_a3_mask_update_spec", None)
    if previous is not None and previous != specification:
        raise ValueError("frozen update configuration differs")
    if not getattr(model, "_a3_mask_boundary", True):
        raise RuntimeError("failed update requires restore to a completed boundary")
    versions = _versions(model)

    def unchanged():
        if versions != _versions(model):
            raise RuntimeError("parameter mutation during streamed update")
        if specification["chunks"] != _chunks_identity(d_chunks, i_chunks):
            raise RuntimeError("cohort mutation during streamed update")
        if specification["computation"] != _computation_identity(model):
            raise RuntimeError("base computation mutation during streamed update")
        if (
            specification["identity"] != _fingerprint(identity)
            or specification["gap"] != gap.item()
        ):
            raise RuntimeError("source identity/gap mutation during streamed update")

    records = []
    sampled = {}
    handles = [
        g.register_forward_hook(
            lambda module, args, out, name=name: sampled.setdefault(name, []).append(
                out.detach().cpu().clone()
            )
        )
        for name, g in support.gates.items()
    ]
    model._a3_update_in_progress = True
    model._a3_mask_boundary = False
    try:
        total = None
        with torch.no_grad():
            for c in d_chunks:
                unchanged()
                sampled.clear()
                state = rng_state()  # immediately before each numerical chunk
                out = forward(model, c)
                unchanged()
                if sampled.keys() != support.gates.keys() or any(
                    not v for v in sampled.values()
                ):
                    raise RuntimeError(
                        "candidate gates were not sampled by the callback"
                    )
                _paired(out["margin"], "patched D")
                if out["margin"].shape != c.baseline_margin.shape:
                    raise ValueError("patched D row shape differs")
                term = (
                    out["margin"].double() - c.baseline_margin.detach().double()
                ).sum()
                total = term if total is None else total + term
                records.append(
                    {
                        "rng": state,
                        "margin": out["margin"].detach().cpu().clone(),
                        "gates": copy.deepcopy(sampled),
                        "after_rng": rng_state(),
                    }
                )
        post_d = rng_state()
        argument = total / (2 * n) + 0.5 * gap.double()
        active = bool(argument.item() > 0)
        optimizer.zero_grad(set_to_none=True)
        for c, record in zip(d_chunks, records):
            unchanged()
            restore_rng(record["rng"])
            sampled.clear()
            out = forward(model, c)
            unchanged()
            after_rng = rng_state()
            expected_rng = record["after_rng"]
            if (
                not torch.equal(after_rng["cpu"], expected_rng["cpu"])
                or len(after_rng["cuda"]) != len(expected_rng["cuda"])
                or any(
                    not torch.equal(a, b)
                    for a, b in zip(after_rng["cuda"], expected_rng["cuda"])
                )
            ):
                raise RuntimeError("D replay RNG numerical path differs")
            if not torch.equal(out["margin"].detach().cpu(), record["margin"]):
                raise RuntimeError("D replay margins differ")
            if sampled.keys() != record["gates"].keys() or any(
                len(sampled[k]) != len(record["gates"][k])
                or any(
                    not torch.equal(a, b)
                    for a, b in zip(sampled[k], record["gates"][k])
                )
                for k in sampled
            ):
                raise RuntimeError("D replay sampled gates differ")
            (out["margin"].mean() * (len(c.ids) / n) * float(active)).backward()
            del out
        restore_rng(post_d)
        i_records = []
        preservation, kl = 0.0, 0.0
        for c in i_chunks:
            unchanged()
            sampled.clear()
            state = rng_state()
            out = forward(model, c)
            unchanged()
            _paired(out["margin"], "patched I")
            if (
                out["margin"].shape != c.baseline_margin.shape
                or out["logits"].shape != c.baseline_logits.shape
            ):
                raise ValueError("patched I target shapes differ")
            weight = len(c.ids) / n
            hinge = F.relu(c.baseline_margin.detach() - out["margin"]).mean() * weight
            divergence = (
                F.kl_div(
                    F.log_softmax(out["logits"], -1),
                    F.softmax(c.baseline_logits.detach(), -1),
                    reduction="none",
                )
                .sum(-1)
                .mean()
                * weight
            )
            ((4 * hinge + divergence) * float(constrained)).backward()
            preservation += hinge.detach().item()
            kl += divergence.detach().item()
            i_records.append({"rng": state, "gates": copy.deepcopy(sampled)})
            del out, hinge, divergence
        removal = support.removed_probability().mean()
        (0.01 * removal).backward()
        unchanged()
        gradients = {
            name: g.log_alpha.grad.detach().cpu().clone()
            for name, g in support.gates.items()
        }
        if any(not torch.isfinite(v).all() for v in gradients.values()):
            raise RuntimeError("nonfinite gate gradient")
        optimizer.step()
        model._a3_mask_update_spec = specification
        model._a3_mask_boundary = True
        return {
            "suppression_argument": argument.item(),
            "suppression_active": active,
            "suppression": max(0.0, argument.item()),
            "preservation": preservation,
            "kl": kl,
            "removal": removal.detach().item(),
            "gradients": gradients,
            "d_replay": records,
            "i_draws": i_records,
            "identity": copy.deepcopy(identity),
        }
    finally:
        model._a3_update_in_progress = False
        for handle in handles:
            handle.remove()


def export_removal_mask(model, *, provenance):
    """Exact complement of native deterministic forward, preserving gate modes."""
    support = support_for(model)
    _check_support(model, support)
    modes = {name: g.training for name, g in support.gates.items()}
    values = {}
    try:
        with torch.no_grad():
            for name, gate in support.gates.items():
                gate.eval()
                values[name] = gate().cpu()
        keep = [
            int(values[_candidate_gate(model, k)[0]][k[2]]) for k in support.candidates
        ]
        return {
            "schema": "a3-removal-mask-v1",
            "candidates": [list(k) for k in support.candidates],
            "keep": keep,
            "removed": [list(k) for k, v in zip(support.candidates, keep) if not v],
            "provenance": copy.deepcopy(provenance),
        }
    finally:
        for name, gate in support.gates.items():
            gate.train(modes[name])


def _base_identity(model):
    return _fingerprint(
        {
            "parameters": {
                name: p
                for name, p in model.named_parameters()
                if "log_alpha" not in name
            },
            "computation": _base_computation(model),
        }
    )


def make_checkpoint(model, support, optimizer, d_chunks, i_chunks, *, identity, update):
    """Snapshot at completed-update boundary; Task5b writes this atomically."""
    if getattr(model, "_a3_update_in_progress", False) or not getattr(
        model, "_a3_mask_boundary", True
    ):
        raise RuntimeError("checkpoint requires completed optimizer boundary")
    _validate_chunks(d_chunks, i_chunks)
    _check_support(model, support)
    previous = getattr(model, "_a3_mask_update_spec", None)
    if previous is not None and (
        previous["chunks"] != _chunks_identity(d_chunks, i_chunks)
        or previous["computation"] != _computation_identity(model)
        or previous["identity"] != _fingerprint(identity)
    ):
        raise ValueError("completed checkpoint boundary identity differs")
    if not isinstance(update, int) or update < 0:
        raise ValueError("nonnegative completed update count required")
    return copy.deepcopy(
        {
            "schema": "a3-mask-checkpoint-v1",
            "boundary": "after_optimizer_step",
            "update": update,
            "identity": identity,
            "chunks": _chunks_identity(d_chunks, i_chunks),
            "update_spec": getattr(model, "_a3_mask_update_spec", None),
            "support": support.candidates,
            "base": _base_identity(model),
            "optimizer": optimizer.state_dict(),
            "gates": {
                name: gate.state_dict()
                for name, gate in model.named_modules()
                if isinstance(gate, HardConcreteGate)
            },
            "rng": rng_state(),
        }
    )


def restore_checkpoint(
    state, model, support, optimizer, d_chunks, i_chunks, *, identity
):
    """Reject altered sources, support, chunk boundaries/order, or intact targets."""
    if getattr(model, "_a3_update_in_progress", False):
        raise RuntimeError("restore requires completed optimizer boundary")
    _validate_chunks(d_chunks, i_chunks)
    _check_support(model, support)
    if (
        state["schema"] != "a3-mask-checkpoint-v1"
        or state["boundary"] != "after_optimizer_step"
        or state["identity"] != identity
        or state["support"] != support.candidates
        or state["chunks"] != _chunks_identity(d_chunks, i_chunks)
        or state["base"] != _base_identity(model)
    ):
        raise ValueError("checkpoint source/support/chunk identity differs")
    gates = {
        name: g for name, g in model.named_modules() if isinstance(g, HardConcreteGate)
    }
    if gates.keys() != state["gates"].keys():
        raise ValueError("checkpoint native gate support differs")
    for name, gate in gates.items():
        if not torch.equal(
            gate.eligibility.cpu(), state["gates"][name]["eligibility"].cpu()
        ):
            raise ValueError("checkpoint eligibility differs")
    for name, gate in gates.items():
        gate.load_state_dict(state["gates"][name], strict=True)
    optimizer.load_state_dict(copy.deepcopy(state["optimizer"]))
    model._a3_mask_update_spec = copy.deepcopy(state["update_spec"])
    model._a3_mask_boundary = True
    restore_rng(state["rng"])
    return state["update"]
