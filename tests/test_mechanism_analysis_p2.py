"""Ticket 04 of mechanism-analysis: the phase-2 builders (outputs/_launch_mechanism_analysis/p2_*.py).

Seams (spec section 4 phase 2, R16, R26): the per-task operand that adds the deciding S_k heads and the C_t MLP
blocks to U at leaf; the deciding sets read from the phase-1 readings; the groups files (composition-set families,
the S2p top 20 as singletons); the batch files; the membership columns; the statistics the readings use (Fisher
exact over an RxC table, the one-sided binomial test); the pre-clause zero assertion; the sweep-to-head-table
tables the roles pass merges from.
"""

from __future__ import annotations

import importlib
import json
import os
import sys

import numpy as np
import pytest

from evaluation import algebra
from evaluation.masks import validate_hierarchy
from component_analysis.components import circuit_components
from tests.helpers import TINY
from tests.test_component_analysis import make_masks

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = os.path.join(REPO, "outputs", "_launch_mechanism_analysis")
HEADS, HEAD_DIM, LAYERS = TINY["heads"], TINY["head_dim"], TINY["layers"]


def _mod(name):
    if LAUNCH not in sys.path:
        sys.path.insert(0, LAUNCH)
    return importlib.import_module(name)


@pytest.fixture(scope="module")
def ops():
    return _mod("p2_operands")


def keys_of(masks):
    comps = circuit_components(masks, num_heads=HEADS, head_dim=HEAD_DIM)
    return {c.key for c in comps}


# ------------------------------------------------------------------ the operand

def test_operand_opens_exactly_the_named_heads_and_mlp_blocks_and_keeps_the_base_keys(ops):
    base = make_masks({0: [0, 2], 1: [1]}, {1}, seed=3)
    heads = [("head", 1, 3), ("head", 0, 2)]
    out = ops.operand_masks(base, heads=heads, mlp_layers=[0], num_heads=HEADS, head_dim=HEAD_DIM)
    assert set(out) == set(base)
    validate_hierarchy(out, num_heads=HEADS, head_dim=HEAD_DIM)
    assert keys_of(out) == {("head", 1, 3), ("head", 0, 2), ("mlp", 0, 0)}
    # every leaf of a named Component is open, so a leaf union with any circuit keeps the whole Component
    assert int(np.asarray(out["attention_neurons"]["1"])[3 * HEAD_DIM:(3 + 1) * HEAD_DIM].sum()) == HEAD_DIM
    assert int(np.asarray(out["mlp_hidden"]["0"]).sum()) == TINY["intermediate"]
    assert int(np.asarray(out["mlp_output"]["0"]).sum()) == TINY["hidden"]
    # untouched layers are closed at every level
    assert int(np.asarray(out["mlp_blocks"])[1]) == 0 and int(np.asarray(out["mlp_hidden"]["1"]).sum()) == 0
    assert int(np.asarray(out["attention_heads"]["0"]).sum()) == 1 and int(np.asarray(out["attention_neurons"]["0"]).sum()) == HEAD_DIM


def test_the_leaf_union_of_u_minus_m_with_the_operand_is_u_plus_the_operand(ops):
    U = make_masks({0: [0, 2], 1: [1]}, {0, 1}, seed=1)          # a "heads-only" circuit still carries MLP leaves
    m = ops.operand_masks(U, heads=[], mlp_layers=list(range(LAYERS)), num_heads=HEADS, head_dim=HEAD_DIM)
    X = ops.operand_masks(U, heads=[("head", 1, 3), ("head", 0, 2)], mlp_layers=[1], num_heads=HEADS,
                          head_dim=HEAD_DIM)
    tree = algebra.parse_expr("(U-m)|X")
    out = algebra.compose(tree, {"U": U, "m": m, "X": X}, granularity="leaf", num_heads=HEADS, head_dim=HEAD_DIM)
    assert keys_of(out) == {("head", 0, 0), ("head", 0, 2), ("head", 1, 1), ("head", 1, 3), ("mlp", 1, 0)}


