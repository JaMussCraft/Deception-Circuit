# Hand-back: A2 CPU export audit and mask comparison

Agent: Codex worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a2-analysis.md`, Task1. Status: handed-back.

## What changed

- For orchestrator commit: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/component_analysis/a2_mask_comparison.py`. Added standard-library module imports with lazy CPU Arrow authentication, file-backed source admission, native export parity, typed algebra, pairwise stability, head/MLP containment, prediction and complete MLP tables, source/group/comparison hashes, and exclusive immutable publication.
- For orchestrator commit: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_a2_mask_comparison.py`. Added synthetic CPU fixtures and adversarial admission/algebra tests; existing completed timing evidence is used only for rejection.
- Hand-back source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/report73-a2-mask-comparison-handback.md`. Mirror: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/report73-a2-mask-comparison-handback.md`.

`compare_masks(records)` accepts an exact full scientific fleet. Each record contains `receipt_path`, `execution_root`, `frozen_config_path`, `build_manifest_path`, and `ruling_path`. The execution root must be absolute and identify the frozen runtime snapshot, rather than the analyst checkout. Relative native paths resolve against that root, and original data/output symlinks are supported. Missing or invalid sources raise before publishing scientific output.

Admission binds the approved build and ruling identities, exact frozen H200 configuration, application source hashes and files, successful non-injected receipts, complete epoch history, original ordered test IDs, native manifest/config/artifact hashes, and dataset files. Full resolved configurations are compared across sources after excluding expected task/seed/cohort-count/path differences. Native metrics remain raw training-test evidence and never become an efficacy filter.

Native eval binary vectors supply membership. Native lists must agree with those masks; dimensions, declared gates, finer-grained representation mismatches, finalized ancestor and bottom-up constraints are checked. Ungated blocks remain explicit implicit-active background, outside learned membership. Diagnostic L0 counts and their discrepancies are retained separately.

`write_comparison(comparison, path)` rejects altered comparison content and existing destinations. The orchestrator should publish accepted scientific comparisons under the plan's distinct analysis run directory. No scientific artifact was emitted during this implementation.

The review77 corrections supersede the initial shallow data/default checks. Source admission now calls the existing `_stored_rows` authenticator against the frozen build's authoritative source inventories, row hashes, labels, recipient/reference fields, ordered IDs and token proofs. Every private Arrow shard must appear in dataset `state.json`, and the complete private-file inventory must match native provenance. Malformed, omitted, unreferenced and self-consistently substituted shards/rows are rejected. Dataset loading remains lazy and CPU-only; importing the comparison module still uses only the standard library.

Execution admission now pins the complete approved snapshot, archive and fleet-plan byte hashes, audits all `207` recorded execution dependencies including `analysis.py`, `l0.py` and model wrappers, and checks recorded live-link targets separately. The exact fleet cell binds receipt, build/config paths and execution root. The five-field source-record API is unchanged; snapshot/archive/fleet paths derive from the explicit execution root. Full resolved native configuration must equal the approved defaults including every structural lambda, depth scaling and edge defaults; equality across seeds alone is insufficient. The approved pretrained model revision is pinned explicitly.

The implementation does not edit snapshots, training code, real receipts, frozen configuration/build/ruling, runner code or scientific outputs. The added positives create tiny real Arrow datasets and freeze concrete synthetic source-file inventories rather than supplying admission booleans.

## How verified

The initial checkpoint commands and results below are retained as history; the final review-fix runs following them supersede their test counts.

Working directory: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a2_mask_comparison.py -q -p no:cacheprovider
```

Observed: `35 passed in 2.59s`, exit `0`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a2_mask_comparison.py -q -p no:cacheprovider
```

Observed: `35 passed in 2.56s`, exit `0`.

TDD evidence: the initial collection failed because the comparison module did not exist. Later red cases exposed missing diagnostic discrepancies, configuration drift detection, immutable publication, duplicate JSON key rejection, bottom-up consistency, frozen-file binding, and missing model revision. A schema correction test exposed native `sys.argv` excluding the interpreter; final admission compares native argv with the wrapper command after removing that interpreter.

Coverage includes a pairwise pattern where two pairs meet the criterion and one fails; empty/empty Jaccard remains undefined; vacuous head containment is uninformative; typed head containment can coexist with D-exclusive MLP blocks. Test fixtures do not load models, GPUs, notebooks, assessment outcomes, or unfinished training artifacts.

Final review-fix commands, from the same working directory:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a2_mask_comparison.py -q -p no:cacheprovider
```

