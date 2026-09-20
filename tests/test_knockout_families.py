"""
Knockout by role family: the grouping, the summary and the files.

The arithmetic over numbers a forward already produced, tested everywhere the
package imports. What the grouped forward actually does to the model is
`tests/test_knockout_families_model.py`, which needs nnsight 0.7.0.

The family question is the one a per-Component ranking cannot answer: whether a
family of small effects is a large one together. Its sign convention is the
single knockout's, unchanged — positive means the family helps deception.
"""

from __future__ import annotations

import os

import pytest

from component_analysis import knockout

SELECTOR = ("head", 17, 25)
MOVER = ("mlp", 31, 0)
UNKNOWN = ("head", 5, 11)


def row(kind, layer, index, proposed=None, confirmed=None):
    one = {"kind": kind, "layer": layer, "index": index,
           "roles.role_proposed": proposed}
    if confirmed is not None:
        one["role_confirmed"] = confirmed
    return one


@pytest.fixture
def rows():
    return [row("head", 5, 11, "unknown"),
            row("head", 17, 25, "selector"),
            row("mlp", 31, 0, "mover"),
            row("head", 24, 18, "unknown")]


def effects_over(families, values):
    """An `Effects` whose per-family numbers are handed in rather than measured."""
    return knockout.Effects(
        ids=["a", "b"], keys=list(families),
        clean_logit_difference=[1.0, 2.0],
        knocked_logit_difference={label: list(one)
                                  for label, one in values.items()})


# ==============================================================================
# WHICH COMPONENTS SHARE A ROLE
# ==============================================================================

def test_components_are_grouped_by_their_proposed_role(rows):
    families = knockout.families_from_rows(rows)

    assert families["unknown"] == [UNKNOWN, ("head", 24, 18)]
    assert families["selector"] == [SELECTOR]
    assert families["mover"] == [MOVER]


def test_a_confirmed_role_wins_over_the_proposed_one(rows):
    """The researcher's column is the grouping when the researcher has set it."""
    rows[1]["role_confirmed"] = "mover"

    families = knockout.families_from_rows(rows)

    assert families["mover"] == [SELECTOR, MOVER]
    assert "selector" not in families


def test_a_component_with_no_role_at_all_is_left_out_rather_than_guessed(rows):
    rows.append(row("head", 2, 2))

    families = knockout.families_from_rows(rows)

    assert ("head", 2, 2) not in [one for group in families.values()
                                  for one in group]


def test_a_table_with_no_role_column_makes_no_families():
    assert knockout.families_from_rows(
        [{"kind": "head", "layer": 1, "index": 1}]) == {}


def test_the_families_keep_head_table_order(rows):
    assert list(knockout.families_from_rows(rows)) == ["unknown", "selector",
                                                       "mover"]


# ==============================================================================
# THE SUMMARY
# ==============================================================================

def test_a_family_is_ranked_by_its_signed_drop_like_a_single_component(rows):
    families = knockout.families_from_rows(rows)
    effects = effects_over(families, {"unknown": [1.2, 2.1],
                                      "selector": [0.4, 1.4],
                                      "mover": [1.1, 2.4]})

    ranked = knockout.summarize_families(effects, families)

    assert [one["role"] for one in ranked] == ["selector", "unknown", "mover"]
    assert ranked[0]["mean_drop"] == pytest.approx(0.6)
    assert ranked[0]["rank"] == 1
    assert ranked[-1]["mean_drop"] == pytest.approx(-0.25), \
        "a family that opposes deception sits at the bottom, not by magnitude"


def test_a_family_row_names_its_members_and_counts_them(rows):
    families = knockout.families_from_rows(rows)
    effects = effects_over(families, {"unknown": [1.0, 1.0],
                                      "selector": [1.0, 1.0],
                                      "mover": [1.0, 1.0]})

    ranked = {one["role"]: one for one in
              knockout.summarize_families(effects, families)}

    assert ranked["unknown"]["n_components"] == 2
    assert ranked["unknown"]["members"] == [list(UNKNOWN), ["head", 24, 18]]


def test_every_component_carries_its_family_s_drop_into_the_head_table(rows):
    families = knockout.families_from_rows(rows)
    effects = effects_over(families, {"unknown": [0.5, 1.5],
                                      "selector": [0.5, 1.5],
                                      "mover": [0.5, 1.5]})

    columns = knockout.family_columns(
        knockout.summarize_families(effects, families))

    assert columns[UNKNOWN]["family"] == "unknown"
    assert columns[UNKNOWN]["family_logit_diff_drop"] == pytest.approx(0.5)
    assert columns[("head", 24, 18)]["family"] == "unknown"


def test_the_payload_states_the_same_sign_convention_as_the_single_knockout(rows):
    families = knockout.families_from_rows(rows)
    effects = effects_over(families, {"unknown": [1.0, 1.0],
                                      "selector": [1.0, 1.0],
                                      "mover": [1.0, 1.0]})

    payload = knockout.family_payload(effects, families, circuit="delta",
                                      task="sdr")

    assert "helps deception" in payload["metric"]["sign"]
    assert payload["grouping"]["column"] == "role_confirmed, else roles.role_proposed"
    assert payload["n_families"] == 3
    assert payload["clean_run"]["n_instances"] == 2
    assert [one["role"] for one in payload["families"]]


def test_the_figure_is_written_beside_the_single_component_one(rows, tmp_path):
    families = knockout.families_from_rows(rows)
    effects = effects_over(families, {"unknown": [1.0, 1.0],
                                      "selector": [0.5, 0.5],
                                      "mover": [0.2, 0.2]})
    path = os.path.join(str(tmp_path), knockout.FAMILY_PNG_NAME)

    knockout.write_family_figure(
        path, knockout.summarize_families(effects, families))

    assert os.path.exists(path)
    assert knockout.FAMILY_JSON_NAME != knockout.JSON_NAME
    assert knockout.FAMILY_PNG_NAME != knockout.PNG_NAME


def test_an_empty_family_set_is_refused_rather_than_drawn(tmp_path):
    with pytest.raises(ValueError, match="no family"):
        knockout.write_family_figure(
            os.path.join(str(tmp_path), "x.png"), [])
