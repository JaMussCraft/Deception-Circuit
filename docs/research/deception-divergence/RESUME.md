# Resume: deception-divergence

Last rewritten: Mon 2 Nov 2026, 8:05 pm EST by claude-5b9b1c28.

## Status

Phase 1 is running under the user's N1 answer (continue under the 80 percent cap, run the option B follow-up, find a defensible route to U1) and ruling R6. Phase 0 is closed: D1 null on size on every task (F5, reviewed, `reviews/02-d1-review.md`); D4 done and reviewed (F1 to F4, `reviews/01-d4-review.md`). The R6 follow-up found the phrasing-1 flip pool empty on every task (F6): the system-turn sentence shifts margins but never flips a compliant answer, so U1 cannot return through phrasing 1; the user-turn phrasing 4 job is the last listener route and runs now. The D2 premise (two-turn lie maintenance; rulings R7 to R13, judge freeze G-D2 at hash 1e41b6b9...) is built, tested and submitted; its judge stage is the orchestrator's and spends OpenRouter credit. U1 is re-admitted only by a qualifying phrasing-4 flip pool or a D2 premise pass (R6 iii and iv); U1 trainer code still waits for the user's word on Codex coordination.

## Branch, worktree and commit

- Branch: `deception-divergence`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`.
- Last commit on the branch: `a0936e5`, "rulings R7 to R13 and freeze G-D2 for the D2 premise" (pushed; Bridges-2 clone synced to it).
- Uncommitted work, if any: none from the orchestrator; worker edits are committed by explicit file list when each hand-back is read.
- Tool-owned records (state, worklog, ledger, handbacks) live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/deception-divergence/`; pass that path as the `dir` argument of every research-session command. Everything else is on the branch.

## In-flight jobs

Reservations r-001 to r-007: 7.08 GPU-hours reserved, 1.99 actual before the two jobs below. Bridges-2 (cis260361p) is the working cluster; Delta's batch queues projected week-long waits and its interactive partitions carry a one-hour cap. The user allows any Delta or Bridges-2 allocation (shared memory note `cluster-allocations`).

| Job | Cluster | What it computes | Output directory | Expected finish |
|---|---|---|---|---|
| `50152632` | Bridges-2 | D1 follow-up: phrasing-4 listener arms on the D1 sample (R6 i, iii) | `outputs/_analyses/deception-divergence/d1/` (`scores_l4.jsonl`, `followup_readings.*`) | Mon about 9:15 pm EST |
| `50153789` | Bridges-2 | D2 premise: elicitation features, acts-on-it proxies and generations, refusal direction (R7 to R13) | `outputs/_analyses/deception-divergence/d2/` | Mon about 10 pm EST |

## Next action

1. When `d1b-worker` reports the phrasing-4 results: log the job and a finding; read the R6 (i) verdict and the (iii) flip pool per task. If a task qualifies, open a need asking the user to confirm Codex coordination before any U1 trainer code; otherwise record that U1 waits on D2.
2. When `d2-worker` reports: log the job; record the proxy token file hash in `spec.md` (G-D2 second part) before any test row is read; run the `judge` stage (OpenRouter, within the $20 cap, `ledger api`), then have the worker run `read` and write the verdict under R13; log a `decision` entry (milestone). If the premise passes, write the patching ruling and plan the 8 to 15 GPU-hour patching run; if it fails, report the rates and the direction is ready for wrap-up.
3. Independent Opus reviews of the follow-up and of D2 before their findings are marked reviewed.
4. Checkpoint 1 fires at 24 session points (cadence set by the user); cap pause at 80 percent weekly.

## Do not

- Do not redo any first-token "necessary in D, not in user-turn I" test (Codex A1 to A3, `docs/research/specificity-ladder/START.md`), the instructed-route tests B1 to B3 (`docs/research/instructed-route/README.md`), the mechanism-analysis phases or the closed SDR gates.
- Do not write under `docs/research/specificity-ladder/`, the `specificity-ladder` worktree or branch, `.scratch/sdr-*`, `outputs/_analyses/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception`, `.scratch/eval5-grader-fixes`, or `docs/research/instructed-route/` (except the F-rte-008 row in FINDINGS.md).
- Do not score any set listed in `docs/research/held_out.json`.
- Do not write U1 trainer code before the user has said the Codex coordination is done (reaffirmed in R6 v).

## Open decisions for the user

- None open. N1 was answered on Mon 2 Nov 2026 (continue, option B, any allocation). The next decision is the U1 go-ahead, which this session asks for only if a flip pool qualifies or the D2 premise passes.
