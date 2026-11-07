# Diagnostic transport 254 revision 3 hand-back

Status: handed-back

## What changed

Created the separate unbound `diagnostic-transport254-r3` packet under the specificity-ladder worktree's `.superpowers/sdd/plan-a3/`. The declared cgroup bind targets alone are checked using effective `statvfs` flags: root and memory for v1, root for v2. Raw cgroup mountinfo remains in the receipt. Unrelated writable controllers no longer cause rejection; writable declared targets still reject. Host and launcher paths point to r3. Revision 2 remains unchanged.

Independent review 256 r2 found B2 and B3 addressed, but B1 blocked on the actual container's unrelated writable controllers. This revision applies its minimum correction. The r3 execution manifest SHA-256 is `ded29ff237b436215d80db6408a878d513b79ffbb0ba7c4ba10fd2c7b391ba2a`; `r3.diff` records the changes. The input template and 1,126-file, eight-alias inventory match r2 byte for byte.

## How verified

The extra writable controller regression failed before the correction, recorded in `red-base.log`. The original eight tests and nine regression tests pass on both supported interpreters, with raw output in `test-results.log`. The tests cover independent writable rejection for each declared target and preservation of raw mount lines. Launcher syntax and byte comparisons passed.

## Execution evidence

Local focused tests only; no scheduler job, scientific rows, baseline reproduction, or scientific `run_manifest.json` applies. Both supported interpreter runs exited zero. The execution manifest seals four files; it is not a scientific result or operational authorization.

## What is NOT done

No actual host Python 3.6 check, container check, deployment, native suite, scheduler operation, or independent r3 review was performed. The diagnostics remain partial and confer no GREEN, GPU, or scientific authority.

## Open questions

The coordinator should independently review r3, repeat the actual host and container checks, and establish the held job, config, source, environment, and alias bindings before any execution.
