# SDR Routing Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. User already approved design and agent execution; do not request another confirmation. Checkboxes track completion.

**Goal:** Run an interpretable, bounded donor/semantic SDR pilot and conditionally test focused pathways.

**Architecture:** One standalone experiment script imports existing task-loading, token-span and activation-hook primitives; it owns only pilot-specific panel/split/matching/reporting logic. All GPU phases use the same capture/scoring path; the runner writes an explicit viability checkpoint before optional Stage2. A small standalone wrapper enforces allocation and runtime limits. Artifact schemas are plain JSON/JSONL dictionaries in this runner, not a reusable provenance or metadata framework.

**Tech Stack:** Existing local Llama-3.1-8B-Instruct, PyTorch/NNsight component-analysis hooks, HF datasets/tokenizer, pytest, Slurm; zero paid APIs.

**Spec:** `/projects/beto/swong2/Alignment/.scratch/sdr-routing-pilot/spec.md` (read first).

## Global Constraints

- Maximum **2 RESERVED H200 GPU-hours**, **zero paid APIs**; independent cap, failed reservations count.
- Stage 1 <=1 reserved GPU-hour; Stage 2 <=1 additional reserved GPU-hour only after written viability gate.
- No notebooks, training, watcher changes, external benchmark reruns or SDR v2 circuit evaluation.
- Implementation only in `Deception-Circuit/.claude/worktrees/sdr-routing-pilot`; lead alone handles git.
- Original story selection and donor panel freeze before model results; no outcome-based pool expansion.
- Keep all MLPs intact; heads are pre-o-proj slices. Intact/self/donor/patch scoring follows identical execution path.

## Review Focus

- Saved metadata may disagree with old scaffold semantics: semantic audit must derive truth from actual saved predicate/designation, retain explicit failure reasons.
- Pressure deletion changes token positions: semantic maps must follow per-prompt anchors/offsets, never equal index assumptions.
- Observed answer crossing may require changed donor truth/content: label that confounding, count natural overlap separately, never equate requested target with emitted answer.
- BF16 scoring paths can differ by .125: same-path full-vocabulary no-op controls precede interpretation.
- Partial jobs or insufficient natural support: atomic checkpoints retain all attempted rows, cap counts failed allocations, Stage2 refuses missing/failed gate.

---

### Task 1: Stage1 runner, mapping tests, and bounded donor pilot

**Files:** Create `scripts/sdr_routing_pilot.py`, `tests/test_sdr_routing_pilot.py` in the pilot worktree. No existing framework edits.

**Interfaces:**
- `build_manifest(dataset_dir: str, tokenizer, *, seed: int = 20261020, max_stories: int = 48) -> dict`: source hashes, frozen story/split/panel/donor plan, maps/exclusions and planned grid.
- `audit_variant(record: dict, prompt: str, tokenizer) -> dict`: truthful/emitted-candidate token identities, literal anchors, actual lengths, alignment validity and errors.
- `semantic_map(recipient: dict, donor: dict, *, scope: str) -> list[tuple[int,int]]`: unique recipient/donor positions, excluding unmapped clauses; `scope` in `readout`, `items`, `common`, `all_aligned`.
- `remap_capture(value, mapping: list[tuple[int,int]], recipient_length: int) -> tuple[torch.Tensor, torch.Tensor]`: recipient-shaped donor values plus boolean valid-position mask (unmapped positions never written).
- `--dry-run --dataset-dir <primary>/data/datasets/sdr --output <run>` writes CPU manifest/gate skeleton only; no model load, CUDA or network.

