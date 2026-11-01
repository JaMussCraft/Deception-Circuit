# Independent fixed-zero transfer review

2026-10-18. Astra static review of `fixed_zero_transfer.py`, its focused tests, wrapper, frozen protocol/rubric, prior transfer validation, and the actual `ZeroHook`, generation and safe-knockout implementations. No real-model execution, GPU/job, API, notebook, git or source edits. Report ownership only.

**Verdict: no Critical or Important implementation finding in the reviewed source.** The protocol's stricter pre-output vetoes are acceptable: previously nonfalse D becoming false includes the unresolved baseline, new ambiguity on previously clear outputs vetoes advancement, and capped outputs are disallowed for advancement. Do not change these after outputs. This review releases neither a model fit nor a mechanism claim; normal final freeze, CPU preparation/test verification and the one-hour reservation remain root responsibilities.

Final reviewed hashes (rechecked after worker handoff):

- Runner: `9a6dcd8e037af4751414379779d8d4a6fbcffac3675a16225155a7664cad54de`
- Tests: `20db4aae3065ebd0c72182c0c388ac790021c91eaa37ad74944f6bf69323994f`
- Slurm wrapper: `aaac58ac28cfc2b94766500b357b85efab3fda0320019fb1a732ad43aad5ff02`
- Protocol: `38d89600fbef8542b359d53f0d2569229eabd610e462268534d860136f214f4e`
- Rubric constant: `c977759ff1a9159e0caddd421387a966aeb93db474635a8effe5dda2da746ebc`

## Findings by requested risk

**Actual intervention.** The new `generate_row` passes `hook=ZeroHook()` directly to `gen_engine.generate`; the generator installs that explicit hook inside cached decoding. Thus the context's historical interchange setting or placeholder corrupted stream does not silently determine replacement values. The hook returns a scalar zero in the activation's dtype/device. Gate-selected clean contributions are replaced by zero; unselected contributions remain on the clean path. The tiny-model test inspects the actual clean pre-output-projection activations, confirms the removed head is zero while retained dimensions are nonzero, changes the corrupted stream without changing tokens, and compares with an independent manual head-zero hook. This tests semantics beyond a configuration label.

**Baseline barrier and resume.** Manifest order is exactly 32 intact rows, 32 core rows, 32 random rows. `execute` produces or loads every intact result, then compares each against its prior token IDs, EOS ID and termination before entering the knockout loop. Resumed baseline records undergo the same comparison. Completed resumed rows do not regenerate, and runtime provenance is checked before the model context is built. The focused tests exercise mismatched baseline rejection without any KO call, successful ordering, complete resume without further calls, and resumed EOS mismatch rejection. Any real intact mismatch aborts; there is no tolerance or baseline-replacement fallback.

**Mask and MLP semantics.** Protocol mask hashes bind the existing core and single layer-matched random support. `masks_for` calls `safe_knockout`, which requires zero MLP membership and explicitly checks that every resulting MLP keep mask stays open. No re-derived gate ranking or mask training occurs. Root's frozen audit records 43 heads each, equal layer allocations and four-head overlap. The comparison therefore tests one matched random perturbation, not a random-mask null distribution.

**Bounds and dependency identity.** Protocol byte hash and fixed contract bind the three conditions, 96 completions, 256-token cap, 24,576-token worst case, zero donors/scores/optimizer steps and one-hour ceiling. Derived manifest fields are reconstructed from the validated prior manifest and compared in full; a rehashed changed decode config cannot pass solely by having a valid self-hash. Prior source/run/results/labels are byte-bound; prior records are checked for exact IDs, inputs, row hashes, result hashes and run fingerprint. The prior validator checks its original source, data and model/tokenizer closure. The new manifest additionally binds its runner and wrapper, exact input map, model/tokenizer/data identity and initialization masks.

**Runtime and storage.** Before inference, the runner requires Slurm CUDA, deterministic CUBLAS configuration, and exact prior GPU name/capability/CUDA version, package versions, Python version and model-file hashes. The new run fingerprint includes those bindings, effective zero intervention and prior run fingerprint. A file lock, explicit resume option and `ResultStore`'s exact identity/row validation prevent accidental mixed runs. Hardware identity means matched type/capability, not the same physical GPU serial; that is appropriate for the declared reproducibility check, whose final barrier is output identity. The wrapper allocates one GPU for one hour, disables requeue, uses the intended environment/offline settings and unsets paid-API credentials.

**No hidden scoring or donor work.** This adapter calls generation directly and does not route through `sr.execute`'s label-based donor diagnostics. Its manifest has no donors/reference rows and no score rows. The inherited context initialization reads existing configuration/masks but performs no optimizer update. No paid judge or benchmark loader is called. Semantic labels are a separate blinded phase; prior intact labels may be reused only after the exact barrier passes, with all 64 newly perturbed outputs independently double-labeled and adjudicated before condition joining.

## Scientific limit retained

The two baseline ambiguous outputs concern the same statement and stay in denominators. Their reference ambiguity is not repaired by a more confident perturbed answer. Preserve all predeclared paired utility/damage vetoes and truth/form-stratified reporting. Zero can produce unnatural-activation damage; even a passing contrast is development evidence about instructed-lying transfer and this fixed support, not a strategic-deception mechanism or an explanation of previous interchange results. No fitting on these 16 pairs.

## Verification status

Closed against final worker handoff and `reports/45-fixed-zero-implementation.md`: runner and test hashes were independently rechecked and match the reviewed bytes. Worker reports all five focused tests pass in base (14.77 seconds) and mgnp (17.14 seconds), including explicit zero semantics and the resume/baseline barrier. Worker CPU preparation and dry-run succeeded with temporary manifest `/tmp/fixed-zero-transfer-worker-check.json`, manifest hash `b5a45df1200387dc3f9abb13d53251000b4f58b4b94a4ba3168204565659ba7d`. Tests were inspected rather than independently rerun by this reviewer. Root canonical preparation, actual-wrapper dry-run and reservation remain operational prerequisites. Scientific/code review is closed with no remaining Critical/Important finding; no real-model result is asserted.
