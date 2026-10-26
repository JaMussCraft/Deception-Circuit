"""The roles pass on a v2 cell: the Neutral-Clause Twin as the paired counterfactual, rule 4b (pressure reader),
`response_line` in `frame` (ticket 02b; docs/component-roles.md, amendment of 2026-10-25; spec rulings R1, R7).

A cell is a v2 cell when its head table's `meta.task.task` is one of `dataloaders.V2_TASKS`. Everything a v1 cell
writes is unchanged, which `tests/test_v1_snapshot_02b.py` enforces byte for byte; the tests here assert the v1
side only where the two variants have to differ.
"""
from __future__ import annotations

import json
import os

import pytest

from component_analysis import path_patching as pp
from component_analysis import roles
from component_analysis.head_table import load_head_table, write_head_table
from tests.test_roles import a_binder, a_mover, a_selector, a_suppressor, knocked, merged, native, reads, row, \
    writes

CELL = ("suite", "dmh__leaf", "sdr_v2")


# ==============================================================================
# ROWS: the v2 columns, by the names the analyses write them under
# ==============================================================================

def twin_paths(incoming=None, incoming_support=None, direct=None, direct_se=None):
    """Path patching under the Neutral-Clause Twin, native sign (positive helps deception)."""
    return {roles.INCOMING_TWIN: incoming, roles.INCOMING_TWIN_SUPPORT: incoming_support,
            roles.DIRECT_SUPPORT_TWIN: direct, roles.DIRECT_SUPPORT_TWIN_SE: direct_se}


def b2(drop, se, twin_segment="pressure_clause"):
    """The B2 signature: Readout-query mass on the clause under D minus under the twin, paired."""
    return {roles.B2_DROP: drop, roles.B2_DROP_SE: se, roles.TWIN_TOP_SEGMENT: twin_segment}


def post_clause(drop, se):
    """The neutral-twin knockout at post-clause positions (1B's S2p)."""
    return {roles.KNOCKOUT_POST: drop, roles.KNOCKOUT_POST_SE: se}


def category(name, path=None, support=None, se=None, segment=None):
    return {roles.RECEIVER_CATEGORY: name, f"{roles.RECEIVER_CATEGORY}_path": path,
            f"{roles.RECEIVER_CATEGORY}_support": support, f"{roles.RECEIVER_CATEGORY}_se": se,
            f"{roles.RECEIVER_CATEGORY}_segment": segment}


def v2(one):
    """A v1 fixture row as a v2 cell carries it: native path columns, no honest-instruction columns."""
    out = native(one)
    return {column: value for column, value in out.items() if "honest_instruction" not in column}


def a_pressure_reader(layer=17, index=25, **kwargs):
    """L17H25 (KV group 6) reading the clause under D and not under its twin, carrying the pressure post-clause,
    the pressure arriving at its group's keys from the clause span."""
    return merged(reads("pressure_clause", 0.45), writes(0.012, 0.004),
                  knocked(0.21, 0.03),
                  v2({"path_patching.direct_effect": -0.004, "path_patching.direct_effect_se": 0.003,
                      "path_patching.strongest_outgoing": "head.17.25->q.24.18",
                      "path_patching.strongest_outgoing_effect": -0.03}),
                  b2(0.12, 0.02), post_clause(0.30, 0.05),
                  twin_paths(incoming="head.9.12->k.17.6", incoming_support=0.03, direct=0.002, direct_se=0.003),
                  category("kv_clause", path="head.9.12->k.17.6", support=0.03, se=0.004, segment="pressure_clause"),
                  layer=layer, index=index, **kwargs)


def a_v2_selector(**kwargs):
    """The v1 selector fixture with the twin at its own query instead of the honest instruction."""
    return merged(v2(a_selector()),
                  twin_paths(incoming="head.14.22->q.17.25", incoming_support=0.021, direct=0.02, direct_se=0.002),
                  category("q", path="head.14.22->q.17.25", support=0.021, se=0.002),
                  layer=17, index=25, **kwargs)


def propose_v2(one, thresholds=None):
    return roles.propose(one, thresholds or roles.Thresholds(), variant=roles.V2)


def propose_v1(one, thresholds=None):
    return roles.propose(one, thresholds or roles.Thresholds())


# ==============================================================================
# WHICH VARIANT A CELL IS
# ==============================================================================

@pytest.mark.parametrize("task", ["far_v2", "sdr_v2", "ser_v2"])
def test_a_v2_task_in_the_head_table_meta_selects_the_v2_variant(task):
    assert roles.variant_of({"task": {"label": task, "task": task}}) is roles.V2


