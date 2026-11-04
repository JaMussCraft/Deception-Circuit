# Spec: weekly PI report for the autoresearch workflow

Date: 2026-11-04. Status: binding for tickets 01 to 04. The template was accepted by the user on 2026-11-04 after
three rounds of review on the 4 November report; the accepted copies are the source for ticket 01.

Short names: **A** is `/projects/beto/swong2/Alignment`; **DC** is its main `Deception-Circuit` checkout; **RS** is
the research-session package at `A/.agents/research_session/`, called as `/u/swong2/.local/bin/research-session`;
**F** is this directory, `DC/docs/research/weekly-report`; **W** is the report directory
`A/project_context/reports/weekly/`.

## 1. Intent

The user presents the week's work to their PI every Wednesday at 3 pm Eastern. The PI is on many projects and wants
the high-level picture: the directions explored in order, each followed by its main finding, where the project
stands and where it is headed, with no code names or execution detail. The recorded research state (the findings
table, the direction handoffs, the live worklogs, the literature survey) holds everything such a report needs, but
in the vocabulary of the sessions. This feature adds a session protocol that turns that state into the report, a
brief assembler so the writer sees the live findings the hook otherwise hides, and a mechanical check for the
vocabulary and structure rules the user enforced by hand during the template review.

## 2. Goals and non-goals

Goals: (1) a weekly-report session can be run from a document, like the synthesis session; (2) the report always has
the accepted structure and never carries a code name, session name, timestamp, path, hardware, cost or methodology
bookkeeping; (3) the writer sees every finding of the window, including those of running sessions that exist only in
`worklog.json`, and every phase of a running direction; (4) prior work and the gap are stated each week from the
literature survey; (5) the checks run on both interpreters, the mgnp environment and the base Python 3.9.

Non-goals: scheduling or any automatic trigger (the user starts the session); prose generation by the tool (the
Opus writer writes, the tool assembles and checks); changing the hook's glue-lint file scope; a Codex adapter beyond
what the bridge generates; any GPU job or paid API call; figures drawn by the tool.

## 3. Deliverables and locations

| # | Deliverable | Location |
|---|---|---|
| a | Session protocol | `A/docs/agents/weekly-report.md`; one line added to the Sessions bullet of `A/.claude/CLAUDE.md` (never `AGENTS.md`, which the bridge regenerates) |
| b | Report template | `DC/docs/research/_templates/weekly-report.md`, byte-identical to the accepted `A/.scratch/weekly-report/TEMPLATE.md` except for the path references in its comments |
| c | Plain-name map | `W/names.md`, from the accepted `A/.scratch/weekly-report/names.md`; a living glossary that the protocol updates each week |
| d | Reports | `W/YYYY-MM-DD.md` with figures in `W/figures/YYYY-MM-DD-figN.png`; the 4 November report is already there |
| e | `research-session weekly-check <file>` | new module `RS/weekly.py`, registered through `add_parsers` like the record modules |
| f | `research-session weekly-collect --since DATE` | same module |
| g | Tests | `A/.agents/tests/test_research_session_weekly.py` with fixtures under `A/.agents/tests/fixtures/weekly/` |

## 4. The protocol (deliverable a)

Written in the style of `synthesis-session.md`: what it is, when to use it, what it produces, words used, numbered
sections. It must say:

1. **Reading.** The synthesis reading list (INDEX, FINDINGS, SESSIONS, DIRECTIONS, worklog heads), then the output of
   `weekly-collect --since <last Wednesday>`, then for every direction in the window its `README.md`, `START.md`
   section 2 and WORKLOG head, then the literature survey `A/project_context/surveys/deception_circuits/SUMMARY.md`
   and `recommendation.md` for the prior-work lines, then last week's report for the carry-over sections. Reports and
   hand-backs are opened only to check a number.
2. **Delegation.** The reading and the writing go to an Opus writer (`model: "opus"`), and an independent Opus
   reviewer gets the collect brief and the draft, never the writer's notes. The reviewer checks that every number
   traces to a finding, a verdict file or the brief, that the depth order matches the importance order, and that no
   code name survives. The Fable-close rule of `research-session.md` applies.
3. **Writing rules**, as the template comments state them, plus: update `W/names.md` first with any direction created
   in the window; at most three tables and three figures; figures are drawn from verdict JSON or the CSV beside an
   existing figure, with the `dataviz` skill invoked before drawing; the "where next" section is the user's plan in
   the user's voice, never a question to the PI (memory `user-decides-advisor-presents`); the "what is already known"
   section cites authors and years, never the internal survey.
4. **Checks**, by hand because the hook's glue lint is scoped by file name: `research-session weekly-check <file>`
   (which also runs the glue lint) must pass before the report reaches the user. `scripts/check_report_numbers.py`
   is **not** run on weekly reports: it resolves numbers against run manifests and reports every rounded value as
   unresolved (67 of 67 on the 4 November report); the reviewer's tracing replaces it.
