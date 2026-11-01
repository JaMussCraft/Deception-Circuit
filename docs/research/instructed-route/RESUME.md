# Resume: instructed-route

Last rewritten: Sun 1 Nov 2026, 2:40 pm EST by claude-230e4716.

## Status

The direction instructed-route is claimed and registered by session claude-230e4716. B2 is two thirds done: P3 (the SER MLP replication) ran and gave F-rte-001 (only mlp.13 replicates; F-mech-009 superseded), P2 (the SDR wish test) passed its gate at 0.54 with nulls near zero and is under independent review, and P1 (the falsity probe) awaits its H200 capture job. B3 is in its premise phase: J1 (calibration generation) and J3 (sycophancy control) are running or queued, the judge is frozen (G1), and J2 waits on the calibration verdict. B1's code is complete except tickets 5 and 6 (sweeps, C3, path patching, readings), which an implementer is finishing; no B1 job has run and Bridges-2 goes offline about 9 November. The pre-registered exit rules are in spec.md with rulings R1 to R5 and the G1 freeze.

## Branch, worktree and commit

- Branch: `instructed-route`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route`.
- Last commit on the branch: `57c9add`, "instructed-route: claim the direction for session claude-230e4716".
- Uncommitted work, if any: RESUME.md and spec.md in the worktree (to be committed on the branch).
- Where the records live: the tool-owned records (state.json, worklog.json, WORKLOG.md, ledger.json) live in the main checkout at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/instructed-route/`, because the research-session tool mirrors the registered session's state into the checkout that contains the session's launch directory (the Alignment root, which resolves to Deception-Circuit main), and the worktree isolation hook refuses other writes there. Pass that main path as the `dir` argument of every research-session command. Everything the session writes itself (RESUME.md, spec.md, plans/, reports/, reviews/, code) lives in the worktree on the branch. The two sets of files meet at the merge.

## In-flight jobs

Three B2 jobs were submitted on Sun 1 Nov 2026 at about 2:45 pm EST from branch commit 4ba00fc; the waiters are armed in this session and must be re-armed from `research-session job list` after a compaction.

| Job | Cluster | What it computes | Output directory | Expected finish |
|---|---|---|---|---|
| `23412454` | Delta, H200 interactive | P1 capture, the falsity-probe residuals and per-token attribution for 9,972 rows in 18 cells (the A100 smoke drifted past the 0.05 margin check) | `outputs/_analyses/instructed-route-b2/p1-cap` | Sun 4:30 pm EST |
| `23412257` | Delta, A100 | B3 J1, calibration generation: both variants, 20 queries, 10 samples plus greedy per condition, with the proxy quantities | `outputs/_studies/b3/j1_calibration` | Sun 3:45 pm EST |
| `23412270` | Delta, A100 | B3 J3, the sycophancy positive control: five sets at the readout against 20 nulls on 800 MMLU items | `outputs/_studies/b3/j3_sycophancy` | Sun 4:00 pm EST |

## Next action

The three plans are committed (8c4d691) with rulings R1 to R5 in spec.md. Eleven Opus implementers run concurrently on the branch, each writing a hand-back under `reports/`: B1 tickets 1 to 4 (hand-backs 04 to 07: manifest in analyze_components, sender position masks in path patching, segment-union knockout positions, the route_closure core with the T2 arms); B2 tickets T2 to T5 (08 to 11: the inversion_reported condition, id and group files, the R-cls port and readers, per-token direct attribution); B3 tickets T1 to T3 (12 to 14: queries and prompts, the proxies, the judge and its freeze). When they land: read each hand-back's test counts, commit by file list, then spawn the dependent tickets (B1 5 to 7, B2 T6 to T8, B3 T4 to T6), record freeze G1 (the judge hash) in spec.md, run the dry runs, and submit B1's smoke to Bridges-2 (reachable on 1 November, offline about 9 November 2026).

## Do not

- Do not redo mechanism-analysis phases 0 to 3 or the selection-sample path patching; see `docs/research/mechanism-analysis/synthesis.md`.
- Do not resume the closed SDR gates or stopped assays listed in `docs/research/sdr-mechanism/README.md`.
- Do not write under `docs/research/specificity-ladder/`, which the Codex session codex-01a1987e owns, and do not touch `.scratch/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception` or `.scratch/eval5-grader-fixes`.
- Do not score any set listed in `docs/research/held_out.json`; the held-out sample here means the mechanism-analysis sample of 100 ids with seed 1.
- Do not put the word for a model's output score (the one ending in "it") in a shell command: the worktree isolation hook matches a three-letter substring of it and refuses the command. Write "answer-token attribution" instead.

## Open decisions for the user

None yet.
