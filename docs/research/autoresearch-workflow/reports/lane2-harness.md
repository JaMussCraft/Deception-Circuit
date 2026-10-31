# Lane 2: Harness mechanics for long multi-agent research sessions (Claude Code 2.1.316, Codex CLI 0.166.0)

Checked 2026-10-31. **[doc]** means from current docs, **[local]** means seen on this machine, **[unverified]** means neither. Nothing was changed.

Doc sources (cached in `tmp/docs/`):
- Claude hooks: https://code.claude.com/docs/en/hooks
- Subagents: https://code.claude.com/docs/en/sub-agents
- Settings reference: https://code.claude.com/docs/en/settings-reference
- Model config (auto-compact window): https://code.claude.com/docs/en/model-config
- Scheduled tasks: https://code.claude.com/docs/en/scheduled-tasks
- Tools reference (background Bash, ScheduleWakeup): https://code.claude.com/docs/en/tools-reference
- Workflows: https://code.claude.com/docs/en/workflows
- Agent teams: https://code.claude.com/docs/en/agent-teams
- Status line: https://code.claude.com/docs/en/statusline
- Commands: https://code.claude.com/docs/en/commands
- Codex hooks: https://learn.chatgpt.com/docs/hooks (developers.openai.com/codex/hooks redirects here)
- Codex subagents: https://learn.chatgpt.com/docs/agent-configuration/subagents

---

## 1. Compaction counter and forced state flush

### Claude Code [doc, hooks page]

| Event | Matcher | Input that matters | Can it inject context? | Can it block? |
|---|---|---|---|---|
| `PreCompact` | `manual`, `auto` | `trigger`, `custom_instructions` (null for auto) | No. Its `systemMessage` and `continue` are discarded. | Yes, with exit 2 or `decision:"block"` |
| `PostCompact` | `manual`, `auto` | `trigger`, **`compact_summary`** | No. It has no decision control. | No |
| `SessionStart` | `startup`, `resume`, `clear`, **`compact`**, `fork` | `source:"compact"`, `model` | **Yes.** Plain stdout or `hookSpecificOutput.additionalContext` | No |

All events also receive `session_id`, `transcript_path`, `cwd`, and `agent_id`/`agent_type` when fired inside a subagent.

Do not block `auto` PreCompact. The docs say that when compaction runs to recover from a context-limit error, blocking it makes the request fail.

**Recommended pattern:**
1. A `SessionStart` hook with matcher `compact` does the counting. It fires exactly once per compaction, so it increments `compactions` in a per-session state file keyed by `session_id`, for example `.agents/sessions/<session_id>.json`. It then injects the new count, the active RESUME path and the RESUME validation result from section 7. It also tells the model to re-read RESUME.md and the last handbacks before acting. Inject a pointer, not the file contents. This replaces the hand-maintained "Orchestrator auto-compact count" line in `.scratch/mechanism-analysis/RESUME.md`. The existing bridge SessionStart hook already matches `compact`, so this can be a second entry.
2. A `PostCompact` hook only appends `compact_summary` to the session worklog, `<date>-<session_id>-worklog.md`. The docs don't state whether PostCompact fires before or after SessionStart(compact), so nothing should depend on that order.
3. The orchestrator registers its RESUME path once at session start in the state file, so the hook knows which feature directory belongs to the session.
4. Put all new hooks in `~/.claude/settings.json`, where the bridge hook lives. Most sessions start in `Deception-Circuit`, a separate git repo, and project settings files are read only from the session's starting directory and repo root.

**[unverified]** The docs don't say whether PreCompact or PostCompact fire for subagent compactions, though `agent_id` would identify them if they do. Test this by logging `agent_id` from the hook.

### Codex [doc, Codex hooks page]

Codex has `PreCompact`, `PostCompact`, `SessionStart` (sources `startup|resume|clear|compact|fork`), `SubagentStart`, `SubagentStop`, `Stop`, `PreToolUse`, `PostToolUse`, `PermissionRequest`, `UserPromptSubmit`, `Interrupt` and `SessionEnd`.

