# Hand-back 03: the weekly-collect brief assembler

Agent: teammate t03 (Claude Opus 5.5). Ticket:
`/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/weekly-report/issues/03-weekly-collect.md`.
Status: resolved. Ticket 02 landed its `cli.py` registration while this ticket was finishing, so the final
acceptance run used the installed command.

## What changed

No worktree; all files were written in the primary Alignment checkout. Nothing is staged for the apply tool. The
orchestrator commits these on Alignment main:

- `/projects/beto/swong2/Alignment/.agents/research_session/weekly_collect.py`, new. It holds the pure core
  `collect(root, since, until, weekly_dir, survey_dir=None) -> str` and `add_parsers(sub)`, which registers
  `weekly-collect --since --until --root --out`. It never imports `weekly`, so ticket 02 can import it.
- `/projects/beto/swong2/Alignment/.agents/tests/test_research_session_weekly.py`, new, with the `WeeklyCollectTests`
  class only (23 tests). Ticket 02 appends its own class.
- `/projects/beto/swong2/Alignment/.agents/tests/fixtures/weekly/collect/`, new, with ten fixture files. They are
  `directions-fixture.json`, `table-fixture.md`, `worklog-fixture.json`, `readme-fixture.md`,
  `readme-nosections-fixture.md`, `start-fixture.md` and `worklog-head-fixture.md`, plus `reports/2026-10-21.md`,
  `reports/2026-10-28.md` and `reports/names.md`. No file is named like an RS-owned record (R16). The tests copy
  them into the temporary root under the real names. The subdirectory keeps them apart from ticket 02's fixtures.

Not committed: the real-root brief `/projects/beto/swong2/Alignment/.scratch/weekly-report/collect-2026-11-04.md`,
the driver `/projects/beto/swong2/Alignment/.scratch/weekly-report/run_collect_03.py` used before 02 landed, and the
pytest temporary directories under `/projects/beto/swong2/Alignment/.scratch/weekly-report/`.

Behaviour, as built:

- **Sections.** The output has four sections per R9, which wins over the ticket's "five sections": window and
  sources, directions touched in the window, findings table rows in the window, and fixed pointers.
- **Selection and order.** Selection and order follow R5. Dates are inclusive at both ends. Worklog `at` and
  `claimed_at` values are truncated to their America/New_York date with `records.from_iso`.
- **Embedded files.** README sections, the START Directions item and the WORKLOG head are reproduced verbatim inside
  a Markdown fence longer than any backtick run in the text. Their own headings therefore never compete with the
  brief's headings.
- **Unusable worklogs.** A worklog that fails `registry.validate_worklog` or is not valid JSON gets a one-line note
  under its direction, and the brief continues.
- **Readers.** The module uses only the readers named in R14. It never reads `legacy_scratch`, `archive` or worktree
  paths.
- **Previous report.** The pointer is the latest dated report strictly before `--until`.
- **Exit codes.** A malformed date, `--since` after `--until`, or a missing or invalid registry exits 2 with a
  message on stderr.

## How verified

Baseline of the untouched suite, run before any file was written:

```
cd /projects/beto/swong2/Alignment/.agents
/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests -p no:cacheprovider -q --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-03-mgnp
/sw/external/python/anaconda3/bin/python3.9 -m pytest tests -p no:cacheprovider -q --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-03-base
```

Observed: 10 failed and 286 passed on each interpreter. All ten failures are in
`test_research_session_cap_exception.py::CapExceptionTests`, with "cap exception requires a fresh uncached known Codex
reading with a future reset".

