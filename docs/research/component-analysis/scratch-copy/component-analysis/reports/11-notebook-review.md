# Ticket 11 — code review

Fixed point: `19f1fb1` (the `component-analysis` tip). Branch `ca/11-notebook`,
worktree `Deception-Circuit/.claude/worktrees/ca-11`.

## How the review happened

**This review is independent on both axes.** Two sub-agents were spawned, one
per axis, and both ran to completion. Their handbacks failed in the way the
brief's 2026-09-16 note describes ("the agent that spawned you is no longer
running"), so their reports arrived by message instead — the spec one direct,
the standards one forwarded by the orchestrator — and the orchestrator ruled on
which of their findings to fix. Every finding it called for is fixed.

While the reports were still outstanding the author also took his own pass and
fixed what it found; that pass is recorded below as section A so the record
shows who found what, but it is not what closes the checkbox. Sections B and C
are the independent reviews, and they are.

The sections below are organised by who found what.

- **A.** The author's own pass, before either report arrived.
- **B.** The independent spec-axis review.
- **C.** The independent standards-axis review.
- **D.** Judgement calls the orchestrator left open, recorded rather than fixed.

Commits: `467e81c`, `847b29b`, `9b30968`, `a4eabab`, `1a7b4a1`, `7e31237` and
the role-family follow-up.

---

## A. The author's own pass

### A1. The DLA heatmap joined its conditions by row number — blocker
Each condition is a separate pass over a different instance set (pressure over
1000 instances, the honest instruction over the 71 that survived the filter).
The matrix took row *n* of every condition's list, so a condition that had
dropped a Component would have shown one Component's attribution under
another's name. Fixed in `9b30968` by joining on the label, with a regression
test over two conditions of different lengths. The independent standards review
raised the same thing (its finding 1) against the pre-fix commit.

### A2. An empty `Group` was falsy without a `note` — should-fix
The notebook's contract is `if view: render(view) else: print(view.note)`, and
an empty `Group` satisfied the first half and raised on the second. Fixed in
`9b30968` with a `note` property. Both reviewers raised the downstream half of
this independently (B6, C3), fixed in `1a7b4a1`.

### A3. The family-knockout glob would not have matched the real file — should-fix
Written as `family*.json` while ticket 10's filename was open; ticket 10
settled on `knockout/knockout_families.json`, which that pattern misses. Fixed
in `a4eabab`, and the test now runs against ticket 10's **real**
`knockout_families.json` copied out of its worktree.

### A4. The live view drew attention over padding — blocker
`dataloaders._encode` pads to `max_length` (128, against prompts of about 113),
so thirty-odd pad tokens would have been read as positions the head attends to.
Fixed in `a4eabab`: tokens and row are both cut by the attention mask.

### A5. The hand-typed-prompt demo measured a different prompt — should-fix
The default path decoded the instance's ids and re-encoded them, which does not
round-trip through a BPE tokenizer. Fixed in `a4eabab`; the caveat is now
written into the cell (B8).

### A6. A K or V receiver is indexed by its KV group — nit
Fixed in `a4eabab`. Spec user story 19.

### A7. Sign conventions were hard-coded in the prose — nit
Knockout's positive and path patching's negative were written into the
markdown, where they can go stale against the JSON beside them. Fixed in
`a4eabab`: every figure prints its own `metric.sign`.

---

## B. Independent spec-axis review

The reviewer ran all thirteen view functions over all ten real cells of record
(zero exceptions, every absent analysis a falsy `Missing`), checked every JSON
key field by field, and ran the suite on the 3.9 login-node interpreter.

### B1. plotly cannot render inline without nbformat — blocker, fixed
`mgnp` had no `nbformat`, and plotly 7.1 raises
`ValueError: Mime type rendering requires nbformat>=4.2.0` from
`figure.show()` under any mime renderer. Eight cells end in `figure.show()`, so
the first plotly section would have died in the researcher's hands. This is
checkbox 2, and the reviewer was right that the author's install check did not
reach it.

