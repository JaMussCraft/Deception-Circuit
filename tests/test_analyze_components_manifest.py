"""
Every cell `analyze_components.py` runs into carries a `run_manifest.json`.

`run_io.make_run_dir` and `evaluation/suite.py` already stamp their outputs
with `run_manifest.write_run_manifest`; this checks the component-analysis
cells get the same record (B1 plan, ticket 1): the 40-hex `git_commit` on a
real run, nothing on a dry run, and the writer's existing convention when a
cell is re-run with a different command line (`run_manifest.1.json` beside the
first, never an overwrite).

The model loader is monkeypatched away and the stub analysis is registered, as
in `tests/test_analyze_components_registry.py`, so this runs in both
environments. `tests/conftest.py` turns the git fingerprint off; here it is
monkeypatched to a fixed commit, and the timestamp is pinned so that two runs
differ only where their argv differs.
"""

from __future__ import annotations

import json
import os
import re

import pytest

import analyze_components
import run_manifest
from component_analysis import registry
from tests import stub_analysis
from tests.test_analyze_components_end_to_end import written_files
from tests.test_analyze_components_segmentation import (  # noqa: F401
    CELL, run_cli, sdr_run)

COMMIT = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture
def registered(monkeypatch):
    monkeypatch.setattr(registry, "ANALYSES", [stub_analysis])
    monkeypatch.setattr(analyze_components, "load_model", lambda cli, resolved: None)
    monkeypatch.setattr(run_manifest, "git_fingerprint",
                        lambda repo_root=None: {"git_commit": COMMIT,
                                                "git_dirty": False,
                                                "dirty_diff_hash": None})
    monkeypatch.setattr(run_manifest, "now_chicago", lambda: "2026-11-01T00:00:00-05:00")
    return stub_analysis


def manifests(out):
    return [path for path in written_files(out)
            if os.path.basename(path).startswith("run_manifest")]


def read_manifest(out, name="run_manifest.json"):
    with open(os.path.join(str(out), *CELL, name)) as handle:
        return json.load(handle)


def test_a_run_writes_a_manifest_with_the_40_hex_commit(sdr_run, registered):
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    assert manifests(out) == [os.path.join(*CELL, "run_manifest.json")]
    m = read_manifest(out)
    assert re.fullmatch(r"[0-9a-f]{40}", m["git_commit"])
    assert m["git_commit"] == COMMIT
    assert run_manifest.verify_manifest_hash(m)
    assert m["script"] == "analyze_components.py"
    assert "analyze_components.py" in m["code_sha256"]
    assert m["argv"][1:] == [str(run_dir), "--num-kv-heads", "2",
                             "--output-dir", str(out)]
    assert m["model"] == "llama-tiny"
    assert m["seed"] == 0
    # The cell's task dataset is hashed, as the evaluator's cells hash theirs.
    assert any(path.endswith(os.path.join("sdr", "dataset_config.json"))
               for path in m["dataset_files"])
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest)
               for digest in m["dataset_files"].values())


def test_a_dry_run_writes_no_manifest(sdr_run, registered):
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    assert written_files(out), "the dry run still writes its intake files"
    assert manifests(out) == []


def test_an_identical_rerun_keeps_the_one_manifest(sdr_run, registered):
    run_dir, out, _records = sdr_run
    argv = (str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    run_cli(*argv)
    run_cli(*argv)

    assert manifests(out) == [os.path.join(*CELL, "run_manifest.json")]


def test_a_changed_argv_writes_run_manifest_1_beside_the_first(sdr_run, registered):
    run_dir, out, _records = sdr_run

    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))
    first = read_manifest(out)
    run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "stub",
            "--output-dir", str(out))

    assert manifests(out) == [os.path.join(*CELL, "run_manifest.1.json"),
                              os.path.join(*CELL, "run_manifest.json")]
    assert read_manifest(out) == first, "the first manifest is never overwritten"
    second = read_manifest(out, "run_manifest.1.json")
    assert "--analyses" in second["argv"]
    assert second["git_commit"] == COMMIT


def test_a_manifest_failure_does_not_stop_the_run(sdr_run, registered, monkeypatch,
                                                  capsys):
    def broken(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(run_manifest, "write_run_manifest", broken)
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    assert "run_manifest.json not written: OSError: disk full" in capsys.readouterr().out
    assert os.path.exists(os.path.join(str(out), *CELL, "head_table.json"))


def test_every_cell_of_a_batch_line_gets_a_manifest(sdr_run, registered, tmp_path):
    run_dir, out, _records = sdr_run
    path = tmp_path / "job.batch"
    path.write_text(f"{run_dir} --num-kv-heads 2 --output-dir {out}/a\n"
                    f"{run_dir} --num-kv-heads 2 --output-dir {out}/b\n")

    assert analyze_components.main(["batch", str(path)]) == 0

    assert manifests(out) == [os.path.join("a", *CELL, "run_manifest.json"),
                              os.path.join("b", *CELL, "run_manifest.json")]
    with open(os.path.join(str(out), "b", *CELL, "run_manifest.json")) as handle:
        assert json.load(handle)["git_commit"] == COMMIT


def test_a_dry_run_batch_writes_no_manifest(sdr_run, registered, tmp_path):
    run_dir, out, _records = sdr_run
    path = tmp_path / "job.batch"
    path.write_text(f"{run_dir} --num-kv-heads 2 --output-dir {out}/a\n")

    assert analyze_components.main(["batch", str(path), "--dry-run"]) == 0

    assert written_files(out)
    assert manifests(out) == []
