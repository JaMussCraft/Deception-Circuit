# Hand-back: A2 CPU comparison independent review

Agent: Sol independent reviewer. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a2-analysis.md`, `Task1`. Status: handed-back.

## What changed

Current scoped re-review recommendation: accept the admission fixes. The initial P1 findings and model revision concern below are closed by code inspection, scoped tests and independent mutation replay. No new blocker was found within the requested closure scope. No implementation files were edited, and the author report was not read.

Initial review follows as historical evidence; its request-changes recommendation is superseded by the closure below.

- Orchestrator commit file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/77-a2-comparison-review-handback.md`.
- Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/77-a2-comparison-review-handback.md`.

**P1 — Authenticate the materialized dataset against frozen authoritative rows, not caller-provided native hashes.** Location: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a2_mask_comparison.py:232`. The build hash is correctly recomputed indirectly by `_private_configs`, but that helper checks only private configuration metadata. The native file loop checks each listed file against the hash in the same caller-supplied manifest, and requires only the dataset configuration file. It does not require a complete Arrow inventory or bind Arrow contents to the frozen build's source rows/token proofs. The fixture already admits no Arrow files at all. Adding invalid bytes as an Arrow file and updating the native hash and enclosing artifact hash still returns `complete_cpu_audit`. This permits wrong private training data under unchanged cohort ids, build, ruling and configuration. Reuse the existing `_stored_rows` authentication or a previously authenticated, frozen materialization inventory with complete coverage; add wrong-row, omitted-shard and self-consistent replacement tests. The wrapper's preflight uses `_stored_rows`, but the comparison does not authenticate that historical invocation against a trust anchor, so its self-consistent receipts do not establish it.

**P1 — Pin execution files implementing the mask semantics.** Location: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a2_mask_comparison.py:26` and `:233`. The frozen source map omits `analysis.py`, `l0.py`, model wrappers and other executable training dependencies. Native manifests ordinarily hash the entry script only; any additional source hashes are accepted when they match caller-supplied files. A fabricated `analysis.py` implementing unrelated mask extraction, listed in native provenance with its correct new hash, passes the complete comparison without modifying any frozen source hash. The string execution commit does not authenticate the omitted files. Pin the scientific execution dependency inventory to the accepted source snapshot, including native gate/export implementations, then reject omitted or substituted dependencies. This can remain a CPU file audit without git or model loading. A concrete existing anchor is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/snapshot.json`: its file SHA is `eb5ca854a7157529095ab820252a246f114250144120c6fc66de98bed9733918` and its `source_files_sha256` map contains `207` files. This review read that metadata only. The orchestrator reports the snapshot is bound by the fleet plan and checked before submission; the consumer currently does not bind or audit its map. Data/output symlinks need the separate dataset checks above.

**P1 — Validate full scientific defaults against a frozen expected config.** Location: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a2_mask_comparison.py:222` and `:312`. `expected_config` covers a subset of `node_config`; fleet equality checks only consistency between seeds. Uniform changes to `lambda_attention_heads`, `lambda_mlp_blocks` and `depth_penalty_scaling` pass after config/native/artifact hashes are updated. The synthetic mutation used zero head/block sparsity weights and depth scaling `10`, retaining the original training argv and frozen source files. The result is `complete_cpu_audit`. These settings change the training objective despite the frozen global sparsity setting. Freeze the full resolved config from the approved execution defaults and permit only explicit task/seed/cohort fields to vary. Test uniform wrong defaults in addition to the existing single-seed drift test.

Additional provenance concern: changing every native `model_revision` to the same unrelated valid hex string also passes. The current check detects cross-seed drift but does not authenticate the approved revision. Bind an expected revision if the training source contract is intended to guarantee that model snapshot.

The typed set implementation follows the frozen algebra: disjoint head/MLP keys, D-minus-I, shared/reverse/union membership, all pairwise mixed Jaccards, undefined empty unions, vacuous head containment, coexistence of head containment and exclusive MLPs, and raw native result retention. The native export review agrees with `extract_active_nodes`, `extract_node_masks`, finalization and the distinction from `get_num_active`; no membership cutoff based on count diagnostics was found. The missing-fleet path raises before a comparison is returned. Bank preparation and effect scoring are intentionally deferred and do not block this bounded comparison task.

Closure review: `_audit_execution` now pins the snapshot, archive and fleet plan hashes, checks every frozen dependency, rejects redirected source paths, binds live links and the exact fleet cell/input paths. `_authenticate_rows` checks referenced private Arrow shards, invokes `_stored_rows` against frozen source inventories/row hashes and recipient/reference proofs, and requires complete native dataset inventory equality. Config equality now uses the full native resolved defaults, including structural weights and depth scaling. Native model revision must equal the approved revision. These changes close the originally reported source, dataset, uniform-default and model-snapshot gaps without changing the five-path input API or training execution. The preexisting algebra and later scoring stages were outside the closure review.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a2_mask_comparison.py -q -p no:cacheprovider
```

