# 00 — Plan hand-back (planner, 2026-10-31)

## What changed

All files were written by the planner inside the worktree and are for the orchestrator to commit:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/spec.md`
- `.../autoresearch-workflow/agent-brief.md`
- `.../autoresearch-workflow/issues/01-lint-apply-tool-hygiene-config.md` through `12-wrap-up.md` (12 tickets)
- `.../autoresearch-workflow/reports/00-plan-handback.md` (this file)

Nothing was staged, applied, installed or run beyond read-only inspection. No git command was run.

The ticket list grew from the nine the lead suggested to twelve. The CLI is split into core (02) and records (03)
so that each fits one context, the science guards (04) run early in parallel with ticket 01, and the migration is
split into a judgment part (09) and a scripted part (10) because the closed `.scratch` text is about 1.4M tokens
and must not be read by an agent.

The spec is 484 lines, above the requested 450, because it carries the command surface (§5.6) and 25 rulings. A
final self-review added three fixes: the gate's PreToolUse matcher now includes Write and Edit so the counter guard
can work; `MEMORY.md` is changed only by `replace_text` and `append_text` ops so tickets 01 and 12 cannot conflict
with each other or with Codex; and the apply tool's lint call goes through `--lint-cmd`.

Dependency order and suggested parallel waves of agents:

| Agent wave | Tickets | Blocked by |
|---|---|---|
| 1 | 01 lint, apply tool, hygiene and config; 04 science guards | none |
| 2 | 02 RS core; 07 profiles; 08 protocol docs and templates | 01 |
| 3 | 03 RS records | 02 |
| 4 | 05 index and registry seeding; 06 hooks | 03 (06 also 02) |
| 5 | 09 migration A; 10 migration B | 09: 05 and 08; 10: 01 and 05 |
| 6 | 11 pilot checklist and audit-scan | 06, 07, 08 |
| 7 | 12 wrap-up | all |

## Verified facts relied on (file:line evidence)

Paths: A is `/projects/beto/swong2/Alignment`, DC is its `Deception-Circuit` main checkout, W is this worktree.

1. **The selective-deception precedent points into ignored bulk, not into docs.** `ls -la A/.scratch` shows
   `selective-deception -> /projects/beto/swong2/Alignment/Deception-Circuit/outputs/_studies/selective-deception/study`.
   `W/.gitignore:15` ignores `outputs/_studies/` (and `:8` ignores `outputs/_analyses/`). The handoff
   `W/docs/research/selective-deception/README.md` describes an inode-preserving move on the same filesystem with
   versioned copies of the reports in `docs/research`. This drives R3.
2. **`A/.scratch` has 17 real directories and one symlink.** The real ones are autoresearch-workflow,
   component-analysis, eval5-grader-fixes, format-control, mechanism-analysis, mechanism-datasets, and eleven `sdr-*`
   directories including `sdr-session-wrapup`, whose mtime is today at 08:35 (`ls -la`).
3. **Code reads `.scratch` paths by string.** A grep of W's `tests`, `scripts`, `evaluation` and `component_analysis`
   found 14 files, with paths such as `/Alignment/.scratch/sdr-native-controls/selection-audit.json`,
   `.scratch/sdr-clause-choice/spec.md` and `rubric.md`, `/Alignment/.scratch/mechanism-analysis/reports` and
   `.scratch/eval5-grader-fixes/issues/`. The SDR handoff says a CPU test needs the retained
   `.scratch/sdr-native-controls/selection-audit.json` (`W/docs/research/sdr-mechanism/README.md`, "Validation scope").
4. **`~/.codex/hooks.json` exists** with one group under `SessionStart`, matcher `startup|resume|clear|compact`,
   running the bridge script with a 30 s timeout. The Claude user settings have the identical bridge hook.
5. **The bridge preserves other hooks.** `A/.agents/claude_codex_sync.py:412-430` (`sync_startup`) filters out only
   groups whose command contains its own script, then appends its group, for both `~/.claude/settings.json` and
   `~/.codex/hooks.json`.
6. **The bridge drops Codex adapters for plugins disabled at user level.** `A/.agents/claude_codex_sync.py:215-217`
   skips a plugin when it is inactive in the effective settings and not enabled at user level. The effective map is
   user, then A's project file, then A's local file (`:189-197`).
7. **Codex agent definitions carry no model.** `A/.agents/claude_codex_sync.py:306-324` writes "inherit the parent's
   Codex model" and no `model` key; `A/.codex/agents/ticket-implementer.toml` confirms.
8. **`~/.codex/config.toml` layout.** Top-level keys on lines 1-6, the first table `[tui]` at line 7, the project
   trust table at line 16, and the bridge block at lines 19-30 (context7, github, jcodemunch). There is no `[agents]`
   table. This drives the `before_first_table` insertion in spec §7.
9. **Existing manifest writers and the name collision.** `W/scripts/sdr_routing_pilot.py:392-403` writes
   `git_commit`, `dirty_diff_hash`, `code_sha256`, `software`, `model_cache`, `model_revision`, `tokenizer_files`,
   `dtype` and `manifest_hash` (sha256 of the canonical manifest), with a 10 s git bound and
   `git_fingerprint_error`. `W/component_analysis/selective_v6_manifest.py:64,125,131` validates, loads and builds a
   different manifest. `manifest.json` is already used for frozen inputs in `W/evaluate_native_sparse.py:334,459` and
   `W/evaluation/generation_checkpoint.py:118`. This drives R2.
10. **Where provenance should be written.** `W/run_io.py:172-187` `make_run_dir` creates the run directory and writes
    only `config.json`. `W/evaluation/suite.py:74-86` defines `suite_root` and `cell_dir`; directories are created at
    `:93`, `:189` and `:315`.
11. **Grader code and judge specs.** `W/evaluation/benchmarks/` holds base, judge, judge_budget, liars_bench,
    mask_bench, notebook, sandbagging and sources; `W/evaluate_circuit.py:626` and `:657` call `bench.judge_spec()`.
12. **Hook contracts (lane 2).** `reports/lane2-harness.md` §1 table: PreCompact (`manual|auto`, cannot inject),
    PostCompact (`compact_summary`, no decision control), SessionStart sources `startup|resume|clear|compact|fork`
    with `additionalContext`. §2: PreToolUse `permissionDecision: "deny"` is the only real pause; Stop `block` makes
    the agent continue. §3: SubagentStop has `last_assistant_message` and `agent_transcript_path` in both tools,
    Codex needs JSON on exit 0. §1 Codex: `additionalContext` default cap 2500 tokens, `/hooks` trust per hook.
13. **Usage file and its writer.** `/u/swong2/.claude/usage.json` at the time of planning: five-hour 9%, seven-day
    11%, Fable row 17% (so the Fable gap of 6 points already exceeds the D8 threshold of 5). `~/.claude/statusline.sh`
    lines 5-11 document the write, line 158 builds `rate_limits` from the stdin payload plus `model_scoped` (an empty
    payload would drop `five_hour`), and line 247 onward writes atomically. This drives R8.
14. **codex-usage.** `/u/swong2/.local/bin/codex-usage` is a two-line wrapper around `A/.agents/codex_usage.py`;
    `--help` lists `--pause-at`, `--limit-id`, `--timeout`, `--codex-bin` and exit codes 0, 2 and 1.
15. **User settings.** Top-level keys of `~/.claude/settings.json` (printed by name only): advisorModel,
    agentPushNotifEnabled, autoMode, effortLevel, enabledPlugins, env, extraKnownMarketplaces, feedbackDrafts, hooks,
    model, modelSettings, skipDangerousModePermissionPrompt, statusLine, tui. The `env` block's only key is
    `GITHUB_PERSONAL_ACCESS_TOKEN` (value not printed). `statusLine` has no `refreshInterval`; `cleanupPeriodDays` is
    absent; `autoMode.environment` describes only the SHIFT_RT repository; `modelSettings` sets
    `autoCompactWindow` 600000 for `claude-opus-5-5` and 400000 for `claude-fable-5-1`.
16. **Project and local settings.** `A/.claude/settings.json` only disables the karpathy plugin.
    `A/.claude/settings.local.json` re-enables karpathy (`true`), sets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, and has
    a `skillOverrides` map with `"off"` values. DC has no `.claude/settings.json` (`ls DC/.claude` shows only
    `worktrees`), and W's `.gitignore` does not list `.claude/worktrees/`.
17. **Agent definitions.** `A/.claude/agents/idea-critic.md:4`, `paper-reader.md:4` and `paper-searcher.md:4` say
    `model: sonnet` (not missing, so H1 is a change, R24). `ticket-implementer.md` has `model: opus`, `effort: high`.
18. **Remotes carry no token.** `A/.git/config:8` is `https://github.com/JaMussCraft/LLM-Alignment.git` and
    `DC/.git/config:7` is `https://github.com/JaMussCraft/Deception-Circuit.git`.
