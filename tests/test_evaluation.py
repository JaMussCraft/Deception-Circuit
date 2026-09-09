"""
CPU tests for the circuit-evaluation harness.

Everything here runs on a tiny randomly-initialised Llama (2 layers, 64 hidden,
4 heads, vocab 101) in a couple of seconds — no downloads, no GPU. The sampler
tests additionally run against the *real* saved circuit's geometry when a run
directory is present, since that is where the interesting shapes live.

The load-bearing ones:

  T1  with no hook installed, `_ablation_ref` returns the identical object, so
      training is bit-identical to before the hook existed
  T2  all gates open through the dual-stream path == plain LlamaForCausalLM
  T4  all gates closed under zero ablation == lm_head(norm(embed_tokens(ids))),
      which only holds if all seven ablation call sites are wired correctly
"""

from __future__ import annotations

import contextlib
import json
import os
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from analysis import (apply_node_masks, assert_masks_equal, extract_node_masks,
                      open_all_gates)
from config import NodePruningConfig
from evaluation import ablation as abl
from evaluation import knockout as K
from evaluation import masks as M
from evaluation import metrics
from evaluation import variants
from models.llama_node import (ABLATION_SITES, _ablation_ref,
                               clear_ablation_hook, install_ablation_hook)
from tasks import Task
from tests.helpers import TINY, build_tiny_pair

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE_RUN = os.path.join(
    REPO_ROOT, "outputs", "llama-8b-instruct_std", "nls0.7_noedge_260721-151636")

NUM_HEADS = TINY["heads"]
HEAD_DIM = TINY["head_dim"]
N_LAYERS = TINY["layers"]
HIDDEN = TINY["hidden"]
INTERMEDIATE = TINY["intermediate"]
VOCAB = TINY["vocab"]

build_pair = build_tiny_pair


def batch(bs=2, seq=8, seed=1, pad=0):
    g = torch.Generator().manual_seed(seed)
    ids = torch.randint(0, VOCAB, (bs, seq), generator=g)
    corrupt = torch.randint(0, VOCAB, (bs, seq), generator=g)
    mask = torch.ones(bs, seq, dtype=torch.long)
    if pad:
        mask[:, -pad:] = 0
    return ids, corrupt, mask


def random_masks_for(model, seed=0, density=0.5):
    """A hierarchically-arbitrary binary mask object matching the model."""
    rng = np.random.default_rng(seed)
    out = {"attention_blocks": rng.integers(0, 2, N_LAYERS).astype(np.uint8),
           "mlp_blocks": rng.integers(0, 2, N_LAYERS).astype(np.uint8)}
    for key, size in (("attention_heads", NUM_HEADS),
                      ("attention_neurons", NUM_HEADS * HEAD_DIM),
                      ("mlp_hidden", INTERMEDIATE),
                      ("mlp_output", HIDDEN)):
        out[key] = {str(l): (rng.random(size) < density).astype(np.uint8)
                    for l in range(len(model.model.layers))}
    return out


# ==============================================================================
# T1 — no-hook identity
# ==============================================================================

def test_t1_ablation_ref_is_identity_without_hook():
    _, pruned = build_pair()
    t = torch.randn(2, 3, 4)
    module = pruned.model.layers[0]
    for site in ABLATION_SITES:
        assert _ablation_ref(module, t, site) is t
        assert _ablation_ref(module.attn, t, site) is t
        assert _ablation_ref(module.mlp, t, site) is t


def test_t1_hook_install_and_clear_round_trip():
    _, pruned = build_pair()
    seen = []

    def hook(module, corrupted, site):
        seen.append(site)
        return corrupted

    n = install_ablation_hook(pruned, hook)
    # 2 layers x (layer + attn + mlp)
    assert n == 3 * N_LAYERS
    # A hook that is an nn.Module must not become a submodule.
    module_hook = torch.nn.Linear(2, 2)
    install_ablation_hook(pruned, module_hook)
    assert all(m is not module_hook for m in pruned.modules())

    install_ablation_hook(pruned, hook)
    ids, corrupt, mask = batch()
    pruned(input_ids=ids, corrupted_input_ids=corrupt, attention_mask=mask,
           use_cache=False)
    # Six sites fire per layer for the default config (no full-layer gates).
    assert set(seen) == {"attn_head", "attn_neuron", "attn_block",
                         "mlp_hidden", "mlp_output", "mlp_block"}

    clear_ablation_hook(pruned)
    t = torch.randn(3)
    assert _ablation_ref(pruned.model.layers[0], t, "attn_block") is t


def test_t1_layer_site_fires_when_full_layer_gates_exist():
    cfg = NodePruningConfig(prune_full_layers=True)
    _, pruned = build_pair(cfg)
    seen = []
    install_ablation_hook(pruned, lambda m, c, s: (seen.append(s), c)[1])
    ids, corrupt, mask = batch()
    pruned(input_ids=ids, corrupted_input_ids=corrupt, attention_mask=mask,
           use_cache=False)
    assert "layer" in seen
    assert abl.required_sites(pruned)["layer"] == list(range(N_LAYERS))


# ==============================================================================
# T2 — all gates open == the plain model
# ==============================================================================

def test_t2_all_open_matches_plain_model_exactly_under_eager():
    """The gating algebra is exact: with the same attention kernel on both
    sides, all-gates-open dual-stream is bit-identical to plain Llama."""
    plain, pruned = build_pair(attn_implementation="eager")
    ids, corrupt, mask = batch()
    open_all_gates(pruned)

    with torch.no_grad():
        got = pruned(input_ids=ids, corrupted_input_ids=corrupt,
                     attention_mask=mask, use_cache=False).logits
        ref = plain(input_ids=ids, attention_mask=mask, use_cache=False).logits

    assert torch.equal(got, ref), f"maxdiff {(got - ref).abs().max().item():.3e}"


