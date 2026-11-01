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

None.

| Job | Cluster | What it computes | Output directory | Expected finish |
|---|---|---|---|---|

## Next action

Three Opus planners, one per sub-direction, write costed plans to `plans/B1-plan.md`, `plans/B2-plan.md` and `plans/B3-plan.md` and hand-backs `reports/01-handback.md` to `reports/03-handback.md`. Then: freeze spec.md from the plans; implement B1's position-resolved path patching on the branch; submit B1 to Bridges-2 (reachable on 1 November, offline about 9 November 2026).

## Do not

- Do not redo mechanism-analysis phases 0 to 3 or the selection-sample path patching; see `docs/research/mechanism-analysis/synthesis.md`.
- Do not resume the closed SDR gates or stopped assays listed in `docs/research/sdr-mechanism/README.md`.
- Do not write under `docs/research/specificity-ladder/`, which the Codex session codex-01a1987e owns, and do not touch `.scratch/sdr-*`, `.scratch/selective-deception`, `outputs/_studies/selective-deception` or `.scratch/eval5-grader-fixes`.
- Do not score any set listed in `docs/research/held_out.json`; the held-out sample here means the mechanism-analysis sample of 100 ids with seed 1.
- Do not put the word for a model's output score (the one ending in "it") in a shell command: the worktree isolation hook matches a three-letter substring of it and refuses the command. Write "answer-token attribution" instead.

## Open decisions for the user

None yet.
