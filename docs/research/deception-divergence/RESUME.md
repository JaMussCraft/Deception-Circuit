# Resume: deception-divergence

Last rewritten: Mon 2 Nov 2026, 11:40 am EST by claude-5b9b1c28.

## Status

Phase 0 is being built. The session claimed the direction (commit 9563f2e on main), registered, and froze the pre-registration in `spec.md` (R1 compliance equals the dataset's margin-0.7-both-streams gate; R2 eight arms with three listener phrasings scored in one job and read in order; R3 stratified regenerated sampling with the 1,000 selected test ids as the reproduction anchor; R4 clause-clustered paired bootstrap; R5 the U1 premise waits for D1 because no attribution-patching code exists). Three Opus workers are building D1 (scoring pipeline, hand-back 01), D4 (riders a to d, hand-back 02; rider d runs on CPU inside the ticket) and the F-rte-008 row correction (hand-back 03). No GPU job has been submitted and no finding exists yet. D2, D3 and U1 wait for the Fable weekly reset (Tue 4 Nov 2026, about 7 am EST) and for D1's verdict.

## Branch, worktree and commit

- Branch: `deception-divergence`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`.
- Last commit on the branch: `8be396f`, "deception-divergence: pre-registration spec".
- Uncommitted work, if any: worker files in progress under `scripts/`, `tests/`, `docs/research/deception-divergence/{jobs,reports}/`; committed by the orchestrator by explicit file list when each hand-back is read.
- Tool-owned records (state, worklog, ledger, handbacks) live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/deception-divergence/`; pass that path as the `dir` argument of every research-session command. Everything else is on the branch.

## In-flight jobs

None submitted. Bridges-2 allocation cis260361p had 397 of 452 GPU service units on Mon 2 Nov 2026 (a second allocation, cis260372p, has 100 unused units and is not used unless the user says so). Delta's H200 queue held nine pending Codex jobs at the same time.

| Job | Cluster | What it computes | Output directory | Expected finish |
|---|---|---|---|---|
| none | | | | |

## Next action

1. Read hand-back 01 (D1 pipeline). Check the anchor match count is 1,000 of 1,000 per task, record R2a if the I-arm token-match relaxation needs a ruling, run the wrapper dry run, then `ledger add`, `sbatch`, `job add`, and message `d1-worker` to monitor and run the `read` stage.
2. Read hand-back 02 (D4). Log rider d's P1 and P2 numbers as a finding if its evidence block is complete; submit riders a, b and c in parallel within the 4.5 GPU-hour D4 allowance.
3. Read hand-back 03 and commit the FINDINGS.md row by explicit file list.
4. On D1's verdict: log a `decision` entry; it is a milestone checkpoint, so open a need, send HOLD and end the turn.

## Do not

- Do not redo any first-token "necessary in D, not in user-turn I" test (Codex A1 to A3, `docs/research/specificity-ladder/START.md`), the instructed-route tests B1 to B3 (`docs/research/instructed-route/README.md`), the mechanism-analysis phases or the closed SDR gates.
- Do not write under `docs/research/specificity-ladder/`, the `specificity-ladder` worktree or branch, `.scratch/sdr-*`, `outputs/_analyses/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception`, `.scratch/eval5-grader-fixes`, or `docs/research/instructed-route/` (except the F-rte-008 row in FINDINGS.md).
- Do not score any set listed in `docs/research/held_out.json`.
- Do not write U1 trainer code before the user has coordinated with Codex.

## Open decisions for the user

- None yet. The START's merged U1/U2 form "awaits the user's confirmation before launch"; this session treats the user's launch instruction as that confirmation and runs phase 0, which does not touch U1 trainer code.
