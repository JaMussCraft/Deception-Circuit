# V4 CPU analyzer implementation and verification

October 21, 2026. Prospective tooling only; no v4 scientific result or finalist freeze is claimed.

Implemented `.scratch/selective-deception/analysis/optimization_v4_summary.py` with CPU toy tests in `test_optimization_v4_summary.py`. It uses the existing audited `extension_summary.py` predicates, gate reconstruction, digest utilities and proposal export writer without editing that file. The v4 run auditor adapts the existing explicit source/cache/checkpoint checks to receipt version 4, amendment-v4, all-head W/rho0/seed0, initialization 1 or 10 and exactly 3072 updates/48 checkpoints per arm. It checks the initialization in amendment/settings/receipt/optimizer; separate manifest, receipt and baseline paths match the launcher interface.

The complete selection grid is exactly `all-W-init1`, then `all-W-init10`. Incomplete, failed or technically invalid grids have no selection proposal, even when one arm has completed. A completed valid arm remains available in the provisional JSON. Segment completion before update3072 cannot select. The complete-grid output also remains nonauthoritative and unfrozen; it never writes a root selection receipt.

Selection keeps the existing prospective joint-preservation/WT-only tiers: 95% then90% target, smallest mask at target, strongest constrained fallback, deterministic ties by update then init1/init10, exact mask deduplication and at most two proposals, including the existing unconstrained diagnostic fallback when a tier is absent or deduplicated. Joint eligibility requires no lost baseline-capable H examples, independently checked against manifest labels; gains cannot conceal losses. WT limits remain PPL rise <=5% and KL <=.05. No historical/native/test evaluation is an input.

The JSON retains all training loss terms, all96 validation rows, paired D surrogate deltas/improvement counts, paired H loss/gain indices/counts and truthful-NLL changes, deterministic head identities, expected stochastic removals reconstructed from checkpoint logits and checked against training logs, checkpoint turnover, source/runtime identities and artifact SHA256 bindings. Matched1536/3072 rows are explicit. Markdown contains the complete frontier and eligibility/failed-target outcomes. Optional `--plots` writes standard matplotlib PNG/SVG trajectories for D reduction, expected and deterministic removals, H losses/gains, WT PPL/KL, and the mask-size frontier, with axis labels and prospective status.

Training does not save actual realized stochastic mask counts, so the analyzer explicitly distinguishes expected stochastic removals from deterministic exports and does not invent realized counts. Scalar terms do not establish gradient dominance. Reused development validation remains exploratory. Fresh heldout assessment after a separate root freeze is required for a generalization claim.

Verification (CPU only):

- `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q .scratch/selective-deception/analysis/test_optimization_v4_summary.py` — **26 passed**, including settings/source tampering, missing or duplicate arms, incomplete history/update coverage, test-split rejection, invalid head identities, no-gradient/nonfinite/invalid expected-count rejection, H loss/gain checks, tiers/ties/dedup/fallback, zero-mask behavior, complete and partial publication, proposal initialization binding, exclusive output directories, and PNG/SVG smoke generation.
- Same command using `/u/swong2/.conda/envs/mgnp/bin/python` — **26 passed**.
- Base `python3.9 -m py_compile` for both assigned Python files — passed.
- Real base-environment CLI against deliberately absent `/tmp/v4-analysis-missing-study` — exit2 and `partial_or_invalid_grid_provisional_only`; no scientific proposal is produced.

Example after both runs finish:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 \
  .scratch/selective-deception/analysis/optimization_v4_summary.py \
  --output .scratch/selective-deception/sparse-optimization-v4/audit --plots
```

The output directory must be new. No model weights, notebooks, old native/test outputs, GPU jobs, Slurm submissions, git operations or ledgers were used or changed. Live v4 artifacts do not yet exist at this implementation checkpoint, so a full real-artifact audit is deferred until root executes the approved fits. The synthetic suite exercises selection/identity helpers and publication; it does not substitute for that future live artifact audit. Only the assigned analyzer, tests and this report were edited by this worker.
