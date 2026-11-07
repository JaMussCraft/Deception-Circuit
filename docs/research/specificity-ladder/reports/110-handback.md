# Shared operational authority independent review

Status: handed-back

## What changed

Review only; no implementation changes. **Spec verdict: FAIL for the bounded shared authority component. Code quality verdict: CHANGES REQUIRED.** Numerical direction integration and the consumer drivers are outside this verdict. The frozen package hashes all matched at review completion; exact runtime SHA is `691c258d8a46140eef0c4407cf8f06a8f36890d475fe3320fdb19fe2326d9871`. See `110-authority-evidence/receipt.json` and the accepted `.superpowers/sdd/plan-a3/unit-f-authority-review-brief.md`.

- **High: current allocation is not bound to frozen GPU type, memory/CPU resources, or scheduler working directory.** In `component_analysis/a3_direction_runtime.py:1653`, the production parser reads typed GPU TRES but drops memory/CPU/WorkDir. In `component_analysis/a3_direction_runtime.py:1697`, the validator checks GPU count and lease identity/duration, but ignores GPU types and its `work_dir` argument. Production-shaped `scontrol -o show job` transport fixtures accept the wrong WorkDir, an A40 allocation for frozen H200 hardware, and a tiny memory allocation below the inventory host requirement. This defeats the stated live resource/workdir binding and may authorize an unmeasured device or insufficient host capacity. Parse scheduler resource units and workdir, compare them with frozen requirements, and fail closed for unavailable resource facts. CPU requirements need an explicit source if the contract requires them; there is currently no comparison.

- **High: the process-local inventory proof is mutable after validation.** In `component_analysis/a3_direction_runtime.py:1553`, context checks bind Python object/list identity and key count, plus selected scalar fields. They never bind current key contents, shards, hardware or storage requirements. The cached branch in `component_analysis/a3_direction_runtime.py:484` skips inventory validation and subset checking. The independent full-API probe changes an existing expected key in place to one absent from the validated upper inventory; `validate_reservation` still returns execution authority. Persisting an immutable inventory file does not freeze the separately retained Python dictionary. Freeze the consumed inventory deeply or validate each actual requested key and all consumed operational fields against retained immutable proof; retain bounded reuse without treating object identity as content integrity.

- **High: symlinked directory descendants escape immutable file witnesses.** In `component_analysis/a3_direction_runtime.py:1496`, directory walking is disabled for a symlink root; nested symlink directories likewise record target-directory metadata without descendants. A same-size child edit with restored mtime leaves the directory metadata unchanged. The full reservation probe uses a symlink to the completed upper-inventory bundle, creates a valid context, then corrupts its payload. The ordinary artifact reader rejects the stale completion marker, while cached reservation validation still authorizes execution. Reject directory symlinks or recursively witness resolved descendants with cycle handling; completion markers and target child bytes must remain covered.

The ledger and successor structure has useful separation: real RS entries remain independent of external phase mappings; original rounded reservation charges survive terminal reconciliation; monotone successors preserve old anchors and admission references; refresh checks old immutable facts before waiting. Dry-run explicitly defers live allocation admission. These strengths do not close the blockers above.

## How verified

Read the bounded brief, parent brief, accepted integration plan and progress rulings; inspected operational publication/reference, ledger normalization, original admission/reservation accounting, global ceilings, context creation/reuse, successor discovery/waits, actual Slurm transport/parser, live guard and dry-run dispatch. Author report and author handoff prose were excluded.

Independent executable probes are preserved at `110-authority-evidence/test_independent_authority.py`. They replace only subprocess transport for production allocation reads, leaving the actual parser and production rejection of injected lease readers intact. Positive production-shaped allocation control succeeds. Invalid pending state, unlimited time and absent GPU TRES reject. Counterexample tests deliberately assert the observed acceptance gaps, so green probe output records a defect reproduction rather than acceptance.

Both supported interpreters used pinned BLAS/OMP/MKL threads, bytecode disabled, pytest cache disabled and dedicated temporary roots. No broad numerical suite or long native direction test was repeated. Existing focused authority controls exercised ordinary file mutation/replacement/removal/addition, context scope/process boundaries, reconciliation, successor anchors, delayed queue leases, invalid allocations, proposal rejection and static dry-run sentinels.

## Execution evidence

CPU fixture runs only: scheduler job/cluster not applicable; no Slurm query was executed. Both independent probe commands exited successfully with eleven passing tests each; the focused owning selection exited successfully with twenty-five passing tests and forty-seven deselected. Exact observed counts and source hashes are in `110-authority-evidence/receipt.json`; pytest outputs are `110-authority-evidence/mgnp-final.log`, `110-authority-evidence/base-final.log` and `110-authority-evidence/owning.log`.

Commands used `/u/swong2/.conda/envs/mgnp/bin/python` and `/sw/external/python/anaconda3/bin/python3.9` with `-m pytest -q -p no:cacheprovider --basetemp=...`. The independent target was the preserved probe file. The owning target was `tests/test_a3_direction_runtime.py`, filtered by `authority_context or authority_file_witness or mapping_successor or pending_binding or live_allocation or main_model_dry_run or cost_proposal_cannot or proposal_is_not_execution`.

Baseline assertion: the unchanged production-shaped positive lease validates, while the changed-workdir/device/resource variants also validate; the symlink-corrupted upper bundle fails its normal completion read while the cached reservation succeeds. No scientific baseline, numerical row panel or `run_manifest.json` exists for these fixture-only checks. The receipt records the exact frozen source identity rather than inventing a scientific run manifest.

## What is NOT done

No source edits, git commands, RS writes, scheduler submissions/mutations, actual scheduler reads, GPU/large-weight/API work, notebook execution or subagents. No production admission is granted. The long full-count direction runtime, model math, packing, fit/selection/power/reporting finality and consumer driver integration remain separately owned and unaccepted by this report. The probes use small injected root bundles for cache counterexamples; the lease probes exercise the production reader through fixture transport. They establish authority seam behavior, not a real job outcome.

## Open questions

Root should route the bounded blockers to the authority owner, freeze the revised exact source, and request focused independent retests. Resource facts need explicit frozen CPU/memory requirements and supported scheduler-unit formats. Cached consumers must receive a deeply immutable inventory or check their actual requested immutable slice. Symlink handling must cover every accepted referenced tree. Separate complete numerical integration evidence remains necessary before combined Unit F acceptance.
