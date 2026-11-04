# Hand-back 04: acceptance run and wrap-up

Agent: teammate t04, Claude Opus 5.5. Ticket:
`/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/weekly-report/issues/04-acceptance-run-and-wrapup.md`.
Status: resolved.

## What changed

No worktree and no git; every file was written in the primary checkouts. Nothing is staged for the apply tool.

Alignment repository, committed by the orchestrator on Alignment main:

- `/projects/beto/swong2/Alignment/.agents/research_session/weekly.py`: the R15 guard is replaced by a plain import.
  `weekly_collect` joins the top-level `from research_session import paths, state` line, and `add_parsers` ends with
  an unconditional `weekly_collect.add_parsers(sub)`. The `try`/`except ModuleNotFoundError` block and its comment
  are gone, and the module docstring no longer says "when that module exists". There is no import cycle, because
  `weekly_collect` imports only `paths`, `records`, `registry`, `state` and `worklog`. Behaviour is otherwise unchanged.
- `/projects/beto/swong2/Alignment/.agents/tests/test_research_session_weekly.py`: ticket 02's
  `test_weekly_check_registers_without_weekly_collect` asserted the guard, which R15 removes; with a plain import it
  would fail. It is replaced by `test_weekly_add_parsers_registers_both_commands`, which builds the real parser with
  no patching and asserts that `weekly-collect --since 2026-10-28` maps to `weekly_collect.cmd_weekly_collect`, that
  `weekly-check x.md` maps to `weekly.cmd_weekly_check`, and that `weekly.weekly_collect` is the collect module. The
  three imports only the old test used (`contextlib`, `io`, `unittest.mock` under underscore aliases) were removed.
  Ticket 03's `cli()` helper is unchanged; its check by subcommand name already tolerates the registration.

Deception-Circuit repository, committed by the orchestrator on DC main:

- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/weekly-report/README.md`: the init placeholder is
  replaced by the handoff, 87 lines. It covers what the feature is, where it lives (protocol, template, name map,
  reports, plus code, tests and this folder), the two commands with one example each, how to run a session, and the
  known first-week artefact.
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/weekly-report/issues/04-acceptance-run-and-wrapup.md`:
  acceptance boxes ticked. The status line stays `open`, as tickets 01 to 03 left theirs, for the orchestrator.
- This hand-back.

Not committed: the regenerated brief `/projects/beto/swong2/Alignment/.scratch/weekly-report/collect-2026-11-04.md`
and the pytest directories `pytest-04-mgnp` and `pytest-04-base` beside it.

Untouched as instructed: `WORKLOG.md` and the session-owned JSON records of this folder, the report, the template and
the name map. Neither the report nor the check needed a fix.

## How verified

The installed wrapper runs the primary source, so the acceptance runs below exercise the edited module:

```
cat /u/swong2/.local/bin/research-session
```

Observed: `exec /sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/.agents/research_session/cli.py "$@"`.

```
for c in weekly-check weekly-collect; do /u/swong2/.local/bin/research-session $c --help >/dev/null; echo "$c --help exit $?"; done
```

Observed: `weekly-check --help exit 0` and `weekly-collect --help exit 0`.

### The collect brief

```
/u/swong2/.local/bin/research-session weekly-collect --since 2026-10-28 --out /projects/beto/swong2/Alignment/.scratch/weekly-report/collect-2026-11-04.md; echo "exit $?"
```

Observed: `exit 0`, 805 lines, eleven directions. The three items the user asked for, quoted with their brief line
numbers.

The specificity ladder's Directions item with its three phases (lines 405 to 408 and 441 to 461, wrapped lines cut):

```
405:### Specificity ladder, pressure-mediating circuits and below-the-head specificity
407:- **Slug:** specificity-ladder
408:- **Status:** claimed; updated 2026-11-01; claimed 2026-11-01T14:08:59-05:00
441:START, Directions item in full:
444:2. **Directions.** Three directions, deliberately open about method. A3 starts only after A1 delivers the control.
445:   - **A1. The control and the ladder.** Build a user-turn transparent inversion condition (the user asks, for
454:   - **A2. Pressure-mediating circuits from a twin corruption.** Train masks whose corruption swaps the pressure
461:   - **A3. Below the head.** Build the probe, direction and feature harness the repository lacks. Fit difference-
```

The neuron-partition live findings from its worklog JSON, ten rows in the window (lines 649 to 650 and 742 to 755,
each row cut at 80 characters):

```
649:- **Slug:** neuron-partition
650:- **Status:** claimed; updated 2026-11-03; claimed 2026-11-03T11:54:20-05:00
742:worklog.json findings in the window (2026-10-28 to 2026-11-04):
746:| F1 | 2026-11-03T12:54:02-05:00 | preliminary | N3: every FAR neuron class
751:| F6 | 2026-11-03T21:31:56-05:00 | preliminary | Pre-registered confirmation (R14): the all-position
752:| F7 | 2026-11-04T11:17:54-05:00 | preliminary | Ablating the honest-only class at size 2,000
755:| F10 | 2026-11-04T12:45:33-05:00 | preliminary | For the 20 strongest neurons by deception score and t
```

The literature survey pointer (lines 801 to 805):

