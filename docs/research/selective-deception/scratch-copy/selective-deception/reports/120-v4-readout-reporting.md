# Supplementary v4 readout reporting

October21,2026. Prepared `analysis/optimization_v4_readouts.py`; no live v4 result or selection is claimed. This is a descriptive supplement to the existing complete audit, not a new selection policy.

The helper requires a passing complete validation-only v4 audit, exactly two3072-update histories with48checkpoints each, all96unique run/update frontier records, and agreement between saved run histories and aggregate frontier rows. The CLI also checks the upstream v4/shared auditor source hashes. Partial/failed grids cannot produce this report. All inputs are existing train/validation audit JSON; no model, GPU, jobs, test/native scoring or source/runtime changes are involved.

It computes:

- D surrogate reduction from the recorded aggregate suppression scalar.
- Exact **saved** D/H/other argmax counts for both D and H recipient streams, checked for119-row coverage.
- Per-pair D-label minus H-label logit margins from saved two-label logits, their means, and negative/zero/positive paired changes relative to the same intact examples. D-stream and H-stream margins are separate.
- Paired signs of the saved D per-example surrogate changes, plus recorded H loss/gain counts.
- **Approximate**, never exact, mean pD: invert each saved per-pair surrogate with `-expm1(-t_i)`, then average. This is not inversion of the mean surrogate. Saved per-pair values were computed through FP32 softmax/log1p after clamping probability to FP32(1−1e−7), so inversion cannot recover pre-clamp probability and retains FP32 rounding error. Inferred saturation counts are reported for every checkpoint and its baseline, using a2e−6 tolerance around the FP32 clamp-surrogate value. Exactly-at-cap values cannot be distinguished from values clipped above the cap.

`readouts.json` retains all96descriptive checkpoint records and paired exact-saved margins. `readouts.md` tables the matched1536/3072points and existing proposed finalists. An optional explicitly frozen root receipt can tag frozen finalists by matching either run/update/export identity or checkpoint path/SHA; no freeze is inferred. No masks are ranked, selected, exported or changed. The output directory must be new; original audit and selection artifacts are never overwritten.

After both fits and their existing full audit complete:

```bash
/sw/external/python/anaconda3/bin/python3.9 \
  .scratch/selective-deception/analysis/optimization_v4_readouts.py \
  --summary .scratch/selective-deception/sparse-optimization-v4/audit/summary.json \
  --output .scratch/selective-deception/sparse-optimization-v4/readouts
```

Add `--frozen-receipt PATH` only for a genuine root selection receipt. This supplementary view does not alter prior selection rules or justify strategic-deception specificity/generalization from reused validation.

Verification: `--self-test` **passed** in base Python3.9 and mgnp Python3.12; base `-m py_compile` **passed**. The bounded stdlib fixtures check known probability inversion/clamp behavior, exact margin arithmetic, paired signs, a119-pair descriptive row, nonfinite/out-of-range rejection and partial-audit rejection. No full live-grid report has been generated at this preparation checkpoint. Only the assigned new helper and this report were retained.