19. **Glued memory.** `A/.agents/memory/MEMORY.md:27` (selective deception) and `:29` (SDR) are glued, for example
    "locally2026-10-31 at133fe82;8selectivebranches". `sdr-mechanism-review.md` is 74,322 bytes and
    `selective-deception-execution.md` is 45,255 bytes. `usage-limit-policy.md` still says 75% weekly.
20. **MCP and skills.** `~/.claude.json` has one user-scope MCP server, `jcodemunch`, and no per-project MCP servers
    for the Alignment paths. User skills: shinka-convert, shinka-inspect, shinka-run, shinka-setup, weco, synced.
21. **Interpreters.** Base python3.9 has pytest 8.3.3. mgnp is Python 3.12.13 with pytest 9.1.1 and `tomllib`.
22. **DC's test conftest imports torch** (`W/conftest.py`), which is one reason RS tests live with the stdlib-only
    bridge tests in `A/.agents/tests/`.
23. **Handoff gaps.** `W/docs/research/mechanism-analysis/` has `synthesis.md` but no `README.md`.
24. **Bridge-generated adapters in DC are untracked.** `DC/AGENTS.md`, `DC/.codex/` and `DC/.agents/skills` exist in the
    main checkout but not in W, so they are not in the repository.

## Not verified (each is assigned to a ticket or the pilot)

