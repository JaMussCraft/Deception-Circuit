# Hand-back `09`: A1 builder independent review

Agent: independent code reviewer, Sol. Ticket: specificity-ladder plan-a1 Task one. Status: resolved; approve the scoped builder after the fixture correction.

## What changed

Review report only. The implementation was inspected directly; no implementation or test files were edited by this reviewer. No worker narrative handback was read.

- Orchestrator-owned worktree report: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/09-a1-builder-review-handback.md`.
- Required primary copy: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/09-a1-builder-review-handback.md`.
- No staged apply operations.

The reviewed files are `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/build_user_inversion_v2.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/user_inversion_requests_v2.json`, and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_user_inversion_v2.py`.

## How verified

Read the START, specification, Task one plan, builder, frozen requests, tests, actual source dataset schemas, and both reused alignment helpers. Source validation checks unique paired ids, pressure ids, neutral-clause metadata, reversed labels, designation metadata, and the exact pressure-only transformation from D to H. Construction keeps H's system and assistant text, appends requests in the actual user turn, inherits each arm's correct label orientation, and moves old behavior columns into source metadata. Both request contrasts and item swaps receive full-token proofs. The explicit optimized-Python refusal protects assertion-based helpers.

Padding is deterministic, ordered by added-token cost and repetition count, and accepted only after both streams pass full-prompt checks. The frozen task-aware requests retain transparent framing and do not label SDR/SER true alternatives false. Source neutral prompts cannot become the new baseline. Hashes, spans, readouts, source counts, pressure strata, padding choices, and rejections are recorded.

Direct logs inspected:

```text
/tmp/user-inversion-final-mgnp.log
/tmp/user-inversion-final-base.log
/tmp/user-inversion-fixture-green.log
```

The first two surrounding-suite logs each show 223 passing tests and two failures. One is the documented pre-existing hyperparameter mismatch, 120 against the required 128. The other was the new padding-priority fixture at `tests/test_user_inversion_v2.py:145`: its request was the single letter `a`, which legitimately matched text already present in the source and yielded no pair. The minimal correction changes that fixture to the absent word `Quizzical`, retaining its six-token difference and expected padding. Direct inspection shows production code was unchanged for this correction. Evidence: `/tmp/user-inversion-final-mgnp.log`, `/tmp/user-inversion-final-base.log`.

The direct focused correction log corresponds to:

```bash
env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_user_inversion_v2.py -k 'fewer_repetitions or duplicate_unpadded'
```

Observed in that log: two passed, seventeen deselected. This command was run by the implementation worker; the reviewer inspected its direct output without duplicating it.

Both surrounding logs contain the actual cached-tokenizer derivation JSON. Each task accepts 200 of 200 training rows, 200 of 200 validation rows, and 1,000 of 1,000 test rows, with zero rejections: 4,200 of 4,200 overall. Request and pressure strata account for the accepted rows. FAR adds zero tokens; SDR records inversion padding [0, 3], baseline padding [1, 0], sixteen added tokens; SER records inversion padding [0, 1], baseline padding [0, 0], three added tokens. The overall count is derived by summing the split counts in `/tmp/user-inversion-final-mgnp.log` and `/tmp/user-inversion-final-base.log`. These are tokenizer-construction counts, not behaviorally filtered pool sizes.

## Execution evidence

Not applicable: no runs.

This is a static review plus inspection of externally generated CPU test logs. No research experiment, GPU job, model inference, API call, or notebook execution was performed by the reviewer. No run manifest or full-commit experiment provenance exists for this review, so it makes no verified scientific-result claim.

## What is NOT done

No remaining correctness findings within Task one. The fixture failure is corrected and its focused regression passes. The final full changed-file reruns on both interpreters were still in progress when inspected; the implementation worker owns those runs, and the orchestrator must consume their terminal logs before committing. Their paths are `/tmp/user-inversion-final-focused-mgnp.log` and `/tmp/user-inversion-final-focused-base.log`.

Task two scoring, Task three CLI and jobs, behavioral screening, the pool-size gate, and causal specificity tests are intentionally outside this review. Construction acceptance does not establish model competence or specificity. No broad test suite was rerun by this reviewer.

## Open questions

None for the scoped code review. Default: approve Task one code, require the implementation worker's terminal dual-interpreter checks before committing, and retain the documented hyperparameter failure as a baseline limitation.
