# Saved H200 reference and predeclared H100 timing-repeat check

Status: handed-back; read-only design, before H100 observations or submission.

The saved H200 references are sufficient for a meaningful paired baseline/pre-update drift check and an end-to-end timing repeat. A fresh Delta GPU reference is not required. This does not establish full-vocabulary equivalence or authorize the fleet.

## Saved evidence

The exact receipts are `outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/sdr_v2-D-seed42.json` and `sdr_v2-I-seed42.json`. Their native `config.json`, `results.json`, `history.json`, `active_nodes.json` and `run_manifest.json` paths/hashes are enumerated in [reference-schema.json](reference-schema.json). All declared native artifact hashes, recorded training-source hashes and native dataset-file hashes match current bytes. Row order, uniqueness and aggregate accuracy/mean-margin reconciliation also pass. The [extractor](extract_reference_schema.py) uses only standard-library reads.

| Saved artifact/field | Actual H200 reference per arm |
|---|---|
| `results.baseline.outputs`, `results.node_eval.outputs` | 952 test rows each, in exact receipt test-ID order |
| Per-row numeric/choice fields | `logit_target`, `logit_distractor`, `logit_difference`, decoded full-vocabulary `chosen_word` |
| Per-row identity | `task`, `condition`, `instance_id`, target/distractor and native entity/template/designation metadata |
| Aggregate evaluation | `accuracy`, `logit_diff`, `kl_div`, `exact_match` |
| `history.node.evals` | Epochs 0, 10 and 20; 187 validation rows each, exact receipt validation-ID order |
| `history.node` trajectories | 20 values each for `loss`, `kl`, `task`, `sparsity`, `lr`, with epoch indices |
| `active_nodes.masks` | Complete binary head arrays and MLP arrays; D retains 796 heads/30 MLPs, I retains 735/26 |

All table quantities and exact file locations are in [reference-schema.json](reference-schema.json). Native directories contain JSON, train logs and PDF plots; no soft-gate, optimizer or RNG checkpoint is saved. The head/MLP masks are JSON binary arrays, not saved soft parameter tensors.

The original H200 launch config `outputs/_analyses/specificity-ladder/a2-timing-h200-config.json` matches the receipt's `config_file_sha256`. The current default config differs; root confirms the deployment uses the accepted frozen application/archive plus that exact original launch config, with original Delta paths preserved in the namespace. Native manifests retain model revision, software versions, source/build execution commits and dataset hashes. Raw file hashes and canonical/launcher-resolved digests are different fields for the same inputs: the build raw hash is `3183d1cb…` and canonical digest `616b6605…`; the launch config raw hash is `4321ef82…`, while `be2f4e7b…` hashes the config after the launcher adds its absolute `data_root`. The archive default differs from that explicit launch config only in `output_root`; it is not the same file. [Launch/source evidence](reference-schema.json), [exact provenance reconciliation](provenance-reconciliation.json), [clarification](provenance-clarification.md).

## Comparison declared before the repeat

Repeat both arms with seed 42 and actual 20 epochs under the same frozen source, resolved native config, cohorts, model/tokenizer snapshot, batching and pruning flags; allow the authenticated frozen script location, explicit new physical output destination and host/job/time provenance to differ. Scientific arguments and input identity stay fixed. Check complete ordered IDs and metadata within each arm; do not compare D rows with I rows as a hardware control. [Machine-readable plan](predeclared-comparison.json).

Use unpruned test `baseline.outputs` as the primary paired numerical reference and initialized-node validation `history.node.evals[epoch=0].outputs` as the pre-update path reference. For every selected logit and margin, report signed mean, mean absolute/RMS error, absolute-error percentiles and maximum; retain all rows and identify every decoded-choice or strict target-versus-distractor decision/sign change, including ties. These are actual paired selected-logit references. Decoded-word equality is not proof of raw token-ID equality. [Fields, statistics and decision rules](predeclared-comparison.json).

Compare later validation, final `node_eval`, all loss components and binary mask counts/Hamming differences/intersection/Jaccard separately as end-to-end retraining diagnostics. Different retrained masks confound a fixed-mask hardware comparison. Do not use fidelity, mask overlap, loss or speed to select arms/seeds, retune settings or replace an accepted scientific cell. The eventual SDR suite stays wholly on H100; legacy H200 timing masks are not mixed into it. [Scope and diagnostic rules](predeclared-comparison.json).

## Decision rule and timing

Exact identity/integrity, row coverage, finite values, epoch indices and learning-rate schedule are prerequisites. Exact paired pretraining values/decoded choices constitute the no-observed-drift state. Any nonzero pretraining numerical delta or changed decision is reported in full and held for independent drift review before fleet release. A single legacy run supplies no empirical cross-hardware noise distribution: this plan invents no equivalence band and permits no post-hoc widening of existing same-path tolerances. Existing sanity guards remain unchanged; their thresholds do not apply to different retrained masks. [Predeclared decision rule](predeclared-comparison.json).

Timing20 uses its genuine 20-epoch cosine schedule, with `T_max=num_epochs`; it is not the first 20 epochs of a 500-epoch schedule. Compare the repeat only with that same timing schedule. Report receipt `total_seconds`, rounded console `pruning_seconds` and `peak_memory_gb` separately; observed H100 startup/resource measurements govern scheduling. [Saved trajectories](reference-schema.json), [schedule rule](predeclared-comparison.json).

## Limits and next boundary

No legacy full-vocabulary logits/probabilities, hidden activations, raw argmax token IDs, per-row KL or tokenized batch/readout arrays are saved in these results. Baseline `kl_div=0` and `exact_match=1` are self-reference defaults, not a cross-GPU test. Aggregate pruned KL/exact match compare each circuit with its own same-host full model and cannot reconstruct cross-device KL. [Evaluator/schema evidence](reference-schema.json).

The proposed retraining repeat does not execute the identical saved H200 final mask on H100. If that distinct question later needs isolation, the existing binary masks and saved per-row pruned results already provide its Delta reference for a separately scoped H100 replay; no new Delta reference is inherently needed. This note ran no model, GPU, jobs, notebook, API, git or source/harness edits. Root/reviewer retain the wrapper dry-run, provenance/protection, resource-cap and observed-drift gates before further execution.
