# Scoped numerical review repair round two

Status: handed-back

## What changed

Review only. **Original B1: addressed. Original B2: addressed within the accepted conditional host-startup lifecycle. Scoped overall spec and quality verdicts: FAIL through the new dry-run regression R1 below.** Accepted scan/context/authority boundaries stay accepted. Whole numerical acceptance and production admission remain separate.

B1 now binds serial donor descriptors to actual typed numeric cache entries, checks ID/condition/stream/readout/map/source provenance, reconciles emitted row mappings/profile/source records, and compares donor membership and source bytes against the independently rebuilt invocation. The original invalid-donor counterexample now rejects while the genuine tiny baseline passes. Targeted anti-forgery tests also reject changed donor source/cache and observed mappings.

B2 now measures all numeric dependencies plus explicit inert final-receipt/startup-record byte envelopes and checks completed payload/marker shape and size before publication. The old measured-versus-executed footprint counterexample now passes. Completed-source authentication and index construction share a fresh process-local path after actual canonical completion. Per-job startup charges, complete guard timing, retained/peak host RAM bounds and CPU/thread/runtime/filesystem provenance are present. Host portability remains explicitly conditional and nonauthorizing; the projector refuses promotion to unconditional host evidence. The scoring process records actual startup separately from immutable pilot data, links bounded shard references to its job/PID/source/scenario record, and checks those linked bytes on final intake. This satisfies the earlier lifecycle ruling without claiming login timing is allocated-host timing.

**R1 — medium: admission dry-run publishes a startup record while claiming no writes.** In `111-round2-evidence/reviewed_runtime.py:855`, preparation calls `_completed_pilot_index` before testing `args.dry_run`. That constructor unconditionally publishes its immutable startup record under `runtime-startup`. The subsequent CLI response reports `writes=false`. A successful `prepare --action admit --dry-run` therefore mutates the work directory, contrary to the unchanged dry-run contract.

The independent test prepares a genuine tiny completed injected serial pilot, then invokes the real CLI dispatch, completed intake, startup constructor and pure projector. Only unrelated live-authority/ledger fixture inputs are injected. Both environments return successfully with `writes=false`, yet file count grows from 23 to 25 through the new startup payload and completion marker. Exact evidence: `111-round2-evidence/test_independent_round2_extra.py`, `111-round2-evidence/extra-mgnp.log`, `111-round2-evidence/extra-base.log`, `111-round2-evidence/run_manifest.json`. The created records are preserved under `111-round2-evidence/dry-run-created-record-mgnp/` and `111-round2-evidence/dry-run-created-record-base/`.

Required narrow repair: preserve read-only provenance/intake checks on dry-run and defer startup-record publication and measured-cost publication to the actual admission action. A dry-run can report the remaining measured-startup prerequisite; it must not execute a publishing constructor before its no-write exit. Preserve the shared real constructor and all B1/B2 checks for the non-dry action.

## How verified

Read the exact round-two diff, relevant source, prior independent failure/lifecycle records and author raw manifests/logs. Author handoff/report prose was excluded. All frozen source hashes match. Runtime is `0401c7a2750cf66ef5508d2dbbaed2f9bcea5f83918d6503e6a8f6b809a44867`; workload is `3e43aaf2b4cacb99df87593ae377c8fdf3eb7b223b258ed8873853841404d8f9`. The exact source overlay and root-supplied documentation commit are in `111-round2-evidence/run_manifest.json`; the runtime and fix diff are preserved there as reviewer evidence.

Reran the preserved independent donor, index/context, byte-witness and guard-footprint oracles against this source. Focused affected owning cases cover donor-source/cache/map tampering, both packed and serial guard envelopes, completed conditional startup/per-job charging, frozen RAM refusal, linked record/PID checks, missing/changed record bytes, and production-shaped completed-versus-running source intake. The new CLI counterexample compares every file byte before/after the dry-run, retaining the valid upstream fixture and generated output.

## Execution evidence

CPU tiny fixtures only; scheduler job/cluster not applicable. The preserved independent suite passes 13 cases per interpreter. The focused owning selection passes five cases per interpreter. Those commands exit successfully. The new dry-run regression fails one case per interpreter, with unsuccessful test-command exits and a successful CLI exit inside the fixture. Exact commands, exit codes, hashes and results: `111-round2-evidence/run_manifest.json`; logs: `111-round2-evidence/original-mgnp.log`, `111-round2-evidence/original-base.log`, `111-round2-evidence/owning-mgnp.log`, `111-round2-evidence/owning-base.log`, `111-round2-evidence/extra-mgnp.log`, `111-round2-evidence/extra-base.log`.

Baseline assertion: the unchanged independent contract suite passes 13 cases in mgnp against 13 in base; previously failing donor and footprint cases are included. Dry-run baseline starts with 23 files in each environment and ends with 25 in each, despite its explicit no-write response. These are integrity and CPU-fixture results, not scientific observations or native GPU timing. Evidence: `111-round2-evidence/run_manifest.json`.

## What is NOT done

No source edits, git, RS writes, scheduler access, GPU, large weights, APIs, notebooks or subagents. No full-proof audit, broad author suite or large native scenario. No production admission, actual H200 timing, target-host portability claim or whole Unit F acceptance. Original failed-source evidence remains intact. The future full bounded pilot/calibration/assessment/summary verification remains required after final scoped source acceptance.

## Open questions

Root should coordinate only the publishing-before-dry-run repair and a bounded independent closure. Default: preserve the current source freeze and original R1 evidence until that coordination. Original B1/B2 do not require another broad review unless the narrow repair changes their accepted seams.
