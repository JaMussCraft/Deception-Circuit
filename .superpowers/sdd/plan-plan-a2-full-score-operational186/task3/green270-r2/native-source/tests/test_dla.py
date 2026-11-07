"""
Library-seam tests for the rules direct logit attribution reads its numbers by:
the aggregation over instances, the suppression margin, the layer the logit
lens flips at, and the direction every condition is reported in.

These need no model, so they run in both environments. The numbers themselves —
the sum invariant, the projection through `o_proj`, the CLI seam — are in
`tests/test_dla_model.py`, which needs a traced forward and so runs only under
the pinned nnsight.
"""

from __future__ import annotations

import os
import sys

import pytest

from component_analysis import dla


# ==============================================================================
# THE PARTS THAT NEED NO MODEL
# ==============================================================================

def test_the_analysis_module_does_not_import_nnsight_at_module_scope():
    """`--dry-run` builds the parser on the login node, which has no 0.7.0.

    `analyze_components.build_parser` imports every registered analysis so each
    can add its flags, so an analysis that pulls nnsight in at import time
    breaks the login-node dry run for every cell, not just its own.
    """
    import subprocess

    probe = ("import component_analysis.dla, sys; "
             "assert 'nnsight' not in sys.modules, sorted(sys.modules)")
    result = subprocess.run([sys.executable, "-c", probe],
                            cwd=os.path.dirname(os.path.dirname(
                                os.path.abspath(__file__))),
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_mean_and_standard_error_over_instances():
    stats = dla.mean_and_se([1.0, 2.0, 3.0, 4.0])

    assert stats["n"] == 4
    assert stats["mean"] == pytest.approx(2.5)
    # sd = 1.29099..., se = sd / sqrt(4)
    assert stats["se"] == pytest.approx(0.6454972, rel=1e-5)


def test_a_single_instance_has_a_mean_but_no_standard_error():
    stats = dla.mean_and_se([1.5])

    assert stats["mean"] == pytest.approx(1.5)
    assert stats["n"] == 1
    assert stats["se"] is None


def test_no_instances_is_reported_as_nothing_measured():
    assert dla.mean_and_se([]) == {"mean": None, "se": None, "n": 0}


def test_suppression_flags_only_a_mean_below_the_negative_margin():
    assert dla.is_suppressing(-0.5, margin=0.05) is True
    assert dla.is_suppressing(-0.01, margin=0.05) is False, \
        "inside the margin is not a suppressor"
    assert dla.is_suppressing(0.5, margin=0.05) is False
    assert dla.is_suppressing(None, margin=0.05) is None, \
        "a Component with no measurement is unflagged, not unsuppressed"


def test_the_sign_flip_row_is_where_the_lens_takes_its_final_sign_for_good():
    # Row 0 is the embedding; the lens goes positive at row 3 and stays.
    assert dla.sign_flip_row([-1.0, -0.5, -0.2, 0.3, 0.9]) == 3


def test_a_lens_that_goes_back_over_the_axis_flips_at_the_later_crossing():
    assert dla.sign_flip_row([-1.0, 0.4, -0.2, 0.3, 0.9]) == 3


def test_a_lens_that_never_changes_sign_has_no_flip():
    assert dla.sign_flip_row([0.2, 0.4, 0.9]) is None


def test_a_lens_row_is_not_a_layer():
    """Row 0 is the embedding's output, so it belongs to no decoder layer."""
    assert dla.layer_of_row(3) == 2
    assert dla.layer_of_row(1) == 0
    assert dla.layer_of_row(0) is None
    assert dla.layer_of_row(None) is None


def test_the_honest_twin_metric_is_negated_into_the_deception_direction():
    """`harvest_honest_twins` swaps target and distractor on the honest split.

    Every other column is logit(deceptive answer) - logit(honest answer), so
    the twin's own fields, read as they stand, would be that column's negative
    and a mover would look like a suppressor.
    """
    assert dla.direction_sign("honest_twin") == -1
    assert dla.direction_sign("pressure") == 1
    assert dla.direction_sign("honest_instruction") == 1


def test_every_crossing_is_reported_beside_the_flip_layer():
    """One number cannot say whether the crossing was decisive or noise."""
    assert dla.sign_change_rows([-1.0, 0.4, -0.2, 0.3, 0.9]) == [1, 2, 3]
    assert dla.sign_change_rows([-0.02, 0.01, 0.05, 3.0]) == [1]
    assert dla.sign_change_rows([0.2, 0.4, 0.9]) == []


def test_an_unknown_condition_is_refused_from_a_list_too():
    """The same typo must not be an error on the command line and a silent
    empty measurement from a library caller."""
    import pytest

    from component_analysis import dla

    with pytest.raises(ValueError, match="nosuch"):
        dla.parse_conditions(["nosuch"])


def test_an_empty_selection_still_means_every_condition():
    """`--dla-conditions ""` meant "all" before the flag was validated at parse
    time, and a silent change from all to none would cost a run its numbers."""
    from component_analysis import dla

    assert dla.parse_conditions("") == list(dla.CONDITIONS)
    assert dla.parse_conditions([]) == list(dla.CONDITIONS)


# ==============================================================================
# THE HEAD-TABLE COLUMNS AND THEIR COVERAGE (ticket 13)
# ==============================================================================

KEYS = [("head", 17, 25), ("mlp", 31, 0)]
SAMPLE = [f"sdr-{one}" for one in range(5)]
PAIRED = SAMPLE[:3]
TWIN_DIR = "data/datasets/sdr_honest"


def _condition(ids, mean):
    return {"n_instances": len(ids), "instance_ids": list(ids),
            "components": [{"key": list(key), "levels": {
                "all": {"mean": mean, "se": 0.01, "n": len(ids)}}}
                for key in KEYS]}


def _payload(*, honest=True):
    conditions = {dla.PRESSURE: _condition(SAMPLE, 0.2),
                  dla.HONEST_TWIN: _condition(["t-0", "t-1"], 0.1)}
    if honest:
        conditions.update({dla.PRESSURE_PAIRED: _condition(PAIRED, 0.3),
                           dla.HONEST_INSTRUCTION: _condition(PAIRED, -0.4),
                           dla.DIFFERENTIAL: _condition(PAIRED, 0.7)})
    return {"suppression_margin": dla.DEFAULT_SUPPRESSION_MARGIN,
            "conditions": conditions,
            "sources": {dla.PRESSURE: {"dataset_dir": "data/datasets/sdr"},
                        dla.HONEST_TWIN: {"dataset_dir": TWIN_DIR}}}


def _written_meta(tmp_path, payload):
    """The columns and the coverage written into a head table, the way the CLI
    writes them, and read back off disk. No model: only the payload."""
    from component_analysis import head_table, registry

    ctx = registry.AnalysisContext(cli=None, intake=None, circuit_spec=None,
                                   task_spec=None, components=[],
                                   cell_dir=str(tmp_path))
    dla.declare_coverage(ctx, payload)
    rows = head_table.merge_columns([], dla.columns(payload), namespace=dla.NAME)
    meta = head_table.add_declarations({}, ctx.take_coverage(),
                                       namespace=dla.NAME)
    head_table.write_head_table(str(tmp_path), rows, meta=meta)
    return head_table.load_head_table_meta(str(tmp_path))


def test_every_paired_dla_column_says_paired_in_its_name():
    row = dla.columns(_payload())[KEYS[0]]

    assert row["honest_instruction_paired"] == -0.4
    assert row["differential_paired"] == 0.7
    assert row["differential_paired_se"] == 0.01
    assert row["pressure_paired"] == 0.3
    assert not {"honest_instruction", "differential", "differential_se"} & set(row)
    assert row["honest_twin_descriptive"] == 0.1, "the unpaired one says descriptive"


def test_every_dla_column_says_in_the_written_table_which_instances_it_covers(
        tmp_path):
    from component_analysis.head_table import coverage_of

    meta = _written_meta(tmp_path, _payload())

    assert set(meta["coverage"]) == {f"dla.{column}" for column
                                     in dla.columns(_payload())[KEYS[0]]}
    for column in ("pressure", "pressure_se", "suppression"):
        entry = coverage_of(meta, f"dla.{column}")
        assert (entry["n"], entry["instance_ids"]) == (len(SAMPLE), SAMPLE)
        assert entry["instance_set"].startswith("test_split:")
    for column in ("pressure_paired", "honest_instruction_paired",
                   "differential_paired", "differential_paired_se"):
        entry = coverage_of(meta, f"dla.{column}")
        assert (entry["n"], entry["instance_ids"]) == (len(PAIRED), PAIRED)
        assert entry["instance_set"].startswith("paired_honest_instruction:")
    twin = coverage_of(meta, "dla.honest_twin_descriptive")
    assert twin["instance_ids"] == ["t-0", "t-1"] and twin["dataset"] == TWIN_DIR
    assert len(meta["instance_sets"]) == 3, "one set per population, written once"


def test_a_paired_condition_that_did_not_run_is_written_as_covering_nothing(
        tmp_path):
    from component_analysis.head_table import coverage_of

    meta = _written_meta(tmp_path, _payload(honest=False))

    entry = coverage_of(meta, "dla.differential_paired")
    assert entry["n"] == 0 and entry["instance_set"] is None
    assert coverage_of(meta, "dla.pressure")["n"] == len(SAMPLE)
