# 01 — Text lint, staging apply tool, hygiene and config

**Status:** claimed
**Type:** task
**Blocked by:** nothing
**Wave:** A for everything except the Codex `[agents]` block, which is wave C. This ticket stages no hook (R26) and
nothing that R28 defers to wave D.
**Estimated size:** reading about 70k tokens (spec, brief, lane 4 §0, lane 2 §5-6, the memory notes and handoff
READMEs named below), writing about 60k tokens. This is the heaviest ticket. If your projection passes 250k tokens,
finish the lint and the apply tool, write the hand-back, and stop for the orchestrator to split the rest (R20).
**Hand-back:** `F/reports/01-handback.md`

## What to do

Build the two tools every later ticket depends on, then stage the hygiene and configuration changes of proposal §5
and H1, H6, H8 that do not touch the live Codex session's files. The lint (spec §5.5) comes first because every
staged Markdown file must pass it. The apply tool (spec §7) is the only way staged files reach A and user config.

## Facts to build on

- Glued samples: `A/.agents/memory/MEMORY.md:27` (selective deception line) and `:29` (SDR line);
  `A/.scratch/sdr-clause-choice/RESUME.md` lines 9-34 (lane 2 §7, lane 4 §0). Copy short excerpts into test fixtures;
  tests must not read live files. Reading these files is fine; staging any change to them is not (R28).
- Clean corpus: the four `F/reports/lane*.md`, `F/reports/proposal-full.md`, `W/docs/research/sdr-mechanism/README.md`,
  `W/docs/research/mechanism-analysis/synthesis.md`.
- `A/.agents/memory/usage-limit-policy.md` still says 75% weekly; D7 makes it 80% for five-hour and weekly (R9).
  `subagent-model-policy.md` should say the defaults are a safety net and that H1 is staged (R24).
- `~/.claude/settings.json` top-level keys: advisorModel, agentPushNotifEnabled, autoMode, effortLevel,
  enabledPlugins, env, extraKnownMarketplaces, feedbackDrafts, hooks, model, modelSettings,
  skipDangerousModePermissionPrompt, statusLine, tui. `statusLine` has no `refreshInterval`; `cleanupPeriodDays` is
  absent. `autoMode.environment` is a list describing only the SHIFT_RT repository. The `env` block holds the
  GitHub token that the bridge documents as its intended home (`A/docs/agents/claude-codex.md`); leave it untouched
  and never print it.
- `A/.claude/agents/{idea-critic,paper-reader,paper-searcher}.md` line 4 is `model: sonnet` (R24).
- `~/.codex/config.toml` has top-level keys on lines 1-6, `[tui]` as the first table at line 7, and the bridge block at
  lines 19-30. There is no `[agents]` table.
- Remotes: `A/.git/config:8` and `DC/.git/config:7` hold plain `https://github.com/JaMussCraft/...` URLs with no
  token (planner checked by reading the files).

## Scope

In S (staged, wave A unless stated):
- `S/tree/projects/beto/swong2/Alignment/.agents/research_session/__init__.py`, `cli.py` (argparse skeleton with a
  `lint` subcommand; later tickets extend it in order, R18), `lint.py`.
- `S/tree/projects/beto/swong2/Alignment/.agents/tests/test_research_session_lint.py` and
  `.agents/tests/fixtures/lint/` (glued and clean excerpts).
- `replace_text` ops on `/projects/beto/swong2/Alignment/.agents/memory/MEMORY.md` for any line other than 27 and 29
  that fails the lint, each listed in the hand-back. Lines 27 and 29 are left to ticket 12's wave D ops (R28).
- Whole-file staged copies under `S/tree/projects/beto/swong2/Alignment/.agents/memory/` with `expect_sha256` and
  `lint: true` for `usage-limit-policy.md` and `subagent-model-policy.md`.
- `S/tree/projects/beto/swong2/Alignment/.claude/agents/{idea-critic,paper-reader,paper-searcher}.md` with
  `model: opus` (whole-file writes with `expect_sha256`).
