# Hand-back: A3 direction validation selection and axis freeze

Agent: Codex Sol worker. Work unit: D. Status: handed-back.

## What changed

Owned worktree changes:

- `component_analysis/a3_direction_pipeline.py`: added `freeze_selection` and private selection helpers; the reviewed Unit C fit implementation remains intact apart from the module description.
- `tests/test_a3_direction_selection.py`: synthetic CPU selection, provenance, geometry, RNG, failure and immutability coverage.
- This hand-back, mirrored identically into the primary research directory.

Selection consumes a complete byte-checked fit bundle and its independently validated train capture. Expected source identity comes from trusted design/protocol; exact candidate task/site/seed coverage, DOM status, original site projection and axis geometry are checked before selection. The exact fit manifest is then supplied to the strict numeric reader for outcome-array loading; its source identity has already been independently checked, rather than inferred from those outcome receipts.

Validation uses canonical `publish_shard` / `read_completed_shards` artifacts. The explicit operational fixture layout is `protocol.selection_cache.groups`, each with exactly `group_id`, `analysis_task`, `source_task`, `site`, `numeric_profile`, and `rows_per_shard`. Every frozen task/site has mechanism, IOI and MMLU groups; finite fitted seeds determine actual row requirements. Expected raw keys and source records come from design membership, never cached key claims. Each group has `<validation_root>/<group_id>/capture` and `<group_id>/shards/shardNNNNNN`. Captures have independently derived scientific identity for their actual validation source/profile. Shards inherit their own capture reference and must link the exact fit bundle through `execution.fit_reference`. Missing groups, source rows, seeds, MMLU floors, completion markers or row keys block publication. Separate mechanism/IOI/MMLU profiles are retained.

`direction_point_metrics` supplies all validation gates; reviewed `select_direction` supplies gate-first, fallback and lexical-tie behavior. Failed fits and noninterpretable validation summaries remain explicit; unavailable fractions serialize as null rather than manufactured finite values. A seed with no usable DOM blocks its task/seed. Unfitted nuisance remains conditionally unavailable and cannot select or rescue DOM.

Each selected record follows the agreed workload contract: learned axis descriptor, ordered assessment and calibration descriptors, explicit fitted/unfitted nuisance, probes, selection receipt and fixed steering references. Descriptor hashes are the reviewed `runner.axis_identity` of the full numeric axis. Geometry and axis arrays are self-contained in the selected bundle. Assessment nulls use the reviewed seed argument; calibration uses the reviewed offset argument, yielding the fixed independent RNG panels. Every null gets its own H variance/center from the original train H and DOM bootstrap weights. Random steering is assessment null zero; both signs are frozen. SDR stays descriptive and no statistics schema changed.

The selection scientific identity retains train FIT/CAPTURE ANCESTRY. Mandatory `selection_split='validation'`, the explanatory scope field and complete validation byte references record the actual site-selection data use. `inventory_identity` separately carries the workload identity. The immutable completion marker covers all selected axes, shared geometry, full embedded protocol, validation table and byte links.

Root approved a narrow provenance amendment: `freeze_selection(..., protocol_path=None)` now accepts an additional keyword-only canonical protocol path. It is required for noninjected production. The canonical envelope must match the trusted protocol payload and payload digest. `protocol_file_reference` records resolved path, exact file digest/size and payload digest outside the protocol object; the link is rechecked immediately before publication. `_selection_protocol_reference(..., expected=recorded_reference)` detects serialization-only byte changes. Explicit injected fixtures may omit a file and remain injected and unable to finalize scientific results.

## How verified

Test-first evidence: initial candidate tests failed because `_select_candidates` was absent; the null panel test failed because `_freeze_null_axes` was absent; integration tests failed because the new selection helpers were absent. A geometry-completeness assertion failed before geometry arrays were included in selection. A substituted fitted projection failed to raise before the independent source-site projection guard. Wrong frozen null-count claims failed to raise before the count guard. Missing production protocol path and absent protocol-reference helper tests failed before the provenance amendment.

