"""
CLI-seam test for the paired Honest-Instruction Counterfactual (ticket 06).

The same shape as `tests/test_analyze_components_segmentation.py` — a throwaway
run directory for the 2-layer random Llama, a real SDR split built by the
repo's own generator, and the real CLI over it — with the one thing no other
CLI fixture has: a **Matched Honest pool and a survivors file**, so the paired
condition actually runs rather than reporting itself skipped. Two thirds of the
split survive the filter, which is what makes "the paired condition reads fewer
instances than the pressure condition" an assertion rather than a coincidence.

nnsight 0.7.0 only, gated the way `tests/test_dla_model.py` gates it: the
login-node base environment carries an nnsight 0.5.12 for the parent Alignment
repo, so `importorskip("nnsight")` does not skip there. The rules that need no
model are in `tests/test_paired_honest.py` and run in both environments.
"""

from __future__ import annotations

import os

import pytest
import torch

PINNED = "0.7.0"
nnsight = pytest.importorskip("nnsight")
if nnsight.__version__ != PINNED:
    pytest.skip(f"nnsight {nnsight.__version__} is installed, not the pinned "
                f"{PINNED}", allow_module_level=True)

import json                                                # noqa: E402

import analyze_components                                  # noqa: E402
from component_analysis import attention_patterns as ap    # noqa: E402
from component_analysis import dla                         # noqa: E402
from dataset import deception_common as dc                 # noqa: E402
from dataset import matched_honest as mh                   # noqa: E402
from tests.fakes import FAKE_VOCAB_SIZE                    # noqa: E402
from tests.helpers import TINY                             # noqa: E402
from tests.test_analyze_components_segmentation import (   # noqa: E402,F401
    CELL, build_sdr_split, read_json, run_cli, sdr_run)

ATTENTION_DIR = ap.SUBDIR
DLA_DIR = dla.SUBDIR


# ==============================================================================
# A CLI FIXTURE THAT HAS A PAIR
# ==============================================================================

def cli_model():
    """The tiny Llama, widened to the fake tokenizer's vocabulary."""
    from nnsight import NNsight
    from transformers import LlamaConfig, LlamaForCausalLM

    torch.manual_seed(0)
    config = LlamaConfig(
        hidden_size=TINY["hidden"], num_hidden_layers=TINY["layers"],
        num_attention_heads=TINY["heads"], num_key_value_heads=TINY["kv_heads"],
        intermediate_size=TINY["intermediate"], vocab_size=FAKE_VOCAB_SIZE,
        max_position_embeddings=TINY["max_pos"], attn_implementation="sdpa")
    return NNsight(LlamaForCausalLM(config).eval())


def write_pool_and_survivors(dataset_dir, pools_dir, records, tokenizer,
                             monkeypatch):
    """A Matched Honest pool for the fixture's split, and two thirds surviving.

    The real candidate ladder is length-matched in the Llama tokenizer, so the
    pool is rebuilt here against the whitespace one exactly as
    `tests/test_dataloaders.py` does: `build_pool` keeps whichever candidate
    has the clause's token count in the tokenizer it is handed.
    """
    pool, unmatched = mh.build_pool(
        tokenizer, dc.load_pressures("sdr")[:3], mh.load_candidates(),
        lambda pressure: [r["clean_prompt"] for r in records
                          if r["pressure"] == pressure["text"]][:1])
    assert not unmatched, unmatched
    mh.write_matched_honest_pool("sdr", pool, pools_dir=str(pools_dir),
                                 meta={"model": "fake"})
    monkeypatch.setattr(mh, "POOLS_DIR", str(pools_dir))

    survivors = records[:2 * len(records) // 3]
    ids = [one["instance_id"] for one in survivors]
    mh.write_survivors(str(dataset_dir), "sdr", survivors,
                       {"overall": {"n_survivors": len(survivors)},
                        "honest_streams": "clean",
                        "survivor_ids": {"clean": ids, "both": ids[:1]}})
    return ids


@pytest.fixture
def paired_run(sdr_run, monkeypatch, tmp_path):
    """(run dir, output dir, records, surviving instance ids).

    Beside the pressure split: a Matched Honest pool, a survivors file, and an
    Honest Twin dataset whose Target and Distractor are swapped and whose
    records say `condition == "honest"`, which is what `harvest_honest_twins`
    produces and what the DLA twin column refuses to run without.
    """
    from datasets import Dataset, DatasetDict

    from component_analysis import instances as ca_instances

    run_dir, out, records = sdr_run
    data_dir = json.loads((run_dir / "config.json").read_text())["data_dir"]
    tokenizer = ca_instances.load_analysis_tokenizer("llama-tiny")

    ids = write_pool_and_survivors(os.path.join(data_dir, "sdr"),
                                   tmp_path / "pools", records, tokenizer,
                                   monkeypatch)

    twin = [dict(one, target=one["distractor"], distractor=one["target"],
                 condition="honest") for one in records]
    twin_dir = os.path.join(data_dir, "sdr_honest")
    DatasetDict({"test": Dataset.from_list(twin)}).save_to_disk(twin_dir)
    with open(os.path.join(twin_dir, "dataset_config.json"), "w") as handle:
        json.dump({"task": "sdr", "max_seq_length": 128, "margin_thresh": 1.0},
                  handle)

    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: cli_model())
    return run_dir, out, records, ids