- `json_merge` into `/u/swong2/.claude/settings.json` (no hooks, so wave A): `env.CLAUDE_CODE_SUBAGENT_MODEL = "opus"`,
  `statusLine.refreshInterval = 60`, `cleanupPeriodDays = 365`, and new entries appended to `autoMode.environment`
  for Alignment and Deception-Circuit (remotes above, default branch `main`, NCSA Delta accounts beto, bimc, bgrb and
  bjhz, Bridges-2 allocation `cis260361p`, the public Deception-Circuit repository, and the data paths). Every
  existing entry, including the SHIFT_RT ones, stays exactly as it is (R31, OQ8).
- `text_block` (wave C, marker `autoresearch-workflow-agents`, `before_first_table`) into
  `/u/swong2/.codex/config.toml`: `[agents]` with `default_subagent_model = "gpt-6.1-sol"`. Ticket 06 verifies the
  key name against the Codex docs; if it differs, record that here as an open question.
- Optional (R11): the bridge sentence in `A/.agents/claude_codex_sync.py` (`sync_agents`, around line 315), staged
  with a copy of `A/.agents/tests/test_claude_codex_sync.py`, only if that test passes on the staged copy in both envs.
- `S/ops/01-hygiene.json` listing every op above.

In W (committed by the orchestrator):
- `F/tools/apply_staged.py` and `F/tools/test_apply_staged.py` (spec §7).

## Acceptance criteria

- [ ] Lint tests pass in both envs:
      `/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/tree/projects/beto/swong2/Alignment/.agents/tests/test_research_session_lint.py`
      and the same with `OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest ...`.
- [ ] `cli.py lint` over the clean corpus reports 0 failures, and over the three glued samples reports at least one
      failing unit for each of MEMORY.md lines 27 and 29 and for at least half of the units in RESUME.md lines 9-34.
      Paste the counts. Any allowlist addition is listed with the token that needed it (R10).
- [ ] The lint module exposes a function that lints a text string (not only a file), because the PreToolUse hook
      lints `content` and `new_string` before the write (R30). A test covers it.
- [ ] The secret scan flags synthetic tokens of every pattern in spec §5.5 and nothing in the clean corpus.
- [ ] Apply-tool tests pass in both envs and cover: write with backup and journal; idempotent re-run; an
      `expect_sha256` conflict; `json_merge` deep merge, hook-group de-duplication by command, list extension that
      never duplicates an identical entry and never removes one (R31); `text_block` before the first TOML table
      (parsed with `tomllib` on mgnp); `replace_text` with zero, one and two matches of `old_text` (only one applies);
      `append_text` skipping text already present; move; symlink; mkdir; `--dry-run` writes nothing; `--rollback`
      restores; the `--wave A|H|B|C|D` and `--only` filters; `lint: true` refusing glued content through `--lint-cmd`
      (default: base python3.9 on the staged `cli.py lint`, fallback to the installed path); and dry-run output that
      never prints a value under `env` (key paths only).
- [ ] `apply_staged.py --staging S --wave A --only 01 --dry-run` lists exactly the planned targets; output pasted.
- [ ] Staged memory files pass the lint, and no op in `S/ops/01-hygiene.json` touches a path R28 defers.
- [ ] Merging the settings fragment into a copy of `~/.claude/settings.json` inside T parses as JSON, adds three keys
      and appends entries to one list, keeps every existing `autoMode.environment` entry byte for byte (compare
      hashes, print nothing), and leaves the `env` block's existing key unchanged by hash.
- [ ] The Codex block applied to a copy of `config.toml` inside T parses with `tomllib` on mgnp, yields an `agents`
      table with `default_subagent_model`, keeps the top-level keys of lines 1-6 at top level, and leaves the bridge
      block byte-identical.
- [ ] Hygiene: remote URLs re-checked by reading the two `.git/config` files; secret scan run over
      `A/.claude/settings*.json`, `~/.codex/config.toml` and both `.git/config` files, with results recorded. The
      user settings `env` block is reported by key name only.
- [ ] The hand-back lists, for the orchestrator to run after checking `mechanism-datasets` is 0 commits ahead of
      main: `git -C /projects/beto/swong2/Alignment/Deception-Circuit worktree remove .claude/worktrees/mechanism-datasets`,
      `git -C ... branch -d mechanism-datasets`, and `git -C ... push origin --delete mechanism-datasets`.

## Verification

Both interpreters for every test file. Paste the dry-run output and the lint counts into the hand-back.

## Comments
