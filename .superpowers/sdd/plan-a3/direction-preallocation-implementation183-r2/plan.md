# A3 Prepared Pilot Metadata Implementation Plan — revision 183-r2

> **For agentic workers:** Use subagent-driven-development under root orchestration: sequential ownership, test-first, and independent review. Root alone runs git, RS, scheduler and source publication. Steps below are the implementation contract; no implementation starts until root accepts this plan.

**Goal:** Prepare deterministic full-target metadata before GPU allocation while preserving exact authenticated values, every original live/numerical guard and the fixed paired timing cap.

**Architecture:** Keep the existing JSON artifact and root pilot-admission interfaces. A CPU producer emits a fully reconstructed target and metadata-only descriptor; a private same-buffer reader returns one immutable graph anchored by the fresh root admission. Runtime integration uses the existing loader/geometry/guard path and a final entry-bound transport barrier immediately before the bounded receipt writer. No daemon, persistent guard cache, model-provider callback or new authority kind.

**Tech Stack:** Existing Python/JSON/pytest, both supported interpreters, original publisher/witness/ledger interfaces.

**Spec:** `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-design175-r2` (manifest `397b788d…`); independent acceptance `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-independent-review180-r2` (manifest `98c182c7…`). Exact interface/schema decisions are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-implementation183-r2/contracts.json`; required fixtures are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-implementation183-r2/test-matrix.json`.

**Revision basis:** Plan183 remains immutable (manifest `315fc52d…`). Review184 manifest `c268d79a…` requires the two corrections mapped in `revision184-resolution.json`; accepted175-r2/180-r2 remain the design basis. No implementation is authorized by this document.

## Global Constraints

