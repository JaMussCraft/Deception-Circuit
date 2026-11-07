# A3 diagnostic transport independent source review

Status: handed-back. BLOCKED on three narrow transport fixes; no execution acceptance.

## What changed

Created only reviewer-owned review256 snapshots, reproductions and this handback. No source, other receipts, scheduler or remote edits. Review binds only the final frozen manifest `8df6759644ae549869a8d4d0675d20b86a0e856e2ababfb6a0f131142f1d2e0d`, superseding the initial prompt identifier. [Scoped verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport-review256/verdict.json).

## How verified

1. **B1: valid readonly mount stacks are rejected.** [inner.py](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport254/inner.py:12) tie-breaks same-path mounts by option strings, choosing `rw` over `ro`; its later loop also rejects hidden lower writable rows. Preserved successful Bridges v1 evidence has exactly such a hidden lower/readonly upper stack with actual ST_RDONLY set. The inner gate rejects before pytest despite effective readonly access. Check effective declared target paths or correctly resolved visible mount IDs, retaining raw evidence and the intended readonly guard.

2. **B2: an expired phase can still launch.** [host.py](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport254/host.py:86) opens stdout/stderr after its final allocation/clock decision. Delaying that I/O beyond the computed deadline still invokes Popen, then marks timeout afterward. Perform the final allocation/clock clamp immediately before launch after all I/O; refuse expired budget without increasing a deadline.

3. **B3: cleanup failure restarts grace.** [host.py](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport254/host.py:103) invokes cleanup again when the normal cleanup itself raises after its fifteen-plus-five-second attempt. That resets the claimed twenty-second cleanup allowance. Keep one absolute cleanup budget or avoid restarting grace after cleanup failure, preserving primary/cleanup errors and bounded KILL/reap evidence.

The four executable hashes, six diagnostic-input pins, recipe `96c57370c5bbc3883eab47774d85d5c38d7c27c2ee5fa1586f246e2082f2c7fb` and 1,120-source-plus-six-input/eight-alias inventory digest match. Original full collection, conftest, preflight and assertions remain. Child source uses only phase-private RW binds; host and previous receipts remain outside them. Remaining-time scheduler polling, immediate owned-group cleanup before post-reap query, nonincreasing End bounds and post-reap shortening are present. Host grammar and shell checks pass; actual host 3.6/container behavior remains root work.

## Execution evidence

Eight supplied tests pass in each supported interpreter, but they miss these three defects. Five independent checks pass in each: three deliberately reproduce B1-B3, while two confirm correct post-reap shortening and real local owned-group reaping after leader exit. These reproduction passes do not mean the wrapper is correct. [Checks and logs](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport-review256/run_manifest.json).

An isolated three-item pytest fixture in each environment executes one intended failing selection through normal setup/call/teardown, preserving all session items. Its failed-call JSONL is visible before teardown/process completion; pytest exit one is expected. The reviewed plugin flushes/fsyncs each event and adds no periodic traceback thread. No original/native suite or model ran here.

Raw prior job `50316975` evidence is preserved and twenty-one files rehash correctly. Its baseline gate succeeded through five expected failures, zero errors/skips and observer exit zero; these were not five passing tests. Full collection had 223 nodes, then timed out at 2,700 seconds after six F glyphs and 121 progress reports. Selected suspects are ordinals 85–88, 117 and 120; the second child probes candidate 122. Node 121 teardown remains a possible original hang site, so passing 122 would not resolve that ambiguity. Last live usage was thirty-five percent, cap eighty and cadence forty.

## What is NOT done

No diagnostic execution, actual Bridges host/container gate, source repair, accepted full suite, model/GPU or scientific admission. Config/source deployment is still unbound. The earlier ready identifier is not accepted. Diagnostic results must remain partial even if selected cases pass.

## Open questions

Commission a distinct cohesive correction for B1-B3 with their targeted regressions; preserve this frozen packet and all old evidence. No generic framework expansion is needed. Keep the pinned passive-only recipe and original assertions unless root separately revises the recipe. After source acceptance, root must verify actual 18-CPU/32-GiB/25-minute/no-GPU allocation, source/environment/alias closure, effective container mounts and owned phase namespaces. No GREEN promotion or timeout extension follows from this review.
