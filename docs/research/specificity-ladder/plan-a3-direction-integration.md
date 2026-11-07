# A3 Direction Pipeline Integration Plan

> **For agentic workers:** Use `executing-plans` task by task with test-driven development. Workers never run git; root commits explicit file lists and assigns ownership before implementation. The plan author authorizes no model execution or spending. Checkbox completion refers to implementation, not scientific completion.

**Goal:** Connect the reviewed direction algebra and statistics to reproducible native inference, with complete timing admission, frozen selection and durable assessment artifacts.

**Architecture:** Extend canonical A3 CPU preparation, then add direction-owned artifact, runner, workload and stage modules. Keep raw row observations authoritative and normalize complete panels only after exact coverage checks. All direction forwards compose the existing inference hooks; no gradient adapter, edge pipeline or mask trainer is introduced.

**Tech Stack:** Existing Python, numpy, torch, pytest, local Arrow/tokenizer/MMLU caches, NNsight inference hooks and the existing cluster wrapper conventions. No new dependency, service or data acquisition.

**Spec:** [Approved A3 plan](plan-a3.md), especially Task 2 and Task 6; [START](START.md); [specificity specification](spec.md). Reviewed implementations are `component_analysis/a3_directions.py` and `component_analysis/a3_statistics.py`. Operational rulings below were supplied by root during this planning task.

## Global constraints and root rulings

- Preserve the original complete A1 parent scope and exact assessment IDs: mechanism `100` per task, both designation streams, IOI `100`, MMLU `32`. FAR/SER are exactly the confirmatory family; SDR stays descriptive. Fit/selection use frozen matched train/validation minus the full historical exclusion union. Do not redraw assessment membership.
- Keep seeds `[42,1,123]`, assessment orientations `199`, selected-site calibration orientations `32`, assessment bootstrap `2000` with seed `9001`, and conditional-power replicates `2000` with seed `19001`. Preserve every START gate and the accepted continuation ruling; no assessment-based site/sign/family changes.
- Root ruling, validation MMLU: call existing `ladder_tasks.mmlu_rows(tokenizer,n=128,seed=2)` against already local cached sources. Exclude all A1 assessment source/instance IDs and exact prompt bytes; keep the first `32` remaining unique eligible rows in that fixed candidate order. Block if insufficient; no second draw, fetch, outcome filter or assessment borrowing. Preserve source `split='test'` and add `analysis_split='validation'`. Freeze source, tokenizer and grader provenance and include this entire new membership in protected-set checks. This prospective CPU membership amendment makes every validation selection gate testable.
- Root ruling, null controls: every assessment null and every calibration null requires primary opposite-designation subspace interchange on all mechanism arms and IOI, both MMLU subspace-zero/centered-H floors, no-op/positive controls, and perturbation diagnostics. Secondary mechanism/IOI zero and centered-H controls apply to learned and nuisance axes only. They are not required extra secondary cells for every null. Secondary passes never replace a failed primary pass.
- Root ruling, steering: both signs for learned, nuisance and the fixed assessment-null axis at index `0`, directly on every mechanism arm, IOI and MMLU. These are signed steering diagnostics, not MMLU floor cells and not necessity tests. No assessment sign selection.
- Root ruling, unusable fits: retain failed-fit receipts. A zero/unstable DOM site is not a fitted candidate; no finite valid DOM candidate for any seed blocks that task. Never discard/replace a seed, invent an axis, substitute a site outside the frozen list or create finite stand-in fractions.
- Root ruling, admission order: bounded prefit M1 timing admits only fit/validation; exact selected-site `199`-axis timing admits remaining calibration/assessment. Both direction M1 pieces together stay within `0.5` GPU-hours; all M1 direction/edge/mask reservations together stay within `2` GPU-hours. Inventory names every actually timed task/site/shape and any measured equivalence; generic per-head timing is insufficient.
- Direction M2 ceiling is `9` GPU-hours, including fitting captures, validation, calibration, assessment, startup and retries. All A3 remains within `40` GPU-hours, including other milestones and contingency. Forecast ceilings are not measurements or authority to spend. Root alone reserves/registers/reconciles through RS. Do not spend another phase's allowance implicitly.
- CPU tests use both supported interpreters with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`, `pytest -p no:cacheprovider`. No notebook execution. Dry-runs cannot load model weights, call CUDA, fit, score, publish outputs or change RS state. Local tokenizer/Arrow/cache metadata reads are permitted.

## Current state and identity boundary

`outputs/_analyses/specificity-ladder/a3-design-a93b4cb` is a CPU-only preparation snapshot, not an execution-ready production freeze. Its A1 parent at source `0253` is stale after the reviewed `positive_control` shape fix `5f450dc`. Root is regenerating the A1 prepared/selected artifacts. Treat old artifacts as immutable; never rewrite their source hashes or bypass `read_selection` to reuse them.

After this pipeline implementation is reviewed and its source is final, run canonical `a3_pipeline.prepare` into a NEW production A3 directory. It must consume the newly complete A1 selection through the original A1 identity, with the full A1 task scope, completion sidecar and exact file-byte links. A3 execution uses root's separately supplied full source commit and A3 code-hash closure. A newer A3 source commit does not replace the ancestor A1 commit in parent reads. A1 assessment and utility ID lists, ordering, prompt bytes and token IDs must equal the preserved scientific membership; a mismatch blocks preparation rather than starting a new scientific sample.

The current `a3_pipeline.py` has preparation functions and no staged CLI. Existing `specificity_ladder.score_cell` performs whole-component interventions and uses all-token H banks; it is not a direction patch dispatcher. Its `LadderBatch`, validation, scoring conventions, positive-control and timing utilities remain useful. `hooks.capture_forward` captures full sequence values and readout residuals under no-grad; `hooks.replace_forward` returns native logits only. Primary analysis must use `capture_forward(...,replacements=...)` followed by `readout_logits(capture.residual[:,-1])`, preserving native diagnostics too.

## File map and ownership seams

Paths are relative to the worktree. Reviewed pure cores remain unchanged unless a separately demonstrated defect requires its own fix/review.

| File | Responsibility |
| --- | --- |
| Modify `component_analysis/a3_design.py` | Pure disjoint local validation-MMLU membership helper and live-access inclusion; no new assessment draw |
| Modify `component_analysis/a3_pipeline.py` | Extend canonical prepare with validation MMLU/protocol links; thin lazy dispatch to direction stages; future experiments reject explicitly |
| Create `component_analysis/a3_direction_artifacts.py` | Immutable tensor bundles, source closure, completion markers, raw row keys and atomic shard publication |
| Create `component_analysis/a3_direction_runner.py` | Streaming readout captures, mapped directional interventions, same-shape controls and exact point metrics |
| Create `component_analysis/a3_direction_workload.py` | Exact cell/shard inventory, measured profile coverage and pure cost admission |
| Create `component_analysis/a3_direction_pipeline.py` | CLI stage orchestration, CPU fitting/selection, panel packing, descriptive SDR and final summaries |
| Create `scripts/jobs/specificity_a3.sh` | Dry-run-first offline direction wrapper; never submits or writes RS state |
| Extend `tests/test_a3_design.py`, `tests/test_a3_pipeline.py` | Parent identity, new validation membership, CPU entry point |
| Create `tests/test_a3_direction_{artifacts,runner,fit,selection,workload,pipeline}.py` | Owning contracts named in the work units below |

Keep `a3_native.py`, `a3_edges.py`, `a3_mask.py` and their future tests outside this assignment. Direction hooks need no autograd/native-gradient path. Later tasks may consume immutable direction selection/fit bundles, not import this runner for receiver gradients.

## Shared interfaces and artifact contracts

The signatures below are proposed implementation interfaces. Existing reviewed functions are named exactly where consumed.

```python
# a3_direction_artifacts.py
code_hashes() -> dict[str, str]
write_bundle(target, metadata: dict, arrays: dict[str, np.ndarray]) -> dict
read_bundle(path, *, expected: dict) -> tuple[dict, dict[str, np.ndarray]]
validate_live(design: dict, protocol: dict, *, registry_paths: list[str]) -> dict
publish_shard(target, *, identity: dict, expected_keys: list[tuple], rows: list[dict], execution: dict) -> dict
read_completed_shards(inventory: dict, shard_root, *, identity: dict) -> list[dict]

