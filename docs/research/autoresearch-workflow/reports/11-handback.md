# Hand-back 11: pilot checklist and `audit-scan`

Agent: ticket-implementer, Opus. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/11-pilot-checklist-and-audit-scan.md`. Status: resolved.

No git command was run. Nothing was launched, applied or installed. No Slurm job and no paid API call was made. The
only writes outside W, S and T were the lock files that `research-session init` and `render` take under the RS
state root, as every RS command does.

## What changed

### Committed by the orchestrator from W

All paths are under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/`.

- `autoresearch-workflow/pilot-checklist.md` (new). Thirteen steps with sub-steps, a table of the hooks each step
  exercises, and the observation table with the columns step, expected, observed, pass or fail, and notes.
- `pilot-hooks/START.md` (new), written from `_templates/START.md` with every item filled in. Item 7 drops the
  template's five-hour clause (R40).
- `pilot-hooks/README.md`, `RESUME.md`, `WORKLOG.md`, `state.json`, `worklog.json` and `ledger.json` (new), created
  by `research-session init` together with START.md. See open question 2 for why they are included.
- `directions.json`: one `proposed` row `pilot-hooks` appended by `init`; nothing else changed (diff below).
- `DIRECTIONS.md`: one row added by `render`. `SESSIONS.md`: only the render time and the last-worklog time of the
  orchestrator's row changed.
- `autoresearch-workflow/reports/11-handback.md` (this file) and `autoresearch-workflow/issues/11-pilot-checklist-and-audit-scan.md`
  (status, checkboxes, comments).

### Staged in S, op file `S/ops/11-audit.json`, wave A

The op file is `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/ops/11-audit.json`, with three `write` ops,
all wave A:

1. `/projects/beto/swong2/Alignment/.agents/research_session/audit.py` (new, 478 lines).
2. `/projects/beto/swong2/Alignment/.agents/research_session/cli.py`, a whole-file write with `expect_sha256`
   664ca82c7ba3a30e1b6a9f4e968587422dee7d5c1ff51faf82b905c38ef1b87e. That is the installed file, re-hashed just before
   the op was written, and it equals the staged copy I started from. The change imports `audit`, appends it to
   `RECORD_MODULES` and adds a docstring paragraph: 7 lines added and 3 removed.
3. `/projects/beto/swong2/Alignment/.agents/tests/test_research_session_audit.py` (new, 17 tests).

Staged hashes: `cli.py` f8559a5c84a5..., `audit.py` 703c0b641318..., the test 5e3160b17fc0... The op file was built by
`/u/swong2/.claude/jobs/b2cb53cd/tmp/11/build_ops.py`, which refuses a new-file op whose destination exists.

### What `audit-scan` does

`research-session audit-scan <transcript.jsonl>... [--no-subagents] [--state STATE_JSON]...` prints one JSON report
and exits 0, or 2 when a path cannot be read. It never opens a file for writing, and the gate already lists it as a
read-only subcommand.

- **Inputs.** A main transcript brings in `<session>/subagents/agent-*.jsonl` unless `--no-subagents` is given. A
  directory brings in every `*.jsonl` under it, and each file is scanned once. Claude and Codex files are told apart
  by their first record.
- **Per agent (Claude).** Compactions from `compact_boundary` records with trigger, `preTokens` and `postTokens`,
  plus `first_compaction_preTokens`. It also gives the `isCompactSummary` count, tool calls and errors, and runs of
  three or more consecutive identical failing calls. It lists Agent or Task calls without a non-empty `model`, Bash
  commands repeated five or more times within 30 minutes, and denials. `agent_type` and `meta_model` come from the
  subagent's `.meta.json`, and no other meta key is read.
- **Per rollout (Codex).** The `compacted` count, with `window_number` and the last request's input tokens, plus
  `spawn_agent` calls without a model.
- **`--state`.** Compares each session's `compactions` in a direction `state.json` with its main transcript's
  count.
- **Echoed text.** Commands and inputs are whitespace-collapsed, cut to 200 characters and passed through the lint's
  secret patterns. Prompts, descriptions and message text are never echoed.

