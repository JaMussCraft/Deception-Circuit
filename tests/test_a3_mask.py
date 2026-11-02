"""A3 Task5a: synthetic CPU objective and exact native gate replay contracts."""

import copy

import pytest
import torch
from transformers import LlamaConfig
from models.llama_node import (
    PrunableLlamaForCausalLM,
    PruningConfig,
    apply_pruning_wrappers,
)
from l0 import HardConcreteGate
from component_analysis import a3_mask as m


def tiny():
    torch.manual_seed(91)
    config = LlamaConfig(
        hidden_size=16,
        intermediate_size=24,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        vocab_size=23,
        attn_implementation="eager",
        attention_dropout=0.2,
    )
    model = PrunableLlamaForCausalLM(config)
    apply_pruning_wrappers(model, PruningConfig())
    support = m.configure_candidates(
        model, [("head", 0, 0), ("mlp", 0, 0), ("head", 1, 1)]
    )
    return model, support


def chunks(kind, sizes=(2, 1)):
    result = []
    start = 0
    for n in sizes:
        tokens = (
            torch.arange(n * 2 * 4).reshape(n, 2, 4) + start + (kind == "I") * 3
        ) % 22 + 1
        result.append(
            m.MaskChunk(
                tuple(str(i) for i in range(start, start + n)),
                torch.ones(n, 2),
                torch.zeros(n, 2, 23),
                {
                    "input_ids": tokens,
                    "neutral_input_ids": tokens.roll(1, -1),
                    "attention_mask": torch.ones_like(tokens),
                    "opposite_ids": torch.full((n, 2), 7),
                    "honest_ids": torch.full((n, 2), 3),
                },
                torch.full((n, 2), 4),
            )
        )
        start += n
    return result


def test_objective_thresholds_targets_and_denominator():
    d = torch.tensor([[0.5, 0.5]], requires_grad=True)
    base = torch.ones(1, 2, requires_grad=True)
    gap = torch.tensor(2.0, requires_grad=True)
    ib = torch.ones(1, 2, requires_grad=True)
    il = torch.tensor([[[1.0, 0.0], [0.0, 1.0]]], requires_grad=True)
    bl = torch.zeros_like(il, requires_grad=True)
    r = torch.tensor([0.2], requires_grad=True)
    im = torch.full((1, 2), 0.75, requires_grad=True)
    out = m.mask_objective(d, base, gap, im, ib, il, bl, r)
    assert out["suppression"].item() == 0.5
    assert out["preservation"].item() == 0.25
    torch.testing.assert_close(
        out["loss"], out["suppression"] + 4 * out["preservation"] + out["kl"] + 0.002
    )
    out["loss"].backward()
    assert (
        base.grad is None and gap.grad is None and bl.grad is None and ib.grad is None
    )
    assert (
        m.mask_objective(d.detach() * 0, base, gap, ib, ib, il, bl, r)["suppression"]
        == 0
    )
    assert (
        m.mask_objective(d.detach() * 0 + 2, base * 3, gap, ib, ib, il, bl, r)[
            "suppression"
        ]
        == 0
    )
    for bad in [0.0, 1e-10, -1.0, float("nan"), float("inf")]:
        with pytest.raises(ValueError):
            m.mask_objective(d, base, torch.tensor(bad), ib, ib, il, bl, r)
    with pytest.raises(ValueError):
        m.mask_objective(d[:, :1], base, gap, ib, ib, il, bl, r)


def test_candidate_only_trainability_initialization_and_native_export():
    model, support = tiny()
    assert not model.training
    for name, gate in model.named_modules():
        if isinstance(gate, HardConcreteGate):
            expected = gate.eligibility
            assert expected is not None
            assert gate.training == bool(expected.any())
            p = torch.sigmoid(
                gate.log_alpha - gate.beta * torch.log(-gate.gamma / gate.zeta)
            )
            torch.testing.assert_close(p[expected], torch.full_like(p[expected], 0.95))
            with torch.no_grad():
                gate.log_alpha[~expected] = -1e6
            assert torch.all(gate()[~expected] == 1)
    assert sum(p.numel() for p in support.parameters()) == 5
    assert all(
        not p.requires_grad for n, p in model.named_parameters() if "log_alpha" not in n
    )
    assert support.removed_probability().numel() == 3
    with torch.no_grad():
        for gate in support.gates.values():
            gate.log_alpha[gate.eligibility] = -0.5  # p-open > .5, native eval closed
    out = m.export_removal_mask(model, provenance={"source": "tiny"})
    assert len(out["removed"]) == 3 and out["keep"] == [0, 0, 0]
    with torch.no_grad():
        for gate in support.gates.values():
            gate.log_alpha[gate.eligibility] = 0.0  # strict > at native eval tie
    assert m.export_removal_mask(model, provenance={})["keep"] == [0, 0, 0]
    assert any(g.training for g in support.gates.values())  # export restores mode


