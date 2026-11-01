# Conditional Stage 2 pilot runner implementation plan

> **For agentic workers:** Apply executing-plans task by task with the checkbox steps below. Root owns dispatch, independent review, git, scientific gates, ledger and launches; do not spawn agents.

Status: DONE — implemented, independently reviewed and committed08c032f; production fit stopped by SDR generation feasibility
Type: task
Blocked by: none for CPU implementation; real model work requires root Stage 1 behavioral/control, prefit-baseline and measured-cost gates

**Goal:** Build a standalone bounded selective-mask trainer and final evaluation adapter using ticket 03's frozen API.

**Architecture:** `train_selective_mask.py` owns CLI and optimization; one small `evaluation/selective_mask_runner.py` owns persistence, deterministic selection and derived evaluation rows if separating these keeps the entry point readable. Reuse existing Session/ModelAdapter, dual-stream gates and Stage 1 score/generate primitives; leave all Stage 1 sources and manifests unchanged.

**Tech stack:** Existing Python/PyTorch/pytest and one Slurm shell wrapper; offline cached artifacts only.

**Spec:** Read reports `04-sparse-pilot-map.md`, `06-sparse-pilot-design.md`, `08-design-amendment.md`, LAST correction in `07-pilot-data-feasibility.md`, and ticket `03-pilot-primitives.md` before implementation. Design 06 governs objective and selection.

## Global constraints and ownership

- Root confirmed the pilot worktree ready at clean HEAD `ef8cc2a`. Work only in root-confirmed `Deception-Circuit/.claude/worktrees/selective-mask-pilot` based on `ef8cc2a`. You are not alone: preserve concurrent changes. Own `train_selective_mask.py`, `evaluation/selective_mask_runner.py` only if needed, `tests/test_selective_mask_runner.py`, `scripts/selective_mask.sbatch`. Any additional source/helper edit needs root reassignment; do not duplicate ticket 03 functionality.
- Worker uses CPU tests/tiny random models only: no real weights/forwards, GPU, submissions, API, downloads, notebooks, git, subagents or package installs. Root alone runs integrated checks and actual jobs.
- Frozen 119 train/119 validation pairs, verified 103-head candidates, original controls/weights, no new screening, no balancing repairs and no test/survivor-sidecar fitting. Train on original-view D/H with the identical split-local nonself clean-H donor for both twins. Other views remain validation/transfer endpoints.
- Head gates only; base frozen. Noncandidates hard-open; no model.eval during optimization. Exactly four rhos `{0, .001, .01, .1}`, beta_KL=beta_label=1, AdamW lr=.03 weight_decay=0, existing clipping. One frozen optimization seed and equal update/validation budgets; max 100 epochs is only a proposed ceiling. No hidden sweep, automatic retry, array or requeue.
- Stage 1 smoke currently has two self-score differences of one BF16 ULP (0.125 versus atol .02), while generation identities pass. Root review must resolve single-stream versus dual-stream intact scoring scientifically. Cache reference, validation intact baseline and masked comparisons must use the validated **same compute path**. No tolerance widening or baseline routing decision is authorized by this ticket; revised source fingerprints must include any root-approved fix. Accept an explicitly root-approved successor to the r1 manifest only through ticket 03's unchanged-endpoint/exposure lineage check; never silently repin the evidence or reuse old result fingerprints.
- Shared limit 20 cumulative reserved GPU-hours including retries/failures, max two active/pending jobs, $0 paid APIs. Training on A40/H200 only (8B OOM on 40GB A100). A proposed ≤9.5 Stage 2 GPU-hour envelope is not authorization to launch every slot.

## Review focus

1. A different intact compute path can change capability flags, utility gates and checkpoint selection at BF16 boundaries.
2. A cache or checkpoint resumed with changed tokenizer, donor, source, mask settings or hardware must fail closed.
3. Summing microbatch means can silently change the capable-H objective when capability prevalence varies.
4. Validation generation safety and test assessment can become an undeclared hyperparameter search.
5. Evaluator condition IDs can silently reuse fixed-core masks/results when the learned mask is substituted.

## Interfaces and CLI

