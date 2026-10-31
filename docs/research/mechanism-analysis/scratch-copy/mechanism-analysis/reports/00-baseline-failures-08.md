# Baseline failures recorded by impl-08 (ticket 08), before any ticket-08 edit

Worktree `mechanism-analysis` at c24b5d9, 2026-10-25, run before any ticket-08 file existed (both suites were
collected before `tests/test_inversion_v2.py` was written; neither log mentions it). It agrees name for name with
ticket 01's `reports/00-baseline-failures.md` (base env). Ticket 01's mgnp list was still pending at the time of
writing, so this file records the mgnp list too.

Commands (from the worktree root):

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python -m pytest tests -q -p no:cacheprovider
/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests -q -p no:cacheprovider
```

| env | failed | passed | skipped | time |
| --- | --- | --- | --- | --- |
| base (py3.9) | 8 | 1726 | 58 | 876 s |
| mgnp (py3.12) | 8 | 1879 | 19 | 1245 s |

The same 8 names in both envs (memory's 7 main-baseline names plus the MASK repo-root test from a worktree):

- tests/test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py
- tests/test_deception_common.py::test_three_specs_registered
- tests/test_deception_common.py::test_pressure_pools_are_well_formed[ser]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[far]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[sdr]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[ser]
- tests/test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap
- tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms
