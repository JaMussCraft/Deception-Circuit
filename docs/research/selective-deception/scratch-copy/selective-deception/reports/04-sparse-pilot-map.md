# Sparse removal pilot: source map and constraints

Read-only audit of primary `Deception-Circuit` at verified HEAD `9d9c2a9`; no worker worktree files inspected, no models, tests, notebooks, jobs or APIs run. This is preparatory: stage 1 chooses preservation controls, donor scheme and final objective.

## Smallest viable seam

Prefer a standalone `train_selective_mask.py` with a small test module, importing `ModelAdapter`, `NodePruningConfig`, existing dataset tokenization and mask export. Reuse the dual-stream model unchanged. Avoid overloading the existing sufficiency-training objective or `joint` task: neither supplies condition-specific suppression/preservation losses. Only add an opt-in shared-gate draw facility in `l0.py` if separate forwards must use identical samples; a combined batch avoids that change.

Relevant current surfaces:

- `models/__init__.py:89–123`: full model is frozen; node model enables only gate-name patterns and converts their parameters to fp32. Assert the trainable-name set explicitly.
- `models/llama_node.py:249–278`: per-query-head gating before `o_proj`, broadcast over batch, sequence and head dimensions; GQA does not change the unit being gated.
- `pruning.py:116–224`: AdamW, epoch cosine schedule, gradient norm clipping, validation cadence and history logging.
- `tasks/deception.py:37–102`, `dataset/deception_common.py:653–750`: data loading and correct readout at `prefix_length - 1`.
- `analysis.py:554–616`: binary keep-mask export; `evaluation/masks.py` and existing knockout/model tests describe evaluation conventions.

## Gates, signs and optimizer

Let K be a keep gate, R=1-K the removal mask. Forward behavior already is `K*clean + R*donor`. For exactly one parameter per head, enable only `prune_attention_heads`; disable attention blocks, attention neurons, MLP blocks/hidden/output, full layers, embedding and edges. Llama-3.1-8B gives 32×32=1,024 fp32 logits named `model.layers.<L>.attn.head_gates.log_alpha`. Historical “heads-only” coarse runs also trained 32 attention-block gates (1,056 parameters); that hierarchy is unnecessary for a minimal head-count removal penalty.

`l0.py` uses noisy hard-concrete sampling with binary STE during training: forward gates are binary, surrogate gradients pass through clipped stretched sigmoid. Eval is deterministic and binary, `log_alpha > 0`; `final_mode` does not alter this. `model.eval()` therefore cannot train gates. There is no existing relaxed-forward mode. Default logits initialize uniformly [2.5,3.5], producing no deterministic removals initially but roughly 3–8% sampled removal per head. `NodePruningConfig.init_value` is not wired into the Llama gate constructors.

Current sparsity minimizes expected **kept** density, with per-layer weighting and warmup; adding it positively would favor widespread removal. For this gate's actual hard sample, `P(R=1)=sigmoid(-log_alpha)` exactly (the 0.5 threshold cancels stretch/temperature). Use positive `rho * mean(sigmoid(-a))` for sparse removal, optionally reporting expected count too. `1 - gate.get_sparsity_loss()` is a different support-based proxy because existing expected L0 measures nonzero relaxed support. Do not confuse these quantities. `get_num_active()` also uses a different cutoff from deterministic forward; export/count actual eval masks.

Reuse AdamW and clipping initially (existing lr .03; current implicit weight_decay .01), but explicitly record optimizer settings; weight decay pulls positive logits toward zero and can encourage removals. Set weight_decay=0 for the pilot's logits unless deliberately studied. Existing cosine eta_min=.0001 is epoch-based. Save logits, binary K and R, objective terms and selected checkpoint. No base parameter may require gradients or enter the optimizer; clean-path gradients must still propagate through frozen attention/MLP operations.

## Objective and jointly scoring D/H

An illustrative minimization is `L = suppression_D + beta*KL(Pbase_H || Pmasked_H) + rho*E[R]`; an honest-label hinge is an optional additional preservation term. Stage 1 must decide H and thresholds. Existing task hinge `relu(margin - (target-distractor))` preserves the deceptive target on D, and full-model KL on D fights suppression: neither belongs unchanged in the pilot. One bounded-below target suppression surrogate is `-log(1-p_D(target))`, computed stably from target logit versus logsumexp of all other vocabulary logits. It does not force the alternative answer, but decreasing one target can still produce a different lie. Coherent refusal is valid success; generation checks remain essential.

