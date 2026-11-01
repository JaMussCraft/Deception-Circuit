# SDR session integration review

Read-only preparation dated2026-10-31. No Git refs/index/main mutations, merges, worktree changes, real-model inference, notebooks, jobs or APIs. User signal is still required before integration.

## Ancestry and inventory

- Common routing/main base: `aef064a27b7a86a0e4a3678894845cb8b8024e8c`.
- Routing tip: `695b126a9d5fe3045c9b5872fac7441d8fcdeec2`;16 session commits,27 additive files,11,874 insertions.
- H100 tip: `e240ecc0809dd56d3abdadf6e6cd6d88a60094b3`; branches share `ca41bfdb2fd4e4c4c784eabd321ea75e41a45299`. H100 has exactly one unique commit; routing has four unique later commits (`645eb5f`, `2949214`, `4f02784`, `695b126`).
- Initial main snapshot `6f5c78b66a4e659ec48733013dcd80feac98b568`: zero changed-path overlap with routing since their common base. Main moved during review; disposable snapshot pins `5c63bcaa502764fb3a1b9c5c35f5fd1668f90371`. Re-read main and overlap after user release.

Exact routing additions:

- `scripts/jobs/run_sdr_clause_choice.sh`
- `scripts/jobs/run_sdr_cue_circuits.sh`
- `scripts/jobs/run_sdr_cue_positions.sh`
- `scripts/jobs/run_sdr_cue_probe.sh`
- `scripts/jobs/run_sdr_native_controls.sh`
- `scripts/jobs/run_sdr_shared_composition.sh`
- `scripts/sdr_clause_choice.py`
- `scripts/sdr_completion_diagnostic.py`
- `scripts/sdr_completion_diagnostic.sbatch`
- `scripts/sdr_cue_circuits.py`
- `scripts/sdr_cue_positions.py`
- `scripts/sdr_cue_probe.py`
- `scripts/sdr_native_controls.py`
- `scripts/sdr_routing_pilot.py`
- `scripts/sdr_routing_pilot.sbatch`
- `scripts/sdr_routing_validation.py`
- `scripts/sdr_routing_validation.sbatch`
- `scripts/sdr_shared_composition.py`
- `tests/test_sdr_clause_choice.py`
- `tests/test_sdr_completion_diagnostic.py`
- `tests/test_sdr_cue_circuits.py`
- `tests/test_sdr_cue_positions.py`
- `tests/test_sdr_cue_probe.py`
- `tests/test_sdr_native_controls.py`
- `tests/test_sdr_routing_pilot.py`
- `tests/test_sdr_routing_validation.py`
- `tests/test_sdr_shared_composition.py`

Exact H100-only modifications (relative to ca41):

- `scripts/jobs/run_sdr_cue_circuits.sh`
- `scripts/sdr_cue_circuits.py`
- `tests/test_sdr_cue_circuits.py`

H100 changes make the cue wrapper derive repository cwd from its own path, bind Delta versus Bridges2 Slurm timezones, validate actual epoch/duration bounds, add explicit `--alignment-root` for freezes, relocate design/suite/mask lookup, and extend source hashes with `analysis.py`, `config.py`, `l0.py`. No scheduler submission or automatic enablement is introduced.

## Compatibility and provenance

Merge routing first, then H100. The27 routing paths have no main overlap at the initial snapshot; the three H100 paths are unchanged on routing after ca41, so the second merge should apply cleanly. This is a path/ancestry assessment, not an executed merge-tree or actual merge.

Mechanical cleanliness does not imply old frozen protocols can execute against the merged tree. The source closure recursively includes all Python in component_analysis/models/dataset; current main changes many of those files. H100 also changes the cue source/protocol contract. In particular sdr_cue_positions.build_protocol calls cc.verify_protocol on immutable ca41 parent; H100 now demands changed source hashes and provenance.alignment_root. Existing parents lack the latter field and normally fail source-drift verification earlier. Tests can mock that verifier, so even a passing suite cannot certify historical protocol replay.

