"""
DLA on v2 (ticket 02a): the `neutral_twin` paired condition and its columns,
and the per-instance logit-lens crossing summary for R-lens (exploratory,
R12; R19 adds the last sign change). The model-free parts run everywhere.
"""

from __future__ import annotations

from types import SimpleNamespace


from component_analysis import dla


# ==============================================================================
# THE CROSSING RULE (layers 8..28, margin < -0.5, the final sign)
# ==============================================================================

def lens(by_layer, final, n_layers=32):
    """Rows: row 0 the embedding, row l+1 after layer l. `by_layer` sets layers."""
    rows = [0.1] * (n_layers + 1)
    for layer, value in by_layer.items():
        rows[layer + 1] = value
    rows[-1] = final
    return rows


def test_an_instance_that_goes_honest_in_the_window_and_ends_deceptive_is_honest_first():
    one = dla.lens_crossing(lens({7: -2.0, 12: -0.6, 13: -0.9, 20: 0.3}, final=1.4))
    # Layer 7 is below the window; layer 12 is the first in 8..28 under -0.5.
    assert one["first_layer_below"] == 12
    assert one["first_row_below"] == 13
    assert one["final_sign"] == 1
    assert one["honest_first"] is True


def test_a_margin_of_exactly_the_cut_is_not_below_it():
    one = dla.lens_crossing(lens({10: -0.5}, final=1.0))
    assert one["first_layer_below"] is None and one["honest_first"] is False


def test_an_instance_that_ends_honest_is_not_honest_first():
    one = dla.lens_crossing(lens({9: -1.0}, final=-0.2))
    assert one["first_layer_below"] == 9
    assert one["final_sign"] == -1
    assert one["honest_first"] is False


def test_a_dip_after_layer_28_does_not_count():
    one = dla.lens_crossing(lens({29: -3.0}, final=2.0))
    assert one["first_layer_below"] is None


def test_the_last_sign_change_is_recorded_as_a_layer():
    # Positive from the embedding to layer 9, negative at 10-11, positive after.
    one = dla.lens_crossing(lens({10: -0.7, 11: -0.2}, final=0.8))
    assert one["last_sign_change_row"] == 13
    assert one["last_sign_change_layer"] == 12


# ==============================================================================
# WHICH CONDITIONS RUN, AND THE COLUMNS THEY WRITE
# ==============================================================================

def ctx(task, conditions=None):
    return SimpleNamespace(cli=SimpleNamespace(dla_conditions=conditions),
                           task_spec=SimpleNamespace(name=task))


def test_a_v2_cell_adds_the_neutral_twin_condition_by_default():
    assert dla.wanted_conditions_for(ctx("sdr_v2")) == list(dla.CONDITIONS) + [dla.NEUTRAL_TWIN]


def test_a_v1_cell_runs_the_conditions_it_always_ran():
    assert dla.wanted_conditions_for(ctx("sdr")) == list(dla.CONDITIONS)


def test_an_explicit_selection_is_kept_as_given():
    assert dla.wanted_conditions_for(ctx("sdr_v2", [dla.PRESSURE])) == [dla.PRESSURE]
    assert dla.parse_conditions("pressure,neutral_twin") == [dla.PRESSURE, dla.NEUTRAL_TWIN]


def payload_with(conditions, skipped=()):
    def condition(mean):
        return {"components": [{"key": ["head", 1, 2], "levels": {
            dla.ALL: {"mean": mean, "se": 0.01, "n": 4}}}], "instance_ids": ["a"]}
    return {"suppression_margin": 0.05,
            "conditions": {name: condition(value) for name, value in conditions.items()},
            "skipped": {name: "why" for name in skipped}}


def test_the_twin_columns_say_paired_in_their_names():
    payload = payload_with({dla.PRESSURE: 0.3, dla.NEUTRAL_TWIN: 0.1,
                            dla.PRESSURE_NEUTRAL_TWIN_PAIRED: 0.25,
                            dla.DIFFERENTIAL_NEUTRAL_TWIN: 0.15})
    row = dla.columns(payload)[("head", 1, 2)]
    assert row["neutral_twin_paired"] == 0.1
    assert row["pressure_neutral_twin_paired"] == 0.25
    assert row["differential_neutral_twin_paired"] == 0.15
    assert row["differential_neutral_twin_paired_se"] == 0.01


def test_a_cell_that_never_asked_for_the_twin_has_no_twin_columns():
    row = dla.columns(payload_with({dla.PRESSURE: 0.3}))[("head", 1, 2)]
    assert not [column for column in row if "neutral_twin" in column]


def test_a_cell_where_the_twin_was_skipped_still_has_the_empty_columns():
    row = dla.columns(payload_with({dla.PRESSURE: 0.3},
                                   skipped=[dla.NEUTRAL_TWIN]))[("head", 1, 2)]
    assert row["neutral_twin_paired"] is None


def test_the_twin_reads_in_the_deception_direction():
    assert dla.direction_sign(dla.NEUTRAL_TWIN) == 1
    assert dla.direction_sign(dla.HONEST_TWIN) == -1
