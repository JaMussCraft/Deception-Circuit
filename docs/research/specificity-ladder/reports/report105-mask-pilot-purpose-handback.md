# Mask disposable pilot-purpose hand-back

Agent: mask pipeline implementer. Status: handed-back.

## What changed

This is the separate core API patch after the token-layout correction accepted by report104 and committed by root at `b92c997`. Root froze the prospective policy in `a3-mask-pilot-ruling.json`; its parent is the unchanged operational ruling.

Only the incremental changes to `component_analysis/a3_mask.py` and `tests/test_a3_mask.py` belong to this patch. `streamed_update`, checkpoint construction/restoration and cohort admission now accept an explicit purpose. The default `scientific_training` accepts actual train chunks only. `validation_timing` accepts actual validation chunks only. The chunks keep their source split. The numerical loss, equal cohort weighting, gradients, two-pass replay and Adam step are unchanged.

The purpose is frozen into update specification and checkpoint state. Unknown purposes, wrong source splits and crossing scientific/timing restore contexts reject. Timing state cannot resume as scientific training. The standalone driver retains this distinction in its timing-only receipt and discards the pilot model before scientific fitting; that driver is a separate unaccepted change.

## How verified

The new regression failed first because the core had no `purpose` argument. It now executes an actual tiny native validation-only update, writes a boundary snapshot, restores it in the same timing context, and rejects the scientific context and relabelled source chunks.

Focused commands:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_mask.py -p no:cacheprovider -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_mask.py -p no:cacheprovider -q
```

Base observed 49 passed, three existing environment warnings, exit zero. The final isolated mgnp core run observed 49 passed, exit zero (15.46 seconds). No broad unrelated suite was run.

## Execution evidence

Local CPU execution only; no scheduler job or cluster allocation. Base core observed 49 tests against 49 expected, exit zero. The isolated mgnp run observed 49 against 49 expected, exit zero. Tiny models use random source weights; no scientific baseline reproduction is claimed. The retained-graph/core comparisons from report103 remain in the passing suite. No scientific `run_manifest.json`, full production commit, GPU runtime or benchmark result exists for this software-only change.

## What is NOT done

Independent review and root commit of this incremental purpose patch are outstanding. The standalone driver requires its own full review and cost/source admission. No validation data was relabelled as train; no production weight, GPU/API, protected assay, notebook, ledger or RS state was accessed or changed. No git command was run.

## Open questions

Root should independently close this purpose seam before real M1 use. The full driver review must test the actual disposable validation-only pilot route and ensure every timing/export receipt remains nonfinal and cannot enter scientific selection or assessment.