D/H tensors can be concatenated into one dual-stream forward: each layer samples once and broadcasts its head gates across both conditions. Compute separate condition means before weighting so batch composition does not silently set beta. Gradients from both losses accumulate into the same 1,024 logits; donors remain independent of gates. Microbatches need not contain matched row counts. Two separate forwards with new independent gate draws still estimate gradients of the additive expected objective (STE approximation), but do **not** realize the same sampled mask and cannot establish per-mask preservation. Reusing a draw or concatenation resolves that distinction; avoid retaining two large graphs if memory is tight.

## Donors and masks

With no ablation hook, the donor is the native corrupted stream. It runs unpruned on its own residual, detached at embeddings with frozen weights; clean interventions never enter its state. Native SDR corruption swaps the designation site/item and reverses its preferred answer. It is not an honest-instruction donor. On H, its preferred answer can likewise be the opposite of H's clean answer. Document exact donor semantics separately for each condition; do not claim this is deletion.

Passing no corrupted inputs bypasses gate intervention entirely. Zero/mean references require the existing ablation hook while still invoking dual-stream mode. Training/evaluation must use identical donor construction; preserve token alignment and attention-mask equality (forward receives one shared mask).

Save removal heads explicitly. An exported model keep mask marks **surviving** heads; evaluating that object as a knockout circuit reverses the experiment. Do not expand and complement all un-gated MLPs: historical coarse expansion includes every MLP inside the circuit. For evaluator compatibility, construct an explicit removal-head object with no removed MLPs and round-trip against the trained keep-mask forward. Generation must stay on the dual-stream intervention path.

## Split provenance and leakage

Existing SDR/D and SDR/H configs describe model Llama-3.1-8B-Instruct, seed 42, 200/200/1000 train/validation/test, margin .7, created 2026-08-18, max length 128. Build code uses one shared `seen` set across splits; uniqueness is the complete instance tuple, not held-out entities/templates. H is harvested from honest failures within each raw split then marginal-matched, not an exact D/H pair.

The existing `sdr/matched_honest_survivors.json` explicitly says `split: test` (364 original both-stream survivors; criterion-specific IDs may differ). `load_matched_honest` reads the single sidecar without validating its split against the requested split. Never train from that file or stage-1 heldout samples. If matched-instruction H wins, construct/filter train and validation counterparts separately into split-specific artifacts, without overwriting heldout provenance. Keep instance-ID and prompt-hash manifests, check overlap across all D/H roles, fit on train only, choose checkpoints/weights on validation, and reserve test/generations for final assessment. Already inspected test diagnostics make this exploratory, not pristine confirmatory testing. Current default training length 120 differs from dataset 128; reject truncation/readout overflow and record the chosen bound.

## Verification and cost envelope

Add meaningful CPU/tiny-random-model checks: suppression gradient sign; removal penalty gradient sign; only intended logits update; combined D/H gradient agreement with a fixed shared mask; donor independence; all-open identity and known-head replacement; binary keep/removal export equivalence; zero MLP removals; split/sidecar mismatch refusal; unpadded readout. Reuse `tests/test_deception_tasks.py`, `test_knockout_model.py`, `test_dataloaders.py` conventions. Run supported transformers environments when implementing; no checks executed here.

Measured historical pure-coarse-head runs (heads plus blocks), A40, 500 epochs, 200 training rows, batch 7, length 120: 8,540.1–8,699.9 seconds (2.37–2.42 hours) for node pruning, peak 40.719 GiB. Sources are `outputs/llama-8b-instruct_sdr_coarse/*_nomb_*/train.log` excluding nopressure; matching original settings are in `config.coarse.json` (expanded `config.json` has altered gate flags). Paired D+H roughly doubles row work; direct extrapolation is only an estimate. Existing cache stores full sequence/vocabulary logits on GPU, so doubling it risks OOM; a dedicated pilot can cache H reference readout logits only. Estimate with a short timed smoke run before bounding training. Charge root-submitted reservations/retries and every stage to the same 20 GPU-hour cap; zero paid APIs. No launch authorized by this map itself.
