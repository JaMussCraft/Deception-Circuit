# 06 — Hand-back: hooks for Claude Code and Codex

Implementer: Opus, ticket 06, 2026-10-31. No git command was run. Nothing was installed or applied, and no settings
file with hooks was created or edited outside staging. The real credentials file was never opened. The only network
access was reading documentation pages and the Codex generated hook schemas.

## What changed

### Committed by the orchestrator from W

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/.gitignore`: two lines
  added under a comment, `.claude/worktrees/` and `.claude/settings.local.json` (R21).
- `F/staged/dc-claude-settings.json`: the full content of the future `W/.claude/settings.json`, a `hooks` block only.
- `F/staged/claude-hooks-fragment.json`: the same `hooks` block, the fragment of the `A/.claude/settings.json` merge.
- `F/staged/codex-hooks-fragment.json`: the fragment of the `~/.codex/hooks.json` merge.
- `F/staged/codex-hooks-note.md`: the Codex-side instruction text (see "Codex instruction text" below).
- `F/tools/hook_smoke.py` and `F/tools/hook_smoke.json`: the wave H smoke test and its crafted PreToolUse Agent call.
- `F/tools/test_hook_settings.py`: tests of the staged settings, the op file, the guard behaviour and the smoke run.
- `F/reports/06-handback.md` (this file) and `F/issues/06-hooks-both-tools.md` (status, checkboxes, comments).

Here F is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow`.

### Staged in S, ops file `S/ops/06-hooks.json`

The ops file is `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/ops/06-hooks.json`. It holds 51 ops: 47 in
wave A, then 4 in wave H. Every wave H op comes after every wave A op.

Wave A, all `write` ops into `/projects/beto/swong2/Alignment/.agents/`:

1. `research_session/hooks.py` (new). Event dispatch for the ten hooks, per-tool input parsing and output shaping,
   the Codex `apply_patch` translation, and the fail-open error path with a log at `<state root>/hook-errors.log`.
2. `research_session/cli.py`, with `expect_sha256` 87c7964227a6... (the installed ticket 03 file, which is
   byte-identical to the staged one I started from). `main` hands `hook ...` to `hooks.main` before argparse runs,
   so no hook call can exit 2. A `hook` parser exists only for `--help`.
3. `tests/test_research_session_hooks.py` (new, 62 tests).
4. 44 input fixtures in `tests/fixtures/hooks/`. `{A}`, `{STATE}` and `{TOKEN}` are filled at test time, so no fixture
   holds a token-shaped string.

Wave H:

5. `json_merge` into `/projects/beto/swong2/Alignment/.claude/settings.json` with `claude-hooks-fragment.json`.
6. `json_merge` into `/u/swong2/.codex/hooks.json` with `codex-hooks-fragment.json`.
7. `write` of `W/.claude/settings.json` from a staged copy that is byte-identical to `F/staged/dc-claude-settings.json`
   (a test checks this). The orchestrator can use this op instead of copying by hand; the apply tool then backs up
   and journals it.
8. `text_block` with marker `autoresearch-workflow-codex-hooks` at the end of `/projects/beto/swong2/Alignment/.claude/CLAUDE.md`,
   with `lint: true`.

No JSON op sets `lint` (01 hand-back, open question 6).

### Scratch files in T

`/u/swong2/.claude/jobs/b2cb53cd/tmp/06/`: `make_fixtures.py` (writes the fixtures), `make_staging.py` (writes the
fragments, the DC settings and the op file), `explore.py` (prints every hook output for review), `merge_copies.py`
(applies the two merges to copies), `fetch_schemas.sh` and `schemas/` (the Codex generated schemas, read only).

## The hooks as built

Every command is the literal guard of spec 5.1 with only the event and `--tool` varying. Timeouts are 10 s, and 20 s
for PreToolUse. Both SessionStart groups share one command, and so do both PostToolUse groups. The script dispatches
on `source` and on `tool_name`, and the apply tool's de-duplication compares matcher plus command (01 hand-back,
open question 2).

