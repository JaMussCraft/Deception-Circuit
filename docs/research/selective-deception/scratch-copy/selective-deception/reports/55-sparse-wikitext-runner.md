# Amendment-v2 runner implementation and root handoff

Task B, 2026-10-19. Owned changes are only `train_selective_mask.py`, `evaluation/selective_mask_runner.py`, `evaluation/selective_mask.py`, `scripts/selective_mask.sbatch`, and `tests/test_selective_amendment.py` in the new selective-wikitext worktree. No old worktree edits, git operations, GPU/model-weight access, submissions, APIs, installs or network were performed by this worker. Worker A owns the WikiText primitives unchanged.

The implementation retains explicit legacy report18-v1 paths and receipt gates. Amendment-v2 has separate preparation, receipt, baseline, calibration/profile, fit and own-arm selection branches. The original source manifest is reconstructed and hashed on validation, with the frozen103-head union retained even for all1024-head amendments. Every changed objective, candidate, schedule or WT identity changes the run fingerprint. Base-reference identity deliberately excludes arm/candidate settings while preserving original SDR, WT, model/tokenizer/runtime/source identities, allowing all-open references to be shared across the six runs. Hardware/software differences invalidate references.

`H`, `W`, `HW` use separately normalized T/H/W observations, the report52 coefficients, a window-level WT NLL hinge, expected removed counts, AdamW constant lr.03/wd0/clip1. Baseline capability is frozen; empty capability yields explicit zero KL and an absence report. No H capability/headroom veto applies to the amendment. The fixed seed0 SDR permutation wraps119 without tail dropping for4096 presentations across512 updates. WT uses one frozen seeded32-block cycle repeated16 times. One gate-noise realization is rebuilt as fresh differentiable graphs for every SDR/WT forward within an update; discarded legacy draws cannot alter subsequent updates differently across arms.

Per-block full-vocabulary FP32 CPU references are staged one at a time. Preparation creates train/validation references only; the test token manifest is frozen but no test reference or score is produced. All arms evaluate D/H/W at64-update intervals. Frontiers retain all dimensions, own-arm admissibility, failed-frontier examples, and the predeclared compact-result flag. Exact gate-only checkpoint/RNG/optimizer resume and binary export use existing reviewed primitives. No old generation safety16 is reused: amendment `--evaluate` stops with an explicit requirement for the root fresh-cluster assessment adapter. This is an evaluation-adapter limitation, not a training veto.

## CPU verification

Initial new contracts failed for missing APIs before implementation. Focused tests subsequently passed in both environments:59 tests in27.24s under Python3.9,59 in26.12s under mgnp Python3.12. These cover the11 new amendment contracts plus48 existing runner/loss contracts. Additional tiny CPU calibration/evidence tests were added afterward; final results will be appended below. `bash -n scripts/selective_mask.sbatch` and compilation of all three edited Python files passed.

The actual `bash scripts/selective_mask.sbatch --dry-run ...` wrapper activated mgnp and returned status0 without model loading. Its temporary current-protocol HW/union manifest hash is `087a3043929e8299fec3b02968824276e7fd04116b7695680bde0ed506d1a325`; this is a worker `/tmp` artifact, not a root-approved production manifest. Source hashes in early dry-run output were development snapshots; root must freeze actual final source hashes after review.

## Exact CLI

All commands below run from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/selective-wikitext`. Paths are shown literally to avoid worktree ambiguity. Root creates one manifest per frozen arm/candidate space, changing only those flags. Rho remains a runtime setting under the fixed grid.

```bash
python train_selective_mask.py --prepare --policy amendment-v2 \
  --source-manifest /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/selective-mask-pilot/outputs/selective-mask-pilot/manifest.json \
  --manifest /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-wikitext-v2/manifest-HW-union.json \
  --freeze-record /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-wikitext-v2/protocol.json \
  --wikitext-manifest /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-wikitext-v2/wikitext-manifest.json \
  --collateral-arm HW --candidate-space union --seed 0 --rho .01 --joint-pairs 1
