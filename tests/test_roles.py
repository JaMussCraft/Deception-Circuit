"""
The Component Role criteria and the `roles` CLI seam.

Every test here builds a head table by hand — a row is a dict of columns, which
is exactly what `head_table.load_head_table` hands back — and asserts on the
role that comes out, or on the files the subcommand writes. No model, no
nnsight, no GPU: the roles pass is a mechanical reading of a finished table and
must run on the login node.

The criteria under test are `docs/component-roles.md`. A test that disagrees
with that file is a bug in one of the two, and the file is the pre-registered
one.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

from component_analysis import roles
from component_analysis.head_table import load_head_table, write_head_table

CELL = ("suite", "delta__head", "sdr")


# ==============================================================================
# ROWS
# ==============================================================================

def row(kind="head", layer=17, index=25, **columns):
    """A head-table row: the key, then whatever columns the test cares about."""
    out = {"kind": kind, "layer": layer, "index": index, "kv_group": 6,
           "head_gate_active": True, "active_neuron_count": 3}
    out.update(columns)
    return out


def reads(segment, mass=0.4):
    return {"attention_patterns.pressure_top_segment": segment,
            "attention_patterns.pressure_top_mass": mass}


def writes(value, se, *, differential=None, differential_se=None,
           suppression=False, honest_instruction=None):
    out = {"dla.pressure": value, "dla.pressure_se": se,
           "dla.suppression": suppression,
           "dla.honest_instruction": honest_instruction}
    if differential is not None:
        out["dla.differential"] = differential
        out["dla.differential_se"] = differential_se
    return out


def knocked(value, se):
    return {"knockout.logit_diff_drop": value, "knockout.standard_error": se}


def paths(direct=None, direct_se=None, outgoing=None, outgoing_effect=None,
          incoming_hi=None, incoming_hi_effect=None):
    return {"path_patching.direct_effect": direct,
            "path_patching.direct_effect_se": direct_se,
            "path_patching.strongest_outgoing": outgoing,
            "path_patching.strongest_outgoing_effect": outgoing_effect,
            "path_patching.strongest_incoming_honest_instruction": incoming_hi,
            "path_patching.strongest_incoming_effect_honest_instruction":
                incoming_hi_effect}


def merged(*parts, **kwargs):
    out = row(**kwargs)
    for part in parts:
        out.update(part)
    return out


def propose(one):
    return roles.propose(one, roles.Thresholds())


# A Component of each role, built to the criteria and to nothing else. The
# numbers are on the scale of the SDR circuit so that a floor that is wrong by
# an order of magnitude shows up here rather than only on the cluster.

def a_binder(**kwargs):
    return merged(reads("predicate_token", 0.42),
                  writes(0.0004, 0.0006),
                  knocked(0.05, 0.01),
                  paths(direct=-0.0002, direct_se=0.0002,
                        outgoing="head.8.3->q.14.1", outgoing_effect=-0.02),
                  layer=8, index=3, **kwargs)


def a_selector(**kwargs):
    return merged(reads("item_1_question_option", 0.35),
                  writes(0.03, 0.0014, differential=0.034,
                         differential_se=0.0027, honest_instruction=0.0002),
                  knocked(0.44, 0.028),
                  paths(direct=-0.021, direct_se=0.0017,
                        outgoing="head.17.25->readout", outgoing_effect=-0.021,
                        incoming_hi="head.14.22->q.17.25",
                        incoming_hi_effect=0.0068),
                  layer=17, index=25, **kwargs)


def a_mover(**kwargs):
    return merged(reads("item_2_question_option", 0.31),
                  writes(0.04, 0.008, differential=0.07, differential_se=0.02,
                         honest_instruction=-0.009),
                  knocked(0.3, 0.06),
                  paths(direct=-0.024, direct_se=0.0065,
                        outgoing="head.24.18->readout", outgoing_effect=-0.024,
                        incoming_hi="head.17.25->v.24.6",
                        incoming_hi_effect=-0.02),
                  layer=24, index=18, **kwargs)


def a_suppressor(**kwargs):
    return merged(reads("question", 0.32),
                  writes(-0.04, 0.008, suppression=True),
                  knocked(-0.09, 0.028),
                  paths(direct=0.02, direct_se=0.004,
                        outgoing="head.14.7->readout", outgoing_effect=0.02),
                  layer=14, index=7, **kwargs)


# ==============================================================================
# THE FOUR ASSIGNABLE ROLES
# ==============================================================================

def test_a_binder_reads_the_designation_writes_nothing_and_feeds_another_component():
    decision = propose(a_binder())
    assert decision.role == "binder"
    assert decision.reads_group == "designation"


def test_a_selector_writes_a_pressure_dependent_contribution_the_honest_instruction_reaches_at_its_query():
    decision = propose(a_selector())
    assert decision.role == "selector"
    assert "q.17.25" in decision.notes


def test_a_mover_writes_straight_to_the_readout_and_the_honest_instruction_misses_its_query():
    decision = propose(a_mover())
    assert decision.role == "mover"


def test_a_suppressor_writes_towards_the_honest_answer_and_its_knockout_raises_the_margin():
    decision = propose(a_suppressor())
    assert decision.role == "suppressor"


def test_the_four_roles_are_the_vocabulary_the_criteria_doc_names():
    assert roles.ROLES == ("binder", "selector", "mover", "suppressor",
                           "unknown")
    assert "pressure reader" in roles.RESERVED


# ==============================================================================
# UNKNOWN: DISAGREEMENT AND SILENCE
# ==============================================================================

def test_views_that_disagree_give_unknown_rather_than_the_loudest_view_s_role():
    """DLA says it writes towards deception; knockout says removing it helps."""
    disagreeing = merged(reads("item_1_question_option", 0.35),
                         writes(0.04, 0.005, differential=0.06,
                                differential_se=0.01),
                         knocked(-0.2, 0.03),
                         paths(direct=-0.02, direct_se=0.004,
                               outgoing="head.24.18->readout",
                               outgoing_effect=-0.02))
    decision = propose(disagreeing)
    assert decision.role == "unknown"
    assert decision.flavour == "disagree"
    assert "disagree" in decision.notes


def test_an_unestablished_read_blocks_the_role_and_says_so_in_the_notes():
    """The mover of every other view, reading the attention sink."""
    decision = propose(a_mover(**{}) | reads("unsegmented", 0.64))
    assert decision.role == "unknown"
    assert decision.flavour == "insufficient"
    assert decision.reads_group == "unestablished"
    assert "mover" in decision.notes, "the lean is what makes the row readable"
    assert "unsegmented" in decision.notes


def test_a_component_no_analysis_scored_is_unknown_and_named_as_such():
    decision = propose(row())
    assert (decision.role, decision.flavour) == ("unknown", "insufficient")
    assert "no analysis scored" in decision.notes


def test_a_number_without_a_standard_error_is_not_significant():
    """A spread that was never measured is not a small spread."""
    decision = propose(a_mover(**{}) | {"dla.pressure_se": None})
    assert decision.role == "unknown"


def test_a_number_inside_its_floor_is_not_significant_however_tight_its_error():
    """Four standard errors from zero at 0.0005 is noise measured precisely."""
    tiny = a_mover(**{}) | writes(0.0005, 0.0001, differential=0.0006,
                                  differential_se=0.0001) \
        | paths(direct=-0.0005, direct_se=0.0001,
                outgoing="head.24.18->readout", outgoing_effect=-0.0005)
    assert propose(tiny).role == "unknown"


def test_a_thin_attention_mass_does_not_establish_a_read():
    assert propose(a_mover(**{}) | reads("item_2_question_option", 0.05)).role \
        == "unknown"


# ==============================================================================
# THE SHAPE OF THE CONJUNCTION
# ==============================================================================

def test_an_mlp_block_has_no_reads_view_and_is_still_assignable():
    """Not applicable is not the same as unestablished (criteria doc)."""
    block = merged(writes(0.18, 0.06, differential=0.33, differential_se=0.083,
                          honest_instruction=-0.57),
                   knocked(0.31, 0.065),
                   paths(direct=-0.114, direct_se=0.019,
                         outgoing="mlp.31.0->readout", outgoing_effect=-0.114,
                         incoming_hi="head.17.25->mlp_in.31.0",
                         incoming_hi_effect=-0.0073),
                   kind="mlp", layer=31, index=0)
    decision = propose(block)
    assert decision.reads_group == "not_applicable"
    assert decision.role == "mover"


def test_a_head_with_a_null_attention_column_is_unestablished_not_not_applicable():
    decision = propose(a_mover(**{}) | {
        "attention_patterns.pressure_top_segment": None,
        "attention_patterns.pressure_top_mass": None})
    assert decision.reads_group == "unestablished"
    assert decision.role == "unknown"


def test_the_incoming_honest_instruction_path_is_what_separates_selector_from_mover():
    """One column apart: the same Component, the honest instruction at its Q."""
    at_the_query = a_mover(**{}) | {
        "path_patching.strongest_incoming_honest_instruction": "head.17.25->q.24.18",
        "path_patching.strongest_incoming_effect_honest_instruction": -0.02}
    assert propose(a_mover()).role == "mover"
    assert propose(at_the_query).role == "selector"


def test_a_query_side_path_on_another_component_does_not_make_a_selector():
    elsewhere = a_mover(**{}) | {
        "path_patching.strongest_incoming_honest_instruction": "head.17.25->q.30.1",
        "path_patching.strongest_incoming_effect_honest_instruction": -0.02}
    assert propose(elsewhere).role == "mover"


def test_a_binder_with_a_direct_path_to_the_readout_is_not_a_binder():
    writing = a_binder(**{}) | paths(direct=-0.03, direct_se=0.004,
                                     outgoing="head.8.3->readout",
                                     outgoing_effect=-0.03)
    assert propose(writing).role != "binder"


# ==============================================================================
# THE RESERVED NAME
# ==============================================================================

def test_a_pressure_reader_signature_is_noted_and_never_assigned():
    candidate = a_binder(**{}) | {
        "attention_patterns.pressure_paired_top_segment": "pressure_clause",
        "attention_patterns.honest_instruction_top_segment": "question"}
    decision = propose(candidate)
    assert decision.role in roles.ROLES
    assert decision.role != "pressure reader"
    assert "pressure-reader signature" in decision.notes


def test_no_component_is_ever_proposed_the_reserved_role():
    for one in (a_binder(), a_selector(), a_mover(), a_suppressor(), row()):
        assert propose(one).role not in roles.RESERVED


# ==============================================================================
# THE SIGN CONVENTION (ADR-0002)
# ==============================================================================

def test_the_derived_support_column_is_the_negation_of_the_path_patching_cell():
    derived = roles.derived_columns(a_selector())
    assert derived["direct_support"] == pytest.approx(0.021)
    assert derived["direct_support_se"] == pytest.approx(0.0017)


def test_the_derived_column_is_absent_rather_than_zero_when_the_cell_is():
    derived = roles.derived_columns(row())
    assert derived["direct_support"] is None


def test_the_honest_instruction_support_column_is_negated_too_and_keeps_its_suffix():
    derived = roles.derived_columns(
        a_selector(**{}) | {"path_patching.direct_effect_honest_instruction": -0.0088})
    assert derived["direct_support_honest_instruction"] == pytest.approx(0.0088)


# ==============================================================================
# THRESHOLDS ARE FLAGS
# ==============================================================================

def test_raising_the_dla_floor_above_a_component_s_write_unmakes_its_role():
    strict = roles.Thresholds(dla_floor=1.0)
    assert roles.propose(a_mover(), strict).role == "unknown"


def test_the_thresholds_used_are_the_defaults_the_criteria_doc_states():
    thresholds = roles.Thresholds()
    assert (thresholds.z, thresholds.dla_floor, thresholds.knockout_floor,
            thresholds.path_floor, thresholds.attention_floor) == \
        (2.0, 0.01, 0.01, 0.005, 0.20)


# ==============================================================================
# SEGMENT GROUPS
# ==============================================================================

@pytest.mark.parametrize("segment,group", [
    ("designation_site", "designation"),
    ("predicate_token", "designation"),
    ("designation_suffix", "designation"),
    ("item_1_intro", "item_mention"),
    ("item_2_question_option", "item_mention"),
    ("pressure_clause", "pressure"),
    ("question", "frame"),
    ("intro", "frame"),
    ("unsegmented", "unestablished"),
    ("readout", "unestablished"),
    ("bos", "unestablished"),
])
def test_every_segment_of_the_prompt_anatomy_has_its_group(segment, group):
    assert roles.segment_group(segment) == group


# ==============================================================================
# THE CLI SEAM
# ==============================================================================

@pytest.fixture
def cell(tmp_path):
    """A finished head table in a cell directory, as the analyses leave it."""
    path = os.path.join(str(tmp_path), *CELL)
    write_head_table(path, [a_binder(), a_selector(), a_mover(),
                            a_suppressor()],
                     meta={"circuit": {"label": "delta__head"},
                           "task": {"name": "sdr"}})
    return path


def run_roles(*argv):
    import analyze_components

    return analyze_components.main(["roles", *argv])


def read(path, *parts):
    with open(os.path.join(path, *parts)) as handle:
        return json.load(handle)


def by_key(rows):
    return {(r["kind"], r["layer"], r["index"]): r for r in rows}


def test_the_subcommand_writes_the_proposed_role_and_the_notes_into_the_table(cell):
    assert run_roles(cell) == 0

    rows = by_key(load_head_table(cell))
    assert rows[("head", 8, 3)]["roles.role_proposed"] == "binder"
    assert rows[("head", 17, 25)]["roles.role_proposed"] == "selector"
    assert rows[("head", 24, 18)]["roles.role_proposed"] == "mover"
    assert rows[("head", 14, 7)]["roles.role_proposed"] == "suppressor"
    assert all(r["roles.role_notes"] for r in rows.values())


def test_the_subcommand_writes_the_derived_support_column_beside_the_native_one(cell):
    run_roles(cell)

    row_17 = by_key(load_head_table(cell))[("head", 17, 25)]
    assert row_17["path_patching.direct_effect"] == pytest.approx(-0.021)
    assert row_17["roles.direct_support"] == pytest.approx(0.021)


def test_the_decisions_json_records_every_threshold_and_every_criterion(cell):
    run_roles(cell)

    payload = read(cell, roles.SUBDIR, roles.JSON_NAME)
    assert payload["thresholds"]["z"] == 2.0
    assert payload["criteria_doc"].endswith("component-roles.md")
    assert payload["counts"]["selector"] == 1
    decisions = {tuple(one["key"]): one for one in payload["components"]}
    selector = decisions[("head", 17, 25)]
    assert selector["role"] == "selector"
    assert selector["criteria"]["selector"]["writes"] is True
    assert selector["views"]["writes"]["value"] == pytest.approx(0.03)


def test_the_pass_keeps_the_columns_and_the_meta_it_did_not_write(cell):
    before = read(cell, "head_table.json")
    run_roles(cell)
    after = read(cell, "head_table.json")

    assert after["meta"]["circuit"] == before["meta"]["circuit"]
    assert after["meta"]["roles"]["criteria_doc"].endswith("component-roles.md")
    for column in before["columns"]:
        assert column in after["columns"]
    assert by_key(after["rows"])[("head", 17, 25)]["dla.pressure"] == \
        pytest.approx(0.03)


def test_a_confirmed_role_is_read_and_never_overwritten(cell):
    rows = load_head_table(cell)
    for one in rows:
        if one["layer"] == 17:
            one["role_confirmed"] = "mover"
    write_head_table(cell, rows, meta=read(cell, "head_table.json")["meta"])

    run_roles(cell)

    after = by_key(load_head_table(cell))[("head", 17, 25)]
    assert after["role_confirmed"] == "mover", "the human's column is untouched"
    assert after["roles.role_proposed"] == "selector", \
        "and the mechanical proposal is still recorded beside it"
    payload = read(cell, roles.SUBDIR, roles.JSON_NAME)
    decisions = {tuple(one["key"]): one for one in payload["components"]}
    assert decisions[("head", 17, 25)]["role_confirmed"] == "mover"


def test_rerunning_the_pass_is_the_same_table_again(cell):
    run_roles(cell)
    once = read(cell, "head_table.json")["rows"]
    run_roles(cell)
    assert read(cell, "head_table.json")["rows"] == once


def test_a_dry_run_proposes_without_writing_anything(cell, capsys):
    before = sorted(os.listdir(cell))

    assert run_roles(cell, "--dry-run") == 0

    assert sorted(os.listdir(cell)) == before, "no roles/ directory"
    assert "roles.role_proposed" not in read(cell, "head_table.json")["columns"]
    assert "selector" in capsys.readouterr().out


def test_a_threshold_flag_changes_the_proposal(cell):
    run_roles(cell, "--roles-dla-floor", "1.0")

    rows = by_key(load_head_table(cell))
    assert rows[("head", 24, 18)]["roles.role_proposed"] == "unknown"


def test_merging_another_cell_brings_its_columns_in_before_the_criteria_run(
        tmp_path):
    """The analyses of record live one suite per analysis, not one cell.

    The DLA cell knows the Component writes towards deception; the knockout
    cell, merged in, says removing it *helps* deception. Neither cell alone
    could produce the disagreement, which is the point of merging them.
    """
    base = os.path.join(str(tmp_path), "dla_suite", *CELL[1:])
    write_head_table(base, [merged(reads("item_1_question_option", 0.35),
                                   writes(0.04, 0.005, differential=0.06,
                                          differential_se=0.01),
                                   paths(direct=-0.02, direct_se=0.004,
                                         outgoing="head.17.25->readout",
                                         outgoing_effect=-0.02))])
    other = os.path.join(str(tmp_path), "knockout_suite", *CELL[1:])
    write_head_table(other, [{"kind": "head", "layer": 17, "index": 25,
                              "knockout.logit_diff_drop": -0.5,
                              "knockout.standard_error": 0.02}])

    assert run_roles(base, "--roles-merge-from", other) == 0

    row_17 = by_key(load_head_table(base))[("head", 17, 25)]
    assert row_17["knockout.logit_diff_drop"] == pytest.approx(-0.5)
    assert row_17["roles.role_proposed"] == "unknown"
    assert row_17["roles.role_notes"].startswith("unknown/disagree")
    assert read(base, roles.SUBDIR, roles.JSON_NAME)["merged_from"] == [other]


def test_a_merge_that_would_overwrite_a_measured_column_is_refused_by_name(
        cell, tmp_path):
    """Whichever cell came last is not a provenance a role can be audited on."""
    other = os.path.join(str(tmp_path), "clash", *CELL[1:])
    write_head_table(other, [{"kind": "head", "layer": 17, "index": 25,
                              "dla.pressure": 0.99}])

    with pytest.raises(SystemExit, match="dla.pressure"):
        run_roles(cell, "--roles-merge-from", other)


def test_a_merge_that_only_fills_blanks_is_allowed(cell, tmp_path):
    other = os.path.join(str(tmp_path), "fills", *CELL[1:])
    write_head_table(other, [{"kind": "head", "layer": 17, "index": 25,
                              "dla.pressure": 0.03,
                              "knockout.accuracy": 0.99}])

    assert run_roles(cell, "--roles-merge-from", other) == 0
    assert by_key(load_head_table(cell))[("head", 17, 25)][
        "knockout.accuracy"] == pytest.approx(0.99)


def test_a_cell_with_no_head_table_is_refused_by_name(tmp_path):
    with pytest.raises(SystemExit, match="head_table.json"):
        run_roles(str(tmp_path))


def test_the_roles_module_does_not_import_nnsight():
    """It must run on the login node, where nnsight 0.7.0 is not installed."""
    import subprocess

    probe = ("import component_analysis.roles, sys; "
             "assert 'nnsight' not in sys.modules, sorted(sys.modules)")
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
