# Starting prompt: autoresearch-workflow

This is a retrospective start file. The session began on 31 October 2026 from the user's description of the
workflow in chat, not from a synthesis session, so this file records the brief as it stood when the user said "go".

- **Goal (1 sentence).** Set up the coding-agent research workflow (synthesis sessions, research sessions, human
  oversight) so that research sessions on Claude Code and Codex are reliable, legible to the user, and enforced by
  hooks rather than by memory.
- **Directions.** One direction: the setup itself, in twelve tickets (lint and apply tool; usage gate; records and
  worklog; science guards; index and registry; hooks; profiles; protocol docs; two migrations; pilot; wrap-up).
  Fallback when a ticket is blocked: continue the next unblocked ticket in the wave plan.
- **Why promising.** The repo already has pre-registration, ledgers and independent review, but nothing indexes the
  findings, checkpoints and counters depend on the orchestrator remembering, state files degrade into glued text,
  and results carry no commit stamp. Fixing those is prerequisite to trusting autonomous research sessions.
- **What exists.** `reports/proposal-full.md` (approved design), `reports/lane1..4-*.md` (research), `spec.md`
  (binding rulings R1-R40), `agent-brief.md`, `issues/01-12`.
- **Do not redo.** Nothing: this is the first feature under the new layout.
- **Do not touch.** The live Codex session's directories (`.scratch/sdr-*`, `selective-deception`,
  `eval5-grader-fixes`, `sdr-session-wrapup`) and its two memory logs (spec R28).
- **Budgets.** GPU 0 hours; OpenRouter $0; weekly usage: stay under the 80% caps.
- **Oversight.** The user approved the plan at the start; the setup session reports at phase boundaries. The
  research-session hooks are not installed until wave H, so this session uses no automatic freeze.
- **Always ask before.** Merging to main; applying wave C (Codex restart) or wave D (live Codex session's files).
- **Exit criteria.** Tickets 01-12 resolved; wave A applied; hooks (wave H) installed and smoke-tested; pilot
  checklist written; FINDINGS and directions rows recorded; branch merged by the user.
- **Files.** This directory: `WORKLOG.md` (human), `RESUME.md` (machine), `state.json`, `worklog.json`,
  `ledger.json`, `reports/`, `issues/`, `handbacks/`.
- **Models.** Orchestrator Fable; every subagent Opus, passed explicitly on each spawn.
