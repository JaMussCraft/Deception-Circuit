# 02 — Hand-back: research-session core (usage readings, session state, the gate, acknowledgement)

Implementer: Opus, ticket 02, 2026-10-31. No git command was run. Nothing was installed or applied, no hook was
written, the real credentials file was never opened, and no network call was made. Every file whose home is in the
Alignment checkout or in `~/.local/bin` is staged under S and listed in one op file.

## What changed

### Committed by the orchestrator from W

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/reports/02-handback.md` (this file)
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/autoresearch-workflow/docs/research/autoresearch-workflow/issues/02-rs-core-usage-state-gate.md` (status, checkboxes and comments)

### Staged in S, ops file `S/ops/02-rs-core.json`

The ops file is `/u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging/ops/02-rs-core.json`. It holds 14 write ops,
all in wave A. Staged sources live under `S/tree/` at the destination path. Paths below are relative to
`/projects/beto/swong2/Alignment/.agents/`.

New package modules:

1. `research_session/paths.py`: the `Config` object with every path and its environment override, the state root
   created with mode 0700 when missing, the `DISABLED` kill switch, the check that the realpath of `cwd` lies inside
   the Alignment root, the session tag of R29, and America/New_York times with computed offsets.
2. `research_session/usage.py`: the Claude reader with per-field freshness and the R8 refresh, the Codex reader with
   the 120 s cache, the segment update, checkpoint crossing, `fable_gap` and the D8 notice.
3. `research_session/oauth_refresh.py`: the R8 refresh with the status line's cache file, lock directory, 60 s lock
   sweep and 300 s retry floor. It holds the one credentials reader `read_token` and the `urllib` fetch `http_get`
   with an 8 s timeout. It merges into `usage.json` by atomic replace.
4. `research_session/state.py`: the session file with `fcntl.flock` on a sidecar lock and atomic replace, the mirror
   into a registered direction's `state.json`, direction resolution under R5, `register`, `ack` and
   `mark_checkpoint_recorded`, which ticket 03 calls from `worklog-append --checkpoint N`.
5. `research_session/gate.py`: the pure `decide` function for spec 5.2 steps 1 to 7, the thin I/O wrapper
   `evaluate`, the fail-closed wrapper `safe_evaluate`, and `hook_output`, which builds the PreToolUse JSON.

Changed module:

6. `research_session/cli.py`, whole-file write with `expect_sha256` 20bfc1443aae... (the installed ticket 01 file,
   which was byte-identical to the staged copy). It adds `register`, `status`, `usage-check`, `usage-ack` and
   `set-cadence`. The `lint` code is unchanged. `__init__.py` is not changed.

New tests and fixtures:

7. `tests/_rs_testlib.py`, a shared helper. It points every path at a temporary directory and replaces the
   credentials reader and the HTTP call with guards that fail the test unless the test installs a mock.
8. `tests/test_research_session_usage.py` (33 tests), `tests/test_research_session_state.py` (23 tests) and
   `tests/test_research_session_gate.py` (38 tests).
9. `tests/fixtures/gate/pretooluse_agent.json`, `pretooluse_bash_sbatch.json` and
   `pretooluse_sendmessage_orchestrator.json`. They follow the documented PreToolUse input shape of lane 2 section 1.
   They are not live recordings, so ticket 06 should replace them with recorded inputs.

Human wrapper:

10. `/u/swong2/.local/bin/research-session`, a two-line `/bin/sh` wrapper that runs base python3.9 with `-B` on the
    installed `cli.py`. The staged file has mode 0755, and the apply tool copies the source mode onto a new file.

Staged without an op, to bring the staged test tree level with the installed one: `tests/test_codex_usage.py` and
`/projects/beto/swong2/Alignment/.agents/codex_usage.py`, both copied unchanged from the installed files. The Codex
usage test finds its script through its own parent directory, so both copies are needed for the staged suite. This
follows ticket 01's bridge-test precedent.

### Scratch files in T

The helper scripts are in `/u/swong2/.claude/jobs/b2cb53cd/tmp/02/`. `cache_keys.py` printed key names and value types
of the OAuth cache and `usage.json`, never values. `reset_diffs.py` printed only differences between reset times.
`nolock_check.py` is the power check described below, and `make_ops.py` writes the op file.

### Orchestrator ruling R40 (applied after the first hand-back)

