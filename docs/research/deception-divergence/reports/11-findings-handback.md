# Hand-back 11: FINDINGS rows F-dd-001 to F-dd-008

Agent: Opus worker (claude-opus-5-5), direction deception-divergence. Ticket: the lead's brief "Write FINDINGS rows
for deception-divergence" of Mon 2 Nov 2026 (wrap-up step 2 of `docs/agents/research-session.md` section 10).
Status: resolved for F1 to F8. F-dd-009 waits for the lead's text.

## What changed

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/FINDINGS.md`:
  eight new rows after F-rte-008, ids F-dd-001 to F-dd-008 for worklog findings F1 to F8 in order. Every row is
  dated 2026-11-02, has status `reviewed` and puts its review in the report column. No other row changed.
- This hand-back. No code, outputs, worklog or tool-owned records were touched. No git was run.

Commit column choices:

| row | finding | commit | source |
|---|---|---|---|
| F-dd-001 | F1, static read | 54cd1eb | fallback; the run manifest names b324c50 with a dirty tree and an uncommitted script |
| F-dd-002 to 004 | F2 to F4, GPU riders | c6752c0 | hand-back 02 addendum and the run manifests |
| F-dd-005 | F5, D1 | 4bdf6bb | hand-back 01 and review 02 |
| F-dd-006, 007 | F6, F7, D1 follow-up | a0936e5 | hand-back 06, which records a0936e5 as the job's commit |
| F-dd-008 | F8, D2 premise | fb2cb9e | hand-back 07 and review 04 |

## How verified

- A script checked that every number in each worklog register row F1 to F8 appears in the matching new row. None
  is missing.
- Every evidence path was checked to exist in the worktree.
- `research-session lint` on FINDINGS.md exits 0.
- `research-session findings-check --root <worktree>/docs/research` reports 0 errors and 0 warnings.

## Execution evidence

No job was run. All checks ran on the Delta login node with the mgnp interpreter. The helper scripts are outside the
repository, in `/u/swong2/.claude/jobs/5b9b1c28/tmp/ddrows/`.

## What is NOT done

- F-dd-009, the D2 follow-up under ruling R15, is not written. The lead will send its text after its review.
- The direction README is not part of this task.

## Open questions

- F4 bundles the T2 query-side verdict and the T1 loop-closure label in one row, as the worklog does. F-rte-005 and
  F-rte-006 split the same pair into two rows. Default: keep one row, because the ids map one to one onto F1 to F8.
- F6's commit is a0936e5, the commit of the reading code. Its input scores come from the D1 job at 4bdf6bb. Default:
  keep a0936e5.