Consume exactly ticket 03's `build_pilot_manifest`, `validate_pilot_manifest`, `configure_candidate_gates`, `pilot_loss`, `export_binary_masks`, `PilotLoss`; ticket 03 owns eligibility and loss formulas. Do not invent a second implementation.

Expose `main(argv: list[str] | None = None) -> int` with Python-3.9-safe annotations and explicit modes:

- `--prepare --stage1-manifest PATH --data-dir PATH --honest-pool PATH --candidate-bindings PATH --manifest PATH`: cached-tokenizer CPU construction/validation only; immutable save with overwrite refusal.
- `--dry-run --manifest PATH --output-dir PATH --rho FLOAT --seed INT --epochs INT --validate-every INT --joint-pairs INT --accumulation INT`: validate frozen inputs and print exact row/update/cache/checkpoint/generation counts, sizes and upper token bounds, without loading weights. Require root-supplied numeric training budget, never an implicit four-run loop.
- `--train` with the same frozen arguments, cached model path/revision/dtype and root gate-record path: one rho per invocation. Require a root-authored freeze record naming validated baseline path, Stage 1 decision, selection/safety policy and measured budget; this is provenance, not a new user approval flow.
- `--evaluate --checkpoint PATH --evaluation-manifest PATH`: execute only immutable derived evaluation rows via the existing score/generate helpers; no fitting or checkpoint selection against test. Support explicit exact-fingerprint `--resume`; no repair/rebuild/resample on resume.

If a separate runner helper is created, export only `select_checkpoint(history: list[dict], baseline: dict) -> dict | None`, `make_evaluation_manifest(source_manifest: dict, mask_exports: dict, *, purpose: str, frozen_slice: list[str], provenance: dict) -> dict`, and persistence functions needed by the CLI. Root reviews any larger interface expansion. Keep this a small pilot; report if the implementation approaches 1,000 lines rather than silently building a framework.

## Task 1: Cache, optimizer and bounded train loop

- [ ] Write failing tests `test_dry_run_never_loads_weights_or_uses_network`, `test_reference_cache_is_readout_only_and_bound_to_validated_path`, `test_capability_is_train_only_frozen_and_not_a_row_filter`, `test_joint_pairs_share_draw_and_accumulation_preserves_stratum_denominators`, and `test_only_candidate_logits_enter_optimizer_and_base_stays_fixed`.
- [ ] Run focused tests for RED. Implement CLI modes, ticket 03 manifest consumption and offline cached model identity. Use one joint D/H forward per microbatch; gate draw broadcasts over both conditions. Frozen reference cache stores H readout logits and truthful labels/capability flags on CPU, transferring current rows only; no full-sequence/vocabulary GPU cache. Freeze train capability from full-vocabulary intact argmax==truth at designated unpadded readout, using the validated compute path. Report donor baseline validity separately; never filter pairs or donors by observed outputs. Globally absent/insufficient capable coverage stops fitting under root's frozen usability decision.
- [ ] Implement equal-budget AdamW updates with explicit candidate initialization from ticket 03, clipping and a single recorded schedule (reuse existing epoch cosine schedule only if its exact min lr is frozen). Accumulation weights D/H sums by their respective update-window row counts and capable KL by update-window capable count; apply the expected-count penalty once per optimizer update. A zero-capable microbatch is allowed; an empty global capable stratum is not. Log raw numerators/counts and deterministic counts; check finite loss/gradients and fail with a retained partial checkpoint, not automatic retry.
- [ ] Run tests to GREEN in both supported environments; use tiny random-model/stub fits to verify intended gates change and base weights do not. No production fitting at this step.

## Task 2: Exact persistence, validation selection and export

