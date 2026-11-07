# Cgroup parent-bind diagnostic independent review

Status: handed-back. Exact r4 accepted for one root-bound diagnostic only.

## What changed

Created only reviewer-owned review211 evidence and this handback. No author packet, genuine adapter, scientific source, authority, scheduler or remote changes. [Scoped verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-cgroup-bind-review211/verdict.json) accepts diagnostic manifest `bf8beb34fe2db3d64a40c71a8fa85ec7de8305971073d602f4ff49ece7f39a81`.

## How verified

All eight r4 manifest members match. After mechanical successor-path substitutions, the sole production delta is the v1 bind selector requesting the existing parent destination `/sys/fs/cgroup:/sys/fs/cgroup:ro`. The v2 request is unchanged. The actual counter reader and allocation helper are byte-identical to r3. The exact native v1 memory subtree, job-component and samefile checks, fresh-output guards, and raw membership/mountinfo/counter/error capture remain unchanged. Host Python 3.6 grammar/API scan and shell syntax pass; an actual Python 3.6 runtime was not tested locally.

The requested `ro` option matches [Apptainer bind syntax](https://apptainer.org/docs/user/main/bind_paths_and_mounts.html). Current [upstream user-bind source](https://github.com/apptainer/apptainer/blob/main/internal/pkg/runtime/engine/apptainer/container_linux.go) uses recursive bind flags and a readonly flag/remount request. Neither establishes the installed Bridges version or effective readonly status of its nested v1 memory mount. Actual diagnostic mount evidence remains required.

## Execution evidence

All eight fetched files from actual job `50311480` independently match the root receipt. The job failed after five seconds with exit `2:0`: host own-job counters were visible, but container exit `255` reported an absent `/sys/fs/cgroup/memory` destination before Python. This is preserved failure evidence, not corrected visibility.

Nine diagnostic cases passed in base and mgnp, against nine expected per environment. Four independent cases passed in each, against four expected, including exact-delta/manifest checks, unchanged native leaf behavior, wrong-job rejection, v2 preservation and a semantic old-selector mismatch. All four runs exited zero; no skips/errors. [Commands and counts](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-cgroup-bind-review211/run_manifest.json). No genuine graph, model or remote mount ran. Last live usage was eighteen percent, below checkpoint thirty-three and ordinary cap eighty.

## What is NOT done

No actual r4 job, corrected container visibility, effective readonly nested-controller observation, genuine proof, resource bound, transfer closure or GPU admission. The existing accepted proof-adapter-r2 bytes and original r3-pinned binding gate remain unchanged; this diagnostic acceptance does not silently substitute r4 evidence into that gate.

## Open questions

Root may stage and bind the exact r4 packet for one separately authorized diagnostic under unchanged five-minute CPU limits and fresh `root-cgroup199-r4/execution`. On completion, inspect actual command, terminal accounting, host/container own-job membership, unchanged native path, samefile checks, required counters and raw mountinfo. For readonly status, inspect per-mount options before the mountinfo separator; superblock `rw,memory` after it is a different field. Missing, ambiguous or unexpected evidence must be preserved and resolved before genuine-proof use. Any genuine adapter successor needs a distinct exact review and all original external gates.
