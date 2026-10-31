# 01 — Hand-back: text lint, staging apply tool, hygiene and config

Implementer: Opus, ticket 01, 2026-10-31. No git command was run, nothing was installed or applied, and no hook was
written. Every change to the Alignment checkout or to user configuration is staged under S and listed in one op file.

## What changed

### Committed by the orchestrator from W

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/test_apply_staged.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/01-handback.md` (this file)
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/01-lint-apply-tool-hygiene-config.md` (status, checkboxes and comments)

### Staged in S, ops file `S/ops/01-hygiene.json`

The ops file is `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/ops/01-hygiene.json`. It holds 21 ops: 19 in
wave A and 2 in wave C. Staged sources live under `S/tree/` at the destination path.

Wave A (19 ops):

1. New RS files: `A/.agents/research_session/__init__.py`, `cli.py` (argparse skeleton with the `lint` subcommand) and
   `lint.py`.
2. New tests: `A/.agents/tests/test_research_session_lint.py` and eight fixtures in `A/.agents/tests/fixtures/lint/`
   (three glued excerpts, five clean excerpts, each copied byte for byte from the source lines named below).
3. `A/.agents/memory/usage-limit-policy.md`, whole-file write with `expect_sha256` 71d924528757... and `lint: true`. The
   weekly cap moves from 75% to 80%, and the weekly reading is recorded as `max(seven_day, Fable model_scoped row)`
   (R9). Three sentences change, in the description and in the body.
4. `A/.agents/memory/subagent-model-policy.md`, whole-file write with `expect_sha256` d9bf4405cd4d... and `lint: true`.
   One new section is appended, saying both defaults are staged as a safety net and that H1 moves the three agent
   definitions to Opus (R24). The two overlapping Codex sections written today by the live session are untouched.
5. `A/.agents/memory/MEMORY.md`, one `replace_text` op with `lint: true` on the usage-limit-policy index line, which
   said "/ 75% weekly". The new text says "/ 80% weekly (raised from 75% on 2026-10-31)". Lines 27 and 29 are not
   touched (R28).
6. `A/.claude/agents/idea-critic.md`, `paper-reader.md` and `paper-searcher.md`, whole-file writes with
   `expect_sha256`; line 4 changes from `model: sonnet` to `model: opus` (R24).
7. `json_merge` into `/u/swong2/.claude/settings.json`: `env.CLAUDE_CODE_SUBAGENT_MODEL`, `statusLine.refreshInterval`
   and `cleanupPeriodDays` are added, and six entries are appended to `autoMode.environment`. The entries cover the
   Alignment and Deception-Circuit repositories, their remotes and default branch `main`, the public Deception-Circuit
   repository, the Delta accounts beto, bimc, bgrb and bjhz, the Bridges-2 allocation `cis260361p`, and the data
   paths. No hook is in the fragment.

