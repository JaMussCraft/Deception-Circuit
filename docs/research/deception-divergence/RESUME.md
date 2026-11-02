# Resume: deception-divergence

<!--
Template for docs/research/<slug>/RESUME.md. This is the machine narrative state of the direction: what a fresh
orchestrator needs in order to continue after a compaction or a new session. It is overwritten, not appended, and
stays under 150 lines. Keep the six headings below, in this order. Write full sentences with normal spacing.
Counters (compactions, checkpoints, usage) live in state.json and are never copied here. RESUME never summarizes the
worklog; the worklog may point here, never the other way.
-->

Last rewritten: <Sun 1 Nov 2026, 2:40 pm EST> by <claude-01a2b3c4>.

## Status

<Two to five sentences. Which direction is active, which is the fallback, and where each stands against its
pre-registered exit rule from spec.md. Name the findings by F number from FINDINGS.md.>

## Branch, worktree and commit

- Branch: `<branch name>`.
- Worktree: `<absolute worktree path>`.
- Last commit on the branch: `<short SHA>`, "<commit subject>".
- Uncommitted work, if any: <files and why they are not committed yet, or "none">.

## In-flight jobs

<One row per job that has not reached a terminal state. The same jobs are recorded with `research-session job add`,
which keeps the waiter command in state.json; this table only says what each job is for.>

| Job | Cluster | What it computes | Output directory | Expected finish |
|---|---|---|---|---|
| `<job id>` | <Delta> | <plain description> | `<outputs/... path>` | <Sun 4:00 pm EST> |

## Next action

<The single next step, stated so that a fresh orchestrator can take it without reading anything else first. Then
at most three follow-up steps, in order.>

## Do not

- <Work that is finished and must not be redone, each with the path that records it.>
- <Protocols that failed their gate, with the path.>
- <Files and directions owned by other sessions, taken from SESSIONS.md.>

## Open decisions for the user

- <Each decision waiting on the user, with its need number from the worklog and the default if no answer.>