def retained(model, support, opt, ds, ins, gap, constrained):
    """Independent retained-graph oracle; identical initial RNG, one draw/chunk."""
    opt.zero_grad(set_to_none=True)
    douts = [m.native_chunk_forward(model, c) for c in ds]
    iouts = [m.native_chunk_forward(model, c) for c in ins]
    out = m.mask_objective(
        torch.cat([o["margin"] for o in douts]),
        torch.cat([c.baseline_margin for c in ds]),
        gap,
        torch.cat([o["margin"] for o in iouts]),
        torch.cat([c.baseline_margin for c in ins]),
        torch.cat([o["logits"] for o in iouts]),
        torch.cat([c.baseline_logits for c in ins]),
        support.removed_probability(),
        constrained=constrained,
    )
    out["loss"].backward()
    grads = {k: g.log_alpha.grad.clone() for k, g in support.gates.items()}
    opt.step()
    return grads, out


@pytest.mark.parametrize("regime", ["active", "inactive", "kink"])
@pytest.mark.parametrize("constrained", [True, False])
def test_streamed_matches_retained_every_gradient_adam_and_rng(regime, constrained):
    model, support = tiny()
    # Keep stochastic gates in their differentiable range.
    with torch.no_grad():
        for gate in support.gates.values():
            gate.log_alpha.zero_()
    ref = copy.deepcopy(model)
    rs = m.support_for(ref)
    opt = torch.optim.Adam(support.parameters(), lr=0.01)
    ropt = torch.optim.Adam(rs.parameters(), lr=0.01)
    ds, ins = chunks("D"), chunks("I")
    gap = torch.tensor(2.0)
    rng = torch.get_rng_state()
    with torch.no_grad():
        initial = [m.native_chunk_forward(model, c)["margin"].double() for c in ds]
    # Opposing chunk hinges catch an incorrect independent-minibatch hinge.
    offsets = {"active": [0.0, 2.0], "inactive": [0.0, 6.0], "kink": [0.0, 3.0]}[regime]
    for c, margin, offset in zip(ds, initial, offsets):
        c.baseline_margin = margin + offset
    torch.set_rng_state(rng)
    expected_grads, expected = retained(ref, rs, ropt, ds, ins, gap, constrained)
    end_rng = torch.get_rng_state()
    torch.set_rng_state(rng)
    actual = m.streamed_update(
        model,
        support,
        opt,
        ds,
        ins,
        m.native_chunk_forward,
        g_d_fit=gap,
        identity={"source": "tiny"},
        constrained=constrained,
    )
    assert actual["suppression_active"] == (regime == "active")
    assert torch.equal(torch.get_rng_state(), end_rng)
    for key, gate in support.gates.items():
        torch.testing.assert_close(
            actual["gradients"][key], expected_grads[key], atol=1e-7, rtol=2e-5
        )
        torch.testing.assert_close(
            gate.log_alpha, rs.gates[key].log_alpha, atol=1e-7, rtol=2e-5
        )
        for state in ["step", "exp_avg", "exp_avg_sq"]:
            torch.testing.assert_close(
                opt.state[gate.log_alpha][state],
                ropt.state[rs.gates[key].log_alpha][state],
                atol=1e-8,
                rtol=2e-5,
            )
    assert any(g.abs().sum() > 0 for g in actual["gradients"].values())
    for key, gate in support.gates.items():
        assert torch.all(actual["gradients"][key][~gate.eligibility] == 0)