- **PreCompact and PostCompact:** these receive `trigger` and `turn_id`, but no summary. Plain stdout is ignored. Use PostCompact only for side effects such as incrementing a counter.
- **Context budget:** a Codex handler returning `additionalContext` is capped at a default of 2500 tokens. Set `additionalContextLimit` explicitly on each handler.
- **SessionStart compact:** after "Codex compacts a root session", SessionStart hooks matching `compact` run before the next model request, even mid-turn. Their `additionalContext` reaches the immediate continuation. This is the flush and re-read hook. It is documented for root sessions only.
- **Trust:** Codex requires `/hooks` trust for every non-managed hook, keyed to the hook's hash. Any new or edited hook in `~/.codex/hooks.json` is skipped until the user trusts it again. **[local]** `~/.codex/hooks.json` holds only the bridge SessionStart hook, with matcher `startup|resume|clear|compact`. Its trust state could not be read from config.

## 2. Usage-checkpoint enforcement (16% Claude, 25% Codex)

**Key inversion [doc]:** On `Stop` and `SubagentStop`, `decision:"block"` (or exit 2) makes the agent **keep going**, with `reason` as its next instruction. A Stop hook cannot force a pause. In Codex, Stop `block` likewise "creates a new continuation prompt".

**The mechanism that actually enforces a pause [doc]** is `PreToolUse` with matcher `Agent` returning `permissionDecision:"deny"` plus a reason, or exit 2.
- Claude Code fires tool hooks inside subagents too, with `agent_id` set. One deny rule therefore stops nested spawns as well.
- In Codex, the `spawn_agent` tool also matches `Agent`, and PreToolUse deny uses the same JSON shape. One script can serve both tools.
- Extend the matcher to Bash commands containing `sbatch`, so no new GPU spend starts while the session is paused.
- Do **not** block `SendMessage`, because the orchestrator needs it to tell agents to hold.

**Suggested hook set (contracts verified, scripts not written or tested):**
1. **`PreToolUse` with matcher `Agent|Bash`.** The script ignores Bash calls unless `tool_input.command` contains `sbatch`. Read the weekly reading. For Claude, take the max of `seven_day` and the Fable `model_scoped` row from usage.json. For Codex, run `codex-usage`. Compute `bucket = floor(pct/16)` for Claude or `floor(pct/25)` for Codex. If the bucket is above `acked_bucket` in a state file, deny with the message "Usage checkpoint N crossed at X%. Write RESUME.md, tell agents to hold at a clean checkpoint, report to the user, end the turn." Also deny when 5-hour usage is at least 80% or weekly is at least 75%. The user acknowledges by running a tiny command such as `! usage-ack` that sets `acked_bucket`. That keeps the human in the loop.
2. **`PostToolUse` on `Agent`.** Emit `hookSpecificOutput.additionalContext` with the current reading. The docs recommend this route for injecting into the parent after a subagent returns. Caveat: for background subagents the Agent call returns at spawn time, not at completion.
3. **`Stop` with `additionalContext` only, never `block`.** When a checkpoint is pending, remind the model to write state. Check `stop_hook_active`, and stay silent when `background_tasks` or `session_crons` are non-empty, so it doesn't nag while legitimately waiting on Slurm. An 8-consecutive-continuation cap applies (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`).
4. **Staleness guard.** The status line goes quiet while the main session idles on background subagents, which is exactly when usage climbs. Add `"refreshInterval": 60` to `statusLine` (documented field). That keeps the Fable `model_scoped` row fresh, because the script fetches it from the usage endpoint itself. It may not refresh `five_hour`, which comes from the session payload after API responses. **[unverified]** The docs don't say whether subagent traffic updates that payload while the main session idles. So the hook must treat `five_hour` as unknown when `timestamp` is older than about 10 minutes, and deny in that case, matching `codex-usage` exit 1 semantics.

Hook input carries no rate-limit fields [doc]. The status-line payload is the only source, which is why usage.json and the refresh interval matter.

**Related default [doc]:** `autoContinueAtUsageLimit` defaults to `true`. At a hard 100% limit, Claude Code waits in the open session and resumes automatically at the reset. Workflow runs also pause and resume on their own. If the user wants a human gate after a hard-limit stop, set it to `false` in user settings.

## 3. Subagent hand-back reliability

