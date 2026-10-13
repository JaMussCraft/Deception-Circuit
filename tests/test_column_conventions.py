"""
The head table's column conventions (ticket 13), at the library seam.

Three things a reader of `head_table.json` relies on and no analysis owns:

  * **coverage** — per column, how many instances it was computed over and
    which ones, so the 71-versus-100 difference between a paired column and
    its causal-sample neighbour is readable from the table rather than from
    the column name;
  * **the paired names** — every column computed over the same instance ids on
    both sides carries `paired` in its bare name, and a table written before
    the rename is read under the new names rather than refused;
  * nothing here imports nnsight or torch, so the file runs in both
    environments.
"""

from __future__ import annotations

import json
import os

import pytest

from component_analysis import head_table
from component_analysis.head_table import (
    add_coverage, coverage_of, load_head_table, load_head_table_meta,
    modernize_columns, write_head_table)

ROW = {"kind": "head", "layer": 5, "index": 8, "kv_group": 2,
       "head_gate_active": True, "active_neuron_count": 128}
SAMPLE = [f"sdr-{n:04d}" for n in range(100)]
PAIRED = SAMPLE[:71]


def _row(**columns):
    return {**ROW, **columns}


# ==============================================================================
# COVERAGE
# ==============================================================================

def test_a_declared_column_reads_back_its_n_and_its_instances(tmp_path):
    meta = add_coverage({}, ["direct_effect", "direct_effect_se"], SAMPLE,
                        instance_set="causal_sample", namespace="path_patching")
    meta = add_coverage(meta, ["direct_effect_honest_instruction_paired"],
                        PAIRED, instance_set="paired_honest_instruction",
                        namespace="path_patching")
    rows = [_row(**{"path_patching.direct_effect": 0.1,
                    "path_patching.direct_effect_se": 0.01,
                    "path_patching.direct_effect_honest_instruction_paired": 0.2})]

    write_head_table(str(tmp_path), rows, meta=meta)
    written = load_head_table_meta(str(tmp_path))

    whole = coverage_of(written, "path_patching.direct_effect")
    paired = coverage_of(
        written, "path_patching.direct_effect_honest_instruction_paired")
    assert whole["n"] == 100 and whole["instance_ids"] == SAMPLE
    assert paired["n"] == 71 and paired["instance_ids"] == PAIRED
    assert whole["instance_set"] != paired["instance_set"]
    assert whole["instance_set"].startswith("causal_sample")
    assert paired["instance_set"].startswith("paired_honest_instruction")


def test_columns_over_the_same_instances_share_one_instance_set(tmp_path):
    """The id list is written once per set, not once per column: a descriptive
    analysis over a thousand instances would otherwise repeat them per column."""
    meta = add_coverage({}, ["pressure", "pressure_se"], SAMPLE,
                        instance_set="test_split", namespace="dla")
    meta = add_coverage(meta, ["pressure_top_segment"], list(reversed(SAMPLE)),
                        instance_set="test_split", namespace="attention_patterns")
    rows = [_row(**{"dla.pressure": 0.1, "dla.pressure_se": 0.01,
                    "attention_patterns.pressure_top_segment": "question"})]

    write_head_table(str(tmp_path), rows, meta=meta)
    with open(os.path.join(str(tmp_path), head_table.JSON_NAME)) as handle:
        raw = json.load(handle)["meta"]

    ids = {raw["coverage"][column]["instance_set"] for column in
           ("dla.pressure", "dla.pressure_se",
            "attention_patterns.pressure_top_segment")}
    assert len(ids) == 1, "the same instances are the same set, in any order"
    assert len(raw["instance_sets"]) == 1


def test_a_column_declared_over_nothing_says_so_rather_than_going_missing(tmp_path):
    meta = add_coverage({}, ["honest_instruction_paired"], [],
                        instance_set="paired_honest_instruction", namespace="dla")
    write_head_table(str(tmp_path), [_row(**{"dla.honest_instruction_paired": None})],
                     meta=meta)

    entry = coverage_of(load_head_table_meta(str(tmp_path)),
                        "dla.honest_instruction_paired")
    assert entry["n"] == 0
    assert entry["instance_set"] is None and entry["instance_ids"] == []


def test_coverage_of_a_column_the_table_no_longer_holds_is_not_written(tmp_path):
    meta = add_coverage({}, ["gone"], SAMPLE, instance_set="causal_sample",
                        namespace="knockout")
    write_head_table(str(tmp_path), [_row()], meta=meta)

    written = load_head_table_meta(str(tmp_path))
    assert coverage_of(written, "knockout.gone") is None
    assert written.get("instance_sets", {}) == {}, \
        "an instance set nothing refers to is dropped with its column"


def test_a_table_written_before_coverage_existed_still_loads(tmp_path):
    """The cells of record have no coverage block; reading them must not fail."""
    write_head_table(str(tmp_path), [_row(**{"dla.pressure": 0.1})],
                     meta={"circuit": {"label": "delta"}})

    assert load_head_table(str(tmp_path))[0]["dla.pressure"] == 0.1
    meta = load_head_table_meta(str(tmp_path))
    assert meta["circuit"] == {"label": "delta"}
    assert coverage_of(meta, "dla.pressure") is None


# ==============================================================================
# THE PAIRED NAMES, AND A TABLE WRITTEN BEFORE THEM
# ==============================================================================

def test_a_legacy_paired_column_is_read_under_its_new_name():
    rows = [_row(**{"dla.honest_instruction": -0.5, "dla.differential": 0.3,
                    "dla.differential_se": 0.08, "dla.pressure": 0.2,
                    "path_patching.direct_effect_honest_instruction": -0.07})]

    modern, renamed = modernize_columns(rows)

    assert modern[0]["dla.honest_instruction_paired"] == -0.5
    assert modern[0]["dla.differential_paired"] == 0.3
    assert modern[0]["dla.differential_paired_se"] == 0.08
    assert modern[0][
        "path_patching.direct_effect_honest_instruction_paired"] == -0.07
    assert "dla.differential" not in modern[0]
    assert modern[0]["dla.pressure"] == 0.2, "an unpaired column keeps its name"
    assert renamed["dla.differential"] == "dla.differential_paired"
    assert rows[0]["dla.differential"] == 0.3, "the input is not mutated"


def test_a_table_holding_both_spellings_with_different_values_is_refused():
    rows = [_row(**{"dla.differential": 0.3, "dla.differential_paired": 0.4})]

    with pytest.raises(ValueError, match="dla.differential"):
        modernize_columns(rows)


def test_every_legacy_name_maps_to_a_name_that_says_paired():
    for old, new in head_table.LEGACY_COLUMNS.items():
        if old.startswith("knockout.family"):
            continue                 # ticket 10's rename, not a paired column
        assert "paired" in new.split(".", 1)[1], (old, new)
        assert "paired" not in old.split(".", 1)[1], (old, new)