Observed: `35 passed in 2.77s`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a2_mask_comparison.py -q -p no:cacheprovider
```

Observed: `35 passed in 2.99s`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/a2_review_mutations.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 /tmp/a2_review_mutations.py
```

The independent reproducer imports the existing test fixture, using its synthetic anchors unchanged for each mutation. Each case starts fresh and rehashes only mutable receipt/native/artifact layers. It changes no production source or scientific data. Observed in both interpreters:

```text
baseline synthetic complete_cpu_audit
uniform wrong gate weights/depth complete_cpu_audit
substituted analysis source complete_cpu_audit
wrong self-consistent Arrow files complete_cpu_audit
uniform wrong model revision complete_cpu_audit
```

Reproduction details: call `tests/test_a2_mask_comparison.py`'s `fleet.__wrapped__(tmp_path, MonkeyPatch())`; for each source update native `manifest_hash` and receipt `artifact_sha256` after modifying a file. For config changes also update native `config_sha256`. For the source case write an execution-root `analysis.py` containing `def extract_node_masks(model): return {}` and add its file hash to each native `code_sha256`. For the dataset case write arbitrary non-Arrow bytes to each private task's `train/data-00000-of-00001.arrow` and add its hash to native `dataset_files`. Pass all fixture records to `compare_masks`. No anchor replacement is performed after fixture setup.

The real timing receipt was inspected only for schema/provenance and exercised by the existing negative admission test. Its timing purpose is rejected before native mask/results loading. No current full-training mask or outcome was consumed.

Scoped re-review commands used the same working directory and thread limits:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a2_mask_comparison.py -q -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a2_mask_comparison.py -q -p no:cacheprovider
```

Observed: `53 passed in 19.04s` on mgnp; `53 passed, 1 warning in 17.26s` on base. The base warning reports the installed optional bottleneck package version; no test was skipped or failed.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python /tmp/a2_review77_closure.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 /tmp/a2_review77_closure.py
```

The independent replay adapts the original mutation logic to the updated real-Arrow fixture, preserving that fixture's anchors after construction. It also calls `_audit_execution` on the real frozen fleet's metadata only, and compares the real timing configuration against `_expected_scientific_config`. Both interpreters exited `0` and printed:

```text
baseline synthetic complete_cpu_audit
uniform wrong gate weights/depth REJECTED full resolved configuration differs from frozen scientific defaults
substituted analysis source REJECTED frozen dependency file hash mismatch: analysis.py
wrong self-consistent Arrow files REJECTED authoritative private row authentication failed: Expected to read 1313821271 metadata bytes, but only read 38
uniform wrong model revision REJECTED missing/wrong approved native model revision
actual frozen execution metadata 18 cells 207 dependencies PASS
actual timing resolved config matches full frozen defaults PASS
```

The source snapshot and fleet metadata checks read no full scientific receipt, mask or result. Real Arrow data/outcomes were not used to exercise the fixes; the row authentication tests use fabricated Arrow datasets.

## Execution evidence

Local CPU tests and synthetic mutations only; no scientific model run is claimed. Both pytest commands exited `0`; both mutation commands exited `0`. Test count and output are recorded above. Synthetic baseline and each mutation returned `complete_cpu_audit`; this baseline is a software fixture and supplies no scientific replication claim. No training rows were assessed and no scientific comparison artifact was published. A scientific `run_manifest.json` and baseline metric comparison are not applicable to this review; scientific results remain not yet verified.

Live quota command `/u/swong2/.local/bin/codex-usage --pause-at 80` returned `status: ok`, weekly `used_percent: 21`, `remaining_percent: 79`, `should_pause: false`, reset `2026-11-06T16:07:41+00:00`.

Closure execution evidence: local CPU test suites and independent mutation commands above exited `0`; the synthetic baseline remained `complete_cpu_audit` while every original exploit was rejected. Real metadata coverage is recorded in the command output above. No scientific baseline replication or model run is claimed. The live quota remained `21` percent spent and `79` percent remaining, with no pause requested, reset `2026-11-06T16:07:41+00:00`.

## What is NOT done

No production source changes, git, additional agents, GPU, Slurm, API, model weights, notebook execution, broad tests, full fleet scientific audit, ladder outcomes or author-report reading. The closure accepts the bounded admission implementation; a complete scientific fleet audit and any specificity claim remain unperformed.

## Open questions

No open blocker remains in this scoped closure. Default: the orchestrator may integrate the admission fixes, retaining the requirement that all scientific sources pass before publishing comparison memberships. This hand-back does not authorize or claim completed effect scoring or scientific results.
