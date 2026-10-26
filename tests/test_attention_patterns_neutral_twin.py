"""
Attention patterns under the Neutral-Clause Twin (ticket 02b, spec R1, R16, B2).

A v2 cell profiles two more conditions, paired by instance id over the whole
test split: `pressure_neutral_twin_paired` (the pressure prompts of the rows
that have a twin, the left term) and `neutral_twin` (their twins, read with
the pressure prompt's Segments, which the twin shares outside the clause by
construction). From the same forwards comes the **B2 signature** per head:
the Readout-query mass on `pressure_clause` under pressure minus under the
twin, per instance, with its paired standard error.

v1 cells see none of it (the snapshot test holds them byte for byte). The pure
tests run everywhere; the CLI tests need nnsight 0.7.0, the Llama tokenizer
and the v2 datasets, and skip where any is missing.
"""

from __future__ import annotations

import argparse
import json
import os

import pytest
import torch

from component_analysis import attention_patterns as ap
from component_analysis import head_table as ht


# ==============================================================================
# NAMES AND SELECTION
# ==============================================================================

def test_the_twin_conditions_are_named_and_the_v1_three_did_not_move():
    assert ap.NEUTRAL_TWIN == "neutral_twin"
    assert ap.PRESSURE_NEUTRAL_TWIN_PAIRED == "pressure_neutral_twin_paired"
    assert ap.CONDITIONS == (ap.PRESSURE, ap.HONEST_INSTRUCTION, ap.HONEST_TWIN)
    assert ap.parse_conditions("pressure,neutral_twin") == [ap.PRESSURE, ap.NEUTRAL_TWIN]
    with pytest.raises(ap.UnknownCondition):
        ap.parse_conditions("neutral_twins")


def ctx_for(task, conditions=None):
    return argparse.Namespace(cli=argparse.Namespace(attention_conditions=conditions),
                              task_spec=type("T", (), {"name": task})())


def test_a_v2_cell_profiles_the_twin_by_default_and_a_v1_cell_does_not():
    assert ap.wanted_conditions_for(ctx_for("sdr")) == list(ap.CONDITIONS)
    assert ap.wanted_conditions_for(ctx_for("sdr_v2")) == \
        list(ap.CONDITIONS) + [ap.NEUTRAL_TWIN]
    assert ap.wanted_conditions_for(ctx_for("sdr_v2", [ap.PRESSURE])) == [ap.PRESSURE]
    assert ap.wanted_conditions_for(ctx_for("sdr", [ap.PRESSURE, ap.NEUTRAL_TWIN])) == \
        [ap.PRESSURE, ap.NEUTRAL_TWIN]


def test_the_flag_default_is_still_the_v1_three():
    parser = argparse.ArgumentParser()
    ap.add_arguments(parser.add_argument_group("attention"))
    cli = parser.parse_args([])
    assert ap.wanted_conditions(cli) == list(ap.CONDITIONS)
    assert ap.wanted_conditions_for(argparse.Namespace(
        cli=cli, task_spec=type("T", (), {"name": "sdr_v2"})())) == \
        list(ap.CONDITIONS) + [ap.NEUTRAL_TWIN]


# ==============================================================================
# COLUMNS
# ==============================================================================

def payload_with(conditions):
    return {"column_query_position": "readout",
            "components": [{"key": ["head", 1, 0], "name": "head.1.0"}],
            "conditions": conditions}


V1_COLUMNS = {"query_position", "pressure_top_segment", "pressure_top_mass",
              "pressure_paired_top_segment", "pressure_paired_top_mass",
              "honest_instruction_paired_top_segment", "honest_instruction_paired_top_mass",
              "honest_twin_descriptive_top_segment", "honest_twin_descriptive_top_mass"}


def test_without_the_twin_the_column_set_is_v1s():
    columns = ap.columns(payload_with([]), wanted=list(ap.CONDITIONS))
    assert set(columns[("head", 1, 0)]) == V1_COLUMNS
    assert set(ap.columns(payload_with([]))[("head", 1, 0)]) == V1_COLUMNS


def test_with_the_twin_wanted_the_paired_and_b2_columns_appear_even_when_it_did_not_run():
    columns = ap.columns(payload_with([]), wanted=list(ap.CONDITIONS) + [ap.NEUTRAL_TWIN])
    cells = columns[("head", 1, 0)]
    assert set(cells) == V1_COLUMNS | {
        "pressure_neutral_twin_paired_top_segment", "pressure_neutral_twin_paired_top_mass",
        "neutral_twin_paired_top_segment", "neutral_twin_paired_top_mass",
        "clause_mass_drop_neutral_twin_paired", "clause_mass_drop_neutral_twin_paired_se"}
    assert cells["clause_mass_drop_neutral_twin_paired"] is None


