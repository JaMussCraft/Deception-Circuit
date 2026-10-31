# 12 — Wrap-up: findings, registry, memory note, merge checklist

**Status:** claimed
**Type:** task
**Blocked by:** 01-11
**Wave:** A for the memory note and index line; D for the deferred memory rewrites (staged, not applied).
**Estimated size:** reading about 70k tokens (every hand-back and review in `F/reports/`, `F/RESUME.md`,
`F/WORKLOG.md`, spec §8 and §9), writing about 25k tokens.
**Hand-back:** `F/reports/12-handback.md`

## What to do

Close the feature's records so the next session finds it through the index, and give the orchestrator one checklist
for merging and applying everything.

## Scope

In W:
- `W/docs/research/FINDINGS.md`: rows for this feature (direction `autoresearch-workflow`), one per verified outcome
  of the hand-backs, such as the lint result on the glued samples, the token size of the index layer, the RS test
  results, and the migration verify result if wave B has run. Status at most `executed` or `reviewed` for anything
  the pilot has not observed.
- `W/docs/research/directions.json`: the `autoresearch-workflow` row's status and pointers (it stays `active` until
  the pilot is done), plus `proposed` rows for the follow-ups: the held-out scoring guard (R19), the Codex writing
  profile if ticket 07 found it unavailable, and any open item the reviews left. Re-render the views.
- `F/README.md`: the handoff for this feature (question, what was built, where it lives, how to use it, what is open).
- `F/merge-checklist.md` for the orchestrator: the DC commit file list grouped by ticket; the Alignment commit file
  list, with the deletion of the deduplicated `project_context` files (ticket 09) marked as a step the user approves;
  the apply order: wave A by ticket with all RS code first (01, 02, 03, 06 code, 11), then the RS tests from the
  installed path in both envs, then the hook smoke command from ticket 06 (timed), and only then wave H (R26); the DC
  merge after the user's approval; wave B, then `migrate_scratch.py verify` and the test reruns from ticket 10; wave C
  after the user's go for Codex; wave D and ticket 10's deferred-migration command only after the user confirms the
  live Codex session is finished (R28). Then the user actions (Codex restart and `/hooks` trust, the session-report
  install, starting the pilot), the `mechanism-datasets` cleanup commands from ticket 01, the kill-switch command for
  emergencies (`touch /u/swong2/.claude/research-session/DISABLED`), and the post-apply checks (`apply_staged.py`
  re-run shows every applied op skipped as already applied; `claude_codex_sync.py --check`).
- The one-time `worklog-append F --import` of `F/WORKLOG.md` (ticket 03), listed for the orchestrator to run after
  wave A so RS owns the worklog from then on.
- A proposed WORKLOG entry text in the hand-back (the orchestrator is the only WORKLOG writer).

Staged (wave A):
- A new memory note `/projects/beto/swong2/Alignment/.agents/memory/autoresearch-workflow.md` (project type; what
  exists and where, the two-stage freeze, the kill switch path, the staging and apply tool, and where the pilot
  stands) as a whole-file write with `expect_sha256: "absent"` and `lint: true`, and one `append_text` op adding
  its pointer line to `MEMORY.md` (never a whole-file write of MEMORY.md, R18).