**Documented failure modes [doc, subagents page]:**
- **Foreground cut off by an API error:** the parent gets partial text with a note. With no text, the call fails with `Agent terminated early due to an API error`. Background agents are marked failed, and the notification includes their last output.
- **`maxTurns` hit:** the output is marked partial and can be resumed.
- **Background results** arrive as a later completion notification. They add to the parent's context, so many verbose reports consume it.
- **Names after a restart:** names given since the last orchestrator compaction survive a restart. Older names don't. Agent IDs always work. They are listed in `~/.claude/projects/<proj>/<session>/subagents/agent-<id>.meta.json`.
- **Agent teams (experimental):** `/resume` does not restore in-process teammates, and task status "can lag". For multi-day durable work, prefer background subagents, which can be resumed by ID, over teammates.

**Recommended pattern:** keep the existing "agent writes `reports/*handback*.md` and returns a pointer" convention, and enforce it with a hook.
- `SubagentStop` input has `last_assistant_message` and `agent_transcript_path` in **both** Claude and Codex [doc].
- A command hook writes `last_assistant_message` to `.scratch/<feature>/handbacks/<agent_type>-<agent_id>.md`. The report then survives orchestrator compaction and truncation, whether or not the agent followed instructions.
- It can also use `decision:"block"` once, guarded by `stop_hook_active`, when the agent's required handback file is missing. That sends the agent back to write it.
- Codex SubagentStop must print JSON on exit 0, because plain text is invalid there.
- Claude SubagentStop also fires for internal agents, so filter on `agent_type`.

**SendMessage versus a fresh spawn [doc]:** `SendMessage` to a finished agent resumes it with full history and a warm cache. Use it for same-thread follow-ups while that agent's context is under about 60% full. Spawn fresh for independent review or near its compaction window. Explore and Plan agents cannot be resumed.

**Codex `followup_task` versus `send_message`:** **[unverified]** The docs don't name these tools. The claim that `send_message` only queues and does not wake an idle agent comes from the user's memory note.

## 4. Waiting on long Slurm jobs without polling

**Claude Code:**
- **Best option:** run `sbatch --wait …` (or `until sacct -j $ID -n -o State | grep -qE 'COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL'; do sleep 300; done`) through Bash with `run_in_background: true`. This produces exactly one completion notification and uses no tokens while waiting.
- **Time limits [doc]:** local terminal, desktop and IDE sessions have **no** background time limit. Unattended sessions (`-p`, SDK, CI, cloud) get a 30-minute default and a 2-hour maximum, raised with `BASH_MAX_TIMEOUT_MS` and `BASH_DEFAULT_TIMEOUT_MS`. **[unverified]** The docs don't say whether an agent-view background session counts as unattended. Pass an explicit `timeout` anyway.
- **Monitor:** expires after at most 30 minutes. Use it only for log streams.
- **`/loop`, `CronCreate` and `ScheduleWakeup`:**
  - They are session-only and expire after 7 days.
  - They fire only while the session is idle.
  - A self-paced `/loop` is **not restored** on `--resume`.
  - Background Bash commands and monitors are **not restarted** on resume. This matches the "background waiters died" note in the mechanism-analysis RESUME.
  - So every waiter must be re-armable from RESUME.md: record job IDs, the waiter command and the expected terminal states.
- **Reset waits:** a one-shot `CronCreate` at `resets_at` works within one session.

**Codex:** **[unverified]** There is no documented scheduler. The local logs show `sleep` and `wait` tools. Background hooks (`async = true`) deliver output only at the next safe point or user turn and cannot start a turn, so they are not a wake-up mechanism. A long blocking `exec` of `sbatch --wait` is the practical equivalent, though its timeout behavior is undocumented.

## 5. Plugins and MCP: what to add, what to trim

**[local] Enabled plugins (12):**

| Plugin | Size or hooks |
|---|---|
| academic-research-skills (ARS) | 30 skills or agents, about 11.2k characters of descriptions. SessionStart announce hook. **PreToolUse guard on every Write, Edit and Bash**, about 0.11 s per call. |
| mattpocock-skills | 35 items, about 6.2k characters |
| superpowers | about 2.3k characters. Its SessionStart hook injects about 3.6k characters on startup, clear **and compact**. |
| academic-writing-agents | 13 items, about 1.9k characters |
| nnsight | 7 items, about 1.6k characters |
| context7, github (MCP), code-review, skill-creator, claude-md-management, claude-code-setup, cc-plugin-you-should-know | smaller |

