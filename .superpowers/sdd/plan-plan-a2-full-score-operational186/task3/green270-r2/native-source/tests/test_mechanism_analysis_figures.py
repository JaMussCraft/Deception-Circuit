"""Ticket 06 of mechanism-analysis: the synthesis figure builder (docs/research/mechanism-analysis/figures/figures.py).

Seams: each figure's extract function (the rows written to the figure's CSV, read from the curated tables under
docs/research/mechanism-analysis/ and the named reports), and the render step (CSV in, PNG out). Expected values come
from the phase readings (reports/03-*, 04-*, 05-*), not from the code under test. Tests that need the real curated
files or the fetched cells skip when those files are absent.
"""

from __future__ import annotations

import csv
import importlib.util
import os

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MA = os.path.join(REPO, "docs", "research", "mechanism-analysis")
FIGURES_PY = os.path.join(MA, "figures", "figures.py")
REPORTS = "/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports"
P1C_JSON = os.path.join(REPORTS, "03-1c-results.json")
LENS = os.path.join(REPO, "outputs", "_analyses", "mechanism-analysis-p1", "lens", "U__leaf")


@pytest.fixture(scope="module")
def fig():
    spec = importlib.util.spec_from_file_location("ma_figures", FIGURES_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _need(*paths):
    for p in paths:
        if not os.path.exists(p):
            pytest.skip(f"missing input {p}")


def _row(table, **match):
    hits = [r for r in table if all(str(r[k]) == str(v) for k, v in match.items())]
    assert len(hits) == 1, (match, len(hits))
    return hits[0]


# ==============================================================================
# R-AB mediation curves (held-out D, neutral twin, post-clause)
# ==============================================================================

def test_mediation_rows_cover_both_selectors_on_the_pre_registered_k_grid(fig):
    _need(P1C_JSON, os.path.join(MA, "phase1", "rinv.csv"))
    rows = fig.extract_mediation(P1C_JSON, os.path.join(MA, "phase1", "rinv.csv"))
    for task in ("far", "sdr", "ser"):
        single = sorted(int(r["k"]) for r in rows if r["task"] == task and r["selector"] == "single")
        greedy = sorted(int(r["k"]) for r in rows if r["task"] == task and r["selector"] == "greedy")
        assert single == [1, 2, 3, 5, 10, 20, 40, 80]
        assert greedy == [1, 2, 3, 5, 10, 20]


def test_mediation_rows_carry_the_twenty_null_draws_and_the_deciding_set(fig):
    _need(P1C_JSON, os.path.join(MA, "phase1", "rinv.csv"))
    rows = fig.extract_mediation(P1C_JSON, os.path.join(MA, "phase1", "rinv.csv"))
    far = _row(rows, task="far", selector="greedy", k=20)
    # 03-1c-results.md: far greedy k = 20, f_D 0.893 [0.860, 0.927], KO acc 0.000, null f max 0.309
    assert round(float(far["f_D"]), 3) == 0.893
    assert round(float(far["f_lo"]), 3) == 0.860 and round(float(far["f_hi"]), 3) == 0.927
    assert round(float(far["null_f_max"]), 3) == 0.309
    assert int(far["n_null"]) == 20 and len(far["null_f_draws"].split(";")) == 20
    assert float(far["null_f_min"]) <= float(far["null_f_mean"]) <= float(far["null_f_max"])
    assert far["deciding"] is True and far["reading"] == "A'"
    # f_I of the deciding set: rinv.csv option B (03-phase1-reading: far 0.798, sdr 0.309, ser 0.679)
    assert round(float(far["f_I"]), 3) == 0.798
    assert round(float(_row(rows, task="sdr", selector="single", k=20)["f_I"]), 3) == 0.309
    assert round(float(_row(rows, task="ser", selector="greedy", k=20)["f_I"]), 3) == 0.679
    # per-instance ratios (spec 2.3, R11(i)): median and quartiles of the 100 per-instance f, beside the ratio of means
    assert int(far["n_per_instance"]) == 100
    assert float(far["f_pi_q1"]) <= float(far["f_pi_median"]) <= float(far["f_pi_q3"])
    assert abs(float(far["f_pi_median"]) - float(far["f_D"])) < 0.05
    # only one deciding row per task, and no f_I elsewhere
    assert sum(1 for r in rows if r["deciding"] is True) == 3
    assert all(r["f_I"] == "" for r in rows if r["deciding"] is not True)


# ==============================================================================
# R-inv paired contrast
# ==============================================================================

def test_rinv_rows_are_the_three_id_sets_per_task_with_their_labels(fig):
    _need(os.path.join(MA, "phase1", "rinv.csv"))
    rows = fig.extract_rinv(os.path.join(MA, "phase1", "rinv.csv"))
    assert len(rows) == 9
    # 03-phase1-reading.md, R-inv table
    far = _row(rows, task="far", rows="optionB")
    assert (round(float(far["diff"]), 3), round(float(far["diff_lo"]), 3), round(float(far["diff_hi"]), 3)) == (
        0.365, 0.332, 0.393)
    assert far["primary"] is True
    assert _row(rows, task="sdr", rows="r19_robustness")["label"] == "undecided"
    assert _row(rows, task="sdr", rows="r19_robustness")["primary"] is False
    assert int(_row(rows, task="far", rows="r19_robustness")["n"]) == 14


# ==============================================================================
# B2 pressure-reader signature by layer (phase-2 D cells)
# ==============================================================================

def test_b2_rows_reproduce_the_b_reader_counts_of_the_phase2_reading(fig):
    paths = {t: os.path.join(MA, "phase2", f"{t}_d_head_table.csv") for t in ("far", "sdr", "ser")}
    _need(*paths.values())
    rows = fig.extract_b2(paths)
    # 04-phase2-reading.md, B-reader table: signature heads / measured, in layers 8-17
    expected = {"far": (36, 136, 32), "sdr": (36, 126, 34), "ser": (28, 134, 27)}
    for task, (n_sig, n_meas, n_band) in expected.items():
        mine = [r for r in rows if r["task"] == task]
        assert len(mine) == n_meas
        sig = [r for r in mine if r["signature"] is True]
        assert len(sig) == n_sig
        assert sum(1 for r in sig if 8 <= int(r["layer"]) <= 17) == n_band
    l1321 = _row(rows, task="far", label="head.13.21")
    assert round(float(l1321["drop"]), 3) == 0.275 and l1321["signature"] is True
    assert _row(rows, task="far", label="head.13.5")["signature"] is False


# ==============================================================================
# A' adjudication: category shares of the deciding set's head weight (phase 3)
# ==============================================================================

def test_a_prime_shares_reproduce_the_phase3_calls(fig):
    _need(os.path.join(MA, "phase3", "a_prime.csv"))
    rows = fig.extract_a_prime(os.path.join(MA, "phase3", "a_prime.csv"))
    share = {(r["task"], r["category"]): float(r["share"]) for r in rows}
    # 05-review.md: the spec reviewer's recomputation, far kv_clause 0.738, sdr q 0.638, ser kv_clause 0.835
    assert round(share[("far", "kv_clause")], 3) == 0.738
    assert round(share[("sdr", "q")], 3) == 0.638
    assert round(share[("ser", "kv_clause")], 3) == 0.835
    for task, n in (("far", 18), ("sdr", 14), ("ser", 19)):
        mine = [r for r in rows if r["task"] == task]
        assert sum(int(r["n_heads"]) for r in mine) == n
        assert abs(sum(float(r["share"]) for r in mine) - 1.0) < 1e-9
        assert {r["category"] for r in mine} == set(fig.CATEGORIES)
    calls = {r["task"]: r["call"] for r in rows}
    assert calls == {"far": "kv_clause", "sdr": "q", "ser": "kv_clause"}
    status = {r["task"]: r["status"] for r in rows}
    assert status["sdr"].startswith("descriptive") and status["far"].startswith("pre-registered")


# ==============================================================================
# Phase-3 entry paths: where the neutral-twin pressure arrives, and the strongest paths
# ==============================================================================

def test_entry_rows_reproduce_the_b4_table_of_the_phase3_reading(fig):
    _need(os.path.join(MA, "phase3", "entry_paths.csv"))
    rows = fig.extract_entry(os.path.join(MA, "phase3", "entry_paths.csv"))
    got = {(r["task"], r["placement"]): (int(r["n"]), round(float(r["sum_abs"]), 2)) for r in rows}
    # 05-phase3-reading.md section 3 (B4): K/V clause span, post-clause named Segment, post-clause template tokens,
    # and the Q / MLP / Readout receivers
    assert got[("far", "kv_clause")] == (117, 2.84)
    assert got[("far", "kv_post_clause_named")] == (6, 0.08)
    assert got[("far", "kv_post_clause_template")] == (19, 0.48)
    assert got[("sdr", "kv_clause")] == (39, 0.79)
    assert got[("ser", "kv_post_clause_named")] == (17, 0.31)
    for task, n, s in (("far", 160, 5.10), ("sdr", 139, 4.40), ("ser", 177, 5.10)):
        q = sum(got[(task, p)][0] for p in ("q", "mlp_in", "readout"))
        assert q == n
    share = {r["task"]: round(float(r["post_clause_share_of_kv"]), 2) for r in rows}
    assert share == {"far": 0.17, "sdr": 0.44, "ser": 0.21}


def test_route_rows_are_the_strongest_paths_and_hold_the_b_selector_route(fig):
    _need(os.path.join(MA, "phase3", "entry_paths.csv"))
    rows = fig.extract_route(os.path.join(MA, "phase3", "entry_paths.csv"), top=25)
    for task in ("far", "sdr", "ser"):
        mine = [r for r in rows if r["task"] == task]
        assert len(mine) == 25
        mags = [abs(float(r["mean"])) for r in mine]
        assert mags == sorted(mags, reverse=True)
        cells = {r["cell"] for r in mine}
        # 05-phase3-reading.md section 2: L17H24's strongest query input, and L17H24 feeding the L24 queries
        assert "head.17.24->q.24.27" in cells
    assert "head.14.4->q.17.24" in {r["cell"] for r in rows if r["task"] == "far"}
    assert "head.15.8->q.17.24" in {r["cell"] for r in rows if r["task"] == "ser"}
    kv = _row(rows, task="far", cell="mlp.9.0->k.13.5")
    assert kv["receiver_node"] == "kv.13.5" and kv["placement"] == "kv_clause"
    assert _row(rows, task="far", cell="mlp.6.0->mlp_in.8.0")["receiver_node"] == "mlp.8.0"


# ==============================================================================
# C1: cross-task knockout matrix, mean d per composition group
# ==============================================================================

def test_c1_group_means_reproduce_the_phase1b_table(fig):
    _need(os.path.join(MA, "phase1", "c1_matrix.csv"))
    rows = fig.extract_c1(os.path.join(MA, "phase1", "c1_matrix.csv"))
    got = {(r["group"], r["column"]): round(float(r["mean_d"]), 2) for r in rows}
    # 03-1b-results.md, C1 table
    assert got[("core", "far:s1")] == 0.18
    assert got[("MLP", "far:s2")] == 0.71
    assert got[("excl_ser", "far:s2")] == 0.24
    assert got[("excl_far", "far:s5")] == -0.03
    n = {r["group"]: int(r["n"]) for r in rows}
    assert n["outside"] == 901 and n["core"] == 31 and n["MLP"] == 32


# ==============================================================================
# Exclusives: layer bands and what they read
# ==============================================================================

def test_exclusive_rows_hold_the_layer_bands_and_the_sink_count(fig):
    paths = {t: os.path.join(MA, "phase2", f"{t}_d_head_table.csv") for t in ("far", "sdr", "ser")}
    _need(*paths.values())
    rows = fig.extract_exclusives(paths)
    by = {t: [r for r in rows if r["task"] == t] for t in ("far", "sdr", "ser")}
    assert {t: len(v) for t, v in by.items()} == {"far": 8, "sdr": 14, "ser": 10}
    # spec 2.7 C-reads (HB (g)): far 8 of 8 at L9-14, sdr 8 of 14 at L4-5, ser 7 of 10 at L15-16
    assert all(9 <= int(r["layer"]) <= 14 for r in by["far"])
    assert sum(1 for r in by["sdr"] if int(r["layer"]) in (4, 5)) == 8
    assert sum(1 for r in by["ser"] if int(r["layer"]) in (15, 16)) == 7
    # 04-phase2-reading.md section 5: 20 of the 32 put their top mass on the attention sink
    assert sum(1 for r in rows if r["read_group"] == "sink") == 20


# ==============================================================================
# Logit lens (exploratory, R12)
# ==============================================================================

def test_lens_rows_are_the_paired_trajectories_with_their_sign_flip(fig):
    _need(*(os.path.join(LENS, f"{t}_v2", "dla", "logit_lens.json") for t in ("far", "sdr", "ser")))
    rows = fig.extract_lens(LENS)
    far_p = [r for r in rows if r["task"] == "far" and r["condition"] == "D"]
    far_t = [r for r in rows if r["task"] == "far" and r["condition"] == "H"]
    assert len(far_p) == 33 and len(far_t) == 33
    assert [int(r["row"]) for r in far_p] == list(range(33))
    assert {int(r["sign_flip_layer"]) for r in far_p} == {15}
    assert {int(r["sign_flip_layer"]) for r in far_t} == {9}
    assert {r["n"] for r in far_p} == {1000}


# ==============================================================================
# Records: the committed CSVs, the meta file, and render from the CSVs alone
# ==============================================================================

FIG_DIR = os.path.join(MA, "figures")
NAMES = ("fig1_mediation", "fig2_rinv", "fig3_b2_by_layer", "fig4_a_prime", "fig5_entry_paths", "fig6_route",
         "fig7_c1_matrix", "fig8_exclusives", "fig9_lens")


def test_the_registry_names_nine_figures_each_with_a_renderer(fig):
    assert tuple(fig.FIGURES) == NAMES
    assert tuple(fig.RENDER) == NAMES


def test_committed_csvs_match_a_fresh_extraction(fig, tmp_path):
    src = fig.default_sources()
    _need(src["p1c_json"], src["lens_root"], *src["head_tables"].values())
    fig.extract_all(str(tmp_path))
    for name in NAMES:
        with open(os.path.join(FIG_DIR, name + ".csv")) as a, open(os.path.join(str(tmp_path), name + ".csv")) as b:
            assert a.read() == b.read(), name
    with open(os.path.join(FIG_DIR, "figures_meta.json")) as a, open(os.path.join(str(tmp_path), "figures_meta.json")) as b:
        assert a.read() == b.read()


def test_meta_gives_every_figure_its_sources_status_and_caption(fig):
    import json
    with open(os.path.join(FIG_DIR, "figures_meta.json")) as fh:
        meta = json.load(fh)
    assert sorted(meta) == sorted(NAMES)
    for name, m in meta.items():
        assert m["csv"] == name + ".csv" and m["png"] == name + ".png"
        assert m["sources"] and m["status"] and m["caption"]
    assert "EXPLORATORY" in meta["fig9_lens"]["status"] and "EXPLORATORY" in meta["fig6_route"]["status"]


def test_render_draws_every_figure_from_the_committed_csvs_alone(fig, tmp_path):
    import shutil
    for name in NAMES:
        shutil.copy(os.path.join(FIG_DIR, name + ".csv"), str(tmp_path))
    written = fig.render_all(str(tmp_path))
    assert [os.path.basename(p) for p in written] == [n + ".png" for n in NAMES]
    for p in written:
        assert os.path.getsize(p) > 10000
