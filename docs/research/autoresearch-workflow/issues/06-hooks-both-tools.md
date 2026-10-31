# 06 — Hooks for Claude and Codex

**Status:** ready-for-agent
**Type:** task
**Blocked by:** 02, 03
**Wave:** A for `A/.claude/settings.json` and `~/.codex/hooks.json`; the tracked `W/.claude/settings.json` is
committed by the orchestrator. Hooks call RS at its installed path, so they work only after wave A has installed RS.
**Estimated size:** reading about 80k tokens (spec §5.1-5.5, R4-R8, R12, R21; lane 2 §1-3 and §8; the Claude hooks
page and the Codex hooks page), writing about 70k tokens.
**Hand-back:** `F/reports/06-handback.md`

## What to do

Implement `research-session hook <event> --tool <claude|codex>` for the ten hooks of spec §5.1 and install them in
the project settings of both repositories and in Codex's user hooks file.

## Facts to build on

- Claude hook events and outputs: lane 2 §1-3 (SessionStart sources include `compact`; PostCompact has
  `compact_summary` and no decision control; PreToolUse denies with `permissionDecision: "deny"`; SubagentStop has
  `last_assistant_message`; Stop `block` makes the agent continue, so never block it). Docs:
  https://code.claude.com/docs/en/hooks.
- Codex: https://learn.chatgpt.com/docs/hooks. Lane 2 reports the same event names, a default `additionalContext`
  cap of 2500 tokens (set `additionalContextLimit`), JSON output required on SubagentStop, and one-time `/hooks`
  trust per new or edited hook. Spawn, shell, message and patch tool names must be verified (R12).
- `~/.codex/hooks.json` has the shape `{"hooks": {"SessionStart": [{"matcher": "...", "hooks": [{"type":
  "command", "command": "...", "timeout": 30}]}]}}` with only the bridge entry. The bridge's `sync_startup`
  (`A/.agents/claude_codex_sync.py:412-430`) removes and re-adds only groups containing its own script, so other
  entries survive regeneration. The same holds for `~/.claude/settings.json`.
- `A/.claude/settings.json` today is `{"enabledPlugins": {"andrej-karpathy-skills@karpathy-skills": false}}`.
  DC has no `.claude/settings.json`; W's `.gitignore` does not ignore `.claude/worktrees/` (R21).
- The installed command path is
  `/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/.agents/research_session/cli.py`.

## Scope

- Staged: `research_session/hooks.py` (event dispatch, per-tool input parsing and output shaping),
  `tests/test_research_session_hooks.py` with recorded input fixtures in `tests/fixtures/hooks/`, and the `hook`
  subcommand in `cli.py`.
- Staged `json_merge` into `/projects/beto/swong2/Alignment/.claude/settings.json` adding the `hooks` block.
- In W: new `W/.claude/settings.json` with the same `hooks` block, and two lines in `W/.gitignore`.
- Staged `json_merge` into `/u/swong2/.codex/hooks.json` for every Codex event whose names are verified.
- `S/ops/06-hooks.json`.

## Acceptance criteria

- [ ] For each hook H-a to H-j, a fixture test feeds a recorded input and asserts the exact stdout JSON and exit code,
      for Claude and, where installed, for Codex. Codex SubagentStop always prints JSON.
- [ ] H-d fixtures include a Write and an Edit on a direction `state.json` and on the session-state root (denied),
      and a Write elsewhere (allowed).
- [ ] The hand-back gives the orchestrator a smoke command for after wave A: write a crafted PreToolUse JSON into a
      file in T, run the installed `cli.py hook pre-tool-use --tool claude` with that file on stdin, and expect exit 0
      and valid JSON. A crash there would deny spawns in every A-rooted session until the kill switch is used.
- [ ] H-b increments `compactions` exactly once per call; H-c never increments; a test runs H-c then H-b and the
      reverse and gets the same count.
- [ ] H-f blocks a glued WORKLOG paragraph and a planted fake token, and stays silent on a clean write and on
      out-of-scope paths (glue) while still scanning secrets under A.
- [ ] H-g acks on "continue", "Continue." and "  continue with X"; does not ack "can you continue?" or a question;
      and injects the freeze notice while frozen.
- [ ] H-i saves the message, blocks once when no hand-back file changed since start, never blocks twice, and skips
      the excluded agent types.
- [ ] H-j is silent when `stop_hook_active` is true or background tasks exist.
- [ ] Every hook no-ops with exit 0 and no output when cwd is outside A and when the kill switch exists.
- [ ] The Codex hooks page was read; the hand-back records each verified event, matcher and tool name with the URL.
      Unverified Codex matchers are not installed and are listed.
- [ ] Applying the two `json_merge` ops to copies in T yields valid JSON that still contains the bridge hook
      unchanged; `W/.claude/settings.json` parses.
- [ ] All RS tests pass in both envs; summaries pasted.

## Verification

Both interpreters. No live session is needed; the pilot (ticket 11) observes the hooks in real sessions.

## Comments