def test_t2_all_open_matches_plain_model():
    """...and to fp32 round-off under the default kernel.

    The dual-stream forward always builds an explicit float causal mask (
    LlamaModel lost `_update_causal_mask` in transformers 4.53+), while the
    plain model's `create_causal_mask` returns None for an unpadded batch and
    lets SDPA take its `is_causal` fast path. Same algebra, different kernel,
    ~1e-7 in fp32 — which is why the harness's all-open anchors are checked
    against a tolerance rather than for bit-equality.
    """
    plain, pruned = build_pair()
    ids, corrupt, mask = batch()
    open_all_gates(pruned)

    with torch.no_grad():
        got = pruned(input_ids=ids, corrupted_input_ids=corrupt,
                     attention_mask=mask, use_cache=False).logits
        ref = plain(input_ids=ids, attention_mask=mask, use_cache=False).logits

    assert torch.allclose(got, ref, rtol=0, atol=1e-6), \
        f"maxdiff {(got - ref).abs().max().item():.3e}"


def test_t2_single_stream_path_is_the_ungated_full_model():
    """No corrupted stream means no gating at all — the vanilla HF path. This is
    what `--reference shared` uses instead of a second 15 GB model."""
    plain, pruned = build_pair(attn_implementation="eager")
    ids, _, mask = batch()
    apply_node_masks(pruned, M.zeros_like(random_masks_for(pruned, seed=2)))

    with torch.no_grad():
        got = pruned(input_ids=ids, attention_mask=mask, use_cache=False).logits
        ref = plain(input_ids=ids, attention_mask=mask, use_cache=False).logits

    assert torch.equal(got, ref), f"maxdiff {(got - ref).abs().max().item():.3e}"


def test_t2_all_open_matches_plain_model_with_padding():
    plain, pruned = build_pair(attn_implementation="eager")
    ids, corrupt, mask = batch(pad=3)
    open_all_gates(pruned)

    with torch.no_grad():
        got = pruned(input_ids=ids, corrupted_input_ids=corrupt,
                     attention_mask=mask, use_cache=False).logits
        ref = plain(input_ids=ids, attention_mask=mask, use_cache=False).logits

    # Only unpadded positions are meaningful under right padding.
    keep = mask.bool()
    assert torch.equal(got[keep], ref[keep]), \
        f"maxdiff {(got[keep] - ref[keep]).abs().max().item():.3e}"


# ==============================================================================
# T3 — mask round trip and validation
# ==============================================================================

def test_t3_mask_round_trip():
    _, pruned = build_pair()
    m = random_masks_for(pruned, seed=3)
    counts = apply_node_masks(pruned, m)

    assert_masks_equal(M.as_lists(m), extract_node_masks(pruned))
    assert counts["attention_neurons"]["total"] == N_LAYERS * NUM_HEADS * HEAD_DIM
    assert counts["mlp_hidden"]["active"] == int(
        sum(v.sum() for v in m["mlp_hidden"].values()))


def test_t3_round_trip_accepts_lists_and_arrays():
    _, pruned = build_pair()
    m = random_masks_for(pruned, seed=4)
    apply_node_masks(pruned, M.as_lists(m))
    assert_masks_equal(M.as_lists(m), extract_node_masks(pruned))


def test_t3_missing_key_raises():
    _, pruned = build_pair()
    m = random_masks_for(pruned, seed=5)
    del m["mlp_output"]
    with pytest.raises(ValueError, match="mlp_output"):
        apply_node_masks(pruned, m)


def test_t3_extra_key_raises():
    _, pruned = build_pair()
    m = random_masks_for(pruned, seed=5)
    m["layers"] = np.ones(N_LAYERS, dtype=np.uint8)
    with pytest.raises(ValueError, match="layers"):
        apply_node_masks(pruned, m)


def test_t3_non_strict_leaves_absent_gates_alone():
    _, pruned = build_pair()
    m = random_masks_for(pruned, seed=5)
    del m["mlp_output"]
    counts = apply_node_masks(pruned, m, strict=False)
    assert "mlp_output" not in counts


def test_t3_wrong_length_raises():
    _, pruned = build_pair()
    m = random_masks_for(pruned, seed=6)
    m["mlp_hidden"]["0"] = m["mlp_hidden"]["0"][:-1]
    with pytest.raises(ValueError, match="values but"):
        apply_node_masks(pruned, m)


def test_t3_non_binary_raises():
    _, pruned = build_pair()
    m = random_masks_for(pruned, seed=7)
    m["attention_heads"]["0"] = np.array([0, 1, 2, 0], dtype=np.uint8)
    with pytest.raises(ValueError, match="not binary"):
        apply_node_masks(pruned, m)


def test_t3_assert_masks_equal_detects_a_single_flip():
    _, pruned = build_pair()
    a = random_masks_for(pruned, seed=8)
    b = {k: (v.copy() if isinstance(v, np.ndarray) else {kk: vv.copy() for kk, vv in v.items()})
         for k, v in a.items()}
    b["attention_neurons"]["1"][5] ^= 1
    with pytest.raises(AssertionError, match="attention_neurons"):
        assert_masks_equal(M.as_lists(a), M.as_lists(b))


