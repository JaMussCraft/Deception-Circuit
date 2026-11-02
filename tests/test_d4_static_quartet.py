"""D4(d) static quartet read (`scripts/d4_static_quartet.py`): the low-rank scores against dense matrices, the GQA
slicing, the own-logit rank, the P1 and P2 readings, and the lazy shard reader. CPU only, synthetic weights."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import d4_static_quartet as sq  # noqa: E402

D, R, NH, NKV = 16, 2, 8, 2          # tiny model: 8 query heads, 2 KV groups of 2 dims
GS = NH // NKV


def _weights(seed=0):
    g = torch.Generator().manual_seed(seed)
    return {"q": torch.randn(NH * R, D, generator=g, dtype=torch.float64),
            "k": torch.randn(NKV * R, D, generator=g, dtype=torch.float64),
            "v": torch.randn(NKV * R, D, generator=g, dtype=torch.float64),
            "o": torch.randn(D, NH * R, generator=g, dtype=torch.float64),
            "gamma": torch.rand(D, generator=g, dtype=torch.float64) + 0.5}


def test_ov_factors_slice_the_kv_group_of_the_head_and_fold_gamma():
    w = _weights()
    a, b = sq.ov_factors(w["v"], w["o"], w["gamma"], head=5, d_head=R, group_size=GS)
    g = 5 // GS
    dense = torch.diag(w["gamma"]) @ w["v"][g * R:(g + 1) * R].T @ w["o"][:, 5 * R:6 * R].T
    assert torch.allclose(a @ b, dense)
    # the row-convention OV equals what the model computes for x: o_proj(v_proj(gamma * x)) restricted to head 5
    x = torch.randn(3, D, dtype=torch.float64)
    v = (w["gamma"] * x) @ w["v"].T                             # [3, NKV*R]
    head_v = v[:, g * R:(g + 1) * R]
    out = head_v @ w["o"][:, 5 * R:6 * R].T
    assert torch.allclose(x @ a @ b, out)


def test_q_composition_matches_dense_and_stacks_heads():
    w = _weights(1)
    a, b = sq.ov_factors(w["v"], w["o"], w["gamma"], head=1, d_head=R, group_size=GS)
    qf = sq.q_factor(w["q"], w["gamma"], [4, 5, 6, 7], d_head=R)
    assert qf.shape == (D, 4 * R)
    assert math.isclose(sq.q_composition(a, b, qf), sq.dense_q_composition(a @ b, qf), rel_tol=1e-12)
    single = sq.q_factor(w["q"], w["gamma"], [6], d_head=R)
    assert torch.allclose(single, qf[:, 2 * R:3 * R])


def test_qk_composition_matches_the_dense_elhage_form():
    w = _weights(2)
    a, b = sq.ov_factors(w["v"], w["o"], w["gamma"], head=0, d_head=R, group_size=GS)
    qf = sq.q_factor(w["q"], w["gamma"], [6], d_head=R)
    kf = sq.k_factor(w["k"], w["gamma"], 6, d_head=R, group_size=GS)
    w_qk = qf @ kf
    w_ov = a @ b
    dense = float(torch.linalg.norm(w_ov @ w_qk) / (torch.linalg.norm(w_ov) * torch.linalg.norm(w_qk)))
    assert math.isclose(sq.qk_composition(a, b, qf, kf), dense, rel_tol=1e-10)


def test_q_composition_is_invariant_to_an_orthogonal_rotation_of_the_query_dims():
    w = _weights(3)
    a, b = sq.ov_factors(w["v"], w["o"], w["gamma"], head=2, d_head=R, group_size=GS)
    qf = sq.q_factor(w["q"], w["gamma"], [7], d_head=R)
    theta = 0.7
    rot = torch.tensor([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]],
                       dtype=torch.float64)
    assert math.isclose(sq.q_composition(a, b, qf), sq.q_composition(a, b, qf @ rot), rel_tol=1e-12)


def test_own_logit_ranks_count_strictly_greater_logits():
    w_u = torch.eye(4, dtype=torch.float32)                    # vocab 4, d 4
    resid = torch.tensor([[0.0, 3.0, 1.0, 2.0],                # token 1 is top -> rank 1
                          [5.0, 0.0, 4.0, 1.0]], dtype=torch.float64)   # token 2 is second -> rank 2
    ranks = sq.own_logit_ranks(resid, [1, 2], torch.ones(4, dtype=torch.float64), w_u, chunk=1)
    assert ranks == [1, 2]
    gamma = torch.tensor([1.0, 1.0, 10.0, 1.0], dtype=torch.float64)
    assert sq.own_logit_ranks(resid, [1, 2], gamma, w_u) == [2, 1]
    s = sq.copy_summary([1, 2, 6, 5], k=5)
    assert s["copy_score"] == 0.75 and s["mean_own_rank"] == 3.5


def test_p1_reading_ranks_cutoff_and_layer_sums():
    scores = {f"head.{L}.{h}": 0.01 * h + (0.5 if L in (14, 15) else 0.0) for L in range(7, 17) for h in range(32)}
    scores["head.15.8"] = 5.0
    scores["head.14.4"] = 4.0
    r = sq.p1_reading(scores, named=["head.15.8", "head.14.4"], named_layers=(14, 15), layers=range(7, 17))
    assert r["n_senders"] == 320 and r["top_rank_cutoff"] == 16
    assert r["named_ranks"] == {"head.15.8": 1, "head.14.4": 2}
    assert r["pass"] and r["layer_sum_order"][:2] in ([15, 14], [14, 15])
    scores["head.14.4"] = 0.0
    r = sq.p1_reading(scores, named=["head.15.8", "head.14.4"], named_layers=(14, 15), layers=range(7, 17))
    assert not r["named_in_top"]["head.14.4"] and not r["pass"]


def test_p1_layer_rule_fails_when_another_layer_sum_is_larger():
    scores = {f"head.{L}.{h}": (1.0 if L == 9 else 0.1) for L in range(7, 17) for h in range(32)}
    scores["head.15.8"], scores["head.14.4"] = 9.0, 8.0
    r = sq.p1_reading(scores, named=["head.15.8", "head.14.4"], named_layers=(14, 15), layers=range(7, 17))
    assert all(r["named_in_top"].values())
    assert r["named_layers_exceed_every_other"] == {"14": False, "15": False}
    assert not r["pass"]


def test_p2_reading_needs_two_heads_at_the_bar():
    assert sq.p2_reading({"a": 0.5, "b": 0.49, "c": 0.1, "d": 0.0})["pass"] is False
    assert sq.p2_reading({"a": 0.5, "b": 0.5, "c": 0.1, "d": 0.0})["pass"] is True


def test_random_heads_are_seeded_and_exclude_the_quartet():
    draws = sq.random_heads(17, (24, 25, 26, 27), 20, 4, 123)
    assert draws == sq.random_heads(17, (24, 25, 26, 27), 20, 4, 123)
    assert all(len(set(d)) == 4 and not set(d) & {24, 25, 26, 27} for d in draws)
    (single,) = sq.random_heads(17, (24, 25, 26, 27), 1, 20, 7)
    assert len(set(single)) == 20


def test_lazy_weights_reads_tensors_and_rows_from_a_sharded_checkpoint(tmp_path):
    safetensors_torch = pytest.importorskip("safetensors.torch")
    a = torch.arange(12, dtype=torch.bfloat16).reshape(4, 3)
    b = torch.ones(2, 2, dtype=torch.bfloat16)
    safetensors_torch.save_file({"x.weight": a}, str(tmp_path / "s1.safetensors"))
    safetensors_torch.save_file({"y.weight": b}, str(tmp_path / "s2.safetensors"))
    (tmp_path / "model.safetensors.index.json").write_text(json.dumps(
        {"weight_map": {"x.weight": "s1.safetensors", "y.weight": "s2.safetensors"}}))
    w = sq.LazyWeights(str(tmp_path))
    assert torch.equal(w.get("x.weight", rows=[3, 1]), a[[3, 1]].to(torch.float64))
    assert w.shards_used() == ["s1.safetensors"]
    assert torch.equal(w.get("y.weight", dtype=torch.float32), b.float())
    assert w.shards_used() == ["s1.safetensors", "s2.safetensors"]
    with pytest.raises(KeyError):
        w.get("z.weight")
