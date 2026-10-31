# Spec: autoresearch workflow setup (binding)

Date: 2026-10-31. Status: binding for tickets 01-12. Source design: `reports/proposal-full.md` (approved by the user
on 2026-10-31 with decisions D1-D8). Evidence for every repo fact used here is in `reports/00-plan-handback.md`.
Where this spec and the proposal differ, this spec wins and the difference is a numbered ruling in §9.

Short names used below:

- **F** is the feature directory `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow`.
- **W** is the worktree root `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow`.
- **S** is the staging root `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging`.
- **A** is the Alignment checkout `/projects/beto/swong2/Alignment`; **DC** is the main Deception-Circuit checkout `A/Deception-Circuit`.
- **RS** is the research-session package, installed at `A/.agents/research_session/` (R1).

## 1. Intent

Research sessions in this project run for days with a Fable orchestrator and Opus or Sol workers. Today the state of
the research lives in prose spread over memory, `.scratch`, two report folders and three handoffs, and every safety
rule (checkpoints, compaction counts, model choice, provenance) depends on the orchestrator remembering it. This
feature makes the state indexable and makes the rules enforced by the harness. It adds one index of findings and
directions, a small CLI that owns counters and usage readings, hooks in both tools that call the CLI, lean plugin
profiles, written protocols for research, synthesis and audit sessions, and provenance guards in the experiment code.

## 2. Goals and non-goals

Goals:

1. A fresh synthesis agent orients from `INDEX.md`, `FINDINGS.md` and `SESSIONS.md` in under 30k tokens.
2. Checkpoints, cap pauses, compaction counts and hand-back capture are enforced by hooks in Claude and Codex.
3. Subagent model defaults are pinned (Opus in Claude, Sol in Codex) as a safety net.
4. Human worklogs and machine state are separate, and every write to them is linted for glued text and secrets.
5. New runs carry a commit-stamped provenance file; verdict wording requires execution evidence; paper claims require
   seed replication and a frozen grader.
6. The paused and closed `.scratch` directions are archived without changing a byte, and their text is indexed.

Non-goals:

- No GPU jobs and no paid API calls. The pilot (ticket 11) only describes what the user launches.
- No backfill of provenance for old runs. Old evidence is marked `pre-manifest` (R16).
- No code guard that refuses to score held-out instances. This feature ships the policy and the registry only (R19).
- No change to any frozen archive, receipt or hash-pinned file. No rewrite of historical manifests.
- No rewrite of the Claude-Codex bridge beyond one instruction sentence (R11).

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
    WORKLOG.md        human log; orchestrator is the only writer; template in _templates
    RESUME.md         machine narrative state; overwritten; 150 lines at most
    state.json        counters, usage segments, checkpoints, jobs (§4.5); written only by RS
    ledger.json       reservations and spend (§4.4)
    reports/ reviews/ handbacks/ history/ issues/
DC/outputs/<run>/run_manifest.json   written by run_io.make_run_dir and by evaluate_circuit cells (§4.6, R2)
DC/outputs/_studies/<slug>/scratch/  byte-identical archive of a migrated .scratch directory (R3)
A/.scratch/<slug> -> DC/outputs/_studies/<slug>/scratch   symlink, same as the selective-deception precedent
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
- `claimed_by` is `<tool>-<session tag>` where tool is `claude` or `codex` and the tag is the first 8 characters of
  the session id. A synthesis session may only add `proposed` rows.
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

