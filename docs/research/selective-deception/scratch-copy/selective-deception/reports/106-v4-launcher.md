# V4 launcher implementation — October21

Task2 launcher complete; no jobs submitted, weights loaded, notebooks executed, source receipts or ledgers changed. Independent review and frozen actual CLI dry-run remain root gates before GPU execution.

Owned files: analysis/optimization_v4.py, optimization_v4.sbatch, test_optimization_v4.py; root-approved scheduling amendment additionally optimization_v4_pair.py, optimization_v4_pair.sbatch, test_optimization_v4_pair.py. CPU scientific analyzer is owned separately.

## Fixed identities and bootstrap

Study sparse-optimization-v4; source tree selective-optimization. Explicit flags baseline/calibrate/train require --initial-expected-removed1 or10; --bootstrap handles both sequentially. Actual shell arguments have normal spaces, e.g. `--train --initial-expected-removed 10`. Commands bind amendment-v4, all1024, W, rho0, seed0, horizon3072, checkpoint64 and profile4. No implicit resume/retry. Dry runs invoke the actual source `scripts/selective_mask.sbatch --dry-run`, never just print commands, without requiring Slurm or writing outputs.

Each init has manifest-W-all-initN.json; receipt-{baseline,calibrate,train}-W-all-initN.json; baseline/initN/reference.pt; reference-cache-wikitext/initN; calibration/initN; runs/all-W-initN. Distinct baseline fingerprints and WT caches are required by the new initialization identity, so none are silently shared.

Real execution requires Slurm. Preflight checks receipt policy/version/init/manifest/protocol/WT/source against manifest and frozen source inventory. Fresh output/cache existence is rejected. Atomic single-use launch claims prevent concurrent duplicate writers; claims remain after a failed attempt. Under prior root `authorize_calibration_bootstrap=true`, bootstrap verifies newly produced baseline report policy, no test references, init/manifest/source, cache SHA and required WT evidence, then exclusively derives its disposable calibration receipt. It never issues training authorization.

The standalone sbatch requests oneGPU/twohours. Root must always supply explicit --time, with calibration bounded15minutes and production bounded by the reservation.

## Root-approved interactive scheduling amendment

Ordinary twohour H200 queue was infeasible; root approved two manually separated twoGPU60minute allocations within the same fourGPUhour production reservation. Scientific horizon/init/objective remain unchanged. The pair wrapper starts both oneGPU exclusive59minute Slurm steps only after root signs both numerical/profile gates via stage authorization. Parent requests twoGPUs/60minutes. A nonzero child terminates its sibling and raises an explicit incomplete-segment error; partial checkpoints remain for root audit. Parent successful exit alone does not establish full scientific completion; root audits3072 updates and48 validations.

Pair command: `optimization_v4_pair.py --stage-authorization PATH`; actual wrapper dry-run: `optimization_v4_pair.py --dry-run`.

Stage authorization schema: version4, policy amendment-v4, study_path exact study, source_revision exact current gitHEAD and frozen receipts, source_files_hash, nonempty root_decision, mode fresh|resume, segment_seconds3600, per_fit_total_reserved_seconds3600..7200, start_both_after_calibration=true, and runs exactly all-W-init1/all-W-init10. Each run binds original_receipt_sha256. Resume additionally binds checkpoint_path exactly runs/all-W-initN/latest.pt, checkpoint_sha256, and previous_job_state terminal (COMPLETED/TIMEOUT/CANCELLED/FAILED/OUT_OF_MEMORY/NODE_FAIL/PREEMPTED). Root independently inspects actual terminal Slurm state; the wrapper checks the signed state claim. The runner verifies full checkpoint identity before restoration. Original training receipts remain unchanged. Authorization hash is an exclusive single-use claim; root must issue a fresh authorization after audit for any later segment. No job submits or requeues itself.

## Verification

Tests were written first and observed failing for missing implementation; targeted negative tests were observed failing before adding single-use claims and baseline init/source/manifest guards.

- Base: `/sw/external/python/anaconda3/bin/python3.9 -m pytest .scratch/selective-deception/analysis/test_optimization_v4.py .scratch/selective-deception/analysis/test_optimization_v4_pair.py -q` —35passed.
- Mgnp: `/u/swong2/.conda/envs/mgnp/bin/python -m pytest .scratch/selective-deception/analysis/test_optimization_v4.py .scratch/selective-deception/analysis/test_optimization_v4_pair.py -q` —35passed.
- `bash -n` both owned sbatch scripts —passed.
- Full scratchanalysis suite both environments:225passed,13failed,2errors. Base additionally2dependency warnings; mgnp56subtests passed. Logs: /tmp/v4-launcher-analysis-suite-base.log and /tmp/v4-launcher-analysis-suite-mgnp.log. The failures below arise from shared pytest import state loading `evaluation` from historical selective-mask-pilot, which lacks selective_wikitext and _amended_admissible. Launcher/pair import only stdlib and each other. These are reported rather than changing unrelated source/tests. This is not a clean broad-suite claim.

Full-suite failed/error names:

- `FAILED .scratch/selective-deception/analysis/test_extension_compare.py::test_tiny_fixed_heads_leave_mlp_open`
- `FAILED .scratch/selective-deception/analysis/test_extension_compare.py::test_tiny_native_full_replay_identity_and_removal`
- `FAILED .scratch/selective-deception/analysis/test_extension_compare.py::test_tiny_sdr_reports_probability_partition_and_paired_h_damage`
- `FAILED .scratch/selective-deception/analysis/test_extension_compare.py::test_tiny_wikitext_references_are_fresh_and_identity_exact`
- `FAILED .scratch/selective-deception/analysis/test_extension_compare.py::test_fresh_native_excludes_every_persisted_screen_user_claim`
- `FAILED .scratch/selective-deception/analysis/tests/test_evaluate_wikitext_final.py::test_identical_logits_allopen_identity`
- `FAILED .scratch/selective-deception/analysis/tests/test_evaluate_wikitext_final.py::test_request_full_file_and_provenance_validation`
- `FAILED .scratch/selective-deception/analysis/tests/test_evaluate_wikitext_final.py::test_request_rejects_updated_export_with_wrong_lineage`
- `FAILED .scratch/selective-deception/analysis/tests/test_evaluate_wikitext_final.py::test_request_rejects_stale_source_even_with_unchanged_artifacts`
- `FAILED .scratch/selective-deception/analysis/tests/test_evaluate_wikitext_final.py::test_score_blocks_uses_frozen_recipient_targets`
- `FAILED .scratch/selective-deception/analysis/tests/test_evaluate_wikitext_final.py::test_exact_checkpoint_restore_and_binary_mask_guard`
- `FAILED .scratch/selective-deception/analysis/tests/test_evaluate_wikitext_final.py::test_prepare_and_dry_run_are_weight_free`
- `FAILED .scratch/selective-deception/analysis/tests/test_summarize_sparse.py::test_independent_rules_match_frozen_runner`
- `ERROR .scratch/selective-deception/analysis/tests/test_summarize_sparse.py::test_complete_disk_run_audits_real_small_cpu_checkpoints`
- `ERROR .scratch/selective-deception/analysis/tests/test_summarize_sparse.py::test_disk_run_rejects_hash_valid_but_incomplete_latest_cursor`

## Root next checks

After source freeze and prepared manifests: run actual bootstrap and pair dry-runs and retain their output; check sbatch test-only with explicit time; root reserves compute before submission. Neither real wrapper dry-run nor GPU calibration was performed by this worker because frozen prepared manifests were not yet available at handoff. No automatic training starts after calibration.
