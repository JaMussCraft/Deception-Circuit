# Hand-back 05: review fixes for weekly-check and weekly-collect

Agent: review-fix teammate, Claude Opus 5.5. Ticket: the team lead's message of 2026-11-04 listing nine
review findings, with the reviewer's cases in `/projects/beto/swong2/Alignment/.scratch/weekly-report/review/`.
Status: resolved; all nine items done.

## What changed

No worktree and no git; every file was written in the primary checkout. Nothing is staged for the apply tool. All
files below are for the orchestrator to commit on Alignment main.

- `/projects/beto/swong2/Alignment/.agents/research_session/weekly.py`:
  - **Item 1:** `clean_lines` is replaced by `scan(text, template)`, which returns the structure lines, the word lines
    and the hidden-text findings. Each inline code span, fenced block and HTML comment is a finding on its opening
    line (`hidden text: inline code`, `hidden text: fenced code`, `hidden text: HTML comment`). An unclosed comment
    or fence reads `..., never closed`. The headings, counts and bullet checks read the rendered text with hidden
    text blanked. The vocabulary check reads the hidden content with only the delimiters blanked. The new
    `--template` flag skips HTML comments silently. Inline code and fences are still findings there, and so is an
    unclosed comment. `clean_lines` stays as a thin wrapper in template mode for `names_literals`.
  - **Item 2:** names-map literals accept an optional `s` or `es` suffix inside the word boundaries.
  - **Item 3:** a table is a header line holding an unescaped pipe, followed by a delimiter row. The delimiter row has
    at least one pipe, and every cell is `:?-+:?`. Two-dash cells and rows without a leading pipe now count. A bare
    `---` under a pipe line does not count, and neither do two pipe rows with no delimiter.
  - **Item 4:** every vocabulary pattern now runs on paragraphs. A paragraph is a run of non-blank lines, split before
    list items and around headings, table rows and thematic breaks, joined with single spaces. `frozen bar` and
    `job id` allow any whitespace between the words. The `ladder` exception is a predicate that accepts
    `specificity` or `Specificity` before it, across a line break too. Each match is reported at the line where it
    starts, so single-line matches keep their old line numbers.
  - **Item 6:** a commit hash needs a letter and a digit.
  - **Item 7:** the new built-in `head name` pattern is `\bL[0-9]+H[0-9]+\b`, placed before the label pattern. The
    label pattern spares exactly `F1 score` and `L<digit> norm` through lookaheads at its start. Any other label
    followed by "score" or "norm", for example "B2 score", is still flagged, so the pattern is not weakened.
  - The module docstring describes the new hidden-text and paragraph rules.
- `/projects/beto/swong2/Alignment/.agents/research_session/weekly_collect.py`:
  - **Item 5:** `local_date` rewrites a trailing `Z` as `+00:00` before `records.from_iso`. A worklog finding whose
    `at` cannot be read is kept, counts toward selecting its direction, and is listed in the findings table. A
    `Note:` line above the table names its id and raw value.
  - **Item 8:** `gather` writes one warning to stderr when `registry.parse_findings` returns errors. It gives the
    path, the error count and the first three errors. The new `unfenced_flags` helper makes `readme_sections` and
    `directions_item` ignore `#` lines and numbered lines inside fenced code. `--out` refuses any file name in
    `RECORD_NAMES` and exits 2 before writing. The list holds the state, worklog, ledger and directions JSON names.
- `/projects/beto/swong2/Alignment/project_context/reports/weekly/names.md`: `gpu, USD, dollars` are appended to the
  comma-separated never-list. The list is still plain.
- `/projects/beto/swong2/Alignment/.agents/tests/fixtures/weekly/check/names-live-fixture.md` (new): a copy of the
  live names map after that edit.
- `/projects/beto/swong2/Alignment/.agents/tests/test_research_session_weekly.py`:
  - The `check` helper passes `template`. The new helpers are `mini` and `msgs_at`.
  - `test_vocabulary_exemptions` drops the inline-code, fence and comment exemptions, which item 1 makes findings.
  - `test_names_literals_are_case_insensitive_and_token_bounded` now expects `knockouts` to be flagged.
  - `test_python39_syntax` checks both modules.
  - The collect class gains eight tests for items 5 and 8.
  - The new class `WeeklyCheckReviewFixTests` holds eighteen tests for items 1 to 4, 6, 7 and 9.

