# Spec: autoresearch workflow setup (binding)

Date: 2026-10-31. Status: binding for tickets 01-12. Source design: `reports/proposal-full.md` (approved by the user
on 2026-10-31 with decisions D1-D8). Evidence for every repo fact used here is in `reports/00-plan-handback.md`.
Where this spec and the proposal differ, this spec wins and the difference is a numbered ruling in §9.

Short names: **A** is `/projects/beto/swong2/Alignment`; **DC** is its main `Deception-Circuit` checkout; **W** is
the worktree `DC/.claude/worktrees/autoresearch-workflow`; **F** is `W/docs/research/autoresearch-workflow`; **S** is
the staging root `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging`; **RS** is the research-session package at
`A/.agents/research_session/` (R1).

## 1. Intent

Research state lives in prose across memory, `.scratch`, reports and handoffs, and every safety rule depends on the
orchestrator remembering it. This feature adds one index, a CLI that owns counters and readings, hooks in both tools,
lean profiles, written session protocols, and provenance guards in the experiment code.

## 2. Goals and non-goals

Goals: (1) a fresh synthesis agent orients from `INDEX.md`, `FINDINGS.md` and `SESSIONS.md` in under 30k tokens;
(2) checkpoints, cap pauses, compaction counts and hand-back capture are enforced by hooks in Claude and Codex;
(3) subagent model defaults are pinned (Opus in Claude, Sol in Codex) as a safety net; (4) worklogs and machine
state are separate, and writes to them are linted before they land; (5) new runs carry a commit-stamped provenance
file, verdicts need execution evidence, and paper claims need seed replication and a frozen grader; (6) closed
`.scratch` directions not owned by a live session are archived byte for byte and their Markdown is indexed.

Non-goals: GPU jobs or paid API calls (the pilot only describes what the user launches); provenance backfill for old
runs (R16); a code guard against scoring held-out instances (R19); any change to a frozen archive, receipt,
hash-pinned file or historical manifest; any bridge change beyond one sentence (R11).

## 3. Target layout

```
DC/docs/research/
  INDEX.md            how to read this tree, in reading order; one page
  FINDINGS.md         one row per claim (schema §4.1)
  directions.json     direction registry (schema §4.2); rendered to DIRECTIONS.md
  DIRECTIONS.md       rendered by RS, never hand-edited
  SESSIONS.md         rendered by RS from directions.json and state.json files (§4.3)
  ledger.json         global spend roll-up, rendered by RS (§4.4)
  held-out.md         held-out instance policy (§6.4); held_out.json is its registry
  _templates/         START.md, proposal.md, WORKLOG.md, RESUME.md, state.json, ledger.json, handback.md, audit.md
  <slug>/             one per direction:
    README.md         handoff: question, verdict, pointers; two pages at most
    START.md          the prompt the session was launched with
    spec.md           frozen design with pre-registered rules and the frozen grader hash
    WORKLOG.md        human log, written only through `worklog-append`; template in _templates
    worklog.json      structured fields behind the WORKLOG head and registers (§4.8); written only by RS
    RESUME.md         machine narrative state; overwritten; 150 lines at most
    state.json        counters, usage segments, checkpoints, jobs (§4.5); written only by RS
    ledger.json       reservations and spend (§4.4)
    reports/ reviews/ handbacks/ history/ issues/
DC/outputs/<run>/run_manifest.json   written by run_io.make_run_dir and by evaluate_circuit cells (§4.6, R2)
DC/outputs/_studies/<slug>/scratch/  byte-identical archive of a migrated .scratch directory (R3)
A/.scratch/<slug> -> DC/outputs/_studies/<slug>/scratch   symlink, same as the selective-deception precedent
A/.scratch/autoresearch-workflow -> DC/docs/research/autoresearch-workflow   the one exception (R34)
A/.agents/research_session/          the RS package (R1); tests in A/.agents/tests/test_research_session_*.py
A/docs/agents/research-session.md, synthesis-session.md, session-audit.md   protocols (ticket 08)
```

Direction directories are created by sessions as needed. A paused direction keeps only what it already has plus a
`ledger.json`; `RESUME.md`, `WORKLOG.md` and `state.json` are created from `_templates/` when a session resumes it.

## 4. Schemas

All JSON files carry `"schema": 1` and are validated by `research-session validate <path>`. RS writes JSON with
`indent=2`, sorted keys inside each record, and a trailing newline, so diffs stay small.

### 4.1 FINDINGS row

```
| id | date | direction | claim | status | commit | evidence | report |
|----|------|-----------|-------|--------|--------|----------|--------|
| F-sdr-007 | 2026-10-26 | sdr-mechanism | One sentence claim. | verified | 695b126 | outputs/_analyses/x/run_manifest.json | docs/research/sdr-mechanism/reports/y.md |
```

- `id` is `F-<direction-short>-NNN`, never reused. `date` is ISO. `claim` is one sentence with no line break.
- `status` is one of `proposed`, `executed`, `reviewed`, `verified`, `replicated`, `refuted`, `superseded`, `paused`.
- `verified` needs at least one evidence path that is a provenance file naming a 40-hex commit (§6.1).
  `replicated` needs `verified` plus evidence from at least two runs with distinct seeds (§6.5).
- `commit` is the short SHA of the producing code, or `pre-manifest` when no provenance file exists (R16).
- `evidence` holds repo-relative paths separated by `<br>`. `report` is one repo-relative path.
- A superseded row stays and its claim ends with `(superseded by F-x-NNN)`. Rows are never deleted.

