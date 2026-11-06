# Hand-back: A3 prepared transport Task 1 RED packet

Agent: Sol. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task-1-brief.md`. Status: RED_READY; claimed, blocked on root-observed attributable RED before implementation.

## What changed

Orchestrator-owned candidate test: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/tests/test_a3_prepared_pilot_target.py`.

Packet and complete root commands: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task-1-report.md`; packet directory `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1`.

Test SHA256 `9a9ae6e2eff235e4ddf95447681204e9a03eb74adc149a1dcc30788aa9e53790`; pins SHA256 `853cc03f5c1247c699496c0fc1baa6c93ab5c45318a4e3b2316e5332d52e9990`. Production implementation untouched. No apply operation or publication.

## How verified

```bash
bash -n /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1/cpu.sbatch
```

Observed: exit zero.

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1/cpu.sbatch --dry-run
```

Observed: exit zero; 55 planned cases, source pin checks pass, CPU-only dual-environment commands printed. Relocating a copy of this wrapper under a temporary Slurm-style spool path and changing working directory produced the same command descriptions. Python AST parsing returned zero. No pytest executed.

## Execution evidence

- Job id and cluster: local stdlib-only wrapper dry-run; no Slurm job submitted.
- Exit code: zero; direct and relocated wrapper command descriptions equal.
- Counts: 55 planned cases against 55 expected cases, not executed test results.
- Baseline reproduces: not yet established; the packet will compare the untouched oracle's emitted bytes against a literal expected payload on both interpreters in the root job.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1/run_manifest.json`; accepted baseline commit `538109e809285b6ddc45d42df8786270a65f7b12`, candidate/packet revisions separately source-pinned.

This is packaging evidence only, not a scientific result. Actual RED and baseline reproduction are not yet verified.

## What is NOT done

Root RED, transport implementation, GREEN, full-suite verification, independent review and publication remain undone. The original target read recipe remains two startup reads plus one explicit final witness read. No model, scheduler, RS, remote, git or GPU actions. Root must lint this research hand-back because worker RS use is prohibited.

## Open questions

The exact root dry-run and bounded CPU `sbatch` commands are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task-1-report.md`. Root returns terminal evidence and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1/red-run-01/run_manifest.json`. Default: stop before production edits until root accepts the RED evidence. This is an intermediate hand-back, not Task 1 completion.
