# Sparse-mask / WikiText implementation audit — 2026-10-19

Read-only source/data inspection; no model loading, GPU, scheduler, network, installs, git or nested agents. Only this report written. Paths below are relative to `Deception-Circuit/.claude/worktrees/selective-mask-pilot/` unless absolute. Existing code is the previously reviewed, unrun trainer; amendment-2026-10-19 supersedes its behavioral launch gate, not its historical results.

## Executable seams and required changes

- `train_selective_mask.py`: CLI currently has no collateral-arm, WikiText, or candidate-space options. Add those explicitly, with frozen weights/block counts and source fingerprints.
- `evaluation/selective_mask.py:264`, `pilot_loss`: D suppression is mean `-log(1-P(deceptive token set))`; H preservation is capable-H full-vocabulary KL(base||masked), plus all-H mean `relu(NLLmasked(truth)-NLLbase(truth))`. Removal penalty is `rho * sum(sigmoid(-candidate_logits))`. Existing helper can remain the H loss and D source; add a small differentiable WikiText reduction rather than duplicating training infrastructure.
- `evaluation/selective_mask_runner.py:176`, `_joint_logits`: exactly one unpadded D/H pair, both sharing one gate draw, same split-local nonself clean-H donor, returns only last-position fp32 logits. Keep this validated geometry for SDR. WikiText requires a separate full-sequence forward adapter with explicit fixed block donor pairing.
- `_train:544`, `_weighted_loss:163`: current accumulation already correctly weights row means by update-window H/D counts and KL by capable count, adding removal penalty once/update. Extend with WikiText token numerator/count; do not sum microbatch means. WikiText-only must set BOTH H KL and H truth terms to zero. H logits may still be computed for a matched forward geometry but cannot enter its objective.
- `_read_manifest:119` hardcodes 103 plus candidate hash; `_prepare:713` checks frozen candidate bindings. Primitive `configure_candidate_gates:301` already accepts any in-range head list and initializes with `log((N-1)/1)`; `export_binary_masks:333` already exports only eligible removals and zero MLP removal. Extend binding validation/manifest provenance, not model architecture.
- `_identity`, `_source_files`, `_baseline_fingerprint`, `_plan`, `_receipt`, `_checked_cache`, `_metrics`, `_validation`, `select_checkpoint`, and final-evaluation paths require new arm/candidate/WikiText/protocol metadata. Review cache identity separation carefully: old receipt/selection comparisons assume one objective and no WikiText state. Preserve old files and failure results.

## SDR target without failed generation gate

Scientifically yes: the task supplies a declared deceptive readout label and nonzero differentiable suppression signal independently of whether the intact model generates a deceptive free response. Optimize/report **SDR deceptive-label suppression / answer routing**, then separately evaluate generated instructed lying and incentive-driven deception. A readout gain alone is neither evidence of either generated behavior nor a discovered general deception circuit. Refusal is valid generated suppression.

Operationally existing code cannot run unchanged: `_receipt:400` requires `policy=report18-v1`, `stage1_behavior=passed`, `generation_headroom=passed`; `_checked_cache:534` requires old H capability usability. Implement an explicit amendment-v2 receipt and factual historical gate fields, not fabricated `passed` values. Preserve same-path baseline, numerical calibration, finite gradients, meaningful D signal, cache validity and measured-cost gates. H-capability requirements should be arm-specific: H-containing arms need a usable capable denominator; WikiText-only does not mathematically require capable-H but still reports all H evaluations. No benign-control result gates fitting under the amendment.

## Cached WikiText and LM hooks

Verified all three local Arrow files and metadata at:

`/work/nvme/beto/swong2/datasets/Salesforce___wikitext/wikitext-2-raw-v1/0.0.0/b08601e04326c79dfdd32d625aee71d232d685c3/`

- `wikitext-train.arrow`: 36,718 text rows.
- `wikitext-validation.arrow`: 3,760 rows.
- `wikitext-test.arrow`: 4,358 rows.
- `dataset_info.json`: dataset `wikitext`, config `wikitext-2-raw-v1`, version `0.0.0`. Hub `refs/main` currently contains the same `b08601e04326c79dfdd32d625aee71d232d685c3`. `/u/swong2/.bashrc` exports `HF_HOME=/work/nvme/beto/swong2`.

