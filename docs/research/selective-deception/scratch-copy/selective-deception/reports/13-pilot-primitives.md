# Ticket 03: CPU pilot primitives handoff

Implemented only `evaluation/selective_mask.py`, `l0.py` and `tests/test_selective_mask.py` in `Deception-Circuit/.claude/worktrees/selective-mask-pilot`. Root owns review, integration and commits. Stage 1 source stayed frozen. No git, pretrained weights, real-model forwards, GPU, jobs, paid API calls, notebooks or subagents were used.

The helper is deliberately one module (362 lines), with five public functions and one dataclass. Existing diagnostics transformations/preflight/semantic keys/derangement are imported directly; neither Stage 1 `build_manifest` nor its selection sampler is called. There is no runner, optimization loop or new sampling mode.

## Public API and runner contract

- `build_pilot_manifest(records_by_split, honest_pool, tokenizer, *, stage1_manifest, candidate_heads, source_metadata) -> dict` reserves raw test > raw validation > train, then actual exposed semantic states, preflights, chooses original representatives, excludes singleton signatures, and rotates donors locally in cluster-hash order. Every exclusion is reported. All eight coverage cells remain explicit, including zero. It retokenizes every actual Stage 1 endpoint before accepting exposure evidence.
- `validate_pilot_manifest(manifest) -> None` checks canonical and nested hashes, source/scenario/prompt relationships, raw reservations, exact donor rotation, nonself donor alignment, prompt lengths/padding/truncation, and semantic/text/full-token isolation across splits and actual Stage 1 endpoints. Frozen serialization validation has no tokenizer parameter; retokenization belongs to construction. Cluster dictionaries retain the existing full preflight schema and `cluster_id`; scoring/generation adapters can continue using diagnostics `_endpoint`.
- `configure_candidate_gates(model, candidate_heads, *, expected_initial_removed=1.) -> list[Parameter]` freezes every parameter, makes every noncandidate/non-head gate hard-open, and enables only candidate-containing fp32 head-logit tensors. Candidate initialization is `log((n_candidates-expected_initial_removed)/expected_initial_removed)`, hence `log(102)` for 103 candidates and count one. The runner must concatenate only eligible entries for the loss and use AdamW `weight_decay=0`. Physical tensors contain other entries whose data-path and pilot-loss gradients are zero; report 103 effective variables.
- `pilot_loss(d_logits, deceptive_token_ids, h_logits, h_base_logits, truthful_token_ids, capable, candidate_logits, *, rho, beta_kl=1., beta_label=1.) -> PilotLoss` implements fp32 deceptive-mass suppression, capable-H full-vocabulary KL, all-H truth-label nondegradation and positive expected removed **count**. `PilotLoss` contains scalar tensors `total`, `suppression`, `capable_kl`, `truth_nondegradation`, `expected_removed`, integers `n_h`, `n_capable`. Base logits detach inside the helper. D and H terms use separate means.
- `export_binary_masks(model, candidate_heads, *, provenance) -> dict` returns `K`, `R`, `removed_heads`, `removal_mask`, `eligibility`, `logits`, `candidate_heads`, candidate/provenance/export hashes and `effective_candidate_count`. `K`/`R` are dictionaries keyed by layer string with per-head lists. `R=1-K` exactly. Deterministic zero logits are removed. The evaluator removal-mask object has head membership and corresponding head-neuron membership, zero MLP hidden/output/block entries, and zero attention-block entries. `safe_knockout(export['removal_mask'])` reproduces trained deterministic forward under the same donor exactly in the tiny model. Caller supplies source/config/data/donor identities in `provenance`; they are preserved and hashed, never inferred here.

`HardConcreteGate.set_eligibility(Optional[Tensor])` is the only additional public gate method. Eligibility is a persistent bool buffer when opted in, follows module device transitions, and combines with sampled or deterministic output using `torch.where(..., ..., ones)`. With `None`, its key is absent from the state dict and old checkpoints load strictly unchanged. For pilot checkpoint loading, construct the same model, call `configure_candidate_gates` with the frozen candidates **before** strict state loading, then load the checkpoint; initialization is overwritten by saved logits. This intentionally avoids a custom state-loading framework. Ordinary frozen-weight graph flow remains intact; masked forwards are not under `no_grad`.

