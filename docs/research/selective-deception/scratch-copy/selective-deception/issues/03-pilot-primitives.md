# Conditional Stage 2 pilot primitives implementation plan

> **For agentic workers:** Apply writing-plans/executing-plans task by task with the checkbox steps below. This is the already authorized bounded CPU preparation; root owns dispatch, review, git and launches. Do not spawn agents.

Status: ready-for-agent — CPU preparation only; production fitting remains conditional
Type: task
Blocked by: none for pure CPU preparation; Stage 1 validity and root cost gates for model-backed use

**Goal:** Add the smallest tested data/loss/gate/export seam for the 103-head selective-removal pilot.

**Architecture:** One helper imports the existing literal prompt transformations and donor derangement; an opt-in eligibility buffer makes noncandidate gates exactly open. The runner in ticket 04 consumes this API without changing Stage 1 sources.

**Tech stack:** Existing Python/PyTorch, existing dual-stream Llama, pytest; no dependency installation.

**Spec:** `reports/06-sparse-pilot-design.md` is the objective/search contract; read `04-sparse-pilot-map.md`, `08-design-amendment.md`, and the LAST authoritative correction in `07-pilot-data-feasibility.md`. Paths are relative to `.scratch/selective-deception/` unless repository source paths are explicit.

## Global constraints and ownership

- Target isolated worktree: `Deception-Circuit/.claude/worktrees/selective-mask-pilot`, created by root from Stage 1 `ef8cc2a`; root confirmed it ready at clean HEAD `ef8cc2a`. Source audit worktree `selective-deception` stays frozen. You are not alone in the codebase; preserve concurrent edits and report ownership collisions.
- Own only `evaluation/selective_mask.py`, `l0.py`, `tests/test_selective_mask.py`. Ask root to reassign before any other source edit. No model weights, real-model forwards, GPU, API, Slurm, notebooks, git or subagents in this worker. CPU tiny random models are allowed.
- Candidate union is the frozen verified D∪H∪F **103 heads**. No MLP/block/layer/edge/neuron/embedding gates or outside supporters. Freeze base parameters; eligible query-head logits are the only effective optimization variables.
- Data is **119 train / 119 validation paired clusters**, unbalanced, with the missing inversion/item-1/lab train stratum disclosed. No resampling, regeneration, survivor sidecar, new outcome filtering or independent SDR-H substitution. Original source records/weights/controls remain unchanged.
- Zero paid APIs; all real-model work is root-only and conditional. Shared research limit is 20 cumulative reserved GPU-hours including failures/retries, max two active/pending jobs. Proposed Stage 2 ≤9.5h is a costing proposal, never automatic spend.
- Stage 1 self-score drift is unresolved: two failures are one BF16 ULP (0.125 versus atol 0.02), while generation identities pass. Do not freeze a numerical tolerance or choose single-stream versus dual-stream baseline here; root scientific review must validate the compute path.

## Review focus

1. A corrupt Stage 1 endpoint reverses semantic truth: reserving its clean source key would leak an exposed scenario.
2. Deduplication or balancing could admit a different wrapper from an excluded cluster or use final validation outcomes.
3. Sparse-removal regularization has the opposite sign and units from existing kept-density regularization.
4. Noncandidate gates must be exactly one even under adversarial logits/noisy draws; their gradients must be zero.
5. Exporting K as a knockout mask or complementing ungated MLPs would invert the intervention or destroy the model.

## Frozen API for ticket 04

All public functions below live in `evaluation/selective_mask.py`; use Python 3.9-compatible annotations. Define `Head = tuple[int, int]`, canonical JSON-compatible dictionaries for manifest/export data, and one `PilotLoss` dataclass with scalar tensors `total`, `suppression`, `capable_kl`, `truth_nondegradation`, `expected_removed`, plus integer `n_h`, `n_capable`. The manifest has `splits.train` and `splits.validation`, each containing ordered `clusters` and `donor_map`; each cluster retains the existing preflight fields plus `cluster_id`. Root metadata additionally freezes `stage1_manifest_hash`, `exposed_scenario_set_hash`, `candidate_heads`, source identities, exclusion/coverage reports and `manifest_hash`. Ticket 04 consumes these fields directly; preserve Stage 1 endpoint dictionaries for scoring/generation adapters.

