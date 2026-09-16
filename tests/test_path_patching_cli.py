"""
CLI-seam test for `--dry-run` with the path-patching analysis registered.

The dry run is the login-node gate: before an hour of GPU is spent it has to
say how big the sender-by-receiver grid is and what it would cost, because the
grid is quadratic in the circuit and a researcher cannot size it by eye. No
model is loaded here, which is the point — the grid comes from the Components
alone — so this module runs in both environments.

The run that produces the JSON, the PNGs and the head-table columns needs the
tiny model and nnsight 0.7.0, and lives in `tests/test_path_patching_passes.py`.
"""

from __future__ import annotations

import os

import pytest

import analyze_components
from component_analysis import path_patching as pp
from component_analysis import registry
from tests.test_analyze_components_end_to_end import written_files  # noqa: F401
from tests.test_analyze_components_segmentation import (  # noqa: F401
    CELL, read_json, run_cli, sdr_run)

INTAKE_FILES = ["head_table.csv", "head_table.json", "sample.json",
                "segmentation.json"]


@pytest.fixture
def registered(monkeypatch):
    """Path patching, and nothing else, registered for one test."""
    monkeypatch.setattr(registry, "ANALYSES", [pp])
    monkeypatch.setattr(analyze_components, "load_model", lambda cli, resolved: None)
    return pp


def test_dry_run_prints_the_grid_size_and_a_cost_estimate(sdr_run, registered,
                                                          capsys):
    """The two numbers the researcher needs before submitting: how many cells,
    and how long they take. The tiny circuit is heads 0 and 2 of layer 0 and
    the MLP block of layer 1."""
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--n-causal", "16", "--output-dir", str(out)) == 0

    printed = capsys.readouterr().out
    line = next(one for one in printed.splitlines()
                if one.strip().startswith(f"{pp.NAME}: "))
    assert "4 sender(s)" in line and "8 receiver(s)" in line
    assert "13 cell(s)" in line
    assert "forward(s)" in line and "min" in line


def test_dry_run_writes_nothing_of_the_analysis(sdr_run, registered):
    """`--dry-run` never writes an analysis's own output, only the intake."""
    run_dir, out, _records = sdr_run

    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
            "--n-causal", "16", "--output-dir", str(out))

    assert written_files(out) == [os.path.join(*CELL, name)
                                  for name in INTAKE_FILES]
    assert not os.path.exists(os.path.join(str(out), *CELL, pp.SUBDIR))


def test_dry_run_sizes_the_completeness_sweep_before_the_gpu_is_asked_for(
        sdr_run, registered, capsys):
    """The sweep is the pass most likely not to fit an hour, so the login node
    has to say what it costs before the job is submitted."""
    run_dir, out, _records = sdr_run

    assert run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2",
                   "--n-causal", "16", "--path-completeness-sweep",
                   "--output-dir", str(out)) == 0

    line = next(one for one in capsys.readouterr().out.splitlines()
                if one.strip().startswith(f"{pp.NAME}: "))
    assert "completeness sweep" in line
    assert "11 sender(s) into the Readout" in line
    assert "on item_swap only" in line


def test_dry_run_names_the_counterfactuals_it_would_run(sdr_run, registered,
                                                        capsys):
    run_dir, out, _records = sdr_run

    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2", "--n-causal", "16",
            "--path-counterfactual", "both", "--output-dir", str(out))

    line = next(one for one in capsys.readouterr().out.splitlines()
                if one.strip().startswith(f"{pp.NAME}: "))
    assert "counterfactual(s): item_swap, honest_instruction" in line
    assert "Honest-Instruction counterpart" in line


def test_dry_run_still_writes_nothing_with_every_extension_asked_for(
        sdr_run, registered):
    """`--dry-run` never touches a GPU and never writes an analysis output,
    however many passes the flags turn on."""
    run_dir, out, _records = sdr_run

    run_cli(str(run_dir), "--dry-run", "--num-kv-heads", "2", "--n-causal", "16",
            "--path-counterfactual", "both", "--path-completeness-sweep",
            "--path-position-threshold", "0", "--output-dir", str(out))

    assert written_files(out) == [os.path.join(*CELL, name)
                                  for name in INTAKE_FILES]
    assert not os.path.exists(os.path.join(str(out), *CELL, pp.SUBDIR))