def test_resume_rejects_identity_chunking_and_reproduces_next_update():
    model, support = tiny()
    ds, ins = chunks("D"), chunks("I")
    opt = torch.optim.Adam(support.parameters(), lr=0.01)
    kw = dict(g_d_fit=torch.tensor(2.0), identity={"source": "frozen"})
    m.streamed_update(model, support, opt, ds, ins, m.native_chunk_forward, **kw)
    saved = m.make_checkpoint(
        model, support, opt, ds, ins, identity=kw["identity"], update=1
    )
    m.streamed_update(model, support, opt, ds, ins, m.native_chunk_forward, **kw)
    expected = [p.detach().clone() for p in support.parameters()]
    end = torch.get_rng_state()
    other, os = tiny()
    oo = torch.optim.Adam(os.parameters(), lr=0.01)
    with pytest.raises(ValueError):
        m.restore_checkpoint(
            saved, other, os, oo, ds, ins, identity={"source": "changed"}
        )
    with pytest.raises(ValueError):
        m.restore_checkpoint(
            saved, other, os, oo, chunks("D", (1, 2)), ins, identity=kw["identity"]
        )
    # Base source weights must actually match, not merely a caller label.
    with torch.no_grad():
        other.lm_head.weight.add_(0.01)
    with pytest.raises(ValueError):
        m.restore_checkpoint(saved, other, os, oo, ds, ins, identity=kw["identity"])
    other.load_state_dict(model.state_dict())
    assert (
        m.restore_checkpoint(saved, other, os, oo, ds, ins, identity=kw["identity"])
        == 1
    )
    m.streamed_update(other, os, oo, ds, ins, m.native_chunk_forward, **kw)
    for p, q in zip(expected, os.parameters()):
        torch.testing.assert_close(p, q, atol=0, rtol=0)
    assert torch.equal(end, torch.get_rng_state())


def test_replay_rejects_parameter_mutation_and_stream_contract():
    model, support = tiny()
    ds, ins = chunks("D"), chunks("I")
    opt = torch.optim.Adam(support.parameters(), lr=0.01)
    calls = [0]

    def mutate(model, chunk):
        calls[0] += 1
        if calls[0] == 3:
            with torch.no_grad():
                next(iter(support.gates.values())).log_alpha.add_(1)
        return m.native_chunk_forward(model, chunk)

    with pytest.raises(RuntimeError, match="parameter"):
        m.streamed_update(
            model, support, opt, ds, ins, mutate, g_d_fit=torch.tensor(2.0), identity={}
        )
    ins[0].token_counts[0, 0] = 3
    with pytest.raises(ValueError, match="token"):
        m.streamed_update(
            model,
            support,
            opt,
            ds,
            ins,
            m.native_chunk_forward,
            g_d_fit=torch.tensor(2.0),
            identity={},
        )


def native_copy(model):
    from transformers import LlamaForCausalLM

    native = LlamaForCausalLM(model.config).eval().requires_grad_(False)
    for name in ["embed_tokens", "norm"]:
        getattr(native.model, name).load_state_dict(
            getattr(model.model, name).state_dict()
        )
    native.lm_head.load_state_dict(model.lm_head.state_dict())
    for src, dst in zip(model.model.layers, native.model.layers):
        dst.self_attn.load_state_dict(src.attn.original_attention.state_dict())
        dst.mlp.load_state_dict(src.mlp.original_mlp.state_dict())
        dst.input_layernorm.load_state_dict(src.input_layernorm.state_dict())
        dst.post_attention_layernorm.load_state_dict(
            src.post_attention_layernorm.state_dict()
        )
    return native


def hook_removal(native, chunk, removed):
    """Independent eval adapter: fixed same-condition donor head/MLP captures."""
    p = chunk.payload
    n, _, seq = p["input_ids"].shape
    donors, handles = {}, []
    try:
        for kind, layer, index in removed:
            key = (kind, layer, index)
            if kind == "head":

                def capture(module, args, key=key, index=index):
                    donors[key] = (
                        args[0][..., index * 8 : (index + 1) * 8].detach().clone()
                    )

                handles.append(
                    native.model.layers[
                        layer
                    ].self_attn.o_proj.register_forward_pre_hook(capture)
                )
            else:

                def capture(module, args, out, key=key):
                    donors[key] = out.detach().clone()

                handles.append(
                    native.model.layers[layer].mlp.register_forward_hook(capture)
                )
        native(
            input_ids=p["neutral_input_ids"].reshape(-1, seq),
            attention_mask=p["attention_mask"].reshape(-1, seq),
            use_cache=False,
        )
    finally:
        for h in handles:
            h.remove()
    handles = []
    try:
        for kind, layer, index in removed:
            key = (kind, layer, index)
            if kind == "head":

                def patch(module, args, key=key, index=index):
                    value = args[0].clone()
                    value[..., index * 8 : (index + 1) * 8] = donors[key]
                    return (value,)

                handles.append(
                    native.model.layers[
                        layer
                    ].self_attn.o_proj.register_forward_pre_hook(patch)
                )
            else:

                def patch(module, args, out, key=key):
                    return donors[key]

                handles.append(
                    native.model.layers[layer].mlp.register_forward_hook(patch)
                )
        out = native(
            input_ids=p["input_ids"].reshape(-1, seq),
            attention_mask=p["attention_mask"].reshape(-1, seq),
            use_cache=False,
        ).logits
        return out[:, -1].float().reshape(n, 2, -1)
    finally:
        for h in handles:
            h.remove()


