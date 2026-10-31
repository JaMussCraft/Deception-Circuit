# Pilot checklist: research-session hooks, gate and audit (P5)

Written Sat 31 Oct 2026 by ticket 11 of the `autoresearch-workflow` feature. The user runs this pilot; no agent
launches it. Each step names the command or the interface action and what you should see. Record what you actually
see in the observation table at the end, which the pilot session copies to `reports/01-observations.md` in its
direction directory.

Names used below:

- **DC main** is the main checkout `/projects/beto/swong2/Alignment/Deception-Circuit`.
- **The pilot worktree** is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/pilot-hooks`.
- **The pilot directory** is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/pilot-hooks/docs/research/pilot-hooks`.
  It already holds `START.md`, `README.md`, `RESUME.md`, `WORKLOG.md`, `state.json`, `worklog.json` and
  `ledger.json`, created by `research-session init`, and `directions.json` has a `proposed` row `pilot-hooks`.
- **The session tag** is `claude-` or `codex-` plus the first 8 characters of the session id. `research-session
  status` prints the tag and the full id.
- **The main transcript.** This feature's own session showed where Claude puts transcripts when a session starts in
  one directory and then enters a worktree. The main transcript stays under the start directory's project folder:
  `/u/swong2/.claude/projects/-projects-beto-swong2-Alignment-Deception-Circuit/<session id>.jsonl`. Subagent
  transcripts go under the worktree's folder:
  `/u/swong2/.claude/projects/-projects-beto-swong2-Alignment-Deception-Circuit--claude-worktrees-pilot-hooks/<session id>/subagents/`.
  If either is missing, find them with `ls -d /u/swong2/.claude/projects/*/<session id>*`.

A command that starts with `!` is one you type into the Claude prompt yourself. It runs in the session's directory
and does not pass through the hooks. Every other command is one you ask the pilot session to run.

The kill switch, if a hook ever blocks ordinary tool calls, is this command typed by you:

```
! touch /u/swong2/.claude/research-session/DISABLED
```

Remove that file to turn the hooks back on. The five-hour limit no longer exists on this account (R40), so every
usage line below shows it as not applicable. Only the weekly readings matter: the cap is 80%, and sessions hold
themselves at 76%.

## Which step exercises which hook

| Hook | What it does | Steps |
|---|---|---|
| H-a | Session start context | 2a, 10a |
| H-b | Counts a compaction and injects the resume instruction | 5a, 9c, 10e |
| H-c | Saves the compaction summary to `handbacks/compaction-<N>.md` (Claude only) | 5a |
| H-d | Usage gate, freeze, self-acknowledgement guard and the write lint | 2e, 3a, 4a, 4d to 4h, 6a, 10c, 10d, 10f |
| H-e | Usage context after a spawn | 3b, 10c |
| H-f | Lint advice after an edit | 6b, 10f |
| H-g | Acknowledges a checkpoint only on the user's own "continue" | 4j to 4m, 10d |
| H-h | Hand-back rules injected into each subagent | 3c, 7a, 10c |
| H-i | Saves a subagent's last message and blocks once without a hand-back | 3e, 4f, 7a, 7b, 10g |
| H-j | Stop reminder while a crossed checkpoint is unrecorded (Claude only) | 4g |

## Step 1. Prerequisites the orchestrator confirms

The orchestrator of the `autoresearch-workflow` session confirms each item and writes the result into the
observation table before the user starts the pilot.