- Create only the new isolated ordinary tree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183` after plan acceptance, copied from accepted `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-optionA-candidate`. Preserve its workload/test hashes. Never edit the original candidate, frozen runtime, W HEAD/index/native files, existing evidence or running base jobs.
- Workers are not alone: own only assigned files/hunks and do not revert another worker's changes. Tasks sharing runtime/tests run sequentially; never change a source-pinned tree while its CPU job is active. Root may use distinct revisions for any deliberate concurrency.
- Hard semantic/authority/alias/resource work and reviews use Sol. Terra may only package hashes/manifests/diffs/AST/syntax after semantic files are frozen, with an explicit bounded assignment.
- Root submits all CPU checks. No local heavy tests, worker scheduler/git/RS state changes, publication, pretrained model run, scientific rescope or cap change.
- Keep workload/digest/independent validator algorithms, generic publisher/reader contracts, live authority minting, all source/protection/ledger/budget/allocation/lease checks and numeric witness schedules unchanged.
- Producer/descriptor/measurement is DATA, never execution permission. Private seals are a trusted-code invariant, not a sandbox against arbitrary same-process Python execution.
- Preserve wrapper-start timing and effective minimum initial/current deadline. Entry and final transport cost count; no assumed cheap hashes or alias savings. No automatic retries or adopt-current repairs.

## Review Focus

- Late target/descriptor replacement during guard-union, final hashes or live guard must block the writer; Task 3 owns the ordering tests.
- Lexical/alias/root replacement is distinct from equal content; Task 1 owns the explicit namespace policy fixtures.
- Read/hash composition can silently multiply whole-payload I/O; Task 1 proves the declared recipe and Task 4 records actual costs.
- JSON parse/freeze expands aliases and must preserve one exact requirement graph; Tasks 1–2 own graph/resource rejection tests.
- New runtime/source identity cannot inherit old numerical or cost admission; Tasks 3–4 preserve downstream reconstruction and separate source/measurement gates.

---

### Task 1: Exact-format transport and phase snapshot

**Owner/model:** Sol; independent Sol review of data/provenance semantics. No parallel writer in these hunks.

**Files:** Modify only private prepared-transport helpers in candidate `component_analysis/a3_direction_runtime.py`; create `tests/test_a3_prepared_pilot_target.py`. Do not modify generic `publish_object`, `read_object`, `object_reference`, `_FileWitness` or workload functions.

**Interfaces:** `_publish_prepared_target_object`, `_prepared_namespace_identity` and `_read_prepared_target_object` as defined in `contracts.json`. Reader returns the frozen value, immutable entry refs, namespace identity, phase witness and observed I/O; no authority. Phase witness uses resolved artifact roots and is never inserted into existing per-operation numeric forests.

- [ ] Write T1 tests first using existing publisher artifacts as fixtures; new helpers are called in test bodies so missing functionality yields attributable RED calls, not collection/setup errors. Include floats/Unicode/frozen containers/default JSON separators and final LF, actual byte hashing, re-signed-file races and exact child/marker semantics. Do not add unreviewed stricter JSON/schema policy.
- [ ] Prepare root-only bounded dual-environment RED packet; assert candidate/oracle module origins and source pins before/after. Root observes the intended missing-transport failures before code edits.
- [ ] Implement only the declared codec/namespace/reader helpers. Bind the writer-emitted bytes; use one target byte buffer for hash+parse; freeze once. Mint the existing phase witness and check exact entry hashes/identities. Approved pre-entry materialization and in-phase replacement policies remain distinct.
- [ ] Root runs T1 GREEN on both interpreters. Exercise the lower reader (two reads/SHA passes: same-buffer read and entry witness mint) plus its explicit final phase-witness recheck (one): total target reads/SHA passes `3`, parse/freeze `1`, receiver target writes `0`. T3 places that last recheck in the real final barrier. Never add a redundant startup scan to force the count; these are verified via actual observers, not source-text assertions. If the correct implementation needs more passes, stop and report the real count for root cost review rather than hiding it.
- [ ] Freeze the task's source/test hashes, raw diffs and results for independent review. No commit/publication by workers; Task 2 starts only after this source-pinned run is terminal and root accepts the handoff.

### Task 2: CPU producer, admission anchoring and receiver resource validation

**Owner/model:** Sol; independent Sol review. Reuse the T1 worker/context if root prefers, with explicit ownership transfer.

**Files:** Candidate runtime prepared producer/loader/data-handle helpers and parser prepare-action enum; append T2 tests to the new test file. No scientific workload or authority-kind change.

**Interfaces:** `prepare_pilot_target`, `_validate_prepared_receiver_resources`, `load_prepared_pilot_target`, `_PreparedPilotTarget.assert_scope`; one existing-kind admission field `pilot_target_preparation`. Exact keys and canonical paths are in `contracts.json`.

- [ ] Write T2 RED fixtures for exact source/input/part/selection bindings, no model construction, independent CPU reconstruction, partial/failure behavior, root anchoring, wrong PID/context/seal and resource arithmetic. Include `test_prepared_correct_identity_understated_observed_resources_rejects`: exact correctly anchored identities and ample nominal capacity, but actual decoded/frozen retention or applicable transient/peak observation exceeds its bound; reject after reader, before loader (zero loader calls). A preparation or measurement artifact offered as a root reservation must reject.
- [ ] Root runs the attributable RED subset on both interpreters, then the worker implements only the declared helpers and `prepare --action pilot-target` route. Prefit builds the full fit-select target with fits/selection unset; selected requires the actual complete selected backing and builds remaining. Keep all CPU pre/post source/protection checks and normal-completion provenance.
- [ ] Derive production expected refs and receiver resources from the fresh original root admission/context. Never accept a caller validation flag, arbitrary provider or CPU-granted lease. Authenticate the data and bind one sealed PID-local graph to exact source/part/workdir/pilot/admission/reservation refs. The lower reader remains usable by CPU measurement without granting model authority. It returns actual buffer/graph/resource observations. Compare those post-decode/freeze observations against the SAME anchored record before the loader; identity agreement alone is insufficient. Use the identified cycle-safe object-identity accounting/temporary-buffer lifetime recipe in contracts.json, supplemented by applicable process/cgroup observations; fail if observations are missing or scope mismatches. Preserve all original actual capacity checks and tiers, with no assumed alias/producer-peak subtraction. Refresh actual capacity and live/deadline/model guards after comparison.
- [ ] Root runs T2 GREEN and T1 regressions on both interpreters. Test exact additive resource charges with fixture existing `50` + retained `20` + extra transient `30`: capacity `100` passes and `99` rejects. Genuine resource numbers must later come from actual evidence; producer peak is not a receiver bound.
- [ ] Freeze exact schemas, source/test hashes, results and scope for independent review. No root admission, genuine target, new source or resource record is created operationally by this coding task.

### Task 3: Runtime integration, final barrier and native adapter

**Owner/model:** Sol implementation and independent Sol review. Sequential access to runtime/new tests; owns only the native adapter file in addition.

**Files:** Candidate runtime `dispatch`, `run_pilot`, `_pilot_origin`, preparation-origin intake checks and handle final barrier; candidate `tests/a3_direction_native_scenario.py`; append T3 tests to the new test file. Narrowly modify candidate `tests/test_a3_direction_runtime.py` only for authentic preparation/intake fixture construction (`_production_cost_source_case`) and directly related prepared/legacy rejection expectations. Preserve every original numerical/authority/tamper assertion and damage case. No production compatibility bypass or unrelated test edits.

**Interfaces:** Production `run_pilot(..., prepared_target=handle)` requires a loader-minted graph. Explicit injected reference behavior is test-only. `_PreparedPilotTarget.final_publication_barrier(reconciliation, receipt)` is called after `_measure_complete_guard_union` and original `reconciliation.before_publication`, immediately before `_publish_measured_pilot_receipt`.

- [ ] Write T3 RED call-order and mutation/deadline fixtures using existing controlled scheduler/clock/model seams in tests only. Do not add production injection parameters. Assert production missing data or cancellation during a slow reader rejects before the loader; actual post-load geometry mismatch rejects before numerical capture.
- [ ] Integrate fresh guard → authenticated reader → fresh guard/remaining lease → unchanged model load → actual geometry equality → original guard. Remove only production full-target rebuilding/late target write/readback. Preserve all numerical invocation/control/selected backing and later independent CPU intake reconstruction.
- [ ] Implement the final sequence exactly: costly union; original before-publication; entry-bound namespace/full witness; fresh live guard and effective deadline; unchanged cheap identity/alias seal and deadline; existing bounded writer. Test same-size/restored-mtime and identical-root replacement during late work, writer count `0` on rejection, and no adopt-current reference.
- [ ] Put all new known metadata into the receipt before envelope sizing. Entry receiver time remains in startup once; final barrier time is charged once in proof-validation/cost evidence. Preserve the original final byte bound and fail oversize updates. Assert actual `workload.project_cost` output charges startup plus proof validation exactly once, beyond checking receipt fields. Root runs T3 GREEN plus targeted existing guard/geometry/pilot/intake regressions on both interpreters.
- [ ] Update the native adapter to exercise prepared-target aggregation without changing the original case set or controls. Migrate the production-shaped runtime fixture to authentic preparation/resource refs anchored in original admission/mapping; correctly prepared origins pass original success/projector assertions. Add explicit old no-preparation origin rejection and missing/changed/unanchored preparation/resource/source/part rejection. Preserve all original completed-source/mapping/reservation/runtime/numeric backing damage assertions. Unit adapter routing is not numerical admission. Freeze the complete diff and hand back for independent review; no fresh numerical jobs or source publication follow automatically.

### Task 4: Code completion, closure and separate measurement handoff

**Owner/model:** Sol decides semantic coverage/resource validation; independent Sol reviews the whole diff. Terra may package the explicitly frozen hashes/diffs/AST/syntax and declared export inventory only.

**Files:** Final candidate test/closure assertions; root-submit fixture/measurement packet descriptions and handback under this plan directory. No further production changes unless a new failing test identifies a defect.

- [ ] Root runs the new test file and targeted existing callers under both interpreters with no pytest cache and isolated discovery/import origins. Include existing root-reservation, prefit-pilot, allocation-before-model, geometry, guard-envelope and completed-pilot-intake tests; exact node list is recorded in `verification-scope.json`. Reuse the completed unchanged765 algorithm suites/oracles by hash; do not blanket-rerun them.
- [ ] Prove exact candidate export/import closure and original-tree preservation. Runtime contains the new reader, so its whole-file hash enters existing source closure. Any future helper file outside it requires an explicit declared/discovered source member. The new test file raises ordinary export membership; root uses the exact new declared inventory, never a stale hard-coded file count.
- [ ] Independent review checks all four180 conditions, rejection tests, actual fixture I/O counts, exact graph, root-only authority and the full diff. Code completion means this review and both-environment focused checks pass; it does not mean genuine BASE equality, resource feasibility or numerical/GPU admission.
- [ ] Prepare, but do not submit, root CPU measurement packets for authentic complete target materialization and cold/warm receiver/final-check profiling. Bind exact bytes/source/reader/freeze/environment/storage and actual CPU allocation; collect per-step wall/user/system/read counts and cgroup current/peak/events. Existing oracle was a hash sink, not a saved file. Do not retarget running jobs or relabel old-context measurement as final-source readiness. Root sizes actual requests from observed evidence separately.
- [ ] Hand back code/evidence plus the remaining gates in `contracts.json`. Root alone decides final source publication, fresh source-dependent artifacts, original nine prefit cases plus complete aggregate/reconciliation, actual CPU receiver resources, conservative paired M1 feasibility and any actual GPU reservation. Selected coverage waits for its real M2/selection dependency. No automatic retry or cap amendment.

## Verification scope and test packets

Each task must produce checkable RED and GREEN evidence under both interpreters: distinct pinned runtime revisions with the same attributable test assertions. Do not mutate either pinned revision during its CPU run. Root chooses allocation and limits before execution; worker packets never submit. Tests use `--confcutdir` at the candidate, importlib mode, `-p no:cacheprovider`, unique basetemp, bytecode disabled and pinned BLAS threads. Record completed calls/failures durably so a timeout remains attributable. Do not edit a candidate while a pinned job is active.

Genuine BASE comparison is separately owned and remains a prerequisite; no cross-environment oracle substitution. Actual producer/reader/RAM costs, fresh source-bound numerical cases and the paired cap are separate evidence gates, not inferred from fixture passes. Any measured extra read/hash/retention cost is reported, never hidden to satisfy a planned count.

## Plan self-review

Spec coverage: T1 addresses180-B/C and exact format; T2 addresses anchoring/180-D resources; T3 addresses180-A and runtime/geometry/guards; T4 closes both-environment/source/resource evidence without admitting a model. Shared interfaces and test ownership are listed above; tasks touching runtime/new tests are sequential. All five Review Focus items have named tests in `test-matrix.json`. No implementation, new source, target, job or publication exists from this plan.