**Aggregation gate for ticket 04:** no-capable-H minibatches produce differentiable zero KL and `n_capable=0`. This does not license a globally empty capable set: ticket 04 must reject that case. During accumulation/epoch aggregation, weight suppression by D-row counts, truth nondegradation by H-row counts, and KL by capable-H counts; an unweighted mean of minibatch KL means changes the objective. Apply the expected removal penalty once per effective optimizer objective, not once for each unnormalized accumulated minibatch. No numerical Stage 1 tolerance or baseline compute path was selected here.

## RED and GREEN evidence

All commands ran from the pilot worktree, offline and thread-pinned:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 <python> -m pytest tests/test_selective_mask.py -q -p no:cacheprovider
```

Before implementation, both interpreters produced **2 failures** (`set_eligibility` missing) and **10 setup errors** (`evaluation.selective_mask` absent). Logs: `/tmp/pilot03-red-base.log`, `/tmp/pilot03-red-mgnp.log`. These were expected missing-API failures, not an unmodified full-suite rerun.

Initial integrated GREEN was 91 passed in each environment. A subsequent additional regression (`test_manifest_rehashed_relational_mutation_is_rejected`) first failed with DID NOT RAISE, exposing missing direct source-prompt/rotation checks; those checks were then added. RED log: `/tmp/pilot03-red-relational.log`.

Final required focused command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 <python> -m pytest tests/test_selective_mask.py tests/test_selective_diagnostics.py tests/test_selective_runner.py -q -p no:cacheprovider
```

- `/sw/external/python/anaconda3/bin/python`: **92 passed, 3 warnings in 21.85s**, `/tmp/pilot03-final-base.log`.
- `/u/swong2/.conda/envs/mgnp/bin/python`: **92 passed in 14.97s**, `/tmp/pilot03-final-mgnp.log`.

Base warnings concern pre-existing bottleneck/pandas, TRANSFORMERS_CACHE deprecation and TensorFlow ml_dtypes deprecation. The bounded worker did not run an untouched full baseline or full integrated suite; root may run its one integrated post-edit suite and compare existing failure names.

Tests cover corrupt-stream truth reversal/whole-cluster exposure, raw validation reservation after exposure exclusion, wrapper/outcome metadata independence, singleton exclusion, token collisions, mutations including recomputed outer hashes, extreme/multiple deceptive labels, duplication/condition means, wrong H baselines, empty capability minibatches, positive removal count/gradient sign, hard eligibility in train/eval, legacy loading, deterministic zero threshold, MLP-safe export roundtrip, all-open/self-donor identity, nonself intervention, eligible-only updates, one head-gate draw per layer under joint D/H batching and equal joint/separate gradients under a fixed shared draw. No equality is asserted for independent draws.

## Actual-data cached-tokenizer preflight

