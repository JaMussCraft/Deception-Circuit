"""Tests for scripts/neuron_partition_sets.py (neuron-partition R6 classes and N3 stability). CPU only."""

import importlib.util
import json
import os
import sys

import numpy as np
import pytest
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location("neuron_partition_sets",
                                              os.path.join(REPO, "scripts", "neuron_partition_sets.py"))
nps = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nps)

L, W = nps.NUM_LAYERS, nps.INTERMEDIATE
PILOT = os.path.join(REPO, "outputs", "_analyses", "neuron-partition", "attribution")
PILOT_DH = os.path.join(PILOT, "far_v2_dh_validation_f4ce555_limit64")
PILOT_IN = os.path.join(PILOT, "far_v2_in_validation_f4ce555_limit64")
KEYS = ("atp_readout_mean", "atp_readout_absmean", "contrast_readout_mean", "contrast_readout_std",
        "atp_clause_mean", "atp_clause_absmean", "contrast_clause_mean", "contrast_clause_std")


def flat(layer, index):
    return layer * W + index


def grid(values):
    """[32, 14336] float32 zeros with {(layer, index): value} set."""
    t = torch.zeros(L, W, dtype=torch.float32)
    for (layer, index), v in values.items():
        t[layer, index] = v
    return t


def write_run(directory, scores, *, task="far_v2", pair="dh", reverse=False, commit="a" * 40):
    os.makedirs(directory, exist_ok=True)
    full = {k: torch.zeros(L, W) for k in KEYS}
    full.update(scores)
    torch.save(full, os.path.join(directory, "scores.pt"))
    json.dump({"n_rows": 4, "reverse": reverse, "task": task, "pair": pair, "splits": ["train"]},
              open(os.path.join(directory, "rows.json"), "w"))
    json.dump({"git_commit": commit, "git_dirty": False, "manifest_hash": "x", "slurm_job_id": None},
              open(os.path.join(directory, "run_manifest.json"), "w"))
    return directory


# Designed scores for k = 3. D's top 3 = {a, b, c}; I's top 3 = {b, c, e}; H's top 3 (from -rev) = {c, d, e}.
A, B, C, D_, E = (0, 1), (5, 7), (10, 3), (20, 11), (31, 14335)
S_D = {A: 3.0, B: 2.0, C: 1.0, D_: 0.5, E: -1.0}
S_I = {B: 5.0, C: 4.0, E: 3.0, A: 0.1}
REV = {C: -3.0, D_: -2.0, E: -1.0, A: 0.2}          # negative rev_atp = supports the honest answer


def designed_dirs(tmp_path, *, rev=True):
    dh = write_run(str(tmp_path / "dh"), {"atp_readout_mean": grid(S_D),
                                          **({"rev_atp_readout_mean": grid(REV)} if rev else {})}, reverse=rev)
    inv = write_run(str(tmp_path / "in"), {"atp_readout_mean": grid(S_I)}, pair="in")
    return dh, inv


# ------------------------------------------------------------------------------ pure functions

def test_top_positive_orders_ties_and_threshold():
    s = np.zeros((L, W))
    s[0, 5] = 2.0
    s[0, 1] = 2.0          # tie with (0, 5): the lower flat index wins
    s[3, 0] = 1.0
    s[4, 4] = -9.0
    got = nps.top_positive(s, 2)
    assert got["set"] == {flat(0, 1), flat(0, 5)}
    assert got["threshold"] == 2.0 and got["max"] == 2.0 and got["n_positive"] == 3 and not got["truncated"]
    one = nps.top_positive(s, 1)
    assert one["set"] == {flat(0, 1)}


def test_k_larger_than_positive_count_takes_all_positive():
    s = np.zeros((L, W))
    s[1, 1], s[2, 2], s[3, 3] = 1.0, 0.5, -1.0
    got = nps.top_positive(s, 500)
    assert got["set"] == {flat(1, 1), flat(2, 2)}
    assert got["truncated"] and got["size"] == 2 and got["n_positive"] == 2 and got["threshold"] == 0.5
    empty = nps.top_positive(-np.abs(s), 10)
    assert empty["set"] == frozenset() and empty["threshold"] is None


def test_designed_classes_at_k3():
    s_d, s_i = grid(S_D).double().numpy(), grid(S_I).double().numpy()
    s_h = -grid(REV).double().numpy()
    part = nps.partition(s_d, s_i, s_h, 3)
    a, b, c, d, e = (flat(*x) for x in (A, B, C, D_, E))
    assert part["sets"]["T_D"] == {a, b, c}
    assert part["sets"]["T_I"] == {b, c, e}
    assert part["sets"]["T_H"] == {c, d, e}
    assert part["sets"]["D_only"] == {a}
    assert part["sets"]["DI_shared"] == {b}
    assert part["sets"]["H_only"] == {d}
    assert part["sets"]["all_shared"] == {c}


