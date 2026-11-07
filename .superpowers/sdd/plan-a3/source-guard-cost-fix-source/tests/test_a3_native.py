"""Task 4a: native branch residual Jacobians on random CPU Llama only."""
import copy

import pytest
import torch
from transformers import LlamaConfig, LlamaForCausalLM

from component_analysis.a3_native import ResidualPatch, native_forward, receiver_sites, causally_upstream


@pytest.fixture
def case():
    torch.manual_seed(37)
    config = LlamaConfig(hidden_size=32, intermediate_size=48, num_hidden_layers=2,
                         num_attention_heads=4, num_key_value_heads=2, vocab_size=43,
                         attn_implementation="eager")
    model = LlamaForCausalLM(config).eval().requires_grad_(False)
    batch = {"input_ids": torch.tensor([[1, 3, 7, 4], [2, 5, 8, 0]]),
             "attention_mask": torch.tensor([[1, 1, 1, 1], [1, 1, 1, 0]])}
    return model, batch


def test_forward_readout_and_native_values(case):
    model, batch = case
    sites = [("head", 0, 1), ("mlp", 0, 0), ("readout", 0, 0)]
    out = native_forward(model, batch, capture_sites=sites)
    direct = model(**batch).logits[torch.arange(2), torch.tensor([3, 2])]
    torch.testing.assert_close(out["logits"], direct)
    from component_analysis.hooks import readout_logits
    expected = readout_logits(model, out["incoming"][("readout", 0, 0)][torch.arange(2), out["readout"]])
    torch.testing.assert_close(out["fp32_logits"], expected)
    assert out["additive"][("head", 0, 1)].shape == (2, 4, 32)
    assert not out["fp32_logits"].requires_grad


@pytest.mark.parametrize("site", [("q", 0, 2), ("k", 0, 1), ("v", 0, 1), ("mlp_in", 0, 0), ("readout", 0, 0)])
def test_receiver_vjp_matches_finite_difference_in_residual_coordinates(case, site):
    model, batch = case
    out = native_forward(model, batch, capture_sites=[site], grad=True)
    leaf = out["leaves"][site]
    assert leaf.is_leaf and leaf.shape == (2, 4, 32)
    score = out["fp32_logits"][0, 7] - out["fp32_logits"][0, 3]
    gradient, = torch.autograd.grad(score, leaf)
    direction = torch.randn_like(leaf)
    direction[1] = 0
    mask = torch.zeros((2, 4), dtype=torch.bool)
    perturb_position = int(out["readout"][0]) if site[0] == "readout" else 2
    mask[0, perturb_position] = True
    direction *= mask[..., None]
    if site[0] == "readout":
        assert (gradient * direction).sum().abs() > 1e-4
    values = []
    for sign in [-1, 1]:
        patch = ResidualPatch(leaf.detach() + sign * 0.001 * direction, mask)
        probe = native_forward(model, batch, capture_sites=[], patches={site: patch})
        values.append(probe["fp32_logits"][0, 7] - probe["fp32_logits"][0, 3])
    torch.testing.assert_close((values[1] - values[0]) / 0.002,
                               (gradient * direction).sum(), atol=5e-5, rtol=0.02)
    assert all(p.grad is None and not p.requires_grad for p in model.parameters())


@pytest.mark.parametrize("kind", ["q", "k", "v"])
def test_branch_patches_preserve_other_branches_and_padding(case, kind):
    model, batch = case
    sites = [(k, 0, i) for k, n in [("q", 4), ("k", 2), ("v", 2)] for i in range(n)]
    intact = native_forward(model, batch, capture_sites=sites)
    site = (kind, 0, 0)
    residual = intact["incoming"][site] + torch.randn(2, 4, 32) * 0.1
    patched = native_forward(model, batch, capture_sites=sites,
                             patches={site: ResidualPatch(residual)})
    for other in sites:
        if other != site:
            torch.testing.assert_close(patched["outputs"][other], intact["outputs"][other])
    torch.testing.assert_close(patched["outputs"][site][1, 3], intact["outputs"][site][1, 3])
    assert not torch.allclose(patched["outputs"][site][0, 2], intact["outputs"][site][0, 2])


def test_causal_positions_and_receiver_geometry(case):
    model, batch = case
    sites = receiver_sites(model)
    assert len(sites) == len(set(sites)) == 19
    assert ("k", 0, 2) not in sites
    assert causally_upstream(("head", 0, 0), ("mlp_in", 0, 0), 1, 1)
    assert not causally_upstream(("mlp", 0, 0), ("q", 0, 1), 1, 1)
    assert not causally_upstream(("head", 0, 0), ("q", 1, 1), 2, 1)
    assert not causally_upstream(("head", 0, 0), ("q", 1, 1), 0, 1)
    assert causally_upstream(("head", 0, 0), ("k", 1, 1), 0, 0)
    site = ("v", 0, 0)
    out = native_forward(model, batch, capture_sites=[site], grad=True)
    gradient, = torch.autograd.grad(out["fp32_logits"][0, 7], out["leaves"][site])
    assert gradient[0, 0].abs().sum() > 0
    assert gradient[0, 2].abs().sum() > 0
    assert not torch.allclose(gradient[0, 0], gradient[0, 2])
    assert gradient[1].abs().sum() == 0


