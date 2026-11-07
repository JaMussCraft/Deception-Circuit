# Diagnostic nested cgroup bind successor

Status: handed-back

## What changed

Created `preflight-r5` under the specificity-ladder worktree's `.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/`. For actual v1, the existing bind argument now contains the ordered comma-separated parent and memory child paths, each bound to itself with `:ro`. Actual v2 retains the root-only bind. Packet and evidence paths name r5. Controller selection, job membership, frozen worker samefile validation, output ownership, failure capture, and allocation checks are unchanged. The r4 packet and evidence remain historical. The r5 manifest SHA-256 is `889ee0c986fd392ba1cf00300d93ae46f6714cae10a58175862a3a9ba7a88db7`.

## How verified

The revised selector assertion first failed against the r4 parent-only selector because the child bind was missing. The focused `test_preflight` and `test_bind_failures` modules then passed 9 tests in each supported Python environment. The checks cover exact ordered bind text, its existing command wiring, the relocated spool wrapper, guards and observations; shell syntax and manifest contents also passed. Local Apptainer 1.5.5 help documents comma-separated bind paths but does not establish actual mount order or effective flags. No broader suite was run under this bounded assignment.

## Execution evidence

The earlier Bridges job 50311765 reported completed with host and container exits zero. Its captured container memory mount line shows a writable per-mount flag despite the parent read-only bind; its raw receipt is under `root-preflight-ops-r4/actual-50311765/execution/`. No job, container, graph, model, or remote execution was run for r5. This handback makes no new runtime visibility or read-only claim.

## What is NOT done

Independent review and a separate real Bridges diagnostic remain outstanding. No genuine adapter or frozen worker was changed. The actual container memory mount flags, membership, samefile identity and counters must be inspected before admission.

## Open questions

Whether Apptainer applies the ordered nested binds so the real container exposes the exact worker path with an effectively read-only memory mount remains empirical. If that check fails, stop for review rather than treat this packet as proof.
