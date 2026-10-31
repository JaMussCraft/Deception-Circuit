# Ticket 07 hand-back: plugin and skill profiles for Claude and Codex

Hand-back trigger, read first: applying the wave A user-settings merge changes Codex through the bridge (Open question
1). The orchestrator decided to apply it as staged. A second round then added three ops: a bridge change that turns
jcodemunch off in Codex, its test, and a Codex paragraph in the bridge doc.

## What changed

Committed by the orchestrator from W:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/07-handback.md` (this file).
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/07-profiles-both-tools.md` (status, checkboxes and comments).

Staged in S, ops file `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/ops/07-profiles.json` (ten ops: seven
in wave A and three in wave C):

| Op | Destination | Wave | What it does |
|---|---|---|---|
| json_merge | `/u/swong2/.claude/settings.json` | A | Sets `enabledPlugins` to the default column of spec §5.7, adds `skillOverrides` with the five user skills off, and adds `deniedMcpServers` naming jcodemunch. |
| json_merge | `/projects/beto/swong2/Alignment/.claude/settings.local.json` | A | Sets `andrej-karpathy-skills@karpathy-skills` to false. |
| write | `/u/swong2/.claude/profiles/research.json` | A | New profile file with `enabledPlugins` only. |
| write | `/u/swong2/.claude/profiles/synthesis.json` | A | New profile file with `enabledPlugins` only. |
| write | `/u/swong2/.claude/profiles/writing.json` | A | New profile file with `enabledPlugins` only. |
| write | `/u/swong2/.claude/profiles/audit.json` | A | New profile file with `enabledPlugins` only. |
| text_block | `/u/swong2/.codex/config.toml` | C | Marker `autoresearch-workflow-profiles`, position `end`: five `[[skills.config]]` entries that turn off the shinka and weco adapters in Codex. |
| replace_text | `/projects/beto/swong2/Alignment/.agents/claude_codex_sync.py` | C | In `sync_mcps`, a server named by a `serverName` entry of Claude's user `deniedMcpServers` keeps its Codex entry but gets `enabled = false`. |
| replace_text | `/projects/beto/swong2/Alignment/.agents/tests/test_claude_codex_sync.py` | C | Adds a test that a denied server is written with `enabled = false` and loses the flag when the denial is removed. |
| text_block | `/projects/beto/swong2/Alignment/docs/agents/claude-codex.md` | A | Marker `autoresearch-workflow-profiles`, position `end`, `lint: true`: a "Profiles and Codex" section that states the Codex gap and how to use the writing plugins in Codex for a while. |

The bridge op applies after ticket 01's whole-file bridge write, because the apply tool runs op files in ticket order
within a wave. Its old text is two lines that ticket 01 does not change, and they occur once in both the live file and
ticket 01's staged copy. Because the change sits in the generator, the `enabled = false` survives every regeneration of
the bridge block. The doc paragraph leaves out jcodemunch and the shinka and weco skills on purpose. Both stay on in
Codex until wave C is applied, and the doc is applied in wave A.

The staged profile files are under `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/tree/u/swong2/.claude/profiles/`.
Every profile lists the whole §5.7 column with explicit true and false values, so a profile stays correct if the user
default drifts. No profile repeats `skillOverrides` or `deniedMcpServers`, because both are off in every column and the
profile inherits them from user settings.

The plugin keys are spelled as installed: `superpowers`, `code-review`, `github`, `claude-md-management`,
`context7`, `skill-creator` and `claude-code-setup` come from `claude-plugins-official`; the others are
`mattpocock-skills@mattpocock`, `nnsight@nnsight-skills`, `academic-research-skills@academic-research-skills`,
`academic-writing-agents@andrehuang-academic-writing-agents`, `cc-plugin-you-should-know@builtin`,
`andrej-karpathy-skills@karpathy-skills` and `session-report@claude-plugins-official`. The session-report key comes
from its entry in the local `claude-plugins-official` marketplace manifest.

