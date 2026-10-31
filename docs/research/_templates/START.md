# Starting prompt: <direction slug>

<!--
Template for docs/research/<slug>/START.md. A synthesis session writes one per proposed research session; the user
launches the research session with it. Follow docs/agents/research-session.md in the Alignment repository for the
protocol. Keep the numbered items; the full agent version may add evidence and cost tables under the same numbers.
-->

Written <Sat 31 Oct 2026> by <synthesis session tag>. Approved by the user on <date>.

1. **Goal.** <One sentence that states the research question in plain words.>

2. **Directions.** <Two to four mid-level directions. Each one is deliberately open about method, and each has a
   fallback for when it is blocked.>
   - <Direction 1, plain name and registry slug.> Fallback: <what to do instead if it is blocked or fails its gate>.
   - <Direction 2.> Fallback: <...>.

3. **Why it is promising.** <Two or three sentences: the gap, what already exists, and what result would change the
   plan.>

4. **What exists.** <Paths to prior findings by F number, code, data and outputs. The branch or worktree to start
   from.>

5. **Do not redo.** <Closed protocols, failed gates and explored null results, each with its path.>

6. **Do not touch.** <Directions and files claimed by other sessions, copied from SESSIONS.md on the date above.>

7. **Budgets.** GPU: <N> reserved GPU-hours per cluster, at most <K> concurrent GPU jobs. OpenRouter: $<N>. Usage:
   pause at 80% of the five-hour window or 80% of the weekly reading. Reserve walltime at the observed runtime plus a
   reasonable buffer; record reserved and actual hours in the ledger.

8. **Oversight.** Review checkpoint every <16> session points of weekly usage on Claude (25 on Codex). A checkpoint
   is a freeze: no new agents, no new Slurm jobs and no messages to workers except HOLD until you reply "continue".
   Stall alarm at 60 minutes without progress. Milestone trigger: any direction that passes or fails its
   pre-registered gate gets a worklog entry, and a checkpoint if it changes the plan.

9. **Always ask before.** Merging to main, any EVAL 5 run (the full five-suite benchmark evaluation), dropping a
   direction, and raising any cap.

10. **Exit criteria.** <For each direction, what "done" and what "stop" look like, including the pre-registered pass
    and fail rule and the frozen grader hash if benchmark evaluations run.>

11. **Files.** Directory `docs/research/<slug>/` in Deception-Circuit. `WORKLOG.md` is the human log, written only
    through `research-session worklog-append`. `RESUME.md` is the machine narrative, at most 150 lines. `state.json`,
    `worklog.json` and `ledger.json` are written only by the research-session tool. Hand-backs go to `reports/` with
    the headings of `_templates/handback.md`.

12. **Registration.** Before branching, the orchestrator runs `research-session claim <slug>` on the main checkout
    and commits the claim. Before its first spawn it runs `research-session register <slug>`; only a registered
    session gets checkpoints.

13. **Models.** Orchestrator: <Fable>. Subagents: Opus on Claude, passed explicitly as `model: "opus"` on every
    spawn; Sol on Codex. When the Fable weekly row is more than 5 points above the all-models row, reading, analysis
    and review go to Opus agents.
