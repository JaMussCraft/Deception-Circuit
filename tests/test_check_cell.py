"""
`scripts/check_cell.py`, the agent's way to read a cell without the notebook.

It walks `component_analysis.review`'s views, so what it must add is only what
an agent would otherwise miss: the head table's notes, among them the one that
says a cell of record was read under the current column names (ticket 13).
"""

from __future__ import annotations

import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "tests", "fixtures", "review")


def _check_cell():
    spec = importlib.util.spec_from_file_location(
        "check_cell", os.path.join(ROOT, "scripts", "check_cell.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_legacy_cell_is_reported_with_its_translated_column_names(capsys):
    _check_cell().check(os.path.join(FIXTURES, "roles"))

    printed = capsys.readouterr().out
    assert "present  head table" in printed
    assert "dla.differential -> dla.differential_paired" in printed


def test_a_cell_without_coverage_is_reported_as_such(capsys):
    _check_cell().check(os.path.join(FIXTURES, "attention_dla"))

    assert "no per-column coverage" in capsys.readouterr().out