- [ ] Write failing tests `test_item_token_injectivity_and_stem_context`, `test_old_saved_suffix_truth_swap` (generic suffix, inversion/identity, corrupt swaps truthful item; inconsistent explicit item suffix fails); `test_group_split_no_related_variant_leakage` (48 groups gives24/24, variant permutations do not change split); `test_panel_frozen_before_emission` (no scoring callback invoked; no exclusion on later patch outcome).
- [ ] Add mapping tests `test_deleted_clause_shifts_readout_without_index_copy`, `test_item_mentions_map_by_identity_and_role`, `test_ambiguous_anchor_and_truncation_fail`, `test_all_aligned_requires_exact_pair_shape`, `test_unmapped_tokens_are_not_written`. Synthetic tensors use donor index-coded values and assert exact selected recipient coordinates; test mask excludes padding.
- [ ] Run the dedicated tests and confirm failure before implementation. Implement interfaces using existing `dataset.deception_common.load_or_generate_deception_data` (read existing test only), `dataset.matched_honest.replace_clause`/`instructed_counterpart`/`load_matched_honest_pool`, tokenizer offsets and `component_analysis.segmentation` conventions. Never rebuild old saved prompts using current SPECS.
- [ ] Load masks by explicit canonical suite paths resolved from `outputs/_launch_format_control/suites.json`; assert shared32 count32 and frozen family membership. Resolve outputs/data via explicit CLI absolute paths, not worktree-relative accidental empty datasets.
- [ ] Run `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python -m pytest tests/test_sdr_routing_pilot.py -q` and the same command with `/u/swong2/.conda/envs/mgnp/bin/python`; run CLI dry-run using cached tokenizer only. Expected all tests pass, manifest supports exact finite panel and no GPU invocation. Lead reviews/commits only owned files.

#### Stage1 measurements and viability checkpoint

**Files:** Extend `scripts/sdr_routing_pilot.py`, `tests/test_sdr_routing_pilot.py`; create `scripts/sdr_routing_pilot.sbatch`.

**Interfaces:**
- `score_capture(model, capture, truth_ids, other_ids, donor_ids=None) -> dict`: use `hooks.readout_logits` on captured READOUT_KEY, return fp32 margins and full-vocabulary outputs/probabilities/checksums.
- `build_comparisons(manifest: dict, baselines: list[dict]) -> list[dict]`: actual argmax classes; deterministic same-split matching, reciprocal directions; explicit content/truth changes; retain non-item outcomes and unsupported classes.
- `evaluate_gate(manifest: dict, baselines: list[dict], comparisons: list[dict], controls: dict) -> dict`: exact spec coverage counts, no effect-size criterion.
- `run_stage1(args) -> dict`: baseline screen, calibration, family patches with mapped `hooks.Replacement`, artifacts and atomic checkpoints before deadline. `--stage stage1|stage2` requires frozen manifest; `--dry-run` remains CPU-only.
- Wrapper accepts `--dry-run` by passing through to Python; ordinary run verifies local model cache and one H200, tracks deadline and emits final receipt on signal/normal completion. Slurm `--time` passed on submit command; no automatic resubmit.

- [ ] Add failing tests `test_actual_argmax_not_target_defines_donor_cell` (other-token argmax retained), `test_truth_changed_answer_cell_is_labelled_confounded`, `test_missing_pressure_overlap_restricts_scope_and_missing_answer_support_stops_stage2`, `test_pressure_identity_overlap_not_pressure_presence`, `test_nonself_and_outside_mask_controls_frozen`, `test_gate_ignores_patch_magnitude`, `test_partial_rows_and_failed_reservations_preserved`, `test_no_cuda_or_model_load_in_dry_run`. Assert gate thresholds from spec exactly.
- [ ] Add tiny-model hook tests reusing fixtures/patterns in `tests/test_component_hooks.py`, `tests/test_path_patching_passes.py`: full-vocab same-path self-patch equality, head slice isolated from neighboring heads/MLPs, donor position map writes correct slice, repeated baseline capture stays same; fail on a simulated .125 BF16 mismatch. Existing `hooks.capture_forward`, `hooks.Replacement`, `hooks.READOUT_KEY`, `hooks.readout_logits`, and `hooks.load_analysis_model` are the only intervention/model entrypoints. Do not add a dual-stream model.
- [ ] Run failing tests, implement minimally, run dedicated suite in both supported environments. Run existing relevant hooks/path tests once in mgnp. Test actual shell wrapper in CPU dry-run (guard bashrc sourcing as documented); never `bash -x` startup.
- [ ] Lead reserves <=1 GPU x01:00:00 only after CPU gate and pre-submission ledger entry. Calibration measures load plus8 stories, throughput/peak memory; project remaining grid before patching. Stop optional work before3300s, preserve checkpoint. First baseline support checkpoint by1800s; if insufficient, complete bounded diagnosis and stop. Run selected families only on frozen panel; no full evaluator/WikiText/null sweep.
- [ ] Confirm artifacts and exact numerical controls; write gate and story-bootstrap summary even when stopped. Lead records reservation/actual GPU-sec and reviews before Stage2. A failed numerical/semantic gate ends scientific interpretation; do not relax tolerance or select successful rows.