# a3_direction_runner.py
capture_readouts(model, batches, *, sites: list[tuple], sink, identity: dict) -> dict
score_direction_cells(model, batches, *, cells: list[dict], capture_index: dict, axes: dict, sink, identity: dict) -> dict
direction_point_metrics(rows: list[dict], *, seed: int, require_mmlu: bool=True) -> dict

# a3_direction_workload.py
build_inventory(design: dict, protocol: dict, *, stage: str, fits=None, selected=None) -> dict
project_cost(pilot_receipts: list[dict], workload: dict, ledger: dict) -> dict

# a3_direction_pipeline.py
fit_from_cache(design: dict, cache_path, *, protocol: dict, output) -> dict
freeze_selection(design: dict, fits_path, validation_root, *, protocol: dict, output) -> dict
pack_statistics_panel(design: dict, selected: dict, rows: list[dict], *, split: str) -> dict
summarize_descriptive_sdr(design: dict, selected: dict, rows: list[dict], *, n_boot=2000, seed=9001) -> dict
main(argv=None, *, tokenizer=None, model_loader=None) -> int
```

Bundle metadata binds schema/kind, analysis split, A3 commit/code hashes, A1 parent artifact and file hashes, original A1 identity, selection sidecar bytes/hash, A3 design/protocol hashes, matched source fingerprints, actual ordered IDs/streams/conditions/sites, canonical wording, source tokenization/readouts/labels, grader hash, model/tokenizer revision and runtime profile. Array descriptors bind name, dtype, shape, exact file content hash and byte count. `code_hashes()` is the union of current `ladder_pipeline.code_hashes()`, `a3_design.py`, `a3_pipeline.py`, both reviewed A3 cores, all new `a3_direction_*.py` modules, `dataset/build_twin_training.py`, `scripts/twin_training.py` and the actual A3 job wrapper, keyed by repository-relative path. Record runtime Python/torch/transformers/NNsight/CUDA versions, model config identity and the resolved frozen local snapshot path separately; no credential/environment dump. Use portable numeric arrays with `allow_pickle=False`; load CPU/memory-mapped arrays, never arbitrary pickle. A source file named by a relative ancestor path resolves against its frozen parent repository, not the caller's CWD.

Write through `common.publish` into a fresh sibling temporary directory on the same filesystem. Write arrays/rows, hash and re-read them, then publish the completion marker last and atomically rename the directory. Consumers require the marker, exact child file hashes, complete expected row-key set and matching metadata. Orphan temporaries and partial bundles are not reusable. Existing output conflicts fail; `--resume` may only skip matching complete shards. A matching partial target is never silently treated as complete; any temporary cleanup is explicit and limited to this invocation's temporary directory. Do not rewrite old bundles or accept changed file bytes just because the deserialized payload is equal.

Raw row key:

```text
(panel, analysis_task, source_task, split, seed, site, family,
 axis_index, operation, instance_id, condition, stream)
