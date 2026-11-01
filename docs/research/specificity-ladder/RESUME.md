# Resume: specificity-ladder

## Status

Paused explicitly by the user for a Codex restart and settings changes. Do not resume until the user says to continue. All workers received HOLD, saved their handoffs and stopped; no owned subprocess remains. No GPU, model inference, training, paid API, or scientific gate has run.

A1 Task 1 constructor is reviewed and committed. All 4,200 source rows align with the cached tokenizer, but behavioral survival is unknown. A1 Task 2 scoring code is saved and has passing tests, awaiting independent review. A2 Task 1 materializer has a confirmed review blocker: it can mistakenly admit unscored/wrong-model I data; do not use matched fleet_ready until fixed. A2 Task 2 wrapper is partial; its combined wrapper/materializer suites passed 47 tests on each interpreter, but the documented launcher and provenance gaps remain. The crossed-ladder plan is prospective only.

## Branch, worktree and commit

- Branch: `specificity-ladder`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.
- Main claim: `16ce5f7`. Plans: `ba9686d`, `fb92cf0`, `083b8f9`. Reviewed constructor: `6c47504`.
- A restart checkpoint may follow those commits; check git log and status before editing. Checkpointed code is not necessarily reviewed or complete.
- Authoritative RS state/worklog/ledger are in primary `Deception-Circuit/docs/research/specificity-ladder/`, because harness cwd is Alignment. Worktree copies of tool-owned template records are not live state. Code, plans and intended report commits belong in the worktree; report duplicates in primary are required by the stop hook.
- Execution ledgers: `.superpowers/sdd/plan-a1/progress.md` and `.superpowers/sdd/plan-a2/progress.md`.

## In-flight jobs

No Slurm jobs have been submitted; the registered job list and live user queue were empty at pause. No reservations or API spend exist. Do not launch a pilot until CPU checks, independent review, actual wrapper dry run, live usage and ledger checks pass.

## Next action

After the user resumes, read the final handoffs 10, 08 and 12 in this direction's reports, then check git status and live RS status for `codex-01a1987e`. Do not re-register this existing session and reset its checkpoint baseline. If the harness genuinely creates a new session id, reconcile ownership and registration through RS before spawning.

1. Independently review A1 Task 2 scoring changes against plan-a1; direct logs are `/tmp/a1-scoring*` as listed in report 10. Focused tests passed 53 on each interpreter and unchanged related suites passed 148 on each. Do not repeat completed constructor work. After review, implement Task 3 staged derive/score/assemble CLI and GPU wrapper, including the new scored-data contract.
2. Fix A2 materializer review 11 test-first: require I threshold 0.7/0.5, matching model identities, actual original D/H source hashes, and verified score receipts/files/prompt hashes per `a1-data-contract.md`. No fix was started before HOLD. Then obtain independent re-review.
3. Resume A2 wrapper Task 2 from report 12; direct script invocation has an unresolved repository import-path issue (module invocation works). Review its final saved test evidence. Task 3 budget projection is not implemented. Keep provisional D-only data out of production training.

CPU baseline before edits: 205 passed and one known failure in `test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms` (120 versus 128), both interpreters. Logs are in reports and `outputs/_analyses/specificity-ladder/cpu-validation/`. No notebooks were executed. Use both interpreters with BLAS threads 1 and pytest cache disabled; compare failures by name.

## Do not

- Launch GPU/API work before resumption or treat raw constructed rows as behaviorally screened survivors.
- Trust A2 matched readiness until review 11 is fixed and reviewed.
- Repeat closed studies, use hidden operator inversion as a specificity test, edit instructed-route or protected paused-study outputs.
- Merge to main, run EVAL 5, score registry-protected sets, raise caps, or bypass human-only cadence controls.
- Score MMLU until grader provenance is frozen in both spec and registry; the RS CLI lacks a metadata setter and that tooling gap remains unresolved.
- Confuse same-instance neutral replacement with independent donor resampling. H-to-itself is a no-op, not evidence of preserved honesty.

## Open decisions for the user

- The restart pause is the only current user action awaited. Resume after settings are corrected.
- The user applied a temporary 40-point cadence to this Codex session until the observed weekly reset; then return to 25 via the human-only command. No automatic reversion exists. Check live account readings rather than assuming the predicted reset date.
- The earlier untargeted cadence command changed Claude session `claude-230e4716`; the later targeted command correctly changed this Codex session. Do not silently modify the other session.
