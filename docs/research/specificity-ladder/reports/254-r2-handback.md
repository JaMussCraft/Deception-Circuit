# Diagnostic transport 254 revision 2 hand-back

Status: handed-back

## What changed

Created the separate unbound `diagnostic-transport254-r2` packet under the specificity-ladder worktree's `.superpowers/sdd/plan-a3/`. The original packet's manifest remains SHA-256 `8df6759644ae549869a8d4d0675d20b86a0e856e2ababfb6a0f131142f1d2e0d`; the new manifest is `7ae57ad0089826888d8917e0c01da15d3d5108ff292200a8c26b99d5aeed9eea`. `r2.diff` records changes and regression tests. Effective cgroup target flags come from `statvfs`, with raw cgroup mount lines retained. A fresh allocation and deadline check follows log opening, and cleanup uses one absolute TERM/KILL window with separate primary and cleanup errors. Paths in the host and launcher point to r2.

The 1,126-file and eight-alias closure and unbound template are byte-identical to v1. Recipe revision 2 remains pinned to `96c57370c5bbc3883eab47774d85d5c38d7c27c2ee5fa1586f246e2082f2c7fb`. This remains passive diagnostic-only work; the proposal is 18 CPU, 32 GiB, 25 minutes, and two 600-second children.

## How verified

All three targeted cases failed before the fix in `red-base.log`. Afterward, the eight original checks and seven regression checks passed on each supported interpreter; raw output is `test-results.log`. The added cases include rejecting an actually writable target and retaining both errors on primary and cleanup failure. Launcher syntax passed `bash -n`; inventory and config comparison passed.

## Execution evidence

Local mocked checks only; no scheduler job, cluster run, scientific rows, baseline reproduction, or scientific `run_manifest.json` applies. Both interpreter test runs exited zero. The r2 `manifest.json` seals its four execution files; it is not a scientific run manifest or an acceptance result.

## What is NOT done

No host Python 3.6 check, container check, deployment, native suite, scheduler operation, or independent r2 review was performed. No admission or operational authority is conferred.

## Open questions

The coordinator should independently review the r2 packet and perform the previously specified actual-host, container, source closure, and deployment checks before any binding or execution. The effective mount check intentionally rejects any visible cgroup mountpoint whose actual filesystem flags are writable; raw evidence supports audit of the resulting decision.