### Task 2: Conditional focused paths/interactions and final report

**Files:** Extend `scripts/sdr_routing_pilot.py`, `tests/test_sdr_routing_pilot.py`; reuse wrapper only after a written Stage1 go checkpoint. Until then this task is **unimplemented and conditional**: queued Stage1 runner/tests/wrapper/manifest/source hashes are immutable. Read `.scratch/sdr-routing-pilot/stage2-path-seam.md` for audited exact APIs and traps. No framework edits or scientific scope expansion.

**Interfaces:**
- `focused_grid(model_geometry: dict) -> list[dict]`:6 candidate senders→selector2 Q/K/V and READOUT; actual32 query heads/8KV heads implies4 heads/group. Q17H24→KVgroup6 and Q24H27→KVgroup6 at their distinct layers. Deduplicate `(kind,layer,group)`; enforce sender_layer<receiver_layer for Q/K/V. Exclude L17H26→L17 Q/K/V, keep all6→readout: **39 valid cells,7 receivers,6 shared pass1 forwards**. Label all four affected query heads per KV receiver.
- `stage2_provenance(parent_manifest_path: str, gate_path: str, args) -> dict`: verify immutable Stage1 manifest content/source/mask/tokenizer/baseline identities and gate; create separate Stage2 provenance with parent manifest/gate hashes plus new code hashes. Never rebuild/overwrite Stage1 manifest after runner changes or bypass its source fingerprint verifier.
- `assemble_path_streams(model, recipient_batch: dict, donor_batch: dict, maps: list, *, senders: list, scope: str) -> path_patching.Streams`: physical8×128 using existing `batch_inputs`; capture recipient `hooks.all_component_keys(model)+[READOUT_KEY]`; put **only all_component_keys** (embedding/every head/every MLP, excluding READOUT and Q/K/V receiver keys) into clean_outputs. Capture donor sender heads with donor's own masks/readout. Per pair use `remap_capture` then fill unmapped/padding/dummy positions with captured recipient sender values, yielding plain recipient-coordinate tensors in corrupt_outputs. `target/distractor` are recipient truth/other IDs; required clean/corrupt metric/gap dataclass fields use same-path fp32 scoring but do not drive row selection.
- `run_stage2(args, gate: dict) -> dict`: refuse failed/missing/mismatched gate or insufficient cap; preserve split/panel/pair recipe. Per recipient batch/scope call `receiver_inputs(model, streams, senders=[sender], receivers=reachable)` once per sender; share capture across receiver cells, each using `readout_from_receivers(model, streams, {receiver: captured_tensor})`. Pass1 receivers already use recipient coordinates: **never semantic-remap them again**. Score/log only logical real rows; primitives return all8. Full freeze is pass1 only; pass2 downstream heads/MLPs evolve normally.
- `summarize_by_story(rows: list[dict], *, seed: int = 20261020, bootstrap_reps: int = 2000) -> dict`: reuse approved directional story summaries; primary sign `patched_truth_margin-baseline_truth_margin`, retaining zero-gap rows and all attempts. No native normalized-effect/MIN_GAP selection.