- [ ] Write failing tests `test_exact_resume_matches_uninterrupted_tiny_fit`, `test_resume_rejects_any_behavior_input_change`, `test_cache_rejects_changed_baseline_path_or_prompt`, `test_selection_requires_both_h_accuracy_gates_and_d_improvement`, and `test_selection_ties_use_size_then_earliest_without_test_access`.
- [ ] Run RED; implement atomic cache/checkpoint writes and exclusive output ownership. Fingerprint covers manifest/data/donor/candidate hashes, original source revision plus dirty-content hash, tokenizer/model snapshot file hashes/config/revision, dtype/device/GPU type/validated compute path, objective/optimizer/init/schedule/seed/batch/accumulation settings and evaluation policy. Save logits, eligibility, optimizer/scheduler, Python/NumPy/Torch/CPU/CUDA RNG states, epoch/update/batch position and fixed row order. Restore exact continuation without skipping/repeating an update; changed hardware/settings require a new run, never a mixed-fingerprint append. Save at complete update boundaries only; reject corrupt completed records, recovering only a clearly incomplete trailing write.
- [ ] Deterministic eval uses the true binary gate threshold. At fixed validation checkpoints report all 119 H rows and intact-capable subgroup separately: full-vocabulary accuracy, argmax D/H/other, truth probability, KL/nondegradation, plus D suppression and paired uncertainty. Admissible requires no observed net loss in all-H accuracy and capable-H accuracy versus frozen intact validation and reduced D surrogate. Select greatest validation suppression, then fewer removed heads, then earliest checkpoint; freeze any root-approved one-time numerical policy revision **before fitting**. Test rows cannot reach `select_checkpoint`. No admissible candidate returns an explicit failed frontier, not relaxed criteria or top-k masks.
- [ ] Export selected deterministic K/R using ticket 03, preserve zero removed MLPs and candidate subset; verify tiny-model training-forward/export equivalence under identical donors. Real-model export equivalence belongs to root's measured smoke under the validated numerical path/tolerance. Record all selection terms and the exact selected source checkpoint.
- [ ] Run GREEN in both environments; record exact resume equivalence and provenance refusal evidence for root review.

## Task 3: Fixed generation safety and fresh evaluation manifest

- [ ] Write failing tests `test_derived_manifest_preserves_old_source_and_binds_learned_mask`, `test_reference_closure_and_cost_include_donor_completions`, `test_generation_safety_slice_is_fixed_before_fit_and_never_test_selection`, `test_knockout_export_has_zero_mlps`, and `test_no_candidate_ends_without_automatic_retrain`.
- [ ] Run RED; implement a narrow adapter to `evaluation.selective_runner.score_row`, `generate_row`, `reference_stream`, `ResultStore`, `summarize`, `export_blind` as compatible. Reuse transformations, greedy/EOS/pad behavior and donor continuation handling; cap every generation at 96 new tokens. Where Stage 1 schema insists on fixed condition IDs, create/validate the derived schema in owned runner code; never mutate Stage 1 validation, monkeypatch condition tables, relabel a learned mask as `core`, or edit the old manifest. Learned conditions get stable IDs containing mask hash, provenance points to immutable parent manifest and checkpoint, and all new row/result hashes are fresh.
- [ ] Before fitting, root freezes a small validation cluster-ID safety slice, transformation/view/condition list, annotation rubric and rejection policy. Use a fixed maximum one readout-selected finalist per rho, assessed once on that slice; no repeated slice regeneration. Preserve rows and blinded annotations for deceptive assertion, truthful, coherent refusal/evasion, malformed/unrelated, empty and ambiguous; disclose EOS/cap/repetition separately. If safety rejects all candidates, stop; no automatic new grid. Final test is assessed only after validation selection/safety, never used to pick a checkpoint/rho or change policies.
- [ ] Bounded final conditions are intact, selected learned mask(s) including rho=0 comparator, frozen shared core, D−F and existing core-sized random, using identical split-appropriate nonself-H donors. A promising selected size may add exactly one declared layer/count-matched random comparator before final assessment; core-sized random is not a learned-size null. Derive final test rows from frozen Stage 1 sources/donors; retain exploratory/non-pristine-test disclosure. Report raw deceptive/n separately from pairwise preference, coherent refusal, quality and H utility; no broad capability/mechanistic claim from matched-H KL. Donor/reference generation and deduplicated donor scoring are included in dry-run cost and exact reference closure.
- [ ] Run GREEN in both environments and confirm changed learned mask/fingerprint refuses old result reuse.

## Task 4: Root-only resource wrapper and handoff

