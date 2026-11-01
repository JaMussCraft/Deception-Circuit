# Native-only v4 assessment driver preparation

October21,2026. Separate native-only driver and wrapper prepared without editing frozen training/runtime/launcher files. Actual root-frozen selection receipt validates through the wrapper dry-run: SHA3b095b5774e7521080de92a7af94243acd76e4df9725541f8ce61f55ff23f525, labels new-allW23 and new-allW30, support23/30heads. Driver independently verifies the spending gate using the exact finalist metrics in the bound full-grid audit. No native output selects a case, donor, mask or hyperparameter.

Driver files are `analysis/optimization_v4_native.py`, `optimization_v4_native.sbatch` and `test_optimization_v4_native.py`. The separately owned `optimization_v4_native_results.py` adapter retains the v3 blinded-label contract while naming oldallW28 explicitly; oldW9 is never relabeled or used. Report133 documents that adapter. The shared old comparison, replay and annotation sources remain immutable.

The native prospective source remains byte-pinned to7f3054489bf04ce670c0e93267e21abce13a3faaaf490bcd22db1cab6d4c2f18. Preparation tokenizes only its already-frozen32D/H recipients and32disjoint H donors with the cached tokenizer, exact established manual chat wrapper, add_special_tokens=false and prompt cap1792. It freezes all64source rows,96prompt-ID streams, tokenizer/model metadata, context limit, EOS128009, greedy256tokens, no padding and right-intersection/terminal-hold alignment in a new runtime-input envelope. Generation independently retokenizes every frozen prompt before executing. No tokenizer or model outcome changes membership.

The five conditions are intact, oldD69, oldallW28, new-allW23 and new-allW30. All use the identical removal/interchange protocol; oldD69 is removed here, rather than evaluated as historical sufficiency. Exactly320target generations,32own-context donor generations and64independent all-open controls are required:416maximum256token generations. The stored352physical response views exclude duplicate identity controls. A nonempty, exactly matching token sequence is required for every intact replay versus its independent full all-open capture. Partial donor/target coverage cannot become a packet. No SDR or WT scoring function is called or exposed through the CLI, and no API judging occurs.

The driver reuses the established v3 model loader and native replay calls. It verifies the bound v3 comparison source inventory and native adapter, the entire v4 runtime source freeze, and exact equality of v3/v4l0/config/analysis/model-core bytes. The model/tokenizer inventory equals the precheckpoint expected-run identity. The actual H200 GPU name/CUDA/capability, Python/packages, BF16/SDPA, deterministic settings, TF32=false, workspace and single-device visibility must match the immutable measured runtime. The new envelope binds the new driver/wrapper/annotation adapter, original source hashes, tokenized input hash, frozen selection and actual runtime/job identity. All old receipts and masks remain immutable.

Root execution authorization must be separate from selection. It must match comparison_inputs (the original prospective file), prepared_inputs (the new tokenized envelope), selection_receipt, driver, wrapper and execution_rule byte bindings, plus assessment_authorized=true, suite=native, root_decision, exact five conditions, absolute output_dir, automatic_retry=false and0<estimated_gpu_seconds<=reserved_gpu_seconds<=1800. A proposal with assessment_authorized=false cannot execute. Output directory creation is exclusive, so a partial attempt cannot be retried automatically. The one-H200 wrapper caps allocation at30minutes/no requeue. Per-donor-group and per-generation remaining-time guards supplement Slurm's hard cap.

Prior full five-condition827seconds gives the conservative estimate1.25×827+30=1063.75seconds, about17.7minutes. The native-only assessment omits old SDR/WT work; response lengths can still vary. This is an estimate, not a guarantee or authorization. Root alone reserves the0.5GPUh and submits after independent review132 and actual wrapper dry-run.

CPU preparation command (cached tokenizer only, no weights/GPU):

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python .scratch/selective-deception/analysis/optimization_v4_native.py prepare --output /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/native-inputs.json
```

Final actual wrapper preflight:

```bash
bash .scratch/selective-deception/analysis/optimization_v4_native.sbatch dry-run --selection-receipt /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/selection-receipt.json
```

After root creates a separate final `comparison/execution-receipt.json`, its allocation runs exactly:

```bash
bash .scratch/selective-deception/analysis/optimization_v4_native.sbatch evaluate --prepared /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/native-inputs.json --selection-receipt /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/selection-receipt.json --run-receipt /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/execution-receipt.json --output /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/run
```

The same source's CPU-only `export` mode takes the same input/selection/execution arguments, adds`--run comparison/run`, and uses a fresh `--output comparison/native-packets`. It validates exact completed file/count/source/runtime/replay closure and writes the standard factual-packet/private-map/rubric/packet-manifest schema, six public chunks of at most64rows, seeded anonymous order, response-quality flags and mode0600private map. Public rows contain only anonymous_id, statement, dataset_truth and response. Condition/policy/donor mappings remain private. Adapter analysis requires root-frozen complete blind labels and their hashes before loading private-map JSON.

Root's annotation plan remains352views, two fresh Sol streams plus fresh blind Astra review of flags/disputes/consistency, then root label freeze before private join. No annotation was requested or performed by this preparation. Small native32descriptive comparisons remain explicit instructed lying, with coherent D refusal treated as suppression and H refusal as utility loss. There is no outcome-based reselection or strategic-deception specificity claim.

Final tokenizer artifact, nonauthorizing receipt proposal and dual-environment CPU verification are recorded below.

Final concrete preparation completed with cached tokenizer only. `comparison/native-inputs.json` SHA256:e32a6044da04e1879c59a67a3bdd04854c577265f5ae88c5738dbcdea50bb14b. It contains96frozen prompt streams of63–89tokens and67source bindings. Original prospective inputs remain unchanged. Driver SHA256:091a4c642729f66271f5ec218f4f5426657e6abc98c23943b1c4b4b9c59f6944; wrapper:59222eb33bbbfa97dc2a661ac04acbaed5fc84b68d8391cab61ef6a1453c5557; adapter:bf574b03fb2bc5aff184059f21c4a2f715fdbea7ce185c41db5aac4607ff8ceb.

Concrete `comparison/execution-receipt-proposal.json` SHA256:303eba7b85657d3d5a9a28adf119e780e6c4c9f940130c6cd5f6e0659b418f28. It binds the actual prepared artifact, root-frozen selection/gate, five conditions, runtime source and fresh`comparison/run`destination. It explicitly sets assessment_authorized=false and reservation_created=false. Root must issue the separate final receipt; this preparation authorizes nothing.

Final combined CPU verification:24driver tests plus25adapter tests,49PASS in mgnp(57.18s) and49PASS in base(58.56s). Functional tests use CPU toy tensors and mocked native capture/replay, proving320target+32donor+64control closure, all-open rejection, time-cap stop, strict native-only receipts and352anonymous packet closure. Rehashed input/policy/generation changes and wrong gate/receipt bindings are rejected. The actual wrapper dry-run with the concrete prepared path and frozen selection succeeded; bash syntax passed. Independent source review132 reports no requested fixes. No model weights were loaded, no GPU/API call or annotation occurred, and no reservation/submission was performed by this worker.

Exact future CPU-only packet export command after a complete authorized run:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python .scratch/selective-deception/analysis/optimization_v4_native.py export --prepared /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/native-inputs.json --selection-receipt /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/selection-receipt.json --run-receipt /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/execution-receipt.json --run /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/run --output /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-optimization-v4/comparison/native-packets
```