def test_t3_open_all_gates_is_the_all_ones_mask():
    _, pruned = build_pair()
    apply_node_masks(pruned, random_masks_for(pruned, seed=9))
    open_all_gates(pruned)
    got = extract_node_masks(pruned)
    for key, value in got.items():
        entries = value.values() if isinstance(value, dict) else [value]
        for v in entries:
            assert all(x == 1 for x in np.atleast_1d(v).tolist())


# ==============================================================================
# T4/T5 — zero and mean ablation
# ==============================================================================

def empty_circuit_masks(model):
    m = random_masks_for(model, seed=0)
    return M.zeros_like(m)


def test_t4_empty_circuit_with_zero_ablation_is_embedding_only():
    plain, pruned = build_pair()
    ids, corrupt, mask = batch()
    apply_node_masks(pruned, empty_circuit_masks(pruned))

    with torch.no_grad():
        with abl.ablation_hook(pruned, abl.ZeroHook()):
            got = pruned(input_ids=ids, corrupted_input_ids=corrupt,
                         attention_mask=mask, use_cache=False).logits
        expected = plain.lm_head(plain.model.norm(plain.model.embed_tokens(ids)))

    assert torch.equal(got, expected), \
        f"maxdiff {(got - expected).abs().max().item():.3e}"


def test_t5_mean_hook_with_a_zero_bank_equals_zero_hook():
    _, pruned = build_pair()
    ids, corrupt, mask = batch(seed=11)
    apply_node_masks(pruned, random_masks_for(pruned, seed=11))

    shapes = {"attn_head": (NUM_HEADS, HEAD_DIM),
              "attn_neuron": (NUM_HEADS, HEAD_DIM),
              "attn_block": (HIDDEN,),
              "mlp_hidden": (INTERMEDIATE,),
              "mlp_output": (HIDDEN,),
              "mlp_block": (HIDDEN,),
              "layer": (HIDDEN,)}
    bank = {site: {l: torch.zeros(shape) for l in range(N_LAYERS)}
            for site, shape in shapes.items()}

    with torch.no_grad():
        with abl.ablation_hook(pruned, abl.make_hook("zero")):
            a = pruned(input_ids=ids, corrupted_input_ids=corrupt,
                       attention_mask=mask, use_cache=False).logits
        with abl.ablation_hook(pruned, abl.make_hook("mean", bank, pruned)):
            b = pruned(input_ids=ids, corrupted_input_ids=corrupt,
                       attention_mask=mask, use_cache=False).logits

    assert torch.equal(a, b)


def test_t5_mean_hook_rejects_an_incomplete_bank():
    _, pruned = build_pair()
    with pytest.raises(KeyError, match="missing"):
        abl.make_hook("mean", {"attn_head": {}}, pruned)


def test_t5_interchange_installs_no_hook():
    _, pruned = build_pair()
    assert abl.make_hook("interchange") is None
    ids, corrupt, mask = batch()
    apply_node_masks(pruned, random_masks_for(pruned, seed=12))
    with torch.no_grad():
        with abl.ablation_hook(pruned, None):
            a = pruned(input_ids=ids, corrupted_input_ids=corrupt,
                       attention_mask=mask, use_cache=False).logits
        b = pruned(input_ids=ids, corrupted_input_ids=corrupt,
                   attention_mask=mask, use_cache=False).logits
    assert torch.equal(a, b)


# ==============================================================================
# T6 — mean bank collection
# ==============================================================================

class _Recorder:
    """Records every reference tensor it is handed; perturbs nothing."""

    def __init__(self):
        self.seen = {}

    def __call__(self, module, corrupted, site):
        layer = getattr(module, "layer_idx", None)
        self.seen.setdefault(site, {}).setdefault(layer, []).append(
            corrupted.detach().clone())
        return corrupted


def _stream_batches(n=3, bs=2, seq=8, pad=2):
    out = []
    for i in range(n):
        ids, corrupt, mask = batch(bs=bs, seq=seq, seed=20 + i, pad=pad)
        out.append({"input_ids": ids, "corrupted_input_ids": corrupt,
                    "attention_mask": mask})
    return out


def test_t6_collect_mean_bank_matches_a_hand_computed_masked_mean():
    _, pruned = build_pair(num_hidden_layers=1)
    batches = _stream_batches()

    rec = _Recorder()
    with torch.no_grad():
        with abl.ablation_hook(pruned, rec):
            for b in batches:
                pruned(input_ids=b["input_ids"],
                       corrupted_input_ids=b["corrupted_input_ids"],
                       attention_mask=b["attention_mask"], use_cache=False)

    bank = abl.collect_mean_bank(pruned, batches, device="cpu", source="corrupt",
                                verbose=False)

    total_tokens = float(sum(b["attention_mask"].sum() for b in batches))
    for site, layers in rec.seen.items():
        for layer, tensors in layers.items():
            acc = None
            for t, b in zip(tensors, batches):
                m = b["attention_mask"].reshape(
                    *b["attention_mask"].shape, *([1] * (t.dim() - 2))).float()
                contrib = (t.float() * m).sum(dim=(0, 1))
                acc = contrib if acc is None else acc + contrib
            expected = acc / total_tokens
            assert torch.allclose(bank[site][layer], expected, atol=1e-6), site


def test_t6_unpadded_single_batch_mean_matches_torch_mean():
    _, pruned = build_pair(num_hidden_layers=1)
    batches = _stream_batches(n=1, pad=0)

    rec = _Recorder()
    with torch.no_grad():
        with abl.ablation_hook(pruned, rec):
            b = batches[0]
            pruned(input_ids=b["input_ids"],
                   corrupted_input_ids=b["corrupted_input_ids"],
                   attention_mask=b["attention_mask"], use_cache=False)

    bank = abl.collect_mean_bank(pruned, batches, device="cpu", source="corrupt",
                                verbose=False)
    for site, layers in rec.seen.items():
        for layer, tensors in layers.items():
            expected = tensors[0].float().mean(dim=(0, 1))
            assert torch.allclose(bank[site][layer], expected, atol=1e-6), site


