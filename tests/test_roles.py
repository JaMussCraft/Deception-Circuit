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
           "dla.honest_instruction_paired": honest_instruction}
    if differential is not None:
        out["dla.differential_paired"] = differential
        out["dla.differential_paired_se"] = differential_se
    return out


def knocked(value, se):
    return {"knockout.logit_diff_drop": value, "knockout.standard_error": se}


def paths(direct=None, direct_se=None, outgoing=None, outgoing_effect=None,
          incoming_hi=None, incoming_hi_effect=None):
    return {"path_patching.direct_effect": direct,
            "path_patching.direct_effect_se": direct_se,
            "path_patching.strongest_outgoing": outgoing,
            "path_patching.strongest_outgoing_effect": outgoing_effect,
            "path_patching.strongest_incoming_honest_instruction_paired":
                incoming_hi,
            "path_patching.strongest_incoming_effect_honest_instruction_paired":
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
                        incoming_hi_effect=0.021),
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
        "path_patching.strongest_incoming_honest_instruction_paired": "head.17.25->q.24.18",
        "path_patching.strongest_incoming_effect_honest_instruction_paired": -0.02}
    assert propose(a_mover()).role == "mover"
    assert propose(at_the_query).role == "selector"


def test_a_query_side_path_on_another_component_does_not_make_a_selector():
    elsewhere = a_mover(**{}) | {
        "path_patching.strongest_incoming_honest_instruction_paired": "head.17.25->q.30.1",
        "path_patching.strongest_incoming_effect_honest_instruction_paired": -0.02}
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
        "attention_patterns.honest_instruction_paired_top_segment": "question"}
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
        a_selector(**{})
        | {"path_patching.direct_effect_honest_instruction_paired": -0.0088})
    assert derived["direct_support_honest_instruction_paired"] == \
        pytest.approx(0.0088)


#: A legacy-sign column (written before 2026-10-13) and the column that
#: replaced it in the new sign, where positive helps deception.
SIGN_FLIPPED = {
    "path_patching.direct_effect": "path_patching.direct_support",
    "path_patching.strongest_outgoing_effect":
        "path_patching.strongest_outgoing_support",
    "path_patching.direct_effect_honest_instruction_paired":
        "path_patching.direct_support_honest_instruction_paired",
    "path_patching.strongest_incoming_effect_honest_instruction_paired":
        "path_patching.strongest_incoming_support_honest_instruction_paired",
}
SE_RENAMED = {
    "path_patching.direct_effect_se": "path_patching.direct_support_se",
    "path_patching.direct_effect_se_honest_instruction_paired":
        "path_patching.direct_support_honest_instruction_paired_se",
}


def native(one):
    """The same row as a path-patching run since 2026-10-13 writes it: the
    signed columns under their new names and negated, the standard errors
    renamed and unchanged."""
    out = {}
    for column, value in one.items():
        if column in SIGN_FLIPPED:
            out[SIGN_FLIPPED[column]] = None if value is None else -value
        else:
            out[SE_RENAMED.get(column, column)] = value
    return out


def test_a_new_cell_s_direct_support_is_the_path_patching_column_read_natively():
    derived = roles.derived_columns(native(a_selector()))
    assert derived["direct_support"] == pytest.approx(0.021)
    assert derived["direct_support_se"] == pytest.approx(0.0017)


def test_a_new_cell_s_honest_instruction_support_is_native_too():
    derived = roles.derived_columns(native(
        a_selector()
        | {"path_patching.direct_effect_honest_instruction_paired": -0.0088}))
    assert derived["direct_support_honest_instruction_paired"] == \
        pytest.approx(0.0088)


def test_a_row_carrying_both_sign_conventions_is_refused_by_name():
    """Reachable by merging a legacy cell into a new one: the two generations
    have different names, so the merge's own conflict check cannot see it,
    and either reading would silently drop the other measurement."""
    both = a_selector() | {"path_patching.direct_support": 0.021}
    with pytest.raises(ValueError, match="path_patching.direct_effect"):
        roles.derived_columns(both)


