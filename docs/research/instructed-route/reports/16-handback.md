# Hand-back 16: B3 T5, the judge and premise entrypoints

Agent: ticket implementer, Claude Opus 5.5. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B3-plan.md`, section 7, ticket T5. Status: resolved; no commit (the orchestrator commits by file list).

## What changed

Committed by the orchestrator from the worktree. All files are new; no frozen G1 file was touched.

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/spontaneous/rows.py` holds the row schema T4 must write, documented in the module docstring. Rows carry `row_id` from `make_row_id`, in the form "split:variant:query_id:condition:sample" with greedy as -1, and `first_token_text` and `opening_ids`. They also carry sparse top-K log-probs at the six stems, which are required on greedy rows. The module also has the loaders and an exact sparse-to-dense readout that raises when a needed id was not stored.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/spontaneous/premise.py` holds pure functions. They compute the gap as an exact `Fraction`, the scored-query rule, the paired bootstrap and the pass rule. They also implement the variant rule with its tie-break, calibration, proxy agreement through the frozen `judge.agreement`, the verdict, and the Sonnet and re-judge comparisons through `judge.flip_report`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/b3_judge.py` has four stages: calibration, main, crosscheck and rejudge. `--ledger` is required, and a live run refuses an absent or invalid ledger before any call. It also refuses when the requests exceed the attempts left in the ledger. `--dry-run` makes no call and writes no file. Labels carry `response_id` and `cost_usd`. The script writes `run_manifest.json` with `grader` set to the G1 fingerprint. The seam for tests is `main(argv, transport=)`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/b3_premise.py` runs calibration, and the verdict when `--labels` is given. `--write-tokens` writes the calibrated file and prints its sha256 for G2. The verdict stops when the frozen R1 differs from the R1 the calibration labels give. The manifest's `grader` is G1 plus the token file's sha256. The seam for tests is `main(argv, tokenizer=)`.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_b3_premise.py` holds 58 tests. It reuses the `FakeTokenizer` from `tests/test_b3_proxy.py` and sets `DC_RUN_MANIFEST_GIT=0`.

Staged for the apply tool: none.

## How verified

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_b3_premise.py tests/test_b3_judge.py tests/test_b3_proxy.py
```

Observed: `131 passed in 9.49s`.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_b3_premise.py tests/test_b3_judge.py tests/test_b3_proxy.py
```

Observed: `131 passed in 14.36s`.

The tests cover the following:

- The gap on a hand-built 3-query table is 20/3.
- The bootstrap is deterministic, matches the p1c recipe and gives (-14.0, 34.0) on a fixed array. A standalone draw gave the same indices and interval on numpy 1.26.4 and 2.5.1.
- Fifty queries at 0.7 against 0.6 give a gap of exactly "10" that passes.
- The pass rule passes at exactly 10, 50 and 0.80, and fails just below each bar.
- The variant rule covers V-B larger, V-A larger, a tie, V-B missing and V-B with no scored query.
- The judge script fails argparse without `--ledger`. It returns 2 for an absent ledger, and the transport is never called.
- The dry run calls nothing and creates no output or cache file. It reports $0.20008 per Haiku request.
- The live mocked run settles `cost_usd` in the ledger and writes a manifest whose `grader.b3_judge_sha256` is 2e819a46... and equals `judge.b3_judge_sha256()`.
- The written token file round-trips byte for byte, and its sha256 changes when R1 changes.

After the stem-key fix in `rows.py`, `tests/test_b3_premise.py` was rerun alone on both interpreters. Observed: `58 passed` on base 3.9 and `58 passed` on mgnp.

```
/u/swong2/.conda/envs/mgnp/bin/python /u/swong2/.claude/jobs/230e4716/tmp/rt.py
```

This script encodes and decodes 16 likely openers with the cached Llama-3.1-8B-Instruct tokenizer. The openers include "Sorry", "Unfortunately", "I", "Sure", "Here", "**", a newline, "Certainly" and " I". Observed: every opener is one id and round-trips through decode and encode.

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/b3_judge.py --rows x --stage main --cache c --out o
```

Observed: `b3_judge.py: error: the following arguments are required: --ledger`.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- The scripts have not run on real rows, because T4 does not exist yet. Neither script has been dry-run against real generation output. The real Llama tokenizer path of `b3_premise.py`, `AutoTokenizer.from_pretrained`, was not exercised; the tests inject the fake tokenizer.
- No paid call and no ledger were made. The orchestrator creates each stage's reviewed header.
- The plan's risk note says to report the gap "on doubly-agreed rows" if the re-judge flip rate exceeds 0.10. That is not computed, because only a 10% sample is re-judged. The verdict sets `rejudge.above_0_10` so the case is flagged.
- T4 must conform to the schema in the `spontaneous/rows.py` docstring. I did not message T4's implementer, because T4 has not been assigned.

## Open questions

1. **Which rows calibrate R1 and the primary proxy?** I used only the chosen variant's calibration rows, sampled and greedy, both conditions, because the test runs that variant. The default is to keep this. The alternative is to use all 880 calibration rows across both variants.
2. **When is a query scored?** A query is scored when both conditions have all ten sampled rows with a label and none has status `error`. Unparsed and empty verdicts count as UNCLEAR in the denominator. The default is to keep this, and the ruling should record it before the test judge run.
3. **Does the 0.80 agreement include greedy rows?** It covers every judged test row, sampled and greedy, as plan section 1.7 says. The default is to keep this.
4. **What R1 do T4's stored margins use?** T4's stored `margins` on calibration rows use the seed R1, and consumers recompute them with `rows.row_margins`. The default is to have T4 store top-K with K of at least 256, plus every first token seen in calibration, so the recomputation is exact.
5. **Should the re-judge and cross-check draw different rows?** Both samples default to seed 20261101 over the same sorted test row ids, so the 220 re-judge rows include the 200 cross-check rows. The default is to keep it, because the overlap is harmless and lets the three judgements be compared on those rows. The alternative is to pass a different `--sample-seed` to the re-judge.
6. **What happens when a joined R1 token does not re-encode to one id?** Calibration keys R1 by `first_token_text`, and `proxy.resolve_tokens` raises when a joined string does not re-encode to exactly one id. Calibration then stops and names the token. The 16 likely openers I checked all round-trip. The default is that the orchestrator drops such a token by hand and records the drop as a ruling before G2.
