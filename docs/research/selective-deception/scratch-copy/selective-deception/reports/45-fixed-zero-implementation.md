# Fixed-zero transfer implementation

Implemented only `analysis/fixed_zero_transfer.py`, `analysis/test_fixed_zero_transfer.py`, and this report. Existing transfer helper and worktree runtime remain unchanged. Root owns the frozen protocol, wrapper, canonical manifest, independent review, annotation, and launch.

The standalone CLI accepts `prepare`, `dry-run`, and `run`, with `--manifest`, optional `--protocol`, and run-only `--output-dir`/`--resume`. Canonical prior manifest/run paths are fixed. Preparation rebuilds the prior native chat prompts through the existing validated transfer helper, verifies all source/protocol/pair/model/tokenizer/initialization bindings, and validates all 32 prior result records and their fingerprints. Prior outputs and frozen annotations are identity dependencies only; no outcomes enter row or mask selection.

The derived manifest contains exactly 96 unique rows: all 32 intact first, then the same 32 under `shared_core43`, then under `layer_random43`. Recipient prompts and the 256-token decode contract are copied exactly. No donor references, scoring, training, or adaptive selection are present. Mask hashes bind the existing core and fixed seed-0/index-0 layer-matched random masks. `safe_knockout` verifies every MLP remains open.

The small generation adapter passes `hook=ZeroHook()` explicitly into `evaluation.gen_engine.generate`. It preserves native generation, placeholder corrupt allocation, per-row padding, cache, EOS trimming, and output quality metadata. `build_context` retains its inert interchange CLI field; run provenance records the effective explicit zero hook. Every gated reference is zero, so placeholder corrupted tokens are not a content donor.

Before model inference, the new run requires exact prior GPU name/capability/CUDA, Python/package versions, and hashes of every model snapshot file. Source hashes include the prior runtime/helper/wrapper plus the new helper/wrapper. Input bindings also pin the supplemental annotation rubric. `ResultStore` retains existing single-writer, fsync, record hash, and exact resume fingerprint behavior.

Execution generates all 32 fresh intact outputs, then requires exact token IDs, EOS token ID, and termination against all prior outputs before any knockout. A mismatch aborts without knockout generation. Resume rechecks this barrier, including already persisted baselines. Different masks always have different row identities; their target generations are never reused.

## Verification

Tests were written first; initial collection failed because the new module did not exist. Final focused suite: **5 passed under base Python 3.9 / Transformers 4.57.3**, **5 passed under mgnp Python 3.12 / Transformers 5.13**. Both used `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` and only tiny randomly initialized CPU models or stubs.

The real tiny-model test captures pre-o_proj tensors and verifies closed clean heads are exactly zero while retained heads remain nonzero. Adapter token outputs match an independent manual pre-o_proj head-zero intervention. Changing placeholder corrupt tokens leaves those outputs unchanged. Stub tests verify all 32 baseline outputs precede every knockout, a mismatch blocks knockout generation, successful ordering reaches exactly 96 outputs, exact resume generates no duplicate rows, and resumed EOS mismatch aborts.

Commands:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python -m pytest .scratch/selective-deception/analysis/test_fixed_zero_transfer.py -q
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest .scratch/selective-deception/analysis/test_fixed_zero_transfer.py -q
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python .scratch/selective-deception/analysis/fixed_zero_transfer.py prepare --manifest /tmp/fixed-zero-transfer-worker-check.json
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python .scratch/selective-deception/analysis/fixed_zero_transfer.py dry-run --manifest /tmp/fixed-zero-transfer-worker-check.json
```

Temporary CPU manifest: `b5a45df1200387dc3f9abb13d53251000b4f58b4b94a4ba3168204565659ba7d`. Plan: 96 completions, 24,576 maximum generated tokens, zero score/donor passes, 1.0 reserved GPU-hour ceiling, no automatic retries. Root must prepare the canonical manifest after final source review. Actual A100 intact reproduction and all semantic outcomes remain untested until the root-launched job.

Review handoff source SHA256:

- Helper: `9a6dcd8e037af4751414379779d8d4a6fbcffac3675a16225155a7664cad54de`.
- Tests: `20db4aae3065ebd0c72182c0c388ac790021c91eaa37ad74944f6bf69323994f`.
- Root-owned wrapper observed: `aaac58ac28cfc2b94766500b357b85efab3fda0320019fb1a732ad43aad5ff02`.
- Protocol: `38d89600fbef8542b359d53f0d2569229eabd610e462268534d860136f214f4e`.
- Annotation rubric: `c977759ff1a9159e0caddd421387a966aeb93db474635a8effe5dda2da746ebc`.

No GPU calls/jobs, API requests, real model instantiation, downloads, git operations, notebook execution, or nested agents were used.
