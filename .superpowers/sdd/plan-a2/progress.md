# SDD ledger — plan: docs/research/specificity-ladder/plan-a2.md

## Preflight scan

| Tasks | Shared interface and consistency | Ruling |
|---|---|---|
| 1 / 2 | Materializer build_manifest feeds wrapper | Freeze explicit schema before wrapper implementation; provisional D-only cannot qualify for full runs. |
| 2 / 3 | Timed receipt feeds projection | Count full process walltime and all pilot reservations, not only pruning time. |
| 1 / 3 | Matched cohort identity feeds fleet coverage | Same split IDs and requested counts across D/I; stale or missing I prevents fleet readiness. |
| 1 | CLI versus package imports | Use python -m, with --commit for full supplied revision; no worker git. |
| 2 | Frozen training config and task defaults | Explicit coarse gates, nls0.3, epochs500, lr0.03, batch7; record defaults for warmup/init. |
| 3 | 6-hour single threshold versus60-hour total | Both gates enforced;18 masks plus pilot costs must fit. |

Ruling: current user authorization covers offline preparation and subsequent measured pilot inside existing budgets; no automatic fleet launches.
Ruling: select seeds42,1,123 and nls0.3 from previous coarse convention, identical across conditions. These are prospective settings, not tuned results.
Ruling: unchanged clean-target objective is sufficient for the new neutral corruption; explicit data metadata prevents legacy condition selector ambiguity.

## Task 1

Dispatched to a2_materializer; no completed implementation yet.

Task 1: Materializer implemented and in independent review; focused32pass mgnp,31pass1cache skip base.

Task 1 fix round1 resumed: matched provenance P1 from review11; materializer_fix_resume implements a1-data-contract.md.
Task 2 resumed: wrapper_finish_resume fixes direct launch and strengthens admission/artifact checks.

Task 1: complete at 19f4895; reviewed matched admission, report17.
Task 2: complete at 77b6487; explicit training margin and actual stored-row checks reviewed23.
Task 3: initial projection complete at 77b6487, reviewed25/27; no measured timing yet.
Ruling: exact matched cohorts below200 accepted before training under existing plan review clause; see a2-cohort-ruling.json. Implement strict build/ID/count-bound support rather than unconditional bypass, then independently review. No cap or scientific gate changes.
