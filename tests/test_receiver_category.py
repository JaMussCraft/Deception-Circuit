"""
The receiver category per head (mechanism-analysis spec §2.3, R11(g); ticket
02b): from the neutral-twin path-patching outputs, the strongest incoming path
at or above the 0.01 floor, read as

    q               arrives at the head's own query (selector)
    kv_clause       K or V of the head's KV group, from the clause span
    kv_post_clause  K or V, from positions after the clause
    kv_unresolved   K or V, but no Segment split for the cell, or its top
                    Segment is `unsegmented` (or, a bug, before the clause)
    none            nothing at or above the floor

Pure: built from synthetic `agnostic_neutral_twin.json` / `segments_neutral_twin.json`
tables, no model. The writer is tested on a hand-made cell directory.
"""

from __future__ import annotations

import json
import os

import pytest

from component_analysis import receiver_category as rc
from component_analysis.head_table import (CAUSAL_SAMPLE_NEUTRAL_TWIN, coverage_of,
                                           load_head_table, load_head_table_meta,
                                           write_head_table)

# Layer 1 of a 2-group model: heads 0 and 1 share KV group 0, heads 2 and 3
# share group 1; heads 0, 1, 2 and 3 are all in the circuit.
RECEIVERS = [
    {"key": "q.1.0", "kind": "q", "layer": 1, "index": 0, "covers_heads": [0], "circuit_heads": [0]},
    {"key": "q.1.1", "kind": "q", "layer": 1, "index": 1, "covers_heads": [1], "circuit_heads": [1]},
    {"key": "q.1.2", "kind": "q", "layer": 1, "index": 2, "covers_heads": [2], "circuit_heads": [2]},
    {"key": "q.1.3", "kind": "q", "layer": 1, "index": 3, "covers_heads": [3], "circuit_heads": [3]},
    {"key": "k.1.0", "kind": "k", "layer": 1, "index": 0, "covers_heads": [0, 1], "circuit_heads": [0, 1]},
    {"key": "v.1.0", "kind": "v", "layer": 1, "index": 0, "covers_heads": [0, 1], "circuit_heads": [0, 1]},
    {"key": "k.1.1", "kind": "k", "layer": 1, "index": 1, "covers_heads": [2, 3], "circuit_heads": [2, 3]},
    {"key": "v.1.1", "kind": "v", "layer": 1, "index": 1, "covers_heads": [2, 3], "circuit_heads": [2, 3]},
    {"key": "readout", "kind": "readout", "layer": 2, "index": 0, "covers_heads": [], "circuit_heads": []},
]


def cell(sender, receiver, mean, se=0.001, n=8):
    return {"sender": sender, "receiver": receiver, "cell": f"{sender}->{receiver}",
            "mean": mean, "se": se, "n": n, "n_excluded": 0}


def agnostic(cells, ids=("i0", "i1", "i2")):
    return {"analysis": "path_patching", "pass": "position_agnostic",
            "counterfactual": "neutral_twin", "receivers": RECEIVERS,
            "cells": cells, "sample": {"instance_ids": list(ids)}}


def split(cell_name, top, mean=None):
    return {"cell": cell_name, "receiver_kind": cell_name.split("->")[1][0],
            "top_segment": {"segment": top, "mean": mean if mean is not None else 0.5},
            "by_segment": {}}


def segments(cells):
    return {"analysis": "path_patching", "pass": "position_specific",
            "counterfactual": "neutral_twin", "cells": cells}


HEADS = [("head", 1, 0), ("head", 1, 1), ("head", 1, 2), ("head", 1, 3)]


def categorize(cells, splits=(), floor=rc.FLOOR):
    return rc.categorize(agnostic(cells), segments(list(splits)), HEADS, floor=floor)


# ==============================================================================
# THE FOUR CATEGORIES, AND NONE
# ==============================================================================

def test_a_query_arrival_is_q():
    out = categorize([cell("head.0.3", "q.1.0", 0.05), cell("head.0.3", "k.1.0", 0.02)],
                     [split("head.0.3->k.1.0", "pressure_clause")])
    one = out[("head", 1, 0)]
    assert one["category"] == "q"
    assert one["path"] == "head.0.3->q.1.0"
    assert one["support"] == 0.05 and one["se"] == 0.001
    assert one["segment"] is None
    assert one["tied"] == []


def test_a_key_arrival_from_the_clause_is_kv_clause():
    out = categorize([cell("head.0.3", "q.1.0", 0.02), cell("head.0.3", "k.1.0", 0.08)],
                     [split("head.0.3->k.1.0", "pressure_clause", 0.07)])
    one = out[("head", 1, 0)]
    assert one["category"] == "kv_clause"
    assert one["path"] == "head.0.3->k.1.0"
    assert one["support"] == 0.08
    assert one["segment"] == "pressure_clause"
    assert one["segment_support"] == 0.07


