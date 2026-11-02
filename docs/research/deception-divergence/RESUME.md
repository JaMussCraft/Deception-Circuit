# Resume: deception-divergence

Last rewritten: Mon 2 Nov 2026, 3:05 pm EST by claude-5b9b1c28.

## Status

Phase 0 is running. The pre-registration is frozen in `spec.md` (R1 to R5 and R2a). D4 is done and independently reviewed (`reviews/01-d4-review.md`): rider (d), the static weight read of the quartet, fails both P1 and P2 (worklog F1); rider (a) shows the quartet's readout attention moves under the clause on FAR and SER (F2); rider (b) shows the sycophancy transfer sits mostly after the cue window with the early MLPs acting on the cue tokens (F3, with caveats); rider (c) shows SDR is query-side and the loop closes on the B1 code path, so the F-sdr-012 contrast does not reproduce (F4, with caveats). The FINDINGS.md corrections (hand-back 03) are committed. D1's pipeline is built, tested and dry-run (hand-back 01) and its scoring job runs on Bridges-2; no gate verdict exists yet. D2, D3 and U1 wait for the weekly reset (Tue 4 Nov 2026, about 7 am EST) and for D1.

## Branch, worktree and commit

- Branch: `deception-divergence`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`.
- Last commit on the branch: `4bdf6bb`, "deception-divergence D1: ruling R2a in the pipeline" (pushed; Bridges-2 clone synced to it).
- Uncommitted work, if any: none from the orchestrator; worker edits are committed by explicit file list when each hand-back is read.
- Tool-owned records (state, worklog, ledger, handbacks) live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/deception-divergence/`; pass that path as the `dir` argument of every research-session command. Everything else is on the branch.

## In-flight jobs

Delta's batch A100 queue projected a start of 9 Nov, so phase 0 jobs run on Delta's interactive partitions (one-hour cap, one job per user per partition) or on Bridges-2. Reservations r-001 to r-005: D4a (job 23443932) and D4b (23443933) completed on Delta in 134 s and 1,048 s; the Delta D4c (23443934) was cancelled after its start slipped to 4 Nov; D4c completed on Bridges-2 (50132625) in 1,868 s; D1 (50145353) is on Bridges-2. Phase 0 actual spend before D1: 0.85 GPU-hours.

| Job | Cluster | What it computes | Output directory | Expected finish |
|---|---|---|---|---|
| `50145353` | Bridges-2 | D1 scoring: P, D, six listener arms and I on about 32,000 sampled ids per task plus the 1,000 anchors (about 622,000 forwards, about 1.2 GPU-h) | `outputs/_analyses/deception-divergence/d1/<task>/` (fetched back with `b2.sh fetch`) | Mon about 6 pm EST |

## Next action

1. When `d1-worker` reports the D1 results: read the Results section of hand-back 01 (both anchors must hold: D clean margins reproduce under instructed-route R7 and the token-matched I arm's compliance on the anchors matches 210, 788 and 249), log the job, log the finding, log a `decision` entry with the per-task verdicts. D1's verdict is a milestone checkpoint: open a need with a default (if D1 passes on any task, the default is to build D3 and the U1 premise after the reset; if null on all three phrasings, the default is that D3 and U1 die and phase 1 is D2 only), send HOLD to running workers, and end the turn.
2. Spawn an independent Opus review of D1 (code, scores, manifests; not the hand-back) before marking its finding reviewed.
3. After the user's answer and the weekly reset: phase 1 per START (D2 premise first).

## Do not

- Do not redo any first-token "necessary in D, not in user-turn I" test (Codex A1 to A3, `docs/research/specificity-ladder/START.md`), the instructed-route tests B1 to B3 (`docs/research/instructed-route/README.md`), the mechanism-analysis phases or the closed SDR gates.
- Do not write under `docs/research/specificity-ladder/`, the `specificity-ladder` worktree or branch, `.scratch/sdr-*`, `outputs/_analyses/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception`, `.scratch/eval5-grader-fixes`, or `docs/research/instructed-route/` (except the F-rte-008 row in FINDINGS.md).
- Do not score any set listed in `docs/research/held_out.json`.
- Do not write U1 trainer code before the user has coordinated with Codex.

## Open decisions for the user

- None yet. The START's merged U1/U2 form "awaits the user's confirmation before launch"; this session treats the user's launch instruction as that confirmation and runs phase 0, which does not touch U1 trainer code.
