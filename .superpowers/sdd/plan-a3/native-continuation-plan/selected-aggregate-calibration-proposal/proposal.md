# Native aggregation and first calibration chunk proposal

Status: handed-back

## What changed

Prepare an unexecuted normal-CPU job for original full selected-pilot aggregation, followed only on success by the original first 32 calibration shards. All 63 authenticated case markers, original scientific counts and frozen source/harness remain preserved. Root accepted the bounded scope in principle and retains submission authority. [Exact request](proposal.json), [pinned original lineage](expectation.json).

## How verified

Only new external operational drivers changed. Aggregation and calibration call the unchanged original `run_phase` API in separate fresh processes. Original aggregation authenticates every case, checks complete case order and restores its injected replay adapter before return; old per-case numerical samples and forwards remain original evidence. New reconciliation captures, positives, guards and IO are actual newly measured work. Calibration executes original scoring and records genuine per-shard forwards, wall/guard costs and the one actual startup record, validated once after completion rather than redundantly per shard. [Coordinator](coordinator.py), [original aggregate](source-evidence/a3_direction_native_scenario--aggregate_pilot_cases.py), [original phase dispatch](source-evidence/a3_direction_native_scenario--run_phase.py).

The new allocation-reader copy accepts exactly 125 minutes on the normal CPU partition, preserving user/node/source/CPU/RAM/no-GPU checks. The original under-hour copy rejected the new positive duration case; the bounded copy passed 7 focused tests in each interpreter. Syntax compilation, shell syntax, source hashes, phase ordering and all saved case-marker hashes passed model-free checks. No native phase was executed. [Narrow reader diff](allocation-reader.diff), [red test](allocation-red-base.log), [base tests](allocation-green-base.log), [mgnp tests](allocation-green-mgnp.log), [static protocol](protocol-checks.json).

## Execution evidence

This is a bounded request, not a completion forecast. Actual recent CPU observations give a maximum first authentication of 61.106 seconds, later authentication of 24.091 seconds and setup of 233.445 seconds. Derived full-case authentication is 1,554.76 seconds. A separate conservative proxy for new proof construction is 1,517.74 seconds; that new work has not been measured. Their derived sum with setup is 3305.95 seconds. Aggregation also executes full target reconciliation, serialization and dependency-forest refreshes whose full selected-scope costs remain unmeasured. [Saved inputs and uncertainties](timing-evidence.json), [explicit budget](proposal.json).

Request 125 minutes, 4 CPUs, 32 GiB and zero GPUs. Aggregation has a 5,400-second child cap plus 15-second grace; the first calibration chunk has 1,800 seconds plus 15-second grace. The outer allowance is 270 seconds. Initial admission requires 7,275 seconds remaining, leaving startup allowance instead of requiring the full allocation after startup. Calibration starts only after successful aggregation with sufficient actual remaining time. [Caps and checks](protocol-checks.json), [supervisor](supervisor.py), [launcher](launch.sbatch).

Existing case fixtures peaked at 6,893,584,384 bytes, while full aggregation retains additional case values/proofs and target inventory; its peak is unmeasured. The 32 GiB request is an enforced limit, not a demonstrated peak bound. Require 16 GiB finite ancestor headroom before each child. Fresh processes release aggregate heap before calibration. Capture direct child CPU/RSS, actual allocation and complete available cgroup ancestry before/after each phase, retaining shared-ancestor pressure without attribution. [Memory rationale](proposal.json), [resource capture](supervisor.py).

The M1 dependency finding is separate: pilot producers build target inventory metadata but do not consume completed calibration/assessment shards or summary artifacts. A scoped independent readiness review may therefore be considered without automatically waiting for unused later stages. Full selected aggregation still exercises a directly relevant seam that remains uncovered until run. Root/reviewer decides readiness; no production admission is claimed. [Dependency note](direction-m1-dependencies.md), [exact trace](m1-dependency-trace.json), [static call graph](source-call-graph.json).

## What is NOT done

No new CPU job submission, model execution, GPU access, source/harness edit, receipt re-signing, full calibration fleet, assessment or summary occurred. The first calibration chunk has not run. Unknown new costs are explicit budget risks; elapsed values from previous CPU hosts are not allocated-GPU bounds or scientific results. [Proposal limits](proposal.json).

## Open questions

Root reviews exact hashes, performs test-only scheduling and submits if accepted. On the first failure or timeout, preserve all partial outcomes and stop without retry. If successful, report actual aggregation/new-forward costs and calibration startup/per-shard timings before sizing any continuation. Both phases retain original injected nonauthorizing semantics.