def test_build_operand_writes_a_loadable_run_dir_with_provenance(ops, tmp_path):
    src = tmp_path / "run"
    src.mkdir()
    base = make_masks({0: [0, 2]}, {1}, seed=2)
    (src / "active_nodes.json").write_text(json.dumps(
        {"masks": {k: (v.tolist() if not isinstance(v, dict) else {l: a.tolist() for l, a in v.items()})
                   for k, v in base.items()}}))
    (src / "config.json").write_text(json.dumps({"model": "llama-tiny", "task": "far_v2"}))
    out = ops.build_operand(str(src), str(tmp_path / "op"), heads=[("head", 1, 0)], mlp_layers=[1],
                            num_heads=HEADS, head_dim=HEAD_DIM, provenance={"task": "far", "note": "test"})
    from evaluation.masks import load_circuit_masks
    masks = load_circuit_masks(out)
    assert keys_of(masks) == {("head", 1, 0), ("mlp", 1, 0)}
    config = json.loads((tmp_path / "op" / "config.json").read_text())
    assert config["model"] == "llama-tiny" and "operand" in config
    prov = json.loads((tmp_path / "op" / "provenance.json").read_text())
    assert prov["task"] == "far" and prov["heads"] == ["head.1.0"] and prov["mlp_layers"] == [1]


# ------------------------------------------------------------------ the deciding sets

def test_deciding_sets_come_from_the_phase_1c_readings_and_their_mlps_lie_in_c_t(ops):
    readings = {
        "rab": {"far": {"reading": "A'", "deciding": "greedy_k20", "deciding_numbers": {
            "selector": "greedy", "k": 20, "members": ["head.9.29", "mlp.6.0", "head.13.23"]}}},
        "routing": {"far": {"candidate": "greedy_k20", "C_t_mlps": ["mlp.4.0", "mlp.6.0"]}},
    }
    sets = ops.deciding_sets(readings)
    assert sets["far"]["candidate"] == "greedy_k20"
    assert sets["far"]["heads"] == [("head", 9, 29), ("head", 13, 23)]
    assert sets["far"]["mlps"] == [("mlp", 6, 0)]
    assert sets["far"]["ct_mlp_layers"] == [4, 6]
    bad = json.loads(json.dumps(readings))
    bad["routing"]["far"]["C_t_mlps"] = ["mlp.4.0"]
    with pytest.raises(ValueError):
        ops.deciding_sets(bad)


# ------------------------------------------------------------------ the groups files and the job files

@pytest.fixture(scope="module")
def jobs():
    return _mod("p2_jobs")


def _head_sets():
    """Six tiny circuits as {name: {(layer, head)}}: a 2-head core, one far exclusive, one far D-H head outside the
    core, one far H-D head in layer 30 and one in layer 5."""
    core = {(17, 24), (14, 4)}
    return {"D_far": core | {(9, 19), (12, 1)}, "D_sdr": core | {(5, 8)}, "D_ser": core | {(16, 2)},
            "H_far": core | {(30, 3), (5, 9), (12, 1)}, "H_sdr": core | {(18, 1)}, "H_ser": core | {(18, 1), (9, 19)}}


def test_family_groups_are_the_composition_sets_of_the_task(jobs):
    g = jobs.family_groups("far", _head_sets())
    assert set(g) == {"core", "excl_far", "DmH_far", "DmH_minus_core_far", "HmD_far", "late_HmD_far"}
    assert sorted(map(tuple, g["core"])) == [("head", 14, 4), ("head", 17, 24)]
    assert sorted(map(tuple, g["excl_far"])) == [("head", 9, 19), ("head", 12, 1)]      # not in D_sdr, not in D_ser
    assert sorted(map(tuple, g["DmH_far"])) == [("head", 9, 19)]                        # 12.1 is in H_far too
    assert sorted(map(tuple, g["DmH_minus_core_far"])) == [("head", 9, 19)]
    assert sorted(map(tuple, g["HmD_far"])) == [("head", 5, 9), ("head", 30, 3)]
    assert sorted(map(tuple, g["late_HmD_far"])) == [("head", 30, 3)]                   # layers 18, 22, 30 only


