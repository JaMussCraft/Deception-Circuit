# A2 Twin Training Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Workers do not run git; the orchestrator reviews and commits explicit files.

**Goal:** Build private same-item twin training data and a timed training wrapper, then measure one pilot before considering fleet reservations.

**Architecture:** Materialize ordinary task datasets in isolated D/I roots, retaining clean recipient labels and replacing only the reference prompt. Reuse the existing training objective and registry. A separate wrapper freezes configuration, measures total process time, and gates the 18-mask projected reservation.

**Tech Stack:** Python 3.9-compatible modules, existing Arrow dataset helpers/tokenizer, pytest, existing train.py and Slurm wrappers.

**Spec:** `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/START.md` A2; reconnaissance `reports/03-twin-training-recon-handback.md`; lead decisions in this task.

## Global Constraints

- Worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`; source D/H unchanged; no global Task/condition registry changes.
- Heads plus MLP blocks, node sparsity 0.3, 500 epochs, seeds 42/1/123, explicit training hinge margin 0.7, identical settings for D/I; extra gates and edge pruning disabled.
- One clean orientation per source instance; D/I share identical matched ids within each split; train/validation/test remain disjoint.
- Actual I materialization waits for A1 user-turn I and its aligned neutral-request twin. Timing-only D preparation is independently implementable now.
- Full 18-mask projected reserved cost, including pilots, must be at most 60 GPU-hours; one heads-plus-MLP mask above 6 GPU-hours triggers heads-only fallback. No fleet reservation before a measured pilot.
- No notebooks; no GPU on login nodes; training uses A40/H100/H200. Check frozen-set registry before scoring. No EVAL 5. No worker git; `DC_RUN_MANIFEST_GIT=0`, with orchestrator-provided commit provenance.

## Review Focus

- Duplicate ids and cross-split overlap must fail, including ids dropped by later matching (Task 1).
- Tokenizer truncation must never hide unequal masks or an overlength prompt (Task 1).
- H.corrupt or H labels must never replace the same-item H.clean reference or recipient labels (Task 1).
- D-only provisional artifacts must never satisfy the fleet-ready gate (Tasks 1 and 3).
- Missing timing provenance, different hardware/configuration, or omitted pilot costs must prevent reservation approval (Tasks 2 and 3).

### Task 1: Offline materializer

**Files:** Create `dataset/build_twin_training.py`; test `tests/test_twin_training.py`. Reuse `deception_common.load_or_generate_deception_data`, `DeceptionDatasetLlama`, `matched_honest.assert_clause_aligned_pair`, and `build_deception_dataset.save_splits`.

**Interfaces:** `validate_sources(recipient: dict, neutral: dict, *, tokenizer, max_length: int) -> dict` returns split-to-id maps and validation summary. `materialize(root_d: str, root_h: str, *, root_i: str | None, root_i_neutral: str | None, output_root: str, tasks: list, cohort: str, tokenizer, max_length: int) -> dict` returns the build manifest. Use `Optional[str]` annotations for Python 3.9 compatibility. Public CLI:

```
python -m dataset.build_twin_training --d-root data/datasets --h-root data/datasets --cohort timing-d-only --output-root outputs/_build_specificity_ladder/a2/timing --max-seq-length 120
python -m dataset.build_twin_training --d-root data/datasets --h-root data/datasets --i-root PATH --i-neutral-root PATH --cohort matched --output-root outputs/_build_specificity_ladder/a2/matched --max-seq-length N
```

Root D resolves `<task>`; H resolves `<task>_honest`. A1 I and neutral roots must expose `<task>` directories; accept an explicit per-task input-path mapping JSON if A1 uses suffix directories, without guessing filenames. Default tasks: far_v2/sdr_v2/ser_v2. All modes require train/validation/test. Add `--commit` for the full orchestrator-supplied source commit, and `--validate-only`, which writes nothing. Refuse existing output roots. `timing-d-only` forbids peer inputs and writes `fleet_ready:false`; `matched` requires both peer roots.

- [ ] Write failing tests: duplicate ids, cross-split ids even among discarded rows, missing twin ids, mismatched items/question/designation, wrong condition/twin metadata, donor H.corrupt substitution, unequal lengths/masks, changed tokens outside replacement span, multiple clause occurrences, and overlength prompts are rejected. Source fixtures remain byte-identical after building.
- [ ] Test valid output: D `clean_prompt` and target/distractor unchanged; `corrupt_prompt=H.clean_prompt`; I similarly pairs I.clean with I-neutral.clean. Store original designation-swap prompts under source-prefixed fields. Preserve source `instance_id`, pressure id, item metadata, and `orientation:'clean'`; record `corruption_kind:'neutral_twin_same_item'`, `recipient_condition`, and donor identity. Reject non-single-token answers rather than silently dropping them.
- [ ] Test matched cohorts: for each split take D∩H∩I∩I-neutral ids, preserve deterministic sorted order, then write identical D/I id lists. Fail on an empty split. Preserve every matched row; training count flags later explicitly select equal deterministic prefixes if needed. Report original/matched counts, attrition by source and strata, and actual selected ids. No replacement sampling or fresh ids in this builder.
- [ ] Implement output `<output_root>/{D,I}/<task>/{train,validation,test,dataset_config.json}` plus `<output_root>/build_manifest.json`. D-only writes D only. Each config records recipient condition despite the legacy CLI directory selector `deceptive`; record source paths/content hashes, exact split ids/order, tokenizer/model identity, replacement spans, max length, source thresholds, source build hashes, and `fleet_ready`. D/I neutral checks use their recorded honest thresholds, not an assumed 0.7. Do not run behavioral filters or infer margins from stale columns; label old margins as source values. Manifest names the exact A1 control/threshold and a caller-supplied full commit id; reject missing required provenance for matched output.
- [ ] Run focused CPU tests on both required interpreters with `-p no:cacheprovider`; fixtures use a deterministic fake tokenizer plus an optional locally cached real-tokenizer alignment check. No model load. Orchestrator reviews and commits explicit files.

### Task 2: Frozen training plan and timed wrapper

**Files:** Create `scripts/twin_training.py`, `scripts/jobs/specificity_ladder_a2.json`, and `tests/test_twin_training_wrapper.py`.

**Interfaces:** `build_command(config: dict, manifest: dict, *, task: str, condition: str, seed: int, timing_epochs: Optional[int]) -> list`; `run_timed(command: list, *, receipt_path: str, provenance: dict) -> dict`. Wrapper CLI `--stage dry-run|run|project`, `--config PATH`, `--build-manifest PATH`, and for dry-run/run: `--task TASK`, `--condition D|I`, `--seed 42|1|123`, `--receipt PATH`, optional `--timing-epochs E`. Dry-run is default and prints command/receipt plan without creating training artifacts, loading a model, or submitting anything. Run is invoked inside an approved allocation, never submits jobs itself. Project arguments are defined in Task 3.

- [ ] Test exact argv: model llama-8b-instruct, private data root D/I, legacy `--deception-condition deceptive`, `--node-lambda-sparsity 0.3 --node-epochs 500 --lr 0.03 --batch-size 7 --faithfulness-weight 1 --deception-margin-loss 0.7`, explicit split counts from matched plan and common max length from manifest. Include `--no-edge-pruning --prune-attention-heads --prune-mlp-blocks --no-prune-attention-neurons --no-prune-attention-blocks --no-prune-mlp-hidden --no-prune-mlp-output --no-prune-full-layers --no-prune-embedding`; prohibit runtime filtering. Explicit unique output directories encode task/condition/seed/granularity/cohort hash. Seeds differ only by seed. Freeze gate init 0.5 and warmup1000 via asserting existing resolved defaults.
- [ ] Implement config with those values, seeds `[42,1,123]`, tasks and both conditions. Set train/validation/test counts only after matching: equal across each D/I task, capped at 200/200/1000 with deterministic id prefixes; record selected ids before launch and require nonzero counts. If under 200 training rows, mark it prominently for lead review before fleet launch; do not silently compare unequal training effort. Record metadata versus legacy directory selector distinctly in the receipt.
- [ ] Test timing-only D with `--timing-epochs 20` is allowed on provisional D data and records `purpose:'timing-only'`, actual epochs20, and planned epochs500; it cannot count as a scientific seed or satisfy fleet readiness. Matched I runs reject absent A1 inputs. A production run rejects `fleet_ready:false`. Timing-only fewer epochs changes the cosine horizon; never promote that mask to a full scientific seed.
- [ ] Measure monotonic total wall time from immediately before subprocess launch through exit and final artifact checks, including model load, cache, validation, training, final evaluation, and writes. Record subprocess exit code, allocation/GPU count, cluster/GPU, peak memory if reported, task/condition/seed, argv/env, resolved-config/build/source hashes, commit, split counts, and result paths. Failed/incomplete runs produce failed receipts and no usable projection. Preserve complete stdout/stderr log. Require existing `config.json`, `active_nodes.json`, results/history and manifest on success; inject orchestrator commit provenance when native git collection is disabled. Parse the existing printed pruning duration separately; do not mistake it for allocation time.
- [ ] Test with fake subprocess execution, success/failure/missing artifacts, stale output, config mismatch, and a monotonic clock. Run both CPU suites; wrapper `--stage dry-run` must produce no model/GPU/API/git/submission calls. Orchestrator reviews and commits explicit files.

### Task 3: Projection gate and pilot handoff

**Files:** Create `scripts/twin_training_projection.py` and `tests/test_twin_training_projection.py`; keep projection independent of the execution wrapper. Its CLI is `python -m scripts.twin_training_projection`, with the same project-stage arguments below.

**Interfaces:** `project_reserved(receipts: list, plan: dict, *, pilot_reserved_gpu_hours: float, buffer_fraction: float=0.20) -> dict`. CLI `--receipts PATH... --config PATH --build-manifest PATH --pilot-reserved-gpu-hours H`; output a JSON recommendation, never submit. Ledger remains tool-owned.

- [ ] Test total process 1200 s, printed pruning 600 s, pilot 20 epochs: full 500-epoch estimate is `(1200-600)+600*500/20=15600` seconds, before the 20% buffer. Reject missing/nonpositive durations or a pruning duration exceeding total. This conservative extrapolation includes initialization validation repeatedly; report that limitation. Record actual reserved allocation hours separately from process time, and count pilots including failures against the phase projection.
- [ ] Extrapolate only comparable model/GPU, batch, padded length, sample count, and coarse gates. Prefer pilot at full planned counts and longest known length, including at least one periodic validation event; do not scale a tiny dataset pilot linearly to full memory. D-only receipt yields a provisional estimate only; final fleet gate requires matched A1 D/I metadata plus pilot shape coverage or a lead-recorded conservative bound for every cell. A changed length/hardware/config invalidates projection coverage.
- [ ] Produce per-cell full-run estimate, buffered reservation rounded upward to whole minutes, complete18-mask total plus already reserved pilot costs, coverage gaps, `single_mask_over_6h`, `within_60h`, and `fleet_reservation_allowed`. Evaluate the6h trigger on projected full allocation time before reservation buffer, and report buffered time too. `fleet_reservation_allowed` requires complete coverage, matched data, all18 planned cells, total<=60h, and no6h heads+MLP trigger. A >6h mask directs a separately measured heads-only pilot; never auto-launch fallback or bypass the phase cap. Heads-only changes only `--no-prune-mlp-blocks` and remains a distinct plan/receipt type.
- [ ] Test 18×6h exceeds60h despite each mask meeting the single-mask bound; missing seed/cell, NaN times, missing pilot cost, D-only data, and foreign hardware receipts block; an exactly60h complete plan passes. Test heads-only requires its own measured timing and complete budget projection.
- [ ] Run CPU suites on both interpreters, read dry-run argv/config, and hand off one conservative pilot reservation proposal to the orchestrator. The orchestrator measures the pilot and rechecks live usage/phase ledger before any fleet reservation. No pilot or fleet execution is authorized by this plan-writing task.

Verification commands for each owning test file:

```
OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training.py tests/test_twin_training_wrapper.py -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training.py tests/test_twin_training_wrapper.py -p no:cacheprovider
```

Expected: focused tests pass in both environments; compare unexpected failures by name to the documented baseline. Broader tests only if shared behavior changes. A2 scientific gates (difference-set Jaccard>=0.5, A1 specificity rule, or >=90% D-head inclusion in I every seed) remain later analysis after full training, not claims from this preparation plan.

## Wrapper review ruling

The training hinge margin is explicitly 0.7 for both D and I. Dataset screening thresholds remain their historical 0.7 or 0.5 and must not implicitly select different training objectives. Prelaunch selected-ID checks must inspect actual Arrow row order/counts and available prompt/label provenance, not only configuration metadata. This is a stale-input check, not a request to repeat tokenizer or behavioral filtering.

## Exact matched-cohort ruling before training

The lead accepts all matched survivors in the first primary-margin build: FAR train/validation/test 177/177/891, SDR 187/187/952, SER 168/167/835. D and I use identical ordered IDs within each task and split, with no neutral-baseline competence filter. The source training pools have 200 rows per task; attrition follows the pre-registered inversion margin rather than training outcomes. This implements the existing smaller-cohort review requirement and changes no scientific threshold.

The machine-readable ruling is `a2-cohort-ruling.json`; its build hash, selected-ID digest and complete count map bind permission to this exact cohort. Projection must still hold below 200 without a valid matching ruling. A malformed, foreign or stale ruling must fail closed. A ruling clears only the cohort-size review flag, never receipt validity, six-hour fallback, full timing coverage or the sixty-hour phase cap. The standalone projection and wrapper project stage must accept the same explicit ruling path. Keep under-200 status visible and record the ruling digest in recommendations.

Unequal task counts limit cross-task comparisons; within-task D/I effort remains matched. No training outcomes existed when this decision was recorded. All eighteen masks and independent timing coverage remain planned.