def test_t6_swapped_pass_recovers_the_clean_prompt_mean():
    _, pruned = build_pair(num_hidden_layers=1)
    batches = _stream_batches(n=2)
    swapped = [{"input_ids": b["corrupted_input_ids"],
                "corrupted_input_ids": b["input_ids"],
                "attention_mask": b["attention_mask"]} for b in batches]

    clean_bank = abl.collect_mean_bank(pruned, batches, device="cpu",
                                       source="clean", verbose=False)
    direct = abl.collect_mean_bank(pruned, swapped, device="cpu",
                                   source="corrupt", verbose=False)

    for site in clean_bank:
        for layer in clean_bank[site]:
            assert torch.allclose(clean_bank[site][layer], direct[site][layer],
                                  atol=1e-6), site


def test_t6_pooled_is_the_average_of_the_two_passes():
    _, pruned = build_pair(num_hidden_layers=1)
    batches = _stream_batches(n=2)

    pooled = abl.collect_mean_bank(pruned, batches, device="cpu",
                                   source="pooled", verbose=False)
    corrupt = abl.collect_mean_bank(pruned, batches, device="cpu",
                                    source="corrupt", verbose=False)
    clean = abl.collect_mean_bank(pruned, batches, device="cpu",
                                  source="clean", verbose=False)

    for site in pooled:
        for layer in pooled[site]:
            expected = 0.5 * (corrupt[site][layer] + clean[site][layer])
            assert torch.allclose(pooled[site][layer], expected, atol=1e-6), site


def test_t6_collector_does_not_perturb_the_forward():
    _, pruned = build_pair()
    apply_node_masks(pruned, random_masks_for(pruned, seed=30))
    ids, corrupt, mask = batch(seed=31)
    with torch.no_grad():
        plain_logits = pruned(input_ids=ids, corrupted_input_ids=corrupt,
                              attention_mask=mask, use_cache=False).logits
        col = abl.MeanCollector()
        col.set_mask(mask)
        with abl.ablation_hook(pruned, col):
            hooked = pruned(input_ids=ids, corrupted_input_ids=corrupt,
                            attention_mask=mask, use_cache=False).logits
    assert torch.equal(plain_logits, hooked)


# ==============================================================================
# T7 — random circuit sampler
# ==============================================================================

@pytest.fixture(scope="module")
def reference_circuit():
    path = os.path.join(REFERENCE_RUN, "active_nodes.json")
    if not os.path.exists(path):
        pytest.skip(f"reference run not present: {path}")
    return M.load_circuit_masks(REFERENCE_RUN)


def test_t7_reference_circuit_is_hierarchically_consistent(reference_circuit):
    M.validate_hierarchy(reference_circuit, num_heads=32, head_dim=128)
    counts = M.count_masks(reference_circuit)
    assert counts["attention_heads"]["active"] == 38
    assert counts["attention_neurons"]["active"] == 1868
    assert counts["mlp_hidden"]["active"] == 5792
    assert counts["mlp_output"]["active"] == 2980


def test_t7_feasibility_report_has_headroom(reference_circuit):
    report = M.check_feasibility(reference_circuit, 32, 128)
    live = {k: v for k, v in report.items() if v["heads"]}
    assert set(live) == {"7", "8", "12", "13", "15", "17"}
    assert all(v["headroom"] > 0 for v in live.values())


def test_t7_infeasible_circuit_raises():
    circuit = {"attention_blocks": np.array([1], dtype=np.uint8),
               "attention_heads": {"0": np.array([1, 0, 0, 0], dtype=np.uint8)},
               "attention_neurons": {"0": np.ones(NUM_HEADS * HEAD_DIM, dtype=np.uint8)}}
    with pytest.raises(ValueError, match="do not fit"):
        M.check_feasibility(circuit, NUM_HEADS, HEAD_DIM)


@pytest.mark.parametrize("alloc", ["uniform", "perhead"])
def test_t7_samples_are_size_matched_and_hierarchical(reference_circuit, alloc):
    target = M.count_masks(reference_circuit)
    n = 200 if alloc == "uniform" else 50
    for index in range(n):
        s = M.sample_random_masks(reference_circuit, num_heads=32, head_dim=128,
                                  seed=42, index=index, alloc=alloc)
        M.validate_hierarchy(s, num_heads=32, head_dim=128,
                             label=f"random circuit {index}")
        assert M.count_masks(s) == target, f"sample {index} is not size-matched"


def test_t7_sampling_is_reproducible_and_index_dependent(reference_circuit):
    kw = dict(num_heads=32, head_dim=128, seed=42)
    a = M.sample_random_masks(reference_circuit, index=7, **kw)
    b = M.sample_random_masks(reference_circuit, index=7, **kw)
    c = M.sample_random_masks(reference_circuit, index=8, **kw)
    d = M.sample_random_masks(reference_circuit, index=7, num_heads=32,
                              head_dim=128, seed=43)

    def same(x, y):
        return all(np.array_equal(x[k][l], y[k][l])
                   for k in ("attention_heads", "attention_neurons",
                             "mlp_hidden", "mlp_output") for l in x[k])

    assert same(a, b)
    assert not same(a, c)
    assert not same(a, d)


