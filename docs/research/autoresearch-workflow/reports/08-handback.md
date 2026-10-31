# Ticket 08 hand-back: protocol documents and templates

Agent: ticket implementer, Opus. Ticket: `F/issues/08-protocol-docs-and-templates.md`. Status: resolved. Two
acceptance items are deferred by the ticket's own wording until ticket 03 lands (see What is NOT done).

## What changed

Committed by the orchestrator from W (all new files):

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/START.md`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/proposal.md`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/WORKLOG.md`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/RESUME.md`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/handback.md`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/audit.md`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/state.json`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/ledger.json`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/_templates/worklog.json`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/08-handback.md` (this file)
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/08-protocol-docs-and-templates.md` (status and comments)

Staged in S, op file `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/ops/08-protocol-docs.json`, all wave A,
all with `"lint": true`:

- `/projects/beto/swong2/Alignment/docs/agents/research-session.md` (new file, 212 lines).
- `/projects/beto/swong2/Alignment/docs/agents/synthesis-session.md` (new file, 79 lines).
- `/projects/beto/swong2/Alignment/docs/agents/session-audit.md` (new file, 82 lines).
- `/projects/beto/swong2/Alignment/.claude/agents/ticket-implementer.md` (whole-file write with `expect_sha256`
  `6bc1560a0bed05286e410c106036d91d04783edd162ce4914d3e65258c73ebd8`, recorded before staging). The frontmatter and
  the original body are unchanged; a Hand-back section (the five headings and the execution-evidence word rule,
  R25) and a HOLD section (R35) are appended.

Helper scripts in T: `/u/swong2/.claude/jobs/b2cb53cd/tmp/08/check_commands.py` and
`/u/swong2/.claude/jobs/b2cb53cd/tmp/08/check_json.py`.

What the research protocol covers, against the ticket's list: start from START.md; read INDEX, FINDINGS, SESSIONS
and DIRECTIONS first; at least two directions with fallbacks; `claim` on main before branching (R23); `register`
before the first spawn, with the statement that only a registered session freezes (R5); state ownership (spec 5.3);
the worklog triggers and every `worklog-append` kind in one table (R33) with the legibility rules; the two-stage
freeze (spec 5.2, R6) and the R35 turn-end text in the ticket's words; acknowledgement only by the user; the cap
pause; stale readings and `--stale-ok`; Slurm waiters recorded with `job add`, timed out within 60 minutes and
re-armed after compaction; the stall alarm; the milestone trigger; the Fable-close rule as mandatory (spec 5.4); the
hand-back headings and execution-evidence rule (spec 4.7); the science gates (provenance, seeds, frozen grader,
held-out set, number checker); the ask-before list; compaction handling; wrap-up (README, FINDINGS rows, `release`,
`render`, `ledger-rollup`, memory pointer); and a Codex section (codex-usage meter at 25 points, freeze denies only
spawns and `sbatch` per R32, HOLD by the orchestrator's own discipline, lint after every write).

## How verified

Lint of every Markdown deliverable (four staged documents, six Markdown templates, this hand-back and the ticket
file), run again after the final edits:

```
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/.agents/research_session/cli.py lint --summary <the 12 files>
```

Observed: `lint: 12 file(s), clean`, exit 0, no failing units.

Secret scan of the three JSON templates (they go to the public repository):

```
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/.agents/research_session/cli.py lint --secrets-only --summary <the 3 JSON templates>
```

Observed: `lint: 3 file(s), clean`.

Command-name check. The script parses the allowed subcommands, `--kind` values and `job` verbs from spec section 5.6,
cross-checks them against a hard-coded copy, then extracts every `research-session <word>`, `--kind <word>` and
`research-session job <word>` from the 10 Markdown files:

```
/sw/external/python/anaconda3/bin/python3.9 -I /u/swong2/.claude/jobs/b2cb53cd/tmp/08/check_commands.py <spec.md> <the 10 files>
```

Observed, key lines:

```
hardcoded-but-not-parsed (expect empty): []
kinds match hardcoded: True job verbs match: True
OK .../docs/agents/research-session.md commands=['claim', 'findings-check', 'job', 'ledger-rollup', 'lint', 'register', 'release', 'render', 'set-cadence', 'status', 'usage-ack', 'usage-check', 'worklog-append'] kinds=['checkpoint', 'compaction', 'decision', 'entry', 'finding', 'handback', 'incident', 'job', 'need', 'need-resolved', 'switch'] job=['add', 'list', 'update'] unknown=[]
OK .../docs/agents/synthesis-session.md commands=['lint', 'render', 'validate'] unknown=[]
OK .../docs/agents/session-audit.md commands=['audit-scan', 'lint'] unknown=[]
files failing: 0
```

JSON templates parse, carry `"schema": 1`, have exactly the top-level keys of spec 4.4, 4.5 and 4.8, and are
byte-equal to `json.dumps(indent=2, sort_keys=True)` plus a newline (the RS write format):

```
/sw/external/python/anaconda3/bin/python3.9 -I /u/swong2/.claude/jobs/b2cb53cd/tmp/08/check_json.py <state.json> <ledger.json> <worklog.json>
```

Observed: three `OK ... schema=1 canonical=True keys_match_spec=True` lines and `files failing: 0`.

Frontmatter of `ticket-implementer.md`:

```
diff /projects/beto/swong2/Alignment/.claude/agents/ticket-implementer.md /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/tree/projects/beto/swong2/Alignment/.claude/agents/ticket-implementer.md
```

Observed: one hunk, `13a14,45`, additions only. Lines 1 to 13 (frontmatter with `name`, `description`,
`model: opus`, `effort: high`, and the original body) are identical.

Protocol length:

```
wc -l <the three staged protocols>
```

Observed: 212, 79 and 82 lines. Each starts with a five-line summary (what this is, when to use it, and two more
lines).

Dry run of the apply tool:

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging --wave A --only 08 --dry-run
```

