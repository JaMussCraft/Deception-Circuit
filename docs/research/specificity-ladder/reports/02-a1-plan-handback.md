# Hand-back 02: A1 control implementation plan

Agent: Codex Sol research worker. Ticket: A1 planning. Status: resolved.

## What changed

- Orchestrator commit file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a1.md`.
- Required handback mirrors: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/02-a1-plan-handback.md` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/02-a1-plan-handback.md`.
- Plan defines paired builder, task-aware exact requests, neutral padding checked against full tokenization, canonical scoring/filter interfaces, split-preserving staged CLI, CPU gates, and a bounded GPU pilot. It reconciles the lead specification. Crossed ladder implementation is deferred to its own task; its mover criterion and scientific defects are recorded.
- No tool-owned records edited and no operations staged.

## How verified

```text
/u/swong2/.local/bin/research-session lint docs/research/specificity-ladder/plan-a1.md
```

Observed: exit success with no lint output, after final revision.

```text
/u/swong2/.conda/envs/mgnp/bin/python scripts/check_report_numbers.py docs/research/specificity-ladder/plan-a1.md
```

Observed: scanner listed prospective constants, task labels and future artifact paths. Manual reconciliation: scientific thresholds/caps come from START/spec; the new token cap comes from the lead spec; padding bounds, pilot limit, batch size and initial reservation are proposed implementation choices. The plan explicitly labels numerical provenance; no listed number is an empirical claim. Future paths belong to implementation and are intentionally absent.

```text
/u/swong2/.local/bin/codex-usage --pause-at 80
```

Observed: live status ok, weekly used three percent, remaining ninety-seven percent, should_pause false, reset November sixth at 11:07 am EST. Read at the handback checkpoint.

Source inspection included the inversion builder, matched-honest assertions, contingency filter, dataset scoring, twin dataloaders, DLA functions and real first-row prompts loaded from each task's original D/H test split. No model inference occurred.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No implementation, tests, GPU/API work, notebook execution, git, or dataset/output edits.
- Real-tokenizer padding feasibility is an explicit CPU gate, not an established fact. The bounded neutral-padding grammar may reject rows and needs coverage inspection before full scoring.
- No full crossed ladder, unrelated-task or MMLU scoring, or response-turn fallback implementation is designed here.

## Open questions

- If the frozen padding grammar has inadequate alignment coverage, report rejected counts and revise the grammar before observing full model scores; never bypass alignment assertions. Default is to preserve semantic neutrality and recorded failures.
- Inversion pool size alone cannot establish a usable effect denominator; the baseline-competent paired subset and signed gaps must be reported separately. Default is no causal specificity claim from this phase.
- Larger user prompts shift positions versus original D/H/F. Default is to retain this caveat and settle donor position correspondence in the subsequent crossed-ladder task.
