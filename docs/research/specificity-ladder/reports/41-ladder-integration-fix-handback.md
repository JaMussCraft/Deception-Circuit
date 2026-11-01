# Ladder adapter, runner and metric integration fixes

Agent: Codex Sol implementer. Status: handed-back.

## What changed

Fixed review 37/38 integration findings in the existing specificity-ladder worktree. Owned production files: `component_analysis/ladder_tasks.py`, `component_analysis/specificity_ladder.py`, `component_analysis/ladder_metrics.py`. Owned test changes: `tests/test_specificity_ladder_model.py`, `tests/test_ladder_metrics.py`. No git commands or subagents were used.

- Utility maps now carry requested/covered position counts, supported/gate-valid state, no-op and degeneracy flags. The actual IOI adapters produce maps accepted by the actual tiny NNsight runner for supported, unsupported and identity cases. Runtime-detected token identity is reflected in emitted donor provenance.
- Added explicit `task_resample` runner operation. It accepts only separate generated clean IOI donors with the same A/B names, a different prefix/id, prescribed seed, matching source hash/id/split provenance and matching full token layout. It remains distinct from H-derived `independent_resample`; relabeling its maps does not bypass H-source requirements. Unsupported own-task maps emit unsupported rows without needing fabricated donors.
- Unsupported F-twin rows no longer erase computable native D/H and I/user-neutral effects. Condition coverage remains explicit; unavailable F accuracy stays unavailable. Degenerate H-twin rows cannot establish H preservation or a standalone twin specificity pass.
- Optional independent donors retain supported-subset effects and uncertainty, requiring all paired conditions/streams and all three donor seeds for included mechanism ids. Results retain fixed assessment counts, explicit supported ids/counts and diagnostic labels. Unsupported coverage blocks the local gate; absent rows/seeds are rejected rather than silently altering the sample.
- Added separate assay coverage readiness. The local `point_pass`/`strong` fields retain same-operation evidence. IOI zero or other-operation evidence cannot replace its primary item-swap evidence. MMLU donor operations are rejected; MMLU floors are zero/H-mean only.

New result fields are `n_assessment_ids`, `assessment_sample_changed=False`, and `supported_subset` containing `ids`, `n_ids`, `diagnostic_only`, `required_conditions`, `required_donor_seeds`, and per-condition assessment/supported-id counts. Existing `coverage` now also contains `by_condition` counts.

Each native cell exposes `complete_assay_ready` and `assay_readiness={complete, missing_crossed_operations, MMLU, IOI}`. Required crossed operations are item swap, zero, H mean and H twin on matched supplied mechanism ids. H twin requires supported D/H/I/user-neutral coverage; predeclared unsupported F twin and H identity do not make coverage impossible. Optional independent donors do not enter this readiness. MMLU readiness requires exactly 32 unique clean rows for each zero/H-mean floor, matching ids across both operations, supported valid nondegenerate evidence, and separately reports each floor's additional errors and pass. IOI readiness requires supported nonidentity clean item-swap evidence. Floor coverage and floor success remain separate.

This is matrix-coverage readiness over supplied rows, not proof of frozen n=100 assessment, registered graders, replay/calibration completeness or provenance manifests. Task 4 must combine it with design hashes, expected counts, pilot/final restrictions and run-manifest validation before claiming completed A1.

## How verified

Tests were written before production changes. Initial mgnp regression run produced `7 failed, 21 passed`; failures covered missing map coverage/gate state, absent task-resample operation and missing descriptive/readiness/subset outputs. An additional metric regression demonstrated acceptance of an invented MMLU item-swap row before the applicability restriction.

Final commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_ladder_design.py tests/test_ladder_tasks.py tests/test_specificity_ladder.py tests/test_specificity_ladder_model.py tests/test_ladder_metrics.py -q
```

Observed: `75 passed in 18.03s`; pytest exited successfully. Log: `/tmp/ladder-integration-mgnp.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_ladder_design.py tests/test_ladder_tasks.py tests/test_specificity_ladder.py tests/test_specificity_ladder_model.py tests/test_ladder_metrics.py -q
```

Observed: `64 passed, 1 skipped in 30.93s`; pytest exited successfully. Log: `/tmp/ladder-integration-base.log`. The expected base NNsight module compatibility skip supplies no model-patch evidence. The pinned mgnp tiny-model module actually ran, including supported/identity/unsupported IOI maps and own-task donor provenance rejection.

## Execution evidence

Local CPU regression tests only. No Slurm job or cluster run, model 8B load, GPU, paid API or notebook execution occurred. No scientific assessment baseline, behavioral output row count, empirical specificity verdict or `run_manifest.json` is claimed. Commands used the required BLAS limits and disabled pytest cache. Test results and logs are listed above; no unrelated legacy suite was run.

Live Codex quota check during final verification: status `ok`, weekly used `12%`, remaining `88%`, pause threshold `80%`, `should_pause=false`, reset `2026-11-06T16:07:41Z`.

## What is NOT done

Task 4 CLI, wrappers, staging/manifests, actual tokenizer/cache preparation, grader registration, frozen scientific sampling and assessment scoring remain outside this hand-back. The lead owns review and explicit-file-list commits. No full A1 completion or general capability claim follows from tiny random-model tests or synthetic metric fixtures.

## Open questions

No blocker within the assigned fixes. The CLI assembler must treat local scientific gate, matrix-coverage readiness, MMLU floor pass and final frozen-run authorization as separate fields. It must enforce expected n=100/IOI counts, fixed sample identity and model/calibration provenance; this metric API cannot reconstruct absent frozen-design metadata from score rows alone.
