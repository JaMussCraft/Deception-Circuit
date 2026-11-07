# Admission dry-run repair

Status: handed-back

## What changed

Admission dry-run now exits before the publishing startup constructor. It retains read-only completed-source authentication, numerical/footprint validation and the pure cost checks, and explicitly reports the pending startup-measurement prerequisite. Actual admission still measures, publishes and charges startup normally.

The footprint loop was moved verbatim into a shared read-only helper. Its AST and the existing accepted startup test are identical to the preserved preceding baseline. Only runtime dispatch/helper placement and the new narrow tests changed. The exact owned source closure is [source_snapshot.json](97-review111-round3-evidence/source_snapshot.json), also frozen at `/tmp/report97-review111-round3-frozen-source.json`.

## How verified

Ran the unchanged independent CLI regression and two focused owning cases in both supported interpreters, with single BLAS/OMP/MKL threads and pytest cache disabled. The dry case compares every file and directory, including contents, inode, mode and modification time; a trap prevents it from reaching the publishing constructor. Invalid execution and footprint evidence still reject without tree changes. The real-action case checks its single startup record, admission proposal and exact original-plus-completed startup charge.

Accepted numerical/source/accounting suites were not broadly repeated. Exact commands, source hashes, raw logs and AST-preservation assertions are in the [manifest](97-review111-round3-evidence/run_manifest.json).

## Execution evidence

CPU fixture checks only; scheduler job/cluster not applicable. The original regression fails in both environments before repair. The final focused set passes all 3 expected cases per interpreter, with successful exits. [Final mgnp](97-review111-round3-evidence/report97-review111-round3-final-mgnp.log), [final base](97-review111-round3-evidence/report97-review111-round3-final-base.log), [preserved failures and commands](97-review111-round3-evidence/run_manifest.json).

Baseline assertion: dry-run preserves 23 files and 16 directories in both environments, with complete-tree equality. Real admission produces the expected 27 files and 20 directories and records/charges startup. These are integrity/CPU-fixture results, not scientific measurements. [Observed trees and results](97-review111-round3-evidence/run_manifest.json).

## What is NOT done

No broad reopening of the accepted numerical repairs, large native scenario, production admission, GPU, large weights, paid API, notebook execution, git, RS mutation, scheduler action or subagent work. The preceding source/failure history remains intact. All owned processes are terminal and source edits are stopped. Whole-unit numerical acceptance remains separate.

## Open questions

Root should send this frozen narrow repair to the existing reviewer. There is no remaining author-side blocker. The previously accepted conditional host-startup limitation and the later full native verification gate remain unchanged.