## How verified

### Key-only inspection of real transcripts

The inspection scripts print key names, short enum values and counts, never message text. They live in
`/u/swong2/.claude/jobs/b2cb53cd/tmp/11/` as `inspect_keys.py`, `inspect_focus.py`, `inspect_blocks.py` and
`inspect_codex_compacted.py`. Every run used base python3.9 with `-B -I`.

The orchestrator's transcript directory under the worktree project slug holds only `subagents/` and `tool-results/`.
Its main transcript sits under the Alignment project slug, because the session started in A. So a main transcript
and its subagents can live under two different project directories. The checklist names both paths for that reason.

```
/sw/external/python/anaconda3/bin/python3.9 -B -I /u/swong2/.claude/jobs/b2cb53cd/tmp/11/inspect_focus.py claude /u/swong2/.claude/projects/-projects-beto-swong2-Alignment/b2cb53cd-c11d-4cbf-9980-27c9ca779b04.jsonl <mechanism-datasets agent-aimpl-05 subagent> <mechanism-analysis agent-aimpl-04 subagent>
```

Key lines observed:

- The orchestrator transcript has 2,586 lines and 0 unparsable ones. It has one `system` record with subtype
  `compact_boundary`. Its `compactMetadata` keys are `cumulativeDroppedTokens`, `durationMs`, `postTokens`,
  `preCompactArtifactReadVersions`, `preCompactDiscoveredTools`, `preTokens`, `preservedMessages`,
  `preservedSegment` and `trigger`. The values were trigger auto and preTokens 368681. It also has one `user` record
  with `isCompactSummary`.
- Subagent records carry a top-level `agentId`; main-session records do not. The mechanism-analysis subagent
  compacted once, with trigger auto and preTokens 372086.
- Tool calls are `tool_use` blocks in `message.content` with keys `id`, `name` and `input`. Agent inputs had the keys
  `description`, `model`, `name`, `prompt` and `subagent_type` in the orchestrator transcript. In the
  mechanism-analysis subagent, its 3 Agent calls had no `model` key.
- Results are `tool_result` blocks in `user` records with keys `content`, `is_error`, `tool_use_id` and `type`.
- Denials: the mechanism-datasets subagent has 3 `user` records with a top-level `toolDenialKind` of
  `automode-blocked`. Those records also carry `permissionDecision` with `decision` reject and `source` config, and
  their `tool_result` has `is_error` true. Accepted calls carry `permissionDecision.decision` accept.
- Bash inputs have the keys `command`, `description` and sometimes `timeout`.
- Every record has `timestamp` in ISO form with a trailing `Z`, which Python 3.9's `fromisoformat` rejects. The
  parser normalises it.

```
/sw/external/python/anaconda3/bin/python3.9 -B -I /u/swong2/.claude/jobs/b2cb53cd/tmp/11/inspect_blocks.py <orchestrator transcript> <mechanism-datasets agent-aimpl-05 subagent>
```

Observed: besides `assistant` and `user` records, both files hold `api-request-blob` records that repeat earlier
`tool_use` and `tool_result` blocks: 77 and 10 in the orchestrator file, 26 and 6 in the subagent file. Every blob
`tool_use` id also appears in an `assistant` record. So the parser reads tool blocks only from `assistant` and `user`
records and deduplicates by id; a test covers it.

Subagent meta keys, from `agent-aimpl-06-920bb5c9991bbad4.meta.json`: `agentType`, `color`, `description`,
`isBuiltIn`, `model`, `name`, `permissionMode`, `planModeRequired`, `requestNonInteractive`, `requestShape`,
`spawnDepth`, `spawnedAgentType`, `taskKind` and `teamName`. The values printed were agentType impl-06 and model
opus.

Codex, three rollouts under `/u/swong2/.codex/sessions/2026/10/`:

- Top-level keys are `metadata`, `ordinal`, `payload`, `timestamp` and `type`.
- A `compacted` record's payload has `window_number`, `latest_token_usage_record` and others. Its
  `latest_token_usage_record.usage.input_tokens` was 176995 in one file and 172679 in another.
- `spawn_agent` is a `response_item` of payload type `function_call`. Its `arguments` is a JSON string whose keys are
  `agent_type`, `fork_turns`, `message`, `model` and `task_name`.

### Tests, test first

The new test file failed first on both counts because `audit-scan` did not exist (`invalid choice: 'audit-scan'`).
After `audit.py` and the `cli.py` change it passed. Then the full staged suite ran on both interpreters:

```
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/u/swong2/.claude/jobs/b2cb53cd/tmp/11 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/tree/projects/beto/swong2/Alignment/.agents/tests
269 passed, 19 subtests passed in 29.40s
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/u/swong2/.claude/jobs/b2cb53cd/tmp/11 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/tree/projects/beto/swong2/Alignment/.agents/tests
269 passed in 32.50s
```

That is the 252 installed tests plus 17 new ones. The new file alone gave 17 passed on each interpreter. The tests
cover the following:

- Compactions per agent with `preTokens`, including subagents found next to a main transcript and their meta model.
- `--no-subagents`, and a directory argument without duplicates.
- `api-request-blob` duplicates that must not be counted.
- Failing runs: a run of 4, two near misses, a run broken by a success, and key-order-insensitive inputs.
- Agent and Task calls without a model, including an empty string.
- Bash repeats inside and outside the 30-minute window, and the count in the best window against the total.
- Redaction of a fake token, assembled at run time, in echoed commands.
- Denials by `toolDenialKind` and by a `reject` decision.
- Codex `compacted` counts with input tokens, `spawn_agent` without a model, and a Codex subagent rollout.
- `--state` match, mismatch and unknown sessions; the state file is left untouched.
- Unparsable lines, every timestamp form, a missing path, a read-only check of the whole temporary tree, and
  `--help`.

### `audit-scan` on real transcripts (staged code, read-only)

```
/sw/external/python/anaconda3/bin/python3.9 -B /u/swong2/.claude/jobs/b2cb53cd/tmp/11/real_scan.py /u/swong2/.claude/projects/-projects-beto-swong2-Alignment/b2cb53cd-c11d-4cbf-9980-27c9ca779b04.jsonl /u/swong2/.claude/projects/-projects-beto-swong2-Alignment-Deception-Circuit--claude-worktrees-autoresearch-workflow/b2cb53cd-c11d-4cbf-9980-27c9ca779b04/subagents
files 18, errors 0, unparsable 0
totals {'agents': 18, 'compactions': 2, 'main_compactions': 1, 'codex_compacted': 0, 'compact_summaries': 2, 'tool_calls': 2023, 'tool_errors': 50, 'failing_runs': 0, 'agent_calls_without_model': 0, 'bash_repeats': 4, 'denials': 0}
claude main  ... compactions=[('auto', 368681)] summaries=1 calls=231 errors=5 agent_calls=17 no_model=0
claude aplan-01-d6d2eb3b41d5d0c7 type=plan-01 meta_model=opus compactions=[('auto', 469658)] summaries=1 calls=321 bash_repeats=[(10, 15)]
(16 more subagents, each meta_model=opus, no compaction)
```

The orchestrator made 17 unique Agent calls, all with a model, and there are 17 subagent transcripts with Opus meta.
The main transcript's 18 Agent blocks include one `api-request-blob` duplicate, which the parser correctly skips.

```
/sw/external/python/anaconda3/bin/python3.9 -B /u/swong2/.claude/jobs/b2cb53cd/tmp/11/real_scan.py <mechanism-datasets agent-aimpl-05> <mechanism-analysis agent-aimpl-04> <Codex rollout 2026-10-26T15-14-02> <Codex rollout 2026-10-17T14-21-03>
claude aimpl-05-98fb750151da6364 type=impl-05 meta_model=opus ... denials=['automode-blocked', 'automode-blocked', 'automode-blocked']
claude aimpl-04-9ac6145034891b22 type=impl-04 meta_model=claude-fable-5-1 compactions=[('auto', 372086)] agent_calls=3 no_model=3
codex main compactions=[(None, 310135)] agent_calls=5 no_model=0
codex main compactions=[(None, 172679)] agent_calls=14 no_model=0
```