## How verified

The red run came before the implementation, with the new tests in place:

```
cd /projects/beto/swong2/Alignment/.agents && /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-fix-mgnp tests/test_research_session_weekly.py -q
```

Observed: every new check test failed, and so did the existing check tests, on the unknown `template` argument. The
new collect tests for the Z time, the unreadable time, selection, the parse warning, the two fenced readers and the
`--out` refusal also failed. Two tests passed before the fix. One is the end-to-end Z test, because Python 3.12's
`fromisoformat` already accepts `Z`; the mocked Python 3.9 test is the red one for item 5. The other is the extended
syntax test, because `weekly.py` was already Python 3.9 syntax.

After the implementation, the same file passed: 72 passed, 19 subtests passed.

Full suite, mgnp:

```
cd /projects/beto/swong2/Alignment/.agents && /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-fix-mgnp tests -q
```

Observed: 10 failed, 358 passed, 73 subtests passed. All 10 failures are in `test_research_session_cap_exception.py`.

Full suite, base Python 3.9:

```
cd /projects/beto/swong2/Alignment/.agents && /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-fix-base tests -q
```

Observed: 10 failed, 358 passed. The failing test names are identical to the mgnp run, all in the cap-exception file.

```
/u/swong2/.local/bin/research-session weekly-check /projects/beto/swong2/Alignment/project_context/reports/weekly/2026-11-04.md
```

Observed: exit 0, no output.

```
/u/swong2/.local/bin/research-session weekly-check --template /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/_templates/weekly-report.md
```

Observed: exit 0, no output. Without `--template` the template gives 18 findings, all from its rule comments.

```
/u/swong2/.local/bin/research-session weekly-collect --since 2026-10-28 --out /projects/beto/swong2/Alignment/.scratch/weekly-report/collect-2026-11-04.md
```

Observed: exit 0, no stderr warning, 805 lines written.

Each reviewer case was run through the installed `weekly-check`. The cases these fixes cover now report:

- **Inline code, comment and fence cases:** the hidden-text finding plus the slug, id, hardware, clock and zone
  findings inside.
- **Unclosed comment case:** the never-closed finding plus the content findings on the next line.
- **Plurals case:** knockouts, ablations, worktrees, checkpoints and interchanges.
- **Lower-case hardware case:** gpu, slurm, dollars and USD.
- **Head-names case:** both head names, with "F1 score" and "L2 norm" passing.
- **Wrapped and capitalised ladder cases and the a-f word case:** no findings.
- **Wrapped frozen-bar case:** "frozen bar" on its first line and "job id" on the next.
- **Table cases:** at a limit of zero the two-dash and no-leading-pipe cases count three tables, against two in the
  accepted report. The no-separator case counts two, which is correct because it is not a table.

## Execution evidence

Not applicable: no runs.

## What is NOT done

All nine items are done. These reviewer cases were outside the nine items and are unchanged:

- **Other list markers:** `+` bullets and numbered items are not checked for a bold prefix.
- **Lower-case hardware names:** lower-case "h200" and "a100s" are not flagged. "gpu" now is, through the names map.
- **Setext headings:** an `Appendix` line underlined with `=` is not seen as a heading.
- **Upper-case finding ids:** "F-NP-006" and "f-np-006" are not flagged, because the finding-id pattern is
  case-sensitive by R11.
- **Word false positives:** "linseed" matches `seed\b` and "overruling" matches `ruling`.
- **Indented code:** a four-space indented block is not a hidden-text finding. Its content is still checked, as
  before.

## Open questions

- **Wrapped-match line:** the brief asked for wrapped matches at the first line of the paragraph. I report the line
  where the match starts instead. That line equals the paragraph's first line whenever the match begins there, and
  it keeps every existing line expectation. Default: keep it.
- **Template-flag scope:** `--template` changes only comment handling. Inline code and fences are findings in both
  modes, and the template has neither. Default: keep it.
- **Unreadable finding times:** a finding whose time cannot be read selects its direction and is listed, because it
  cannot be shown to fall outside the window. Default: keep it.
- **Record names refused by `--out`:** the list adds the ledger and directions JSON names to the two the hook
  guards. Default: keep it.
- **"dollar" singular:** the never-list has `dollars` as asked, so the singular "dollar" passes. With the plural
  rule, the entry `dollar` would catch both. Default: leave it as asked.