Staged (wave D, pending the user's confirmation that the live Codex session is finished; R13, R28):
- `replace_text` ops rewriting `MEMORY.md` lines 27 (selective deception) and 29 (SDR) in full sentences, with the
  current line text as `old_text`.
- Pointer notes of at most 15 lines replacing `sdr-mechanism-review.md` and `selective-deception-execution.md`
  (whole-file writes with `expect_sha256` and `lint: true`), each pointing to its handoff README and to its verbatim
  copy.
- Byte-identical copies of the two current notes to
  `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_studies/sdr-mechanism/memory-log-20261031.md` and
  `.../_studies/selective-deception/memory-log-20261031.md`.
- These ops sit in their own op file `S/ops/12d-deferred-memory.json`, every op marked wave D. The hand-back says that
  the `expect_sha256` values will likely be stale by the time the user confirms, so the orchestrator re-stages them
  (the agent's ops record how) right before applying.
- `S/ops/12-wrap-up.json`.

## Acceptance criteria

- [ ] `cli.py validate` and `findings-check` pass on the updated FINDINGS and directions files; renders are stable.
- [ ] Every file listed in `merge-checklist.md` exists at the stated path (a script checks; output pasted), and the
      file lists match the hand-backs' lists exactly (a script diffs them).
- [ ] The memory note and the MEMORY.md line pass the lint; the MEMORY.md op is an `append_text` of exactly one line.
- [ ] `F/README.md` and `merge-checklist.md` pass the lint.
- [ ] `apply_staged.py --staging S --dry-run` over all tickets runs without error; its summary is pasted, grouped by
      wave, and shows no hook-installing op outside wave H and no R28 path outside wave D.

## Comments

**Orchestrator, 2026-10-31 4:15 pm EDT, additions from the hand-backs so far (all binding):**

1. Wave H is already applied (hooks in `A/.claude/settings.json`, `W/.claude/settings.json`, `~/.codex/hooks.json`;
   the Codex note block in `A/.claude/CLAUDE.md`), and the smoke test passed afterwards. Tickets 01, 02, 03, 05, 06,
   07, 08 and 09 have had their wave A ops applied. The merge checklist records these as done and lists the
   post-apply re-run check only.
2. Ticket 09 dedupe ruling: the 21 byte-identical `project_context` copies stay in place for now. Stage, wave A, a
   `README.md` in `A/project_context/reports/` and one in
   `A/project_context/research_notes/Deception specificity and shared circuits/` that name the canonical
   `Deception-Circuit/docs/research/...` path for each file and say the copy there is frozen because the live
   session's manifests pin these paths. Stage the moves themselves as wave D (destination on the same file system, for
   example `DC/outputs/_studies/project-context-dedupe-20261031/`), together with the matching edit of the
   selective-deception README sentence about the originals. Before that can run, give `op_move` in
   `F/tools/apply_staged.py` a cross-device fallback (copy, verify sha256, unlink) with a test in
   `F/tools/test_apply_staged.py`; the current bare `os.rename` fails with EXDEV from `/projects` to `/u`.
3. CLAUDE.md overlap: stage a wave A `replace_text` op that removes the one-line "Codex lint rule" bullet from the
   Deception-Circuit section of `A/.claude/CLAUDE.md`; the `autoresearch-workflow-codex-hooks` block stays.
4. `AGENTS.md` is a pointer to CLAUDE.md, not a generated copy; nothing to regenerate. The bridge sync was run after
   wave H.
5. Memory note `usage-limit-policy.md`: the self-hold is 76% under the 80% caps (it still says 70%/72%); the five-hour
   limit no longer exists on the account (user, 2026-10-31 about 1:50 pm EDT), so a missing `five_hour` key means not
   applicable (R40), and the note and the protocol docs' cap wording must say so.
6. The installed `A/docs/agents/research-session.md` must name the R39 commands `init`, `ledger` and `worklog-set`
   (replace_text op, wave A).
7. The `mechanism-datasets` worktree and branch are fully merged; the removal commands are in
   `F/reports/01-handback.md` and go in the merge checklist as an orchestrator step after ExitWorktree.
8. Ticket 04 found the root `conftest.py` is not loaded by `pytest W/tests`, so its thread limit never applied; record
   it as a follow-up `proposed` row, not fixed here.
9. The session-report plugin install sequence is in `F/reports/07-handback.md`; list it under user actions.
10. Process incidents for the worklog proposal: plan-01 ran one read-only `git diff --stat`; impl-04 stalled for
    about 2.5 hours with drafts only in its tmp directory until the orchestrator resumed it.
11. The user's time zone is Eastern; every human-facing time is 12-hour EDT/EST.
12. `W/.claude/settings.json` is force-added because the repo's local `info/exclude` ignores `.claude/`; the merge
    checklist must say so, and the user decides whether to keep it tracked.
13. Ticket 10 is applied in W but its wave B ops wait for the DC merge. The merge checklist copies the exact
    sequence from `F/reports/10-handback.md` ("Commands for the orchestrator after wave B" and "The deferred
    command"): `verify --wave B` right before, apply, `verify`, the 33-path resolution check, the seven-module reruns
    compared by name with the DC main rows of `10-tests-before.md`, and the wave D plan/apply/verify commands with
    the durable staging root `/u/swong2/.claude/research-session/staging-10d`.
14. Make `apply_staged.py --dry-run` carry planned state forward within a run (paths a planned `mkdir` creates, a
    planned `move` frees or fills, a planned `write` creates), so a chained mkdir/move/symlink sequence dry-runs
    without ERROR or CONFLICT, with a test in `F/tools/test_apply_staged.py`. Ticket 10's dry run exits 1 today for
    that reason only. The acceptance criterion "dry run over all tickets runs without error" depends on this.
15. `W/docs/research/INDEX.md`: the Layout bullet saying `component-analysis`, `format-control` and
    `eval5-grader-fixes` do not exist yet is stale for the first two, which now hold `scratch-copy/`; rewrite it to
    say what each holds and that `eval5-grader-fixes` arrives with wave D. Also note the `held-out.md` bullet once
    ticket 04 lands (it does).
16. `migrate_scratch.py` copied `component-analysis/scratch-copy/component-analysis/.pytest_cache/README.md`, a
    pytest cache file. Make the Markdown selection skip dot-directories (test it), delete that copy and its row in
    the folder's `provenance.json`, and note the change in the hand-back. Do not re-plan the wave B ops for this.
17. Ticket 11 is applied (audit-scan installed, 269 RS tests, smoke passed). The merge checklist refers to the staging
    root by its durable copy `/u/swong2/.claude/research-session/staging-20261031/` (the orchestrator makes that copy
    after your ops are staged); every apply command in the checklist uses that path, not the job tmp path.
18. Follow-up `proposed` rows from ticket 11: the Opus compaction-window test (planner compacted at 469,658
    preTokens, inconclusive; R20 binding until pilot step 9); an `audit-scan` rule for hook denials once the pilot
    records their record shape; a research-session command that sets a direction's summary (R39 forbids hand edits
    and `init` leaves a placeholder).
19. The pilot-hooks row is `proposed` with init's placeholder summary; leave it.
20. **Stall-prevention rule for agents** (root cause of incident P3: an in-process teammate subagent is not
    re-invoked when a Bash command it launched with `run_in_background` exits, so an agent that ends its turn to
    "wait for the completion notification" idles until the orchestrator messages it). Add the rule, in your own
    words, to `F/agent-brief.md`, to the installed `A/.claude/agents/ticket-implementer.md` (staged text op,
    wave A, `expect_sha256`), and to the delegation section of `A/docs/agents/research-session.md` (staged text op):
    never end a turn while a run you own is unfinished; wait actively with the Monitor tool on the log's final line,
    or run the suite in the foreground under the 10-minute timeout in chunks; if you cannot wait, put the exact
    comparison command in the hand-back's Open questions and say the orchestrator must run it; never write
    "pending" as the Status.
21. **Hook enforcement.** Extend the SubagentStop handler in the staged RS package (the H-i rule in `hooks.py` that
    blocks once when the hand-back file is missing) so it also blocks once when the hand-back's `Status:` line is
    missing, is not a terminal word (use the vocabulary `hooks.py` already has), or contains "pending",
    "to be filled", "TBD" or "in progress". Same one-block semantics and reason style, a fixture in the fixtures
    directory, tests in the staged tests tree, full staged suite green on both interpreters. Stage `hooks.py` (and
    `cli.py` if touched) as whole-file writes with `expect_sha256` of the installed files re-read right before
    staging, in `S/ops/12-wrap-up.json`, wave A. The merge checklist's post-apply step re-runs the installed tests
    and `F/tools/hook_smoke.py --live`.
22. **Orchestrator rule** for `A/docs/agents/research-session.md` (same staged op as 20): an idle notice whose text
    says the agent is waiting on something is a stall signal; the orchestrator answers it at once with the waiting
    instruction above instead of accepting it.