def test_classes_without_s_h():
    got = nps.classes_from_tops(frozenset({1, 2, 3}), frozenset({3, 4}), None)
    assert got == {"D_only": {1, 2}, "DI_shared": {3}}


def test_jaccard_and_floor_formulas():
    assert nps.jaccard({1, 2, 3}, {2, 3, 4}) == 0.5
    assert nps.jaccard(set(), set()) is None
    assert nps.jaccard({1}, set()) == 0.0
    n = 458752
    assert nps.N_NEURONS == n
    for k in (500, 1000, 2000):
        assert nps.expected_random_jaccard(k, k) == pytest.approx(k / (2 * n - k), rel=1e-12)
    assert nps.expected_random_jaccard(1000, 1000) == pytest.approx(0.001091102712, rel=1e-9)   # 1000 / 916504
    # unequal sizes: E[|A&B|] = 500*2000/458752 = 2.17983; J = 2.17983 / (2500 - 2.17983)
    assert nps.expected_random_jaccard(500, 2000) == pytest.approx(2.179827 / 2497.820173, rel=1e-5)
    assert nps.expected_random_jaccard(0, 0) is None
    emp = nps.empirical_floor(2000, 2000, draws=20, seed=2)
    assert emp["draws"] == 20 and len(emp["values"]) == 20
    assert emp["mean"] == pytest.approx(2000 / (2 * n - 2000), abs=0.002)
    assert nps.empirical_floor(2000, 2000, draws=20, seed=2)["values"] == emp["values"]   # seeded


# ------------------------------------------------------------------------------ signs and inputs

def test_reverse_sign_flip_uses_rev_key_not_forward(tmp_path):
    dh, inv = designed_dirs(tmp_path)
    run_dh, run_in = nps.load_run(dh), nps.load_run(inv)
    signed = nps.signed_scores(run_dh, run_in, run_dh, score="atp", position="readout", allow_missing_reverse=False)
    # s_H is minus rev_atp: the neurons with negative rev_atp (honest-supporting) are positive in s_H
    assert signed["s_H"][C] == 3.0 and signed["s_H"][D_] == 2.0 and signed["s_H"][A] == pytest.approx(-0.2)
    assert signed["keys"]["s_H"].startswith("-rev_atp_readout_mean")
    # never -atp_readout_mean of the reverse directory
    assert not np.allclose(signed["s_H"], -signed["s_D"])


def test_missing_reverse_refused_unless_allowed(tmp_path):
    dh, inv = designed_dirs(tmp_path, rev=False)
    run_dh, run_in = nps.load_run(dh), nps.load_run(inv)
    with pytest.raises(SystemExit, match="rev_atp_readout_mean"):
        nps.signed_scores(run_dh, run_in, run_dh, score="atp", position="readout", allow_missing_reverse=False)
    with pytest.raises(SystemExit):
        nps.signed_scores(run_dh, run_in, None, score="atp", position="readout", allow_missing_reverse=False)
    got = nps.signed_scores(run_dh, run_in, run_dh, score="atp", position="readout", allow_missing_reverse=True)
    assert got["s_H"] is None


def test_contrast_ranking_is_antisymmetric(tmp_path):
    dh = write_run(str(tmp_path / "dh"), {"contrast_readout_mean": grid({A: 1.0, B: -2.0, C: 0.5})})
    inv = write_run(str(tmp_path / "in"), {"contrast_readout_mean": grid({B: -1.0, A: 3.0})}, pair="in")
    signed = nps.signed_scores(nps.load_run(dh), nps.load_run(inv), None, score="contrast", position="readout",
                               allow_missing_reverse=False)
    part = nps.partition(signed["s_D"], signed["s_I"], signed["s_H"], 5)
    assert part["sets"]["T_D"] == {flat(*A), flat(*C)} and part["sets"]["T_H"] == {flat(*B)}
    assert part["sets"]["all_shared"] == frozenset()
    assert part["sets"]["D_only"] == {flat(*C)}           # A is in T_I
    assert any("disjoint by construction" in n for n in signed["notes"])


def test_clause_position_reads_clause_keys(tmp_path):
    dh = write_run(str(tmp_path / "dh"), {"atp_clause_mean": grid({A: 1.0}), "rev_atp_clause_mean": grid({B: -1.0}),
                                          "atp_readout_mean": grid({C: 1.0})}, reverse=True)
    inv = write_run(str(tmp_path / "in"), {"atp_clause_mean": grid({D_: 1.0})}, pair="in")
    run_dh = nps.load_run(dh)
    signed = nps.signed_scores(run_dh, nps.load_run(inv), run_dh, score="atp", position="clause",
                               allow_missing_reverse=False)
    part = nps.partition(signed["s_D"], signed["s_I"], signed["s_H"], 10)
    assert part["sets"]["T_D"] == {flat(*A)} and part["sets"]["T_H"] == {flat(*B)} and part["sets"]["T_I"] == {
        flat(*D_)}


