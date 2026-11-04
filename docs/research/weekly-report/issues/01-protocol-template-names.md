# 01 — Protocol, template and name map

**Status:** resolved
**Type:** task
**Blocked by:** nothing. Runs in parallel with 02 and 03.
**Estimated size:** reading about 40k tokens (spec §1 to §4 and §8, `A/docs/agents/synthesis-session.md`,
`A/docs/agents/research-session.md` sections on delegation and the Fable-close rule, the accepted template and
name map, memory `user-decides-advisor-presents.md`), writing about 15k tokens.
**Hand-back:** `F/reports/01-handback.md`

## What to do

Write the weekly-report session protocol, install the accepted template and name map at their canonical locations,
and add the one-line pointer to the project CLAUDE.md.

## Scope

- `A/docs/agents/weekly-report.md`: everything spec §4 lists, in the style and length of `synthesis-session.md`
  (under 120 lines). Name the exact commands: `research-session weekly-collect --since <date>` and
  `research-session weekly-check <file>`. State the no-`check_report_numbers.py` ruling (R2) with its reason.
- `DC/docs/research/_templates/weekly-report.md`: copy of `A/.scratch/weekly-report/TEMPLATE.md`; in its comments,
  replace `names.md` with the path `project_context/reports/weekly/names.md`.
- `A/project_context/reports/weekly/names.md`: copy of `A/.scratch/weekly-report/names.md` with a row added for
  `weekly-report` ("this report process; never mentioned") and the header sentence "Updated each week before the
  report is written."
- `A/.claude/CLAUDE.md`: extend the Sessions bullet with "A weekly PI report follows `docs/agents/weekly-report.md`."
  Touch nothing else in that file. Do not edit `AGENTS.md`.
- `DC/docs/research/INDEX.md`: add `weekly-report.md` to the Protocols list, one line.

## Acceptance criteria

- [x] Every written Markdown file passes `research-session lint`; output pasted.
- [x] The protocol names only RS commands that exist in `research-session --help` or in spec §5 and §6; a grep
      pasted.
- [x] The template is byte-identical to the accepted one apart from the comment path change (diff pasted).
- [x] Hand-back written with the five headings.
