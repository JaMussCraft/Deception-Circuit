"""Ticket 05 of mechanism-analysis: the phase-3 builders (outputs/_launch_mechanism_analysis/p3_*.py).

Seams (spec section 2.3, section 4 phase 3, R25 A, R28): the grid circuit C_t and its job line; the identity of C_t
with phase 1C's routing-check C_t; the A' adjudication (category per deciding-set head, weighted majority,
sub-reading, the routing condition); B-selector; where the pressure enters; the completeness share; the roles
merge table restricted to the phase-3 cell's rows.
"""

from __future__ import annotations

import importlib
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCH = os.path.join(REPO, "outputs", "_launch_mechanism_analysis")


def _mod(name):
    if LAUNCH not in sys.path:
        sys.path.insert(0, LAUNCH)
    return importlib.import_module(name)


@pytest.fixture(scope="module")
def jobs():
    return _mod("p3_jobs")


# ==============================================================================
# p3_jobs: C_t and the job line
# ==============================================================================

def test_the_expression_is_core_excl_and_dmh_minus_core_then_the_operand(jobs):
    assert jobs.expr("far") == "Ct=(((Df&Ds&De)|(Df-Ds-De)|((Df-Hf)-(Df&Ds&De)))-m)|X"
    assert jobs.expr("sdr") == "Ct=(((Df&Ds&De)|(Ds-Df-De)|((Ds-Hs)-(Df&Ds&De)))-m)|X"
    assert jobs.expr("ser") == "Ct=(((Df&Ds&De)|(De-Df-Ds)|((De-He)-(Df&Ds&De)))-m)|X"


def test_the_line_binds_the_operand_and_the_references(jobs):
    for counterfactual in ("neutral_twin", "item_swap"):
        argv = jobs.line("ser", counterfactual)
        joined = " ".join(argv)
        assert "X=outputs/_launch_mechanism_analysis/operands/skct_ser" in joined
        assert "--reference x_ser=outputs/_launch_mechanism_analysis/operands/skct_ser" in joined
        for u in ("far", "sdr", "ser"):
            assert f"--reference {u}_D=" in joined and f"--reference {u}_H=" in joined
        assert argv[argv.index("--task-from") + 1] == jobs.RUNS["ser"][0]
        assert argv[argv.index("--compose-granularity") + 1] == "leaf"
        # the default causal sample: no --n-causal or --seed override
        assert "--n-causal" not in argv and "--seed" not in argv


def test_the_twin_line_runs_its_segment_pass_at_the_floor_and_the_sweep(jobs):
    argv = jobs.line("far", "neutral_twin")
    assert argv[argv.index("--analyses") + 1] == "path_patching"
    assert argv[argv.index("--path-counterfactual") + 1] == "neutral_twin"
    assert argv[argv.index("--path-twin-position-threshold") + 1] == "0.01"
    assert "--path-completeness-sweep" in argv
    assert argv[argv.index("--output-dir") + 1] == "outputs/_analyses/mechanism-analysis-p3/d"


def test_the_item_swap_line_keeps_the_default_threshold_and_has_no_sweep(jobs):
    argv = jobs.line("far", "item_swap")
    assert argv[argv.index("--path-counterfactual") + 1] == "item_swap"
    assert "--path-position-threshold" not in argv and "--path-twin-position-threshold" not in argv
    assert "--path-completeness-sweep" not in argv
    assert argv[argv.index("--output-dir") + 1] == "outputs/_analyses/mechanism-analysis-p3/d_is"


def test_the_batch_file_runs_the_twin_first_and_the_cli_parses_both_lines(jobs):
    import shlex

    import analyze_components
    from component_analysis import path_patching as pp

    text = jobs.batch_text("sdr")
    lines = [one for one in text.splitlines() if one and not one.startswith("#")]
    assert len(lines) == 2
    twin, swap = (analyze_components.build_parser().parse_args(shlex.split(one)) for one in lines)
    assert twin.path_counterfactual == "neutral_twin" and swap.path_counterfactual == "item_swap"
    # the twin line sweeps under the twin (its one selected pair) with its Segment pass at 0.01
    ctx = type("C", (), {"cli": twin, "task_spec": type("T", (), {"name": "sdr_v2"})()})()
    assert pp.sweep_counterfactual(ctx) == pp.NEUTRAL_TWIN
    assert pp.position_threshold(ctx, pp.NEUTRAL_TWIN) == 0.01
    ctx_swap = type("C", (), {"cli": swap, "task_spec": type("T", (), {"name": "sdr_v2"})()})()
    assert pp.position_threshold(ctx_swap, pp.ITEM_SWAP) == 0.05
    assert twin.output_dir != swap.output_dir


