# Hand-back: A3 prepared transport native JSON fixture correction

Agent: Sol. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task-1-brief.md`. Status: handed-back.

## What changed

Only the native fixture comparison changed in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/tests/test_a3_prepared_pilot_target.py`, following root authorization and independent review 193. The corrected expectation uses the unchanged publisher's JSON representation, adds canonical builder-digest and exact native emitted-byte checks, and preserves all coverage/count/digest/witness assertions.

Runtime remains exactly `f39162481d54b9e86119cf4528ba0d9a9c90809e41daf101053891206ee2c6b9`. Test hash is `4082bc6d81fc86479bf9cb0e44f3a49afc75533f7cd7c26c0f6d21c5fcba2097`; packet source-pins hash is `6a7756fe46db30cea28b26b5926bd24d4de529c8e168357523019c39a7df2e29`.

Packet and one-hunk rationale/diff: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r3`. Exact root commands: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task-1-report.md`. Original RED tests, failed GREEN-r2 results and runtime snapshots remain immutable. No apply operation or publication.

## How verified

```bash
bash -n /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r3/cpu.sbatch
```

Observed: exit zero.

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r3/cpu.sbatch --dry-run
```

Observed: exit zero; 55 planned cases per environment. Direct and relocated Slurm-style wrappers resolve the same absolute packet. AST comparison identifies exactly one changed test function; runtime byte comparison matches r2. Packaging provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r3/run_manifest.json`. No pytest ran in this worker.

## Execution evidence

- Job id and cluster: root failed GREEN-r2 `23612764`, Delta.
- Status and exit: FAILED, packet exit one; no normal-completion claim.
- Cases: base 54 passes and one native representation assertion failure out of 55 cases, zero errors/skips; mgnp not run.
- Baseline reproduces: base untouched oracle emitted 62 bytes against expected 62 bytes.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r2/green-run-01/run_manifest.json`, accepted baseline commit `538109e809285b6ddc45d42df8786270a65f7b12`, manifest SHA256 `0d9d1ea125810251047e4cf748d49fadbf99b8993d2ab31394132598bd7ff98d`.

The correction is not yet verified by execution; GREEN-r3 remains a root-owned rerun.

## What is NOT done

Root GREEN-r3 on both interpreters, corrected-packet independent review and Task 1 acceptance remain. No worker heavy tests, scheduler, RS, git, remote, model or GPU actions. Root owns research-report linting because this worker cannot run RS.

## Open questions

Root reviews the correction packet and runs the exact command in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task-1-report.md`. Return terminal evidence and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r3/green-run-01/run_manifest.json`. Default: keep source frozen; do not claim completion or advance Task 2 before root acceptance.