def test_cleanup_after_exception_and_strict_contract(case):
    model, batch = case
    before = sum(len(m._forward_hooks) + len(m._forward_pre_hooks) for m in model.modules())
    def fail(*args):
        raise RuntimeError("deliberate failure")
    handle = model.model.layers[1].register_forward_pre_hook(fail)
    with pytest.raises(RuntimeError, match="deliberate"):
        native_forward(model, batch, capture_sites=[("q", 0, 0)], grad=True)
    handle.remove()
    assert sum(len(m._forward_hooks) + len(m._forward_pre_hooks) for m in model.modules()) == before
    native_forward(model, batch, capture_sites=[])
    model.train()
    with pytest.raises(ValueError, match="eval"):
        native_forward(model, batch, capture_sites=[])
    model.eval().requires_grad_(True)
    with pytest.raises(ValueError, match="frozen"):
        native_forward(model, batch, capture_sites=[])


def test_actual_nnsight_inference_parity(case):
    nnsight = pytest.importorskip("nnsight")
    if nnsight.__version__ != "0.7.0":
        pytest.skip("actual inference parity requires pinned nnsight 0.7.0")
    from nnsight import NNsight
    from component_analysis.hooks import capture_forward
    model, batch = case
    sites = [("head", 0, 1), ("mlp", 0, 0), ("q", 0, 1), ("k", 0, 1), ("v", 0, 1), ("mlp_in", 0, 0), ("readout", 0, 0)]
    native = native_forward(model, batch, capture_sites=sites)
    inference = capture_forward(NNsight(copy.deepcopy(model)), batch["input_ids"],
                                batch["attention_mask"], components=sites)
    torch.testing.assert_close(native["logits"], inference.logits)
    for site in sites:
        torch.testing.assert_close(native["outputs"][site], inference.outputs[site])


def test_patch_constants_become_independent_leaves_and_joint_branches(case):
    model, batch = case
    sites = [("q", 0, 0), ("k", 0, 0), ("v", 0, 0)]
    intact = native_forward(model, batch, capture_sites=sites)
    constants = {site: (intact["incoming"][site] + 0.1 * torch.randn(2, 4, 32)).requires_grad_()
                 for site in sites}
    patches = {site: ResidualPatch(value) for site, value in constants.items()}
    joint = native_forward(model, batch, capture_sites=sites, patches=patches, grad=True)
    assert set(joint["leaves"]) == set(sites)
    gradients = torch.autograd.grad(joint["fp32_logits"].sum(), list(joint["leaves"].values()))
    assert all(g.abs().sum() > 0 for g in gradients)
    assert all(value.grad is None for value in constants.values())
    for site in sites:
        torch.testing.assert_close(joint["incoming"][site], intact["incoming"][site])
        separate = native_forward(model, batch, capture_sites=[site], patches={site: patches[site]})
        torch.testing.assert_close(joint["outputs"][site], separate["outputs"][site])
    assert all(p.grad is None for p in model.parameters())


def test_frozen_readout_clamp_blocks_upstream_patch(case):
    model, batch = case
    readout, source = ("readout", 0, 0), ("v", 0, 0)
    intact = native_forward(model, batch, capture_sites=[readout, source])
    patches = {source: ResidualPatch(intact["incoming"][source] + torch.randn(2, 4, 32)),
               readout: ResidualPatch(intact["incoming"][readout])}
    clamped = native_forward(model, batch, capture_sites=[readout], patches=patches)
    torch.testing.assert_close(clamped["fp32_logits"], intact["fp32_logits"])


def test_invalid_patch_cleans_up_and_padding_gradient_is_zero(case):
    model, batch = case
    site = ("v", 0, 0)
    before = sum(len(m._forward_hooks) + len(m._forward_pre_hooks) for m in model.modules())
    with pytest.raises(ValueError, match="shape"):
        native_forward(model, batch, capture_sites=[site],
                       patches={site: ResidualPatch(torch.zeros(1))}, grad=True)
    assert sum(len(m._forward_hooks) + len(m._forward_pre_hooks) for m in model.modules()) == before
    out = native_forward(model, batch, capture_sites=[site], grad=True)
    gradient, = torch.autograd.grad(out["fp32_logits"].sum(), out["leaves"][site])
    assert gradient[1, 3].abs().sum() == 0


def test_bfloat16_fp32_readout_matches_inference_convention(case):
    model, batch = case
    model.to(torch.bfloat16)
    from component_analysis.hooks import readout_logits
    site = ("readout", 0, 0)
    out = native_forward(model, batch, capture_sites=[site], grad=True)
    expected = readout_logits(model, out["incoming"][site][torch.arange(2), out["readout"]])
    torch.testing.assert_close(out["fp32_logits"], expected, atol=0, rtol=0)
    assert torch.autograd.grad(out["fp32_logits"].sum(), out["leaves"][site])[0].abs().sum() > 0


def test_projected_heads_sum_to_attention_write_and_hidden_capture(case):
    model, batch = case
    seen = {}
    handles = [model.model.layers[0].self_attn.o_proj.register_forward_hook(
        lambda m, a, out: seen.update(attention=out.detach().clone())),
        model.model.layers[0].mlp.down_proj.register_forward_pre_hook(
        lambda m, a: seen.update(hidden=a[0].detach().clone()))]
    try:
        out = native_forward(model, batch, capture_sites=[("head", 0, h) for h in range(4)]
                             + [("neuron_hidden", 0, 0)])
    finally:
        for handle in handles:
            handle.remove()
    torch.testing.assert_close(sum(out["additive"].values()), seen["attention"])
    torch.testing.assert_close(out["outputs"][("neuron_hidden", 0, 0)], seen["hidden"])


def test_invalid_group_and_readout_padding_are_rejected(case):
    model, batch = case
    with pytest.raises(ValueError, match="KV groups"):
        native_forward(model, batch, capture_sites=[("k", 0, 2)])
    with pytest.raises(ValueError, match="padding"):
        native_forward(model, dict(batch, readout=torch.tensor([3, 3])), capture_sites=[])