- `build_pilot_manifest(records_by_split: dict, honest_pool: dict, tokenizer, *, stage1_manifest: dict, candidate_heads: list[Head], source_metadata: dict) -> dict`: returns the immutable derived training manifest described below, including canonical `manifest_hash`, exclusions, counts, source/donor maps and hashes. `records_by_split` contains original train/validation/test in stored order. It contains no predictions, capable flags or weights inferred from outcomes.
- `validate_pilot_manifest(manifest: dict) -> None`: checks schema/hash, split/exposure isolation, twin/donor alignment, nonself donors, candidate binding, lengths/readouts and frozen provenance; raises on mismatch rather than repairing inputs.
- `configure_candidate_gates(model, candidate_heads: list[Head], *, expected_initial_removed: float = 1.0) -> list[torch.nn.Parameter]`: installs eligibility, explicitly initializes candidate logits to `log(103 - 1)` for expected count one, disables every other parameter, and returns only per-layer eligible-head-containing fp32 logits. Physical tensors may include noncandidate entries; forward/loss masking must give those entries zero gradients and keep them unchanged with weight_decay=0. Report 103 effective variables, not 1,024.
- `pilot_loss(d_logits, deceptive_token_ids, h_logits, h_base_logits, truthful_token_ids, capable, candidate_logits, *, rho: float, beta_kl: float = 1.0, beta_label: float = 1.0) -> PilotLoss`: logits are `[rows,vocab]` at the designated readout, base logits detached, capability is a frozen bool mask. `deceptive_token_ids` is `[D_rows,n_declared_deceptive_tokens]`; one token is the current task. `candidate_logits` is a flat tensor of eligible logits only.
- `export_binary_masks(model, candidate_heads: list[Head], *, provenance: dict) -> dict`: includes exact deterministic K and R, explicit removed head IDs, eligibility/logits, hashes and an evaluator-compatible removal mask whose MLP entries are all zero. Selection never changes threshold or uses top-k.
- Add only `HardConcreteGate.set_eligibility(eligible: torch.Tensor | None) -> None` in `l0.py` (spell union as `Optional[...]` if evaluated under Python 3.9). Default None preserves legacy behavior/state loading. Opt-in bool eligibility follows device/state transitions; combine output with `torch.where(eligible, sampled_keep, ones)` in both train/eval paths. No new sampling mode or shared-draw mechanism: joint D/H batching provides shared masks.

## Task 1: Structural manifest and exact exposure boundary

- [ ] Write failing CPU tests `test_actual_corrupt_exposure_flips_truth_and_excludes_whole_cluster`, `test_original_precedence_reserves_all_raw_validation_and_test_clusters`, `test_no_wrapper_replacement_or_outcome_filter`, `test_split_local_derangement_has_no_singletons`, and `test_manifest_rejects_token_collision_truncation_or_mutation`. Use synthetic fixtures with deliberately overlapping semantic keys but different wrappers, token collisions despite unequal text, a singleton signature, and outcome-looking metadata that must not change selection.
- [ ] Run the named new tests in each supported environment and record the expected missing-helper failures; do not rerun the unmodified full-suite baseline.
- [ ] Implement the builder/validator using `selective_diagnostics._scenario`, `_preflight`, `_signature`, `_derangement`, canonical hashing and existing matched-instruction transformations. Do **not** call `build_manifest`/`_select`: those enforce Stage 1's 64/eight-stratum sampling contract. Derive original raw test > raw validation > train reservation first, then reserve actual Stage 1 recipient/donor/reference scenarios (truth=H for clean, D for corrupt), then preflight, original representative rule, singleton exclusion, and split-local hash-ordered rotation. Preserve raw validation reservation even when validation records are later exposure-excluded. Assert semantic/text/full-token nonintersection across final train/validation and every actual Stage 1 endpoint; include all four views and assigned donors. Record every exclusion and all eight coverage counts; never infer exposure from completed result rows.
- [ ] Pin frozen Stage 1 manifest canonical hash `29da71bd7cef5f03bec931e5a4231cb93b3bfb026ce3b00f1ea3367a6aab95a0`, exposed-scenario-set hash `b2e4c7630552ae1fc12d62d0b90d21b6d653fe2801ecacedad37f4e367b49e10`, 122 exposed scenarios and 388 distinct actual texts/token sequences. Default to that r1 evidence. A root-explicit approved successor lineage may update the manifest/source hash for the Stage 1 same-path correction only when exact row IDs, prompt/token inputs, donor assignments, exposed-scenario set and final pilot donor/endpoint hashes remain unchanged; retain both hashes and the root decision, never silently repin. Reproduce final 119/119 denominators plus all report-07 final representative/donor/endpoint hashes in cached-tokenizer CPU preflight; source-change mismatch stops preparation, never updates expected hashes silently. Donor mapping hashes: train `36f2a7f9f6a6824650c2423d0a3efc19e7a9625bee3d8a5e75eabe815d400ec2`, validation `4e6b8a1359ead8f6720f35baef582bded3e35a0ed6e17c2039673dbde03b031f`.
- [ ] Run focused tests to green and record the exact commands/output and reproduced manifest summary in the root handoff.