Observed: `53 passed, 1 warning in 16.40s`, exit `0`. The warning concerns the installed optional `bottleneck` version used by pandas; no test failed.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a2_mask_comparison.py -q -p no:cacheprovider
```

Observed: `53 passed in 17.07s`, exit `0`.

Regression evidence: all twelve independent review mutation cases failed their rejection assertions before the fix, then passed after admission was tightened. They cover uniform wrong sparsity weights/depth, uniform wrong model revision, altered analysis/gate/model dependencies with self-consistent native hashes, omitted dependency, altered snapshot/archive, missing Arrow inventory, malformed Arrow, wrong private rows and altered authoritative source rows. Separate cases cover each relevant default independently, changed live output links, positive complete inventory/source coverage, and an extra unreferenced Arrow shard. The unreferenced-shard case also failed first, before the state-inventory check was added.

Additional read-only checks used completed timing configuration as a schema example only: the complete resolved-default schema matched after an explicit prospective epoch-field normalization. The timing source still fails scientific admission.

The following exact command audited only frozen execution metadata and source files; it did not open any scientific receipt or native training output:

```bash
python - <<'PYCODE'
import json
from pathlib import Path
from component_analysis.a2_mask_comparison import _audit_execution
p=Path('outputs/_analyses/specificity-ladder/a2-fleet-6bd8bf5-h200/fleet-plan.json');fleet=json.loads(p.read_text());cell=fleet['cells'][0];a=cell['argv']
record=dict(receipt_path=cell['receipt'],frozen_config_path=a[a.index('--config')+1],build_manifest_path=a[a.index('--build-manifest')+1])
audit=_audit_execution(Path(cell['cwd']).resolve(),record,cell['task'],cell['condition'],cell['seed'],{})
print('Frozen execution dependency files:',len(audit['source_files_sha256']))
print('Snapshot/archive/fleet anchors and live links: pass; scientific receipts or outputs opened: 0')
PYCODE
```

Observed: `Frozen execution dependency files: 207`; `Snapshot/archive/fleet anchors and live links: pass; scientific receipts or outputs opened: 0`; exit `0`. This is an execution-source file audit, not a scientific training result.

## Execution evidence

Not applicable: no runs.

The commands above are CPU software tests only. No scientific training/evaluation run, numerical baseline reproduction, scientific row-count comparison, or new run manifest is claimed. The prospective execution source identity is retained in the implementation; scientific replay remains unavailable until all full sources have terminal successful receipts. No GPU/API/Slurm operation occurred, and no git command was run.

## What is NOT done

- Full scientific mask comparison and publication remain deferred until the fleet is complete. No unfinished scientific output was consumed and no scientific stability, containment, faithfulness, or specificity outcome is asserted.
- Task2 bank and scoring integration and Task3 effect aggregation are explicitly deferred by the assigned scope, rather than missing Task1 implementation.
- No native model replay, efficacy cutoff, assessment selection, A1 artifact modification, budget change, RS state/worklog/ledger write, or source training change occurred.
- Immutable storage prevents replacement at publication and detects comparison mutation through hashes; filesystem administrators can still modify stored files, so downstream consumers must validate hashes.

## Open questions

- Default: obtain independent re-review of the review77 corrections before scientific admission. The orchestrator independently reviews this CPU source contract before scientific admission. Supply the explicit frozen runtime execution root, frozen H200 configuration, exact matched build manifest and committed cohort ruling with every source record.
- Default: publish once in a new analysis run directory after every scientific source completes successfully; preserve all groups and all source aliases before any assessment scoring. A failed or absent source remains orchestration-level incomplete evidence, never a partial scientific comparison.
