# Hand-back 03: Same-item twin training interfaces and timing gate

Agent: Codex research worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/START.md`, A2. Status: resolved (read-only reconnaissance).

## What changed

Only this report and its hook-required primary-checkout copy are written:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/03-twin-training-recon-handback.md`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/03-twin-training-recon-handback.md`.

No code, datasets, training artifacts, ledger, or shared memory changed. No staged operations.

### Minimal data and training path

1. `/projects/beto/swong2/Alignment/Deception-Circuit/tasks/deception.py` owns directory resolution and loader creation. `/projects/beto/swong2/Alignment/Deception-Circuit/tasks/deception_v2.py` subclasses it without changing behavior. `build_dataloaders(...)` loads train/validation/test, resolves the margin from dataset config, wraps `DeceptionDatasetLlama`, and caches the ordinary clean-stream evaluator. No loss-loop rewrite is needed to change the reference prompts.
2. `/projects/beto/swong2/Alignment/Deception-Circuit/dataset/deception_common.py` supplies `DeceptionDatasetLlama(data, tokenizer, max_length)`. It tokenizes `clean_prompt` and `corrupt_prompt` directly and does **not** call the one-token designation-swap assertion. Returned tensors are `input_ids`, `attention_mask`, `corrupted_input_ids`, `corrupted_attention_mask`, `target_token`, `distractor_token`, and `prefix_length`. Keep clean labels on the recipient. Its docstring assumes swapped answers, but its basic tensor construction does not require that assumption.
3. `/projects/beto/swong2/Alignment/Deception-Circuit/tasks/__init__.py`: `Task.model_inputs(batch)` forwards clean ids, corrupt ids, and **only the clean attention mask**. `Task.target_inputs(batch)` reads the clean prompt only. Thus both prompts must have identical real length and mask, and share a readout position. Merely right-padding different-length prompts is invalid here. Source pair checks must run before the dataset wrapper's truncation can conceal errors.
4. For D, join D and its H twin **within each split** by unique `instance_id`; require pressure ids, items, designation, question, and scaffold identity. Recipient `clean_prompt = D.clean_prompt`; reference `corrupt_prompt = H.clean_prompt`. Keep D `target`/`distractor`. Do not use `H.corrupt_prompt`: that would also swap the designated item. Use `/projects/beto/swong2/Alignment/Deception-Circuit/dataset/matched_honest.py` `assert_clause_aligned_pair` to check the clause-only difference, common length/readout, and BPE boundaries.
5. Existing D and H have both designation streams. Default minimal training is one clean-oriented example per source instance, matching the earlier 200-row training convention. If augmenting with the opposite designation stream, create a separate orientation record from D.corrupt/H.corrupt and **swap target/distractor**, keeping a source-instance grouping id; do not call it a new independent id or allow its two orientations into different splits. Apply the same augmentation decision to D and I.
6. For transparent I, first extend the A1 user-turn builder to train and validation, and produce a same-user-layout neutral-request twin for each split. The original I builder in `/projects/beto/swong2/Alignment/Deception-Circuit/dataset/build_inversion_v2.py` only builds the **test** split. Its system-clause neutral twin cannot automatically serve the new user-turn control. Keep exact matched I/I-neutral tokens outside the user-request replacement span and keep source identity stable.
7. Most isolated implementation: an offline builder writes two private data roots (D-twin and I-twin), each exposing normal task directories `far_v2`, `sdr_v2`, `ser_v2`, normal split storage, and `dataset_config.json`. Each row uses its clean-condition prompt plus neutral reference in the ordinary two prompt fields. Existing `train.py --task <task> --data-dir <root>` then works without a new Task or loss. Record `recipient_condition`, `corruption_kind`, source roots/hashes, original source id, orientation, neutral-twin id, margin/filter rule, and split in dataset metadata; preserve original designation-swap prompts under explicitly named source fields. The CLI condition remains `deceptive` solely as a directory selector in this route: the run manifest must identify actual I data unambiguously, and consumers must read dataset metadata before interpreting the run.
8. Cleaner integrated alternative: add an explicit `--deception-corruption neutral_twin` mode that joins references during `DeceptionTask.build_dataloaders`, register a transparent-I condition, and persist both new switches in resolved config and provenance. This changes more plumbing but avoids calling an I directory “deceptive.” Choose one route before implementation; do not overwrite canonical v2 datasets. Proposed files: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/build_twin_training.py` plus focused tests; optional task/config changes only for the integrated route.

