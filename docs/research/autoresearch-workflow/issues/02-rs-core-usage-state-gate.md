# 02 — RS core: usage readings, session state, the gate, acknowledgement

**Status:** claimed
**Type:** task
**Blocked by:** 01 (package skeleton and `cli.py`)
**Wave:** A
**Estimated size:** reading about 60k tokens (spec §4.5, §5.1-5.5, §9 R5-R9, R26-R30, R36-R37; lane 4 §2; lane 2
§2; the files named below), writing about 90k tokens of code and tests.
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
- The status line's OAuth refresh (`~/.claude/statusline.sh:19-22` for the paths, `:41-113` for the logic) fetches
  `https://api.anthropic.com/api/oauth/usage` into `~/.claude/.usage_oauth_cache.json` as
  `{"fetched_at": <epoch>, "body": {...}}`, holds the lock directory `~/.claude/.usage_oauth_cache.lock` (swept when
  older than 60 s) and retries at most every 300 s. The cache body carries `five_hour`, `seven_day` and a `limits`
  list whose kinds include `session`, `weekly_all` and `weekly_scoped` (reviewer printed key names only). The status
  line's mapping from the body to `model_scoped` is at about lines 200-230; reuse it. You may print key names of the
  cache body; you may not open `~/.claude/.credentials.json` (brief constraint 11).
- `/u/swong2/.local/bin/codex-usage` runs `A/.agents/codex_usage.py`; JSON output has `weekly.used_percent`,
  `weekly.remaining_percent` and the reset; exit 0 below cap, 2 reached, 1 unknown (`A/docs/agents/codex-usage.md`).
- Segment algorithm: lane 4 §2 "Computing the increment", adopted by spec §5.2.
- Hook inputs carry `session_id`, `cwd`, and `agent_id`/`agent_type` inside subagents (lane 2 §1).

## Scope

Staged in S (paths relative to `S/tree/projects/beto/swong2/Alignment/.agents/`):
- `research_session/paths.py` (state root `/u/swong2/.claude/research-session/`, created with mode 0700; the
  `DISABLED` kill switch; the cwd-inside-A check).
- `research_session/usage.py` (Claude reader with per-field freshness; the stale-reading refresh of R8; Codex
  reader with the 120 s cache; segment update; `fable_gap`).
- `research_session/oauth_refresh.py`: the R8 refresh. It takes the same lock directory as the status line (and
  honours its 60 s stale sweep and 300 s retry floor), reads the token inside the process through one small
  credentials-reader function, calls the endpoint with `urllib` and an 8 s timeout, updates the cache file, and merges
  `five_hour`, `seven_day` and the weekly-scoped rows into `usage.json` by atomic replace, keeping every existing key
  and setting `timestamp` and `model_scoped_fetched_at` to the fetch time. The token never appears in output, logs,
  exceptions, `argv` or the environment of a child process.
- `research_session/state.py` (local session file: load, lock with `fcntl.flock`, atomic replace; mirror into a
  registered direction's `state.json`; direction resolution per R5).
- `research_session/gate.py` (pure decision function implementing spec §5.2 steps 1-7, returning allow or deny
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
- [ ] Refresh tests, with a mocked credentials reader and a mocked HTTP endpoint (no real token, no network): a
      stale `usage.json` is refreshed and the reading becomes fresh; every pre-existing key of `usage.json` survives;
      the lock held by another process within 60 s makes RS skip the fetch; a lock older than 60 s is swept; a cache
      younger than 300 s is reused without a fetch; an endpoint error or an 8 s timeout leaves the reading unknown
      and the gate denies spawns with the refresh error in the reason; a planted fake token never appears in stdout,
      stderr, the cache or `usage.json`.
- [ ] `usage-check` prints the reading, its freshness, whether a refresh happened, and the Fable gap.
- [ ] Gate tests have one case per row of spec §5.2 (self-ack guard for Bash and for Write/Edit, cap pause on
      five-hour and on weekly, unknown reading, unregistered session, freeze `crossed`, freeze `recorded` with a
      normal message, a `HOLD` message, a message to `main`, and a subagent message, and allow), plus: a `stale-ok`
      window allowing spawns, the kill switch, a cwd outside A, Bash without `sbatch` allowed during a freeze, and an
      exception inside the decision giving deny for Agent and `sbatch` and allow for others.
- [ ] Unregistered-session fixtures (R5, §5.2 step 4), each a recorded PreToolUse input with a session file that has
      no `register` entry: (a) session points at 40 with cadence 16 and fresh usage under 80%: Agent, `sbatch` and an
      orchestrator SendMessage are all allowed and no freeze is recorded; (b) the same session at `w = 81`: Agent and
      `sbatch` are denied by the cap pause; (c) the same session with a stale reading and a failed mocked refresh:
      Agent is denied as unknown; (d) a session whose cwd matches a direction `worktree` but never ran `register` is
      still treated as unregistered; (e) `register` at 40 points stores `points_at_register = 40`, the next call is
      allowed, and checkpoint 1 crosses only at 56 points. The self-ack guard and the Write/Edit lint still apply
      in unregistered sessions, because they protect files rather than pace work.
- [ ] State tests cover: two concurrent writers (two processes) without lost updates; mirroring into a direction
      `state.json`; resolution by explicit `register`, by cwd match against a fixture `directions.json`, and the
      unregistered case.
- [ ] `register <slug>` binds the most recent session whose `cwd` matches, and `register <slug> --session ID` binds
      that session; both print the session tag and direction.
- [ ] Gate tests include Write and Edit calls: denied under the session-state root and on
      `docs/research/<slug>/state.json` or `worklog.json`, allowed on `docs/research/_templates/state.json` and
      elsewhere, regardless of freeze state. Bash `research-session validate .../state.json` is allowed; the same
      command with a `>` redirection, or any non-read-only subcommand naming that path, is denied (R37).
- [ ] The gate's Write and Edit path calls the lint's string function on `content` or `new_string` and denies with the
      failing units in at most 400 characters for scoped paths, and runs the secret scan for every path under A (R30).
      Tests cover a glued WORKLOG paragraph, a planted fake token, a clean write, and an out-of-scope Markdown file.
- [ ] `usage-ack` acks the most recent session whose `cwd` matches, prints which one, refuses `--stale-ok` above 60,
      and records `acked_by: "usage-ack"`.
- [ ] All tests pass in both envs (commands from the brief); paste the summary lines.
- [ ] Every reason string the gate can return is at most 400 characters and names the next action.
- [ ] `apply_staged.py --staging S --wave A --only 02 --dry-run` output pasted.

## Verification

Both interpreters. Tests use temporary directories and environment overrides for the state root and the usage file
path; they never read the real `~/.claude`.

## Comments