Final focused commands from the worktree:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_selection.py tests/test_a3_direction_fit.py tests/test_a3_directions.py -q -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_selection.py tests/test_a3_direction_fit.py tests/test_a3_directions.py -q -p no:cacheprovider
```

Observed exit codes were zero: base had 78 passed, one skipped, and four dependency/environment warnings; mgnp had 79 passed and three dependency/environment warnings. The base skip is `test_tiny_llama_direction_replays_through_existing_inference_hooks`, which requires the pinned NNsight version. Warnings concern existing dependency deprecations, bottleneck version and NVML discovery. The requested focused core includes randomly initialized tiny CPU Llama hook tests; no scientific model or downloaded weights were used.

Coverage includes every validation gate and both MMLU floors, fallback retention, lexical ties, all failed DOM seeds, unavailable nuisance, nonfinite denominators, missing fit seeds, source/profile/axis changes, pilot/assessment layout rejection, partial shards, original-site projection linkage, exact null RNG panels/H statistics, selected-axis reconstruction hashes, child-byte tampering and protocol-file serialization changes. A final base rerun of `test_selected_axes_are_frozen_before_assessment` after adding protocol-file output assertions also passed. No broader suite was run, per root's scope.

Report checks:

```bash
/u/swong2/.local/bin/research-session lint docs/research/specificity-ladder/reports/report91-direction-selection-handback.md
/u/swong2/.local/bin/research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report91-direction-selection-handback.md
cmp docs/research/specificity-ladder/reports/report91-direction-selection-handback.md /projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report91-direction-selection-handback.md
```

Both report lints and the primary/worktree mirror comparison returned zero.

## Execution evidence

Not applicable: no scientific runs. All artifacts generated here are injected temporary CPU fixtures. There is no Slurm job, scientific outcome count, production baseline comparison or scientific run manifest to claim. The latest observed Codex weekly checkpoint reported 26 percent spent, 74 percent remaining, and no pause requirement.

## What is NOT done

No production selection, scientific fit, model weights, GPU, Slurm, API, notebooks, git, subagents, RS state/worklog/ledger write or broader test suite occurred. Runner, artifacts, reviewed cores and workload files were not edited.

Unit F's canonical `selection_cache` layout/capture/scoring producer remains deferred. Current canonical preparation lacks that layout and selection therefore fails closed. Root must pass the actual canonical `protocol_path`, publish source-bound per-profile captures and complete raw shards, and obtain independent contract review before production use. This work confers no execution or spend admission. The selected `inventory_identity` and conditional nuisance contract were coordinated with the workload owner; that consumer requires validation selection and no blocked task/seeds before remaining work.

## Open questions

No unresolved scientific choice. Independent review and canonical Unit F integration remain root-owned. Reviewers should explicitly inspect the full-manifest numeric-reader boundary described above: trusted source identity and fit coverage are established independently before the strict reader loads unknown numerical fit outcomes. The current reader requires exact full outcome metadata and has no separate structural-only outcome-read API.


### Review 94 fix appendix

Status: handed-back. The two blockers in `94-direction-selection-review-handback.md` are repaired in the same owned pipeline and selection test files. Unit C, runner, artifacts, workload and reviewed cores were not changed.

Shared geometry is now independently derived from each linked source projection before any fitted axis or validation row is consumed. `_validate_shared_geometry` checks exact source projection, the source-derived retained rank and cutoff, all array shapes, finite values, full spectrum and full pseudoinverse. The retained basis must be orthonormal and span the source-derived image. Equivalent basis rotations/signs are permitted; learned-axis pullback agreement alone is insufficient. Each source/geometry pair is checked once, without materializing a residual-width square projector. Legitimate unfitted geometry receipts remain explicit rather than becoming stand-in axes.

`_validate_fit_bootstrap_h` independently regenerates bootstrap weights and the full receipt from trusted ordered train IDs, canonical cluster IDs and seed. DOM, nuisance, image-probe and metadata-probe receipts must all match, including failed/unfitted receipts. Both fitted DOM and nuisance weights must equal the independent draw. Their retained H centers, projected variances and sigmas are checked against the linked train H cache and loaded fitted axis before any null is created. This uses the existing fitted axis as data; it does not refit DOM/nuisance/probes, inspect validation outcomes to revise an axis, or change selection policy.

Test-first evidence: the perpendicular pseudoinverse substitution with genuinely unfitted nuisance and the re-signed `[.5,.5,0,0]` weight substitution with fitted/unfitted nuisance all failed their new rejection tests before repair. A second red sweep covered all four bootstrap receipts, rank/cutoff/spectrum/nonorthonormal-basis substitutions, and DOM/nuisance H-center/variance substitutions. All attacks publish a fresh byte-correct fit bundle and re-sign validation fit-reference links. The complete failing case groups were:

- `test_resigned_perpendicular_pseudoinverse_rejected_with_unfitted_nuisance`.
- `test_resigned_bootstrap_weights_rejected_from_trusted_draw`, both nuisance states.
- `test_resigned_bootstrap_receipts_checked_even_if_nuisance_unfitted`, all four receipt families.
- `test_full_shared_geometry_is_bound_to_source_projection`, all four geometry mutations.
- `test_fitted_h_statistics_are_recomputed_from_trusted_train_h`, both statistics on both fitted axis families.

One edit script had a Python quoting error before writing the implementation. Verification launched during that error still imported the pre-fix source and repeated the same fifteen failing cases: base had 15 failed, 79 passed, one skipped; mgnp had 15 failed, 80 passed. After correcting the script and applying the validators, the targeted attack sweep passed all 15 cases. The final scoped commands were then rerun on the applied source:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_selection.py tests/test_a3_direction_fit.py tests/test_a3_directions.py -q -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_selection.py tests/test_a3_direction_fit.py tests/test_a3_directions.py -q -p no:cacheprovider
```

