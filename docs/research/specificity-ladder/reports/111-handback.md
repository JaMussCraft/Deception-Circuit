# Independent direction numerical integration review

Status: handed-back

## What changed

Review only. **Spec verdict: FAIL. Code quality verdict: FAIL at the production cost-intake boundary.** One high-priority blocker remains. The separately accepted shared-authority review remains accepted; this finding concerns the evidence supplied to the new numerical cost consumer, not reservation authorization.

**B1 — completed synthetic or contradictory timing receipts are accepted as production cost evidence.** In `component_analysis/a3_direction_runtime.py:815`, preparation reads pilot objects and immediately calls the cost projector through `_cost_packing_proofs`. That helper silently ignores legacy inline packing evidence. The pure projector validates numerical shapes and claimed coverage, but does not authenticate the completed pilot's execution class, actual execution, original job/output, runtime, pilot inventory, part or source split. The new orchestration supplies no additional validation. A completion marker binds the submitted bytes; it does not establish that those bytes describe the required native pilot.

The independent counterexample builds an inventory with production execution class and required frozen assessment/utility cardinalities, publishes a completed receipt, then uses the same intake calls as preparation. The receipt explicitly declares `injected=true`, `actual_execution=false`, a CPU injection job, assessment source scope, the wrong pilot part and a bogus pilot-inventory digest. Its packing evidence comes solely from the synthetic pure-core fixture, with no independently resolved numeric backing. Both interpreters accept the proposal. Changing the synthetic samples from the baseline to tiny positive values lowers projected time from 141.77500000000143 seconds to 12.00000648875 seconds. Exact evidence: `111-numerical-evidence/probe_cost_intake.py`, `111-numerical-evidence/cost-intake-mgnp.log`, `111-numerical-evidence/cost-intake-base.log`.

The returned proposal still has `execution_authorized=false`; this does not bypass live root reservation authority. It does violate the independent measured-cost intake requirement and permits an unjustifiably optimistic proposal for root admission. Repair the runtime evidence boundary: independently resolve completed pilot and target inventory, source, original job/reservation/output, execution class, hardware/runtime, stage and numeric evidence; reject contradictions, absent backing and synthetic legacy evidence for production. Preserve the pure synthetic test API where explicitly appropriate. Checking only the added booleans would leave fabricated positive claims unauthenticated.

## How verified

Inspected the frozen numerical package, changed source seams and accepted integration requirements without reading the author's report or handoff. Independently hashed every source file against the package manifest. Exact source identity and commands are in `111-numerical-evidence/run_manifest.json`; runtime hash is `bb54a6076c4edf507bed43abaa256cd2ce3a6cded85a4315b4a3c86d1f8047f1`, workload hash is `7726495fb2388491f56f442dd404e151f72d4eedd3bbf1106e7d10e70ead154a`.

Independent oracle cases compare the new immutable index with full numerical validation under changed physical profile, tokens, masks, readout, source membership, metadata and axis selectors. Additional checks cover donor convention, prediction thresholds/ties, unequal label counts, nonfinite probe inputs, exact scalar balanced accuracy, reference-proof versus full-proof projected costs, absent typed proofs and condition/stream candidate selection. These tests exercise the index's numerical semantics; they do not authenticate an untrusted producer.

Targeted owning cases exercise source-shaped parents and interior token zero, tail aliases, canonical task order, actual operation clocks, frozen measured proof reuse, external backing mutation, atomic deadline/authority boundaries, validation-only conditional power, assessment prerequisites and injected finality refusal. No broad authority suite or long native run was duplicated. Code inspection found no additional concrete numerical blocker in the reviewed capture/fit/selection/probe/power/finality seams.

Initial reviewer harness failures came from choosing a capture requirement without axis scope, expecting only one exception type for an invalid stream, and omitting the numeric descriptor on a prefit axis. The original harness and failure logs are retained; the corrected harness uses an actual measured axis descriptor. These failures are not product failures.

## Execution evidence

CPU commands only; no scheduler job or cluster. Independent cases: 29 observed against 29 expected per interpreter. Targeted owning cases: 14 observed against 14 expected per interpreter. All final commands exit successfully. Exact commands, interpreters, log hashes, baseline package commit and reviewed source overlay are recorded in `111-numerical-evidence/run_manifest.json`. Outputs: `111-numerical-evidence/final-mgnp.log`, `111-numerical-evidence/final-base.log`, `111-numerical-evidence/owning-mgnp.log`, `111-numerical-evidence/owning-base.log`.

Counterexample commands exit successfully in both environments and show the same production-target admission defect. Baseline comparison: projected time 141.77500000000143 seconds in each interpreter against 141.77500000000143 seconds in the other; corrupted evidence projects 12.00000648875 seconds in each. These are deliberately synthetic arithmetic and provenance checks, not model timing or scientific observations. Evidence: `111-numerical-evidence/cost-intake-mgnp.log`, `111-numerical-evidence/cost-intake-base.log`.

The model-free scaling evidence supplied by root remains injected old-source evidence and cannot admit production. The fresh full-count native tiny run is still owned by the author. At this hand-back, root has not supplied its completed calibration, assessment and summary result. Its earlier stage messages are not a pass. Full acceptance remains gated even if the cost blocker is repaired.

## What is NOT done

No implementation edits, git, RS writes, scheduler reads or submissions, GPU, large model weights, APIs, notebooks or subagents. Only reviewer-owned report/evidence files were written. No production prepare or production admission. No scientific conclusion or new effect estimate. Shared authority findings were not reopened. The long native run was not duplicated, interrupted or described as complete.

## Open questions

Root should coordinate a bounded source reopen for B1 and an independent closure review. Default: retain the source freeze and original failure evidence until that coordination occurs. A repaired provenance seam needs completed positive production-shaped evidence plus negative injected, wrong-stage, changed source/job/output, missing backing and incomplete receipt cases in both interpreters. The full native completion result remains a separate gate; root owns how to preserve or repeat it after any source change.
