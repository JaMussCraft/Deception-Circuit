# Baseline failing tests on the branch base (5b61031), both environments

Recorded 2026-10-13 by the orchestrator on a fresh `format-control` worktree at
5b610314d16344dfa25f57eb6d153ee50806c759, before any edit.

Commands (run from the worktree root):

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python -m pytest tests/ -q -p no:cacheprovider --no-header -rf
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/ -q -p no:cacheprovider --no-header -rf
```

(`/u/swong2/.conda/envs/mgnp/bin/python` is the `mgnp` interpreter; calling it by
path is equivalent to `conda activate mgnp` and avoids `source` in hook-checked
commands.)

| env | result |
| --- | --- |
| login base (py3.9, transformers 4.57.3) | 8 failed, 584 passed, 20 skipped |
| mgnp (py3.12, transformers 5.13) | 8 failed, 585 passed, 19 skipped |

The same 8 names fail in both envs:

- tests/test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py  (worktree-location artefact: `--benchmark-repo-root` defaults to the parent of the checkout)
- tests/test_deception_common.py::test_three_specs_registered
- tests/test_deception_common.py::test_pressure_pools_are_well_formed[ser]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[far]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[sdr]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[ser]
- tests/test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap
- tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms

"No new failures" is judged by name against this list, never by count.
