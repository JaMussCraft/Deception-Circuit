"""
The B1 readings script (plan ticket 6): `scripts/route_closure_readings.py`.

Synthetic `route_closure.json` payloads only; no model and no torch. The formulas, the
verdicts at their boundaries (0.4999 / 0.5000 and 0.1499 / 0.1500), ruling R1's labels and
the seeded bootstrap clustered by `pressure_id`.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "route_closure_readings.py"


def load_script():
    """The script as a module, loaded by path as the other script tests do."""
    spec = importlib.util.spec_from_file_location("route_closure_readings", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rr = load_script()

N = 8


def payload(*, task="far_v2", m_d=None, m_t=None, arms=None, o=None, o_q=None,
            controls=None, pids=None, estimator="forward", dq=None, o_fwd=None, o_q_fwd=None,
            offline_rule_arms=True):
    """A minimal route_closure.json. Per-instance values default to exact binary fractions.

    `o` and `o_q` are the offline outside sums; the forward ones are `o_fwd` and `o_q_fwd`,
    equal to the offline ones unless given. `estimator="offline"` writes no forward sweep;
    `offline_rule_arms=False` drops the offline T and dq_all (a forward-only file)."""
    m_d = list(m_d or [1.0] * N)
    m_t = list(m_t or [0.0] * N)
    n = len(m_d)
    gap = [a - b for a, b in zip(m_d, m_t)]
    pids = list(pids or [f"p{i % 4}" for i in range(n)])
    arms = dict(arms or {})
    arms.setdefault("q_readout", ("D", [0.75] * n))
    arms.setdefault("k_options", ("D", [0.5] * n))
    arms.setdefault("out_readout", ("D", [0.25] * n))
    arms.setdefault("dq_all", ("D", dq or [0.5] * n))
    o = list(o or [1.0] * n)
    o_q = list(o_q or [0.75] * n)

    def sweep(outside_sum, margins=None):
        return {"per_instance": {"outside_sum": list(outside_sum),
                                 "margins": list(margins or [0.0] * n)},
                "O": sum(outside_sum) / sum(gap)}

    offline = {"T": sweep(o, m_t), "dq_all": sweep(o_q, arms["dq_all"][1])} \
        if offline_rule_arms else {}
    for name, values in (controls or {}).items():
        offline[name] = sweep(values)
    forward = {"T": sweep(list(o_fwd or o), m_t),
               "dq_all": sweep(list(o_q_fwd or o_q), arms["dq_all"][1])}
    return {
        "schema": "route_closure/1", "task": task,
        "instances": {"ids": [f"i{k}" for k in range(n)], "pressure_ids": pids,
                      "without_twin": []},
        "baseline": {"m_D": m_d, "m_T": m_t, "G": gap, "mean_m_D": sum(m_d) / n,
                     "mean_m_T": sum(m_t) / n, "mean_G": sum(gap) / n,
                     "P": sum(m_d) / n - sum(m_t) / n},
        "arms": {name: {"base": base, "margins": list(values),
                        "mean": sum(values) / len(values)}
                 for name, (base, values) in arms.items()},
        "t1": {"sweeps": {"status": "computed",
                          "forward": forward if estimator == "forward" else {},
                          "offline": offline},
               "summary": {"rule_estimator": estimator}},
    }


# ==============================================================================
# FORMULAS
# ==============================================================================

def test_the_share_of_a_restore_and_a_reverse_arm():
    data = payload(m_d=[2.0, 4.0] * 4, m_t=[1.0, 1.0] * 4,
                   arms={"q_readout": ("D", [1.5, 3.0] * 4), "rev_k_options": ("T", [1.5] * 8)})
    p = 2.0   # mean m_D 3.0 minus mean m_T 1.0
    assert rr.arm_share(data, "q_readout") == pytest.approx((3.0 - 2.25) / p)
    assert rr.arm_share(data, "rev_k_options") == pytest.approx((1.5 - 1.0) / p)


def test_m_q_r_q_and_the_t2_shares_as_ratios_of_means():
    data = payload(m_d=[2.0, 4.0] * 4, m_t=[1.0, 1.0] * 4,
                   o=[1.0, 3.0] * 4, o_q=[1.0, 0.5] * 4,
                   arms={"q_readout": ("D", [1.5, 3.0] * 4),
                         "k_options": ("D", [1.0, 2.0] * 4),
                         "out_readout": ("D", [1.0, 1.0] * 4)},
                   dq=[1.0, 3.0] * 4)
    out = rr.read_task(data, n_resamples=50, seed=1)
    assert out["t1"]["M_q"]["point"] == pytest.approx(0.75 / 2.0)
    assert out["t1"]["O"]["point"] == pytest.approx(2.0 / 2.0)
    assert out["t1"]["O_q"]["point"] == pytest.approx(0.75 / 2.0)
    assert out["t1"]["r_q"]["point"] == pytest.approx((3.0 - 2.0) / 2.0)
    assert out["t2"]["r_Q"]["point"] == pytest.approx((3.0 - 2.25) / 2.0)
    assert out["t2"]["r_K"]["point"] == pytest.approx((3.0 - 1.5) / 2.0)
    assert out["t2"]["r_out"]["point"] == pytest.approx((3.0 - 1.0) / 2.0)
    # Per-instance medians: M_q,i = O_q,i / O_i, r_a,i = (m_D,i - m_a,i) / G_i.
    assert out["t1"]["M_q"]["median"] == pytest.approx(np.median([1.0, 0.5 / 3.0] * 4))
    assert out["t2"]["r_Q"]["median"] == pytest.approx(np.median([0.5, 1.0 / 3.0] * 4))
    assert out["t1"]["rule_estimator"] == "offline"


def test_the_offline_estimator_is_used_when_the_forward_sweep_did_not_run():
    data = payload(estimator="offline", o=[2.0] * N, o_q=[1.0] * N)
    for requested in ("offline", "forward"):
        out = rr.read_task(data, n_resamples=10, seed=1, rule_estimator=requested)
        assert out["t1"]["rule_estimator"] == "offline"
        assert out["t1"]["M_q"]["point"] == pytest.approx(0.5)
        assert out["t1"]["beside"] is None
    assert out["t1"]["rule_estimator_fallback"].startswith("forward requested")


# ==============================================================================
# THE RULE ESTIMATOR (ruling R9: offline, forward beside it)
# ==============================================================================

def two_estimators():
    """Offline M_q 0.75 (closes), forward M_q 0.375 (bypass)."""
    return payload(o=[1.0] * N, o_q=[0.75] * N, o_fwd=[2.0] * N, o_q_fwd=[0.75] * N,
                   controls={"c3_push": [0.25] * N})


def test_the_default_rule_estimator_is_offline_with_forward_reported_beside_it():
    out = rr.read_task(two_estimators(), n_resamples=20, seed=1)
    t1 = out["t1"]
    assert rr.DEFAULT_RULE_ESTIMATOR == "offline"
    assert t1["rule_estimator"] == t1["rule_estimator_requested"] == "offline"
    assert t1["rule_estimator_fallback"] is None
    assert t1["O"]["point"] == pytest.approx(1.0)
    assert t1["M_q"]["point"] == pytest.approx(0.75)
    assert t1["verdict"] == "closes"
    beside = t1["beside"]
    assert beside["estimator"] == "forward"
    assert beside["O"]["point"] == pytest.approx(2.0)
    assert beside["O_q"]["point"] == pytest.approx(0.75)
    assert beside["M_q"]["point"] == pytest.approx(0.375)
    assert beside["verdict_if_read_on_it"] == "bypass"
    assert beside["M_q"]["ci95"] is not None


def test_the_forward_setting_reads_the_rule_on_forward_and_reports_offline_beside_it():
    out = rr.read_task(two_estimators(), n_resamples=20, seed=1, rule_estimator="forward")
    t1 = out["t1"]
    assert t1["rule_estimator"] == "forward"
    assert t1["M_q"]["point"] == pytest.approx(0.375)
    assert t1["verdict"] == "bypass" and t1["label"] == "bypass"
    assert t1["beside"]["estimator"] == "offline"
    assert t1["beside"]["M_q"]["point"] == pytest.approx(0.75)
    assert t1["beside"]["verdict_if_read_on_it"] == "closes"
    # The controls stay offline whichever estimator the rule is read on.
    assert t1["controls"]["M_C3"]["point"] == pytest.approx(0.25)
    assert t1["M_q_offline"] == pytest.approx(0.75)


def test_offline_requested_on_a_forward_only_file_falls_back_and_says_so():
    data = payload(o=[1.0] * N, o_q=[0.5] * N, offline_rule_arms=False)
    out = rr.read_task(data, n_resamples=10, seed=1)
    assert out["t1"]["rule_estimator"] == "forward"
    assert out["t1"]["rule_estimator_requested"] == "offline"
    assert out["t1"]["rule_estimator_fallback"] == \
        "offline requested but not in this file; forward used"
    assert out["t1"]["beside"] is None


def test_an_unknown_rule_estimator_is_refused():
    with pytest.raises(ValueError, match="sideways"):
        rr.read_task(two_estimators(), n_resamples=5, seed=1, rule_estimator="sideways")
    with pytest.raises(SystemExit):
        rr.build_parser().parse_args(["x.json", "--rule-estimator", "sideways"])
    assert rr.build_parser().parse_args(["x.json"]).rule_estimator == "offline"


@pytest.mark.parametrize("setting, rule, other", [(None, "offline", "forward"),
                                                  ("forward", "forward", "offline")])
def test_main_names_the_estimator_of_every_t1_number(tmp_path, setting, rule, other):
    path = tmp_path / "route_closure.json"
    path.write_text(json.dumps(two_estimators()))
    out_dir = tmp_path / "out"
    argv = [str(path), "--out-dir", str(out_dir), "--n-resamples", "50"]
    if setting:
        argv += ["--rule-estimator", setting]
    rr.main(argv)
    readings = json.load(open(out_dir / "b1_readings.json"))
    assert readings["rule_estimator"] == rule
    assert readings["tasks"]["far_v2"]["t1"]["rule_estimator"] == rule
    assert readings["tasks"]["far_v2"]["t1"]["beside"]["estimator"] == other
    table = open(out_dir / "b1_readings.md").read()
    # Rows in order: the T1 rule table, the T1 beside table, the T2 table.
    rule_rows = [line for line in table.splitlines() if line.startswith("| far_v2 |")]
    assert len(rule_rows) == 3
    assert rule_rows[0].split("|")[3].strip() == rule
    assert rule_rows[1].split("|")[2].strip() == other
    assert "| task | n | estimator | O | O_q | M_q |" in table
    assert "### T1 on the other estimator, reported beside the rule" in table


def test_an_instance_with_a_vanishing_outside_sum_is_left_out_of_the_median_and_counted():
    data = payload(o=[1.0] * 7 + [0.0], o_q=[0.5] * 8)
    out = rr.read_task(data, n_resamples=10, seed=1)
    assert out["t1"]["M_q"]["median"] == pytest.approx(0.5)
    assert out["t1"]["M_q"]["n_excluded_from_median"] == 1


# ==============================================================================
# VERDICTS AT THEIR BOUNDARIES
# ==============================================================================

@pytest.mark.parametrize("o_q, verdict", [(0.4999, "bypass"), (0.5, "closes")])
def test_the_t1_verdict_closes_at_m_q_0_5000_and_not_at_0_4999(o_q, verdict):
    data = payload(o=[1.0] * N, o_q=[o_q] * N)
    out = rr.read_task(data, n_resamples=10, seed=1)
    assert out["t1"]["verdict"] == verdict
    assert rr.t1_verdict(o_q) == verdict


@pytest.mark.parametrize("r_q, r_k, verdict", [
    (0.2, 0.3499, "indeterminate"), (0.2, 0.35, "key-side"),
    (0.3499, 0.2, "indeterminate"), (0.35, 0.2, "query-side")])
def test_the_t2_verdict_at_0_1499_and_0_1500(r_q, r_k, verdict):
    assert rr.t2_verdict(r_q, r_k, r_out=0.9) == (verdict, verdict)
    data = payload(arms={"q_readout": ("D", [1.0 - r_q] * N),
                         "k_options": ("D", [1.0 - r_k] * N),
                         "out_readout": ("D", [0.1] * N)})
    out = rr.read_task(data, n_resamples=10, seed=1)
    assert out["t2"]["verdict"] == verdict


@pytest.mark.parametrize("r_out, ceiling", [(0.1499, True), (0.15, False)])
def test_a_ceiling_below_0_15_makes_t2_indeterminate(r_out, ceiling):
    verdict, frozen = rr.t2_verdict(0.0, 0.5, r_out=r_out)
    assert frozen == "key-side"
    assert verdict == ("indeterminate, ceiling below 0.15" if ceiling else "key-side")


def test_the_r1_labels():
    assert rr.r1_label(0.8, m_c3=0.65, c1=[0.1, 0.2], c2=[0.3]) == \
        ("closes, route-specific", ["route-specific"])
    assert rr.r1_label(0.8, m_c3=0.6501, c1=[0.1], c2=[0.3]) == \
        ("closes, generic amplification", ["generic amplification"])
    assert rr.r1_label(0.8, m_c3=0.2, c1=[0.1, 0.8], c2=[0.3]) == \
        ("closes, not specific", ["not specific"])
    assert rr.r1_label(0.8, m_c3=0.2, c1=[0.1], c2=[0.9]) == \
        ("closes, not specific", ["not specific"])
    # Both qualifiers: R1's order puts generic amplification first; both are listed.
    assert rr.r1_label(0.8, m_c3=0.7, c1=[0.85], c2=[]) == \
        ("closes, generic amplification", ["generic amplification", "not specific"])
    assert rr.r1_label(0.4999, m_c3=0.0, c1=[], c2=[]) == ("bypass", [])
    assert rr.r1_label(0.8, m_c3=None, c1=[], c2=[]) == \
        ("closes, controls not computed", [])


def test_the_r1_label_is_read_off_the_offline_controls():
    data = payload(o=[1.0] * N, o_q=[0.75] * N,
                   controls={"c1_d0": [0.25] * N, "c2_d0": [0.125] * N,
                             "c3_push": [0.5] * N, "s_k": [0.5] * N})
    out = rr.read_task(data, n_resamples=10, seed=1)
    assert out["t1"]["controls"]["M_C3"]["point"] == pytest.approx(0.5)
    assert out["t1"]["controls"]["M_C1"]["c1_d0"]["point"] == pytest.approx(0.25)
    assert out["t1"]["controls"]["M_S"]["point"] == pytest.approx(0.5)
    assert out["t1"]["label"] == "closes, route-specific"
    assert out["t1"]["M_q_minus_M_C3"]["point"] == pytest.approx(0.25)


# ==============================================================================
# THE CLUSTERED BOOTSTRAP
# ==============================================================================

def test_the_bootstrap_resamples_whole_pressure_clusters_and_is_seeded():
    pids = ["a", "a", "b", "c", "c", "c", None, None]
    first = rr.cluster_resamples(pids, n_resamples=200, seed=20261101)
    again = rr.cluster_resamples(pids, n_resamples=200, seed=20261101)
    other = rr.cluster_resamples(pids, n_resamples=200, seed=7)
    assert len(first) == 200
    assert all(np.array_equal(x, y) for x, y in zip(first, again))
    assert not all(np.array_equal(x, y) for x, y in zip(first, other))
    members = {"a": {0, 1}, "b": {2}, "c": {3, 4, 5}, "n6": {6}, "n7": {7}}
    for sample in first:
        counts = {k: int(np.sum(np.isin(sample, sorted(v)))) for k, v in members.items()}
        # A drawn cluster comes whole: every member the same number of times.
        for k, v in members.items():
            per = [int(np.sum(sample == i)) for i in v]
            assert len(set(per)) == 1, (k, per)
        # Five clusters (each None is its own) are drawn per resample.
        assert sum(counts[k] // len(members[k]) for k in members) == 5
    # The draw is numpy's default_rng over the sorted cluster labels.
    rng = np.random.default_rng(20261101)
    labels = rr.cluster_labels(pids)
    order = sorted(set(labels))
    picks = rng.integers(0, len(order), size=len(order))
    want = np.concatenate([np.flatnonzero(np.array(labels) == order[p]) for p in picks])
    assert np.array_equal(first[0], want)


def test_the_bootstrap_interval_is_reproducible_and_brackets_the_point():
    data = payload(o=[1.0, 2.0, 1.5, 0.5, 1.0, 2.0, 1.5, 0.5],
                   o_q=[0.5, 1.5, 0.5, 0.25, 0.75, 1.0, 1.0, 0.5])
    one = rr.read_task(data, n_resamples=2000, seed=20261101)
    two = rr.read_task(data, n_resamples=2000, seed=20261101)
    lo, hi = one["t1"]["M_q"]["ci95"]
    assert (lo, hi) == tuple(two["t1"]["M_q"]["ci95"])
    assert lo <= one["t1"]["M_q"]["point"] <= hi and lo < hi
    assert one["bootstrap"] == {"n_resamples": 2000, "seed": 20261101,
                                "cluster": "pressure_id", "n_clusters": 4}


# ==============================================================================
# THE SCRIPT
# ==============================================================================

def test_main_writes_the_json_and_the_markdown_table(tmp_path):
    paths = []
    for task in ("far_v2", "ser_v2"):
        cell = tmp_path / task / "route_closure"
        cell.mkdir(parents=True)
        path = cell / "route_closure.json"
        path.write_text(json.dumps(payload(task=task, controls={"c3_push": [0.5] * N})))
        paths.append(str(path))
    out_dir = tmp_path / "results"
    rr.main([*paths, "--out-dir", str(out_dir), "--n-resamples", "100"])
    readings = json.load(open(out_dir / "b1_readings.json"))
    assert set(readings["tasks"]) == {"far_v2", "ser_v2"}
    assert readings["bootstrap"]["seed"] == 20261101
    assert readings["inputs"][0]["path"] == paths[0]
    assert len(readings["inputs"][0]["sha256"]) == 64
    table = open(out_dir / "b1_readings.md").read()
    assert "| far_v2 |" in table and "| ser_v2 |" in table
    assert "M_q" in table and "r_K - r_Q" in table


def test_a_skipped_cell_is_refused_by_path(tmp_path):
    path = tmp_path / "route_closure.json"
    path.write_text(json.dumps({"schema": "route_closure/1", "task": "far",
                                "skipped": "no instance has a twin"}))
    with pytest.raises(SystemExit, match="skipped"):
        rr.main([str(path), "--out-dir", str(tmp_path / "out")])