@pytest.mark.parametrize("meta", [{"task": {"label": "sdr", "task": "sdr"}}, {"task": {"name": "sdr"}}, {}, None])
def test_anything_else_is_the_v1_variant(meta):
    assert roles.variant_of(meta) is roles.V1


def test_the_v1_variant_is_the_default_and_its_views_carry_no_v2_key():
    """The v1 roles JSON is byte-identical to before 02b; no new key may appear in its views."""
    decision = propose_v1(a_selector())
    assert decision == roles.propose(a_selector(), roles.Thresholds(), variant=roles.V1)
    assert "paired_at_own_query" not in decision.views["depends"]
    assert "b2_drop" not in decision.views["reads"]
    assert "pressure reader" not in decision.criteria
    assert roles.Thresholds().as_dict() == {"z": 2.0, "dla_floor": 0.01, "knockout_floor": 0.01,
                                             "path_floor": 0.01, "attention_floor": 0.20}


def test_response_line_is_a_frame_segment():
    assert roles.segment_group("response_line") == "frame"
    assert roles.SEGMENT_GROUPS["response_line"] == "frame"


# ==============================================================================
# RULE 4 READS THE TWIN ON A V2 CELL
# ==============================================================================

def test_rule_4_reads_the_twin_at_the_component_s_own_query_on_a_v2_cell():
    selector = a_v2_selector()
    assert propose_v2(selector).role == "selector"
    # The same row read as v1 has no honest-instruction path, so the query clause fails.
    assert propose_v1(selector).role != "selector"
    assert propose_v1(selector).criteria["selector"]["query"] is False


def test_a_twin_path_at_another_component_s_query_does_not_make_a_selector():
    elsewhere = a_v2_selector() | twin_paths(incoming="head.14.22->q.17.24", incoming_support=0.021)
    assert propose_v2(elsewhere).criteria["selector"]["query"] is False


def test_the_evidence_line_names_the_twin_not_the_instruction_on_a_v2_cell():
    notes = propose_v2(a_v2_selector()).notes
    assert "neutral twin in head.14.22->q.17.25" in notes
    assert "honest instruction" not in notes
    assert "honest instruction in" in propose_v1(a_selector()).notes


def test_rule_6_s_last_clause_reads_the_twin_on_a_v2_cell():
    """A knockout-only candidate whose twin path lands at its own query has a path above the floor."""
    from tests.test_roles import knockout_alone

    candidate = v2(knockout_alone()) | twin_paths(incoming="head.4.3->q.5.8", incoming_support=0.02)
    decision = propose_v2(candidate)
    assert decision.flavour != roles.KNOCKOUT_ONLY
    assert propose_v2(v2(knockout_alone())).flavour == roles.KNOCKOUT_ONLY


# ==============================================================================
# RULE 4b: PRESSURE READER
# ==============================================================================

def test_a_pressure_reader_reads_the_clause_only_under_pressure_carries_it_post_clause_and_takes_it_at_its_keys():
    decision = propose_v2(a_pressure_reader())
    assert decision.role == "pressure reader"
    assert decision.flavour is None
    assert decision.criteria["pressure reader"] == {"reads": True, "depends": True, "where": True}
    assert decision.notes.startswith("pressure reader: ")


def test_without_path_data_the_role_is_assigned_with_the_attention_and_knockout_only_flavour():
    no_paths = {column: value for column, value in a_pressure_reader().items()
                if not column.startswith(roles.RECEIVER_CATEGORY) and column not in twin_paths()}
    decision = propose_v2(no_paths)
    assert decision.role == "pressure reader"
    assert decision.flavour == roles.ATTENTION_AND_KNOCKOUT_ONLY
    assert decision.notes.startswith("pressure reader/attention and knockout only: ")
    assert decision.views["depends"]["twin_paths_measured"] is False


def test_a_b2_drop_without_a_post_clause_knockout_is_not_a_pressure_reader_and_is_noted():
    decision = propose_v2(a_pressure_reader() | post_clause(0.004, 0.003))
    assert decision.role != "pressure reader"
    assert "pressure-reader signature (B2), knockout silent post-clause" in decision.notes


def test_a_b2_drop_inside_its_floor_is_not_a_read_however_tight_its_error():
    tight = a_pressure_reader() | b2(0.03, 0.001)
    assert propose_v2(tight).role != "pressure reader"
    assert propose_v2(tight, roles.Thresholds(b2_floor=0.02)).role == "pressure reader"


