# Hand-back 01: protocol, template and name map

Agent: teammate t01 (Claude Opus 5.5). Ticket:
`/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/weekly-report/issues/01-protocol-template-names.md`.
Status: resolved.

## What changed

No worktree; all files were written in the primary checkouts. Nothing is staged for the apply tool.

Alignment repository, committed by the orchestrator on Alignment main:

- `/projects/beto/swong2/Alignment/docs/agents/weekly-report.md`, new: the weekly report session protocol, 95 lines,
  six numbered sections mapping to spec section 4 items 1 to 6 (read, delegate, write, check, what it may write,
  hand over). States the R2 ruling with its reason.
- `/projects/beto/swong2/Alignment/project_context/reports/weekly/names.md`, new: copy of the accepted name map with
  the sentence "Updated each week before the report is written.", a short paragraph saying what the check enforces
  by pattern, a `weekly-report` row, and the `## Never in the report` section rewritten per R12 as a plain
  comma-separated list of 18 literal tokens.
- `/projects/beto/swong2/Alignment/.claude/CLAUDE.md`: one line added to the Sessions bullet, "A weekly PI report
  follows `docs/agents/weekly-report.md`." Nothing else touched; `AGENTS.md` not edited.

Deception-Circuit repository, committed by the orchestrator on DC main:

- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/_templates/weekly-report.md`, new: the accepted
  template with `(see names.md)` replaced by `(see project_context/reports/weekly/names.md)`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/INDEX.md`: one bullet added to Protocols.
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/weekly-report/issues/01-protocol-template-names.md`:
  acceptance boxes ticked.
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/weekly-report/reports/01-handback.md`: this file.

## How verified

Lint of every written Markdown file (run from `/projects/beto/swong2/Alignment`, absolute paths):

```
for f in docs/agents/weekly-report.md Deception-Circuit/docs/research/_templates/weekly-report.md \
  project_context/reports/weekly/names.md .claude/CLAUDE.md Deception-Circuit/docs/research/INDEX.md; do
  echo "== $f"; /u/swong2/.local/bin/research-session lint "$PWD/$f"; echo "exit $?"; done
```

Observed: every file printed no findings and `exit 0`. The ticket file and this hand-back were linted afterwards
with the same command and also exited 0 with no findings. Lint is silent on a pass; a negative control file with
a planted OpenRouter-style key printed `neg.md:3: secret: openrouter-key match redacted` and exited 1, so a silent
exit 0 is a real pass.

RS commands the protocol names, against `research-session --help`:

```
grep -o -E 'research-session [a-z-]+' docs/agents/weekly-report.md | sort | uniq -c
```

Observed:

```
      1 research-session lint
      1 research-session tool
      1 research-session usage-check
      1 research-session weekly-check
      1 research-session weekly-collect
```

`lint` and `usage-check` are in `--help`. `weekly-check` and `weekly-collect` are the spec section 5 and 6 commands,
not yet in `--help` until tickets 02 and 03 land. `research-session tool` is the prose phrase "the research-session
tool", not a command. No other RS command is named.

Template against the accepted copy:

```
diff .scratch/weekly-report/TEMPLATE.md Deception-Circuit/docs/research/_templates/weekly-report.md
```

Observed:

```
13c13
<     in "Where things stood" and use the same plain phrase for it everywhere (see names.md).
---
>     in "Where things stood" and use the same plain phrase for it everywhere (see project_context/reports/weekly/names.md).
```

`grep -c names.md` on the accepted template returned 1, so this is the only path reference changed.

Protocol length: `wc -l docs/agents/weekly-report.md` printed 95, under the 120-line limit.

R12 token parsing, simulated in Python: split the `## Never in the report` section on commas, strip, keep entries
of three characters or more with no space. Observed: 18 entries, all 18 used; a case-insensitive substring search
of the accepted 4 November report found no hits, so the list cannot fail the report ticket 04 must pass.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- Nothing in ticket scope is left undone.
- The changed template line is 123 characters, over the 120 used elsewhere. It was left on one line to keep the
  template byte-identical apart from the path change. Line 24 of the name map is 127 characters, inherited
  unchanged from the accepted copy.

## Open questions

- The Never list drops the prose categories the accepted map had (finding ids, labels, timestamps, paths, hardware,
  costs, hashes, session ids, seeds), because the check covers them by regex; the new header paragraph of the name
  map says so. Tokens that would collide with English as case-insensitive substrings were left out, including
  `Delta`, `Bridges-2`, `sample`, `seed`, `job`, `commit` and `ladder`; R4 and the section 5 regexes cover the
  needed ones. Default if no answer: keep the list as is.
- `Slurm`, `sbatch` and `GPU-hours` duplicate section 5 regexes, so ticket 02 may report them twice on one line.
  Default: ticket 02 deduplicates findings per line and pattern, or the duplication is accepted.
