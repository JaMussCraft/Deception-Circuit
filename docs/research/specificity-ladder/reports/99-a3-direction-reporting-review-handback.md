# Hand-back 99: Pure direction reporting review

Agent: Codex independent statistical/code reviewer. Status: handed-back.

## What changed

Review only. No implementation or test source changed. The author hand-back was not read. Reviewed the new reporting module/tests against accepted integration work unit F, actual runner/selection row contracts and reviewed pure statistics.

- Worktree report: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/99-a3-direction-reporting-review-handback.md`.
- Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/99-a3-direction-reporting-review-handback.md`.

Closure verdict: both original bounded findings are closed after independent narrow re-review. The replay validator now consumes the reviewed matched-batch validity attestation, finite nonnegative measured maxima and replay-derived epsilon without an absolute-only ceiling. A shared frozen-profile guard binds primary rows and every diagnostic input, including primary baselines and reused MMLU floors, to the selected model, revision and code-source digest. No new breakage was identified within this scoped closure. The original findings below are retained as history; neither remains open.

### Closed P2: Reporting rejected replay results accepted by the reviewed runner

Location: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_direction_reporting.py:187`, compared with `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_direction_runner.py:965`.

Reporting requires every measured replay maximum to be at most `1e-5` absolutely. The runner's actual acceptance criterion is `torch.allclose(...,atol=1e-5,rtol=1e-5)` plus exact argmax agreement. It retains the measured absolute maximum and derives epsilon from that measurement. A replay difference greater than the absolute tolerance can therefore be valid under the approved relative tolerance, yet reporting refuses the emitted row. This blocks valid primary panels and diagnostics after successful runner checks.

Reproduction: take a valid synthetic row, set each stored replay maximum to `2e-5` and epsilon to `2e-4`. A margin pair `[2.0]` and `[2.00002]` passes the runner comparator with unchanged argmax. `_validate_row` rejects that row with `missing/failed measured replay controls`, despite adequate epsilon. Both interpreters produced this mismatch in the independent probe.

Required correction: preserve the reviewed absolute-plus-relative acceptance contract. Do not replace it with an absolute-only ceiling. Reporting may validate finite nonnegative measured errors and the epsilon lower bound, with actual comparator/argmax evidence supplied through the accepted runner/control lineage. Add a regression using a replay error accepted by the relative tolerance. Because stored maxima can cover a whole batch, avoid inventing a per-row relative comparison from a different scale.

### Closed P2: Diagnostic rows were not bound to the selected production model/source identity

Location: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_direction_reporting.py:489`, also the reused diagnostic floors at line `509`. The existing correct primary guard is at line `260`.

Primary packing compares each noninjected row's model, model revision and code-source digest against `selected['inventory_identity']`. Diagnostic assembly only calls `_validate_row`, which checks that the row's profile hashes itself and agrees with its own positive-control reference. It never compares those fields with the frozen selected identity. Identical intact values and valid source tokens do not establish the same model/source execution. As a result, nuisance, secondary and steering tables can be marked complete under a different model/revision/code profile, with potential effects on diagnostic readiness or the framing interpretation.

Reproduction: construct a noninjected FAR design with complete original mechanism/utility sizes, all selected seeds and immutable axis descriptors. Supply learned baseline rows with the correct selected model profile and exact source/label provenance. For all positive learned-steering rows, substitute a different model/revision/source digest and recompute each row's profile ID and own positive-control profile reference. Preserve the exact source-derived keys, axes, intact values, finite observations and valid flags. `summarize_direction_diagnostics` returns `status='complete'` for every affected seed's positive-steering group instead of rejecting the frozen-identity mismatch. The strengthened independent probe also validates the learned baseline rows through the production row guard before diagnostic assembly.

Required correction: share the primary frozen-profile identity validation across every production diagnostic observation, including reused same-axis MMLU floors. Add regressions that alter a diagnostic model, revision and code digest independently while keeping the profile self-hash internally valid. This is an in-memory identity check available to the pure module, separate from the runtime reader's responsibility to attest actual files and current registries.

### Boundaries that behaved as intended

Primary expected keys are independently reconstructed from frozen source rows, selected sites, ordered axes, all seeds and paired mechanism streams; both MMLU operations remain required. Missing/duplicate primary coverage, changed source labels/tokens and inconsistent intact baselines reject rather than shrinking the panel. Secondary/steering observations cannot replace primary rows. FAR/SER alone enter Holm; descriptive SDR reuses the reviewed seed gates, strict null/rank logic and paired cluster/prompt bootstrap without a Holm field.

Calibration excludes assessment aliases and exact prompt bytes, requires validation sources and rejects mixed assessment outcome rows. Canonical source D wording is retained for shared cluster inference. Missing diagnostic/probe observations remain explicitly incomplete; unfitted nuisance requires a reason/receipt, and passing primary nuisance marks framing ambiguity. Signed steering remains raw descriptive output.

