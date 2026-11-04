# 04 — Acceptance run and wrap-up

**Status:** resolved
**Type:** task
**Blocked by:** 01, 02, 03.
**Estimated size:** reading about 30k tokens (the three hand-backs, the protocol, spec §8), writing about 10k tokens.
**Hand-back:** `F/reports/04-handback.md`

## What to do

Run the whole pipeline once as the acceptance test, fix what it finds, and leave the feature documented.

## Scope

- Run `research-session weekly-collect --since 2026-10-28 --out A/.scratch/weekly-report/collect-2026-11-04.md` and
  check by reading that every item the user asked for on 4 November is visible in it: the specificity ladder's
  three phases, the neuron-partition live findings, and the pointer to the literature survey.
- Run `research-session weekly-check A/project_context/reports/weekly/2026-11-04.md`. Fix the report (wording only,
  no numbers) or the check (if a rule misfires) until it exits 0; record which in the hand-back.
- Run both test suites one final time; paste the output.
- Write the `README.md` handoff of `F` (replace the init placeholder): what the feature is, the four locations, the
  two commands, and how to run a weekly-report session.
- Leave `F/WORKLOG.md`, `state.json`, `worklog.json` and `ledger.json` untouched (RS-owned; the orchestrator
  records the closing entry).

## Acceptance criteria

- [x] `weekly-check` exits 0 on the 4 November report; output pasted.
- [x] The collect brief for the 4 November window contains the three items above; the lines quoted.
- [x] Both suites pass; output pasted.
- [x] `F/README.md` passes `research-session lint`.
- [x] Hand-back written with the five headings.
