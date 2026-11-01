# Hand-back: A1 paired scoring independent review

Agent: Codex Sol reviewer. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a1.md`, Task `2`. Status: resolved, approval with no blocking findings.

## What changed

Review only. No implementation files changed. Reviewed the approved START, specification, data contract, Task `2` plan, direct scoring code and tests. The implementation handback was not read.

- Commit from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/13-a1-scoring-review-handback.md`.
- Matching primary report: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/13-a1-scoring-review-handback.md`.

## How verified

Direct static inspection covered `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/build_user_inversion_v2.py`, its test file, and the actual `contingency.stream_words`, `_deceptive`, `_honest` and `deception_common.score_prompts` implementations.

The scoring boundary sends clean and swapped prompts from both arms with canonical words taken from inversion D labels. H labels therefore cannot reverse baseline orientation. Native margins, logits, argmax ids, decoded argmax and choices survive unchanged; the code deliberately avoids recomputing model-dtype subtraction from promoted scalar logits.

Filtering requires opposite full-vocabulary argmax and the supported margin in both streams. Exact boundary and immediately-below-boundary tests exist for each stream and threshold. Baseline competence requires honest argmax and the diagnostic margin in both streams, but baseline failure does not alter inversion membership.

Validation covers complete arm/stream dictionaries, finite margins and native logits, required argmax fields, canonical expected answers, signed-margin consistency, canonical JSON prompt hashes, duplicate ids, lengths and exact id order. Prompt or answer changes fail the filter. This is sufficient for Task `2`; model/source receipt validation belongs to the explicitly deferred CLI and materializer boundary.

Metrics distinguish full-vocabulary choice from binary margin wins and ties. Each stream uses the number of paired ids as denominator. Joint rates require both streams to satisfy the category and intentionally need not sum to unity for mixed outcomes. Joint margins average within id before paired subtraction. Empty rates remain undefined; signed gap distributions include zero and negative counts. No causal removal or specificity verdict is computed.

Commands used to inspect the existing test evidence:

```bash
head -n 15 /tmp/a1-scoring-green-mgnp.log /tmp/a1-scoring-green-base.log /tmp/a1-scoring-related-mgnp.log /tmp/a1-scoring-related-base.log
```

```bash
tail -n 5 /tmp/a1-scoring-green-mgnp.log /tmp/a1-scoring-green-base.log /tmp/a1-scoring-related-mgnp.log /tmp/a1-scoring-related-base.log
```

Observed focused results: 53 passing tests in each interpreter, with the test file and correct worktree shown in `/tmp/a1-scoring-green-mgnp.log` and `/tmp/a1-scoring-green-base.log`.

Observed related results: 148 passing tests in each interpreter, covering contingency, original inversion and matched-honest modules in `/tmp/a1-scoring-related-mgnp.log` and `/tmp/a1-scoring-related-base.log`.

These are direct log observations, not fresh test executions or measured model behavior. No concrete uncovered flaw warranted a focused reproduction.

## Execution evidence

Not applicable: no runs.

No GPU, API, inference, notebook, git command or test suite was run by this reviewer. Existing local CPU test logs were inspected; they do not contain a model run manifest or establish a scored control pool. Scientific results remain not yet verified by this review.

## What is NOT done

Task `3` CLI, manifests, score receipts, split assembly, wrapper, pilot, full-pool scoring and the full ladder remain outside this review. No pool-size milestone or inference validity is approved. Before scoring, retain the planned protected-set registry check and CPU acceptance gate. The assembler must still capture every rejection reason and enforce the complete data contract rather than treating these helper checks as a substitute.

## Open questions

None blocking Task `2`. Default: accept the scoring/filter/metrics implementation and proceed to the separate Task `3` review when its code and execution evidence exist.
