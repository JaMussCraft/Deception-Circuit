# 02 — `research-session weekly-check`

**Status:** resolved
**Type:** task
**Blocked by:** nothing. Runs in parallel with 01 and 03; coordinate with 03 only through the shared module file:
02 creates `RS/weekly.py` with `add_parsers` registering `weekly-check`, and 03 adds `weekly-collect` to the same
`add_parsers`. To avoid a write conflict, 02 owns `RS/weekly.py` and 03 writes `RS/weekly_collect.py`, which
02's `add_parsers` imports lazily with a guarded import (if the module is absent, only `weekly-check` registers).
**Estimated size:** reading about 40k tokens (spec §5, §7, §8; `RS/lint.py`, `RS/cli.py` around `add_parsers`,
`A/.agents/tests/_rs_testlib.py`, `test_research_session_lint.py`), writing about 30k tokens.
**Hand-back:** `F/reports/02-handback.md`

## What to do

Implement the structural and vocabulary check of spec §5 test-first, register it in the CLI, and prove it on the
accepted 4 November report.

## Scope

- `RS/weekly.py`: `check_report(text, names_text, slugs, max_tables, max_figures) -> list[(line, message)]` as the
  pure core, and the `weekly-check` subcommand that reads the files, defaults `--names` and `--directions` to the
  paths in spec §3 and §5, runs `lint.py`'s glue lint and secret scan on the same file, prints `file:line: message`
  and exits 1 on any finding.
- `RS/cli.py`: register the module the way the record modules are registered (the loop over modules with
  `add_parsers`); keep the existing subcommands untouched.
- Tests in `A/.agents/tests/test_research_session_weekly.py` (shared file with 03; 02 creates it with a
  `WeeklyCheckTests` class, 03 adds a `WeeklyCollectTests` class) and fixtures under `A/.agents/tests/fixtures/weekly/`:
  the accepted report copied from `A/project_context/reports/weekly/2026-11-04.md`, a planted-violations copy, a
  four-table copy, and a names map.

## Acceptance criteria

- [x] The accepted 4 November report passes with exit 0 (output pasted). If it does not, the hand-back lists each
      finding and says whether the report or the check is wrong; the orchestrator decides.
- [x] Each planted violation is reported with its line number; one test per check in spec §5.1 to §5.4.
- [x] `research-session weekly-check --help` works from the installed command.
- [x] The whole `A/.agents/tests` suite passes on both interpreters with `-p no:cacheprovider`; failures compared
      by name against main's baseline; output pasted.
- [x] Python 3.9 syntax throughout (the base interpreter run proves it).
- [x] Hand-back written with the five headings.
