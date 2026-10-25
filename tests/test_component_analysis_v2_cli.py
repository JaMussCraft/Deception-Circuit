"""
The CLI seam for v2 cells (ticket 02a): a v2 cell is segmented, sampled and
paired, never skipped silently; the held-out sample comes from the id options;
the I condition binds through a config-only stand-in.

A throwaway tiny-model run (as in `test_analyze_components_segmentation.py`)
whose config points at the real v2 datasets, with the real Llama tokenizer.
Skips cleanly where either is missing.
"""

from __future__ import annotations

import json
import os

import pytest

import analyze_components
from component_analysis import instances as ca_instances
from tests.test_analyze_components_end_to_end import write_run
from tests.test_component_analysis import make_masks
from tests.test_component_analysis_v2_dataloaders import DATA, make_fixture, need

N_RECORDS = 40


@pytest.fixture(scope="module")
def real_tokenizer():
    try:
        return ca_instances.load_analysis_tokenizer("llama-8b-instruct")
    except Exception as exc:                                  # noqa: BLE001
        pytest.skip(f"the Llama tokenizer is not available here: {exc}")


@pytest.fixture
def v2_run(tmp_path, monkeypatch, real_tokenizer):
    """A factory: (run dir, output dir) for a task, condition and data dir."""
    from models import MODEL_REGISTRY

    monkeypatch.setitem(MODEL_REGISTRY, "llama-tiny", ("llama-tiny", "llama"))
    monkeypatch.setattr(ca_instances, "load_analysis_tokenizer",
                        lambda *a, **k: real_tokenizer)

    def make(task="sdr_v2", condition="deceptive", data_dir=DATA, name="run"):
        need(task)
        run_dir = write_run(tmp_path / name, make_masks({0: [0, 2]}, {1}, seed=3),
                            task=task)
        config = json.loads((run_dir / "config.json").read_text())
        config.update(task=task, data_dir=str(data_dir),
                      deception_condition=condition, test_samples=N_RECORDS)
        (run_dir / "config.json").write_text(json.dumps(config))
        return run_dir, tmp_path / "analyses"
    return make


def run_cli(*argv):
    return analyze_components.main(list(argv))


def cell(out, task="sdr_v2"):
    return os.path.join(str(out), "self", task)


def read(path, name):
    with open(os.path.join(path, name)) as handle:
        return json.load(handle)


def test_a_v2_cell_is_segmented_sampled_and_paired(v2_run, capsys):
    run_dir, out = v2_run()
    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--analyses", "knockout", "--n-causal", "16",
                   "--output-dir", str(out)) == 0
    printed = capsys.readouterr().out

    segmentation = read(cell(out), "segmentation.json")
    assert segmentation["scheme"] == "mechanism_v2"
    assert "response_line" in segmentation["segment_names"]
    assert segmentation["n_instances"] == N_RECORDS
    assert read(cell(out), "sample.json")["n_drawn"] == 16
    assert "neutral-clause twin on 16 of 16" in printed


def test_a_mechanism_task_that_cannot_be_segmented_is_refused_not_skipped(
        v2_run, monkeypatch):
    run_dir, out = v2_run()
    monkeypatch.setattr(analyze_components.segments, "is_segmentable",
                        lambda task: task != "sdr_v2")
    with pytest.raises(SystemExit, match="sdr_v2"):
        run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                "--analyses", "knockout", "--output-dir", str(out))


def test_the_held_out_sample_excludes_the_selection_cells_sample_file(v2_run, tmp_path):
    run_dir, out = v2_run()
    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2", "--analyses",
            "knockout", "--n-causal", "16", "--output-dir", str(out))
    selection = os.path.join(cell(out), "sample.json")
    held_out_dir = tmp_path / "held_out"

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--analyses", "knockout", "--n-causal", "16", "--seed", "1",
                   "--exclude-ids", selection, "--output-dir", str(held_out_dir)) == 0

    first = read(cell(out), "sample.json")
    second = read(cell(held_out_dir), "sample.json")
    assert second["n_drawn"] == 16 and second["seed"] == 1
    assert not set(first["instance_ids"]) & set(second["instance_ids"])
    assert second["id_exclusion"]["source"] == selection
    assert second["id_exclusion"]["n_ids"] == 16


def test_an_inclusion_file_fixes_the_sample(v2_run, tmp_path):
    run_dir, out = v2_run()
    from datasets import load_from_disk
    ids = [row["instance_id"] for row in load_from_disk(need("sdr_v2"))["test"]][:5]
    ids_file = tmp_path / "ids.txt"
    ids_file.write_text("\n".join(ids))

    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2", "--analyses",
            "knockout", "--include-ids", str(ids_file), "--output-dir", str(out))

    sample = read(cell(out), "sample.json")
    assert sorted(sample["instance_ids"]) == sorted(ids)
    assert sample["id_inclusion"]["source"] == str(ids_file)


def test_the_inversion_condition_binds_through_a_config_only_stand_in(
        v2_run, tmp_path, capsys):
    pressure_dir, _ids = make_fixture(tmp_path, n=6)
    run_dir, out = v2_run(condition="inversion",
                          data_dir=os.path.dirname(pressure_dir))

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--analyses", "knockout", "--n-causal", "4",
                   "--output-dir", str(out)) == 0

    printed = capsys.readouterr().out
    assert "neutral-clause twin on 4 of 4" in printed
    assert str(tmp_path / "datasets" / "sdr_v2_honest") in printed
    assert read(cell(out), "segmentation.json")["n_instances"] == 6


@pytest.mark.parametrize("condition, says", [
    ("honest", "is the Neutral-Clause Twin"), ("nopressure", "no Pressure Clause")])
def test_on_h_and_f_cells_the_dry_run_says_why_there_is_no_twin(
        v2_run, capsys, condition, says):
    run_dir, out = v2_run(condition=condition)
    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--analyses", "knockout", "--n-causal", "8",
                   "--output-dir", str(out)) == 0
    assert says in capsys.readouterr().out