| Hook | Event and matcher, Claude | Codex | Behaviour notes |
|---|---|---|---|
| H-a | SessionStart `startup\|resume` | same | At most 600 characters. Never fetches: Claude reads `usage.json` without a refresh; Codex uses only a cached reading under 120 s old. |
| H-b | SessionStart `compact` | same | The only counter. Text up to 1000 characters, because it names the direction directory and two lint results. |
| H-c | PostCompact `manual\|auto` | not installed | Saves `compact_summary`, redacted by the secret patterns, to `<dir>/handbacks/compaction-<N>.md`. Never overwrites: it writes `compaction-<N>.2.md` instead. Subagent compactions (with `agent_id`) are ignored. |
| H-d | PreToolUse `Agent\|Bash\|SendMessage\|Write\|Edit` | PreToolUse `Agent\|spawn_agent\|Bash\|apply_patch` | `gate.safe_evaluate` as built in ticket 02. A Codex `apply_patch` call is split per file, and each file runs `gate.guard_write`; the first denial wins. |
| H-e | PostToolUse `Agent` | PostToolUse `Agent\|spawn_agent` | Uses the reading that the preceding gate call stored in the session file, so it never waits on a refresh. |
| H-f | PostToolUse `Write\|Edit` | PostToolUse `apply_patch` | After an Edit or a patch update, it lints the whole file and reports only findings outside the written text. A Write reports nothing, because H-d already linted the whole text. |
| H-g | UserPromptSubmit | same | Ack rule below. |
| H-h | SubagentStart | same | Records the agent; injects only in registered sessions and not for the four excluded types. |
| H-i | SubagentStop | same | Saves the message, then blocks once when no `*handback*.md` under `<dir>` has changed since the start. Codex always gets JSON. |
| H-j | Stop | not installed | Claude `additionalContext` reminder for a crossed, unrecorded freeze. |

Judgment calls, each tested:

- **R5 scope for subagents.** In an unregistered session, H-h injects nothing, and H-i saves the message privately
  under `<state root>/handbacks/<tool>-<id>/` and never blocks. A quick-question session in A should not be told to
  write hand-backs. H-c uses the same private fallback.
- **The ack rule (R36).** A prompt acks only when the trimmed text starts with the word "continue", does not start
  with `<`, contains none of the four envelopes, and does not end with `?`. A prompt with an `agent_id` never acks.
  So "Continue?" and "continued" do not ack. The word boundary and the question-mark rule are slightly stricter
  than the spec's literal wording.
- **Codex Stop and SubagentStop print `{}`** whenever the script runs, even outside A or with the kill switch, because
  the Codex page says plain text is invalid there. The ticket's "no output outside A" holds for every other pair. When
  the shell guard short-circuits, there is no output at all, which the Codex page calls success.
- **The Claude Stop reminder continues the turn once.** The Claude docs say Stop `additionalContext` "continues the
  conversation". So H-j makes the orchestrator take one more step to record the checkpoint, and the next Stop carries
  `stop_hook_active: true`, so H-j stays silent then. A test covers that sequence.

## Verified harness facts

### Claude Code, https://code.claude.com/docs/en/hooks

- SessionStart matcher values are `startup`, `resume`, `clear`, `compact` and `fork`. Its input has `source` and
  `model`. Its output is context only, via `hookSpecificOutput.additionalContext`.
- PostCompact matches `manual` or `auto`. Its input has `trigger` and `compact_summary`, and it has no decision
  control.
- PreToolUse denies with `hookSpecificOutput.permissionDecision: "deny"` and `permissionDecisionReason`. A timed-out
  PreToolUse hook does not block unless `onFailure: "block"` is set. Exit 2 blocks; other non-zero exits are
  non-blocking errors.
- PostToolUse takes `hookSpecificOutput.additionalContext`, and `decision: "block"` cannot undo the tool.
- UserPromptSubmit has no matcher. It also fires for session-scoped scheduled tasks, a background subagent reporting
  back, and a message from another session. **No origin or source field is documented.** The documented fields are
  the common ones (`session_id`, `prompt_id`, `transcript_path`, `cwd`, `scratchpad_dir`, `permission_mode`,
  `effort`, `hook_event_name`, optional `agent_id` and `agent_type`) plus `prompt` and `session_title`. Envelope
  rejection is therefore the only guard (R36).
- SubagentStart and SubagentStop match on agent type. SubagentStop input has `stop_hook_active`, `agent_id`,
  `agent_type`, `agent_transcript_path`, `last_assistant_message`, `background_tasks` and `session_crons`.
- Stop input has `stop_hook_active`, `last_assistant_message`, `background_tasks` and `session_crons`. Stop accepts
  `hookSpecificOutput.additionalContext`, which continues the conversation under the same loop protections as
  `block`, with an 8-continuation cap.
- Identical handlers in more than one settings file run once. The file watcher picks up direct edits to hooks.
- The tool table names `Agent`, `Bash`, `Edit` and `Write`. `SendMessage` is not in that table; it is the tool name
  this session's own tool list shows.

### Codex CLI 0.166.0, https://learn.chatgpt.com/docs/hooks and the generated schemas