1a. **Waves A and H.** Both were applied on 31 October 2026, A first. H came only after the research-session tests
passed from the installed path and the hook smoke test passed. Confirm the installed hooks still pass:

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/hook_smoke.py
```

Expected: every line says PASS and the last line is `hook smoke: all checks passed`.

1b. **Ticket 11's own wave A ops** are applied, so `audit-scan` is installed. Expected: the command below prints the
usage line of `audit-scan`, and the installed tests pass on both interpreters with the count the hand-back of
ticket 11 gives.

```
/u/swong2/.local/bin/research-session audit-scan --help
```

1c. **The merge and wave B.** The `autoresearch-workflow` branch is merged into DC main with the user's go, and wave
B is applied after the merge, as ticket 10's hand-back describes. Expected: `docs/research/pilot-hooks/START.md`
exists in DC main, and the command below reports "applied" for all five entries and 0 problems. Hooks in DC sessions
come from the tracked `.claude/settings.json`, so DC worktrees get them only after this merge.

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/migrate_scratch.py verify --wave B
```

1d. **Waves C and D.** Wave C changes `~/.codex/config.toml` and needs the user's go and a Codex restart. Steps 10
and 11 need it for the Sol worker default and the Codex skill and server checks; the rest of the pilot does not.
Wave D waits until the live Codex session is finished; the pilot does not need it.

1e. **session-report** is installed and stays off by default. It was not installed on 31 October 2026. Run the three
commands of ticket 07's hand-back in order:

```
/u/swong2/.local/bin/claude plugin install session-report@claude-plugins-official --scope user
/u/swong2/.conda/envs/mgnp/bin/python -B /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py --staging /u/swong2/.claude/jobs/b2cb53cd/tmp/alignment-staging --only 07 --wave A
/sw/external/python/anaconda3/bin/python3.9 -c "import json;print(json.load(open('/u/swong2/.claude/settings.json'))['enabledPlugins'].get('session-report@claude-plugins-official'))"
```

Expected: the last command prints `False`.

1f. **Codex hook trust.** The user opens a fresh Codex session in the Alignment checkout, runs `/hooks` and trusts
the six research-session groups. Expected: `/hooks` lists them as trusted. Until then Codex skips them, and step 10
cannot run.

1g. **Profiles.** Expected: the command below lists `audit.json`, `research.json`, `synthesis.json` and
`writing.json`.

```
ls /u/swong2/.claude/profiles/
```

1h. **Bridge intact.** Expected: the check reports no drift, and the Codex hook file still holds the bridge's own
SessionStart group, so the count printed by the second command is at least 1.

```
/sw/external/python/anaconda3/bin/python3.9 -B /projects/beto/swong2/Alignment/.agents/claude_codex_sync.py --check
/sw/external/python/anaconda3/bin/python3.9 -c "import json;h=json.load(open('/u/swong2/.codex/hooks.json'))['hooks'];print(sum('claude_codex_sync' in json.dumps(g) for g in h.get('SessionStart',[])))"
```

1i. **No kill switch and room in the weekly window.** Expected: the listing shows no `DISABLED` file, and the weekly
reading is well below the 76% hold.

```
! ls /u/swong2/.claude/research-session/
/u/swong2/.local/bin/research-session usage-check
```

## Step 2. Start, claim, register and time the gate (Claude)

2a. **Start.** In a terminal, change to DC main and run the command below. Your first prompt is: "Follow
docs/research/pilot-hooks/START.md and docs/research/autoresearch-workflow/pilot-checklist.md, from step 2b."

```
claude --settings ~/.claude/profiles/research.json
```

Expected (H-a): the session's start context, which you see in the transcript view (`ctrl+o`) or by asking the
session to quote it, reads like "research-session: session claude-XXXXXXXX. Direction: none; not registered. This
session gets only the cap and stale gates, no checkpoints. To get checkpoints, run `research-session register
<slug>`. Usage: five-hour not applicable, seven-day N%, Fable M%, weekly max K%." It is at most 600 characters.

2b. **Claim on main.** The session runs the commands below in DC main, then commits `docs/research/directions.json`,
`DIRECTIONS.md` and `SESSIONS.md` on main by explicit file list. Expected: the claim names the session tag, and
SESSIONS.md shows one row for that tag with `pilot-hooks`.

```
/u/swong2/.local/bin/research-session claim pilot-hooks
/u/swong2/.local/bin/research-session render
```