```

`--freeze-record` at prepare time is the canonical scientific protocol JSON; the stored protocol hash is its canonical content hash, not its raw-file SHA256. Subsequent modes use a separate actual root receipt at that argument. A root receipt must never replace the canonical protocol file. The latest root protocol explicitly binds constant lr.03 and clip1; the temporary worker manifest was recreated after that clarification.

For dry-run use the same manifest/WT/arm/space/seed/rho/joint flags, replace `--prepare` with `--dry-run`, omit `--source-manifest`, and provide `--output-dir`. No receipt, model revision, data directory or WT cache is needed. Production defaults enforce512 updates/checkpoints64; `--max-updates` and `--checkpoint-every` are explicit identity fields but cannot silently shorten the frozen amendment budget.

For baseline/calibration/training use the same flags with `--baseline`, `--calibrate`, or `--train`, plus:

```text
--output-dir <new mode-specific directory>
--freeze-record <root receipt JSON for this manifest>
--data-dir <original frozen SDR data directory>
--model-path /work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
--model-revision 0e9e39f249a16976918f6564b8830bc894c89659
--wikitext-cache <shared writable CPU reference directory>
```

Calibration/training additionally require `--reference-cache <baseline output>/reference.pt`. `--resume` is explicit for existing outputs/references. Root can call the actual wrapper for these modes under a separately reserved A40/H200 allocation. There is no array, retry, optimizer hidden in baseline, or job launch in this handoff.

## Root receipt schema

Baseline minimum fields, with actual values filled by root:

```json
{
  "version": 2,
  "policy": "amendment-v2",
  "manifest_hash": "<derived amendment manifest hash>",
  "protocol_hash": "<canonical protocol content hash from manifest.amendment>",
  "wikitext_manifest_hash": "dce0f346dd0381d2ee44ef0b1b5d849afab29230ff8afc1766836f4d23d882bd",
  "baseline_path": "dual_stream_self_donor_all_gates_open_uncached",
  "root_decision": "<actual authorization/provenance>",
  "source_revision": "<root source revision>",
  "source_files_hash": "<runner._source_files canonical hash>",
  "model_revision": "0e9e39f249a16976918f6564b8830bc894c89659",
  "user_authorized_fit": true,
  "prior_behavior": {"stage1_behavior": "<factual previous outcome>", "generation_headroom": "<factual previous outcome>"}
}
```

Calibration adds measured `baseline_fingerprint`, `baseline_cache_sha256`, `wikitext_cache_fingerprint`, `wikitext_cache_inventory_hash`, obtained from the baseline report. No former behavioral passed labels are requested or asserted. Training additionally requires `training_settings` exactly matching the CLI fields `rho,seed,joint_pairs,collateral_arm,candidate_space,max_updates,checkpoint_every`, an `allowed_rhos` list containing the current rho, and:

```json
{
  "numerical_evidence": {
    "calibration_path": "<actual calibration.json path>",
    "calibration_sha256": "<actual raw file SHA256>",
    "source_files_hash": "<same frozen source hash>",
    "baseline_fingerprint": "<same measured baseline identity>",
    "wikitext_cache_fingerprint": "<same measured WT identity>",
    "root_review": "passed"
  },
  "measured_budget": {
    "passed": true,
    "profile_sha256": "<same raw calibration.json SHA256>",
    "root_cost_and_reservation": "<actual measured allocation decision>"
  }
}
```

The actual calibration/profile artifact hash and report contents are verified before model loading; source, references, nonzero T-gradient signal and exact export equivalence must match. These are schema examples, not issued receipts. Baseline source identity excludes evolving receipt contents to avoid a circular dependency.

## Smoke and cost interpretation

`--calibrate --profile-updates 3` performs the report25 self/no-grad → nonself/no-grad → forced-open gradient ladder on every SDR structural length representative and two WT blocks, for union103 and all1024 eligibility. Forced-open backward retains the real gate graph, checks finite gradients/isolation, and logs measured distributional floors. The existing0.02 threshold applies only to semantic D/H label logits; full-vocabulary drift remains diagnostic. WT floors require root review and receive no invented full-vocabulary0.02 cutoff. The whole119-pair validation no-op is checked, with16 WT validation blocks measured alongside it.

Profiling measures each of H/W/HW under both candidate spaces: one disposable warmup plus3 measured eight-pair updates, of which the first additionally measures exact component gradient norms; its instrumentation overhead is excluded from pricing. The remaining two actual update times, full validation time, checkpoint IO, model startup/hash/load time, peak CUDA allocation, reference preparation/storage, raw terms and unit coefficients are reported. Each profile deliberately probes a nonempty deterministic binary export and verifies live-forward identity. All smoke parameter/gate/RNG states are discarded; production optimizer step count is0. Allowed smoke range is3..8 measured updates, not an unbounded calibration fit.

One run has512 updates,4096 joint pair forwards,512 WT forwards for W/HW (zero H),8 validations ×119 pair/16 WT forwards,521 checkpoint writes (initial +512latest +8frontier), and at most9 checkpoint files. Baseline shared work is238 paired readouts plus48 WT blocks; no new generation/test forwards. Startup/cache/validation/export costs must be budgeted separately from gradient steps. The per-run estimate includes measured startup +512 warmed update means +8 full validations +521 measured checkpoint writes. It is a measured extrapolation, not proof of an hour allocation or reuse of previous generation timing. Root prices two rhos per arm from the corresponding candidate-space rows before reserving production.

## Final review and verification

Independent Task B review found one substantive issue: the compact-useful-result flag considered only the selected best-D finalist. This was corrected to scan the complete frontier, preserving a useful earlier1..16-head checkpoint even if a later larger mask wins finalist selection. A RED regression reproduced the missing full-frontier predicate before the fix. Reviewer independently checked full eight-pair objective/gradient agreement for H/W/HW and found no remaining source blocker.

Final focused suite after this correction: **62 passed under Python3.9 in25.95s;62 passed under Python3.12 in24.74s**. Additional contracts exercise all six disposable calibration profiles with tiny CPU geometry, measured-artifact SHA rejection, and the full-frontier compact-result rule. The exact-resume test was additionally strengthened to compare the entire latest checkpoint digest (optimizer, cursor, gates and RNG), beyond selected-mask identity.

Frozen production file SHA256:

- `train_selective_mask.py`: `db85a17cff0dff4806db74af59c6eafdda595774194e2ac41515297e68ac68ca`
- `evaluation/selective_mask_runner.py`: `e2deca68a89b71482fe7b4425ab0f65ba8cd560e4291f45132033a538d666c4d`
- `evaluation/selective_mask.py`: `952819f1a7ebbf2c5071484244f049cf17a255a15db6a84303bea6739dfad34c`
- `scripts/selective_mask.sbatch`: `3ac4514212c4a576fea5e50b71b2b8f99a1457f49c98c070753230abf6dd00ba`
- final `tests/test_selective_amendment.py`: `8d368cea850558e4d93bd83c183b8d428ac727fc3551e9c83e9762409d080f71`

No further source changes are planned. Root owns the integrated whole-suite baseline comparison, explicit-file commit, canonical manifests, actual receipts, measured resource review, and job launch. Real CUDA numerical accuracy, memory feasibility and throughput are intentionally unmeasured by this worker.