def test_the_b2_floor_is_the_spec_s_proposal_and_needs_two_standard_errors():
    assert roles.Thresholds().b2_floor == 0.05
    assert propose_v2(a_pressure_reader() | b2(0.12, 0.08)).role != "pressure reader"


def test_the_pressure_arriving_from_post_clause_positions_is_not_a_pressure_reader_and_is_noted():
    mover_like = a_pressure_reader() | category("kv_post_clause", path="head.9.12->v.17.6", support=0.03,
                                                 se=0.004, segment="item_1_question_option") \
        | twin_paths(incoming="head.9.12->v.17.6", incoming_support=0.03)
    decision = propose_v2(mover_like)
    assert decision.role != "pressure reader"
    assert decision.criteria["pressure reader"]["where"] is False
    assert "post-clause" in decision.notes


def test_an_unresolved_or_absent_category_with_path_data_present_fails_the_where_clause():
    for name in ("kv_unresolved", "none"):
        decision = propose_v2(a_pressure_reader() | category(name))
        assert decision.role != "pressure reader", name
        assert decision.criteria["pressure reader"]["where"] is False


def test_the_strongest_twin_path_must_land_on_this_head_s_own_kv_group():
    other_group = a_pressure_reader() | twin_paths(incoming="head.9.12->k.17.3", incoming_support=0.03) \
        | category("kv_clause", path="head.9.12->k.17.3", support=0.03, se=0.004, segment="pressure_clause")
    assert propose_v2(other_group).criteria["pressure reader"]["where"] is False


def test_b2_columns_that_were_never_measured_are_named_not_failed():
    unmeasured = {column: value for column, value in a_pressure_reader().items()
                  if column not in b2(0, 0)}
    decision = propose_v2(unmeasured)
    assert decision.role != "pressure reader"
    assert "not measured" in decision.notes and "B2" in decision.notes


def test_a_suppressor_is_still_a_suppressor_when_it_also_carries_the_b2_signature():
    """The check order puts suppressor and binder before rule 4b, selector before it, mover after."""
    assert roles.CHECK_ORDER_V2 == ("suppressor", "binder", "selector", "pressure reader", "mover")
    both = v2(a_suppressor()) | b2(0.12, 0.02) | post_clause(0.3, 0.05)
    assert propose_v2(both).role == "suppressor"


def test_a_v1_cell_never_assigns_the_reserved_role_even_with_the_v2_columns_present():
    assert propose_v1(a_pressure_reader()).role != "pressure reader"
    assert roles.V1.reserved == ("pressure reader",) and roles.V2.reserved == ()


def test_on_a_v2_cell_the_b2_note_replaces_the_honest_instruction_signature_note():
    noted = a_pressure_reader() | category("none")
    decision = propose_v2(noted)
    assert "pressure-reader signature (B2)" in decision.notes
    assert "under the instruction" not in decision.notes


# ==============================================================================
# THE TWIN'S PATH COLUMNS HAVE NO LEGACY GENERATION
# ==============================================================================

def test_the_twin_path_reads_have_no_legacy_column_and_are_read_natively():
    assert roles.PATH_READS["incoming_neutral_twin_support"] == (roles.INCOMING_TWIN_SUPPORT, None)
    assert roles.path_value(a_pressure_reader(), "incoming_neutral_twin_support") == pytest.approx(0.03)
    assert roles.path_value(a_pressure_reader(), "direct_support_neutral_twin_paired") == pytest.approx(0.002)
    assert roles.generations_of([a_pressure_reader()]) == [pp.CONVENTION]
    assert roles.MARKED_BY[pp.NEUTRAL_TWIN] == roles.PATH_READS["direct_support_neutral_twin_paired"]


# ==============================================================================
# THE CLI SEAM ON A V2 CELL
# ==============================================================================

def write_agnostic(cell_dir, counterfactual, convention):
    metric = (pp.metric_meta(counterfactual) if convention == pp.CONVENTION
              else {"effect": "(patched - clean) / (clean - corrupt)"})
    directory = os.path.join(cell_dir, pp.SUBDIR)
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, pp.output_name(pp.AGNOSTIC_STEM, counterfactual, "json")), "w") as handle:
        json.dump({"counterfactual": counterfactual, "metric": metric}, handle)


