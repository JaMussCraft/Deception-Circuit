# Hand-back 20: B2 ticket T7, the falsity-probe fit, score and per-token read

Agent: ticket implementer (Opus). Ticket: `docs/research/instructed-route/plans/B2-plan.md` section 6, T7 (with
section 1, section 8 and ruling R2 of `spec.md`). Status: resolved.

## What changed

All three files are new. The orchestrator commits them from the worktree. Nothing is staged for the apply tool.

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/component_analysis/probe.py`. It holds the pure pieces in numpy and torch only. These are standardisation, the float64 LBFGS logistic regression, the mass-mean direction and the Mann-Whitney AUROC with ties at one half. It also holds the cluster bootstrap and percentile CI, the permutation swaps, the frozen bands, the anti-aligned flag, the FAR gate fallback, the CI band-edge check and the R2 label.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/falsity_probe.py`. The CLI is `fit|score|read --capture DIR [--out DIR]`, and `--out` defaults to `docs/research/instructed-route/results`. The module docstring documents every output key of `p1_fit.json`, `p1_fit.pt`, `p1_probe.json` and `p1_tokens.json`. It also documents the row and layer convention and the cell lookup.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_falsity_probe.py`. It holds 38 tests. Its fixture writes a synthetic 18-cell capture by hand in the T6 format, with 33 rows, the 1,057 real key layout and a planted direction.
- This hand-back: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/20-handback.md`.

Design points the P1 run depends on:

- **Rows and layers.** Row 0 is the embedding and row l + 1 follows decoder layer l, as in `fig9_lens.csv`, where E16's layer 17 is row 18. "Layers 4 to 31 eligible" is therefore rows 5 to 32, and the tie target is row 18. Every output names both `row` and `layer`.
- **Stages.** `fit` writes the frozen artefact `p1_fit.pt` and `p1_fit.json`, which hold the standardisation, the weights for every row and C, the selection table and the selection. `score` and `read` never reselect.
- **Selection.** Each row takes its best C, and an exact tie goes to the smaller C. Among the eligible rows within 0.005 of the best, the layer nearest 17 wins. `check_selection_rows` raises on any row that is not a FAR validation select row, and `check_fit_rows` does the same for the fit split. Both read the row metadata, not file names.
- **Twins.** Every AUROC compares a cell's rows with its own H twins, joined on `instance_id`. Clusters are `pressure_id`, which twins share on 1000 of 1000 FAR test ids, checked on the login node. The probe is never flipped.
- **Excluded rows.** SDR I-reported rows flagged `in_seed0_sample` or `in_seed1_sample` are dropped, and the drop is counted. This is T6's open question 1, so the held-out sample is never read. HI rows under the 0.3 bar are dropped if any reached the capture.
- **Seeds.** The bootstrap uses `default_rng(20261101)`. The permutation null uses seed 20261102.
- **Non-finite residuals.** These are T6's float16 overflow. `fit` stops on any non-finite fit or select residual. `score` drops the affected pairs at the affected row and counts them.
- **Thread pinning.** `main` pins torch to one thread. On the 128-core login node, one 400 by 4,096 fit took 4.7 s with the default threads and 0.05 s with one.

## How verified

The test file was written first, and the first run failed at import:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_falsity_probe.py
```

Observed before the code existed: `ImportError: cannot import name 'probe' from 'component_analysis'`, 1 error during collection.

Observed after: `38 passed in 9.12s`.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider -rs tests/test_falsity_probe.py
```

Observed: `38 passed in 11.57s`, with no skips.

The tests cover every item in the ticket:

- **AUROC.** Hand values with ties match, a separable set gives 1.0, a reversed set gives 0.0 and equal sets give 0.5. A random tied set matches the pairwise count, and empty or NaN input raises.
- **Fit.** The fit recovers a planted direction with cosine above 0.9.
- **Selection.** Selection raises on any SER, FAR gate, SDR, fit or wrong-split row, through both `check_selection_rows` and `selection_table`. The tie and the eligibility rules are tested.
- **Rules.** The bands split at 0.75, 0.7499, 0.6 and 0.5999. Under 0.5 counts as literal falsity and sets the anti-aligned flag. The fallback flag sets at 0.7499 and not at 0.75. The R2 label logic and the CI band-edge flag are tested.
- **Determinism.** The bootstrap is seed-deterministic, both as a function and end to end through `score`.
- **Imports.** The module and the script import in a subprocess that blocks sklearn and scipy.
- **End to end.** `fit`, `score` and `read` run on the synthetic capture. The run includes the permutation null, leave-one-clause-out, the SDR sample drop, the fallback path, the non-finite refusal, the quartet's planted promotion of +1.0 and suppression of -0.5, and the Markdown files.
- **Head list.** `LATE_HONEST_HEADS` equals the `c_honest.heads` lists of `docs/research/mechanism-analysis/phase2/p2_readings.json`.

A login-node timing run used the same fixture at hidden size 4,096, with 2,000 resamples and 200 permutations:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python /u/swong2/.claude/jobs/230e4716/tmp/t7_e2e.py
```

Observed: `fit 5.3s`, `score 5.3s`, `read 1.8s`.

I ran no other test files. This ticket touches no shared module, so I made no baseline comparison.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **No real capture exists yet**, so `fit`, `score` and `read` have not run on P1 data. Every P1 number is not yet verified until the P1-cap job and this script have run.
- **Real-scale cost is estimated, not measured.** The fixture has 40 to 48 rows per cell, against the real 200 to 800. The real fit is 132 LBFGS fits on 400 by 4,096, at about 0.05 s each single-threaded. The 200 permutation refits cost about the same per fit. Loading the score cells reads about 2.7 GB of float16, one cell at a time.
- **No `run_manifest.json` is written by T7 itself.** `p1_probe.json` records the capture's manifest commit, or "not yet verified" when it is missing, and the sha256 of `p1_fit.pt`.

## Open questions

1. **Is "layers 4 to 31" decoder layers (rows 5 to 32) or residual rows 4 to 31?** Row 32 is the final residual. Default: decoder layers, following the plan's "row l+1 follows layer l" and the `fig9_lens.csv` convention. Under this default, row 32 is eligible and row 4 is not.
2. **R2 covers a misleadingness verdict that is not clean.** Default: any misleadingness verdict that is not clean is labelled "instruction-confounded". With SER D at 0.75 or more, a FAR I or HI cell at 0.6 or more is predicted only by the detector column of the control table. In other bands the label is null.
3. **Which heads are "C6's late heads"?** Default: every head listed under each task's `c_honest.heads`, not only the heads where C6 held. Each task reads its own list as `late_honest_own`, plus the union of the FAR and SER lists as `late_honest_far_ser`, so FAR against SER compares the same set.
4. **The F-cell warning band is mine.** The plan says "about 0.5". Default: an F control outside 0.4 to 0.6 is listed in `f_controls_off_half` as a broken-probe warning that decides nothing.
5. **What happens on a non-finite residual in a fit or select cell?** Default: `fit` stops and names the cell, so the orchestrator chooses between a bfloat16 recapture and dropping the rows.
6. **The permutation seed is not pre-registered.** Default: 20261102, recorded in the output. The plan fixes only the bootstrap seed.