Keep archived source commits and all frozen manifests/source hashes unchanged. Preserve output bytes at their existing relative paths in primary outputs and ignored .superpowers evidence separately. Do not rewrite absolute paths inside evidence to make relocated execution work. Historical reproductions must use the original source environment and appropriately preserved inputs; integrating dormant scripts is not authorization to run H100 or restart any stopped assay.

Wrappers other than the H100 cue wrapper still pin the original routing worktree cwd; main integration is archival and does not make them deployable. Tiny synthetic tests do not verify GPU numerics or new hardware equivalence. Cached tokenizer/weight-file hashing may occur, but no real weights were loaded.

## Focused verification

All commands pin OMP_NUM_THREADS=1, MKL_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1; use PYTHONDONTWRITEBYTECODE=1 and pytest -p no:cacheprovider. Environments: `/sw/external/python/anaconda3/bin/python` and `/u/swong2/.conda/envs/mgnp/bin/python`.

| File | Combined snapshot collected cases |
| --- | --- |
| `tests/test_sdr_clause_choice.py` | 31 |
| `tests/test_sdr_completion_diagnostic.py` | 44 |
| `tests/test_sdr_cue_circuits.py` | 64 |
| `tests/test_sdr_cue_positions.py` | 51 |
| `tests/test_sdr_cue_probe.py` | 19 |
| `tests/test_sdr_native_controls.py` | 33 |
| `tests/test_sdr_routing_pilot.py` | 42 |
| `tests/test_sdr_routing_validation.py` | 32 |
| `tests/test_sdr_shared_composition.py` | 32 |

Fresh H100 original-worktree focused tests: base 64 passed / 1 warning in51.85s; mgnp 64 passed in44.57s. Logs `h100-base-tests.log`, `h100-mgnp-tests.log`.

Original-routing nine-file test runs were deliberately terminated before completion after discovering completion tests publish new synthetic artifacts under outputs. Partial progress showed no reported failure; these runs are INCOMPLETE, not PASS or failure. Tracked routing 27 files and H100 18 files freshly compared byte-for-byte against their Git tips: zero mismatches.

The six newly generated pytest-cpu/pytest-annotations-source/pytest-annotations-joined directories contain60 files / 112,100,578 bytes, classified in artifact-inventory.json synthetic_oct31_summary. Tests use exclusive new_output creation; no preexisting regular-file size/mtime changed in the refreshed inventory check. No original pretest SHA256 inventory existed, so this is not a complete byte-level pre/post proof. See test-artifact-changes.json; preservation root performs actual destination hashing.

Disposable combined snapshot recipe: git archive the pinned main tracked tree; overlay27 routing Git blobs; overlay three H100 Git blobs. Independently copy routing outputs/_analyses and .superpowers fixtures; no symlinks remain in copied outputs. This avoids writes through to historical evidence. `integration-snapshot-recipe.json` records exact commits and final SHA256 of every session source path. Snapshot is not a Git worktree and has no source fixes.

Pre-fix combined snapshot nine-file suites FINISHED: base 11 failed / 331 passed / 3 skipped / 3 errors in 364.84s; mgnp 11 failed / 334 passed / 3 errors in 325.14s. Failure node sets are identical. Both used a 900s bound per environment. Logs `integration-base-tests.log`, `integration-mgnp-tests.log`; collect inventory `integration-collection.log`. Actual-main validation remains required after release.

## Full-suite limits and release sequence

No full suite or tests on live main were run by this worker while another session integrated. Historical primary-checkout baseline has seven known failing node IDs; older worktree baseline adds MASK repo-root location failure. These are historical names, not a fresh claim about today main:

- `tests/test_deception_common.py::test_three_specs_registered`
- `tests/test_deception_common.py::test_pressure_pools_are_well_formed[ser]`
- `tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[far]`
- `tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[sdr]`
- `tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[ser]`
- `tests/test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap`
- `tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms`

