# Hand-back for ticket #40: Exact matched-cohort ruling and launch preflight

Agent: Codex worker. Ticket: approved exact matched-cohort ruling in plan-a2.md. Status: handed-back.

## What changed

Orchestrator-owned commit list from the worktree:

- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/twin_training_projection.py: validates explicit cohort-size-only rulings against build hash, canonical ordered selected-ID digest, exact typed task/split counts, schema, decision, conditions, selection rule, and nonempty ruling/session identities. Missing rulings retain the small-cohort hold. Recommendations expose the small-cohort fact, remaining review requirement, and ruling digest. Other receipt, timing, hardware, coverage and reservation gates remain in force.
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/twin_training.py: project stage forwards to the same projection parser. Planning and immediate runtime preflight refresh the union of primary/worktree protected registries using only the standard library, rejecting missing/malformed registries, bad protected-file paths/hashes/counts and selected-ID overlap. Receipts retain refreshed registry hashes. Real run requires explicit full execution revision via --commit; execution_commit is separate from build source_commit, and the augmented native manifest records execution_commit, orchestrator_source_commit and build_source_commit distinctly.
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_twin_training_projection.py: regression, rejection, unchanged-gate, CLI parity and execution-provenance cases.
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_twin_training_wrapper.py: dry-run/runtime registry rejection and refresh tests, distinct execution provenance and explicit run commit requirement.

No edits to the prospective ruling JSON. Ruling validation binds cohort identity and records supplied provenance; it does not authenticate human signatures. The machine-readable decision remains the lead's responsibility.

## How verified

Commands ran from /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training_projection.py tests/test_twin_training_wrapper.py -p no:cacheprovider -q
```

Observed: 157 passed, recorded in /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/40-cohort-ruling-checks.json. Before implementation, the exact-ruling regression failed because a valid ruling still held; registry regressions failed in all seven selected cases, including a child invocation after registry changes; all six selected execution-revision regressions failed because missing/foreign revisions were accepted. These failures preceded their implementation changes.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training_projection.py tests/test_twin_training_wrapper.py -p no:cacheprovider -q
```

Observed: 157 passed, with the existing pandas/bottleneck version warning; see /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/40-cohort-ruling-checks.json.

Offline direct validation of /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07/build_manifest.json against the unchanged ruling returned digest `343bff33ea69a9e40ba9fade582f7e038f508e4bfe333c3328b93eeb14784605` and build hash `c79830a14f94a6f8a7bce937dba8d2444abfc911676f7f71016b37ca6463781f`. Selected train/validation/test counts were FAR 177/177/891, SDR 187/187/952 and SER 168/167/835, matching the recorded decision. An initial primary-checkout manifest lookup failed because the artifact lives in the worktree; the corrected worktree lookup succeeded.

Live quota command /u/swong2/.local/bin/codex-usage --pause-at 80 returned exit zero, weekly used 13 percent, remaining 87 percent, should_pause false, reset 2026-11-06T16:07:41+00:00; see /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/40-cohort-ruling-checks.json.

Sandbox startup failed creating its temporary directory. Read/write/test commands used justified require_escalated fallback; no automatic approval rejection occurred.

Both handback copies pass research-session lint. The report-number check traces cohort counts to the manifest and operational test/quota counts to the retained worker-observation summary.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No model, GPU, API, notebook, training pilot, fleet reservation, Slurm submission or git operation. CPU tests use synthetic timing fixtures and injected child processes. Actual scientific provenance, timing coverage and reservations await the orchestrator's measured receipts and ledger. Broader unrelated suites were not run. Independent review and explicit-file commit belong to the orchestrator.

## Open questions

Independent review should also inspect the root-owned launcher /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/scripts/jobs/specificity_twin_training.sh. Its activation dry-run must be repeated by root after these guards and the final execution revision are committed.

None blocking. Supply the final committed full revision with --commit for real training, and optionally the same revision when projecting receipts. Keep the existing build source revision unchanged. Root must review before launch.
