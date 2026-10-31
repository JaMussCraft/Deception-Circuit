# Baseline test failures on the branch base (ticket 01, before any edit)

Worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis`, branch
`mechanism-analysis` at c24b5d9 (= main), untouched tree, 2026-10-25. Commands from the worktree root
(test path given absolutely):

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python -m pytest tests -q -rfE -p no:cacheprovider
/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests -q -rfE -p no:cacheprovider
```

Later tickets compare their failures by name against these lists. Memory says main has 7 baseline names, plus the
MASK repo-root test when run from a worktree (`test_mask_judge_kwargs_and_roles_match_evaluate_py`).

## Login base env (py3.9, transformers 4.57.3): 8 failed, 1726 passed, 58 skipped (409 s)

- tests/test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py  (worktree location)
- tests/test_deception_common.py::test_three_specs_registered
- tests/test_deception_common.py::test_pressure_pools_are_well_formed[ser]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[far]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[sdr]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[ser]
- tests/test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap
- tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms

## Job env mgnp (py3.12, transformers 5.13, nnsight 0.7.0): the same 8 names

Run on the untouched existing files (the first mgnp run's output file was deleted by a shared-tmp clean-up, so
it was re-run with BLAS threads pinned to 1 and ticket 01's two new test files ignored). 11 failed, 1961 passed,
19 skipped (761 s); 3 of the 11 are not baseline: they are in `tests/test_component_analysis_v2_dataloaders.py`,
a new file impl-02a added while the run was going (its red TDD tests), not on the branch base.

- tests/test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py  (worktree location)
- tests/test_deception_common.py::test_three_specs_registered
- tests/test_deception_common.py::test_pressure_pools_are_well_formed[ser]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[far]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[sdr]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[ser]
- tests/test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap
- tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms

So: the 7 main baseline names plus the MASK repo-root test, identical in both envs. Any other failure name in a
later run is new, apart from other tickets' in-progress test files (compare by file).