### 4.2 directions.json

```json
{"schema": 1, "updated": "2026-10-31", "directions": [
 {"id": "sdr-mechanism", "title": "How shared SDR heads compose into deceptive reporting",
  "status": "paused", "status_source": "docs/research/sdr-mechanism/README.md", "summary": "One sentence.",
  "claimed_by": null, "claimed_at": null, "branch": null, "worktree": null,
  "dir": "docs/research/sdr-mechanism", "spec": null, "resume": null, "worklog": null, "state": null,
  "ledger": "docs/research/sdr-mechanism/ledger.json", "frozen_grader_sha256": null,
  "parent_findings": ["F-sdr-001"], "do_not_touch": ["outputs/_analyses/sdr-*"],
  "legacy_scratch": [".scratch/sdr-cue-probe"], "archive": ["outputs/_studies/sdr-cue-probe/scratch"],
  "updated": "2026-10-31"}]}
```

- `status` is one of `proposed`, `open`, `claimed`, `active`, `paused`, `done`, `abandoned`.
- `claimed_by` is `<tool>-<short session id>`: tool is `claude` or `codex`, and the short id is the first 8
  characters of the session id. This session's tag is `claude-b2cb53cd` (R29). A synthesis session may only add
  `proposed` rows.
- `status_source` names the file that justifies the status. Uncertain closed directions are `paused`, not `done`.

### 4.3 SESSIONS.md render

One row per direction with a non-null `claimed_by`, grouped by session:
`| Session | Directions claimed | State | Last worklog entry | Worklog | Do not touch |`. State comes from the direction's
`state.json` field `session_state`; the last entry time comes from `last_worklog_entry_at`. A header line states the
render time and says the file is generated.

### 4.4 ledger.json (per direction) and the global roll-up

```json
{"schema": 1, "direction": "selective-deception",
 "caps": {"reserved_gpu_hours": 40.0, "paid_api_usd": 20.0, "max_concurrent_gpu_jobs": 2},
 "totals": {"reserved_gpu_hours": 38.35, "actual_gpu_seconds": 45167, "api_usd_known": 4.18, "api_usd_reserve": 0.66},
 "reservations": [{"id": "r-001", "job_id": "123", "cluster": "delta", "account": "bimc-delta-gpu",
   "partition": "gpuA40x4", "gpus": 1, "requested_minutes": 15, "reserved_gpu_hours": 0.25, "actual_seconds": null,
   "status": "RUNNING", "source_commit": "abc1234", "manifest_hash": null, "output_dir": "outputs/..."}],
 "api_calls": [{"date": "2026-10-31", "provider": "openrouter", "calls": 0, "usd": 0.0}],
 "converted_from": null}
```

Reservation `status`: `PLANNED`, `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `TIMEOUT` or
`OUT_OF_MEMORY`. `converted_from` names a converted legacy ledger. `ledger-rollup` renders the global
`docs/research/ledger.json` as `{"schema": 1, "generated": ..., "directions": {id: totals}, "totals": {...}}`.

### 4.5 state.json (per direction, tracked) and the local session file

The local session file `/u/swong2/.claude/research-session/sessions/<tool>-<session_id>.json` is authoritative for
gate decisions (R5). Every RS write to it is mirrored into the registered direction's `state.json` under
`sessions.<tool>-<short session id>`, the same tag as `claimed_by` (R29). Models never edit either file (§5.3).

```json
{"schema": 1, "direction": "pilot-hooks", "session_state": "running", "last_worklog_entry_at": "2026-11-02T10:05:00-06:00",
 "sessions": {"claude-01a2b3c4": {
   "tool": "claude", "session_id": "...", "cwd": "/abs/worktree", "started_at": "...", "orchestrator_model": "claude-fable-5-1",
   "compactions": 2, "compaction_log": [{"n": 1, "at": "...", "trigger": "auto"}],
   "usage": {"metric": "max(seven_day, Fable)", "cadence": 16, "segments": [{"resets_at": 1793797200, "baseline": 11, "last": 27}],
     "session_points": 16, "registered_at": "...", "points_at_register": 0, "next_checkpoint": 1, "acked_through": 0, "stale_ok_until": null,
     "freeze": {"checkpoint": 1, "stage": "crossed", "crossed_at": "...", "recorded_at": null},
     "last_reading": {"five_hour": 9, "seven_day": 11, "fable": 17, "read_at": "...", "fresh": true}},
   "checkpoints": [{"n": 1, "at": "...", "session_points": 16, "all_models": 27, "fable": 33, "acked_at": null, "acked_by": null}],
   "agents": {"a1b2": {"agent_type": "ticket-implementer", "started_at": "...", "stop_blocks": 0}}}},
 "jobs": [{"job_id": "123", "cluster": "delta", "submitted_at": "...", "waiter": "until sacct ...; do sleep 300; done",
   "expected_terminal": ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL"],
   "status": "PENDING", "last_progress_at": "..."}]}
```

`freeze.stage` is `crossed` (threshold passed, block not yet written) or `recorded` (checkpoint block written by
`worklog-append --checkpoint`). `acked_by` is `prompt` (a human message starting with "continue") or `usage-ack`.

### 4.6 run_manifest.json (R2)

```json
{"schema": "run-manifest/1", "created": "2026-11-01T09:00:00-05:00", "script": "train.py", "argv": ["..."], "cwd": "/abs",
 "git_commit": "<40 hex>", "git_dirty": false, "dirty_diff_hash": null, "code_sha256": {"train.py": "<sha256>"},
 "config_sha256": "<sha256 of config.json>", "dataset_files": {"data/datasets/sdr_v2/train.json": "<sha256>"},
 "model": "llama-8b-instruct", "model_revision": "<snapshot dir name>", "seed": 42,
 "software": {"python": "3.12.x", "torch": "...", "transformers": "...", "nnsight": "..."},
 "host": "...", "slurm_job_id": null, "direction": null,
 "grader": null, "manifest_hash": "<sha256 of canonical JSON without manifest_hash>"}