The jcodemunch off switch in Claude uses `deniedMcpServers` with the entry `{"serverName": "jcodemunch"}`. The fallback through
`permissions.deny` was not needed, because the entry shape is confirmed (see How verified).

Nothing was staged for Codex profiles. The reason is under What is NOT done.

Helper scripts, outside every repository: `/u/swong2/.claude/jobs/b2cb53cd/tmp/07/build_ops.py` builds the profile
files and the op file from one copy of the §5.7 table, and `/u/swong2/.claude/jobs/b2cb53cd/tmp/07/verify.py` checks
them. The Codex experiment lives in `/u/swong2/.claude/jobs/b2cb53cd/tmp/07/codexlab/`.

## How verified

### Documentation checked, with the key each page confirms

Claude Code:

- https://code.claude.com/docs/en/settings, section "Settings precedence". It lists managed settings, then command
  line, then project local, shared project and user. It also says that `--settings` applies "above your user, project,
  and local files and below managed settings", and that a key left out keeps its value from the files. This confirms
  the profile layering.
- https://code.claude.com/docs/en/settings-reference, entry `enabledPlugins`. The scope is any file, and the value is
  an object of `plugin-name@marketplace-name` to a Boolean.
- The same page, entry `skillOverrides`. The scope is any file, and the values are `on`, `name-only`,
  `user-invocable-only` and `off`. The page adds: "Overrides don't apply to plugin skills". The five shinka and weco
  skills are user skills in `~/.claude/skills/`, so they qualify. Their `name:` frontmatter lines match the keys used.
- The same page, entry `deniedMcpServers`. The scope is any file, and each entry is an object with exactly one key:
  `serverName`, `serverCommand` or `serverUrl`. The example is `{ "serverName": "filesystem" }`. This confirms the
  MCP off switch shape.
- https://code.claude.com/docs/en/managed-mcp, sections "Policy-based control with allowlists and denylists" and "How a
  server is evaluated". They say: "The denylist applies to every server regardless of where it came from", and that
  denylists merge from every scope, "so users can always block servers for themselves". The page does not name
  `~/.claude.json` explicitly, so the pilot should confirm that jcodemunch disappears from `/mcp` (Open question 5).

Codex (installed version `codex-cli 0.166.0`):

- `codex --help` prints: `-p, --profile <CONFIG_PROFILE_V2>  Layer $CODEX_HOME/<name>.config.toml on top of the base
  user config`.
- https://learn.chatgpt.com/docs/config-file/config-advanced, profiles section. Profiles are separate files
  `~/.codex/<name>.config.toml` with top-level keys. The page says: "In Codex 0.134.0 and later, `--profile` no longer
  reads `[profiles.profile-name]` from `config.toml`". It also says the profile file is "a layer above your base user
  config and below project and CLI config".
