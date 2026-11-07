# H100 timing repeat matches the saved H200 reference

Status: handed-back

## What changed

Compared the fetched H100 SDR D/I timing repeat with the original H200 references under the predeclared plan. The result is **exact no observed drift in every saved comparison field**. The reference gate passes; scientific fleet placement and resource admission remain root decisions. Both runs use the genuine timing-only cosine schedule, not a prefix of the full scientific schedule. No original receipt or native output was changed. [Comparison and scope](124-h100-timing-comparison-evidence/comparison.json).

## How verified

Authenticated both receipts, every declared native-file hash, complete native manifests, frozen archive/source closure, model revision/software, exact training arguments, native configurations, dataset hashes and ordered row identities. H100 virtual native paths map exclusively into the explicit fetched `returned-native` root. No fallback to legacy H200 files is allowed. Config, active-node mask, results and history bytes match exactly within each arm. Native manifests retain the expected differences in script location, creation time, working directory, host, job ID and manifest hash. Protected-registry path aliases resolve to the same files and content. [Integrity evidence and actual paths](124-h100-timing-comparison-evidence/comparison.json).

The initial analysis attempt expected the receipt hash in the per-arm execution record; it is appended by the parent completion record. That script/schema assumption was corrected after checking every shared field and the actual parent receipt hash. The first script and trace are preserved. No input or numerical policy changed. [Commands and preserved failure](124-h100-timing-comparison-evidence/run_manifest.json).

## Execution evidence

Job 50147300 on cluster `bridges2` completed with exit `0:0` in 481 seconds, from `21:01:04` to `21:09:05 UTC`. Its receipt reports a single H100. This author task performed local model-free JSON/file analysis only; no GPU, model, scheduler or remote action was run. [Fetched accounting and hardware provenance](124-h100-timing-comparison-evidence/comparison.json).

Each arm preserves 187 train, 187 validation and 952 test IDs. Across baseline test, final node test and validation epochs 0/10/20, all 4,930 paired evaluation rows were retained, including repeated evaluation of the same subjects. All 14,790 saved selected-logit/margin comparisons are exactly equal. The primary baseline/epoch-zero references contain 2,278 paired rows. There are no decoded-choice or margin-sign/strict-decision changes. Every reported mean, RMS, percentile and maximum absolute delta is zero. [Full row comparisons and summaries](124-h100-timing-comparison-evidence/comparison.json), [all paired rows](124-h100-timing-comparison-evidence/paired-rows.jsonl).

All 20 values in each loss/KL/task/sparsity/learning-rate trajectory match exactly, as do the validation checkpoints and final native aggregates. Binary masks also match exactly: D has 796 heads and 30 MLPs; I has 735 heads and 26 MLPs. Every mask Hamming difference is zero and Jaccard is 1. No efficacy-based arm/seed selection or tolerance widening was used. [Trajectories and diagnostic deltas](124-h100-timing-comparison-evidence/comparison.json), [mask comparison](124-h100-timing-comparison-evidence/mask-comparison.json).

Observed timing values are receipt process seconds and rounded console pruning seconds. [Timing records](124-h100-timing-comparison-evidence/comparison.json).

| Arm | H200 process | H100 process | H200 pruning | H100 pruning |
|---|---:|---:|---:|---:|
| D | 191.82 | 213.34 | 121.3 | 138.5 |
| I | 192.73 | 188.58 | 123.0 | 130.7 |

Both H100 arms report the same native peak-memory field, 52.222. Their receipt process times sum to 401.92 seconds; 79.08 seconds of allocation time lie outside those measured processes and remain separate from pruning. Container-wrapper elapsed times and batch RSS are retained in the raw result. [Resource and timing evidence](124-h100-timing-comparison-evidence/comparison.json).

## What is NOT done

No full-vocabulary logits/probabilities, raw argmax token IDs, per-row KL or legacy runtime token arrays were invented. Decoded-choice equality does not establish raw token-ID equality. Baseline KL/exact-match self-reference defaults are not a cross-device test. The saved selected-logit and metadata comparisons are the evidence actually available.

This was the same 20-epoch timing schedule on each GPU type; it does not validate full500 outcomes or provide a hardware noise distribution across seeds. No full scientific source audit was applied to these timing receipts. No masks, seeds, cohorts, hyperparameters or same-path tolerances changed. [Predeclared scope and limits](124-h100-timing-comparison-evidence/comparison.json).

## Open questions

Independent drift review remains the next gate. Root can use the observed timing/resource data for a bounded scheduling plan while keeping the scientific SDR suite on one GPU type. The process-only work-count extrapolations in the raw result exclude future outer protection/startup variability and reservation buffers; the observed filesystem/cache state is not a guaranteed cold-host bound. All author analysis processes are terminal, and the original H200 references remain intact.