```

Field names reuse `scripts/sdr_routing_pilot.py:392-403`. `grader` is null unless benchmark evals ran; then it is
`{"grader_sha256": ..., "files": {path: sha256}, "judge_spec": {benchmark: spec}}` (§6.3). `direction` comes from
the environment variable `RESEARCH_DIRECTION` when set. If git is unavailable the writer records
`git_fingerprint_error` instead of failing, as the pilot writer does.

### 4.7 Hand-back template

Every agent writes `<dir>/reports/<NN>-handback.md` with these headings, in order: `What changed` (absolute paths),
`How verified` (each command in a code block, then the observed output or its key lines), `Execution evidence`
(required for any claim about a run: job id and cluster, exit code or Slurm state, row counts observed against
expected, one baseline-reproduces assertion with both numbers, and the provenance file path with its commit),
`What is NOT done`, and `Open questions`. The words confirmed, refuted, verified and replicated may only describe a
result whose execution-evidence block is complete. The template file is `_templates/handback.md`.

### 4.8 worklog.json and the WORKLOG layout (R33)

```json
{"schema": 1, "title": "Plain session title", "state": "Running", "right_now": "Three lines at most.",
 "directions": [{"name": "Plain name", "state": "active"}], "terms": [{"term": "U5", "meaning": "..."}],
 "budgets": {"gpu": "6.5 of 20 GPU-h actual", "openrouter": "$1.84 of $10"}, "transcripts": "Claude session ...",
 "needs": [{"id": "N1", "at": "...", "text": "...", "default": "If no answer: ...", "answer": null, "answered_at": null}],
 "findings": [{"id": "F1", "at": "...", "plain": "...", "setup": "...", "strength": "reviewed", "evidence": "..."}],
 "incidents": [{"id": "P1", "at": "...", "what": "...", "effect": "...", "fix": "..."}]}
```

Everything above `## Log` is regenerated from `worklog.json`, `state.json` and `ledger.json` on every RS write, row
for row as in `_templates/WORKLOG.md` (two weekly usage rows, all models and Fable). The Log is append-only. A
resolved need is rendered struck through with its answer and time; it is never deleted. Times use
`%-I:%M %p %Z` in America/New_York with `am` and `pm` in lower case; day headings are `### <Weekday> <D> <Month> <YYYY>`.

## 5. Harness

### 5.1 Hook set

Every hook command is one literal shell guard with no variables (R26), shown here for the PreToolUse hook:

```
sh -c 'test -f /projects/beto/swong2/Alignment/.agents/research_session/cli.py && ! test -e /u/swong2/.claude/research-session/DISABLED && exec /sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/.agents/research_session/cli.py hook pre-tool-use --tool claude || exit 0'
```

A missing CLI or the kill switch therefore gives exit 0 and no output, never the exit 2 that would block every tool.
`-B` keeps `__pycache__` out of A. The script itself also no-ops when the realpath of `cwd` is outside `A`.
Timeouts are 10 s, 20 s for the gate. A timed-out hook fails open, so the pilot times the gate on Lustre.

| # | Event | Matcher | Tools | Behaviour |
|---|---|---|---|---|
| H-a | SessionStart | `startup\|resume` | both | Create or load the session file, resolve the direction (R5), inject at most 600 characters: session tag, direction, freeze state, usage reading, and the register command if unregistered. |
| H-b | SessionStart | `compact` | both | Increment `compactions` (the only place that counts). Inject the RESUME and WORKLOG paths, the lint result for both, and "Write a 'Resumed after compaction #N' worklog entry; do not restart finished work." |
| H-c | PostCompact | `manual\|auto` | Claude | Write `compact_summary` to `<dir>/handbacks/compaction-<N>.md`. Never block, never count. Codex: not installed. |
| H-d | PreToolUse | `Agent\|Bash\|SendMessage\|Write\|Edit` | both | The usage gate (§5.2). For Write and Edit it also runs the glue lint (scoped paths) and the secret scan (every path under A) on `tool_input.content` or `tool_input.new_string`, and denies with the failing units in at most 400 characters (R30). Codex: `spawn_agent` matches `Agent`; `apply_patch` matches `Write` and `Edit` once ticket 06 verifies its input shape, else the gap is documented. |
| H-e | PostToolUse | `Agent` | both | `additionalContext` with the reading, session points, next checkpoint and the Fable-gap notice (§5.4). |
| H-f | PostToolUse | `Write\|Edit` (Claude), `apply_patch` (Codex, if verified) | both | Advice only: after an Edit, lint the whole resulting file and report problems outside the edited text as `additionalContext`. It cannot undo a write and never claims to block. |
| H-g | UserPromptSubmit | none | both | Ack a pending checkpoint only when the prompt text starts with "continue" (case-insensitive, after whitespace) and contains none of `<teammate-message`, `<agent-message`, `<cross-session-message`, `<task-notification`; a prompt starting with `<` never acks (R36). Otherwise, while frozen, inject "Freeze holds; answer questions only." |
| H-h | SubagentStart | none | both | Inject the hand-back path convention, the no-git rule, and the agent brief path if the direction has one. Record the start time. |
| H-i | SubagentStop | none | both | Save `last_assistant_message` to `<dir>/handbacks/<agent_type>-<agent_id>.md`. If no `*handback*.md` under `<dir>` changed since the agent started, block once (guarded by `stop_hook_active` and `stop_blocks`). Skip `Explore`, `Plan`, `claude-code-guide`, `statusline-setup`. Codex output is always JSON. |
| H-j | Stop | none | both | If a freeze is `crossed` and not `recorded`, add a reminder as `additionalContext`. Silent when `stop_hook_active` is true or `background_tasks` or `session_crons` is non-empty. Never block. |