- https://learn.chatgpt.com/docs/config-file/config-reference. It documents `skills.config` (array of objects),
  `skills.config.<index>.path` and `skills.config.<index>.enabled`; `mcp_servers.<id>.enabled` ("Disable an MCP server
  without removing its configuration"); `agents.default_subagent_model` ("Default model for spawned agents. An explicit
  spawn model takes precedence.", which is ticket 01's R11 key); and `plugins.<plugin>.enabled`.
- https://learn.chatgpt.com/docs/build-skills, section on disabling skills. It shows `[[skills.config]]` with
  `path = "/path/to/skill/SKILL.md"` and `enabled = false` in `~/.codex/config.toml`. It also says Codex "follows the
  symlink target" of symlinked skill folders. The bridge already uses the same shape with the adapter target path
  (`A/.agents/claude_codex_sync.py:301`), so the staged paths point at `~/.codex/claude-bridge/skills/<name>/SKILL.md`.

Codex experiment with a throwaway `CODEX_HOME` in T, using fake `/bin/true` servers, no network and no real config. A
profile file that holds only `[mcp_servers.otherserver]` with `enabled = false` turned that server off:

```
CODEX_HOME=/u/swong2/.claude/jobs/b2cb53cd/tmp/07/codexlab/home /u/swong2/.local/bin/codex mcp list --json
CODEX_HOME=/u/swong2/.claude/jobs/b2cb53cd/tmp/07/codexlab/home /u/swong2/.local/bin/codex --profile lean mcp list --json
```

Observed: without the profile both servers report `"enabled": true`; with `--profile lean` the server `otherserver`
reports `"enabled": false`. The base file in that lab also carried a `[[skills.config]]` block, and Codex loaded it
without an error. A test of the project layer (`codex -C <dir> mcp list`) was inconclusive, because the lab directory
is not a git repository and agents do not run git.

### Merge, profile and TOML checks

```
/u/swong2/.conda/envs/mgnp/bin/python -B /u/swong2/.claude/jobs/b2cb53cd/tmp/07/verify.py
OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -B /u/swong2/.claude/jobs/b2cb53cd/tmp/07/verify.py
```

The script imports `deep_merge` and `apply_text_block` from the apply tool and works on in-memory copies. It prints
hash prefixes of the `env` blocks, never their values. Key lines, identical on both interpreters for the JSON part:

```
env sha256 prefix before: a23b322f8d6be7b6 after: a23b322f8d6be7b6
PASS user env byte-identical
PASS every other user key unchanged: 14 keys
PASS no key removed from user settings
PASS user enabledPlugins equals the default column exactly
PASS skillOverrides: five user skills off
PASS deniedMcpServers names jcodemunch
PASS user merge is idempotent (second merge reports no change)
PASS local env block identical after merge (hash)
PASS every other local key unchanged
PASS research profile has only enabledPlugins
PASS research effective plugins match its column
PASS synthesis profile has only enabledPlugins
PASS synthesis effective plugins match its column
PASS writing profile has only enabledPlugins
PASS writing effective plugins match its column
PASS audit profile has only enabledPlugins
PASS audit effective plugins match its column
PASS default session effective plugins match
FAILURES: 0
```

The effective check stacks user settings after the merge, the project file, the local file after the merge, and then
the profile, in the documented order. The default session turns on exactly superpowers, mattpocock-skills,
code-review, github and claude-md-management. Research adds nnsight, writing adds the two academic plugins, and audit
adds session-report.

Codex part, mgnp only, because base python3.9 has no `tomllib` and prints a SKIP line there:

```
PASS ticket 01 marker differs from ours (R18)
PASS 01 then 07: parses, 5 skills.config entries off
PASS 01 then 07: bridge mcp_servers unchanged
PASS 01 then 07: ticket 01 [agents] table still present
PASS 07 then 01: parses, 5 skills.config entries off
PASS 07 then 01: bridge mcp_servers unchanged
PASS 07 then 01: ticket 01 [agents] table still present
PASS text_block idempotent
PASS adapter exists: /u/swong2/.codex/claude-bridge/skills/weco/SKILL.md
PASS ~/.agents/skills link resolves to it: /u/swong2/.agents/skills/weco
jcodemunch probe rejected (end, [mcp_servers.jcodemunch]): Cannot declare ('mcp_servers', 'jcodemunch') twice
jcodemunch probe rejected (before_first_table, [mcp_servers.jcodemunch]): Cannot declare ('mcp_servers', 'jcodemunch') twice
jcodemunch probe parsed (end, mcp_servers.jcodemunch.enabled = false)
jcodemunch probe rejected (before_first_table, mcp_servers.jcodemunch.enabled = false): Cannot declare ('mcp_servers', 'jcodemunch') twice
```

The staged block survives bridge reconciles. `Writer.block` in `A/.agents/claude_codex_sync.py:104-110` reads the
whole file and replaces only the text between the bridge's own markers, in place (line 109). Text outside those
markers, including this block at the end of the file, is kept, so the file order stays as the apply tool wrote it.

The adapter checks pass for all five skills. The one probe that parsed is not a working route. A dotted key at the end
of the file lands inside the bridge's last table, `[mcp_servers.jcodemunch]`, so it defines a meaningless nested key.
The block uses position `end` on purpose. Ticket 01's block uses `before_first_table`, and a second block with that
position would be inserted inside ticket 01's block once that block holds the first table header.

### Bridge change: tests on the combined copy

`/u/swong2/.claude/jobs/b2cb53cd/tmp/07/bridge_lab.py` builds the bridge as wave C would leave it: ticket 01's staged
bridge plus the 07 `replace_text`. It also builds the live bridge test plus the new test, under
`/u/swong2/.claude/jobs/b2cb53cd/tmp/07/bridgelab/.agents/`. The test loads the bridge next to itself, so it runs
against the combined copy.

```
/sw/external/python/anaconda3/bin/python3.9 -B /u/swong2/.claude/jobs/b2cb53cd/tmp/07/bridge_lab.py
bridge on 01-staged old_text occurrences: 1
bridge on live old_text occurrences: 1
test (lab copy from live) old_text occurrences: 1

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider /u/swong2/.claude/jobs/b2cb53cd/tmp/07/bridgelab/.agents/tests/test_claude_codex_sync.py
7 passed in 0.35s

/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider /u/swong2/.claude/jobs/b2cb53cd/tmp/07/bridgelab/.agents/tests/test_claude_codex_sync.py
7 passed in 0.33s
```

The seven tests are the six existing bridge tests and the new denylist test. The new test also checks that a
`serverUrl` entry in the denylist does not disable anything, since the bridge matches by name only.

### Apply-tool dry-runs

`--wave` is required by the apply tool, so there are separate runs per wave. The output below is from the first round
and has since grown. Current state after the second round:

```
dry run, wave A: 7 op(s) selected from 10
(the six ops below, then)
[07#10] text_block /projects/beto/swong2/Alignment/docs/agents/claude-codex.md WOULD APPLY: +21 -0 lines

dry run, wave C: 3 op(s) selected from 10
[07#7] text_block /u/swong2/.codex/config.toml WOULD APPLY: +25 -0 lines
[07#8] replace_text /projects/beto/swong2/Alignment/.agents/claude_codex_sync.py WOULD APPLY: +4 -1 lines
[07#9] replace_text /projects/beto/swong2/Alignment/.agents/tests/test_claude_codex_sync.py WOULD APPLY: +15 -0 lines

dry run of every ticket's wave C ops (no --only):
dry run, wave C: 5 op(s) selected from 35
[01#20] text_block /u/swong2/.codex/config.toml WOULD APPLY: +5 -0 lines
[01#21] write /projects/beto/swong2/Alignment/.agents/claude_codex_sync.py WOULD APPLY: +1 -1 lines
[07#7] text_block /u/swong2/.codex/config.toml WOULD APPLY: +25 -0 lines
[07#8] replace_text /projects/beto/swong2/Alignment/.agents/claude_codex_sync.py WOULD APPLY: +4 -1 lines
[07#9] replace_text /projects/beto/swong2/Alignment/.agents/tests/test_claude_codex_sync.py WOULD APPLY: +15 -0 lines
```

The doc op has `lint: true`, and the apply tool runs the lint before it reports WOULD APPLY, so the paragraph passes
the lint. First-round output:

```
/u/swong2/.conda/envs/mgnp/bin/python -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging --only 07 --wave A --dry-run
dry run, wave A: 6 op(s) selected from 7
[07#1] json_merge /u/swong2/.claude/settings.json WOULD APPLY: +22 -8 lines; + deniedMcpServers, ~ enabledPlugins.academic-research-skills@academic-research-skills, ~ enabledPlugins.academic-writing-agents@andrehuang-academic-writing-agents, + enabledPlugins.andrej-karpathy-skills@karpathy-skills, ~ enabledPlugins.cc-plugin-you-should-know@builtin, ~ enabledPlugins.claude-code-setup@claude-plugins-official, ~ enabledPlugins.context7@claude-plugins-official, ~ enabledPlugins.nnsight@nnsight-skills, + enabledPlugins.session-report@claude-plugins-official, ~ enabledPlugins.skill-creator@claude-plugins-official, + skillOverrides
[07#2] json_merge /projects/beto/swong2/Alignment/.claude/settings.local.json WOULD APPLY: +1 -1 lines; ~ enabledPlugins.andrej-karpathy-skills@karpathy-skills
[07#3] write /u/swong2/.claude/profiles/research.json WOULD APPLY: +18 -0 lines, new file
[07#4] write /u/swong2/.claude/profiles/synthesis.json WOULD APPLY: +18 -0 lines, new file
[07#5] write /u/swong2/.claude/profiles/writing.json WOULD APPLY: +18 -0 lines, new file
[07#6] write /u/swong2/.claude/profiles/audit.json WOULD APPLY: +18 -0 lines, new file

/u/swong2/.conda/envs/mgnp/bin/python -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging --only 07 --wave C --allow codex-config --dry-run
dry run, wave C: 1 op(s) selected from 7
[07#7] text_block /u/swong2/.codex/config.toml WOULD APPLY: +25 -0 lines
```

No JSON settings op sets `lint: true`, as ticket 01's Open question 6 advises. The apply tool creates
`~/.claude/profiles/` itself when it writes the first profile, so no `mkdir` op is needed.

### Commands for the orchestrator

Profile launch commands for Claude. The shell function `claude` passes these arguments through the bridge launcher.

```
claude --settings ~/.claude/profiles/research.json
claude --settings ~/.claude/profiles/synthesis.json
claude --settings ~/.claude/profiles/writing.json
claude --settings ~/.claude/profiles/audit.json
```

A plain `claude` gives the lean default. Codex has no profiles from this ticket, so Codex sessions launch with a plain
`codex`.

Install session-report after wave A is applied, then re-run the wave A apply for ticket 07. Use the real binary, so
the bridge does not reconcile in between. The install may need network for the marketplace.

```
/u/swong2/.local/bin/claude plugin install session-report@claude-plugins-official --scope user
/u/swong2/.conda/envs/mgnp/bin/python -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging --only 07 --wave A
/sw/external/python/anaconda3/bin/python3.9 -c "import json;print(json.load(open('/u/swong2/.claude/settings.json'))['enabledPlugins'].get('session-report@claude-plugins-official'))"
```

The documentation says that `claude plugin enable` and `/plugin` write `enabledPlugins`, so an install at user scope
is expected to write `true` there, which would break the lean default. Re-running the wave A apply flips that value
back to `false`, because `json_merge` replaces a differing scalar. The verification above checked that behaviour.
The last command prints only that one value and must print `False`. The alternative
`claude plugin disable session-report@claude-plugins-official --scope user` was not run. Its `--help` was read, but
it is not verified to write `false` rather than remove the key. If it removed the key, the plugin's own default would
decide. Until the plugin is installed, the audit profile names a plugin that Claude reports as not installed.

## Execution evidence

Not applicable: no runs. No job, GPU or paid API call was used.

## What is NOT done

- **No Codex profiles were staged.** The spec's `[profiles.<name>]` blocks would be inert: Codex 0.134.0 and later
  no longer reads them, and the installed version is 0.166.0. Profile files would not help either. Once user-level
  `enabledPlugins` turns nnsight and the two academic plugins off, the bridge skips them
  (`A/.agents/claude_codex_sync.py:215-216`) and prunes their adapter links (line 446), so a Codex profile has no
  skill to enable. A project-level disable cannot be undone by a profile either, because the profile layer sits below
  project config. So the Codex research and writing profiles are not available, which is the fallback spec §5.7
  names. The audit profile has nothing to add in Codex, because session-report is a Claude plugin that stays disabled
  at user level. The synthesis profile would equal the default. I did not ship four identical files.
- **jcodemunch stays on in Codex until wave C.** Today the bridge copies it from `~/.claude.json` into its own block
  of `~/.codex/config.toml` (`A/.agents/claude_codex_sync.py:250-251`) without reading `deniedMcpServers`. A second
  definition outside the bridge block is a TOML error (the probe above), so the fix is the wave C generator change.
  The next bridge reconcile after wave C writes `enabled = false` for it. That has not been observed live.
- **session-report is not installed.** That is an orchestrator action; the commands are above.
- **Not observed live:** jcodemunch disappearing from `/mcp` in Claude, and the five skills disappearing from Codex
  after wave C. Both are pilot checks (Open question 5).
- **Not tested:** the Codex project layer. The lab experiment was inconclusive, as described under How verified.

## Open questions

1. **Wave A changes Codex through the bridge (hand-back trigger).** The bridge reads user and local `enabledPlugins`
   on every reconcile. A reconcile runs on any `claude` or `codex` launch through the shell functions, on
   `claude_codex_sync.py --apply`, and in the SessionStart hook of both tools on startup, resume, clear and compact.
   That includes a compaction in the live Codex session and the user's next `claude` launch anywhere. After wave A,
   that reconcile does three things. It removes the `~/.agents/skills/` links for the nnsight, academic-research-skills,
   academic-writing-agents and claude-code-setup adapters. It removes the karpathy link in `A/.agents/skills/`, because
   of the local merge. It rewrites the bridge block in `~/.codex/config.toml` without `[mcp_servers.context7]`
   (`A/.agents/claude_codex_sync.py:215-216, 360, 446`). `Writer.prune` removes only the links; the adapter files under
   `~/.codex/claude-bridge/skills/` stay. Codex skill discovery is live, so a running Codex session can lose those
   skills at its next compaction. Spec §5.7 relies on exactly this propagation, and the ticket assigns the merge to
   wave A, so I staged it as wave A. The orchestrator has two choices:
   - apply wave A as staged and accept the live-session effect, which is the spec's intended path; or
   - ask me to move the `enabledPlugins` part of the user merge and the local karpathy merge into a separate op held
     with the wave D work until the Codex session is finished. The `skillOverrides` and `deniedMcpServers` parts and the
     four profile files would stay in wave A, because the bridge does not read them.

   Decided by the orchestrator: apply as staged. The pruning is the intended lean default, and the skills the live
   Codex session uses (code-review and claude-pr-review) stay.
2. **jcodemunch in Codex: settled by a wave C bridge change.** The orchestrator asked for an option that turns
   jcodemunch off by default and survives the bridge's regeneration of its block. A `enabled = false` written outside
   the block cannot coexist with the block's own `[mcp_servers.jcodemunch]` table. So the change is in the generator:
   `sync_mcps` now marks any server named in Claude's user `deniedMcpServers` with `enabled = false`. The bridge tests
   pass on the combined copy on both interpreters. The change is four lines, which is more than the one-sentence
   bridge change R11 allows, but the orchestrator explicitly allowed a staged generator change. The Codex lab showed
   that `enabled = false` is honoured (`codex mcp list --json` reported the server off). A profile file was the other
   route, but it only takes effect when a launch passes `--profile`.
3. **Codex gap documented.** The new "Profiles and Codex" section in the bridge doc (wave A) states that Codex has no
   profiles, says why, and gives the steps for using the writing plugins, or nnsight, in Codex for a while. Spec §5.7
   and proposal D6 still name `[profiles.<name>]`, which Codex no longer reads. Ticket 08's docs should follow the
   bridge doc and not repeat that syntax.
4. **Turning an item back on for one task.** A profile can turn a user skill back on, for example with
   `claude --settings '{"skillOverrides": {"weco": "on"}}'`, because `--settings` outranks user settings. The
   jcodemunch denylist cannot be undone that way, because denylists merge from every scope. Re-enabling jcodemunch
   for an evolution task means removing the entry from user settings by hand, since `json_merge` never removes.
5. **Pilot checks (ticket 11).** First, start a plain `claude` and confirm in `/mcp` that jcodemunch is absent, which
   checks the denylist against a server from `~/.claude.json`. Second, after wave C, one bridge reconcile and a Codex
   restart, confirm that the shinka and weco skills are absent from the Codex skill list. Also confirm that
   `codex mcp list` reports jcodemunch as disabled. Codex does not document how `skills.config` arrays
   combine across the user and project layers. Today the bridge's project block in `A/.codex/config.toml` is empty,
   and it stays empty after wave A, so the two cannot interact yet.
