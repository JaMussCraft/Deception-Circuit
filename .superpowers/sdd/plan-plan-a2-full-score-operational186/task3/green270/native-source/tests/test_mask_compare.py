"""Tests for evaluation/mask_compare.py."""

from __future__ import annotations

import json

import numpy as np
import pytest

from evaluation import mask_compare as C
from evaluation.masks import as_arrays, as_lists
from tests.test_evaluation import random_masks_for
from tests.helpers import build_tiny_pair


def _payload(masks, heads=None, mlps=None):
    return {
        "active_heads": heads or {},
        "active_mlps": mlps or [],
        "masks": masks,
    }


def test_compare_vectors_identical_and_disjoint():
    a = np.array([1, 1, 0, 0], dtype=np.uint8)
    b = np.array([1, 1, 0, 0], dtype=np.uint8)
    same = C.compare_vectors(a, b)
    assert same["identical"]
    assert same["jaccard"] == 1.0

    c = np.array([0, 0, 1, 1], dtype=np.uint8)
    diff = C.compare_vectors(a, c)
    assert diff["intersection"] == 0
    assert diff["jaccard"] == 0.0
    assert diff["symmetric_diff"] == 4


def test_compare_masks_per_layer():
    _, model = build_tiny_pair()
    m1 = random_masks_for(model, seed=1, density=0.5)
    m2 = random_masks_for(model, seed=2, density=0.5)
    report = C.compare_masks(as_arrays(m1), as_arrays(m2))
    assert not report["problems"]
    for key in ("attention_heads", "attention_neurons", "mlp_hidden", "mlp_output"):
        entry = report["granularities"][key]
        assert entry["compatible"]
        assert 0.0 <= entry["jaccard"] <= 1.0
        assert entry["symmetric_diff"] >= 0


def test_compare_many_intersection():
    _, model = build_tiny_pair()
    masks = [as_arrays(random_masks_for(model, seed=i, density=0.4)) for i in range(3)]
    multi = C.compare_many(masks, keys=["attention_heads"])
    entry = multi["granularities"]["attention_heads"]
    assert entry["compatible"]
    assert entry["all_active"] <= entry["any_active"]


def test_active_summaries():
    payloads = [
        _payload({}, heads={"0": [1, 2], "1": [3]}, mlps=[0, 1]),
        _payload({}, heads={"0": [2], "1": [3, 4]}, mlps=[1, 2]),
    ]
    summary = C.compare_active_summaries(payloads)
    assert summary["attention_heads"]["per_layer"]["0"]["intersection"] == 1
    assert summary["active_mlps"]["intersection"] == 1
    assert summary["active_mlps"]["union"] == 3


def test_load_masks_rejects_missing(tmp_path):
    path = tmp_path / "active_nodes.json"
    path.write_text(json.dumps({"active_heads": {}, "active_mlps": []}))
    with pytest.raises(ValueError, match="no 'masks' key"):
        C.load_masks(str(path))


def test_build_report_from_paths(tmp_path):
    _, model = build_tiny_pair()
    masks = random_masks_for(model, seed=0, density=0.3)
    paths = []
    for i, seed in enumerate((0, 1)):
        p = tmp_path / f"run_{i}" / "active_nodes.json"
        p.parent.mkdir()
        m = masks if seed == 0 else random_masks_for(model, seed=2)
        p.write_text(json.dumps(_payload(as_lists(m))))
        paths.append(str(p.parent))
    report = C.build_report(["a", "b"], paths)
    assert len(report["pairwise"]) == 1
    assert "a vs b" in report["pairwise"]