`status` in a reservation is one of `PLANNED`, `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `TIMEOUT`,
`OUT_OF_MEMORY`. `converted_from` names the legacy ledger a converted file came from. The global
`docs/research/ledger.json` is `{"schema": 1, "generated": ..., "directions": {id: totals}, "totals": {...}}` and is
rendered by `research-session ledger-rollup`.

### 4.5 state.json (per direction, tracked) and the local session file

The local session file `/u/swong2/.claude/research-session/sessions/<tool>-<session_id>.json` is authoritative for
gate decisions (R5). Every RS write to it is mirrored into the registered direction's `state.json` under
`sessions.<tool>-<tag>`. Models never edit either file (§5.3).

```json
{"schema": 1, "direction": "pilot-hooks", "session_state": "running", "last_worklog_entry_at": "2026-11-02T10:05:00-06:00",
 "sessions": {"claude-01a2b3c4": {
   "tool": "claude", "session_id": "...", "cwd": "/abs/worktree", "started_at": "...", "orchestrator_model": "claude-fable-5-1",
   "compactions": 2, "compaction_log": [{"n": 1, "at": "...", "trigger": "auto"}],
   "usage": {"metric": "max(seven_day, Fable)", "cadence": 16, "segments": [{"resets_at": 1793797200, "baseline": 11, "last": 27}],
     "session_points": 16, "next_checkpoint": 1, "acked_through": 0,
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

## 5. Harness

### 5.1 Hook set

Every hook runs `/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/.agents/research_session/cli.py hook <event> --tool <claude|codex>`.
The script no-ops (exit 0, no output) when the realpath of `cwd` is outside `A`, or when the file
`/u/swong2/.claude/research-session/DISABLED` exists (the human kill switch). Timeouts are 10 s, 20 s for the gate.

| # | Event | Matcher | Tools | Behaviour |
|---|---|---|---|---|
| H-a | SessionStart | `startup\|resume` | both | Create or load the session file, resolve the direction (R5), inject at most 600 characters: session tag, direction, freeze state, usage reading, and the register command if unregistered. |
| H-b | SessionStart | `compact` | both | Increment `compactions` (the only place that counts). Inject the RESUME and WORKLOG paths, the lint result for both, and "Write a 'Resumed after compaction #N' worklog entry; do not restart finished work." |
| H-c | PostCompact | `manual\|auto` | Claude | Write `compact_summary` to `<dir>/handbacks/compaction-<N>.md`. Never block, never count. Codex: not installed. |
| H-d | PreToolUse | `Agent\|Bash\|SendMessage\|Write\|Edit` | both | The usage gate (§5.2); Write and Edit are matched only for the self-ack guard. Codex tool names are verified in ticket 06 (R12). |
| H-e | PostToolUse | `Agent` | both | `additionalContext` with the reading, session points, next checkpoint and the Fable-gap notice (§5.4). |
| H-f | PostToolUse | `Write\|Edit` (Claude), the Codex patch tool (verify) | both | Lint (§5.5) on scoped paths and secret scan on every file under `A`; on failure return `decision: "block"` with the failing units. |
| H-g | UserPromptSubmit | none | both | If a checkpoint is pending and the prompt starts with "continue" (case-insensitive, after whitespace), ack it. Otherwise, while frozen, inject "Freeze holds; answer questions only." |
| H-h | SubagentStart | none | both | Inject the hand-back path convention, the no-git rule, and the agent brief path if the direction has one. Record the start time. |
| H-i | SubagentStop | none | both | Save `last_assistant_message` to `<dir>/handbacks/<agent_type>-<agent_id>.md`. If no `*handback*.md` under `<dir>` changed since the agent started, block once (guarded by `stop_hook_active` and `stop_blocks`). Skip `Explore`, `Plan`, `claude-code-guide`, `statusline-setup`. Codex output is always JSON. |
| H-j | Stop | none | both | If a freeze is `crossed` and not `recorded`, add a reminder as `additionalContext`. Silent when `stop_hook_active` is true or background tasks exist. Never block. |

Placement (R4): Claude hooks go into `A/.claude/settings.json` (staged JSON merge) and into a new tracked
`DC/.claude/settings.json` written in W. Codex hooks go into `~/.codex/hooks.json` (staged), next to the bridge
hook, which the bridge preserves. User-level Claude settings carry only `env`, `statusLine.refreshInterval`,
`cleanupPeriodDays`, `autoMode`, `enabledPlugins`, `skillOverrides` and `permissions.deny`.

### 5.2 Usage gate and the FREEZE checkpoint

Reading (Claude): `w = max(seven_day, Fable model_scoped row)` and `h = five_hour` from `/u/swong2/.claude/usage.json`.
A missing key reads as 0 only when the file is fresh. Freshness: `timestamp` for `five_hour` and `seven_day`,
`model_scoped_fetched_at` for the Fable row; a reading older than 15 minutes is unknown (R8). Reading (Codex): run
`/u/swong2/.local/bin/codex-usage`, cache the JSON for 120 s in the session file; exit 1 or `status: unknown` means
unknown.

Segments: if `resets_at` changed or `w` fell below the open segment's `last`, close the segment and open a new one
with `baseline = w`. `session_points = Σ(last − baseline)`. Checkpoint N crosses when
`session_points ≥ N × cadence` (cadence 16 for Claude, 25 for Codex, per-session override by the human only).

Decisions, evaluated in this order for each PreToolUse call:

1. **Self-ack guard.** Deny any Bash command that contains `usage-ack`, `set-cadence`, `research-session/sessions`, the `DISABLED` kill-switch path, or a direction
   `state.json` path, and any Write or Edit whose path is under `/u/swong2/.claude/research-session/` or ends in
   `docs/research/*/state.json`. Only humans acknowledge (R7).
2. **Cap pause.** If `h ≥ 80` or `w ≥ 80`: deny Agent and any Bash containing `sbatch`. The pause lifts by itself
   when a fresh reading falls below 80, for example after the window reset.
3. **Unknown reading.** If the reading is unknown: deny Agent and `sbatch` with a message naming the stale file and
   its age, and naming the human override `! research-session usage-ack --stale-ok 30` (R8).
4. **Freeze, stage `crossed`.** When checkpoint N has crossed and N > `acked_through`: deny Agent and `sbatch`.
   SendMessage stays allowed so the orchestrator can tell workers to hold.
5. **Freeze, stage `recorded`.** After `worklog-append --checkpoint N` writes the block: additionally deny
   SendMessage from the orchestrator (no `agent_id` in the hook input) to any recipient other than `main`, unless the
   message starts with `HOLD` (R6). SendMessage from a subagent is never denied.
6. Everything else is allowed. Running Slurm jobs and running agents are never cancelled.

A denial uses `permissionDecision: "deny"` with a reason of at most 400 characters that says what to do next. If the
gate itself raises, it denies Agent and `sbatch` with "gate error" and allows everything else (fail closed for new
spend, open for the rest).

Acknowledgement: the UserPromptSubmit hook (H-g) or the human running `! research-session usage-ack` sets
`acked_through = N`, writes `acked_at` and `acked_by`, and clears the freeze. A question from the user during a
freeze does not lift it. `usage-ack` without `--session` acks the most recent session whose `cwd` equals the
current directory and prints which session it acked.

### 5.3 State ownership

RS is the only writer of the local session files, `state.json`, `ledger.json`, `DIRECTIONS.md`, `SESSIONS.md` and the
global `ledger.json`. The orchestrator changes them through RS subcommands only. Models never edit them by hand; the
gate enforces this for the session files and `state.json` (§5.2 step 1).

### 5.4 The Fable-close rule (D8)

Each reading also computes `fable_gap = Fable row − seven_day`. When it exceeds 5 points, H-a, H-e and every
checkpoint block carry "Fable is N points above all-models: delegate reading, analysis and review to Opus agents."
The worklog header always shows both rows. The rule is advisory in hooks and mandatory in the protocol (ticket 08).
Checkpoint increments use `max(all-models, Fable)`, so the gap never delays a checkpoint.

### 5.5 Lint rule (lane 4 §0 numbers)

- **Scope.** Glue lint runs on files named `WORKLOG.md`, `RESUME.md`, `START.md`, `SESSIONS.md`, `FINDINGS.md`,
  `README.md` under `docs/research/`, and every `*.md` under `A/.agents/memory/`. The secret scan runs on every file
  written under `A`.
- **Units.** A unit is a maximal run of non-blank lines, except that each list item, table row and heading is its own
  unit. Fenced code blocks, HTML comments, YAML frontmatter and table separator rows are skipped.
- **Tokens.** Remove inline code spans, link targets and bare URLs, then split on whitespace and strip surrounding
  punctuation. Tokens containing `/`, `\`, `@` or `=` are dropped.
- **Long-token rule.** In a unit with at least 8 tokens, fail when more than 15% of tokens have 20 or more characters.
- **Join rule.** Fail when a unit has more than 3 tokens matching `[A-Za-z]{3,}[0-9]` or `[0-9][A-Za-z]{3,}`, after
  removing tokens in the allowlist (`sha1`, `sha256`, `sha512`, `eval5`, `int8`, `uint8`, `float16`, `float32`,
  `bfloat16`, `utf8`, `base64`, `python3`, plus Slurm partition names such as `gpuA100x4`). The allowlist may grow;
  the thresholds may not change without a ruling.
- **Secrets.** Fail on `ghp_` or `gh[osur]_` plus 36 alphanumerics, `github_pat_`, `sk-ant-`, `sk-or-v1-`, `sk-` plus
  32 or more alphanumerics, `AKIA` plus 16, `hf_` plus 30 or more, `xox[baprs]-`, and private-key headers.
- **Output.** `research-session lint <file>...` prints one line per failing unit (`path:line: rule: excerpt`) and exits
  1 on any failure. Drift reset: after two failures on the same entry, regenerate it from its fields with
  `worklog-append`; do not hand-patch it.

### 5.6 RS command surface (binding names)

`research-session` subcommands: `hook <event>`, `register <slug> [--session ID]` (default: the most recent session
whose cwd matches), `status`, `usage-check`, `usage-ack [--session ID]
[--stale-ok MIN]`, `set-cadence <points>` (human only), `lint <file>...`, `validate <path>...`, `render`
(DIRECTIONS.md and SESSIONS.md), `ledger-rollup`, `claim <slug>`, `release <slug> --status <status>`,
`worklog-append <dir> --kind <entry|checkpoint|handback|job|compaction|decision|incident|switch> --title ... --body ...`
(and `--checkpoint N` for the checkpoint block), `job add|update|list`, `findings-check [--paper DRAFT]`,
`audit-scan <transcript.jsonl>`. Tickets 02, 03 and 11 implement them; ticket 08 documents them.

### 5.7 Profiles (D6)

| Item | Default (user-level) | research | synthesis | writing | audit |
|---|---|---|---|---|---|
| superpowers, mattpocock-skills, code-review, github, claude-md-management | on | on | on | on | on |
| nnsight | off | on | off | off | off |
| academic-research-skills, academic-writing-agents | off | off | off | on | off |
| session-report (to install) | off | off | off | off | on |
| context7, skill-creator, claude-code-setup, cc-plugin-you-should-know, karpathy | off | off | off | off | off |
| shinka-* and weco user skills (via `skillOverrides`) | off | off | off | off | off |
| jcodemunch MCP | off (key verified in ticket 07, fallback `permissions.deny`) | off | off | off | off |

Claude launches a profile with `claude --settings ~/.claude/profiles/<name>.json`. Codex profiles use
`[profiles.<name>]` in `~/.codex/config.toml` only if ticket 07 verifies per-profile skill and MCP keys against
https://learn.chatgpt.com/docs or `codex --help`. Otherwise Codex gets the lean default through the bridge, which
drops adapters for plugins disabled at user level, and the Codex writing profile is reported as not available.

## 6. Science guards

### 6.1 Provenance

`run_io.make_run_dir` and the evaluate_circuit cell writer emit `run_manifest.json` (§4.6). They never overwrite an
existing `run_manifest.json` with different content; they write `run_manifest.<n>.json` instead and say so. Tests mock
the git call. Library code may call `git rev-parse` at run time; agents still never run git (brief).

### 6.2 Number-resolution checker

`DC/scripts/check_report_numbers.py <report.md> [--strict] [--json]` lists every number in prose and tables, except
dates, times, section and ruling numbers, ticket numbers, finding ids, component ids such as `L17H24`, versions,
`file:line` references and numbers inside code. A number resolves when its unit, or the heading paragraph of its
table, cites an existing file and the number occurs in that file: as a JSON or CSV numeric leaf within half a unit of
its last displayed digit (a percentage also matches the fraction), or as a literal in text files. A unit containing the
word "derived" lists its numbers as derived. `--strict` exits 1 on any unresolved number.

### 6.3 Grader freeze

`evaluation/grader_hash.py` computes `grader_sha256` over the sorted `(relative path, sha256)` pairs of
`evaluation/benchmarks/*.py` and `evaluation/benchmark_eval.py`. A direction records its frozen value in its
`spec.md` and in `directions.json` (`frozen_grader_sha256`) before its first benchmark run. `findings-check` errors
on a row whose evidence provenance names a different grader hash.

### 6.4 Held-out set policy

`docs/research/held-out.md` states the rule: research sessions never score held-out instance ids; a paper-gating run
records its provenance path in the registry's `scored_runs`; a scored set is spent for that claim.
`docs/research/held_out.json` is `{"schema": 1, "sets": [{"id", "task", "path", "sha256", "n", "created",
"created_by", "purpose", "scored_runs": []}]}`. The audit checks provenance `dataset_files` against the registry.

### 6.5 Seed-replication gate

`research-session findings-check` errors when a `replicated` row lacks two provenance files with distinct seeds, when
a `verified` row lacks a commit-naming provenance file, and, with `--paper <draft.md>`, when the draft cites any F-id
whose status is not `replicated`.

## 7. Staging and apply (constraint 3)

Agents never write in place to `A`, to `~/.claude`, `~/.codex` or `~/.local/bin`. They write full files under
`S/tree/<absolute destination without the leading slash>` and an op list `S/ops/<NN>-<slug>.json`:

```json
{"ticket": "01", "ops": [
 {"op": "write", "dest": "/abs/path", "src": "tree/abs/path", "expect_sha256": "<sha256 or absent>", "lint": true, "wave": "A"},
 {"op": "json_merge", "dest": "/abs/settings.json", "fragment": {}, "replace_paths": ["autoMode.environment"], "wave": "A"},
 {"op": "replace_text", "dest": "/abs/MEMORY.md", "old_text": "exact line", "new_text": "new line", "lint": true, "wave": "A"},
 {"op": "append_text", "dest": "/abs/MEMORY.md", "text": "- [Title](file.md) — hook\n", "lint": true, "wave": "A"},
 {"op": "text_block", "dest": "/abs/file", "marker": "autoresearch-workflow", "text": "...", "position": "before_first_table", "wave": "C"},
 {"op": "move", "src": "/abs/a", "dest": "/abs/b", "wave": "B"},
 {"op": "symlink", "path": "/abs/link", "target": "/abs/target", "wave": "B"},
 {"op": "mkdir", "path": "/abs/dir", "wave": "B"}]}
```

The apply tool `F/tools/apply_staged.py` (stdlib only, tested on both interpreters) reads every op file in ticket
order and supports `--dry-run`, `--wave A|B|C`, `--only NN`, `--allow codex-config` and `--rollback <journal>`. It is
idempotent: an op whose target already has the desired content is skipped and reported. Before changing a target it
copies it to `/u/swong2/.claude/research-session/backups/<timestamp>/<abs path>` and records the op in a journal
there. `json_merge` deep-merges dicts, appends list entries that are not already present (hook groups compare by
command string), and replaces the lists named in `replace_paths`. A `write` with `expect_sha256` refuses when the
current file differs (a concurrent Codex edit) and reports a conflict; whole-file memory writes always carry it
(constraint 4). `replace_text` requires `old_text` to occur exactly once in the current file at apply time and
`append_text` skips text already present, so line edits to a shared file such as `MEMORY.md` survive concurrent
edits elsewhere in it; two tickets that touch the same shared file must use these two ops, never whole-file writes.
An op with `lint: true` lints the resulting file first. The lint runs through `--lint-cmd`, which defaults to base
python3.9 on the staged `S/tree/.../research_session/cli.py lint` and falls back to the installed path. `text_block` inserts or replaces a
`# BEGIN <marker>` and `# END <marker>` block; for TOML, `before_first_table` places it before the first `[table]`
header. Any op touching `~/.codex/config.toml` requires `--allow codex-config`. The tool prints a diff summary (path,
lines added and removed) for each op.

Waves: **A** is applied after the ticket's review and needs no merge (memory, user settings, staged RS code, docs).
**B** needs the Deception-Circuit branch merged to main (migration symlinks and anything pointing into DC main).
**C** needs the user's go because Codex must restart (`~/.codex/config.toml`).

## 8. Acceptance per phase

- **P0 (ticket 01).** The lint passes on the clean corpus and fails on all three glued samples; MEMORY.md and the
  two pointer notes pass the lint; wave A dry-run shows only the planned targets; settings JSON parses after a dry
  merge; the Codex TOML text parses with `tomllib` on mgnp.
- **P1 (tickets 05, 09, 10).** `research-session validate` passes on FINDINGS, directions.json and every ledger;
  the renders are byte-stable on a second run; every `.scratch/...` string in DC code resolves before and after
  migration; the named tests pass identically before and after; a token count of INDEX, FINDINGS and SESSIONS is
  under 30k (bytes divided by 4).
- **P2 (tickets 02, 03, 06).** RS tests pass on both interpreters; each hook event has a fixture test with a recorded
  input that asserts the exact JSON output; the gate's decision table (§5.2) has one test per row.
- **P3 (tickets 07, 08).** Protocol docs and templates pass the lint; every command named in a doc exists in
  `research-session --help`; profile files parse and contain only the keys in §5.7.
- **P4 (ticket 04).** New tests pass on both interpreters; the DC suite shows no new failure names against the
  recorded baseline; the checker runs on `docs/research/mechanism-analysis/synthesis.md` and its counts are reported.
- **P5 (tickets 11, 12).** The checklist names every observation in §5 with the command or UI step that shows it.

## 9. Rulings

All rulings are the planner's under the user's go of 2026-10-31, unless marked otherwise.

- **R1. RS lives at `A/.agents/research_session/`, staged by agents, applied by the orchestrator.** Its absolute path
  is the same before and after the Deception-Circuit merge and from every worktree of both repositories, so hook
  commands never change between the pilot and production. It sits next to `codex_usage.py` and the bridge, whose
  tests already run on both interpreters, and the `.gitignore` there excludes only memory, skills and caches. A
  human-facing wrapper `~/.local/bin/research-session` follows the `codex-usage` precedent. The science-guard code
  (§6.1-6.3) lives in DC because it runs inside experiments.
- **R2. The provenance file is `run_manifest.json`, not `manifest.json`.** `manifest.json` already means a frozen
  input manifest with hash verification in `evaluate_native_sparse.py:334,459`, `evaluation/generation_checkpoint.py:118`
  and the SDR scripts. Field names are reused. `findings-check` accepts a legacy `manifest.json` that names
  `git_commit` as provenance, with a warning that its dirty state is unknown.
- **R3. Migration archives whole `.scratch` directories, byte for byte, and copies a curated text subset.** Each
  migrated directory is renamed on the same filesystem to `DC/outputs/_studies/<slug>/scratch/` and replaced by a
  symlink, exactly as selective-deception was (its symlink points into `outputs/_studies`, not `docs/research`).
  Every absolute and relative `.scratch/...` path used by code, tests and receipts keeps resolving. The curated
  subset (spec, plan, progress or RESUME, analysis, final reviews, issues) is copied into
  `docs/research/<direction>/scratch-copy/<scratch slug>/` with a `provenance.json` mapping each copy to its archive
  path and sha256. The migration is a script with sha256
  before and after; the implementer does not read the directories. Excluded: `sdr-session-wrapup` (written today by
  another session) and `selective-deception` (already moved). A directory with any file modified in the last 12
  hours is skipped and reported.
- **R4. Hook placement.** Gate, lint, hand-back and compaction hooks live in the project settings of both repos, so
  they never fire in the user's other repositories. User-level settings carry only the keys in §5.1. Codex has only
  user-level `hooks.json`, so the scripts' own cwd check confines them.
- **R5. Session to direction mapping.** The authoritative counters live in a private local session file keyed by tool
  and session id. The direction is resolved by an explicit `research-session register <slug>` (whose session id is
  injected by H-a), else by matching the session's cwd against `worktree` in DC main's `directions.json`. An
  unregistered session still gets the cap, stale and checkpoint gate; its counters stay local only.
- **R6. FREEZE is two-stage.** The proposal's D2 denies SendMessage to workers while H4 says never deny SendMessage.
  Stage `crossed` denies only Agent and `sbatch`, so the orchestrator can send hold instructions; stage `recorded`
  adds the SendMessage denial, with `HOLD` messages and subagent messages always allowed.
- **R7. Acknowledgement is human-only.** The gate denies model-issued commands and edits that could ack or edit
  counters. `!` commands typed by the user do not pass through PreToolUse, so `! research-session usage-ack` works.
- **R8. Stale threshold is 15 minutes, and unknown denies spawns.** The pilot measures whether background sessions
  refresh `usage.json`. The human-only `usage-ack --stale-ok <minutes>` (at most 60) allows spawns on a stale reading
  for that window. RS never fetches the usage endpoint itself and never calls `statusline.sh` (a call with an empty
  payload would drop `five_hour` from `usage.json`).
- **R9. Usage targets.** Five-hour and weekly caps are both 80% (D7). The memory note `usage-limit-policy` is updated
  from 75% to 80% and records that the weekly reading is `max(seven_day, Fable row)`.
- **R10. Lint numbers are fixed as in §5.5.** Ticket 01 may extend the allowlist only, and must report every
  clean-corpus failure it found and how it was resolved.
- **R11. Codex worker model.** `[agents] default_subagent_model = "gpt-6.1-sol"` is staged as a wave C text block
  before the first table header of `~/.codex/config.toml`. The bridge sentence "inherit the parent's Codex model" is
  changed to "use the model the spawn names, else the configured default" only if the bridge tests pass on the
  staged copy; otherwise it is left unchanged and reported.
- **R12. Codex event and tool names are verified, not assumed.** Ticket 06 checks the Codex hooks page for the spawn,
  shell, message and patch tool names and records them with the doc URL. Unverified matchers are not installed.
- **R13. The two large memory logs move verbatim, not rewritten.** `sdr-mechanism-review.md` and
  `selective-deception-execution.md` become pointer notes of at most 15 lines; their full bodies are copied unchanged to
  `DC/outputs/_studies/<slug>/memory-log-20261031.md` (ignored, local, never pushed) because they contain cluster and
  allocation details and the DC repository is public.
- **R14. Archived glued files are not rewritten.** `sdr-clause-choice/RESUME.md` stays as it is inside its archive.
  Ticket 09 writes a readable rewrite to `docs/research/sdr-mechanism/history/sdr-clause-choice-RESUME-readable.md`.
- **R15. Direction granularity.** One registry row per research direction. The ten `sdr-*` study directories and the
  wrap-up directory are listed as `legacy_scratch` and `archive` entries of the `sdr-mechanism` row.
- **R16. Old evidence.** A seeded FINDINGS row backed only by outputs without provenance gets `commit = pre-manifest`
  and at most `reviewed`. It becomes `verified` only when a provenance-stamped run reproduces it.
- **R17. Status vocabulary.** `verified` and `replicated` are separate statuses (the proposal wrote them as one).
  Paper headlines require `replicated`.
- **R18. Staging is per ticket.** Each ticket writes its own op file, so two tickets never edit the same staged file.
  Two tickets may target the same destination only through `json_merge`, `replace_text`, `append_text` or distinct
  `text_block` markers. `MEMORY.md` is only ever changed by `replace_text` and `append_text`.
- **R19. Held-out guard.** This feature ships the policy and registry only. A scoring guard in `evaluate_circuit.py`
  is a follow-up direction, recorded as a `proposed` row in `directions.json` by ticket 12.
- **R20. Sizing.** Each ticket fits one Opus context with margin: reading plus writing under about 250k tokens, and
  briefs sized to finish under 350k until the 600k window test passes (ticket 11).
- **R21. Gitignore in DC.** Ticket 06 adds `.claude/worktrees/` and `.claude/settings.local.json` to DC's
  `.gitignore` when it creates the tracked `DC/.claude/settings.json`.
- **R22. Times.** RS writes worklog times in America/Chicago with the zone abbreviation computed, never typed; the
  zone changes from CDT to CST on 1 November 2026.
- **R23. Claims.** Only the orchestrator edits `directions.json` (through `research-session claim`) and commits the
  claim on DC main before creating the branch. Pushing follows the user's standing push policy.
- **R24. The agent definitions change from Sonnet to Opus.** `idea-critic`, `paper-reader` and `paper-searcher`
  currently say `model: sonnet`; H1 changes them to `model: opus`, and `env.CLAUDE_CODE_SUBAGENT_MODEL = "opus"`
  covers spawns without a model.
- **R25. Execution-evidence block lives in two places.** `_templates/handback.md` (ticket 08) and the shared section of
  `A/.claude/agents/ticket-implementer.md` (ticket 08, staged), so every future feature brief inherits it.