- Codex: the exact tool names that PreToolUse and PostToolUse match for spawning, shell, messages and patches; the
  `[agents] default_subagent_model` key; per-profile skill and MCP enablement keys. Tickets 06 and 07 check the docs.
- Claude: whether `--settings` profile files merge `enabledPlugins` over user settings key by key; the documented off
  switch for a user-scope MCP server. Ticket 07 checks the docs; the pilot observes.
- Whether `!` commands typed by the user bypass PreToolUse hooks (R7 relies on it). Pilot step 4.
- Whether UserPromptSubmit can tell a human "continue" from a teammate message delivered in the user turn. Pilot.
- Whether background sessions keep `usage.json` fresh. If not, every spawn is denied as unknown until a human grants
  `--stale-ok`. Pilot step 8 and open question 2.
- Whether SessionStart(compact) and PostCompact fire for subagent compactions, and whether the 600k
  `autoCompactWindow` reaches Opus subagents. Pilot step 9.
- Whether `A/.agents/*.py` are git-tracked. The A `.gitignore` bridge block ignores only memory, skills, caches,
  `.codex/agents` and `.codex/config.toml`, which suggests they are, but no git command was run.
- Whether the Deception-Circuit GitHub repository is public. The proposal says it stays public; the plan treats it as
  public (R13, secret scan).
- Byte-identity of the `project_context` duplicates (lane 3 P2). Ticket 09 re-checks by sha256 before any move.

## Open questions for the orchestrator

1. **Session tag.** Ticket 05 needs this orchestrator session's tag (`claude-<first 8 characters of the session id>`)
   for the `autoresearch-workflow` row's `claimed_by`.
2. **Stale readings in background sessions.** The plan denies spawns on a reading older than 15 minutes and gives the
   human a `--stale-ok` override (R8). If the pilot shows background sessions never refresh `usage.json`, the user
   must choose between living with the override and letting RS call the usage endpoint itself with the OAuth token,
   as `statusline.sh` does.
3. **Wave B touches other sessions' archives.** Memory says the SDR wrap-up was waiting on another session's merge.
   Before applying the migration, confirm with the user that no live session uses `A/.scratch/sdr-*`,
   `component-analysis`, `format-control`, `mechanism-*` or `eval5-grader-fixes`.
4. **Merge timing.** Hooks in A's project settings work after wave A, because RS installs under `A/.agents`. Hooks in
   DC sessions need the DC branch merged to main (the user approves merges). The pilot can start from an A-rooted
   session before the merge if the user prefers.
5. **The GitHub token in user settings.** Proposal §5 says setup verifies no token remains in settings, but the
   bridge documents `env.GITHUB_PERSONAL_ACCESS_TOKEN` in user settings as the token's intended home for the GitHub
   MCP server. The plan leaves it in place and never prints it. Ask the user whether to move it to a credential store.
6. **nnsight off by default.** D6 says "nnsight (research only)", so a plain `claude` session lacks nnsight skills
   unless launched with the research profile. Confirm with the user.
7. **The Opus window test costs weekly usage.** Pilot step 9 reads past 450k tokens in one Opus subagent. Schedule it
   when the weekly reading has room.
8. **autoMode.** Ticket 01 rewrites `autoMode.environment` to cover Alignment and Deception-Circuit and keeps the
   SHIFT_RT entries. Confirm the user still wants SHIFT_RT covered.
