# 00 — Plan review (builder check, fresh Opus reviewer, 2026-10-31)

Inputs read: `reports/proposal-full.md`, `spec.md`, `agent-brief.md`, tickets 01-12, `reports/00-plan-handback.md`,
`reports/00-orchestrator-rulings.md`, `reports/lane2-harness.md` in full, lane 3 §4 and lane 4 §0-§3, `WORKLOG.md` and
`RESUME.md`. Live docs fetched: the Claude hooks page (all three parts), the Claude settings reference (index part),
and the Codex hooks page. No file other than this one was written. No git command was run.

## Verdict

**Approve with fixes.** The spec carries the user's main decisions faithfully. The checkpoint is a freeze enforced by
a PreToolUse deny with a human-only acknowledgement. Superpowers stays on in every profile. Both caps are 80%. The
Fable-close rule is in §5.4. The worklog keeps day sections, a header block and both registers. The science guards
run in the first wave. The blockers below are ordering and consistency problems, not design problems. Two of them
can lock live sessions out of their own tools, so fix them before any agent starts.

## Blockers (fix before implementation)

1. **Hook install order can lock the orchestrator out of its own tools.** I verified that base python3.9 exits with
   code 2 when its script file is missing. The hooks page says exit 2 from PreToolUse blocks the tool call, and that
   direct edits to settings hooks are picked up by the file watcher. Ticket 06 writes `W/.claude/settings.json`
   directly in the worktree, which is this session's project directory, before wave A installs
   `A/.agents/research_session/cli.py`. From that moment every Agent, Bash, SendMessage, Write and Edit call in the
   orchestrator and the ticket 06 implementer would be denied. The kill switch cannot help, because it is checked
   inside the missing script. The same happens if `--only 06` is applied before tickets 01-03.
   Fix in `spec.md` §5.1 and R4, and in `issues/06-hooks-both-tools.md`:
   - The hook `command` becomes a shell guard that exits 0 when the CLI is absent or the kill switch exists, for
     example `/bin/sh -c 'test -f CLI || exit 0; test -e DISABLED && exit 0; exec PY -B CLI hook EVENT --tool claude'`,
     or a staged wrapper `~/.local/bin/research-session-hook` from ticket 02 with the same logic.
   - Ticket 06 stages the DC settings content in `F/staged/dc-claude-settings.json`; the orchestrator copies it to
     `W/.claude/settings.json` only after wave A and the smoke test pass.
   - Ticket 06's op file orders RS code before the `json_merge`, and ticket 12's merge checklist applies 01, 02, 03
     and 11 code before any settings merge.

2. **The orchestrator's OQ2 ruling contradicts R8 and ticket 02.** OQ2 says RS fetches the usage endpoint itself
   when `usage.json` is older than 15 minutes. R8 says RS never fetches it, and ticket 02 has no fetch, no HTTP mock
   and no credentials rule. Fix `spec.md` R8 and §5.2 "Reading (Claude)", and add to `issues/02-*.md`:
   - The OAuth cache body already carries `five_hour`, `seven_day` and a `limits` list whose kinds are `session`,
     `weekly_all` and `weekly_scoped` (I printed key names only). One fetch can refresh all three fields.
   - Reuse the status line's cache file `~/.claude/.usage_oauth_cache.json`, its lock file with the 60 s stale
     sweep, and its 300 s retry floor (`~/.claude/statusline.sh:19-22`, `:41-113`). Bound the request at 8 s so the
     gate stays inside its 20 s timeout.
   - The token is read inside the process, never printed, logged or put on a command line. The implementer does not
     open `~/.claude/.credentials.json`; tests mock both the credentials reader and the HTTP call.
   - The write-back to `usage.json` is atomic and keeps every existing key.