Descriptions total about 25k characters, roughly 6–7k tokens. The bigger cost is behavioral: auto-trigger skills such as superpowers' `brainstorming` ("MUST use before any creative work") or ARS pipelines can pull an autonomous orchestrator into heavyweight processes.

**Per-session-type profiles.** `enabledPlugins` has scope "Any file" [doc]. **[local]** Alignment's `.claude/settings.json` currently only disables the karpathy plugin, and `Deception-Circuit` has no project settings. Project files are read from the session's starting directory and repo root, so a profile in Alignment would not reach Deception-Circuit sessions. The portable route is `claude --settings ~/.claude/profiles/<type>.json`, which sits above project and user files for that one session. The user-level defaults stay unchanged.

| Session type | Keep | Disable |
|---|---|---|
| Research or experiment orchestration | nnsight, context7, claude-md-management, code-review | ARS, academic-writing-agents, mattpocock-skills, superpowers (keep only if its planning skills are wanted), github (unless PR work) |
| Synthesis or writing | ARS, academic-writing-agents, context7 | nnsight, mattpocock-skills, superpowers |
| Audit (fresh session reviews a past one) | superpowers (for `diagnosing-superpowers`), session-report | everything else |

**Add:**
- **`session-report@claude-plugins-official`:** local HTML report of tokens, cache efficiency, subagents, skills and the most expensive prompts, built from `~/.claude/projects` transcripts. It answers "where did the weekly budget go".
- **Built-in `/insights`** (no install): generates an HTML report of recent sessions, including "where things go wrong". 

**Skip, with reasons:**
- **`ralph-loop`:** a self-referential continue-until-done loop. That is the opposite of the checkpointed pause policy.
- **`hookify`:** hand-written, tested hooks are clearer for usage and compaction.
- **`mlflow`:** agent tracing adds nothing to these Slurm experiments.
- **W&B, MLflow or Slurm MCP servers:** not justified here. None of the Slurm kind is in the official marketplace.

**Fix (reliability, not plugins) [local]:** `~/.claude/settings.json` `autoMode.environment` describes a different repository. It names `github.com/Hal1903/SHIFT_RT`, "default branch master", and accounts `bimc-*` only. It applies in every project, so the auto-mode classifier sees the wrong trusted repo, branch and paths when working in Alignment. `autoMode` is scoped "User or managed" [doc], so it cannot move to a project file. Rewrite the user block to cover both repos, including Alignment's and Deception-Circuit's remotes and branches and the beto/bimc/bgrb/bjhz accounts.

## 6. Model, effort and compaction routing

**Claude subagent model resolution [doc]**, in order:
1. The Agent tool `model` parameter (aliases only).
2. Frontmatter `model`.
3. `CLAUDE_CODE_SUBAGENT_MODEL`.
4. The parent's model.

`CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` also overrides frontmatter.

- **Fix for the 2026-10-26 failure:** set `"CLAUDE_CODE_SUBAGENT_MODEL": "opus"` in the settings `env` block. An omitted `model` parameter then resolves to Opus, not Fable.
- **Agent definitions:** `.claude/agents/ticket-implementer.md` already has `model: opus`. Add it to `idea-critic`, `paper-reader` and `paper-searcher` as well.
- **Forks:** the built-in fork always inherits the parent model.

**Subagent compaction window:**
- **[doc]** The `modelSettings.<model>.autoCompactWindow` entry is documented "for that model". The docs never say whether it reaches subagents.
- **[doc]** Frontmatter `autoCompactWindow` (100000–1000000, v2.1.296+) is described as making a subagent "compact earlier than it otherwise would", which reads as lower-only.
- **[doc]** `CLAUDE_CODE_AUTO_COMPACT_WINDOW` applies to subagents, but it is one global value that overrides the per-model setting. It would also move the Fable orchestrator off 400k.
- **[local]** Eleven transcripts contain compaction boundaries. Opus 5.5 subagents compacted at 368k–442k tokens, most around 370k, on Oct 25–27. The Fable orchestrator compacted at 368k–378k.
- **[local]** The Oct 25 settings backup shows Opus 5.5 had **no** window set then. The 600k entry was added around Oct 30 14:22.
- **What those numbers show:** the default tuned window for Opus 5.5 is roughly 400k. They do not show whether the new 600k setting reaches subagents, and no subagent compaction has happened since it was added.
- **Status: [unverified].** Test with one Opus subagent on a long-read task, then run `grep compact_boundary ~/.claude/projects/<proj>/<session>/subagents/agent-*.jsonl` and check `compactMetadata.preTokens`.
- **Brief sizing:** until that test passes, size subagent briefs to finish under about 350k tokens.