def test_ct_sets_compose_the_parts(jobs):
    sets = {"D_far": {(1, 1), (2, 2), (3, 3)}, "D_sdr": {(1, 1), (4, 4)}, "D_ser": {(1, 1), (5, 5)},
            "H_far": {(3, 3)}, "H_sdr": set(), "H_ser": set()}
    operand = {"heads": ["head.9.9"], "members": ["head.9.9", "mlp.6.0"], "mlp_layers": [6, 7]}
    parts = jobs.ct_sets("far", sets, operand)
    assert parts["core"] == {"head.1.1"}
    assert parts["excl"] == {"head.2.2", "head.3.3"}
    assert parts["DmH_minus_core"] == {"head.2.2"}
    assert parts["mlps"] == {"mlp.6.0", "mlp.7.0"}
    assert parts["C_t"] == {"head.1.1", "head.2.2", "head.3.3", "head.9.9", "mlp.6.0", "mlp.7.0"}


def test_routing_identity_holds_only_for_the_exact_complement(jobs):
    universe = jobs.all_components(n_layers=2, n_heads=2)
    assert len(universe) == 6
    ct = {"head.0.0", "mlp.1.0"}
    route_c = [["head", 0, 1], ["head", 1, 0], ["head", 1, 1], ["mlp", 0, 0]]
    assert jobs.routing_identity(ct, route_c, universe)["identical"]
    off = jobs.routing_identity({"head.0.0"}, route_c, universe)
    assert not off["identical"] and off["only_in_prelim"] == ["mlp.1.0"]


# ==============================================================================
# p3_merge: the roles pass's merge tables, restricted to the phase-3 cell's rows
# ==============================================================================

@pytest.fixture(scope="module")
def merge():
    return _mod("p3_merge")


def test_restrict_keeps_only_the_wanted_rows_and_namespaces_with_their_coverage(merge):
    from component_analysis import head_table as ht

    rows = [{"kind": "head", "layer": 1, "index": 0, "kv_group": 0, "active_neuron_count": 9,
             "attention_patterns.pressure_top_segment": "stem", "dla.pressure": 0.1,
             "knockout.logit_diff_drop": 0.5, "roles.role_proposed": "mover", "reference.far_D": True},
            {"kind": "head", "layer": 2, "index": 3, "kv_group": 0, "dla.pressure": 0.2},
            {"kind": "mlp", "layer": 4, "index": 0, "kv_group": None, "dla.pressure": -0.3}]
    meta = ht.add_coverage({}, ["pressure"], ["a", "b"], instance_set="test_split", namespace="dla")
    meta = ht.add_coverage(meta, ["logit_diff_drop"], ["c"], instance_set="causal_sample", namespace="knockout")
    keys = [("mlp", 4, 0), ("head", 1, 0), ("head", 9, 9)]
    out, out_meta = merge.restrict_columns(rows, meta, keys)
    assert [ht.row_key(r) for r in out] == [("mlp", 4, 0), ("head", 1, 0)]   # keys order; absent key no row
    cols = {c for r in out for c in r}
    assert cols == {"kind", "layer", "index", "kv_group", "attention_patterns.pressure_top_segment", "dla.pressure"}
    assert set(out_meta[ht.COVERAGE_KEY]) == {"dla.pressure"}
    assert len(out_meta[ht.INSTANCE_SETS_KEY]) == 1


def test_a_merge_of_the_restricted_table_adds_no_row(merge, tmp_path):
    """The point of the restriction: `roles.merge_cells` appends rows it does not find."""
    from component_analysis import head_table as ht
    from component_analysis.roles import merge_cells

    src = [{"kind": "head", "layer": 1, "index": 0, "kv_group": 0, "dla.pressure": 0.1},
           {"kind": "head", "layer": 5, "index": 5, "kv_group": 1, "dla.pressure": 0.4}]
    p3 = [{"kind": "head", "layer": 1, "index": 0, "kv_group": 0, "head_gate_active": True,
           "active_neuron_count": 1, "path_patching.direct_support_neutral_twin_paired": 0.3}]
    out, meta = merge.restrict_columns(src, {}, [ht.row_key(r) for r in p3])
    ht.write_head_table(str(tmp_path / "m"), out, meta=meta)
    merged, _meta, _renamed = merge_cells(p3, [str(tmp_path / "m")], meta={})
    assert len(merged) == 1 and merged[0]["dla.pressure"] == 0.1
    # control: the unrestricted source does append its extra row, so the restriction is what prevents it
    ht.write_head_table(str(tmp_path / "raw"), src, meta={})
    merged_raw, _m, _r = merge_cells(p3, [str(tmp_path / "raw")], meta={})
    assert len(merged_raw) == 2


