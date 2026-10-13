"""
The knockout completeness sweep, at the seams that need no model: the ranked
list, circuit membership, the threshold, the head-table columns, the JSON and
the PNG, and `--dry-run`'s sizing at the CLI.

The forwards have their own tests on the tiny random Llama in
`tests/test_knockout_model.py`, which nnsight 0.7.0 gates. Everything here is
arithmetic over numbers a forward already produced, worked by hand, so it runs
in both environments.
"""

from __future__ import annotations

import json
import os

import pytest

from component_analysis import knockout
from tests.test_analyze_components_end_to_end import written_files  # noqa: F401
from tests.test_analyze_components_segmentation import (  # noqa: F401
    CELL, run_cli, sdr_run)


def effects(clean, knocked):
    return knockout.Effects(
        ids=[f"i{n}" for n in range(len(clean))],
        keys=list(knocked),
        clean_logit_difference=list(clean),
        knocked_logit_difference={key: list(values)
                                  for key, values in knocked.items()})


#: Four Components of a pretend model, two of them in the circuit. Drops:
#: head 0.0 +0.30, head 0.1 -0.50 (opposes deception), mlp 0 +0.05,
#: head 1.0 +0.12.
SWEPT = effects(
    clean=[2.0, 2.0],
    knocked={("head", 0, 0): [1.7, 1.7],
             ("head", 0, 1): [2.5, 2.5],
             ("mlp", 0, 0): [1.95, 1.95],
             ("head", 1, 0): [1.88, 1.88]})
CIRCUIT = [("head", 0, 0), ("mlp", 0, 0)]


def by_key(rows):
    return {tuple(row["key"]): row for row in rows}


# ==============================================================================
# THE RANKED LIST
# ==============================================================================

def test_the_sweep_ranks_every_component_by_the_size_of_its_drop_either_sign():
    """A strong suppressor outside the circuit is exactly what the sweep is for,
    so it ranks by |drop| and keeps the sign in the drop."""
    rows = knockout.summarize_sweep(SWEPT, CIRCUIT, threshold=0.1)

    assert [tuple(row["key"]) for row in rows] == [
        ("head", 0, 1), ("head", 0, 0), ("head", 1, 0), ("mlp", 0, 0)]
    assert [row["rank"] for row in rows] == [1, 2, 3, 4]
    assert [row["mean_drop"] for row in rows] == pytest.approx(
        [-0.5, 0.3, 0.12, 0.05])


def test_the_signed_rank_is_carried_beside_it_on_knockout_s_own_convention():
    rows = by_key(knockout.summarize_sweep(SWEPT, CIRCUIT, threshold=0.1))

    assert rows[("head", 0, 0)]["signed_rank"] == 1
    assert rows[("head", 1, 0)]["signed_rank"] == 2
    assert rows[("mlp", 0, 0)]["signed_rank"] == 3
    assert rows[("head", 0, 1)]["signed_rank"] == 4


def test_circuit_membership_is_marked_and_only_outsiders_are_flagged():
    rows = by_key(knockout.summarize_sweep(SWEPT, CIRCUIT, threshold=0.1))

    assert rows[("head", 0, 0)]["in_circuit"] is True
    assert rows[("head", 0, 1)]["in_circuit"] is False
    # Clears the threshold, inside the circuit: clears, not flagged.
    assert rows[("head", 0, 0)]["clears_threshold"] is True
    assert rows[("head", 0, 0)]["flagged"] is False
    # Outside the circuit and above the threshold on either side: flagged.
    assert rows[("head", 0, 1)]["flagged"] is True
    assert rows[("head", 1, 0)]["flagged"] is True
    # Inside the circuit and below it: neither.
    assert rows[("mlp", 0, 0)]["clears_threshold"] is False


def test_a_drop_exactly_at_the_threshold_clears_it():
    rows = by_key(knockout.summarize_sweep(SWEPT, CIRCUIT, threshold=0.5))

    assert rows[("head", 0, 1)]["clears_threshold"] is True
    assert rows[("head", 0, 0)]["clears_threshold"] is False


def test_a_sweep_row_carries_the_single_knockout_s_numbers_for_its_component():
    """The same summary as `knockout.json`'s, plus the sweep's own fields."""
    single = by_key([{**row, "key": list(row["key"])}
                     for row in knockout.summarize(SWEPT)])
    swept = by_key(knockout.summarize_sweep(SWEPT, CIRCUIT, threshold=0.1))

    for key, row in swept.items():
        for field in ("mean_drop", "standard_error", "accuracy",
                      "knocked_logit_difference", "n"):
            assert row[field] == single[key][field]


