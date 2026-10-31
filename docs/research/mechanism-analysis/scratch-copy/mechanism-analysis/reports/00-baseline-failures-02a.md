# Baseline failures recorded by impl-02a (branch base c24b5d9, worktree mechanism-analysis)

Recorded 2026-10-25 because `reports/00-baseline-failures.md` did not exist when 02a started. No existing source
file had been edited when collection ran. The only addition was a new test file, `--ignore`d here. Raw logs:
`/u/swong2/.claude/jobs/1c836bb8/tmp/impl02a/{base02a,mgnp02a}_baseline.txt`.

| env | result | wall |
| --- | --- | --- |
| base (`/sw/external/python/anaconda3/bin/python`, BLAS threads 1) | 8 failed, 1726 passed, 58 skipped | 464 s |
| mgnp (`/u/swong2/.conda/envs/mgnp/bin/python`) | 8 failed, 1879 passed, 19 skipped | 838 s |

The same 8 names in both envs:

- tests/test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py (the MASK repo-root test, worktree location)
- tests/test_deception_common.py::test_three_specs_registered
- tests/test_deception_common.py::test_pressure_pools_are_well_formed[ser]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[far]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[sdr]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[ser]
- tests/test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap
- tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms
