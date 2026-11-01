# Hand-back 11: B2 ticket T5, per-token direct logit attribution

Agent: Opus implementer (claude-opus-5-5). Ticket: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B2-plan.md`, section 6, T5. Status: resolved.

## What changed

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/component_analysis/dla.py`. A new section after `_difference_over_rows` adds `component_token_logits(model, capture, keys, token_ids, centre=True)`, two private helpers (`_fixed_scale_normed`, `_mean_unembedding_row`) and the constant `MEAN_ROW_CHUNK = 8192`. It returns `[batch, k, n_tokens]` in fp32. `token_ids` is `[batch, n_tokens]` per row, or 1-D `[n_tokens]` read on every row. The norm arithmetic mirrors `hooks.readout_logits` with `scale_from` in the same order. Only the gathered `lm_head` rows are multiplied. Centring subtracts each contribution's projection on the fp32 mean unembedding row, which is accumulated in chunks of 8192 rows so no 2 GB fp32 copy of the 8B `lm_head` is made. The change is a pure insertion: a diff against the primary checkout's copy shows only `507a508,600` and no removed lines, so every existing function is unchanged.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_dla_model.py`. Six tests are appended after line 488, again a pure insertion (`488a489,608`):
  - the Target column minus the Distractor column equals `component_logit_difference` to 1e-5, with and without centring;
  - the centred sum over every head, every MLP and the embedding equals the model's vocab-centred Readout logit per token to 1e-4, the existing completeness test's tolerance;
  - `centre=False` equals `fixed_scale_readout` gathered at the ids to 1e-5, and differs from the centred values;
  - a 1-D id list gives the same result as the list repeated per row;
  - a random vector added to every `lm_head` row leaves the centred values unchanged to 1e-4 and moves the raw ones. The test asserts the tiny model's `lm_head` is untied and restores the weight in `finally`;
  - a receiver key such as `("q", 0, 0)` is refused.

## How verified

All six new tests failed before the implementation, each with `AttributeError: module 'component_analysis.dla' has no attribute 'component_token_logits'`.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_dla_model.py tests/test_dla.py
```

Observed: `41 passed in 44.76s`.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider -rs tests/test_dla_model.py tests/test_dla.py
```

Observed: `16 passed, 1 skipped in 13.13s`. The skip is the module-level gate already in the file: `tests/test_dla_model.py:39: nnsight 0.5.12 is installed, not the pinned 0.7.0`. There were no failures, so there was nothing to compare with the baseline.

```
diff /projects/beto/swong2/Alignment/Deception-Circuit/component_analysis/dla.py /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/component_analysis/dla.py | grep -E "^[0-9]+[acd]"
```

Observed: `507a508,600`, and zero lines marked `<`.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- The full test suite was not run. Only `tests/test_dla.py` and `tests/test_dla_model.py` were run, as the ticket asks.
- The function was not run on the 8B model or a GPU. Memory per call is about `[batch, k, hidden]` fp32 for the contributions plus `[batch, n_tokens, hidden]` for the gathered rows. With every head and MLP of the 8B model at batch 8 that is about 140 MB. T6 can chunk keys if it needs to.
- `component_contributions` still runs one matmul per head. A full sweep over the 1,024 heads repeats `o_proj_weight(...).float()` per head, which is the existing behaviour and was not changed.

## Open questions

- `dla.py` reads the final norm and `lm_head` through `hooks._hf`, because no hook returns gathered unembedding rows and `hooks.py` is not this ticket's file. Other modules already do this, for example `component_analysis/selective_v6_attention.py:49`. Default: keep it, and add a `hooks.unembedding_rows` helper the next time someone owns `hooks.py`.
- The mean unembedding row is recomputed on every call. On the 8B model that is one pass over 128k by 4096 bf16 values per batch, which is cheap on a GPU. Default: leave it uncached, since a cache could go stale if weights change, as they do in the shift test. If T6 profiling shows a cost, T6 can add an optional precomputed-row argument.