```

`family` is `learned`, `assessment_null`, `calibration_null`, `nuisance`, `steering_learned`, `steering_nuisance`, or `steering_random`. Steering operation names include sign. Utility `analysis_task` retains the selecting mechanism task, while `source_task` is `ioi` or `mmlu`; utility rows from different task-selected sites must not collide. Each row retains labels, intact/patched canonical and raw/native margins, full-vocabulary argmax/correctness, binary diagnostics and MMLU four-option diagnostics, donor/readout mapping, perturbation norms, replay/positive-control references, source/axis hashes and validity flags. Missing/unsupported cells remain explicit blocked outcomes, never a smaller sample.

`direction_protocol.json` is an A3 operational artifact, not a mutation of `ROOT_RULING_V1` or of the ancestor A1 identity. It freezes this plan's accepted operational rulings, exact operation inventory, numeric profile, task order, candidate sites, stream order, source closure, utility membership and all limits before model access. Store the full protocol object and digest, not merely a human label. Any future operational amendment creates a new immutable artifact lineage.

## Runtime order and admission boundary

```text
final-source canonical CPU prepare + protocol + prefit inventory
    -> M1 prefit shape timing (validation only)
    -> admit bounded M2 fit capture + validation-selection subinventory
    -> train/validation captures -> CPU fits/probes -> validation scores
    -> CPU site freeze + assessment199/calibration32 axis freeze
    -> M1 selected-site exact199 timing (same fixed validation shard)
    -> admit remaining M2 calibration + assessment + steering inventory
    -> validation calibration shards -> CPU conditional power
    -> fixed assessment shards -> paired inference + descriptive outputs
