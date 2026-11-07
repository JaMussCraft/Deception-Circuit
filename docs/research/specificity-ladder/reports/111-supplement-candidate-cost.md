# Supplemental scoring lookup and cost review

Status: handed-back

## What changed

Review only. **B2 — repeated full candidate validation is absent from the measured cost accounting.** Original B1 remains unchanged. In `component_analysis/a3_direction_runtime.py:679`, scoring calls `_validated_measurement` before comparing each candidate's immutable profile. Even a cached completed proof performs a fresh full witness check. Each witness includes the common selected numeric backing, so rejected candidates repeatedly reread that same tree. The matching candidate is refreshed again inside `freeze_profile_reuse`. The runner subsequently validates reuse through `_geometry` and its separate exact-cell check.

The owner's scan records eighteen completed calibration attestations selecting candidate 47 from 63. Those are source-bound observations of an incomplete injected run, not completed scientific evidence. The independent tiny call-count fixture executes the frozen candidate-loop AST and actual cached-proof access path: candidate 47 causes 48 shared-backing refreshes before the runner. Source inspection identifies two further runner refreshes. Both interpreter outputs agree. Evidence: `111-numerical-evidence/owner-calibration-candidate-scan.json`, `111-numerical-evidence/candidate-lookup-mgnp.log`, `111-numerical-evidence/candidate-lookup-base.log`, `111-numerical-evidence/run_manifest.json`.

The inventory prices eight guard refreshes per shard, additional capture refreshes and job boundaries. The measured guard refresh deduplicates common proof dependencies, including the selected backing, before its full witness pass. Pilot runner timing uses `measuring=True` and never executes the target scoring candidate scan or target reuse validation. Startup proof validation is charged separately, but repeated scoring lookup has no corresponding measured operation/count. The fixed workload buffer supplies no demonstrated conservative bound for this candidate-dependent repeated work. This is an unrepresented runtime cost, not an exact wall-clock underestimate quantified by this review. Evidence: `component_analysis/a3_direction_workload.py:719`, `component_analysis/a3_direction_runtime.py:1371`, `component_analysis/a3_direction_runtime.py:1033`.

## How verified

Read the scoring, packing-validation, reconciliation and measured-cost paths. The small fixture compiles the unchanged candidate-loop AST, uses fake cache entries solely to count refresh callbacks, and executes the real `_validated_measurement` and completed-proof refresh path. It performs no proof construction, numeric validation or backing-file reads and grants no authority. A fixture inventory independently reproduces the guard-count formula. Probe: `111-numerical-evidence/probe_candidate_lookup.py`.

A validator-minted immutable profile/axis index can remove rejected-candidate I/O without weakening the contract. It must be process-local, bind the exact completed receipt/reference and source/stage/runtime profile, own immutable children, and preserve exact axis/site/operation, donor, mask-branch, target bytes and measured-versus-target semantics. Profile equality alone is insufficient. Index selection is only metadata lookup; it must not become execution authority.

Before every actual model boundary, perform one deduplicated full content-byte refresh over the complete referenced receipt/backing dependency union and fresh live source/protection/ledger/allocation/cap/deadline checks. Reuse the immutable result only within that bounded operation; do not reuse live authority across boundaries. Continue periodic deadline checks during pure work, reject changed backing before further model work/publication, preserve fresh shard/resume checks and retain a final byte check before publication. Measure and price index construction/retained memory, each boundary refresh and exact per-target checks. This is a conditional design constraint, not acceptance of an implementation that does not yet exist.

## Execution evidence

CPU fixture only; scheduler job/cluster not applicable. Both interpreter commands exit successfully. Observed pre-runner shared-backing refreshes: 48 against expected 48. Observed guard batches in the tiny inventory: 773 against expected 773. Baseline reproduces: the mgnp refresh count 48 equals the base count 48. Exact commands, source overlay hashes and counts are in `111-numerical-evidence/run_manifest.json`; raw logs are `111-numerical-evidence/candidate-lookup-mgnp.log` and `111-numerical-evidence/candidate-lookup-base.log`.

No scientific row panel or scientific provenance claim exists for these control-flow counts. The full native run remains incomplete evidence pending root's completed result.

## What is NOT done

No source edits, git, RS writes, scheduler access, GPU, weights, APIs, notebooks, subagents, full-proof audit or native rerun. No broad reopening of accepted authority behavior. No numeric runtime speedup, scientific completion or production admission is claimed. Original B1 report and evidence remain preserved.

## Open questions

Root should include B2 in the bounded repair and require independent call-count, mutation, exact-scope and measured-overhead closure. Default: preserve the current source freeze and incomplete native artifacts until root coordinates the stop/reopen. The immutable index and deduplicated boundary proposal is acceptable in principle only under the checks above.