def analyse(run_dir, out, *extra):
    return run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out),
                   "--analyses", f"{ap.NAME},{dla.NAME}", *extra)


def patterns_of(out):
    return read_json(out, *CELL, ATTENTION_DIR, ap.PATTERNS_FILE)


def head_table(out):
    from component_analysis import head_table as ht

    return ht.load_head_table(os.path.join(str(out), *CELL))


def conditions_of(payload):
    return {one["name"]: one for one in payload["conditions"]}


# ==============================================================================
# THE PAIRED ATTENTION SIDE
# ==============================================================================

def test_the_paired_condition_runs_and_says_how_many_instances_it_paired(
        paired_run):
    run_dir, out, records, ids = paired_run

    assert analyse(run_dir, out) == 0

    conditions = conditions_of(patterns_of(out))
    assert ap.HONEST_INSTRUCTION in conditions
    assert conditions[ap.HONEST_INSTRUCTION]["n_instances"] == len(ids)
    assert conditions[ap.PRESSURE]["n_instances"] == len(records)


def test_both_sides_of_the_pair_are_profiled_over_the_same_instances(paired_run):
    """The property the word "paired" names, asserted at the file a reader gets."""
    run_dir, out, _records, ids = paired_run
    analyse(run_dir, out)

    conditions = conditions_of(patterns_of(out))

    assert conditions[ap.PRESSURE_PAIRED]["n_instances"] == len(ids)
    assert conditions[ap.PRESSURE_PAIRED]["paired"] is True
    assert conditions[ap.HONEST_INSTRUCTION]["paired"] is True
    for level in conditions[ap.PRESSURE_PAIRED]["levels"]:
        other = {one["level"]: one for one in
                 conditions[ap.HONEST_INSTRUCTION]["levels"]}[level["level"]]
        assert level["n"] == other["n"]


def test_the_head_table_carries_the_paired_attention_columns(paired_run):
    run_dir, out, _records, _ids = paired_run
    analyse(run_dir, out)

    rows = head_table(out)
    heads = [row for row in rows if row["kind"] == "head"]
    assert heads

    for row in heads:
        assert row[f"{ap.NAME}.honest_instruction_top_segment"]
        assert row[f"{ap.NAME}.pressure_paired_top_segment"]
        assert 0.0 <= float(row[f"{ap.NAME}.honest_instruction_top_mass"]) <= 1.0


def test_the_paired_columns_are_distinguishable_from_the_descriptive_twin(
        paired_run):
    """A CSV reader sees `_descriptive` on the unpaired column and nothing on
    the paired one, which is block C's rule and spec user story 27's demand."""
    run_dir, out, _records, _ids = paired_run
    analyse(run_dir, out)

    names = set(head_table(out)[0])

    assert f"{ap.NAME}.honest_twin_descriptive_top_segment" in names
    assert f"{ap.NAME}.honest_instruction_top_segment" in names
    assert f"{ap.NAME}.honest_instruction_descriptive_top_segment" not in names


def test_the_paired_condition_can_be_turned_off_by_name(paired_run):
    run_dir, out, _records, _ids = paired_run

    assert analyse(run_dir, out, "--attention-conditions",
                   "pressure,honest_twin") == 0

    payload = patterns_of(out)
    assert ap.HONEST_INSTRUCTION not in conditions_of(payload)
    assert ap.PRESSURE_PAIRED not in conditions_of(payload)
    skipped = {one["condition"]: one["reason"] for one in payload["skipped"]}
    assert "--attention-conditions" in skipped[ap.HONEST_INSTRUCTION]


def test_an_unknown_attention_condition_is_refused_by_name_in_a_dry_run(
        paired_run):
    """`--dry-run` is where a bad configuration is meant to die, on the login
    node. A real run validates the flag inside `run()`, after the model is
    loaded, exactly as `--dla-conditions` does; the dry run is the cheap gate
    and is what the sbatch header tells the researcher to rehearse with."""
    run_dir, out, _records, _ids = paired_run

    with pytest.raises(ValueError) as failure:
        analyse(run_dir, out, "--dry-run", "--attention-conditions", "honest")

    assert "honest" in str(failure.value)


