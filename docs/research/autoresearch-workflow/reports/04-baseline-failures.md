# Ticket 04: Deception-Circuit test baseline before any code edit

This file records the failing test names of the full Deception-Circuit suite in both interpreters, taken before
ticket 04 changed any code. After the change, the suite is run the same way and compared by name. A failure
name that is not listed here is a regression.

## How the baseline was taken

Both runs started at about 12:54 pm CDT on 2026-10-31, in parallel on the same login node, from the worktree W at its committed state.
The only file changed in W before them was the ticket's own Status line. Each run used the script
`/u/swong2/.claude/jobs/b2cb53cd/tmp/04/run_suite.sh`, which changes into W and runs one of these commands.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider -rfE <W>/tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider -rfE <W>/tests
```

The logs are `suite-baseline-mgnp.log` and `suite-baseline-base.log` in the same scratch directory.

| interpreter | pytest summary | exit and wall time |
|---|---|---|
| mgnp, Python 3.12 | 19 failed, 3069 passed, 22 skipped, 2 warnings, 101 errors in 1634.52s (0:27:14) | EXIT=1 WALL_SECONDS=1646.594420449 |
| base, Python 3.9 | 19 failed, 2863 passed, 78 skipped, 4 warnings, 101 errors in 652.28s (0:10:52) | EXIT=1 WALL_SECONDS=658.554653600 |

## Why there are more failures than the seven that memory records for main

Most errors come from running in a worktree. Those tests read ignored files that exist only in the main
checkout, such as `outputs/_analyses/sdr-routing-validation/.../manifest.json` and
`.superpowers/sdd/plan-sdr-cue-probe/.../protocol.json`, and fail with FileNotFoundError at setup. They are
stable from run to run, so a comparison by name is still exact.

## Names failing in both interpreters (120)

- `ERROR tests/test_sdr_completion_diagnostic.py::test_all1280_parent_ids_and_prompt_bytes_unchanged`
- `ERROR tests/test_sdr_completion_diagnostic.py::test_calibration_rows_excluded_main_and_rubric_frozen`
- `ERROR tests/test_sdr_completion_diagnostic.py::test_cpu_dryrun_writes_planned_rows_without_loading_model`
- `ERROR tests/test_sdr_completion_diagnostic.py::test_full_annotation_export_missingness_and_join_cli`
- `ERROR tests/test_sdr_completion_diagnostic.py::test_original_baseline_batchorder_reconstructed`
- `ERROR tests/test_sdr_completion_diagnostic.py::test_parent_numeric_pass_capability_fail_is_valid_diagnostic_entry`
- `ERROR tests/test_sdr_completion_diagnostic.py::test_prefix115_no_truncation`
- `ERROR tests/test_sdr_cue_circuits.py::test_complete_synthetic_panel_fixed_triples_interactions_and_natural_denominators`
- `ERROR tests/test_sdr_cue_circuits.py::test_donor_involutions_and_exact_directed_pair_order`
- `ERROR tests/test_sdr_cue_circuits.py::test_exact_named_panel_and_independent_example_order`
- `ERROR tests/test_sdr_cue_circuits.py::test_portable_build_roots_and_persisted_rebuild`
- `ERROR tests/test_sdr_cue_positions.py::test_accepted_resumed_attempt_still_requires_operational_supersession_reason`
- `ERROR tests/test_sdr_cue_positions.py::test_actual_allocation_buffers_rechecked_before_model[calibration]`
- `ERROR tests/test_sdr_cue_positions.py::test_actual_allocation_buffers_rechecked_before_model[preflight]`
- `ERROR tests/test_sdr_cue_positions.py::test_actual_wrapper_dryrun_calibration_main_resume`
- `ERROR tests/test_sdr_cue_positions.py::test_all_nine_categories_zero_filled_transitions_triples`
- `ERROR tests/test_sdr_cue_positions.py::test_allocation_deadline_binding_and_nonfit_before_model`
- `ERROR tests/test_sdr_cue_positions.py::test_analysis_equal_fixture_weight_with_unequal_variant_counts`
- `ERROR tests/test_sdr_cue_positions.py::test_annotation_provenance_coverage_disagreement_finish_override`
- `ERROR tests/test_sdr_cue_positions.py::test_atomic_terminal_crash_boundary`
- `ERROR tests/test_sdr_cue_positions.py::test_attempt_requires_bound_immutable_invocation`
- `ERROR tests/test_sdr_cue_positions.py::test_blind_exact_view_join_all_multiplicities`
- `ERROR tests/test_sdr_cue_positions.py::test_bounded_worst_batch_and_streamed_assembly_size`
- `ERROR tests/test_sdr_cue_positions.py::test_calibration_causal_null_cannot_be_replaced_by_pass_flag`
- `ERROR tests/test_sdr_cue_positions.py::test_calibration_natural_timing_excluded`
- `ERROR tests/test_sdr_cue_positions.py::test_completed_resume_is_idempotent_and_validates_existing_assembly`
- `ERROR tests/test_sdr_cue_positions.py::test_completed_resume_rejects_conflicting_assembly_without_overwrite[boolean_slot]`
- `ERROR tests/test_sdr_cue_positions.py::test_completed_resume_rejects_conflicting_assembly_without_overwrite[foreign_row]`
- `ERROR tests/test_sdr_cue_positions.py::test_completed_terminal_skipped_only_after_full_audit`
- `ERROR tests/test_sdr_cue_positions.py::test_corrupt_terminal_ids_masks_controls_hash_rejected`
- `ERROR tests/test_sdr_cue_positions.py::test_deadline_stop_before_batch_and_no_outcome_retry`
- `ERROR tests/test_sdr_cue_positions.py::test_every_pair_family_has_base_donor_three_sites`
- `ERROR tests/test_sdr_cue_positions.py::test_exact_4224_schedule_ids_and_order`
- `ERROR tests/test_sdr_cue_positions.py::test_exact_mask_donor_head_and_current_history_receipts`
- `ERROR tests/test_sdr_cue_positions.py::test_exact_parent_identity_and_new_commit`
- `ERROR tests/test_sdr_cue_positions.py::test_factorial_components_and_outside_contrasts`
- `ERROR tests/test_sdr_cue_positions.py::test_failed_invocation_hard_stops_resume`
- `ERROR tests/test_sdr_cue_positions.py::test_final_terminal_before_assembly_resume_recovers_outputs[False]`
- `ERROR tests/test_sdr_cue_positions.py::test_final_terminal_before_assembly_resume_recovers_outputs[True]`
- `ERROR tests/test_sdr_cue_positions.py::test_fixture_equal_strata_reciprocal_and_alignment`
- `ERROR tests/test_sdr_cue_positions.py::test_header_cut_token_alignment_and_ambiguity`
- `ERROR tests/test_sdr_cue_positions.py::test_killed_attempt_resumed_as_next_number_without_overwrite`
- `ERROR tests/test_sdr_cue_positions.py::test_missing_forward_coverage_and_boolean_control_step_rejected`
- `ERROR tests/test_sdr_cue_positions.py::test_natural_pairs_and_parent_full_reference_descriptive_only`
- `ERROR tests/test_sdr_cue_positions.py::test_observed_forecast_keeps_full_cap_and_all_controls`
- `ERROR tests/test_sdr_cue_positions.py::test_pair_boundary_and_unchanged_prefix_contract`
- `ERROR tests/test_sdr_cue_positions.py::test_position_partition_excludes_dummy_padding_generated`
- `ERROR tests/test_sdr_cue_positions.py::test_resume_binding_rejected_before_model_load`
- `ERROR tests/test_sdr_cue_positions.py::test_scheduler_receipt_must_bind_prior_job_and_eligible_state`
- `ERROR tests/test_sdr_cue_positions.py::test_small_fake_calibration_main_resume_assembly`
- `ERROR tests/test_sdr_cue_positions.py::test_source_parent_and_zero_offset_corruptions_fail_closed`
- `ERROR tests/test_sdr_cue_probe.py::test_blind_export_join_exact_coverage_and_cap_override`
- `ERROR tests/test_sdr_cue_probe.py::test_calibration_control_and_hardware_forgery_blocked`
- `ERROR tests/test_sdr_cue_probe.py::test_dryrun_never_loads_model_and_main_stays_blocked`
- `ERROR tests/test_sdr_cue_probe.py::test_fullcap_forecast_includes_4224_and_conservative_io`
- `ERROR tests/test_sdr_cue_probe.py::test_imported_kernel_fixed_b8l224_and_control_modes`
- `ERROR tests/test_sdr_cue_probe.py::test_main_forecast_blocks_before_model_and_deadline_retains_receipt`
- `ERROR tests/test_sdr_cue_probe.py::test_overlong_prefix_fails_all_candidates`
- `ERROR tests/test_sdr_cue_probe.py::test_parent_alias_drift_and_hashed_semantic_tamper_abort`
- `ERROR tests/test_sdr_cue_probe.py::test_partial_failure_preserves_tokens_and_all_rows_no_retry`
- `ERROR tests/test_sdr_cue_probe.py::test_rank_crossing_render_and_hash_selection`
- `ERROR tests/test_sdr_cue_probe.py::test_rules_exact_denominators_transitions_and_lofo[F-favored]`
- `ERROR tests/test_sdr_cue_probe.py::test_rules_exact_denominators_transitions_and_lofo[Q-question_order]`
- `ERROR tests/test_sdr_cue_probe.py::test_rules_exact_denominators_transitions_and_lofo[R-record_order]`
- `ERROR tests/test_sdr_cue_probe.py::test_rules_exact_denominators_transitions_and_lofo[T-truth]`
- `ERROR tests/test_sdr_cue_probe.py::test_rules_exact_denominators_transitions_and_lofo[X0-None]`
- `ERROR tests/test_sdr_cue_probe.py::test_rules_exact_denominators_transitions_and_lofo[X1-None]`
- `ERROR tests/test_sdr_cue_probe.py::test_run_distinct_cal_main_dispatch_and_receipt_artifacts`
- `ERROR tests/test_sdr_cue_probe.py::test_unresolved_transition_never_copies_or_flips`
- `ERROR tests/test_sdr_routing_validation.py::test192_no_truncation_and_stem_token_injectivity`
- `ERROR tests/test_sdr_routing_validation.py::test80percent_gate_is_per_template_truth_and_keeps_all_rows`
- `ERROR tests/test_sdr_routing_validation.py::test_all_model_shards_and_compatibility_dependencies_hashed`
- `ERROR tests/test_sdr_routing_validation.py::test_calibration_requires_all_variants_of_first_eight_stories`
- `ERROR tests/test_sdr_routing_validation.py::test_changed_clauses_omitted_from_semantic_map`
- `ERROR tests/test_sdr_routing_validation.py::test_complete_factorial_and_exact_donor_axes`
- `ERROR tests/test_sdr_routing_validation.py::test_dryrun_does_not_load_model_or_cuda`
- `ERROR tests/test_sdr_routing_validation.py::test_failed_gate_does_not_resample_or_tune`
- `ERROR tests/test_sdr_routing_validation.py::test_fresh_fixtures_are_compositional_not_population_holdout`
- `ERROR tests/test_sdr_routing_validation.py::test_gate_rejects_missing_numeric_kind_coverage_or_nonfinite_receipt`
- `ERROR tests/test_sdr_routing_validation.py::test_named_primary_role_support_is_exact_axis_and_task_intersection`
- `ERROR tests/test_sdr_routing_validation.py::test_named_truth_favored_correct_answer_distinct_fields`
- `ERROR tests/test_sdr_routing_validation.py::test_native_neutral_deletes_only_pressure`
- `ERROR tests/test_sdr_routing_validation.py::test_native_order_truth_suffix_consistent`
- `ERROR tests/test_sdr_routing_validation.py::test_neutral_reporting_truth_failure_is_visible_without_affecting_retrieval_gate`
- `ERROR tests/test_sdr_routing_validation.py::test_no_stakes_or_emission_threshold`
- `ERROR tests/test_sdr_routing_validation.py::test_primary_support_identical_between_report_and_retrieval`
- `ERROR tests/test_sdr_routing_validation.py::test_primary_support_intersection_identical_across_donor_axes`
- `ERROR tests/test_sdr_routing_validation.py::test_rejects_bf16_step_and_manifest_mutation`
- `ERROR tests/test_sdr_routing_validation.py::test_resolved_honest_sample_sources_and_conservative_native_pool`
- `ERROR tests/test_sdr_routing_validation.py::test_sources_use_real_sample_json_and_exclude_prior_stories`
- `ERROR tests/test_sdr_routing_validation.py::test_split_bundle_and_hash_domains_do_not_leak`
- `ERROR tests/test_sdr_routing_validation.py::test_stakes_and_task_precede_record`
- `ERROR tests/test_sdr_routing_validation.py::test_truth_flip_swaps_predicates_not_record_name_order`
- `ERROR tests/test_selective_v6_manifest.py::test_balanced_disjoint_panel_and_shared_fixed_donors`
- `ERROR tests/test_selective_v6_manifest.py::test_deterministic_selection_and_requested_labels`
- `ERROR tests/test_selective_v6_manifest.py::test_hash_binding_detects_modified_source`
- `ERROR tests/test_selective_v6_manifest.py::test_rejects_corrupted_panel[donor]`
- `ERROR tests/test_selective_v6_manifest.py::test_rejects_corrupted_panel[duplicate]`
- `ERROR tests/test_selective_v6_manifest.py::test_rejects_corrupted_panel[labels]`
- `ERROR tests/test_selective_v6_manifest.py::test_rejects_corrupted_panel[mask]`
- `ERROR tests/test_selective_v6_manifest.py::test_rejects_corrupted_panel[missing_variant]`
- `FAILED tests/test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py`
- `FAILED tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[far]`
- `FAILED tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[sdr]`
- `FAILED tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[ser]`
- `FAILED tests/test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap`
- `FAILED tests/test_deception_common.py::test_pressure_pools_are_well_formed[ser]`
- `FAILED tests/test_deception_common.py::test_three_specs_registered`
- `FAILED tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms`
- `FAILED tests/test_sdr_cue_circuits.py::test_real_branch_fake_calibration_and_main_validate_metadata_and_fixed_journal_counts`
- `FAILED tests/test_sdr_cue_circuits.py::test_virtual_fullcap_main_journal_reuses_exact_reconstruction_and_control_audit`
- `FAILED tests/test_sdr_cue_positions.py::test_flock_exclusion_and_release_after_process_exit`
- `FAILED tests/test_sdr_shared_composition.py::test_freeze_binds_original_inputs_source_and_provisional_execution`
- `FAILED tests/test_sdr_shared_composition.py::test_full_panel_analysis_preserves_direction_and_story_balancing`
- `FAILED tests/test_sdr_shared_composition.py::test_input_panel_preserves_originals_both_truths_and_exact_maps`
- `FAILED tests/test_sdr_shared_composition.py::test_schedule_covers_3936_and_calibration_excludes_main`
- `FAILED tests/test_selective_v6_manifest.py::test_donor_identity_must_match_source_key`
- `FAILED tests/test_selective_v6_manifest.py::test_duplicate_source_ids_rejected`
- `FAILED tests/test_selective_v6_manifest.py::test_missing_proposal_source_rejected`
- `FAILED tests/test_selective_v7.py::test_frozen_prepare_rejects_case_source_and_support_drift`

## Names failing only in mgnp (0)

None.

## Names failing only in base (0)

None.
