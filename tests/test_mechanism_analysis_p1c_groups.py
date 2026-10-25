"""Ticket 03 of mechanism-analysis: the phase-1C groups builder (outputs/_launch_mechanism_analysis/p1c_groups.py).

Seams (spec 2.3, 4 phase 1C/3; R11): the two selectors' candidate sets S_k, the 20-draw layer-matched null, the
preliminary grid circuit C_t and the routing groups (a)-(c) built from it.
"""

import importlib
import os
import random
import sys
from collections import Counter

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = os.path.join(REPO, "outputs", "_launch_mechanism_analysis")


@pytest.fixture(scope="module")
def g():
    if LAUNCH not in sys.path:
        sys.path.insert(0, LAUNCH)
    return importlib.import_module("p1c_groups")


ALL = [("head", l, h) for l in range(32) for h in range(32)] + [("mlp", l, 0) for l in range(32)]


def _ranking():
    """A fake signed ranking of all 1,056 Components with the layer-0 MLP at rank 1 (it must be skipped)."""
    rest = [k for k in ALL if k != ("mlp", 0, 0)]
    random.Random(3).shuffle(rest)
    return [("mlp", 0, 0)] + rest


def test_single_selector_is_the_signed_top_k_without_the_positive_control(g):
    r = _ranking()
    S = g.single_sets(r, ks=(1, 2, 5))
    assert S[1] == [r[1]] and S[2] == r[1:3] and S[5] == r[1:6]


def test_greedy_selector_is_the_greedy_prefix(g):
    steps = [("head", 17, 24), ("mlp", 14, 0), ("head", 5, 8)]
    assert g.greedy_sets(steps, ks=(1, 2, 3, 5)) == {1: steps[:1], 2: steps[:2], 3: steps}   # k = 5 absent: too short


def test_null_draws_are_layer_and_kind_matched_seeded_and_skip_the_positive_control(g):
    S = [("head", 3, 1), ("head", 3, 7), ("head", 20, 2), ("mlp", 14, 0)]
    draws = g.layer_matched_nulls(S, n=20, seed=11)
    assert len(draws) == 20
    want = Counter((k[0], k[1]) for k in S)
    for d in draws:
        assert Counter((k[0], k[1]) for k in d) == want
        assert len(set(d)) == len(d) and ("mlp", 0, 0) not in d
    assert draws == g.layer_matched_nulls(S, n=20, seed=11)
    assert draws != g.layer_matched_nulls(S, n=20, seed=12)


def test_grid_circuit_adds_the_set_heads_and_fills_mlps_to_ten_set_first(g):
    named = {("head", 1, 1), ("head", 2, 2)}
    S = [("head", 9, 9), ("mlp", 20, 0)]
    r = _ranking()
    C = g.grid_circuit(named, S, r, max_mlps=10)
    mlps = [k for k in C if k[0] == "mlp"]
    assert len(mlps) == 10 and ("mlp", 20, 0) in mlps and ("mlp", 0, 0) not in mlps
    ranked_mlps = [k for k in r[1:] if k[0] == "mlp" and k != ("mlp", 20, 0)][:9]
    assert set(mlps) == {("mlp", 20, 0), *ranked_mlps}
    assert {("head", 1, 1), ("head", 2, 2), ("head", 9, 9)} <= set(C)


def test_routing_groups_split_the_model_around_the_grid_circuit(g):
    C = {("head", 1, 1), ("mlp", 5, 0)}
    a, b, c = g.routing_groups(C)
    assert set(a) == {("mlp", l, 0) for l in range(32)}
    assert set(b) == {k for k in ALL if k[0] == "head"} - C
    assert set(c) == set(ALL) - C and len(c) == 1054


def test_groups_json_keys_are_lists_in_row_key_form(g):
    out = g.to_json({"x": [("head", 3, 1), ("mlp", 2, 0)]})
    assert out == {"x": [["head", 3, 1], ["mlp", 2, 0]]}


def test_paired_strata_counts_the_sampler_strata_and_lists_the_inversion_polarity_subset(g):
    rows = {
        "a": {"designation_polarity": "inversion", "item_polarity": 1, "template_variant": "lab"},
        "b": {"designation_polarity": "identity", "item_polarity": 2, "template_variant": "audit"},
        "c": {"designation_polarity": "inversion", "item_polarity": 2, "template_variant": "lab"},
        "d": {"designation_polarity": "identity", "item_polarity": 1, "template_variant": "lab"},
    }
    s = g.paired_strata(["c", "a", "b"], rows)
    assert s["n"] == 3
    assert s["designation_polarity"] == {"inversion": 2, "identity": 1}
    assert s["item_polarity"] == {"1": 1, "2": 2}
    assert s["template_variant"] == {"lab": 2, "audit": 1}
    assert s["inversion_polarity_ids"] == ["c", "a"]
