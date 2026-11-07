# A3 Tasks 2–3 scoped correction review

Status: handed-back

## What changed

Reviewed only the R225-A/B correction diff and directly related regressions in frozen `task23-green-r3`, plus possible breakage introduced by that correction. Did not read author report228. Source verdict: changes required for one remaining resource-comparability gap; native route finding R225-A is statically closed under root’s explicit injected-harness ruling.

**R225-A closed at source level.** Native `run_phase` now receives the prepared graph before model loading and passes that exact handle/inventory to aggregation. The test-module-only subclass uses the existing entry reader, one final full witness and cheap namespace seals, without granting production root authority. Runtime imports no tests; production `run_pilot` requires the exact loader-minted runtime type and rejects the injected subclass. Original case ordering/replay checks and controls remain. New regression drives the actual phase route, rejects postmodel target rebuild/publication/readback, checks all original nine prefit IDs/order and entry/final witness counts. This is source review, not fresh numerical admission.

**R225-B substantially corrected.** The record now requires per-path mountinfo/storage evidence, `/proc` CPU family, allocation CPU/RAM/cluster family, original-admission deployment binding and source-bound completed measurement provenance. Cold/warm wall/user/system, process scope and cgroup current/peak/events scope are explicitly validated. Production freshly observes actual receiver context before/after decoding and compares it with the original binding. Completed intake checks bound deployment and original allocation support. Synthetic fixture observations are explicitly labeled; no genuine feasibility claim follows.

**R225-B remains open: cgroup applicability/scope is never reconciled with the actual receiver.** `_validate_prepared_measurement` (runtime lines 338–391) validates each measurement phase internally. The loader’s post-reader check (runtime lines 538–551) independently checks current process peak and conditionally current cgroup peak. Neither connects measured applicability/scope to current applicability/scope. A measurement declaring cgroup observations unavailable can pass on a receiver where they apply; conversely, a measurement requiring cgroup evidence can pass when the current receiver observations are unavailable. In the latter case the applicable peak check is skipped. This contradicts accepted plan 183-r2 `contracts.json:receiver_observation_contract`: bound evidence and production must use the same accounting/environment/scope, and missing or incomparable applicable observations reject. Accepted plan 175-r2 `receiver-graph-and-RAM.json` likewise binds measured scope and applicable peak overlap.

Smallest correction: reconcile measurement-phase applicability and semantic process/cgroup scope with current receiver observations before model loading, failing closed on missing/incomparable applicable observations. Preserve existing bounds and live guards. Literal cgroup path identity across different processes/jobs is not required. Add correctly original-anchored, complete-record regressions for both mismatch directions with ample capacity, matching artifact/source/deployment/recipe and below-bound peaks; loader count stays zero. Reject internally inconsistent cold/warm scopes where applicable. This is a schema/comparison correction, not a request for genuine measurements or a new plan.

## How verified

Read raw source/tests and frozen packet. Runtime SHA: `66c33953dc8c61ed2292744a362d47f69e6cf565732fb3716402657cc80d15c5`. Source-pins SHA: `bdae741f0be02fabd68f28b247a7ae8eb07a1a261f00ae3a1703c878c5daf8f6`.

The stdlib-only extracted-function probe runs the unchanged new measurement/resource validator and the unchanged loader current-process checks. Both measured-unavailable/current-applicable and measured-applicable/current-unavailable cases are accepted. The synthetic source/ref/context dependencies are uniformly matching; no production imports or model calls occur. Evidence: `.superpowers/sdd/plan-a3/preallocation-task23-review225/r2/cgroup-comparability-probe.json`.

AST audit shows the baseline observer support contains exactly the three allowlisted observation helpers, identical to candidate helper ASTs. No validator or route is among them. Prior prepared tests remain a byte prefix. No prior runtime test function/class changed in this round. Workload765 and workload-test846 hashes remain unchanged. Detailed evidence and smallest regression scope are in the review directory’s `static-evidence.json` and `findings.json`.

## Execution evidence

No full/native tests, operational resource measurements, model runs, scheduler/remote calls or source publication were performed. The local pure probe completed in approximately half a second. It also exercised the packet’s nine schema-gap rejection checks and additive 100-pass/99-reject arithmetic. These pure checks are not the root-owned test gate. The packet expects ten correction RED cases against actual preserved r2 runtime/native source and 218 GREEN cases per environment. Their actual execution results are not claimed here; root owns submission and result review.

## What is NOT done

No source acceptance or Task4 source publication, genuine producer/receiver cold-warm/RAM measurement, BASE equality acceptance, fresh numerical/GPU admission or scientific rescope. Actual measurement values are not invented. The original nine fresh final-source prefit cases plus complete aggregate/reconciliation and selected dependency remain separate gates. No code edits, git, RS, jobs, remote operations, extra agents or unowned file writes.

## Open questions

No new research decision is needed. Root can request the narrow remaining R225-B comparison and its attributable regressions before scheduling a replacement GREEN packet. Keep this frozen revision/evidence immutable. Both-environment execution and corrected-diff review must close before source acceptance. Root owns Markdown lint because this reviewer was instructed not to invoke RS.