def test_the_b2_columns_read_the_twin_conditions_signature_block():
    twin = {"name": ap.NEUTRAL_TWIN, "levels": [{"level": ap.ALL_LEVEL, "masses": {
                "head.1.0": {"readout": {"pressure_clause": 0.1, "question": 0.9}}}}],
            "b2": {"query_position": "readout", "segment": "pressure_clause",
                   "per_head": {"head.1.0": {"drop": 0.25, "se": 0.05, "n": 3,
                                             "pressure_mean": 0.35, "twin_mean": 0.1}}}}
    cells = ap.columns(payload_with([twin]), wanted=[ap.NEUTRAL_TWIN])[("head", 1, 0)]
    assert cells["neutral_twin_paired_top_segment"] == "question"
    assert cells["clause_mass_drop_neutral_twin_paired"] == 0.25
    assert cells["clause_mass_drop_neutral_twin_paired_se"] == 0.05


def test_the_paired_drop_is_the_mean_and_standard_error_of_per_instance_differences():
    """Three instances, two heads, by hand: drops 0.1, 0.3, 0.2 for head 0
    (mean 0.2, sample sd 0.1, se 0.1/sqrt(3)); head 1 is flat (drop 0, se 0).
    An instance on one side only is left out and named."""
    pressure = {"a": torch.tensor([0.5, 0.4]), "b": torch.tensor([0.6, 0.4]),
                "c": torch.tensor([0.7, 0.4]), "only_pressure": torch.tensor([1.0, 1.0])}
    twin = {"a": torch.tensor([0.4, 0.4]), "b": torch.tensor([0.3, 0.4]),
            "c": torch.tensor([0.5, 0.4])}
    drop = ap.paired_clause_drop(pressure, twin, ["head.1.0", "head.1.1"])
    assert drop["n"] == 3
    assert drop["unpaired"] == ["only_pressure"]
    head0 = drop["per_head"]["head.1.0"]
    assert head0["drop"] == pytest.approx(0.2)
    assert head0["se"] == pytest.approx(0.1 / 3 ** 0.5)
    assert head0["pressure_mean"] == pytest.approx(0.6)
    assert head0["twin_mean"] == pytest.approx(0.4)
    head1 = drop["per_head"]["head.1.1"]
    assert head1["drop"] == pytest.approx(0.0) and head1["se"] == pytest.approx(0.0)


def test_a_single_pair_has_no_standard_error():
    drop = ap.paired_clause_drop({"a": torch.tensor([0.5])}, {"a": torch.tensor([0.2])},
                                 ["head.0.0"])
    assert drop["per_head"]["head.0.0"]["drop"] == pytest.approx(0.3)
    assert drop["per_head"]["head.0.0"]["se"] is None


# ==============================================================================
# THE CLI ON A REAL V2 CELL, TINY MODEL
# ==============================================================================

nnsight = pytest.importorskip("nnsight")
if nnsight.__version__ != "0.7.0":
    pytest.skip("attention weights are a nnsight 0.7.0 behaviour", allow_module_level=True)

import analyze_components                                          # noqa: E402
from component_analysis import registry                            # noqa: E402
from tests.helpers import tiny_config                              # noqa: E402
from tests.test_component_analysis_v2_cli import (                 # noqa: E402, F401
    cell, read, real_tokenizer, run_cli, v2_run)

WHOLE_SPLIT = 1000
#: The fixture run is built with `test_samples` = 40, so the cell's
#: segmentation covers 40 of the split's 1,000 rows and the paired conditions
#: profile those 40 (a real cell segments the whole split).
SEGMENTED = 40


@pytest.fixture
def tiny_llama(monkeypatch, real_tokenizer):
    from nnsight import NNsight
    from transformers import LlamaForCausalLM

    config = tiny_config(attn_implementation="sdpa")
    config.vocab_size = len(real_tokenizer)
    torch.manual_seed(0)
    wrapped = NNsight(LlamaForCausalLM(config).eval())
    monkeypatch.setattr(analyze_components, "load_model", lambda cli, resolved: wrapped)
    monkeypatch.setattr(registry, "ANALYSES", [ap])
    return wrapped


def common(run_dir, out, *extra):
    return [str(run_dir), "--num-kv-heads", "2", "--device", "cpu", "--n-causal",
            "8", "--output-dir", str(out), *extra]