### Loss and behavior semantics

- `/projects/beto/swong2/Alignment/Deception-Circuit/tasks/deception.py` `compute_objective` computes KL from circuit clean-stream logits to **full-model clean-stream logits**, plus `relu(state['margin'] - (logit(target)-logit(distractor)))` at `prefix_length-1`. `/projects/beto/swong2/Alignment/Deception-Circuit/pruning.py` combines `(1-lambda_sp) * (faithfulness_weight * KL + hinge) + lambda_sp * sparsity`. Nothing trains the corrupt stream to emit the recipient target. Therefore D labels remain deceptive and I labels remain requested-inversion labels even though each neutral reference naturally answers with the distractor. Do not relabel recipients to H's answer.
- Old behavior helpers assume corrupt answers flip: `evaluate_behavior` measures corrupt `distractor-target`, and `behavior_passes` requires corrupt argmax=distractor. That expected flip can describe the proposed twin pair, but its same-threshold-on-both-streams policy is **not** the source policy: D/I use their recorded target threshold (0.7 or A1 fallback 0.5), while original H uses its honest threshold (0.3). Do not enable `--deception-runtime-filter` blindly or silently reselect held-out rows.
- `assert_aligned_pair` and original `build_deception_v2.recheck` require exactly one designation-token change: they are wrong validators for this new pair. `contingency.stream_words` also assumes designation-swap stream semantics; use explicit recipient/reference label directions when scoring newly materialized twin pairs.
- `run_evaluation` reads only the clean task outcome. Its accuracy is binary target-over-distractor, with full-vocabulary `chosen_word` separately recorded; it does not establish pressure mediation, specificity, or neutral-reference preservation. A2 masks must still pass the A1 intervention ladder on independent ids.

### Exact pruning flags and defaults

- `/projects/beto/swong2/Alignment/Deception-Circuit/config.py` v2 inherits 500 node epochs, 300 edge epochs, batch 7, length 120, learning rate 0.03, train/validation/test counts 200/200/1000. Default node sparsity is **0.95**, faithfulness weight 1.0, gate init 0.5, sparsity warmup 1000 optimizer steps. Earlier coarse runs used explicit sparsity choices; do not mistake their 0.3 setting for the CLI default.
- For START's heads plus **MLP blocks**, explicitly set `--no-edge-pruning --prune-attention-heads --prune-mlp-blocks --no-prune-attention-neurons --no-prune-attention-blocks --no-prune-mlp-hidden --no-prune-mlp-output --no-prune-full-layers --no-prune-embedding`. Defaults otherwise prune several extra dimensions and blocks. Heads-only fallback changes MLP blocks to `--no-prune-mlp-blocks`; unpruned MLPs are intact, not absent circuitry.
- `/projects/beto/swong2/Alignment/Deception-Circuit/models/__init__.py`: Llama weights are bf16, gates train in fp32, full model is frozen, and `cache_target_logits=True`. `train.py` disables training shuffle for that cache. Cache keys are batch indices, so immutable order and batch size matter. Both a full 8B model and a prunable 8B model are resident, plus cached full-sequence vocabulary logits and training activations; use H100/H200/A40, not 40 GB A100. A heads-only fallback is not guaranteed to eliminate the memory or runtime cost.
- User-turn prompts may exceed 120 tokens. Derive an explicit common length bound from constructed D/I data and override `--max-seq-length` consistently if necessary. Cache memory and runtime scale with padded length; do not retain 120 and accept silent truncation.

### Artifacts and timing pilot