def test_t7_sharded_set_matches_the_contiguous_set(reference_circuit):
    kw = dict(num_heads=32, head_dim=128, seed=42, validate=False)
    whole = M.sample_random_mask_set(reference_circuit, n=6, **kw)
    shard = M.sample_random_mask_set(reference_circuit, n=3, start=3, **kw)
    for i, s in enumerate(shard):
        assert np.array_equal(s["mlp_hidden"]["0"], whole[3 + i]["mlp_hidden"]["0"])


def test_t7_perhead_preserves_the_per_head_count_multiset(reference_circuit):
    s = M.sample_random_masks(reference_circuit, num_heads=32, head_dim=128,
                              seed=1, index=0, alloc="perhead")
    for layer in ("7", "8", "12", "13", "15", "17"):
        src = np.asarray(reference_circuit["attention_neurons"][layer])
        got = np.asarray(s["attention_neurons"][layer])
        a = sorted(x for x in src.reshape(32, 128).sum(axis=1) if x)
        b = sorted(x for x in got.reshape(32, 128).sum(axis=1) if x)
        assert a == b, layer


def test_t7_sampler_works_on_the_tiny_geometry():
    _, pruned = build_pair()
    circuit = {
        "attention_blocks": np.array([1, 0], dtype=np.uint8),
        "mlp_blocks": np.array([1, 1], dtype=np.uint8),
        "attention_heads": {"0": np.array([1, 0, 1, 0], dtype=np.uint8),
                            "1": np.zeros(NUM_HEADS, dtype=np.uint8)},
        "attention_neurons": {
            "0": np.concatenate([np.ones(5), np.zeros(11), np.zeros(16),
                                 np.ones(3), np.zeros(13), np.zeros(16)]).astype(np.uint8),
            "1": np.zeros(NUM_HEADS * HEAD_DIM, dtype=np.uint8)},
        "mlp_hidden": {"0": (np.arange(INTERMEDIATE) < 7).astype(np.uint8),
                       "1": (np.arange(INTERMEDIATE) < 3).astype(np.uint8)},
        "mlp_output": {"0": (np.arange(HIDDEN) < 4).astype(np.uint8),
                       "1": (np.arange(HIDDEN) < 2).astype(np.uint8)},
    }
    M.validate_hierarchy(circuit, num_heads=NUM_HEADS, head_dim=HEAD_DIM)
    for index in range(50):
        s = M.sample_random_masks(circuit, num_heads=NUM_HEADS, head_dim=HEAD_DIM,
                                  seed=0, index=index)
        M.validate_hierarchy(s, num_heads=NUM_HEADS, head_dim=HEAD_DIM)
        assert M.count_masks(s) == M.count_masks(circuit)
        # An inactive block stays entirely empty.
        assert s["attention_heads"]["1"].sum() == 0
        # The sampled circuit must be loadable onto a real model.
        apply_node_masks(pruned, s)


# ==============================================================================
# T8 — knockout
# ==============================================================================

def test_t8_finest_knockout_is_the_exact_complement(reference_circuit):
    k = M.knockout_masks(reference_circuit, "finest")
    M.assert_complement(reference_circuit, k)

    counts = M.count_masks(k)
    for key in M.COARSE_KEYS:
        if key in k:
            assert counts[key]["active"] == counts[key]["total"], key

    src = M.count_masks(reference_circuit)
    ablated = sum(src[key]["active"] for key in M.FINEST_KEYS)
    assert ablated == 1868 + 5792 + 2980 == 10640
    for key in M.FINEST_KEYS:
        assert counts[key]["active"] == src[key]["total"] - src[key]["active"]


def test_t8_all_knockout_complements_every_granularity(reference_circuit):
    k = M.knockout_masks(reference_circuit, "all")
    M.assert_complement(reference_circuit, k,
                        keys=M.FINEST_KEYS + ("attention_heads", "attention_blocks",
                                              "mlp_blocks"))


def test_t8_assert_complement_catches_an_overlap(reference_circuit):
    k = M.knockout_masks(reference_circuit, "finest")
    k["mlp_hidden"]["0"] = np.asarray(reference_circuit["mlp_hidden"]["0"]).copy()
    with pytest.raises(AssertionError, match="overlaps"):
        M.assert_complement(reference_circuit, k)


def test_t8_knockout_rejects_an_unknown_granularity(reference_circuit):
    with pytest.raises(ValueError, match="finest"):
        M.knockout_masks(reference_circuit, "coarse")


def test_t8_coarsen_opens_every_fine_gate_under_a_live_parent(reference_circuit):
    coarse = M.coarsen_masks(reference_circuit, head_dim=128)
    M.validate_hierarchy(coarse, num_heads=32, head_dim=128, label="coarse")

    src, got = M.count_masks(reference_circuit), M.count_masks(coarse)
    # Coarse gates are untouched.
    for key in ("attention_blocks", "mlp_blocks", "attention_heads"):
        assert got[key] == src[key], key
    # Fine gates are exactly "all of the units under an open parent".
    assert got["attention_neurons"]["active"] == 38 * 128
    assert got["mlp_hidden"]["active"] == src["mlp_blocks"]["active"] * 14336
    assert got["mlp_output"]["active"] == src["mlp_blocks"]["active"] * 4096
    # And it is a superset of the discovered circuit.
    for key in M.FINEST_KEYS:
        for layer, vec in reference_circuit[key].items():
            assert (np.asarray(coarse[key][layer]) >= np.asarray(vec)).all(), (key, layer)


