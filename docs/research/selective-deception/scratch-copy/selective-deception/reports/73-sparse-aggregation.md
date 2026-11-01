# Sparse-grid aggregation implementation

2026-10-19. CPU-only implementation in `analysis/summarize_sparse.py` with synthetic focused tests in `analysis/tests/test_summarize_sparse.py`, relative to `.scratch/selective-deception`. No frozen training source edits, GPU/model construction, model-weight loading/hashing, submissions, API calls, git operations, ledger edits or finality receipts. No actual training losses or learner outputs were inspected for this implementation. No scientific selection or expansion decision is asserted here.

The analyzer independently implements report52's own-arm admissibility and compact thresholds, then checks those answers against the frozen runner helpers. It ignores stored admissibility/compact flags when calculating answers; mismatches cause a technical rejection. H loss does not veto W, WT loss does not veto H, and HW requires both. It ranks the joint two-rho frontier for each arm by lower D suppression surrogate, fewer removed heads, earlier checkpoint and rho order0 then.01. With a shared intact baseline, lower suppression is exactly greater reduction. If none is admissible, the best-D failed-frontier example remains present. Every validation checkpoint, including earlier checkpoints that lose finalist selection, contributes to the restricted compact-finding test: any own-arm-admissible1..16-head removal with at least10% reduction prevents the no-finding expansion trigger.

A candidate space must have all six H/W/HW×rho0/.01 runs with512 completed updates,4096 SDR presentations and all eight scheduled validations. Interruptions, technical failures, missing records or invalid identities yield `incomplete_or_invalid_technical_grid`, no selection proposal and no scientific expansion inference. Numerical failure cannot be reinterpreted as a negative search result. The CLI supports either union alone or union plus all; the latter requires all12 fits and retains all six finalists, three from each space.

Disk audits load only gate checkpoints and the frozen SDR CPU reference cache. They verify checkpoint payload digests/run fingerprints; optimizer steps; exact latest/frontier cursor histories and loss-log prefixes; the fixed SDR order hash and WT block schedule; finite raw training/validation losses and gradient isolation; canonical manifests/protocol/WT identities; receipt/settings/source/revision bindings; current frozen source inventory; recorded model/tokenizer inventory; deterministic runtime and cross-run software/hardware/model identity; baseline-cache bytes/fingerprint/reference bindings; and measured calibration evidence. Every frontier export is independently reconstructed from small checkpoint gate tensors, including outside-support openness, exact threshold behavior, logits, eligibility, all-MLP-open removal geometry and full export hash. Actual original model-weight bytes are deliberately not rehashed here: training's recorded inventory and frozen identities are bound, while final callers perform their own actual snapshot identity checks.

The JSON retains every run's512-step training curve, all eight raw D/H/WT validation rows, paired D summaries/H truth probabilities and derived H truth-NLL changes, complete head sets, layer counts and in/out-union membership, checkpoint byte hashes and exact input bindings. Probability underflow is explicitly marked and receives no invented finite NLL delta. The Markdown is a short finalist table; detailed curves and out-of-objective dimensions remain in `summary.json`. The analyzer makes no generated-behavior or global-selectivity claim.

## Output and root handoff

After all six union fits finish, root can run:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 \
  /projects/beto/swong2/Alignment/.scratch/selective-deception/analysis/summarize_sparse.py \
  --output /projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-wikitext-v2/aggregation-union
```

For the completed authorized expansion, add `--spaces union all` and use a new output directory. Existing output directories are rejected; no overwrite/resume is implicit. Exit0 means a complete audited grid/provisional proposal; exit2 means an incomplete/invalid run grid with no selection. Fatal cross-run identity mismatches also fail rather than producing a proposal.

Outputs are `summary.json`, `summary.md`, and, only after valid complete coverage, `selection-proposal.json` plus standalone provenance JSON files. The trainer does not write a separate run-identity file; these analyzer copies preserve the selected export's exact provenance and allow the shared caller schema's `run_identity_path/run_identity_sha256` bindings. Each finalist also binds canonical manifest, selected gate export and its chosen checkpoint with absolute path and raw SHA256, preserving `admissible`/`failed_frontier`. The proposal uses the reports67/68/70 shared schema but deliberately has `finalists_frozen:false` and `authoritative:false`; final callers must refuse it as authority. Root alone closes the union/conditional-all-head decision, reviews identities, and freezes the final shared receipt. This worker does not edit that receipt or the compute ledger.

## Verification and source freeze

Focused synthetic suite: **19 passed under Python3.9 in15.98s**, one pre-existing pandas/bottleneck dependency warning. The preceding mgnp Python3.12 focused run also passed19 in21.28s; final post-reporting-change rerun is recorded below when terminal. Tests cover exact compact/WT thresholds, rho/size/update ties, failed-frontier retention, W success despite H failure, earlier compact nonfinalists preventing expansion, missing/duplicate runs, incomplete update/validation coverage, nonfinite losses, gradient failures, heldout-selection rejection, six retained union/all finalists, independent agreement with runner predicates, missing-disk-grid refusal, deterministic gate threshold/outside-support reconstruction, and actual digest-bound CPU checkpoint files including a hash-valid511-update interruption. Actual CLI `--help` exited0 without importing training helpers or reading learner metrics. No full suite or real-grid readiness claim is made.

Frozen analyzer SHA256: `94dc1ef95619e82e1162551b4442f0c081d4ecc668601320d8a68c6e29c80a4f`.

Frozen tests SHA256: `7109f7ceae6f1dec96bf37a26366311c446019855550b57a7fcfad6872628b8f`.

Executable logic is frozen for independent review; the only subsequent source change after those Python3.9 tests corrected the module description from “imports a model” to “constructs a model,” without changing execution. No training/final assessment authority is conferred by these tests.

Final mgnp rerun after checkpoint-byte-hash/probability-underflow reporting changes: **19 passed in26.25s**. The description-only wording correction is the sole later source edit. Both supported environments therefore exercised the same executable logic. Independent review remains root's next step; no actual grid analysis was run here.