These are the known real signals. One subagent had three automode denials. The 26 October subagent that ran on Fable
spawned three agents without a model. Every Codex spawn named its model. The same agent-aimpl-04 scan through the
staged `cli.py` as a script also printed the full JSON report with exit 0.

### The pilot direction

```
/u/swong2/.local/bin/research-session usage-check --no-refresh
reading (claude): five-hour not applicable, seven-day 18%, Fable 22%, weekly max 22%
refresh: not needed
```

I checked first that the reading was fresh, so `init` could not cause a token fetch; `worklog.py` does not read
usage anyway.

```
/u/swong2/.local/bin/research-session lint /u/swong2/.claude/jobs/b2cb53cd/tmp/11/START.md
(no output, exit 0)
/u/swong2/.local/bin/research-session init pilot-hooks --root /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research --from-start /u/swong2/.claude/jobs/b2cb53cd/tmp/11/START.md
.../docs/research/pilot-hooks: created START.md, README.md, RESUME.md, state.json, ledger.json, worklog.json, WORKLOG.md
added a proposed row for pilot-hooks to directions.json; it is not claimed
```

The `directions.json` diff against the snapshot in T adds only the row with `"id": "pilot-hooks"`, `"status":
"proposed"`, `"title": "Pilot of the research-session hooks"`, `"claimed_by": null` and `dir`, `resume`, `worklog`,
`state` and `ledger` under `docs/research/pilot-hooks`. Its summary is init's placeholder.

```
/u/swong2/.local/bin/research-session validate .../docs/research/directions.json .../pilot-hooks/state.json .../pilot-hooks/worklog.json .../pilot-hooks/ledger.json
(each) valid
/u/swong2/.local/bin/research-session render --root /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research
DIRECTIONS.md written; SESSIONS.md written
/u/swong2/.local/bin/research-session lint --summary <pilot-hooks START.md, README.md, RESUME.md, WORKLOG.md> <DIRECTIONS.md> <SESSIONS.md>
lint: 6 file(s), clean
/u/swong2/.local/bin/research-session lint --summary .../autoresearch-workflow/pilot-checklist.md
lint: 1 file(s), clean
```

### Facts the checklist relies on

- The gate's `READ_ONLY_SUBCOMMANDS` already include `audit-scan` (`gate.py:35`), so step 12's command with
  `--state .../state.json` passes the self-acknowledgement guard.
- The expected texts in steps 2 to 7 are copied from the installed `hooks.py`, `gate.py` and `cli.py`. They are the
  H-a start text, the H-b compaction text and the H-c file header. They also include the denial reasons for the
  freeze, messages, the lint and the guard, plus the H-e, H-g, H-h, H-i and H-j texts and the `set-cadence` and
  `register` output lines.
- `usage-check --no-refresh` on a stale file prints "refresh: not attempted (--no-refresh)" and exits 1
  (`cli.py:163`, `usage.py:143`).
- The four profiles match spec §5.7 today. The research profile adds nnsight, writing adds the two academic plugins,
  audit adds session-report, and synthesis adds nothing:

```
/sw/external/python/anaconda3/bin/python3.9 -c "<print true enabledPlugins per profile>"
audit.json ['claude-md-management', 'code-review', 'github', 'mattpocock-skills', 'session-report', 'superpowers']
research.json ['claude-md-management', 'code-review', 'github', 'mattpocock-skills', 'nnsight', 'superpowers']
synthesis.json ['claude-md-management', 'code-review', 'github', 'mattpocock-skills', 'superpowers']
writing.json ['academic-research-skills', 'academic-writing-agents', 'claude-md-management', 'code-review', 'github', 'mattpocock-skills', 'superpowers']
```

