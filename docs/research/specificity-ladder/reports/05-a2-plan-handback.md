# Hand-back 05: A2 preparation implementation plan

Agent: Codex research worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/START.md`, A2 preparation. Status: resolved.

## What changed

- Plan for orchestrator review: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a2.md`.
- Handback: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/05-a2-plan-handback.md`; hook-required copy at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/05-a2-plan-handback.md`.
- Three implementable tasks: isolated materializer, frozen training/timing wrapper, and complete-fleet budget projection. D-only timing preparation is independent of A1; matched I waits for its aligned inputs. Coarse nls0.3, 500epochs, seeds42/1/123 fixed. No global task changes.

## How verified

Read `/u/swong2/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/skills/writing-plans/SKILL.md`, START, and the completed A2 reconnaissance. Self-reviewed interface consistency, source identity/mask/label checks, matched cohort handling, frozen gates, and allocation-time versus pruning-time distinction. No implementation tests exist or ran in this planning task. Required Markdown lint is run after writes.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No code, tests, materialization, dry-run wrapper execution, git, GPU/API work, or fleet reservations. I data and timing receipts do not yet exist. Later scientific training/analysis is outside this preparation plan.

## Open questions

- A1 directory conventions: plan accepts explicit per-task source-path mapping instead of guessing. I train/validation and neutral twins remain prerequisites for matched production data.
- Runtime gate uses total-process fixed cost plus conservative scaled pruning time, then20% reservation buffer. Real pilot/hardware coverage and ledger costs are required before a fleet recommendation; D-only timing cannot approve it.
- If matched training count falls below200, the plan surfaces the count for lead scientific review while keeping D/I identical. It does not invent replacement samples or train on held-out ids.