3. **The OQ3 ruling contradicts ticket 10, and the same live-session concern reaches ticket 01.** Ticket 10 and R3
   list the ten `sdr-*` study directories as migration candidates and exclude only `sdr-session-wrapup` and
   `selective-deception`. OQ3 excludes every `sdr-*` directory and `selective-deception` until the user confirms
   the Codex session is finished. The 12-hour liveness check will not catch them, because their mtimes run from
   20 to 26 October. OQ3 also limits wave B to closed or paused directions, but `eval5-grader-fixes` is `open` per
   ticket 05, so it is excluded too. Ticket 01 rewrites `sdr-mechanism-review.md` and
   `selective-deception-execution.md` into pointer notes and edits the SDR and selective-deception lines of
   `MEMORY.md`. Those are the live session's own logs; `sdr-mechanism-review.md` was last written at 08:35 today.
   Fix:
   - `issues/10-*.md` and R3: move the ten `sdr-*` directories and `eval5-grader-fixes` to the excluded list, and
     give the later one-line command.
   - `issues/01-*.md`: put the two pointer-note writes and the two MEMORY.md line rewrites in a separate op group
     gated on the same user confirmation, for example wave B. `expect_sha256` catches a concurrent write, but not a
     later Codex append to what has become a pointer note.

4. **The claim-tag format disagrees between OQ1 and the spec.** §4.2 says `claimed_by` is `<tool>-<first 8
   characters of the session id>`, and §4.5 keys `sessions` by the same tag. OQ1 rules
   `claude-autoresearch-setup-20261031` and the format `<tool>-<slug>-<YYYYMMDD>`. Ticket 03's validator rejects
   one or the other, and ticket 05 seeds the row. Fix one format in `spec.md` §4.2, §4.5 and R5, then in tickets 03
   and 05. I recommend keeping the session-id form as the machine key, because R5 resolves sessions by id. The
   human-readable label can become a separate optional field. This session's id begins with `b2cb53cd`, so the tag
   would be `claude-b2cb53cd`.

5. **H-f cannot block a write, so the glue lint does not stop glued text from landing.** The hooks page says
   PostToolUse `decision: "block"` only adds `reason` next to the tool result, and the tool has already run. Ticket
   06 ("H-f blocks a glued WORKLOG paragraph") and ticket 11 step 6 ("is blocked") state an outcome that cannot
   happen. Fix in `spec.md` §5.1 and tickets 06 and 11: lint `tool_input.content` and `tool_input.new_string` in the
   PreToolUse hook H-d, which already matches Write and Edit, and deny with the failing units. Keep the PostToolUse
   hook for the secret-scan report and for whole-file checks after an Edit. The Codex hooks page says `apply_patch`
   also matches `Edit` and `Write`, so the same route works there once the patch input shape is checked.

6. **The OQ8 ruling says extend `autoMode.environment`, but the spec replaces it.** `spec.md` §7 and ticket 01 put
   `autoMode.environment` in `replace_paths`. I confirmed it is a list. The default `json_merge` already appends
   list entries that are not present, which is exactly "extend". Fix `issues/01-*.md`: drop it from `replace_paths`.
   Add an acceptance check that every existing entry is still present byte for byte after the merge (compare
   hashes, print nothing). The phrase "adds only the four keys" should read "adds three keys and appends entries to
   one list".

7. **The worklog writer has no way to add findings, needs or struck-through needs.** The user asked for a findings
   register, process incidents and struck-through needs. Ticket 03's kinds are `entry`, `checkpoint`, `handback`,
   `job`, `compaction`, `decision`, `incident` and `switch`. None adds a findings row or a need, and none resolves a
   need. The ticket also calls the body append-only without saying whether the registers belong to the rewritten
   head or the append-only log. A need cannot be struck through in an append-only region. Fix in `spec.md` §5.6 and
   `issues/03-*.md`:
   - Add `--kind finding` and `--kind need`, plus `worklog-append <dir> --resolve-need N1 --answer ...`.
   - State that everything above `## Log` is regenerated from `state.json` fields, and only the Log is append-only.
   - State that `--kind incident` adds a Process incidents row as well as a log entry.
   - Set the time format to 12-hour with a computed zone (`%-I:%M %p %Z`, lowercase am and pm), matching `F/WORKLOG.md`.