## Task 2: Objective and candidate gate restriction

- [ ] Write failing tests `test_deceptive_mass_suppression_is_stable_and_gradient_has_correct_sign`, `test_capable_kl_ignores_initially_wrong_h_but_truth_non_degradation_does_not`, `test_removal_penalty_is_positive_expected_count`, `test_eligibility_is_exact_in_train_eval_and_zero_gradient`, and `test_legacy_gate_without_eligibility_loads_unchanged`. Include extreme logits, multi-token deceptive mass, wrong H baseline, duplicated rows/changed condition counts, empty capability stratum and invalid eligibility shape/type.
- [ ] Run the named tests and record RED; implement the API with separate D/H means. Suppression is mean `logsumexp(all)-logsumexp(non-deceptive)`; capable-H uses full-vocabulary KL(Pbase||Pmasked) normalized by capable count; every H row contributes `relu(NLLmasked(truth)-NLLbase(truth))`; regularization is **sum(sigmoid(-eligible_logits))**, positive rho. The pure helper cannot infer global capability: a joint minibatch with no capable H returns zero KL with its zero count explicitly recorded. Ticket 04 rejects a globally empty capable set and preserves the appropriate capable denominator when aggregating. No KL on D or all-row KL-to-wrong. Use stable fp32 loss math on readout tensors, not full-sequence caches.
- [ ] Add tiny random-model behavioral tests: all-open/self-donor identity, nonself intervention changes logits, only eligible logits update, and joint D/H forward receives one gate draw per layer. Compare joint versus separately computed loss gradients under a fixed shared draw; do not require equality for independently sampled draws. Existing gate tests must continue passing without opt-in eligibility.
- [ ] Run focused tests to green in both environments. Preserve ordinary graph flow through frozen model operations; do not wrap masked forward in no_grad.

## Task 3: Exact binary export and handoff

- [ ] Write and run failing `test_export_roundtrip_replaces_only_removed_heads_and_no_mlps` with one deliberately negative candidate, one zero candidate (eval removes at zero), an outside negative logit and live MLPs. Assert `R=1-K`, subset-of-candidates, exact removed IDs and tiny-model exported-knockout/trained-forward equivalence under the same donor.
- [ ] Implement export using existing mask conventions without `get_num_active()` or expansion/complement of every MLP. Save source/config/data/donor/candidate hashes and effective candidate count.
- [ ] Verify with both interpreters, thread-pinned and offline, using `python -m pytest tests/test_selective_mask.py tests/test_selective_diagnostics.py tests/test_selective_runner.py -q -p no:cacheprovider`; Python paths are `/sw/external/python/anaconda3/bin/python` and `/u/swong2/.conda/envs/mgnp/bin/python`, env `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`. Root may run one integrated suite after actual edits and compare failure names against documented base=7/mgnp=8; do not reinstall packages or rerun an untouched baseline.
- [ ] Hand root exact public API, owned files, RED/GREEN evidence, data hashes/counts/coverage and remaining scientific gates. Root reviews and commits by explicit file list. Stop before runner implementation or any real model execution.

## Comments

This ticket prepares structural data and pure functionality. A nonempty capable set, usable donor behavior, generation quality and measured training/export cost remain evidence gates; implementation success does not establish them.
