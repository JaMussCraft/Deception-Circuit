"""
CLI-seam test for the segmentation and the causal sample.

The same shape as `tests/test_analyze_components_end_to_end.py` — a throwaway
run directory for the 2-layer random Llama and the real CLI over it — but with
a real SDR dataset behind it, built by the repo's own `generate_task_data` from
the real pools and tokenized with `tests.fakes.FakeWordTokenizer`. So the
prompts are real SDR prompts, the Segments are found the way they are found on
the cluster, and the assertions are on the two files the researcher gets.
"""

from __future__ import annotations

import json
import os

import pytest

import analyze_components
from component_analysis import instances as ca_instances
from dataset.deception_common import (SPECS, generate_task_data, load_entities,
                                      load_item_pairs, load_pressures)
from tests.fakes import FakeWordTokenizer
from tests.test_analyze_components_end_to_end import write_run, written_files
from tests.test_component_analysis import make_masks

CELL = ("self", "sdr")
N_RECORDS = 48


# ==============================================================================
# FIXTURE
# ==============================================================================

def build_sdr_split(path, tokenizer, n=N_RECORDS):
    """A real SDR test split on disk, whitespace-tokenized.

    The pools are sliced because `FakeWordTokenizer` has a 256-word vocabulary
    and the real ones spend it on entity names and pressure clauses. The
    prompts are real SDR prompts either way — same scaffold, same designating
    sentence, same Designation Suffix — and the sliced pools still give every
    level of all three metadata factors.
    """
    from datasets import Dataset, DatasetDict

    records = generate_task_data(
        tokenizer, SPECS["sdr"], n, load_entities()[:4], load_item_pairs()[:6],
        load_pressures("sdr")[:3], seed=0)
    DatasetDict({"test": Dataset.from_list(records)}).save_to_disk(str(path))
    # Every built dataset carries one, and the loaders read the token budget
    # from it rather than guessing, so the fixture writes one too.
    with open(os.path.join(str(path), "dataset_config.json"), "w") as handle:
        json.dump({"task": "sdr", "max_seq_length": 128, "margin_thresh": 1.0},
                  handle)
    return records


@pytest.fixture
def sdr_run(tmp_path, monkeypatch):
    """(run dir, output dir, the records on disk)."""
    from models import MODEL_REGISTRY

    monkeypatch.setitem(MODEL_REGISTRY, "llama-tiny", ("llama-tiny", "llama"))
    tokenizer = FakeWordTokenizer()
    data_dir = tmp_path / "datasets"
    records = build_sdr_split(data_dir / "sdr", tokenizer)
    monkeypatch.setattr(ca_instances, "load_analysis_tokenizer",
                        lambda *a, **k: tokenizer)

    run_dir = write_run(tmp_path / "run", make_masks({0: [0, 2]}, {1}, seed=3),
                        task="sdr")
    config = json.loads((run_dir / "config.json").read_text())
    config.update(task="sdr", data_dir=str(data_dir),
                  deception_condition="deceptive", test_samples=N_RECORDS)
    (run_dir / "config.json").write_text(json.dumps(config))
    return run_dir, tmp_path / "analyses", records


def run_cli(*argv):
    return analyze_components.main(list(argv))


def read_json(root, *parts):
    with open(os.path.join(str(root), *parts)) as handle:
        return json.load(handle)


# ==============================================================================
# TESTS
# ==============================================================================

def test_dry_run_writes_the_segmentation_and_the_sample_beside_the_head_table(sdr_run):
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    assert written_files(out) == [
        os.path.join(*CELL, "head_table.csv"),
        os.path.join(*CELL, "head_table.json"),
        os.path.join(*CELL, "sample.json"),
        os.path.join(*CELL, "segmentation.json"),
    ]


def test_the_segmentation_file_covers_every_instance_and_every_segment(sdr_run):
    run_dir, out, records = sdr_run
    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
            "--output-dir", str(out))

    written = read_json(out, *CELL, "segmentation.json")
    assert written["task"] == "sdr" and written["split"] == "test"
    assert written["n_instances"] == len(records)
    assert written["segment_names"] == list(
        analyze_components.segments.MECHANISM_SEGMENTS)
    assert set(written["segment_sources"].values()) == {"default"}

    ids = [one["record_id"] for one in written["instances"]]
    assert ids == [r["instance_id"] for r in records]

    for one in written["instances"]:
        assert one["readout"] == one["n_tokens"] - 1
        covered = sorted(i for spans in one["segments"].values()
                         for start, end in spans
                         for i in range(start, end))
        assert covered == list(range(one["n_tokens"]))
        for name in analyze_components.segments.DESIGNATION_POSITIONS:
            assert len(one["segments"][name]) == 1


def test_a_segment_override_is_merged_into_every_instance(sdr_run):
    run_dir, out, records = sdr_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--segment", r"threat=terminated|contract|wiped",
                   "--output-dir", str(out)) == 0

    written = read_json(out, *CELL, "segmentation.json")
    assert written["overrides"] == {"threat": r"terminated|contract|wiped"}
    assert written["segment_sources"]["threat"] == "override"
    assert written["report"]["override_match_counts"]["threat"] > 0
    assert any(one["segments"]["threat"] for one in written["instances"])


def test_an_override_that_never_matches_fails_the_dry_run(sdr_run):
    run_dir, out, _records = sdr_run

    with pytest.raises(analyze_components.segments.SegmentationError,
                       match="matched nothing"):
        run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                "--segment", "nowhere=zzzz-not-in-any-prompt",
                "--output-dir", str(out))


def test_the_sample_records_ids_and_achieved_counts_per_stratum(sdr_run):
    run_dir, out, records = sdr_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--n-causal", "16", "--seed", "5",
                   "--output-dir", str(out)) == 0

    sample = read_json(out, *CELL, "sample.json")
    assert sample["task"] == "sdr"
    assert sample["n_requested"] == 16 and sample["n_drawn"] == 16
    assert sample["seed"] == 5
    assert sample["factors"] == ["designation_polarity", "item_polarity",
                                 "template_variant"]
    assert sum(stratum["achieved"] for stratum in sample["strata"]) == 16
    known = {r["instance_id"] for r in records}
    assert set(sample["instance_ids"]) <= known
    assert len(set(sample["instance_ids"])) == 16
    for factor in sample["factors"]:
        assert sum(sample["marginals"][factor].values()) == 16


def test_the_same_seed_writes_the_same_sample(sdr_run):
    run_dir, out, _records = sdr_run
    args = ("--dry-run", "--num-kv-heads", "2", "--n-causal", "12",
            "--seed", "9", "--output-dir", str(out))

    run_cli(str(run_dir), *args)
    first = read_json(out, *CELL, "sample.json")["instance_ids"]
    run_cli(str(run_dir), *args)
    assert read_json(out, *CELL, "sample.json")["instance_ids"] == first

    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2", "--n-causal",
            "12", "--seed", "10", "--output-dir", str(out))
    assert read_json(out, *CELL, "sample.json")["instance_ids"] != first


def test_the_n_causal_default_is_a_hundred(sdr_run):
    run_dir, out, records = sdr_run
    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
            "--output-dir", str(out))

    sample = read_json(out, *CELL, "sample.json")
    assert sample["n_requested"] == 100
    assert sample["n_drawn"] == len(records)     # the split is smaller than N