# ------------------------------------------------------------------------------ the CLI with W3's nulls

def _run_designed_partition(tmp_path, extra=()):
    dh, inv = designed_dirs(tmp_path)
    out = str(tmp_path / "out")
    assert nps.main(["partition", "--dh", dh, "--in", inv, "--dh-reverse", dh, "--out-dir", out, "-k", "3", "4",
                     *extra]) == 0
    return out


def test_partition_cli_writes_sets_summary_and_nulls(tmp_path):
    out = _run_designed_partition(tmp_path)
    sets = json.load(open(os.path.join(out, "far_sets_k3.json")))
    assert sets["D_only"] == [["mlp_hidden", 0, 1]]
    assert sets["H_only"] == [["mlp_hidden", 20, 11]]
    assert sets["all_shared"] == [["mlp_hidden", 10, 3]]
    assert sets["DI_shared"] == [["mlp_hidden", 5, 7]]
    assert len(sets["T_D"]) == 3 and len(sets["T_I"]) == 3 and len(sets["T_H"]) == 3
    summary = json.load(open(os.path.join(out, "partition_summary.json")))
    entry = summary["by_k"]["3"]
    assert entry["sizes"] == {"D_only": 1, "DI_shared": 1, "H_only": 1, "all_shared": 1, "T_D": 3, "T_I": 3,
                              "T_H": 3}
    assert entry["per_layer"]["H_only"][20] == 1 and len(entry["per_layer"]["T_D"]) == 32
    assert entry["tops"]["T_D"]["threshold"] == 1.0
    assert entry["overlaps"]["regions"]["DIH"] == 1
    assert summary["inputs"]["dh"]["scores_sha256"] == nps.sha256_file(os.path.join(str(tmp_path / "dh"),
                                                                                    "scores.pt"))
    assert summary["inputs"]["dh"]["git_commit"] == "a" * 40
    assert "nulls" in entry["null_calls"]["D_only"]["command"]
    # k = 4: T_D gains D_, which is in T_H, so it leaves D_only; T_H holds every positive -rev (3 of 4 asked)
    entry4 = summary["by_k"]["4"]
    assert entry4["tops"]["T_H"]["truncated"] and entry4["sizes"]["T_H"] == 3


def test_nulls_match_size_and_layers_and_exclude_tested(tmp_path):
    # bigger designed sets so the nulls are not trivial: D gets 40 neurons over 3 layers, I and H elsewhere
    s_d = {(3, i): 1.0 + i for i in range(20)}
    s_d.update({(17, 100 + i): 0.5 for i in range(15)})
    s_d.update({(30, 7 + i): 0.2 for i in range(5)})
    dh = write_run(str(tmp_path / "dh"), {"atp_readout_mean": grid(s_d),
                                          "rev_atp_readout_mean": grid({(9, 9): -1.0})}, reverse=True)
    inv = write_run(str(tmp_path / "in"), {"atp_readout_mean": grid({(3, 0): 1.0})}, pair="in")
    out = str(tmp_path / "out")
    assert nps.main(["partition", "--dh", dh, "--in", inv, "--dh-reverse", dh, "--out-dir", out, "-k", "500"]) == 0
    groups = json.load(open(os.path.join(out, "far_sets_k500_with_nulls.json")))
    tested = groups["D_only"]
    assert len(tested) == 39                                   # (3, 0) is in T_I
    tested_set = nps.from_members(tested)
    hist = nps.layer_histogram(tested_set)
    nulls = [name for name in groups if name.startswith("null_D_only_500_")]
    assert len(nulls) == 20 and nulls[0] == "null_D_only_500_0" and nulls[-1] == "null_D_only_500_19"
    for name in nulls:
        null = nps.from_members(groups[name])
        assert len(null) == len(tested_set)
        assert nps.layer_histogram(null) == hist
        assert not (null & tested_set)
    assert len({tuple(map(tuple, groups[n])) for n in nulls}) == 20
    # every class with members has 20 nulls; empty classes are omitted from both files
    assert set(n for n in groups if not n.startswith("null_")) == {"D_only", "DI_shared", "H_only"}
    assert "all_shared" not in json.load(open(os.path.join(out, "far_sets_k500.json")))
    summary = json.load(open(os.path.join(out, "partition_summary.json")))
    assert "all_shared" in summary["by_k"]["500"]["empty_omitted"]
    prov = json.load(open(summary["by_k"]["500"]["null_calls"]["D_only"]["provenance_path"]))
    assert prov["seed"] == 2 and prov["k"] == 20


