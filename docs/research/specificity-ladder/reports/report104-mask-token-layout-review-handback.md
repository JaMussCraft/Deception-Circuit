# Hand-back report104: Mask token-layout compatibility review

Agent: Codex Sol independent reviewer. Ticket: narrow A3 Task5 token-layout compatibility patch. Status: handed-back.

## What changed

Verdict: accept this narrow compatibility patch. No blocker was found. The supplied diff changes only cohort validation and its focused tests. It removes cross-condition token-count equality while preserving complete paired ids/order, positive finite integer counts, native recipient/own-neutral shape agreement, binary attention masks and agreement between each own mask sum and its recorded counts. This matches the prospective operational ruling. There is no loss, RNG replay, optimizer, export or source/checkpoint algebra change in the supplied diff.

The reviewer edited no implementation or test source and did not read the author report. Commit by explicit file list from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/`: `report104-mask-token-layout-review-handback.md`, `report104-mask-token-layout-repro.py`, `report104-mask-token-layout-repro.log`, and `report104-mask-token-layout-pytest.log`. Identical primary mirrors are under `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/`.

Reviewed inputs: `/tmp/report104-mask-token-layout.diff`, actual core/tests, accepted Task5 plan, and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/a3-mask-operational-ruling.json`. The ruling explicitly permits different D/I lengths because conversational layouts differ, while preserving each recipient's own neutral geometry and equal stream/id weighting. The stated frozen FAR lengths were supplied by the orchestrator/ruling; this review did not inspect production rows or weights.

## How verified

Both commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder` with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`.

```bash
/sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_a3_mask.py
```

Observed: 48 passed in 16.77 seconds with three dependency warnings (`report104-mask-token-layout-pytest.log`).

```bash
PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 -u docs/research/specificity-ladder/reports/report104-mask-token-layout-repro.py
```

Observed: the separate reviewer oracle passes all six active/inactive/exact-kink by constrained/unconstrained cases. Maximum absolute gradient error is 2.9103830456733704e-11 (`report104-mask-token-layout-repro.log`). It independently constructs the full-cohort loss and KL expression instead of calling `mask_objective`, then compares every gate-tensor gradient, next gate parameter, Adam step and moments, and final CPU RNG.

The native fixture uses D tensors of length `98` and I tensors of length `118`, with different valid counts across ids and designation streams and right padding. D chunk sizes are `2+1`; I chunk sizes are `1+2`. Every full-cohort scalar averages the two streams within each id and all ids uniformly; token counts never appear as objective weights. This catches accidental per-token weighting and incorrect equal weighting of unequal chunks (`report104-mask-token-layout-repro.py`).

Ten malformed own-layout cases reject before any model callback or optimizer state creation: zero, negative, infinite, NaN and fractional counts; fractional and negative nonbinary masks that preserve the original total; a NaN mask; a mask/count mismatch; and a neutral-donor shape mismatch. The same script constructs a changed I layout whose shapes, binary masks and counts are internally valid. `_validate_chunks` accepts that prospective cohort, while restoring the old checkpoint rejects its changed content identity. Reusing the original unequal layout restores the next parameters and CPU RNG exactly (`report104-mask-token-layout-repro.py`, `report104-mask-token-layout-repro.log`).

The narrow diff leaves the reviewed objective and source/export/replay implementation untouched. The existing cohort content fingerprint still includes payload tensor bytes/shapes, counts and chunk boundaries; removing cross-condition equality therefore does not loosen exact resume identity. No D/I token splice, truncation to equalize conditions or mask falsification is introduced.

## Execution evidence

- Job/cluster: local tiny CPU model tests and reviewer script only; no production or scheduled run.
- Exit status: both commands above returned `0`.
- Counts: forty-eight observed tests against forty-eight expected; six observed independent mathematical-oracle cases against six expected; ten malformed-layout rejections against ten expected.
- Baseline reproduces: retained and streamed gradients differ by at most 2.9103830456733704e-11 (`report104-mask-token-layout-repro.log`). Uninterrupted and restored unequal-layout next parameters and CPU RNG agree exactly, against the expected equality asserted by the script.
- Provenance: the report-local script and logs above. Reviewed mask SHA256 is `dd17f7183dd7455113c683e1cbf0df4c6fd9452050de3ac02cafb8f55400b30a`; focused test SHA256 is `2f5aa03a78827fef51b82ace11fcf5dbb53efd06fcf234151fab948e09f44db4`; operational ruling SHA256 is `40e9cef75f9e62e99081105157dbba54a2ccaf085306061ef6669e51a032980c`; supplied diff SHA256 is `2ecf37777eb109a219fe90e787442ade38652b3125301ec6f9d2718c926e24ea`. No scientific run manifest or full-commit scientific provenance is claimed.

## What is NOT done

No implementation fix, broad suite, extra isolated mgnp run, driver review, production dataset/weight loading, GPU/CUDA execution, scheduler/API activity, notebooks, git command, state-file operation or subagent delegation. The author-reported driver test coverage was not used as independent evidence. Earlier accepted objective/export semantics were not reopened.

An initial reviewer fixture used left padding and produced nonfinite native margins before update admission. The final fixture uses right padding; no left-padding support or diagnosis is claimed, and no native-forward source change is part of this diff. This compatibility verdict concerns different condition lengths and their validated own-condition geometry.

## Open questions

No blocker remains for this narrow patch. Default: accept it and continue the separate driver review. Production admission must still preserve each condition's actual neutral mapping evidence and the frozen paired id/order contract; this local review does not authorize a model fit or scientific execution.
