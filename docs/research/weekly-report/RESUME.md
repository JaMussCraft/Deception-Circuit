# Resume: weekly-report

Last rewritten: Wed 4 Nov 2026, 1:15 pm EST by the orchestrator session claude-75658dea (Fable), at the user's
pause after ticket 04 reported.

## Status

The weekly PI report feature is built but not committed. All four tickets are resolved: protocol, template and
name map (01); `weekly-check` (02); `weekly-collect` (03); the acceptance run, README and plain import (04). The
acceptance run passed: `weekly-check` exits 0 on the 4 November report and on the template, the collect brief for
28 October to 4 November shows the ladder phases, the live neuron findings and the survey pointer, and both suites
give 10 failed and 333 passed, the 10 being the baseline cap-exception tests by name. An independent Opus review found no blocking bugs and no writes to RS state, but a
list of evasion holes and false positives in `weekly-check` that still need a fixer pass (see "Open decisions").
The 4 November report is in place at `project_context/reports/weekly/2026-11-04.md` (Alignment) and passes
`weekly-check`.

## Branch, worktree and commit

- Branch: `main` in both repositories; no worktree. Nothing committed yet.
- Alignment files to commit by explicit list: `docs/agents/weekly-report.md`, `.claude/CLAUDE.md`,
  `project_context/reports/weekly/` (2026-11-04.md, figures/2026-11-04-fig1.png, names.md),
  `.agents/research_session/cli.py`, `.agents/research_session/weekly.py`,
  `.agents/research_session/weekly_collect.py`, `.agents/tests/test_research_session_weekly.py`,
  `.agents/tests/fixtures/weekly/`. Do not sweep in the other untracked files of the checkout.
- Deception-Circuit files to commit by explicit list: `docs/research/_templates/weekly-report.md`,
  `docs/research/INDEX.md`, `docs/research/directions.json`, `docs/research/DIRECTIONS.md`,
  `docs/research/SESSIONS.md` (render side effect), `docs/research/weekly-report/` (spec, issues, reports,
  README, RESUME, START and the RS records created by init). The neuron-partition and specificity-ladder record
  changes in the same checkout belong to other sessions; leave them out.

## In-flight jobs

None. No GPU jobs and no paid API calls in this feature.

## Next action

Steps 1 to 3 of the earlier plan are done (Wed 4 Nov 2026, 1:40 pm EST): the acceptance run passed, the nine
review fixes landed test-first (`reports/05-review-fixes-handback.md`; both suites 10 failed and 358 passed, the
10 being the baseline cap-exception names), and the protocol wordings are fixed. The memory note
`weekly-report-design.md` exists with its MEMORY.md line.

1. Commit by file list in both repositories (section above, plus `.agents/tests/fixtures/weekly/` which now holds
   the live name-map fixture, and `reports/05-review-fixes-handback.md`), when the user asks.
2. Set the tickets' `Status:` lines to `resolved`. The registry row stays `proposed` with the init placeholder
   summary: there is no sanctioned command to set a summary (`rs-direction-summary-command` is itself a proposed
   row) and `release` applies to claimed rows only; the README explains the feature's state.

## Do not

- Do not run `check_report_numbers.py` on weekly reports (spec ruling R2).
- Do not edit RS-owned records by hand, and do not name them in shell commands (the hook refuses).
- Do not change the accepted template's structure without the user; the user accepted it on 4 November 2026.

## Open decisions for the user

- Whether to run a weekly-report session at all next week or keep writing the report by hand from the template.
- Whether older done or paused directions that only entered the 4 November window because the registry seeding
  touched their dates should be filtered by a stricter rule (they will not recur in later windows).
