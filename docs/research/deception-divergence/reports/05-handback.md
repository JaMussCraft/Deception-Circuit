# Hand-back 05: independent review of the D1 gate

Agent: Opus reviewer (claude-opus-5-5), direction deception-divergence. Ticket: the lead's review request of Mon 2 Nov
2026 for the D1 result and hand-back 01. Status: resolved. This file is a pointer that the stop hook requires. The
review itself is `docs/research/deception-divergence/reviews/02-d1-review.md`.

## What changed

- New: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reviews/02-d1-review.md`.
- New: this pointer file.
- No code, outputs, `state.json`, `worklog.json`, `ledger.json` or `WORKLOG.md` were touched. No git was run.

## How verified

Every verdict-bearing count, rate and interval in `readings.json` and hand-back 01 was recomputed from `scores.jsonl`
and the stored datasets with independent scripts outside the repository, in
`/u/swong2/.claude/jobs/5b9b1c28/tmp/d1rev/`. The per-cell matched-n tables were checked at their totals and smallest
cells only. The D1 tests were run on mgnp:

```
OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_d1_visibility.py
```

Observed: 31 passed in 90 s. `research-session lint` passed on the review.

## Execution evidence

No job was run. The recomputations ran on the CPU of the Delta login node. Counts and point estimates match exactly,
and intervals drawn with seed 7 agree with the reported seed within half a point.

## What is NOT done

- The D1 tests were not run on the base Python 3.9 interpreter.
- The full-suite failures in hand-back 01 were not compared with the baseline names (review issue 8).

## Open questions

- Should the D1 finding carry the review's two qualifiers before it is marked reviewed? The first is that the shared
  stakes clauses are not content-matched (issue 1). The second is that FAR's pooled scale dilutes the D-compliant
  phrasing-1 effect (issue 3). The review's default is yes, with the suggested wording in its Recommendation.
