# Ticket 04 CPU implementation handoff

Source re-frozen after the one scoped report28 provenance correction; root owns final integrated verification and commit. No production model execution, pretrained-weight reading, GPU use, job submission, API call, notebook execution, package installation, git operation or subagent delegation was performed by this worker. Root retains review, fixes/integration, scientific decisions, receipts, ledger and launches. Default bwrap failed before command execution; narrowly scoped escalated CPU reads/tests were used.

Owned files only: `train_selective_mask.py` (42 lines), `evaluation/selective_mask_runner.py` (808), `tests/test_selective_mask_runner.py` (442), `scripts/selective_mask.sbatch` (26), and this report. Production Python is 850 lines; no new framework or edits to Stage 1/helper sources.

## Behavior and interfaces

`main(argv=None)` has mutually exclusive `--prepare`, `--dry-run`, `--baseline`, `--calibrate`, `--train`, `--evaluate`. Every non-prepare invocation specifies exactly one rho, seed, epochs, validation cadence, joint-pair count and accumulation. Exactly `joint_pairs=1` is supported pending separate geometry proof. Constant lr .03, AdamW weight_decay=0, clip norm 1, beta_KL=beta_label=1 and expected initial removal count one are recorded. Four allowed rhos remain 0/.001/.01/.1; there is no loop over rhos.

The runner directly consumes ticket 03 manifest, gate, loss and export functions. D/H share one unpadded batch-two forward and one nonself clean-H donor. Baselines use the same pair constructor with self donors, all-open gates, no cache and no gradients. Validation uses matched no-grad pair geometry; stochastic optimization leaves the model in training mode with dropout disabled by the existing loader. Accumulation weights D/H terms by complete-window pair counts, KL by complete-window capable counts; the expected-removal penalty is applied once per update. All rows remain present. Capability is frozen only as the training KL stratum and separately reported for validation.

Atomic tensor persistence includes content digests, exact gate/eligibility state, tiny optimizer, Python/NumPy/Torch CPU/CUDA RNG, fixed order, epoch/window/update position, loss numerators/counts and validation history. It stores at complete update boundaries, including the initial boundary. A nonfinite failure retains the last complete checkpoint and a failure record; it never retries. Resume requires an exact source/model/tokenizer/data/donor/hardware/settings/policy fingerprint. Incomplete `.tmp` writes are ignored; corrupt completed tensors fail closed. Deterministic selection uses both H accuracy gates, reduced D surrogate, positive actual removal, then smaller removal count and earliest update. No admissible candidate produces a failed frontier.

**Root-found correction:** the draft checkpoint substring filter `"gate" in name` also included SwiGLU `gate_proj` base weights. The earlier worker message claiming gate-only persistence was incorrect. The frozen source enumerates tensors owned by actual `HardConcreteGate` modules for both save and restore. The new regression first failed, then passed, explicitly excludes real tiny-Llama `gate_proj` keys and bounds checkpoint bytes. No production checkpoint was created under the draft.

Selected export yields a fresh validation-safety manifest, not an automatic generation run. Learned condition/row identities include mask/provenance hashes; donor reference IDs are also newly derived while preserving semantic donors. Fixed Stage 1 conditions are never monkeypatched or relabeled as learned. Generation delegates to existing score/generate/reference/ResultStore/summary/blinding machinery with the 96-token cap. One shared reference store, independently fingerprinted by intact execution identity plus exact parent/prompt/decode, supplies the same 16 validation donor completions and scores to each rho. Target results remain separately fingerprinted and are never reused across learned masks. A real ResultStore/stub-generation regression demonstrates one donor completion/score and two target completions across two rho manifests.

Calibration is separate and cannot create an optimizer or take a step. It chooses the first structural representative in each of at most five length groups and runs repeated no-grad self/all-open, no-grad nonself/all-open, and grad-enabled nonself/forced-open STE paths. Temporary hooks force eligible gate outputs to one while preserving the sampler gradient graph; hooks, RNG, mode and gradients are restored. It reports full-vocabulary drift, two-label logits/probability drift, argmax/capability flips, loss floors, finite/isolation checks and candidate gradient signal. Only label-logit absolute tolerance .02, unchanged argmax/capability and finite/isolated gradients enter its numerical gate. Full-vocabulary max and KL/NLL/target floors are diagnostics without a new cutoff. All 119 validation no-op rows are also measured. Root must review the floors and author the numerical-calibration decision before fitting.