def test_a_new_cell_gets_the_same_roles_and_support_as_its_legacy_twin(tmp_path):
    new = os.path.join(str(tmp_path), "new", *CELL)
    old = os.path.join(str(tmp_path), "old", *CELL)
    table = [a_binder(), a_selector(), a_mover(), a_suppressor(),
             knockout_alone()]
    write_head_table(old, table)
    write_head_table(new, [native(one) for one in table])

    assert run_roles(new) == 0 and run_roles(old) == 0

    rows_new, rows_old = (by_key(load_head_table(new)),
                          by_key(load_head_table(old)))
    for key, one in rows_old.items():
        assert rows_new[key]["roles.role_proposed"] == one["roles.role_proposed"]
        assert rows_new[key]["roles.direct_support"] == \
            one["roles.direct_support"]
    assert rows_new[("head", 17, 25)]["roles.role_proposed"] == "selector"
    assert rows_new[("head", 24, 18)]["roles.direct_support"] == \
        pytest.approx(0.024)
    assert "native" in read(new, roles.SUBDIR, roles.JSON_NAME)[
        "sign_convention"]
    assert "negat" in read(old, roles.SUBDIR, roles.JSON_NAME)[
        "sign_convention"]


def test_a_legacy_cell_of_record_reads_the_direct_support_it_always_had(
        tmp_path):
    """Two rows of `sdr-first-run`'s head table as written (item-swap direct
    effect in the legacy sign, honest columns already under ticket 13's
    names). The derived support is what the roles pass of record wrote."""
    path = os.path.join(str(tmp_path), *CELL)
    record = [
        row("mlp", 31, 0, **{
            "path_patching.direct_effect": -0.09507,
            "path_patching.direct_effect_se": 0.01611,
            "path_patching.strongest_outgoing": "mlp.31.0->readout",
            "path_patching.strongest_outgoing_effect": -0.09507,
            "path_patching.direct_effect_honest_instruction_paired": -0.07700,
            "path_patching.direct_effect_se_honest_instruction_paired": 0.02290}),
        row("head", 17, 25, **{
            "path_patching.direct_effect": -0.01920,
            "path_patching.direct_effect_se": 0.00140,
            "path_patching.strongest_outgoing": "head.17.25->readout",
            "path_patching.strongest_outgoing_effect": -0.01920}),
    ]
    write_head_table(path, record)

    assert run_roles(path, "--roles-allow-missing-views") == 0

    rows = by_key(load_head_table(path))
    assert rows[("mlp", 31, 0)]["roles.direct_support"] == pytest.approx(0.09507)
    assert rows[("mlp", 31, 0)]["roles.direct_support_se"] == \
        pytest.approx(0.01611)
    assert rows[("mlp", 31, 0)][
        "roles.direct_support_honest_instruction_paired"] == \
        pytest.approx(0.07700)
    assert rows[("head", 17, 25)]["roles.direct_support"] == \
        pytest.approx(0.01920)
    assert rows[("head", 17, 25)]["path_patching.direct_effect"] == \
        pytest.approx(-0.01920), "the legacy column itself is never rewritten"


def test_the_derived_columns_of_a_new_cell_take_the_native_columns_coverage(
        tmp_path):
    from component_analysis.head_table import (
        add_coverage, coverage_of, load_head_table_meta)

    path = os.path.join(str(tmp_path), *CELL)
    meta = add_coverage({}, ["direct_support", "direct_support_se"],
                        [f"i{one}" for one in range(100)],
                        instance_set="causal_sample", namespace="path_patching")
    meta = add_coverage(meta, ["direct_support_honest_instruction_paired"],
                        [f"i{one}" for one in range(71)],
                        instance_set="paired_honest_instruction",
                        namespace="path_patching")
    write_head_table(path, [native(a_selector(**{
        "path_patching.direct_effect_honest_instruction_paired": -0.0088}))],
        meta=meta)

    assert run_roles(path) == 0

    written = load_head_table_meta(path)
    assert coverage_of(written, "roles.direct_support")["n"] == 100
    assert coverage_of(written, "roles.direct_support_se")["n"] == 100
    assert coverage_of(
        written, "roles.direct_support_honest_instruction_paired")["n"] == 71


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
        (2.0, 0.01, 0.01, 0.01, 0.20)


