# 12 — Wrap-up: findings, registry, memory note, merge checklist

**Status:** ready-for-agent
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
