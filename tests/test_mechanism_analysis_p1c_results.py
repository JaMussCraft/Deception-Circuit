"""Ticket 03 of mechanism-analysis: the phase-1C results builder (outputs/_launch_mechanism_analysis/p1c_results.py).

Seams (spec 2.3, 2.4, R19(3)): the mediated fraction f (ratio of means), test (i) with its null, test (ii) on H and F,
the A / A' / B reading with the deciding set, the paired R-inv label, the S7-vs-S2p "inversion-shared" call and B's
shared-class share.
"""

import importlib
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = os.path.join(REPO, "outputs", "_launch_mechanism_analysis")


@pytest.fixture(scope="module")
def r():
    if LAUNCH not in sys.path:
        sys.path.insert(0, LAUNCH)
    return importlib.import_module("p1c_results")


def test_mediated_fraction_is_a_ratio_of_means(r):
    # clean mean 3, knocked mean 1, twin mean -1: (3 - 1) / (3 - (-1)) = 0.5
    assert r.mediated_fraction([2.0, 4.0], [0.0, 2.0], [-2.0, 0.0]) == pytest.approx(0.5)


def test_two_way_accuracy_counts_positive_margins(r):
    assert r.two_way_accuracy([1.0, -0.5, 0.2, -3.0]) == pytest.approx(0.5)


def test_test_i_needs_low_accuracy_high_f_and_beating_every_null_draw(r):
    assert r.test_i(acc=0.20, f=0.80, null_fs=[0.1, 0.79]) is True
    assert r.test_i(acc=0.30, f=0.80, null_fs=[0.1]) is False          # accuracy above 0.25
    assert r.test_i(acc=0.20, f=0.70, null_fs=[0.1]) is False          # f below 0.75
    assert r.test_i(acc=0.20, f=0.80, null_fs=[0.1, 0.80]) is False    # does not exceed every draw
    assert r.test_i(acc=0.25, f=0.75, null_fs=[0.0]) is True           # edges inclusive


def test_test_ii_bounds_accuracy_and_relative_margin_moves_on_one_set(r):
    assert r.test_ii_one(clean_acc=0.95, ko_acc=0.90, clean_margin=4.0, ko_margin=3.2) is True   # 0.05, 20%
    assert r.test_ii_one(clean_acc=0.95, ko_acc=0.80, clean_margin=4.0, ko_margin=3.9) is False  # 0.15
    assert r.test_ii_one(clean_acc=0.95, ko_acc=0.95, clean_margin=4.0, ko_margin=2.9) is False  # 27.5%
    assert r.test_ii_one(clean_acc=0.95, ko_acc=0.95, clean_margin=4.0, ko_margin=5.1) is False  # moves up 27.5%


def _cand(sel, k, i, ii):
    return {"selector": sel, "k": k, "i": i, "ii": ii}


def test_reading_A_takes_the_smallest_k_meeting_both_with_single_winning_ties(r):
    c = {"single_k5": _cand("single", 5, True, True), "greedy_k5": _cand("greedy", 5, True, True),
         "greedy_k3": _cand("greedy", 3, True, False), "single_k10": _cand("single", 10, True, True)}
    assert r.reading(c) == ("A", "single_k5")


def test_reading_A_prime_when_only_i_holds_and_B_when_nothing_holds(r):
    c = {"single_k3": _cand("single", 3, False, True), "greedy_k10": _cand("greedy", 10, True, False),
         "single_k20": _cand("single", 20, True, False), "single_k40": _cand("single", 40, True, True)}
    assert r.reading(c) == ("A'", "greedy_k10")
    c = {"single_k3": _cand("single", 3, False, True), "single_k40": _cand("single", 40, True, True)}
    assert r.reading(c) == ("B", "single_k20")    # k > 20 never counts; B's descriptive set is single S_20


def test_rinv_label_reads_the_paired_ci_of_f_I_minus_half_f_D(r):
    assert r.rinv_label((0.05, 0.4)) == "instructed inversion machinery"
    assert r.rinv_label((-0.4, -0.05)) == "deception-specific"
    assert r.rinv_label((-0.1, 0.2)) == "undecided"


def test_inversion_shared_needs_both_significant_and_a_ratio_in_half_to_double(r):
    assert r.inversion_shared(d_D=0.2, sig_D=True, d_I=0.3, sig_I=True) is True
    assert r.inversion_shared(d_D=0.2, sig_D=True, d_I=0.5, sig_I=True) is False
    assert r.inversion_shared(d_D=0.2, sig_D=True, d_I=0.3, sig_I=False) is False
    assert r.inversion_shared(d_D=0.2, sig_D=True, d_I=-0.3, sig_I=True) is False


def test_shared_share_is_the_shared_class_part_of_the_positive_top80_effect(r):
    rows = [("a", 1.0, "shared"), ("b", 2.0, "deception-leaning"), ("c", -1.0, "shared"), ("d", 1.0, "shared")]
    assert r.shared_share(rows) == pytest.approx(0.5)


def test_paired_cluster_bootstrap_of_a_constant_difference_has_a_degenerate_ci(r):
    clusters = ["p1", "p1", "p2", "p3"]
    ci = r.paired_cluster_ci(clusters, lambda idx: 0.3, n_boot=50, seed=0)
    assert ci == (pytest.approx(0.3), pytest.approx(0.3))


def test_reading_ignores_the_descriptive_u_only_arm(r):
    c = {"uonly_k1": _cand("uonly", 1, True, True), "single_k5": _cand("single", 5, True, True)}
    assert r.reading(c) == ("A", "single_k5")
    assert r.reading({"uonly_k1": _cand("uonly", 1, True, True)}) == ("B", "single_k20")
