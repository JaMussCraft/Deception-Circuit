# 07 — Plugin and skill profiles for Claude and Codex

**Status:** resolved
**Type:** task
**Blocked by:** 01 (apply tool)
**Wave:** A for Claude files; C for `~/.codex/config.toml` profile blocks.
**Estimated size:** reading about 50k tokens (spec §5.7, proposal D6, lane 2 §5, `A/docs/agents/claude-codex.md`,
`A/.agents/claude_codex_sync.py:189-256`, the Claude settings and Codex config docs), writing about 20k tokens.
**Hand-back:** `F/reports/07-handback.md`

## What to do

Make the lean default real in both tools and add four Claude profiles (research, synthesis, writing, audit) per the
table in spec §5.7. Verify the Codex per-profile mechanism before staging anything for Codex.

## Facts to build on

- Enabled plugins today (user level): context7, superpowers, code-review, skill-creator, github,
  claude-md-management, claude-code-setup, nnsight, mattpocock-skills, cc-plugin-you-should-know,
  academic-writing-agents, academic-research-skills.
- `A/.claude/settings.local.json` sets `andrej-karpathy-skills@karpathy-skills: true`, which overrides the project
  file's `false`. It also has a `skillOverrides` map (`"name": "off"`), which is the verified syntax for turning a
  skill off.
- User skills in `~/.claude/skills/`: shinka-convert, shinka-inspect, shinka-run, shinka-setup, weco, synced.
- jcodemunch is a user-scope MCP server in `~/.claude.json` `mcpServers`, not a plugin.
- The bridge drops Codex adapters for a plugin that is disabled at user level and not enabled in A's project or
  local settings (`A/.agents/claude_codex_sync.py:215-216`). So the Claude user-level default also becomes Codex's
  default, and a Codex profile cannot re-enable a plugin whose adapters were dropped.
- session-report is not installed; installing it is an orchestrator action that needs network.

## Scope

- Staged `json_merge` into `/u/swong2/.claude/settings.json`: `enabledPlugins` per the default column; `skillOverrides`
  for the shinka and weco skills; the jcodemunch off switch through `deniedMcpServers` (the reviewer found it in the
  settings index: "block specific MCP servers by URL, command, or name"; confirm its entry shape on
  https://code.claude.com/docs/en/settings), falling back to `permissions.deny: ["mcp__jcodemunch"]` only if that
  shape cannot be confirmed. This merge carries no hooks, so it is wave A.
- Staged files `/u/swong2/.claude/profiles/{research,synthesis,writing,audit}.json`, each containing only
  `enabledPlugins` (and `skillOverrides` if needed).
- Staged `json_merge` into `/projects/beto/swong2/Alignment/.claude/settings.local.json` setting karpathy to false.
- Codex: read https://learn.chatgpt.com/docs (configuration and profiles pages) and `codex --help` output if the
  orchestrator provides it. If per-profile skill or MCP enablement keys exist, stage `[profiles.<name>]` blocks
  (wave C, marker `autoresearch-workflow-profiles`). Otherwise stage nothing for Codex and write the fallback.
- `S/ops/07-profiles.json`.

## Acceptance criteria

- [x] Applying the user-settings merge to a copy in T gives exactly the default column of spec §5.7, keeps every
      other key, and leaves the `env` block byte-identical (compared by hash, never printed).
- [x] Each profile file parses and contains only the keys allowed in spec §5.7.
- [x] The hand-back states which docs page confirmed the profile layering (`--settings` above user settings) and the
      MCP off switch, with URLs, or marks them unverified for the pilot to check.
- [x] The Codex outcome is one of: profile blocks staged with the doc URL for each key and a `tomllib` parse of the
      result on mgnp; or "not available" with the URL checked and the fallback described.
- [x] The hand-back gives the orchestrator the exact install command for session-report and the launch commands
      for each profile.
- [x] `apply_staged.py --staging S --only 07 --dry-run` output pasted.

## Verification

Dry-run the ops; parse every staged JSON with both interpreters.

## Comments

Ticket 07 implementer, 2026-10-31. The full record is in `reports/07-handback.md`.

Hand-back trigger first: the wave A user-settings merge changes Codex through the bridge at its next reconcile, which
includes a compaction in the live Codex session. The bridge removes the adapter links for the plugins turned off and
drops context7 from the bridge block in `~/.codex/config.toml`. The merge stays staged as wave A, as the ticket says.
Hand-back Open question 1 gives the orchestrator the choice to apply it as staged or to split it.

Files for the orchestrator to commit from W:

- `docs/research/autoresearch-workflow/reports/07-handback.md`
- `docs/research/autoresearch-workflow/issues/07-profiles-both-tools.md`

Staged in S, op file `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/ops/07-profiles.json`. Wave A has six ops:
the user-settings merge, the local-settings karpathy merge and the four profile files under
`/u/swong2/.claude/profiles/`. Wave C has one op: a `text_block` with marker `autoresearch-workflow-profiles` at the
end of `/u/swong2/.codex/config.toml` that turns off the five shinka and weco adapters.

Codex outcome: profiles are not available. The installed Codex 0.166.0 reads profile files
`~/.codex/<name>.config.toml`, not `[profiles.<name>]` tables. Profiles could not restore the nnsight or academic
adapters that the bridge prunes. jcodemunch is handled in the second round below.

Tests per env, run with the scratch script `/u/swong2/.claude/jobs/b2cb53cd/tmp/07/verify.py`:

- mgnp: every check passed (FAILURES: 0), including the JSON checks and the `tomllib` parse of the Codex config with
  ticket 01's block and ours applied in both orders.
- base python3.9: every JSON check passed (FAILURES: 0); the TOML checks were skipped because there is no `tomllib`.
- Apply-tool dry-runs: wave A would apply six ops and wave C one op, with no refusal.
- The hand-back passes `research-session lint` (clean, which includes the secret scan).

Status is resolved because staging is complete. The Open question 1 decision is made at apply time.

Second round, after the orchestrator's decision to apply wave A as staged:

- The op file now has ten ops: seven in wave A and three in wave C.
- New wave A op: a "Profiles and Codex" section added to `A/docs/agents/claude-codex.md`, with marker
  `autoresearch-workflow-profiles` and `lint: true`.
- New wave C ops: a `replace_text` in `A/.agents/claude_codex_sync.py` and a `replace_text` that adds a test to
  `A/.agents/tests/test_claude_codex_sync.py`. With them, the bridge writes `enabled = false` for any server named in
  Claude's user `deniedMcpServers`, so jcodemunch is off in Codex after wave C, and the setting survives every
  regeneration of the bridge block. The old text occurs once in the live bridge and once in ticket 01's staged bridge.
- Bridge tests on the combined copy (ticket 01's staged bridge plus this change): 7 passed on base python3.9 and 7
  passed on mgnp.
- Dry-runs: wave A would apply 7 ops and wave C would apply 3, with no refusals. A dry-run across all tickets selects
  5 wave C ops (01#20, 01#21, 07#7, 07#8, 07#9) and refuses none.
