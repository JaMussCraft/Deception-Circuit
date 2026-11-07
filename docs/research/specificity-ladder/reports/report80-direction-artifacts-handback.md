# Direction preparation and immutable artifacts hand-back

Agent: Codex worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a3-direction-integration.md`, work unit A. Status: handed-back.

## What changed

The orchestrator commits these owned worktree files by explicit file list:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_design.py`: first disjoint cached MMLU validation candidates, retained source split, actual source/instance/donor registry checks, including optional utility donor pools.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_pipeline.py`: canonical preparation retains original assessment membership and utility bytes, freezes separate validation donor maps and operational protocol, and atomically publishes a fresh design/protocol directory. Preparation accepts a separate full execution commit. Its lazy dispatcher blocks absent direction stages explicitly.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_direction_artifacts.py`: numeric-only portable arrays, byte-bound completion markers, immutable fresh publication, exact raw-key shard coverage, profile-bound cache reuse, complete runtime source closure, live parent/protected/grader checks and injected finalization rejection.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_design.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_pipeline.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_direction_artifacts.py`: owning contracts and failure cases.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report80-direction-artifacts-handback.md`: this hand-back; mirrored to `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report80-direction-artifacts-handback.md`. No staged apply operations or RS writes.

The numeric-profile schema agreed with the runner owner requires `padded_width`, `physical_batch_size`, `axis_tile_size`, `dtype`, `backend`, `model`, `model_revision` and `source_sha256`. The optional `profile_id` hashes the entire profile except itself. Model-derived bundle reads must explicitly supply the same profile. Shards require an outer immutable profile, including injected shards.

Bundle layout is `manifest.json`, `arrays/*.npy` and final `COMPLETE.json`; shard layout is `rows.jsonl`, `run_manifest.json` and final `COMPLETE.json`. Readers reject partial targets, extra/changed child bytes, symlinks, object arrays, duplicate/missing keys and identity/profile mismatches. Missing inventory shards remain missing; present incomplete shards block reuse.

Canonical preparation now accepts `commit=FULL_SHA` and optional `injected_code_hashes` only for explicitly injected ancestry. `output=None` performs CPU validation without publication. `output=NEW_ROOT/design.json` requires a fresh root and publishes both `design.json` and `direction_protocol.json` atomically. Historical prepared artifacts were not rewritten.


**Review83 corrections.** The intrinsic cache-path and optional-identity blockers from the independent review are addressed in the artifact module and scoped tests; the pipeline test changes only make its generic fixture explicit. This amendment supersedes the earlier permissive generic metadata behavior. No frozen data or artifacts were changed.

Cached utility paths now require lexical relative-path containment before resolution. Normal snapshot files remain valid, and a Hugging Face snapshot symlink may target a hexadecimal blob directly inside the same dataset repository's real `blobs` directory. Its frozen file hash must match exactly. Absolute paths, traversal, arbitrary external targets, another repository's blob, changed bytes and a redirected blob directory reject. The actual unchanged local MMLU Parquet symlink passes the live guard.

Every scientific numeric bundle now requires a registered kind and strict metadata: `schema_version`, `kind`, `split`, `injected`, plus full `identity`. The identity requires `analysis_split`, `injected`, full A3 `commit`, complete `code_hashes`, original `a1_identity`, `parent_evidence` with prepared/selected/completion file-byte digests and completion payload, `design_sha256`, `protocol_sha256`, `matched_source_hashes`, `ordered_ids`, `streams`, `conditions`, `sites`, `row_identity_sha256`, `grader_sha256`, `model`, `model_revision`, `tokenizer_revision`, `tokenizer_identity`, `numeric_profile` and `capture_lineage`. The row digest binds the ordered source prompt UTF8, token IDs, readouts and native labels. Model/tokenizer/grader identity must agree with the original A1 identity, and the numeric profile must agree with model revision and code-closure digest.

Both writer and reader enforce the schema for every registered scientific kind, including fits, probes, axes and selections. Unknown kinds and aliases reject. Scientific readers require the complete exact metadata object; empty, profile-only or partial expectations reject. Noninjected scientific reads/writes also require equality with the actual current complete runtime closure, so a fabricated complete-looking map cannot bypass absent later source modules.

`capture_reference(path, expected=full_capture_metadata)` reads a strict capture and returns exact manifest/completion file hashes and byte counts, full capture identity digest and shared ancestry/profile digests. Every derived scientific cache requires nonempty references and inherits their original ancestry and physical capture profile. Profile drift breaks those references. Production shard publication/resume applies the same strict identity. Generic fixtures have a separate explicit namespace: `schema_version=1`, `kind='a3_injected_fixture'`, `injected=True`. Generic shard identities additionally require `fixture_schema='a3_injected_fixture_v1'`. Neither seam grants production finalization.

## How verified

All commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`. Initial RED output in `/tmp/a3-unit-a-red.log` showed 12 failures and 44 passes, including absent membership/artifact interfaces. Later targeted RED runs in `/tmp/a3-profile-red.log`, `/tmp/a3-final-guards-red.log`, `/tmp/a3-donor-red.log` and `/tmp/a3-dispatch-red.log` exercised profile omission, external donor omission and missing dispatch. Existing parent-sidecar/stale-source guards already rejected their named failures before the new implementation.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py tests/test_a3_direction_artifacts.py -p no:cacheprovider -q
```