Schemas: https://github.com/openai/codex/tree/main/codex-rs/hooks/schema/generated (the page warns that `main` may be
ahead of the release). `codex features list` shows `hooks` stable and enabled, and `multi_agent` stable and enabled.

| Item | Verified fact | Installed |
|---|---|---|
| Events | PreToolUse, PermissionRequest, PostToolUse, PreCompact, PostCompact, UserPromptSubmit, SubagentStop, Stop, Interrupt, SessionStart, SubagentStart, SessionEnd | see rows below |
| Matchers | `matcher` is a regex; `"*"`, `""` or no matcher match everything; SessionStart matches `source` | yes |
| Shell | shell and unified exec (`exec_command`) match as `Bash`; `tool_name` is `Bash`; the command is `tool_input.command` | `Bash` |
| Edits | `apply_patch` matches `apply_patch`, `Edit` or `Write`; `tool_name` is `apply_patch`; the patch text is `tool_input.command` | `apply_patch` |
| Spawns | `spawn_agent` also matches `Agent`; the page does not state the `tool_name` string, so the gate accepts `Agent`, `Task` and `spawn_agent` | `Agent\|spawn_agent` |
| Messages | no message tool is documented; local rollouts show top-level `send_message` and `followup_task` calls | not installed (R32) |
| Code mode | "hook decisions apply to that nested call" when a tool is called from JavaScript in code mode | covered |
| PreToolUse output | `hookSpecificOutput.permissionDecision` is `allow`, `deny` or `ask`, with `permissionDecisionReason` | yes |
| PostToolUse output | the schema allows `hookSpecificOutput.additionalContext` with `decision` absent; the page's only example pairs it with `block` | yes; the pilot should confirm |
| SessionStart, SubagentStart, UserPromptSubmit output | `hookSpecificOutput.additionalContext` | yes |
| SubagentStop output | JSON required on exit 0; `decision`, `reason` and the common fields only | yes, always JSON |
| Stop output | JSON required on exit 0; no `hookSpecificOutput` (the schema forbids extra keys), so no model-visible text without `block` | **H-j not installed** |
| PostCompact input | `trigger` only, no summary | **H-c not installed** |
| UserPromptSubmit input | `prompt` and `turn_id`; no source field | yes |
| Session ids | subagent hooks carry the parent session id | relied on by H-h and H-i |
| Trust | "Codex records trust against the hook's current hash"; new or changed hooks are skipped until trusted with `/hooks` | user action |
| Fields | `timeout` in seconds, default 600; `additionalContextLimit` default 2500 tokens | timeouts set |

