# Hand-back 259: A2 operational Task 3 RED packet

Agent: Sol implementation worker. Status: handed-back. Scope: RED tests and root-run CPU packet only.

## What changed

- Assigned tests: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-operational186/candidate/tests/test_full_score_release.py`, `test_full_score_cache.py`, and `test_full_score_usage.py`.
- Immutable packet: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/red259`. Packet pins SHA256 `3dae43ebb643a61a27fe45a89eedc2cbd0d5c5c2e262308223af8c7b46026bf6`; original-source pins SHA256 `515214e6c6e145f1840b43f3a314de7e570b8c524127ff23ff32be92f10a38a1`.
- Uses actual accepted Task 1 WAITING producer, Task 2 request validator and COMPLETE constructor, and Task 1 composite consumer. Fixture boundaries prevent native imports, model loading and actual authority. Accepted wrapper sources and fixture files are copied into the packet and checked against original source hashes before and after each invocation.
- Tests require full-only job/source/G3/bank/config/resource identity; immutable full-domain CPU proof; current cadence arithmetic and ordinary80 cap; hard80 command plus targeted session status; missing protected closure review; retained failed/cancelled budget charges and reviewed duration; per-operation pin checks; once-only atomic files; exact historical cache bytes; and executable Python3.6-compatible generated remote final guards.
- Pure `validate_cutover(attestation, now=...)` is a proposed helper test seam for fresh quiescence and completed native pair prerequisites. This introduces no native authority kind. Root acceptance of this RED packet must explicitly accept or revise that seam before implementation.

## How verified

```bash
bash -n /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/red259/run_cpu.sh
```

Observed exit 0. All packet Python files passed stdlib AST parsing; neither pytest nor native project code was imported. Source and packet hashes matched in the dry run.

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/red259/run_cpu.sh --dry-run --output /tmp/task3-unused-red259
```

Observed exit 0, `execution=false`, 98 expected cases per invocation. A copied wrapper at a temporary Slurm-like spool path also resolved the same absolute packet and returned exit 0. Static-only evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/static-check259.json`.

## Execution evidence

Not applicable: no runs.

No tests, native normalization, scientific validation, scheduler job, remote transport or publication was executed by this worker. AST and wrapper dry-run metadata checks above do not establish RED acceptance. The root-run packet will create its own `run_manifest.json`, four raw logs, JUnit files and `RESULT.json` under a new exclusive output directory.

## What is NOT done

- Root has not yet observed attributable RED. Semantic production files remain absent: `candidate/root/helper.py`, `cache_gate.py`, and `bindings.template.json` were not created.
- No GREEN, native budget-chain transition, actual resource proof, resource binding, actual CPU proof, reservation, mapping successor, admission or release was created.
- These initial RED tests do not yet exercise the complete Producer.publish transfer/composite path against fake transport, native normalize_ledger lineage fixtures, complete closure staging, SIF/cache/catalogue changes during transfer, or final once-only lease expiry through the actual Task 1 consumer. Those integration cases remain necessary during the post-RED implementation phase before Task 3 completion.
- No root diagnostic239 or A3 worker files were changed. No git, scheduler, RS mutation, external communication or delegation occurred.

## Open questions

Root must execute the packet on Slurm CPU: 2 CPUs, 4 GiB, 6 minutes, zero GPUs. The four pytest invocations each have a 70-second timeout and require 98 cases, exit 1, at least one assertion failure and one positive control, no errors and no skips. Historical baseline and absent implementation are both intentional RED targets; actual failure names and counts must be reviewed from XML/logs before acceptance.

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/red259/run_cpu.sh --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task3/root-red-01
```

Default next step: root runs/reviews this RED packet and accepts or revises the `validate_cutover` test seam; only then resume implementation. Actual resources and full scoring remain unbound. There is no scientific blocker to this CPU fixture validation. The sandbox launcher failed creating its temporary directory, so filesystem reads/writes used auto-reviewed escalations; no action was rejected.
