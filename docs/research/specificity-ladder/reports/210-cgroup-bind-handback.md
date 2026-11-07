# Diagnostic cgroup bind successor

Status: handed-back

## What changed

Created the distinct `preflight-r4` packet under the specificity-ladder worktree's `.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/`. Its v1 selector binds `/sys/fs/cgroup` to the same path with `:ro`; v2 retains that binding. Packet and evidence paths now name r4. Actual controller selection, job membership and frozen worker samefile checks, failure capture, output ownership, and allocation validation are unchanged. The r3 packet and its failure evidence remain historical. The manifest SHA-256 is `bf8beb34fe2db3d64a40c71a8fa85ec7de8305971073d602f4ff49ece7f39a81`.

## How verified

The modified selector assertion first failed against the copied r3 implementation on the v1 path. Both supported Python environments then ran the focused `test_preflight` and `test_bind_failures` unittest modules: 9 tests passed in each. The copied spool-wrapper test checks the r4 absolute path, and shell syntax and manifest contents passed. No broader suite was run, per the bounded diagnostic assignment.

## Execution evidence

No job, remote execution, graph, or model was run for r4. The prior Bridges job 50311480's reported container exit 255 and missing destination motivated this successor; its raw result remains under `root-preflight-ops-r3/actual-50311480/execution/`. This handback makes no new scientific or runtime visibility claim.

## What is NOT done

Independent review and a real Bridges diagnostic remain outstanding. A read-only parent bind argument does not establish effective read-only status for a nested v1 memory mount. Inspect the captured host and container memory mount lines and actual controller membership, worker-path identity and counters before any admission. The genuine adapter and frozen worker were not changed.

## Open questions

Whether the actual container exposes the nested controller at the frozen worker path with effective read-only mount flags remains an empirical question. If it does not, stop and review a successor; do not treat this packet as proof or invent counters.
