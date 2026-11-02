# Hand-back: A2 ladder pipeline

Agent: Codex worker. Ticket: approved bank/scoring and summary tasks in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a2-analysis.md`. Status: handed-back.

## What changed

Orchestrator-owned commit files, all inside the assigned worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a2_pipeline.py`: distinct freeze, bank, score and summarize stages around unchanged A1 scoring functions.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a2_pipeline.py`: synthetic contracts, actual tiny NNsight bank/scoring integration and actual shell-wrapper dry-run.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/jobs/specificity_a2.sh`: staged execution wrapper; no submission or reservation capability.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report100-a2-ladder-pipeline-handback.md`: this report, mirrored to `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report100-a2-ladder-pipeline-handback.md`.

No existing A1 runner, design, metrics, grader, generic hooks or shared model source was edited. The comparison module is reused unchanged.

Freeze requires the complete audited comparison and validates the original A1 selected artifact and mandatory sidecar through unchanged `read_selection`. The new receipt binds all source receipts, comparison, A1 design/selected bytes and sidecar, source/utility hashes, model/tokenizer identity, execution commit, code, graders and protected registries. A1 ancestor identity remains distinct from future A2 execution identity. Group source is `matched_pressure_twin`, source kind is `twin_trained_mask_difference`, and independently trained SDR groups do not inherit the historical descriptive-source qualifier.

The source-record input file is a JSON object with `records` containing all original comparison-module `audit_source` input records. The comparison file is the unchanged comparison-module `write_comparison` output. Freeze and every resumed stage re-audit the complete source domain; incomplete training cannot freeze scientific memberships. No training memberships or assessment outcomes were read during implementation.

Bank stage recollects the full required typed union from the exact frozen original-H train/validation IDs and both streams. It never relabels the old partial A1 bank, zero-fills keys, uses I/test banks or changes source IDs. Contracts bind source rows/tokens, stream token counts, pooling, coverage and numerical environment, including library versions, backend precision settings and CPU threads. Bank/scoring execution requires matching dtype, device class and GPU architecture. Every H-mean row carries a separate A2 owner plus file/content/bank/contract hashes.

Scoring composes unchanged `score_cell`, `collect_h_mean_bank`, batching and positive-control calibration. All crossed operations, IOI/MMLU cells, alias memberships and donor maps remain explicit. Identical memberships deduplicate computation while retaining every seed alias; canonical JSON key order cannot change the predeclared seed order. Empty and unsupported rows remain visible. Stage directories publish atomically with completion manifests, and consumers require their exact runtime/content links. CPU dry-run never loads tokenizer or model weights.

Summary uses unchanged paired pressure-cluster metrics and reports each primary numerical rule, complete assay readiness, both joined MMLU floors, seed ranges, typed counts, containment numerators/denominators, every membership table and pre-registered MLP prediction, and native training-cohort metrics separately. Robust task pass requires every seed's specificity gate plus every primary mixed Jaccard. Strong evidence remains a separate label. Collection completeness and scientific readiness remain separate: a valid empty set can fail necessity; an unsupported required primary cell is blocked/uninterpretable. An unsupported predeclared F H-twin diagnostic does not shrink or invalidate the required primary assay. A failed positive control aborts rather than becoming a scientific null. A readable per-seed TSV accompanies summary JSON.

## How verified

Focused regression command on base:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a2_pipeline.py tests/test_a2_mask_comparison.py tests/test_ladder_design.py tests/test_ladder_metrics.py tests/test_specificity_ladder.py tests/test_specificity_ladder_calibration.py tests/test_specificity_ladder_model.py tests/test_specificity_ladder_cli.py -q -p no:cacheprovider > /tmp/a2-pipeline-base.log 2>&1
```

Observed: `222 passed, 3 skipped`, exit zero. Source: `/tmp/a2-pipeline-base.log`. The skips concern the pinned NNsight version; no focused regression failure occurred.

Focused regression command on mgnp:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a2_pipeline.py tests/test_a2_mask_comparison.py tests/test_ladder_design.py tests/test_ladder_metrics.py tests/test_specificity_ladder.py tests/test_specificity_ladder_calibration.py tests/test_specificity_ladder_model.py tests/test_specificity_ladder_cli.py -q -p no:cacheprovider > /tmp/a2-pipeline-mgnp.log 2>&1
```

Observed: `236 passed`, exit zero, no skips. Source: `/tmp/a2-pipeline-mgnp.log`. Actual tiny NNsight hook tests ran here.

After final publication, serialization-order and numerical-environment hardening, the changed A2 suite was rerun on both interpreters:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a2_pipeline.py -q -p no:cacheprovider > /tmp/a2-pipeline-final-base.log 2>&1
```

Observed: `25 passed, 1 skipped`, exit zero. Source: `/tmp/a2-pipeline-final-base.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a2_pipeline.py -q -p no:cacheprovider > /tmp/a2-pipeline-final-mgnp.log 2>&1
```

Observed: `26 passed`, exit zero, no skips. Source: `/tmp/a2-pipeline-final-mgnp.log`. Warnings concern external pandas/bottleneck, transformers cache, TensorFlow alias and astor deprecations, depending on interpreter.

```bash
/u/swong2/.local/bin/ruff format component_analysis/a2_pipeline.py tests/test_a2_pipeline.py
/u/swong2/.local/bin/ruff check component_analysis/a2_pipeline.py tests/test_a2_pipeline.py
bash -n scripts/jobs/specificity_a2.sh
```

Observed: formatting completed; `All checks passed!`; shell syntax exited zero. The actual wrapper dry-run is executed by `test_actual_wrapper_cpu_dry_run_with_tiny_injected_artifacts` in the final suite, with fixture source/access injection and forbidden tokenizer/weight loaders.