Placement (R4, R26): Claude hooks go into `A/.claude/settings.json` (staged JSON merge) and into a new tracked
`DC/.claude/settings.json`, staged as `F/staged/dc-claude-settings.json` and copied into W by the orchestrator only in
wave H. Codex hooks go into `~/.codex/hooks.json` (staged), next to the bridge hook, which the bridge preserves.
User-level Claude settings carry only `env`, `statusLine.refreshInterval`, `cleanupPeriodDays`, `autoMode`,
`enabledPlugins`, `skillOverrides`, `deniedMcpServers` and `permissions.deny`.

### 5.2 Usage gate and the FREEZE checkpoint

Reading (Claude): `w = max(seven_day, Fable model_scoped row)` and `h = five_hour` from `/u/swong2/.claude/usage.json`.
A missing weekly key reads as 0 only when the file is fresh. A missing `five_hour` key means the five-hour limit is
not applicable (R40: Anthropic removed it from this account on 2026-10-31); the cap row below then uses `w` alone.
Freshness: `timestamp` for `five_hour` and `seven_day`,
`model_scoped_fetched_at` for the Fable row. A reading older than 15 minutes is first refreshed by RS itself (R8):
it fetches the OAuth usage endpoint with the status line's cache and lock, then merges the result into `usage.json`.
The reading is unknown only when that refresh also fails. Reading (Codex): run
`/u/swong2/.local/bin/codex-usage`, cache the JSON for 120 s in the session file; exit 1 or `status: unknown` means
unknown.

Segments: if `resets_at` changed or `w` fell below the open segment's `last`, close the segment and open a new one
with `baseline = w`. `session_points = Σ(last − baseline)`. In a registered session checkpoint N crosses when
`session_points − points_at_register ≥ N × cadence` (cadence 16 Claude, 25 Codex, overridable by the human only).

Decisions, evaluated in this order for each PreToolUse call:

1. **Self-ack guard.** Deny any Bash command that contains `usage-ack`, `set-cadence`, `research-session/sessions`
   or the `DISABLED` kill-switch path. Deny a Bash command naming a direction `state.json` or `worklog.json` unless
   it is a read-only RS subcommand (`validate`, `status`, `usage-check`, `lint`, `findings-check`, `audit-scan`) with
   no `>` redirection. Deny any Write or Edit under `/u/swong2/.claude/research-session/` or on
   `docs/research/<slug>/state.json` or `worklog.json`; `docs/research/_templates/` is exempt. Only humans acknowledge
   (R7, R37).
2. **Cap pause.** If `w ≥ 80`, or `h` is present and `h ≥ 80`: deny Agent and any Bash containing `sbatch`. The pause lifts by itself
   when a fresh reading falls below 80, for example after the window reset.
3. **Unknown reading.** If the reading is still unknown after the refresh: deny Agent and `sbatch` with a message
   naming the stale file, its age, the refresh error and the human override `! research-session usage-ack --stale-ok 30`.
4. **Unregistered session.** No `register` entry (a cwd match does not count): allow, skipping steps 5 and 6 (R5).
   `register` stores the current total as `points_at_register`, so registering late never freezes at once.
5. **Freeze, stage `crossed`.** When checkpoint N has crossed and N > `acked_through`: deny Agent and `sbatch`.
   SendMessage stays allowed so the orchestrator can tell workers to hold.
6. **Freeze, stage `recorded`.** After `worklog-append --checkpoint N` writes the block: additionally deny
   SendMessage from the orchestrator (no `agent_id` in the hook input) to any recipient other than `main`, unless the
   message starts with `HOLD` (R6). SendMessage from a subagent is never denied. Codex: spawns and `sbatch` only (R32).
7. Everything else is allowed by the gate, so the orchestrator can finish the atomic step in flight, write the block
   and answer the user. Running Slurm jobs and running agents are never cancelled.

What the protocol requires at a freeze (R35): the orchestrator finishes the atomic step in flight, writes the
checkpoint block with `worklog-append --checkpoint N`, sends `HOLD` to every running worker, and ends its turn. It
does not poll for the human and starts no new work until the acknowledgement. A worker that receives `HOLD` finishes
its current atomic step, writes its hand-back, and stops.

A denial uses `permissionDecision: "deny"` with a reason of at most 400 characters naming the next action. If the
gate raises, it denies Agent and `sbatch` with "gate error" and allows everything else.

Acknowledgement: H-g or the human's `! research-session usage-ack` sets `acked_through = N`, `acked_at` and `acked_by`
and clears the freeze; a user question does not. Without `--session` it acks the most recent session whose `cwd`
equals the current directory and prints which.

**5.3 State ownership.** RS is the only writer of the session files, `state.json`, `worklog.json`, `WORKLOG.md`,
`ledger.json`, `DIRECTIONS.md`, `SESSIONS.md` and the global ledger. The orchestrator changes them through RS only;
the gate enforces this for the session files, `state.json` and `worklog.json` (§5.2 step 1).