2c. **Worktree.** The session creates branch `pilot-hooks` and the pilot worktree with its EnterWorktree tool, name
`pilot-hooks`. Expected: the session's working directory is the pilot worktree.

2d. **Register.** Expected: the output says "registered session claude-XXXXXXXX to direction pilot-hooks", gives
checkpoint 1 at +16 points with cadence 16, and its `state.json:` line names the pilot directory's `state.json`
with "written". A path in DC main instead of the pilot worktree is a fail.

```
/u/swong2/.local/bin/research-session register pilot-hooks
/u/swong2/.local/bin/research-session status
```

`status` should show "direction: pilot-hooks (registered ...)", "freeze: none" and "compactions: 0".

2e. **Time one gate call on Lustre (H-d allow path).** Expected: the reading line, "note: five-hour limit not
applicable", and a `real` time well under the 20-second PreToolUse timeout. A refresh can take up to the 8-second
fetch bound. A gate that times out fails open, so a slow time is a finding, not a block. Record the `real` value.

```
/usr/bin/time -p /u/swong2/.local/bin/research-session usage-check
```

## Step 3. A spawn without a model (Claude)

3a. **Spawn.** The session calls the Agent tool with `subagent_type` general-purpose, no `model` parameter, and this
prompt: "Write docs/research/pilot-hooks/reports/03-handback.md in the current worktree with the five hand-back
headings, saying only that this was the model-default test, then reply with one line naming the model you run on."
Expected (H-d): the spawn is allowed.

3b. **H-e.** Expected: right after the spawn returns, the session receives context like "research-session after
spawn: Usage: five-hour not applicable, seven-day N%, Fable M%, weekly max K%. Session points +P since register.
Freeze: none. Next checkpoint 1 at +16 points since register (now +P)." If the Fable row is more than 5 points above
all-models, a Fable-gap notice follows.

3c. **H-h.** Expected: the subagent's transcript holds the injected rules. The command prints 1 or more.

```
grep -c "research-session rules for this agent" /u/swong2/.claude/projects/-projects-beto-swong2-Alignment-Deception-Circuit--claude-worktrees-pilot-hooks/<session id>/subagents/agent-<agent id>.jsonl
```

3d. **The model default.** Run `audit-scan` on the main transcript and the subagent folder. Expected: the agent's
`meta_model` is `opus` or `claude-opus-5-5`, not `claude-fable-5-1`. The main agent's `agent_calls_without_model`
lists exactly this spawn, which is correct, because the spawn omitted the model on purpose.

```
/u/swong2/.local/bin/research-session audit-scan /u/swong2/.claude/projects/-projects-beto-swong2-Alignment-Deception-Circuit/<session id>.jsonl /u/swong2/.claude/projects/-projects-beto-swong2-Alignment-Deception-Circuit--claude-worktrees-pilot-hooks/<session id>/subagents
```

3e. **H-i, saved message.** Expected: `handbacks/general-purpose-<agent id>.md` exists in the pilot directory and
starts with "# Last message of general-purpose". The agent was not blocked, because it wrote a hand-back file.

## Step 4. Freeze drill (Claude)

This drill needs the weekly reading to rise by at least 1 point after registration, which costs about 1% of the
weekly limit. Do ordinary reading work between the steps, such as reading the spec, until it rises.

4a. **The model cannot change the cadence (H-d self-acknowledgement guard).** Ask the session to run the command
below. Expected: denied with "Denied: only a human may acknowledge a checkpoint, change the cadence, or touch the
session files or the kill switch (R7)."

```
/u/swong2/.local/bin/research-session set-cadence 1
```

4b. **You can (R7: `!` commands skip the hooks).** Type the command below. Expected: "cadence for session
claude-XXXXXXXX set to 1 points; next checkpoint 1 at +1 points since register".

```
! research-session set-cadence 1
```

