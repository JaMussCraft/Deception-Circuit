# Hand-back 02: the weekly-check command

Agent: ticket implementer, Claude Opus 5.5. Ticket:
`/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/weekly-report/issues/02-weekly-check.md`. Status:
resolved.

## What changed

Committed by the orchestrator on Alignment main, by explicit file list. No worktree was used and no git was run.

- `/projects/beto/swong2/Alignment/.agents/research_session/weekly.py`: new module. It holds the pure core
  `check_report(text, names_text, slugs, max_tables, max_figures)`, the `weekly-check` subcommand, and an
  `add_parsers` that registers `weekly-check` and then imports `weekly_collect` behind the R15 guard.
- `/projects/beto/swong2/Alignment/.agents/research_session/cli.py`: two one-line edits. The top-level import line
  now names `weekly`, and `RECORD_MODULES` ends with `weekly`. No other subcommand changed.
- `/projects/beto/swong2/Alignment/.agents/tests/test_research_session_weekly.py`: a `WeeklyCheckTests` class with
  23 tests, inserted between ticket 03's `WeeklyCollectTests` class and the main guard. Ticket 03's class is
  untouched. My imports use underscore aliases, so the class does not depend on ticket 03's header.
- `/projects/beto/swong2/Alignment/.agents/tests/fixtures/weekly/check/`: four fixtures. Ticket 03 owns the sibling
  `collect/` directory. No file here is named like an RS-owned record (R16). The directions file is written into
  the temporary root by test code.
  - `accepted-2026-11-04.md` is a byte copy of the accepted report.
  - `planted-violations.md` is the accepted report with 16 planted lines, one finding each.
  - `four-tables.md` is the accepted report with a third and fourth table.
  - `names-fixture.md` is the accepted names map with its last section rewritten as a comma list (R12).
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/weekly-report/issues/02-weekly-check.md`: the
  acceptance boxes are ticked.
- This hand-back, which the orchestrator commits on DC main.

These are the design decisions the orchestrator should know about:

- **HTML comments are skipped by every check, like fenced code.** The accepted template states its rules in comments.
  Those comments contain a bare list and the very tokens the check forbids, so R17 holds only if comments are
  exempt. This matches how `lint.split_units` treats comments.
- **Names-map literals match whole tokens.** Each literal must not be flanked by a letter or digit, and matching is
  case-insensitive. A raw case-insensitive substring would flag ordinary words that contain a short literal.
- **Slugs match as whole hyphenated words.** A hyphen or alphanumeric neighbour blocks a match, so a longer slug that
  contains a shorter one is not reported twice.
- **A missing directions file follows R10.** The spec is silent on this case. An explicit path that is absent exits
  2, and an absent default warns on stderr and skips the slug rule.
- **Each span is reported once.** The session-id pattern is tried before the commit-hash pattern, because the hex
  tail of a session id would otherwise be reported as a hash.
- **The heading-order finding points at the first heading out of place.** That is the heading that sits where the
  expected one should be.

## How verified

The accepted report, with the fixture names map and with the defaults. Ticket 01's canonical names map had landed
by the time of the second run, so both runs used a names map.

```
/u/swong2/.local/bin/research-session weekly-check /projects/beto/swong2/Alignment/project_context/reports/weekly/2026-11-04.md --names /projects/beto/swong2/Alignment/.agents/tests/fixtures/weekly/check/names-fixture.md
```

Observed: no output, exit 0.

```
/u/swong2/.local/bin/research-session weekly-check /projects/beto/swong2/Alignment/project_context/reports/weekly/2026-11-04.md
```

Observed: no output, exit 0. The default names map yielded 18 literals, including the benign-task name, the
interchange and knockout words, the model names and the tool words.

The help text, from the installed command:

```
/u/swong2/.local/bin/research-session weekly-check --help
```

Observed: exit 0, with the usage line
`research-session weekly-check [-h] [--names NAMES] [--directions DIRECTIONS] [--max-tables MAX_TABLES] [--max-figures MAX_FIGURES] file`.

The planted copy, from the installed command, with directory prefixes removed:

```
/u/swong2/.local/bin/research-session weekly-check .agents/tests/fixtures/weekly/check/planted-violations.md --names .agents/tests/fixtures/weekly/check/names-fixture.md
```

Observed: exit 1 and one finding per planted line, as follows.

```
planted-violations.md:59: headings: #### heading 'Planted deeper heading'; no #### or deeper headings
planted-violations.md:142: headings: ### heading 'Planted stray direction heading' under 'Where the project stands'; ### headings belong only under 'What I explored this week' and 'Ongoing work'
planted-violations.md:153: bullets: list item does not start with a bold prefix and colon: 'Planted bullet without a bold prefix.'
planted-violations.md:155: vocabulary: finding id 'F-sdr-001'
planted-violations.md:157: vocabulary: label 'B2'
planted-violations.md:159: vocabulary: time zone 'EST'
planted-violations.md:161: vocabulary: clock time '14:05'
planted-violations.md:163: vocabulary: path 'outputs/'
planted-violations.md:165: vocabulary: hardware or run 'H200'
planted-violations.md:167: vocabulary: hardware or run '$3'
planted-violations.md:169: vocabulary: commit hash '4253bb6'
planted-violations.md:171: vocabulary: session id 'claude-0a1b2c3d'
planted-violations.md:173: vocabulary: methodology 'frozen bar'
planted-violations.md:175: vocabulary: methodology 'ladder'
planted-violations.md:177: vocabulary: direction slug 'neuron-partition'
planted-violations.md:179: vocabulary: names-map literal 'Ioi'
```

The four-table copy:

```
/u/swong2/.local/bin/research-session weekly-check .agents/tests/fixtures/weekly/check/four-tables.md --names .agents/tests/fixtures/weekly/check/names-fixture.md
```

Observed: `four-tables.md:110: tables: table 4 exceeds the limit of 3`, exit 1.

Each check of spec sections 5.1 to 5.4 has its own test, all in `WeeklyCheckTests`:

- **Headings:** planted deeper and stray headings; order, missing, duplicate and unexpected headings; the optional
  ongoing section and its placement; a direction section with no subheading.
- **Counts:** four tables fail on the fourth and pass with a limit of four; four figures fail on the fourth.
- **Bullets:** the planted item; star items, nested items, thematic breaks and bold paragraphs.
- **Vocabulary:** all 11 planted families; exemptions for inline code, fences, comments, table and figure numbers,
  the specificity-ladder phrase, the exempt slug, a hex run with no letter, and lower-case words; whole-word slugs;
  R12 parsing; case-insensitive, token-bounded literals.
- **Subcommand:** output format and exit 1; the glue lint and secret scan folded in, with the secret redacted; the
  default names map absent, which warns, and present, which is used; explicit missing inputs exit 2; the default
  directions file absent warns; help from the script and from the installed command; and `weekly-check` still
  registers when the collect module is hidden.

The whole suite, on both interpreters, run from `/projects/beto/swong2/Alignment/.agents`:

```
OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests -p no:cacheprovider -q -rf --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-02-mgnp
OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests -p no:cacheprovider -q -rf --basetemp /projects/beto/swong2/Alignment/.scratch/weekly-report/pytest-02-base
```

| Run | Failed | Passed |
|---|---|---|
| Baseline before any change, mgnp | 10 | 286 |
| Baseline before any change, base | 10 | 286 |
| First run after the change, base | 10 | 333 |
| First run after the change, mgnp | 15 | 328 |
| Final run, mgnp | 10 | 333 |
| Final run, base | 10 | 333 |

On both interpreters the 10 baseline failures are the same test names. They are all in
`test_research_session_cap_exception.py::CapExceptionTests`, and each one raises the same error in `usage.py`,
"cap exception requires a fresh uncached known Codex reading with a future reset". In the final runs both
interpreters fail on exactly those 10 names and no others.

The first mgnp run after the change had five more failures, all in ticket 03's collect tests, with
`argparse.ArgumentError: argument command: conflicting subparser: weekly-collect`. Their test helper added the
collect module to `RECORD_MODULES` whenever it was missing. Under R15 it is never in that tuple, because
`weekly.add_parsers` registers it, so the subcommand registered twice. Python 3.12 rejects the duplicate and
Python 3.9 tolerates it. I told ticket 03, who changed the helper to check the built parser instead. I did not
edit their class. The final runs above were taken after their fix.

Lint of every Markdown file this ticket wrote:

```
/u/swong2/.local/bin/research-session lint /projects/beto/swong2/Alignment/.agents/tests/fixtures/weekly/check/*.md /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/weekly-report/reports/02-handback.md
```

Observed: no output, exit 0.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **The planted fixture has no line for the GPU-hour, job-id, `.json`, `.py`, `.md` or `.csv` variants.** Each
  family is planted once. The other members of each family share the family's one regular expression.

## Open questions

- **Should HTML comments be checked?** I skip them, as decided above. If the orchestrator wants comments in the final
  report checked, the default I would take is to keep skipping them and to have the protocol tell the writer to delete
  the template's comments before hand-over.
- **Is the commit-hash rule too wide?** It flags any word of seven or more letters drawn only from a to f, such as
  "defaced". Nothing in the accepted report hits it. The default I would take is to keep the rule as the spec states
  it and to rephrase a report if a hit ever occurs.
