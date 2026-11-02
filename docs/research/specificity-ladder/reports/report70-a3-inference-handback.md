# Hand-back: A3 pure direction inference and conditional power

Agent: Codex Sol worker. Ticket: approved `plan-a3.md`, Task 2b inference/power. Status: handed-back.

## What changed

Orchestrator-owned worktree files:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_statistics.py`: pure normalized outcome schema, exact triplet inference, shared cluster uncertainty, and validation-only conditional power.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a3_statistics.py`: synthetic contracts for inference, covariance linkage, denominator weakness, calibration exclusions, correlated collateral, and power edge cases.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report70-a3-inference-handback.md`: this hand-back.

Identical primary hand-back: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report70-a3-inference-handback.md`.

The module docstring defines the consumer contract. Mechanism observations retain both designation streams; intact tensors have shape `[3,N,2]`, patched tensors `[A,3,N,2]`. Utilities retain prompt IDs with intact shape `[3,P]` and patched shape `[A,3,P]`. Seeds are ordered `[42,1,123]`. Axes are `learned` followed by numbered nulls. Assessment requires the full null panel; calibration requires the separate validation null panel. Both MMLU floors use the same fixed prompt IDs. `MMLU_zero` and `MMLU_h_mean` denote subspace zero and centered-H interventions, not whole-head ablation. Missing assessment MMLU blocks a complete point pass; missing validation MMLU labels power conditional on the utility guard passing.

Public functions are `summarize_direction_outcomes`, `simulate_conditional_power`, `triplet_statistic`, `compare_triplets`, `holm_two`, `draw_pressure_clusters`, and `inject_correctness_loss`. The inference and power defaults, strict percentile index, tied rank probability, two-task Holm thresholds, effect grid, and axis expansion implement the approved prospective settings in `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/plan-a3.md`. Gates, null comparison, Holm decision and confidence intervals remain distinct report fields.

Canonical exact wording clusters are jointly resampled within task-incidence strata. Every member ID travels with its occurrence, every task weights its expanded IDs equally, and seeds are never resampled. Utility prompts share draws across tasks, seeds, axes and MMLU operations. Separate occurrence keys allow repeated bootstrap copies to receive distinct Bernoulli loss uniforms while preserving all cross-task linkage. Task/seed-specific intact accuracy determines each loss threshold. Observed calibration null outcomes receive no synthetic effect injection.

Original invalid denominators and infeasible collateral settings yield undefined power. Bootstrap-invalid denominators remain nonrejections in the full replicate denominator and have separate counts. Joint any/both probabilities are undefined if either original task cell is ineligible. The other task still competes in the frozen Holm family with the ineligible task assigned `p=1`. Reports include Wilson binomial Monte Carlo intervals, per-seed/any-seed/all-seed gate failures, strict null pass frequencies, calibration coverage, failed-null counts and tested-neighbor detectability brackets. Internal failed statistics use negative infinity; public reports use `null` plus failure flags/counts and accept strict JSON serialization.

## How verified

Tests were written before the new module. The first collection reported the missing `a3_statistics` import. Additional red-to-green regressions covered missing failure-frequency output and a nonmonotone detectability curve whose earliest detectable tested fraction had no lower neighbor.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_statistics.py tests/test_ladder_metrics.py -p no:cacheprovider -q
```

Observed:

```text
41 passed in 2.19s
```

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_statistics.py tests/test_ladder_metrics.py -p no:cacheprovider -q
```

Observed:

```text
41 passed in 2.72s
```

The owning statistics file supplies the new synthetic tests; existing ladder metric tests supply regression coverage. The complete repository suite was not run by this worker.

The following synthetic-only smoke commands exercised unchanged production replicate defaults. Each ran with BLAS, OMP and MKL threads pinned to one.

```python
import runpy, time, json
from component_analysis.a3_statistics import simulate_conditional_power
make = runpy.run_path('tests/test_a3_statistics.py')['panel']
start = time.monotonic()
r = simulate_conditional_power(make())
json.dumps(r, allow_nan=False)
print({'n_rep': r['n_rep'], 'n_scenarios': len(r['scenarios']),
       'seconds': round(time.monotonic()-start, 3), 'json_strict': True})
```

Observed on mgnp:

```text
{'n_rep': 2000, 'n_scenarios': 60, 'seconds': 6.499, 'json_strict': True}
```

```python
import runpy, time, json
from component_analysis.a3_statistics import summarize_direction_outcomes
make = runpy.run_path('tests/test_a3_statistics.py')['panel']
start = time.monotonic()
r = summarize_direction_outcomes(make(200, 'assessment'))
json.dumps(r, allow_nan=False)
print({'n_boot': r['bootstrap']['n_boot'], 'tasks': len(r['tasks']),
       'seconds': round(time.monotonic()-start, 3), 'json_strict': True})
```

Observed on mgnp:

```text
{'n_boot': 2000, 'tasks': 2, 'seconds': 5.33, 'json_strict': True}
```

These timings describe only tiny synthetic fixtures, not experimental cost forecasts. Scenario tensors are vectorized within a replicate; expanded null panels index already computed axis statistics rather than duplicating outcome arrays across all replicates.

## Execution evidence

- Job and cluster: no Slurm, GPU, API, model, notebook or scientific analysis run. Local CPU pytest and synthetic smoke commands are recorded above.
- Exit state: both final pytest commands and both synthetic smoke commands returned `0`.
- Row counts: synthetic fixtures contain `4` mechanism IDs per task with `2` streams, `3` seeds, `4` IOI prompts and `32` MMLU prompts per floor. Calibration contains `33` axes including learned; synthetic assessment contains `200` including learned. The dedicated unequal-cluster threshold test expands to `20` IDs per task. The tests passed the expected tensor-shape and membership assertions.
- Baseline assertion: the raw-ratio test observes intact D mean `2.0` and patched D mean `1.0`, matching synthetic expectations `2.0` and `1.0`; fractional removal is `0.5`.
- Provenance: no experimental `run_manifest.json` exists because no scientific run occurred. The worker did not run git; the orchestrator owns the eventual source commit. This is implementation test evidence, not a provenance-complete empirical finding.

## What is NOT done

No direction fitting, real calibration, real assessment, power claim about the experiment, scientific continuation decision, model loading or job submission occurred. The module consumes explicit normalized complete arrays; the production consumer must bind those arrays to frozen source receipts, task IDs, utility IDs, validation-selected sites and replay tolerances. Declaring a tensor `split='validation'` cannot authenticate its origin; the pure layer additionally requires explicit assessment exclusions and rejects overlap and mixed/unknown keys.

The additive-noise power model is conditional on frozen sites, validation residuals, original validation gaps and the cached orientation panel. Its expanded null distribution is an approximation and cannot support an unconditional discovery-power claim. Missing disjoint validation MMLU produces a conditional-guard limitation, never an invented validation utility set. Synthetic learned margins do not predict D/I token accuracy; no such accuracy is fabricated. Assessment retains observed D/I correctness.

No SDR, nuisance, neuron, edge or mask hypothesis is added to the confirmatory family. No other worker's code or any RS state, worklog or ledger was edited. No independent code review was performed by this worker.

## Open questions

None blocking this pure-module hand-back. Default next action: root reviews the three owned files, then integrates an outcome-to-schema adapter in its own scope. Production data lineage, source hashes, frozen exclusions, supported operation coverage and actual calibration admission remain the consumer's responsibility.
