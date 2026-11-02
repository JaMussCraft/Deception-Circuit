# Hand-back 25: B2 P1, the margin-check deviation and the falsity-probe run

Agent: analysis worker (Opus), session claude-230e4716, direction instructed-route. Brief: Task A (verify the P1
capture's margin-check deviation) and Task B (run `scripts/falsity_probe.py` fit, score and read on the P1 capture under
plan section 1 and ruling R2). CPU only. No Slurm job, no git, no frozen file edited, no rule changed.

## What changed

No tracked source file was edited. Files written:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_fit.json`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_fit.pt`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_probe.json`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_probe.md`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_tokens.json`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-probe/p1_tokens.md`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_analyses/instructed-route-b2/p1-margin-check/`
  holds the Task A and Task B helper scripts and the Task A result: `taskA_precision.py`, `taskA.json`,
  `taskA_quantiles.py`, `taskA_hfields.py`, `taskA_sanity.py`, `taskB_dump.py` and `taskB_select_hi.py`. They are
  copies of the scratch files in `/u/swong2/.claude/jobs/230e4716/tmp/p1/`, which also holds two exploratory readers,
  `cfgs.py` and `taskA_keys.py`, that are not copied.
- This hand-back: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/25-handback.md`.

## How verified

All commands ran from the worktree with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` and the mgnp
interpreter `/u/swong2/.conda/envs/mgnp/bin/python` (written `PY` below).

Task A:

```
PY /u/swong2/.claude/jobs/230e4716/tmp/p1/taskA_precision.py outputs/_analyses/instructed-route-b2/p1-cap /u/swong2/.claude/jobs/230e4716/tmp/p1/taskA.json
PY /u/swong2/.claude/jobs/230e4716/tmp/p1/taskA_quantiles.py outputs/_analyses/instructed-route-b2/p1-cap
PY /u/swong2/.claude/jobs/230e4716/tmp/p1/taskA_hfields.py outputs/_analyses/instructed-route-b2/p1-cap data/datasets
PY /u/swong2/.claude/jobs/230e4716/tmp/p1/taskA_sanity.py /u/swong2/.claude/jobs/230e4716/tmp/p1/taskA.json outputs/_analyses/instructed-route-b2/p1-cap/run_manifest.json
```

`taskA_precision.py` loads only `lm_head.weight` and `model.norm.weight` (bf16) from the cached snapshot
`0e9e39f249a16976918f6564b8830bc894c89659`, shard 4. It takes each row's captured pre-norm final residual (row 32 of
`resid.<cell>.pt`) and computes three margins:

1. The fp32 path of `hooks.readout_logits`. This is a sanity check against the capture's own `model_margin`.
2. The Hugging Face bf16 path. The RMSNorm statistics are in fp32, the result is cast to bf16 and multiplied by the
   bf16 weight, the unembedding is accumulated in fp32 and rounded to bf16, and the two logits are subtracted in bf16
   and cast to float, as `deception_common.evaluate_behavior` and `score_prompts` do.
3. The capture's fp32 logits rounded to bf16 and subtracted in bf16.

Each is compared with the row's `dataset_margin`.

Task B, the pre-registered defaults (2,000 resamples, 200 permutations), output outside `docs/research`:

```
PY scripts/falsity_probe.py fit   --capture outputs/_analyses/instructed-route-b2/p1-cap --out outputs/_analyses/instructed-route-b2/p1-probe
PY scripts/falsity_probe.py score --capture outputs/_analyses/instructed-route-b2/p1-cap --out outputs/_analyses/instructed-route-b2/p1-probe
PY scripts/falsity_probe.py read  --capture outputs/_analyses/instructed-route-b2/p1-cap --out outputs/_analyses/instructed-route-b2/p1-probe
PY /u/swong2/.claude/jobs/230e4716/tmp/p1/taskB_dump.py outputs/_analyses/instructed-route-b2/p1-probe
PY /u/swong2/.claude/jobs/230e4716/tmp/p1/taskB_select_hi.py outputs/_analyses/instructed-route-b2/p1-cap outputs/_analyses/instructed-route-b2/p1-probe
```

Observed stdout of the three script calls:

```
fit: selected row 18 (layer 17), C 0.001, select AUROC 1.0000; 0 fit(s) not converged
score: FAR gate 1.0000, rule (SER D vs H) 0.9999 [0.999826507148696, 1.0], band misleadingness, R2 instruction-confounded; reading: misleadingness, instruction-confounded: the per-token DLA carries the reading
read: FAR 800 pairs, SER 800 pairs; quartet FAR - SER promotion 0.083 [0.062, 0.104]
```

One stray `score` call named a nonexistent capture directory before the real one. It exited at once with
"capture directory ... does not exist" and wrote nothing. Provenance in `p1_probe.json` is "ok", with the capture
manifest's `git_commit` `27877e512841084b318624c9b8e23c8ed4f00b43` (40 hex). No test suite was run, because no code
changed.

## Execution evidence

**Task A: the margin deviation is precision, not a mismatch.**

**Conclusion.** The deviation comes from the numerical convention, and no row shows a prompt, item or sample mismatch.
It has two parts:

- **Readout precision.** The dataset margins are bf16 arithmetic: 100% are bf16-representable and on the 0.125 grid of
  the logits' binade. The capture reads through an fp32 final norm and unembedding. This alone explains the I cells.
- **Upstream bf16 forward drift.** The D, H, HI and F cells carry an additional difference that is already present in
  the residual stream entering the final norm. It is not readout rounding.

The orchestrator's hypothesis, bf16 rounding of the logits alone, explains only the I cells and is half of the
picture for the others.

Measured, per cell group (full per-cell numbers in `taskA.json`):

| quantity | D, H, HI, F cells (14 cells, 8,983 rows) | I and I-reported cells (3 cells, 989 rows) |
| --- | --- | --- |
| capture minus dataset, mean absolute | 0.076 to 0.104 per cell | 0.041 to 0.043 per cell |
| signed mean, pooled (sd) | -0.0066 (0.110) | -0.0002 (0.052) |
| absolute difference, median / 90% / 99% / max | 0.071 / 0.177 / 0.315 / 0.548 | 0.037 / 0.087 / 0.113 / 0.233 |
| share within one bf16 ulp (0.125) / two ulps | 0.763 / 0.972 | 0.997 / 1.000 |
| rows beyond three ulps (0.375) | 27 | 0 |
| bf16 reconstruction from the captured residual, exact match | 31.5% to 47.6% per cell | 99.4%, 99.0%, 99.7% |
| bf16 reconstruction, mean absolute difference | 0.077 to 0.110 per cell | 0.0004 to 0.0019 |
| sign flips | 0 | 0 |
| Pearson, capture against dataset | 0.9969 to 0.9990 | 0.9993 to 0.9995 |

The I numbers are FAR I, SER I and SDR I-reported in that order where three are given.

- **Sanity checks.** The fp32 recompute from the stored residual matches the capture's `model_margin` within 1.9e-5 on
  every cell, so the reconstruction chain is right. The fp16 residual copy is bf16-exact on every cell.
- **The I-cell match.** Reproducing the I-cell dataset margins exactly from the captured residual means the capture's
  prompt, encoding, item tokens, Readout position and residual stream are bit-identical to the I builder's forward.
  That builder is `dataset/build_inversion_v2.py` through `score_prompts`, built 2026-10-25 with Bridges-2 delivery.
  This is the sharpest available check of the capture pipeline.
- **The other cells.** The D, H and F datasets came from the 2026-10-21 build scripts through `evaluate_behavior`, a
  separate pass. The bf16 reconstruction does not close their gap, so their residual stream differs slightly from the
  capture's.
- **Probable cause, not proven.** The software and GPU of that build are not recorded in the dataset files, and the
  mechanism-datasets compute ledger lists mostly A100 interactive partitions. The likely cause is bf16 kernel or
  library-version drift: shared memory records A100 bf16 drift and one-ulp differences between transformers
  generations. Per the orchestrator's brief, which I did not re-check, the capture gave identical check values on the
  A100 smoke and the H200 run. If so, the drift is between the dataset build and the capture, not inside the capture.
- **Prompt identity.** Each cell's reconstructed honest-minus-deceptive margin matches only its own record field:
  - D matches `clean_margin` and `h_pressure_clean`.
  - H matches `h_neutral_clean`.
  - HI matches `h_honest_instruction_clean`.
  - F matches `h_nopressure_clean`.

  Each match is a mean absolute difference of 0.078 to 0.104 with 37% to 48% exact. Every other field is 0.62 to 4.7
  logits away on average. A wrong prompt would match some other field or none.
- **A test that did not discriminate.** Whether the absolute difference scales with logit magnitude could not be
  tested. The larger logit of every one of the 9,972 rows lies in one binade (ulp 0.125), so there was no spread in
  magnitude.
- **No effect on the probe.** Every probe input was captured in one job (H200, 23412454) with one convention, so the
  drift against the dataset files does not enter any AUROC.

**Proposed restatement of the section 7 bar.** This is a proposal for the orchestrator, not enacted. A capture margin
check passes when, per cell:

- the signed mean of model minus dataset margin is within 0.05;
- the Pearson correlation is at least 0.99;
- there is no sign flip.

All 18 cells pass this. The frozen bar of section 7 names the D cells only, and every D cell fails it, at 0.078 to
0.092. The I cells would pass it, and the text of the bar does not cover the H, HI and F cells. The largest signed
mean is -0.021 (SER D) and the lowest Pearson is 0.9969 (FAR fit D and FAR select D). A stricter
alternative fits only the I builder: the bf16 reconstruction reproduces at least 99% of rows exactly.

**Task B: the probe.**

**Selection.** The FAR fit split had 200 D and 200 H rows; the select split had 200 D, 200 H and 200 HI. All 132 fits
converged.

- **The select score was saturated.** The AUROC of D against pooled H and HI is 1.0000 at every C on every eligible
  layer 4 to 31. Layer 3 reaches 0.9999 to 1.0, and layers 0 to 2 range from 0.65 to 0.98.
- **The tie rule picked the layer.** All 28 eligible layers fall inside the 0.005 tie, so the rule picked layer 17 (row
  18), and the exact tie in C went to the smallest value, 0.001.
- **The HI penalty never engaged.** At the selected layer on the select split, HI scores above H with AUROC 0.961. D
  against HI is 1.000. Mean decision values are D 4.79, HI -3.65 and H -4.56, so HI sits mostly above H and entirely
  below D, and the pooled score cannot see it (`taskB_select_hi.py`).

**Rule number.** SER D against SER H at layer 17:

| quantity | value |
| --- | --- |
| AUROC | 0.99993 |
| 95% CI, 17 `pressure_id` clusters, 2,000 resamples, seed 20261101 | 0.99983 to 1.0 |
| pairs | 800, 0 unjoined |
| frozen band | misleadingness (at least 0.75) |
| CI crosses a band edge | no |
| anti-aligned | no |
| FAR gate, FAR D against H, 800 pairs, 12 clusters | 1.000 (CI 1.000 to 1.000); fallback off |

Mean SER decision values are D -0.42 (sd 0.62) and H -3.50 (sd 0.47). The AUROC is a ranking. Most SER D rows sit
below the probe's own zero.

**Control table** (each cell against its own H twin at layer 17, C 0.001):

| cell | AUROC | 95% CI | pairs | literal-falsity prediction | misleadingness prediction | detector prediction |
| --- | --- | --- | --- | --- | --- | --- |
| SER D (rule) | 1.000 | 1.000 to 1.000 | 800 | under 0.6 | 0.75 or more | high |
| FAR I | 1.000 | 1.000 to 1.000 | 177 | high | low | high |
| FAR HI | 0.963 | 0.945 to 0.976 | 800 | low | low | high |
| SER HI | 0.747 | 0.726 to 0.777 | 783 | low | low | high |
| SER I | 1.000 | 0.999 to 1.000 | 194 | low | low | high |
| FAR F | 0.681 | 0.650 to 0.712 | 800 | about 0.5 | about 0.5 | about 0.5 |
| SER F | 0.624 | 0.608 to 0.644 | 800 | about 0.5 | about 0.5 | about 0.5 |
| SDR D (descriptive) | 1.000 | 1.000 to 1.000 | 800 | | | |
| SDR I-reported (descriptive) | 1.000 | 1.000 to 1.000 | 502 | | | |

- **HI rows kept.** FAR gate HI kept 1.0 of its rows and SER HI kept 0.979. No row below the 0.3 bar reached the
  capture.
- **SDR I-reported.** 116 sample-flagged rows were dropped, leaving 502 pairs.
- **No non-finite residual** appeared in any cell.

**R2 label: "instruction-confounded".** R2's clean condition fails on all three named cells, each at or above 0.6: FAR
I 1.000, FAR HI 0.963, SER HI 0.747. The pattern is the detector column. Every clause or instruction cell is high,
including SER I, which both other columns predict low. Both F controls are outside 0.4 to 0.6, which is
`f_controls_off_half`, the broken-probe warning that decides nothing. So under R2 the per-token direct attribution
carries the reading.

**SER curve across layers.** Measured at each layer's best select C, which is 0.001 on every eligible layer. It
decides nothing.

| layer | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 to 16 | 17 to 20 | 21 to 25 | 26 to 28 | 29 | 30 | 31 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SER AUROC | 0.890 | 0.966 | 0.943 | 0.971 | 0.971 | 0.994 | 0.995 | 0.9997 | 0.9999 | 1.000 | 0.9998 to 0.9999 | 0.9977 to 0.9995 | 0.9965 to 0.9970 | 0.992 | 0.993 | 0.999 |

- **Every eligible layer is in the misleadingness band.** The minimum is 0.890 at layer 4, so the verdict does not
  depend on the layer.
- **Before the eligible range,** layer 0 already gives SER 0.993 to 0.997 and a FAR gate of 1.000. The mass-mean
  direction gives SER 0.85 to 1.00 on eligible layers.

**Further checks.**

- **Permutation null.** 200 refits with D and H swapped in random pairs, scored on SER at layer 17. Mean 0.525, sd
  0.235, 5% quantile 0.126, 95% quantile 0.877, maximum 0.976. Observed 0.99993, one-sided p 0.005, the smallest
  value possible with 200 refits.
- **Leave-one-clause-out.** Over 13 FAR clauses of train and validation: pooled AUROC 1.000, minimum 1.000.

**Per-token direct attribution** (D minus H, centred logits). Suppression is the change on the honest item, where
negative means D lowers it. Promotion is the change on the deceptive item. 95% CIs resample `pressure_id` clusters.
FAR has 800 pairs and 12 clusters; SER has 800 pairs and 17 clusters. The largest DLA-sum error is 0.034.

| group | FAR suppression | FAR promotion | SER suppression | SER promotion | FAR - SER suppression | FAR - SER promotion |
| --- | --- | --- | --- | --- | --- | --- |
| whole model, centred | -4.73 (-4.98, -4.44) | 5.05 (4.85, 5.27) | -3.09 (-3.38, -2.70) | 3.09 (2.64, 3.44) | -1.63 (-2.11, -1.24) | 1.97 (1.56, 2.46) |
| whole model, raw | -4.37 (-4.62, -4.11) | 5.41 (5.20, 5.64) | -3.07 (-3.39, -2.63) | 3.11 (2.72, 3.43) | -1.30 (-1.82, -0.89) | 2.30 (1.93, 2.74) |
| whole model, log-softmax | -2.68 (-2.90, -2.45) | 7.10 (6.79, 7.43) | -2.72 (-3.20, -2.06) | 3.46 (3.24, 3.62) | 0.04 (-0.67, 0.57) | 3.64 (3.28, 4.01) |
| quartet L17H24 to H27 | -0.143 (-0.155, -0.132) | 0.202 (0.182, 0.219) | -0.120 (-0.135, -0.102) | 0.119 (0.107, 0.127) | -0.023 (-0.045, -0.006) | 0.083 (0.062, 0.104) |
| late honest heads, own task | -0.53 (-0.58, -0.47) | 0.92 (0.87, 0.98) | -0.28 (-0.31, -0.24) | 0.41 (0.38, 0.45) | -0.25 (-0.32, -0.17) | 0.51 (0.45, 0.58) |
| late honest heads, FAR and SER union | -0.59 (-0.64, -0.53) | 1.03 (0.98, 1.09) | -0.61 (-0.65, -0.54) | 0.75 (0.68, 0.81) | 0.02 (-0.06, 0.10) | 0.29 (0.21, 0.37) |
| mlp.30 | 0.14 (0.07, 0.21) | -0.49 (-0.63, -0.37) | 0.23 (0.15, 0.30) | -0.36 (-0.42, -0.31) | -0.09 (-0.19, 0.02) | -0.13 (-0.28, 0.01) |
| mlp.31 | -0.60 (-0.77, -0.46) | 1.39 (1.24, 1.49) | -0.25 (-0.39, -0.06) | 0.48 (0.31, 0.60) | -0.36 (-0.61, -0.16) | 0.91 (0.72, 1.13) |

**SDR, descriptive.** In the whole-model centred readout, SDR D against H shows suppression -2.45 (-2.77, -2.11) and
promotion 4.30 (3.91, 4.63). The 502 I-reported pairs against SDR H show suppression -2.31 (-2.47, -2.15) and promotion
3.81 (3.66, 3.94).

**What the attribution shows, measured.** On SER the whole model lowers the honest item's centred logit by 3.09 and
raises the deceptive one by 3.09 relative to H. Both CIs exclude zero, so SER D is suppression plus promotion, not pure
promotion. FAR shows larger centred changes on both items than SER. On log-softmax the suppression is equal (FAR minus
SER 0.04, CI -0.67 to 0.57) and only the promotion is larger on FAR (3.64). The quartet and the late honest heads
promote the deceptive item and lower the honest one on both tasks; FAR has more quartet promotion than SER by 0.083.
mlp.30 opposes the deception on both tasks, raising the honest item and lowering the deceptive one. mlp.31 promotes
the deceptive item on both, by more on FAR.

**My reading, extrapolation.** These points are mine, not measured:

- The probe is a clause or instruction detector. It separates any operator clause from the neutral twin, whether the
  clause is false-and-transparent (FAR I), true-and-transparent (SER I) or honest (HI). That is why FAR I, SER I and
  the HI cells are all high.
- The P1 number therefore says nothing about misleadingness against literal falsity, which matches risk 1 of plan
  section 8.
- The wide permutation null points the same way. It reaches 0.98 with partly scrambled labels, so the D-against-H
  difference on SER is reachable by many directions in the clause-difference subspace.
- The per-token result fits plan section 8's row "SER D suppresses the honest item against H". By that row's reading,
  the honest answer is computed and overridden on SER as well. The two whole-model normalisations disagree on whether
  FAR suppresses more than SER, so I would not rest a FAR-against-SER knows-versus-says contrast on suppression alone.

## What is NOT done

- **No FINDINGS row was written.** The orchestrator decides how "misleadingness, instruction-confounded" enters
  `FINDINGS.md`.
- **The section 7 bar was not restated.** The proposal above needs a ruling, and nothing was changed.
- **The D, H and F builds' precision cause is not proven.** It is inferred from the I-cell exact match and the build
  provenance. Proving it would need a GPU rerun of `evaluate_behavior` on a few rows in the capture environment,
  which this brief excluded.
- **Some outputs rest on hand-back 20's open-question defaults, not on pre-registration:**
  - "layers 4 to 31" means decoder layers, rows 5 to 32;
  - the F warning band is 0.4 to 0.6;
  - a misleadingness verdict that is not clean is labelled "instruction-confounded";
  - "C6's late heads" means every `c_honest.heads` entry;
  - the permutation seed is 20261102;
  - the 116 sample-flagged SDR I-reported rows are dropped.

  With these controls the detector pattern holds under any of these readings.
- **Run times were not recorded.** Each call finished within a few minutes on the login node.

## Open questions

1. **Does the saturated selection need a ruling?** The pre-registered selection score was 1.0 on all 28 eligible layers,
   and its HI penalty could not see HI scoring above H (0.961 on the select split). Default: the result stands as run,
   because R2's control table already catches the confound. A future probe would need a selection score that compares
   HI with H directly, which would be a new ruling.
2. **Should the section 7 margin bar be restated?** The proposal is |signed mean| at most 0.05, Pearson at least 0.99
   and no sign flip, which passes on all 18 cells. Default: record the deviation as explained by precision and leave
   the frozen text unchanged until the orchestrator rules.
3. **Does B2's write-up read P1 off the per-token attribution, as R2 directs?** Default: yes. The measured FAR-against-SER
   numbers are the table above. The disagreement between the centred and log-softmax readings on suppression should be
   reported, not resolved by choosing one.
