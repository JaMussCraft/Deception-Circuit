# Scoped admission dry-run closure

Status: handed-back

## What changed

Review only. **R1 addressed. Scoped spec verdict: PASS. Scoped code quality verdict: PASS.** No remaining finding in this narrow repair. Original B1/B2 acceptance and the conditional target-host startup caveat remain unchanged. This is not whole numerical acceptance or production admission.

Admission dry-run now authenticates completed pilot inputs, checks their measured dependency footprints and runs the nonauthorizing pure projector before returning without reaching the publishing startup constructor. Its output explicitly lists the remaining completed authentication/index startup measurement. Actual admission retains the shared constructor, startup publication and per-job startup charge.

The footprint loop was extracted into a read-only helper. Independent AST comparisons show the extracted loop is identical to the accepted prior loop, and the actual constructor is identical after replacing only that loop with its helper call. The previously accepted startup test is also unchanged. Evidence: `111-round3-evidence/check_extraction.py`, `111-round3-evidence/extraction.json`.

## How verified

Inspected only the frozen fix diff, affected source and raw execution evidence. Author handoff/report prose was excluded. All package source hashes match independently. Runtime is `b66c2d8cd26c36f321b5079758209214746b0e4eec16a6c801742086d729c0cc`; workload remains `3e43aaf2b4cacb99df87593ae377c8fdf3eb7b223b258ed8873853841404d8f9`. Exact source and commands are in `111-round3-evidence/run_manifest.json`; reviewed runtime/diff copies are preserved there.

Reran the original independent CLI counterexample and focused dry/non-dry controls on both supported interpreters. Controls compare complete file/directory paths, bytes, inode, mode and modification time; forbid the publishing constructor on dry-run; reject invalid execution/footprint inputs without mutation; and check actual admission publication and the original-plus-completed startup charge. Broader accepted numerical/authority scopes were not repeated.

## Execution evidence

CPU tiny fixtures only; scheduler job/cluster not applicable. Three cases pass per interpreter, with successful command exits. Dry-run retains 23 files and 16 directories before and after; actual admission changes 23 files to 27 and 16 directories to 20 while charging startup. Evidence: `111-round3-evidence/mgnp.log`, `111-round3-evidence/base.log`, `111-round3-evidence/run_manifest.json`.

Baseline assertion: the unchanged original counterexample now retains 23 files against the expected 23 in each environment. Dry-run tree equality includes every recorded file byte and directory metadata field. These are integrity and CPU-fixture results, not scientific observations or GPU timing. Provenance, exact commands and source overlay are recorded in `111-round3-evidence/run_manifest.json`.

## What is NOT done

No source edits, git, RS writes, scheduler access, GPU, large weights, APIs, notebooks or subagents. No broad test suite, full native scenario or production admission. The required future bounded native pilot/calibration/assessment/summary evidence remains open. Earlier failure artifacts remain preserved.

## Open questions

No remaining narrow R1 blocker. Root can combine this closure with the accepted B1/B2 and authority reviews before coordinating the required full native verification. Host startup portability remains conditional until matched or conservatively bounded under the existing lifecycle ruling.