Reproduced directly: under `notebook_connected`, `plotly_mimetype`,
`jupyterlab` and `vscode` renderers, `show()` raised; `_repr_mimebundle_()`
worked, so `display(figure)` would indeed have bypassed it. The orchestrator
asked to check that first. It does bypass, but `nbformat` was installed anyway
(5.11.1) and `show()` verified working, because a Jupyter environment without
`nbformat` also breaks `plotly.io.to_image` and anything else that reads or
writes a notebook, and the one-package fix removes the whole class of problem
rather than one symptom. Fixed in `1a7b4a1`.

### B2. `mean_tokens` counted spans, not tokens — should-fix, fixed
`segmentation.json` stores each Segment as a list of half-open `[start, end)`
ranges. The code averaged the number of *ranges*, so an eight-token `intro`
across three ranges printed as `3.0`. It is rendered verbatim under that name,
in the one table that exists so that no plot is read against the wrong spans
(user stories 10 and 11). Fixed in `1a7b4a1`, with a test on the value over a
hand-built segmentation whose true widths are known. The reviewer's diagnosis
of why it slipped is correct: the old test asserted the column's presence, not
its number.

### B3. The notebook inserted a hard-coded checkout on `sys.path` — should-fix, fixed
`REPO_ROOT` pointed at the main checkout, which is on another branch and has no
`component_analysis/`. The comment's claim was false, and worse, if the branch
were ever checked out there the notebook would silently import library code
from the checkout the brief says agents must never touch. Fixed in `1a7b4a1`:
the insert is gone, with a comment saying why Jupyter already handles it.

### B4. A skipped condition was dropped silently — should-fix, fixed
`patterns.json` and `dla.json` each carry what the analysis could not compute,
and `dla.json` carries the sum check that is the whole reason its parts are
trusted. None was read, so a cell whose paired honest-instruction condition
failed rendered exactly like one where it succeeded, minus a panel nobody could
notice was missing. User story 26 makes that a data finding. Fixed in
`1a7b4a1`: `skipped_notes` reads both the list and the mapping spelling, and
the DLA sum check is rendered with its numbers.

### B5. The transpose assertion was tautological — should-fix, fixed
`values[0][0] == heatmap.values[0][0]` is invariant under transposition, so it
could never have disagreed with the code, while its comment claimed to check
the transpose. The reviewer is right, and this was the only tautological
assertion in the file. Fixed in `1a7b4a1`: an off-diagonal cell, plus an
assertion that the two off-diagonal cells differ.

### B6 to B8, B9 to B13 — nits, all fixed
Cell 8's `else` reaching for `.note` on a possible empty `Group` (`1a7b4a1`,
via `render` testing falsiness first); the live cells assuming `head_table.json`
and `sample.json` exist (`1a7b4a1`, a note now, gated on `LIVE_READY`); the
Target/Distractor round trip (`a4eabab`, with the caveat written into the cell);
hover strings drawn on the bars instead of on hover (`hovertext`, `1a7b4a1`);
the lens's x-axis title being a two-sentence paragraph (`ROW_AXIS`, paragraph
moved to a note); `Series.se` ignored by the renderer (error bands drawn);
duplicated constants (see C5); `dla_heatmap` by position (already A1).

### B14. Checkbox 5 was thin on the Slurm script — fixed
The README gave the sbatch one example line. It now describes the partition,
account, GPU count, memory and time defaults, what they are sized for, where
the logs land, that it must be submitted from the repository root and why, and
what `--dry-run` checks.

---

## C. Independent standards-axis review

### C1. `dla_heatmap` aligned by position — should-fix
Same as A1, already fixed in `9b30968` before the report arrived.

### C2. The sum-to-one note formatted `None` with `:.2g` — should-fix, fixed
A condition whose `checks` key was absent would have raised `TypeError` and
taken the whole attention section down — in the section whose entire job is to
render a note instead of an error. Fixed in `1a7b4a1`: everything goes through
`_number`, which prints "unrecorded" for a missing value, and a test builds a
`patterns.json` with an empty `checks`.

### C3. `Group.__bool__` was used inconsistently — should-fix, fixed
`render()` now tests falsiness before the `Group` branch, and the circuitsvis
cell delegates to `render` rather than reaching for `.note` itself.