**5.4 The Fable-close rule (D8).** Each reading computes `fable_gap = Fable row − seven_day`. Above 5 points, H-a,
H-e and every checkpoint block say "Fable is N points above all-models: delegate reading, analysis and review to Opus
agents." Advisory in hooks, mandatory in the protocol (ticket 08); checkpoints use `max(all-models, Fable)`.

### 5.5 Lint rule (lane 4 §0 numbers)

- **Scope.** Glue lint runs on files named `WORKLOG.md`, `RESUME.md`, `START.md`, `SESSIONS.md`, `FINDINGS.md`,
  `README.md` under `docs/research/`, and every `*.md` under `A/.agents/memory/`. The secret scan runs on every file
  written under `A`. Both run before the write, in H-d (R30).
- **Units and tokens.** A unit is a maximal run of non-blank lines; each list item, table row and heading is its own
  unit; fenced code, HTML comments, YAML frontmatter and table separators are skipped. Tokens are whitespace-split
  after removing inline code, link targets and URLs, with punctuation stripped and tokens containing `/`, `\`, `@`
  or `=` dropped. **Long-token rule:** in a unit of at least 8 tokens, fail when over 15% have 20 or more characters.
- **Join rule.** Fail when a unit has more than 3 tokens matching `[A-Za-z]{3,}[0-9]` or `[0-9][A-Za-z]{3,}`, after
  removing tokens in the allowlist (`sha1`, `sha256`, `sha512`, `eval5`, `int8`, `uint8`, `float16`, `float32`,
  `bfloat16`, `utf8`, `base64`, `python3`, plus Slurm partition names such as `gpuA100x4`). The allowlist may grow;
  the thresholds may not change without a ruling.
- **Secrets.** Fail on `ghp_` or `gh[osur]_` plus 36 alphanumerics, `github_pat_`, `sk-ant-`, `sk-or-v1-`, `sk-` plus
  32 or more alphanumerics, `AKIA` plus 16, `hf_` plus 30 or more, `xox[baprs]-`, and private-key headers.
- **Output.** `lint <file>...` prints `path:line: rule: excerpt` per failing unit and exits 1 on any failure. After
  two failures on the same entry, regenerate it from its fields with `worklog-append`; never hand-patch it.

### 5.6 RS command surface (binding names)

`research-session` subcommands: `hook <event>`, `register <slug> [--session ID]` (default: the most recent session
whose cwd matches), `status`, `usage-check` (refreshes a stale reading, R8), `usage-ack [--session ID]
[--stale-ok MIN]`, `set-cadence <points>` (human only), `lint <file>...`, `validate <path>...`, `render`
(DIRECTIONS.md and SESSIONS.md), `ledger-rollup`, `claim <slug>`, `release <slug> --status <status>`,
`job add|update|list`, `findings-check [--paper DRAFT]`, `audit-scan <transcript.jsonl>`, and these. Tickets 02, 03
and 11 implement them; ticket 08 documents them.
- `worklog-append <dir> --kind <entry|checkpoint|handback|job|compaction|decision|incident|switch|finding|need|need-resolved>`
  with `--title --body` for log entries, `--checkpoint N` for the checkpoint block, `--plain --setup --strength
  --evidence` for `finding` (next F#), `--text --default` for `need` (next N#), `--id N# --answer` for
  `need-resolved`, and `--what --effect --fix` for `incident` (next P#, also logged) (R33).
- `init <slug> [--from-start START.md] [--gpu-cap H] [--max-gpu-jobs K] [--api-cap USD]` creates `<root>/<slug>/`
  from `_templates/`: `state.json`, `worklog.json`, `ledger.json`, a rendered `WORKLOG.md`, `RESUME.md`, a `README.md`
  stub and `START.md` (the given file, else the template). It adds a `proposed` row to `directions.json` when the
  slug is absent and never overwrites an existing file (R39).
- `ledger add <dir> --cluster --account --partition --gpus --minutes --job-id [--commit]` (refuses a reservation past
  `caps`), `ledger reconcile <dir> <job-id> --actual-seconds S --status STATUS` and `ledger api <dir> --usd X
  [--provider P] [--calls N] [--reserve]` are the only commands that record spend; each recomputes `totals` (R39).
- `worklog-set <dir> <field> <value>` for `title`, `state`, `right-now`, `directions`, `terms`, `transcripts`,
  `gpu-cap`, `max-gpu-jobs` and `api-cap`. Caps go to `ledger.json` and the head's budget rows are rendered from it;
  a freeze or cap pause overrides the State row's set value in the render (R39).

### 5.7 Profiles (D6)

| Item | Default (user-level) | research | synthesis | writing | audit |
|---|---|---|---|---|---|
| superpowers, mattpocock-skills, code-review, github, claude-md-management | on | on | on | on | on |
| nnsight | off | on | off | off | off |
| academic-research-skills, academic-writing-agents | off | off | off | on | off |
| session-report (to install) | off | off | off | off | on |
| context7, skill-creator, claude-code-setup, cc-plugin-you-should-know, karpathy | off | off | off | off | off |
| shinka-* and weco user skills (via `skillOverrides`) | off | off | off | off | off |
| jcodemunch MCP | off (`deniedMcpServers`, fallback `permissions.deny`) | off | off | off | off |

Claude launches a profile with `claude --settings ~/.claude/profiles/<name>.json`. Codex uses `[profiles.<name>]` only
if ticket 07 verifies per-profile skill and MCP keys in the Codex docs or `--help`; otherwise Codex gets the lean
default through the bridge and the Codex writing profile is reported as not available.

## 6. Science guards

**6.1 Provenance.** `run_io.make_run_dir` and the evaluate_circuit cell writer emit `run_manifest.json` (§4.6). They
never overwrite an existing `run_manifest.json` with different content; they write `run_manifest.<n>.json` instead
and say so. Tests mock the git call. Library code may call `git rev-parse` at run time; agents never run git.

**6.2 Number-resolution checker.** `DC/scripts/check_report_numbers.py <report.md> [--strict] [--json]` lists every
number in prose and tables, except dates, times, section, ruling and ticket numbers, finding ids, component ids such
as `L17H24`, versions, `file:line` references and code. A number resolves when its unit, or its table's heading
paragraph, cites an existing file containing it: as a JSON or CSV numeric leaf within half a unit of its last
displayed digit (a percentage also matches the fraction), or as a literal in text files. A unit containing "derived"
lists its numbers as derived. `--strict` exits 1 on any unresolved number.

**6.3 Grader freeze.** `evaluation/grader_hash.py` computes `grader_sha256` over the sorted `(relative path, sha256)`
pairs of `evaluation/benchmarks/*.py` and `evaluation/benchmark_eval.py`. A direction records its frozen value in its
`spec.md` and in `directions.json` (`frozen_grader_sha256`) before its first benchmark run. `findings-check` errors on
a row whose evidence provenance names a different grader hash.

**6.4 Held-out set policy.** `held-out.md`: sessions never score held-out ids; a paper-gating run's provenance path
in `scored_runs` spends the set for that claim. The audit checks provenance `dataset_files` against `held_out.json`:
`{"schema": 1, "sets": [{"id", "task", "path", "sha256", "n", "created", "created_by", "purpose", "scored_runs": []}]}`.

**6.5 Seed-replication gate.** `research-session findings-check` errors when a `replicated` row lacks two provenance
files with distinct seeds, when a `verified` row lacks a commit-naming provenance file, and, with `--paper <draft.md>`,
when the draft cites any F-id whose status is not `replicated`.

## 7. Staging and apply (constraint 3)

Agents never write in place to `A`, to `~/.claude`, `~/.codex` or `~/.local/bin`. They write full files under
`S/tree/<absolute destination without the leading slash>` and an op list `S/ops/<NN>-<slug>.json`:

```json
{"ticket": "01", "ops": [
 {"op": "write", "dest": "/abs/path", "src": "tree/abs/path", "expect_sha256": "<sha256 or absent>", "lint": true, "wave": "A"},
 {"op": "json_merge", "dest": "/abs/settings.json", "fragment": {}, "wave": "H"},
 {"op": "replace_text", "dest": "/abs/MEMORY.md", "old_text": "exact line", "new_text": "new line", "lint": true, "wave": "A"},
 {"op": "append_text", "dest": "/abs/MEMORY.md", "text": "- [Title](file.md) — hook\n", "lint": true, "wave": "A"},
 {"op": "text_block", "dest": "/abs/file", "marker": "autoresearch-workflow", "text": "...", "position": "before_first_table", "wave": "C"},
 {"op": "move", "src": "/abs/a", "dest": "/abs/b", "wave": "B"},
 {"op": "symlink", "path": "/abs/link", "target": "/abs/target", "wave": "B"},
 {"op": "mkdir", "path": "/abs/dir", "wave": "B"}]}
```

The apply tool `F/tools/apply_staged.py` (stdlib only, both interpreters) reads every op file in ticket order and
supports `--dry-run`, `--wave A|H|B|C|D`, `--only NN`, `--allow codex-config`, `--lint-cmd` and `--rollback
<journal>`. It is idempotent: an op whose target already has the desired content is skipped and reported. Before
changing a target it copies it to `/u/swong2/.claude/research-session/backups/<timestamp>/<abs path>` and journals the
op there. `json_merge` deep-merges dicts and only extends lists, skipping an entry with equal canonical JSON (hook
groups also compare by command string); it never replaces or removes one (R31). A `write` with `expect_sha256`
refuses and reports a conflict when the file differs; whole-file memory writes always carry it. `replace_text` needs
`old_text` exactly once and `append_text` skips text already present, so line edits to `MEMORY.md` survive concurrent
edits elsewhere. `lint: true` lints the resulting file first through `--lint-cmd` (default: base python3.9 on the
staged `research_session/cli.py lint`, else the installed one). `text_block` inserts or replaces a `# BEGIN <marker>`
and `# END <marker>` block; in TOML, `before_first_table` puts it before the first `[table]`. Ops on
`~/.codex/config.toml` need `--allow codex-config`. Each op prints a diff summary; no value under `env` is printed.

Waves, applied in this order (R26, R28):

- **A**: RS code and tests, docs, templates, memory, user settings without hooks. Applied after review; no merge.
- **H**: every hook installation (the `A/.claude/settings.json` and `~/.codex/hooks.json` merges, and the copy of
  `F/staged/dc-claude-settings.json` to `W/.claude/settings.json`), only after wave A, after the RS tests pass from the
  installed path in both envs, and after the hook smoke test of ticket 06 passes.
- **B**: needs the DC branch merged to main (the migrations R28 allows and the `.scratch/autoresearch-workflow` link).
- **C**: needs the user's go because Codex must restart (`~/.codex/config.toml`).
- **D**: needs the user's confirmation that the live Codex session is finished (the memory rewrites of R28, staged
  but not applied; the deferred migrations run from ticket 10's command at the same time).

## 8. Acceptance per phase

- **P0 (01).** Lint passes the clean corpus and fails all three glued samples; staged memory edits pass it; the wave A
  dry-run lists only planned targets; settings keep every `autoMode.environment` entry; Codex TOML parses on mgnp.
- **P1 (05, 09, 10).** `validate` passes on FINDINGS, directions and ledgers; renders are byte-stable; every
  `.scratch/...` string in DC code resolves and the named tests match before and after; INDEX, FINDINGS and SESSIONS
  together are under 30k tokens (bytes divided by 4).
- **P2 (02, 03, 06).** RS tests pass on both interpreters; every hook has a recorded-input fixture asserting exact
  output; the §5.2 decision table has one test per row; the hook smoke test passes before wave H.
- **P3 (07, 08).** Docs and templates pass the lint; every command they name is in `--help`; profiles parse.
- **P4 (04).** New tests pass in both envs; no new DC failure names; the checker's counts on `synthesis.md` reported.
- **P5 (11, 12).** The checklist exercises every hook with a named command or UI step and an expected observation.

## 9. Rulings

Planner rulings under the user's go of 2026-10-31. R26-R38 are orchestrator rulings on the plan review
(`reports/00-plan-review.md`) and the open questions (`reports/00-orchestrator-rulings.md`); they override earlier text.

- **R1. RS lives at `A/.agents/research_session/`, staged by agents, applied by the orchestrator.** The path is the
  same before and after the DC merge and from every worktree, so hook commands never change. It sits beside
  `codex_usage.py` and the bridge, whose tests already run on both interpreters. A human wrapper
  `~/.local/bin/research-session` follows the `codex-usage` precedent. The science guards (§6.1-6.3) live in DC.
- **R2. The provenance file is `run_manifest.json`.** `manifest.json` already names frozen input manifests in
  `evaluate_native_sparse.py:334,459`, `evaluation/generation_checkpoint.py:118` and the SDR scripts. Field names are
  reused where they exist. `findings-check` accepts a legacy `manifest.json` naming `git_commit`, with a warning.
- **R3. Migration archives whole `.scratch` directories byte for byte and copies their Markdown.** Each migrated
  directory is renamed on the same filesystem to `DC/outputs/_studies/<slug>/scratch/` and replaced by a symlink, as
  selective-deception was. Every `.scratch/...` path used by code, tests and receipts keeps resolving. The copy rule
  is R34. The migration is a script with sha256 before and after; the implementer never reads the directories.
  Which directories may move, and when, is R28. Any directory with a file modified in the last 12 hours is skipped.
- **R4. Hook placement.** Claude hooks live in the project settings of both repos, so they never fire in the user's
  other repositories. Codex hooks stay in the user-level `~/.codex/hooks.json`, confined by the script's cwd check.
  Codex also loads `<repo>/.codex/hooks.json` when the project layer is trusted; ticket 06 verifies whether that
  layer loads for A and for DC (whose `.codex/` holds bridge symlinks) and reports which placement is better (R32).
- **R5. Session to direction mapping.** Counters live in a private local session file keyed by tool and session id.
  The direction comes from `register <slug>`, else from a cwd match in DC main's `directions.json` (attribution only).
  Only a registered session gets the FREEZE; any other gets only the cap and stale gates, because the hooks fire in
  every A or DC session and a quick question session must not freeze (orchestrator addendum).
- **R6. FREEZE is two-stage.** Stage `crossed` denies Agent and `sbatch`, so hold messages can still go out; stage
  `recorded` adds the SendMessage denial, with `HOLD` messages and subagent messages always allowed.
- **R7. Acknowledgement is human-only.** The gate denies model-issued commands and edits that could ack or edit
  counters. `!` commands typed by the user do not pass through PreToolUse (the pilot confirms this).
- **R8. Stale readings are refreshed by RS (OQ2; supersedes the planner's "never fetch").** When `usage.json` is
  older than 15 minutes, RS fetches `https://api.anthropic.com/api/oauth/usage` itself (8 s bound) with the status
  line's cache, lock and 300 s retry floor (paths in ticket 02). The token is read inside the process from
  `~/.claude/.credentials.json` and never printed, logged or put on a command line. RS merges the rows into
  `usage.json` atomically, keeps every key and sets the freshness stamps. If the refresh fails the reading is unknown
  and the human `usage-ack --stale-ok <minutes>` (at most 60) overrides. RS never calls `statusline.sh`.
- **R9. Usage targets.** Five-hour and weekly caps are 80% (D7). Memory note `usage-limit-policy` moves from 75% to
  80% and records that the weekly reading is `max(seven_day, Fable row)`.
- **R10. Lint thresholds are fixed as in §5.5.** Ticket 01 may only extend the allowlist and must report each case.
- **R11. Codex worker model.** `[agents] default_subagent_model = "gpt-6.1-sol"` is a wave C block before the first
  TOML table. The bridge sentence about inheriting the parent's model changes only if the bridge tests pass staged.
- **R12. Codex names are verified, not assumed.** Ticket 06 records each Codex event and tool name with its doc URL.
  Unverified matchers are not installed.
- **R13. The two large memory logs move verbatim.** Their bodies are copied unchanged to
  `DC/outputs/_studies/<slug>/memory-log-20261031.md` (ignored, never pushed) and the notes become pointers of at most
  15 lines. These ops are wave D (R28).
- **R14. Archived glued files are not rewritten.** Ticket 09 writes a readable copy of `sdr-clause-choice/RESUME.md` to
  `docs/research/sdr-mechanism/history/`.
- **R15. Direction granularity.** One registry row per direction; the `sdr-*` study directories are `legacy_scratch`
  and `archive` entries of the `sdr-mechanism` row.
- **R16. Old evidence.** A seeded FINDINGS row without provenance gets `commit = pre-manifest` and at most `reviewed`.
- **R17. Status vocabulary.** `verified` and `replicated` are separate; paper headlines require `replicated`.
- **R18. Staging is per ticket.** Each ticket writes its own op file. Two tickets reach the same destination only through
  `json_merge`, `replace_text`, `append_text` or distinct `text_block` markers; `MEMORY.md` changes only through the
  two text ops. The staged `cli.py` is the one shared staged file: tickets 01, 02, 03, 06 and 11 extend it in that
  order, never in parallel, and each starts from the latest staged copy (R38).
- **R19. Held-out guard.** Policy and registry only; the scoring guard is a `proposed` direction added by ticket 12.
- **R20. Sizing.** Reading plus writing under about 250k tokens per ticket; briefs finish under 350k until the 600k
  window test passes. Ticket 01 hands back after the lint and the apply tool if its projection passes 250k.
- **R21. Gitignore in DC.** Ticket 06 adds `.claude/worktrees/` and `.claude/settings.local.json` to `W/.gitignore`.
- **R22. Times.** America/New_York with a computed zone; EDT becomes EST on 1 November 2026.
- **R23. Claims.** Only the orchestrator edits `directions.json` claims (through `claim`) and commits them on DC main
  before branching. Pushing follows the user's standing policy.
- **R24. Agent definitions move from Sonnet to Opus.** `idea-critic`, `paper-reader` and `paper-searcher` get
  `model: opus`; `env.CLAUDE_CODE_SUBAGENT_MODEL = "opus"` covers spawns without a model.
- **R25. The execution-evidence block** is in `_templates/handback.md` and in `A/.claude/agents/ticket-implementer.md`.
- **R26. Install order (review blocker 1).** Every hook command is the literal shell guard of §5.1, which exits 0 when
  the CLI is missing or the kill switch exists. DC's hook settings are staged in `F/staged/dc-claude-settings.json`,
  never written to `W/.claude/settings.json` by an agent. All hook installation is wave H (§7).
- **R27. Fetch mechanics (blocker 2).** Ticket 02 implements R8 with a mocked credentials reader and a mocked HTTP
  endpoint. No test and no implementer opens the real credentials file or uses a real token.
- **R28. Live-session protection (blocker 3, OQ3).** Waves A and B never touch `A/.scratch/sdr-*` (including
  `sdr-session-wrapup`), `selective-deception` or `eval5-grader-fixes`, nor the memory notes
  `sdr-mechanism-review.md` and `selective-deception-execution.md` or their `MEMORY.md` lines (27 and 29). Ticket 10
  gives the one-line command that migrates those directories later; ticket 12 stages the memory ops as wave D. Both
  wait for the user's confirmation that the Codex session is finished. The 12-hour mtime skip is a second guard.
- **R29. Claim tag (blocker 4, refines OQ1).** `claimed_by` and the `state.json` session key are
  `<tool>-<first 8 characters of the session id>`; this session is `claude-b2cb53cd`.
- **R30. The lint refuses before the write (blocker 5).** H-d lints and scans Write `content` and Edit `new_string`
  and denies with the failing units. H-f only advises. Codex uses `apply_patch` in PreToolUse if ticket 06 verifies
  its input shape; otherwise the gap is documented and the Codex protocol says to run `lint` after every write.
- **R31. `json_merge` only extends (blocker 6, OQ8).** No `replace_paths`; identical list entries are never
  duplicated. `autoMode.environment` keeps every existing entry and gains the Alignment and DC entries.
- **R32. Codex freeze scope.** Codex documents no message tool, so a Codex freeze denies spawns and `sbatch` only.
- **R33. Worklog structure (blocker 7).** The kinds of §5.6 cover findings, needs, resolved needs and incidents.
  Everything above `## Log` is regenerated from `worklog.json` (§4.8) and `state.json`; only the Log is append-only.
- **R34. Markdown copy and the autoresearch-workflow exception (blocker 9).** The curated copy is every `*.md` at any
  depth (including `reports/`, `reviews/`, `handbacks/`), at most 200 KB per file and 1.5 MB per directory, with
  `provenance.json` and a report of what the caps excluded, all behind the secret scan. `.scratch/autoresearch-workflow`
  holds only stale copies of files whose canonical copy is in this feature directory: it moves to the backup root
  and its symlink points at `DC/docs/research/autoresearch-workflow` (wave B).
- **R35. Turn end at a freeze (blocker 8).** The protocol text of §5.2 binds ticket 08 and the agent brief.
- **R36. Envelope rejection.** H-g never acks a prompt that starts with `<` or contains a teammate, agent,
  cross-session or task-notification envelope. Ticket 06 checks the UserPromptSubmit payload for a source field.
- **R37. Guard scope.** The self-ack guard exempts `_templates/` and read-only RS subcommands (§5.2 step 1).
- **R38. Ordering of dependent tickets.** Ticket 11 is blocked by 10 as well, because 05, 10, 11 and 12 all edit
  `directions.json` in that order.
- **R39. Setup, spend and head fields are RS commands (ticket 08 hand-back).** `init`, `ledger` and `worklog-set`
  (§5.6) are ticket 03 scope, so no RS-owned file is ever created or edited by hand; `job add` does not write ledgers.