Test-first failures were observed for missing module/functions, omitted required operations, rehashed seed-membership/bank/alias drift, completion-marker absence, publication fields, serialization seed order and missing numerical-environment identity before their implementations. Counterexamples cover a passing primary numerical cell with a failing joined MMLU floor, unstable/all-pass seeds, missing seeds, empty groups, failed controls and unsupported required versus diagnostic cells.


Review follow-up: the typed-bank-width and empty-group completeness blockers in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/101-a2-ladder-pipeline-review-handback.md` are addressed in the owned A2 module and tests. Exact bank vector shapes now derive independently from a frozen pinned local model configuration, distinguishing head output width from whole-MLP hidden width. Config content/file identity is frozen and rechecked; injected fixtures use their authoritative prepared model config. The loaded model geometry must match before collection or scoring. Scalar, short, wrong-type, nested, boolean and nonfinite vectors are rejected before model work. Bank-declared widths cannot override the configuration-derived contract.

Empty-group completion now additionally requires supported, assay-valid, finite evidence for every required crossed, no-op/control and utility cell. Expected empty-patch degeneracy is allowed; the predeclared unsupported F H-twin and optional independent-donor diagnostics remain excluded from required evidence. A valid empty set still fails necessity. Unsupported or invalid required evidence produces blocked/uninterpretable accounting with incomplete scientific assessment, including failures in the zero, H-twin, H-mean, no-op and utility arms.

Test-first review regressions initially reported `11 failed, 7 passed`, with the already-passing cases demonstrating existing type/nonfinite guards. Source: `/tmp/a2-review101-red.log`. Final covering commands were:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a2_pipeline.py -q -p no:cacheprovider > /tmp/a2-review101-base.log 2>&1
```

Observed: `43 passed, 1 skipped`, exit zero. Source: `/tmp/a2-review101-base.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a2_pipeline.py -q -p no:cacheprovider > /tmp/a2-review101-mgnp.log 2>&1
```

Observed: `44 passed`, exit zero, no skips. Source: `/tmp/a2-review101-mgnp.log`. Actual tiny original-H bank/scoring hooks and the fixture-driven actual wrapper dry run executed. Ruff formatting/checking passed after these changes. Canonical A1 sources remain unchanged.

The unchanged independent tiny-hook scalar probe was rerun on mgnp through this rejection-check wrapper:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. /u/swong2/.conda/envs/mgnp/bin/python - <<'PYCODE'
import runpy
try:
    runpy.run_path('/tmp/a2_review101_scalar_hooks.py', run_name='__main__')
except ValueError as error:
    assert str(error) == 'nonfinite/malformed bank vectors or wrong typed shape', str(error)
    print('EXPECTED_SCALAR_BANK_REJECTION_BEFORE_SCORING', str(error))
else:
    raise AssertionError('independent scalar bank probe was accepted')
PYCODE
```

Observed exit zero: `real collected widths [64]`, followed by `EXPECTED_SCALAR_BANK_REJECTION_BEFORE_SCORING nonfinite/malformed bank vectors or wrong typed shape`. The previously accepted scalar replacement is rejected before scoring.

The unchanged independent pure probe at `/tmp/a2_review101_probes.py` was also run through an equivalent exact-error wrapper on both supported interpreters. Both exited zero. The valid empty baseline retained `failed_necessity_empty_group True False`; unsupported required zero and H-twin cases each changed to `blocked_uninterpretable False False`. Its malformed scalar bank then raised the required typed-shape rejection. This remains synthetic CPU evidence without a scientific effect or hardware claim.

## Execution evidence

- Local CPU commands: pytest commands above. No Slurm, GPU, production-weight or scientific assessment execution occurred.
- Exit codes: both focused regression suites, both final changed-file suites, Ruff and shell syntax exited zero.
- Tiny hook coverage: complete expected rows, positive controls, every seed alias and original-H bank source/token counts are asserted by `test_tiny_actual_hooks_new_bank_scoring_and_references` in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a2_pipeline.py`. Its mgnp test ran without skip.
- Baseline/control assertions: unchanged canonical no-op and all-sender donor-logit controls execute on the tiny native model. No baseline competence, effect size, BF16 hardware parity or GPU timing result is claimed.
- Provenance: no scientific `run_manifest.json` or scientific execution commit was produced. Test artifacts are injected CPU fixtures and cannot finalize production results.

## What is NOT done

Independent acceptance of the review follow-up and orchestrator commit are pending. No full scientific source comparison was attempted while the fleet remains incomplete. No original-H scientific bank, assessment scoring, production summary, protected/EVAL5 scoring, API call, notebook execution, GPU reservation/submission, ledger mutation or git command was performed.

Operational execution remains gated on the complete audited training-source domain, current A1 receipts/access/grader/source checks, a measured cost sheet covering all required banks/groups/controls/utilities and overhead, and root's budget admission. The remaining analysis allowance is about 40.78 GPU-hours under the accepted plan; no CPU timing is used to justify a GPU reservation. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a2-analysis.md`.

CUDA/BF16 numerical behavior and actual cost remain untested here. Production execution must preserve the canonical strict control tolerances. No optional core, typed-subgroup or parent/shared/reverse ladder runs were added; they require separately frozen scope and cost admission. There is no efficacy filter, post-hoc seed selection or budget transfer.

## Open questions

No scientific design question remains for this implementation. Independent re-review of the bank-shape and empty-evidence fixes remains with root. Default: root independently reviews the explicit owned file list, then freezes measured operational costs before admitting any future execution. Complete report publication can retain blocked/unsupported statuses, but never turns them into a completed scientific specificity assessment or a robust pass.
