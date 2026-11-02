# Hand-back 30: the rule-estimator flag in the B1 readings script (ruling R9)

Agent: ticket implementer (Claude Opus 5.5), session claude-230e4716. Task: the lead's go on hand-back 29's recommendation. Add `--rule-estimator` to `scripts/route_closure_readings.py`, defaulting to offline for O, O_q and M_q, with the forward values reported beside them. Status: resolved.

## What changed

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/route_closure_readings.py`. It gains `--rule-estimator {offline,forward}`, default `offline` (ruling R9).
  - **Where the rule is read.** O, O_q, M_q and the T1 verdict are read on the chosen estimator.
  - **The other estimator.** Its O, O_q and M_q go under `t1.beside`, with their intervals and the verdict they would give, labelled as not the rule.
  - **Fallback.** A file without the requested estimator uses the other one. The JSON says so in `t1.rule_estimator_fallback`, and the Markdown writes "(fallback)".
  - **Top-level JSON.** It records `rule_estimator` and `rule_estimator_ruling`.
  - **Markdown.** The T1 table gains an estimator column. A new table, "T1 on the other estimator, reported beside the rule", sits under it, and a note says the controls are always offline.
  - **Unchanged.** The controls (M_C1, M_C2, M_C3, M_S), the R1 label comparison (offline against offline) and T2 are as before. The docstring states R9.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_route_closure_readings.py`. The synthetic payload can carry different forward sums and can drop the offline rule arms.
  - Two tests now expect offline, the new default.
  - Six tests are new: the default setting, the forward setting, the fallback both ways, refusal of an unknown estimator with the parser default, and `main` naming the estimator in both the JSON and the Markdown under both settings.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_route_closure_t1.py`. The test that the readings script reads what `run()` writes had asserted the old forward default. It now checks the offline default against the run's `M_q_offline` and offline O, and the forward setting against the run's forward summary.
- Committed by the orchestrator from the worktree: this file.

`component_analysis/route_closure.py`, the JSON files and `docs/research/instructed-route/results/` were not touched.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_route_closure_readings.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_route_closure_readings.py
```

Observed: 24 passed on mgnp, and 24 passed on base 3.9.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_route_closure_readings.py tests/test_route_closure_t1.py tests/test_route_closure_t2.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_route_closure_readings.py tests/test_route_closure_t1.py tests/test_route_closure_t2.py
```

Observed: 69 passed on mgnp. On base 3.9, 44 passed and 25 were skipped (the nnsight 0.7.0 model tests), with 3 warnings.

The script was also run on the two smoke JSON files, with the output sent to the job's temporary directory and not to `results/`:

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/route_closure_readings.py outputs/_analyses/instructed-route-b1/smoke/far/Ct__leaf/far_v2/route_closure/route_closure.json outputs/_analyses/instructed-route-b1/smoke/ser/Ct__leaf/ser_v2/route_closure/route_closure.json --out-dir /u/swong2/.claude/jobs/230e4716/tmp/r9check
```

Observed in the T1 rule table:

| task | estimator | O | M_q | verdict |
|---|---|---|---|---|
| far_v2 | offline | 0.744 | 0.369 | bypass |
| ser_v2 | offline | 0.780 | 0.472 | bypass |

The beside table shows the forward values:

| task | O | M_q |
|---|---|---|
| far_v2 | 0.732 | 0.376 |
| ser_v2 | 1.033 | 0.414 |

These match hand-back 29's numbers.

## Execution evidence

Not applicable: no runs. The script run above is a CPU check of the output format on the existing smoke JSON files. It wrote nothing outside the job's temporary directory, and it makes no new claim about job 50105613.

## What is NOT done

- The readings in `docs/research/instructed-route/results/b1-smoke/` were not regenerated, as instructed. They still show the forward estimator as the rule.
- R9 was not written into `spec.md`; the lead is recording it.

## Open questions

1. **Should the smoke readings be regenerated under R9?** Regenerating them would make `results/b1-smoke/` match the ruling. Default: leave them as the record of what the smoke read before R9. The 100-id readings will be the first produced under R9.
2. **Should a missing estimator fall back silently?** When the requested estimator is absent the script uses the other one and marks it, rather than refusing. Under R9 that only happens if a task job is run with `--route-sweep forward`, which the batch files do not do. Default: keep the marked fallback.