def test_t8_coarsen_leaves_dead_heads_and_closed_blocks_empty(reference_circuit):
    coarse = M.coarsen_masks(reference_circuit, head_dim=128)
    heads = np.asarray(reference_circuit["attention_heads"]["14"])
    neurons = np.asarray(coarse["attention_neurons"]["14"]).reshape(32, 128)
    assert (neurons.sum(axis=1) == heads.astype(int) * 128).all()

    blocks = np.asarray(reference_circuit["mlp_blocks"])
    for layer in reference_circuit["mlp_hidden"]:
        expected = 14336 if blocks[int(layer)] else 0
        assert int(np.asarray(coarse["mlp_hidden"][layer]).sum()) == expected, layer


def test_t8_coarsen_is_loadable_onto_a_model():
    _, pruned = build_pair()
    m = random_masks_for(pruned, seed=41)
    head_dim = pruned.config.hidden_size // pruned.config.num_attention_heads
    coarse = M.coarsen_masks(m, head_dim=head_dim)
    apply_node_masks(pruned, coarse)
    assert_masks_equal(M.as_lists(coarse), extract_node_masks(pruned))


def test_t8_empty_and_full_masks():
    _, pruned = build_pair()
    m = random_masks_for(pruned, seed=40)
    empty, full = M.zeros_like(m), M.ones_like(m)
    assert M.count_masks(empty)["mlp_hidden"]["active"] == 0
    counts = M.count_masks(full)["attention_neurons"]
    assert counts["active"] == counts["total"]
    apply_node_masks(pruned, empty)
    apply_node_masks(pruned, full)


def test_t8_load_rejects_a_run_without_masks(tmp_path):
    path = tmp_path / "active_nodes.json"
    path.write_text(json.dumps({"active_heads": {}, "active_mlps": []}))
    with pytest.raises(ValueError, match="no 'masks' key"):
        M.load_circuit_masks(str(tmp_path))


# ==============================================================================
# T9 — eval 2's per-example flip audit and task-side null
# ==============================================================================

def audit_row(index, argmax, ref, target=10, distractor=20):
    return {"index": index, "argmax_id": argmax, "ref_argmax_id": ref,
            "target_id": target, "distractor_id": distractor}


def test_t9_flip_audit_splits_stayed_flipped_and_other():
    rows = [
        audit_row(0, argmax=10, ref=10),        # deceptive -> deceptive
        audit_row(1, argmax=20, ref=10),        # deceptive -> honest
        audit_row(2, argmax=99, ref=10),        # deceptive -> neither
        audit_row(3, argmax=20, ref=20),        # full model was already honest
        audit_row(4, argmax=10, ref=99),        # full model left the readout
    ]
    per_example, summary = K.flip_audit(rows)

    assert [r["status"] for r in per_example] == [
        "stayed_deceptive", "flipped_honest", "other", "other", "other"]
    assert summary["n_stayed_deceptive"] == 1
    assert summary["n_flipped_honest"] == 1
    assert summary["n_other"] == 3
    # Rows 3 and 4 are 'other' because the FULL model was observed not to be
    # deceptive; row 2 is 'other' because the knockout left the readout.
    assert summary["n_full_not_deceptive"] == 2
    assert summary["n_full_unknown"] == 0
    assert summary["stayed_ids"] == [0]
    assert summary["flipped_ids"] == [1]


def test_t9_flip_audit_does_not_read_a_missing_reference_as_evidence():
    """No reference means the full model's choice is UNKNOWN, not 'not deceptive'.

    Counting an unobserved row as evidence that the full model was already
    honest would turn a missing reference into a finding.
    """
    per_example, summary = K.flip_audit([audit_row(0, argmax=10, ref=None),
                                         audit_row(1, argmax=20, ref=None)])
    assert [r["full_choice"] for r in per_example] == ["unknown", "unknown"]
    assert [r["status"] for r in per_example] == ["other", "other"]
    assert summary["n_stayed_deceptive"] == 0 and summary["n_flipped_honest"] == 0
    assert summary["n_other"] == 2
    assert summary["n_full_unknown"] == 2
    assert summary["n_full_not_deceptive"] == 0


def test_t9_flip_audit_carries_prompt_excerpts_and_ids():
    per_example, _ = K.flip_audit([audit_row(1, argmax=10, ref=10)],
                                  excerpts=["prompt zero", "prompt one"])
    assert per_example[0] == {
        "example_id": 1, "prompt_excerpt": "prompt one",
        "full_choice": "deceptive", "knockout_choice": "deceptive",
        "full_token_id": 10, "knockout_token_id": 10,
        "status": "stayed_deceptive"}


def test_t9_resolve_null_count_defaults_to_every_drawn_circuit():
    assert K.resolve_null_count(SimpleNamespace(knockout_null_count=None), 50) == 50
    assert K.resolve_null_count(SimpleNamespace(), 50) == 50


def test_t9_resolve_null_count_is_capped_by_the_drawn_set():
    cli = SimpleNamespace(knockout_null_count=100)
    assert K.resolve_null_count(cli, 50) == 50
    assert K.resolve_null_count(cli, 0) == 0
    assert K.resolve_null_count(SimpleNamespace(knockout_null_count=3), 50) == 3
    assert K.resolve_null_count(SimpleNamespace(knockout_null_count=0), 50) == 0