Observed: 75 passed, exit code zero. Output: `/tmp/a3-unit-a-mgnp-final.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py tests/test_a3_direction_artifacts.py -p no:cacheprovider -q
```

Observed: 75 passed, exit code zero. Output: `/tmp/a3-unit-a-base39-final.log`. The existing pandas/bottleneck dependency warning remains.

Actual protected-registry collision tests insert validation instance IDs, source IDs and donor IDs after a successful live check and then attempt a model-loader sentinel. Each overlap raises before the sentinel is reached. Other tests cover changed grader registries, stale parent sidecar bytes, changed cached utility parquet bytes, unchanged parent scientific memberships, independent validation maps and forbidden injected finalization.

The bounded cache check used the canonical tokenizer loader and `ladder_tasks.mmlu_rows(tokenizer,n=128,seed=2)`, followed by `assessment_exclusions(parent)`, `eligible_mmlu(...,n=32)` and the original `mmlu_calibration_maps`. Reproduction script: `/tmp/a3-unit-a-cache-check.py`.

```bash
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python /tmp/a3-unit-a-cache-check.py
```

Observed output is retained in `/tmp/a3-unit-a-cache-check.log`. This is prospective CPU membership checking, not scoring or a production freeze.

```json
{"a1_commit": "5f450dc93dac707af649dee8c8ca60888b2831db", "analysis_split": "validation", "assessment_utility_hash": "ba67e24ea2fa123ae2010994c3439bb036ae5811ff1ce87f7669068264d15184", "candidates": 128, "first_source_id": "all/test-00000-of-00001.parquet:00013910", "maps": 32, "selected": 32, "selection_hash": "5bcf0d7d2d2680e6a0d301904d4d0dc0eee0eeabb8f43a151dd59878fc1915e1", "source_revision": "c30699e8356da336a370243923dbaf21066bb9fe", "source_split": "test"}
```


**Review83 correction checks.** New owning tests invert both reported permissive reproductions and cover omissions, aliases, complete expected metadata, derived capture lineage, production shard propagation and current source closure. Initial targeted RED output records 10 failures in `/tmp/a3-review83-red.log`; schema omission/consumer checks record 31 failures in `/tmp/a3-review83-schema-red.log`. The additional stale production closure reproduction also failed before its guard was added; evidence: `/tmp/a3-review83-source-red.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_artifacts.py -k 'hf_' -p no:cacheprovider -q
```

Observed: 8 passed, including the actual frozen cache layout and traversal/arbitrary-target failures. Output: `/tmp/a3-review83-cache-green.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py tests/test_a3_direction_artifacts.py -p no:cacheprovider -q
```

Observed after all correction edits: 128 passed, exit code zero. Output: `/tmp/a3-review83-mgnp-final.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py tests/test_a3_direction_artifacts.py -p no:cacheprovider -q
```

Observed after all correction edits: 128 passed, exit code zero; the existing pandas/bottleneck dependency warning remains. Output: `/tmp/a3-review83-base39-final.log`.

## Execution evidence

Not applicable: no runs.

No scientific model run, fit, score, benchmark, GPU job or API request is claimed. The CPU test and local cache checks above produced no scientific run manifest. They do not establish a production execution source or any scientific result.

## What is NOT done

Deferred work units B through F own model execution, capture-to-bundle adapters, fitting/selection, workload admission, CLI stages, the job wrapper and final panel aggregation. The production runtime closure deliberately requires those modules and wrapper; Unit A alone cannot create a production-ready freeze. Root must prepare a new lineage only after final implementation and independent review, with the fresh original A1 identity and a separate full A3 source commit.

The stage orchestrator must call `validate_live` immediately before every loader, new shard and resumed shard and retain its returned fresh protected/grader hashes in execution evidence. The low-level byte/row publishers do not themselves admit models or spend. Stage completion and full scientific validity remain separate from byte-complete bundles. Runtime package/CUDA/config/snapshot metadata must be supplied by the actual model-stage producer; no model runtime was instantiated here.

No full-repository suite, model-hook test, production preparation, timing pilot, model access, scheduler command, notebook execution, RS write or git command was performed. There is no production finalization claim. Temporary test logs and the reproduction script are local evidence and are not in the orchestrator's tracked file list.


Review83 corrections do not introduce a production freeze or stage adapter. Downstream adapters must build the strict metadata from actual frozen sources and supply complete expected metadata on every scientific read. Injected scientific schema fixtures use synthetic ancestry explicitly; the positive production shard unit test substitutes a test closure to exercise noninjected schema propagation without manufacturing an actual complete runtime. All real production source, parent and registry checks remain mandatory. No runner, frozen source data, original prepared output or RS-owned file was edited for these corrections.

## Open questions

No scientific ruling is requested. Root should review the fresh-root publication contract and profile schema alongside downstream stage integration. Default: keep the original historical preparation immutable, require complete source closure and explicit live checks, and block production until the remaining units and review finish.