def test_the_path_floor_sits_above_the_measured_cross_card_noise():
    """Ticket 09 measured about 0.005 between an A40 and an A100 on one cell.

    A criterion resting on a cell inside that noise is a criterion that changes
    with the card the job landed on, so the floor is twice it. The number is in
    the criteria doc's amendment log with the same reason.
    """
    assert roles.Thresholds().path_floor >= 2 * 0.005


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


def test_the_columns_written_are_the_ones_the_module_declares(cell):
    """`COLUMNS` is an interface, so it is asserted rather than described."""
    run_roles(cell)

    written = {column for column in read(cell, "head_table.json")["columns"]
               if column.startswith("roles.")}
    assert written == {f"roles.{one}" for one in roles.COLUMNS}


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


# ==============================================================================
# WHAT THE REVIEWS FOUND
# ==============================================================================

def test_a_standard_error_of_exactly_zero_is_not_a_measured_spread():
    """A spread of zero over a sample was not measured; it is not significance."""
    assert propose(a_mover(**{}) | {"dla.pressure_se": 0.0}).role == "unknown"
    assert roles.direction(1.0, 0.0, 0.01, roles.Thresholds()) == 0


def test_a_boolean_column_read_back_as_a_string_is_not_always_true():
    """`bool("0")` is True, and the suppressor clause is checked first."""
    not_suppressing = a_mover(**{}) | {"dla.suppression": "0"}
    assert propose(not_suppressing).role == "mover"
    assert roles._flag("false") is False
    assert roles._flag("true") is True
    assert roles._flag(1) is True


def test_a_table_missing_a_whole_view_is_refused_and_names_the_columns(tmp_path):
    """A table of `unknown` reads like a finding; a refusal does not."""
    only_knockout = os.path.join(str(tmp_path), "one_view", *CELL[1:])
    write_head_table(only_knockout, [merged(knocked(0.4, 0.02))])

    with pytest.raises(SystemExit, match="dla.pressure"):
        run_roles(only_knockout)


def test_the_missing_views_may_be_allowed_and_are_then_recorded(tmp_path):
    only_knockout = os.path.join(str(tmp_path), "allowed", *CELL[1:])
    write_head_table(only_knockout, [merged(knocked(0.4, 0.02))])

    assert run_roles(only_knockout, "--roles-allow-missing-views") == 0

    payload = read(only_knockout, roles.SUBDIR, roles.JSON_NAME)
    assert any("dla" in view for view in payload["missing_views"])
    assert payload["components"][0]["role"] == "unknown"


def test_a_table_with_every_view_records_no_missing_view(cell):
    run_roles(cell)

    assert read(cell, roles.SUBDIR, roles.JSON_NAME)["missing_views"] == []


def test_the_circuit_and_the_task_are_label_strings_like_every_sibling_json(cell):
    """The notebook reads `circuit` across the analyses and must meet one type."""
    run_roles(cell)

    payload = read(cell, roles.SUBDIR, roles.JSON_NAME)
    assert payload["circuit"] == "delta__head"
    assert payload["task"] == "sdr"


def test_an_unknown_segment_name_is_unestablished_not_a_group_of_its_own():
    """An override such as ticket 03's `bos` has not been shown to be anything."""
    assert roles.segment_group("bos") == "unestablished"
    assert roles.segment_group(None) == "unestablished"


def test_a_query_cell_inside_the_cross_card_noise_does_not_make_a_selector():
    """The amendment of 2026-09-20, asserted rather than only written down.

    L17H25 on SDR nls0.3 is the real case: its honest-instruction query cell is
    0.0068, which cleared the old 0.005 floor and does not clear 0.01.
    """
    marginal = a_selector(**{}) | {
        "path_patching.strongest_incoming_effect_honest_instruction_paired":
            0.0068}

    assert propose(a_selector()).role == "selector"
    assert propose(marginal).role != "selector"
    assert roles.propose(marginal, roles.Thresholds(path_floor=0.005)).role \
        == "selector", "and the old floor is what admitted it"



# ==============================================================================
# unknown/knockout-only (the researcher's 2026-10-13 decision)
# ==============================================================================

