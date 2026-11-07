# Hand-back `38`: Independent design and utility adapter review

Agent: Codex reviewer. Ticket: Task `1` and Task `3` of the ladder plan. Status: handed-back.

## What changed

Production files were read only. The orchestrator may commit this report from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report38-design-adapters-review.md`. No staged apply operations exist.

**Verdict: request changes for adapter-to-runner integration.** The earlier eligible-pool index issue is closed in the inspected code; the required IOI item-swap path currently fails before model execution.

- **P1: utility donor maps do not satisfy the runner contract.** `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_tasks.py:234` constructs maps without `requested_positions`, `covered_positions`, `gate_valid`, `no_op`, or `degenerate`. A supported result of `ioi_item_swap_maps` fails `_check_map` in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/specificity_ladder.py:179` because `covered_positions` is absent. Adding that field alone is insufficient: `score_cell` takes `mapping.get('gate_valid', False)`, so the primary IOI collateral rows would still be excluded from gate evidence. Missing requested/covered counts also make aggregate position coverage misleading. Supply the complete common map contract and test an actual adapter map against its consumer, including supported, unsupported, and identity behavior.
- **P2: optional IOI task-resample maps have no runnable operation.** `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_tasks.py:266` emits `task_resample`, but the runner's `OPERATIONS` excludes it. Renaming to `independent_resample` is insufficient because that path requires H-derived train/validation donors, which these generated IOI donors correctly are not. Add a dedicated own-task operation and validation, or explicitly defer the optional diagnostic and show it as unfinished. Required IOI item swap remains necessary regardless.

The previous index issue is closed: `freeze_design` now stores ordered `eligible_pool_ids`, renames indices to `eligible_pool_indices`, and states the authoritative join key. Indexing that recorded pool reconstructs assessment IDs exactly, even with excluded IDs and reversed source order. No raw-split index claim remains in the frozen sample metadata. The explicit `mover_selection_ids` preserves caller order, requires unique nonempty IDs present in this task's H test rows and in the exclusion union, and supplies selection rows in that order. The broader union independently excludes assessment IDs. These are the correct separate roles; upstream artifact provenance remains a caller responsibility.

The remaining reviewed adapter choices match the plan: sorted names make IOI replay independent of set iteration; the adapter restores Python RNG state; the generator's omitted `name_pool` branch preserves historical loading/filtering and positional arguments. Final answers are removed before tokenization with exact suffix checks. Both answer options must extend each clean/corrupt prefix by exactly one contextual token. Selection uses generated order, eligibility and deduplication without model outputs. Clean IOI is the utility assessment; corrupt batches carry `utility_assessment=False`. Masks, BOS handling and final-prefix readouts are consistent.

MMLU uses the existing local-only cache helpers, stable sorted parquet-relative row IDs, source file hashes, actual snapshot revision, malformed/length/contextual-token rejections before seeded sampling, the neutral system prompt and formatted question, contextual option IDs, and full-vocabulary expected-letter accuracy. Preparation retains prompt bytes/tokens and tokenizer/adapter/formatter fingerprints. Calibration maps explicitly map readout to readout across different questions. No MMLU item swap is invented. Preparation honestly leaves grader registration unfinished and does not itself authorize scoring. The unused revision constant does not falsely claim that a different loaded snapshot is the inspected revision: the manifest records the actual revision. A real cached-data/tokenizer run remains necessary before empirical claims.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_ladder_design.py tests/test_ladder_tasks.py -q
```

Observed literal output: `37 passed in 2.80s`; exit code `0`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_ladder_design.py tests/test_ladder_tasks.py -q
```

Observed literal output: `37 passed in 2.68s`; final process exit code `0`.

```python
import runpy
from component_analysis import ladder_tasks as t
from component_analysis.specificity_ladder import _check_map, OPERATIONS
fixture = runpy.run_path('tests/test_ladder_tasks.py')
t._generate_ioi = lambda *args: [fixture['source']()]
rows = t.ioi_rows(fixture['Tokenizer'](), n=1)
recipient = t.task_batches(rows)[0]
donor = t.task_batches(rows, stream='corrupt')[0]
mapping = t.ioi_item_swap_maps(rows)[0]
print(mapping['supported'], mapping.get('covered_positions'), mapping.get('gate_valid'))
try:
    _check_map(recipient, donor, mapping, 'item_swap')
except ValueError as exc:
    print(str(exc))
print('task_resample' in OPERATIONS)
```

Ran through the mgnp interpreter with BLAS threads pinned to one. Observed: `True None None`, then `whole-sequence map must cover every unpadded recipient position`, then `False`. This reproduction uses no model and exposes a gap that the passing isolated adapter tests miss.

## Execution evidence

Local CPU test/reproduction commands only; no scientific run, job, model, GPU, API or notebook execution occurred. Both focused test commands and the model-free reproduction exited `0`. The focused test counts were `37` passing against `37` collected in each interpreter. No behavioral baseline, assessment row output or `run_manifest.json` exists for this review, so behavioral results are not yet verified.

## What is NOT done

No production edits, real tokenizer/cache sampling, model-level intervention, empirical capability assessment, grader registration, GPU/API execution, or git command was performed. Author reports `31` and `33` were not read. The passing CPU suites do not establish adapter-to-runner interoperability or model patch correctness.

## Open questions

The orchestrator should fix the common utility map contract before the required IOI pilot. Default: keep map generation explicit, including coverage and gate validity, and add a direct consumer integration test. The optional task-resample operation may be implemented separately or deferred with honest coverage labeling; it must not be relabeled as H-derived resampling.