4c. **A worker before the freeze.** The session spawns one named worker with `model: "opus"` and name
`pilot-worker`. The prompt: "Read the twelve ticket files under docs/research/autoresearch-workflow/issues/ one at a
time and, after each, append one sentence about it to docs/research/pilot-hooks/reports/04-handback.md. When you
receive a message that starts with HOLD, finish the sentence in flight, complete the hand-back headings, send the
message 'continue' to main with SendMessage, and stop." Expected: the spawn is allowed.

4d. **Crossing.** The session keeps reading until `research-session status` shows "+1" or more points since
register. Expected: at the next gated call, `status` shows "freeze: checkpoint 1, stage crossed".

4e. **Spawns and Slurm are held (H-d).** The session tries one Agent spawn and the Bash command below. Expected: both
are denied with "Checkpoint 1 crossed (+N points since register). New agents and sbatch are held. Finish the step in
flight, run `research-session worklog-append <dir> --kind checkpoint --checkpoint 1`, send HOLD to running workers,
and end the turn." The Slurm command never runs.

```
sbatch --test-only --time=00:01:00 --wrap=true
```

4f. **HOLD passes.** The session sends "HOLD: checkpoint 1; finish and stop" to `pilot-worker`. Expected: the
message is allowed. The worker finishes its sentence, writes its hand-back, sends "continue" to main and stops. Its
last message lands in `handbacks/` (H-i), and it is not blocked, because it wrote a hand-back file.

4g. **H-j.** After the worker has stopped, ask the session to end its turn without recording the checkpoint.
Expected: the Stop hook adds "research-session: checkpoint 1 crossed and is not recorded yet. Before ending the
turn, run `research-session worklog-append ... --kind checkpoint --checkpoint 1 ...`", and the session takes one more
step. On its next stop the reminder does not repeat. If a background task is still running, the reminder stays
silent by design; record that and repeat once nothing runs.

4h. **Recording.** The session runs the command below. Expected: the WORKLOG gains a checkpoint block and `status`
shows "stage recorded".

```
/u/swong2/.local/bin/research-session worklog-append /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/pilot-hooks/docs/research/pilot-hooks --kind checkpoint --checkpoint 1 --body "Freeze drill." --plan "Finish the pilot checklist."
```

4i. **Messages are held (H-d, stage recorded).** The session sends "status?" to `pilot-worker`. Expected: denied with
"Checkpoint 1 is recorded and waits for the user. Only messages that start with HOLD, or messages to main, may go
out now." The session then ends its turn and makes no further tool calls while it waits; it does not poll.