8. **The FREEZE text omits "ends its turn" and what workers do on HOLD.** D2 says the orchestrator finishes the step
   in flight, writes the block, tells workers to hold and ends its turn. Spec §5.2 lists only denials and says
   "everything else is allowed", so it reads as a gate that allows other work, which is what the user rejected. Fix
   `spec.md` §5.2 and `issues/08-*.md`. After `worklog-append --checkpoint N` and the HOLD messages, the
   orchestrator ends its turn. A worker that receives HOLD writes its hand-back at a clean point and stops. Running
   Slurm jobs and running agents are not cancelled. The H-g freeze notice already says "answer questions only";
   the protocol must match it.

9. **The migration copies too little text into the docs to count as moving the text.** The user decided to "move
   .scratch text into Deception-Circuit docs". R3 archives the whole directory byte for byte, which is sound because
   of the hash-pinned receipts. But ticket 10's curated subset keeps only names like `spec*`, `plan*` and `RESUME*`,
   plus `issues/*.md`. It drops `reports/`, `reviews/` and `handbacks/`, which hold most of the findings. Fix in R3
   and `issues/10-*.md`: copy every `*.md` at any depth, plus JSON ledgers under 200 KB, within the existing size
   caps and the secret scan. Report what the caps excluded. Also resolve the `autoresearch-workflow` symlink target:
   ticket 10 points it at `DC/docs/research/autoresearch-workflow`, while R3 says every symlink points into
   `outputs/_studies`. Either is fine, but R3 must name the exception.

## Deviations from the approved proposal (A)

The spec records most of these as rulings, and I accept them. The user should still hear about each one.

- **Symlink target.** `.scratch/<slug>` points into the ignored archive, not into `docs/research` (R3). The verified
  selective-deception precedent and the hash-pinned receipts justify it. Blocker 9 covers the text coverage.
- **Two-stage SendMessage denial** (R6). This reconciles D2 with H4. Blocker 8 covers the missing turn end.
- **Provenance file name.** It is `run_manifest.json`, not `manifest.json` (R2), because the name collision is real.
- **Status vocabulary.** `verified` and `replicated` are separate statuses (R17).
- **GitHub token.** It stays in the user settings `env` block (OQ5), against proposal §5. The bridge needs it.
- **Stale threshold** is 15 minutes, and unknown readings deny spawns (R8, as amended by OQ2).
- **nnsight** is off by default and on only in the research profile (OQ6).
- **Codex profiles** may be reported "not available" (§5.7), which is weaker than D6's "both tools".
- **The Fable-close rule** is advisory in hooks and mandatory only in the protocol (§5.4). This matches D8's wording.

## Ticket executability and dependencies (B)

- **Ticket 11** edits `directions.json`, as do tickets 05, 10 and 12. Its Blocked-by line lists 06, 07 and 08 but
  not 10. The planned waves serialize them, but the ticket text alone does not. Add 10 to 11's Blocked-by line.
- **Ticket 01 is the heaviest.** It holds the lint, an apply tool with eight op kinds, rollback and journal, the
  memory rewrites, three config merges and an optional bridge edit. Its 50k writing estimate is optimistic. Keep it
  whole, but tell the implementer to hand back after the lint and the apply tool if the projection passes 250k.
- **R18 is not literally true.** Tickets 01, 02, 03, 06 and 11 all write the staged `cli.py`. This is safe because
  they run in sequence and every write op reads the latest staged file. Say so in R18, so no reviewer flags it later.
- **Ticket 08** stages `ticket-implementer.md` as a whole-file write but does not require `expect_sha256`. Add it.
- **Ticket 09** moves tracked `project_context` files out of the Alignment repository. Ticket 12's checklist should
  list the matching Alignment commit as a user-approved step.
- **The acceptance criteria are otherwise concrete.** Every ticket names its files, test commands for both
  interpreters and a dry-run command. I found no other missing path.

## Hook contracts and settings keys (C)

Checked against the live pages fetched today.

