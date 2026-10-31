# 02 — RS core: usage readings, session state, the gate, acknowledgement

**Status:** ready-for-agent
**Type:** task
**Blocked by:** 01 (package skeleton and `cli.py`)
**Wave:** A
**Estimated size:** reading about 50k tokens (spec §4.5, §5.1-5.4, §9 R5-R9; lane 4 §2; lane 2 §2; the files named
below), writing about 70k tokens of code and tests.
**Hand-back:** `F/reports/02-handback.md`

## What to do

Implement the parts of RS that hold the counters and make the gate decision, as pure functions with thin I/O, so
ticket 06 only wires hook input and output to them. Stage a human-facing wrapper.

## Facts to build on

- `/u/swong2/.claude/usage.json` shape: `{"rate_limits": {"five_hour": {"used_percentage", "resets_at"},
  "seven_day": {...}, "model_scoped": [{"display_name": "Fable", "used_percentage", "resets_at"}],
  "model_scoped_fetched_at": <epoch>}, "timestamp": <epoch>}`. It is written by `~/.claude/statusline.sh`
  (lines 5-11 and 247 onward). A status-line call with an empty payload rewrites the file without `five_hour`
  (line 158), so RS must never call it (R8).
- `/u/swong2/.local/bin/codex-usage` runs `A/.agents/codex_usage.py`; JSON output has `weekly.used_percent`,
  `weekly.remaining_percent` and the reset; exit 0 below cap, 2 reached, 1 unknown (`A/docs/agents/codex-usage.md`).
- Segment algorithm: lane 4 §2 "Computing the increment", adopted by spec §5.2.
- Hook inputs carry `session_id`, `cwd`, and `agent_id`/`agent_type` inside subagents (lane 2 §1).

## Scope

Staged in S (paths relative to `S/tree/projects/beto/swong2/Alignment/.agents/`):
- `research_session/paths.py` (state root `/u/swong2/.claude/research-session/`, created with mode 0700; the
  `DISABLED` kill switch; the cwd-inside-A check).
- `research_session/usage.py` (Claude reader with per-field freshness; Codex reader with the 120 s cache; segment
  update; `fable_gap`).
- `research_session/state.py` (local session file: load, lock with `fcntl.flock`, atomic replace; mirror into a
  registered direction's `state.json`; direction resolution per R5).
- `research_session/gate.py` (pure decision function implementing spec §5.2 steps 1-6, returning allow or deny
  with the reason text, plus the fail-closed wrapper).
- `cli.py` subcommands `register`, `status`, `usage-check`, `usage-ack [--session] [--stale-ok]`, `set-cadence`.
- Tests: `tests/test_research_session_usage.py`, `test_research_session_state.py`, `test_research_session_gate.py`.
- `S/tree/u/swong2/.local/bin/research-session`, a two-line `/bin/sh` wrapper that execs base python3.9 on
  `A/.agents/research_session/cli.py`, mode 0755.
- `S/ops/02-rs-core.json`.

## Acceptance criteria

- [ ] Usage tests cover: a fresh reading; a stale `timestamp` with a fresh `model_scoped_fetched_at` (five-hour
      unknown); a missing key in a fresh file (reads 0); a missing Fable row; `resets_at` rollover; a drop below
      `last` without a reset change; points summed across two segments; the Codex reader on exit 0, 1 and 2 using a
      fake `codex-usage` executable; the Codex cache hit within 120 s.
- [ ] Gate tests have one case per row of spec §5.2 (self-ack guard for Bash and for Write/Edit, cap pause on
      five-hour and on weekly, unknown reading, freeze `crossed`, freeze `recorded` with a normal message, a `HOLD`
      message, a message to `main`, and a subagent message, and allow), plus: a `stale-ok` window allowing spawns, the
      kill switch, a cwd outside A, Bash without `sbatch` allowed during a freeze, and an exception inside the
      decision giving deny for Agent and `sbatch` and allow for others.
- [ ] State tests cover: two concurrent writers (two processes) without lost updates; mirroring into a direction
      `state.json`; resolution by explicit `register`, by cwd match against a fixture `directions.json`, and the
      unregistered case.
- [ ] `register <slug>` binds the most recent session whose `cwd` matches, and `register <slug> --session ID` binds
      that session; both print the session tag and direction.
- [ ] Gate tests include Write and Edit calls: denied under the session-state root and on `docs/research/*/state.json`,
      allowed elsewhere, regardless of freeze state.
- [ ] `usage-ack` acks the most recent session whose `cwd` matches, prints which one, refuses `--stale-ok` above 60,
      and records `acked_by: "usage-ack"`.
- [ ] All tests pass in both envs (commands from the brief); paste the summary lines.
- [ ] Every reason string the gate can return is at most 400 characters and names the next action.
- [ ] `apply_staged.py --staging S --wave A --only 02 --dry-run` output pasted.

## Verification

Both interpreters. Tests use temporary directories and environment overrides for the state root and the usage file
path; they never read the real `~/.claude`.

## Comments
