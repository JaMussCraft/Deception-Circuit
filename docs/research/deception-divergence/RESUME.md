# Resume: deception-divergence

Last rewritten: Tue 3 Nov 2026, 1:30 am EST by claude-5b9b1c28 (after compaction 4), at wrap-up. Note: Delta file times are Central; these timestamps are Eastern.

## Status

Closed on Tue 3 Nov 2026 at about 1:30 am EST; the direction is released as paused. At about 2:00 am EST the user asked for the full wrap-up: the branch was merged into main at `67919fa`, deleted locally and on origin, the worktree removed, and the worktree and Bridges-2 outputs copied into this primary checkout (`outputs/_analyses/deception-divergence/`, `logs/bridges2/`, `data/d2/_downloads/`). The handoff is `README.md` in this directory; the nine findings F-dd-001 to F-dd-009 are in `docs/research/FINDINGS.md`, each independently reviewed (reviews 01 to 06). Verdict: no readout in this direction separates deceiving an unaware user (D) from transparent inversion (I) at the pre-registered bars. The listener-knowledge routes are null on size with empty flip pools (F5 to F7); D4's riders closed (F1 to F4); the D2 premise passes the frozen rule by one point on SDR from the classifier arm alone, attributed to clause wording (F8); the R15 follow-up with the honest-instructed control labels (b) on every task, so the D2 route closes U1 under R6 iv (F9). The classifier reads being told to lie, not having lied. One descriptive lead remains (README, Open leads): a FAR score-space D minus I difference of 2.35 log-odds that the saturated rate readout cannot register and that review 06 reads as clause wording; the only design worth a new ruling is a wording-controlled I pool.

## Branch, worktree and commit

- Branch: `deception-divergence`, merged into main at `67919fa` and deleted.
- Worktree: removed after the merge; everything is in the primary checkout.
- Last commit on the branch: see `git log -1`; the final commits hold review 06, F-dd-009, the README, this RESUME and the hand-back 10 wording corrections.
- Tool-owned records (state, worklog, ledger, hand-backs saved by the hook) live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/deception-divergence/`; everything else is on the branch.
- The Bridges-2 clone (`/ocean/projects/cis260361p/swong2/Deception-Circuit`) is at `54cd1eb` and holds the D2 and follow-up feature files under `outputs/_analyses/deception-divergence/`; Bridges-2 goes offline about 9 Nov 2026.

## In-flight jobs

None. Reservations r-001 to r-011: 10.58 of 55 GPU-hours reserved, 3.38 actual (r-003 and r-009 cancelled at 0 s, r-007 failed at 158 s, r-010 failed at 4 s). OpenRouter: $2.71 of $20 (4,064 judge calls; `ledger.json` shows 8,409 calls because the tool merged the reserve with the actual).

## Next action

1. The user answers need N2 (run the follow-up, admit U1, or wrap up). The session ran the follow-up under the stated default and recommends C, wrap-up. Record the answer with `research-session worklog-append <dir> --kind need-resolved --id N2 --answer ...`.
2. Merged and cleaned up on Tue 3 Nov 2026.
3. If listener knowledge is pursued again: a new synthesis proposes the wording-controlled I pool design from `reviews/06-d2-followup-review.md` (Verdict (b)) as a new direction with its own START; do not re-run first-token or second-turn D-versus-I readouts on the existing clause pools.

## Do not

- Do not redo any first-token "necessary in D, not in user-turn I" test (Codex A1 to A3, `docs/research/specificity-ladder/START.md`), the instructed-route tests B1 to B3 (`docs/research/instructed-route/README.md`), the mechanism-analysis phases or the closed SDR gates.
- Do not write under `docs/research/specificity-ladder/`, the `specificity-ladder` worktree or branch, `.scratch/sdr-*`, `outputs/_analyses/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception`, `.scratch/eval5-grader-fixes`, or `docs/research/instructed-route/` (except the F-rte-008 row in FINDINGS.md).
- Do not score any set listed in `docs/research/held_out.json`.
- Do not write U1 trainer code: U1 is closed through D2 (R15, R6 iv) and was never admitted.
- Do not create judge ledgers whose ceilings sum to more than the remaining OpenRouter cap (the D2 ledgers summed to $21 against a $20 cap while spend was $2.71; review 04, hand-back check).
- On Bridges-2, `DC_B2_ALLOC` names the clone's path (cis260361p); charge another allocation with `sbatch -A`.

## Open decisions for the user

- N2 (opened Mon 2 Nov 2026, about 10:45 pm EST): after the D2 verdict, (A) run the pre-registered follow-up and decide U1 on its result, (B) admit U1 on the letter of R6 iv, or (C) wrap the direction. The session ran A under the stated default; its result closes U1 under the frozen rule, so the recommendation is C. Whether to open a new direction on the wording-controlled I pool is also the user's call.
