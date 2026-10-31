# 11 — Pilot checklist and `audit-scan`

**Status:** ready-for-agent
**Type:** task
**Blocked by:** 06, 07, 08, 10 (05, 10, 11 and 12 edit `directions.json` in that order, R38)
**Wave:** A for the `audit-scan` code; the checklist is in W.
**Estimated size:** reading about 60k tokens (spec §5, §8, R8, R20; lane 2 §6-7; lane 4 §3; the hand-backs of tickets
02, 03, 06 and 07), writing about 40k tokens.
**Hand-back:** `F/reports/11-handback.md`

## What to do

Write the checklist the user follows to pilot the setup (P5), and implement `research-session audit-scan` so the
pilot and later audits can count compactions, errors and model omissions from transcripts. Do not launch anything.

## Facts to build on

- Claude transcripts: `~/.claude/projects/<slug>/<session>.jsonl`, subagents in `<session>/subagents/agent-<id>.jsonl`
  with `.meta.json`. Compactions appear as `isCompactSummary` records and `compact_boundary` records with
  `compactMetadata.preTokens`; errors as `tool_result` with `is_error: true`; denials as `toolDenialKind` (lane 2 §7,
  lane 4 §3). Codex rollouts are under `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` with `"type": "compacted"`
  lines. Inspect key names in one real transcript with a script that prints keys only, never message text.
- Open tests to schedule: whether `modelSettings.claude-opus-5-5.autoCompactWindow = 600000` reaches subagents
  (lane 2 §6); whether background sessions keep `usage.json` fresh (R8); whether UserPromptSubmit can tell a human
  "continue" from a teammate message; whether SessionStart(compact) fires for subagent compactions.

## Scope

- Staged: `research_session/audit.py`, the `audit-scan <transcript>` subcommand, and
  `tests/test_research_session_audit.py` with synthetic transcripts. Output JSON: compactions with `preTokens` per
  agent, runs of three or more identical failing tool calls, Agent calls without `model`, Bash commands repeated
  five or more times within 30 minutes, permission denials, and Codex `compacted` counts.
- In W: `F/pilot-checklist.md`; `W/docs/research/pilot-hooks/START.md` for a trivial pilot direction (from
  `_templates/START.md`); a `proposed` row `pilot-hooks` in `W/docs/research/directions.json`.
- `S/ops/11-audit.json`.

## Checklist content (each step names the command or UI action and the expected observation)

1. Prerequisites the orchestrator confirms: waves A and H applied in that order (H only after the installed RS tests
   and the hook smoke test passed), wave B applied, DC branch merged, session-report installed, Codex `/hooks` trust
   done by the user, profiles present, `claude_codex_sync.py --check` still shows the bridge hooks intact.
2. Start `claude --settings ~/.claude/profiles/research.json` in a fresh DC worktree with the pilot START.md; see
   the H-a context and run `register pilot-hooks`. Time one gate call (`usage-check`) on Lustre and record it; a gate
   that times out fails open.
3. Spawn one agent without a model: the subagent's meta file shows Opus; H-e context appears.
4. Freeze drill: the user runs `! research-session set-cadence 1`; an Agent spawn and `sbatch --test-only` are
   denied; a `HOLD` SendMessage passes; after `worklog-append --checkpoint 1` a normal SendMessage is denied and the
   orchestrator ends its turn without polling; a worker that got `HOLD` writes its hand-back and stops; a user
   question leaves the freeze in place; a teammate message and a message from another session that say "continue"
   do not lift it; the user's own "continue" lifts it; the user restores the cadence.
5. Compaction drill: `/compact` increments `compactions` once, writes `handbacks/compaction-1.md`, and injects the
   resume instruction.
6. Lint drill: an Edit adding a glued paragraph to WORKLOG.md is denied before it lands, with the failing unit in
   the reason, and the file is unchanged afterwards (R30).
7. Hand-back capture: a subagent's last message lands in `handbacks/`; a subagent that skips its hand-back file is
   blocked once.
8. Staleness: during a 20-minute idle in a background session, record the age of `usage.json` with
   `research-session usage-check`, and whether RS refreshed it from the usage endpoint (R8). Exercise
   `usage-ack --stale-ok 30` only if a refresh failure happens on its own; otherwise record that the override was not
   exercised in the pilot (its behaviour is covered by ticket 02's mocked tests).
9. Opus window test (costs weekly usage; the checklist states an estimate and asks the user to choose when): one Opus
   subagent reads past 450k tokens; `audit-scan` on its transcript shows the first compaction's `preTokens`. Pass if
   it is at least 550k.
10. Codex: steps 2-7 in a Codex session where verified hooks exist.
11. Profiles: the plugin list in each profile matches spec §5.7.
12. Audit: run `audit-scan` on the pilot transcripts and compare its compaction count with `state.json`.
13. Next: the first real synthesis session, started from `docs/agents/synthesis-session.md`.

An observation table follows the steps with columns: step, expected, observed, pass or fail, notes.

## Acceptance criteria

- [ ] `audit-scan` tests pass in both envs on synthetic Claude and Codex transcripts covering each counted item.
- [ ] A key-only inspection of one real transcript is recorded in the hand-back, and the parser handles those keys.
- [ ] Every step of the checklist names an exact command or UI action and an expected observation; every hook
      H-a to H-j is exercised by at least one step.
- [ ] `pilot-checklist.md` and `pilot-hooks/START.md` pass the lint; `directions.json` validates.
- [ ] `apply_staged.py --staging S --only 11 --dry-run` output pasted.

## Comments