def test_t9_log_excerpts_are_grouped_by_status_and_single_lined():
    per_example, _ = K.flip_audit(
        [audit_row(0, argmax=10, ref=10), audit_row(1, argmax=20, ref=10),
         audit_row(2, argmax=99, ref=10), audit_row(3, argmax=10, ref=10)],
        excerpts=["stayed\n  one", "flipped one", "other one", None])
    grouped = K.KnockoutEvaluation._excerpts_by_status(
        {"per_example": per_example})

    # Newlines collapsed, so one example is one log line; 'other' is not shown,
    # and example 3's missing excerpt drops out rather than printing "None".
    assert grouped == {"stayed_deceptive": [(0, "stayed one")],
                       "flipped_honest": [(1, "flipped one")]}


class NullContext:
    """Only the EvalContext surface `_task_null` touches."""

    def __init__(self, n_random, knockout_null_count=None):
        self.random_indices = list(range(100, 100 + n_random))
        self.random_masks = [{"seed": i} for i in range(n_random)]
        self.cli = SimpleNamespace(knockout_null_count=knockout_null_count,
                                   knockout_granularity="finest")
        self.task = Task()
        self.loaded = []

    @contextlib.contextmanager
    def circuit(self, masks, verify=False):
        self.loaded.append(masks)
        yield None


def test_t9_task_null_evaluates_the_capped_number_of_circuits(monkeypatch):
    monkeypatch.setattr(K, "knockout_masks", lambda masks, granularity: masks)
    monkeypatch.setattr(K, "evaluate_task_metrics",
                        lambda ctx, loader, **kw: {"accuracy": 0.5,
                                                   "logit_diff": 1.0})
    ctx = NullContext(n_random=5, knockout_null_count=3)
    null = K.KnockoutEvaluation()._task_null(ctx, None, None, None,
                                             {"accuracy": 0.9, "logit_diff": 2.0})

    assert null["n"] == 3
    # The first three of the drawn set, carrying the drawn index so the rows
    # join to the wikitext null's rows offline.
    assert [r["index"] for r in null["rows"]] == [100, 101, 102]
    assert ctx.loaded == ctx.random_masks[:3]
    assert null["stats"]["accuracy"]["n"] == 3


def test_t9_task_null_is_empty_and_silent_without_random_circuits(monkeypatch):
    monkeypatch.setattr(K, "evaluate_task_metrics",
                        lambda *a, **kw: pytest.fail("evaluated with no circuits"))
    null = K.KnockoutEvaluation()._task_null(NullContext(n_random=0), None, None,
                                             None, {"accuracy": 0.9})
    assert null == {"n": 0, "granularity": "finest", "rows": [], "stats": {}}


def test_t9_prompt_excerpts_keeps_only_the_tail():
    dataset = SimpleNamespace(processed_data=[{"clean_prompt": "a" * 500}])
    got = K.prompt_excerpts(SimpleNamespace(dataset=dataset), chars=200)
    assert got == ["a" * 200]


def test_t9_prompt_excerpts_follows_a_subset_and_tolerates_missing_prompts():
    records = [{"clean_prompt": f"prompt {i}"} for i in range(4)]
    records[2] = {}                       # a dataset without the prompt field
    subset = SimpleNamespace(dataset=SimpleNamespace(processed_data=records),
                             indices=[2, 3])
    assert K.prompt_excerpts(SimpleNamespace(dataset=subset)) == [None, "prompt 3"]
    # A dataset with no processed_data at all degrades to ids, not a crash.
    assert K.prompt_excerpts(SimpleNamespace(dataset=SimpleNamespace())) is None


# ---- the per-example rows the audit consumes, off a real forward -------------

class PredTask(Task):
    """A pred_spec task over the tiny model: the answer is at the last position."""

    name = "predtask"

    def pred_spec(self, batch):
        return {"pred_pos": batch["prefix_length"] - 1,
                "target": batch["target_token"],
                "distractor": batch["distractor_token"]}


class MetricsContext:
    """Only the EvalContext surface `evaluate_pred_position` touches."""

    def __init__(self, model):
        self.node_model = model
        self.task = PredTask()
        self.device = "cpu"
        self.tokenizer = None
        self.reference_model = None
        # 'shared' means the prunable model with no corrupted stream IS the
        # ungated full model, so the tiny pair needs no second copy.
        self.cli = SimpleNamespace(reference="shared", ref_cache_device="cpu")

    def reference_logits(self, input_ids, attention_mask):
        with torch.no_grad():
            return self.node_model(input_ids=input_ids,
                                   attention_mask=attention_mask,
                                   use_cache=False).logits


def pred_loader(n=6, seq=8, bs=2, seed=3):
    g = torch.Generator().manual_seed(seed)
    rows = [{
        "input_ids": torch.randint(0, VOCAB, (seq,), generator=g),
        "corrupted_input_ids": torch.randint(0, VOCAB, (seq,), generator=g),
        "attention_mask": torch.ones(seq, dtype=torch.long),
        "prefix_length": torch.tensor(seq),
        "target_token": torch.randint(0, VOCAB, (), generator=g),
        "distractor_token": torch.randint(0, VOCAB, (), generator=g),
    } for _ in range(n)]
    return torch.utils.data.DataLoader(rows, batch_size=bs, shuffle=False)


def test_t9_collect_per_example_returns_one_row_per_sample_in_loader_order():
    _, pruned = build_pair()
    out = metrics.evaluate_pred_position(MetricsContext(pruned),
                                         pred_loader(n=6, bs=2),
                                         collect_per_example=True)

    rows = out["per_example"]
    assert len(rows) == out["n"] == 6
    assert [r["index"] for r in rows] == list(range(6))
    for row in rows:
        for key in ("argmax_id", "ref_argmax_id", "target_id", "distractor_id"):
            assert isinstance(row[key], int), key