def test_partition_refuses_to_overwrite(tmp_path):
    out = _run_designed_partition(tmp_path, ("--no-nulls",))
    dh = str(tmp_path / "dh")
    with pytest.raises(SystemExit, match="exists"):
        nps.main(["partition", "--dh", dh, "--in", str(tmp_path / "in"), "--dh-reverse", dh, "--out-dir", out,
                  "-k", "3", "--no-nulls"])


def test_contrast_and_clause_variants_get_their_own_file_names(tmp_path):
    dh, inv = designed_dirs(tmp_path)
    out = str(tmp_path / "out")
    nps.main(["partition", "--dh", dh, "--in", inv, "--out-dir", out, "-k", "3", "--score", "contrast",
              "--no-nulls"])
    assert os.path.exists(os.path.join(out, "partition_summary_contrast.json"))
    nps.main(["partition", "--dh", dh, "--in", inv, "--dh-reverse", dh, "--out-dir", out, "-k", "3", "--position",
              "clause", "--allow-missing-reverse", "--no-nulls"])
    assert os.path.exists(os.path.join(out, "partition_summary_clause.json"))


# ------------------------------------------------------------------------------ stability

def test_stability_identical_and_disjoint_halves(tmp_path):
    dh_a, in_a = designed_dirs(tmp_path / "a")
    # half B: same T_D and T_I, but H's top moves to brand-new neurons
    dh_b = write_run(str(tmp_path / "b" / "dh"), {"atp_readout_mean": grid(S_D),
                                                  "rev_atp_readout_mean": grid({(2, 2): -3.0, (4, 4): -2.0,
                                                                                (6, 6): -1.0})}, reverse=True)
    in_b = write_run(str(tmp_path / "b" / "in"), {"atp_readout_mean": grid(S_I)}, pair="in")
    out = str(tmp_path / "stab")
    assert nps.main(["stability", "--dh", dh_a, dh_b, "--in", in_a, in_b, "--dh-reverse", dh_a, dh_b,
                     "--out-dir", out, "-k", "3", "--floor-draws", "5"]) == 0
    summary = json.load(open(os.path.join(out, "stability_summary.json")))
    rows = summary["by_k"]["3"]["sets"]
    assert summary["by_k"]["3"]["ceiling"] == 1.0
    assert rows["T_D"]["jaccard"] == 1.0 and rows["T_D"]["stable"]
    assert rows["T_H"]["jaccard"] == 0.0 and rows["T_H"]["stable"] is False
    # half A: D_only {A}, H_only {D_}, all_shared {C}; half B: T_H = {(2,2),(4,4),(6,6)} so D_only {A}, DI {B, C}
    assert rows["D_only"]["jaccard"] == 1.0
    assert rows["DI_shared"]["jaccard"] == 0.5 and rows["DI_shared"]["stable"]
    assert rows["all_shared"]["verdict"].startswith("n/a")
    assert rows["T_D"]["floor_analytic"] == pytest.approx(3 / (2 * 458752 - 3))
    assert rows["T_D"]["floor_empirical"]["draws"] == 5
    md = open(os.path.join(out, "stability_summary.md")).read()
    assert "| 3 | T_D | 3 | 3 | 1.0000 | 1.0000 |" in md


# ------------------------------------------------------------------------------ pilot fixtures (git-ignored)

@pytest.mark.skipif(not (os.path.isdir(PILOT_DH) and os.path.isdir(PILOT_IN)),
                    reason="pilot score directories are git-ignored outputs and are absent here")
def test_pilot_fixtures_load_and_partition(tmp_path):
    out = str(tmp_path / "pilot")
    assert nps.main(["partition", "--dh", PILOT_DH, "--in", PILOT_IN, "--dh-reverse", PILOT_DH,
                     "--allow-missing-reverse", "--no-nulls", "--label", "pilot, 64 rows, not for findings",
                     "--out-dir", out]) == 0
    summary = json.load(open(os.path.join(out, "partition_summary.json")))
    assert summary["inputs"]["dh"]["n_rows"] == 64 and summary["inputs"]["in"]["n_rows"] == 64
    assert summary["inputs"]["dh"]["git_commit"].startswith("f4ce555")
    for k in ("500", "1000", "2000"):
        entry = summary["by_k"][k]
        assert set(entry["sizes"]) == {"D_only", "DI_shared", "T_D", "T_I"}
        assert entry["sizes"]["T_D"] == int(k) and entry["sizes"]["T_I"] == int(k)
        assert entry["sizes"]["D_only"] + entry["sizes"]["DI_shared"] == int(k)
        assert all(len(h) == 32 for h in entry["per_layer"].values())
        assert sorted(entry["not_built"]) == ["H_only", "T_H", "all_shared"]
        sets = json.load(open(os.path.join(out, f"far_sets_k{k}.json")))
        assert all(m[0] == "mlp_hidden" and 0 <= m[1] < 32 and 0 <= m[2] < 14336 for m in sets["T_D"])
