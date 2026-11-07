# A3 prepared metadata Tasks 2–3 independent review

Status: handed-back

## What changed

Reviewed accepted design 175-r 2 and acceptance 180-r 2, implementation 183-r 2 plan/contracts, candidate runtime, native adapter, runtime fixture migration, new prepared tests and frozen task 23-green-r 2 packet. Did not read author report 222. No production files changed. Review evidence is in `.superpowers/sdd/plan-a3/preallocation-task23-review225/` in the specificity-ladder worktree.

Verdict: changes required on two concrete implementation seams before source acceptance. The implementation worker should receive one scoped correction round; the accepted design itself does not need reopening.

1. **R225-A: actual native aggregate phase still takes the legacy path.** `tests/a3_direction_native_scenario.py:239` calls `aggregate_pilot_cases` without the new handle. Its default at line 191 is `None`; lines 205–210 then pass legacy args/no-op guard to `run_pilot`, which rebuilds/publishes/reads back the target. The new test at `test_a3_prepared_pilot_target.py:727` supplies a handle directly to the helper and misses this actual phase route. Implementation 183-r 2 Task 3 explicitly requires fresh native aggregation to use the prepared path. Correct the actual phase route, preserving the original nine prefit case IDs, ordering, exact samples and controls. A bounded regression must drive that route and reject a missing handle or prepared-path target rebuild/write/readback; helper-only routing is insufficient.

2. **R225-B: receiver evidence schema does not anchor deployment-specific measurement scope.** Runtime lines 292–297 unconditionally classify production as `slurm-receiver`/`lustre`; lines 358–376 validate those generic labels, hashes, recipe, peak integers and source-completion booleans. No field binds actual allocation/CPU family or receiver storage evidence, or requires cold/warm wall/CPU scope and measurement allocation/run provenance. The same validator is used by completed intake at lines 2649–2652. Accepted 175-r 2 `receiver-graph-and-RAM.json` requires exact allocation/CPU/storage family and cold/warm scope; implementation 183-r 2 `contracts.json:receiver_resources_required_fields` requires actual environment, declared deployment/storage family, cold/warm wall/CPU/cgroup scope and normal-completion provenance. Add the minimal explicit schema/anchoring required to support those later measurements, and reject missing/incomparable receiver deployment/scope in correctly anchored fixtures before model load and on completed intake. This asks for schema/anchoring, not genuine measurements now. The original admission remains the sole authority.

`findings.json` gives exact correction/regression scopes. `resource-schema-probe.json` demonstrates that the unchanged pure validator accepts a minimal record lacking deployment/measurement fields despite correct hashes/recipe and additive capacity. Hash dependencies were uniformly stubbed; this is only a schema counterexample.

## How verified

Read raw accepted contracts and actual candidate source. Candidate runtime SHA is `b48f8b8dd5cb91ffd8fb2b88d96e40cb844ace09fbaccde2a9f9a4ff3835c03f`; packet source-pins SHA is `3700539550ec8d15e39e50c74a46403c526ca2975bbbf804ef7bb7895fc51f10`.

Compared original and candidate runtime test ASTs and raw diff without git. Only `_production_cost_source_case` changed among original functions/classes; no original node disappeared. Its changes construct prepared descriptor/resources and root admission/mapping references. All original test bodies, parameter decorators and control/damage assertions are structurally unchanged. The new file retains the original cases before five appended correction cases. Workload and its tests retain the accepted 765/846 pins in the frozen packet.

The inspected runtime keeps original reservation/admission/mapping/ledger/allocation checks before receiver use. Descriptor/resources do not independently grant authority. Postdecode retained/transient/process/cgroup bounds are compared before loader; full target host tier and pilot/authority obligations remain additive. Selected preparation requires actual complete backing and `load_selected_axes`. One sealed PID-local frozen graph feeds reconciliation, with original requirement identities. Dispatch keeps fresh guard → receiver → fresh guard → model → actual geometry → guard. Production run_pilot removes target rebuilding and late target output operations.

Final source ordering is union → original before_publication → entry-bound namespace/full witness → fresh original live/deadline → cheap identity/alias seal → deadline → bounded writer. No new final witness was inserted into per-operation numeric forests. Entry reader counts remain two target reads/hashes and one parse/freeze; the final witness is the third target read/hash. Task 1 transport is unchanged and was not re-reviewed. New receipt metadata precedes envelope sizing, barrier time enters proof validation, and cost test uses actual project_cost for startup plus proof charges. No additional static blocker was found in those reviewed seams; executable claims require the root-owned test evidence.

## Execution evidence

No full/native tests, model runs, scheduler/remote calls, source publication or operational resource measurements were performed by this reviewer. The local pure AST-extracted schema probe finished successfully in under one second. It is not a numerical result or resource upper bound. Root supplied predecessor RED job 23618388 and queued final jobs 23620419/23620420; this report makes no claim that either queued final job completed. The frozen expected scope is five correction RED cases against preserved r 1 runtime and 201 GREEN cases in each interpreter. Root must inspect actual job state, manifests, pins, failures and exit codes before acceptance.

## What is NOT done

No source acceptance, Task 4 closure/export publication, genuine producer/cold-warm receiver/RAM measurement, BASE equality acceptance, numerical admission or GPU admission. Actual resource values are intentionally not invented. Fresh final-source original nine prefit cases and complete aggregate/new reconciliation remain separate; selected coverage still waits real fit/selection dependency. Conservative paired timing feasibility and actual host/storage/allocation support remain separate gates. No git, RS, jobs, other agents or unowned files were changed.

## Open questions

No new research decision is needed. Root should request the two scoped seam corrections and attributable regressions, preserve the queued packet/results as immutable evidence, then obtain actual both-environment GREEN and independently review the corrected diff. Root owns Markdown lint and execution-result incorporation because this worker was instructed not to run RS. Source acceptance remains withheld until those findings and execution gates close.
