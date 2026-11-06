# A3 prepared metadata design independent review

Status: handed-back. Verdict: REVISE; the phase-scoped transport approach is compatible in principle, subject to the narrow corrections below. No implementation or feasibility acceptance.

## What changed

Wrote only this review and [verdict.json](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-independent-review180/verdict.json) with [input-pins.json](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-independent-review180/input-pins.json). Read the raw design and original runtime/artifact/workload contracts, without the author handback. The candidate runtime remains byte-identical to the original; candidate workload bytes and existing evidence are untouched.

The original pilot target was an in-memory value, absent from per-operation file-witness dependencies. An authenticated immutable process-local value can preserve that contract. Requiring a huge target-file hash on every refresh would add a new obligation; it is not required by the original target semantics. CPU preparation authenticates data only: all existing source/protection/ledger/allocation/lease/numeric witnesses and actual post-load geometry remain fresh.

## How verified

Verified raw design manifest and every member hash, then read original `run_pilot`, `_PilotReconciliationPass`, `_AuthorityContext`, `_DependencyForest`, `_FileWitness`, artifact completion and downstream intake. Verified candidate/original runtime hash equality. Exact inspected inputs are pinned in [input-pins.json](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-independent-review180/input-pins.json). No tests or models ran.

## Execution evidence

No new execution. The raw design records a 11421127399-byte genuine target; paired allowance remains 0.5 GPU-hours, or 1800 seconds. These are input constraints, not a measured feasibility result. See [verdict.json](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-independent-review180/verdict.json).

## What is NOT done

No implementation, publication, source admission, cap change, CPU/GPU job or numerical equivalence claim. Current original witness refreshes cannot be cached or removed. Parsing a CPU-produced target does not grant execution authority. Full reader/parse/freeze/backing-check costs and selected-part footprint remain unmeasured.

## Open questions

Revise the final transport barrier placement: check exact entry-bound target and descriptor after costly guard-union measurements and immediately before receipt publication, then retain fresh authority/deadline checking. Specify lexical alias versus content-only replacement semantics; `object_reference` alone does not detect every byte-identical root replacement. Measure actual scan multiplicity and raw/decode/freeze overlap, and retain one exact immutable requirement graph. Concrete rejection tests and minimal corrections are in [verdict.json](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-independent-review180/verdict.json).

Accept the transport seam through normal root and independent source review, rather than inventing a per-refresh transport witness. Admission still needs a conservative measured bound for both parts, including selected preparation when its real dependency exists. No blanket complexity rejection or new human policy approval is justified merely by moving deterministic construction to CPU.