- `CLAUDE_CODE_SUBAGENT_MODEL` is present in the user `env` and equals opus. Only that boolean pair was printed.
- `modelSettings.claude-opus-5-5` holds `autoCompactWindow` 600000.
- session-report is not in `installed_plugins.json`, and its user `enabledPlugins` value is False. So step 1e is
  still to do.
- `claude_codex_sync.py` has a `--check` flag that reports drift without writing (`claude_codex_sync.py:535`).

### Apply-tool dry run

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging --only 11 --wave A --dry-run
dry run, wave A: 3 op(s) selected from 3
[11#1] write /projects/beto/swong2/Alignment/.agents/research_session/audit.py WOULD APPLY: +478 -0 lines, new file
[11#2] write /projects/beto/swong2/Alignment/.agents/research_session/cli.py WOULD APPLY: +7 -3 lines
[11#3] write /projects/beto/swong2/Alignment/.agents/tests/test_research_session_audit.py WOULD APPLY: +399 -0 lines, new file
```

After applying, the orchestrator should run the RS tests from the installed path on both interpreters and expect 269
passed. Then run the installed smoke test, because `cli.py` imports `audit` at start-up. An import error there would
show a hook-error notice on every tool call; the kill switch is the remedy (06 open question 3).

### Usage at hand-back

At 4:23 pm EDT the weekly reading was 18% for all models and 22% for Fable. The Fable gap was 4 points, and there is
no five-hour window.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- Nothing is applied. Wave A for ticket 11 is the orchestrator's, and the pilot itself is the user's.
- No real hook denial was found in any transcript I inspected, because the hooks were installed only today. So
  whether a PreToolUse hook denial carries `toolDenialKind` or a `reject` decision is unknown. If it carries neither,
  `audit-scan` shows it only as a `tool_errors` entry. Step 12a asks the pilot to record which.
- Codex parsing covers only what the ticket names: `compacted` counts plus spawns without a model. Codex errors,
  shell polling and denials are not parsed.
- The step 9 cost estimate is a guess. No measured figure exists for one Opus agent reading to 600k tokens.
- The ticket 06 request to record one real payload per hook event is not in the checklist. RS logs no payloads, and
  adding a recorder would mean a hook change, which is out of this ticket's scope.

## Open questions

1. **The planner subagent compacted at 469,658 tokens on 31 October 2026.** That was after the 600k Opus setting
   existed. It is above the old pattern of about 370k but below the 550k pass mark, and one large read can
   overshoot the trigger. Default: treat R20 as still binding, which keeps briefs under 350k tokens, until step 9
   passes.
2. **`init` created seven files, not only START.md.** `init` is the only RS command that adds a `proposed` row (R39).
   The extra records are also what the pilot needs. `register` mirrors into the direction's `state.json` and skips
   when the directory is missing (`state.py:310`), and the lint and compaction drills write to `WORKLOG.md` and
   `RESUME.md`. Default: commit all seven with the row.
3. **The row's summary is init's placeholder.** No RS command sets a summary, and R39 forbids hand edits. Default:
   leave it until `release pilot-hooks --status done`, and let ticket 12 or the user decide if a summary command is
   wanted.
4. **Step 1e uses the staging root.** The session-report install re-runs ticket 07's wave A apply from
   `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging`, which disappears when this job is deleted. Default: the
   orchestrator runs step 1e before the job ends, or keeps a copy of the staging root.
5. **Claim flow in step 2.** The checklist starts the pilot in DC main, claims and commits there, then enters the
   worktree with EnterWorktree and registers. The register mirror path comes from the session's recorded working
   directory, so step 2d marks a DC main path as a fail. Default: as written. If 2d fails, register again with
   `--session` after the first tool call in the worktree, and record it as a hook finding.
6. **Hook denials in `audit-scan`.** If step 12a shows that hook denials appear only as `tool_errors`, `audit-scan`
   needs one more rule, for example matching the `permissionDecision.source` value hooks use. Default: extend the
   parser after the pilot, with a recorded record shape as a fixture.
