# Hand-back 22: independent review of the B2 P3 result, the SER MLP replication

Agent: independent reviewer (Claude Opus 5.5), session claude-230e4716. Brief: the team lead's review request for job
23412229. Status: done.

## What changed

I wrote `docs/research/instructed-route/reviews/01-p3-review.md`, the verdict, five checks and a proposed FINDINGS row.
No code, results or outputs were changed. Throwaway check scripts live in the job's temporary directory only.

## How verified

I recomputed every R-cls class from the 21 `knockout/groups.json` files with `component_analysis/rcls.py`. All 42 rows
of `p3_rcls.csv` agree (0 mismatches). I compared the seed-0 cells per instance with the original S1, S5 and S6
sweeps, and the seed-1 clean margins with the mechanism-analysis held-out runs. All matched to 0.0. I checked every
manifest, id file, id overlap and per-cell instance count. `research-session lint` passes on the review.

## Execution evidence

Not applicable: no runs. CPU-only reads with the mgnp interpreter.

## What is NOT done

- I did not resolve which tracked file made 20 of 21 cells `git_dirty`, because that needs git. The empirical
  reproduction shows it did not change a number.
- No seed-2 cell was rerun to test determinism directly.

## Open questions

- The brief names 4ba00fc as the branch commit, but all manifests record a7827d4. The FINDINGS row should carry a7827d4.
- mlp.13 is deception-leaning on FAR in seed 2 (ratio 1.34) and misses by 1% in seed 1. The orchestrator should decide
  whether the new F-rte row drops "SER alone" from the F-mech-009 wording. The proposed row in the review does.
