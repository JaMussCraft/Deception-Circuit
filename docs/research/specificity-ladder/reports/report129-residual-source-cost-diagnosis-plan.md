# Residual fresh-source cost diagnosis and plan

Agent: Codex Sol. Status: handed-back. Diagnosis and proposed plan only.

## What changed

Added observational profile evidence only under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile`. Source, genuine prepared artifacts,
scientific inputs, guards, cadence, jobs, reservations and caps are unchanged. Proposed
source-only private batching plan: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/repair-plan.md`; it requires root acceptance and
a new isolated candidate before any implementation.

## How verified

One bounded fresh real context per owner, then one actual fresh source refresh per owner,
serially, with no authority substitution or model. Both completed successfully within the
recorded timeout. Source bytes/read-only status still match the immutable snapshot:
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/source-after.json`. The initial harness used a wrong worktree ancestor, so the genuine
registry guard rejected the nonexistent path; the original script, failed receipt/log and
correction remain in `attempt1-*`, `profile-before-path-correction.py` and
`procedure-correction.json` under the evidence directory. The corrected run uses the
unchanged original explicit registry.

cProfile and a read-only audit observer collect calls and open paths without replacing
source functions. Timings include profiler overhead. File volume is derived from full-read
open paths and post-run file identities; immutable witness volumes also agree exactly
with the successful sealed witness rows. Metadata figures below are Python/C function
call counts, not kernel syscall traces. Root-ancestor candidate counts are descriptive,
exclude extra target routes and do not promise the same reduction in real syscalls.
Raw: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/mask-profile.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/edge-profile.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/summary.json`, function JSON,
text call profiles and pstats files.

| Owner | Wall seconds | CPU seconds | Witness inclusive | Links inclusive | Current protection inclusive | Path.stat calls | posix.lstat calls |
|---|---|---|---|---|---|---|---|
| mask | 2.866 | 1.667 | 2.054 | 0.688 | 0.112 | 7959 | 12702 |
| edge | 2.696 | 1.526 | 1.884 | 0.693 | 0.118 | 7702 | 12528 |

Inclusive timings overlap and must not be added. Neither refresh calls inventory work.
The witness reads 355125694 logical bytes versus
323627510 physically unique bytes for mask. Its
31498184 duplicate bytes are the same interpreter
file reached through the executable/launcher bindings. Edge reads
273277323 physically unique static bytes, with no static byte
duplication. Root lexical ancestor candidates repeat 5138
versus 415 unique paths for mask, and
4977 versus 391 for edge.
These exact counts and observed per-open aliases are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/summary.json` and the raw
owner profile JSON.

The bottleneck combines full fresh witness file reads/open/close with repeated lexical
ancestry resolution. The largest individual source reads are the original A1 design
and new canonical design; neither is an inventory or model weight. Exact paths/volumes
are in the raw owner profile JSON. Pure hash CPU is only 0.306 seconds for mask
and 0.236 for edge. File open/close alone remain visible in the
profiles, alongside thousands of metadata calls. Current registry/grader work is small;
there is no evidence for registry semantic caching or inventory changes as the remedy.
Exact hash/open/close/read values: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/summary.json`.

## Execution evidence

- Classification: actual CPU source-check diagnostic; no scientific numerical verdict.
- Controls: unchanged genuine source-bound inputs, real byte/ancestry/protected/grader checks, no injected authority. All complete-artifact validation remains in the earlier raw preparation manifest.
- Exact commands, environment, start/end times, timeout, exit and raw logs: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/mask-command.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/edge-command.json` and corresponding owner logs. Procedure: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/profile-refresh.py`.
- Profile terminal marker: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/terminal.json`; both root and reviewer were notified before any large independent replay.
- Evidence hashes: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/file-manifest.json`. The proposed scanner is not implemented or benchmarked.

## What is NOT done

No source/test edit, new preparation, skipped check, TTL/stat-only proof, cross-refresh
cache, model, GPU, scheduled job, RS/git mutation, paid API, notebook or subagent.
Lease/ledger/reservation hooks remain intact and unexercised without a real authorized
allocation. No hardware, science, coverage, guard frequency or budget changes. The
profiles do not establish cap feasibility or upgrade the old held source/reservation.

## Open questions

Accept the narrow source-only batch-scanner experiment or stop with this diagnosis.
The proposed helper-local change shares fresh prefix resolution only inside one scan,
retains all byte reads, uses closing identity/provenance checks and leaves both static
provenance phases plus actual registry/grader checks intact. Tests must establish exact
witness equivalence and mid-scan invalidation before root freeze and independent review.
See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120/evidence/residual-profile/repair-plan.md`. Most static bytes are already unique, so a successful path
optimization can still leave substantial repeated source cost; full feasibility needs
fresh measured accounting and the unchanged admission gates.