def by_name(payload):
    return {one["name"]: one for one in payload["conditions"]}


def test_a_v2_cell_profiles_both_twin_conditions_over_the_same_thousand_rows(
        v2_run, tiny_llama):
    run_dir, out = v2_run()
    assert run_cli(*common(run_dir, out, "--attention-conditions",
                           "pressure,neutral_twin")) == 0

    payload = read(os.path.join(cell(out), ap.SUBDIR), ap.PATTERNS_FILE)
    conditions = by_name(payload)
    assert set(conditions) == {ap.PRESSURE, ap.PRESSURE_NEUTRAL_TWIN_PAIRED, ap.NEUTRAL_TWIN}
    left, right = conditions[ap.PRESSURE_NEUTRAL_TWIN_PAIRED], conditions[ap.NEUTRAL_TWIN]
    assert left["paired"] and right["paired"]
    assert left["n_loaded"] == right["n_loaded"] == WHOLE_SPLIT
    assert left["n_instances"] == right["n_instances"] == SEGMENTED
    assert left["instance_ids"] == right["instance_ids"]
    assert len(left["instance_ids"]) == SEGMENTED
    assert any("960 instance(s) with a twin have no resolved segmentation" in note
               for note in left["notes"])
    assert right["alignment"]["n_pairs"] == SEGMENTED
    assert right["alignment"]["n_differing_outside_the_clause"] == 0
    assert right["alignment"]["n_identical_to_pressure"] == 0

    # B2: the paired drop per head is the difference of the two conditions'
    # pooled clause masses at the Readout, because both are means over the
    # same instances.
    b2 = right["b2"]
    assert b2["segment"] == "pressure_clause" and b2["query_position"] == "readout"
    assert b2["n"] == SEGMENTED and b2["unpaired"] == []
    for component in payload["components"]:
        name = component["name"]
        left_mass = left["levels"][0]["masses"][name]["readout"]["pressure_clause"]
        right_mass = right["levels"][0]["masses"][name]["readout"]["pressure_clause"]
        signature = b2["per_head"][name]
        assert signature["drop"] == pytest.approx(left_mass - right_mass, abs=1e-5)
        assert signature["se"] is not None and signature["se"] >= 0.0

    table = read(cell(out), "head_table.json")
    for column in ("attention_patterns.pressure_neutral_twin_paired_top_segment",
                   "attention_patterns.neutral_twin_paired_top_mass",
                   "attention_patterns.clause_mass_drop_neutral_twin_paired",
                   "attention_patterns.clause_mass_drop_neutral_twin_paired_se"):
        assert column in table["columns"]
        entry = ht.coverage_of(table["meta"], column)
        assert entry["n"] == SEGMENTED
        assert entry["instance_set"].startswith(ht.PAIRED_NEUTRAL_TWIN)
    row = next(one for one in table["rows"] if one["kind"] == "head")
    assert isinstance(row["attention_patterns.clause_mass_drop_neutral_twin_paired"], float)
    skipped = {one["condition"] for one in payload["skipped"]}
    assert skipped == {ap.HONEST_INSTRUCTION, ap.HONEST_TWIN}


def test_on_a_nopressure_cell_the_twin_is_skipped_with_the_loaders_reason(
        v2_run, tiny_llama):
    run_dir, out = v2_run(condition="nopressure")
    assert run_cli(*common(run_dir, out, "--attention-conditions",
                           "pressure,neutral_twin")) == 0

    payload = read(os.path.join(cell(out), ap.SUBDIR), ap.PATTERNS_FILE)
    assert set(by_name(payload)) == {ap.PRESSURE}
    reason = next(one for one in payload["skipped"]
                  if one["condition"] == ap.NEUTRAL_TWIN)["reason"]
    assert "nopressure" in reason
    table = read(cell(out), "head_table.json")
    column = "attention_patterns.clause_mass_drop_neutral_twin_paired"
    assert column in table["columns"]
    assert ht.coverage_of(table["meta"], column)["n"] == 0


def test_dry_run_prices_the_twin_pass_on_a_v2_cell(v2_run, tiny_llama, capsys):
    run_dir, out = v2_run()
    assert run_cli(*common(run_dir, out, "--dry-run")) == 0
    line = next(one for one in capsys.readouterr().out.splitlines()
                if one.strip().startswith(f"{ap.NAME}: "))
    assert "neutral_twin" in line
    assert "neutral twin (paired), both sides: 1000 instance(s)" in line