4j. **A question does not lift the freeze (H-g).** You ask "What is the freeze state?". Expected: the session gets
"Freeze holds; answer questions only. Checkpoint 1 waits for the user's `continue` or `! research-session
usage-ack`; start no new work." It answers, and `status` still shows the freeze.

4k. **A teammate's "continue" does not lift it (H-g).** The worker's "continue" from step 4f arrives in a
`<teammate-message` envelope. Expected: no acknowledgement; `status` still shows the freeze.

4l. **Another session's "continue" does not lift it (H-g).** In a second terminal, start a plain `claude` in the
Alignment checkout and ask it to send the message "continue" to the pilot session with SendMessage (find the name
with ListAgents). Expected: it arrives in a `<cross-session-message` envelope, and `status` still shows the freeze.

4m. **Your own "continue" lifts it (H-g).** You type "continue". Expected: the session gets "research-session: the
user acknowledged checkpoint 1 with `continue`. New agents and sbatch are allowed again", and `status` shows "freeze:
none; acked through checkpoint 1".

4n. **Restore the cadence.** Expected: "set to 16 points".

```
! research-session set-cadence 16
```

## Step 5. Compaction drill (Claude)

5a. **Compact.** You type `/compact`. Expected:

- H-c: `handbacks/compaction-1.md` exists in the pilot directory and starts with "# Compaction 1 summary (manual,".
- H-b: the session gets "research-session: compaction #1 recorded for session claude-XXXXXXXX. Write a 'Resumed
  after compaction #1' worklog entry; do not restart finished work.", followed by the RESUME and WORKLOG paths with
  their lint results.
- `research-session status` shows "compactions: 1". The `compactions` count in the pilot `state.json` is also 1.

5b. **Resume entry.** The session runs the command below. Expected: the WORKLOG Log gains a "Resumed after
compaction #1" entry.

```
/u/swong2/.local/bin/research-session worklog-append /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/pilot-hooks/docs/research/pilot-hooks --kind compaction --body "Resumed the pilot at step 6."
```

## Step 6. Lint drills (Claude)

6a. **A glued paragraph is refused before it lands (H-d, R30).** The session records the hash, tries an Edit that
appends the paragraph below to the pilot `WORKLOG.md`, then records the hash again. Expected: the Edit is denied with
"Write refused by the text lint (R30) for WORKLOG.md. Fix and retry:" followed by the failing line and rule, and the
two hashes are equal.

```
sha256sum /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/pilot-hooks/docs/research/pilot-hooks/WORKLOG.md
```

The glued paragraph to try:

```
Lead8unchanged ratio3holds check2passed gate4closed seed7stable after the rerun.
```

6b. **Advice after an edit (H-f).** The session appends the same glued line to the pilot `RESUME.md` through Bash,
which the write lint does not see, and then makes a clean Edit elsewhere in `RESUME.md`. Expected: after the clean
Edit, the session gets "Lint advice (the write already happened and is not undone): problems outside the text you
just wrote in RESUME.md:" naming the planted line. The session then removes the planted line with an Edit, and the
lint passes.

```
printf '%s\n' 'Lead8unchanged ratio3holds check2passed gate4closed seed7stable' >> /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/pilot-hooks/docs/research/pilot-hooks/RESUME.md
/u/swong2/.local/bin/research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/pilot-hooks/docs/research/pilot-hooks/RESUME.md
```

## Step 7. Hand-back capture (Claude)

7a. **A saved last message.** Steps 3e and 4f already show it. Expected: one file per agent under `handbacks/`,
named `<agent type>-<agent id>.md`.

7b. **A missing hand-back is blocked once (H-i).** The session spawns a general-purpose agent with `model: "opus"`
and the prompt "Reply with the single word done. Do not write any file." Expected: at its first stop the agent is
blocked once with "No hand-back file changed under <dir> since you started ... This reminder is sent once." It then
writes a hand-back or stops, and it is never blocked a second time. Check that the reminder appears exactly once:

```
grep -c "This reminder is sent once" /u/swong2/.claude/projects/-projects-beto-swong2-Alignment-Deception-Circuit--claude-worktrees-pilot-hooks/<session id>/subagents/agent-<agent id>.jsonl
```

Expected: 1. The agent's record in the pilot `state.json` shows `stop_blocks` 1.

## Step 8. Staleness of the usage file (Claude)

The status line refreshes `usage.json` only while an interactive Claude terminal is open. A background session has
no status line, so its reading goes stale, and research-session must refresh it itself (R8).

8a. In a background Claude session in the Alignment checkout, make no tool call for 20 minutes, then run the first
command. Expected: the freshness line says stale with an age of at least 15 minutes, and "refresh: not attempted
(--no-refresh)". If an interactive terminal kept the file fresh, the line says fresh; record that, close the other
terminals and repeat.

```
/u/swong2/.local/bin/research-session usage-check --no-refresh
/u/swong2/.local/bin/research-session usage-check
```

8b. Then run the second command. Expected: "refresh: fetched from the usage endpoint" or "merged from the cache", and
the freshness line says fresh. Record which one happened and the age before the refresh.

8c. **The stale override.** Run `! research-session usage-ack --stale-ok 30` only if a refresh failure happens on its
own during the pilot. Otherwise record "override not exercised in the pilot; covered by ticket 02's mocked tests".

## Step 9. Opus window test (costs weekly usage; you choose when)

The question is whether `modelSettings.claude-opus-5-5.autoCompactWindow = 600000` reaches subagents. Opus
subagents compacted at about 370k tokens before the setting existed. On 31 October 2026, after the setting was added,
one Opus planner subagent of the `autoresearch-workflow` session compacted at 469,658 tokens. That is above the old
pattern but below the pass mark, and one large read can overshoot the threshold, so it does not settle the question.

**Estimate.** One Opus agent that reads to about 600k tokens. This is a guess, not a measurement: about 3 to 8 points
of the weekly all-models reading. Run it only when the weekly reading plus 8 points stays below the 76% hold. Record
`usage-check` before and after, which gives the real cost.

9a. **Spawn.** The session spawns one general-purpose agent with `model: "opus"` and this prompt: "Read in full,
with the Read tool, every Markdown file under docs/research/mechanism-datasets/scratch-copy/,
docs/research/mechanism-analysis/scratch-copy/, docs/research/component-analysis/scratch-copy/ and
docs/research/format-control/scratch-copy/, one file at a time. After each file, append one sentence about it to
docs/research/pilot-hooks/reports/09-handback.md. Stop after all files." These copies hold about 2.9 MB of
Markdown, roughly 700k tokens.

9b. **Read the first compaction.** Expected: the agent's `first_compaction_preTokens` is at least 550000, which is a
pass. Below 550000 is a fail: the per-model window does not reach subagents, and briefs stay under 350k tokens (R20).

```
/u/swong2/.local/bin/research-session audit-scan /u/swong2/.claude/projects/-projects-beto-swong2-Alignment-Deception-Circuit--claude-worktrees-pilot-hooks/<session id>/subagents/agent-<agent id>.jsonl
```

9c. **Does a subagent compaction fire SessionStart(compact)?** Compare `compactions` in `research-session status`
before and after the agent's compaction. Expected: unchanged. If it rises, SessionStart(compact) fires for subagent
compactions, and the session count mixes them in; record it as a finding for the hook.

## Step 10. Codex (needs step 1f, and step 1d for the Sol default)

Repeat steps 2 to 7 in a Codex session started with a plain `codex` in the pilot worktree. Codex has no profiles
from this feature. These differences are expected:

- H-c and H-j are not installed for Codex, so no `compaction-<N>.md` appears and no Stop reminder fires.
- The Codex freeze denies spawns and `sbatch` only, because Codex documents no message tool (R32). There is no HOLD
  or message check, and no teammate envelope.
- The Codex cadence is 25 points, and the reading comes from `codex-usage` through `research-session usage-check
  --tool codex`.
- Run the human-only commands from a separate terminal with the Codex tag, for example
  `research-session set-cadence 1 --session codex-XXXXXXXX`.
- The Claude pilot session has the same working directory, so a bare `register` or `status` could pick the wrong
  session. Every RS command in this step passes `--session codex-XXXXXXXX`, using the tag from step 10a.

10a. **H-a.** Start `codex` in the pilot worktree and ask it to quote its session start context. Expected: the text
names the session `codex-XXXXXXXX`, says it is not registered, and gives the register command and the reading.

10b. **Register and time.** Run the commands below. Expected: the register output names `codex-XXXXXXXX` and the
pilot `state.json`, `status` shows that tag registered to `pilot-hooks`, and the reading line gives the Codex weekly
value with a `real` time well under 20 seconds.

```
/u/swong2/.local/bin/research-session register pilot-hooks --session codex-XXXXXXXX
/u/swong2/.local/bin/research-session status --session codex-XXXXXXXX
/usr/bin/time -p /u/swong2/.local/bin/research-session usage-check --tool codex
```

10c. **Spawn without a model (H-d, H-e, H-h).** Ask Codex to spawn one worker without naming a model. Expected: the
spawn is allowed; the worker receives the hand-back rules; and the orchestrator sees the after-spawn usage context.
That context is schema-verified only, so record whether Codex really shows it. With wave C applied, the worker runs
on `gpt-6.1-sol`; without it, the worker inherits the parent's model. `audit-scan` on the rollout lists this spawn
under `agent_calls_without_model`.

10d. **Freeze (H-d, H-g).** With the cadence at 1, after the reading rises, a spawn and the `sbatch --test-only`
command are denied. A question does not lift the freeze, and your own "continue" does. Restore the cadence to 25.

10e. **Compaction (H-b).** Type `/compact`. Expected: the compaction context with the RESUME and WORKLOG paths, and
`compactions` 1 for the Codex tag in `research-session status --session codex-XXXXXXXX`.

10f. **Lint (H-d, H-f).** Ask Codex to add the glued paragraph of step 6a to the pilot `WORKLOG.md` with
`apply_patch`. Expected: denied with the lint reason. If Codex makes the edit through a shell command instead, it is
not linted before the write; that is the documented gap, so record which route it took and run `research-session
lint` on the file. A clean `apply_patch` update after a planted line should give the lint advice of step 6b.

10g. **Hand-back (H-i).** Ask Codex to spawn one worker with the step 7b prompt, "Reply with the single word done.
Do not write any file." Expected: each worker's last message is saved under `handbacks/`, and this worker is blocked
once at its first stop and never again.

## Step 11. Profiles

11a. **Profile contents.** Expected, by spec §5.7: every profile turns on superpowers, mattpocock-skills,
code-review, github and claude-md-management. The research profile adds nnsight, writing adds academic-research-skills
and academic-writing-agents, audit adds session-report, and synthesis adds nothing.

```
/sw/external/python/anaconda3/bin/python3.9 -c "import json,glob;[print(p.split('/')[-1], sorted(k.split('@')[0] for k,v in json.load(open(p))['enabledPlugins'].items() if v)) for p in sorted(glob.glob('/u/swong2/.claude/profiles/*.json'))]"
```

11b. **Live sessions.** In a plain `claude`, `/plugin` shows only the five default plugins on, and `/mcp` does not
list jcodemunch. In `claude --settings ~/.claude/profiles/writing.json`, `/plugin` also shows the two academic plugins
on.

11c. **Codex, after wave C, one bridge run and a Codex restart.** Expected: the shinka and weco skills are absent from
the Codex skill list, and `codex mcp list` reports jcodemunch disabled.

## Step 12. Audit the pilot transcripts

12a. **Claude.** Expected: under `state`, the pilot session's tag has `"match": true`, and `totals.main_compactions`
equals the `compactions` count in `status`. `agent_calls_without_model` lists only the step 3 spawn. Each denial of
steps 4a, 4e, 4i and 6a appears under `denials` or as a `tool_errors` entry. Record which, because hook denials were
not in the transcripts inspected for ticket 11.

```
/u/swong2/.local/bin/research-session audit-scan /u/swong2/.claude/projects/-projects-beto-swong2-Alignment-Deception-Circuit/<session id>.jsonl /u/swong2/.claude/projects/-projects-beto-swong2-Alignment-Deception-Circuit--claude-worktrees-pilot-hooks/<session id>/subagents --state /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/pilot-hooks/docs/research/pilot-hooks/state.json
```

12b. **Codex.** Run `audit-scan` on the Codex rollout under `/u/swong2/.codex/sessions/2026/` with the same `--state`.
Expected: the Codex tag has `"match": true`, and `codex_compacted` equals its `compactions` count.

12c. **Close the pilot.** The session writes `reports/01-observations.md` from the table below, then runs
`research-session release pilot-hooks --status done`, and the orchestrator commits the pilot directory.

## Step 13. Next

Start the first real synthesis session from DC main with `claude --settings ~/.claude/profiles/synthesis.json`. Its
first prompt is "Follow /projects/beto/swong2/Alignment/docs/agents/synthesis-session.md." Expected: it orients from
`INDEX.md`, `FINDINGS.md` and `SESSIONS.md`, and it adds only `proposed` rows.

## Observation table

| Step | Expected | Observed | Pass or fail | Notes |
|---|---|---|---|---|
| 1a | Smoke test passes from the installed hooks | | | |
| 1b | `audit-scan --help` works; installed tests pass in both environments | | | |
| 1c | Branch merged; wave B applied; verify reports no change | | | |
| 1d | Wave C applied after the user's go, or noted as pending | | | |
| 1e | session-report installed; user default prints False | | | |
| 1f | Codex `/hooks` shows the six groups trusted | | | |
| 1g | Four profile files present | | | |
| 1h | Bridge check clean; bridge hook count at least 1 | | | |
| 1i | No kill switch; weekly reading well below 76% | | | |
| 2a | H-a context names the tag, the register command and the reading | | | |
| 2b | Claim committed on main; SESSIONS.md row present | | | |
| 2c | Session pinned to the pilot worktree | | | |
| 2d | Registered; mirror written to the pilot `state.json` | | | |
| 2e | `usage-check` real time well under 20 s | | | |
| 3a | Spawn without a model allowed | | | |
| 3b | H-e context after the spawn | | | |
| 3c | H-h rules in the subagent transcript | | | |
| 3d | Meta model is Opus; the spawn listed without a model | | | |
| 3e | Last message saved under `handbacks/`; no block | | | |
| 4a | Model-issued `set-cadence` denied | | | |
| 4b | User `!` command sets cadence 1 | | | |
| 4c | Worker spawned before the freeze | | | |
| 4d | Freeze stage crossed after one point | | | |
| 4e | Agent and `sbatch --test-only` denied | | | |
| 4f | HOLD allowed; worker writes hand-back and stops | | | |
| 4g | H-j reminder once, then silent | | | |
| 4h | Checkpoint block written; stage recorded | | | |
| 4i | Normal SendMessage denied; turn ends without polling | | | |
| 4j | Question gets "Freeze holds"; freeze stays | | | |
| 4k | Teammate "continue" does not ack | | | |
| 4l | Cross-session "continue" does not ack | | | |
| 4m | User "continue" acks checkpoint 1 | | | |
| 4n | Cadence restored to 16 | | | |
| 5a | H-c file, H-b context, compactions 1 | | | |
| 5b | Resume entry in the WORKLOG | | | |
| 6a | Glued Edit denied; WORKLOG hash unchanged | | | |
| 6b | H-f advice names the planted line; lint clean after removal | | | |
| 7a | One saved message per agent | | | |
| 7b | Agent without hand-back blocked exactly once | | | |
| 8a | Stale age recorded with `--no-refresh` | | | |
| 8b | Refresh fetched or merged from cache | | | |
| 8c | Stale override exercised or recorded as not exercised | | | |
| 9a | Long-read Opus agent spawned; usage before recorded | | | |
| 9b | First compaction at 550000 tokens or more | | | |
| 9c | Session compactions unchanged by the subagent compaction | | | |
| 10a | Codex H-a context | | | |
| 10b | Codex register and timed reading | | | |
| 10c | Codex spawn allowed; context shown or not; worker model | | | |
| 10d | Codex freeze denies spawn and sbatch; user "continue" acks | | | |
| 10e | Codex compaction counted | | | |
| 10f | Codex lint route recorded | | | |
| 10g | Codex hand-back capture and single block | | | |
| 11a | Profile contents match spec §5.7 | | | |
| 11b | Plugins and servers as expected in live sessions | | | |
| 11c | Codex skills and jcodemunch off after wave C | | | |
| 12a | `audit-scan` state match; denials located | | | |
| 12b | Codex `audit-scan` state match | | | |
| 12c | Observations written; direction released | | | |
| 13 | Synthesis session started from its protocol | | | |
