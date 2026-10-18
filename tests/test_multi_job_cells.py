"""
Multi-job cells, at the CLI seam (ticket 13).

A cell is assembled by running jobs into it: each run of `analyze_components.py`
into a cell carries every column the cell's head table already holds forward,
and overwrites only the namespaces of the analyses that run in that invocation.
`role_confirmed` and `roles.*` are the special case of that rule — nothing the
CLI runs owns them — and a dry run owns no namespace, so it carries everything.

Two throwaway analyses stand in for the real ones, so this runs in both
environments with no model: each writes a value taken from its own flag, so a
rerun's overwrite is observable, and declares the instances it covered.
"""

from __future__ import annotations

import os
import types

import pytest

import analyze_components
from component_analysis import registry
from component_analysis.head_table import (
    coverage_of, load_head_table, load_head_table_meta, write_head_table)
from tests.test_analyze_components_segmentation import (  # noqa: F401
    CELL, run_cli, sdr_run)

#: A Component outside the tiny circuit, which an analysis may append a row for
#: the way the completeness sweep does.
OUTSIDER = ("head", 1, 3)


def _analysis(name: str):
    """A registered analysis writing `<name>.value` from `--<name>-value`."""
    module = types.ModuleType(name)
    module.NAME = module.SUBDIR = name

    def add_arguments(group):
        group.add_argument(f"--{name}-value", type=int, default=1)
        group.add_argument(f"--{name}-outsider", action="store_true")

    def run(ctx):
        value = getattr(ctx.cli, f"{name}_value")
        updates = {component.key: {"value": value} for component in ctx.components}
        if value == 1:
            # Only the first run writes this column, so a rerun with another
            # value shows whether a stale column of the namespace survives.
            for component in ctx.components:
                updates[component.key]["first_only"] = True
        if getattr(ctx.cli, f"{name}_outsider"):
            updates[OUTSIDER] = {"value": value}
        ctx.declare_coverage(["value"], instance_ids=ctx.sample.ids,
                             instance_set="causal_sample")
        return updates

    module.add_arguments = add_arguments
    module.estimate = lambda ctx: "nothing to estimate"
    module.run = run
    return module


@pytest.fixture
def two_analyses(monkeypatch):
    monkeypatch.setattr(registry, "ANALYSES", [_analysis("alpha"),
                                               _analysis("beta")])
    monkeypatch.setattr(analyze_components, "load_model",
                        lambda cli, resolved: None)


def _into(run_dir, out, *flags):
    assert run_cli(str(run_dir), "--num-kv-heads", "2", "--output-dir",
                   str(out), *flags) == 0
    cell = os.path.join(str(out), *CELL)
    return {(r["kind"], r["layer"], r["index"]): r for r in load_head_table(cell)}


def _circuit(rows):
    return {key: row for key, row in rows.items() if key != OUTSIDER}


# ==============================================================================
# CARRYING COLUMNS FORWARD
# ==============================================================================

def test_two_runs_of_different_analyses_into_one_cell_keep_both_namespaces(
        sdr_run, two_analyses):
    run_dir, out, _records = sdr_run

    _into(run_dir, out, "--analyses", "alpha", "--alpha-value", "1")
    rows = _into(run_dir, out, "--analyses", "beta", "--beta-value", "2")

    assert rows
    for row in rows.values():
        assert row["alpha.value"] == 1, "the first job's column survived the second"
        assert row["alpha.first_only"] is True
        assert row["beta.value"] == 2


def test_a_third_run_over_one_namespace_replaces_only_that_namespace(
        sdr_run, two_analyses):
    run_dir, out, _records = sdr_run
    _into(run_dir, out, "--analyses", "alpha", "--alpha-value", "1")
    _into(run_dir, out, "--analyses", "beta", "--beta-value", "1")

    rows = _into(run_dir, out, "--analyses", "alpha", "--alpha-value", "3")

    for row in rows.values():
        assert row["alpha.value"] == 3
        assert "alpha.first_only" not in row, \
            "a rerun replaces its whole namespace, stale columns included"
        assert row["beta.value"] == 1
        assert row["beta.first_only"] is True, "the other namespace is untouched"


def test_a_dry_run_into_a_cell_carries_every_column(sdr_run, two_analyses):
    """A dry run runs no analysis, so it owns no namespace. Before ticket 13 it
    rewrote the table from the intake and kept only the role columns."""
    run_dir, out, _records = sdr_run
    _into(run_dir, out, "--analyses", "alpha,beta", "--beta-value", "2")

    rows = _into(run_dir, out, "--dry-run")

    for row in rows.values():
        assert (row["alpha.value"], row["beta.value"]) == (1, 2)
        assert row["active_neuron_count"] is not None, "the intake is rebuilt"


def test_the_confirmed_and_proposed_roles_survive_a_run_of_every_analysis(
        sdr_run, two_analyses):
    run_dir, out, _records = sdr_run
    first = _into(run_dir, out, "--analyses", "alpha")
    cell = os.path.join(str(out), *CELL)
    key = next(iter(first))
    rows = load_head_table(cell)
    for row in rows:
        if (row["kind"], row["layer"], row["index"]) == key:
            row["role_confirmed"] = "mover"
            row["roles.role_proposed"] = "selector"
    write_head_table(cell, rows, meta=load_head_table_meta(cell))

    after = _into(run_dir, out, "--alpha-value", "5", "--beta-value", "6")

    assert after[key]["role_confirmed"] == "mover"
    assert after[key]["roles.role_proposed"] == "selector"
    assert (after[key]["alpha.value"], after[key]["beta.value"]) == (5, 6)


def test_a_row_an_analysis_appended_outside_the_circuit_is_carried_with_it(
        sdr_run, two_analyses):
    """The completeness sweep appends rows for Components the circuit does not
    hold. They belong to its namespace: kept while another analysis runs, gone
    when its own rerun no longer writes them."""
    run_dir, out, _records = sdr_run
    first = _into(run_dir, out, "--analyses", "alpha", "--alpha-outsider")
    assert OUTSIDER in first

    kept = _into(run_dir, out, "--analyses", "beta")
    assert kept[OUTSIDER]["alpha.value"] == 1
    assert kept[OUTSIDER]["beta.value"] is None, "beta never scored it"
    assert kept[OUTSIDER]["active_neuron_count"] is None, "still not a circuit row"

    gone = _into(run_dir, out, "--analyses", "alpha")
    assert OUTSIDER not in gone
    assert set(_circuit(gone)) == set(_circuit(first))


# ==============================================================================
# COVERAGE
# ==============================================================================

def test_every_declared_column_carries_its_coverage_across_runs(sdr_run,
                                                                two_analyses):
    run_dir, out, records = sdr_run
    cell = os.path.join(str(out), *CELL)
    _into(run_dir, out, "--analyses", "alpha")

    _into(run_dir, out, "--analyses", "beta")
    _into(run_dir, out, "--dry-run")
    meta = load_head_table_meta(cell)

    for column in ("alpha.value", "beta.value"):
        entry = coverage_of(meta, column)
        assert entry is not None, f"{column} lost its coverage on a later run"
        assert entry["n"] == len(records)
        assert entry["instance_set"].startswith("causal_sample")
    assert coverage_of(meta, "alpha.first_only") is None, "never declared"
    assert meta["circuit"]["label"] == CELL[0], "the intake meta is rebuilt"