5. **What it may write.** Only `W/<date>.md`, `W/figures/`, `W/names.md` and the session's own notes. It claims no
   direction, adds no registry row, never edits RS-owned files, and does not register, so it never freezes at a
   checkpoint; the cap pause at 80% of the all-models weekly reading and the stale-reading rule still apply.
6. **Hand-over.** The final message gives the report path, the check output, the numbers the reviewer could not
   trace, and the sections carried over from last week. The user reviews before the report goes anywhere.

## 5. `weekly-check` (deliverable e)

`research-session weekly-check <file> [--names W/names.md] [--directions DC/docs/research/directions.json]
[--max-tables 3] [--max-figures 3]`. Prints `file:line: message` per finding and exits 1 on any finding, 0 otherwise.
Then runs the glue lint and secret scan of `lint.py` on the same file and folds its findings in.

Checks, all outside fenced code and with inline code stripped first:

1. **Headings.** These `##` headings in this order: `TL;DR`, `Where things stood`, `What I explored this week`,
   `What is already known, and the gap we could fill`, `Where the project stands`, `Where we are headed next`.
   `Ongoing work` is optional and, when present, sits between `What I explored this week` and `What is already
   known`. Every direction under `What I explored this week` and `Ongoing work` is a `###` heading. No `####`.
2. **Counts.** At most `--max-tables` tables (a table is a `|` header line followed by a `|---` separator line) and
   at most `--max-figures` images (`![`).
3. **Bullets.** Every list item (`- ` or `* ` after optional indentation) starts with `**<text>:**`.
4. **Vocabulary.** A finding for each match of: finding ids `F-[a-z]+-[0-9]+`; labels `\b[A-Z][0-9]{1,2}\b`
   (experiment labels and rulings) except inside `Table N` and `Figure N`; `\b(EST|EDT|UTC)\b`; clock times
   `\b[0-9]{1,2}:[0-9]{2}\b`; paths (`outputs/`, `docs/`, `.scratch/`, `\.json\b`, `\.py\b`, `\.md\b`, `\.csv\b`);
   hardware and runs (`H200|H100|A100|A40|GPU|Slurm|sbatch|Bridges-2|Delta`, `GPU-hour`, `job id`, `\$[0-9]`);
   commit hashes `\b[0-9a-f]{7,40}\b` when they contain a letter; session ids `\b(claude|codex)-[0-9a-f]{6,}\b`;
   methodology words `frozen bar|pre-regist|ruling|\bR[0-9]+\b|seed\b|seeds\b`; the word `ladder` except in the phrase
   `specificity ladder`; every direction slug in `--directions` as a whole hyphenated word, except `weekly-report`;
   and every entry of the `## Never in the report` section of `--names` that is a literal token (the module reads
   that section, splits on commas, and uses the entries of three characters or more that contain no space as
   additional literal, case-insensitive patterns).
5. **Names.** For every row of the `## Directions` table in `--names`, the slug must not appear (already covered) and
   nothing else is enforced; the map is guidance for the writer.

The check is deterministic, reads no RS state, and needs no session.

## 6. `weekly-collect` (deliverable f)

`research-session weekly-collect --since YYYY-MM-DD [--until YYYY-MM-DD] [--root DC/docs/research]
[--out FILE]`. `--until` defaults to today. Writes Markdown to stdout or `--out`. Reads only the research root and the
Alignment files named below; never writes RS state. It is the sanctioned reader of `worklog.json`, which the hook
refuses to shell commands.

Sections of the output, in this order:

1. **Window and sources.** The dates and the files read.
2. **Directions touched in the window.** One section per direction whose `updated` falls in the window or whose
   status is `claimed` or `active`, ordered by the earliest of (`claimed_at`, first finding `at`, `updated`), with:
   title, slug, status, summary; the `## Question` and `## Verdict` sections of its `README.md` when present (else the
   first 30 lines); for `claimed` or `active` rows the numbered directions item of `START.md` (the section whose
   heading contains "Directions") in full, so every phase of a running direction is visible; the head of
   `WORKLOG.md` above `## Log`; every `worklog.json` finding whose `at` is in the window, as `F<n> | at | strength |
   plain | setup`; every open `need` of `worklog.json` as `N<n> | plain | default`.
3. **Findings table rows** of `FINDINGS.md` whose `date` is in the window, verbatim, grouped by direction.
4. **Registry changes.** Rows added or whose status changed in the window, as far as `updated` shows it.
5. **Fixed pointers.** The literature survey directory, the previous weekly report (the latest `W/*.md` before
   `--until`), and `W/names.md`.

The module uses `records.py`, `registry.py` and `worklog.py` readers where they exist and does not duplicate their
parsers. It never follows `legacy_scratch` or `archive` paths.

## 7. Tests (deliverable g)

`RSTestCase` with temporary roots, as the other suites. Fixtures: a three-row `directions.json` (one `done`, one
`claimed`, one `proposed`), a `FINDINGS.md` with rows inside and outside the window, a `worklog.json` with findings
inside and outside the window and one open need, a `README.md` with Question and Verdict, a `START.md` with a
Directions item, a names map, and three report fixtures: the accepted 4 November report (must pass), a copy with
one planted violation per check (each must be reported with its line), and a copy with four tables (count failure).
Both interpreters: `/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider` and
`/sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider`, with the suite's basetemp. New code is
Python 3.9: no `match`, no `X | Y` annotations, no `list[str]` at runtime without `from __future__ import annotations`.