def test_a_value_arrival_from_after_the_clause_is_kv_post_clause():
    for segment in ("question", "response_line", "item_2_question_option", "stem", "readout"):
        out = categorize([cell("mlp.0.0", "v.1.1", -0.03)],
                         [split("mlp.0.0->v.1.1", segment)])
        assert out[("head", 1, 2)]["category"] == "kv_post_clause", segment
        assert out[("head", 1, 2)]["segment"] == segment
        assert out[("head", 1, 2)]["support"] == -0.03


def test_the_kv_cell_reaches_every_circuit_head_of_its_group():
    out = categorize([cell("mlp.0.0", "v.1.1", 0.03)],
                     [split("mlp.0.0->v.1.1", "question")])
    assert out[("head", 1, 2)]["category"] == out[("head", 1, 3)]["category"] == "kv_post_clause"
    assert out[("head", 1, 0)]["category"] == "none"


def test_a_kv_cell_without_a_segment_split_is_unresolved():
    """Between the category floor and --path-position-threshold no split was
    run, so the position is unknown; never folded into clause or post-clause."""
    out = categorize([cell("head.0.3", "k.1.0", 0.02)], [])
    one = out[("head", 1, 0)]
    assert one["category"] == "kv_unresolved"
    assert one["path"] == "head.0.3->k.1.0" and one["support"] == 0.02
    assert one["segment"] is None
    assert "no position-specific split" in one["note"]


def test_an_unsegmented_top_segment_is_unresolved():
    out = categorize([cell("head.0.3", "k.1.0", 0.02)],
                     [split("head.0.3->k.1.0", "unsegmented")])
    assert out[("head", 1, 0)]["category"] == "kv_unresolved"


def test_a_pre_clause_top_segment_is_unresolved_and_flagged_as_a_bug():
    """Every position before the clause is identical in D and its twin, so a
    neutral-twin path cannot originate there; one that reads so is a bug."""
    out = categorize([cell("head.0.3", "k.1.0", 0.02)],
                     [split("head.0.3->k.1.0", "designation_site")])
    one = out[("head", 1, 0)]
    assert one["category"] == "kv_unresolved"
    assert one["note"].startswith("!!")


def test_nothing_at_the_floor_is_none():
    out = categorize([cell("head.0.3", "q.1.0", 0.009), cell("head.0.3", "k.1.0", -0.0099),
                      cell("head.0.3", "q.1.1", None)])
    for key in HEADS:
        one = out[key]
        assert one["category"] == "none"
        assert one["path"] is None and one["support"] is None and one["se"] is None


def test_the_floor_is_inclusive_and_by_absolute_value():
    out = categorize([cell("head.0.3", "k.1.0", -0.01)],
                     [split("head.0.3->k.1.0", "pressure_clause")])
    assert out[("head", 1, 0)]["category"] == "kv_clause"


def test_a_lower_floor_admits_a_smaller_path():
    out = categorize([cell("head.0.3", "q.1.0", 0.005)], floor=0.004)
    assert out[("head", 1, 0)]["category"] == "q"


def test_the_strongest_is_by_absolute_mean_across_every_incoming_cell():
    out = categorize([cell("head.0.3", "q.1.0", 0.03), cell("mlp.0.0", "q.1.0", -0.04),
                      cell("head.0.3", "k.1.0", 0.035), cell("embed", "v.1.0", 0.02)],
                     [split("head.0.3->k.1.0", "pressure_clause")])
    assert out[("head", 1, 0)]["path"] == "mlp.0.0->q.1.0"
    assert out[("head", 1, 0)]["category"] == "q"
    # Head 1 shares the K and V cells but has its own query, with nothing on it.
    assert out[("head", 1, 1)]["path"] == "head.0.3->k.1.0"
    assert out[("head", 1, 1)]["category"] == "kv_clause"


# ==============================================================================
# TIES
# ==============================================================================

def test_a_k_v_tie_inside_one_group_that_agrees_on_the_span_keeps_the_category():
    out = categorize([cell("head.0.3", "k.1.0", 0.08), cell("head.0.3", "v.1.0", 0.08)],
                     [split("head.0.3->k.1.0", "pressure_clause"),
                      split("head.0.3->v.1.0", "pressure_clause")])
    one = out[("head", 1, 0)]
    assert one["category"] == "kv_clause"
    assert one["path"] == "head.0.3->k.1.0"            # receiver order q, k, v
    assert one["tied"] == ["head.0.3->k.1.0", "head.0.3->v.1.0"]


