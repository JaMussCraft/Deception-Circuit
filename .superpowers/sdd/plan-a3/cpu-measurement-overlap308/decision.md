# CPU measurement overlap decision

Status: handed-back. Recommend overlapping a candidate CPU producer measurement with the remaining native tests, using the existing interfaces. This is operational advice, not an actual source, job or resource acceptance.

## Judgment

Waiting for both complete native suites before collecting any genuine CPU producer measurement is avoidable serialization. Native acceptance remains mandatory before promotion and GPU admission. It is not an intrinsic prerequisite of the CPU-only producer path.

The accepted design 175-r2 explicitly lists producer and reader work under `measure_before_source_publication`; its decision document recommends measuring costs before publishing merely to repeat gates. The later packet 247, review 279-r2 and preparation 301 describe a final-source execution sequence. Their stronger order must not be silently reinterpreted as already authorizing an early run. Root can record a narrow candidate-measurement decision consistent with the original design, keeping that work provisional and preserving the final-source packet unchanged. No new transport framework, runtime feature or scientific gate is needed.

## What the actual code requires

Paths below are relative to the specificity-ladder worktree's `.superpowers/sdd`.

- `plan-a3/direction-preallocation-candidate287/component_analysis/a3_direction_runtime.py:764` requires a real full execution commit argument; dispatch at line 1400 requires the canonical work-directory design and agreement between CLI commit, frozen protocol and protocol hash. No native-suite result or acceptance status is read there.
- `prepare_pilot_target` at line 421 calls `live_guard` before and after construction, hashes the source, validates and independently reconstructs the supplied pilot, builds and validates the genuine full target, publishes ordinary target bytes and a preparation descriptor, and rejects changed source. It expressly emits `model_loaded=False` and `execution_authorized=False`. The old streamed hash sink is not an input substitute.
- `live_guard` at line 1130 always performs source/protection/parent/grader checks through `artifacts.validate_live`, plus production model-configuration metadata validation. It enters ledger/reservation/allocation/model-authority validation only when given an execution inventory. The producer calls it without that inventory. Preserving this existing CPU branch is not removing a ledger check from a model path. Do not invoke model stages, `prepare admit`, or use `dry_run`, injection, replacement guards or fabricated authority to manufacture a measurement.
- `a3_direction_artifacts.py:28` hashes the declared whole runtime closure, including deferred modules; `validate_live` at line 366 rechecks source, real registries, protected access, graders, parent files, utility files and matched/historical sources. These checks stay intact. A syntactically valid commit is not independent proof of a real commit/export correspondence: root's existing supervisor must establish that correspondence and actual import origins.
- `prepared-resource-runner278-r2/runner.py:270` calls `runtime.main(native_argv)` unchanged and records observations. Its docstring assigns actual source/import/allocation/storage authentication to root's supervisor. It neither reads native acceptance nor grants authority. The standalone unbound CLI/template is not a launcher permission.

## Smallest useful next operation

Root should freeze a real isolated candidate execution commit and immutable export containing the exact reviewed r8 runtime, unchanged workload, required helpers and source closure. Attribute it to the running suite's exact file pins. Preserve every running source/export, active worktree reader and existing job. This is a candidate source snapshot, not a declaration of code completion, a merge, a final publication or GPU admission.

Then bind the already accepted measurement adapter to the existing CPU supervisor in a separate candidate-only namespace. Use the normal native prepare/freeze and prefit inventory path to obtain fresh canonical design/protocol/pilot objects for that commit, followed by the genuine `prepare --action pilot-target --pilot-part prefit` through `produce_native`. Preserve the full noninjected inputs and original execution settings, model metadata, registries, literal paths and checks; do not edit old source-coupled objects into the new identity. No model loader or selected backing is involved.

Root must authenticate an actual CPU allocation, supported interpreter, source/export/origins, storage capacity and private output namespace, and review a bounded request before release. Reuse the established supervisor and observation fields. The historical approximately fifty-minute producer comparison and roughly 134 GB peak are sizing inputs, not a promise that the genuine producer fits the old seventy-five-minute/192-GiB proposal. Include fresh preparation, pilot reconstruction, operational serialization, full rereads, guards and terminal work. Do not infer a receiver bound from this producer peak. A suitable existing mgnp environment may be used with its true provenance; this recommendation creates no reason to resume the abandoned BASE port.

Keep normal CPU job/accounting controls and all existing GPU reservations, mappings and charges unchanged. Preserve genuine original authority references as historical context where required; they do not become matching candidate GPU authority. Packet 247's `source_publication` and `admission` fields must not be filled with a draft or mismatched artifact and called final. Use a plainly labelled candidate measurement manifest through the same existing supervisor/API, with no claim that the final-source packet passed readiness. This narrow distinction needs root's explicit operational record and normal actual binding review, not a new software subsystem.

## Reuse and duplicate-cost rule

The target identity includes the commit, code hashes, design and protocol hashes. Its descriptor additionally binds actual design/protocol/pilot/target paths and bytes. The receiver source identity also contains the commit and protocol hash. Equal production Python bytes alone therefore do not make a target or measurement reusable under a different commit.

The best case is that root later accepts the same frozen execution commit and its unchanged inputs/export after both native suites pass. Subsequent documentation commits need not force a different execution identity, but root must explicitly adopt the actual tested candidate identity. Promotion still requires independent attribution, fresh source/protection/input/storage checks and the normal final-source decision; it is not automatic.

If a failing test requires a source change, or final publication selects another execution commit/design/protocol/namespace, preserve the early run as candidate diagnostic evidence. Regenerate the required artifacts and measure the applicable final path. Never rewrite a descriptor, transplant hashes, reuse an old GPU admission, or call source-equivalent bytes the same scientific identity. The early CPU run may be duplicated; its value is earlier genuine target size/build/publication evidence and earlier discovery of infeasible RAM or startup costs. It is not guaranteed wall-clock acceleration if the CPU allocation queues or inputs require lengthy preparation.

## Receiver and remaining gates

Do not add a generic RM-shared receiver run merely to claim progress. The native `_validate_prepared_measurement` compares the full deployment context: execution class, CPU architecture/model, cluster/CPU count/memory, and each artifact's resolved path/mount/filesystem/source/device; software and exact references are separately checked. A generic CPU or different-cluster measurement cannot become GPU-host bounds. Root must first identify an actually obtainable CPU-only placement with the required consumer match. If none is available under current authorization, defer admissible receiver measurement and record that concrete blocker. Do not spend a GPU solely to escape it.

Where matching placement is established, an early genuine new-executable receiver and same-process repeat may also be collected provisionally using the existing adapter. Preserve the actual object through the final witness, raw observations, full-launch costs and truthful cache/cgroup scope. It still supplies no production authority handle, upper bound or GPU admission by itself.

Before promotion or GPU work, retain: complete 223 identities in each native environment with all existing controls and terminal aggregation; accepted final execution source; authentic target and applicable receiver evidence; production-handle/full-final-barrier accounting and conservative resource review; fresh original nine prefit numerical cases with aggregate/reconciliation; paired M1 feasibility and all original ledger, mapping, allocation, lease, deadline, protection and model guards. Selected materialization retains its real M2/selection prerequisite. No current gate is waived by moving provisional measurement earlier.

## Limits of this review

Read-only inspection of the named source, original design and accepted adapters. No candidate commit, export, inputs, job, native execution, result or source-to-commit proof was created. Queue and partial-test counts remain root-provided observations. Root owns the next concrete source freeze and actual CPU binding review.