## 8. Process rules

- Workers never run git. The orchestrator commits by explicit file list: Alignment files on Alignment main, the
  template and this directory's records on DC main, as the synthesis protocol does for `directions.json`.
- Every Markdown file a ticket writes passes `research-session lint` before hand-back; the output is pasted.
- Hand-backs go to `F/reports/<NN>-handback.md` with the five fixed headings of `_templates/handback.md`.
- Ticket 04 runs the whole pipeline once on the 4 November window (`--since 2026-10-28`) and on the 4 November
  report, and fixes the report or the tools until `weekly-check` passes. That run is the acceptance test.

## 9. Rulings

- R1. The name map lives beside the reports, not in `_templates/`, because it grows every week.
- R2. `check_report_numbers.py` is exempt for weekly reports (section 4.4).
- R3. The feature directory is a registered `proposed` row created by `research-session init`, like
  `autoresearch-workflow`; it is never claimed, because no research session runs it.
- R4. `Delta` and `Bridges-2` are forbidden tokens even though Delta is an English word; the check is case-sensitive
  for capitalised cluster names.

## 10. Amendments after the builder check (2026-11-04; these win over §5 and §6 where they differ)

- R5. **Selection (§6.2).** A direction is in the window when its status is `claimed` or `active`, or it has a
  `worklog.json` finding whose `at` date is in the window, or it has a `FINDINGS.md` row whose `date` is in the
  window, or its status is `done` or `paused` and its `updated` is in the window. `proposed` and `abandoned` rows are
  never included, nor is `weekly-report`. Order by the earliest of: first in-window finding `at`, first in-window
  FINDINGS row date, `claimed_at`, `updated`; ties by slug.
- R6. **START directions item (§6.2).** The numbered top-level item whose bold lead is `Directions` (the line
  matches `^\d+\. \*\*Directions\.\*\*`), taken through the line before the next top-level numbered item. There is
  no heading to look for.
- R7. **README sections (§6.2).** Match `##` headings case-insensitively against `question` and `verdict` with an
  optional leading `the`; when neither matches, take the first 30 lines.
- R8. **Needs (§6.2).** Fields are `id`, `at`, `text`, `default`, `answer`, `answered_at`; a need is open when
  `answer` is null; print `N<n> | text | default`.
- R9. **Registry changes (§6.4) is dropped.** `directions.json` has no history; the section would duplicate §6.2.
  The output has four sections: window and sources, directions, findings rows, fixed pointers.
- R10. **Missing names map (§5).** When `--names` is given explicitly and absent, exit 2 with a message. When the
  default path is absent, print one warning to stderr and skip the names-derived literals; the other checks run.
  Ticket 02 tests with the fixture names map.
- R11. **Label exception (§5.4).** The `Table N` and `Figure N` exception is void: the label pattern needs a letter
  immediately followed by a digit, so those never match. All patterns are case-sensitive except the names-map
  literals, which are case-insensitive.
- R12. **Names-map literals (§5.4).** Ticket 01 rewrites the `## Never in the report` section of `names.md` as a
  plain comma-separated list of literal tokens with no quotes, parentheses or prose; the check splits on commas,
  strips whitespace, and uses every entry of three characters or more that contains no space.
- R13. **Headings rule (§5.1), as enforced.** Each of `What I explored this week` and, when present,
  `Ongoing work` contains at least one `###`; there is no `####` anywhere; there is no `###` under any other `##`.
- R14. **Readers (§6).** Use `registry.load_directions_file(root)`, `registry.parse_findings(text)`,
  `state.load_json(path, default)` with `registry.validate_worklog` for `worklog.json`, `worklog.split_log(text)`
  for the WORKLOG head, and `records.from_iso` and `records.read_text`. `worklog._load` is private; do not call it.
- R15. **CLI registration (§5).** `cli.py` holds a hard-coded `RECORD_MODULES` tuple and a top-level import line;
  ticket 02 edits both, one line each. The guarded import of `weekly_collect` catches `ModuleNotFoundError` only
  when `exc.name == "research_session.weekly_collect"`; ticket 04 replaces the guard with a plain import.
- R16. **Fixtures (§7).** Fixture files that mirror RS-owned names are stored under other names (for example
  `worklog-fixture.json`) and copied into temporary roots by test code at run time; nothing named like an RS-owned
  record is checked in under `fixtures/`. Shell commands must not name RS-owned record files (the hook refuses
  them); Python test code may. Pytest runs with
  `--basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-<ticket>-<mgnp|base>`.
- R17. **Template placeholders.** The accepted template's `What I found` placeholder sub-bullets carry bold
  prefixes (`**Main result:**`, `**Caveat:**`) so the template itself passes the bullet rule; done in the accepted
  copy on 2026-11-04.
