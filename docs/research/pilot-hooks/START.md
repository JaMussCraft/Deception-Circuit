# Pilot of the research-session hooks

<!--
Starting prompt for docs/research/pilot-hooks/, written from _templates/START.md by ticket 11 of the
autoresearch-workflow feature. The user launches it after the prerequisites of the pilot checklist hold.
-->

Written Sat 31 Oct 2026 by claude-b2cb53cd (ticket 11 of autoresearch-workflow). Approved by the user when they
launch it.

1. **Goal.** Check in one short live session that the research-session hooks, the usage gate, the freeze, the
   compaction counter, the lint and the hand-back capture behave as the spec says, in Claude Code and then in Codex.
   Follow `docs/research/autoresearch-workflow/pilot-checklist.md` step by step and record what you observe.

2. **Directions.** One direction, the pilot itself, registry slug `pilot-hooks`.
   - Run the checklist steps in order and record each observation. Fallback: if a hook blocks tool calls or
     misbehaves, ask the user to create the kill switch with `! touch /u/swong2/.claude/research-session/DISABLED`,
     record the failure in the worklog with the exact error text, and stop.

3. **Why it is promising.** The hooks were tested with recorded fixtures and one smoke run, but never in a live
   session. A pilot that exercises each hook once is cheap, and every real research session will rely on them.

4. **What exists.** The spec is `docs/research/autoresearch-workflow/spec.md`. The hooks and their verified harness
   facts are in `docs/research/autoresearch-workflow/reports/06-handback.md`. The tool is installed at
   `/projects/beto/swong2/Alignment/.agents/research_session/` with the wrapper `research-session`. The session
   protocol is `docs/agents/research-session.md` in the Alignment repository. Start from DC main after the merge.

5. **Do not redo.** Do not rerun the unit tests of the research-session package, the apply tool or the smoke test;
   they passed before the hooks were installed. Do not edit hook settings; the orchestrator owns them.

6. **Do not touch.** Every other direction in `docs/research/SESSIONS.md`, in particular the `sdr-*` and
   `selective-deception` directions of the live Codex session. Write only under `docs/research/pilot-hooks/`, and
   only through the commands the checklist names.

7. **Budgets.** GPU: zero. No Slurm job runs; the only Slurm command is `sbatch --test-only`, which the gate should
   deny during the freeze drill. OpenRouter: zero dollars. Usage: pause at 80% of the weekly reading, which is the
   larger of the all-models row and the Fable row. The five-hour limit no longer exists on this account, so the
   tool reports it as not applicable. The Opus window test in step 9 is the one step that costs noticeable weekly
   usage; the user decides when it runs.

8. **Oversight.** For the freeze drill the user sets the cadence to 1 point with `research-session set-cadence 1`
   and restores it afterwards (16 points on Claude, 25 on Codex). A checkpoint is a freeze: no new agents, no Slurm
   commands and no messages to workers except HOLD until the user replies "continue". Stall alarm at 60 minutes
   without progress.

9. **Always ask before.** The Opus window test, any change to settings or hooks, merging to main, and raising any
   cap. Never run a real Slurm submission.

10. **Exit criteria.** Done when every row of the observation table has an observed value and a pass or fail mark.
    Stop at once if a hook blocks ordinary tool calls; the kill switch above is the remedy.

11. **Files.** Directory `docs/research/pilot-hooks/` in Deception-Circuit. `WORKLOG.md` is the human log, written
    only through `research-session worklog-append`. `RESUME.md` is the machine narrative, at most 150 lines.
    `state.json`, `worklog.json` and `ledger.json` are written only by the research-session tool. The observation
    table goes to `reports/01-observations.md`, copied from the checklist. Hand-backs go to `reports/` with the
    headings of `_templates/handback.md`.

12. **Registration.** Before branching, the orchestrator runs `research-session claim pilot-hooks` on the main
    checkout and commits the claim. Step 2 of the checklist runs `research-session register pilot-hooks` before the
    first spawn.

13. **Models.** Orchestrator: Fable. Subagents: Opus on Claude, passed explicitly as `model: "opus"`, except the
    one spawn in step 3 that omits the model on purpose to test the default. Sol on Codex.