The user reports that Anthropic removed the five-hour limit from this account on 2026-10-31. The orchestrator's
revised R40 answers open question 1 and replaces an earlier version of the ruling. A missing `five_hour` key in a
fresh `usage.json` means the five-hour limit does not apply. It is not read as 0, and it does not trigger a refresh.
The reading's `notes` list says "five-hour limit not applicable". When the key is present, the 80% five-hour cap
still applies. The weekly rule is unchanged. Spec 5.2 now says the same.

The code changes are small. `usage.py` sets the five-hour value to None, flags it as missing, and adds the note.
`format_reading` prints "five-hour not applicable". The cap check already skips a None value, so the weekly reading
alone decides the cap. `cli.py` prints each note, and `status` shows a missing five-hour value as "not applicable".
The earlier version of the ruling had added refresh-on-missing code, and that code is removed. At the orchestrator's
request, two merge improvements from that pass are kept in `oauth_refresh.py`. The merge fills a window that is
absent from `usage.json` from a fetched or cached body even when the body is older than the file's `timestamp`, and
it leaves `timestamp` unchanged then. It also does not rewrite `usage.json` when a merge changes nothing. A refresh
can therefore put a `five_hour` key back into the file when the endpoint still reports one, and the 80% cap then
applies to it.

### Time zone (orchestrator request)

The user's time zone is US Eastern. `paths.TIMEZONE` is now `America/New_York`, and `paths.iso` computes every offset
from it with `zoneinfo`. No zone label or offset is typed anywhere in the staged code. A grep of the staged package,
tests and wrapper finds no `America/Chicago`, `CDT` or `CST` text. The staged `paths.py` has sha256 257760f46265...
and says `America/New_York` at line 33 and in the `iso` docstring at line 142. A re-run after this check gave 136
passed on mgnp, with 19 subtests, and 136 passed on base python3.9.

The tests for the revised ruling are as follows. A fresh file without `five_hour` is known, has no five-hour value,
carries the note, and causes no token read and no fetch. A stale refresh whose body lacks the five-hour window gives
the same result. A missing weekly key in a fresh file still reads as 0. The cap row allows spawns at weekly 79 with
no five-hour key and denies them at 80. An end-to-end gate call on a fresh file without `five_hour` allows a spawn
without a fetch. `usage-check` prints the note. The five-hour cap test with the key present at 85 still denies. Two
more tests cover the kept merge behaviour: an absent five-hour window is filled from a 100 s old cache without moving
`timestamp` or overwriting the newer seven-day value, and an unchanged merge keeps the file's inode and mtime. A
state test checks that `iso` matches `zoneinfo` for America/New_York on both sides of the 1 November 2026
daylight-saving change, and that the two offsets differ.

## How verified

### Staged suite, both interpreters

```
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/u/swong2/.claude/jobs/b2cb53cd/tmp/02 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider S/tree/projects/beto/swong2/Alignment/.agents/tests
136 passed, 19 subtests passed in 15.22s
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/u/swong2/.claude/jobs/b2cb53cd/tmp/02 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider S/tree/projects/beto/swong2/Alignment/.agents/tests
136 passed in 17.19s
```

These results are from after the revised R40 change and the time-zone change. The 136 tests are the 35 from ticket
01, the 7 Codex usage tests, and 94 new ones. The first hand-back reported 128 passed on each interpreter, before the R40 tests. The two
failures of the first
run were fixed as follows. The two-process test exposed a real race: two processes creating the state root at the
same moment raised `FileExistsError`, and `ensure_dir` now tolerates it. One register test expected no warning while
its direction directory was missing, so the test now creates the directory.

### The concurrency test can detect lost updates

```
/u/swong2/.conda/envs/mgnp/bin/python -B /u/swong2/.claude/jobs/b2cb53cd/tmp/02/nolock_check.py
without lock: 60 of 120 updates kept
```

With the lock in place, the test keeps all 120 updates from two processes.

### Wave A dry run

