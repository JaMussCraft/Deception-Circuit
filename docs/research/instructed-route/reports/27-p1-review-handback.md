# Hand-back 27: independent review of B2 P1, the falsity probe

Agent: independent reviewer (Opus), session claude-230e4716, direction instructed-route. Brief: review hand-back 25,
the B2 P1 falsity-probe result. CPU only. No Slurm job, no git, no research-session command, and no frozen file edited.
The review itself is `docs/research/instructed-route/reviews/04-p1-review.md`. This file exists because the session's
stop hook requires a hand-back. The lead's brief allowed only the review file under `docs/research`, so the lead
should decide whether to keep this file.

## What changed

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reviews/04-p1-review.md`:
  the review, with the headings Verdict, Checks, Problems found and Proposed finding text.
- This hand-back.
- Scratch scripts and their output, outside the repository, in `/u/swong2/.claude/jobs/230e4716/tmp/rev04/`:
  `a_prec.py`, `b_probe.py` and `c_more.py`, with their `.out` files.

No source file, output file or frozen document was edited.

## How verified

Every command ran from the worktree on the mgnp interpreter with one BLAS thread:

```
PY a_prec.py outputs/_analyses/instructed-route-b2/p1-cap data/datasets
PY b_probe.py outputs/_analyses/instructed-route-b2/p1-cap outputs/_analyses/instructed-route-b2/p1-probe <worktree>
PY c_more.py  outputs/_analyses/instructed-route-b2/p1-cap outputs/_analyses/instructed-route-b2/p1-probe
```

- **`a_prec.py`** rebuilds the bf16 readout independently of the worker's script. It also checks every non-I cell
  against every margin field of its D record.
- **`b_probe.py`** recomputes the rule number and the controls with its own AUROC and its own clustered bootstrap. It
  also recomputes the selection table, tests that the saved weights are optimal on the fit rows only, checks for id
  and clause leakage, and examines the structure of the permutation null.
- **`c_more.py`** covers the neutral-sentence overlap, the score shifts as a share of the D shift, the I-against-H
  per-token attribution and the margin tails per cell.

## Execution evidence

**Verdict: as stated, with caveats.** The full numbers are in the review.

| check | result |
| --- | --- |
| SER D against H at layer 17, C 0.001 | AUROC 0.99993, CI 0.99983 to 1.0 |
| selection table, recomputed against `p1_fit.json` | differs by at most 0.0 |
| eligible layers in the tie | all 28 |
| HI against H on the select split, every eligible layer | at least 0.943, so no layer could give "clean" |
| bf16 rebuild, I cells, exact match | 0.990 to 0.997 |
| bf16 rebuild, other cells, exact match | 0.315 to 0.476 |
| sign flips, 9,972 rows | 0 |
| rows within two ulps | 97.5% |
| ids shared between fit or select and any test cell | 0 |

- **Own field.** Every cell is nearest its own record field.
- **Neutral-sentence overlap.** 325 SER H rows reuse FAR fit neutral sentences. Splitting the rule number on that
  overlap leaves it unchanged, at 0.99991 against 0.99997.
- **Inversion against H, per-token, my addition.** On SER, inversion lowers the honest item by 2.65 and raises the
  deceptive item by 3.15. D does 3.09 and 3.09. On FAR, inversion gives 5.21 and 5.19 against D's 4.73 and 5.05.
- **Score shift as a share of the D shift.** Inversion moves it 0.91 on FAR and 1.17 on SER. The honest instruction
  moves it 0.09 and 0.13, and no clause 0.02 and 0.06.
- **Random directions.** Isotropic random directions reach a SER AUROC of 0.978.

## What is NOT done

- **No FINDINGS row was written.** The review proposes F-rte-003 for the orchestrator.
- **The inversion attribution has no intervals.** I did not compute clustered CIs for the inversion-against-H
  attribution.
- **The cause of the drift is not proven.** Proving the build-drift cause behind the D, H, HI and F margins would
  need a GPU rerun, which the brief excluded.
- **No lint was run.** I did not run `research-session lint` on either file, because the brief excluded
  research-session commands.

## Open questions

1. **The no-clause controls.** They score 0.681 and 0.624, and the plan says anything far from 0.5 means a broken
   probe. The orchestrator should rule; the review reads the result as weak answer-confidence leakage.
2. **The read step.** Should `falsity_probe.py read` gain an inversion-against-H contrast before R2's per-token
   reading is used?
3. **The margin bar.** Should the frozen margin bar be recorded as failed and explained by precision, or restated?
   If restated, the review recommends a tail bound and the own-field gap instead of the proposed bar.
4. **Missing manifests.** The probe output roots have no run manifest. Should one be added?
