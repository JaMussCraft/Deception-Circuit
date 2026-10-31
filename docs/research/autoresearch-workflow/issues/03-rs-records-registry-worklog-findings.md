# 03 — RS records: registry, renders, worklog, jobs, findings-check

**Status:** ready-for-agent
**Type:** task
**Blocked by:** 02 (shared `cli.py` and `state.py`)
**Wave:** A
**Estimated size:** reading about 60k tokens (spec §4, §5.3, §5.4, §5.6, §6.3, §6.5, R15-R17, R22-R23; lane 4 §1
template and checkpoint block; lane 3 §4 schemas), writing about 80k tokens.
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
- `research_session/registry.py`: validators for `directions.json` (§4.2), ledger (§4.4), `state.json` (§4.5),
  the FINDINGS table (§4.1) and `held_out.json` (§6.4); `render` for `DIRECTIONS.md` and `SESSIONS.md` (§4.3);
  `ledger-rollup`; `claim <slug>` and `release <slug> --status` (R23; they edit `directions.json` under a `--root`
  that defaults to `DC/docs/research`).
- `research_session/worklog.py`: `worklog-append` with the kinds of spec §5.6. It rewrites the header (State,
  Directions, Started and last updated, compactions from `state.json`, weekly usage with both the all-models and the
  Fable rows, checkpoints acknowledged, budgets, open needs), appends the entry under the right day heading, writes
  the checkpoint block of lane 4 §1 for `--checkpoint N` and sets that freeze to `recorded`, updates
  `last_worklog_entry_at`, and lints its own output before replacing the file.
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
- [ ] `worklog-append` tests: an entry on a new day adds the day heading; the header rewrite keeps the body
      byte-identical (append-only body); the checkpoint block contains both usage rows and sets freeze `recorded`; a
      glued `--body` is refused with the lint message; time strings carry CDT before 2 a.m. on 1 November 2026 and
      CST after (fixed clocks in tests).
- [ ] `findings-check` tests: `replicated` with one seed fails, with two distinct seeds passes; grader hash mismatch
      fails; `--paper` fails on a cited `reviewed` row and passes on `replicated` rows only.
- [ ] `job add` and `update` round-trip through `state.json`, and `list` prints the waiter commands.
- [ ] All tests pass in both envs; summaries pasted.
- [ ] `cli.py --help` lists every subcommand named in spec §5.6 that tickets 01-03 own.
- [ ] `apply_staged.py --staging S --wave A --only 03 --dry-run` output pasted.

## Verification

Both interpreters. No test reads the real `DC/docs/research`; ticket 05 runs the commands on real data.

## Comments