```
/sw/external/python/anaconda3/bin/python3.9 -B F/tools/apply_staged.py --staging /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging --wave A --only 02 --dry-run
dry run, wave A: 14 op(s) selected from 14
[02#1] write /projects/beto/swong2/Alignment/.agents/research_session/paths.py WOULD APPLY: +156 -0 lines, new file
[02#2] write /projects/beto/swong2/Alignment/.agents/research_session/usage.py WOULD APPLY: +309 -0 lines, new file
[02#3] write /projects/beto/swong2/Alignment/.agents/research_session/oauth_refresh.py WOULD APPLY: +340 -0 lines, new file
[02#4] write /projects/beto/swong2/Alignment/.agents/research_session/state.py WOULD APPLY: +389 -0 lines, new file
[02#5] write /projects/beto/swong2/Alignment/.agents/research_session/gate.py WOULD APPLY: +381 -0 lines, new file
[02#6] write /projects/beto/swong2/Alignment/.agents/research_session/cli.py WOULD APPLY: +208 -0 lines
[02#7] write /projects/beto/swong2/Alignment/.agents/tests/_rs_testlib.py WOULD APPLY: +191 -0 lines, new file
[02#8] write /projects/beto/swong2/Alignment/.agents/tests/test_research_session_usage.py WOULD APPLY: +395 -0 lines, new file
[02#9] write /projects/beto/swong2/Alignment/.agents/tests/test_research_session_state.py WOULD APPLY: +272 -0 lines, new file
[02#10] write /projects/beto/swong2/Alignment/.agents/tests/test_research_session_gate.py WOULD APPLY: +463 -0 lines, new file
[02#11] write /projects/beto/swong2/Alignment/.agents/tests/fixtures/gate/pretooluse_agent.json WOULD APPLY: +15 -0 lines, new file
[02#12] write /projects/beto/swong2/Alignment/.agents/tests/fixtures/gate/pretooluse_bash_sbatch.json WOULD APPLY: +13 -0 lines, new file
[02#13] write /projects/beto/swong2/Alignment/.agents/tests/fixtures/gate/pretooluse_sendmessage_orchestrator.json WOULD APPLY: +14 -0 lines, new file
[02#14] write /u/swong2/.local/bin/research-session WOULD APPLY: +2 -0 lines, new file
```

### Smoke run of the staged CLI as a script on base python3.9

`usage-check --no-refresh` reads the real `usage.json` and returns before the refresh, so it never reaches the
credentials reader.

```
python3.9 -B S/tree/.../research_session/cli.py usage-check --no-refresh
reading (claude): five-hour not applicable, seven-day 15%, Fable 20%, weekly max 20%
freshness: five-hour and seven-day fresh (16 s old); Fable fresh (75 s old); limit 15 min
refresh: not needed
fable gap: 5 points
note: five-hour limit not applicable
```

This run is from after the revised R40 change. The live file has no `five_hour` key.

`--help` lists the six subcommands. `status` with a scratch state root exits 1 and says that no session has this
cwd, which is correct before any hook has created a session file.

### What the tests cover, by acceptance criterion

- **Usage readings.** A fresh reading, a stale `timestamp` with a fresh `model_scoped_fetched_at` (five-hour
  unknown), a missing weekly key in a fresh file (reads 0), a missing `five_hour` in a fresh file (not applicable,
  no refresh, R40), a missing key in a stale file (unknown), a missing Fable row
  (reads 0), a malformed value (unknown), a `resets_at` rollover, a drop below `last`, points summed across two
  segments, and reset jitter under a minute. The Codex reader is tested on exit 0, 1 and 2 with a fake executable,
  with a cache hit at 119 s and a new run at 121 s.
- **Refresh.** A stale file becomes fresh after a mocked fetch, and the merge keeps every pre-existing key. A lock
  30 s old skips the fetch, and a lock 61 s old is swept. A cache 200 s old is reused with no fetch and no token read.
  A failed fetch inside the retry floor stays unknown. An endpoint error and a timeout each leave the reading unknown,
  and the gate then denies a spawn with the refresh error in the reason. An expired token is never sent. The real
  `http_get` passes an 8 s timeout and maps a timeout to a safe message with the exception context suppressed. A
  planted fake token is absent from stdout, stderr, the cache and `usage.json`, even when the mocked endpoint raises
  an exception whose text contains the token.
- **Gate rows.** One test per row of spec 5.2: the self-ack guard for Bash and for Write and Edit, the cap pause on
  five-hour and on weekly, an unknown reading, an unregistered session, freeze `crossed`, and freeze `recorded` with
  a normal message, a `HOLD` message, a message to `main` and a subagent message, plus allow. Extra cases cover a
  stale-ok window, the kill switch, a cwd outside A, Bash without `sbatch` during a freeze, an exception in the
  decision, a corrupt session file, an acknowledged freeze, and the Codex freeze, which never denies messages (R32).
- **Unregistered sessions.** Fixtures (a) to (e) of the ticket run through `evaluate` with the fixture inputs. A
  further test shows that the state-file guard, the self-ack guard and the lint still apply in an unregistered
  session.