No Arrow content/tokenization performed here; metadata confirms files/splits, not token counts or a checked token manifest. CPU preparation should load explicit local Arrow files (or pinned offline cache), hash them and save frozen token blocks with tokenizer identity. Use train only for fitting, validation for selection, test only after freeze. Existing test collateral was already used historically: disclose it as a familiar capability benchmark, not pristine research holdout.

`evaluation/wikitext.py:43` `load_wikitext_blocks` currently hardcodes **test**, concatenates text with `\n\n`, tokenizes without special tokens, chunks to first N fixed blocks, replaces each block's first token with BOS. `pair_blocks` supplies deterministic nonself derangement; reuse this behavior with split parameter/frozen manifests. `wikitext_batches` supplies `(clean, corrupt, attention_mask)` compatible with node-model inputs. Freeze block count/length/pair seed and provenance separately for all three splits; never train using the existing test loader by accident.

`reference_log_probs`, `_nll`, `_kl_and_nll`, `collateral_damage` already define KL(base||masked), next-token NLL and perplexity ratio. They are evaluation-only: `collateral_damage` is under `no_grad`, reductions cast tensors to Python `float`, configurations are applied as deterministic masks. Reuse formulas/pairing/evaluation reporting; write tensor-preserving training reduction. Existing KL averages all positions, NLL predicts positions 1..S-1 from 0..S-2. Prefer a declared common **S-1 predictive positions** for training KL/NLL, and identify any difference from historical all-position KL in reports.

## All-head space and memory

Llama-3.1-8B has 32 layers x 32 query-output heads = **1,024** eligible variables, versus 103. `models/llama_node.py:249-263` gates per-query-head output after attention and before `o_proj`. GQA shares K/V computation, but does not reduce these 32 output units to eight KV groups. This is output-head interchange, not independent Q/K/V circuit discovery. Keep all MLP/block/neuron gates hard-open. Backprop still traverses the frozen model; 10x gate count does not imply 10x model runtime, and starting at layer0 can increase retained activation/gradient memory. Measure rather than scale linearly.

Vocabulary V=128,256. Existing H readout cache is `238*V*4 = 122,100,480` bytes (~116.4 MiB), before metadata. Full-vocabulary WikiText reference cache is `N*S*V*bytes`: 16x128 fp32 ~0.98 GiB; 32x128 ~1.96 GiB; 32x512 ~7.83 GiB. BF16 halves storage but changes reference precision and needs validation. FP32 log-probability/probability copies and autograd tensors multiply transient GPU use. Chunking reductions alone does not eliminate the model's full output-logit allocation or retained backward graph. Cache on CPU and stage one block, or compute intact reference under no_grad per block with a measured time tradeoff.

Empirical next-token NLL requires token targets and, for nondegradation, only one detached base NLL/token: 32x128 FP32 scalar references are ~16 KiB instead of ~1.96 GiB. It does **not** preserve the intact predictive distribution and must not be called KL. KL matches existing H preservation semantics; the smallest cache is achieved by fewer short training blocks, not silently substituting NLL. Evaluate both KL and NLL/PPL in every arm regardless of fitting choice.

## Smallest matched grid and costing recommendation

Recommended initial comparison: **3 arms x 2 rhos {0,.01} x 1 seed = 6 restricted fits**. Existing four-rho grid is not necessary to answer the three-arm question; document amendment rather than silently changing it. Rho0 is the removal-cost ablation; rho.01 keeps existing expected-count units. Both shared budgets and identical initialization/row order/validation cadence matter. Repeat the same grid on all heads only if a prespecified useful-result criterion fails and measured cost fits the authorized tranche. No retry/sweep escalation.

Use `L = L_D + I_H*(KL_Hcap + hinge_Htruth) + I_W*KL_Wtoken + rho*E[removed]`, unit coefficients initially. Separate means keep H+W an additive two-domain constraint; do not divide it by2 or normalize by pooled D/H/W tokens. Within each optimizer window normalize D/H by their row counts, H-cap KL by capable count, WikiText by scored token count. Log each numerator/count, raw loss and gradient norm. Fixed WikiText blocks must be visited on a fixed schedule with equal token exposure in W-containing arms; do not attach an unweighted full-block mean to every SDR microbatch.