@pytest.mark.parametrize("kind", ["D", "I"])
@pytest.mark.parametrize(
    "removed",
    [
        [],
        [("head", 0, 0)],
        [("mlp", 0, 0)],
        [("head", 0, 0), ("mlp", 0, 0), ("head", 1, 1)],
    ],
)
def test_actual_eval_export_matches_native_hook_condition_neutral_donors(kind, removed):
    model, support = tiny()
    native = native_copy(model)
    with torch.no_grad():
        for key in support.candidates:
            _, gate = m._candidate_gate(model, key)
            gate.log_alpha[key[2]] = -100 if key in removed else 100
    exported = m.export_removal_mask(model, provenance={"source": "synthetic"})
    assert sorted(map(tuple, exported["removed"])) == sorted(removed)
    model.eval()
    chunk = chunks(kind)[0]
    with torch.no_grad():
        dual = m.native_chunk_forward(model, chunk)["logits"]
        hooked = hook_removal(native, chunk, exported["removed"])
    torch.testing.assert_close(dual, hooked, atol=1e-7, rtol=1e-6)
    if removed:
        wrong = chunks("I" if kind == "D" else "D")[0]
        wrong.payload["input_ids"] = chunk.payload["input_ids"]
        with torch.no_grad():
            wrong_donor = hook_removal(native, wrong, exported["removed"])
        assert not torch.allclose(hooked, wrong_donor, atol=1e-7, rtol=1e-6)


def test_nonzero_native_gate_gradients_without_regularizer_and_frozen_source():
    model, support = tiny()
    with torch.no_grad():
        for gate in support.gates.values():
            gate.log_alpha.zero_()
    before = {
        name: p.detach().clone()
        for name, p in model.named_parameters()
        if "log_alpha" not in name
    }
    # Native masked margins themselves carry gradients; the sparsity term is absent.
    out = m.native_chunk_forward(model, chunks("D")[0])
    gradients = torch.autograd.grad(out["margin"].sum(), support.parameters())
    assert sum(g.abs().sum() for g in gradients) > 1e-6
    for name, p in model.named_parameters():
        if name in before:
            assert (
                not p.requires_grad and p.grad is None and torch.equal(before[name], p)
            )


def test_train_split_id_and_candidate_rejections():
    model, support = tiny()
    ds, ins = chunks("D"), chunks("I")
    ds[0].split = "test"
    opt = torch.optim.Adam(support.parameters(), lr=0.01)
    with pytest.raises(ValueError, match="train split"):
        m.streamed_update(
            model,
            support,
            opt,
            ds,
            ins,
            m.native_chunk_forward,
            g_d_fit=torch.tensor(2.0),
            identity={},
        )
    ds[0].split = "train"
    ins[1].ids = ("changed",)
    with pytest.raises(ValueError, match="ids"):
        m.streamed_update(
            model,
            support,
            opt,
            ds,
            ins,
            m.native_chunk_forward,
            g_d_fit=torch.tensor(2.0),
            identity={},
        )
    for bad in [
        [("mlp_output", 0, 0)],
        [("mlp", 0, 1)],
        [("head", 0, 2)],
        [("head", 0, 0)] * 2,
    ]:
        with pytest.raises(ValueError):
            m.configure_candidates(model, bad)


