# Hand-back: Eligible-pool sample coordinates

Agent: Codex worker. Ticket: review correction for pure ladder design. Status: resolved.

## What changed

Orchestrator commit candidates from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_design.py`: replace inherited raw split-coordinate metadata with `eligible_pool_indices`, record ordered `eligible_pool_ids`, and set `join_on` to `instance_id`. Assessment IDs remain authoritative; no source-position mapping is implied.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_ladder_design.py`: regression reconstructs assessment IDs from eligible-pool indices after excluding an early source row, rejects the old field, and preserves invariance to source ordering.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/31-ladder-design-fix-handback.md`: this report.

Read the independent design review before applying its correction. No plan, sampler, baseline or builder files changed.

## How verified

Working directory: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_ladder_design.py::test_sample_indices_reconstruct_ids_only_with_recorded_eligible_pool -p no:cacheprovider -q
```

Observed before the fix: the new regression failed because `join_on` still claimed source split coordinates.

```bash
OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_ladder_design.py tests/test_sampling.py -p no:cacheprovider -q
```

Observed after the fix: all focused tests passed.

```bash
OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_ladder_design.py tests/test_sampling.py -p no:cacheprovider -q
```

Observed after the fix: all focused tests passed.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No real source pool was sampled or frozen. No model, GPU, notebook, API, scheduler, git operation or empirical assessment occurred. The focused suites cover this metadata correction; the whole repository suite was not rerun.

## Open questions

None for this correction. The later CLI should join rows by `instance_id` and use eligible-pool positions only together with their recorded ordered pool IDs.