The pure summary explicitly refuses `final=True`. Its reference hash/length checks are for canonical JSON payload bytes, and optional runtime artifact evidence is retained separately. This is clearly documented and is not a claim that canonical serialization proves the bytes or completion state of an on-disk file. Runtime still owns actual file-byte readers, inventory completion, current protected access and finalization.

IOI's original `split='generated'` and validation `analysis_split='validation'` remain distinct: reporting accepts the former source label with the latter analysis label and rejects generated validation rows missing the analysis label. The already identified canonical-prepare annotation defect remains a runtime/preparation integration obligation; reporting should not relabel the source split to hide it.

## How verified

All commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`. Independent synthetic reproduction script: `/tmp/a3_reporting_review99_probes.py`. It uses only local synthetic fixture factories and CPU dictionaries/tensors; no scientific dataset or production model is loaded.

```bash
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python /tmp/a3_reporting_review99_probes.py
```

```bash
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 /tmp/a3_reporting_review99_probes.py
```

Both initial probes exited zero and printed:

```text
runner_relative_replay_accepts: True
reporting_replay_accepts: False; missing/failed measured replay controls
wrong_model_steering_status: [(42, 'complete'), (1, 'complete'), (123, 'complete')]
generated_ioi_requires_validation_analysis_split: True
```

The probe was subsequently strengthened so learned baseline rows carry and pass production validation with the correct frozen profile; positive steering retains the wrong profile. That strengthened mgnp run has the same output.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_reporting.py -k 'scalar_runner_oracle or validation_excludes or sdr_same or original_ioi' -p no:cacheprovider -q
```

Observed: four passed and the other tests were deselected; exit zero. These focused contracts cover scalar-estimator parity, assessment alias/prompt exclusion, descriptive SDR inference and IOI source/analysis split handling. Passing existing targeted tests does not resolve the adversarial failures above. The complete author suite was not repeated.

### Independent closure checks

Inspected only the changed replay validator, shared frozen-profile helper and call sites, and the newly added report-specific regressions. The guard applies while indexing all diagnostic input rows, so baseline reuse and MMLU-floor reuse do not bypass it. The replay fix preserves the runner's batch-scale evidence rather than inventing a per-row comparator.

```bash
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python /tmp/a3_reporting_review99_closure.py
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 /tmp/a3_reporting_review99_closure.py
```

Both independent closure probes exited zero with:

```text
runner_relative_replay_accepts: True
reporting_replay_accepts: True
wrong_model_steering_rejected: changed production model/source profile
generated_ioi_requires_validation_analysis_split: True
```

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_reporting.py -k 'review99' -p no:cacheprovider -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_reporting.py -k 'review99' -p no:cacheprovider -q
```

Observed closure subset: eight passed in each interpreter; exit zero. The tests exercise both batch-relative margin scales, too-small epsilon, invalid replay flags, and independent model/revision/source-digest mutations in steering and reused-floor inputs. No full suite or broader review was repeated.

An initial probe invocation omitted the worktree import path and failed before running with `ModuleNotFoundError`; subsequent commands set `PYTHONPATH=.` explicitly. No test/source fix was needed.

## Execution evidence

- Local synthetic CPU probes and focused pytest only; no Slurm or model run.
- Initial adversarial probes exited zero in both interpreters. The strengthened mgnp probe exited zero. Initial focused pytest exited zero with all four requested tests passing. Closure probes exited zero in both interpreters, and the closure regression subset passed all eight cases in each interpreter.
- Synthetic comparator baseline: the approved relative replay comparison accepts the displayed margin pair, while reporting rejects its measured-error row. Frozen-profile baseline rows pass production validation, while wrong-profile steering groups are still reported complete.
- Scientific row counts, model baseline, job ID and model-run provenance manifest: not applicable. No scientific inference or production power result is claimed.

All numerical literals above are code locations/identifiers, frozen seed/tolerance settings, or explicit synthetic reproduction inputs. No new efficacy, timing or power estimate is presented.

## What is NOT done

No fixes, full-suite rerun, artifact reader/runtime finalization review, production assessment, conditional-power estimate, model loading, GPU, API, scheduler execution, git, subagents or notebooks. Runtime must still attest actual artifact file bytes/completion, live access registries and complete workload execution. The pure module's explicit nonfinal boundary is appropriate and does not itself need broadening.

## Open questions

No remaining blocker from these two findings. Default: accept their bounded closure while retaining the runtime finalization/file/registry obligations above. Keep the separate canonical IOI analysis-split preparation correction assigned to the runtime owner. No new scientific ruling is needed.
