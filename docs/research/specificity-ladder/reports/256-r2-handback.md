# A3 diagnostic transport r2 independent re-review

Status: handed-back. BLOCKED: B1 NOT ADDRESSED; B2 and B3 addressed. No diagnostic release or acceptance.

## What changed

Created only reviewer-owned r2 snapshots, targeted checks, logs and verdict, preserving original256 and frozen v1/r2 production packets. Review binds manifest `7ae57ad0089826888d8917e0c01da15d3d5108ff292200a8c26b99d5aeed9eea`. [Scoped verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport-review256/r2/verdict.json).

## How verified

**B1 remains a launch blocker.** [inner.py](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport254-r2/inner.py:20) now uses effective statvfs and correctly handles hidden lower RW / visible upper RO rows. However, it unions declared paths with every cgroup submount, imposing RO on controllers the command never explicitly binds RO. The existing contract declares root plus v1 memory only. Actual root flags15 and memory4111 satisfy ST_RDONLY; other controllers4110 do not. The gate rejects before pytest. Minimum correction: restrict targets to `set(paths)`, preserving raw mountinfo and effective flags. Add a positive root/memory RO plus unrelated controller RW case, and negative cases for each declared target RW; v2 checks its declared root.

**B2 addressed:** after stdout/stderr open, fresh allocation and wall/monotonic checks clamp the existing deadline without increasing it; expired budget launches no child. **B3 addressed:** cleanup has one absolute twenty-second final bound, cleanup failure cannot restart cleanup, and primary/cleanup errors survive in separate receipt fields. Leader-exited descendants remain reaped. No further correction blocker found in these changed paths. The unchanged transport helper hashes identically; host-reachable Python 3.6 grammar parses in both local interpreters. This is a grammar check, not actual host execution.

## Execution evidence

Four executable members and the exact manifest rehash. Fresh seven targeted regressions plus four independent checks pass in each supported interpreter. The independent B1 test intentionally confirms the residual rejection, so its passing result does not mean B1 is fixed. Other checks cover writable declared root refusal, cleanup absolute bound, final delayed-log launch refusal, post-reap shortening, real local owned-group cleanup and preserved paired errors. [Raw runs](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport-review256/r2/run_manifest.json).

Read author raw evidence: eight existing plus seven targeted cases pass per interpreter; its red log records the original three failures. The original eight were not rerun here. The actual [container check](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-deployment262/container-pure-check.json) exits one before its intended eight pure tests, recording root15/memory4111 and all other controller flags4110; no inner-mounts receipt was published. Exact raw receipt hash is recorded in [pins and observations](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport-review256/r2/pins-and-observations.json). No native/full suite or job ran in this review. Latest live usage is thirty-six percent, cap eighty, cadence forty.

## What is NOT done

No production edits, remote action, scheduler action, source admission, full/native suite, model or GPU use. No actual host/container acceptance for a corrected successor, no GREEN or scientific admission. Existing failed evidence remains preserved. Root's actual deployment check is evidence of a transport rejection, not execution of the selected diagnostic cases.

## Open questions

Root should commission a distinct minimal B1 successor and retain both earlier packets. After its scoped source review, root must close actual host3.6/container behavior and exact job/config/source/environment/alias bindings. The selected runs remain DIAGNOSTIC_PARTIAL under the unchanged eighteen-CPU/thirty-two-GiB/twenty-five-minute, no-GPU proposal. No timeout extension or acceptance follows from selected-case outcomes.
