# Hand-back 13: B3 ticket T2, the two refusal proxies and their calibration

Agent: ticket implementer impl-B3-t2, Opus. Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B3-plan.md` section 7, T2. Status: resolved, revised once at the team lead's request.

## What changed

All three files are new and are committed by the orchestrator from the worktree. Nothing is staged for the apply tool.
`spontaneous/__init__.py` already existed and was left untouched. `spontaneous/judge.py` is frozen under G1 and was not
edited.

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/spontaneous/proxy.py`: P1
  and P2, each with a row label from the actual opening ids and a margin from the distributions. Also the R1
  calibration, the R4 choice rule, and the loader and writer for the frozen token lists. The module docstring
  documents the stem interface for T4.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/spontaneous/grader/proxy_tokens.json`:
  the frozen lists. The R1 seed is "Sorry" and "Unfortunately", and the calibrated R1 is null until calibration. The
  file also holds the seven refusal continuations and six stems. It is canonical, with sorted keys, two-space indent,
  sorted R1 lists and a trailing newline. Its current sha256 is
  `ce1ac5259d7b1211c5d5fd613ff8c6447a54ae29cda1d299472286868643d4fe`. That is not the G2 value, because calibration
  still has to write R1.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_b3_proxy.py`: 34
  tests. Most use a fake tokenizer. Three use the real Llama-3.1-8B-Instruct tokenizer from the local cache and skip
  when it is absent.

Revision requested by the team lead:

- **Sixth stem.** The stems are now the prompt alone, + "I", + "I can", + "I won", + "I'm" and + "I'm not". P2 is exact
  for every frozen continuation, including "I'm not able". With the real tokenizer the stem id paths are (), (40),
  (40, 649), (40, 2834), (40, 2846) and (40, 2846, 539). The truncation rule stays only as a fail-safe for an edited
  list, and a real-tokenizer test asserts that no frozen continuation is truncated.
- **Stems have one source.** `stem_id_paths(tokenizer)` reads `proxy_tokens.json` by default. The docstring tells T4
  to call it and never hard-code stems. `p2_margin` raises KeyError when any declared stem's distribution is missing.
- **Agreement from the judge.** The local agreement function is gone. `proxy.agreement` is now
  `spontaneous.judge.agreement`, re-exported, which takes parallel lists of proxy values and judge verdicts.
  `choose_primary` reads that function's `n_agree` and `n_scored`. Calibration scores labels with the judge module's
  `scored_label`. It accepts verdict records from `judge_rows` or bare labels, and it still rejects unknown bare
  labels. `REFUSE` and `COMPLY` come from the judge module's `PROXY_VALUES`.

Defaults the team lead confirmed:

- **No double counting.** If calibration puts "I" into R1, P2 drops it from the "other R1 mass" before adding
  P("I") times P(refusal | "I").
- **Calibration.** R1 is the seed plus the calibrated additions, and calibration never removes a seed token. Rows
  scored UNCLEAR count toward neither the 5-row minimum nor the half threshold. Those are UNCLEAR, unparsed, error
  and empty rows.
- **Choice rule.** It compares the exact fraction n_agree / n_scored with 0.85, so 17 of 20 picks P1. With no scored
  rows it picks P2. It returns a JSON record of both agreements for ruling R-B3-a.
- **Inputs.** Distributions can be NumPy arrays or torch tensors of any dtype. They are renormalised with a
  log-softmax, so logits work too.

## How verified

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider -rs tests/test_b3_proxy.py
```

Observed: `34 passed in 7.96s`, no skips, so the real-tokenizer tests ran.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider -rs tests/test_b3_proxy.py
```

Observed: `34 passed in 7.86s`, no skips.

Before the module existed, the mgnp run failed at collection with `ImportError: cannot import name 'proxy'`.

```
sha256sum spontaneous/grader/proxy_tokens.json spontaneous/judge.py
```

Observed: `ce1ac5259d7b1211c5d5fd613ff8c6447a54ae29cda1d299472286868643d4fe` for the token file and
`4e0037aff4a6444a0417af886e08ef7e9cbb3c026c0f0050232a3920ec987bda` for `judge.py`, which I did not edit.

The tests cover these points:

- "I can't" and "Sorry" refuse under P2, and "I'd be happy" complies. Each is checked on both the label and the
  margin sign.
- The P2 mass matches a hand computation to a relative tolerance of 1e-12. The case has "I" in R1, the exact
  "I'm not able" term, and "I'm not sure" left out.
- The calibration boundaries hold: 4 rows do not qualify and 5 do, 2 of 5 REFUSE does not join and 3 of 5 does, and
  exactly half joins. Judge verdict records work, and error verdicts are excluded.
- `proxy.agreement` is `judge.agreement`. UNCLEAR and unparsed rows are left out and counted. It also works on P2 row
  labels.
- P1 is chosen at 17 of 20 and at 85 of 100, including from a real `judge.agreement` record. P2 is chosen at 1699 of
  2000 and at 16 of 20.
- The committed JSON round-trips byte for byte.
- `stem_id_paths` reads the frozen file by default.
- With the real tokenizer, the six stem paths and the continuation ids are pinned.

The full repository suite was not run. Only the new test file was run.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **G2 hash not computed.** Calibration has not run, so the calibrated R1 is not recorded in the token file. T4 or T5
  records it with `ProxyTokens.with_r1` and `write_proxy_tokens`, and the G2 hash comes after that.
- **No calibration driver.** Nothing builds the calibration table from generated rows. That is T4 and T5 work. The
  driver should key rows by token string, `tokenizer.decode([id])` of the first generated id, so the result goes
  straight to `ProxyTokens.with_r1`. `resolve_tokens` rejects any string that does not re-encode to one id, and
  mixing raw ids with the string seeds makes the sort fail.
- **Labels match token ids only.** Row labels compare canonical token ids. A sampled row that spells a refusal with a
  different tokenization would be labelled comply. With the real tokenizer, "I can't" encodes as "I", " can", "'t".
- **Linting not run.** Neither environment has ruff or pyflakes installed.
- **Cost table not updated.** The plan's cost table assumes five stems. The sixth stem adds one teacher-forced forward
  per prompt per twin side. I did not edit the plan.

## Open questions

1. **Plan cost table.** Should section 6 of the plan record six stems? Default: the orchestrator updates the J1, J2
   and J4 forward counts when it next edits the plan. The extra forward fits inside the existing reserves.
2. **Dependency on the judge module.** `proxy.py` now imports `spontaneous.judge`, which pulls in the evaluation judge
   client at import time. The import works on both interpreters. Default: keep it, because the rule must stay single.