Observed:

```
dry run, wave A: 4 op(s) selected from 4
[08#1] write /projects/beto/swong2/Alignment/docs/agents/research-session.md WOULD APPLY: +212 -0 lines, new file
[08#2] write /projects/beto/swong2/Alignment/docs/agents/synthesis-session.md WOULD APPLY: +79 -0 lines, new file
[08#3] write /projects/beto/swong2/Alignment/docs/agents/session-audit.md WOULD APPLY: +82 -0 lines, new file
[08#4] write /projects/beto/swong2/Alignment/.claude/agents/ticket-implementer.md WOULD APPLY: +32 -0 lines
```

The ticket's command used `--staging S --only 08 --dry-run` without `--wave`; the tool requires `--wave`, so the
run adds `--wave A`.

## Execution evidence

Not applicable: no runs. This ticket writes documents only.

## What is NOT done

- `cli.py validate` on the `state.json` and `ledger.json` templates is not run, because ticket 03 has not landed and
  the installed CLI has only `lint`. The structural check above is a stand-in, not a substitute.
- The command-name comparison against `cli.py --help` is not run for the same reason. Only the comparison against
  spec section 5.6 was run.
- Nothing was applied; the orchestrator applies wave A.

## Open questions

1. **Who creates a direction's RS-owned files.** Spec 5.3 makes RS the only writer of `state.json`, `worklog.json`,
   `WORKLOG.md` and `ledger.json`, and the gate refuses hand edits of the first two, but no command in spec 5.6 says
   it creates them from `_templates/`. The protocol says these files "belong to RS". Default: `register` creates
   `state.json` and `ledger.json`, and the first `worklog-append` creates `worklog.json` and `WORKLOG.md`. Tickets 02
   and 03 should confirm.
2. **Ledger reservations.** RS is the only writer of `ledger.json`, but no spec 5.6 command writes reservations,
   caps or API spend; ticket 03's `job add` writes `state.json` only. Default: `job add` also appends the reservation.
   Without one of these, the protocol's ledger rule cannot be followed.
3. **Worklog head fields.** No spec 5.6 option sets `title`, `state`, `right_now`, `terms`, `directions`, `budgets`
   or `transcripts` in `worklog.json`, and the gate refuses hand edits of that file. Ticket 03 needs options for
   them, or the head's Right now block can never change. The protocol does not name any option for them.
4. **Milestone checkpoint.** `--checkpoint N` is tied to the usage count, so the protocol handles a plan-changing
   milestone as a need plus HOLD plus a turn end, with no RS freeze. Say if a real freeze is wanted there.
5. **`session_state` vocabulary.** Spec 4.5 shows only `running`; the template uses it. Ticket 03's validator
   should fix the allowed values.
6. **Codex lint rule.** Ticket 06 has not reported on the `apply_patch` route, so the Codex section says to run
   `research-session lint` after every write unconditionally. If ticket 06 verifies the hook, the sentence still
   holds as a backstop and can stay.
7. **`ticket-implementer.md` description.** Its frontmatter says the agent "commits", which conflicts with this
   feature's no-git rule. It is left unchanged because the ticket requires a byte-identical frontmatter.
8. **Codex adapter.** `ticket-implementer.md` is the source of the generated Codex adapter
   `A/.codex/agents/ticket-implementer.toml`. After wave A applies it, the bridge sync may need a run, as it did for
   ticket 01's three agent-file edits.
9. **Worklog head layout for ticket 03.** Ticket 03 is told to match the head of `F/WORKLOG.md`, which has one
   weekly-usage row. The template head has two rows, all-models and Fable, as spec 5.4 requires. Ticket 03's render
   should match the template head, not `F/WORKLOG.md`.
10. **Wording choices in the docs.** The protocols state end-state rules only. Setup status, such as `audit-scan`
    not yet being installed or the Codex `apply_patch` hook being unverified, is kept here and out of the docs.
