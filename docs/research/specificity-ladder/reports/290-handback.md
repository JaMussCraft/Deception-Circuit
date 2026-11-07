# A3 startup-identity correction review290

Status: handed-back. TEST SOURCE ACCEPTED for combined unbound successor review. Scoped spec and quality verdicts pass; no production change or launch acceptance.

## What changed

Created only reviewer-owned copies, static checks, logs and [verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/startup-identity-review290/verdict.json). Corrected runtime-test SHA `760cfe9c9aef14b0ab3a0b41eaba526b2aa64376334be1bea5a710978f9c6f23` is accepted against exercised original `8a314262a2c4fb09c9f6ca883264e072d475affde7a4b927a4379b9c276ec112`. No source, scheduler, remote, RS or active-job edit occurred.

## How verified

The native recorder truthfully uses ambient SLURM_JOB_ID, falling back to injected-cpu for this injected fixture. Its validator correctly checks the supplied expected job and optional PID. The test's hardcoded local fallback caused the actual Slurm mismatch; no production-validator change is warranted.

The correction captures expected job and os.getpid independently before constructing the fixture, without changing the environment or reading observed record identity as its oracle. Positive validation now requires both captured identities. Wrong PID uses independent captured PID plus one, and the new wrong-job check supplies the correct PID. Absent/actual/empty environment values follow the recorder's exact get-with-default semantics. Other top-level ASTs, function signature and parametrizations are identical. All seventeen original assertions and statement order survive modulo the intended identity arguments; one explicit record-identity assertion is added. Original marker/payload damage paths remain.

## Execution evidence

Raw JUnit, events and run manifest for mgnp shard50319108 agree on111 executed items,109 passes and two failures, zero errors/skips. Its original test pin matches, source-before/after is equal, terminal status is FAILED and full-suite acceptance is false. The startup traceback shows the injected-cpu argument rejected by the unchanged job-identity guard. The separate legacy-no-preparation failure remains preserved and belongs to accepted correction282; it was not re-reviewed here. [Evidence pins](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/startup-identity-review290/pins-and-evidence.json).

Static and exact extracted identity-guard checks exit zero in Python3.9 and Python3.12 for absent, actual50319108 and empty job-environment specimens. They confirm positive identity, wrong-PID rejection and wrong-job rejection; extracted identity guards alone naturally do not exercise damaged artifact paths. Both expected captures precede construction and no environment assignment appears. [Runs](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/startup-identity-review290/run_manifest.json). No native import, native collection or full test ran. Latest usage is forty-six percent, cap eighty and cadence forty.

## What is NOT done

No combined successor acceptance, publication, job release, native validation/code completion, genuine measurement, resource-bound, numerical or GPU admission. Existing failed evidence is not relabeled passing, and no claim is made that these pure guards execute the complete test or validator.

## Open questions

Root may combine this exact startup fixture with accepted correction282 runtime/prepared-test into distinct unbound r8, preserving old packets. That combined packet still needs exact source/export/import/pin review, both interpreters' complete native validation and original controls, actual deployment/resource/environment/spool/source-before/after binding and final root release checks. Final publication and Task 4 genuine measurement, resource, numerical, GPU and selection gates remain separate.