- [ ] Write failing CPU tests `test_grid_has_39_cells_and_6_shared_pass1_calls`, `test_grid_deduplicates_gqa_by_layer_and_enforces_order`, `test_stage2_requires_matching_passed_gate`, `test_stage2_provenance_preserves_stage1_manifest_bytes`; assert Stage1 source/content hashes cannot be silently updated to edited Stage2 source. `focused_grid` builds explicit tuples/receiver metadata, never `build_grid` (which adds unwanted senders/receivers).
- [ ] Write physical8×128 tiny-model regression `test_variable_length_semantic_two_pass_matches_manual_reference`:>=2 real rows with different donor/recipient lengths/readouts, deleted middle-clause shift, multiple disjoint spans, padding/dummies. Assert donor-coded mapped positions and recipient-filled unmapped positions exactly; independently assemble all-component baseline replacements and compare pass1 Q/K/V/readout, every nonsender freeze, and pass2 full-vocab scoring. Deliberately wrong equal-index donor patch must fail mapping expectation; recapturing must not mutate saved baselines.
- [ ] Add `test_full_freeze_no_sender_and_identity_sender_full_vocab_noop`, `test_simultaneous_sender_unmapped_positions_use_recipient_baseline`, `test_kv_patch_group_only_and_q_single_head`, `test_zero_gap_rows_retained_with_finite_raw_effect`. Same-path full-vocab <=1e-5 tolerance, never .125 BF16-step tolerance. These Stage2 controls are additional to Stage1 receipts. Test fixed receiver positions separately: Q/readout at recipient readout; K/V at explicitly declared recipient semantic key spans. Do not substitute donor/sender map for receiver-position mask.
- [ ] Implement direct paths with lower-level `receiver_inputs` and `readout_from_receivers`. Do **not** use native `capture_streams`, `counterfactual_pair`, `stream_batches`, `positioned_effects`, or `normalized_effect`: they assume aligned readouts and/or normalize/drop low-gap rows. No donor-reproduction invariant for unaligned partial maps; compare manual reference, self and empty invariants instead. Q/K are pre-RoPE; preserve recipient positional geometry.
- [ ] Implement interactions on ordinary recipient path (no full-freeze): candidate6/selector2/outsider2 singles and candidate∪selector/candidate∪outsider joints; assert set unions. Shared32 dose.5 replacement target=`recipient_capture+.5*(mapped_donor-recipient_capture)` only at mapped positions via masked `hooks.Replacement`; outside map current values evolve freely. Test `(m_CS-m_C)-(m_S-m_0)` and corresponding outsider interaction against explicit margins. Reuse Stage1 singles only after scoring/provenance equality; otherwise recapture. Freeze<=3 exploratory discovery-ranked position followups before confirmation effects, retain every tested result.
- [ ] Run focused tests in both environments and relevant existing path tests. CPU dry-run counts **6 pass1+39 pass2 forwards/batch/scope**, plus recipient/donor captures, controls and interactions; dual scopes double path work. Keep one full recipient freeze batch at a time (~520MiB before trace overhead), not all480 captures. Compare Stage2 recaptured baselines to same-provenance Stage1 baseline; calibrate actual full-freeze throughput before final grid, do not extrapolate blindly from Stage1.
- [ ] Lead allocates <=1H200-hour only after written scientific go, review and remaining-cap check (operator owns budget). Existing allocation-specific deadline remains binding, maximum3300s internal for1h; omit optional followups first and preserve partial cells. Do not edit/resubmit running Stage1. No all-core grid, MLP receivers or completeness claim.
- [ ] Reconcile operator cost receipts, write final summary/report addendum with donor-content caveats, directional discovery/confirmation story uncertainty and accessibility controls; independent review before lead-only explicit-file commit. No merge/push needed for reviewable result.

Self-review: all spec requirements map to tasks1–2; interfaces are defined above; scientific gates precede Stage2 allocation; numerical no-op cannot be traded for a favorable behavioral effect. User's existing approval supersedes skill's generic handoff request for another confirmation.


## Task1 runtime refinement (binding lead ruling)

Keep all480 baseline/support rows. `build_comparisons` must freeze <=12 recipient/donor pairs/story before inference; six families ×`readout`,`common` gives <=6912 patch rows at48 stories. Extra pressure clauses are baseline/support only; omit optional scopes and exhaustive <=57600-row patching. Freeze priorities for reciprocal P↔H/P↔N, truth0/1, changed/unchanged truth and nonself same-condition controls. The worker chooses and manifests the exact deterministic recipe; classify actual emissions afterward and preserve unsupported comparisons as missing, never select by patched effect. Add `test_frozen_patch_pair_bound_and_coverage` asserting <=12 pairs/story, <=6912 patch rows, genuine reciprocal condition comparisons and both truth roles; `test_pair_selection_precedes_model_and_patch_results` asserts emission/effect changes cannot alter frozen pairs. Mandatory self/no-op controls and all480 baseline support gates remain. See spec's matching runtime refinement; lead compactions0, no GPU reserved at this checkpoint.
