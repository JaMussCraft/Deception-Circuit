# A3 sharded validation source review272

Status: handed-back. CHANGES REQUIRED. Spec and quality verdicts both require the three narrow corrections below; no deployment acceptance.

## What changed

Created only reviewer-owned source snapshots, pins, focused reproductions, logs and [verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-validation-review272/verdict.json). Review binds source-pins `25c817e97f7ae276ac49a6f5194c3741885c830df6863e8f2dc0c11be3a1b77f` and partition `0fdb618b919c0622f13cb3bb4af29ffad32df42ee6bfe92dc531a1d73b02a72a`, under accepted plan268. No implementation, remote file or scheduler state changed.

## How verified

1. **B1, high: retained host evidence boundary is lost.** [host.py](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-sharded/bridges/host.py:93) binds the whole job root, output.parent, writable inside the Bridges container. Host-before and previous command/terminal files are created in that same directory. The accepted diagnostic wrapper kept host receipts outside the child writable subtree. Restore that boundary while adapting fresh child output and inner receipts mechanically; test permitted child writes and denied host/prior-receipt changes. This identifies exposure, not a demonstrated forged complete aggregate; in-memory stage hashes and terminal accounting remain additional checks.

2. **B2, high: deadlines renew after preparation, with an expired-launch gap.** [host.py](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-sharded/bridges/host.py:131) freezes the command deadline before command receipt/log I/O, but [supervisor.py](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-sharded/supervisor.py:59) creates fresh now-plus-cap bounds afterward. A pure oracle example sets caller deadline90, advances preparation to100, then gets normal supervisor completion under deadline190. Separately, if the last fresh query exhausts an existing bound, Popen still runs before post-exit rejection. Carry the initial wall/monotonic stage bounds through all I/O and the final query, shrink only and refuse expired launch. Keep raw error evidence and the one cleanup budget.

3. **B3, medium: partition promotes the wrong resource family.** [partition.json](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-sharded/partition.json:5) names test_prepared_correct_identity_understated_observed_resources_rejects instead of repaired test_prepared_receiver_resource_identity_and_capacity. The repaired family starts at indices48/46. Complete parity coverage survives, but the accepted repaired-family-first requirement does not. Correct the literal family, recompute order/dependent pins and add an independent literal-family assertion.

The suspected inner receipt collision is absent: filenames already include baseline/oracle/suite and three sequential mocked invocations succeed. No correction is requested there.

The remaining structure matches the plan: full original223 collection, disjoint112/111 parity coverage, deterministic per-partition order, preserved session items and original conftest/preflight; exact phase and JUnit identities/outcomes; root-authenticated expected_bindings, distinct jobs/outputs, unchanged source identities, host/stage completion and accounting. Full acceptance requires both exact interpreters; partial shards cannot confer full acceptance. Corrected fixture e2a7 remains exact; baseline_red, fixture_preflight, closure, conftest and existing regression copies are byte-identical to r5. Runtime remains unchanged. No framework redesign is needed.

## Execution evidence

Four focused pure checks pass in each interpreter: two reproduce deadline defects, one confirms RW scope exposure and one confirms distinct inner receipts. Passing reproduction tests are evidence of these defects, not wrapper correctness. [Runs](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-validation-review272/run_manifest.json). The partition mismatch is independently recorded in [test attribution](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-validation-review272/test-and-template-attribution.json).

Read raw original thirty-two RED failures and thirty-four GREEN passes in each environment, with their exact test-source hashes. Those full pure suites were not repeated. Current source hashes agree with frozen evidence. Root271 separately establishes source-bound dry runs, Python3.6 grammar and the actual absolute-root-bootstrap/relocated-spool interface; these are pure checks, with no actual job or native acceptance. Direct cpu.sbatch submission is not the intended interface. Templates retain NULL job/config bindings. [Pins and scope](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-validation-review272/pins-and-scope.json). Live usage was forty percent, cap eighty and cadence forty; no freeze was inferred from an unrelated worker-hook false positive.

## What is NOT done

No native/full suite, actual deployment/binding, host/container execution, scheduler action, complete validation, model/GPU or scientific admission. Four independent CPU shards and their complete outcomes are still prospective. The eighty-minute proposal is not evidence of feasibility. Historical failures and frozen source remain preserved.

## Open questions

Create a distinct minimal successor fixing B1-B3, preserving this packet. Focused regression checks should verify the restored evidence boundary, final expired-budget refusal/nonrenewal and exact repaired-family literals/order. After independent scoped acceptance, root must bind actual configs/resources/environments/spooled immutable bootstraps and source/alias closure before releasing any job. Keep the accepted four-shard proposal: Delta two CPUs and Bridges eighteen, thirty-two GiB and eighty minutes per shard; stage caps610/90/3600, final reserve120, one fifteen-plus-five cleanup allowance and no automatic retry. Only both complete interpreters' normal exact223 coverage may satisfy complete validation; numerical/GPU gates remain separate.
