# Baseline test failures on the unmodified branch base (ticket 01, spec section 13.12)

Recorded 2026-10-19 by the ticket-01 implementer, before any edit by ticket 01 or ticket 02.
Worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets`,
branch `mechanism-datasets` at aef064a, clean working tree. Command run from the worktree root:
`pytest tests -q`.

Every later ticket compares its failures against these names. Results differ by about one fp32 ulp
across the two envs; that is not a regression.

## Base env (`/sw/external/python/anaconda3/bin/python`, py3.9, transformers 4.57.3)

Run with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`.
Totals: 8 failed, 1361 passed, 58 skipped (1427 collected).

- tests/test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py
- tests/test_deception_common.py::test_three_specs_registered
- tests/test_deception_common.py::test_pressure_pools_are_well_formed[ser]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[far]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[sdr]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[ser]
- tests/test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap
- tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms

## Job env mgnp (`/u/swong2/.conda/envs/mgnp/bin/python`, py3.12, transformers 5.13)

Totals: 8 failed, 1514 passed, 19 skipped (1541 collected).

- tests/test_benchmarks.py::test_mask_judge_kwargs_and_roles_match_evaluate_py
- tests/test_deception_common.py::test_three_specs_registered
- tests/test_deception_common.py::test_pressure_pools_are_well_formed[ser]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[far]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[sdr]
- tests/test_deception_common.py::test_clauses_never_reuse_an_item_word_or_a_predicate_word[ser]
- tests/test_deception_common.py::test_length_matching_narrows_the_cross_task_median_gap
- tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms

## Notes

- The two envs fail the same 8 names. `test_three_specs_registered` fails in both, as spec 14.C3 expects
  (it asserts old predicate words).
- The MASK repo-root test (`test_mask_judge_kwargs_and_roles_match_evaluate_py`) fails with
  `FileNotFoundError: the MASK checkout not found at
  /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mask/mask`. It resolves the MASK
  checkout beside the repo root, and from a worktree that path does not exist. The other 7 are the
  main-checkout names.
- Collected counts differ by env (1427 vs 1541) because some tests skip or are not collected under the
  base env's dependencies. Compare by name, not by count.
