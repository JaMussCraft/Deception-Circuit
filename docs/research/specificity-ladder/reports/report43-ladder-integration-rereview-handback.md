# Handback: ladder runner and adapter integration re-review

Agent: Codex Sol reviewer. Status: handed-back.

## What changed

Review only; no production edits, git commands or subagents. Read updated `component_analysis/ladder_tasks.py`, `component_analysis/specificity_ladder.py`, `component_analysis/ladder_metrics.py` and their tests, plus the prior independent adapter review. The author's fix report was not read. CLI implementation is outside this review.

Owned report: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report43-ladder-integration-rereview-handback.md`. Full mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report43-ladder-integration-rereview-handback.md`.

**Verdict: no remaining blocker found for the required runner/adapter integration in this scope. One optional diagnostic reporting gap remains.** This is not an empirical specificity result or authorization to score an assessment.

The earlier findings are addressed:

- `ladder_tasks._map` now supplies requested/covered positions, validity, no-op and degeneracy fields. Actual adapter-generated IOI item-swap maps reach the native shared-hook runner on a random tiny Llama. Supported, identity and unsupported maps retain their intended behavior; identity cannot establish collateral preservation.
- `specificity_ladder._check_map` has dedicated `task_resample` semantics. It requires IOI clean-to-clean different-instance generated donors, matching names, source hash/id/split, prescribed donor seed matching generation provenance, a different prefix and compatible explicit layouts. It rejects forged sources and does not relabel own-task donors as H-derived donors.
- `ladder_metrics` retains condition-level coverage and computable D/I estimates after unsupported F twin alignment. H identity remains nontrivial=false and cannot certify H preservation. The frozen assessment count remains visible; independent-resample support requires complete conditions/streams/seeds for each diagnostic recipient, with a supported-subset label and no primary-sample mutation.
- Local scientific gates remain separate from `assay_readiness`/`complete_assay_ready`. Readiness checks required crossed mechanism operations, primary IOI item swap, and distinct fixed MMLU zero/H-mean floor cells with matching IDs. Missing MMLU blocks complete readiness while leaving a valid local primary estimate reportable. Unsupported F twin alignment is allowed only as its documented descriptive limitation. No invented MMLU item swap or blending of interventions supplies the primary gate.

**Minor: optional IOI task-resample outcomes disappear from the summary.** At `component_analysis/ladder_metrics.py:122-126`, utility rows are stored by group/operation, but output cells are driven exclusively by mechanism operations. There is no mechanism `task_resample` cell, so its IOI rows never appear in the returned summary. A standalone optional diagnostic returns an empty cell list; adding those rows to a primary item-swap assay leaves only its item-swap cell. Its seed-level outcomes, between-seed range and own-task paired uncertainty therefore remain available only in raw rows, rather than in the summary API. This does not block required IOI item swap or full required assay readiness. Default: add explicitly separate own-task utility diagnostic output, or mark that optional summary deferred. Do not attach it as H-derived robustness or primary collateral evidence.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`, with BLAS threads pinned.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_specificity_ladder.py tests/test_specificity_ladder_model.py tests/test_ladder_metrics.py tests/test_ladder_tasks.py -q
```

Observed: `48 passed in 25.13s`, exit `0`. The actual NNsight tiny-model module ran, including adapter map consumption, identity/unsupported behavior, dedicated own-task resampling, source rejection, joint sender patches and calibration.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_specificity_ladder.py tests/test_specificity_ladder_model.py tests/test_ladder_metrics.py tests/test_ladder_tasks.py -q
```

Observed: `37 passed, 1 skipped in 25.14s`, exit `0`. The expected incompatible-NNsight module skip is not used as patch-correctness evidence.

```python
from tests.test_ladder_metrics import rows
from component_analysis.ladder_metrics import summarize_ladder
s = [dict(r, operation='task_resample', donor_seed=seed)
     for seed in (101, 102, 103) for r in rows() if r['condition']=='IOI']
print(summarize_ladder(s, n_boot=10))
print([c['operation'] for c in summarize_ladder(rows()+s, n_boot=10)['cells']])
t = [dict(r, operation='h_twin') for r in rows() if r['condition']!='IOI']
for r in t:
    if r['condition']=='H': r.update(gate_valid=False, degenerate=True)
    if r['condition']=='F':
        r['supported']=False
        r.pop('patched_margin'); r.pop('patched_correct')
c = summarize_ladder(t, n_boot=10)['cells'][0]
print(c['D']['fraction_removed'], c['I']['fraction_removed'],
      c['point_pass'], c['collateral']['H']['nontrivial'], c['coverage']['by_condition']['F'])
c = summarize_ladder(rows(), n_boot=10)['cells'][0]
print(c['point_pass'], c['complete_assay_ready'], c['assay_readiness']['MMLU']['complete'])
```

Observed: optional-only output has `cells=[]`; mixed output operations are `['item_swap']`. Missing-F twin retains D fraction `0.5`, I fraction `0.10000000000000009`, `point_pass=False`, H `nontrivial=False`, and F coverage `total=8, unsupported=8`. Without MMLU, the local point gate is `True`, full readiness is `False`, and MMLU completion is `False`.

## Execution evidence

Local CPU tests and synthetic metric reproductions only, all exited successfully. Observed test counts and synthetic outputs are above. No real-model baseline, behavioral output rows, Slurm job, GPU/API call or notebook run occurred. No behavioral `run_manifest.json` exists, and no scientific run is claimed. Tiny-model tests use the repository fixture rather than a downloaded model.

## What is NOT done

Optional IOI task-resample summary/uncertainty remains unfinished as described above. No production fix or new test was authored by this reviewer. CLI staging, frozen-design completeness, cached production tokenizer/data, protected registry, grader registration and empirical model pilot remain outside this review. Full assay readiness in synthetic tests does not establish readiness of any real prepared assessment.

## Open questions

No question blocks the required integration. Default for the optional gap: keep raw donor-seed rows, expose a separate utility diagnostic summary when implementing that optional phase, and preserve its distinction from the primary IOI item-swap guard.
