# Builder review: complete sharded validation

Verdict: implementable with the four concrete clarifications below incorporated into the packet contract. No broader audit, user decision or framework is needed. This accepts the implementation approach, not a completed validation result.

## Required clarifications

1. The aggregate verifier needs a trusted expected deployment binding, not only expected source and partition. Add `expected_bindings` to `verify_shards`, or explicitly require an authenticated root deployment map inside the existing expected input. Match interpreter/shard to the actual job, cluster, output root and terminal host receipt. Checking only that self-reported job IDs are distinct cannot reject a consistently substituted job. Root deployment files remain the existing binding authority; do not create a new authority system. Pure tests should reject a fully consistent but unexpected substituted deployment.
2. The existing diagnostic selector constructs `items` by filtering `session.items` in collection order and then asserts that result equals the requested selection. That will reject the proposed repaired-family-first execution order. Build a unique node-ID-to-item lookup after asserting the untouched original complete collection, then construct the execution list in frozen partition order. Keep `session.items` unchanged. Retain the existing `pytest_runtest_protocol(item, nextitem)` dispatch and exact phase events. This is a small selector change, not a scheduler.
3. Derived budget arithmetic: `4800 - 3600 - 610 - 90 - 120 = 380` seconds remain before cleanup. Reserving the single `15 + 5 = 20` second TERM/KILL/reap allowance leaves `360` seconds for non-stage overhead. Name that allowance explicitly; it is not all available for setup. Derive absolute stage deadlines from the original allocation boundary and current end without renewing them. Check observation time before accepting a reaped zero-exit child, and preserve failure if the process cannot be reaped within the fixed cleanup budget. The original fixture preflight is inside the pytest-child bound, not an extra stage added outside it.
4. Correct the spaced runtime digest in Global constraints. The unchanged literal is `aea07dbf153824f373be70629dd24edc28dd6566cafa5955f43c69fd1119ec90`.

## Coverage and reuse assessment

The exact complete collection, original parameter multiplicities, disjoint partition and full union per interpreter are retained. Full collection order is preserved separately from the intentional execution order. Original baseline, oracle, candidate preflight, source/import checks, phase records and host completion remain acceptance prerequisites. Requiring complete setup/call/teardown plus both process completion and source-finalization receipts prevents a selector finished marker alone from becoming acceptance.

Use exact JUnit-to-node mapping from filename/classname and parameterized test name, checked against the authoritative event node IDs. Do not strip parameter suffixes or accept function counts as identity. Preserve raw child status before parsing artifacts. A partial environment remains explicitly partial even if every shard available so far passed.

The successor packet location preserves the existing sibling candidate/oracle path relationships. `--environment` already exists in the old packet; restrict real shard execution to one environment, and add the explicit shard selector. Preserve the independent oracle-proof path: it should not require a shard execution selection or start baseline/pytest recursively. Existing dry-run behavior should print only the chosen real command when a specific environment/shard is supplied. Bridges host scripts remain compatible with their existing host interpreter; candidate and pytest execution still use the exact designated native interpreter.

Separate CPU allocations avoid unsupported concurrent-memory assumptions. The larger finite wall-time proposal is consistent with the stage caps and leaves an explicit buffer, but neither successful completion nor queue acceleration is established. Keep the sequential complete-suite fallback if packet adaptation grows. No reuse of the rejected native BASE port or of pure BASE checks as native acceptance is permitted.

## Scope of this check

Read the concrete plan, original packet command/control flow and diagnostic selector. No code was changed; no tests, jobs, remote operations, Git, research-state mutation or additional agents were used. Root's newer diagnostic completion facts do not alter this recommendation and are not independently re-audited here. This check adds no numerical, scientific or GPU acceptance.
