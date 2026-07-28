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

import json
import os

import numpy as np
import pytest
import torch

from analysis import (apply_node_masks, assert_masks_equal, extract_node_masks,
                      open_all_gates)
from config import NodePruningConfig
from evaluation import ablation as abl
from evaluation import masks as M
from models.llama_node import (ABLATION_SITES, _ablation_ref,
                               clear_ablation_hook, install_ablation_hook)
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