def knockout_alone(**kwargs):
    """L5H8 on SDR nls0.3: a knockout five standard errors from zero, an
    unestablished read, and nothing written or passed on above a floor."""
    return merged(reads("unsegmented", 0.42),
                  writes(-0.0000, 0.0006, differential=0.0001,
                         differential_se=0.0006),
                  knocked(0.0572, 0.0112),
                  paths(direct=-0.0001, direct_se=0.00004,
                        outgoing="head.5.8->q.13.17", outgoing_effect=0.0029),
                  layer=5, index=8, **kwargs)


def test_a_component_that_matters_on_knockout_alone_is_unknown_knockout_only():
    decision = propose(knockout_alone())

    assert decision.role == "unknown"
    assert decision.flavour == roles.KNOCKOUT_ONLY == "knockout-only"
    assert decision.notes.startswith("unknown/knockout-only: ")
    assert "supports deception" in decision.notes


def test_an_established_read_is_reads_evidence_so_knockout_is_not_alone():
    """L5H11's case: an item-mention read at 0.35 is a view that speaks."""
    decision = propose(knockout_alone() | reads("item_1_question_option", 0.35))

    assert decision.role == "unknown"
    assert decision.flavour == roles.INSUFFICIENT


@pytest.mark.parametrize("speaks", [
    writes(0.03, 0.001),                                     # it writes
    writes(0.0, 0.0006, differential=0.04, differential_se=0.005),
    paths(direct=-0.02, direct_se=0.002, outgoing="head.5.8->readout",
          outgoing_effect=-0.02),                            # a direct path
    paths(direct=-0.0001, direct_se=0.00004, outgoing="head.5.8->q.13.17",
          outgoing_effect=0.02),                             # feeds another
])
def test_any_other_view_above_its_floor_means_knockout_is_not_alone(speaks):
    decision = propose(knockout_alone() | speaks)

    assert decision.flavour != roles.KNOCKOUT_ONLY


def test_a_knockout_that_does_not_clear_its_bar_is_not_knockout_only():
    decision = propose(knockout_alone() | knocked(0.0203, 0.0406))

    assert decision.flavour == roles.INSUFFICIENT


def test_a_negative_knockout_alone_is_knockout_only_and_says_which_way():
    decision = propose(knockout_alone() | knocked(-0.0936, 0.0284))

    assert decision.flavour == roles.KNOCKOUT_ONLY
    assert "opposes deception" in decision.notes


def test_an_mlp_block_has_no_reads_evidence_to_wait_for_and_can_be_knockout_only():
    mlp = {k: v for k, v in knockout_alone().items()
           if not k.startswith("attention_patterns.")}
    mlp.update(kind="mlp", layer=30, index=0, kv_group=None)

    assert propose(mlp).flavour == roles.KNOCKOUT_ONLY


def test_the_criteria_doc_states_the_knockout_only_criterion_and_its_date():
    path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(roles.__file__))), roles.CRITERIA_DOC)
    with open(path) as handle:
        text = handle.read()

    assert "unknown/knockout-only" in text
    assert "2026-10-13" in text


def test_the_decisions_json_counts_the_flavours_of_unknown(tmp_path):
    path = os.path.join(str(tmp_path), *CELL)
    write_head_table(path, [knockout_alone(), a_mover()])

    assert run_roles(path) == 0

    payload = read(path, roles.SUBDIR, roles.JSON_NAME)
    assert payload["flavour_counts"] == {roles.KNOCKOUT_ONLY: 1}
    assert by_key(load_head_table(path))[("head", 5, 8)][
        "roles.role_notes"].startswith("unknown/knockout-only")


# ==============================================================================
# A CELL WRITTEN BEFORE THE PAIRED NAMES (ticket 13)
# ==============================================================================

def legacy(one):
    """The same row under the names written before 2026-10-13."""
    from component_analysis.head_table import LEGACY_COLUMNS

    current = {new: old for old, new in LEGACY_COLUMNS.items()}
    return {current.get(column, column): value for column, value in one.items()}