def test_boundary_checkpoint_and_support_tampering_fail_closed():
    model, support = tiny()
    ds, ins = chunks("D"), chunks("I")
    opt = torch.optim.Adam(support.parameters(), lr=0.01)

    def forward(model, chunk):
        with pytest.raises(RuntimeError, match="boundary"):
            m.make_checkpoint(model, support, opt, ds, ins, identity={}, update=0)
        return m.native_chunk_forward(model, chunk)

    m.streamed_update(
        model, support, opt, ds, ins, forward, g_d_fit=torch.tensor(2.0), identity={}
    )
    state = m.make_checkpoint(model, support, opt, ds, ins, identity={}, update=1)
    gate_state = next(v for v in state["gates"].values() if v["eligibility"].any())
    gate_state["eligibility"].zero_()
    with pytest.raises(ValueError, match="eligibility"):
        m.restore_checkpoint(state, model, support, opt, ds, ins, identity={})
    model.model.layers[0].mlp.hidden_gates.set_eligibility(None)
    with pytest.raises(ValueError, match="eligibility"):
        m.export_removal_mask(model, provenance={})


def test_replay_rejects_extra_rng_draw_even_when_binary_gate_values_match():
    model, support = tiny()
    # Saturated-open gate values can conceal changed underlying hard-concrete draws.
    with torch.no_grad():
        for gate in support.gates.values():
            gate.log_alpha.fill_(100.0)
    ds, ins = chunks("D"), chunks("I")
    opt = torch.optim.Adam(support.parameters(), lr=0.01)
    calls = [0]

    def changed_path(model, chunk):
        calls[0] += 1
        if calls[0] == 3:
            torch.rand(1)
        return m.native_chunk_forward(model, chunk)

    with pytest.raises(RuntimeError, match="RNG"):
        m.streamed_update(
            model,
            support,
            opt,
            ds,
            ins,
            changed_path,
            g_d_fit=torch.tensor(2.0),
            identity={},
        )


def test_resume_binds_gap_arm_epsilon_and_fixed_adam_configuration():
    model, support = tiny()
    ds, ins = chunks("D"), chunks("I")
    opt = torch.optim.Adam(support.parameters(), lr=0.01)
    kwargs = dict(g_d_fit=torch.tensor(2.0), identity={"source": "tiny"})
    m.streamed_update(model, support, opt, ds, ins, m.native_chunk_forward, **kwargs)
    saved = m.make_checkpoint(
        model, support, opt, ds, ins, identity=kwargs["identity"], update=1
    )
    restored, rs = tiny()
    ropt = torch.optim.Adam(rs.parameters(), lr=0.01)
    m.restore_checkpoint(
        saved, restored, rs, ropt, ds, ins, identity=kwargs["identity"]
    )
    for changes in [
        {"g_d_fit": torch.tensor(3.0)},
        {"constrained": False},
        {"epsilon": 1e-4},
    ]:
        changed = dict(kwargs, **changes)
        with pytest.raises(ValueError, match="update configuration"):
            m.streamed_update(
                restored, rs, ropt, ds, ins, m.native_chunk_forward, **changed
            )
    ropt.param_groups[0]["lr"] = 0.02
    with pytest.raises(ValueError, match="Adam"):
        m.streamed_update(restored, rs, ropt, ds, ins, m.native_chunk_forward, **kwargs)


def test_replay_rejects_native_distribution_buffer_mutation():
    model, support = tiny()
    with torch.no_grad():
        for gate in support.gates.values():
            gate.log_alpha.fill_(100.0)
    ds, ins = chunks("D"), chunks("I")
    opt = torch.optim.Adam(support.parameters(), lr=0.01)
    calls = [0]

    def changed_distribution(model, chunk):
        calls[0] += 1
        if calls[0] == 3:
            next(iter(support.gates.values())).beta.add_(0.1)
        return m.native_chunk_forward(model, chunk)

    with pytest.raises(RuntimeError, match="parameter"):
        m.streamed_update(
            model,
            support,
            opt,
            ds,
            ins,
            changed_distribution,
            g_d_fit=torch.tensor(2.0),
            identity={},
        )


