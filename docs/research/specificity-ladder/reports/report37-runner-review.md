# Runner and metrics independent review

Agent: Codex Sol reviewer. Status: handed-back.

## What changed

Review only. No production files changed and no git commands run. The orchestrator owns integration.

Reviewed the runner, metrics and focused tests directly against START, spec and the runner task of the ladder plan. Author reports and implementation handbacks were not read.

Owned report: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report37-runner-review.md`.

### Findings requiring changes

- **P1: unsupported F twin erases otherwise supported D/I estimates.** In `component_analysis/ladder_metrics.py:125-134`, any unsupported observation short-circuits the entire operation before computing native effects. This includes explicitly allowed missing F twin alignment. Reproduction using `tests.test_ladder_metrics.rows`: set mechanism operations to `h_twin`, retain IOI as `item_swap`, mark H degenerate, and set only F observations unsupported. The summary returns `status=unsupported` with no `D` or `I` entries, although the complete native D/H and I/user-neutral rows remain available. The plan explicitly says missing F mapping does not invalidate the other required crossed results. Preserve supported effect estimates and condition-specific coverage; report absent F evidence separately. A whole-assay verdict may remain incomplete. Do not blend operations or certify the H self-patch as preservation.

- **P1: there is no separate full-assay readiness gate for the MMLU floor.** At `component_analysis/ladder_metrics.py:148-151,198-215`, absent MMLU sets its guard to `None`, the point gate accepts that value, and the result can be labeled `strong`. Running the existing metric fixture unchanged produces `status=strong`, `point_pass=True`, `strong=True`, `MMLU.pass=None`. An item-swap specificity estimate can legitimately remain separate from MMLU, which has no native item-swap intervention. However, the API must distinguish that local estimate from completed A1 readiness: the fixed MMLU zero/H-mean floor and its coverage are required before claiming the full assay complete. Add an explicit readiness/incomplete result or require a later assembler to consume the distinct utility cells. Never invent MMLU item-swap rows to make this field pass.

- **P2: optional donor failures suppress all supported-subset robustness results.** The same unconditional short-circuit at `component_analysis/ladder_metrics.py:130-134` applies to `independent_resample`. Build the fixture for each prescribed seed, then mark a single donor observation unsupported. The result contains coverage but no effect estimates, supported recipient count or supported-subset analysis. Task 1 explicitly requires supported-subset results without changing the primary assessment sample. Keep the fixed sample unchanged and distinguish full-support coverage from a clearly labeled diagnostic subset requiring complete paired conditions, streams and donor seeds.

### Behavior that passed review within this scope

The runner calls the actual shared `hooks.capture_forward` and `hooks.Replacement`, jointly applies mixed head/MLP sets, and reads every arm through `hooks.readout_logits` on the saved final residual. It retains native logits as separate diagnostics. Donors use their own masks and readouts; explicit maps are checked against unpadded lengths and layouts. Mean collection delegates to the shared equal-token fp32 collector on both original-H streams, with split/source checks and recipient-source exclusion. Empty and self-replay checks fail on argmax or margin disagreement. Positive calibration replaces every sender, including embeddings, at readout and tests donor-logit recovery without the receiver shortcut.

Metric estimates use ratio of means, average streams within paired ids, guard each stream denominator, preserve pressure clusters, and resample independent donor seeds outside recipient estimates. Native mechanism tasks remain separate from IOI/MMLU. Accuracy uses full-vocabulary argmax; the tests include disagreement with binary wins and restricted-choice accuracy.

The primary item-swap gate must remain the primary verdict. The H identity row correctly cannot establish preservation, and its inability to yield a standalone h-twin specificity pass is not itself a defect. The missing F behavior above concerns lost computable descriptive effects.

## How verified

Both commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_specificity_ladder.py tests/test_specificity_ladder_model.py tests/test_ladder_metrics.py -q
```

Observed: `28 passed in 23.20s`. The pinned NNsight tiny-model module actually ran, including joint patches, mean banks, replay and positive calibration.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_specificity_ladder.py tests/test_specificity_ladder_model.py tests/test_ladder_metrics.py -q
```

Observed: `21 passed, 1 skipped in 30.72s`. The module-level NNsight compatibility skip is expected in base; its skip is not patch-correctness evidence.

```python
from tests.test_ladder_metrics import rows
from component_analysis.ladder_metrics import summarize_ladder
s = rows()
c = summarize_ladder(s, n_boot=100)['cells'][0]
print(c['status'], c['point_pass'], c['strong'], c['MMLU']['pass'])
t = [dict(r, operation='h_twin') if r['condition'] != 'IOI' else dict(r) for r in s]
for r in t:
    if r['condition'] == 'H': r.update(gate_valid=False, degenerate=True)
    if r['condition'] == 'F': r['supported'] = False
c = summarize_ladder(t, n_boot=10)['cells'][0]
print(c['status'], 'D' in c, 'I' in c)
ind = [dict(r, operation='independent_resample', donor_seed=seed)
       for seed in (101, 102, 103) for r in rows()]
ind[0]['supported'] = False
c = summarize_ladder(ind, n_boot=10)['cells'][0]
print(c['status'], 'D' in c)
```

Observed respectively: `strong True True None`; `unsupported False False`; `unsupported False`. These are synthetic regression reproductions, not behavioral model results.

Live Codex usage at handback remained below the requested pause threshold; the fresh account lookup returned `status=ok` and `should_pause=false`.

## Execution evidence

Only local CPU tests and synthetic metric reproductions ran. No Slurm job, real-model assessment, GPU, API or notebook ran. Both pytest commands exited successfully; test counts are listed above. There is no behavioral output row count, baseline assessment or `run_manifest.json` to certify. No scientific run result is claimed.

## What is NOT done

Production fixes and new regression tests remain with the implementer. Full-assay readiness, independent-donor subset handling and supported D/I reporting after missing F remain unfinished. No empirical specificity verdict is supported by this review.

No broad legacy suite was run; this review executed the requested focused files in both environments. The baseline commit was supplied by the orchestrator; this reviewer did not inspect repository history.

## Open questions

The lead should define the machine-readable distinction between an operation's native specificity estimate and full A1 readiness. Default: retain operation-specific gates, expose all coverage, and require separate MMLU floor completion for full readiness. Do not combine interventions into an invented specificity gate.