def test_the_kv_group_of_a_head_outside_the_circuit_comes_from_the_geometry():
    rows = by_key(knockout.summarize_sweep(SWEPT, CIRCUIT, threshold=0.1,
                                           heads_per_group=2))

    assert rows[("head", 0, 1)]["kv_group"] == 0
    assert rows[("mlp", 0, 0)]["kv_group"] is None


def test_restricting_the_effects_to_the_circuit_keeps_every_number():
    """How `knockout.json` is read out of the sweep's forwards: no recompute."""
    circuit = SWEPT.restrict([("mlp", 0, 0), ("head", 0, 0)])

    assert circuit.keys == [("mlp", 0, 0), ("head", 0, 0)]
    assert circuit.ids == SWEPT.ids
    assert circuit.clean_logit_difference == SWEPT.clean_logit_difference
    assert circuit.knocked_logit_difference == {
        ("mlp", 0, 0): SWEPT.knocked_logit_difference[("mlp", 0, 0)],
        ("head", 0, 0): SWEPT.knocked_logit_difference[("head", 0, 0)]}


def test_restricting_to_a_component_the_sweep_never_knocked_out_is_refused():
    with pytest.raises(ValueError, match="mlp"):
        SWEPT.restrict([("mlp", 7, 0)])


# ==============================================================================
# THE HEAD TABLE, THE JSON, THE PNG
# ==============================================================================

def test_only_circuit_components_get_sweep_columns():
    """Non-circuit Components are listed in the JSON, never added as rows."""
    rows = knockout.summarize_sweep(SWEPT, CIRCUIT, threshold=0.1)

    columns = knockout.sweep_columns(rows)

    assert columns == {("head", 0, 0): {"sweep_rank": 2,
                                        "sweep_clears_threshold": True},
                       ("mlp", 0, 0): {"sweep_rank": 4,
                                       "sweep_clears_threshold": False}}


def test_the_json_lists_the_flagged_outsiders_and_states_its_conventions():
    rows = knockout.summarize_sweep(SWEPT, CIRCUIT, threshold=0.1)

    written = knockout.sweep_payload(SWEPT, rows, circuit="delta", task="sdr",
                                     threshold=0.1)

    assert written["flagged"] == ["head.0.1", "head.1.0"]
    assert written["threshold"] == 0.1
    assert "logits" in written["threshold_units"]
    assert "positive drop means the Component helps deception" \
        in written["metric"]["sign"]
    assert "|drop|" in written["metric"]["ranking"]
    assert "embedding" in written["excludes"]
    assert "twice the standard error" in written["threshold_justification"]
    assert "knockout.sweep_rank" in written["head_table_columns"]
    assert written["n_components"] == 4 and written["n_in_circuit"] == 2
    assert [one["key"] for one in written["components"]] == [
        ["head", 0, 1], ["head", 0, 0], ["head", 1, 0], ["mlp", 0, 0]]
    assert written["instances"] == ["i0", "i1"]
    assert written["clean_run"]["mean_logit_difference"] == 2.0
    json.dumps(written)


def test_the_json_counts_what_clears_each_cut_so_the_threshold_can_move():
    rows = knockout.summarize_sweep(SWEPT, CIRCUIT, threshold=0.1)

    counts = {one["threshold"]: one for one in knockout.sweep_payload(
        SWEPT, rows, circuit="delta", task="sdr",
        threshold=0.1)["threshold_counts"]}

    # |drops|: 0.5 out, 0.3 in, 0.12 out, 0.05 in.
    assert counts[0.05] == {"threshold": 0.05, "outside_circuit": 2,
                            "in_circuit": 2}
    assert counts[0.2] == {"threshold": 0.2, "outside_circuit": 1,
                           "in_circuit": 1}


def test_the_png_is_written_and_is_a_png(tmp_path):
    rows = knockout.summarize_sweep(SWEPT, CIRCUIT, threshold=0.1)
    path = str(tmp_path / knockout.SWEEP_PNG_NAME)

    knockout.write_sweep_figure(path, rows, threshold=0.1)

    with open(path, "rb") as handle:
        assert handle.read(8) == b"\x89PNG\r\n\x1a\n"


def test_an_empty_sweep_is_refused_rather_than_drawn(tmp_path):
    with pytest.raises(ValueError, match="no Component"):
        knockout.write_sweep_figure(str(tmp_path / "x.png"), [], threshold=0.1)