@pytest.mark.parametrize(
    "mutation",
    ["i_margin", "i_logits", "payload", "tokens", "ids", "order", "boundaries"],
)
def test_update_rejects_cohort_mutation_before_i_or_adam(mutation):
    model, support = tiny()
    ds, ins = chunks("D"), chunks("I")
    opt = torch.optim.Adam(support.parameters(), lr=0.01)
    before = [p.detach().clone() for p in support.parameters()]
    calls = [0]

    def changed_data(model, chunk):
        calls[0] += 1
        if calls[0] == 3:
            if mutation == "i_margin":
                ins[0].baseline_margin.add_(100.0)
            elif mutation == "i_logits":
                ins[0].baseline_logits.add_(1.0)
            elif mutation == "payload":
                ins[0].payload["neutral_input_ids"].add_(1)
            elif mutation == "tokens":
                ins[0].token_counts.add_(1)
            elif mutation == "ids":
                ins[0].ids = ("changed", "1")
            elif mutation == "order":
                ins.reverse()
            elif mutation == "boundaries":
                ins.append(ins.pop(0))
        return m.native_chunk_forward(model, chunk)

    with pytest.raises(RuntimeError, match="cohort"):
        m.streamed_update(
            model, support, opt, ds, ins, changed_data, g_d_fit=2.0, identity={}
        )
    assert calls[0] == 3  # fail immediately after the mutating D callback, before I
    assert not opt.state
    for p, q in zip(before, support.parameters()):
        torch.testing.assert_close(p, q, atol=0, rtol=0)
    with pytest.raises(RuntimeError, match="boundary"):
        m.make_checkpoint(model, support, opt, ds, ins, identity={}, update=0)


@pytest.mark.parametrize(
    "mutation",
    ["norm_epsilon", "attention_dropout", "attention_backend", "config", "rope_buffer"],
)
def test_resume_rejects_effective_base_computation_change(mutation):
    model, support = tiny()
    ds, ins = chunks("D"), chunks("I")
    opt = torch.optim.Adam(support.parameters(), lr=0.01)
    m.streamed_update(
        model, support, opt, ds, ins, m.native_chunk_forward, g_d_fit=2.0, identity={}
    )
    saved = m.make_checkpoint(model, support, opt, ds, ins, identity={}, update=1)
    other, os = tiny()
    oo = torch.optim.Adam(os.parameters(), lr=0.01)
    mutate_computation(other, mutation)
    with pytest.raises(ValueError, match="identity"):
        m.restore_checkpoint(saved, other, os, oo, ds, ins, identity={})
    assert not oo.state


def mutate_computation(model, mutation):
    if mutation == "norm_epsilon":
        model.model.norm.variance_epsilon = 1.0
    elif mutation == "attention_dropout":
        model.model.layers[0].attn.original_attention.attention_dropout = 0.4
    elif mutation == "attention_backend":
        model.config._attn_implementation = "sdpa"
    elif mutation == "config":
        model.config.rope_theta = 20000.0
    elif mutation == "rope_buffer":
        model.model.rotary_emb.inv_freq.add_(0.1)


@pytest.mark.parametrize(
    "mutation",
    ["norm_epsilon", "attention_dropout", "attention_backend", "config", "rope_buffer"],
)
def test_update_rejects_effective_base_computation_mutation(mutation):
    model, support = tiny()
    ds, ins = chunks("D"), chunks("I")
    opt = torch.optim.Adam(support.parameters(), lr=0.01)
    calls = [0]

    def changed_computation(model, chunk):
        calls[0] += 1
        if calls[0] == 3:
            mutate_computation(model, mutation)
        return m.native_chunk_forward(model, chunk)

    with pytest.raises(RuntimeError, match="computation"):
        m.streamed_update(
            model, support, opt, ds, ins, changed_computation, g_d_fit=2.0, identity={}
        )
    assert calls[0] == 3
    assert not opt.state


@pytest.mark.parametrize("mutation", ["target", "computation"])
def test_completed_checkpoint_rejects_changed_authenticated_boundary(mutation):
    model, support = tiny()
    ds, ins = chunks("D"), chunks("I")
    opt = torch.optim.Adam(support.parameters(), lr=0.01)
    m.streamed_update(
        model, support, opt, ds, ins, m.native_chunk_forward, g_d_fit=2.0, identity={}
    )
    if mutation == "target":
        ins[0].baseline_margin.add_(1.0)
    else:
        model.model.norm.variance_epsilon = 1.0
    with pytest.raises(ValueError, match="boundary identity"):
        m.make_checkpoint(model, support, opt, ds, ins, identity={}, update=1)