def test_a_k_v_tie_inside_one_group_that_disagrees_on_the_span_is_unresolved():
    out = categorize([cell("head.0.3", "k.1.0", -0.08), cell("head.0.3", "v.1.0", 0.08)],
                     [split("head.0.3->k.1.0", "pressure_clause"),
                      split("head.0.3->v.1.0", "question")])
    one = out[("head", 1, 0)]
    assert one["category"] == "kv_unresolved"
    assert one["tied"] == ["head.0.3->k.1.0", "head.0.3->v.1.0"]
    assert "tie" in one["note"]


def test_a_tie_between_q_and_k_goes_to_q_and_is_recorded():
    out = categorize([cell("head.0.3", "k.1.0", 0.05), cell("head.0.3", "q.1.0", 0.05)],
                     [split("head.0.3->k.1.0", "pressure_clause")])
    one = out[("head", 1, 0)]
    assert one["category"] == "q"
    assert one["tied"] == ["head.0.3->q.1.0", "head.0.3->k.1.0"]


# ==============================================================================
# THE SEGMENT CLASSES
# ==============================================================================

def test_the_segment_classes_follow_the_v2_segment_order():
    assert rc.segment_class("pressure_clause") == "clause"
    for name in ("question", "response_line", "item_1_question_pair",
                 "item_1_question_option", "item_2_question_pair",
                 "item_2_question_option", "stem", "readout"):
        assert rc.segment_class(name) == "post_clause", name
    for name in ("intro", "item_1_intro", "item_2_intro", "designating_sentence",
                 "designation_site", "predicate_token", "other_token",
                 "inverse_predicate_token", "designation_suffix"):
        assert rc.segment_class(name) == "pre_clause", name
    assert rc.segment_class("unsegmented") == "unresolved"
    assert rc.segment_class(None) == "unresolved"
    assert rc.segment_class("bos") == "unresolved"


# ==============================================================================
# COLUMNS AND THE WRITER
# ==============================================================================

def test_the_columns_carry_the_category_the_path_its_numbers_and_the_segment():
    out = categorize([cell("head.0.3", "k.1.0", 0.08)],
                     [split("head.0.3->k.1.0", "pressure_clause", 0.07)])
    columns = rc.columns(out)
    assert columns[("head", 1, 0)] == {
        "receiver_category_neutral_twin": "kv_clause",
        "receiver_category_neutral_twin_path": "head.0.3->k.1.0",
        "receiver_category_neutral_twin_support": 0.08,
        "receiver_category_neutral_twin_se": 0.001,
        "receiver_category_neutral_twin_segment": "pressure_clause",
    }
    assert columns[("head", 1, 2)]["receiver_category_neutral_twin"] == "none"
    assert columns[("head", 1, 2)]["receiver_category_neutral_twin_path"] is None


@pytest.fixture
def cell_dir(tmp_path):
    rows = [{"kind": "head", "layer": 1, "index": index, "kv_group": index // 2,
             "head_gate_active": True, "active_neuron_count": 0,
             "path_patching.direct_support_neutral_twin_paired": 0.1}
            for index in range(4)]
    rows.append({"kind": "mlp", "layer": 0, "index": 0, "kv_group": None,
                 "head_gate_active": None, "active_neuron_count": 5,
                 "path_patching.direct_support_neutral_twin_paired": 0.2})
    write_head_table(str(tmp_path), rows, meta={"task": {"task": "sdr_v2"}})
    sub = tmp_path / "path_patching"
    sub.mkdir()
    (sub / "agnostic_neutral_twin.json").write_text(json.dumps(agnostic(
        [cell("head.0.3", "k.1.0", 0.08), cell("mlp.0.0", "q.1.2", 0.03)])))
    (sub / "segments_neutral_twin.json").write_text(json.dumps(segments(
        [split("head.0.3->k.1.0", "pressure_clause")])))
    return str(tmp_path)


def test_the_writer_puts_the_columns_in_the_head_table_with_their_coverage(cell_dir):
    written = rc.write(cell_dir)

    rows = {(r["kind"], r["layer"], r["index"]): r for r in load_head_table(cell_dir)}
    assert rows[("head", 1, 0)]["path_patching.receiver_category_neutral_twin"] == "kv_clause"
    assert rows[("head", 1, 1)]["path_patching.receiver_category_neutral_twin"] == "kv_clause"
    assert rows[("head", 1, 2)]["path_patching.receiver_category_neutral_twin"] == "q"
    assert rows[("head", 1, 3)]["path_patching.receiver_category_neutral_twin"] == "none"
    assert rows[("mlp", 0, 0)]["path_patching.receiver_category_neutral_twin"] is None
    meta = load_head_table_meta(cell_dir)
    entry = coverage_of(meta, "path_patching.receiver_category_neutral_twin")
    assert entry["n"] == 3
    assert entry["instance_set"].startswith(CAUSAL_SAMPLE_NEUTRAL_TWIN)

    payload = json.load(open(written["json"]))
    assert payload["floor"] == rc.FLOOR
    assert payload["counts"] == {"q": 1, "kv_clause": 2, "kv_post_clause": 0,
                                 "kv_unresolved": 0, "none": 1}
    assert payload["heads"][0]["key"] == ["head", 1, 0]


