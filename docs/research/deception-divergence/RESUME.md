# Resume: deception-divergence

Last rewritten: Mon 2 Nov 2026, 1:45 pm EST by claude-5b9b1c28.

## Status

Phase 0 is running. The pre-registration is frozen in `spec.md` (R1 to R5). D4 is three quarters read: rider (d), the static weight read of the quartet, fails both P1 and P2 (worklog finding F1, preliminary); rider (a) shows the quartet's readout attention moves under the clause on FAR and SER (F2); rider (b) shows the sycophancy transfer is mostly downstream of the cue window with the early MLPs acting on the cue tokens (F3); rider (c), SDR route closure, runs on Bridges-2. The FINDINGS.md corrections to F-rte-005, 006, 008 and F-mech-009 are committed (hand-back 03). D1's scoring pipeline is still being built by the Opus worker `d1-worker` (hand-back 01 pending); no D1 job has run, so no gate verdict exists. D2, D3 and U1 wait for the weekly reset (Tue 4 Nov 2026, about 7 am EST) and for D1.

## Branch, worktree and commit

- Branch: `deception-divergence`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`.
- Last commit on the branch: `c6752c0`, "deception-divergence D4: static QK/OV read ... hand-back 02" (pushed to origin; Bridges-2 clone synced to it).
- Uncommitted work, if any: `scripts/remote/b2.sh` and its test (fetch glob for deception-divergence outputs), the addendum to `reports/02-handback.md`, and the D1 worker's files `scripts/d1_visibility.py`, `scripts/jobs/run_d1_visibility.sh`, `tests/test_d1_visibility.py`; committed by explicit file list when the hand-backs are read.
- Tool-owned records (state, worklog, ledger, handbacks) live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/deception-divergence/`; pass that path as the `dir` argument of every research-session command. Everything else is on the branch.

## In-flight jobs

Delta's batch A100 queue projected a start of 9 Nov, so phase 0 jobs run on Delta's interactive partitions (one-hour cap, one job per user per partition) or on Bridges-2. Reservations r-001 to r-004: D4a (job 23443932) and D4b (23443933) completed on Delta in 134 s and 1,048 s; the Delta D4c (23443934) was cancelled after its start slipped to 4 Nov and resubmitted on Bridges-2.

| Job | Cluster | What it computes | Output directory | Expected finish |
|---|---|---|---|---|
| `50132625` | Bridges-2 | D4c SDR route closure (T1 and T2 on the 100 held-out ids) | `outputs/_analyses/deception-divergence/d4c/sdr` (fetched back with `b2.sh fetch`) | Mon 3:15 pm EST |

## Next action

1. Read hand-back 01 (D1 pipeline) when `d1-worker` reports. Check the anchor match is 1,000 of 1,000 per task; add ruling R2a if the I-arm token-match relaxation needs one; dry-run the wrapper; sync the branch to Bridges-2 (push, then `b2.sh sync-code --branch deception-divergence` with `DC_DELTA_REPO_ROOT` set to this worktree); submit on Bridges-2 or a Delta interactive partition (the script is resumable in chunks under the one-hour cap); `ledger add`, `job add`; message `d1-worker` to monitor and run `read`.
2. When `d4-worker` reports D4c: log the job and the SDR T2 finding, commit the hand-back 02 addendum, `b2.sh` and its test by explicit file list.
3. On D1's verdict: `decision` entry; milestone checkpoint (need with default, HOLD, end turn).

## Do not

- Do not redo any first-token "necessary in D, not in user-turn I" test (Codex A1 to A3, `docs/research/specificity-ladder/START.md`), the instructed-route tests B1 to B3 (`docs/research/instructed-route/README.md`), the mechanism-analysis phases or the closed SDR gates.
- Do not write under `docs/research/specificity-ladder/`, the `specificity-ladder` worktree or branch, `.scratch/sdr-*`, `outputs/_analyses/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception`, `.scratch/eval5-grader-fixes`, or `docs/research/instructed-route/` (except the F-rte-008 row in FINDINGS.md).
- Do not score any set listed in `docs/research/held_out.json`.
- Do not write U1 trainer code before the user has coordinated with Codex.

## Open decisions for the user

- None yet. The START's merged U1/U2 form "awaits the user's confirmation before launch"; this session treats the user's launch instruction as that confirmation and runs phase 0, which does not touch U1 trainer code.