Wave C (2 ops, both need the user's go because Codex must restart):

1. `text_block` into `/u/swong2/.codex/config.toml`, marker `autoresearch-workflow-agents`, position
   `before_first_table`: `[agents]` with `default_subagent_model = "gpt-6.1-sol"` (R11).
2. The optional bridge sentence (R11): `A/.agents/claude_codex_sync.py`, whole-file write with `expect_sha256`
   a0a337033f2b.... The developer instruction "inherit the parent's Codex model" becomes "Your model comes from the
   spawn call, else from `[agents] default_subagent_model` in the Codex config when it is set, else from the parent".
   It is wave C because it describes the wave C config. An unchanged copy of `test_claude_codex_sync.py` is staged
   beside it only so the bridge test runs against the staged bridge; it has no op.

`S/README.md` was rewritten. It used to say staged files are copied with plain `cp`. It now says the op files are
authoritative, gives the apply command, and says a file under `tree/` without an op is not installed.

### Scratch files in T

Helper scripts are in `/u/swong2/.claude/jobs/b2cb53cd/tmp/01/`: `stage_hygiene.py` (writes the staged memory, agent and
op files, reading each live file once for its hash), `stage_bridge.py`, `make_fixtures.py`, `glued_counts.py`,
`verify_t_copies.py` and `check_r28.py`. The copies of the user settings and Codex config made for verification were
deleted by the script that made them.

## How verified

### Lint tests, both interpreters

```
PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider S/tree/projects/beto/swong2/Alignment/.agents/tests
35 passed, 19 subtests passed in 0.84s
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider S/tree/projects/beto/swong2/Alignment/.agents/tests
35 passed in 0.71s
```

The 35 tests are 29 lint tests and the 6 bridge tests running against the staged bridge. The lint file alone gives
29 passed on both interpreters.

### Apply-tool tests, both interpreters

```
PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider F/tools/test_apply_staged.py
33 passed in 0.56s
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider F/tools/test_apply_staged.py
33 passed in 1.04s
```

The 33rd test came from the final review. A `replace_text` whose new text was a shortened copy of the old text was
reported as SKIP on its first run and changed nothing. Ticket 12's pointer-line rewrites of MEMORY.md have that
shape. The test failed first, the idempotency check was fixed, and both suites were re-run.

The tests cover the following:

- write with backup and journal, an idempotent re-run that carries `expect_sha256`, and an `expect_sha256` conflict;
- `json_merge` deep merge, list extension without duplicates or removals, and hook groups de-duplicated by matcher
  and command;
- `text_block` before the first TOML table (parsed with `tomllib` on mgnp, skipped on 3.9), including replace and
  idempotence;
- `replace_text` with zero, one and two matches (only the single match applies), and `append_text` skipping present
  text;
- move, symlink and mkdir, each with rollback;
- `--dry-run` writing nothing, including no backup directory, and `--rollback` restoring or refusing after a later
  edit;
- the `--wave` and `--only` filters, `--allow codex-config`, and `lint: true` refusing glued content through a fake
  `--lint-cmd`;
- default lint-command resolution (staged first, then installed), output that never prints any value under `env`,
  the R26 refusal and the R28 refusal.

### Lint counts on the clean corpus and the glued samples

```
python3.9 -B S/.../research_session/cli.py lint --summary F/reports/lane1-public-patterns.md F/reports/lane2-harness.md F/reports/lane3-repo-structure.md F/reports/lane4-oversight.md F/reports/proposal-full.md W/docs/research/sdr-mechanism/README.md W/docs/research/mechanism-analysis/synthesis.md
lint: 7 file(s), clean
```

Glued samples, counted per unit by `T/01/glued_counts.py` with the final lint:

| Sample | Failing units | Rules hit |
|---|---|---|
| MEMORY.md line 27 | 1 of 1 | long-token |
| MEMORY.md line 29 | 1 of 1 | join |
| RESUME.md lines 9-34 | 9 of 13 | long-token in 9 units, join in 5 of them |

The four passing RESUME units are the line 9 paragraph (4 long tokens in 32), two short units under 8 tokens after
path-like tokens are dropped (lines 21 and 27), and the clean heading at line 32. The whole-file lint of MEMORY.md
fails only on lines 27 and 29, so no other MEMORY.md line needed a lint repair.

Allowlist additions (R10), each with the token that needed it:

- File names with a known extension, needed by `lane1-public-patterns.md` in `proposal-full.md:3`.
- Lower-case kebab-case identifiers with at least three short parts, two of them purely alphabetic, needed by
  `claude-md-management` and `cc-plugin-you-should-know` in `lane2-harness.md:119`. The alphabetic-part condition was
  added after the first version exempted the glued token `locally2026-10-31` on MEMORY.md line 27.

Both additions apply to both rules, because the second clean failure was a long-token failure. In the glued samples
they exempt four glued tokens, `inpriority-review.md`, `sdr-routing-pilot`, `tofreeze-final-4f02784.json` and
`logsamebasename.log`. Every unit holding them still fails, and with the spec's base allowlist the counts above are
identical.

### Secret scan

The synthetic tokens are assembled at run time, one per pattern of spec §5.5 (14 cases), and every one is flagged.
The tests also show that output never echoes the token, that prefix names in documentation are not flagged, and that
the clean fixtures have no secrets. Hygiene scan:

```
python3.9 -B S/.../research_session/cli.py lint --secrets-only --summary A/.claude/settings.json A/.claude/settings.local.json /u/swong2/.codex/config.toml A/.git/config DC/.git/config
lint: 5 file(s), clean
```

Remote URLs were re-checked by reading the two files: `A/.git/config:8` is `https://github.com/JaMussCraft/LLM-Alignment.git`
and `DC/.git/config:7` is `https://github.com/JaMussCraft/Deception-Circuit.git`. Neither holds a token. The user settings `env` block has one
key, `GITHUB_PERSONAL_ACCESS_TOKEN`; its value was never printed.

### Wave A dry run (default lint command)

```
/sw/external/python/anaconda3/bin/python3.9 -B F/tools/apply_staged.py --staging /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging --wave A --only 01 --dry-run
dry run, wave A: 19 op(s) selected from 21
[01#1] write /projects/beto/swong2/Alignment/.agents/research_session/__init__.py WOULD APPLY: +7 -0 lines, new file
[01#2] write /projects/beto/swong2/Alignment/.agents/research_session/cli.py WOULD APPLY: +62 -0 lines, new file
[01#3] write /projects/beto/swong2/Alignment/.agents/research_session/lint.py WOULD APPLY: +273 -0 lines, new file
[01#4] write /projects/beto/swong2/Alignment/.agents/tests/test_research_session_lint.py WOULD APPLY: +228 -0 lines, new file
[01#5] write /projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/clean_lane2_plugin_table.md WOULD APPLY: +5 -0 lines, new file
[01#6] write /projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/clean_lane4_section0.md WOULD APPLY: +7 -0 lines, new file
[01#7] write /projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/clean_proposal_header.md WOULD APPLY: +5 -0 lines, new file
[01#8] write /projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/clean_synthesis_prose.md WOULD APPLY: +6 -0 lines, new file
[01#9] write /projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/clean_synthesis_table.md WOULD APPLY: +9 -0 lines, new file
[01#10] write /projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/glued_memory_line27.md WOULD APPLY: +1 -0 lines, new file
[01#11] write /projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/glued_memory_line29.md WOULD APPLY: +1 -0 lines, new file
[01#12] write /projects/beto/swong2/Alignment/.agents/tests/fixtures/lint/glued_resume_excerpt.md WOULD APPLY: +7 -0 lines, new file
[01#13] write /projects/beto/swong2/Alignment/.agents/memory/usage-limit-policy.md WOULD APPLY: +5 -4 lines
[01#14] write /projects/beto/swong2/Alignment/.agents/memory/subagent-model-policy.md WOULD APPLY: +9 -0 lines
[01#15] replace_text /projects/beto/swong2/Alignment/.agents/memory/MEMORY.md WOULD APPLY: +1 -1 lines
[01#16] write /projects/beto/swong2/Alignment/.claude/agents/idea-critic.md WOULD APPLY: +1 -1 lines
[01#17] write /projects/beto/swong2/Alignment/.claude/agents/paper-reader.md WOULD APPLY: +1 -1 lines
[01#18] write /projects/beto/swong2/Alignment/.claude/agents/paper-searcher.md WOULD APPLY: +1 -1 lines
[01#19] json_merge /u/swong2/.claude/settings.json WOULD APPLY: +13 -4 lines; + env.CLAUDE_CODE_SUBAGENT_MODEL, + statusLine.refreshInterval, + cleanupPeriodDays, + autoMode.environment[] (6 entries appended)
```

The four removed lines in the settings merge are trailing-comma changes on the lines before each appended item. The
file stores non-ASCII characters as `\u` escapes, and the tool keeps that style, so an unchanged load and dump of the
file is byte-identical (checked with string literals masked). The wave C dry run with `--allow codex-config` lists
the Codex block (+5 -0 lines) and the bridge write (+1 -1 lines).

### Settings and Codex copies inside T

`T/01/verify_t_copies.py` copied both files into T, applied the real ops through `apply_staged.main` with the targets
redirected to the copies, checked them on mgnp, and deleted the copies:

```
wave A exit 0; output mentions a value of env: False
wave C exit 0; output mentions a value of env: False
settings parses: True
new top-level keys: ['cleanupPeriodDays']; new env keys: ['CLAUDE_CODE_SUBAGENT_MODEL']; new statusLine keys: ['refreshInterval']
existing env key(s) unchanged by hash: True (keys: ['GITHUB_PERSONAL_ACCESS_TOKEN'])
autoMode.environment entries before/after: 25/31; every existing entry kept byte for byte, in place: True
all other top-level values unchanged by hash: True
codex config parses with tomllib: True; agents table: {'default_subagent_model': 'gpt-6.1-sol'}
lines 1-6 keys still top level with same values: True; bridge block byte-identical: True
tables other than agents unchanged: True; copies removed: True
```

### Staged memory and R28

```
python3.9 -B S/.../research_session/cli.py lint --summary S/tree/.../memory/usage-limit-policy.md S/tree/.../memory/subagent-model-policy.md
lint: 2 file(s), clean
python3.9 -B T/01/check_r28.py
ops: 21; waves: ['A', 'C']; R28 protected targets: []; hook-installing ops: []
MEMORY.md ops: [('replace_text', 'stay under 80% 5-hour (lowered 2026-10-2')]
memory ops without lint:true: []; whole-file memory writes without expect_sha256: []
```

The dry run also ran the lint on the three memory ops through the default lint command, and none was refused.

## Execution evidence

Not applicable: no runs. No Slurm job, GPU job or paid API call was made.

## What is NOT done

- Nothing is applied. The orchestrator applies wave A after review and wave C after the user's go.
- MEMORY.md lines 27 and 29 and the two live-session memory notes are left to ticket 12's wave D ops (R28).
- `usage-limit-policy.md` still gives agents a self-check rule of "hold at 70% / 72%", which was set for the old 75%
  weekly cap. I left it unchanged, because R9 names only the cap and the weekly reading.
- The Codex key name `default_subagent_model` is not verified against the Codex docs. Ticket 06 verifies it.
- The orchestrator runs these commands after checking that `mechanism-datasets` is 0 commits ahead of main:

```
git -C /projects/beto/swong2/Alignment/Deception-Circuit worktree remove .claude/worktrees/mechanism-datasets
git -C /projects/beto/swong2/Alignment/Deception-Circuit branch -d mechanism-datasets
git -C /projects/beto/swong2/Alignment/Deception-Circuit push origin --delete mechanism-datasets
```

## Open questions

1. **Lint scope for text ops (deviation from spec §7 wording).** For `write`, `lint: true` lints the whole resulting
   file. For `replace_text`, `append_text` and `text_block`, the tool lints the file before and after the op and
   refuses only failures the op introduces. Otherwise every MEMORY.md op fails until lines 27 and 29 are rewritten in
   wave D, and ticket 12's two wave D line ops could not both apply. Tickets 05, 08 and 12 rely on this behaviour.
2. **Hook-group de-duplication (refinement of "compare by command string").** A fragment hook group counts as
   present when an existing group has the same matcher and contains all of its commands. A group with the same
   command but a different matcher is appended, so the SessionStart groups H-a (`startup|resume`) and H-b
   (`compact`) can share one command. Ticket 06 builds on this.
3. **Allowlist used by both rules.** The two additions above are pattern classes, and the spec's allowlist was
   written for the join rule only. If the orchestrator prefers a join-only allowlist, lane2-harness.md line 119 fails
   the long-token rule and needs a ruling.
4. **Secret patterns.** The bare prefixes in spec §5.5 (`github_pat_`, `sk-ant-`, `sk-or-v1-`, `xox?-`) require a
   token body after the prefix (20 or 10 characters), so documents that name a prefix do not fail. I also added the
   `sk-proj-` pattern.
5. **Safety nets beyond spec §7.** The apply tool refuses a hook-installing op (a `json_merge` fragment with `hooks`,
   or a staged JSON file with `hooks`) outside wave H (R26). It also refuses a wave A or B op on a path R28 defers. That
   covers `.scratch/sdr-*`, `selective-deception` and `eval5-grader-fixes`, the two live-session notes, and MEMORY.md
   text ops that name those notes.
6. **Apply-tool interface choices.** `--wave` is required unless `--rollback` is given. `--backup-root` exists for
   tests and defaults to `/u/swong2/.claude/research-session/backups`. `json_merge` replaces a differing scalar inside
   a dict and reports it as `~ key.path`; lists only extend. Ticket 07 may need that to switch an `enabledPlugins`
   value. An op on any `.codex/config.toml` needs `--allow codex-config`. A `lint: true` refusal prints unit
   excerpts, which never contain a secret match. Tickets 06 and 07 should still not set `lint: true` on JSON settings
   ops, because an excerpt could then show an `env` value.
7. **Scope widened by one op.** The MEMORY.md index line for usage-limit-policy did not fail the lint, but it would
   contradict the updated note, so one `replace_text` op updates it.
8. **Planner open question 8.** The SHIFT_RT entries of `autoMode.environment` are kept unchanged, as R31 says. The
   user may still want to confirm that SHIFT_RT should stay covered.