Observed final exit codes were zero: base 94 passed, one known NNsight skip and four existing dependency/environment warnings in 91.58 seconds; mgnp 95 passed and three existing dependency/environment warnings in 91.43 seconds. Positive coverage accepts an equivalent orthonormal image basis and checks every assessment/calibration null's pullback and independently derived bootstrap weights with nuisance genuinely unfitted.

No scientific runs or production selection occurred. Execution evidence remains injected synthetic CPU fixtures only; the requested core tests include tiny random CPU model checks. No weights, GPU, Slurm, API, notebooks, git, subagents or RS writes occurred. The follow-up weekly checkpoint reported 27 percent used and 73 percent remaining, with no pause requirement. Canonical Unit F integration and independent re-review remain root-owned before production admission.

The amended report was mirrored into primary; both report lints and the mirror comparison were rerun successfully.


### Review 94 axis-array schema closure

Status: handed-back. The independent reviewer closed the original geometry/bootstrap blockers but identified a separate schema-shadowing path: extra fitted-axis array references could overwrite the already validated shared projection and pseudoinverse during dictionary merging.

`_loaded_fit_axis` now requires exactly `v`, `pullback`, `h_center` and `id_weights` before loading any receipt arrays. It merges only those explicit names. Both fitted DOM and fitted nuisance obey this same contract; legitimate unfitted nuisance keeps its existing conditional-unavailable behavior. Shared geometry cannot be overridden through receipt keys. No selection policy, axes, seeds, null counts, protocol boundary or scientific schema changed, and Unit C remains unchanged.

Test-first evidence: `test_resigned_fit_axis_arrays_cannot_shadow_shared_geometry` initially failed for both DOM and nuisance because the malformed bundle was accepted. The fixture adds `projection=2W` and `pinv=W+/2`, halves pullback, publishes a fresh byte-correct fit, re-signs validation fit links and updates validation axis hashes. The DOM attack uses genuinely unfitted nuisance. `test_fitted_axis_array_schema_requires_all_four_fields` also initially failed for both fitted families because the loader accepted a missing required field. All four cases pass after the exact-key guard and explicit merge.

Final scoped commands:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_selection.py tests/test_a3_direction_fit.py tests/test_a3_directions.py -q -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_selection.py tests/test_a3_direction_fit.py tests/test_a3_directions.py -q -p no:cacheprovider
```

Both final commands exited zero: base had 98 passed, one known NNsight skip and four existing dependency/environment warnings in 116.22 seconds; mgnp had 99 passed and three existing dependency/environment warnings in 112.40 seconds. This includes the original geometry/bootstrap attacks and legitimate geometry/null consistency coverage.

Execution evidence remains synthetic CPU fixtures and the requested tiny random CPU core tests only. No scientific run, production selection, model weights, GPU, Slurm, API, notebooks, git, subagents, broader suite or RS writes occurred. The weekly checkpoint reported 28 percent spent, 72 percent remaining, and no pause requirement. Independent closure review and Unit F production integration remain root-owned.

The amended report was mirrored into primary; both report lints and the mirror comparison returned zero.