- `/projects/beto/swong2/Alignment/Deception-Circuit/analysis.py` `save_active_nodes` writes `active_nodes.json` containing `active_heads` (layer-string to head lists), `active_mlps` (sorted layers), and `masks`. Coarse masks contain full-width `attention_heads` vectors by layer plus `mlp_blocks` list; absent gate keys mean unpruned. Calculate head/MLP set differences from actual binary masks, not counts or assumed exclusions.
- `/projects/beto/swong2/Alignment/Deception-Circuit/train.py` persists `results.json` (model/task/family/seed, baseline/node/edge eval, dense-edge stats, granularity stats). `/projects/beto/swong2/Alignment/Deception-Circuit/run_io.py` saves resolved `config.json`, `train.log`, training history/plots, and attempts `run_manifest.json`. Require a complete source/data/seed manifest before treating any result as usable. Native manifests invoke git unless `DC_RUN_MANIFEST_GIT=0`; workers under the no-git rule must set that and have the orchestrator supply the recorded commit/hash provenance.
- `/projects/beto/swong2/Alignment/Deception-Circuit/pruning.py` `_optimize_gates` uses AdamW, cosine decay per epoch, gradient clip 1, initial validation, and validation every 10 epochs. With 200 rows/batch 7: 29 steps/epoch and 14,500 training steps for 500 epochs. No early stopping or optimizer-state resume path was seen in this loop. A short-epoch timing mask changes the cosine horizon and is a timing artifact, not automatically a valid full-run seed.
- The printed pruning timer starts **after target-logit caching**, and excludes full-model load, prunable-model load, baseline test, post-training test, and artifact writing. Measure allocation start-to-finish, cache time, initial validation, warmed training epochs, periodic validation, finalization/test, peak memory, real row counts, and hardware. GPU synchronization is needed around isolated timing intervals. Use planned full row counts, batch, sequence length, model, and granularities for the pilot; include a validation event and distinguish cold warmup from steady state. If sampling a few epochs, extrapolate training and evaluation separately and add measured fixed costs; report an uncertainty range and reasonable buffer, not a claimed benchmark runtime.
- A2 is **18 masks** (3 tasks × D/I × 3 seeds). The >6 GPU-hour fallback trigger is not a fleet budget: 18 × 6 = 108 GPU-hours, above the 60-hour phase cap. Before reserving the fleet, total projected **reserved** time, including pilot and other A2 work, must fit 60 hours; average per-mask allowance is below 3.33 hours after overhead. START's timing dry-run gates reservation. If one mask exceeds 6 hours, use heads-only; if that fallback exceeds the phase cap, stop per START. No phase-cap increase is authorized.

## How verified

Source inspection in the worktree, including these exact commands:

```
sed -n '50,170p' train.py
sed -n '366,490p' train.py
sed -n '653,708p' dataset/deception_common.py
sed -n '117,145p' pruning.py
sed -n '140,365p' pruning.py
sed -n '610,666p' dataset/build_deception_v2.py
sed -n '554,619p' analysis.py
sed -n '795,820p' analysis.py
```

Observed: clean-only objective and reference target; direct prompt tensorization; one model mask for both streams; initial/every-10-epoch validation; timer after cache; coarse-mask serialization. Also read v2 defaults, model adapter, START A2, run-config provenance, and script defaults. These are static code observations, not executed training results. Parent supplied weekly usage 3% under cap 80%; no substantial budgeted execution occurred.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No git, implementation, tests, dataset build, GPU/API work, or notebook execution. No measured pilot estimate, mask quality, or Jaccard result exists from this reconnaissance.
- Needed meaningful checks: split/id and orientation leakage rejection; source item/question preservation; clause-only exact token alignment and common masks; unchanged clean KL/hinge labels; invalid/overlength prompts fail before truncation; same-item H.clean chosen instead of H.corrupt; loader count matches requested count; source-specific thresholds; mask round-trip; no-op reference and full-gate baseline agreement.

## Open questions

- **A1-dependent:** build train/validation I and neutral-request twins only after A1 freezes wording and threshold; never generate training by borrowing the authorized held-out n=100 sample. Default: derive from original disjoint train/validation identities, report attrition, and rebuild from fresh split-specific ids if necessary.
- **Scientific matching:** D/I pool attrition can alter sample count, polarity, form, and steps. Default: use an explicitly paired D/I intersection per split and record balanced strata/counts; if 200 matched training rows cannot be supplied, pre-register matched smaller counts or construct fresh training ids. Keep the test/ladder sample independent.
- **Optimization choice:** START fixes three seeds and coarse head/MLP scope, not sparsity coefficient or epoch count. Default: freeze identical settings across D/I using the prior coarse reference as a starting candidate, then measure timing; do not tune seeds or conditions against held-out specificity.
- **Seed-stability definition:** START calls D-twin minus I-twin seed-stable at Jaccard at least 0.5. Default: pair D/I masks by seed, compute all pairwise Jaccards of those differences, separately report head and MLP membership and empty differences, and freeze whether the gate pools component types before runs.
- **Pilot budget:** 60 hours must cover all 18 masks and pilot costs; use measured fleet projection in addition to the single-mask six-hour gate. Timing uncertainty or a changed plan needs the session's ordinary checkpoint/worklog handling.
