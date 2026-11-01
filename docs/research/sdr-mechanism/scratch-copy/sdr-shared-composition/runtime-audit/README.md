# Independent raw/runtime audit

Prepared for committed original-SDR shared-composition study `695b126a9d5fe3045c9b5872fac7441d8fcdeec2`. This directory is audit-owned; the immutable runner and its tests are untouched. No producer module is imported. The checker uses stdlib only unless optional CPU tokenizer decoding is requested.

Final protocol file SHA256 is pinned to `0f49bbec41852f33bca8896b83ace6080a7ba1f96e910e91ab58db9cd08f731c`, manifest `959824dc8973cd91f8423c00b7cf34d888bb054770c4fc31711fa2b8731adc44`. The command line rejects another protocol or an uncommitted binding. Hand fixtures call the same audit function with deliberately small protocols; there are no old-study count/schema bindings.

## What is recomputed

- Literal protocol equality, canonical scientific/manifest/run/accepted-envelope digests, exact planned batch/row IDs and order, matching attempt/invocation links and actual-bound deadline admission.
- Main is96baselines+192pairs×20arms=3,936rows/492batches. Calibration is4baselines+8pairs×20arms=164natural rows/21batches plus16forced-stress rows/2batches=180/23; forced arms10/18 are reconstructed separately and never counted as main outcomes.
- Numerical-control coverage per slot and generation step, finite/argmax/tolerance/bitwise/hash consistency, firstscore→decoder checksum/token linkage, and setup donor/U5/repeat/empty/self coverage. Exact forward counts/profile sums, eight setup calls and conservative guard call floor are checked.
- All B8×L224 Boolean mask bytes and hashes, exact bank keys/shapes/dtypes/counts, original-prefix containment and false generated/pad/dummy positions. Actual arm value hashes must match the declared source, clean or induced setup bank. Source masks use frozen common maps; receiver masks use full recipient prefixes.
- Exact logical readouts, legal vocabulary IDs, EOS-union/cap64 and forced64 contracts, baseline-versus-clean-only full token/finish/firstscore equality. Optional local tokenizer decoding verifies continuation, stem-plus-continuation and raw full response from saved IDs without reading semantic choices.
- Complete norm key/row/prefix-length coverage and denominator/finite schema. Norm values cannot be recalculated without activation tensors.
- Every accepted file's raw SHA256 plus an inventory of all raw files. `--previous` requires all prior accepted bytes and immutable attempt/failure/run/setup/interruption evidence to remain unchanged after an explicit resume.
- Optional bound-file checking independently rehashes the66 source files, historical inputs/masks, parent, and cached configuration/tokenizer files. `--rehash-weights` additionally reads all four weight shards. The protocol binds software versions/metadata, but the raw run does not independently record loaded distribution metadata beyond hardware Torch/CUDA identity; external software closure must be reconciled separately.

## What remains receipt-verified or external

Raw full-vocabulary vectors and activation tensors are not archived. The checker verifies complete structured comparisons, hashes and provenance links; it cannot independently recompute vector error/argmax, natural propagation, norm values, BF16 values or immutable-bank behavior without rerunning the model. Those claims are numerical receipts supported by the reviewed runner and tiny-model tests, not independent model inference here.

Scheduler start/end, terminal state, GPU allocation/elapsed time and accounting must be reconciled against operator-provided raw scheduler receipts. The run's recorded allocation is checked internally, not treated as independent scheduler truth. Likewise, the fixed10second nonforward floor must be checked from actual calibration costs before main release, including measured setup minus forward time, publication, read/hash, and any unexplained wall-time residual. Producer summaries or a `calibration.json` file alone never establish PASS.

Operational failure files and unclosed attempts remain visible. A complete audit rejects hard numerical failures. `--allow-incomplete` exists for a pre-resume snapshot and reports missing/unclosed work; it does not authorize resume. The operator/root still verifies the external interruption cause and exact resume action. The checker never mutates a run directory and creates a fresh audit report only.

## Commands

Use mgnp for CPU tokenizer compatibility; no CUDA/model is loaded:

```bash
/u/swong2/.conda/envs/mgnp/bin/python .scratch/sdr-shared-composition/runtime-audit/audit.py \
  --protocol .scratch/sdr-shared-composition/freeze-final-695b126.json \
  --run-dir RAW_DIRECTORY --phase calibration \
  --decode-cache /work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659 \
  --repository Deception-Circuit/.claude/worktrees/sdr-routing-pilot \
  --output .scratch/sdr-shared-composition/runtime-audit/calibration-raw.json
```

For main change `--phase main`; for a terminal operational interruption add `--allow-incomplete` and save the report before any exact resume. After a reviewed resume supply `--previous PRIOR_AUDIT_JSON` and a fresh output path. Rehashing weights is explicit because it reads roughly16GB; no model loading occurs. Audit output must remain outside the raw run directory so its inventory is stable.

The independent narrative audit will cite the raw report, scheduler/accounting reconciliation, timing arithmetic, source/cache/software closure and limitations. A raw report's `status=complete` means the planned receipt set is complete; it is not independent behavioral or scientific success.

## Hand-fixture verification

Test-first evidence: initial13contracts failed at an explicit missing-checker assertion; added norm-coverage, prior-failure-preservation and independent timing-cost tests each exposed a real gap before their implementation. Final21tests pass in both base Python3.9 and mgnp Python3.12; ruff F passes. The only external-model behavior in the tests is absent: fixtures are handwritten tiny JSON receipts and token strings.

Fixtures exercise correct acceptance without producer summaries, corrupt digests/tokens/readouts/firstscores/controls/deadlines, missing attempts/batches, accepted-byte and failure-evidence preservation across resume, CPU decode mismatch, independent physical-mask hashing, separate calibration stress rows, mixed-mask source/receiver bank origins, missing setup controls/norms and clean-only identity.

```bash
/sw/external/python/anaconda3/bin/python3.9 -m pytest -q .scratch/sdr-shared-composition/runtime-audit
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q .scratch/sdr-shared-composition/runtime-audit
/u/swong2/.local/bin/ruff check --select F .scratch/sdr-shared-composition/runtime-audit
```

Calibration job23232031 raw files have now been checked. See `calibration-audit-23232031.md` and its independent JSON evidence for the final verdict and exact limits. Main has not been audited. Operator `shared_composition_seams` notifies the reviewer with actual terminal raw paths/accounting; no polling is performed.
