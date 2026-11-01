# Resume: instructed-route

Last rewritten: Sun 1 Nov 2026, 2:40 pm EST by claude-230e4716.

## Status

The direction instructed-route is claimed and registered by session claude-230e4716. All three sub-directions are active and none has run a job yet: B1 (close the loop on FAR and SER with position-resolved path patching), B2 (the falsity signal across tasks, the SDR wish test and the SER MLP replication) and B3 (alignment faking on Llama-3.1-8B-Instruct, then transfer of the route). No finding has been logged. The pre-registered exit rules are copied verbatim from START.md section 10 into spec.md.

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
| `23412228` | Delta, A100 interactive | P2, the SDR wish test: 29 group knockouts on the 618 reported-wish ids and their D reference | `outputs/_analyses/instructed-route-b2/p2` | Sun 3:30 pm EST |
| `23412229` | Delta, H200 interactive | P3, the SER MLP replication: seeds 0, 1, 2 on D, H and F for the three tasks | `outputs/_analyses/instructed-route-b2/p3` | Sun 4:00 pm EST |
| `23412232` | Delta, A100 | P1 smoke, the falsity-probe capture at 64 rows per cell | `outputs/_analyses/instructed-route-b2/p1-smoke` | Sun 3:30 pm EST |

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
