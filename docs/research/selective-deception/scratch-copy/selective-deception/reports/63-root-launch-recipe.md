# Root launch recipe — 2026-10-19

Read-only follow-up to reports55/59. No receipt, manifest, GPU job or git change was issued here. Frozen runner SHA remains `e2deca68a89b71482fe7b4425ab0f65ba8cd560e4291f45132033a538d666c4d`. Root should commit first, then keep that source revision and source contents fixed throughout reference preparation/calibration/production; a revision/source/runtime change invalidates baseline reuse.

## Paths and exact preparation

Run from the new worktree. These shell variables are recipe examples for root, not executed by the reviewer:

```bash
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/selective-wikitext
SW_STUDY=/projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-wikitext-v2
SW_MODEL=/work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
SW_REV=0e9e39f249a16976918f6564b8830bc894c89659
SW_DATA=/projects/beto/swong2/Alignment/Deception-Circuit/data/datasets/sdr
SW_WTCACHE="$SW_STUDY/reference-cache-wikitext"

/sw/external/python/anaconda3/bin/python train_selective_mask.py \
  --prepare --policy amendment-v2 \
  --source-manifest /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/selective-mask-pilot/outputs/selective-mask-pilot/manifest.json \
  --manifest "$SW_STUDY/manifest-HW-union.json" \
  --freeze-record "$SW_STUDY/protocol.json" \
  --wikitext-manifest "$SW_STUDY/wikitext-manifest.json" \
  --collateral-arm HW --candidate-space union --seed 0 --rho .01 --joint-pairs 1 \
  --max-updates 512 --checkpoint-every 64
```

Repeat preparation for H and W union manifests with matching filenames/arm flags when root freezes those runs. Rho is a runtime setting, not a separate manifest. All-head manifests change only candidate space/filename and remain conditional on the full valid restricted-grid result and budget. Preparation is CPU-only and exclusively creates the output manifest. `--freeze-record` here means the immutable canonical scientific protocol, **not** a root execution receipt. Raw protocol SHA is `f973ecadc851666646795ab5bf9cdb5990326c123acc6c8b3470bd7f8b71255e`.

## Baseline receipt construction

Use actual runner functions, not raw JSON-file hashes in place of canonical hashes:

```python
import json
from pathlib import Path
from evaluation import selective_diagnostics as sd
from evaluation import selective_mask_runner as r

study = Path('/projects/beto/swong2/Alignment/.scratch/selective-deception/sparse-wikitext-v2')
m = r._read_manifest(study / 'manifest-HW-union.json')
protocol = json.loads((study / 'protocol.json').read_text())
assert m['amendment']['protocol_hash'] == sd.content_hash(protocol)
assert r._hash_file(study / 'protocol.json') == 'f973ecadc851666646795ab5bf9cdb5990326c123acc6c8b3470bd7f8b71255e'
record = dict(
    version=2, policy='amendment-v2', manifest_hash=m['manifest_hash'],
    protocol_hash=m['amendment']['protocol_hash'],
    wikitext_manifest_hash=m['amendment']['wikitext_manifest_hash'],
    baseline_path=r.BASELINE_PATH,
    root_decision='2026-10-19 user-authorized sparse amendment; root-authorized reference preparation',
    source_revision='ROOT FILLS ACTUAL FINAL COMMIT ID',
    source_files_hash=sd.content_hash(r._source_files()),
    model_revision='0e9e39f249a16976918f6564b8830bc894c89659',
    user_authorized_fit=True,
    prior_behavior={
        'SDR_original_generation_gate':'failed',
        'SDR_grounded_generation_gate':'failed',
        'fixed_core_zero_selectivity_gate':'failed',
        'benign_recoding_control':'independent; does not veto authorized fitting',
    },
)
r._amended_receipt(record, m, 'baseline')
with (study / 'receipt-baseline-HW-union.json').open('x') as f:
    f.write(sd.canonical_json(record) + '\n')
```

`r._source_files()` hashes the complete enumerated production source inventory, not only four B files; tests/reports are excluded. `sd.content_hash` hashes canonical content. `r._hash_file` hashes exact file bytes. `source_revision` must be the actual stable committed revision, not the example string. Baseline receipt needs no baseline fingerprint, numerical passed label, measured budget, allowed-rho list or training settings. Historical failed behavior stays factual. The baseline receipt binds one manifest, even though resulting all-open references are shareable across arms/spaces.

## Exact baseline and calibration invocations

Common arguments below bind HW/union as the representative baseline/calibration request. Calibration internally measures **both spaces × all three arms**, regardless of this representative arm:

```bash
SW_COMMON=(
  --policy amendment-v2
  --manifest "$SW_STUDY/manifest-HW-union.json"
  --wikitext-manifest "$SW_STUDY/wikitext-manifest.json"
  --wikitext-cache "$SW_WTCACHE"
  --model-path "$SW_MODEL" --model-revision "$SW_REV"
  --data-dir "$SW_DATA" --device cuda --dtype bfloat16
  --collateral-arm HW --candidate-space union --seed 0 --rho .01 --joint-pairs 1
  --max-updates 512 --checkpoint-every 64
)

# CPU wrapper dry-run first; it reads frozen manifests and loads no weights.
bash scripts/selective_mask.sbatch --dry-run "${SW_COMMON[@]}" \
  --output-dir "$SW_STUDY/baseline"

# Payload for a root-reserved A40/H200 Slurm allocation:
bash scripts/selective_mask.sbatch --baseline "${SW_COMMON[@]}" \
  --freeze-record "$SW_STUDY/receipt-baseline-HW-union.json" \
  --output-dir "$SW_STUDY/baseline"

# After baseline completion and receipt extension described below:
bash scripts/selective_mask.sbatch --calibrate "${SW_COMMON[@]}" \
  --freeze-record "$SW_STUDY/receipt-calibrate-HW-union.json" \
  --reference-cache "$SW_STUDY/baseline/reference.pt" \
  --output-dir "$SW_STUDY/calibration" --profile-updates 3
```

The last two are GPU payloads, **never login-node commands**. For sbatch submission, replace the leading `bash` with `sbatch` and add explicit root-chosen `--account`, `--partition`, `--time`, and `--chdir` before `scripts/selective_mask.sbatch`; the remaining CLI arguments are identical. Create worktree `logs/` before submission. Prefer a single H200 (`gpuH200x8` or its interactive variant) for memory headroom and heavier smoke; A40 (`gpuA40x4`) is supported. Do not use A100 for this backward workload. Choose one GPU type for baseline, calibration and production: putting both A40 and H200 in a partition list can produce a different runtime identity and unusable shared references. Queue/account choice and concrete reservations remain root decisions, not the wrapper defaults. Interactive partitions cap walltime at1h. Root caps remain20 cumulative reserved GPUh/max2 concurrent jobs/zero paid APIs; do not interfere with the active old-worktree control job. Reference preparation, calibration and production each require charged explicit reservations. No throughput/resource claim has been measured yet.

After successful baseline, read `baseline/baseline.json`. Extend the baseline receipt into a new calibration receipt with exactly:

```python
b = json.loads((study / 'baseline/baseline.json').read_text())
record.update(
    baseline_fingerprint=b['fingerprint'],
    baseline_cache_sha256=b['baseline_cache_sha256'],
    wikitext_cache_fingerprint=b['wikitext_cache_fingerprint'],
    wikitext_cache_inventory_hash=b['wikitext_cache_inventory_hash'],
)
r._amended_receipt(record, m, 'calibrate')
with (study / 'receipt-calibrate-HW-union.json').open('x') as f:
    f.write(sd.canonical_json(record) + '\n')
```

Baseline output contains the actual runtime fingerprint; do not invent it on CPU. Internally it is `r._baseline_fingerprint(identity)`: canonical hash of runtime identity excluding `receipt,settings,optimizer,manifest_hash,amendment`, while retaining original SDR hash, WT hash, actual model-file hashes, fixed masks, source contents/revision, packages, GPU name/capability/CUDA and declared numerical path. WT fingerprint is `wt.cache_fingerprint(wm, r._wt_reference_identity(identity))`; its reference identity contains that baseline fingerprint, baseline path and WT manifest hash. Inventory uses `r._wt_inventory` and each block's validated digest/token hash. Baseline prepares238 joint SDR readouts plus48 WT blocks, no test references/generations.

One completed baseline supplies the same `reference.pt` and per-block WT cache to all arms/rhos/spaces **only with identical retained runtime/source/data identity**. Each arm/space still needs its own root receipt with that manifest's hash/protocol/WT binding; copy the measured four technical fields, not the old receipt's manifest hash. Root must preserve the same `source_revision` as well as file contents. Source patches, environment changes or a different GPU model require regenerated matching references. No simultaneous baseline cache writers. Explicit `--resume` is required when continuing an existing baseline/cache/output; calibration should use a fresh output directory.

After calibration, inspect measured full-vocabulary WT floors, semantic-label0.02 tests, all-open validation, finite/isolated gradients, six actual profiles and nonempty binary-export identity. Freeze `calibration.json` raw SHA with `r._hash_file`; the numerical evidence and budget/profile SHA refer to the same artifact. Production receipts additionally require report55's actual numerical evidence, matching `r._amended_settings(args)`, allowed rhos, root resource decision and actual artifact path. Price the fixed six×512 grid using the measured per-space/arm times **before** issuing production receipts. Calibration is disposable and returns production_optimizer_steps0; native `--evaluate` remains pending root fresh-cluster adapter.

## Existing full-suite log comparison

At this read, `62-wikitext-full-base.log` is complete: **7 failed,1507 passed,77 skipped**,207.53s. Its seven failure names exactly match report33 base; **0 new failure names**. They are the MASK worktree-path test; FAR/SDR/SER clause-word reuse; SER pressure pool; three-spec registry; and cross-mechanism hyperparameter equality. Baseline report33 base had1474 passed, so33 additional passing tests.

`62-wikitext-full-mgnp.log` is still incomplete (progress near4%, no terminal pytest summary), so its comparison is pending; no rerun was started. Report33 mgnp's expected eight names are those seven plus `tests/test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap`. Root must compare completed names, not counts alone. No completed mgnp result is asserted here.
