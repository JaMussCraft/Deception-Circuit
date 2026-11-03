# Hand-back 11: independent review of the D2 follow-up result

Written Tue 3 Nov 2026 (Eastern time) by the Opus reviewer of direction `deception-divergence`. The substance is in
`reviews/06-d2-followup-review.md`. This file exists because the session's stop hook requires a hand-back, and it
only points to the review.

## What changed

- New file `reviews/06-d2-followup-review.md`: the review of the D2 follow-up read from job 50161975 under R15.
- No code, data, plan, spec or result file was edited.

## How verified

- Read-only scratch scripts in `/u/swong2/.claude/jobs/5b9b1c28/tmp/` on the mgnp interpreter re-ran the read on
  the stored features and checked every hash and manifest. They also recomputed the `C_HI` logits per condition,
  their splits by clause, frame and lie word, and the clustered intervals of the logit shift and interaction.
- `tests/test_d2_followup.py` passes, 43 of 43, on mgnp.
- `research-session lint` passes on the review and on this file.

## Execution evidence

- The re-read equals the stored `readings.json` except 10 non-coefficient floats at the last bit.
- All nine manifests are pre-registered, on the pinned stack and direction, with zero fallback firings and 5,481 rows.
- On FAR's act-form ids, the mean `C_HI` logits are D 8.01, I 5.66, HI -8.03 and IH -6.52. D minus I is 2.35
  [0.92, 4.34] by D clause.

## What is NOT done

- No git, Slurm or GPU was used.
- The SDR and SER compliance-like component and the FAR wording analysis are descriptive. Nothing about them is
  pre-registered.

## Open questions

- Whether the finding adopts the qualifiers in the review's Verdict, in particular the saturated readout and the
  rewording of "clause-driven on every task".
- Whether the user wants the frame-prefixed minimal-pair design proposed in the review's Verdict (b), which needs a
  new ruling.
