# Hand-back 07: Crossed ladder implementation plan

Agent: Codex Sol research worker. Ticket: ladder planning. Status: resolved.

## What changed

- Orchestrator commit file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-ladder.md`.
- Required handback mirrors: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/07-ladder-plan-handback.md` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/07-ladder-plan-handback.md`.
- Plan defines sampling/donor design, native joint patch scorer, effect and uncertainty calculations, IOI adapter, neutral MMLU floor and staged pilot. Per the subsequent lead ruling, same-instance same-stream conditional twin replacement is the required crossed cell; independent different-id resampling is optional. It records unsupported mappings and freezes assessment apart from mover selection.
- No code, builder module, tool-owned record, or other planning file edited.

## How verified

```text
/u/swong2/.local/bin/research-session lint docs/research/specificity-ladder/plan-ladder.md
```

Observed: exit success with no output.

```text
/u/swong2/.conda/envs/mgnp/bin/python scripts/check_report_numbers.py docs/research/specificity-ladder/plan-ladder.md
```

Observed: prospective constants and source citations inspected; scanner output saved at `/tmp/specificity-ladder-plan-numbers.txt`. All assay thresholds are inherited from START/spec or explicitly proposed defaults; no measured performance numbers are asserted. Future implementation paths are intentionally absent.

Source inspection covered native knockout/hooks/DLA and sampling interfaces, direct IOI task/dataset code, local benchmark sources and question formatter. A local-only source lookup found the MMLU cached snapshot named in the plan; reading its parquet schema succeeded. Original selection sample files exist under primary artifacts, with ids stored as `instance_ids`; the corresponding output directory is absent from the worktree. No network request or model inference occurred.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No implementation, unit suite, GPU/API work, model scoring, notebooks or git.
- No behavioral validation of donor eligibility, mover candidates, baseline competence, positive control or inference tolerance.
- No benchmark grader registration: the lead must resolve registry tooling before MMLU scoring.

## Open questions

- Lead ruling applied: the required crossed resample cell is deterministic same-instance same-stream replacement, D from original H and I from its own H-derived user-neutral. H from itself is a labeled degenerate no-op and cannot establish H preservation; item-swap, zero and H mean assess H nontrivially.
- Independent different-id same-answer donors remain optional robustness. Missing support cannot block the required crossed assay. F from same-id H is scored only with supported alignment; otherwise report that cell limitation without fabricating a mapping. No donor terminology implies randomness for deterministic twins.
- IOI has an answer-erasing corruption, and MMLU lacks a native H or item-swap control. Proposed default: use IOI collateral with that caveat; MMLU stays a small neutral utility floor under zero and H mean, with its stated additional-error guard and uncertainty.
- The candidate mover rule measures answer contribution, not validated copying. Proposed default: retain an empty/unsupported screen and the full set rather than invent movers.
