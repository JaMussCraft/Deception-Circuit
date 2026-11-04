# Handoff: weekly-report

Status: built. Tickets 01 to 04 are resolved and the 4 November 2026 report passes the check. Written by ticket 04
on 2026-11-04. This is a feature of the autoresearch workflow, not a research direction: no session claims it, and
it runs no GPU job and no paid API call.

## What it is

The user presents the week's work to their PI every Wednesday at 3 pm Eastern. The PI wants the high-level picture:
the directions explored, each with its main finding, where the project stands and where it is headed, with no code
names and no execution detail. The recorded research state holds all of that, but in the sessions' vocabulary.

The feature turns that state into the report in three parts:

- **A session protocol** that an orchestrator follows to read the state, delegate the writing to an Opus writer and
  an independent Opus reviewer, and hand the draft to the user.
- **`research-session weekly-collect`**, a read-only brief assembler. It gathers every direction touched in a window,
  including the live findings and open needs of running sessions that exist only in their worklog JSON, and the
  full phase list of each running direction.
- **`research-session weekly-check`**, a deterministic check of the accepted structure and the forbidden vocabulary,
  which also runs the glue lint and secret scan on the report.

## Where it lives

| What | Path |
|---|---|
| Session protocol | `docs/agents/weekly-report.md` in the Alignment checkout |
| Report template | `docs/research/_templates/weekly-report.md` in this repository |
| Plain-name map | `project_context/reports/weekly/names.md` in the Alignment checkout |
| Reports and figures | `project_context/reports/weekly/YYYY-MM-DD.md` and its `figures/` directory |
| Tool code | `.agents/research_session/weekly.py` and `weekly_collect.py` in the Alignment checkout |
| Tests and fixtures | `.agents/tests/test_research_session_weekly.py` and `.agents/tests/fixtures/weekly/` |
| Spec, tickets, hand-backs | `spec.md`, `issues/` and `reports/` in this folder |

The name map is a living glossary beside the reports (spec ruling R1). Each week's session adds a row for every new
direction and adds new code words to its `## Never in the report` list, a plain comma-separated list of tokens.

## The two commands

`weekly-collect` writes the brief to stdout or to `--out`. `--until` defaults to today and `--root` to this
repository's `docs/research/`. It reads only; it never writes session state.

```
/u/swong2/.local/bin/research-session weekly-collect --since 2026-10-28 \
  --out /projects/beto/swong2/Alignment/.scratch/weekly-report/collect-2026-11-04.md
```

The brief has four sections: the window and the files read; the directions touched in the window, each with its
README Question and Verdict, the Directions item of its START for running rows, its WORKLOG head, its in-window
worklog findings and its open needs; the in-window rows of `FINDINGS.md`; and fixed pointers to the literature
survey, the previous weekly report and the name map.

`weekly-check` prints `file:line: message` per finding. It exits 0 when clean, 1 on any finding and 2 when an input
named explicitly cannot be read. A clean run prints nothing.

```
/u/swong2/.local/bin/research-session weekly-check \
  /projects/beto/swong2/Alignment/project_context/reports/weekly/2026-11-04.md
```

It checks the six required headings in order with the optional ongoing section, at most three tables and three
figures, a bold prefix and colon on every bullet, and the forbidden vocabulary: finding ids, experiment labels,
time zones and clock times, paths, hardware and costs, commit hashes, session ids, methodology words, every
direction slug, and the name map's literal tokens. Fenced code, inline code and HTML comments are skipped.
`--names`, `--directions`, `--max-tables` and `--max-figures` override the defaults.

## How to run a weekly-report session

Follow `docs/agents/weekly-report.md` in the Alignment checkout. In short: read the synthesis list, run
`weekly-collect --since <last Wednesday>`, read each direction in the window and the literature survey, update the
name map, have an Opus writer fill the template and an Opus reviewer trace every number, run `weekly-check` until it
exits 0, and hand the report path and check output to the user. The session claims no direction and writes only the
report, its figures, the name map and its own notes. `scripts/check_report_numbers.py` is not run on weekly reports
(spec ruling R2).

## Known first-week artefact

The 4 November brief lists eleven directions, more than the report covers. Six older done or paused rows have no
finding in the window and appear only because the registry seeding of 31 October and 1 November set or refreshed their
`updated` date, and spec ruling R5 includes a done or paused row whose `updated` falls in the window. Those rows are
component-analysis, format-control, mechanism-analysis, mechanism-datasets, selective-deception and sdr-mechanism.
Two of them, sdr-mechanism and selective-deception, were also wrapped up on those days. The writer skims all six.
The noise ends once 1 November leaves the window, so the 11 November brief will not show them unless they change
again. The autoresearch-workflow row is in the window on its own findings of 31 October, not through the seeding.

The 4 November brief also prints "none before" for the previous report, because the 4 November report is the first
one and the pointer takes the latest report strictly before `--until`.