Start candidate numerical/throughput smoke with 16 train and16 validation blocks of128 tokens, one-block microbatch, fixed derangement; freeze final block/token counts only after offline token preflight and memory measurement. This is a small pilot subset, not a broad capability guarantee. Evaluate all-H/capable-H accuracy, truth probability/nondegradation/KL, benign-control truth/instruction following, WikiText KL/NLL/PPL, generated D suppression/coherence/refusal, removed count, and fixed matched-size random nulls in every arm. Keep the common preservation-based admissibility policy across arms, or explicitly present full frontiers; arm-specific reporting/selection hides collateral tradeoffs.

Critical update-budget detail: default expected removal1 initializes logit≈4.625 for103,≈6.930 for1,024. At lr.03 deterministic threshold crossing may need many updates; a handful of smoke updates cannot establish that the search is uninformative. Measure gate movement/gradient and choose enough equal optimization updates before invoking all-head fallback. Do not relax deterministic threshold or use top-k post hoc.

No historical mask backward throughput exists: trainer never ran. Report20's245s/116 outputs and ledger generation runs cannot price optimization. Root smoke must time separately model load, self-donor cache, actual-donor all-open A/B and autograd C calibration, warmed D/H forward+backward, WikiText forward+backward, deterministic119-pair validation, WikiText validation, checkpoint I/O, and peak allocated/reserved memory on actual A40/H200. Price `6*(updates*t_update + n_validations*t_val + checkpoints*t_io) + shared cache/load + final generation + margin`; all-head uses its own measured update/memory. Existing20h cumulative cap and4h reserved leave16h before new reservations, subject to live root ledger. No trustworthy numeric production reservation can be inferred from generation timings.

## Worker boundary contract (follow-up for selective-wikitext worktree)

This additive interface proposal assumes a new `selective-wikitext` worktree based on08c032f; no implementation here. Worker A owns **only** new `evaluation/selective_wikitext.py` and `tests/test_selective_wikitext.py`. Worker B owns existing runner/CLI/wrapper integration and its tests. A must not import the existing selective-mask runner, mutate gates, select checkpoints, create model contexts, or make model forwards; B imports A. Both preserve concurrent work. Freeze this small API in the tickets so independent workers agree:

```python
# Python3.9-compatible annotations (Optional where needed).
# JSON dict manifest; token blocks are embedded lists of integers, not Arrow objects.
build_manifest(tokenizer, *, arrow_paths: dict, expected_arrow_sha256: dict,
               tokenizer_identity: dict, n_blocks: dict,
               block_size: int = 128, pairing_seed: int = 0) -> dict
validate_manifest(manifest: dict) -> None
iter_blocks(manifest: dict, split: str)  # yields dict below, stable source order

# Each block: {'block_id': str, 'input_ids': LongTensor[1,128] CPU,
#  'corrupted_input_ids': LongTensor[1,128] CPU,
#  'attention_mask': LongTensor[1,128] CPU, 'n_tokens': 127}

cache_fingerprint(manifest: dict, reference_identity: dict) -> str
write_reference_block(cache_dir, *, fingerprint: str, block_id: str,
                      logits: Tensor, input_ids: Tensor) -> dict
read_reference_block(cache_dir, *, fingerprint: str, block_id: str) -> dict

# Returns tensor scalars with gradients through masked_logits only.
block_loss(masked_logits: Tensor, reference_log_probs: Tensor,
           input_ids: Tensor) -> WikiTextLoss
# WikiTextLoss dataclass fields: kl_sum:Tensor, nll_sum:Tensor, n_tokens:int.
```

