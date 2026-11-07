# Hand-back 287 r2: Isolated startup identity test correction

Agent: Sol. Status: resolved drafting; native acceptance outstanding.

## What changed

New test-file copy: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/startup-identity-correction287/tests/test_a3_direction_runtime.py`.

Only the existing startup cost test changes. It captures job identity from ambient `SLURM_JOB_ID` with the injected fallback, and PID from `os.getpid()`, before construction. The positive check uses both independent values; the existing wrong-PID check uses the correct job and independently captured PID plus one; a separate wrong-job check uses the correct PID. All four original hardcoded job arguments now use the captured expected job. Every original cost/resource/linkage/damage assertion and expected exception remains.

Supporting files under the same new directory are `check_draft.py`, `pure-results.json`, `scope-pins.json` and `test_a3_direction_runtime.diff`. Detailed report: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task-4-startup287-report.md`.

Output SHA-256: `760cfe9c9aef14b0ab3a0b41eaba526b2aa64376334be1bea5a710978f9c6f23`. Exercised input SHA-256: `8a314262a2c4fb09c9f6ca883264e072d475affde7a4b927a4379b9c276ec112`.

## How verified

```bash
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/startup-identity-correction287/check_draft.py
```

```bash
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/startup-identity-correction287/check_draft.py
```

Observed both exit zero, no stderr. Whole source compiles in memory; all other top-level AST nodes and the target's decorators/arguments remain equal. Original target statements retain their order and content after only the authorized validator identity-argument changes. Seventeen original assertion statements remain, plus one independent identity assertion; the added wrong-job rejection stays inside the same existing case. No test identity or parametrization changed.

Extracted draft assignments and native job/PID guards pass three controlled environment specimens: absent, observed Slurm job, and present empty string. Each gives positive pass, wrong-PID reject, wrong-job reject, and identity-only pass for the two byte-tamper paths. No observed record supplies expected identity; no real environment changes. These extracted checks do not exercise record authentication, filesystem tamper detection or cost projection. Exact structured outputs and diff are saved in the new directory.

## Execution evidence

- Native RED: the existing Bridges job 50319108 failed the startup identity case at the expected hardcoded-job assertion. Saved terminal observation is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-failure281/observed-terminal-50319108.json`.
- Saved child provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task23-green-r6-r2-sharded/jobs/job-50319108/child/execution/run_manifest.json`, accepted baseline commit `538109e809285b6ddc45d42df8786270a65f7b12` with isolated revision bound separately by exact source pins. Child exit one; 109 passed against 111 expected, two failures, zero errors/skips. No scientific baseline reproduction claim.
- New local checks: two bounded stdlib/AST commands, exit zero on both interpreters; three identity specimens each. Exact commands/results: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/startup-identity-correction287/pure-results.json`.
- Native GREEN: not yet verified. No new native run or `run_manifest.json` exists for this draft, and no acceptance follows from pure/static checks.

## What is NOT done

No active/frozen edits, runtime change, environment spoofing, weakened exception/guard, source publication, native import/full test/target construction, Git/RS/SSH/scheduler/job operation or agent. Root owns lint/number checks, review and any distinct successor assembly. Candidate183, correction282 and unsubmitted r7 remain untouched. The complete original 223-case identities, both-environment validation and all final gates remain required.

## Open questions

- Does root's independent full-diff review accept this test-only file for distinct r8 assembly with correction282? Default: preserve this draft and all prior packets until reviewed.
- Will the unchanged complete scope pass natively on both interpreters? Default: no acceptance or automatic rerun from these bounded checks.