The `apply_patch` grammar comes from `codex-rs/apply-patch/src/parser.rs`
(https://raw.githubusercontent.com/openai/codex/main/codex-rs/apply-patch/src/parser.rs): `*** Begin Patch`, hunks
`*** Add File:`, `*** Delete File:` and `*** Update File:` with optional `*** Move to:`, `@@` context lines, and
`+`, `-` and space lines, then `*** End Patch`.

Local observation: in the 26 October Codex rollout, the shell calls I sampled went through code mode's `exec` with
`tools.exec_command`, and a grep found zero `tools.apply_patch` calls. So on this machine Codex edits usually arrive as
shell commands, which H-d does not lint. The Codex note therefore keeps the lint-after-write rule of the protocol.

### Project-level `.codex/hooks.json` (R4)

The config page (https://learn.chatgpt.com/docs/config-file/config-advanced) says Codex walks from the project root,
a directory with `.git` by default, to the working directory. It loads project `.codex/` layers, including hooks,
only when the project is trusted. `~/.codex/config.toml` trusts only `/projects/beto/swong2/Alignment`.

- **A sessions:** the project root is A, which is trusted, so `A/.codex/hooks.json` would load.
- **DC sessions:** DC has its own `.git`, so the walk starts at DC and never reaches `A/.codex/`. A `DC/.codex/hooks.json`
  would need DC to be trusted. Whether A's trust covers a nested repository is not documented, so this is unverified.
  `DC/.codex/` also holds bridge-managed symlinks only.
- **Worktrees:** a worktree has no `.codex/` directory at all.

The user-level `~/.codex/hooks.json` loads in every project regardless of trust, and the script's cwd check confines
it. So I staged only the user-level placement, as R4 already says.

### Codex instruction text

`A/AGENTS.md` is not a durable home. The bridge rewrites it whole when it owns the file
(`A/.agents/claude_codex_sync.py:383-387`), and that file carries no bridge marker. `AGENTS.md` tells Codex to read
`.claude/CLAUDE.md`, so the note goes there as a marked block (op 8). Its text is in `F/staged/codex-hooks-note.md`
and passes the lint.

## How verified

### Staged RS suite, both interpreters

```
PYTHONDONTWRITEBYTECODE=1 TMPDIR=T/06 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider S/tree/projects/beto/swong2/Alignment/.agents/tests
252 passed, 19 subtests passed in 29.73s
PYTHONDONTWRITEBYTECODE=1 TMPDIR=T/06 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider S/tree/projects/beto/swong2/Alignment/.agents/tests
252 passed in 30.78s
```

The new hook test file alone gave 62 passed on each interpreter, the last time after the H-f test was made exact.
An earlier full run on mgnp had 2 failures in `test_research_session_registry.py`, which another implementer was
editing in staging at 14:45 to 14:46. The rerun above, after that edit, passed.

### Settings, guard, merges and smoke, both interpreters

```
/sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider F/tools/test_hook_settings.py
11 passed in 5.30s
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider F/tools/test_hook_settings.py
11 passed in 4.22s
/sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider F/tools/test_apply_staged.py
33 passed in 4.39s
```

`test_hook_settings.py` checks that every staged command equals the literal guard for its event and tool and holds
no `$`. It checks that the DC settings equal the Claude fragment, and the op fragments equal the staged files. It
checks that no message matcher is installed for Codex, and that waves are A then H with no `lint` on JSON ops. It
merges both fragments in memory into the pre-wave-H contents of `A/.claude/settings.json` and
`~/.codex/hooks.json`, held as literals so the test stays valid after installation. It checks that the bridge
group is unchanged and that a second merge changes nothing, and that the live Codex file still holds the bridge
hook. It runs every unique staged command through
`/bin/sh -c` with the CLI path rewritten to a missing file, then with the kill switch rewritten to an existing file
in a temporary directory, and expects exit 0 with empty stdout and stderr. Finally it runs the smoke script against
the staged `cli.py`.

### The merges applied for real to copies in T

```
/sw/external/python/anaconda3/bin/python3.9 -B T/06/merge_copies.py
run 1 exit 0
[06#1] json_merge .../merge-check/a-settings.json APPLY: +114 -0 lines; + hooks
[06#2] json_merge .../merge-check/codex-hooks.json APPLY: +87 -0 lines; + hooks.SessionStart[] (2 entries appended), + hooks.PreToolUse, + hooks.PostToolUse, + hooks.UserPromptSubmit, + hooks.SubagentStart, + hooks.SubagentStop
run 2 exit 0
[06#1] ... SKIP: already applied
[06#2] ... SKIP: already applied
a-settings.json: valid JSON, existing hook groups kept unchanged: True, other keys unchanged: True, hook groups now 10
codex-hooks.json: valid JSON, existing hook groups kept unchanged: True, other keys unchanged: True, hook groups now 9
```

### Smoke script against the staged CLI

```
/sw/external/python/anaconda3/bin/python3.9 -B F/tools/hook_smoke.py --settings F/staged/claude-hooks-fragment.json F/staged/codex-hooks-fragment.json --cli S/tree/projects/beto/swong2/Alignment/.agents/research_session/cli.py
PASS session-start --tool claude (startup)                      0.21 s
PASS pre-tool-use --tool claude (Agent)                         0.20 s
...
PASS subagent-stop --tool codex (SubagentStop)                  0.36 s
PASS ... (each of the 14 commands, missing CLI and kill switch)
slowest isolated call: 0.36 s (Claude timeout 10 s, 20 s for PreToolUse)
hook smoke: all checks passed
```

### Dry runs (the apply tool needs `--wave`, so there are two)

```
python3.9 -B F/tools/apply_staged.py --staging S --wave A --only 06 --dry-run
dry run, wave A: 47 op(s) selected from 51
[06#1] write .../research_session/hooks.py WOULD APPLY: +762 -0 lines, new file
[06#2] write .../research_session/cli.py WOULD APPLY: +15 -0 lines
[06#3] write .../tests/test_research_session_hooks.py WOULD APPLY: +644 -0 lines, new file
[06#4] ... [06#47] write .../tests/fixtures/hooks/*.json WOULD APPLY (44 new files)
python3.9 -B F/tools/apply_staged.py --staging S --wave H --only 06 --dry-run
dry run, wave H: 4 op(s) selected from 51
[06#48] json_merge /projects/beto/swong2/Alignment/.claude/settings.json WOULD APPLY: +114 -0 lines; + hooks
[06#49] json_merge /u/swong2/.codex/hooks.json WOULD APPLY: +87 -0 lines; + hooks.SessionStart[] (2 entries appended), ...
[06#50] write .../autoresearch-workflow/.claude/settings.json WOULD APPLY: +116 -0 lines, new file
[06#51] text_block /projects/beto/swong2/Alignment/.claude/CLAUDE.md WOULD APPLY: +13 -0 lines
```

## Wave H procedure and smoke command for the orchestrator

1. Apply wave A for 06 (together with or after 02 and 03). Op 2 refuses if the installed `cli.py` is no longer the
   ticket 03 file.
2. Run the RS tests from the installed path on both interpreters.
3. Run the smoke test against the staged fragments. The commands in them point at the installed CLI, so this
   exercises the installed code without any hook being active:

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/hook_smoke.py --settings /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/staged/claude-hooks-fragment.json /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/staged/codex-hooks-fragment.json --live
```

   Expect `hook smoke: all checks passed` and exit 0. The isolated runs feed `F/tools/hook_smoke.json` to the guarded
   PreToolUse command with a fresh 85% usage fixture and expect the exact cap denial. `--live` adds one real-environment
   PreToolUse call with the same input and accepts exit 0 with no output or valid JSON, timed. That call reads the
   real `usage.json` and may refresh it through the OAuth endpoint, as any real hook call would. The script removes
   its session file afterwards. If any line says FAIL, do not apply wave H.
4. Apply wave H for 06. The hooks hot-reload in Claude sessions rooted in A at once.
5. Run the smoke script again with no `--settings`, which reads the installed files.
6. In a fresh Codex session, open `/hooks` and trust the six new groups. Until then Codex skips them.

The kill switch, if a hook misbehaves, is a human command typed in the prompt:

```
! touch /u/swong2/.claude/research-session/DISABLED
```

### Final state of the staged files

```
sha256 S/tree/.../research_session/cli.py    664ca82c7ba3a30e1b6a9f4e968587422dee7d5c1ff51faf82b905c38ef1b87e
sha256 S/tree/.../research_session/hooks.py  e255196b84537a895e0bc37c6ff8966306b550b43df5988146ff5b73856f626e
sha256 installed A/.agents/research_session/cli.py (ticket 03, the op's expect_sha256)  87c7964227a6...
```

The full staged suite was run again after these hashes were taken: 252 passed with 19 subtests on mgnp, and 252
passed on base python3.9.

## Execution evidence

Not applicable: no runs. No Slurm job, GPU job or paid API call was made.

## What is NOT done

- Nothing is applied or installed. Wave A and wave H are the orchestrator's.
- The fixtures follow the documented examples and the Codex schemas. They are not live recordings, because recording
  needs an installed hook. The pilot (ticket 11) should record one real payload per event, and especially check
  whether a real UserPromptSubmit payload carries any undocumented origin field.
- Codex H-c and H-j are implemented in the script (Codex PostCompact no-ops; Codex Stop returns `systemMessage` or
  `{}`) but not installed, for the schema reasons above.
- Codex PostToolUse with `additionalContext` alone is schema-verified only. The pilot should confirm that Codex shows
  it to the model.
- `--live` smoke was not run by me, because it may use the real token (brief constraint 11).

## Open questions

1. **Bridge reordering and Codex trust.** The bridge removes and re-appends its own SessionStart group on every run,
   so our groups move position in `~/.codex/hooks.json`. Codex keys trust to each hook's hash. Whether the hash covers
   position is undocumented. If Codex asks for trust again after a bridge run, that is the cause.
2. **Hooks before the DC merge.** Claude reads project settings from the session's repository root. After wave H, the
   hooks are active in A sessions and in this worktree only. DC main and other worktrees get them only when
   `W/.claude/settings.json` is committed and merged.
3. **An import-time failure of `cli.py`** exits 1 before any hook code runs. That is non-blocking, but it would show a
   hook-error notice on every tool call in every A session. The smoke test before wave H is the guard; the kill switch
   is the remedy.
4. **Lint coverage for Codex.** Codex shell writes are not linted before the write. The note asks Codex to run the
   lint after every write, as the protocol already does.
5. **Ordering with ticket 09.** Ticket 09 trims `A/.claude/CLAUDE.md`. Apply 09's CLAUDE.md op before 06's wave H
   `text_block`, never after: a whole-file write with `expect_sha256` would conflict with the block in place.
6. **`clear` and `fork` sources** get no H-a text under the spec's matcher. A forked session gets a new session file
   at its first gated call.
