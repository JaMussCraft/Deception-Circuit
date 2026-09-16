"""
Library-seam tests for the parts of the per-Component knockout that need no
model: the ranking, the standard error, the accuracy, the scheme flag and the
two files the researcher reads.

The forward passes have their own tests on the tiny random Llama in
`tests/test_knockout_model.py`, which nnsight 0.7.0 gates. Everything here is
arithmetic over numbers a forward already produced, so it runs in both
environments and the expected values are worked by hand rather than recomputed
the way `summarize` computes them.
"""

from __future__ import annotations

import json
import math
import os

import pytest

from component_analysis import knockout


def effects(clean, knocked, ids=None):
    """Hand-built per-instance numbers, as one forward loop would have left them."""
    return knockout.Effects(
        ids=list(ids or [f"i{n}" for n in range(len(clean))]),
        keys=list(knocked),
        clean_logit_difference=list(clean),
        knocked_logit_difference={key: list(values)
                                  for key, values in knocked.items()},
    )


# ==============================================================================
# THE RANKING
# ==============================================================================

def test_components_are_ranked_by_how_much_knocking_them_out_costs():
    """Rank 1 is the Component whose knockout drops the metric the most."""
    got = knockout.summarize(effects(
        clean=[4.0, 4.0],
        knocked={("head", 0, 1): [3.0, 3.0],      # drop 1.0
                 ("head", 5, 2): [1.0, 1.0],      # drop 3.0
                 ("mlp", 3, 0): [4.0, 4.0]}))     # drop 0.0

    assert [row["key"] for row in got] == [("head", 5, 2), ("head", 0, 1),
                                           ("mlp", 3, 0)]
    assert [row["rank"] for row in got] == [1, 2, 3]
    assert [row["mean_drop"] for row in got] == [3.0, 1.0, 0.0]


def test_a_component_that_fights_deception_gets_a_negative_drop():
    """The sign convention: positive helps deception, negative opposes it.

    A suppressor's knockout *raises* logit(Target) - logit(Distractor), so its
    drop is negative and it sorts to the bottom rather than being ranked by
    magnitude — a ranking that mixed the two directions could not be read.
    """
    got = knockout.summarize(effects(
        clean=[1.0], knocked={("head", 0, 0): [5.0], ("head", 0, 1): [0.5]}))

    assert got[0]["key"] == ("head", 0, 1) and got[0]["mean_drop"] == 0.5
    assert got[1]["key"] == ("head", 0, 0) and got[1]["mean_drop"] == -4.0


def test_ties_keep_the_order_the_components_came_in():
    got = knockout.summarize(effects(
        clean=[2.0], knocked={("head", 9, 9): [1.0], ("head", 0, 0): [1.0]}))

    assert [row["key"] for row in got] == [("head", 9, 9), ("head", 0, 0)]
    assert [row["rank"] for row in got] == [1, 2]


def test_the_standard_error_is_the_spread_over_the_causal_sample():
    """Drops of 1, 2 and 3: mean 2, sample sd 1, standard error 1/sqrt(3)."""
    got = knockout.summarize(effects(
        clean=[4.0, 4.0, 4.0], knocked={("head", 0, 0): [3.0, 2.0, 1.0]}))

    assert got[0]["mean_drop"] == pytest.approx(2.0)
    assert got[0]["standard_error"] == pytest.approx(1.0 / math.sqrt(3))
    assert got[0]["n"] == 3


def test_one_instance_has_no_standard_error_rather_than_a_zero_one():
    """Zero would read as "measured and tiny"; None reads as "not measured"."""
    got = knockout.summarize(effects(clean=[4.0], knocked={("head", 0, 0): [3.0]}))

    assert got[0]["mean_drop"] == pytest.approx(1.0)
    assert got[0]["standard_error"] is None


# ==============================================================================
# ACCURACY
# ==============================================================================

def test_accuracy_is_the_share_of_instances_the_target_still_wins():
    """Two of four instances keep a positive logit difference under the knockout."""
    got = knockout.summarize(effects(
        clean=[1.0, 1.0, 1.0, 1.0],
        knocked={("head", 0, 0): [0.5, -0.5, 2.0, -3.0]}))

    assert got[0]["accuracy"] == pytest.approx(0.5)
    assert got[0]["accuracy_drop"] == pytest.approx(0.5)   # clean accuracy is 1.0


def test_the_clean_run_is_reported_beside_the_knockouts():
    summary = knockout.clean_run(effects(
        clean=[2.0, -1.0], knocked={("head", 0, 0): [0.0, 0.0]}))

    assert summary["mean_logit_difference"] == pytest.approx(0.5)
    assert summary["accuracy"] == pytest.approx(0.5)
    assert summary["n_instances"] == 2


