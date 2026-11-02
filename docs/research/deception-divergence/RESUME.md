# Resume: deception-divergence

Last rewritten: Mon 2 Nov 2026, 4:35 pm EST by claude-5b9b1c28.

## Status

Phase 0 is complete and the session is frozen on need N1 (a milestone checkpoint: D1's verdict). D1 is null on every task under the frozen rule: the visibility sentence moves first-token compliance by +2.5 (FAR), -5.2 (SDR) and -2.4 (SER) points under phrasing 1, with the belief and consequence phrasings also under 10, and operator-D compliance does not sit below role-matched transparent compliance (worklog F5; both reproduction anchors pass; independent review `reviews/02-d1-review.md` running). By the rule, D3 and U1 are closed and phase 1 holds only D2. D4 is done and independently reviewed (`reviews/01-d4-review.md`): the static read fails P1 and P2 (F1); the quartet's readout attention moves under the clause (F2); the sycophancy transfer sits mostly after the cue window (F3); SDR is query-side and the loop closes on the B1 code path, so the F-sdr-012 contrast does not reproduce (F4). The FINDINGS.md corrections are committed (hand-back 03). Two descriptive D1 readings outside the rules are recorded in the decision entry (FAR D-compliant subset +14.7; SDR negative under every phrasing).

## Branch, worktree and commit

- Branch: `deception-divergence`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`.
- Last commit on the branch: `adc8723`, "deception-divergence D1: results ... hand-back 01 Results section" (pushed).
- Uncommitted work, if any: none from the orchestrator; worker edits are committed by explicit file list when each hand-back is read.
- Tool-owned records (state, worklog, ledger, handbacks) live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/deception-divergence/`; pass that path as the `dir` argument of every research-session command. Everything else is on the branch.

## In-flight jobs

None. Reservations r-001 to r-005 are reconciled: 5.33 GPU-hours reserved, 1.99 actual (D4a 134 s, D4b 1,048 s on Delta interactive A100s; D4c 1,868 s and D1 4,107 s on Bridges-2 H100s; the Delta D4c copy was cancelled at 0 s). Delta's batch GPU queues projected week-long waits, so phase 0 ran on Delta interactive partitions (one-hour cap) and Bridges-2 (cis260361p, 397 of 452 units before this session). The Bridges-2 clone is at the pushed branch head and `scripts/remote/b2.sh fetch` now brings back `outputs/_analyses/deception-divergence*`.

| Job | Cluster | What it computes | Output directory | Expected finish |
|---|---|---|---|---|
| none | | | | |

## Next action

1. Wait for the user's answer to need N1 (phase 1 scope after the D1 null; default A: D2 alone after the Tuesday 4 Nov reset). Do not start new work before the acknowledgement. When `d1-reviewer` reports, commit `reviews/02-d1-review.md` by explicit file list and log it; if it supports the null, F5 becomes reviewed.
2. After "continue" and the reset: write the D2 plan (two-turn row builder, teacher-forced first answer, Pacchiardi-style undictated follow-ups, the acts-on-it turn, the refusal-direction control with a harmful/harmless prompt set to be sourced), record its rulings in `spec.md`, freeze the judge or classifier hash before any judged row, and run the 1 GPU-hour premise first.
3. If the user chooses C, run the wrap-up of the protocol (README, FINDINGS rows for F1 to F5, release paused, render, ledger-rollup, memory note).

## Do not

- Do not redo any first-token "necessary in D, not in user-turn I" test (Codex A1 to A3, `docs/research/specificity-ladder/START.md`), the instructed-route tests B1 to B3 (`docs/research/instructed-route/README.md`), the mechanism-analysis phases or the closed SDR gates.
- Do not write under `docs/research/specificity-ladder/`, the `specificity-ladder` worktree or branch, `.scratch/sdr-*`, `outputs/_analyses/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception`, `.scratch/eval5-grader-fixes`, or `docs/research/instructed-route/` (except the F-rte-008 row in FINDINGS.md).
- Do not score any set listed in `docs/research/held_out.json`.
- Do not write U1 trainer code before the user has coordinated with Codex.

## Open decisions for the user

- N1: phase 1 scope after the D1 null (A: D2 alone after the reset; B: also a small pre-registered follow-up on the two descriptive signals; C: stop and release paused), and whether the second Bridges-2 allocation cis260372p may be used. Default A, cis260361p only.
