# Hand-back: Independent ladder design review

Agent: independent reviewer, Codex Sol. Ticket: Task 1 of `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-ladder.md`. Status: resolved review; request a provenance correction before freezing assessment artifacts.

## What changed

- Orchestrator commit candidate: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/30-ladder-design-review-handback.md` only. No implementation or test changes.
- No staged apply operations.

**Spec finding, P2:** `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/ladder_design.py:230` sorts and filters the candidate records before calling `draw_sample`, then exports `sample.as_json()` unchanged. Its `split_indices` index that filtered candidate pool, while its inherited `join_on` explicitly claims they index the split returned by the task loader. Excluding an early row therefore produces wrong source positions. A later consumer or audit that follows the exported metadata can recover excluded or mismatched rows. The actual `assessment_ids` remain correctly excluded and matched; this finding does not establish current assessment leakage.

Derived focused example using the existing `pools` fixture: `pools(5)`, exclusion `{'0'}`, explicit mover list `['0']`, and `n=2` return assessment IDs `['1', '2']` and exported `split_indices=[0, 1]`; those positions in original D rows contain `['0', '1']`. Correct this by naming the indices as eligible-pool positions, recording the ordered eligible-pool IDs, and replacing the inherited source-split claim. This preserves the existing input-order-invariance contract. Alternatively publish explicitly translated source indices with an unambiguous source ordering. Add a focused assertion covering an excluded early row and reordered source inputs.

Standards review found no separate actionable issue. The scientific design passes static review otherwise: explicit ordered task-specific mover IDs are distinct from union exclusions; sampling has no model/outcome filter and rejects short fixed-size draws; groups parse exact recorded members and label SDR descriptive; mover screening uses joint strict positivity, the clean mean, and head-only subtraction; no movers or ranks are invented. Required twins use same-id original H or H-derived user-neutral, optional resampling uses different-id train/validation donors, exact labels and layouts, sorted eligibility and independent recipient seeds. H identity is marked unusable for a collateral gate. Missing or unequal explicit layouts produce unsupported cells.

## How verified

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_ladder_design.py tests/test_sampling.py > /tmp/ladder-design-review-mgnp.log 2>&1
```

Observed: 37 passing tests in `/tmp/ladder-design-review-mgnp.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_ladder_design.py tests/test_sampling.py > /tmp/ladder-design-review-base.log 2>&1
```

Observed: 37 passing tests in `/tmp/ladder-design-review-base.log`.

```bash
OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 - <<'PY'
import json, runpy
from component_analysis import ladder_design as ld
helpers = runpy.run_path('tests/test_ladder_design.py')
rows = helpers['pools'](5)
out = ld.freeze_design(rows, {'0'}, mover_selection_ids=['0'], n=2)
print(json.dumps({'assessment_ids': out['assessment_ids'], 'reported_split_indices': out['sample']['split_indices'], 'ids_at_reported_positions_in_source_D': [rows['D'][i]['instance_id'] for i in out['sample']['split_indices']], 'join_on': out['sample']['join_on']}))
with open('docs/research/mechanism-analysis/phase1/p1c_readings.json') as handle:
    groups = ld.recorded_groups(json.load(handle))
print(json.dumps({t: {'count': len(v['members']), 'descriptive': v['descriptive']} for t,v in groups.items()}))
PY
```

Observed the derived mismatch above. Actual recorded groups parsed successfully; each contains the recorded membership, with only SDR marked descriptive. No source artifact or implementation-worker narrative was used as a review conclusion.

## Execution evidence

- Job and cluster: local CPU commands above; no Slurm/model/GPU/API run.
- Exit status: local command wrappers exited successfully, and both pytest logs report completion without failed tests.
- Counts: 37 passed against the worker-reported expected 37 in each of `/tmp/ladder-design-review-mgnp.log` and `/tmp/ladder-design-review-base.log`; this review independently reran the same focused suite.
- Baseline reproduces: not applicable to empirical model behavior; no baseline model result is claimed.
- Provenance file and commit: not applicable to these local unit tests and pure reproduction; no scientific execution claim or empirical result is made, and git was not run.

## What is NOT done

`Task 2` patching and `Task 3` source adapters are deliberately outside scope. No assessment design was frozen and no model was loaded. Source provenance, protected-registry checks, raw-row normalization, and token-layout construction remain obligations of the later CLI; the pure normalized-row contract is usable for them. The defect above remains unfixed in accordance with the review-only assignment. The worker report numbered `28` was not read.

## Open questions

The orchestrator accepted the correction: publish `eligible_pool_indices` with ordered `eligible_pool_ids`, use `join_on='instance_id'`, remove misleading raw `split_indices`, and keep primary `assessment_ids` authoritative. Default: fix the exported index provenance before freezing artifacts, then review only that focused change. Retain the current ID-based assessment selection and the distinction between task mover IDs and union exclusions. Do not broaden or repeat the whole suite unless the correction changes sampling behavior.