# ==============================================================================
# p3_logic: the A' adjudication (spec 2.3)
# ==============================================================================

@pytest.fixture(scope="module")
def logic():
    return _mod("p3_logic")


def heads(*triples):
    return [{"label": f"head.{n}.0", "category": c, "weight": w} for n, (c, w) in enumerate(triples)]


def test_the_call_is_the_category_with_more_than_half_the_weight(logic):
    out = logic.weighted_call(heads(("q", 3.0), ("kv_clause", 1.0), ("none", 1.0)))
    assert out["call"] == "q" and out["sub_reading"] == "A'-selector"
    assert out["shares"]["q"] == pytest.approx(0.6)
    # by weight, not by count: two light post-clause heads lose to one heavy clause reader
    out = logic.weighted_call(heads(("kv_post_clause", 1.0), ("kv_post_clause", 1.0), ("kv_clause", 3.0)))
    assert out["call"] == "kv_clause" and out["sub_reading"] == "A'-clause-reader"
    assert out["counts"]["kv_post_clause"] == 2


def test_exactly_half_is_mixed(logic):
    out = logic.weighted_call(heads(("q", 1.0), ("kv_post_clause", 1.0)))
    assert out["call"] is None and out["sub_reading"] == "A'-mixed"


def test_the_four_categories_name_the_four_sub_readings(logic):
    assert logic.weighted_call(heads(("kv_post_clause", 1.0)))["sub_reading"] == "A'-mover"
    assert logic.weighted_call(heads(("none", 1.0)))["sub_reading"] == "A'-unresolved"
    out = logic.weighted_call(heads(("kv_unresolved", 1.0)))
    assert out["sub_reading"] is None and "ruling" in out["note"]


def test_a_negative_weight_counts_as_zero_and_is_recorded(logic):
    out = logic.weighted_call(heads(("q", 1.0), ("kv_clause", -5.0)))
    assert out["shares"]["q"] == 1.0 and out["negative_weights_floored"] == ["head.1.0"]


def test_mover_and_unresolved_need_routing_share_c_at_most_a_quarter(logic):
    assert logic.routing_gate("A'-mover", 0.163)["final"] == "A'-mover"
    assert logic.routing_gate("A'-mover", 0.25)["final"] == "A'-mover"
    gate = logic.routing_gate("A'-unresolved", 0.297)
    assert gate["final"] == "A', route outside C_t" and gate["r14"]
    # selector and clause-reader are positive results: not gated
    assert logic.routing_gate("A'-selector", 0.9)["final"] == "A'-selector"
    assert logic.routing_gate("A'-mixed", 0.9)["final"] == "A'-mixed"


def test_adjudicate_counts_the_mlp_members_and_refuses_a_missing_category(logic):
    cats = {"head.9.1": {"category": "q", "support": 0.05, "se": 0.01, "path": "head.7.1->q.9.1"},
            "head.10.2": {"category": "kv_clause", "support": 0.02, "se": 0.005, "segment": "pressure_clause"}}
    out = logic.adjudicate(["head.9.1", "mlp.6.0", "head.10.2"], cats,
                           {"head.9.1": 1.0, "head.10.2": 0.5, "mlp.6.0": 2.0}, 0.1)
    assert out["mlp_members"] == ["mlp.6.0"] and out["n_heads"] == 2
    assert out["sub_reading"] == "A'-selector"
    assert out["heads"][0]["support"] == 0.05 and out["heads"][0]["se"] == 0.01
    with pytest.raises(ValueError, match="head.11.3"):
        logic.adjudicate(["head.11.3"], cats, {"head.11.3": 1.0}, 0.1)


# ==============================================================================
# p3_logic: receivers, B-selector, entry points, completeness
# ==============================================================================