def test_family_groups_drop_an_empty_set_and_say_which(jobs):
    sets = _head_sets()
    sets["H_sdr"] = {(17, 24), (14, 4)}                 # H_sdr inside D_sdr: sdr's H-D is empty, D-H is not
    g = jobs.family_groups("sdr", sets)
    assert "HmD_sdr" not in g and "late_HmD_sdr" not in g
    assert jobs.empty_families("sdr", sets) == ["HmD_sdr", "late_HmD_sdr"]


def test_top20_groups_are_the_s2p_signed_top_20_as_singletons_plus_the_joint_set(jobs):
    components = [{"label": "mlp.0.0", "kind": "mlp", "layer": 0, "index": 0, "signed_rank": 1}]
    for r in range(2, 40):
        components.append({"label": f"head.{r}.{r % 32}", "kind": "head", "layer": r % 32, "index": (r * 7) % 32,
                           "signed_rank": r})
    sweep = {"components": components, "excluded_from_ranking": ["mlp.0.0"]}
    g = jobs.top20_groups(sweep)
    names = list(g)
    assert len(names) == 21 and names[-1] == "top20_joint"
    assert names[0] == "head.2.2" and names[19] == "head.21.21"
    assert all(len(g[n]) == 1 for n in names[:20]) and len(g["top20_joint"]) == 20
    assert g["head.2.2"] == [["head", 2, 14]]            # the key comes from the row, not from the label


def test_segment_lines_cover_every_v2_segment_but_unsegmented_with_the_pre_clause_ones_marked(jobs):
    assert jobs.SEGMENTS[0] == "intro" and jobs.SEGMENTS[-1] == "readout" and "unsegmented" not in jobs.SEGMENTS
    assert jobs.PRE_CLAUSE == ("intro", "item_1_intro", "item_2_intro", "designating_sentence", "designation_site",
                               "predicate_token", "other_token", "inverse_predicate_token", "designation_suffix")
    assert "pressure_clause" in jobs.POST_CLAUSE and "readout" in jobs.POST_CLAUSE


def test_batch_text_has_the_cells_of_spec_section_4_on_u_prime(jobs):
    text = jobs.batch_text("far")
    lines = [l for l in text.splitlines() if l and not l.startswith("#")]
    cells = [l[2:] for l in text.splitlines() if l.startswith("# ") and not l.startswith("# Ticket")
             and " " not in l[2:]]
    assert cells[:5] == ["d", "d_twinko", "h", "f", "i"] and cells[5:] == [f"seg_{s}" for s in jobs.SEGMENTS]
    assert len(lines) == 5 + len(jobs.SEGMENTS)
    d = lines[0]
    assert "--expr 'Up=((Df|Hf|Ds|Hs|De|He)-m)|X'" in d and "--compose-granularity leaf" in d
    assert "--circuit X=outputs/_launch_mechanism_analysis/operands/skct_far" in d
    assert "--reference x_far=outputs/_launch_mechanism_analysis/operands/skct_far" in d
    assert "--analyses attention_patterns,dla,knockout" in d and "--knockout-singles off" in d
    assert "--attention-conditions pressure,neutral_twin --dla-conditions pressure,neutral_twin" in d
    assert "--knockout-groups docs/research/mechanism-analysis/phase2/groups/far_families.json" in d
    assert "--attention-token-level" in d
    assert "--output-dir outputs/_analyses/mechanism-analysis-p2/d" in d
    assert "--knockout-counterfactual neutral_twin --knockout-positions after=pressure_clause,exclude=readout" in lines[1]
    assert "--task-from outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_" in lines[2]
    assert "--attention-conditions pressure --dla-conditions pressure" in lines[2] and "neutral_twin" not in lines[2]
    assert "standins/far_v2_nopressure" in lines[3]
    assert "outputs/_launch_mechanism_analysis/standins/far_v2_inversion" in lines[4]
    assert "--attention-conditions pressure,neutral_twin" in lines[4]
    seg = lines[5]
    assert "--knockout-groups docs/research/mechanism-analysis/phase2/groups/far_top20.json" in seg
    assert "--knockout-counterfactual neutral_twin --knockout-positions intro" in seg
    assert "--output-dir outputs/_analyses/mechanism-analysis-p2/seg_intro" in seg
    assert "attention" not in seg


