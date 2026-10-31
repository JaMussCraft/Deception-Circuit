# 08 — Protocol docs and templates

**Status:** ready-for-agent
**Type:** task
**Blocked by:** 01 (lint, to check the docs). It uses the command names fixed in spec §5.6, so it runs in parallel
with 02 and 03.
**Wave:** A for the Alignment docs and the agent definition; the templates are in W.
**Estimated size:** reading about 80k tokens (proposal §1-4, spec §4-7 and §9, lane 4 §1-4 in full, lane 1 §1d-1g,
`A/.scratch/mechanism-analysis/agent-brief.md` as a style model, `A/docs/agents/issue-tracker.md`), writing about
50k tokens.
**Hand-back:** `F/reports/08-handback.md`

## What to do

Write the three session protocols and the templates they use, so a research, synthesis or audit session can start
from a document instead of from memory.

## Scope

Staged (wave A):
- `/projects/beto/swong2/Alignment/docs/agents/research-session.md`: start from START.md; register and claim
  (R23), stating that only a registered session gets the checkpoint freeze, so a research session must register
  before its first spawn (R5); read FINDINGS and SESSIONS first; at least two directions, each with a fallback; the worklog triggers of
  lane 4 §1 and the use of `worklog-append` with every kind (entries, findings, needs with a default, resolved needs,
  incidents; R33); the checkpoint protocol with the two-stage freeze (spec §5.2, R6) and the turn end of R35, in these
  words or stronger: "finish the atomic step in flight, write the checkpoint block, send HOLD to every running worker,
  and end your turn; do not poll for the human; start no new work until the acknowledgement; a worker that receives
  HOLD finishes its atomic step, writes its hand-back and stops; running Slurm jobs and agents are not cancelled";
  the cap pause, the stall alarm (waiters time out within 60 minutes and the orchestrator switches direction when a job
  shows no progress), and the milestone trigger; the Fable-close rule (§5.4); Slurm waiters recorded with `job add`;
  the hand-back template and the execution-evidence rule (§4.7); the ask-before list (merge, EVAL 5, dropping a
  direction, any cap raise); wrap-up (README handoff, FINDINGS rows, `release`, SESSIONS row, memory pointer).
  A short Codex section: the same protocol, `codex-usage` as the meter with a 25-point cadence, a freeze that denies
  only spawns and `sbatch` because Codex documents no message tool (R32), so HOLD instructions go through the
  orchestrator's own discipline, and "run `research-session lint <file>` after every write" unless ticket 06 verified
  the `apply_patch` PreToolUse route.
- `/projects/beto/swong2/Alignment/docs/agents/synthesis-session.md`: reading order (INDEX, FINDINGS, SESSIONS,
  DIRECTIONS, recent worklog headers); re-survey only where FINDINGS has gaps; propose only unclaimed directions or
  hand over a paused one explicitly; output is the one-screen proposal plus one START.md per session; reviewers get
  code, logs and provenance files, not the report (lane 1 §1e).
- `/projects/beto/swong2/Alignment/docs/agents/session-audit.md`: the 11-check rubric of lane 4 §3 with the verdict
  rule, the inputs, and which checks `research-session audit-scan` automates (ticket 11).
- `/projects/beto/swong2/Alignment/.claude/agents/ticket-implementer.md`: add the hand-back headings and the
  execution-evidence rule and the HOLD rule below the frontmatter (R25, R35), keeping `model: opus` and the existing
  text. Whole-file write with `expect_sha256`.

In W:
- `W/docs/research/_templates/START.md`, `proposal.md`, `WORKLOG.md`, `RESUME.md` (fixed headings: Status;
  Branch, worktree and commit; In-flight jobs; Next action; Do not; Open decisions for the user), `state.json`,
  `ledger.json`, `worklog.json`, `handback.md`, `audit.md`. Base them on lane 4 §1-4 and spec §4, including §4.8 (the
  WORKLOG template shows the regenerated head above `## Log` and the append-only log below it).

## Acceptance criteria

- [ ] Every document and Markdown template passes `cli.py lint`; output pasted.
- [ ] Every RS command a document names appears in spec §5.6 (a script in T greps the docs and compares; output
      pasted). When ticket 03 has landed, the same check runs against `cli.py --help`.
- [ ] `state.json` and `ledger.json` templates pass `cli.py validate` once ticket 03 has landed; until then the
      hand-back says so.
- [ ] `ticket-implementer.md` keeps its frontmatter byte-identical (`name`, `description`, `model: opus`,
      `effort: high`); a diff is pasted.
- [ ] Each protocol is under about 250 lines and starts with a five-line "what this is and when to use it" summary.
- [ ] `apply_staged.py --staging S --only 08 --dry-run` output pasted.

## Verification

Lint and the command-name check. No code changes.

## Comments