def test_a_legacy_cell_gets_the_same_roles_and_is_written_under_the_new_names(
        tmp_path):
    new = os.path.join(str(tmp_path), "new", *CELL)
    old = os.path.join(str(tmp_path), "old", *CELL)
    table = [a_binder(), a_selector(), a_mover(), a_suppressor(),
             knockout_alone()]
    write_head_table(new, table)
    write_head_table(old, [legacy(one) for one in table])
    assert "dla.differential" in load_head_table(old)[1], "the fixture is legacy"

    assert run_roles(new) == 0 and run_roles(old) == 0

    roles_new = {k: r["roles.role_proposed"] for k, r
                 in by_key(load_head_table(new)).items()}
    roles_old = by_key(load_head_table(old))
    assert {k: r["roles.role_proposed"] for k, r in roles_old.items()} == roles_new
    assert roles_new[("head", 17, 25)] == "selector", \
        "the selector's query clause reads the renamed honest-instruction column"
    selector = roles_old[("head", 17, 25)]
    assert "dla.differential_paired" in selector
    assert "dla.differential" not in selector
    assert "roles.direct_support_honest_instruction_paired" in selector
    assert read(old, roles.SUBDIR, roles.JSON_NAME)["renamed_columns"][
        "dla.differential"] == "dla.differential_paired"


def test_a_legacy_cell_merged_into_a_new_one_compares_under_the_new_names(
        tmp_path):
    """Translated before the conflict check, so the same value under two
    spellings is the same column, not two."""
    base = os.path.join(str(tmp_path), "base", *CELL)
    other = os.path.join(str(tmp_path), "other", *CELL)
    write_head_table(base, [a_selector()])
    write_head_table(other, [legacy(a_selector())])

    assert run_roles(base, "--roles-merge-from", other) == 0

    row_17 = load_head_table(base)[0]
    assert "dla.differential" not in row_17


def test_the_derived_columns_take_the_coverage_of_the_columns_they_negate(
        tmp_path):
    from component_analysis.head_table import (
        add_coverage, coverage_of, load_head_table_meta)

    path = os.path.join(str(tmp_path), *CELL)
    meta = add_coverage({}, ["direct_effect", "direct_effect_se"],
                        [f"i{one}" for one in range(100)],
                        instance_set="causal_sample", namespace="path_patching")
    meta = add_coverage(meta, ["direct_effect_honest_instruction_paired"],
                        [f"i{one}" for one in range(71)],
                        instance_set="paired_honest_instruction",
                        namespace="path_patching")
    write_head_table(path, [a_selector(**{
        "path_patching.direct_effect_honest_instruction_paired": -0.0088})],
        meta=meta)

    assert run_roles(path) == 0

    written = load_head_table_meta(path)
    assert coverage_of(written, "roles.direct_support")["n"] == 100
    assert coverage_of(written, "roles.direct_support_se")["n"] == 100
    assert coverage_of(
        written, "roles.direct_support_honest_instruction_paired")["n"] == 71


@pytest.mark.parametrize("unmeasured", [
    ("dla.pressure", "dla.pressure_se", "dla.differential_paired",
     "dla.differential_paired_se"),
    ("path_patching.direct_effect", "path_patching.direct_effect_se",
     "path_patching.strongest_outgoing", "path_patching.strongest_outgoing_effect"),
])
def test_a_view_that_was_never_measured_is_not_a_view_that_is_silent(unmeasured):
    """Under --roles-allow-missing-views a table may lack DLA or path patching
    altogether; "no other view speaks" would then be a claim about views
    nobody measured, so the flavour is insufficient instead."""
    one = {column: value for column, value in knockout_alone().items()
           if column not in unmeasured}

    decision = propose(one)

    assert decision.flavour == roles.INSUFFICIENT
    assert "not measured" in decision.notes
    assert unmeasured[0].split(".")[0] in decision.notes


def test_a_measured_and_insignificant_view_is_silent_so_knockout_is_alone():
    """The other side of the distinction: measured, below its bar, says nothing."""
    decision = propose(knockout_alone())

    assert decision.flavour == roles.KNOCKOUT_ONLY
    assert "not measured" not in decision.notes


def test_every_flavour_of_unknown_is_named_in_the_criteria_doc():
    path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(roles.__file__))), roles.CRITERIA_DOC)
    with open(path) as handle:
        text = handle.read()

    for flavour in roles.FLAVOURS:
        assert f"unknown/{flavour}" in text
