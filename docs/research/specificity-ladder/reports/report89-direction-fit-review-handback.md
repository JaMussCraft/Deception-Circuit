# Hand-back: Independent direction fit review

Agent: Codex independent reviewer. Ticket: direction integration Unit C. Status: handed-back.

## What changed

Review disposition: no blocking finding in Unit C. No production source or repository test was edited. Author report87 was not read. Review used the integration plan's Unit C and shared contracts, the fit pipeline and fit tests, and the reviewed artifact, direction, design and preparation implementations.

Report for the orchestrator's explicit file list:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report89-direction-fit-review-handback.md`
- Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report89-direction-fit-review-handback.md`

Standards: no concrete standards defect found. Spec: Unit C's fit-side contract is implemented, subject to the explicitly deferred orchestration boundary below.

The expected train identity is constructed before reading the cache at `component_analysis/a3_direction_pipeline.py:45` and consumed at `component_analysis/a3_direction_pipeline.py:212`. Frozen protocol source fields include the complete source closure, original parent and sidecar bytes, matched-source fingerprints, grader/model/tokenizer identity and actual capture numeric profile. Parent identity/evidence and source commit/closure are checked against the independent design/protocol. Membership, task/site/condition layout, row prompt/token/readout/label digest and stream order are derived from frozen train rows. Optional attached protocol and operational fields must agree when present. Strict artifact metadata equality prevents loaded metadata from supplying its own expected identity. Re-signing array descriptors and completion markers does not authorize changed source, profile or ordering. Exact array names and paired shapes are checked before fitting.

The same canonical-wording cluster draw feeds DOM, nuisance and both probes. Probes expand integer multiplicities without trimming; every paired stream has the same within-bootstrap weight. The independent oracle uses unequal cluster sizes and a seed with repeated cluster draws. It compares fitted weights and probe center, scale and coefficient against direct residual mapping followed by image coordinates. The small associated map in `component_analysis/a3_direction_pipeline.py:188` gives the intended image coordinates without storing residual-width activations. Metadata features match the frozen role/length/position feature definition. Ridge fitting keeps the reviewed regularization and unpenalized intercept; standardization consumes only the expanded train design.

The probe byte preflight precedes expansion allocation. The injected allocation sentinel is never called when the frozen byte limit is insufficient. Failed probes remain diagnostics; failed DOM/nuisance geometry/numeric fits retain explicit receipts. No replacement axis, dropped seed or finite stand-in is introduced. Blocking is computed for every frozen task/seed lacking a valid candidate. Geometry arrays are deduplicated by projection content across seeds and sites; the output inherits the capture numeric profile and adds exact capture byte lineage without claiming CPU fitting generated new model activations.

## How verified

All commands below ran in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`. Both suites used single-thread BLAS and disabled pytest's cache provider.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_fit.py tests/test_a3_directions.py tests/test_a3_direction_artifacts.py -q -p no:cacheprovider
```

Observed: `126 passed, 3 warnings in 29.70s`; exit `0`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_fit.py tests/test_a3_directions.py tests/test_a3_direction_artifacts.py -q -p no:cacheprovider
```

Observed: `125 passed, 1 skipped, 4 warnings in 35.35s`; exit `0`. The skip is `test_tiny_llama_direction_replays_through_existing_inference_hooks`, whose guard requires pinned NNsight `0.7.0`. It passed under mgnp. These tests create random tiny CPU models; no pretrained weight files or GPU forwards were used. The NVML initialization warning arose from dependency discovery, not a model job.

Independent adversarial/oracle script: `/tmp/test_report89_fit_review.py`, SHA-256 `b67c948f76e267c9f3d6dd4872de3103883a9275b771a84f369a8bc861e58720`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python -m pytest /tmp/test_report89_fit_review.py -q -p no:cacheprovider
```

Observed: `14 passed in 7.99s`; exit `0`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 -m pytest /tmp/test_report89_fit_review.py -q -p no:cacheprovider
```

Observed: `14 passed, 1 warning in 8.31s`; exit `0`.

The script covers rectangular projection coordinates and an independent numpy ridge solve; unequal cluster sizes and multiplicities; condition/layout/ID order, source-row bytes, row digest, extra/malformed arrays, re-signed wrong source/profile; cross-site geometry deduplication; and rejection before expansion allocation. Runtime monkeypatch mutants deliberately corrupt the image map and cluster multiplicities. The oracle catches both. No repository implementation was mutated.

Review harness correction: the first multiplicity mutant check did not fail because the original two-cluster synthetic fixture happened to draw each cluster once for every frozen seed. That initial harness run had `13 passed, 1 failed` in each environment. The final fixture uses three clusters with unequal sizes and an actual repeated draw; the final results above include both killed mutants. This was a test-fixture weakness, not an implementation failure.

```bash
/u/swong2/.local/bin/codex-usage --pause-at 80
```

Observed live reading: weekly used `25`, remaining `75`, `should_pause=false`, reset `2026-11-06T16:07:41+00:00`; exit `0`.

## Execution evidence

- Job and cluster: local CPU pytest commands above; no Slurm/GPU/API job.
- Exit codes: final scoped and independent suites all `0`; the initial reviewer-harness mutant check failed as documented above.
- Counts against expected: mgnp scoped `126/126`; base scoped `125` passes plus the documented dependency skip against `126` collected; independent suites `14/14` on each interpreter. Normal synthetic fits retain all frozen seeds; the two-site dedup case retains all six task/site/seed receipts with one stored geometry. Zero DOM and zero geometry tests retain blocked receipts for every seed.
- Baseline assertion: final unmodified rectangular-projection/unequal-cluster oracle passes on both interpreters; expected numpy center/scale/coefficient and expanded weights match fitted arrays within `2e-6` absolute/relative tolerance. The altered image map and multiplicities fail this same oracle. This is a CPU implementation check, not a scientific baseline reproduction.
- Provenance: no scientific run or `run_manifest.json` was created and no scientific commit is claimed. Exact reviewed file hashes: fit pipeline `fc5d9c2b01f2e12b7c1ec7230ac215c772ba1b24566f151c682eace02eb80684`; fit tests `5407d6c4a5c34db69974d709e547746be31e74c2f79d002329b7891ceec3d8e7`. Git was not run.

## What is NOT done

Unit F's production freeze of `fit_cache.capture_identity`, probe byte limit and actual capture adapter remains deferred as explicitly scoped by the orchestrator. Canonical preparation currently does not generate that contract; the fit stage rejects its absence. This is not a Unit C blocker and the injected fixtures do not authorize production execution. The future adapter must freeze the actual measured capture profile/source before capture and preserve the canonical array ordering.

No production capture, validation/assessment scoring, site selection, finalization, GPU memory measurement or scientific effect estimate was performed. Validation and selected-site assessment balanced accuracy belong to later consumers of these frozen train transforms. The independent script remains a temporary review artifact, not a committed regression file. No broad suite, notebook, API call, weight download, Slurm submission, subagent or git command was used.

## Open questions

None blocking Unit C. Default: accept the fit-side implementation and keep production admission closed until the deferred capture contract, adapter and consuming selection/inference stages receive their own integration review. Consider promoting the unequal-cluster rectangular-projection oracle and pre-allocation sentinel into permanent tests when the orchestrator next owns this test file.
