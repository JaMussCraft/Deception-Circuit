"""Ticket 03 of mechanism-analysis: the phase-1 reading rules in outputs/_launch_mechanism_analysis/p1_readings.py.

Seams: R-cls (spec 2.2, amended per R16: signed d, five classes checked in order, the upper-95%-bound clause), the
significance rule of docs/component-roles.md (|drop| >= 2 SE and >= 0.01 logits), and the d = drop / clean margin
normalisation in each test set's own target direction.
"""

import importlib
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = os.path.join(REPO, "outputs", "_launch_mechanism_analysis")


@pytest.fixture(scope="module")
def rd():
    if LAUNCH not in sys.path:
        sys.path.insert(0, LAUNCH)
    return importlib.import_module("p1_readings")


def E(drop, se, clean=2.0):
    """One sweep entry: the knockout drop and its SE in logits, and the test set's clean margin."""
    return {"drop": drop, "se": se, "clean": clean}


# ---------------------------------------------------------------- significance: |drop| >= 2 SE and >= 0.01 logits

@pytest.mark.parametrize("drop, se, sign", [
    (0.30, 0.10, +1), (-0.30, 0.10, -1), (0.19, 0.10, 0),     # under 2 SE
    (0.008, 0.001, 0),                                         # 8 SE but under 0.01 logits
    (0.20, 0.10, +1),                                          # edges inclusive
])
def test_significance_needs_two_se_and_a_hundredth_of_a_logit(rd, drop, se, sign):
    assert rd.significant_sign(E(drop, se)) == sign


# ---------------------------------------------------------------- R-cls, checked in order (spec 2.2)
# d = drop / clean. Below clean = 2.0 everywhere, so d = drop / 2.

def test_opposes_wins_over_everything(rd):
    assert rd.rcls(D=E(-0.4, 0.1), H=E(0.8, 0.1), F=E(0.8, 0.1))["class"] == "opposes"


def test_shared_when_d_and_the_honest_side_are_within_a_factor_two(rd):
    # d(D) = 0.3, m_HF = max(0.25, 0.1) = 0.25; ratio 1.2
    assert rd.rcls(D=E(0.6, 0.1), H=E(0.5, 0.1), F=E(0.2, 0.05))["class"] == "shared"


def test_deception_leaning_needs_twice_the_upper_bound(rd):
    # d(D) = 0.5; H d = 0.05, SE_d = 0.02 -> U = 0.05 + 1.96 * 0.02 = 0.0892; F non-significant small.
    out = rd.rcls(D=E(1.0, 0.1), H=E(0.1, 0.04), F=E(0.02, 0.04))
    assert out["class"] == "deception-leaning"
    assert out["U_HF"] == pytest.approx(0.0892)


def test_a_large_noisy_honest_side_blocks_deception_leaning(rd):
    # d(D) = 0.5, H not significant (drop 0.3 < 2 * 0.2) but U = 0.15 + 1.96 * 0.1 = 0.346 > 0.25
    assert rd.rcls(D=E(1.0, 0.1), H=E(0.3, 0.2), F=E(0.0, 0.05))["class"] == "none"


def test_honest_leaning(rd):
    # d(D) = 0.05 (not significant), F d = 0.4 significant
    assert rd.rcls(D=E(0.1, 0.1), H=E(0.0, 0.05), F=E(0.8, 0.1))["class"] == "honest-leaning"


def test_shared_band_edges_and_the_gap_between_shared_and_leaning(rd):
    # d(D) = 0.5, m_HF = 0.24 -> ratio 2.083 (> 2, not shared); U = 0.24 + 1.96*0.025 = 0.289 -> 2U = 0.578 > 0.5
    out = rd.rcls(D=E(1.0, 0.1), H=E(0.48, 0.05), F=E(0.0, 0.05))
    assert out["class"] == "none"
    assert out["reason"]                                   # the sub-reason is reported


def test_negative_honest_side_is_floored_at_zero(rd):
    # H and F significantly negative: m_HF = 0, U = max(d + 1.96 SE, 0) = 0 -> deception-leaning
    assert rd.rcls(D=E(0.6, 0.1), H=E(-0.6, 0.1), F=E(-0.4, 0.1))["class"] == "deception-leaning"


# ---------------------------------------------------------------- C-own (spec 2.7): one-sided sign test, Holm over tasks

def test_sign_test_matches_the_spec_minimum_for_eight_heads(rd):
    assert rd.sign_test_p(8, 8) == pytest.approx(0.00390625)       # "far's 8 heads give a minimum p of 0.004"
    assert rd.sign_test_p(7, 8) == pytest.approx(9 / 256)
    assert rd.sign_test_p(0, 8) == pytest.approx(1.0)


def test_holm_adjusts_in_step_down_order_and_stays_monotone(rd):
    adj = rd.holm({"far": 0.004, "sdr": 0.03, "ser": 0.02})
    assert adj == pytest.approx({"far": 0.012, "sdr": 0.04, "ser": 0.04})


def test_c_own_counts_heads_whose_home_effect_beats_both_other_tasks(rd):
    d = {"L1H1": {"far": 0.3, "sdr": 0.1, "ser": 0.2},
         "L1H2": {"far": 0.1, "sdr": 0.2, "ser": 0.0},
         "L1H3": {"far": 0.2, "sdr": 0.2, "ser": 0.0}}    # a tie is not "exceeds"
    out = rd.c_own("far", d)
    assert (out["k"], out["n"]) == (1, 3)
    assert out["own"] == {"L1H1": True, "L1H2": False, "L1H3": False}


# ---------------------------------------------------------------- R-lens CIs: bootstrap clustered by pressure_id (R12)

def test_cluster_bootstrap_resamples_clauses_not_instances(rd):
    # a: clause x has 99 honest-first instances, clause y one that is not. Resampling clauses can draw (y, y), a rate
    # of 0, with probability 1/4, so the 95% CI must reach down to 0; an instance bootstrap would stay near 0.99.
    a = [("x", 1)] * 99 + [("y", 0)]
    b = [("z", 0)] * 50
    out = rd.cluster_bootstrap_diff(a, b, n_boot=2000, seed=0)
    assert out["diff"] == pytest.approx(0.99)
    assert out["ci"][0] <= 1e-9 and out["ci"][1] == pytest.approx(1.0)
    assert out["n_clusters"] == (2, 1)


def test_cluster_bootstrap_is_seeded(rd):
    a = [(f"c{i % 5}", i % 3 == 0) for i in range(60)]
    b = [(f"d{i % 4}", i % 2 == 0) for i in range(40)]
    assert rd.cluster_bootstrap_diff(a, b, seed=7) == rd.cluster_bootstrap_diff(a, b, seed=7)


def test_rcls_reports_d_and_h_f_significance_for_opposes(rd):
    out = rd.rcls(D=E(-0.4, 0.1), H=E(0.8, 0.1), F=E(0.0, 0.1))
    assert out["d"] == {"D": pytest.approx(-0.2), "H": pytest.approx(0.4), "F": pytest.approx(0.0)}
    assert out["sig"] == {"D": -1, "H": 1, "F": 0}