def test_the_writer_refuses_a_cell_without_the_twin_pass(tmp_path):
    write_head_table(str(tmp_path), [{"kind": "head", "layer": 1, "index": 0,
                                      "kv_group": 0, "head_gate_active": True,
                                      "active_neuron_count": 0}], meta={})
    with pytest.raises(FileNotFoundError, match="agnostic_neutral_twin.json"):
        rc.write(str(tmp_path))


def test_the_writer_runs_without_a_segment_file_and_says_so(cell_dir):
    os.remove(os.path.join(cell_dir, "path_patching", "segments_neutral_twin.json"))
    written = rc.write(cell_dir)
    rows = {(r["kind"], r["layer"], r["index"]): r for r in load_head_table(cell_dir)}
    assert rows[("head", 1, 0)]["path_patching.receiver_category_neutral_twin"] == "kv_unresolved"
    assert json.load(open(written["json"]))["segments_file"] is None


def test_the_subcommand_is_wired(cell_dir, capsys):
    import analyze_components

    assert analyze_components.main(["receiver-category", cell_dir]) == 0
    printed = capsys.readouterr().out
    assert "kv_clause" in printed
    rows = load_head_table(cell_dir)
    assert any(r.get("path_patching.receiver_category_neutral_twin") == "q" for r in rows)


# ==============================================================================
# THE REVIEW FIXES (02b)
# ==============================================================================

def test_a_skipped_twin_pass_is_refused_not_read_as_none(tmp_path):
    """A v2 H or F cell's twin pass writes a skipped file; its heads have no
    category, and the roles pass must see the columns absent, never `none`."""
    write_head_table(str(tmp_path), [{"kind": "head", "layer": 1, "index": 0,
                                      "kv_group": 0, "head_gate_active": True,
                                      "active_neuron_count": 0}], meta={"task": {"task": "sdr_v2"}})
    sub = tmp_path / "path_patching"
    sub.mkdir()
    (sub / "agnostic_neutral_twin.json").write_text(json.dumps(
        {"analysis": "path_patching", "pass": "position_agnostic", "counterfactual": "neutral_twin",
         "skipped": "no instance of the causal sample has a neutral_twin counterpart", "cells": []}))

    with pytest.raises(rc.TwinPassSkipped, match="skipped"):
        rc.categorize_cell(str(sub), [("head", 1, 0)])
    with pytest.raises(rc.TwinPassSkipped):
        rc.write(str(tmp_path))
    with pytest.raises(SystemExit, match="skipped"):
        rc.main([str(tmp_path)])
    assert not os.path.exists(sub / rc.JSON_NAME)
    assert rc.COLUMN not in load_head_table(str(tmp_path))[0]
    assert f"path_patching.{rc.COLUMN}" not in load_head_table(str(tmp_path))[0]


def test_the_floor_flag_has_the_analysis_prefix_and_is_the_job_s_name():
    cli = rc.build_parser().parse_args(["cell", "--path-category-floor", "0.02"])
    assert cli.path_category_floor == 0.02
    with pytest.raises(SystemExit):
        rc.build_parser().parse_args(["cell", "--floor", "0.02"])


def test_a_tie_between_two_senders_goes_to_the_grid_s_order_like_strongest_incoming():
    """`path_patching.strongest_incoming` is a stable sort of the incoming cells in grid order
    (receiver q, then k, then v; senders in run order), so the category breaks ties the same way:
    file order, not the sender's name (which would put `head.10.0` before `head.9.1`)."""
    cells = [cell("head.9.1", "k.1.0", 0.2), cell("head.10.0", "k.1.0", 0.2)]
    splits = {s["cell"]: s for s in [split("head.9.1->k.1.0", "pressure_clause"),
                                     split("head.10.0->k.1.0", "pressure_clause")]}
    one = rc.categorize_head(("head", 1, 0), cells, splits)
    assert one["path"] == "head.9.1->k.1.0"
    assert one["tied"] == ["head.9.1->k.1.0", "head.10.0->k.1.0"]
    reordered = rc.categorize_head(("head", 1, 0), cells[::-1], splits)
    assert reordered["path"] == "head.10.0->k.1.0"
