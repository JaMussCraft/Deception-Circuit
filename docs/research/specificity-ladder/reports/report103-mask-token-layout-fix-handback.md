# Mask token-layout correction hand-back

Agent: mask pipeline implementer. Status: handed-back.

## What changed

The reviewed numerical core required identical D/I token counts even though D is a system-pressure conversation and I is a user-request conversation. The canonical A1 prepared artifact at `outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json` contains a FAR train example with D length 98 and I length 118; these are direct lengths of the stored clean token arrays, with no model scoring. Root froze the allowance in `a3-mask-operational-ruling.json` before fitting.

Only `component_analysis/a3_mask.py` and `tests/test_a3_mask.py` form this correction. Cross-condition token-count equality is removed. Each condition still requires the identical complete ordered identity cohort and two streams, finite positive integer token counts, and native recipient/own-neutral shapes matching its binary attention mask and actual counts. Changed chunk/count identities still reject resume. No objective, weighting, optimizer, two-pass RNG replay, eligibility or export algebra changed.

The new unequal-layout tiny native regression compares streamed gradients and the next Adam parameters against the retained-graph oracle, then checks changed-count resume and incorrect own-count rejection. Invalid zero, negative, nonfinite and fractional per-condition counts have focused regressions.

## How verified

Test-first unequal-layout regression failed at the original cross-condition count check. Existing replay tests exposed an early-rejection dependency; the correction retains early own-condition shape/count validation instead of weakening the failure-boundary rule.

Focused command on each supported interpreter, from the specificity-ladder worktree:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_mask.py -p no:cacheprovider -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_mask.py -p no:cacheprovider -q
```

Base result: 48 passed, three environment warnings, exit zero. The final isolated mgnp core result is 48 passed, exit zero (15.35 seconds). All models are tiny random native CPU Llamas. No pretrained weights were loaded.

## Execution evidence

Job/cluster: local CPU commands, no scheduler job. Observed base core coverage is 48 tests against 48 expected, exit zero; mgnp isolated coverage is 48 against 48 expected, exit zero. The native retained-graph oracle and streamed update compare the same source and RNG bank with absolute gradient/parameter tolerance 2e-6 and relative tolerance 2e-5, unchanged from this regression's explicit assertions. This is numerical software evidence, not a scientific baseline reproduction. No scientific `run_manifest.json` exists because no production run occurred; no full production commit or GPU timing is claimed.

## What is NOT done

Root independent review/commit is outstanding. New standalone mask driver files are a separate change and do not become production-admitted through this patch. No source weights, GPU/API, notebook, protected assessment, closed assay, ledger or RS state was touched. No git command was run.

## Open questions

Root should obtain independent closure for this narrow core correction before any real mask use. The actual D/I semantic layouts remain distinct; they must never be spliced, truncated or given fabricated attention masks to force cross-condition equality.
