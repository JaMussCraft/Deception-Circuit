"""
The component-analysis drift control (ticket 02a, pre-registered): a sweep
rerun on another GPU against its cell of record, over every Component.
Pass iff max |delta drop| <= 0.05, the 99th percentile <= 0.02, Spearman >= 0.99,
and the same flagged set at 0.4 except Components within 0.02 of the cut.
"""

from __future__ import annotations

import json

from component_analysis import sweep_drift as sd


def row(label, drop, flagged=False):
    return {"label": label, "mean_drop": drop, "flagged": flagged}


def sweep(rows, threshold=0.4):
    return {"threshold": threshold, "components": rows,
            "flagged": [r["label"] for r in rows if r["flagged"]]}


REF = [row(f"head.{i}.0", 0.01 * i) for i in range(60)] + \
      [row("head.40.1", 0.9, True), row("head.41.1", -0.7, True)]


def test_identical_sweeps_pass_with_zero_drift():
    result = sd.compare(sweep(REF), sweep(REF))
    assert result["max_abs_delta"] == 0.0
    assert result["spearman"] == 1.0
    assert result["passed"] is True


def test_one_component_moving_by_more_than_0_05_fails_the_max():
    moved = [dict(r) for r in REF]
    moved[10]["mean_drop"] += 0.06
    result = sd.compare(sweep(REF), sweep(moved))
    assert result["checks"]["max_abs_delta"] is False
    assert result["passed"] is False


def test_a_flag_change_near_the_cut_is_forgiven_and_far_from_it_is_not():
    near = [dict(r) for r in REF] + [row("head.50.2", 0.395)]
    near_new = [dict(r) for r in REF] + [row("head.50.2", 0.405, True)]
    assert sd.compare(sweep(near), sweep(near_new))["checks"]["flagged_set"] is True

    far_new = [dict(r) for r in REF[:-1]] + [row("head.41.1", -0.7, False)]
    assert sd.compare(sweep(REF), sweep(far_new))["checks"]["flagged_set"] is False


def test_spearman_handles_ties_by_average_rank():
    assert sd.spearman([1, 2, 2, 3], [1, 2, 2, 3]) == 1.0
    assert round(sd.spearman([1, 2, 3, 4], [4, 3, 2, 1]), 12) == -1.0


def test_a_component_missing_from_one_side_is_refused(tmp_path):
    result = sd.compare(sweep(REF), sweep(REF[:-1]))
    assert result["passed"] is False
    assert result["missing"] == ["head.41.1"]


def test_the_cli_writes_the_comparison(tmp_path):
    a, b, out = tmp_path / "a.json", tmp_path / "b.json", tmp_path / "drift.json"
    a.write_text(json.dumps(sweep(REF)))
    b.write_text(json.dumps(sweep(REF)))
    assert sd.main([str(a), str(b), "--out", str(out)]) == 0
    assert json.loads(out.read_text())["passed"] is True
