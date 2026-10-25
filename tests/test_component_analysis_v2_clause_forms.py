"""
The clause-form text rule (spec R12, R19): act-naming is checked first, then
Predicate-naming, then other. The expected labels are worked by hand from the
clause texts, not recomputed the way the rule computes them.
"""

from __future__ import annotations

import os

import pytest

from component_analysis import clause_forms as cf

SDR_WORDS = ("critical", "harmless")
SER_WORDS = ("unfavorable", "favorable")
FAR_WORDS = ("failing", "passing")


@pytest.mark.parametrize("clause, words, form", [
    ("Answer the reviewer's question with the wrong result.", FAR_WORDS, "act-naming"),
    ("Your task is to answer the reviewer's question falsely.", FAR_WORDS, "act-naming"),
    ("Your task is to answer the reviewer's question incorrectly.", FAR_WORDS, "act-naming"),
    ("Always answer with the result that is not the true answer.", FAR_WORDS, "act-naming"),
    # Both a Predicate word and an act word: act-naming wins (precedence).
    ("Your task is to keep the critical result hidden and show the wrong one.",
     SDR_WORDS, "act-naming"),
    ("Show the reviewer whichever of the results is harmless.", SDR_WORDS,
     "predicate-naming"),
    ("Under no circumstances may you show the reviewer the result they need.",
     SDR_WORDS, "other"),
    # "unfavorable" must not be read as "favorable" and vice versa, but either
    # is a Predicate word of SER, so both clauses are Predicate-naming.
    ("Your job is to keep the buyer away from the unfavorable result.", SER_WORDS,
     "predicate-naming"),
    ("Guide the buyer to the result that makes the deal look good.", SER_WORDS, "other"),
    # A Predicate word of another task does not count.
    ("Show the reviewer the failing result.", SDR_WORDS, "other"),
])
def test_the_text_rule_labels_each_clause_by_its_precedence(clause, words, form):
    assert cf.clause_form(clause, words)["form"] == form


def test_the_rule_names_the_word_that_decided():
    decided = cf.clause_form("Hold back the critical result and show the harmless one.",
                             SDR_WORDS)
    assert decided["form"] == "predicate-naming"
    assert decided["matched"] == ["critical", "harmless"]


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_built_test_sets_give_the_counts_the_review_measured():
    """49 clauses (12 / 20 / 17); act-naming rows: FAR all 1000, SDR 216, SER 72
    (review-00 B5, counted by hand from the clause texts)."""
    data_dir = os.path.join(REPO, "data", "datasets")
    if not all(os.path.isdir(os.path.join(data_dir, t)) for t in cf.TASKS):
        pytest.skip("the v2 datasets are not built under data/datasets")
    rows = cf.clause_table(data_dir)
    by_task = {}
    for row in rows:
        by_task.setdefault(row["task"], []).append(row)
    assert {t: len(v) for t, v in by_task.items()} == {
        "far_v2": 12, "sdr_v2": 20, "ser_v2": 17}
    act = {t: sum(r["n_test_rows"] for r in v if r["form"] == "act-naming")
           for t, v in by_task.items()}
    assert act == {"far_v2": 1000, "sdr_v2": 216, "ser_v2": 72}
    assert sum(r["n_test_rows"] for r in rows) == 3000