@pytest.fixture
def v2_cell(tmp_path):
    path = os.path.join(str(tmp_path), *CELL)
    write_head_table(path, [v2(a_binder()), a_v2_selector(), v2(a_mover()), v2(a_suppressor()),
                            a_pressure_reader(layer=17, index=24)],
                     meta={"circuit": {"label": "dmh__leaf"}, "task": {"label": "sdr_v2", "task": "sdr_v2"}})
    write_agnostic(path, pp.ITEM_SWAP, pp.CONVENTION)
    write_agnostic(path, pp.NEUTRAL_TWIN, pp.CONVENTION)
    return path


def run_roles(*argv):
    import analyze_components

    return analyze_components.main(["roles", *argv])


def read(path, *parts):
    with open(os.path.join(path, *parts)) as handle:
        return json.load(handle)


def by_key(rows):
    return {(r["kind"], r["layer"], r["index"]): r for r in rows}


def test_the_subcommand_assigns_the_role_on_a_v2_cell_and_records_the_variant(v2_cell):
    assert run_roles(v2_cell) == 0

    table = by_key(load_head_table(v2_cell))
    assert table[("head", 17, 24)]["roles.role_proposed"] == "pressure reader"
    assert table[("head", 17, 25)]["roles.role_proposed"] == "selector"
    payload = read(v2_cell, roles.SUBDIR, roles.JSON_NAME)
    assert payload["variant"] == "v2"
    assert payload["paired_counterfactual"] == pp.NEUTRAL_TWIN
    assert payload["reserved"] == []
    assert "pressure reader" in payload["vocabulary"]
    assert payload["thresholds"]["b2_floor"] == 0.05
    assert payload["counts"]["pressure reader"] == 1 and payload["counts"]["selector"] == 1
    assert read(v2_cell, "head_table.json")["meta"]["roles"]["variant"] == "v2"


def test_the_b2_floor_flag_changes_the_proposal(v2_cell):
    rows = load_head_table(v2_cell)
    for one in rows:
        if one["layer"] == 17 and one["index"] == 24:
            one.update(b2(0.03, 0.001))
    write_head_table(v2_cell, rows, meta=read(v2_cell, "head_table.json")["meta"])

    run_roles(v2_cell)
    assert by_key(load_head_table(v2_cell))[("head", 17, 24)]["roles.role_proposed"] != "pressure reader"
    run_roles(v2_cell, "--roles-b2-floor", "0.02")
    assert by_key(load_head_table(v2_cell))[("head", 17, 24)]["roles.role_proposed"] == "pressure reader"
    assert read(v2_cell, roles.SUBDIR, roles.JSON_NAME)["thresholds"]["b2_floor"] == 0.02


def test_a_v1_cell_s_json_records_neither_the_variant_nor_the_b2_floor(tmp_path):
    """What the byte-identity snapshot enforces on a real v1 cell, stated on the fixture."""
    path = os.path.join(str(tmp_path), "suite", "delta__head", "sdr")
    write_head_table(path, [a_binder(), a_selector(), a_mover(), a_suppressor()],
                     meta={"circuit": {"label": "delta__head"}, "task": {"label": "sdr", "task": "sdr"}})
    assert run_roles(path) == 0

    payload = read(path, roles.SUBDIR, roles.JSON_NAME)
    assert "variant" not in payload and "paired_counterfactual" not in payload
    assert "b2_floor" not in payload["thresholds"]
    assert payload["reserved"] == ["pressure reader"]
    assert "variant" not in read(path, "head_table.json")["meta"]["roles"]


def test_a_twin_json_whose_marker_contradicts_the_columns_is_refused(v2_cell):
    write_agnostic(v2_cell, pp.NEUTRAL_TWIN, pp.LEGACY_CONVENTION)
    with pytest.raises(SystemExit, match="agnostic_neutral_twin.json"):
        run_roles(v2_cell)


def test_the_columns_written_on_a_v2_cell_are_the_same_set_as_on_a_v1_cell(v2_cell):
    run_roles(v2_cell)
    written = {column for column in read(v2_cell, "head_table.json")["columns"] if column.startswith("roles.")}
    assert written == {f"roles.{one}" for one in roles.COLUMNS}


def test_the_roles_module_still_does_not_import_nnsight_with_the_v2_detection():
    import subprocess
    import sys

    probe = ("import component_analysis.roles as r, sys; r.variant_of({'task': {'task': 'sdr_v2'}}); "
             "assert 'nnsight' not in sys.modules, sorted(sys.modules)")
    result = subprocess.run([sys.executable, "-c", probe],
                            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
