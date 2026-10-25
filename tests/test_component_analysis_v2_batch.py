"""
`analyze_components.py batch FILE` (ticket 02a): several invocations in one
job, one model load, a timing record per invocation (the phase-1 cost basis).
"""

from __future__ import annotations

import json
import os

import pytest

import analyze_components
from component_analysis import batch
from tests.test_analyze_components_segmentation import sdr_run  # noqa: F401


def write_batch(tmp_path, lines):
    path = tmp_path / "jobs.batch"
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def test_a_batch_file_is_one_invocation_per_line_comments_and_blanks_skipped(tmp_path):
    path = write_batch(tmp_path, ["# the drift control", "", "run_a --dry-run",
                                  "  --circuit 'x=a b' --expr x   # trailing note"])
    assert batch.read_batch(path) == [["run_a", "--dry-run"],
                                      ["--circuit", "x=a b", "--expr", "x"]]


def test_a_batch_may_not_nest_or_name_another_subcommand(tmp_path):
    with pytest.raises(ValueError, match="line 1"):
        batch.read_batch(write_batch(tmp_path, ["batch other.batch"]))


def test_a_dry_run_batch_runs_every_line_and_records_each(sdr_run, tmp_path):  # noqa: F811
    run_dir, out, _records = sdr_run
    timings = tmp_path / "timings.json"
    path = write_batch(tmp_path, [
        f"{run_dir} --dry-run --num-kv-heads 2 --output-dir {out}/one",
        f"{run_dir} --dry-run --num-kv-heads 2 --seed 1 --output-dir {out}/two"])

    assert analyze_components.main(["batch", path, "--timings", str(timings)]) == 0

    assert os.path.exists(os.path.join(str(out), "one", "self", "sdr", "sample.json"))
    assert os.path.exists(os.path.join(str(out), "two", "self", "sdr", "sample.json"))
    record = json.loads(timings.read_text())
    assert [one["status"] for one in record["invocations"]] == ["ok", "ok"]
    assert all(one["seconds"] >= 0 for one in record["invocations"])


def test_a_failing_line_is_recorded_and_the_rest_still_run(sdr_run, tmp_path):  # noqa: F811
    run_dir, out, _records = sdr_run
    timings = tmp_path / "timings.json"
    path = write_batch(tmp_path, [
        f"{run_dir} --dry-run --num-kv-heads 2 --include-ids /no/such/file "
        f"--output-dir {out}/bad",
        f"{run_dir} --dry-run --num-kv-heads 2 --output-dir {out}/good"])

    assert analyze_components.main(["batch", path, "--timings", str(timings)]) == 1

    statuses = [one["status"] for one in json.loads(timings.read_text())["invocations"]]
    assert statuses[0].startswith("error") and statuses[1] == "ok"
    assert os.path.exists(os.path.join(str(out), "good", "self", "sdr", "sample.json"))


def test_the_timings_file_may_name_a_directory_that_does_not_exist_yet(
        sdr_run, tmp_path):  # noqa: F811
    """A GPU job writes its timings under outputs/_analyses/<new suite>/; a
    missing directory must not stop the job after its first line."""
    run_dir, out, _records = sdr_run
    timings = tmp_path / "not" / "yet" / "timings.json"
    path = write_batch(tmp_path, [f"{run_dir} --dry-run --num-kv-heads 2 --output-dir {out}/a"])

    assert analyze_components.main(["batch", path, "--timings", str(timings)]) == 0
    assert json.loads(timings.read_text())["invocations"][0]["status"] == "ok"


def test_batch_dry_run_dry_runs_every_line_of_a_job_file(sdr_run, tmp_path, monkeypatch):  # noqa: F811
    """The login check of a GPU job file is the same file, under --dry-run."""
    run_dir, out, _records = sdr_run
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: pytest.fail("a dry run loaded a model"))
    path = write_batch(tmp_path, [f"{run_dir} --num-kv-heads 2 --output-dir {out}/a"])

    assert analyze_components.main(["batch", path, "--dry-run"]) == 0
    assert os.path.exists(os.path.join(str(out), "a", "self", "sdr", "sample.json"))


def test_the_model_is_loaded_once_for_every_line_of_a_run(sdr_run, tmp_path, monkeypatch):  # noqa: F811
    run_dir, out, _records = sdr_run
    loads, runs = [], []
    sentinel = object()
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: loads.append(cli) or sentinel)
    monkeypatch.setattr(analyze_components, "run",
                        lambda cli, resolved, model=None: runs.append(model) or 0)
    path = write_batch(tmp_path, [f"{run_dir} --num-kv-heads 2 --output-dir {out}/a",
                                  f"{run_dir} --num-kv-heads 2 --output-dir {out}/b"])

    assert analyze_components.main(["batch", path]) == 0

    assert len(loads) == 1
    assert runs == [sentinel, sentinel]