Harness: `/tmp/pilot03-preflight.py`; summary: `/tmp/pilot03-preflight-summary.json`. It uses original Arrow records, the matched phrase pool, frozen r1 input manifest, cached tokenizer snapshot `0e9e39f249a16976918f6564b8830bc894c89659`, and the existing CPU circuit resolver for `(D|H|F)-m`. It compares all eight final hashes against the final semantic audit output. No outcomes or model weights are read. An initial harness import typo (`evaluation.compose` rather than existing `evaluation.circuits`) was corrected before successful preflight.

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 <python> /tmp/pilot03-preflight.py
```

Final cached-tokenizer preflight completed successfully under both interpreters (exit 0), with logs `/tmp/pilot03-final-preflight-base.log` and `/tmp/pilot03-final-preflight-mgnp.log`. Reproduced **119 train / 119 validation**, **103 heads**, **122 actual exposed scenarios**, **388 distinct actual texts and 388 complete token sequences**, and zero final train/validation/Stage-1 semantic/text/token intersections. No source/hash mismatch occurred.

- r1 canonical manifest: `29da71bd7cef5f03bec931e5a4231cb93b3bfb026ce3b00f1ea3367a6aab95a0`.
- exposed scenario set: `b2e4c7630552ae1fc12d62d0b90d21b6d653fe2801ecacedad37f4e367b49e10`.
- canonical sorted candidate heads: `6c5943656abc881d8ff949f776a3fa9dc11e7161254a2c16738c7306b8624420`.
- derived manifest with harness source metadata: `27da2ac2098486c144e5d8362c47fdad5852c406809d9bee07f18846450d2302`. This depends on explicit source metadata paths and is not a universal new data pin.

| Hash | Train | Validation |
|---|---|---|
| Retained records | `f9a895ea5e05720c2e658132118c2da6924885b3f2abd582f002f174dc32a737` | `8256872e93a4ba4ba34f5c5c45c4f7dda8c2a29903b3b58f8b73ce23a8a667b8` |
| Representatives | `15e75543b365e739b779a06a11c3f6a063208016c078e646fb09a2824a290d09` | `fc5f4e989a7eba00a65efe70d24030b46fd5b526b04b0a0961ddb53cbc66d9da` |
| Donors | `36f2a7f9f6a6824650c2423d0a3efc19e7a9625bee3d8a5e75eabe815d400ec2` | `4e6b8a1359ead8f6720f35baef582bded3e35a0ed6e17c2039673dbde03b031f` |
| Clean all-view endpoints | `1ab6cf1c7538d17f2286964dff89bf3efd23a82de0d39c3ad2c456b118ba441e` | `47551a18a8e08fb11b7b1a3ea002ca0cf02af75baee0c54b36674ac47ccd1a41` |

| Designation/item/template | Train | Validation |
|---|---:|---:|
| identity/1/audit | 25 | 20 |
| identity/1/lab | 14 | 13 |
| identity/2/audit | 15 | 23 |
| identity/2/lab | 11 | 11 |
| inversion/1/audit | 24 | 24 |
| inversion/1/lab | 0 | 4 |
| inversion/2/audit | 29 | 22 |
| inversion/2/lab | 1 | 2 |

Default construction pins r1 manifest and exposed-scenario hashes. An approved successor requires `source_metadata.stage1_lineage` containing `original_manifest_hash`, `approved_manifest_hash`, nonempty `root_decision`, and `inputs_unchanged_from_r1: true`; both manifest hashes and that decision remain in the derived manifest. Root must verify the exact row IDs, prompt/token inputs, donor assignments and final pilot hashes before making that assertion. This worker used no successor and invented no approval. Synthetic tests patch evidence constants locally rather than opening a production bypass.

## Rulings and remaining gates

Ruling: strict opted-in checkpoint loading requires prior eligibility configuration; legacy None remains exact — keeps the public gate edit minimal and avoids custom loading behavior — cost if wrong: ticket 04 must configure before loading, as documented above.

Ruling: return zero/count-zero KL for an empty capable minibatch, with global validation/aggregation delegated to ticket 04 — the pure helper cannot infer global capability — cost if wrong: naïve minibatch averaging changes preservation weighting; the runner contract above makes the required denominators explicit.

Ruling: preserve and hash caller-supplied export provenance rather than invent source/config/data/donor identities inside a model-only exporter — cost if wrong: ticket 04 must supply those identities before persisting/exporting.

Implementation verification does not establish Stage 1 compute-path validity, usable H-capable coverage, donor validity, generation quality, specificity, or acceptable measured fitting/export cost. Those scientific/root cost gates remain open. No ticket 04 code or production fitting was started. Root should perform its fresh review and explicit-file integration; author self-review is not an independent review.

Root subsequently notified this worker that Stage 1 same-path fix `faa4109` and approved r2 lineage were recorded in report 17. Per root instruction this handoff keeps r1 preflight unchanged; root will bind that successor for ticket 04 after reviewing these frozen edits. No successor inputs or Stage 1 source were changed by this worker.
