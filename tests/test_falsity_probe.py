"""Tests for the B2 P1 falsity probe (instructed-route ticket T7).

`component_analysis/probe.py` holds the pure pieces (standardisation, LBFGS logistic regression, Mann-Whitney AUROC,
the clustered bootstrap, the permutation swaps, the bands and the R2 label). `scripts/falsity_probe.py` runs `fit`,
`score` and `read` over a capture directory in the T6 format, which the fixture below writes by hand following the
module docstring of `scripts/falsity_probe_capture.py`.
"""

import importlib.util
import json
import os
import subprocess
import sys

import numpy as np
import pytest
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from component_analysis import probe  # noqa: E402

SCRIPT = os.path.join(ROOT, "scripts", "falsity_probe.py")


def load_script():
    spec = importlib.util.spec_from_file_location("falsity_probe_t7", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fp():
    return load_script()


# ==============================================================================
# AUROC
# ==============================================================================

def test_auroc_matches_hand_values_with_ties():
    # pos {1, 2, 2}, neg {2, 0}: pairs (1>2? no, 1>0 yes), (2 vs 2 tie, 2>0), (2 vs 2 tie, 2>0)
    # wins 1 + (0.5 + 1) + (0.5 + 1) = 4 of 6.
    assert probe.auroc([1, 2, 2], [2, 0]) == pytest.approx(4 / 6)
    # every value tied: 0.5
    assert probe.auroc([3, 3], [3, 3, 3]) == pytest.approx(0.5)
    # pos {0, 1}, neg {1}: 0 < 1 loses, 1 = 1 ties -> 0.5 / 2
    assert probe.auroc([0, 1], [1]) == pytest.approx(0.25)


def test_auroc_is_one_when_separable_zero_when_reversed_and_half_when_equal():
    assert probe.auroc([5, 6, 7], [1, 2]) == 1.0
    assert probe.auroc([1, 2], [5, 6, 7]) == 0.0
    x = np.arange(10.0)
    assert probe.auroc(x, x) == pytest.approx(0.5)


def test_auroc_agrees_with_the_pairwise_count_on_random_data():
    rng = np.random.default_rng(3)
    pos = np.round(rng.normal(0.3, 1, 37), 1)
    neg = np.round(rng.normal(0.0, 1, 41), 1)
    wins = (pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()
    assert probe.auroc(pos, neg) == pytest.approx(wins / (37 * 41), abs=1e-12)


def test_auroc_refuses_empty_or_nonfinite_input():
    with pytest.raises(ValueError):
        probe.auroc([], [1.0])
    with pytest.raises(ValueError):
        probe.auroc([np.nan, 1.0], [0.0])


# ==============================================================================
# STANDARDISATION, FIT, MASS-MEAN
# ==============================================================================

def test_standardise_uses_the_fit_rows_and_guards_a_constant_feature():
    X = np.array([[1.0, 5.0], [3.0, 5.0]])
    mean, std = probe.standardise_fit(X)
    assert mean.tolist() == [2.0, 5.0]
    assert std.tolist() == [1.0, 1.0]  # the constant feature's 0 becomes 1
    Z = probe.standardise_apply(np.array([[4.0, 7.0]]), mean, std)
    assert Z.tolist() == [[2.0, 2.0]]


def test_the_fit_recovers_a_planted_direction():
    rng = np.random.default_rng(0)
    d, n = 40, 3000
    u = rng.normal(size=d)
    u /= np.linalg.norm(u)
    X = rng.normal(size=(n, d))
    y = (rng.random(n) < 1 / (1 + np.exp(-3 * X @ u))).astype(float)
    fit = probe.fit_logistic(X, y, C=1.0)
    w = fit["w"]
    assert float(w @ u / np.linalg.norm(w)) > 0.9
    assert fit["converged"]


def test_stronger_regularisation_shrinks_the_weights():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(200, 10))
    y = (X[:, 0] > 0).astype(float)
    small = np.linalg.norm(probe.fit_logistic(X, y, C=1e-3)["w"])
    large = np.linalg.norm(probe.fit_logistic(X, y, C=1.0)["w"])
    assert small < large


def test_mass_mean_is_the_difference_of_class_means():
    X = np.array([[1.0, 0.0], [3.0, 0.0], [0.0, 1.0], [0.0, 3.0]])
    y = np.array([1, 1, 0, 0])
    assert probe.mass_mean(X, y).tolist() == [2.0, -2.0]


# ==============================================================================
# BANDS, GATE, R2
# ==============================================================================

@pytest.mark.parametrize("value,band", [
    (1.0, "misleadingness"), (0.75, "misleadingness"), (0.7499, "indeterminate"),
    (0.6, "indeterminate"), (0.5999, "literal_falsity"), (0.5, "literal_falsity"),
    (0.3, "literal_falsity"),
])
def test_the_bands_split_at_075_and_06(value, band):
    assert probe.band(value) == band


def test_an_auroc_under_half_is_literal_falsity_and_flagged_anti_aligned():
    assert probe.anti_aligned(0.4999)
    assert not probe.anti_aligned(0.5)
    assert probe.band(0.4999) == "literal_falsity"


def test_the_fallback_flag_sets_below_a_075_far_gate():
    assert probe.gate_fallback(0.7499)
    assert not probe.gate_fallback(0.75)
    assert not probe.gate_fallback(0.9)


def test_a_ci_crossing_a_band_edge_is_flagged():
    assert probe.ci_band_edges_crossed(0.70, 0.80) == [0.75]
    assert probe.ci_band_edges_crossed(0.55, 0.80) == [0.6, 0.75]
    assert probe.ci_band_edges_crossed(0.76, 0.90) == []
    assert probe.ci_band_edges_crossed(0.60, 0.70) == []  # 0.6 is inside the indeterminate band


def test_the_r2_label_logic():
    under = {"far_I": 0.55, "far_HI": 0.5, "ser_HI": 0.59}
    assert probe.r2_label("misleadingness", under) == "clean"
    for cell in under:
        over = dict(under, **{cell: 0.6})
        assert probe.r2_label("misleadingness", over) == "instruction-confounded"
    assert probe.r2_label("indeterminate", under) is None
    assert probe.r2_label("literal_falsity", under) is None
    with pytest.raises(KeyError):
        probe.r2_label("misleadingness", {"far_I": 0.5, "far_HI": 0.5})


# ==============================================================================
# BOOTSTRAP AND PERMUTATION
# ==============================================================================

def test_the_cluster_bootstrap_is_seed_deterministic_and_resamples_clusters():
    clusters = np.array(["a", "a", "b", "b", "c", "c", "d"])
    values = np.array([1.0, 1.0, 2.0, 2.0, 3.0, 3.0, 4.0])
    stat = (lambda idx: float(values[idx].mean()))
    one = probe.cluster_bootstrap(stat, clusters, n_resamples=300, seed=20261101)
    two = probe.cluster_bootstrap(stat, clusters, n_resamples=300, seed=20261101)
    other = probe.cluster_bootstrap(stat, clusters, n_resamples=300, seed=7)
    assert np.array_equal(one, two)
    assert not np.array_equal(one, other)
    assert one.shape == (300,)

    seen = []
    probe.cluster_bootstrap(lambda idx: seen.append(sorted(idx.tolist())) or 0.0, clusters, n_resamples=50, seed=1)
    for idx in seen:  # every draw takes whole clusters: a and b and c come in pairs
        for pair in ([0, 1], [2, 3], [4, 5]):
            assert idx.count(pair[0]) == idx.count(pair[1])


def test_percentile_ci():
    lo, hi = probe.percentile_ci(np.arange(1001.0))
    assert lo == pytest.approx(25.0)
    assert hi == pytest.approx(975.0)


def test_the_permutation_swaps_are_seeded_and_about_half():
    one = probe.permutation_swaps(400, 20, seed=5)
    assert one.shape == (20, 400) and one.dtype == bool
    assert np.array_equal(one, probe.permutation_swaps(400, 20, seed=5))
    assert 0.4 < one.mean() < 0.6


# ==============================================================================
# SELECTION
# ==============================================================================

def test_selection_takes_the_best_c_per_row_then_the_layer_nearest_17_within_0005(fp):
    rows, n_c = 33, 4
    table = np.full((rows, n_c), 0.80)
    table[10, 2] = 0.999       # layer 9: the global best
    table[22, 1] = 0.996       # layer 21: within 0.005, distance 4
    table[16, 0] = 0.9945      # layer 15: within 0.005, distance 2
    table[16, 3] = 0.9945      # same row, larger C ties: the smaller C wins
    table[2, 0] = 1.0          # layer 1: ineligible
    sel = fp.select_from_table(table, fp.C_GRID)
    assert sel["row"] == 16 and sel["layer"] == 15
    assert sel["C"] == fp.C_GRID[0]
    assert sel["auroc"] == pytest.approx(0.9945)
    assert sel["best_auroc"] == pytest.approx(0.999)

    table[18, 1] = 0.9941      # layer 17 itself, within 0.005
    assert fp.select_from_table(table, fp.C_GRID)["layer"] == 17


def test_selection_never_offers_rows_outside_layers_4_to_31(fp):
    table = np.full((33, 4), 0.5)
    table[4, 0] = 1.0  # layer 3
    table[0, 0] = 1.0  # the embedding
    sel = fp.select_from_table(table, fp.C_GRID)
    assert 4 <= sel["layer"] <= 31 and sel["row"] == sel["layer"] + 1
    table[:, :] = 0.5
    table[32, 3] = 0.9  # layer 31 is eligible
    assert fp.select_from_table(table, fp.C_GRID)["layer"] == 31


def _meta(role, task, split, condition):
    return {"role": role, "task": task, "split": split, "condition": condition, "instance_id": "x"}


def test_selection_raises_on_any_ser_or_far_test_row(fp):
    good = [_meta("select", "far_v2", "validation", c) for c in ("D", "H", "HI")]
    fp.check_selection_rows(good)
    for bad in (_meta("ser_test", "ser_v2", "test", "D"), _meta("far_gate", "far_v2", "test", "H"),
                _meta("select", "ser_v2", "validation", "D"), _meta("select", "far_v2", "test", "D"),
                _meta("sdr", "sdr_v2", "test", "D"), _meta("fit", "far_v2", "train", "D")):
        with pytest.raises(ValueError):
            fp.check_selection_rows(good + [bad])


def test_selection_scores_raise_when_a_ser_row_is_passed(fp):
    good = [_meta("select", "far_v2", "validation", c) for c in ("D", "H", "HI")]
    scores = np.zeros((3, 33, 4))
    fp.selection_table(good, scores)
    with pytest.raises(ValueError):
        fp.selection_table(good + [_meta("ser_test", "ser_v2", "test", "H")], np.zeros((4, 33, 4)))


def test_the_fit_refuses_anything_but_far_train_rows(fp):
    with pytest.raises(ValueError):
        fp.check_fit_rows([_meta("fit", "far_v2", "train", "D"), _meta("select", "far_v2", "validation", "H")])
    with pytest.raises(ValueError):
        fp.check_fit_rows([_meta("fit", "far_v2", "train", "HI")])
    fp.check_fit_rows([_meta("fit", "far_v2", "train", "D"), _meta("fit", "far_v2", "train", "H")])


# ==============================================================================
# NO SKLEARN, NO SCIPY
# ==============================================================================

def test_the_module_and_script_import_without_sklearn_or_scipy():
    code = (
        "import sys, importlib.abc\n"
        "class Block(importlib.abc.MetaPathFinder):\n"
        "    def find_spec(self, name, path, target=None):\n"
        "        if name.split('.')[0] in ('sklearn', 'scipy'):\n"
        "            raise ImportError('blocked ' + name)\n"
        "sys.meta_path.insert(0, Block())\n"
        f"sys.path.insert(0, {ROOT!r})\n"
        "import component_analysis.probe\n"
        "import importlib.util\n"
        f"spec = importlib.util.spec_from_file_location('fp', {SCRIPT!r})\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "print('ok')\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip().endswith("ok")


# ==============================================================================
# A SYNTHETIC CAPTURE DIRECTORY IN THE T6 FORMAT
# ==============================================================================

HIDDEN = 6
N_LAYERS = 32
KEYS = [["embed", 0, 0]] + [[kind, layer, index] for layer in range(N_LAYERS)
                            for kind, index in ([("head", h) for h in range(32)] + [("mlp", 0)])]
CLAUSES = {"far_v2": [f"far_c{i}" for i in range(4)], "ser_v2": [f"ser_c{i}" for i in range(5)],
           "sdr_v2": [f"sdr_c{i}" for i in range(3)]}
CELLS = [  # name, role, task, condition, split, n
    ("far_fit_D", "fit", "far_v2", "D", "train", 48), ("far_fit_H", "fit", "far_v2", "H", "train", 48),
    ("far_select_D", "select", "far_v2", "D", "validation", 32),
    ("far_select_H", "select", "far_v2", "H", "validation", 32),
    ("far_select_HI", "select", "far_v2", "HI", "validation", 32),
    ("far_gate_D", "far_gate", "far_v2", "D", "test", 40), ("far_gate_H", "far_gate", "far_v2", "H", "test", 40),
    ("far_gate_HI", "far_gate", "far_v2", "HI", "test", 40), ("far_gate_F", "far_gate", "far_v2", "F", "test", 40),
    ("far_gate_I", "far_gate", "far_v2", "I", "test", 12),
    ("ser_test_D", "ser_test", "ser_v2", "D", "test", 40), ("ser_test_H", "ser_test", "ser_v2", "H", "test", 40),
    ("ser_test_HI", "ser_test", "ser_v2", "HI", "test", 36), ("ser_test_F", "ser_test", "ser_v2", "F", "test", 40),
    ("ser_test_I", "ser_test", "ser_v2", "I", "test", 10),
    ("sdr_test_D", "sdr", "sdr_v2", "D", "test", 24), ("sdr_test_H", "sdr", "sdr_v2", "H", "test", 24),
    ("sdr_test_I_reported", "sdr", "sdr_v2", "I_reported", "test", 12),
]
#: The planted shift along the falsity axis, per (task, condition). D carries it on FAR and SER; nothing else does,
#: so the probe should be a clean misleadingness probe on this capture.
SHIFT = {("far_v2", "D"): 3.0, ("ser_v2", "D"): 3.0, ("sdr_v2", "D"): 1.0}


def _ids(task, split, n):
    return [f"{task}-{split}-{i:03d}" for i in range(n)]


def _quartet_index():
    return [KEYS.index(["head", 17, h]) for h in range(24, 28)]


def write_capture(directory, *, gate_shift=None, seed=11):
    """Write a capture in the T6 format with a planted direction on axis 0, from layer 4 onwards."""
    rng = np.random.default_rng(seed)
    os.makedirs(directory, exist_ok=True)
    for name, role, task, condition, split, n in CELLS:
        ids = _ids(task, split, n)
        if condition in ("I", "I_reported"):
            ids = _ids(task, split, 40 if task != "sdr_v2" else 24)[:n]
        shift = SHIFT.get((task, condition), 0.0)
        if gate_shift is not None and (task, condition, role) == ("far_v2", "D", "far_gate"):
            shift = gate_shift
        resid = rng.normal(size=(n, N_LAYERS + 1, HIDDEN))
        resid[:, 5:, 0] += shift
        rows = []
        for i, one in enumerate(ids):
            clause = CLAUSES[task][int(one[-3:]) % len(CLAUSES[task])]
            row = {"row": i, "cell": name, "role": role, "task": task, "condition": condition, "split": split,
                   "prompt_field": "honest_instruction_clean_prompt" if condition == "HI" else "clean_prompt",
                   "instance_id": one, "pressure_id": clause if condition != "F" else clause,
                   "pressure": "" if condition == "F" else f"clause {clause}", "framing_id": "f",
                   "instructed_inversion_id": "inv" if condition.startswith("I_") or condition == "I" else None,
                   "items": ["a", "b"], "item_token_ids": [10, 11], "honest_item_index": 0,
                   "honest_item": "a", "deceptive_item": "b", "honest_token": 10, "deceptive_token": 11,
                   "target_item": "a", "distractor_item": "b", "target_token": 10, "distractor_token": 11,
                   "prefix_length": 9, "readout": 8, "model_margin": 0.0, "model_honest_margin": 0.0,
                   "dataset_margin": 0.0, "dataset_margin_field": "clean_margin", "clean_margin": 0.0,
                   "keep_if_value": 0.5 if condition == "HI" else None,
                   "in_seed0_sample": task == "sdr_v2" and condition == "I_reported" and i == 0,
                   "in_seed1_sample": task == "sdr_v2" and condition == "I_reported" and i == 1}
            rows.append(row)
        with open(os.path.join(directory, f"rows.{name}.jsonl"), "w") as handle:
            handle.write("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
        torch.save({"ids": ids, "readout": torch.full((n,), 8, dtype=torch.long),
                    "resid": torch.tensor(resid, dtype=torch.float16)},
                   os.path.join(directory, f"resid.{name}.pt"))
        # Per-token DLA: the quartet writes +1 on the deceptive item and -0.5 on the honest item under D only,
        # mlp.31 writes +0.2 on the honest item on every row, and the embedding carries noise.
        dla = np.zeros((n, len(KEYS), 2), dtype=np.float32)
        dla[:, 0, :] = rng.normal(scale=0.1, size=(n, 2))
        dla[:, KEYS.index(["mlp", 31, 0]), 0] = 0.2
        if condition == "D":
            for k in _quartet_index():
                dla[:, k, 1] += 0.25
                dla[:, k, 0] -= 0.125
        centred = dla.sum(1)
        torch.save({"ids": ids, "token_order": ["honest", "deceptive"],
                    "token_ids": torch.tensor([[10, 11]] * n, dtype=torch.long).reshape(-1, 2),
                    "logits_raw": torch.tensor(centred + 5.0), "logits_logsoftmax": torch.tensor(centred - 3.0),
                    "logits_centred": torch.tensor(centred), "keys": KEYS,
                    "dla": torch.tensor(dla), "dla_centre": True},
                   os.path.join(directory, f"tokens.{name}.pt"))
    plan = {"schema": "falsity-probe-capture/1", "cells": {
        name: {"spec": {"role": role, "task": task, "condition": condition, "split": split}, "n_rows": n,
               "report": ({"kept_share": 0.9, "n_kept_by_filter": n, "n_before_filter": n + 4}
                          if condition == "HI" else {})}
        for name, role, task, condition, split, n in CELLS}}
    with open(os.path.join(directory, "capture_plan.json"), "w") as handle:
        json.dump(plan, handle)
    with open(os.path.join(directory, "run_manifest.json"), "w") as handle:
        json.dump({"git_commit": "a" * 40}, handle)
    return directory


@pytest.fixture(scope="module")
def capture(tmp_path_factory):
    return write_capture(str(tmp_path_factory.mktemp("capture")))


@pytest.fixture(scope="module")
def scored(fp, capture, tmp_path_factory):
    out = str(tmp_path_factory.mktemp("results"))
    assert fp.main(["fit", "--capture", capture, "--out", out]) == 0
    assert fp.main(["score", "--capture", capture, "--out", out, "--n-resamples", "200",
                    "--n-permutations", "6"]) == 0
    with open(os.path.join(out, "p1_probe.json")) as handle:
        return out, json.load(handle)


def test_fit_writes_the_frozen_artifact_and_the_selection(fp, scored):
    out, _ = scored
    with open(os.path.join(out, "p1_fit.json")) as handle:
        fitted = json.load(handle)
    sel = fitted["selected"]
    assert 4 <= sel["layer"] <= 31 and sel["row"] == sel["layer"] + 1
    assert sel["C"] in fp.C_GRID
    assert len(fitted["select_auroc"]) == 33 and len(fitted["select_auroc"][0]) == 4
    assert fitted["n_fit"] == {"D": 48, "H": 48}
    art = torch.load(os.path.join(out, "p1_fit.pt"), weights_only=True)
    assert tuple(art["weights"].shape) == (33, 4, HIDDEN)
    assert tuple(art["mass_mean"].shape) == (33, HIDDEN)
    # The planted axis is 0, so the selected probe should load on it.
    w = art["weights"][sel["row"], fp.C_GRID.index(sel["C"])].numpy()
    assert abs(w[0]) == np.abs(w).max()


def test_score_writes_the_rule_number_the_gate_and_the_controls(scored):
    _, result = scored
    assert result["far_gate"]["auroc"] > 0.9 and result["far_gate"]["fallback"] is False
    rule = result["rule"]
    assert rule["auroc"] > 0.9 and rule["band"] == "misleadingness" and rule["anti_aligned"] is False
    assert rule["n_pairs"] == 40 and rule["n_clusters"] == 5 and rule["n_resamples"] == 200
    assert rule["seed"] == 20261101
    lo, hi = rule["ci"]
    assert lo <= rule["auroc"] <= hi
    controls = result["controls"]
    assert set(controls) == {"ser_D", "far_I", "far_HI", "ser_HI", "ser_I", "far_F", "ser_F"}
    assert controls["far_I"]["n_pairs"] == 12 and controls["ser_HI"]["n_pairs"] == 36
    for cell in ("far_I", "far_HI", "ser_HI", "ser_I", "far_F", "ser_F"):
        assert controls[cell]["auroc"] < 0.8
    assert result["r2"]["label"] in ("clean", "instruction-confounded")
    assert result["verdict"]["band"] == "misleadingness"
    assert len(result["by_layer"]) == 33
    assert result["provenance"]["git_commit"] == "a" * 40
    assert result["hi_kept_share"]["far_gate_HI"] == pytest.approx(0.9)


def test_score_runs_the_permutation_null_and_leave_one_clause_out(scored):
    _, result = scored
    null = result["permutation_null"]
    assert null["n_permutations"] == 6 and len(null["aurocs"]) == 6
    assert 0.0 <= null["p_one_sided"] <= 1.0
    loco = result["loco"]
    assert set(loco["by_clause"]) == set(CLAUSES["far_v2"])
    assert all(entry["auroc"] > 0.8 for entry in loco["by_clause"].values())


def test_score_reports_sdr_descriptively_without_the_sample_rows(scored):
    _, result = scored
    sdr = result["sdr"]
    assert sdr["D"]["n_pairs"] == 24
    assert sdr["I_reported"]["n_dropped_sample"] == 2 and sdr["I_reported"]["n_pairs"] == 10


def test_score_writes_a_markdown_table(scored):
    out, _ = scored
    with open(os.path.join(out, "p1_probe.md")) as handle:
        text = handle.read()
    assert "| SER D" in text and "rule" in text.lower()


def test_a_weak_far_gate_sets_the_fallback(fp, tmp_path):
    capture = write_capture(str(tmp_path / "cap"), gate_shift=0.0)
    out = str(tmp_path / "out")
    assert fp.main(["fit", "--capture", capture, "--out", out]) == 0
    assert fp.main(["score", "--capture", capture, "--out", out, "--n-resamples", "20",
                    "--n-permutations", "0"]) == 0
    with open(os.path.join(out, "p1_probe.json")) as handle:
        result = json.load(handle)
    assert result["far_gate"]["auroc"] < 0.75 and result["far_gate"]["fallback"] is True
    assert result["verdict"]["reading"] == "per-token DLA only"


def test_the_bootstrap_ci_is_seed_deterministic_end_to_end(fp, capture, scored, tmp_path):
    out, first = scored
    again = str(tmp_path / "again")
    os.makedirs(again)
    for name in ("p1_fit.pt", "p1_fit.json"):
        with open(os.path.join(out, name), "rb") as src, open(os.path.join(again, name), "wb") as dst:
            dst.write(src.read())
    assert fp.main(["score", "--capture", capture, "--out", again, "--n-resamples", "200",
                    "--n-permutations", "6"]) == 0
    with open(os.path.join(again, "p1_probe.json")) as handle:
        second = json.load(handle)
    assert second["rule"]["ci"] == first["rule"]["ci"]
    assert second["permutation_null"]["aurocs"] == first["permutation_null"]["aurocs"]


def test_fit_refuses_a_nonfinite_fit_residual(fp, tmp_path):
    capture = write_capture(str(tmp_path / "cap"))
    path = os.path.join(capture, "resid.far_fit_D.pt")
    blob = torch.load(path, weights_only=True)
    blob["resid"][0, 10, 0] = float("inf")
    torch.save(blob, path)
    with pytest.raises(SystemExit):
        fp.main(["fit", "--capture", capture, "--out", str(tmp_path / "out")])


def test_read_writes_the_per_token_contrasts(fp, capture, tmp_path):
    out = str(tmp_path / "read")
    assert fp.main(["read", "--capture", capture, "--out", out, "--n-resamples", "100"]) == 0
    with open(os.path.join(out, "p1_tokens.json")) as handle:
        tokens = json.load(handle)
    far = tokens["tasks"]["far"]["groups"]
    ser = tokens["tasks"]["ser"]["groups"]
    # The quartet promotes the deceptive item by 1.0 and suppresses the honest item by 0.5 under D.
    assert far["quartet"]["promotion"]["mean"] == pytest.approx(1.0, abs=1e-6)
    assert far["quartet"]["suppression"]["mean"] == pytest.approx(-0.5, abs=1e-6)
    assert ser["quartet"]["promotion"]["mean"] == pytest.approx(1.0, abs=1e-6)
    # mlp.31 is the same on D and H, so its contrast is 0.
    assert far["mlp.31"]["suppression"]["mean"] == pytest.approx(0.0, abs=1e-6)
    whole = far["whole_model"]
    lo, hi = whole["promotion"]["ci"]
    assert lo <= whole["promotion"]["mean"] <= hi
    assert set(far) >= {"whole_model", "quartet", "late_honest_own", "late_honest_far_ser", "mlp.30", "mlp.31"}
    diff = tokens["far_minus_ser"]["quartet"]["promotion"]
    assert diff["mean"] == pytest.approx(0.0, abs=1e-6)
    assert tokens["tasks"]["far"]["n_pairs"] == 40
    assert tokens["tasks"]["far"]["dla_sum_max_abs_error"] < 1e-4
    assert os.path.exists(os.path.join(out, "p1_tokens.md"))


# ==============================================================================
# B2-T9: THE INSTRUCTED-INVERSION CONTRAST IN `read` AND THE RUN MANIFESTS
# ==============================================================================

def _plant_inversion(capture, name, twin, *, honest_shift, deceptive_shift):
    """Give an I cell a known contrast against its H twin, keyed by instance_id, and reverse its row order.

    mlp.30 is set per row to the row's id number on both files, plus `honest_shift` on the I honest column; the
    quartet carries `deceptive_shift` on the I deceptive column. Reversing the I files makes a positional join give
    the wrong mlp.30 value, so only the instance_id join reproduces `honest_shift` exactly.
    """
    mlp30 = KEYS.index(["mlp", 30, 0])
    for cell in (twin, name):
        path = os.path.join(capture, f"tokens.{cell}.pt")
        blob = torch.load(path, weights_only=True)
        number = torch.tensor([float(one[-3:]) for one in blob["ids"]])
        blob["dla"][:, mlp30, 0] = number
        if cell == name:
            blob["dla"][:, mlp30, 0] += honest_shift
            for k in _quartet_index():
                blob["dla"][:, k, 1] += deceptive_shift / 4
        blob["logits_centred"] = blob["dla"].sum(1)
        torch.save(blob, path)
    rows_path = os.path.join(capture, f"rows.{name}.jsonl")
    with open(rows_path) as handle:
        rows = [line for line in handle if line.strip()]
    with open(rows_path, "w") as handle:
        handle.write("".join(rows[::-1]))
    for kind, tensors in (("resid", ("readout", "resid")),
                          ("tokens", ("token_ids", "logits_raw", "logits_logsoftmax", "logits_centred", "dla"))):
        path = os.path.join(capture, f"{kind}.{name}.pt")
        blob = torch.load(path, weights_only=True)
        blob["ids"] = list(blob["ids"])[::-1]
        for key in tensors:
            blob[key] = blob[key].flip(0)
        torch.save(blob, path)


@pytest.fixture(scope="module")
def inversion_capture(tmp_path_factory):
    capture = write_capture(str(tmp_path_factory.mktemp("inversion")))
    _plant_inversion(capture, "far_gate_I", "far_gate_H", honest_shift=-0.3, deceptive_shift=0.8)
    _plant_inversion(capture, "ser_test_I", "ser_test_H", honest_shift=-0.7, deceptive_shift=0.4)
    return capture


def test_read_adds_the_i_minus_h_contrast_joined_on_instance_id(fp, inversion_capture, tmp_path):
    out = str(tmp_path / "read")
    assert fp.main(["read", "--capture", inversion_capture, "--out", out, "--n-resamples", "100"]) == 0
    with open(os.path.join(out, "p1_tokens.json")) as handle:
        tokens = json.load(handle)
    far_i, ser_i = tokens["tasks"]["far_I"], tokens["tasks"]["ser_I"]
    assert far_i["cells"] == ["far_gate_I", "far_gate_H"] and ser_i["cells"] == ["ser_test_I", "ser_test_H"]
    assert far_i["n_pairs"] == 12 and ser_i["n_pairs"] == 10
    assert far_i["n_unjoined"] == 0 and far_i["n_token_mismatch"] == 0
    assert far_i["n_clusters"] == 4 and ser_i["n_clusters"] == 5
    # Only the instance_id join gives these exactly; the I files are in reverse order.
    for entry, honest, deceptive in ((far_i, -0.3, 0.8), (ser_i, -0.7, 0.4)):
        groups = entry["groups"]
        assert groups["mlp.30"]["suppression"]["mean"] == pytest.approx(honest, abs=1e-5)
        assert groups["mlp.30"]["suppression"]["sd"] == pytest.approx(0.0, abs=1e-5)
        assert groups["quartet"]["promotion"]["mean"] == pytest.approx(deceptive, abs=1e-5)
        assert groups["quartet"]["suppression"]["mean"] == pytest.approx(0.0, abs=1e-6)
        for group in ("whole_model", "whole_model_logsoftmax"):
            for label in ("suppression", "promotion"):
                one = groups[group][label]
                lo, hi = one["ci"]
                assert lo <= one["mean"] <= hi
    # The D rows are still D against H; far_minus_ser stays D only.
    assert tokens["tasks"]["far"]["groups"]["quartet"]["promotion"]["mean"] == pytest.approx(1.0, abs=1e-6)
    assert set(tokens["far_minus_ser"]) == set(tokens["tasks"]["far"]["groups"])
    with open(os.path.join(out, "p1_tokens.md")) as handle:
        text = handle.read()
    assert "Instructed inversion (I minus H)" in text
    assert "FAR I - H promotion" in text and "SER I - H suppression" in text and "FAR D - H promotion" in text
    assert "FAR 12 pairs, SER 10 pairs" in text


def test_the_inversion_contrast_leaves_the_d_entries_unchanged(fp, inversion_capture, tmp_path):
    import shutil

    with_i = str(tmp_path / "with")
    assert fp.main(["read", "--capture", inversion_capture, "--out", with_i, "--n-resamples", "50"]) == 0
    stripped = shutil.copytree(inversion_capture, str(tmp_path / "noI"))
    for name in ("far_gate_I", "ser_test_I"):
        os.remove(os.path.join(stripped, f"rows.{name}.jsonl"))
    without = str(tmp_path / "without")
    assert fp.main(["read", "--capture", stripped, "--out", without, "--n-resamples", "50"]) == 0
    with open(os.path.join(with_i, "p1_tokens.json")) as handle:
        a = json.load(handle)
    with open(os.path.join(without, "p1_tokens.json")) as handle:
        b = json.load(handle)
    assert "far_I" not in b["tasks"] and "ser_I" not in b["tasks"]
    for task in ("far", "ser", "sdr", "sdr_I_reported"):
        assert a["tasks"][task]["groups"] == b["tasks"][task]["groups"]
    assert a["far_minus_ser"] == b["far_minus_ser"]
    with open(os.path.join(without, "p1_tokens.md")) as handle:
        plain = handle.read()
    with open(os.path.join(with_i, "p1_tokens.md")) as handle:
        assert handle.read().startswith(plain)
    assert "Instructed inversion" not in plain


def _manifest(path):
    import run_manifest

    with open(path) as handle:
        manifest = json.load(handle)
    assert manifest["schema"] == "run-manifest/1"
    assert run_manifest.verify_manifest_hash(manifest)
    return manifest


def test_fit_score_and_read_each_write_a_run_manifest(fp, capture, tmp_path):
    out = str(tmp_path / "out")
    assert fp.main(["fit", "--capture", capture, "--out", out]) == 0
    assert fp.main(["score", "--capture", capture, "--out", out, "--n-resamples", "10",
                    "--n-permutations", "0"]) == 0
    assert fp.main(["read", "--capture", capture, "--out", out, "--n-resamples", "10"]) == 0
    written = sorted(name for name in os.listdir(out) if name.startswith("run_manifest"))
    assert written == ["run_manifest.1.json", "run_manifest.2.json", "run_manifest.json"]
    by_command = {}
    for name in written:
        manifest = _manifest(os.path.join(out, name))
        by_command[manifest["argv"][1]] = manifest
    assert set(by_command) == {"fit", "score", "read"}
    assert _manifest(os.path.join(out, "run_manifest.json"))["argv"][1] == "fit"
    assert _manifest(os.path.join(out, "run_manifest.1.json"))["argv"][1] == "score"
    assert _manifest(os.path.join(out, "run_manifest.2.json"))["argv"][1] == "read"

    probe_py = os.path.join(ROOT, "component_analysis", "probe.py")
    for command, manifest in by_command.items():
        assert manifest["script"] == "falsity_probe.py"
        assert manifest["argv"][0] == SCRIPT and manifest["argv"][2:4] == ["--capture", capture]
        assert manifest["git_fingerprint_error"] == "disabled"   # tests/conftest.py sets DC_RUN_MANIFEST_GIT=0
        assert manifest["code_sha256"] == {"scripts/falsity_probe.py": _sha(SCRIPT),
                                           "component_analysis/probe.py": _sha(probe_py)}
        assert manifest["created"]
        files = manifest["dataset_files"]
        for path, digest in files.items():
            assert digest == _sha(path)
        assert os.path.join(capture, "capture_plan.json") in files
        assert os.path.join(capture, "run_manifest.json") in files
    assert by_command["fit"]["seed"] is None
    assert by_command["score"]["seed"] == by_command["read"]["seed"] == 20261101

    fit_files = set(by_command["fit"]["dataset_files"])
    assert os.path.join(capture, "resid.far_fit_D.pt") in fit_files
    assert os.path.join(capture, "rows.far_select_HI.jsonl") in fit_files
    assert not any("ser_test" in path or "far_gate" in path or "tokens." in path for path in fit_files)

    score_files = set(by_command["score"]["dataset_files"])
    assert {os.path.join(out, "p1_fit.pt"), os.path.join(out, "p1_fit.json"),
            os.path.join(capture, "resid.ser_test_D.pt"), os.path.join(capture, "resid.far_gate_I.pt"),
            os.path.join(capture, "resid.sdr_test_I_reported.pt"),
            os.path.join(capture, "resid.far_fit_H.pt")} <= score_files
    assert not any("tokens." in path for path in score_files)

    read_files = set(by_command["read"]["dataset_files"])
    assert {os.path.join(capture, "tokens.far_gate_I.pt"), os.path.join(capture, "tokens.ser_test_I.pt"),
            os.path.join(capture, "rows.ser_test_H.jsonl")} <= read_files
    assert not any("resid." in path or "far_fit" in path for path in read_files)


def _sha(path):
    import hashlib

    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def test_a_rerun_with_identical_content_writes_no_new_manifest_and_a_failure_never_stops_the_run(
        fp, capture, tmp_path, monkeypatch, capsys):
    import run_manifest

    out = str(tmp_path / "out")
    monkeypatch.setattr(run_manifest, "now_chicago", lambda: "2026-11-01T00:00:00-05:00")
    assert fp.main(["read", "--capture", capture, "--out", out, "--n-resamples", "5"]) == 0
    assert fp.main(["read", "--capture", capture, "--out", out, "--n-resamples", "5"]) == 0
    assert sorted(n for n in os.listdir(out) if n.startswith("run_manifest")) == ["run_manifest.json"]

    def broken(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(run_manifest, "write_run_manifest", broken)
    other = str(tmp_path / "other")
    assert fp.main(["read", "--capture", capture, "--out", other, "--n-resamples", "5"]) == 0
    assert os.path.exists(os.path.join(other, "p1_tokens.json"))
    assert not any(n.startswith("run_manifest") for n in os.listdir(other))
    assert "run_manifest.json not written: OSError: disk full" in capsys.readouterr().out


def test_the_late_honest_heads_follow_the_phase2_readings(fp):
    path = os.path.join(ROOT, "docs", "research", "mechanism-analysis", "phase2", "p2_readings.json")
    if not os.path.exists(path):
        pytest.skip("phase2 readings not present in this checkout")
    with open(path) as handle:
        readings = json.load(handle)
    for task in ("far", "ser", "sdr"):
        expected = [tuple(int(x) for x in label.split(".")[1:]) for label in readings[task]["c_honest"]["heads"]]
        assert [tuple(h) for h in fp.LATE_HONEST_HEADS[task]] == expected