def test_t9_per_example_reference_argmax_matches_the_reference_cache():
    """The audit's 'full model' column is the same tensor exact_match uses."""
    _, pruned = build_pair()
    ctx = MetricsContext(pruned)
    loader = pred_loader(n=4, bs=2)

    cache = metrics.build_ref_cache(ctx, loader)
    out = metrics.evaluate_pred_position(ctx, loader, ref_cache=cache,
                                         collect_per_example=True)
    expected = cache.float().argmax(dim=-1).tolist()
    assert [r["ref_argmax_id"] for r in out["per_example"]] == expected
    # With all gates open the circuit IS the reference, so every example also
    # reads back as the full model's own choice.
    assert [r["argmax_id"] for r in out["per_example"]] == expected
    assert out["exact_match"] == 1.0


def test_t9_per_example_reference_is_none_without_a_reference():
    _, pruned = build_pair()
    out = metrics.evaluate_pred_position(MetricsContext(pruned),
                                         pred_loader(n=4, bs=2),
                                         use_reference=False,
                                         collect_per_example=True)
    assert all(r["ref_argmax_id"] is None for r in out["per_example"])


def test_t9_per_example_is_absent_unless_asked_for():
    _, pruned = build_pair()
    out = metrics.evaluate_pred_position(MetricsContext(pruned), pred_loader())
    assert "per_example" not in out


# ---- the variant sections, actually executed --------------------------------

class ExcerptDataset(torch.utils.data.Dataset):
    """A pred_spec dataset that also carries `processed_data.clean_prompt`,
    so `prompt_excerpts` runs for real rather than degrading to None."""

    def __init__(self, rows, variant):
        self.rows = rows
        self.processed_data = [
            {"clean_prompt": f"scenario {i} under {variant}. Which do you pick?"}
            for i in range(len(rows))]

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        return self.rows[i]


class VariantContext(MetricsContext):
    """MetricsContext plus the gate plumbing `_variant_side` needs."""

    def __init__(self, model, variants_available=K.VARIANTS):
        super().__init__(model)
        self.has_pred_spec = True
        self.cli.verify = False
        self.circuit_masks = random_masks_for(model, seed=7)
        self.knockout_masks = M.knockout_masks(self.circuit_masks, "finest")
        apply_node_masks(model, self.circuit_masks)
        self.loaders = {
            v: torch.utils.data.DataLoader(
                ExcerptDataset(list(pred_loader(n=4, bs=4).dataset), v),
                batch_size=2, shuffle=False)
            for v in variants_available}

    def variant_loader(self, variant):
        loader = self.loaders.get(variant)
        if loader is None:
            return None, f"the tiny task cannot build '{variant}' prompts"
        return loader, ""

    def hook_for(self, bank_name="task"):
        return None                      # interchange installs no hook

    @contextlib.contextmanager
    def all_gates_open(self):
        open_all_gates(self.node_model)
        try:
            yield self.node_model
        finally:
            apply_node_masks(self.node_model, self.circuit_masks)

    @contextlib.contextmanager
    def circuit(self, masks, verify=False):
        apply_node_masks(self.node_model, masks)
        try:
            yield self.node_model
        finally:
            apply_node_masks(self.node_model, self.circuit_masks)


@pytest.mark.parametrize("variant", K.VARIANTS)
def test_t9_variant_side_runs_three_configurations_and_audits_them(variant):
    """The real `_variant_side`, both variants, on the tiny model.

    The end-to-end task has no pressure clause, so both variants skip there and
    this path — the live full-model reference, the per-example collection under
    a variant, the flip audit off it — is otherwise never executed.
    """
    _, pruned = build_pair()
    ctx = VariantContext(pruned)
    section = K.KnockoutEvaluation()._variant_side(ctx, variant)

    assert section["variant"] == variant
    assert section["description"] == variants.VARIANT_DESCRIPTIONS[variant]
    assert section["label_convention"] == variants.LABEL_CONVENTION
    assert set(section["rows"]) == {"full", "circuit", "knockout"}

    # KL is against a LIVE full-model forward on these prompts, so the
    # all-gates-open row is the reference and must come out exact.
    assert section["rows"]["full"]["exact_match"] == 1.0
    assert section["rows"]["full"]["kl_div"] < 1e-6

    head = section["headline"]
    assert head["full_minus_knockout"] == pytest.approx(
        head["full_accuracy"] - head["knockout_accuracy"])

    # The audit ran off the knockout pass, and its rows did not stay behind in
    # the metrics dict.
    assert "per_example" not in section["rows"]["knockout"]
    per_example = section["per_example"]
    assert len(per_example) == section["rows"]["knockout"]["n"] == 4
    assert [r["example_id"] for r in per_example] == [0, 1, 2, 3]
    for row in per_example:
        assert row["status"] in {"stayed_deceptive", "flipped_honest", "other"}
        # The live reference is available here, so no choice is unobserved.
        assert row["full_choice"] in {"deceptive", "honest", "other"}
        assert variant in row["prompt_excerpt"]

    flips = section["flip_summary"]
    assert (flips["n_stayed_deceptive"] + flips["n_flipped_honest"]
            + flips["n_other"]) == 4
    assert flips["n_full_unknown"] == 0
    assert section["flip_audit_reason"] == ""


def test_t9_variant_side_records_why_it_stood_down():
    _, pruned = build_pair()
    ctx = VariantContext(pruned, variants_available=())
    section = K.KnockoutEvaluation()._variant_side(ctx, "no_pressure")
    assert section == {"variant": "no_pressure",
                       "skipped": "the tiny task cannot build 'no_pressure' "
                                  "prompts"}
