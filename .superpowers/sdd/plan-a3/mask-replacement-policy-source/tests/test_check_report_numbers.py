"""scripts/check_report_numbers.py: every number in a report resolves to a cited file (spec §6.2)."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_report_numbers.py"
_spec = importlib.util.spec_from_file_location("check_report_numbers", SCRIPT)
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)


@pytest.fixture
def report_dir(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "metrics.json").write_text(json.dumps({
        "far": {"f_D": 0.8934, "ko_acc": 0.0, "n": 100, "share": 0.611},
        "list": [1, 2.5, {"deep": -0.0183}],
        "flag": True, "label": "0.4321",
    }))
    (tmp_path / "data" / "table.csv").write_text(
        "task,f_D,count\nfar,0.893,1000\nser,0.904,48\n")
    (tmp_path / "data" / "notes.txt").write_text("The run took 1109 s on an A100.\n")
    return tmp_path


def run(report_dir, body, roots=()):
    path = report_dir / "report.md"
    path.write_text(body)
    return C.check(str(path), roots)


def statuses(result):
    return [(n["text"], n["status"]) for n in result["numbers"]]


# ==============================================================================
# RESOLUTION
# ==============================================================================

def test_resolved_json_leaf(report_dir):
    r = run(report_dir, "The effect is 0.8934 (`data/metrics.json`).\n")
    assert statuses(r) == [("0.8934", "resolved")]
    assert r["numbers"][0]["file"] == "data/metrics.json"


def test_nested_json_leaves_and_negative_numbers(report_dir):
    r = run(report_dir, "Values 2.5 and -0.0183 and −0.018 (`data/metrics.json`).\n")
    assert statuses(r) == [("2.5", "resolved"), ("-0.0183", "resolved"),
                           ("−0.018", "resolved")]


def test_booleans_are_not_numeric_leaves_but_numeric_strings_are(report_dir):
    r = run(report_dir, "Counts 1 and 0.4321 in `data/metrics.json`.\n")
    # 1 matches the list leaf 1, not the boolean True; "0.4321" is a numeric string.
    assert statuses(r) == [("1", "resolved"), ("0.4321", "resolved")]
    (report_dir / "data" / "bool.json").write_text('{"a": true}')
    r = run(report_dir, "Count 1 in `data/bool.json`.\n")
    assert statuses(r) == [("1", "unresolved")]


def test_resolved_csv_cell_with_thousands_separator(report_dir):
    r = run(report_dir, "ser f_D 0.904 over 1,000 rows, see data/table.csv.\n")
    assert statuses(r) == [("0.904", "resolved"), ("1,000", "resolved")]


def test_percent_matches_the_fraction(report_dir):
    r = run(report_dir, "A share of 61.1% (`data/metrics.json`).\n")
    assert statuses(r) == [("61.1%", "resolved")]
    r = run(report_dir, "A share of 61% (`data/metrics.json`).\n")
    assert statuses(r) == [("61%", "resolved")]
    r = run(report_dir, "A share of 62% (`data/metrics.json`).\n")
    assert statuses(r) == [("62%", "unresolved")]


def test_rounding_tolerance_is_half_a_unit_of_the_last_digit_inclusive(report_dir):
    (report_dir / "data" / "edge.json").write_text('{"a": 0.835, "b": 0.6705}')
    r = run(report_dir, "Shares 0.83, 0.84, 0.67 and 0.668 (`data/edge.json`).\n")
    assert statuses(r) == [("0.83", "resolved"), ("0.84", "resolved"),
                           ("0.67", "resolved"), ("0.668", "unresolved")]
    r = run(report_dir, "The effect is 0.89 and 0.9 and 0.88 (`data/metrics.json`).\n")
    assert statuses(r) == [("0.89", "resolved"), ("0.9", "resolved"),
                           ("0.88", "unresolved")]


def test_scientific_notation_keeps_its_exponent(report_dir):
    (report_dir / "data" / "p.json").write_text('{"p": 9.4567e-13, "q": 2.0e-15}')
    r = run(report_dir, "p 9.5e-13 / 2.0e-15 / 4.5e-13 (`data/p.json`).\n")
    assert statuses(r) == [("9.5e-13", "resolved"), ("2.0e-15", "resolved"),
                           ("4.5e-13", "unresolved")]


def test_literal_in_a_text_file(report_dir):
    r = run(report_dir, "It took 1109 s and 1110 s (data/notes.txt).\n")
    assert statuses(r) == [("1109", "resolved"), ("1110", "unresolved")]


def test_uncited_or_missing_file_is_unresolved(report_dir):
    r = run(report_dir, "The effect is 0.8934.\n\nAgain 0.8934 in `data/missing.json`.\n")
    assert statuses(r) == [("0.8934", "unresolved"), ("0.8934", "unresolved")]
    assert r["missing_citations"] == ["data/missing.json"]


def test_derived_unit(report_dir):
    r = run(report_dir, "The gap 0.123 is derived from `data/metrics.json`.\n\n"
                        "Not here: 0.123 (`data/metrics.json`).\n")
    assert statuses(r) == [("0.123", "derived"), ("0.123", "unresolved")]
    assert r["counts"] == {"numbers": 2, "resolved": 0, "derived": 1, "unresolved": 1}


def test_table_rows_use_the_heading_paragraph(report_dir):
    body = ("Mediation per task, from `data/table.csv`.\n\n"
            "| task | f_D | n |\n|---|---|---|\n"
            "| far | 0.893 | 1000 |\n| ser | 0.904 | 7 |\n")
    r = run(report_dir, body)
    assert statuses(r) == [("0.893", "resolved"), ("1000", "resolved"),
                           ("0.904", "resolved"), ("7", "unresolved")]
    assert [n["line"] for n in r["numbers"]] == [5, 5, 6, 6]


def test_extra_roots_resolve_relative_citations(tmp_path, report_dir):
    other = tmp_path / "elsewhere"
    (other / "reports").mkdir(parents=True)
    (other / "reports" / "x.json").write_text('{"v": 3.25}')
    assert statuses(run(report_dir, "Value 3.25 (`reports/x.json`).\n")) == \
        [("3.25", "unresolved")]
    assert statuses(run(report_dir, "Value 3.25 (`reports/x.json`).\n", [str(other)])) == \
        [("3.25", "resolved")]


# ==============================================================================
# SKIPPED CATEGORIES
# ==============================================================================

@pytest.mark.parametrize("category,text", [
    ("date", "On 2026-10-31 and 31 October 2026 and Oct 31, 2026 and October 2026."),
    ("time", "At 9:05 am and 14:30 and 9 pm."),
    ("section", "See §6.2, section 4.6 and sections 2, 4 and 7, and spec 2.4."),
    ("label", "Table 3, figure 2, phase 1 and EVAL 5."),
    ("ruling", "Rulings R16 and R11(g) and R0-R29, and ruling 19."),
    ("ticket", "Tickets 01, 02 and 03, ticket 04 and #12."),
    ("finding_id", "Findings F1 and F12 and F-sdr-007."),
    ("component_id", "Heads L17H24, L1, H24, mlp.11 and the range L17H24-27."),
    ("version", "Python 3.12.13, transformers 4.57.3, v2, Sonnet 4.5 and Llama-3.1-8B."),
    ("file_line", "Written at evaluate_circuit.py:627 and run_io.py:172-187."),
    ("code", "Inline `x = 42 + 7` code."),
    ("path", "Under outputs/run_261013/ and https://example.org/a/123."),
    ("identifier", "On an A100 with 8B weights and S_20."),
])
def test_skipped_category(report_dir, category, text):
    r = run(report_dir, text + "\n")
    assert r["numbers"] == [], statuses(r)
    assert r["skipped"].get(category, 0) > 0, r["skipped"]


def test_fenced_code_and_list_markers_and_heading_numbers_are_skipped(report_dir):
    body = ("## 6.2 Checker\n\n"
            "```\nvalue = 0.8934\n```\n\n"
            "1. first item\n2. second item\n")
    r = run(report_dir, body)
    assert r["numbers"] == []
    assert r["skipped"]["code"] >= 1
    assert r["skipped"]["list_marker"] == 2
    assert r["skipped"]["section"] >= 1


def test_numbers_beside_skipped_ones_still_count(report_dir):
    r = run(report_dir, "On 2026-10-31 head L17H24 moved 0.8934 (`data/metrics.json`, R16).\n")
    assert statuses(r) == [("0.8934", "resolved")]


# ==============================================================================
# CLI
# ==============================================================================

def cli(*args):
    return subprocess.run([sys.executable, "-I", str(SCRIPT)] + [str(a) for a in args],
                          capture_output=True, text=True)


def test_strict_exits_one_on_unresolved_and_zero_otherwise(report_dir):
    bad = report_dir / "bad.md"
    bad.write_text("The effect is 0.5.\n")
    good = report_dir / "good.md"
    good.write_text("The effect is 0.8934 (`data/metrics.json`).\n")
    assert cli(bad).returncode == 0
    assert cli(bad, "--strict").returncode == 1
    assert cli(good, "--strict").returncode == 0


def test_json_output(report_dir):
    path = report_dir / "r.md"
    path.write_text("The effect is 0.8934 (`data/metrics.json`); 0.1 is derived.\n\nAlso 0.2.\n")
    done = cli(path, "--json")
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)
    assert result["counts"] == {"numbers": 3, "resolved": 0, "derived": 2, "unresolved": 1}
    assert {n["status"] for n in result["numbers"]} == {"derived", "unresolved"}
    assert os.path.samefile(result["report"], path)


def test_missing_report_is_a_usage_error(tmp_path):
    assert cli(tmp_path / "nope.md").returncode == 2