def test_the_sweep_size_is_every_head_and_every_mlp_block():
    """1056 on Llama-3.1-8B: the ticket's "about 1057" counted the embedding,
    which the path-patching sweep includes and a knockout cannot."""
    assert knockout.sweep_size({"num_layers": 32, "num_heads": 32}) == 1056


# ==============================================================================
# THE CLI FLAGS
# ==============================================================================

def parse(*argv):
    import argparse

    parser = argparse.ArgumentParser()
    knockout.add_arguments(parser)
    return parser.parse_args(list(argv))


def test_the_sweep_is_off_by_default_and_the_threshold_has_its_stated_default():
    cli = parse()

    assert cli.knockout_completeness_sweep is False
    assert cli.knockout_sweep_threshold == knockout.DEFAULT_SWEEP_THRESHOLD == 0.1


def test_a_negative_threshold_is_refused_at_parse_time(capsys):
    with pytest.raises(SystemExit):
        parse("--knockout-sweep-threshold", "-0.1")
    assert "knockout-sweep-threshold" in capsys.readouterr().err


# ==============================================================================
# --dry-run, AT THE CLI SEAM
# ==============================================================================

@pytest.fixture
def registered(monkeypatch):
    """The knockout, and nothing else, registered; no model is ever loaded."""
    import analyze_components
    from component_analysis import registry

    monkeypatch.setattr(registry, "ANALYSES", [knockout])
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: pytest.fail("a dry run loaded "
                                                          "the model"))
    return knockout


def knockout_line(printed):
    return next(one for one in printed.splitlines()
                if one.strip().startswith(f"{knockout.NAME}: "))


def test_dry_run_sizes_the_sweep_over_every_component_of_the_model(
        sdr_run, registered, capsys):
    """The tiny model has 2 layers x (4 heads + 1 MLP block) = 10 Components,
    and the sweep's forwards replace the circuit's singles rather than adding
    to them: (10 + 2) per batch."""
    import re

    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--n-causal", "16", "--knockout-completeness-sweep",
                   "--output-dir", str(out)) == 0

    line = knockout_line(capsys.readouterr().out)
    assert "completeness sweep: 10 Component(s) of the model" in line
    batches = int(re.search(r"x (\d+) batch\(es\)", line).group(1))
    assert batches >= 1
    assert f"= {batches * 12} forward pass(es)" in line
    assert "threshold 0.1 logits" in line


def test_without_the_flag_the_dry_run_does_not_mention_a_sweep(
        sdr_run, registered, capsys):
    run_dir, out, _records = sdr_run

    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2", "--n-causal",
            "16", "--output-dir", str(out))

    assert "completeness sweep" not in knockout_line(capsys.readouterr().out)


def test_the_sweep_dry_run_writes_nothing_of_the_analysis(sdr_run, registered):
    run_dir, out, _records = sdr_run

    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2", "--n-causal",
            "16", "--knockout-completeness-sweep", "--output-dir", str(out))

    assert written_files(out) == [os.path.join(*CELL, name) for name in
                                  ("head_table.csv", "head_table.json",
                                   "sample.json", "segmentation.json")]
    assert not os.path.exists(os.path.join(str(out), *CELL, knockout.SUBDIR))


# ==============================================================================
# THE REVIEW VIEW
# ==============================================================================

def write_sweep_cell(tmp_path, threshold=0.1):
    rows = knockout.summarize_sweep(SWEPT, CIRCUIT, threshold=threshold)
    directory = tmp_path / knockout.SUBDIR
    directory.mkdir(parents=True)
    (directory / knockout.SWEEP_JSON_NAME).write_text(json.dumps(
        knockout.sweep_payload(SWEPT, rows, circuit="delta", task="sdr",
                               threshold=threshold)))
    return str(tmp_path)


def test_the_review_view_draws_the_sweep_in_its_rank_order(tmp_path):
    from component_analysis import review

    view = review.knockout_sweep_view(write_sweep_cell(tmp_path))

    assert view
    assert view.labels == ["head.0.1", "head.0.0", "head.1.0", "mlp.0.0"]
    assert view.values == pytest.approx([-0.5, 0.3, 0.12, 0.05])
    assert "in the circuit" in view.hover[1]
    assert "flagged" in view.hover[0] and "flagged" not in view.hover[1]
    assert any("|drop|" in note for note in view.notes)
    assert any("head.0.1, head.1.0" in note for note in view.notes)


def test_a_cell_without_a_sweep_renders_a_note_not_an_error(tmp_path):
    from component_analysis import review

    view = review.knockout_sweep_view(str(tmp_path))

    assert not view
    assert "--knockout-completeness-sweep" in view.note