| Claim in spec or lane 2 | Result |
|---|---|
| SessionStart sources include `compact` | Confirmed. The matcher list is startup, resume, clear, compact and fork. |
| PostCompact has `compact_summary`, matcher `manual|auto`, no decision control | Confirmed. |
| SubagentStart can return `additionalContext`; its matcher is the agent type | Confirmed. |
| SubagentStop input has `stop_hook_active`, `agent_transcript_path` and `last_assistant_message` | Confirmed. |
| Stop is silent "when background tasks exist" | Confirmed. The fields are `background_tasks` and `session_crons`; name both in §5.1 H-j. |
| PreToolUse deny shape uses `permissionDecision` and `permissionDecisionReason` | Confirmed for both tools. |
| PostToolUse `decision: "block"` blocks the write | Wrong. It only adds a reason (blocker 5). |
| Any exit other than 0 or 2 is non-blocking | Confirmed. Exit 2 blocks (blocker 1). A timed-out gate therefore fails open; the pilot should time the hook on Lustre. |
| Settings hooks need a restart | Wrong. They are picked up by the file watcher (blocker 1). |
| UserPromptSubmit fires only for human prompts | Wrong. It also fires for scheduled tasks, background subagent reports and messages from other sessions. No documented field tells them apart. H-g must ack only when the prompt text itself starts with "continue". It must never ack a prompt that starts with `<`, and ticket 06 needs fixtures for teammate, task-notification and cross-session wrappers. The pilot keeps this item. |
| SendMessage is matchable in Claude PreToolUse | Not documented. The page says the matcher covers any tool except EndConversation, so it should work. The pilot must observe it. |
| Codex has only a user-level `hooks.json` (R4) | Wrong. The Codex page lists `<repo>/.codex/hooks.json`, which loads when the project layer is trusted. R4's conclusion still holds, because the cwd check confines the user-level hooks. Fix the sentence. |
| Codex `spawn_agent` matches `Agent` | Confirmed. |
| Codex patch tool name | `apply_patch` matches `apply_patch`, `Edit` and `Write`. |
| Codex SendMessage equivalent | Not documented. Per R12, do not install the stage-recorded message denial for Codex; state in ticket 08 that Codex freezes deny spawns and `sbatch` only. |
| Codex `additionalContextLimit`, default 2500 tokens | Confirmed. |
| `autoMode` is user or managed scope | Confirmed from the settings index. |
| `skillOverrides` and `enabledPlugins` allowed in any settings file | Confirmed from the settings index. |
| A documented off switch for a user-scope MCP server | `deniedMcpServers` ("block specific MCP servers by URL, command, or name") exists. Point ticket 07 at it before the `permissions.deny` fallback. |

I could not confirm `statusLine.refreshInterval`, `CLAUDE_CODE_SUBAGENT_MODEL` or the `--settings` merge behaviour,
because those parts of the settings page were past the fetched range. Lane 2 cites the status line and sub-agents
pages for the first two, and ticket 07 already owns the third.

## Safety and isolation (D)

- **Agent constraints are respected.** No ticket asks an agent to run git. Every Alignment and user-config file is
  staged with a backup, a journal and JSON merge. `MEMORY.md` changes only through `replace_text` and `append_text`.
  The `env` block is compared by hash and never printed. No ticket submits a GPU job.
- **Blockers 1 and 3 are the two real risks.** Blocker 1 can lock live sessions out of their tools. Blocker 3 can
  disturb the live Codex session's directories and memory logs.
- **Wave A changes other Claude sessions immediately.** Because hooks hot-reload, every Claude session rooted
  anywhere under A picks up the gate when wave A lands. An unregistered session then starts counting checkpoints
  from its first hook call and freezes after 16 points. Either apply wave A when no other A-rooted Claude session is
  live, or give unregistered sessions only the cap and stale gates. Ask the user which.
- **The self-ack guard matches too broadly.** It matches `docs/research/*/state.json`, which includes
  `docs/research/_templates/state.json`. It also denies `research-session validate` on any `state.json` path.
  Exclude `_templates` and allow read-only RS subcommands.
