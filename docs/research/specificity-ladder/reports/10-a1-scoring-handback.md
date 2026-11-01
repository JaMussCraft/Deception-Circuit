# Hand-back 10: A1 paired scoring and filtering

Agent: Codex Sol worker. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/plan-a1.md`, Task 2. Status: resolved implementation; held for requested restart before independent review or commit.

## What changed

- Orchestrator commits `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/build_user_inversion_v2.py`: appended pure canonical scoring, validated inversion-only filtering, and paired metrics. Task 1 constructor and request pool were not edited.
- Orchestrator commits `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_user_inversion_v2.py`: appended 34 scoring tests, including parametrized cases. Existing 19 constructor tests remain.
- Report copies: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/10-a1-scoring-handback.md` and `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/10-a1-scoring-handback.md`. No staged operations.

### Frozen interface for Task 3

`score_pairs(pairs, score_fn)` calls the scorer once, in pair order, then inversion/baseline arm order, then clean/corrupt stream order. Its word pairs come from the inversion row through `contingency.stream_words` for BOTH arms. Return records have `instance_id`, `inversion`, and `baseline`; each arm has `clean` and `corrupt` dictionaries. Each dictionary preserves native `logit_a`, `logit_b`, `margin`, `argmax_id`, `argmax`, and `choice`, and adds:

- `expected_honest`, `expected_opposite`: canonical D answer words.
- `expected_honest_token`, `expected_opposite_token`: leading-space strings, matching `dc.encode_answer_token`. Tokenizer IDs cannot be obtained through the two-argument scoring callable; capture the tokenizer/revision in Task 3 provenance.
- `honest_minus_opposite`: native margin; `opposite_minus_honest`: its negation. Do not recompute native-dtype subtraction from separately promoted logits.
- `prompt_hash`: SHA256 of the exact prompt using existing `_hash`, which hashes UTF-8 JSON with sorted keys, compact separators, and `ensure_ascii=False`. This hashes the JSON string representation, not bare prompt bytes.

`filter_pairs(pairs,scores,margin=.7|.5)` requires matching ordered unique ids, exact prompt hashes, canonical words, complete native fields and finite logits/margins. It calls `contingency._deceptive` for inversion only. Baseline competence uses full-vocabulary honest argmax and honest margin at least 0.3 in both streams. Report keys: `margin`, `baseline_honest_margin`, `input_count`, `retained_count`, `rejected_count`, `rejected_ids`, `retention`, `paired_competent_count`, `paired_competent_ids`, `baseline_failure_ids`, `baseline_competence`, `all_metrics`, `retained_metrics`. Every rate record is `{count,denominator,rate}`; empty rate is `None`. Baseline failures remain in retained pairs. Paired-competent ids are diagnostic, not the unqualified pool.

`paired_metrics(scores)` returns `count` plus `clean`, `corrupt`, `joint`. Each scope contains each arm's `count`, `full_vocab` honest/opposite/other rate records, `binary` honest/opposite/tie rate records, and both signed margin means. Joint category counts require BOTH streams, with id denominator; mixed outcomes need not sum to one. Joint margins average streams within id. `response_gap` and `margin_gap` contain per-id inversion-minus-baseline opposite-response indicators and opposite-minus-honest margins, respectively: `count`, `values`, `mean`, `positive_count`, `zero_count`, `negative_count`. `opposite_rate_gap` aliases the response gap mean. Empty means are `None`. No causal removal percentages are computed.

## How verified

All commands ran in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder` through escalated terminal because sandbox setup was broken. TDD tests stub only native scoring; construction, validation, filtering and metrics execute real code.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_user_inversion_v2.py -k 'not real_tokenizer' > /tmp/a1-scoring-red.log 2>&1
```

Observed RED: `28 failed, 18 passed, 1 deselected in 7.13s`, missing new scoring/filter/metric interfaces. After initial implementation the same command with log `/tmp/a1-scoring-green-fast.log` gave `46 passed, 1 deselected in 7.91s`.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_user_inversion_v2.py -k 'score_prompt_hashes or incomplete_or_reordered or baseline_competence_exact' > /tmp/a1-scoring-hash-red.log 2>&1
```

Observed second RED: `3 failed, 3 passed, 47 deselected in 2.32s`. Failures were missing prompt hashes and missing-id rejection; reordering was already rejected. Hash implementation followed this run.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_user_inversion_v2.py > /tmp/a1-scoring-green-mgnp.log 2>&1
```

Observed GREEN: `53 passed in 37.84s`, including real cached tokenizer over all source rows.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_user_inversion_v2.py > /tmp/a1-scoring-green-base.log 2>&1
```

Observed GREEN: `53 passed, 2 warnings in 34.95s`. Warnings: old bottleneck dependency and deprecated TRANSFORMERS_CACHE.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider tests/test_contingency.py tests/test_inversion_v2.py tests/test_matched_honest.py > /tmp/a1-scoring-related-mgnp.log 2>&1
```

Observed: `148 passed in 29.31s`. These unchanged suites cover the reused canonical-word predicates, native-score conventions, and constructor alignment helpers.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider tests/test_contingency.py tests/test_inversion_v2.py tests/test_matched_honest.py > /tmp/a1-scoring-related-base.log 2>&1
```

Observed: `148 passed, 1 warning in 30.16s` (bottleneck dependency warning).

```bash
/u/swong2/.local/bin/codex-usage --pause-at 80
```

Observed latest reading: 5 percent weekly used, 95 remaining, should_pause false; reset 2026-11-06T16:07:41+00:00. No further work follows the restart HOLD.

## Execution evidence

- Local CPU pytest commands above; no model inference, GPU, paid API, Slurm job, git or notebook execution.
- Exit codes: focused final suites and both related suites exited 0; TDD RED runs intentionally failed.
- Counts: 53 of 53 focused tests passed on each interpreter; 148 of 148 related tests passed on each interpreter. The cached-tokenizer acceptance test ran, without skip.
- Baseline behavior: all original 19 constructor tests remain passing within each focused run; all 148 unchanged dependency tests pass. The broader known `test_hyperparameters_are_identical_across_the_three_mechanisms` failure was not rerun or claimed fixed.
- Provenance file: not applicable to CPU unit tests; no dataset/scoring manifest was created. Task 1 starting commit supplied by lead was `6c47504`; worker did not run git. Exact command logs are listed above.

## What is NOT done

- Independent review and commit remain with orchestrator. User requested restart HOLD after tests began; all running tests finished and no new test suites were started after HOLD.
- Task 3 CLI, file I/O, score manifest, dataset scoring provenance, protected-set recheck and GPU pilot are not implemented. Task 3 must freeze and verify prompt/source/request/score-file hashes and distinguish accepted scored datasets from raw derivation.
- No pool behavior or 300-id gate has been measured. Scorer tests use deterministic native-contract outputs; cached tokenizer work proves construction acceptance only.
- No broad repository suite was run; authorized verification was focused plus justified unchanged dependencies. No numerical inference equivalence or causal specificity claim follows.

## Open questions

- Default next action after restart authorization: independently review these two files and the RED/GREEN logs; commit Task 2 by explicit file list, then implement Task 3. Do not start inference merely because CPU tests pass.
- If Task 3 requires answer-token ids, obtain them from the tokenizer in its scoring wrapper/manifest. Keep canonical answer strings and the native scorer margin intact.