# ==============================================================================
# THE SCHEME FLAG
# ==============================================================================

def test_interchange_is_the_scheme_that_exists():
    assert knockout.resolve_scheme("interchange") == "interchange"


@pytest.mark.parametrize("scheme", ["mean", "zero"])
def test_mean_and_zero_are_refused_by_name_as_future_work(scheme):
    with pytest.raises(ValueError) as refused:
        knockout.resolve_scheme(scheme)

    message = str(refused.value)
    assert scheme in message and "future work" in message
    assert "interchange" in message


def test_an_unknown_scheme_is_refused_too():
    with pytest.raises(ValueError, match="nonsense"):
        knockout.resolve_scheme("nonsense")


def test_the_cli_refuses_the_scheme_before_a_gpu_is_touched(capsys):
    """argparse, so `--knockout-scheme zero` fails on the login node."""
    import analyze_components

    with pytest.raises(SystemExit):
        analyze_components.build_parser().parse_args(
            ["run", "--knockout-scheme", "zero"])

    stderr = capsys.readouterr().err
    assert "zero" in stderr and "future work" in stderr


def test_the_cli_takes_interchange():
    import analyze_components

    cli = analyze_components.build_parser().parse_args(
        ["run", "--knockout-scheme", "interchange"])

    assert cli.knockout_scheme == "interchange"


# ==============================================================================
# THE FILES
# ==============================================================================

def test_the_json_says_which_way_a_positive_drop_points():
    payload = knockout.payload(
        effects(clean=[1.0], knocked={("head", 0, 0): [0.0]}),
        circuit="delta", task="sdr")

    assert payload["scheme"] == "interchange"
    assert "clean" in payload["metric"]["sign"]
    assert "deception" in payload["metric"]["sign"]
    assert payload["metric"]["figure"] == knockout.PNG_NAME
    assert payload["components"][0]["key"] == ["head", 0, 0]


def test_the_png_is_written_and_is_a_png(tmp_path):
    rows = knockout.summarize(effects(
        clean=[2.0, 2.0],
        knocked={("head", 0, 1): [1.0, 1.5], ("mlp", 1, 0): [2.5, 2.0]}))
    path = os.path.join(str(tmp_path), knockout.PNG_NAME)

    knockout.write_figure(path, rows, title="delta x sdr")

    with open(path, "rb") as handle:
        assert handle.read(8) == b"\x89PNG\r\n\x1a\n"


def test_a_json_twin_and_a_png_carry_the_same_components(tmp_path):
    """The PNG is unreadable to an agent; the twin is what it reads instead."""
    made = effects(clean=[2.0], knocked={("head", 0, 1): [1.0], ("mlp", 1, 0): [3.0]})
    payload = knockout.payload(made, circuit="delta", task="sdr")
    with open(os.path.join(str(tmp_path), knockout.JSON_NAME), "w") as handle:
        json.dump(payload, handle)
    knockout.write_figure(os.path.join(str(tmp_path), knockout.PNG_NAME),
                          payload["components"], title="delta x sdr")

    with open(os.path.join(str(tmp_path), knockout.JSON_NAME)) as handle:
        twin = json.load(handle)
    # The head's knockout costs 1.0 of margin, the MLP block's knockout adds
    # 1.0, so the head is rank 1 and the MLP block is last.
    assert [one["key"] for one in twin["components"]] == [["head", 0, 1],
                                                          ["mlp", 1, 0]]
    assert twin["clean_run"]["n_instances"] == 1


def test_the_head_table_columns_are_the_ones_the_orchestrator_named():
    updates = knockout.columns(knockout.summarize(effects(
        clean=[2.0], knocked={("head", 0, 1): [1.0], ("mlp", 1, 0): [3.0]})))

    assert set(updates) == {("head", 0, 1), ("mlp", 1, 0)}
    # Bare names: the CLI puts the `knockout` namespace in front of each, and
    # ticket 03 looks the result up as `knockout.rank`.
    assert set(updates[("head", 0, 1)]) == set(knockout.COLUMNS)
    assert updates[("head", 0, 1)]["rank"] == 1
    assert updates[("mlp", 1, 0)]["rank"] == 2
    assert updates[("head", 0, 1)]["logit_diff_drop"] == pytest.approx(1.0)
    assert updates[("mlp", 1, 0)]["logit_diff_drop"] == pytest.approx(-1.0)
    assert updates[("head", 0, 1)]["accuracy"] == pytest.approx(1.0)