- **Bytecode files in Alignment.** RS will write `__pycache__` under `A/.agents/research_session/`, which A's
  `.gitignore` does not cover. Run python with `-B` in the hook command, or add the ignore line.
- **Nothing pushes to main.** R23 commits claims on DC main under the user's standing policy, and the merge stays a
  user decision in ticket 12.

## Spot checks (E)

| # | Claim | Result | Evidence |
|---|---|---|---|
| 1 | `.scratch/selective-deception` points into `outputs/_studies` | Pass | `ls -la A/.scratch` shows the target `DC/outputs/_studies/selective-deception/study`. |
| 2 | `A/.scratch` has 17 real directories and one symlink | Pass | The same listing. `sdr-session-wrapup` has an mtime of 08:35 today. |
| 3 | `make_run_dir` creates the run directory and writes only `config.json` | Pass | `W/run_io.py:172-186`. |
| 4 | Manifest field names in the SDR pilot | Pass, with a note | `W/scripts/sdr_routing_pilot.py:392-403` has `git_commit`, `dirty_diff_hash`, `git_fingerprint_error`, `code_sha256`, `software`, `model_cache`, `model_revision`, `tokenizer_files` and `manifest_hash`. `git_dirty`, `config_sha256`, `dataset_files` and `seed` are new names in §4.6, not reused ones. |
| 5 | `judge_spec()` call sites | Pass, incomplete | `W/evaluate_circuit.py:627` (the statement starts at 626) and `:657`, plus a third at `:916` that the handback omits. |
| 6 | Where evaluation output directories are created | Pass | `W/evaluation/suite.py:93`, `:189` and `:315`. `evaluate_circuit.py` itself has no `makedirs`. |
| 7 | Grader files exist | Pass | `W/evaluation/benchmark_eval.py` and eight modules in `W/evaluation/benchmarks/`. |
| 8 | `~/.codex/hooks.json` exists | Pass | 364 bytes, dated 17 October. |
| 9 | DC has no `.claude/settings.json` | Pass | `DC/.claude` holds only `worktrees`. |
| 10 | Three agent definitions say `model: sonnet` | Pass | Line 4 of `idea-critic.md`, `paper-reader.md` and `paper-searcher.md`. `ticket-implementer.md:4` says `opus`. |
| 11 | `A/.claude/settings.json` only disables karpathy | Pass | I read the file. |
| 12 | Memory log sizes | Pass | The files are 74,322 and 45,255 bytes. `sdr-mechanism-review.md` changed at 08:35 today. |
| 13 | Remotes carry no token | Pass | `A/.git/config:8` and `DC/.git/config:7`, read as files. |
| 14 | User settings keys; `autoMode.environment` | Pass | 14 top-level keys match the handback. `autoMode.environment` is a list (blocker 6). |
| 15 | A missing hook script blocks | Confirmed hazard | base python3.9 on a missing file exits 2 (blocker 1). |
| 16 | A fetch can refresh all three usage fields (OQ2) | Pass | The cache body has `five_hour`, `seven_day` and `limits` kinds `session`, `weekly_all` and `weekly_scoped`. `usage.json` was 155 s old at the check. |
| 17 | Test files locate the code from their own path | Pass | `A/.agents/tests/test_codex_usage.py:8`. |
| 18 | The bridge has `--check` | Pass | `A/.agents/claude_codex_sync.py:535`. |

## Non-blocking suggestions

- Put the Stop field names `background_tasks` and `session_crons` into §5.1 H-j, so ticket 06 need not search for them.
- Add a pilot step that times one gate call on Lustre. A timed-out gate allows the call.
- In ticket 11, add a pilot step where a teammate or another session sends "continue" during a freeze. The expected
  result is no acknowledgement.
- Give ticket 05 the tag decided in blocker 4, so it does not need to ask.
- Name `evaluate_circuit.py:916` in ticket 04 as a third grader call site to check.
