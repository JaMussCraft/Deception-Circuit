# Next unchanged-source native chunk

Status: proposed and UNEXECUTED. Root acceptance is required before the model fixture starts. Planning used compact saved descriptors and timing summaries; no large artifact/model read was performed while source profiling was active.

## Proposed scope

Run contiguous indices 2, 3 and 4 in a single original `pilot_cases` call. Preserve the completed indices 0 and 1. Successful completion would leave 5 authenticated cases of the original 63. There is no aggregate, follow-on chunk, replayed numeric evidence or extra standalone reauthentication pass. [Exact IDs and scope](proposal.json).

One call amortizes the fresh model/inventory/selected-axis setup. The first new case constructs its own selected numeric backing proof; subsequent cases use only the original process-local cache. Every cache hit retains reference/PID/source checks and fresh byte witnesses. No validator/cache object, prior success flag or numeric receipt is transported across processes.

## Profile comparability

All candidates retain tile size 32, physical batch size 64, padded width 4, float32, SDPA and the same requested head site/model/source identity. Only `source_task` differs within the profile. Full original descriptors and all conditions/IDs/cells remain unchanged. [Profiles](proposal.json).

| Index | Source | Cells | Batch groups | Operations |
|---|---|---:|---:|---|
| 2 | IOI | 211 | 1 | Same interchange/replay/steering mix as the measured FAR case |
| 3 | MMLU | 408 | 2 | Zero/mean patches and steering; no interchange cells |
| 4 | FAR calibration pilot | 33 | 10 | Original learned/calibration-null interchange cells |

The corresponding cell/group products are 211, 816 and 330 versus 2,110 for the measured case. These are structural workload descriptors, not timing or forward-count guarantees. MMLU retains its distinct frozen cyclic-positive donor path. The proposal takes no proportional speed credit for the smaller products. [Comparability and operation counts](proposal.json).

## Explicit cap calculation

Charge the observed older CLI setup of 583.17 seconds, even though the accepted lower-API setup actually took 406.61 seconds. Charge each new case the larger observed original-case timer, 102.63 seconds. Charge the first authentication 186.89 seconds and each subsequent authentication the measured same-process 67.55 seconds. Add a chosen publication allowance of 5 seconds per case and final-check/exit allowance of 20 seconds. [Observed-derived allowances](proposal.json).

The subtotal is 1,248.05 seconds; a 20% buffer gives 1,497.66 seconds. Round up to a **1,500-second process cap plus 15-second kill grace**. This is a bounded-trial allowance, not a measured upper bound, allocated-host cost claim or guaranteed completion duration. It retains a larger startup allowance instead of assuming the latest filesystem-cache timing repeats. [Calculation](proposal.json).

## Concrete command and dependencies

After root acceptance and the profiling contention gate is cleared:

```bash
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder
/sw/external/python/anaconda3/bin/python3.9 \
  .superpowers/sdd/plan-a3/native-continuation-plan/next-chunk-proposal/supervisor.py
```

The prepared [coordinator](coordinator.py) and [supervisor](supervisor.py) are confined to this new proposal directory. They depend on the frozen source/case catalogue in the parent plan, the exact existing scenario/design/protocol/tiny-model/selection and ancestry, the original selected inventory and preserved case directories. The coordinator rechecks source hashes and canonical full case order before execution, using original scenario and inventory reconstruction APIs. The original `pilot_cases` API still independently validates inventory, loads its own axes, executes every original numeric/control requirement, publishes durable case evidence and fully authenticates each case.

## Refusal, evidence and current state

The supervisor requires fresh output `diagnostics/next-cases2-4-01`, the same finite-ancestor headroom check and single BLAS/OMP/MKL threads as the completed step. It captures direct child exit/wall/RSS plus leaf and ancestor cgroup events/limits. Initial case children must be exactly the preserved set, all new case destinations absent and scratch empty. Any mismatch, failure or timeout stops the attempt; nothing is cleared or retried automatically.

Passive wrappers time each original native invocation and each original full case reader, call each original once and restore all adapters afterward. They record actual per-case forwards and authentication time, reject forwards during read-only authentication, and check that original case counters sum to the external count. Completed authentication events remain separate from mere byte-complete publication if a later case fails. Old references must remain unchanged; no completed whole-pilot flag is published.

Syntax and static protocol checks pass; neither coordinator nor supervisor has been imported/executed. No source/harness file, original evidence or numerical tolerance was edited. No model, GPU, job, remote access or subagent was used. [Checks](protocol-checks.json).