- **R37 and the write lint.** Writes and edits to a direction `state.json` or `worklog.json` and under the state root
  are denied in every freeze state, and `_templates/` is exempt. `research-session validate` on a direction file is
  allowed, but the same command with `>`, or `render`, `cat`, `rm` or `sed` naming the file, is denied. The lint
  tests cover a glued WORKLOG paragraph, a glued Edit, a planted fake token, a clean write, an out-of-scope Markdown
  file, and a write outside A.
- **Reasons.** Every reason text is built with extreme inputs, and the test checks that it stays within 400
  characters, names a next action, and is not cut short.

## Execution evidence

Not applicable: no runs. No Slurm job, GPU job or paid API call was made.

## What is NOT done

- Nothing is applied. The orchestrator applies wave A after review.
- The `hook` subcommand and the wiring of stdin and stdout to `gate.safe_evaluate` and `gate.hook_output` are
  ticket 06.
- The real `http_get` was never run against the endpoint, because the brief forbids a real token and network calls.
  Its request headers copy the status line's, and its error mapping is tested with a mocked `urlopen`.
- I wrote the first draft of the modules before their tests, so this ticket was not strictly test-first. Every
  acceptance item has a test, and the first test run found two problems, both fixed above.

## Open questions

1. **A fresh file without `five_hour`.** Resolved by the revised ruling R40: the five-hour limit is not applicable
   (see "Orchestrator ruling R40" above). The earlier conflict between the first ruling message and `RESUME.md` is
   closed, because the revised ruling matches `RESUME.md` and spec 5.2.
2. **Retry floor and failed fetches.** The status line touches the cache file after a failed fetch when a good body
   exists. RS follows it and reuses a cached body inside the 300 s floor only when its `fetched_at` is within 15
   minutes. Otherwise the reading stays unknown and the reason says "retry floor". So after a failure the gate denies
   spawns for up to 5 minutes before the next fetch.
3. **Reset jitter.** The status-line payload gives whole seconds and the endpoint gives fractions, measured here at
   0.317 s apart. A segment therefore closes only when `resets_at` moves by more than 60 s. Without that tolerance,
   each refresh after a status-line write would open a new segment and drop the points earned between the readings.
4. **Mirror destination.** `register` stores the mirror path at bind time. The path is
   `<checkout of the session cwd>/docs/research/<slug>/state.json`, where the checkout is the nearest ancestor with
   `docs/research`, or DC main otherwise. A `state` field in the registry row overrides the relative part. When the
   direction directory does not exist, the mirror is skipped with a warning, and RS never creates a directory in a
   repository. When `directions.json` is missing, which is true until ticket 05, `register` still binds and warns.
5. **The mirror skips writes that only change the read time.** A mirror write that would change only
   `last_reading.read_at` is skipped, so a tracked `state.json` does not change on every tool call. The local session
   file is still written on every gated call.
6. **Strict Bash guard.** Any shell operator in a command that names a direction file denies it, even with a
   read-only subcommand. The operators are `>`, `<`, `;`, `&`, `|`, a backtick, `$(` and a newline, so
   `research-session validate x/state.json 2>/dev/null` is denied too. A path that cannot be resolved, because it
   holds `$`, `*`, `?` or `[`, counts as a direction file. Plain `cat` of a direction file is denied, and the Read
   tool is the way to view it.
7. **Gate scope.** The gate takes a reading only for Agent, Bash and SendMessage calls. Write and Edit calls run the
   file guards and the lint, with no reading and no session-file write. Messages and Bash calls without `sbatch` are
   never denied for an unknown reading or a cap. They still update the counters, so checkpoints cross on time.
8. **Tool names.** The gate treats `Agent`, `Task` and Codex `spawn_agent` as spawns. It treats `Bash`, `shell`,
   `local_shell` and `exec_command` as shells, and it joins a list-form command. It treats `Write`, `Edit`,
   `MultiEdit` and `NotebookEdit` as writes. Ticket 06 verifies the Codex names (R12) and `apply_patch`.
9. **Re-applying ticket 01 would overwrite cli.py (R18).** Ticket 01's op file still has a `write` op for `cli.py`.
   It has no `expect_sha256` and reads the shared staged source, which now holds the ticket 02 version. So a later
   run of `--wave A --only 01` would install ticket 02's `cli.py` without the hash check. Applying with `--only 02`
   is safe, and so is applying both tickets together, because 02#6 then reports SKIP. Later tickets that extend
   `cli.py` will add the same overlap.
