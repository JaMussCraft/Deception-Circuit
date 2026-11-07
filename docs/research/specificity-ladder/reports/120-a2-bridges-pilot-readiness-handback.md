# Independent Bridges timing pilot readiness handback

Status: handed-back

## What changed

Scoped source/spec and orchestration-quality verdict: **PASS for one bounded timing-only SDR D/I attempt**, with the corrected scheduler authorizer. This does not admit scientific results or migration. Application execution source remains frozen at `6bd8bf5334f2e83613a129d2fcfeacf83e762191`. The separate build/materializer identity is retained in receipts rather than conflated with execution source. [Exact bindings](120-a2-bridges-pilot-readiness-evidence/run_manifest.json).

The accepted deployment binds the physical Bridges project into the original absolute namespace inside a genuine Ubuntu container. Original archive, snapshot, operational timing config, authoritative inputs and manifests remain byte identical. The explicit operational config is required; the archived default has a different output root. Raw versus canonical config/build digests and authenticated relocation of the training script are reconciled. [Local checks](120-a2-bridges-pilot-readiness-evidence/local-check.json), [deployment cross-check](120-a2-bridges-pilot-readiness-evidence/deployment-crosscheck.json), [native provenance reconciliation](120-a2-bridges-pilot-readiness-evidence/H200-provenance-reconciliation.json).

The root resource envelope is fifty minutes on one typed H100, with four CPUs and the declared host memory. The original planned schedule is retained, while the actual timing run uses twenty epochs and a twenty-epoch cosine schedule. It repeats the old timing experiment rather than a prefix of the full scientific schedule. [Exact resource and cap fields](120-a2-bridges-pilot-readiness-evidence/run_manifest.json).

## How verified

Independently checked every local transfer row, frozen ordinary source file, archive member and declared link; invoked the real frozen CPU planning path for both arms, including actual Arrow rows, labels, readout and prompt proofs. Exact non-script command arguments and resolved configs match saved native references; the relocated script is authenticated by byte identity. Compared actual remote wrapper dry-run output against those local plans. Root-produced remote source, namespace, full model-cache byte checks and actual post-activation cache lookups were examined locally; the reviewer made no remote or model calls. [Local proof](120-a2-bridges-pilot-readiness-evidence/local-check.json), [remote bindings](120-a2-bridges-pilot-readiness-evidence/deployment-crosscheck.json), [packed activation cache probe](120-a2-bridges-pilot-readiness-evidence/post-activation-cache-probe.json).

The loader does not pass an explicit model revision. Therefore the checked current cache reference, explicit hub-cache environment, offline mode and fresh per-arm reference/metadata checks are load-bearing. The actual packed activation resolves the intended snapshot through the hub cache. Initial root full shard hashing is preserved; per-arm checks additionally bind shard size and content-addressed target. No claim of repeated full shard hashing is made.

Read the outer launcher and bounded authorizer. Genuine success receipts pass; malformed success/source/purpose cases and incomplete, duplicated or wrong-hash registry authorization lists reject. Fresh real local wrapper preflights authenticate both current empty protection catalogs; catalogs must remain stable through copying and remote hashing. Authorization is atomic, short-lived, job/arm/source-bound and fails closed on newly protected sets. [Independent closure](120-a2-bridges-pilot-readiness-evidence/launch-closure.json), [actual preflights](120-a2-bridges-pilot-readiness-evidence/authorizer-check-D-preflight.json), [other arm](120-a2-bridges-pilot-readiness-evidence/authorizer-check-I-preflight.json).

The final scheduler delta uses actual Bridges `TRES` when `AllocTRES` is absent, then requires an exact GPU count and typed `TresPerNode`. Independently executed those exact parser/guard AST nodes against the genuine held scheduler record: the held state rejects; a test-only running-state clone accepts; wrong count, type and account reject. This is a fixture transport test, not evidence of a running allocation. [Scheduler closure](120-a2-bridges-pilot-readiness-evidence/scheduler-delta-closure.json).

## Execution evidence

The final launcher hash is `1d293dc473af7406048fd7d007d72336a24594c73971338c5c690501d7e518a8`; job wrapper hash is `f9a40ccc39b16f79536a8bf08641d6e7819624ab865e7a5a6019becfc524cc51`; corrected authorizer hash is `80b7d88535d5cf145082b493f2e9fc42ff3dab8fc7d13668ab82bde6156e337c`. Previous authorizer acceptance is superseded only for this scheduler-format repair. Original failed probes, the earlier manifest and prior authorizer remain preserved. [Current manifest](120-a2-bridges-pilot-readiness-evidence/run_manifest.json), [delta](120-a2-bridges-pilot-readiness-evidence/scheduler-delta-closure.json).

The actual held scheduler record has zero runtime and the intended allocation shape. Root reports registration and successor mapping completed; this review did not create or mutate those objects. Root also reported an initial release followed immediately by re-hold after the scheduler-format failure, without model execution. The accepted delta does not reinterpret that failed check as a successful admission. [Held record](120-a2-bridges-pilot-readiness-evidence/held-job.txt), [recorded root registration](120-a2-bridges-pilot-readiness-evidence/run_manifest.json).

The cold-load envelope includes all independent model constructions. It is an exploratory allowance, not a measured H100 forecast or guarantee both arms finish. Before the second arm, the launcher checks the live remaining lease against its fixed floor and observed first-arm walltime allowance, then checks again after fresh authorization. An insufficient lease retains the first arm and stops without shortening the second or extending the reservation. [Exact arithmetic and predicate](120-a2-bridges-pilot-readiness-evidence/run_manifest.json).

## What is NOT done

No reviewer source edits, remote access, scheduler actions, reservation writes, model loading or GPU work occurred. No scientific efficacy, cross-device equivalence, full vocabulary comparison, fixed-mask retraining equivalence or fleet admission is claimed. The initial comparison fixture incorrectly required the historical script location; the corrected comparison authenticates the same bytes and exact remaining arguments, with the initial failure retained.

Saved native references support paired selected-logit and decoded-choice checks for unpruned test rows and pre-update validation rows. Later trained endpoints are retraining drift diagnostics. Actual legacy token arrays, full vocabulary tensors and optimizer checkpoints were not saved. Any nonzero pretraining drift requires independent review before fleet work under the predeclared plan. [Reference rules](120-a2-bridges-pilot-readiness-evidence/H200-predeclared-comparison.json), [saved schema](120-a2-bridges-pilot-readiness-evidence/H200-reference-schema.json).

## Open questions

No concrete timing-launch blocker remains in the reviewed bytes. Root must keep the bounded authorizer alive or re-arm it after a long queue, obtain fresh live ledger/allocation/catalog checks at actual execution, enforce the existing charge/caps, and retain receipts even on partial completion. A test-only scheduling estimate is not a start-time promise.

Later scientific Bridges intake needs an explicitly reviewed hardware, namespace, placement and returned-artifact contract while preserving full scientific epochs, timing exclusion, source/archive/config/input/export checks and original evidence. The current comparison audit does not simply reject all non-Delta hardware by name; its exact original fleet/path/source contracts must be reconciled deliberately. Returning the same virtual output names must not overwrite local native references. Timing, numerical drift and intake reviews precede any migration or cancellation decision. [Concrete future intake changes](120-a2-bridges-pilot-readiness-evidence/future-scientific-intake.json).