**Codex [doc]:**
- **Model selection:** a custom agent file's `model` or `model_reasoning_effort` wins. Otherwise Codex uses the explicit spawn value, then the `[agents]` default, then the parent's value.
- **[local]** All four `.codex/agents/*.toml` set no `model`. The bridge writes "inherit the parent's Codex model", so workers run on **Astra** unless every spawn names Sol.
- **Fix:** add `[agents] default_subagent_model = "gpt-6.1-sol"` to `~/.codex/config.toml`, or have the bridge generator emit `model = "gpt-6.1-sol"`. Editing the TOMLs by hand would be overwritten by the generator.
- **Compaction:** the agent schema has no compaction field. The model-catalog route already in use (Sol 600k, Astra 400k) is per model, so Sol workers get 600k once they actually run Sol.

## 7. Auditing a past session from a fresh session

**Where transcripts live:**
- **Claude main transcripts [doc]:** `~/.claude/projects/<slug>/<sessionId>.jsonl`.
- **Claude subagent transcripts [doc]:** `…/<sessionId>/subagents/agent-<id>.jsonl` and `.meta.json`.
- **Workflow scripts and results [doc]:** under the same session directory.
- **Codex [local]:** `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`, 707 MB. Compactions are recorded as `"type":"compacted"` lines.

**Retention:** `cleanupPeriodDays` defaults to **30** and deletes silently [doc]. For a dissertation with audits weeks later, set it to 365 or more in user settings. **[local]** Claude transcripts are currently 471 MB.

**Session tools [doc]:** `claude --resume <id>`, `/export <file>` (plain text), `/insights`, `/usage` and `/context`.

**Audit checks a fresh agent can script from the jsonl:**
1. Count `compact_boundary` events and their `preTokens` per agent.
2. Find runs of `tool_result` with `is_error: true` on the same tool and input. These indicate stuck loops.
3. Find the same Bash command repeated N times within M minutes. This indicates polling.
4. List Agent tool calls without a `model` parameter, which inherit Fable.
5. List `SendMessage` calls to names that were refused.
6. Compare each subagent's final message length against its handback file.
7. Check that RESUME.md was edited after each compaction.

`superpowers:diagnosing-superpowers` is installed and handles "past session by id or path, any harness". Use it as the narrative audit, and use the script for counts.

**Durable-state validator (from the real failure) [local]:**
- `.scratch/sdr-clause-choice/RESUME.md` was written by Codex on 2026-10-26.
- Its characters per whitespace-separated token rise from about 8 (normal) to 25–60 on lines 9–34. Those lines have no spaces, for example "Lead8unchanged", "CPUgeometrypreliminaryPASS". Later lines recover to about 8.
- The cause is not diagnosed.
- **Guard:** add a `PostToolUse` hook on `Write|Edit` (Claude) or `apply_patch` (Codex) for paths matching `RESUME.md` or `*worklog*.md`. Fail any line whose average token length exceeds 20 and feed that back as `additionalContext` (or `decision:"block"` in Codex, which replaces the tool result with the feedback). Run the same check in the SessionStart(compact) hook and include the pass or fail result alongside the RESUME pointer.

## 8. Other features worth knowing

- **Dynamic workflows [doc]:** a JS orchestration script keeps intermediate results out of the orchestrator's context. Runs resume within the session and pause on usage limits. They take no mid-run user input. They suit review fan-outs. Run one workflow per stage so the human gate sits between stages.
- **`SubagentStart` additionalContext [doc]:** injects the shared agent brief (usage self-check, no git, handback path) into every subagent, and again after it compacts.