`build_manifest` defaults are frozen explicitly by B to `n_blocks={'train':16,'validation':16,'test':32}` and length128. Read only the three explicit cached Arrow paths above (e.g. `datasets.Dataset.from_file`, no `load_dataset` network fallback). Require and verify each root-supplied SHA256; include source path, SHA256, tokenizer identity, dataset revision/config/version, text-join rule, BOS replacement, exact block tokens and per-split donor permutation/hash in canonical manifest hash. Validate count>=2, lengths, token bounds if supplied, all-ones masks, block IDs/hash integrity and a split-local nonself permutation. Deterministic first-N full blocks from separately concatenated splits; insufficient tokens fails, never wraps or pads. Fingerprint model/tokenizer/source/hardware/numerical path via `reference_identity`; no global mutable context. CPU preparation computes actual hashes, not guessed constants.

Per-block cache layout: `<cache_dir>/<fingerprint>/<block_id>.pt`; atomic temp+replace; refuse overwrite; payload `version=1,fingerprint,block_id,input_ids_hash,n_tokens=127,reference_log_probs=float32 CPU contiguous[1,127,V],base_nll_sum=float64/Python scalar,payload_digest`. Cache write receives intact full logits `[1,128,V]`, detaches, rejects nonfinite values, saves `log_softmax(logits[:,:-1].float(),-1)`; base NLL uses actual next tokens `input_ids[:,1:]`. Read validates fingerprint/block identity/digest/shapes/dtype and remains CPU. B transfers only the current block's log-probs to the logits device. Test cache stores no GPU tensors or model state. At128tokens, one block is~62.1MiB, 16block train cache~0.97GiB; all64blocks~3.88GiB. Do not eagerly load all references onto GPU. File checksums, not unsupported assertions about numeric equivalence, bind cached reference content.

`block_loss` takes `[1,128,V]` masked logits and `[1,127,V]` detached reference log-probs, uses fp32 math on positions0..126, returns `sum KL(Pbase||Pmasked)` and empirical next-token `sum NLL`; denominator127. Validate matching shapes/devices, finite values, valid token IDs and detached reference. KL is the **only WT training term**. NLL is a reported metric; no empirical-NLL training or NLL hinge unless subsequently requested by the scientific advisor. Chunk reductions if needed, without `float()`/`.item()` on masked loss paths. The runner divides summed KL by total scored WT tokens in its declared update window. Module A does not choose arm weights, scheduling, H gating, or admissibility thresholds.

Forward ownership and intervention semantics: B calls `ctx.node_model(input_ids=clean,corrupted_input_ids=donor,attention_mask=ones,use_cache=False).logits` **without** `[:,-1]`, yielding full `[1,128,V]` logits. The training WT donor is the frozen other block from the split-local derangement, using the same existing **interchange** semantics as SDR. Do not switch WT to zero ablation or self donor when masked: self donor would erase the preservation cost. The all-open intact cache uses dual-stream self-donor, matching the existing baseline path; B separately verifies all-open self versus actual donor and forced-open autograd with actual donor for this block geometry before fitting. Numerical failure stops and records evidence; no threshold widening.

B owns model/gate contexts: cache under temporary all-open/eval/no_grad with **every gate** restored afterward; training in `model.train()` with only eligible query-head entries trainable and noncandidate/MLP/block/neuron gates exactly open; validation under deterministic `model.eval()`/no_grad using the learned thresholded eligible gates. Existing `_preserve_gates` disables eligibility and temporarily sets eval to let `open_all_gates` work, but restores original logits/eligibility/training state on exit. Never wrap the training forward in it or call `ctx.apply_circuit` on the learned model without save/restore. Unused MLP gates are still present: keep their eligibility allfalse and outputs exactly1, exported removal0. A's iterator is CPU block data only; it must not hide gating context inside a generator whose lifetime could leak into masked forwards.

B extends source/cache/run fingerprints with WT manifest hash, reference fingerprint, arm, coefficients, candidate-space hash, update/block schedule and protocol-v2 receipt. Cache identity may be shared across arms only when their validated reference geometry/model/tokenizer/source identity is exactly the same; run/checkpoint identity must differ. Add calibration/cache counts and bytes to dry-run. B must freeze whether one update visits all16WT blocks or a scheduled subset and weight KL over that window's actual token count; A makes no schedule decision. Validation evaluates H and WT in every arm even when one is absent from the objective. This boundary supports independent CPU tests without duplicating model runtime or changing the original frozen manifests.