```

The two-pass split is an ordering solution, not a relaxation of M1. No full assessment reservation is inferred from the prefit microbenchmark. Preselection pilot directions are timing-only axes at named frozen sites, never site-selection evidence. The selected-site pilot uses the exact frozen assessment axes after selection; pilot outcome files cannot be read by selection or merged into assessment/calibration. M1 accounting includes both pieces, their startup, failures/retries and remaining edge/mask pilot shares. Full production stages wait until all implementation and its contract review pass.

## Work unit A: Canonical CPU preparation and complete lineage

**Files:** `a3_design.py`, `a3_pipeline.py`, `a3_direction_artifacts.py`, existing design/pipeline tests and new artifact tests.

- [ ] Write failing tests `test_validation_mmlu_first_disjoint_seed2_candidates`, `test_validation_mmlu_source_split_retained`, `test_validation_utility_prompt_alias_collision`, `test_validation_mmlu_insufficient_blocks_without_redraw`, `test_new_utility_is_in_live_protected_checks`, `test_parent_sidecar_and_file_bytes_required`, `test_stale_a1_code_rejected_before_loader`, `test_changed_assessment_membership_refused`, and `test_partial_bundle_never_reused`.
- [ ] Run those named files first and observe absent-helper/interface failures. Implement `eligible_mmlu(candidates,fixed_rows,*,n=32)->list[dict]` using existing `_utility_identity` semantics for instance/source/donor IDs and exact UTF bytes. Extend canonical prepare with local candidates, retained candidate-source manifest and `mmlu_validation`; extend `validate_access` to include its actual source/instance IDs. No alternate tokenizer loading or dataset parsing path.
- [ ] Bind new production A3 output to complete fresh A1 evidence through current `load_a1_parents` and `_validate_parent_files`, preserving strict A1 source checks. Freeze `mmlu_validation`, existing `ioi_validation`, exact original A1 utilities and operation protocol. Create validation-only maps through existing `ioi_item_swap_maps(ioi_validation)` and `mmlu_calibration_maps(mmlu_validation)`; do not reuse assessment map donors for validation. Check historical exclusions in fit and validation and exact original assessment membership. Permit fixtures only with explicit injected provenance that finalization rejects.
- [ ] Implement portable immutable bundle readers/writers and `validate_live`. Union primary/worktree/extra protected registries and refresh both grader registries immediately before every model load, before each resumed shard and before a new shard in a long-running worker. Check actual IDs, source IDs and donors, not only registry hashes. New collisions block even a previously admitted job. Retain fresh registry hashes in each shard's run manifest.
- [ ] Run the owning CPU tests on both interpreters. Expected: all named failure cases reject before the model-loader sentinel is reached; fresh canonical preparation preserves every original assessment row. Hand root the exact changed file list for review/commit.

## Work unit B: Streaming captures and native directional evaluator

**Files:** `a3_direction_runner.py`, runner/artifact tests.

- [ ] Write failing tests `test_cache_readouts_equal_existing_hooks`, `test_unequal_padding_maps_actual_readouts`, `test_direction_only_changes_named_head_readout`, `test_secondary_zero_and_centered_h_are_subspace_patches`, `test_mmlu_has_no_item_swap`, `test_same_shape_controls_compare_same_kernel_path`, `test_positive_control_keeps_parent_padding`, `test_axis_packing_equals_serial` and `test_capture_failure_leaves_no_complete_shard`.
- [ ] Build mechanism `LadderBatch` objects through existing `ladder_pipeline.batches`, utilities through `ladder_tasks.task_batches`. Validate right padding and explicit per-row unpadded readouts; no truncation or D/I token splice. Fit captures cover only train D/I/H/user-neutral and the frozen site union; validation covers all five conditions and separate validation utilities. Store only per-ID/stream readout head vectors, requested own-clause pooled summaries for the already approved diagnostic, scalar outcomes and exact projection blocks. Clause summaries are unsupported when spans are missing; they never replace the primary readout.
- [ ] Capture the union of requested sites per bounded chunk when it fits; one intact forward can serve all its fitted axes, donors and probes under the exact execution identity. Immediately gather readouts to CPU, release full sequence captures/readout residuals/logits and flush a bounded shard. `hooks` may transiently save full `o_proj` input for a requested layer: do not misestimate memory as only head width, persist every layer activation, or retain vocabulary logits/graphs across chunks. Capture geometry and CPU/disk byte forecasts are part of inventory. No gradients.
- [ ] Use reviewed `direction_replacement` on CPU intact head tensors and explicit readout masks, then send the computed replacement back to the original device/dtype via `hooks.Replacement`. Primary donor is same ID/condition/opposite stream for mechanism, frozen repeated-B corrupt IOI donor for IOI. Gather each donor's own readout into recipient-shaped storage; only readout-to-readout correspondence is asserted. MMLU has no native donor operation.
- [ ] Subspace zero is reviewed interchange with a zero donor at readout, implementing `z - W+v vT Wz`. Centered-H is reviewed `mode='remove'` with that seed/site/axis's train-bootstrap H center, implementing `z - W+v vT W(z-mu_H)`. Do not use A1's all-token mean bank or zero an entire head. Apply these two floors to MMLU for every primary candidate/null axis. Steering uses reviewed positive/negative modes directly and is not packed as a floor.
- [ ] Preserve fp32 canonical margin and full-vocabulary condition-correct accuracy through existing `_stats`; retain native BF16 diagnostics and MMLU choice metrics. Empty replacement, actual head self-replay, and zero-coefficient directional replay must reproduce the intact margin/argmax under the SAME batch width, padding, dtype/backend and capture/readout path. Use existing `1e-5` absolute/relative no-op tolerance and exact argmax agreement. Epsilon is `max(1e-6,10*max_replay_margin_error)` per task/seed, propagated across the complete panel.
- [ ] Run existing `positive_control` separately on all relevant recipient/donor rows, preserving the reviewed shared-width padding fix. It proves complete all-sender readout donor recovery, never donor recovery from one direction. For MMLU use frozen readout calibration maps only for this positive control. A3 controls must not change the scientific patch's padding or labels. Keep assay validity and numerical calibration separate from scientific gates; no invalid row is filtered.
- [ ] Batch equivalent forwards by stacking independent recipient/axis replicas only after measured serial/packed equivalence: same recipient tokens/masks/readout, donor map, axis-specific replacement and no cross-example state. Freeze a padded axis tile and padded final tile with dummy lanes excluded by keys. Each tile has matched intact/empty/replay controls; repeated intact lanes must agree and support one common intact panel before normalization. If any equivalence/no-op or memory check fails, retain the failure and use the admitted serial profile, or block pending a newly measured profile. Never silently switch batch geometry using existing cache outcomes. Union captures and exact reuse still remove redundant intact/donor forwards.
- [ ] Run owning tests on both interpreters and actual tiny-Llama existing-hook replay on mgnp, requiring it to execute rather than skip. The base environment's known pinned-NNsight mismatch is a reported limitation, not substitute production evidence. No production weights are loaded by tests. Root reviews the runner before model-stage implementation is admitted.

## Work unit C: CPU train fits, neutral-frame diagnostics and probes

**Files:** `a3_direction_pipeline.py`, fit tests.

- [ ] Write failing tests `test_fit_consumes_train_only_complete_cache`, `test_cluster_weights_shared_dom_nuisance_probe`, `test_zero_dom_receipt_is_not_replaced`, `test_probe_standardization_never_uses_validation`, `test_nuisance_never_changes_sites` and `test_fit_bundle_deduplicates_geometry`.
- [ ] Implement `fit_from_cache` using exactly frozen train IDs and streams. Per task/site/seed call reviewed `fit_direction(D,I,H,W_h,seed,cluster_ids,instance_ids)`. Nuisance calls `fit_nuisance_direction(H,user_neutral,H,W_h,...)`: original neutral D-frame versus user-neutral frame, with the identical cluster draw/weights. Save multiplicities, expanded/unique/effective sizes, raw norm, singular spectrum, rank, H center, pullback, fit variance and cosine. No token-position alignment between D/I is inferred.
- [ ] Train the descriptive ridge probe on `U.T @ W_h @ z` coordinates. Use the seed's recorded integer cluster multiplicities to expand paired IDs/streams for both D and I on CPU one site at a time, and call reviewed `fit_ridge_probe`; every stream/id has equal weight within the expanded bootstrap. Keep regularization `1`, unpenalized intercept and train-only standardization. Fit the same binary ridge diagnostic on the already frozen role/length/position features with the same labels/bootstrap. Existing multicondition nearest-centroid diagnostics stay labeled separately. Report fixed validation and selected-site assessment balanced accuracy without correctness filtering; neither probe selects sites or signs.
- [ ] Share one projection/SVD geometry file per actual site and one train activation cache, not one copy per axis/seed. Store per-fit axis/center/variance/weight references and deduplicate immutable geometry by content hash. Bound expanded CPU probe storage by a measured byte preflight and process one fit at a time; no GPU activation graph or enlarged saved train cohort. An overflow/nonfinite probe is a failed diagnostic, not a score of chance.
- [ ] Unfittable DOM sites retain explicit reason and no axis. Selection receives exactly the finite fitted candidates from the frozen site list. If a seed has none, emit a task-blocked receipt and do not proceed with incomplete inference. Unfittable nuisance is reported unfitted, never replaced by DOM or a new random axis; it cannot become evidence against role confounding.
- [ ] Run fit/core tests on both interpreters and hand root fit contracts for review. Expected: injected validation/assessment cache identities reject, cluster multiplicities are preserved, and no zero vector/seed replacement reaches output.

## Work unit D: Validation selection and immutable axis freeze

**Files:** direction pipeline/runner selection logic and selection tests.

- [ ] Write failing tests `test_validation_all_gates_include_disjoint_mmlu`, `test_gate_first_and_fallback_match_reviewed_core`, `test_nonfinite_fraction_blocks_seed_if_no_valid_candidate`, `test_selection_cannot_read_pilot_or_assessment`, `test_exact_null_rng_offsets`, `test_selected_axes_are_frozen_before_assessment` and `test_nuisance_uses_dom_site`.
- [ ] Score each finite DOM candidate site/seed on the COMPLETE frozen selection IDs with primary interchange, validation IOI and both validation MMLU floors. `direction_point_metrics` accepts rows already scoped to exactly one task/site/family/axis and rejects mixed scopes; it must reproduce A1 ratio-of-means, equal stream/ID weighting, separate D/H and I/user-neutral denominators with per-stream epsilon checks, D `>=0.5`, I `<0.25`, absolute H/F/IOI movement `<0.05` and at most one extra MMLU error in EACH floor. Replay/support validity also gates. Test parity against existing ladder metrics on synthetic complete cells; unsupported rows cannot create finite valid selection fractions.
- [ ] Call reviewed `select_direction` only on finite interpretable fitted candidate summaries, with their exact candidate site list, frozen seed and validation split. Retain the complete fit/validation failure table outside its input. Among passes maximize D; otherwise maximize D-minus-I and mark validation failure; use core lexical ties. A failed validation gate does not remove that seed or permit an assessment choice. No usable finite candidate blocks the task under the root ruling.
- [ ] Publish one selected site per seed and task, selected DOM/nuisance/probes and complete validation evidence. Freeze assessment axes via `random_image_directions(W_h,n=199,seed=fit_seed)`, whose internal RNG offset gives `10000+fit_seed`. Freeze calibration axes via `random_image_directions(W_h,n=32,seed=21000+fit_seed)`, giving `31000+fit_seed`; do not add the offset twice. Store actual axis tensors/hashes/RNG identities and bind each axis to the selected site's retained image geometry. Attach each null's own train H variance/center with reviewed `prepare_image_direction` and the DOM fit's weights.
- [ ] Fix random steering to assessment-null index `0`; attach its own train H sigma. Freeze both signs for each learned/nuisance/random steering family without inspecting outcomes. Selected nuisance stays at DOM's site and cannot rescue DOM. SDR has the same frozen selection/null sizes with descriptive provenance; do not add it to `a3_statistics`' exact FAR/SER schema.
- [ ] Publish selection last with a completion sidecar linking exact fit/cache/protocol/validation file bytes, all selected site/seed axes and evidence. Tests must reject partial marker, altered child bytes, axis/site substitution, wrong calibration seed or missing seed. Run both interpreters and hand root the exact artifact contract before timing the selected panel.

## Work unit E: Exact inventories, bounded timing and cost admission

**Files:** `a3_direction_workload.py`, direction pipeline pilot/prepare actions, wrapper and workload tests.

- [ ] Write failing tests `test_inventory_explicitly_covers_all_cells`, `test_prefit_admission_excludes_assessment`, `test_selected_timing_requires_every_199_axis`, `test_missing_shape_coverage_blocks`, `test_nan_or_failed_receipt_blocks`, `test_startup_and_shared_m1_charged_once`, `test_selected_site_or_hardware_change_invalidates_profile`, `test_short_shard_is_not_full_completion`, `test_no_fresh_ledger_or_reservation_blocks` and `test_actual_wrapper_dry_run_never_calls_loader`.
- [ ] Build exact row-key inventory before reservation. Symbolic formulas below are a checksum only; persist actual row-key lists, unique captures/donors, replay/positive-control forwards, probe reads, projected cache/host bytes, concrete microbatch/axis tiles and expected completed shard IDs. Batch counts are derived from actual deterministic chunking, not row count divided by an assumed batch size. Every actual forward maps to a named inventory operation. The prefit inventory conservatively includes every frozen site; after CPU fitting, publish a new fit-linked validation inventory that records unfittable sites as attempted-fit failures rather than requiring nonexistent intervention rows. Its admitted cost cannot exceed the original fit/validation reservation, and its still-required fitted-candidate rows remain exact; this is numeric fit eligibility, not outcome-based site selection.

Let `N_t` be validation IDs, `S_t` finite fitted sites (prefit admission uses the full frozen candidate upper bound), `F_t` train IDs, and `Q(N)=10*N+100+2*32`. `Q` counts primary mechanism stream rows, IOI clean rows and both MMLU floor rows per axis. These are derived accounting formulas, not runtime estimates.

| Inventory part | Required scientific recipient rows before capture/control overhead |
| --- | --- |
| Train capture | Per task: `4*2*F_t` once per admitted site-union capture grouping; no per-seed repeat of intact data |
| Validation candidate scores | Per task: `3*S_t*Q(N_t)`; primary learned axis only, every selection gate |
| Selected calibration | Per task: `32*3*Q(N_t)` null rows plus selected learned rows reused only under exact geometry/identity, otherwise explicitly rescored |
| Assessment primary/null floors | Per task: `(1+199)*3*Q(100)` |
| Nuisance primary/floors | Per task: `3*Q(100)` when fittable |
| Learned/nuisance secondary controls | Per task: `2 families * 3 seeds * 2 operations * (10*100+100)`; learned MMLU floors already counted in primary/floors |
| Steering | Per task: `3 families * 3 seeds * 2 signs * (10*100+100+32)`; direct MMLU steering once per sign, no floor alias |
| Probes | CPU readout-only validation/assessment evaluations; no extra forward when matched intact captures exist |

Preserve all frozen tasks including descriptive SDR. Calibration uses separate validation IOI/MMLU, not assessment utility rows. Add exact intact/donor captures, matching-geometry empty/self/directional replay, complete all-sender positive controls, warm-up, serialization and final completion costs to the inventory. Controls may be deduplicated only by exact task/row/site-set/operation/numeric geometry identity; every dependent row references the reused control. Per-axis perturbation diagnostics still remain per row. No count silently disappears because two seeds choose the same site.

- [ ] Freeze timing membership from selection IDs before any GPU outcome: for each task take the first `4` IDs in deterministic descending maximum frozen prompt-length order, lexical ID ties; freeze separate first `4` validation utility prompts by that same metadata-only rule. Retain lists/hashes in the protocol. Reuse these IDs in both pilot passes. Long assessment/train shapes may be profiled only by right-padding these validation inputs to the exact predeclared execution widths; never score an assessment ID in M1 or truncate long rows.
- [ ] Prefit pilot measures every distinct named task/site/capture-group/operation/length/batch/dtype/backend profile needed for train capture and learned validation scores, using timing-only axes and same-path controls. Freeze deterministic chunk widths/profiles before execution; exact width padding is allowed with preserved masks/readouts and no truncation. Profiles with different heads/layers must be measured or have a directly measured equivalence receipt. Include worst required utility lengths via validation-input padding. This admits only its bounded M2 fit/selection inventory.
- [ ] After selection, exact pilot exercises ALL frozen `199` null axes for each selected task/seed site's complete required shape/control inventory on the fixed timing cohort, with no scientific final gate. It measures actual axis packing and cleanup, not a short prefix extrapolated to the full panel. It also times selected-site calibration/nuisance/secondary/steering operation profiles; the calibration count remains separate in inventory. Save profile row counts, axis coverage, startup, GPU synchronization boundaries, batch seconds/distribution, CPU/serialization/cache bytes and CUDA allocated/reserved peaks in an atomic receipt. If the complete exact pilot cannot fit the remaining directional M1 allowance, block before further spend; no lower axis count.
- [ ] `project_cost` requires successful matching-profile receipts and a fresh root-provided read-only ledger snapshot. For each proposed job use measured startup plus `1.25*sum(required_batches*conservative_measured_batch_seconds)` plus a fixed finish reserve declared in its workload. Use the largest observed matching-profile operation time; include warm-up/serialization separately if not already inside it. The finish reserve is an explicit root-supplied operational input, not a guessed generic speed forecast. Reject absent/nonfinite timings, changed geometry/hardware/source hashes, missing validation/control profiles, cache-fit failure and incomplete axis/row coverage. No historic cross-device ratio or unmeasured generic per-head inference.
- [ ] Admission returns projected seconds/GPU-hours, charged phase/subphase, exact workload digest, profile receipt digests, required job count/startups, existing spend/reservation accounting and proposed walltime. Enforce M1 direction/all-M1 bounds, M2 direction ceiling and the full A3 remaining/contingency ceiling without double counting already reserved/completed work. This is a concrete proposal for root's RS reservation, not a ledger write. Actual execution also requires a matching root reservation receipt and full identity; stale source/registry/ledger/reservation blocks.
- [ ] Wrapper follows existing `specificity_ladder.sh`: cluster environment, offline flags, pinned threads, correct working tree, explicit stage arguments, no scheduler submission. `--dry-run` calls CPU validation and prints resolved full command, identity, inventory digest and missing admission prerequisites; it cannot publish or load weights. Production loads cached weights only after live guards and a real Slurm CUDA allocation. Root alone supplies explicit command-line walltime when submitting. Run shell syntax, subprocess dry-run and both CPU workload test suites before review.

## Work unit F: Durable scoring, normalized inference and final gate separation

**Files:** direction pipeline/artifacts/runner completion logic and pipeline tests.

- [ ] Write failing tests `test_resume_exact_completed_shards_only`, `test_protected_collision_on_resume_blocks`, `test_missing_null_seed_stream_or_utility_blocks_final`, `test_calibration_cannot_read_assessment_rows`, `test_raw_row_pack_matches_statistics_schema`, `test_sdr_never_enters_holm`, `test_partial_pilot_or_injected_never_finalizes` and `test_summary_staleness_and_bytes_rejected`.
- [ ] Shard by inventory keys over task/panel/seed/family/axis blocks and deterministic recipient chunks. Stage `assess --panel calibration` scores ONLY selected-site validation learned/calibration-null cells with validation utilities; selected learned rows are reused only if exact source, numeric profile and readout/operation identities match, otherwise inventory covers their rescore. Save centered validation D/I residuals and original gaps as diagnostic artifacts; `simulate_conditional_power` remains authoritative for their additive model. Never read assessment outcomes into calibration.
- [ ] Stage `assess --panel assessment` consumes the immutable selection/axis bundle and exact A1 assessment IDs/utilities. It emits all admitted primary/null, nuisance, secondary and steering rows plus controls and selected-site probe results. No per-shard gate can alter subsequent cells. Each shard refreshes access checks and writes `rows.jsonl`, numeric arrays if needed and `run_manifest.json` with source/parent/registry/axis identities, measured counts, GPU/runtime/memory, job/cluster labels and completion status. Interrupted shards remain incomplete and cannot contribute to a final panel; retries charge root's ledger.
- [ ] Pack the FAR/SER calibration schema EXACTLY as `a3_statistics` documents: `kind='a3_direction_calibration'`, `split='validation'`, ordered seeds, `axis_ids=['learned']+list(range(32))`, arrays `[3,N,2]` and `[33,3,N,2]`, paired utility IDs/arrays, explicit original assessment instance/source/prompt exclusions and replay-derived epsilon. Utility MMLU fields are `MMLU_zero` and `MMLU_h_mean`; correctness must be binary. Keep provenance in linked manifests, not unknown keys inside the strict schema. Canonical pressure wording comes from D source text for every arm. Reject duplicates/missing rows before reshape; never fill unsupported outcomes with zero or pass validity by default.
- [ ] Pack assessment with `kind='a3_direction_outcomes'`, `split='assessment'` and the complete learned-plus-null axis list. Verify all same-axis/seed condition IDs, streams, native labels, both MMLU floors and common intact outcomes before calling `summarize_direction_outcomes`. Coverage validity is aggregated into explicit `gate_valid` arrays; unsupported/incomplete production cells block finalization even if a diagnostic summary is possible. Preserve the primary and secondary operation distinction; only primary mechanism/IOI plus corresponding MMLU floors enter this panel.
- [ ] Call the reviewed statistics functions unchanged at their defaults. Save strict JSON reports and input hashes. Three-seed gates, failed negative-infinity null counts/flags, strict percentile/rank, FAR/SER Holm and paired interval precision remain separate. Do not call a secondary/steering result a primary pass. Calibration outputs retain original/resampled denominator invalidity, infeasible cells, MC intervals, calibration-axis approximation and tested-neighbor detectability limits. The pure missing-validation-MMLU conditional capability remains available for legacy diagnostics, but this production protocol blocks missing validation membership/outcomes rather than turning absent gates into passes.
- [ ] Descriptive SDR uses the same `direction_point_metrics`, exact triplet/rank helpers and `draw_pressure_clusters` with SDR-only clusters, plus paired utility prompts and all three linked seeds, at the same bootstrap defaults. Report numerical gate/null/interval results with `descriptive_only=True` and no Holm rejection field. Nuisance/secondary/steering/probe reports remain outside all confirmatory axis panels. If nuisance also passes point gates, report role/framing ambiguity. No claim of a unique deceptive-intent representation follows.
- [ ] `--final` requires exact complete inventory keys, all three seeds, fixed original cohort/utility sizes, selection and run completion markers, passed replay/positive controls, noninjected production identity and current artifact/source validity. A scientific negative remains a valid complete outcome; invalid/missing data yields blocked/incomplete, not a null. Final summaries cannot themselves authorize continuation or write RS state. Root records the frozen direction fallback/milestone decision.
- [ ] Run an injected tiny-model end-to-end flow through prepare/dry-run, capture, fit, select, exact null index freeze, calibration/assessment shard packing and summary. Synthetic test cohorts may use explicit injected manifests, never production finalization. Test a restart after one durable shard and compare final row keys and numbers with uninterrupted execution. Run both supported interpreters and actual pinned-hook mgnp tests, then hand root the explicit file list for independent review before any real pilot.

## Proposed CLI contract and executable order

These are implementation targets, not existing commands claimed to have run. Every stage requires `--experiment directions --stage ... --design PATH --commit FULL_SHA --work-dir ROOT`; source identity, model/tokenizer revisions, task scope and protocol are derived from the frozen design and checked against any supplied override. `FULL_SHA` must be root's full immutable execution source identity, never a short hash. Existing `prepare(...)` remains the canonical callable seam.

Prepare actions: `freeze` (default), `inventory`, `admit`. Fit actions: `capture`, `solve`. Select actions: `score`, `freeze`. Pilot parts: `prefit`, `selected`. Assess panels: `calibration`, `assessment`. Summarize requires no model. Unknown experiment/action combinations reject before I/O. `--final` is valid only for summarize. Counts/seeds/nulls are not CLI overrides. `--shard-id` must name an existing inventory shard; `--resume` means exact completed-shard reuse only. `--dry-run` is permitted for every stage and does no writes/model calls.

Use a shell variable such as `A3_ROOT` for a fresh root-chosen production output path; do not repurpose system variables. Examples omit repeating optional additional `--registry PATH` arguments, which are unioned with mandatory primary/worktree registries.

```bash
# CPU freeze after final implementation source and fresh complete A1 ancestry.
python -m component_analysis.a3_pipeline --experiment directions --stage prepare --action freeze --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --a1-design "$A1_DESIGN" --a1-selected "$A1_SELECTED" --matched-root "$MATCHED_ROOT" --historical-csv docs/research/mechanism-analysis/phase3/a_prime.csv --root-ruling "$ROOT_RULING" --dry-run
# Repeat without --dry-run to publish only the CPU design/protocol.

