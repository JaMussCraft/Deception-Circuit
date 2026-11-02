# Hand-back: independent A2 analysis plan review

Agent: Codex Sol reviewer. Status: resolved, no blocking design issue found. Scope: prospective design review only; the author hand-back was not read.

## What changed

- Orchestrator-owned worktree report: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report66-a2-analysis-review-handback.md`.
- Identical primary report: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report66-a2-analysis-review-handback.md`.
- The reviewed plan and implementation were not edited.

Review verdict: suitable for lead freeze and subsequent implementation, subject to its existing execution prerequisites. No scientific execution is authorized by this review.

Blocking findings: none.

Minor finding: the plan's global budget paragraph still says the completed timing coverage awaits independent audit. Refresh this sentence using the completed timing audit and cite its calculation artifact. The conservative fleet-plus-pilots projection is 19.22 GPU-hours; the derived residual against the phase cap is about 40.78 GPU-hours before analysis reservations, later failures or changed training reservations. This is projected headroom, not spend or scoring authorization. The plan already correctly requires a measured analysis cost sheet and prevents borrowing other phase hours. Sources: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/62-a2-complete-timing-audit-calculations.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/START.md`.

The smallest change is this factual timing refresh; no new experiment, efficacy threshold or analysis arm is required.

Review conclusions against `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a2-analysis.md`:

- Typed head and MLP keys match the native hook representation. Per-seed difference, reverse difference, intersection and union are explicit. Mixed typed Jaccard requires every pair to pass, while separate head/MLP tables remain diagnostic. Empty unions are undefined, empty candidates cannot pass necessity, and missing seeds remain incomplete.
- Each task requires every per-seed mixed difference group to pass the unchanged primary specificity rule, alongside complete crossed controls, utility floor and source validity. The fixed seed-intersection core is computed from memberships and cannot replace or rescue those tests. No assessment result selects groups, seeds, donors or task coverage.
- Head containment uses its own nonempty head denominator and remains distinct from whole-mask containment. Simultaneous head containment and causal MLP exclusivity are allowed. Invalid pressure denominators remain uninterpretable; aggregate and stream gaps and raw numerators remain visible.
- Native export logic is correct: `analysis.extract_active_nodes` and `extract_node_masks` inspect actual deterministic eval gates after finalization. `l0.HardConcreteGate.get_num_active` uses a different statistic. The proposed export-parity audit, dimension/config checks and rejection of unexpected fine granularity avoid substituting that statistic for scientific membership. Full training completion, matched cohorts, timing-only exclusion and native faithfulness limitations are retained.
- New groups require a separate source/group receipt and bank artifact. The current A1 pipeline hardcodes full/minus group names in expected keys, score dispatch and bank owners; its summary also hardcodes historical SDR ancestry. The plan explicitly avoids coercing these paths and preserves local competence limitations without copying an old deciding-set label onto a newly trained group.
- The original prepared assessment, utility rows, source hashes and donor maps remain fixed. `read_selection` requires the selection completion sidecar, actual artifact/file linkage and execution identity; the plan retains that prerequisite and preserves the original selection evidence as ancestry. New original-H bank keys come from the same frozen train/validation bank IDs, both streams and unpadded token pooling, with independent immutable ownership and coverage checks.
- The pure runner supports arbitrary group labels, joint mixed-component patches, original-H banks and empty controls. Existing metrics accept arbitrary group labels and keep point gates, interval strength and assay readiness separate. The planned A2 aggregator must explicitly enforce readiness and the MMLU floor rather than treating a local operation's point flag as a complete task pass; the plan already requires this.
- Required costs include new bank coverage, every required group assay, crossed/control/utility cells, load/calibration overhead and buffer. Optional diagnostic runs come afterward. Budget shortfalls require an explicit reviewed rescope and incomplete labels; there is no new-seed, EVAL 5, protected-set or API authorization.

## How verified

Static reads covered START, spec, twin-training and ladder plans, the prospective analysis plan, native gate/export/finalization code, hook keys, runner/bank interfaces, selection completion validation, hardcoded A1 orchestration and pure metric/readiness logic. The completed timing calculation artifact was inspected as documentary evidence, not independently replayed as a run.

Representative exact inspection command, run from the worktree:

```bash
sed -n '516,618p' analysis.py
```

Observed: active lists use eval gate outputs and block activity; compact masks retain binary gate vectors and omit gate types that were never created.

```bash
sed -n '470,495p' component_analysis/ladder_pipeline.py
```

Observed: selection validation checks immutable design, execution, raw selection axes, source bank IDs and the exact completion-manifest linkage.

```bash
sed -n '220,320p' component_analysis/specificity_ladder.py
```

Observed: group labels are caller supplied; required mean-bank key coverage, joint patches, no-op calibration and empty-group degeneracy are explicit.

Report lint, number-provenance check and primary/worktree byte comparison are performed before handoff. No implementation tests are warranted for this read-only review.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No plan implementation, mask comparison, scientific training, model load, scoring, GPU/API job, notebook execution or git operation was performed. The author hand-back was not read. No claim is made that full scientific masks exist or that any specificity gate has passed. Timing evidence was not independently reproduced. The conditional analysis budget cannot be approved until measured scoring costs and the live ledger support it.

## Open questions

No blocking question. Default: refresh the timing paragraph, have the lead freeze the explicitly labeled proposals, then implement only the existing tasks. Retain the current source audit, tiny-model calibration, independent contract review and measured budget gates before production scoring.