# ==============================================================================
# THE TWO PAIRED FIGURES, UNDER THE DLA SUBDIRECTORY
# ==============================================================================

def test_the_paired_dla_scatter_is_written_with_its_json_twin(paired_run):
    run_dir, out, _records, ids = paired_run
    analyse(run_dir, out)

    directory = os.path.join(str(out), *CELL, DLA_DIR)
    assert os.path.getsize(os.path.join(directory,
                                        dla.PAIRED_SCATTER_PNG_NAME)) > 0

    twin = read_json(out, *CELL, DLA_DIR, dla.PAIRED_SCATTER_JSON_NAME)
    assert twin["figure"] == dla.PAIRED_SCATTER_PNG_NAME
    assert twin["x"] == dla.PRESSURE_PAIRED and twin["y"] == dla.HONEST_INSTRUCTION
    assert twin["n_instances"] == len(ids)
    assert "deceptive answer" in twin["metric"]
    labels = [one["label"] for one in twin["points"]]
    assert labels and all(one["x"] is not None for one in twin["points"])


def test_the_scatter_labels_every_component_of_the_circuit(paired_run):
    run_dir, out, _records, _ids = paired_run
    analyse(run_dir, out)

    twin = read_json(out, *CELL, DLA_DIR, dla.PAIRED_SCATTER_JSON_NAME)
    rows = head_table(out)

    assert sorted(one["label"] for one in twin["points"]) == sorted(
        dla.label_of((row["kind"], row["layer"], row["index"])) for row in rows)


def test_the_paired_lens_overlays_only_the_two_paired_conditions(paired_run):
    run_dir, out, _records, _ids = paired_run
    analyse(run_dir, out)

    directory = os.path.join(str(out), *CELL, DLA_DIR)
    assert os.path.getsize(os.path.join(directory,
                                        dla.PAIRED_LENS_PNG_NAME)) > 0

    twin = read_json(out, *CELL, DLA_DIR, dla.PAIRED_LENS_JSON_NAME)
    assert twin["figure"] == dla.PAIRED_LENS_PNG_NAME
    assert set(twin["conditions"]) == {dla.PRESSURE_PAIRED,
                                       dla.HONEST_INSTRUCTION}
    assert dla.PRESSURE not in twin["conditions"]
    assert dla.HONEST_TWIN not in twin["conditions"]


def test_the_paired_lens_rows_are_rows_and_say_so(paired_run):
    run_dir, out, _records, _ids = paired_run
    analyse(run_dir, out)

    twin = read_json(out, *CELL, DLA_DIR, dla.PAIRED_LENS_JSON_NAME)

    assert "row" in twin["rows"]
    for condition in twin["conditions"].values():
        assert len(condition["mean"]) == TINY["layers"] + 1


def test_both_figures_say_why_they_are_empty_when_nothing_is_paired(
        sdr_run, monkeypatch, tmp_path):
    """No survivors file, so no paired condition — and a PNG must still exist.

    A JSON sitting beside no PNG reads as a crashed run; a figure that says
    why it is empty reads as the finding it is.
    """
    run_dir, out, _records = sdr_run
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: cli_model())

    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out),
                   "--analyses", dla.NAME) == 0

    directory = os.path.join(str(out), *CELL, DLA_DIR)
    for name in (dla.PAIRED_SCATTER_PNG_NAME, dla.PAIRED_LENS_PNG_NAME):
        assert os.path.getsize(os.path.join(directory, name)) > 0
    twin = read_json(out, *CELL, DLA_DIR, dla.PAIRED_SCATTER_JSON_NAME)
    assert twin["points"] == [] and twin["skipped"]


# ==============================================================================
# THE DIFFERENTIAL, END TO END
# ==============================================================================

def test_the_differential_column_is_the_paired_difference_of_the_two_columns(
        paired_run):
    """The head table's own arithmetic, checked where the researcher reads it."""
    run_dir, out, _records, _ids = paired_run
    analyse(run_dir, out)

    for row in head_table(out):
        left = row[f"{dla.NAME}.pressure_paired"]
        right = row[f"{dla.NAME}.honest_instruction"]
        if left in (None, "") or right in (None, ""):
            continue
        assert float(row[f"{dla.NAME}.differential"]) == pytest.approx(
            float(left) - float(right), abs=1e-4)


def test_the_dry_run_names_the_paired_condition_without_touching_a_gpu(
        paired_run, capsys):
    run_dir, out, _records, ids = paired_run

    assert analyse(run_dir, out, "--dry-run") == 0

    printed = capsys.readouterr().out
    assert f"{len(ids)} paired instance(s)" in printed
    assert "honest-instruction (paired)" in printed
    assert not os.path.isdir(os.path.join(str(out), *CELL, DLA_DIR))
    assert not os.path.isdir(os.path.join(str(out), *CELL, ATTENTION_DIR))