- [ ] Write failing shell/CLI tests for `test_wrapper_tolerates_bashrc_test_failure_but_requires_conda`, `test_wrapper_dry_run_is_cpu_only`, and `test_wrapper_has_no_array_retry_requeue_or_a100_training`. Exercise actual wrapper with stubs, including activation failure, rather than merely checking string presence.
- [ ] Implement one-GPU A40/H200 wrapper with offline flags, explicit short smoke default ≤30min, `--no-requeue`, guarded bashrc/conda mgnp activation, no arrays/retry/judges/network. Root supplies `sbatch --time` for each concrete reservation; training CLI is one frozen rho per invocation. Never print credentials/environment or encode blanket 20h permission. Wrapper can support CPU `--dry-run` without scheduler/model loading.
- [ ] Verify shell syntax, stubbed wrapper dry-run, focused pytest under `/sw/external/python/anaconda3/bin/python` and `/u/swong2/.conda/envs/mgnp/bin/python`, thread-pinned/offline. Include ticket 03 and existing selective tests. Root runs one final integrated suite after changes against documented base 7 / mgnp 8 failure-name baseline; no untouched-baseline rerun or package installs.
- [ ] Hand root API/commands, tests, source hashes, counts/cache bytes, conservative runtime arithmetic and unresolved gates. Root reviews and commits explicit files. **No training launches until Stage 1 behavioral validity is accepted and root measures paired forward/backward/cache/validation/export throughput.** Root costs the four equal runs against remaining cumulative ledger before launching them.

Proposed slots for root review only: ≤0.5h training/export smoke; four ≤1.5h rho runs; ≤1.5h second-seed repeat only for a useful validated/safe setting; ≤1.5h final evaluation, total ≤9.5h. Every slot includes actual reservations charged to the same 20h ledger; failed jobs/retries consume balance and need a revised concrete ledger decision. If measured throughput cannot fit, return a reduced costed batch to root; do not shrink data, change updates selectively, or silently launch. At most two jobs active/pending; root alone submits. No further user confirmation for routine authorized implementation.

## Comments

Ticket remains held on the root Stage 1 decision. CPU primitive preparation in ticket 03 can proceed independently. Neither successful unit tests nor a proposed ceiling supplies missing behavioral validity or spending authorization.

## Root prefit amendment (frozen before relevant outcomes)
Report18-prefit-gates.md supplies exact usability/safety rules and supersedes vague meaningful-capability wording: H readout truth>=60/119 independently train/validation plus both designation/position coverage; freeze16valclusters2perstratum seed0 beforeoutputs; intactgeneration headroom>=8Ddeceptive and>=8Htruthful; paired damage/benigntruth/newdeception vetoes; strictlylowerrawDdeception foradvancement, targetrefusalswelcome. Max160targetcompletions+actualdonorclosure<=16 beforeoptionalrepeat. All119 retained. This is an exploratoryengineeringfloor, notproof ofgenerality/safety.
Numerical baseline path is validated dual-stream self-donor all-open uncached; Stage1fixfaa4109, r2manifest7c0918edd8cfd877729d00ece65fb1c70ec9be64207c0e68930625a20e4157ce, report17-successor-lineage.json. Root will explicitly release CPU implementation after03independentreview andcorrectedsmoke. Actualoptimizer/productionlaunch stillheldonStage1behaviorandprefitbaselines plusmeasuredrootbudget. Baseline-onlycache/generation/calibration run must be a separateexplicitpreparationmode; it cannot claimgatesalreadymeasured or perform optimization beforethosegatesaremet.

Root release: ticket03 independentlyPASS(report19), committed76baea9; samepathfix cherry-picked10b6c2a, pilotHEAD10b6c2a. Correctedsmoke22994903 all8identitiesPASS(report20-smoke-gate.json). CPU-only04 released underreport18; no GPU/production launchdelegated.

Root/Astra numericalamendmentreport25 accepted: joint_pairs=1 only (jointD/H batch2, unpaddedpairlength) forreferencecache/train/deterministicval; accumulationforeffectivebatch. Cachegeometryfingerprinted. Existingcalibration addsfixedlengthrepresentatives A no_gradself/allopen,B no_gradactualdonor/allopen,C autogradSTEforcedopen/actualdonor; capturefullvocabdrift,labelprobs,argmax/capabilityflips,retentionfloor,finitecandidategrads/frozenbase. No optimizerstep orautomaticthresholdwidening; materialdriftblocksfit. See report25for exactgateinterpretation.