### C4. The notebook's dependencies would be installed by the documented command — should-fix, fixed
They sat in `requirements.txt`, which the README tells the reader to
`pip install -r`, so following the README would have pulled circuitsvis's torch
pin into the login-node base environment and moved the torch everything else
runs on. That is a real hazard and the author had not seen it. Fixed in
`1a7b4a1`: `requirements-notebook.txt` holds them, spells out the `--no-deps`
commands and records the verified versions; `requirements.txt` carries a
pointer saying why they are not there; the README points at the new file.

### C5. The duplicated constants were justified by a wrong reason — should-fix, fixed
The comment said importing the analysis modules would pull torch. Checked by
parsing each module's top-level imports: only `attention_patterns.py` imports
torch at module scope. The reviewer also caught that the copied
`component_label` had already drifted from `dla.label_of`. Fixed in `1a7b4a1`:
the subdirectory and file names come from `dla`, `knockout`, `path_patching`
and `head_table`, the label delegates to `dla.label_of`, only
`ATTENTION_SUBDIR` stays spelled out with the narrowed reason, and the unused
`HEAD_TABLE_CSV` is gone. Drift is now impossible rather than merely tested
against.

### C6 to C14 — nits, all fixed
The house docstring header line; the lens axis title and Group subtitle; the
two dead glob filters removed with a comment saying why each pattern is already
exact; `if LIVE_INSTANCE_ID is None` rather than `or`; the overlap test
asserting the specific sentence and adding the overlapping case; the hand-built
head-table fixture going through `head_table.write_head_table` so a schema
change reaches the test; `from __future__ import annotations` in the test file.

### C15. Clean axes
The reviewer found Python 3.9 compatibility, dict ordering, glossary
vocabulary, fixture honesty, test quality, LIVE placement and the README clean.

---

## D. Judgement calls, recorded rather than fixed

1. **Return annotations.** Several view functions are annotated with their
   happy-path type while also returning `Missing`. A union would be honest but
   the module has no runtime type checking, and the name of every such function
   is documented as returning one or the other. Left as is.
2. **Several family files in one cell.** `family_knockout_view` renders the
   first match and now names the others in a note rather than choosing between
   them or concatenating. A cell should not have two, and if one does the
   researcher should see that it does.
3. **No section for `roles/roles.json`.** Ticket 10 writes it, plus
   `roles.reads_group`, `roles.direct_support` and
   `roles.direct_support_honest_instruction`. All of those render as ordinary
   namespaced head-table columns, which is what ticket 11 was asked for. A
   section devoted to the roles payload belongs to whoever owns that schema.
   Carried to ticket 12.

## E. The role-family columns

Raised separately by the orchestrator after both reviews: the family knockout
writes two head-table columns, and ticket 10 is renaming them from
`knockout.family` to `knockout.role_family`. Both spellings are now accepted,
for the same reason both spellings of the role triple are — a namespace settled
after this module was written must not silently blank a column — and the two
columns are ordered right after the role triple, because the family a Component
was grouped into is read with its role rather than twenty columns later among
the rest of the knockout numbers. A cell without them carries a note naming
both spellings. Tested against ticket 10's real `ca10-family` head table (the
current spelling) and against a hand-built one in the renamed spelling.

---

## Checkbox verdicts, after the fixes

| Checkbox | Verdict |
|---|---|
| Every section reads only JSON and CSV; a missing analysis renders a note | met. Thirteen view functions over ten real cells with no exception, an empty-directory fixture for all ten notes, and B4's skipped conditions now visible rather than merely absent |
| circuitsvis and plotly added; the notebook renders them inline | met after B1. `show()` verified working under a notebook renderer in mgnp |
| Live section imports the library, loads the model once, three drill-downs with the CLI's signatures | met. The spec reviewer verified each call against its definition; one model load, no second nnsight path |
| Notebook correctness verified by reading, not execution | met. No agent executed it; the defects the reading missed were found by reading, by two other readers |
| README documents the layout, CLI, Slurm script and notebook | met after B14 |
| Subagent code review completed and findings addressed | met. Both axes reviewed independently, every finding the orchestrator called for fixed, the rest recorded above |
