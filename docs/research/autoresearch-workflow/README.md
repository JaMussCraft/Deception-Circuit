# Handoff: autoresearch-workflow

Status: active until the pilot is done. Setup tickets 01 to 12 are resolved; the pilot has not started. Written by ticket
12 on 2026-10-31.

## Question

Research state lived in prose across memory notes, `.scratch` directories, reports and handoffs, and every safety rule
depended on the orchestrator remembering it. Can the research workflow be made legible and enforced by tools, so that
a fresh session orients in under 30,000 tokens, checkpoints and cap pauses are enforced by hooks in Claude and Codex,
and findings carry provenance?

## What was built

- **The index layer** in `docs/research/`: `INDEX.md` (the reading order and the rules), `FINDINGS.md` (one row per
  claim), the registry `directions.json` with its renders `DIRECTIONS.md` and `SESSIONS.md`, the global `ledger.json`,
  and `_templates/` for new directions. The three orientation files come to about 8,900 tokens (F-arw-002).
- **The research-session tool** (RS): the Python package `.agents/research_session/` in the Alignment checkout, run as
  `research-session` (`~/.local/bin/research-session`). It owns counters, the usage gate, worklogs, ledgers, the
  registry renders, `findings-check` and `audit-scan`. Its tests pass on both interpreters (F-arw-003).
- **Hooks in both tools** (spec section 5.1): installed in the project settings of Alignment and Deception-Circuit and
  in `~/.codex/hooks.json`. Each hook command is a shell guard that exits 0 when the tool is missing or the kill switch
  exists. Only a registered session gets the two-stage checkpoint freeze; every session gets the cap pause.
- **Profiles and protocols**: four Claude launch profiles in `~/.claude/profiles/`, and the protocols
  `docs/agents/research-session.md`, `synthesis-session.md` and `session-audit.md` in the Alignment checkout.
- **Science guards** in Deception-Circuit: `run_manifest.py` writes a commit-stamped provenance file per run,
  `evaluation/grader_hash.py` freezes the grader, `scripts/check_report_numbers.py` checks that report numbers
  resolve, and `docs/research/held-out.md` with `held_out.json` sets the held-out policy (F-arw-005).
- **Migration**: the Markdown of four closed `.scratch` directions was copied into `docs/research/<direction>/scratch-copy/`,
  and the byte-for-byte archive moves wait for wave B (F-arw-006).
- **Staging and apply**: `tools/apply_staged.py` applies staged files and op lists by wave, with backups, journals
  and rollback. Ticket 12 gave it a dry run that carries planned state forward, a cross-device move, the `absent`
  guard, and a skip for writes that an earlier run already applied (F-arw-007, F-arw-008).

## Where it lives

| What | Path |
|---|---|
| Spec and rulings R1 to R40 | `spec.md` in this folder |
| Tickets and hand-backs | `issues/` and `reports/` in this folder |
| Merge and apply checklist | `merge-checklist.md` in this folder |
| Pilot steps | `pilot-checklist.md` in this folder, direction `pilot-hooks` |
| Apply tool, migration script, smoke test | `tools/` in this folder |
| RS package and tests | `/projects/beto/swong2/Alignment/.agents/research_session/` and `.agents/tests/` |
| Staging root, durable copy | `/u/swong2/.claude/research-session/staging-20261031/` |
| Backups and journals of every apply | `/u/swong2/.claude/research-session/backups/` |
| Kill switch | `touch /u/swong2/.claude/research-session/DISABLED` |
| Orchestrator transcript | `/u/swong2/.claude/projects/-projects-beto-swong2-Alignment/b2cb53cd-c11d-4cbf-9980-27c9ca779b04.jsonl` |

The orchestrator's subagent transcripts are under
`/u/swong2/.claude/projects/-projects-beto-swong2-Alignment-Deception-Circuit--claude-worktrees-autoresearch-workflow/b2cb53cd-c11d-4cbf-9980-27c9ca779b04/subagents/`.
Run `research-session audit-scan` on the main transcript to count its compactions, failed runs and model omissions.

## How to use it

1. A new research session starts from a filled `_templates/START.md` and follows `docs/agents/research-session.md`:
   claim the direction, create its records with `research-session init <slug>`, register with
   `research-session register <slug>`, and write the worklog only through `research-session worklog-append`.
2. A synthesis session follows `docs/agents/synthesis-session.md` and may add only `proposed` rows.
3. An audit of a finished session follows `docs/agents/session-audit.md` and starts with `research-session audit-scan`.
4. To turn every hook off at once, create the kill-switch file above; delete it to turn them back on.

## What is open

- **The pilot.** The hooks have passed the smoke test but have not been observed in a live session. The steps are in
  `pilot-checklist.md`; this direction stays `active` until they are done.
- **Waves B, C and D** are staged but not applied. Wave B needs the Deception-Circuit merge, wave C needs the user's go
  for Codex, and wave D needs the user's confirmation that the live Codex session is finished.
- **Follow-ups** are `proposed` rows in `directions.json`: the held-out scoring guard, a Codex writing profile, the
  test thread limit, rubric files in the grader hash, section numbers in the report checker, the Opus compaction
  window, an audit rule for hook denials, a summary-setting command, legacy ledger totals and the Codex shell-write
  lint.
