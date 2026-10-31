# 06 — Hooks for Claude and Codex

**Status:** resolved
**Type:** task
**Blocked by:** 02, 03
**Wave:** A for the RS hook code; H for every settings change that installs a hook (R26). You never write
`W/.claude/settings.json`, any `A/.claude/settings*.json` or `~/.codex/hooks.json` yourself (brief constraint 9).
**Estimated size:** reading about 90k tokens (spec §5.1-5.5, R4-R8, R12, R21, R26, R30, R32, R36-R37; lane 2 §1-3
and §8; `F/reports/00-plan-review.md` section C; the Claude hooks page and the Codex hooks page), writing about 70k.
**Hand-back:** `F/reports/06-handback.md`

## What to do

Implement `research-session hook <event> --tool <claude|codex>` for the ten hooks of spec §5.1, and stage their
installation for wave H so that no hook can exist before the code it calls.

## Facts to build on

- Hook settings hot-reload, and base python3.9 exits 2 when its script file is missing; exit 2 from PreToolUse blocks
  the tool call (review blocker 1). This is why every command is the literal shell guard of spec §5.1 and why all
  installation is wave H.
- Claude contracts (confirmed by the reviewer against https://code.claude.com/docs/en/hooks): SessionStart sources
  `startup|resume|clear|compact|fork`; PostCompact has `compact_summary` and no decision control; PreToolUse denies
  with `permissionDecision: "deny"` and `permissionDecisionReason`; PostToolUse `decision: "block"` only adds a reason
  and cannot undo the write; SubagentStop has `stop_hook_active`, `agent_transcript_path` and
  `last_assistant_message`; Stop `block` makes the agent continue, so never block it; Stop carries `background_tasks`
  and `session_crons`; any exit other than 0 or 2 is non-blocking, so a timed-out hook fails open.
- UserPromptSubmit also fires for scheduled tasks, background subagent reports and messages from other sessions, and
  no documented field tells them apart (review section C). Look for a source field in the payload anyway and record
  what you find.
- Codex (https://learn.chatgpt.com/docs/hooks, per the reviewer): `spawn_agent` matches `Agent`; `apply_patch`
  matches `apply_patch`, `Edit` and `Write`; no message tool is documented (R32); `additionalContextLimit` defaults
  to 2500 tokens; SubagentStop must print JSON; new or edited hooks need one-time `/hooks` trust; Codex also loads
  `<repo>/.codex/hooks.json` when the project layer is trusted (R4).
- `~/.codex/hooks.json` holds only the bridge's SessionStart group. The bridge's `sync_startup`
  (`A/.agents/claude_codex_sync.py:412-430`) removes and re-adds only groups containing its own script, so other
  groups survive regeneration, in that file and in `~/.claude/settings.json`.
- `A/.claude/settings.json` today is `{"enabledPlugins": {"andrej-karpathy-skills@karpathy-skills": false}}`.
  DC has no `.claude/settings.json`; W's `.gitignore` does not ignore `.claude/worktrees/` (R21).

## Scope

- Staged (wave A): `research_session/hooks.py` (event dispatch, per-tool input parsing and output shaping),
  `tests/test_research_session_hooks.py` with recorded input fixtures in `tests/fixtures/hooks/`, and the `hook`
  subcommand in `cli.py`.
- Staged (wave H): `json_merge` into `/projects/beto/swong2/Alignment/.claude/settings.json` adding the `hooks` block;
  `json_merge` into `/u/swong2/.codex/hooks.json` for every Codex event and matcher you verified. Both ops come after
  every wave A op in apply order.
- In W: `F/staged/dc-claude-settings.json` holding the full content of the future `W/.claude/settings.json` (the same
  `hooks` block), and two lines in `W/.gitignore` (`.claude/worktrees/`, `.claude/settings.local.json`).
- `F/tools/hook_smoke.json` and a smoke command for the orchestrator (see acceptance).
- `S/ops/06-hooks.json`.

## Acceptance criteria

- [x] Every `command` string in the staged settings and in `F/staged/dc-claude-settings.json` matches the shell guard
      of spec §5.1 exactly, apart from the event name and `--tool`, and contains no `$`. A test checks this.
- [x] Running each staged command with a temporary copy where the CLI path does not exist, and again with the kill
      switch present, exits 0 with no output (use test-only copies of the command string that point at paths in T).
- [x] For each hook H-a to H-j, a fixture test feeds a recorded input and asserts the exact stdout JSON and exit code,
      for Claude and, where installed, for Codex. Codex SubagentStop always prints JSON.
- [x] H-a in an unregistered session prints the `research-session register <slug>` line and says the session gets
      only the cap and stale gates; in a registered session it prints the freeze state instead (spec R5).
- [x] H-d denies a Write of a glued WORKLOG paragraph and a Write or Edit containing a planted fake token, with the
      failing units in the reason; allows a clean write; and denies Write and Edit on a direction `state.json`,
      `worklog.json` and the session-state root, but not on `_templates/` (R30, R37).
- [x] H-f returns `additionalContext` only, never `decision: "block"`, and reports a lint problem elsewhere in a file
      after a clean Edit.
- [x] H-g acks on "continue", "Continue." and "  continue with X"; does not ack "can you continue?", a question, any
      prompt starting with `<`, or a prompt containing `<teammate-message`, `<agent-message`,
      `<cross-session-message` or `<task-notification` (fixtures for each wrapper); and injects the freeze notice while
      frozen. The hand-back says whether the payload has a source field (R36).
- [x] H-b increments `compactions` exactly once per call; H-c never increments; H-c then H-b and the reverse give the
      same count.
- [x] H-i saves the message, blocks once when no hand-back file changed since start, never blocks twice, and skips
      the excluded agent types.
- [x] H-j is silent when `stop_hook_active` is true or `background_tasks` or `session_crons` is non-empty.
- [x] Every hook no-ops with exit 0 and no output when cwd is outside A.
- [x] The Codex hooks page was read. The hand-back records each verified event, matcher and tool name, the
      `apply_patch` input shape, and whether the project-level `.codex/hooks.json` would load for A and for DC, with
      URLs. Unverified Codex matchers are not installed and are listed. No message-tool matcher is installed (R32).
- [x] The hand-back gives the orchestrator the smoke command for wave H: feed `F/tools/hook_smoke.json` (a crafted
      PreToolUse Agent call) on stdin to the installed guarded command and expect exit 0 and valid JSON, timed. A
      crash there would deny spawns in every A-rooted session until the kill switch is used.
- [x] Applying the two `json_merge` ops to copies in T yields valid JSON that still contains the bridge hook
      unchanged; `F/staged/dc-claude-settings.json` parses.
- [x] `apply_staged.py --staging S --only 06 --dry-run` shows the code ops as wave A and the settings ops as wave H.
- [x] All RS tests pass in both envs; summaries pasted.

## Verification

Both interpreters. No live session is needed; the pilot (ticket 11) observes the hooks in real sessions.

## Comments

Ticket 06 implementer, 2026-10-31. Every box above was checked against a command whose output I read; the
hand-back gives each command and its output. Two boxes carry a stated deviation. For "every hook no-ops with no
output outside A", Codex SubagentStop and Stop print `{}` instead, because the Codex page calls plain text invalid
there. For "for Claude and, where installed, for Codex", Codex H-c and H-j are not installed, because the Codex
PostCompact input has no summary and the Codex Stop output schema has no `additionalContext`.

Committed by the orchestrator from W:

- `.gitignore` (two lines, R21)
- `docs/research/autoresearch-workflow/staged/dc-claude-settings.json`, `claude-hooks-fragment.json`,
  `codex-hooks-fragment.json` and `codex-hooks-note.md`
- `docs/research/autoresearch-workflow/tools/hook_smoke.py`, `hook_smoke.json` and `test_hook_settings.py`
- `docs/research/autoresearch-workflow/reports/06-handback.md` and this ticket

Staged in S, ops file `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/ops/06-hooks.json`: 47 wave A writes
(`research_session/hooks.py`, `cli.py` with `expect_sha256`, `tests/test_research_session_hooks.py` and 44 fixtures
in `tests/fixtures/hooks/`), then 4 wave H ops (the two `json_merge` ops, the write of `W/.claude/settings.json`, and
a `text_block` in `A/.claude/CLAUDE.md`).

Tests: the staged RS suite gave 252 passed with 19 subtests on mgnp, and 252 passed on base python3.9.
`F/tools/test_hook_settings.py` gave 11 passed on each interpreter, and `F/tools/test_apply_staged.py` gave 33
passed on base. The smoke script passed against the staged CLI with every isolated call under 0.4 s.