After explicit user release: record fresh main HEAD/clean tracked state and confirm concurrent owner is finished; verify output preservation and historical snapshots before cleanup; merge routing then H100; run the same nine session suites in both environments against copied writable evidence or otherwise prevent synthetic additions from contaminating research evidence; run focused component hooks/model compatibility regressions if dependencies changed; compare any broader suite failures by exact node ID against a fresh same-main baseline. Test-created synthetic artifacts are not scientific outputs. Do not execute archival manifests with changed hashes or alter tolerances. Remove only this session worktrees/branches after source integration and preservation receipts prove coverage.


## Pre-fix combined snapshot failure classification

Both initial combined runs completed. Findings below are exact fixture limitations, not permission to relax production checks.

- Completion amendment fixture: three errors in `test_operational_amendment_preserves_science_and_old_provenance`, `test_amended_main_accepts_measured3208_but_retains_historical_3000_fail`, `test_operational_amendment_rejects_changed_scientific_payload`. `ORIGINAL_CODE` uses current absolute CODE_ROOT keys while archived manifest keys bind the historical routing path. Reproduced the same three errors on a separately archived, relocated 695b126 control: `routing-control-amendment.log`. Thus relocation alone causes these errors, without merged main or H100. Repair tests with a synthetic copied temporary original/calibration and consistently patched exact binding constants; retain all source, budget and scientific-payload tamper checks.
- H100 source inventory test: all six missing/changed × analysis.py/config.py/l0.py cases fail their hardcoded closure size 60 (actual78) after main adds local modules. Historical H100 focused test64 passed. Repair to exact path-set equality derived from inherited cue source closure union NEW_SOURCES union the three added files, plus exact per-file SHA256 comparisons; preserve mutation rejection.
- `test_portable_build_roots_and_persisted_rebuild` fails at immutable parent inherited-source verification (`component_analysis/attention_patterns.py`), since main changed that module. Detailed traceback: `portable-build-isolated.log`. Repair the test parent fixture to bind an isolated current source closure with exact temporary PARENT_SHA/PARENT_SCIENCE; keep parent tamper/source tamper coverage. Production rejection is correct.
- Cue probe `test_rank_crossing_render_and_hash_selection` hardcodes source closure size 54 (actual72); replace with exact inherited source path-set plus NEW_SOURCES and matching hashes.
- Position `test_actual_wrapper_dryrun_calibration_main_resume` and cue probe `test_wrapper_and_cli_modes` invoke wrappers from relocated ROOT, but their production guards require the historical absolute routing worktree cwd. For relocated checkouts, test the actual unchanged wrapper rejects the cwd; retain actual dryrun assertions only when running at the approved historical path. Do not mock away its guard, change historical wrappers or imply archived run release.

The test portability worker owns five approved test files in the disposable snapshot and was released for edits only after both initial suite processes finished. Original pre-fix logs must remain intact. Main/index and historical worktrees remain untouched.


The remaining eleventh failure, `tests/test_sdr_routing_validation.py::test_sources_use_real_sample_json_and_exclude_prior_stories`, expects 25 historical component sample files but the current shared primary evidence contains 26. This test builds fresh metadata from live primary outputs; the historical count is stale. Proposed repair independently enumerates exactly all SDR sample.json paths, hashes those files, derives union of instance IDs and SDR/test intersection, independently reads selective source IDs, and retains both native/fresh leak assertions. Historical immutable manifests remain unchanged. The caller's requested fixture coverage is current-unit validation, not exact reproduction of an old panel.

Pre-fix full failure inventory is preserved in both integration log summaries. Base skips are 3 environment-specific cases; mgnp has no skips. The original-worktree runs were interrupted, and these are not substituted as original-source full-pass evidence. Post-fix changed-file tests and independent source review are complete; actual main integration remains gated on the user signal.


## Test-only repair review