Blinded annotation and scientific classification remain root tasks. The runner generates/blinds outputs and enforces root's report18 receipt; it does not infer deception or automatically mark headroom/safety passed. Final-test execution requires an exact root-bound final manifest and passed validation-safety decision. A separately pinned selected rho=0 checkpoint can accompany the primary learned mask. An optional learned-size random null is not automatically constructed.

## CPU evidence

Pre-review focused command (before the narrow loader-hash correction), run from the pilot worktree with OMP/MKL/OpenBLAS threads one and HF/Transformers offline:

```bash
<python> -m pytest tests/test_selective_mask_runner.py tests/test_selective_mask.py tests/test_selective_diagnostics.py tests/test_selective_runner.py -q -p no:cacheprovider
```

- Base `/sw/external/python/anaconda3/bin/python`: **130 passed, 3 existing warnings in 27.14s**, `/tmp/pilot04-final-base4.log`.
- mgnp `/u/swong2/.conda/envs/mgnp/bin/python`: **130 passed in 22.89s**, `/tmp/pilot04-final-mgnp4.log`.
- `bash -n scripts/selective_mask.sbatch`: exit 0.
- Shell tests execute the actual wrapper with stubs: failing final bashrc test is tolerated, conda activation failure is fatal, dry-run does not require CUDA, no array/retry/requeue/A100 training configuration exists.
- A separate actual-wrapper execution used exported `source`/`conda` functions (source returned 1, activation returned 0) and the real Python CLI/data manifest with `--dry-run`. Exit 0; exact plan `/tmp/pilot04-wrapper-dry.json`.
- Real tiny training interruption/resume exercised four actual optimization updates and matched uninterrupted gate tensors, raw loss log and Torch RNG exactly.
- No untouched full baseline or full repository suite was run; root owns its final integrated suite after independent review.

RED artifacts include missing-runner `/tmp/pilot04-red.log`, joint geometry `/tmp/pilot04-geometry-red.log`, donor-template `/tmp/pilot04-adapter-red.log`, forced-open calibration `/tmp/pilot04-calibration-red.log`, persisted corruption `/tmp/pilot04-integrity-red.log`, shared-reference `/tmp/pilot04-reference-red.log`, fresh references `/tmp/pilot04-fresh-reference-red.log`, and gate ownership `/tmp/pilot04-gate-only-red.log`. Intermediate logs are not final verification. The first actual prepare also failed because the existing phrase-pool JSON wraps entries under `instructions`; the CLI reader was corrected and both final preparations succeeded.

## Actual r2 construction and prepare command

Both supported interpreters successfully ran the actual `--prepare` command using cached tokenizer only, producing identical 14,065,994-byte files `/tmp/pilot04-manifest-0.json` and `/tmp/pilot04-manifest-1.json`. Logs `/tmp/pilot04-prepare-{0,1}.log`. The helper and runner enforce **119 train/119 validation, 103 candidates and all eight report13 audit hashes**.

- Prepared manifest: `2ec18aa1452d1f00a6f0eef2f727190040e886723c2ee613e5581e554f9eebe3`.
- Approved r2 parent: `7c0918edd8cfd877729d00ece65fb1c70ec9be64207c0e68930625a20e4157ce`.
- Original r1: `29da71bd7cef5f03bec931e5a4231cb93b3bfb026ce3b00f1ea3367a6aab95a0`.
- Candidate hash: `6c5943656abc881d8ff949f776a3fa9dc11e7161254a2c16738c7306b8624420`.

Bindings file `/tmp/pilot04-bindings.json` is JSON containing `bindings: DEFAULT_BINDINGS` imported from `evaluation.selective_runner`, plus `source_metadata.stage1_lineage` mapped from root's report17: `original_manifest_hash=parent_manifest_hash`, `approved_manifest_hash=successor_manifest_hash`, `root_decision=decision`, `inputs_unchanged_from_r1=all_other_manifest_content_equal`. No approval was invented. Those bindings are the existing absolute D/H/F/m artifacts; the whole immutable r2 is retokenized by the helper exposure audit.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
/sw/external/python/anaconda3/bin/python train_selective_mask.py --prepare \
  --stage1-manifest /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/selective-deception/outputs/selective-sdr-stage1-r2/manifest.json \
  --data-dir /projects/beto/swong2/Alignment/Deception-Circuit/data/datasets/sdr \
  --honest-pool /projects/beto/swong2/Alignment/Deception-Circuit/dataset/deception_pools/matched_honest_sdr.json \
  --candidate-bindings /tmp/pilot04-bindings.json \
  --model-path /work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659 \
  --manifest /tmp/pilot04-manifest-0.json