# CPU inventories; outputs live under a new named inventory directory.
python -m component_analysis.a3_pipeline --experiment directions --stage prepare --action inventory --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --inventory-stage prefit --inventory "$A3_ROOT/inventory/prefit"
scripts/jobs/specificity_a3.sh --dry-run --experiment directions --stage pilot --pilot-part prefit --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --inventory "$A3_ROOT/inventory/prefit" --ledger-snapshot "$LEDGER_SNAPSHOT"
# Root reserves/registers bounded M1, then runs the same pilot with its reservation.

# CPU admission for fit/validation only; ledger and reservation belong to root.
python -m component_analysis.a3_pipeline --experiment directions --stage prepare --action inventory --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --inventory-stage fit-select --inventory "$A3_ROOT/inventory/fit-select"
python -m component_analysis.a3_pipeline --experiment directions --stage prepare --action admit --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --inventory "$A3_ROOT/inventory/fit-select" --pilot-receipts "$A3_ROOT/pilot/prefit" --ledger-snapshot "$LEDGER_SNAPSHOT" --finish-reserve-seconds "$FINISH_RESERVE_SECONDS"
# Model stages are root-reserved jobs, always dry-run their actual wrapper first.
scripts/jobs/specificity_a3.sh --dry-run --experiment directions --stage fit --action capture --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --inventory "$A3_ROOT/inventory/fit-select" --admission "$A3_ROOT/admission/fit-select.json" --reservation "$FIT_RESERVATION" --shard-id "$SHARD_ID"
python -m component_analysis.a3_pipeline --experiment directions --stage fit --action solve --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --fit-cache "$A3_ROOT/cache/fit-selection"
scripts/jobs/specificity_a3.sh --dry-run --experiment directions --stage select --action score --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --fits "$A3_ROOT/fits" --inventory "$A3_ROOT/inventory/fit-select" --admission "$A3_ROOT/admission/fit-select.json" --reservation "$FIT_RESERVATION" --shard-id "$SHARD_ID"
python -m component_analysis.a3_pipeline --experiment directions --stage select --action freeze --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --fits "$A3_ROOT/fits" --validation-root "$A3_ROOT/validation"

