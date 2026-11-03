# Hand-back 09: independent review of the D2 follow-up plan

Written Mon 2 Nov 2026, about 11:40 pm EST, by the Opus plan reviewer of direction `deception-divergence`. The
substance is in `reviews/05-d2-followup-plan-review.md`. This file exists because the session's stop hook requires a
hand-back; the lead asked for one file only, so it only points to the review.

## What changed

- New file `reviews/05-d2-followup-plan-review.md`: the review of `plans/D2-followup-plan.md` before ruling R15.
  The verdict is to freeze the plan with named amendments.
- No code, data, plan, spec or result file was edited.

## How verified

- Five read-only scripts in the job scratch directory `rev05/` on the mgnp interpreter. They compare the 50 pool
  texts with the plan table, render one D prompt per task, list the act-form I clauses and cluster sizes, run
  `build_inversion_v2._fits` on the proposed rewrites over every row that uses them, and print the 37-pair table.
- I checked the D2 manifests and timings under `results/d2/job50155519/`, and the sha256 of the stored refusal
  direction.
- `research-session lint` passes on the review.

## Execution evidence

- The pool hash matches the plan: `c03fc1fb…8ac`. All 50 texts, forms, token counts and word diffs reproduce.
- The SDR 15 and SDR 18 rewrites fit 34 of 34 and 63 of 63 rows, with token counts 13 and 11 and full-prompt
  difference 0.
- The refusal direction hashes to `3e03edcd…f0cf0`, which matches its manifest.
- The measured rates reproduce the 0.41 GPU-hour estimate.

## What is NOT done

- I did not rerun the full-prompt fit over all 1,909 HI rows. The dry run must reproduce it.
- I did not check the full-prompt fit of the proposed IH mirrors, only their standalone token counts.
- No git, Slurm or GPU was used.

## Open questions

- Whether R15 adds the IH frame-control arm or states that a (c) alone does not re-admit U1 (review 05,
  recommendation 2).
- Whether R15 adopts the remaining amendments, recommendations 3 to 14 of review 05.
