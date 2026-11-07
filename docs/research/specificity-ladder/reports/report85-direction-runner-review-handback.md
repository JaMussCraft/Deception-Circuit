# Hand-back: Independent direction runner review

Agent: Codex Sol. Ticket: Work unit B of `plan-a3-direction-integration.md`. Status: handed-back.

## What changed

Initial review verdict: request changes for the packed-equivalence and positive-control consumers. The scoped re-review below supersedes that verdict and closes both blockers. No implementation edits by this reviewer.

Files for the orchestrator, with identical primary mirrors:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report85-direction-runner-review-handback.md`: this independent review.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report85-runner-review-repro.py`: injected CPU reproduction using existing test fixtures.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report85-runner-review-evidence.log`: observed execution output.

**High priority: packed execution accepts asserted equivalence without measured execution binding.** In `component_analysis/a3_direction_runner.py:113`, `_geometry` validates Boolean assertions, profile geometry and digest syntax. The input, donor-map and axis digests are never checked against their claimed measurements or an execution scope; no producer of measured serial/packed evidence exists in the runner. Consequently an invented fixture receipt permits packed execution even when patched outputs differ from serial execution. Same-shape no-op controls and repeated intact lanes cannot establish equivalence of nonzero directional interventions. The current packing test uses identical axes and zero interventions on a synthetic backend, while the actual tiny NNsight test runs serial only. Add a measured equivalence path that exercises the axis-specific patches, donors, controls and dummy lanes and emits source-bound evidence; consume that evidence against its tested scope/coverage. A mere `measured=True` or collection of unrelated digest strings must not authorize packing.

Reproduction: the attached script wraps the existing fake backend with an injected packing-sensitive patched-logit transformation while preserving all intact and no-op outputs. Serial and packed scoring both succeed, with zero replay error, but disagree on every patched margin. The exact observed values are in `report85-runner-review-evidence.log`. This is a deliberate synthetic fault demonstrating the guard gap, not a claim of an observed production kernel discrepancy.

**High priority: positive-control references can mark unmeasured or changed calibration as valid.** In `component_analysis/a3_direction_runner.py:471`, `_positive_reference` accepts a syntactically valid `control_id` without recomputing the row digest or resolving a measured control artifact. It does not require the measured full-vocabulary error, complete sender coverage or donor provenance. The reproduction supplies only a task/condition/ID/stream, current recipient/profile digests, `valid=True` and an invented digest; production scoring emits `gate_valid=True`. Even changing measured fields on a genuine row leaves its old digest accepted. In addition, `run_positive_controls` attaches the requested profile identity without calling `_runtime`, so it can mislabel the runtime dtype/backend. Require actual measured calibration evidence and digest/content validation before producing compact references, check runtime identity, and retain/check the calibration donor source and separately padded calibration geometry. Keep compact per-row references after validating the backing record. This finding concerns the runner's direct consumption/creation of control rows, not the separately reviewed artifact module.

The bounded inference path otherwise uses the reviewed direction algebra and shared hook/statistics path. Named head readouts and padding masks are isolated; zero, H-centered removal and signed steering use the reviewed subspace formulas. Mechanism donors require same ID/condition/opposite stream; IOI requires corrupt donors; MMLU interchange rejects. Scalar outcomes include canonical FP32 full-vocabulary correctness, native diagnostics and MMLU choice diagnostics. Chunk cleanup avoids cross-chunk activation/logit/graph retention. Point estimators pair both streams, require per-stream positive denominators, use the intended D/I fractions and strict collateral boundaries, and check both MMLU memberships and common intact outcomes.

### Scoped re-review: both blockers closed

Current verdict: the updated Unit B runner is acceptable at this bounded seam. No new intrinsic blocker found. This does not admit model stages or approve future profile reuse.

The new measured packing producer runs distinct nonzero numeric axes through the actual directional patch path, mapped donors, intact/replay controls, full tiles and a dedicated final partial tile. It binds exact ordered inputs, source/profile, cell axes/maps and donor-cache content. The consumer checks receipt and scope content digests, complete comparison coverage and equality of serial/packed canonical margins and argmax before checking the requested cells against the tested scope. The independent original packing-sensitive fault now fails measurement with `equivalence margin disagreement`. Changed source, inputs, numeric axis and receipt content each block before additional scoring forwards. Regression coverage also rejects changed donors/maps, missing cells and missing comparisons even after rehashing.

Positive-control creation now checks runtime identity and uses the unchanged reviewed helper once per recipient. Its returned recovery error/validity, full sender set and donor provenance are preserved with fixed tolerance and separately padded calibration snapshots. Consumption recomputes the complete content digest, checks backing measurement, runtime/profile, donor/recipient provenance, padding geometry and sender coverage before emitting compact references. Fabricated references and stale error/validity/sender/donor/geometry/tolerance mutations now block before candidate forwards; wrong backend blocks before calibration. The independent fixture observed `6` forwards against expected `6` for `2` recipients, consistent with one reviewed three-forward pass per recipient. Output: `report85-runner-rereview-evidence.log`.

Additional report artifacts for the orchestrator, mirrored identically in the primary reports directory:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report85-runner-rereview-repro.py`: independent adapted fault and stale/fabricated-record attacks.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report85-runner-rereview-evidence.log`: fresh suite and attack output.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder` with thread limits:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_runner.py -p no:cacheprovider -q -rs
```

Observed: 39 passed; actual tiny CPU NNsight model executed. Output: `report85-runner-review-evidence.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_runner.py -p no:cacheprovider -q -rs
```

Observed: 38 passed, 1 known skip for NNsight 0.5.12, not substituted for the mgnp hook result. Output: `report85-runner-review-evidence.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python docs/research/specificity-ladder/reports/report85-runner-review-repro.py
```

The script first ran under its identical temporary path `/tmp/a3_runner_review_repro.py`. Both execution modes accepted the injected discrepancy; fabricated positive controls also passed. Output: `report85-runner-review-evidence.log`.

### Scoped re-review checks

The same runner-only pytest commands above were rerun against the updated source. Observed mgnp: 56 passed, including both actual tiny NNsight tests. Observed base: 54 passed and 2 known NNsight version skips. These are the focused runner suite counts, not the author's wider integration-suite totals. Output: `report85-runner-rereview-evidence.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python docs/research/specificity-ladder/reports/report85-runner-rereview-repro.py
```

The adapted attack script also ran from its initial identical temporary path `/tmp/a3_runner_rereview.py`, then from the durable path above in both environments. All attacks blocked; the unaffected measured baseline returned `valid=True`. Output: `report85-runner-rereview-evidence.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /sw/external/python/anaconda3/bin/python3.9 docs/research/specificity-ladder/reports/report85-runner-rereview-repro.py
```

## Execution evidence

- Job and cluster: local CPU pytest and injected synthetic script; no Slurm job.
- Exit codes: all commands returned `0`.
- Row counts: each synthetic scoring mode emitted `8` rows against expected `8`; fabricated production controls yielded `2` gate-valid rows against expected `2` recipients. Exact output: `report85-runner-review-evidence.log`.
- Baseline comparison: serial margins `[-6, -14]` repeated across cells versus packed margins `[-9, -21]`; replay error `0.0` in both modes. This is fault injection, not production model evidence.
- Provenance: no production `run_manifest.json` or immutable commit provenance; scientific results remain not yet verified. No production weights, GPU, paid API or notebooks used.

### Scoped re-review execution evidence

- Job and cluster: local CPU runner-only tests and injected re-attack script; no Slurm job.
- Exit codes: both updated focused suites and the independent script returned `0`.
- Rows and forwards: reviewed positive calibration returned `2` control records for `2` recipients; helper used `6` forwards against expected `6`; stale and fabricated consumption attacks used `0` extra scoring forwards. Source: `report85-runner-rereview-evidence.log` and the script's recipient loop.
- Baseline comparison: the unchanged fake-backend measured equivalence baseline returned `valid=True`; the original deliberately divergent serial/packed fault now raised the expected equivalence error. This establishes software guard behavior on injected data only.
- Provenance: no production manifest or immutable scientific run provenance. This re-review makes no production scientific claim.

## What is NOT done

No admission, CLI, fit, selection or summary orchestration review; no broad suites; no implementation fixes; no git; no author report read. Full frozen inventory binding remains the caller's obligation. The caller must also propagate the maximum replay-derived epsilon across the complete task/seed panel before selection/statistics; the runner explicitly returns this obligation. Those are not reported as Unit B defects.

At the initial review, actual packed NNsight equivalence and actual all-sender positive controls lacked coverage. The scoped re-review ran their new actual tiny-model coverage in mgnp; base retains its known NNsight mismatch skips. Production hardware/kernel coverage remains a later admitted pilot obligation.

## Open questions

Initial default was to return both blockers to the runner owner. The scoped re-review closes those blockers. Current default: continue the planned integration reviews. Packing reuse at this seam is deliberately limited to the exact tested scope; Unit E must implement and independently review the approved validation-to-assessment profile-reuse policy before model admission. Full frozen inventory binding and panel-wide epsilon propagation remain caller obligations. Artifact strict identity and HF symlink fixes remain with the separate Unit A owner.