```
## Fixed pointers

- **Literature survey:** /projects/beto/swong2/Alignment/project_context/surveys/deception_circuits
- **Previous weekly report:** none before 2026-11-04 in /projects/beto/swong2/Alignment/project_context/reports/weekly
- **Plain-name map:** /projects/beto/swong2/Alignment/project_context/reports/weekly/names.md
```

Selection, from the Slug and Status lines and the in-window worklog headers of the brief: five directions carry
in-window findings (autoresearch-workflow, instructed-route, specificity-ladder, deception-divergence,
neuron-partition). The other six (component-analysis, format-control, mechanism-analysis, mechanism-datasets,
selective-deception, sdr-mechanism) are done or paused with `updated` on 2026-10-31 or 2026-11-01 and no in-window
finding. They are the first-week artefact the README records.

### weekly-check on the 4 November report

```
/u/swong2/.local/bin/research-session weekly-check /projects/beto/swong2/Alignment/project_context/reports/weekly/2026-11-04.md; echo "exit $?"
```

Observed: no findings, `exit 0`. Nothing was fixed: neither the report wording nor a check rule changed.

Negative control, to show the silent pass is real after the import change:

```
/u/swong2/.local/bin/research-session weekly-check .agents/tests/fixtures/weekly/check/four-tables.md --names .agents/tests/fixtures/weekly/check/names-fixture.md; echo "exit $?"
```

Observed: `.agents/tests/fixtures/weekly/check/four-tables.md:110: tables: table 4 exceeds the limit of 3`, `exit 1`.
The planted-violations fixture with the same names map printed 16 findings, one per planted line, as in hand-back 02.

### weekly-check on the template

```
/u/swong2/.local/bin/research-session weekly-check /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/_templates/weekly-report.md; echo "exit $?"
```

Observed: no findings, `exit 0`. The template passes as it stands, because its rules sit in HTML comments, which the
check skips, and its placeholder bullets carry bold prefixes (R17). The template was not changed.

### Both suites

Run from `/projects/beto/swong2/Alignment/.agents`:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests -p no:cacheprovider -q -rf --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-04-mgnp
OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests -p no:cacheprovider -q -rf --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-04-base
```

Observed, mgnp:

```
FAILED tests/test_research_session_cap_exception.py::CapExceptionTests::test_copy_to_other_session_does_not_exempt
FAILED tests/test_research_session_cap_exception.py::CapExceptionTests::test_five_hour_unknown_and_checkpoint_still_block
FAILED tests/test_research_session_cap_exception.py::CapExceptionTests::test_grant_retains_fresh_cache_for_next_real_hook
FAILED tests/test_research_session_cap_exception.py::CapExceptionTests::test_human_command_and_revoke_use_only_temporary_state
FAILED tests/test_research_session_cap_exception.py::CapExceptionTests::test_meter_drop_same_reset_permanently_expires
FAILED tests/test_research_session_cap_exception.py::CapExceptionTests::test_observed_reset_permanently_expires_even_after_old_reading_returns
FAILED tests/test_research_session_cap_exception.py::CapExceptionTests::test_old_hook_lookup_cannot_overwrite_fresh_grant
FAILED tests/test_research_session_cap_exception.py::CapExceptionTests::test_only_target_codex_weekly_cap_is_exempt
FAILED tests/test_research_session_cap_exception.py::CapExceptionTests::test_real_hook_persists_expiration_and_status_exposes_it
FAILED tests/test_research_session_cap_exception.py::CapExceptionTests::test_unchanged_window_keeps_cadence_and_records_checkpoint
10 failed, 333 passed, 56 subtests passed in 10.38s
```

Observed, base Python 3.9: the same ten failure names in the same order, and `10 failed, 333 passed in 13.02s`.

Every failure raises `ValueError: cap exception requires a fresh uncached known Codex reading with a future reset`
from `research_session/usage.py:276`. These are the ten baseline names of hand-backs 02 and 03. The pass count is
unchanged at 333 because one test was replaced, not added. The replacement test passes on its own on both
interpreters:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest "tests/test_research_session_weekly.py::WeeklyCheckTests::test_weekly_add_parsers_registers_both_commands" -p no:cacheprovider -q --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-04-mgnp
```

Observed: `1 passed in 0.09s` on mgnp. The same command on the base interpreter with its own basetemp gave
`1 passed in 0.13s`.

### Lint

```
/u/swong2/.local/bin/research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/weekly-report/README.md; echo "exit $?"
```

Observed: no findings, `exit 0`. The same command on the ticket file and on this hand-back, run after both were
written, also printed no findings and exited 0. No README line exceeds 120 characters.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **Nothing in ticket scope is left undone.**
- **The cap-exception failures are not fixed.** They are the pre-existing baseline and outside this feature.
- **The closing WORKLOG entry is not written.** It belongs to the orchestrator, as the ticket says.

## Open questions

- **Selection noise.** Ticket 03 asked whether R5 should drop done or paused rows whose only in-window evidence is an
  `updated` date. Default: keep R5 as written; the README records the artefact and it clears after one week.
- **Template check.** The template passes `weekly-check` today. A future template edit that puts a forbidden token
  outside a comment would make it fail. Default: no test pins this, and none is needed unless the template changes.