The new tests were red first: 23 failed before `weekly_collect.py` existed. After the module was written, three tests
failed. Two were test helpers that counted headings inside fenced blocks. The third expectation was wrong: R5 orders
by the earliest date including `updated`, so the open row updated on 2026-10-01 sorts before the paused row updated
on 2026-10-28. The test now asserts the R5 order. Final run on both interpreters:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_research_session_weekly.py -p no:cacheprovider -q --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-03-mgnp
/sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_research_session_weekly.py -p no:cacheprovider -q --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-03-base
```

Observed: 23 passed on each.

Whole suite after the change, same two commands as the baseline, first before ticket 02 landed and then after:

```
before 02, mgnp: 10 failed, 309 passed, 54 subtests passed in 9.26s
before 02, base: 10 failed, 309 passed in 11.71s
after 02, mgnp: 10 failed, 333 passed, 56 subtests passed in 10.72s
after 02, base: 10 failed, 333 passed in 12.36s
```

Observed: each time the failure names were diffed against the baseline, and they are identical on both
interpreters. My 23 tests account for the rise from 286 to 309, and ticket 02's tests for the rest.

The CLI tests register `weekly-collect` only when the built parser lacks that subcommand. The check is by name, not
by module in `RECORD_MODULES`, because 02 registers it through its own module, and Python 3.12 argparse refuses a
second registration. The 47 tests of the shared file pass on both interpreters with 02's registration in place.

Python 3.9 syntax: the base run imports and runs the module under Python 3.9, and
`test_python39_syntax` parses it with `ast.parse(feature_version=(3, 9))`.

What the fixture tests check, one test each unless noted:

- **Structure.** The four sections appear in order and there is no `####` heading outside fences.
- **Selection.** The proposed row is absent, and the claimed row comes before the done row by R5's earliest date.
  A separate test covers open, paused, done, abandoned, active and `weekly-report` rows, and ties break by slug.
- **README.** The Question and Verdict sections appear, with an optional leading "the" and a subsection kept. Text
  outside both sections is absent. A README without either section gives its first 30 lines, so line 30 is present
  and line 31 is absent.
- **START.** The running row's Directions item appears in full, with indented sub-bullets, a wrapped line and a
  blank line inside it. The Goal item and the item after it are absent, and the done row's START is not shown.
- **WORKLOG.** The head appears and the Log body is absent.
- **Worklog findings.** The New York date decides the window. A finding at 02:30 UTC on the since day is the
  previous evening in New York and is absent. A finding at 01:00 UTC on the day after until is in the window and
  present. A finding before the window is absent.
- **Needs.** The open need is printed as `| N1 | text | default |` and the answered need is absent.
- **Findings rows.** The in-window rows of the findings table appear verbatim, including an escaped pipe, grouped
  by direction. The out-of-window row is absent, and the proposed row's in-window row is still listed.
- **Pointers.** The previous report is `2026-10-28.md`, and adding reports dated on and after `--until` does not
  change it. A directory with no dated report prints "none before".
- **Read-only.** A snapshot of every file's size and modification time under the temporary tree is unchanged after
  `collect` and the CLI run. `--out` writes the same text that stdout gives.
- **CLI.** `--until` defaults to today under a fixed clock and `--root` defaults to the research root. Bad dates and
  a missing registry exit 2.
- **Robustness.** An invalid or non-JSON worklog is noted and the brief continues. Missing files are reported.
  Paths under `legacy_scratch` and `archive` are never read.

Real-root acceptance run. It is read-only. It first went through `cli.main` with a temporary registration, using
the driver in `.scratch/weekly-report/run_collect_03.py`. After 02 landed it was repeated with the installed command:

```
/u/swong2/.local/bin/research-session weekly-collect --since 2026-10-28 --out /projects/beto/swong2/Alignment/.scratch/weekly-report/collect-2026-11-04.md
```

Observed: exit 0 and 805 lines. The first 40 lines are identical to the earlier driver run. Later lines differ only
where live worklog heads were updated between the two runs. The first 40 lines of the output:

```
# Weekly collect brief, 2026-10-28 to 2026-11-04

## Window and sources

- **Window:** 2026-10-28 to 2026-11-04, both days included; worklog times are read as America/New_York dates.
- **Research root:** /projects/beto/swong2/Alignment/Deception-Circuit/docs/research
- **Directions in the window:** autoresearch-workflow, component-analysis, format-control, mechanism-analysis, mechanism-datasets, selective-deception, instructed-route, sdr-mechanism, specificity-ladder, deception-divergence, neuron-partition
- **Files read:**
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/directions.json
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/FINDINGS.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/worklog.json
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/worklog.json
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/instructed-route/worklog.json
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/deception-divergence/worklog.json
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition/worklog.json
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/README.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/WORKLOG.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/mechanism-analysis/README.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/selective-deception/README.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/instructed-route/README.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/instructed-route/WORKLOG.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/sdr-mechanism/README.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/README.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/START.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/WORKLOG.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/deception-divergence/README.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/deception-divergence/WORKLOG.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition/README.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition/START.md
  - /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition/WORKLOG.md

## Directions touched in the window

### Setting up the autoresearch workflow

- **Slug:** autoresearch-workflow
- **Status:** done; updated 2026-11-01
- **Summary:** Builds the findings index, the research-session tool, hooks, profiles, protocols and provenance guards, and runs no GPU jobs.
- **Directory:** /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow
```

Summary of the rest of the output:

- **Directions.** There are eleven, and the four the ticket requires are among them. Instructed-route is done,
  deception-divergence is paused, and neuron-partition and specificity-ladder are claimed.
- **Neuron-partition.** Its worklog findings table lists F1 to F10. F1 to F6 are dated 3 November and F7 to F10
  are dated 4 November. It has no open need.
- **Specificity-ladder.** Its README falls back to the first 30 lines, because it has no Question or Verdict
  heading. Its START Directions item is shown in full, with the A1, A2 and A3 phases. Neuron-partition's
  Directions item is shown in full as well.
- **Other directions.** Instructed-route and deception-divergence show their Question and Verdict sections.
  Deception-divergence shows its open needs.
- **Validation.** Every real worklog validated, so no note was printed.
- **Findings rows.** The table section groups the in-window rows of autoresearch-workflow (eight rows dated
  2026-10-31), deception-divergence (nine) and instructed-route (eight).
- **Pointers.** The survey directory and the names map exist. The previous report is "none before 2026-11-04",
  because the only dated report is 2026-11-04 itself.

## Execution evidence

- Job id and cluster: no Slurm job. The installed command ran locally on the Delta login node, as shown above.
- Exit code or Slurm state: 0.
- Row counts: 805 lines of output, with 11 directions selected. Neuron-partition has 10 worklog findings in the
  window, and 25 findings table rows are in the window across three directions.
- Baseline reproduces: not applicable, because the brief has no numeric baseline. The test baseline reproduces with
  10 failures before and 10 after, identical by name.
- Provenance file: not applicable, because this is a read-only text assembly with no run manifest.

## What is NOT done

- **Selection is wider than the four directions.** R5 includes every done or paused row whose `updated` falls in
  the window. Seven older rows were last updated on 2026-10-31 or 2026-11-01 by the registry seeding, so they
  appear too: sdr-mechanism, selective-deception, mechanism-analysis, mechanism-datasets, component-analysis,
  format-control and autoresearch-workflow. The tool follows R5 literally and does not narrow it.
- **No previous report on 4 November.** With `--until` 2026-11-04, the pointer prints "none", because the 4
  November report is not strictly before `--until`. A run for 11 November will point at it.

## Open questions

- **Selection noise.** Should R5 exclude done or paused rows whose only in-window evidence is an `updated` date,
  when they have no in-window finding? This would drop the seven seeded rows. Default: keep R5 as written. Ticket 04
  and the writer skim them, and the noise ends once 2026-10-31 leaves the window.
- **Brief length.** The WORKLOG head already holds the rendered findings register, so the worklog findings appear
  twice, once in the WORKLOG head and once as the worklog findings table of section 6.2. Default: keep both as the
  spec asks. The table is the one that applies the window.