# ------------------------------------------------------------------ the results builder

@pytest.fixture(scope="module")
def res():
    return _mod("p2_results")


def test_fisher_exact_rxc_matches_the_tea_tasting_table_and_a_hand_enumerated_2x3(res):
    assert res.fisher_exact_rxc([[3, 1], [1, 3]]) == pytest.approx(34 / 70)          # Fisher's tea tasting, two-sided
    assert res.fisher_exact_rxc([[2, 0, 0], [0, 1, 1]]) == pytest.approx(1 / 3)       # four tables: 1/6, 1/3, 1/3, 1/6
    assert res.fisher_exact_rxc([[3, 1], [1, 3], [0, 0]]) == pytest.approx(34 / 70)   # an empty row changes nothing
    assert res.fisher_exact_rxc([[3, 1, 0], [1, 3, 0]]) == pytest.approx(34 / 70)     # nor an empty column
    assert res.fisher_exact_rxc([[5, 0], [0, 0]]) == 1.0                              # one non-empty row: no test


def test_one_sided_binomial_is_the_upper_tail(res):
    assert res.binomial_upper_tail(3, 3, 0.5) == pytest.approx(0.125)
    assert res.binomial_upper_tail(0, 3, 0.5) == 1.0
    assert res.binomial_upper_tail(2, 2, 0.25) == pytest.approx(0.0625)
    assert res.binomial_upper_tail(3, 4, 10 / 32) == pytest.approx(4 * 0.3125 ** 3 * 0.6875 + 0.3125 ** 4)


def test_membership_columns_come_from_the_six_head_sets_and_the_operand(res):
    sets = _head_sets()
    prov = {"heads": ["head.9.19", "head.3.3"], "mlp_layers": [6, 7]}
    m = res.membership("far", sets, prov)
    assert m[("head", 17, 24)] == {"U": True, "S_k": False, "C_t": False, "core": True, "excl_t": False,
                                   "DmH_t": False, "DmH_minus_core_t": False, "HmD_t": False, "late_HmD_t": False}
    assert m[("head", 9, 19)]["S_k"] and m[("head", 9, 19)]["excl_t"] and m[("head", 9, 19)]["U"]
    assert m[("head", 3, 3)]["S_k"] and not m[("head", 3, 3)]["U"]                   # an S_k head outside U
    assert m[("head", 30, 3)]["HmD_t"] and m[("head", 30, 3)]["late_HmD_t"]
    assert m[("mlp", 6, 0)]["C_t"] and not m[("mlp", 6, 0)]["U"]
    assert ("mlp", 5, 0) not in m


def _row(layer, index, **cols):
    base = {"kind": "head", "layer": layer, "index": index}
    base.update(cols)
    return base


def test_b_reader_counts_signature_heads_in_layers_8_to_17_against_10_of_32(res):
    drop = "attention_patterns.clause_mass_drop_neutral_twin_paired"
    se = "attention_patterns.clause_mass_drop_neutral_twin_paired_se"
    rows = [_row(9, 1, **{drop: 0.10, se: 0.01}), _row(10, 2, **{drop: 0.06, se: 0.02}),
            _row(13, 5, **{drop: 0.20, se: 0.05}), _row(20, 3, **{drop: 0.30, se: 0.10}),
            _row(13, 20, **{drop: 0.04, se: 0.01}),       # below the floor
            _row(13, 21, **{drop: 0.10, se: 0.08}),       # under 2 SE
            _row(4, 0, **{drop: None, se: None})]         # unmeasured
    out = res.b_reader(rows, floor=0.05, z=2.0)
    assert out["n_signature"] == 4 and out["n_in_8_17"] == 3
    assert out["p"] == pytest.approx(4 * 0.3125 ** 3 * 0.6875 + 0.3125 ** 4)
    assert [h["label"] for h in out["signature_heads"]] == ["head.9.1", "head.10.2", "head.13.5", "head.20.3"]
    assert out["l13"]["head.13.5"]["signature"] is True and out["l13"]["head.13.20"]["signature"] is False
    assert out["l13"]["head.13.21"]["signature"] is False