```

The manifest already exists; rerunning that exact output path must refuse overwrite. Root should archive/reuse it or choose a new path rather than overwrite.

## Root receipt schema and command handoff

Root authors a version-1 JSON receipt. Baseline preparation accepts a planned receipt; baseline gates do not have to pass before producing them. Minimum planned fields:

```json
{
  "version": 1,
  "manifest_hash": "2ec18aa1452d1f00a6f0eef2f727190040e886723c2ee613e5581e554f9eebe3",
  "baseline_path": "dual_stream_self_donor_all_gates_open_uncached",
  "root_decision": "ROOT FILLS actual scope and receipt decision",
  "source_revision": "ROOT FILLS final reviewed pilot commit",
  "source_files_hash": "ROOT RECOMPUTES after review fixes",
  "model_revision": "0e9e39f249a16976918f6564b8830bc894c89659",
  "policy": "report18-v1",
  "donor_reference_dir": "ROOT FILLS absolute shared validation reference directory",
  "safety_cluster_ids": ["ROOT COPIES all16 IDs from the frozen dry-run plan"]
}
```

Baseline mode additionally needs the ordinary numeric CLI budget arguments, `--freeze-record`, `--data-dir`, `--model-revision`, cached `--model-path`, and `--output-dir`. It creates `reference.pt`, `baseline.json`, intact blinded generations and the exact shared donor closure. It cannot optimize.

Calibration/train/evaluate receipts additionally require `stage1_behavior`, `capability`, `generation_headroom` all equal `passed`; `baseline_fingerprint`, `baseline_cache_sha256`, `baseline_generation_fingerprint` copied from actual measured baseline artifacts; `training_settings` exactly matching `seed`, `epochs`, `validate_every`, `joint_pairs`, `accumulation`; and `allowed_rhos` containing the declared setting(s). Train/evaluate also require `measured_budget.passed=true`; train requires `numerical_calibration="passed"`. These are root attestations, not a worker-generated scientific verdict. Root should retain the full measured budget/ledger details in the receipt. Baseline cache identity excludes subsequent receipt-state/optimizer/budget changes but still binds actual compute identity and data.

`--calibrate` takes a passed-baseline receipt plus `--reference-cache BASELINE/reference.pt`; `--train` takes the final passed/measured receipt and same reference cache. Run one rho per call, with the identical frozen numeric settings. Training emits `frontier.json`; a selected candidate also emits `selected-mask.json` and `safety-manifest.json`. `--evaluate --checkpoint SELECTED_VALIDATION_PT --evaluation-manifest safety-manifest.json` generates that one finalist on the fixed 32 rows. Use explicit `--resume` only for exact continuation; never repoint an old output directory.

Final evaluation adds `final_assessment="passed_validation_safety"` and exact `final_evaluation_manifest_hash`. A separate rho=0 export must be pinned by `evaluation_checkpoints[export_hash]` with `checkpoint` and its original run `fingerprint`. These final-assessment fields are intentionally excluded from the frozen training identity; other identity/settings changes refuse checkpoint reuse. Final manifests come from `make_evaluation_manifest` and root's frozen Stage 1 source slice; all annotations/test conclusions remain root decisions.

Example actual CPU dry-run budget (an arithmetic example, not a training release): `--rho 0 --seed 0 --epochs 2 --validate-every 1 --joint-pairs 1 --accumulation 8`, using the above prepared manifest and cached model path. This prints 119 micros/epoch, **30 updates, 238 paired train forwards, two validation checkpoints/238 validation pair forwards, 238 baseline pair forwards, 32 targets plus 16 shared references, 4,608 maximum generated tokens**. The actual wrapper command was this CLI argument list passed to `bash scripts/selective_mask.sbatch` with mocked environment activation; no scheduler was invoked.

## Resource arithmetic and frozen hashes

CPU reference logits are 238 x 128256 x 4 = **122,099,712 bytes (116.44 MiB)** plus small flags/metadata. Only current H rows transfer to GPU. Gate-only tiny checkpoint measured **17,666 bytes**, of which **64 bytes** were gate tensors; no `gate_proj` or other base weights were present. For the real head-only geometry, head tensors are 1,024 fp32 logits, 1,024 bool eligibility entries and 96 scalar gate buffers: 5,504 raw bytes before optimizer/RNG/serialization/history. Candidate-containing physical tensors have at most 1,024 entries; AdamW moments add at most 8,192 raw bytes plus scalar steps. Validation history/loss logs dominate large-budget checkpoint size; dry-run bounds retained files at validation checkpoints plus latest/failure, at most 102 for the 100-epoch ceiling. No full base-model checkpoint is saved. Snapshot SHA256 reads all original local snapshot files once per real invocation, never per update; dry-run reads no weights.

For E epochs and V validation epochs, training cost is `119*E` measured paired forward/backward calls, `119*V` measured deterministic validation pair calls, checkpoint overhead and one export. Baseline preparation adds 238 paired readout calls, 16 deduplicated donor score calls and at most 48 completions. Four finalist safety evaluations add at most 128 target completions; all five target conditions total **160**, with exactly one frozen shared closure of at most **16** donor completions: **176/16,896 token cap** before an optional repeat. Each rho's target ResultStore can contain copied reference records, but those are explicitly linked to the one shared reference fingerprint and incur no extra generation. No seconds/GPU-hour guarantee can be supplied without the held real calibration. Root must measure, cost four equal runs against the remaining ledger, and reserve each concrete walltime. The wrapper defaults to one A40 GPU and 20 minutes/no-requeue; root may choose H200 and must pass explicit Slurm time. No A100 backward, arrays, automatic retries or launches are supplied.

Frozen file SHA256:

- CLI `eb4b3d962bd93f62bd26f8f506a65a293923f36322bad827ad506b09dea256bd`.
- Runner `74d8d2007d5ecedab8f83cbaee65c9e113c6dd2c69108003e7a351400a4161fe`.
- Tests `ec04145ca5f1cbe043984adcb67ca7093164caa61436b783807b72bf5b303d3e`.
- Wrapper `b9e0cc85b5df5bd5a1795fd318b9f54cd45f34c686aee81c731631562f94fc5d`.
- Aggregate current `_source_files` hash `f7358da8a15da2adabfd3962e74f9c925d6701219326572dd4740a7c131e139c`.

**Report28 scoped correction completed:** `_source_files` now explicitly includes root `evaluate_selective_deception.py`, which supplies the runtime loader and cached snapshot helper. `test_loader_content_changes_source_identity_and_refuses_stale_receipt` changes real loader content in a temporary source tree, verifies its digest contributes to source identity, exercises the normal `_identity` path rejecting the unchanged receipt, and confirms an updated receipt produces a different run identity. Only cached-snapshot/circuit/hardware boundaries are stubbed; neither the fingerprint implementation nor receipt comparison is mocked. Stage 1 sources were never edited.

The regression first failed for the omitted digest (`/tmp/pilot04-loader-red.log`), then the complete runner test file passed under both interpreters:

- Base: **35 passed, 3 existing warnings in 15.88s**, `/tmp/pilot04-loader-final-base.log`.
- mgnp: **35 passed in 19.73s**, `/tmp/pilot04-loader-final-mgnp.log`.
- Command: same offline/thread-pinned interpreter invocation with `-m pytest tests/test_selective_mask_runner.py -q -p no:cacheprovider`.
- Refreshed actual-wrapper CPU dry-run: exit 0, `/tmp/pilot04-wrapper-dry-fixed.json`; same real manifest/numeric arguments and source/conda stubs documented above, with output directory `/tmp/pilot04-wrapper-dry-fixed`. Shell syntax also passed.
- Current hash summary: `/tmp/pilot04-loader-fix-summary.json`; root should archive these new small artifacts alongside the earlier `reports/21-artifacts` evidence.

No other source enhancement was made in this fix pass. Root owns the final integrated suites and commit. Production remains held on scientific/control and measured-resource gates; passing the provenance regression does not release fitting.