RECEIVERS = [{"key": "q.17.24", "kind": "q", "layer": 17, "index": 24, "covers_heads": [24], "circuit_heads": [24]},
             {"key": "q.17.25", "kind": "q", "layer": 17, "index": 25, "covers_heads": [25], "circuit_heads": [25]},
             {"key": "k.17.6", "kind": "k", "layer": 17, "index": 6, "covers_heads": [24, 25, 26, 27],
              "circuit_heads": [24, 25]},
             {"key": "v.17.6", "kind": "v", "layer": 17, "index": 6, "covers_heads": [24, 25, 26, 27],
              "circuit_heads": [24, 25]},
             {"key": "readout", "kind": "readout", "layer": 32, "index": 0, "covers_heads": [], "circuit_heads": []}]


def acell(sender, receiver, mean, se=0.001):
    return {"sender": sender, "receiver": receiver, "cell": f"{sender}->{receiver}", "mean": mean, "se": se, "n": 100}


AGNOSTIC = {"receivers": RECEIVERS, "cells": [
    acell("head.13.22", "q.17.24", 0.04), acell("mlp.6.0", "q.17.24", -0.02), acell("embed", "q.17.24", 0.005),
    acell("head.13.22", "k.17.6", 0.03), acell("mlp.7.0", "v.17.6", 0.06), acell("head.13.22", "q.17.25", 0.001),
    acell("head.17.24", "readout", 0.2)]}
SEGMENTS = {"cells": [
    {"cell": "head.13.22->k.17.6", "top_segment": {"segment": "pressure_clause", "mean": 0.02}},
    {"cell": "mlp.7.0->v.17.6", "top_segment": {"segment": "response_line", "mean": 0.05}}]}


def test_receiver_totals_split_query_from_keys_and_values_over_the_floor(logic):
    out = logic.receiver_totals(AGNOSTIC, "head.17.24")
    assert out["q_n"] == 2 and out["q_signed"] == pytest.approx(0.02) and out["q_abs"] == pytest.approx(0.06)
    assert out["kv_n"] == 2 and out["kv_abs"] == pytest.approx(0.09)
    # head 25 shares the group's K/V cells, has its own (sub-floor) query cell
    out25 = logic.receiver_totals(AGNOSTIC, "head.17.25")
    assert out25["q_n"] == 0 and out25["kv_abs"] == pytest.approx(0.09)
    assert logic.strongest_kv(AGNOSTIC, "head.17.25")["cell"] == "mlp.7.0->v.17.6"


def test_b_selector_reads_clause_one_literally_and_reports_the_loose_reading(logic):
    base = {h: "none" for h in logic.L17_HEADS}
    by_task = {"far": dict(base, **{"head.17.24": "q", "head.17.25": "kv_clause", "head.24.1": "kv_post_clause"}),
               "sdr": dict(base, **{"head.17.25": "q", "head.24.1": "kv_post_clause"}),
               "ser": dict(base, **{"head.17.24": "none", "head.24.1": "q"})}
    out = logic.b_selector(by_task, {"far": ["head.24.1"], "sdr": ["head.24.1"], "ser": ["head.24.1"]})
    assert not out["clause1_literal"]            # no single head is q on two tasks
    assert out["clause1_loose"] and out["clause1_loose_tasks"] == ["far", "sdr"]
    assert out["clause2_tasks"] == ["far", "sdr"] and not out["clause2_all_tasks"]
    by_task["ser"]["head.17.24"] = "q"
    assert logic.b_selector(by_task, {"far": [], "sdr": [], "ser": []})["clause1_literal"]


def test_entry_points_place_kv_paths_by_their_split_and_q_paths_at_the_query(logic):
    out = logic.entry_points(AGNOSTIC, SEGMENTS)
    where = {c["cell"]: c["where"] for c in out["cells"]}
    assert where["head.13.22->k.17.6"] == "clause"
    assert where["mlp.7.0->v.17.6"] == "post_clause"
    assert where["head.13.22->q.17.24"] == "query_positions"
    assert "embed->q.17.24" not in where and "head.13.22->q.17.25" not in where   # under the floor
    assert out["senders"][0]["sender"] == "head.17.24"                           # strongest summed |mean|
    h = next(s for s in out["senders"] if s["sender"] == "head.13.22")
    assert h["n"] == 2 and h["abs_by_where"]["clause"] == pytest.approx(0.03)
    assert out["pre_clause_bug"] == []


