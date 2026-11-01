# Independent benign recoding review

2026-10-19. **PASS after scoped correction and independent re-verification. No unresolved blockers.** This is a bounded review of `analysis/benign_recode.py`, its tests and wrapper against the frozen benign protocol/rubric, report 53 and report 52 section 1. No existing experiment source was edited by this reviewer. No GPU inference, model weights, paid API, network, job submission, git operation or nested agent was used. Root retains launch and annotation responsibility; a PASS does not replace the runtime identity barrier or the blinded baseline gate.

## Final correction and verification

The original P1 below is **resolved**. `baseline_records` now requires keyword `expected_identity` and compares the full provenance object exactly before accepting self-consistent hashes. Stage B derives the expected identity from the same verified current/prior runtime, source, initialization, policy and prior fingerprint used by stage A, changes only phase to `baseline`, and checks it before adding intervention gate provenance. Wrong phase, GPU and source now have focused negative tests using otherwise valid complete 48-row records with exact native tokens; the exact expected identity has a positive case. Whole-object equality also covers initialization, package, model-file and prior-fingerprint changes without field omissions.

Independent final focused runs completed with exit 0: **28 passed** in base (20.49 s; same two existing warnings) and **28 passed** in mgnp (21.94 s), with BLAS threads pinned. The test set remained the same three focused files. Independent final preparation at `/tmp/benign-recode-review-manifest-v2.json` and actual wrapper dry-run of `/tmp/benign-recode-worker-manifest-v2.json` both completed with exit 0. Final manifest hash: **`aac9da955dbe026fb4aaaf5d82dbf55d726878baca4418a5bf779deef4853345`**. The independently prepared JSON equals the worker's final manifest exactly; all 97 current source hashes were independently rechecked. Wrapper plan `/tmp/benign-recode-review-wrapper-plan-v2.json` matches that final hash, 80 total completions, 48/32 stages, and 20,480-token ceiling. Initial manifest hashes and 24-test results below are historical and superseded by these final checks.

## Original finding, now resolved

**P1: intervention accepts baseline stores without the required runtime/source/phase provenance.** `benign_recode.py:112–126` checks the baseline manifest, complete 48-row coverage, inputs, record hashes and a fingerprint computed from the baseline's own provenance. It never checks that this provenance equals the expected baseline identity. `run():191–193` calls it without an expected identity, despite already constructing the current required identity immediately above. Thus baseline rows carrying a different GPU/package/source/initialization/policy/prior fingerprint or even `phase=intervention` can be used to authorize stage B if their row/content hashes are internally consistent. The 32 native token/EOS/termination comparisons do not establish the required runtime lineage when outputs happen to match.

CPU reproduction used the existing synthetic manifest fixture and actual `ResultStore`, wrote its first 48 rows with provenance `{'phase':'intervention','hardware':{'gpu':'WRONG'},'source_files':{}}`, and passed that directory to `baseline_records`. Observed result: `wrong_phase_runtime_source_accepted_rows 48`. No real outputs were changed.

Require the complete baseline provenance to equal the expected current identity with `phase='baseline'` and without the intervention gate; pass this expectation explicitly into `baseline_records` before loading a model or accepting a gate. Add negative tests for cross-phase, runtime, source, initialization and prior-fingerprint changes. This is a required source fix before a blanket launch PASS; at minimum stage B must remain blocked until reviewed.

## Verified behavior

- Actual CPU prepare succeeded at `/tmp/benign-recode-review-manifest.json`: manifest `59436d7835ce97308625bbad3aee16f04cb1575642a603a5df40e5648276f56c`, 80 rows, 97 source bindings and 14 input bindings. Groups are 16 each of native D intact, native H intact, recoding intact, recoding core and recoding random. Native recipients match the original 32 exactly; all recoding targets are `1-correct_option`; both source truth strata have eight rows. Only system text changes for recoding. Greedy decode remains 256 tokens, no donor or score passes.
- Generation stops after 32 native rows if any token/EOS/termination differs, before producing recoding. Baseline emits at most 48; stage B emits only the final 32 recoding knockout rows. Same-phase ResultStore resume requires exact identity, uses a writer lock, rejects corrupt complete records and requires explicit `--resume` in the CLI.
- The gate binds the actual baseline run/results and annotation bytes, requires exactly the 16 intact recoding row IDs, recomputes category/uncertainty/empty/cap eligibility, requires 12 successes and both truth strata. It does not trust a pass boolean. All 16 remain represented; ordinary incidental flags do not add a novel veto. Independent double annotation, adjudication and freeze remain root's external annotation workflow, not a claim made by this adapter.
- Every frozen prior file hash is rechecked. Actual preparation confirmed the fixed-zero manifest's declared internal hash equals `prior_fixed_zero_manifest_hash`; its existing 64 D/H knockout rows are provenance-bound reuse, not new rows. No old source was changed. The benign rubric grades the transparent code and explicitly does not treat correctly encoded false as deceptive factual assertion. Sparse training remains independent of this gate.
- Focused CPU tests: **24 passed** under base Python 3.9 (24.15 s; existing bottleneck/TRANSFORMERS_CACHE warnings) and **24 passed** under mgnp Python 3.12 (24.74 s). OPENBLAS/OMP/MKL thread counts were all pinned to 1. Tests comprised `test_benign_recode.py`, `test_fixed_zero_transfer.py`, and `test_transfer_feasibility.py`; no broad repo suite was required.

Actual wrapper CPU dry-run completed with exit 0 using `bash analysis/benign_recode.sbatch dry-run --manifest /tmp/benign-recode-review-manifest.json` (path shown relative to the selective-deception directory). Its output at `/tmp/benign-recode-review-wrapper-plan.json` matches manifest `59436d7835ce97308625bbad3aee16f04cb1575642a603a5df40e5648276f56c`, 80 completions, 48/32 phases and 20,480 maximum new tokens. Wrapper inspection confirms guarded mgnp activation, offline HF flags, single BLAS threads, deterministic CUBLAS workspace, and removal of common paid-provider API keys before execution. It does not submit a job or load model weights in dry-run mode. Existing source/rubric/prior hashes were revalidated on this path.

## Reviewed hashes

| File | SHA256 |
|---|---|
| `analysis/benign_recode.py` | `6ae60a6e860653eeb3df6614cbcddd0f3b6f4cef6eaa3627387f1e293669049d` |
| `analysis/test_benign_recode.py` | `2b7b4ae088cb9f985d9c5d6f42288d5b08b175904da1972570c53f8333ffd9e0` |
| `analysis/benign_recode.sbatch` | `d870cb393603ffe8ade9e3988632fb7df45b442ba385af3b5ababe024cb30142` |
| `benign-recode-v1/protocol.json` | `96df87126e184faef2625c448af2cb7c58a7bdf24c6178b5fae1fc55faa9e288` |
| `benign-recode-v1/annotation-rubric.md` | `b2e661c4bfae822099c15a1c805f867524c090ca06fd22c4bf7785f4260e0fd9` |

Source edits after these hashes require re-preparation and repeat review of the changed behavior before canonical freeze or launch. No new scientific outcomes exist.
