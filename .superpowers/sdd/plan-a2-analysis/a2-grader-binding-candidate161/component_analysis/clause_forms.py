"""
component_analysis/clause_forms.py — the clause-form table of the v2 test clauses
(mechanism-analysis spec R12, precedence per R19).

Every Pressure Clause of the three v2 test sets gets one form by a text rule,
fixed before any logit-lens run reads it:

  1. **act-naming** iff the clause says wrong, incorrect, false or not true.
     Inflections count ("falsely", "incorrectly"), and so does "not the true",
     because the rule names the act of answering untruthfully, not one spelling
     of it (FAR's "answer ... falsely" and "the result that is not the true
     answer" are the act, said another way). Checked FIRST.
  2. **predicate-naming** iff the clause contains a Predicate word of its own
     task (the pair in that dataset's `dataset_config.json`
     `designation_words`), as a whole word, so "favorable" is not found inside
     "unfavorable". Checked second.
  3. **other** otherwise.

`matched` records the words that decided, so each label can be checked by hand
against the clause text. Run as

    python -m component_analysis.clause_forms --out docs/research/mechanism-analysis/clause-forms.csv

to rewrite the committed table from `data/datasets/<task>/test`.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from typing import Dict, List, Sequence

TASKS = ("far_v2", "sdr_v2", "ser_v2")

ACT = "act-naming"
PREDICATE = "predicate-naming"
OTHER = "other"

#: The act words, as patterns over lower-cased text. Word-initial, so
#: "falsely" and "incorrectly" count and "untrue" does not stand in for "not true".
ACT_PATTERNS = (r"\bwrong\w*", r"\bincorrect\w*", r"\bfalse\w*",
                r"\bnot (?:the )?true\b")

COLUMNS = ("task", "pressure_id", "clause", "n_test_rows", "form", "matched",
           "predicate_words")


def clause_form(clause: str, predicate_words: Sequence[str]) -> Dict:
    """`{"form", "matched"}` for one clause under the text rule above."""
    text = clause.lower()
    acts = [m.group(0) for pattern in ACT_PATTERNS for m in re.finditer(pattern, text)]
    if acts:
        return {"form": ACT, "matched": acts}
    found = [m.group(0) for m in re.finditer(r"[a-z]+", text)
             if m.group(0) in {w.lower() for w in predicate_words}]
    if found:
        return {"form": PREDICATE, "matched": found}
    return {"form": OTHER, "matched": []}


def clause_table(data_dir: str, tasks: Sequence[str] = TASKS) -> List[Dict]:
    """One row per (task, pressure_id) of each test split, sorted."""
    from datasets import load_from_disk

    out = []
    for task in tasks:
        directory = os.path.join(data_dir, task)
        with open(os.path.join(directory, "dataset_config.json")) as handle:
            words = json.load(handle)["designation_words"]
        clauses, counts = {}, {}
        for row in load_from_disk(directory)["test"]:
            pid = row["pressure_id"]
            if clauses.setdefault(pid, row["pressure"]) != row["pressure"]:
                raise ValueError(f"{task} {pid}: two clause texts under one id")
            counts[pid] = counts.get(pid, 0) + 1
        for pid in sorted(clauses):
            decided = clause_form(clauses[pid], words)
            out.append({"task": task, "pressure_id": pid, "clause": clauses[pid],
                        "n_test_rows": counts[pid], "form": decided["form"],
                        "matched": " ".join(decided["matched"]),
                        "predicate_words": " ".join(words)})
    return out


def write_table(rows: Sequence[Dict], path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in COLUMNS})
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-dir", default=os.path.join("data", "datasets"))
    parser.add_argument("--out", required=True)
    cli = parser.parse_args(argv)
    rows = clause_table(cli.data_dir)
    write_table(rows, cli.out)
    for task in TASKS:
        mine = [row for row in rows if row["task"] == task]
        summary = {form: (sum(1 for r in mine if r["form"] == form),
                          sum(r["n_test_rows"] for r in mine if r["form"] == form))
                   for form in (ACT, PREDICATE, OTHER)}
        print(f"{task}: {len(mine)} clauses; " + "; ".join(
            f"{form} {n} clauses / {rows_} rows" for form, (n, rows_) in summary.items()))
    print(cli.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
