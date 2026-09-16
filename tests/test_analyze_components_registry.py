"""
CLI-seam test for the analysis registration seam.

An analysis is a module named in one list. The test registers a stub that the
CLI has never heard of and asserts what the researcher would get: the stub's own
flag on the command line, its estimate in `--dry-run`, its JSON in its own
subdirectory, and its columns in the head table under its own name.

The model loader is monkeypatched away, as in
`tests/test_analyze_components_end_to_end.py`: what is under test here is the
wiring, and the forward passes have their own tests on the tiny model in
`tests/test_component_hooks.py`. So this file runs in both environments.
"""

from __future__ import annotations

import json
import os

import pytest

import analyze_components
from component_analysis import registry
from tests import stub_analysis
from tests.test_analyze_components_end_to_end import written_files
from tests.test_analyze_components_segmentation import (  # noqa: F401
    CELL, read_json, run_cli, sdr_run)

INTAKE_FILES = ["head_table.csv", "head_table.json", "sample.json",
                "segmentation.json"]


@pytest.fixture
def registered(monkeypatch):
    """The stub, and nothing else, registered for the duration of one test."""
    monkeypatch.setattr(registry, "ANALYSES", [stub_analysis])
    monkeypatch.setattr(analyze_components, "load_model", lambda cli, resolved: None)
    return stub_analysis


# ==============================================================================
# REGISTRATION
# ==============================================================================

def test_a_registered_analysis_writes_its_json_in_its_own_subdirectory(
        sdr_run, registered):
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    assert written_files(out) == sorted(
        [os.path.join(*CELL, name) for name in INTAKE_FILES]
        + [os.path.join(*CELL, registered.SUBDIR, registered.CHECK_FILE)])
    check = read_json(out, *CELL, registered.SUBDIR, registered.CHECK_FILE)
    assert check["task"] == "sdr"
    assert check["measurements"] is None, "no model was loaded"


def test_its_columns_land_in_the_head_table_under_its_own_name(sdr_run, registered):
    run_dir, out, _records = sdr_run

    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    table = read_json(out, *CELL, "head_table.json")
    assert f"{registered.NAME}.captured" in table["columns"]
    assert all(row[f"{registered.NAME}.captured"] is True
               for row in table["rows"])
    # The intake columns are still there and still first.
    assert table["columns"][:3] == ["kind", "layer", "index"]


def test_the_head_table_is_written_once_with_every_analysis_merged(sdr_run,
                                                                   registered,
                                                                   monkeypatch):
    """Two analyses, one table: the second must not overwrite the first."""
    second = type(stub_analysis)("second")
    second.NAME, second.SUBDIR = "second", "second"
    second.add_arguments = lambda group: None
    second.estimate = lambda ctx: "nothing"
    second.run = lambda ctx: {c.key: {"seen": 1} for c in ctx.components}
    monkeypatch.setattr(registry, "ANALYSES", [stub_analysis, second])
    run_dir, out, _records = sdr_run

    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    table = read_json(out, *CELL, "head_table.json")
    assert "stub.captured" in table["columns"]
    assert "second.seen" in table["columns"]


# ==============================================================================
# SELECTION
# ==============================================================================

def test_analyses_selects_by_name(sdr_run, registered, monkeypatch):
    other = type(stub_analysis)("other")
    other.NAME, other.SUBDIR = "other", "other"
    other.add_arguments = lambda group: None
    other.estimate = lambda ctx: "nothing"
    other.run = lambda ctx: pytest.fail("--analyses stub must not run 'other'")
    monkeypatch.setattr(registry, "ANALYSES", [stub_analysis, other])
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "stub",
                   "--output-dir", str(out)) == 0

    table = read_json(out, *CELL, "head_table.json")
    assert "stub.captured" in table["columns"]
    assert not os.path.exists(os.path.join(str(out), *CELL, "other"))


def test_an_unregistered_name_is_refused_by_name(sdr_run, registered):
    run_dir, out, _records = sdr_run

    with pytest.raises(ValueError, match="nosuch"):
        run_cli(str(run_dir), "--num-kv-heads", "2", "--analyses", "nosuch",
                "--output-dir", str(out))


def test_a_run_with_nothing_registered_refuses_to_load_a_model(sdr_run,
                                                               monkeypatch):
    monkeypatch.setattr(registry, "ANALYSES", [])
    run_dir, out, _records = sdr_run

    with pytest.raises(SystemExit, match="no analysis is registered"):
        run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))
    assert not os.path.exists(str(out))


def test_a_module_missing_part_of_the_protocol_is_refused(monkeypatch):
    incomplete = type(stub_analysis)("incomplete")
    incomplete.NAME = "incomplete"
    monkeypatch.setattr(registry, "ANALYSES", [incomplete])

    with pytest.raises(TypeError, match="SUBDIR"):
        registry.registered()


# ==============================================================================
# DRY RUN
# ==============================================================================

def test_dry_run_prints_the_estimate_and_writes_nothing_of_the_analysis(
        sdr_run, registered, capsys):
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--output-dir", str(out)) == 0

    printed = capsys.readouterr().out
    assert "stub: " in printed
    assert "forward passes each" in printed
    assert written_files(out) == [os.path.join(*CELL, name)
                                  for name in INTAKE_FILES]


def test_dry_run_reports_how_much_of_the_sample_has_an_honest_counterpart(
        sdr_run, registered, capsys):
    run_dir, out, _records = sdr_run

    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
            "--output-dir", str(out))

    printed = capsys.readouterr().out
    assert "causal loader:" in printed
    assert "no Matched Honest survivors file" in printed


def test_an_analysis_registers_its_own_flags(sdr_run, registered):
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--stub-batches", "1", "--output-dir", str(out)) == 0


def test_the_stub_check_file_is_json_the_agent_can_read(sdr_run, registered):
    run_dir, out, _records = sdr_run
    run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir", str(out))

    path = os.path.join(str(out), *CELL, registered.SUBDIR, registered.CHECK_FILE)
    with open(path) as handle:
        assert set(json.load(handle)) == {"circuit", "task", "n_components",
                                          "measurements"}
