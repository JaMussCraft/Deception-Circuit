# Hand-back report107: Explicit mask pilot-purpose seam review

Agent: Codex Sol independent reviewer. Ticket: narrow A3 mask pilot-purpose API seam. Status: handed-back.

## What changed

Verdict: accept the narrow core seam. No blocker was found. The supplied diff against the accepted `b92c997` adds an explicit keyword purpose to cohort admission, updates, checkpoint creation and restore. `scientific_training` remains the default and admits only train chunks; `validation_timing` admits only validation chunks without relabeling. Purpose joins the immutable update specification and checkpoint identity. The diff contains no change to objective weighting, numerical forward/readout, RNG replay, Adam algebra, eligibility/export, or source identity guards.

The reviewer edited no core or test source and did not read the author report. Reviewed inputs were `/tmp/report107-mask-pilot-purpose.diff`, actual core/tests, and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/a3-mask-pilot-ruling.json`.

Commit by explicit file list from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/`: `report107-mask-pilot-purpose-review-handback.md`, `report107-mask-pilot-purpose-repro.py`, `report107-mask-pilot-purpose-repro.log`, and `report107-mask-pilot-purpose-pytest.log`. Identical primary mirrors are under `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/`.

## How verified

Both commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder` with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`.

```bash
/sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_a3_mask.py -k validation_timing_context
```

Observed: 1 passed, 48 deselected, three dependency warnings, in 11.32 seconds (`report107-mask-pilot-purpose-pytest.log`).

```bash
PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 -u docs/research/specificity-ladder/reports/report107-mask-pilot-purpose-repro.py
```

Observed: the independent native script completes both constrained and unconstrained purpose comparisons and same-purpose next-update resume (`report107-mask-pilot-purpose-repro.log`). It uses the same frozen tiny native model and identical tensor contents with unequal D/I sequence lengths and unequal final chunks. The scientific reference retains train labels and uses the default API purpose; the timing model retains validation labels and requests the explicit timing purpose. Every gate-tensor gradient, next parameter, Adam step/moment and final CPU RNG match exactly. No validation chunk is relabeled during timing.

The same script checks all three public admission boundaries: update, checkpoint creation and restore. Each rejects default-purpose validation/test chunks, timing-purpose train/test chunks, and an unknown purpose before any model callback or optimizer-state creation. A timing checkpoint cannot restore into a valid train cohort under default scientific purpose. An altered checkpoint purpose rejects in the timing context. Already-used timing state cannot continue as a scientific fit after the caller supplies train-labeled chunks, and its checkpoint cannot be retagged as a scientific checkpoint. A changed native norm setting still rejects source-bound restore. Same-purpose restore reproduces the next update exactly for both arms (`report107-mask-pilot-purpose-repro.py`, `report107-mask-pilot-purpose-repro.log`).

The update specification, saved top-level purpose, unchanged chunk-content fingerprint including split labels, and completed-boundary check jointly enforce these context separations. The patch's rejection paths do not modify optimizer state in the independent fresh-target probes.

## Execution evidence

- Job/cluster: local tiny CPU model test and independent native review script only.
- Exit status: both commands returned `0`.
- Counts: one observed selected pytest test against one expected, with forty-eight deselected. Both expected objective arms complete native parity and exact same-purpose resume. Every expected wrong-context probe rejects, and the script reaches `PURPOSE_REVIEW_COMPLETE`.
- Baseline reproduces: timing versus scientific gradients, next parameters, Adam state and CPU RNG agree exactly against the unchanged-scientific reference. Uninterrupted and restored timing next parameters and CPU RNG also agree exactly; assertions use zero tolerance (`report107-mask-pilot-purpose-repro.py`, `report107-mask-pilot-purpose-repro.log`).
- Provenance: report-local script/logs above. Reviewed mask SHA256 is `93e1c70fb6073fc0c8e8eb5bf0ca1a37946ab2733cd8e09a5167ab2394e0a505`; test SHA256 is `6728ea080b91a64f727cc6791a11e1547aa505c592f6e5022bbbc5de6f25c480`; ruling SHA256 is `e1126ba764bf9f1b1502edeba2f73f6453f2b49376cd1a82a7a48d7321ebccfe`; supplied diff SHA256 is `665b763f845ea0e4e0444fcdb00fc35c58df24831c327b5f529443e11a156a0d`. No scientific run manifest or full-commit scientific provenance is claimed.

## What is NOT done

No full core rerun, broad suite, driver review, production data/weight loading, GPU/CUDA execution, scheduler/API work, notebooks, git command, state-file operation or subagent delegation. Author-reported full-suite and driver results are not substituted for independent evidence here. Previously accepted objective, replay, export and source-binding semantics were not broadly reopened.

The ruling's output-label and disposal policies remain the driver's responsibility: timing outputs must be nonfinal, and pilot model/optimizer state must be discarded before fitting. This core API review establishes explicit admission/context separation; it does not establish that a separate driver honors output labeling and lifecycle policy or authorize a pilot execution.

## Open questions

No blocker remains in the scoped core patch. Default: accept this seam and keep nonfinal output labeling and disposal-before-fit checks in the separate driver review.