def test_completeness_sums_the_direct_paths_outside_the_candidates(logic):
    sweep = {"flagged": ["head.20.1"], "senders": [
        {"sender": "embed", "mean": 0.01, "in_circuit": False},
        {"sender": "head.17.24", "mean": 0.3, "in_circuit": True},
        {"sender": "mlp.31.0", "mean": 0.2, "in_circuit": False},
        {"sender": "head.20.1", "mean": -0.05, "in_circuit": False}]}
    out = logic.completeness(sweep, ["head.17.24"])
    assert out["inside_signed"] == pytest.approx(0.3)
    assert out["outside_signed"] == pytest.approx(0.15) and out["outside_abs"] == pytest.approx(0.25)
    assert out["embed"] == 0.01 and out["membership_disagrees"] == []
    assert out["top_outside"][0]["sender"] == "mlp.31.0"
    assert logic.completeness(sweep, [])["membership_disagrees"] == ["head.17.24"]


# ==============================================================================
# p3_results: one fabricated task end to end (file shapes as the 02b smoke cell wrote them)
# ==============================================================================

METRIC = {"counterfactual": "neutral_twin", "convention": "positive_helps_deception", "convention_version": 2}


def _write(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        import json
        json.dump(payload, f)


def fake_task(tmp_path):
    from component_analysis import head_table as ht

    root, p1 = tmp_path / "p3", tmp_path / "p1"
    d = root / "d" / "Ct__leaf" / "far_v2"
    dis = root / "d_is" / "Ct__leaf" / "far_v2"
    rows = [{"kind": "head", "layer": 17, "index": i, "kv_group": 6, "head_gate_active": True,
             "active_neuron_count": 1, "roles.role_proposed": "unknown"} for i in (24, 25, 26, 27)]
    rows += [{"kind": "head", "layer": 13, "index": 22, "kv_group": 5, "head_gate_active": True,
              "active_neuron_count": 1, "roles.role_proposed": "pressure reader"},
             {"kind": "mlp", "layer": 7, "index": 0, "kv_group": None, "head_gate_active": None,
              "active_neuron_count": 1, "roles.role_proposed": "unknown"},
             {"kind": "head", "layer": 20, "index": 1, "kv_group": None, "head_gate_active": None,
              "active_neuron_count": None}]        # appended by the sweep
    ht.write_head_table(str(d), rows, meta={"task": {"task": "far_v2"}})
    receivers = RECEIVERS + [{"key": "k.17.6", "kind": "k", "layer": 17, "index": 6, "covers_heads": [24, 25, 26, 27],
                              "circuit_heads": [24, 25, 26, 27]}]
    receivers = [r for r in receivers if r["key"] not in ("k.17.6", "v.17.6")] + [
        {"key": k, "kind": k[0], "layer": 17, "index": 6, "covers_heads": [24, 25, 26, 27],
         "circuit_heads": [24, 25, 26, 27]} for k in ("k.17.6", "v.17.6")]
    agn = {"receivers": receivers, "cells": AGNOSTIC["cells"], "sample": {"n_instances": 100, "n_excluded_by_gap": 0},
           "gap": {"mean": 5.0}, "cost": {"forwards": 10}, "metric": METRIC}
    _write(str(d / "path_patching" / "agnostic_neutral_twin.json"), agn)
    _write(str(d / "path_patching" / "segments_neutral_twin.json"), {**SEGMENTS, "threshold": 0.01, "n_selected": 2})
    _write(str(d / "path_patching" / "receiver_category_neutral_twin.json"), {
        "counts": {"q": 1}, "heads": [
            {"key": ["head", 17, 24], "category": "q", "path": "head.13.22->q.17.24", "support": 0.04, "se": 0.001,
             "segment": None, "note": ""},
            {"key": ["head", 17, 25], "category": "kv_post_clause", "path": "mlp.7.0->v.17.6", "support": 0.06,
             "se": 0.001, "segment": "response_line", "note": ""},
            {"key": ["head", 17, 26], "category": "q", "path": "head.13.22->q.17.26", "support": 0.02, "se": 0.001,
             "segment": None, "note": ""},
            {"key": ["head", 17, 27], "category": "none", "path": None, "support": None, "se": None,
             "segment": None, "note": ""},
            {"key": ["head", 13, 22], "category": "none", "path": None, "support": None, "se": None,
             "segment": None, "note": ""}]})
    _write(str(d / "path_patching" / "sweep_neutral_twin.json"), {
        "counterfactual": "neutral_twin", "flagged": ["head.20.1"], "sample": {"same_as_grid": True},
        "metric": METRIC,
        "senders": [{"sender": "embed", "mean": 0.0, "in_circuit": False},
                    {"sender": "head.17.24", "mean": 0.2, "in_circuit": True},
                    {"sender": "head.20.1", "mean": 0.05, "in_circuit": False}]})
    _write(str(d / "roles" / "roles.json"), {"counts": {"pressure reader": 1, "unknown": 5}, "missing_views": []})
    ht.write_head_table(str(dis), rows[:6], meta={})
    _write(str(dis / "path_patching" / "agnostic.json"), {"cells": [], "sample": {"n_instances": 100},
                                                          "metric": METRIC})
    _write(str(p1 / "s2p" / "U__leaf" / "far_v2" / "knockout" / "sweep.json"), {"components": [
        {"label": "head.17.24", "mean_drop": 1.0}, {"label": "head.13.22", "mean_drop": 0.5},
        {"label": "mlp.7.0", "mean_drop": 2.0}]})
    members = {"core": ["head.17.24", "head.17.25", "head.17.26", "head.17.27"], "excl": [], "DmH_minus_core": [],
               "S_k_heads": ["head.17.24", "head.13.22"], "S_k": ["head.17.24", "head.13.22", "mlp.7.0"],
               "mlps": ["mlp.7.0"]}
    members["C_t"] = sorted(set(members["core"]) | {"head.13.22", "mlp.7.0"})
    ct = {"tasks": {"far": {"members": members, "candidate": "greedy_k20",
                            "routing_shares": {"a_all_mlps": 0.2, "b_heads_outside_C": 0.2, "c_all_outside_C": 0.163}}}}
    readings = {"rab": {"far": {"reading": "A'", "deciding": "greedy_k20"}}}
    return str(root), str(p1), ct, readings


def test_results_end_to_end_on_a_fabricated_task(tmp_path):
    res = _mod("p3_results")
    root, p1, ct, readings = fake_task(tmp_path)
    r = res.task_results("far", root, p1, ct, readings)
    a = r["a_prime"]
    assert a["n_heads"] == 2 and a["mlp_members"] == ["mlp.7.0"]
    assert a["weighted"]["shares"]["q"] == pytest.approx(1.0 / 1.5)
    assert a["sub_reading"] == "A'-selector" and a["status"].startswith("pre-registered")
    assert r["b_selector_heads"]["head.17.25"]["category"] == "kv_post_clause"
    assert r["b_selector_heads"]["head.17.26"]["strongest_kv"]["cell"] == "mlp.7.0->v.17.6"
    assert r["checks"]["sweep_counterfactual"] == "neutral_twin"
    assert r["checks"]["rows_outside_C_t"] == ["head.20.1"]
    assert r["completeness"]["outside_signed"] == pytest.approx(0.05)
    # S_k is the first part a Component is counted under (its MLP member included); the sweep-appended row apart
    assert r["roles_by_part"]["S_k"] == {"unknown": 2, "pressure reader": 1}
    assert r["roles_by_part"]["core"] == {"unknown": 3}
    assert r["roles_by_part"]["outside_C_t"] == {None: 1}
    results = {"b_selector": _mod("p3_logic").b_selector(
        {"far": {k: v["category"] for k, v in r["b_selector_heads"].items()}}, {"far": r["core_l24"]}),
        "tasks": {"far": r}}
    text = res.markdown(results)
    assert "A'-selector" in text and "head.13.22" in text
    res.write_curated(str(tmp_path / "curated"), root, results)
    for name in ("categories.csv", "a_prime.csv", "b_selector.csv", "entry_paths.csv", "completeness.csv",
                 "roles_by_part.csv", "p3_readings.json", "far_head_table.csv", "roles/far.json",
                 "roles_cross_task.csv"):
        assert os.path.isfile(tmp_path / "curated" / name), name
    assert "robustness" in r["a_prime"] and "Cross-task roles" in text


# ==============================================================================
# Exploratory: robustness of the call, cross-task roles (C3)
# ==============================================================================

def rhead(label, category, weight, support, path, q_abs=0.0, kv_abs=0.0):
    return {"label": label, "category": category, "weight": weight, "support": support, "path": path,
            "q_abs": q_abs, "kv_abs": kv_abs}


def test_robustness_recomputes_the_call_three_ways_and_counts_kv_groups(logic):
    hs = [rhead("head.9.29", "kv_clause", 2.0, 0.05, "mlp.6.0->k.9.7", q_abs=0.01, kv_abs=0.2),
          rhead("head.9.31", "kv_clause", 1.0, -0.015, "mlp.6.0->k.9.7", q_abs=0.0, kv_abs=0.1),
          rhead("head.9.16", "q", 1.0, 0.03, "mlp.8.0->q.9.16", q_abs=0.03, kv_abs=0.02),
          rhead("head.11.27", "none", 1.0, None, None)]
    out = logic.robustness(hs)
    # strongest path opposing the pressured answer counts as none: kv_clause keeps 2 of 5
    assert out["positive_path_only"]["shares"]["kv_clause"] == pytest.approx(0.4)
    assert out["positive_path_only"]["call"] is None
    # at twice the floor the -0.015 path drops out as well
    assert out["floor_x2"]["shares"]["kv_clause"] == pytest.approx(0.4)
    # Q total vs K+V total per head: head.9.31 and head.9.29 are K/V, head.9.16 Q, head.11.27 neither
    assert out["totals"]["shares"]["kv"] == pytest.approx(0.6) and out["totals"]["call"] == "kv"
    # head.9.29 and head.9.31 share KV group 9.7: one test, not two
    assert out["kv_clause_heads"] == 2 and out["kv_clause_groups"] == 1


def test_cross_task_roles_line_up_each_component_over_the_tasks():
    res = _mod("p3_results")
    def row(t, label, part, role, cat):
        return {"task": t, "label": label, "part": part, "role": role, "category": cat}
    results = {"tasks": {
        "far": {"table": [row("far", "head.17.24", "core", "selector", "q"),
                          row("far", "head.9.29", "S_k", "pressure reader", "kv_clause"),
                          row("far", "mlp.31.0", "outside_C_t", "unknown", None)]},
        "sdr": {"table": [row("sdr", "head.17.24", "core", "selector", "q")]},
        "ser": {"table": [row("ser", "head.17.24", "core", "unknown", "q"),
                          row("ser", "head.9.29", "S_k", "pressure reader", "kv_clause")]}}}
    rows, summary = res.cross_task_roles(results)
    by = {r["label"]: r for r in rows}
    assert by["head.17.24"]["n_tasks_in_C_t"] == 3 and by["head.17.24"]["same_role"] is False
    assert by["head.17.24"]["role_sdr"] == "selector" and by["head.17.24"]["role_ser"] == "unknown"
    assert by["head.9.29"]["n_tasks_in_C_t"] == 2 and by["head.9.29"]["same_role"] is True
    assert by["head.9.29"]["role_sdr"] is None
    # a sweep-appended row is not in C_t
    assert by["mlp.31.0"]["n_tasks_in_C_t"] == 0
    assert summary["in_all_three"] == 1 and summary["same_role_all_three"] == 0
    assert summary["in_two_or_more"] == 2


def test_same_role_is_not_claimed_when_no_role_was_proposed():
    res = _mod("p3_results")
    row = {"label": "head.1.0", "part": "core", "role": None, "category": "q"}
    results = {"tasks": {t: {"table": [dict(row, task=t)]} for t in ("far", "sdr", "ser")}}
    rows, summary = res.cross_task_roles(results)
    assert rows[0]["same_role"] is None and summary["same_role_all_three"] == 0


# ==============================================================================
# Review fixes (05-review.md): no silent fallback, labels, guards
# ==============================================================================

def test_a_positive_path_under_twice_the_floor_drops_only_at_floor_x2(logic):
    hs = [rhead("head.9.1", "kv_clause", 1.0, 0.015, "mlp.6.0->k.9.0", kv_abs=0.015),
          rhead("head.9.2", "q", 1.0, 0.05, "mlp.6.0->q.9.2", q_abs=0.05)]
    out = logic.robustness(hs)
    assert out["positive_path_only"]["shares"]["kv_clause"] == pytest.approx(0.5)
    assert out["floor_x2"]["shares"]["kv_clause"] == 0.0


def test_unsegmented_kv_arrivals_are_post_clause_by_construction(logic):
    """Pre-clause positions are identical in D and its twin, so an `unsegmented` top Segment can only be the
    post-clause template tokens (spec review 2)."""
    seg = {"cells": SEGMENTS["cells"] + [{"cell": "head.13.22->k.17.6", "top_segment": {"segment": "unsegmented"}}]}
    seg["cells"] = [c for c in seg["cells"] if not (c["cell"] == "head.13.22->k.17.6"
                                                   and c["top_segment"]["segment"] == "pressure_clause")]
    out = logic.entry_points(AGNOSTIC, seg)
    where = {c["cell"]: c["where"] for c in out["cells"]}
    assert where["head.13.22->k.17.6"] == "post_clause_unsegmented"


def test_adjudicate_refuses_a_head_whose_category_is_null(logic):
    with pytest.raises(ValueError, match="head.9.1"):
        logic.adjudicate(["head.9.1"], {"head.9.1": {"category": None}}, {"head.9.1": 1.0}, 0.1)


def test_no_positive_weight_has_its_own_note(logic):
    out = logic.weighted_call(heads(("q", -1.0), ("kv_clause", -2.0)))
    assert out["sub_reading"] == "A'-mixed" and "no positive" in out["note"]


def test_b_selector_refuses_a_missing_l17_or_core_l24_category(logic):
    full = {h: "q" for h in logic.L17_HEADS}
    with pytest.raises(ValueError, match="head.17.27"):
        logic.b_selector({"far": {h: "q" for h in logic.L17_HEADS[:3]}}, {"far": []})
    with pytest.raises(ValueError, match="head.24.1"):
        logic.b_selector({"far": full}, {"far": ["head.24.1"]})
    with pytest.raises(ValueError, match="head.17.24"):
        logic.b_selector({"far": dict(full, **{"head.17.24": None})}, {"far": []})


def test_completeness_counts_unmeasured_senders_and_drops_the_direct_sum_ratio(logic):
    sweep = {"senders": [{"sender": "head.17.24", "mean": None, "in_circuit": True},
                         {"sender": "mlp.31.0", "mean": 0.2, "in_circuit": False}]}
    out = logic.completeness(sweep, ["head.17.24"])
    assert out["unmeasured_inside"] == ["head.17.24"] and out["unmeasured_outside"] == []
    assert "outside_share_of_signed_total" not in out


def test_a_b_task_gets_a_descriptive_label_not_a_sub_reading(tmp_path):
    res = _mod("p3_results")
    root, p1, ct, readings = fake_task(tmp_path)
    readings["rab"]["far"] = {"reading": "B", "deciding": "single_k20"}
    a = res.task_results("far", root, p1, ct, readings)["a_prime"]
    assert a["sub_reading"] == "descriptive: q-dominated" and a["shape"] == "A'-selector"


def test_results_refuse_a_legacy_sign_file(tmp_path):
    import json
    res = _mod("p3_results")
    root, p1, ct, readings = fake_task(tmp_path)
    path = os.path.join(root, "d", "Ct__leaf", "far_v2", "path_patching", "agnostic_neutral_twin.json")
    with open(path) as f:
        payload = json.load(f)
    payload.pop("metric")
    _write(path, payload)
    with pytest.raises(ValueError, match="convention"):
        res.task_results("far", root, p1, ct, readings)


def test_results_refuse_a_missing_twin_segment_pass(tmp_path):
    res = _mod("p3_results")
    root, p1, ct, readings = fake_task(tmp_path)
    os.remove(os.path.join(root, "d", "Ct__leaf", "far_v2", "path_patching", "segments_neutral_twin.json"))
    with pytest.raises(FileNotFoundError):
        res.task_results("far", root, p1, ct, readings)


def test_role_counts_are_over_c_t_with_the_sweep_rows_apart(tmp_path):
    res = _mod("p3_results")
    root, p1, ct, readings = fake_task(tmp_path)
    r = res.task_results("far", root, p1, ct, readings)
    assert r["roles"]["counts_C_t"] == {"unknown": 5, "pressure reader": 1}
    assert r["roles"]["outside_C_t"] == [{"label": "head.20.1", "role": None}]


def test_the_report_refuses_a_task_subset():
    res = _mod("p3_results")
    with pytest.raises(SystemExit, match="all three"):
        res.main(["--tasks", "far"])


def test_roles_argv_merges_the_three_sources_in_order():
    roles = _mod("p3_roles")
    argv = roles.roles_argv("sdr", "R")
    assert argv[:2] == ["roles", "R/d/Ct__leaf/sdr_v2"]
    assert [argv[i + 1] for i, a in enumerate(argv) if a == "--roles-merge-from"] == [
        "R/_merge/sdr_p2d", "R/_merge/sdr_ko", "R/d_is/Ct__leaf/sdr_v2"]
    assert argv[argv.index("--roles-b2-floor") + 1] == "0.05" and "--roles-allow-missing-views" not in argv
    assert roles.roles_argv("sdr", "R", allow_missing=True)[-1] == "--roles-allow-missing-views"


def test_roles_retry_only_on_the_missing_view_refusal():
    roles = _mod("p3_roles")
    assert roles.missing_view_refusal(SystemExit("cell 'x' has no column at all for: dla (dla)"))
    assert not roles.missing_view_refusal(SystemExit("no such cell"))
    assert not roles.missing_view_refusal(SystemExit(2))
