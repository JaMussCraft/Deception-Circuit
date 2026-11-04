# 03 — `research-session weekly-collect`

**Status:** resolved
**Type:** task
**Blocked by:** nothing. Runs in parallel with 01 and 02. Writes `RS/weekly_collect.py` only (see ticket 02 for the
registration contract: expose `add_parsers(sub)` registering `weekly-collect`; 02's `weekly.py` imports it).
If 02 has not landed when you finish, also show that `python -m research_session.cli weekly-collect` works through
a temporary registration in your test, without editing `cli.py` or `weekly.py`.
**Estimated size:** reading about 60k tokens (spec §6 to §8; `RS/records.py`, `registry.py`, `worklog.py`,
`findings.py`, `paths.py`; `DC/docs/research/INDEX.md`; one real direction directory such as `instructed-route` for
the shapes of README, START and WORKLOG), writing about 35k tokens.
**Hand-back:** `F/reports/03-handback.md`

## What to do

Implement the brief assembler of spec §6 test-first. It reads the research root and the Alignment report directory
and writes Markdown; it never writes any state.

## Scope

- `RS/weekly_collect.py`: `collect(root, since, until, weekly_dir) -> str` as the pure core and the `weekly-collect`
  subcommand. Reuse the existing readers for `directions.json`, `FINDINGS.md` and `worklog.json`; do not write new
  parsers for files that already have one. Dates compare as `YYYY-MM-DD`; a `worklog.json` `at` timestamp is
  truncated to its date in America/New_York.
- Tests in the shared `test_research_session_weekly.py` (`WeeklyCollectTests`) with fixtures under
  `A/.agents/tests/fixtures/weekly/`: the three-row registry, the findings table, the worklog with findings inside
  and outside the window and one open need, a README with Question and Verdict, a START with a Directions item, and
  a weekly directory with two dated reports.

## Acceptance criteria

- [x] On the fixtures, the output has the five sections of spec §6 in order; the out-of-window finding and the
      out-of-window findings-table row are absent; the running direction's Directions item appears in full; the
      open need appears; the previous report pointer is the latest one before `--until`.
      Verified 2026-11-04 with four sections per R9, which drops registry changes; see `reports/03-handback.md`.
- [x] On the real root with `--since 2026-10-28`, the output names instructed-route, deception-divergence,
      neuron-partition and specificity-ladder, shows neuron-partition's worklog findings F1 to F6 and
      specificity-ladder's START directions item (first 40 lines of the output pasted, the rest summarised).
      This run is read-only; use the installed command, which the hook permits.
      Verified 2026-11-04 with the installed command, after ticket 02 registered it in `cli.py`.
- [x] The whole `A/.agents/tests` suite passes on both interpreters with `-p no:cacheprovider`; failures compared
      by name against main's baseline; output pasted.
      Verified 2026-11-04: 333 passed on both with ticket 02's tests included. The 10 failures are the same
      baseline tests by name, all in the Codex usage-exception suite.
- [x] Python 3.9 syntax throughout.
- [x] Hand-back written with the five headings.