def test_c_reads_tabulates_the_exclusives_top_segment_groups_and_runs_fisher(res):
    seg = "attention_patterns.pressure_top_segment"
    mass = "attention_patterns.pressure_top_mass"
    rows = {"far": [_row(9, 19, **{seg: "pressure_clause", mass: 0.4}),
                    _row(12, 1, **{seg: "designation_suffix", mass: 0.3}),
                    _row(17, 24, **{seg: "pressure_clause", mass: 0.9})],
            "sdr": [_row(5, 8, **{seg: "item_1_intro", mass: 0.5})],
            "ser": [_row(16, 2, **{seg: "question", mass: 0.2})]}
    excl = {"far": {("head", 9, 19), ("head", 12, 1)}, "sdr": {("head", 5, 8)}, "ser": {("head", 16, 2)}}
    out = res.c_reads(rows, excl)
    assert out["counts"] == {"far": {"pressure": 1, "designation": 1}, "sdr": {"item_mention": 1},
                             "ser": {"frame": 1}}
    assert out["groups"] == ["designation", "item_mention", "pressure", "frame"]
    assert out["table"] == [[1, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]
    assert 0 < out["p"] <= 1
    assert out["heads"]["far"][0] == {"label": "head.9.19", "segment": "pressure_clause", "group": "pressure",
                                      "mass": 0.4}


def _groups_json(members, drops, ses, *, n=10):
    return {"groups": [{"name": name, "members": [name] if name != "top20_joint" else list(members),
                        "mean_drop": d, "standard_error": s, "n": n, "accuracy": 1.0, "accuracy_drop": 0.0,
                        "knocked_logit_difference": 2.0 - d, "n_components": 1}
                       for name, d, s in zip(members, drops, ses)],
            "clean_run": {"mean_logit_difference": 2.0, "standard_error": 0.1, "accuracy": 1.0, "n_instances": n}}


def test_segment_matrix_asserts_exact_zero_before_the_clause_and_keeps_the_informative_segments(res):
    labels = ["head.9.29", "mlp.13.0"]
    cells = {"intro": _groups_json(labels, [0.0, 0.0], [0.0, 0.0]),
             "pressure_clause": _groups_json(labels, [0.8, 0.3], [0.1, 0.05]),
             "readout": _groups_json(labels, [0.2, 0.1], [0.05, 0.02])}
    mat = res.segment_matrix(cells)
    assert mat["head.9.29"]["pressure_clause"] == {"mean_drop": 0.8, "standard_error": 0.1, "accuracy_drop": 0.0}
    assert res.pre_clause_check(mat, ("intro",)) == {"ok": True, "max_abs_drop": 0.0, "nonzero": []}
    cells["intro"] = _groups_json(labels, [0.0, 1e-6], [0.0, 0.0])
    bad = res.pre_clause_check(res.segment_matrix(cells), ("intro",))
    assert bad["ok"] is False and bad["nonzero"] == [{"label": "mlp.13.0", "segment": "intro", "mean_drop": 1e-6}]


def test_c_honest_reads_the_late_h_minus_d_heads_in_the_honest_direction(res):
    d, twin = "dla.pressure", "dla.neutral_twin_paired"
    rows_d = [_row(30, 3, **{d: -0.02, twin: -0.10}), _row(22, 7, **{d: -0.12, twin: -0.10})]
    rows_h = [_row(30, 3, **{d: 0.15}), _row(22, 7, **{d: 0.05})]
    rows_f = [_row(30, 3, **{d: 0.11}), _row(22, 7, **{d: -0.01})]
    out = res.c_honest({("head", 30, 3), ("head", 22, 7)}, rows_d, rows_h, rows_f)
    h30 = out["heads"]["head.30.3"]
    # on D the metric is deceptive-positive, so the honest direction is the negation
    assert h30 == {"dla_H": 0.15, "dla_F": 0.11, "honest_dla_D_pressure": 0.02, "honest_dla_D_twin": 0.10,
                   "suppression": pytest.approx(0.8), "writes_honest_on_H_and_F": True, "suppressed": True}
    assert out["heads"]["head.22.7"]["suppressed"] is False
    assert out["heads"]["head.22.7"]["writes_honest_on_H_and_F"] is False
    assert out["n"] == 2 and out["n_writes_honest"] == 1 and out["n_suppressed"] == 1


def test_ct_proposal_is_core_excl_dmh_minus_core_sk_heads_and_at_most_ten_mlps(res):
    sets = _head_sets()
    deciding = {"heads": [("head", 9, 19), ("head", 3, 3)], "mlps": [("mlp", 6, 0)]}
    sweep_rank = ["mlp.13.0", "mlp.6.0", "mlp.14.0", "mlp.7.0"]
    out = res.ct_proposal("far", sets, deciding, sweep_rank, mlp_cap=3)
    assert set(out["heads"]) == {"head.17.24", "head.14.4", "head.9.19", "head.12.1", "head.3.3"}
    assert out["mlps"] == ["mlp.6.0", "mlp.13.0", "mlp.14.0"]          # the deciding set's first, then S2p rank
    assert out["sizes"] == {"core": 2, "excl_t": 2, "DmH_minus_core_t": 1, "S_k_heads": 2, "heads": 5, "mlps": 3,
                            "components": 8}


# ------------------------------------------------------------------ the roles pass on the phase-2 cells

def test_roles_argv_merges_the_phase_1_single_knockout_cells_per_test_set(res):
    import p2_roles
    d = p2_roles.roles_argv("far", "d", cell_dir="outputs/_analyses/mechanism-analysis-p2/d/Up__leaf/far_v2")
    assert d[:2] == ["roles", "outputs/_analyses/mechanism-analysis-p2/d/Up__leaf/far_v2"]
    assert d.count("--roles-merge-from") == 2
    assert "outputs/_analyses/mechanism-analysis-p1/s1/U__leaf/far_v2" in d
    assert "outputs/_analyses/mechanism-analysis-p1/s2p/U__leaf/far_v2" in d
    assert "--roles-b2-floor" in d and d[d.index("--roles-b2-floor") + 1] == "0.05"
    assert "--roles-allow-missing-views" in d                       # phase 2 has no path patching (phase 3 does)
    for cell, p1 in (("h", "s5"), ("f", "s6"), ("i", "s7")):
        argv = p2_roles.roles_argv("sdr", cell, cell_dir=f"x/{cell}")
        assert argv.count("--roles-merge-from") == 1
        assert f"outputs/_analyses/mechanism-analysis-p1/{p1}/U__leaf/sdr_v2" in argv


def test_cell_dir_picks_the_tasks_test_set_under_a_shared_cell_root(res, tmp_path):
    for name in ("far_v2", "sdr_v2", "ser_v2"):
        (tmp_path / "d" / "Up__leaf" / name).mkdir(parents=True)
    (tmp_path / "f" / "Up__leaf" / "far_v2_nopressure").mkdir(parents=True)
    assert res.cell_dir(str(tmp_path), "d", "sdr") == str(tmp_path / "d" / "Up__leaf" / "sdr_v2")
    assert res.cell_dir(str(tmp_path), "f", "far") == str(tmp_path / "f" / "Up__leaf" / "far_v2_nopressure")
    with pytest.raises(FileNotFoundError):
        res.cell_dir(str(tmp_path), "f", "sdr")
