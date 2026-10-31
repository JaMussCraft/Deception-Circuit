# 03 — RS records: registry, renders, worklog, jobs, findings-check

**Status:** ready-for-agent
**Type:** task
**Blocked by:** 02 (shared `cli.py` and `state.py`)
**Wave:** A
**Estimated size:** reading about 60k tokens (spec §4 including §4.8, §5.3, §5.4, §5.6, §6.3, §6.5, R15-R17,
R22-R23, R29, R33; lane 4 §1 template and checkpoint block; lane 3 §4 schemas; `F/WORKLOG.md`), writing about 100k.
**Hand-back:** `F/reports/03-handback.md`

## What to do

Implement the RS commands that own the research records: schema validation, the rendered views, claims, the
structured worklog writer with the checkpoint block, the Slurm job list, and the findings gates.

## Facts to build on

- Worklog template and checkpoint block: lane 4 §1 (header table, Right now, Terms, Needs from you, Findings
  register, Process incidents, Log). The worklog in use is `F/WORKLOG.md`; match its format.
- Two legacy ledger styles for later conversion: `A/.scratch/mechanism-analysis/compute-ledger.json` and
  `DC/outputs/_studies/selective-deception/study/compute-ledger.json` (lane 3 P4). Read their key names only.
- Times: America/Chicago computed with `zoneinfo` (available on Python 3.9). DST ends 1 November 2026 (R22).
- Existing provenance field names: `W/scripts/sdr_routing_pilot.py:392-403`.

## Scope

Staged in S (relative to `S/tree/projects/beto/swong2/Alignment/.agents/`):
- `research_session/registry.py`: validators for `directions.json` (§4.2, `claimed_by` as `<tool>-<8 hex>` per
  R29), ledger (§4.4), `state.json` (§4.5), `worklog.json` (§4.8),
  the FINDINGS table (§4.1) and `held_out.json` (§6.4); `render` for `DIRECTIONS.md` and `SESSIONS.md` (§4.3);
  `ledger-rollup`; `claim <slug>` and `release <slug> --status` (R23; they edit `directions.json` under a `--root`
  that defaults to `DC/docs/research`).
- `research_session/worklog.py`: `worklog-append` with every kind and option of spec §5.6, keeping the structured
  fields in `<dir>/worklog.json` (spec §4.8, R33). On every call it regenerates everything above `## Log` (the header
  table with State, Directions, Started and last updated, compactions from `state.json`, weekly usage with both the
  all-models and the Fable rows, checkpoints acknowledged, budgets and open needs; then Right now, Terms, Needs from
  you, Findings register and Process incidents) and leaves everything after `## Log` byte-identical except for the
  appended entry. `finding` allocates the next F#, adds a register row and logs an entry; `need` allocates the next N#
  with its default-if-no-answer clause; `need-resolved --id N# --answer` renders that need struck through with the
  answer and time and logs an entry; `incident` allocates the next P#, adds a row and logs an entry; `--checkpoint N`
  writes the checkpoint block of lane 4 §1 and sets that freeze to `recorded`. It updates `last_worklog_entry_at`
  and lints its whole output before an atomic replace. Times use `%-I:%M %p %Z` in America/Chicago with lower-case
  `am` and `pm`; day headings are `### <Weekday> <D> <Month> <YYYY>` (match `F/WORKLOG.md`).
- An importer, `worklog-append <dir> --import`, that builds `worklog.json` from an existing hand-written WORKLOG.md in
  the lane 4 format (used once on `F/WORKLOG.md` by the orchestrator, then RS owns it). It refuses if the result does
  not regenerate the same head text apart from whitespace, and reports the differences.
- `research_session/jobs.py`: `job add|update|list` on `state.json` `jobs`, printing the waiter command
  (an `until sacct ...; do sleep 300; done` loop with an explicit timeout of at most 60 minutes).
- `findings-check [--paper DRAFT]` implementing §6.5 and the grader check of §6.3; it accepts legacy `manifest.json`
  with `git_commit` as a warning (R2).
- `validate <path>...` dispatching on file name.
- Tests: `tests/test_research_session_registry.py`, `test_research_session_worklog.py`,
  `test_research_session_findings.py`, with fixture trees built in temporary directories.
- `S/ops/03-rs-records.json`.

## Acceptance criteria

- [ ] Validators reject each malformed case they guard (bad status, missing field, unknown key, duplicate F-id,
      a `verified` row with no provenance, `claimed_by` in the wrong format) and accept the examples in spec §4.
- [ ] `render` is byte-stable: a second run over unchanged input changes nothing (test asserts equal bytes).
- [ ] `render` handles a claimed direction whose `state.json` does not exist yet (the `autoresearch-workflow` row will
      be exactly that in ticket 05): the SESSIONS row shows "no state yet" instead of failing.
- [ ] A test asserts `zoneinfo.ZoneInfo("America/Chicago")` loads (the planner confirmed it does on both
      interpreters on 2026-10-31).
- [ ] `claim` refuses a direction already `claimed` or `active` by another session and refuses an unknown slug.
- [ ] `worklog-append` tests: an entry on a new day adds the `### <Weekday> <D> <Month> <YYYY>` heading; the head
      regeneration leaves everything after `## Log` byte-identical apart from the appended entry; `finding`, `need`
      and `incident` allocate F1, N1 and P1 and then F2, N2 and P2; `need-resolved` strikes through the right need with
      its answer and time and refuses an unknown or already-resolved id; the checkpoint block contains both usage rows
      and sets freeze `recorded`; a glued `--body` is refused with the lint message; times render as `8:05 am CDT`
      before 2 a.m. on 1 November 2026 and `8:05 am CST` after (fixed clocks).
- [ ] `--import` on a copy of `F/WORKLOG.md` in T produces a `worklog.json` that validates and regenerates the head;
      the differences, if any, are pasted.
- [ ] `findings-check` tests: `replicated` with one seed fails, with two distinct seeds passes; grader hash mismatch
      fails; `--paper` fails on a cited `reviewed` row and passes on `replicated` rows only.
- [ ] `job add` and `update` round-trip through `state.json`, and `list` prints the waiter commands.
- [ ] All tests pass in both envs; summaries pasted.
- [ ] `cli.py --help` lists every subcommand named in spec §5.6 that tickets 01-03 own.
- [ ] `apply_staged.py --staging S --wave A --only 03 --dry-run` output pasted.

## Verification

Both interpreters. No test reads the real `DC/docs/research`; ticket 05 runs the commands on real data.

## Comments