Independent source review PASS for the five approved test files in `test-portability/portability-tests.patch`. No production guards, provenance validators or archived manifests are changed. Fixed counts become exact independently enumerated path sets and SHA256 dictionaries. Synthetic parent provenance hashes are internally consistent; temporary dependency mutation still triggers real production source rejection. Amendment checks use a self-contained exact-bound synthetic release and timing fixture; a 3208-second synthetic forecast exercises allocation math, not the historical calibration receipt. Relocated wrapper tests exercise real guard rejection, while the historical approved path retains its original dryrun branch. Exclusion checks independently derive actual sample/source/story unions. Optional future strengthening: derive SDR-test source IDs independently too rather than using the producer's source_ids_by_dataset field for that one intersection; current independent all-component and exclusion checks remain intact.

Changed-file dual-environment validation PASS: base 210 passed / 3 environment warnings in 267.42s; mgnp 210 passed / 1 environment warning in 233.99s, both exit 0. Logs are `test-portability/green-base.log` and `green-mgnp.log`. Combine these five suites with the four unchanged suites that already passed the initial combined runs. Do not describe that union as a freshly rerun full nine-file suite. No broader rerun is required absent a new issue.

## Cleanup-independent checks versus archival fixtures

The nine-file snapshot runs currently retain the historical source worktree. They do not demonstrate the full tests survive its removal. In particular completion's `frozen` fixture calls build_completion_manifest, which hashes the immutable baseline parent's 1 absolute prior-pilot manifest and 14 code_sha256 files beneath the original routing worktree even if the parent output directory itself was copied. These seven direct fixture consumers need the historical source paths restored:

- test_all1280_parent_ids_and_prompt_bytes_unchanged
- test_original_baseline_batchorder_reconstructed
- test_calibration_rows_excluded_main_and_rubric_frozen
- test_prefix115_no_truncation
- test_parent_numeric_pass_capability_fail_is_valid_diagnostic_entry
- test_cpu_dryrun_writes_planned_rows_without_loading_model
- test_full_annotation_export_missingness_and_join_cli

Cue/position tests also read ignored fixtures at ROOT/.superpowers/sdd and relative ROOT/outputs. Preserve those under the agreed external preservation namespace; do not populate main .superpowers or alter contracts simply to make default main tests standalone. For an archival check, restore fixture copies into an isolated checkout at their recorded relative paths. For a historical scientific replay, recreate the original routing worktree at the manifest's recorded source revision and its recorded absolute path, restore its bound output dependencies and use the recorded software/cache/hardware computation path. The merged H100/current-main tree cannot substitute for those historical source hashes. Do not edit archived path or source hashes.

A practical small unit check after cleanup runs from the primary Deception-Circuit checkout:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 timeout 300 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_sdr_clause_choice.py tests/test_sdr_native_controls.py
```

This is 31 clause cases plus 33 native-control cases. The same command can use `/sw/external/python/anaconda3/bin/python` for the base environment. Its only root-scratch prerequisite is `/projects/beto/swong2/Alignment/.scratch/sdr-native-controls/selection-audit.json`, plus tracked pool JSONs, installed CPU test dependencies and writable pytest temporary storage. Native build_protocol copies the audit's historical-reference paths as metadata; it does not open those historical paths. These tests use synthetic tokenizers/models or local wrapper stubs, require no original worktree, .superpowers fixture restoration, archived outputs or real model weights. This command is proposed for actual main after cleanup, not claimed already run there.


## Final preparation verdict

Ready for the lead's gated integration decision, subject to fresh main/source parity and preservation receipts. The final patch changes exactly five approved test files; all production session SHA256 values still match the initial combined-source recipe. Independent review PASS. Changed five suites passed 210/210 in each environment. The unchanged four suites had already passed in the initial combined runs (base 135 passed / 3 skipped, mgnp 138 passed), giving union evidence of base 345 passed / 3 skipped and mgnp 348 passed. This is combined evidence across two runs, not a fresh all-nine post-patch rerun and not a post-cleanup archival replay claim. The original pre-fix 11 failures / 3 errors remain preserved and classified in the logs above.

Final test-only patch SHA256: `09c20636332c8c38f341853733d3cda8c5c352c7b5e3f98878c9737f09789b99`. No main/index/ref mutation or merge was performed by this reviewer. Preserve historical source paths/revisions for replay; do not activate H100 or restart stopped studies as part of the merge.
