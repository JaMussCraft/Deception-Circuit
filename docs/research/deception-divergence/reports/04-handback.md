# Hand-back 04: independent review of the D4 riders

Agent: Opus reviewer (claude-opus-5-5), direction deception-divergence. Ticket: the lead's review request of Mon 2 Nov
2026 for hand-back 02. Status: resolved. This file is a pointer that the stop hook requires. The review itself is
`docs/research/deception-divergence/reviews/01-d4-review.md`.

## What changed

- New: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reviews/01-d4-review.md`.
- New: this pointer file.
- No code, outputs, `state.json`, `worklog.json`, `ledger.json` or `WORKLOG.md` were touched. No git was run.

## How verified

Every number in hand-back 02 was recomputed with independent scripts outside the repository, in
`/u/swong2/.claude/jobs/5b9b1c28/tmp/rev_*.py`. Each rider's recomputation table is in the review. The D4 tests were
run on both interpreters:

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_d4_static_quartet.py tests/test_d4a_attention_instances.py tests/test_d4_after_cue.py tests/test_d4_jobs.py
OMP_NUM_THREADS=4 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q (same files)
```

Observed: mgnp 34 passed; base 30 passed, 4 skipped. `research-session lint` passed on the review.

## Execution evidence

No job was run. The recomputations ran on the CPU of the Delta login node.

- The P1 scores of all 320 senders match `static_quartet.json` to 1.2e-15.
- The P2 copy scores and mean ranks match exactly.
- The D4(b) margins at post_tag are bit-identical to J4 and its supplement.
- The D4(c) T1 and T2 numbers match `b1_readings.json` under my own clustered bootstrap.

## What is NOT done

- Nothing is left out of the review scope.
- The findings register is empty, so the F1 to F4 mapping in the review is my assumption: F1 is rider (d), F2 rider
  (a), F3 rider (b) and F4 rider (c).

## Open questions

- Should the wording of F3 and F4 take the review's issues 1 to 4 before those findings are marked reviewed? The
  review's default is yes.