# Selected-site M1 pilot, then CPU inventory/admission for the rest of directions.
python -m component_analysis.a3_pipeline --experiment directions --stage prepare --action inventory --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --selected "$A3_ROOT/selected" --inventory-stage selected-pilot --inventory "$A3_ROOT/inventory/selected-pilot"
scripts/jobs/specificity_a3.sh --dry-run --experiment directions --stage pilot --pilot-part selected --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --selected "$A3_ROOT/selected" --inventory "$A3_ROOT/inventory/selected-pilot" --reservation "$PILOT_RESERVATION" --ledger-snapshot "$LEDGER_SNAPSHOT"
python -m component_analysis.a3_pipeline --experiment directions --stage prepare --action inventory --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --selected "$A3_ROOT/selected" --inventory-stage remaining --inventory "$A3_ROOT/inventory/remaining"
python -m component_analysis.a3_pipeline --experiment directions --stage prepare --action admit --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --inventory "$A3_ROOT/inventory/remaining" --pilot-receipts "$A3_ROOT/pilot/prefit" "$A3_ROOT/pilot/selected" --ledger-snapshot "$LEDGER_SNAPSHOT" --finish-reserve-seconds "$FINISH_RESERVE_SECONDS"

# Root separately executes every admitted calibration and assessment shard.
scripts/jobs/specificity_a3.sh --dry-run --experiment directions --stage assess --panel calibration --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --selected "$A3_ROOT/selected" --inventory "$A3_ROOT/inventory/remaining" --admission "$A3_ROOT/admission/remaining.json" --reservation "$DIRECTION_RESERVATION" --shard-id "$SHARD_ID"
scripts/jobs/specificity_a3.sh --dry-run --experiment directions --stage assess --panel assessment --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --selected "$A3_ROOT/selected" --inventory "$A3_ROOT/inventory/remaining" --admission "$A3_ROOT/admission/remaining.json" --reservation "$DIRECTION_RESERVATION" --shard-id "$SHARD_ID" --resume
python -m component_analysis.a3_pipeline --experiment directions --stage summarize --design "$A3_ROOT/design.json" --commit "$A3_COMMIT" --work-dir "$A3_ROOT" --selected "$A3_ROOT/selected" --inventory "$A3_ROOT/inventory/remaining" --final
```

CPU `admit` writes its immutable proposal under `admission/<inventory-name>.json`; pilot outputs are `pilot/<part>/`, fit caches `cache/fit-selection/`, CPU fits `fits/`, validation rows `validation/`, frozen selection `selected/`, calibrated/scored shards `calibration/` and `assessment/`, and CPU summaries `summary/`. These defaults and path identities are explicit parser contracts. Every model call receives only the requested panel/shard's permitted split through an injected row resolver; CLI parsing must not eagerly materialize or score all assessment arrays while running calibration. `--inventory-stage` choices are exactly `prefit`, `fit-select`, `selected-pilot`, and `remaining`; `--pilot-receipts` accepts one or more completed receipt directories. Each model stage requires the admission/reservation for its exact inventory (M1 pilots use their bounded root reservation), while CPU solve/freeze/summarize validate their completed input evidence without requiring a new GPU reservation.

## Acceptance and plan self-review

Implementation owners use exact test names above in RED/GREEN order, run their owning files on both interpreters, then root runs the combined changed-code contract suite and wrapper checks. The final target set is the existing A3 design/pipeline/direction/statistics tests, all new direction tests, ladder metric/task/runner/calibration regressions and actual tiny-model hook tests. Compare any legacy failure by name with the documented baseline; an unexecuted/skipped required production hook test leaves admission open. Wrapper checks:

```bash
bash -n scripts/jobs/specificity_a3.sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py tests/test_a3_directions.py tests/test_a3_statistics.py tests/test_a3_direction_*.py -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_design.py tests/test_a3_pipeline.py tests/test_a3_directions.py tests/test_a3_statistics.py tests/test_a3_direction_*.py -p no:cacheprovider
```

No source changes or model commands were executed while writing this plan. Numeric counts and gates above are the approved plan settings or root's explicitly supplied operational rulings; the inventory expressions are derived counts, not measured timings. Every new function has an owning work unit and tests; canonical A3 preparation, parent source closure, M1 ordering, frozen fit/site/null identity, complete utility gates, raw outcomes, paired inference and budget admission have explicit consumers. Actual runtime/cost/memory numbers remain unknown until admitted measurements exist.

## Review focus

- Parent changes between CPU freeze and model load: work unit A rejects stale A1 sidecars/source/file bytes and changed scientific memberships; F rechecks resumed shards.
- Longer donor/utility prompts or packed axes change BF16 kernels: B tests matched shape, actual readouts and serial/packed equality; E requires exact measured profile coverage before reuse.
- Missing/unsupported candidate or axis outcomes: C/D retain failed fit/selection records without inventing vectors, and F blocks finalization rather than shrinking or filling a panel.
- Registry collision after a successful dry-run or first shard: A/F refresh actual instance/source/donor access immediately before each load/shard/resume.
- Timing/admission ordering hides partial work or spends another allowance: E's two-pass accounting includes every startup/control/axis and rejects incomplete M1/M2/full-A3 ledgers without modifying them.
