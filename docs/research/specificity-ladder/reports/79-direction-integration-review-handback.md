# Hand-back 79: Direction integration subplan review

Agent: Codex independent inference reviewer. Status: handed-back.

## What changed

Documentation-only independent review of `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a3-direction-integration.md` against the approved A3 plan and actual reviewed APIs. The author hand-back was not read. No implementation files changed.

- Worktree report: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/79-direction-integration-review-handback.md`.
- Primary mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/79-direction-integration-review-handback.md`.

Verdict: no load-bearing conflict identified. The implementation subplan is suitable to implement under the root's accepted operational rulings. This is not acceptance of an implemented pipeline, runtime feasibility, scientific outcome or cost projection.

No blocking finding has a severity/location/reproduction entry. The following requirements were traced to executable consumers rather than treated as implied future work:

| Review boundary | Assessment |
| --- | --- |
| Execution DAG | Runtime order and work units C–F freeze fit/site choice before assessment axes, then exact selected-site timing before remaining admission. Prefit timing only admits the bounded fit/selection subinventory. Neither admission pass requires assessment outcomes or a future selection artifact that its predecessors cannot produce. |
| Parent provenance | Work unit A uses the original A1 execution identity, selected completion sidecar and exact file-byte links. New A3 source closure is separate. Canonical preparation preserves original assessment IDs, prompt bytes, tokenization, ordering and utility rows rather than redrawing them. The root reports the fresh A1 parent and selection already complete; the plan's older pending-parent narrative does not alter its required fresh-parent boundary. |
| Validation MMLU amendment | Fixed local candidate order, disjoint IDs and exact prompt bytes, original source split retained alongside analysis split, source manifest retained, shortage blocks, and live protected-access checks include the new rows. Existing `mmlu_rows` returns rows and a provenance manifest; retaining both is compatible with work unit A's candidate-source manifest requirement. |
| Fit boundary | Train-only paired D/I/H captures feed `fit_direction`; H/user-neutral/H feeds the framing nuisance with the same bootstrap. Probe standardization remains train-only. Failed DOM sites retain receipts, and no usable fit for a seed blocks its task. Failed nuisance remains explicitly unavailable. |
| Selection and RNG | Work unit D scopes `direction_point_metrics` to one candidate and includes every selection gate before `select_direction`. Finite candidates are passed with their exact site list; full failure tables stay outside that strict core interface. Calibration passes the seed offset into `random_image_directions` once, yielding the approved independent calibration RNG. Null axes receive their own train H statistics through `prepare_image_direction`. |
| Native intervention | CPU fp32 direction algebra, actual unpadded readouts, explicit readout donor gathering and `Replacement` masks agree with the existing hooks. Directional zero/centered-H operations remain subspace patches. Primary canonical scoring uses the captured final readout residual; raw native diagnostics remain separate. |
| Numerical controls | Work unit B requires the same padded batch/kernel path for intact, empty and self/directional replay; preserves the reviewed positive-control shared-width fix; propagates replay epsilon; and requires serial/packed equivalence before axis packing. Positive calibration remains complete-sender recovery rather than a claim of one-axis donor recovery. |
| Exact cell inventory | Work unit E requires concrete row keys, deterministic chunks and actual forward counts in addition to its formulas. Learned/null mechanism arms, IOI and both MMLU floors, selected calibration, nuisance controls, learned/nuisance secondary operations, signed steering, probes, intact/donor capture, replay and positive controls all have named inventory consumers. Descriptive SDR is retained. |
| Timing extrapolation | Frozen validation timing cohorts can be padded to exact declared train/assessment widths without reading assessment outcomes. Both passes require task/site/capture-group/operation/width/batch/dtype/backend profiles or directly measured equivalence. The selected pilot exercises every frozen assessment orientation and relevant calibration/nuisance/secondary/steering profiles. Generic per-head timing and a short null prefix cannot admit the workload. |
| Budget accounting | Work unit E separately charges both direction pilot pieces, startup, failures, retries, other milestone pilot shares, prior spend/reservations and the remaining direction inventory. Root alone supplies finish reserve, ledger snapshot and matching reservation. Phase ceilings block admission; they are not assumed runtime measurements. |
| Statistics packing | Work unit F uses the strict FAR/SER schema, binary correctness, paired mechanism streams, canonical pressure wording, explicit coverage flags and both utility floors. Calibration consumes validation outcomes only and assessment identities solely for exclusion. Nuisance, secondary and signed steering results cannot enter the confirmatory axis panel. |
| Finalization | Complete expected key sets, all seed/axis/control rows, source identity and durable markers are required. Partial/pilot/injected outputs cannot finalize. SDR is descriptive and outside Holm. A scientific gate failure remains a complete negative; missing/invalid execution remains blocked. |

## How verified

Static source inspection only. Read the integration subplan in full, the approved Task 2 executable power specification and global/Task 6 constraints, and the actual interfaces in these worktree files:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_directions.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_statistics.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_pipeline.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a3_design.py`

Also inspected the relevant batch/map/source/readout/control seams in ladder tasks, ladder pipeline, specificity ladder and hooks. In particular, current `a3_pipeline` still exposes canonical CPU preparation without the proposed staged CLI; the plan correctly labels new commands and modules as implementation targets.

Representative read-only commands, run from the worktree:

```bash
nl -ba docs/research/specificity-ladder/plan-a3-direction-integration.md
rg -n '^def ' component_analysis/a3_directions.py component_analysis/a3_statistics.py component_analysis/a3_pipeline.py component_analysis/a3_design.py
sed -n '120,210p' component_analysis/ladder_tasks.py
sed -n '120,180p' component_analysis/a3_design.py
sed -n '1,55p' component_analysis/a3_pipeline.py
```

The plan review did not require rerunning already reviewed pure tests, and no new integration implementation exists to test. No git, subagents, notebooks, models, GPU, APIs, scheduler commands or scientific data execution was performed.

## Execution evidence

Not applicable: no runs.

## What is NOT done

Integration remains unimplemented. No loader, CLI, immutable artifact writer, workload calculator, shard execution or normalized panel packer has been accepted through executable tests. The specified tiny-model, dual-environment, restart, lineage, exact-inventory and admission tests remain implementation acceptance requirements.

No actual pilot duration, model memory, final cell inventory, phase affordability, protected-registry clearance or production power estimate is established by this review. A measured workload that does not fit must block under the accepted ceilings; this review grants no extra compute or reduced scientific scope.

## Open questions

None blocking at the subplan level. Default: implement the stated work units with root-assigned ownership, then independently review actual coverage, artifact binding, tiny-model/native replay and admission behavior before any real pilot. Keep the fresh A1 parent binding and original scientific membership explicit in implementation evidence.
