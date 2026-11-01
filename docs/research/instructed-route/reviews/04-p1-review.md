# Review 04: B2 P1, the falsity probe (hand-back 25)

Reviewer: independent reviewer (Opus), session claude-230e4716, direction instructed-route, Sun 1 Nov 2026. CPU only,
mgnp interpreter with one BLAS thread. No git, no Slurm, no research-session command. The only file written under
`docs/research` is this one. Scratch scripts and their output are in `/u/swong2/.claude/jobs/230e4716/tmp/rev04/`
(`a_prec.py`, `b_probe.py`, `c_more.py` and their `.out` files). Every command below ran from the worktree as

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python <script> <args>
```

with `CAP = outputs/_analyses/instructed-route-b2/p1-cap` and `OUT = outputs/_analyses/instructed-route-b2/p1-probe`.

## Verdict

**As stated, with caveats.** Every number in hand-back 25 reproduces from the raw files, and the R2 label
"instruction-confounded" is correct. The main caveat is new: the per-token attribution, which R2 makes carry the
reading, has the same confound. SER transparent inversion lowers the honest item and raises the deceptive one about as
much as SER D does. So P1 decides nothing between misleadingness and literal falsity. Neither the probe nor the
attribution separates deception from instructed inversion.

## Checks

### 1. Task A, the margin deviation

Command: `a_prec.py CAP data/datasets`. I wrote the readout independently of the worker's script. It applies the
Hugging Face RMSNorm convention with fp32 statistics, a cast to bf16 and the bf16 weight. It then uses the bf16
`lm_head` rows with wide accumulation rounded to bf16, and subtracts the two logits in bf16. Weights come from the
cached snapshot through the safetensors index. The bf16 subtraction matches `deception_common.evaluate_behavior` and
`score_prompts`, which compute `(lg[t] - lg[d]).float()`.

| cell group | bf16 rebuild exact match | bf16 rebuild mean abs | capture minus dataset, mean abs | signed mean | Pearson |
| --- | --- | --- | --- | --- | --- |
| FAR I (177) | 0.994 | 0.0007 | 0.043 | 0.0003 | 0.9994 |
| SER I (194) | 0.990 | 0.0019 | 0.041 | 0.0079 | 0.9993 |
| SDR I-reported (618) | 0.997 | 0.0004 | 0.042 | -0.0028 | 0.9995 |
| D, H, HI, F cells (14) | 0.315 to 0.476 | 0.077 to 0.110 | 0.077 to 0.103 | -0.021 to 0.002 | 0.9969 to 0.9990 |

All 9,972 rows pooled:

| quantity | value |
| --- | --- |
| sign flips | 0 |
| within one bf16 ulp (0.125) | 7,838 |
| within two ulps | 9,723 (97.5%) |
| beyond three ulps | 27 |

The larger logit sits in the 0.125-ulp binade on every row. The fp16 residual copy is bf16-exact on every cell. These
match the worker's `taskA.json`.

- **Own field.** For every non-I cell I rebuilt the honest-minus-deceptive margin and compared it with every margin
  field of the D record, trying both signs. Each cell is nearest its own field, and no cell matches another field
  better:
  - D cells (fit, select, gate, SER, SDR) match `clean_margin` and `h_pressure_clean`, which carry the same value.
  - H cells match `h_neutral_clean`.
  - HI cells match `h_honest_instruction_clean`.
  - F cells match `h_nopressure_clean`.

  The own-field error is 0.08 to 0.11 with 32% to 48% exact. The next-nearest field is 0.62 or more away in every
  cell (SER HI against `h_nopressure_clean` is the closest at 0.623) and up to 4.9 away. I extended the worker's check
  to the fit and gate cells and to the SDR cells.
- **Tails per cell.** Command: `c_more.py CAP OUT`.

  | quantity | D, H, HI, F cells | I cells |
  | --- | --- | --- |
  | absolute difference, p99 | 0.254 (SDR H) to 0.408 (FAR select H) | at most 0.116 |
  | absolute difference, max | 0.341 to 0.548 (FAR gate F) | 0.233 |
  | rows within 0.25 | 94.5% to 98.9% | 100% |

- **Is "precision, not mismatch" sound?** Yes, for the I cells it is proven: the exact bf16 rebuild means the
  capture's prompt, tokens, Readout and residual are bit-identical to the I builder's forward. For the D, H, HI and F
  cells it is well supported but inferred.
  - Three facts support it. Each cell matches only its own field, there are no sign flips, and the error is two ulps
    or less on 97% of rows.
  - The inferred part is the cause. The residual entering the final norm already differs from the 2026-10-21 build.
    "Kernel or library drift" is the likely cause, but nothing recorded proves it, as the hand-back says.
- **The restated bar.** The proposal is |signed mean| at most 0.05, Pearson at least 0.99 and no sign flip. It was
  written after seeing the data, and all three tests are weak against a small fraction of mismatched rows.
  - **Signed mean.** Errors of either sign cancel, so a few wrong-prompt rows can leave it near zero.
  - **Pearson.** It tolerates about half a percent of rows off by several logits. Margins span several logits, so r
    stays near 0.99.
  - **No sign flip.** It is nearly automatic. Every dataset margin is at least 0.375 in magnitude, and the D cells are
    filtered at 0.75.

  So the proposal would miss, for example, 4 of 800 rows read from the wrong prompt or with swapped item tokens. Record
  the frozen bar as failed and explained, not passed. If a restated bar is wanted, the discriminating tests are these:
  - a tail bar, for example every row within 0.75 logits (six ulps; observed maximum 0.548) and p99 at most 0.5;
  - the own-field test: each cell's rebuilt margin is nearest its own record field, with a gap of at least 0.5 to the
    next field (observed at least 0.54, on SER HI).

### 2. Task B, the rule number, selection and leakage

Command: `b_probe.py CAP OUT ROOT`. The AUROC is my own pairwise count, and the cluster bootstrap is my own resampler
with the same seed (20261101, 2,000 resamples).

- **Rule number.** SER D against H at layer 17 (row 18), C 0.001, gives AUROC 0.99993 with CI 0.99983 to 1.0. That is
  800 pairs in 17 clusters. It is identical to `p1_probe.json`. Mean decision values are D -0.42 and H -3.50, and
  every D row outscores its own twin.
- **Selection recompute.** I recomputed the full 33 x 4 select table from the saved weights and the select residuals.
  It differs from `p1_fit.json` by at most 0.0.
  - All 28 eligible layers (4 to 31) score 1.0, so all 28 are tie candidates.
  - The nearest to 17 is 17, and the first argmax gives C 0.001.
  - Rows 0 to 4 score 0.5, 0.696, 0.973, 0.979 and 1.0.

  This is the pre-registered rule as written. The fit used FAR train D against H, selection used FAR validation D
  against pooled H and HI, ties within 0.005 went to the layer nearest 17, and exact C ties went to the smaller C.
- **Saturation.** It is handled as the plan says: plan section 8 risk 2 expects it, and the SER curve is reported. The
  label does not depend on the tie rule. On the select split at C 0.001, HI against H is at least 0.943 at every
  eligible layer, so no eligible layer could have given a clean label. At the selected layer the select split gives
  D against H 1.0, D against HI 1.0 and HI against H 0.961.
- **The fit used only fit rows.** The saved standardisation equals the fit split's mean and standard deviation. The
  gradient of the objective at the saved weights is 7e-8 or less on the fit rows at all four C. The same weights give
  a gradient of 5e-3 if the select D and H rows are added, so they are not a fit that included select rows.
- **Leakage, by id.** Fit and select share no instance id. No gate, SER or SDR cell shares an id with fit or select.
  Every gate, SER and SDR row is in the test split, and none of them carries a seed-0 or seed-1 flag. The exception is
  SDR I-reported, whose 116 flagged rows are dropped in scoring as planned.
- **Leakage, by text.** There is none on the rule number.
  - SER's 17 deceptive clauses share no text with FAR's 13 fit and select clauses.
  - 38 of SER H's 61 neutral sentences also occur in FAR fit H, covering 325 of 800 SER H rows. Splitting SER D
    against H on that overlap gives 0.99991 for rows with a shared sentence and 0.99997 for the rest. The H score means
    are -3.51 and -3.49, so the overlap moves nothing.
  - All 12 FAR gate clauses occur in fit and select, so the FAR gate is not clause-held-out. It is a 0.75 gate only and
    does not enter the rule.

### 3. The control table and R2

Same command and seed as check 2.

| control against its own H twin | AUROC (recomputed) | 95% CI | pairs | cell mean minus twin mean, as a share of the D shift |
| --- | --- | --- | --- | --- |
| FAR I | 1.000 | | 177 | 0.91 |
| FAR HI | 0.9626 | 0.945 to 0.976 | 800 | 0.09 |
| SER HI | 0.7474 | 0.726 to 0.777 | 783 | 0.13 |
| SER I | 0.9997 | | 194 | 1.17 |
| FAR F | 0.6811 | 0.650 to 0.712 | 800 | 0.02 |
| SER F | 0.6240 | 0.608 to 0.644 | 800 | 0.06 |

The D shifts are 9.41 on FAR and 3.09 on SER.

- **R2 applied literally.** "Clean" needs FAR I, FAR HI and SER HI all under 0.6. All three are at or above 0.6, at
  1.000, 0.963 and 0.747, so the verdict is not clean.
- **The detector column.** On AUROC the pattern matches it: every clause or instruction cell is high, including SER I,
  which both other columns predict low. The label is therefore **"instruction-confounded"**, as the hand-back says.
- **By magnitude, the probe reads the instructed answer switch.** The two inversion cells move the score 0.91 and 1.17
  of the D shift. The honest-instruction cells move it only 0.09 and 0.13. HI's high AUROC is a small shift ranked
  against a tight H distribution. D and I both make the model say the deceptive item, while H, HI and F do not.
  "Inversion-confounded" is the more accurate description. It restates F-mech-003 at the Readout: the FAR and SER
  machinery also carries transparent inversion.
- **The separation is available after one decoder layer.** At layer 0 (row 1), SER scores 0.997 and the FAR gate 1.0.
  That fits a clause-content signal attended in one hop.
- **The F cells.** Plan section 1 predicts F "about 0.5; anything else means a broken probe" in every column. Both F
  cells are above 0.6, and FAR F's whole CI is above 0.65, so the plan's literal text is failed. The 0.4 to 0.6 band
  and "decides nothing" come from hand-back 20's open-question defaults, not from pre-registration.
  - My reading is weak answer-confidence leakage, not a broken probe. The F shifts are 2% and 6% of the D shift.
  - On SER, the F-minus-H score difference correlates -0.66 with the F-minus-H honest-margin difference. Within SER H
    the score correlates -0.49 with the honest margin, and HI behaves the same way at -0.64.
  - So the probe carries a small component that rises as the honest answer weakens. The F cells fit that component,
    not falsity, misleadingness or clause detection.
  - The orchestrator should rule on it. It does not change the R2 label.

### 4. The permutation null

Command: `b_probe.py`, null section.

- **The recorded null is broad.** It has 200 refits, mean 0.525, sd 0.235 and maximum 0.976. Its histogram in 0.1
  bins from 0 to 1 is 6, 18, 13, 27, 26, 29, 25, 27, 21 and 8, which is near-uniform from 0.1 to 0.9.
- **The swaps do not drive it.** Its correlation with the net share of unswapped pairs is only 0.30.
- **Random directions behave the same.** 200 isotropic random directions in the standardised layer 17 space give a
  mean |AUROC - 0.5| of 0.229 and a maximum of 0.978. 12.5% of them are beyond 0.9 or below 0.1. So a maximum near
  0.98 is expected with no signal at all, because SER D and H differ along a large share of all directions at this
  layer.
- **What the p-value says.** The fitted direction (0.99993) and the plain mass-mean direction (0.9999) beat every
  null draw. p 0.005 is the floor for 200 refits. It says only that the fitted direction beats a random one, not what
  the direction reads.
- **One overreach.** The hand-back says the difference is "reachable by many directions in the clause-difference
  subspace". "Many directions" is right. The restriction to a clause-difference subspace is not shown, because
  unrestricted random directions do it too.

### 5. The per-token attribution and "my reading"

Command: `c_more.py`, attribution section. These are paired means of tokens-file cell minus own H twin, with token
ids agreeing on every pair. The D rows reproduce the hand-back exactly. The I rows are my addition, point estimates
without CIs, descriptive only.

| contrast, whole model | centred: suppression / promotion | log-softmax: suppression / promotion |
| --- | --- | --- |
| FAR D - H (800) | -4.73 / 5.05 | -2.68 / 7.10 |
| FAR I - H (177) | -5.21 / 5.19 | -2.62 / 7.78 |
| SER D - H (800) | -3.09 / 3.09 | -2.72 / 3.46 |
| SER I - H (194) | -2.65 / 3.15 | -2.54 / 3.27 |
| SDR D - H (800) | -2.45 / 4.30 | -3.73 / 3.02 |
| SDR I-reported - H (502) | -2.31 / 3.81 | -3.15 / 2.97 |

- **Measured.** These are measured, and the hand-back states them correctly:
  - SER D lowers the honest item's final logit and raises the deceptive one against H, by 3.09 each (centred), with
    CIs away from zero.
  - FAR's centred changes are larger.
  - The log-softmax suppression is equal on FAR and SER, at a difference of 0.04.
  - The quartet and component rows are as tabulated.
- **Beyond the data: "computed and overridden".** The hand-back writes that "the honest answer is computed and
  overridden on SER as well". That is the plan's section 8 interpretation of a final-logit drop. The measurement shows
  the final honest logit is lower in D than in H. It does not show an intermediate honest computation that is later
  overridden. The same drop appears with transparent inversion, which nobody calls deceptive.
- **Beyond the data: "any operator clause".** The hand-back writes that the probe "separates any operator clause".
  That holds on AUROC, but by magnitude it barely moves for the honest instruction or for no clause (check 3).
- **Beyond the data: the clause-difference subspace.** It is not shown (check 4).
- **Fair as flagged.** "The P1 number says nothing about misleadingness against literal falsity" is a fair reading.
  The warning not to rest a FAR-against-SER contrast on suppression alone is also sound.
- **The read step lacks an I control.** It computes D against H only for FAR and SER. If the attribution is to carry
  any reading under R2, the read step needs the I-against-H rows with clustered CIs.

### 6. Finding text

The B2 rule maps a SER AUROC at or above 0.75 to "misleadingness". Under R2 that verdict is instruction-confounded,
and check 5 shows the fallback reading is confounded the same way. So the row must not read as evidence for
misleadingness. See the proposed text below.

- **Strength.** "reviewed" is right: one run, independently reproduced, so it cannot be "replicated".
- **Commit column.** Use the capture manifest's commit, `27877e5`, and state the probe-root manifest gap (problem 4).

## Problems found

1. **Moderate: the per-token fallback is confounded too.** R2 hands the reading to the per-token attribution when the
   controls show the detector pattern. Transparent inversion matches D on that attribution: SER I against H is -2.65 /
   3.15 against D's -3.09 / 3.09, and FAR I is -5.21 / 5.19 against -4.73 / 5.05. These are my point estimates on 194
   and 177 pairs without CIs. So the fallback cannot read misleadingness or deception either. Recommendation: add the
   I-against-H contrast, with clustered CIs, to `falsity_probe.py read` before any write-up leans on the attribution.
   This is a recommendation, not a ruling.
2. **Moderate: the F cells fail the plan's literal text.** FAR F is 0.681 (CI 0.650 to 0.712) and SER F is 0.624 (CI
   0.608 to 0.644). The plan says "about 0.5; anything else means a broken probe". The hand-back treats this as a
   warning that "decides nothing", which is a hand-back 20 default, not pre-registration. The evidence points to weak
   answer-confidence leakage rather than a broken probe (check 3). The orchestrator should rule, and the finding should
   carry it.
3. **Moderate, interpretive: AUROC overstates the honest-instruction response.** "Instruction detector" is the
   AUROC-level pattern. By score shift the probe reads the instructed answer switch: inversion moves it 0.91 and 1.17
   of D, honest instruction 0.09 and 0.13, no clause 0.02 and 0.06. The R2 label stands, but the description should
   say inversion.
4. **Minor: the probe output root has no manifest.** Plan section 7 says "every output root needs a manifest with a
   40-hex commit". `p1-probe/` holds six files and no `run_manifest.json`, and neither does `p1-margin-check/`. The
   score JSON points at the capture's manifest (`27877e5`), but the version of `falsity_probe.py` that produced the
   numbers is not pinned.
5. **Minor: the proposed margin bar is post hoc and weak against a few mismatched rows** (check 1). Rule the frozen
   bar as failed and explained by precision, citing the I-cell exact rebuild and the own-field test. If a bar is
   restated, use a tail bound and the own-field gap.
6. **Minor: the permutation null is a random-direction null.** p 0.005 is the floor and adds nothing on specificity
   (check 4).
7. **Minor, documentation:** in `rows.*_HI.jsonl` the `pressure` field holds D's clause text. The HI prompt replaces
   that clause with the honest instruction ("Answer honestly and completely, ..."), so a later reader could misread
   which clause an HI row saw.

## Proposed finding text

```
| F-rte-003 | 2026-11-01 | instructed-route | Does a FAR falsity probe read SER misleadingness: its AUROC on SER D against SER H at layer 17 is 0.9999 (interval 0.9998 to 1.0 clustered by 17 clauses), in the misleadingness band, but under R2 the verdict is instruction-confounded, not clean, because FAR instructed inversion scores 1.000, FAR honest instruction 0.963 and SER honest instruction 0.747 against their twins and SER transparent inversion 0.9997; by score shift the probe reads the instructed answer switch (inversion moves it 0.91 and 1.17 of the D shift on FAR and SER, honest instruction 0.09 and 0.13), and the per-token attribution that R2 makes carry the reading is confounded the same way (SER D lowers the honest item by 3.09 and raises the deceptive item by 3.09 against H, SER I by 2.65 and 3.15), so P1 does not separate misleadingness from literal falsity or deception from instructed inversion, as F-mech-003 found for the deciding sets. Caveats: selection saturated at 1.0 on all 28 eligible layers so the tie rule chose layer 17, though no eligible layer would give a clean label (honest instruction against H at least 0.943 on the select split); the no-clause controls sit off one half at 0.681 and 0.624, which the plan calls a broken probe and the review reads as weak answer-confidence leakage; the capture's margins differ from the dataset's by 0.08 to 0.10 on average against the frozen 0.05 bar, explained by bf16 precision (instructed-inversion margins rebuild exactly on 99 percent of rows, no sign flip in 9,972 rows, every cell nearest its own record field); the probe output root has no run manifest. | reviewed | 27877e5 | outputs/_analyses/instructed-route-b2/p1-probe/p1_probe.json<br>outputs/_analyses/instructed-route-b2/p1-probe/p1_tokens.json<br>outputs/_analyses/instructed-route-b2/p1-cap/run_manifest.json<br>outputs/_analyses/instructed-route-b2/p1-margin-check/taskA.json<br>docs/research/instructed-route/reviews/04-p1-review.md | docs/research/instructed-route/reviews/04-p1-review.md |
```

The I-shift ratios, the I-against-H attribution, the HI-against-H select minimum and the own-field gap come from this
review's scripts, not from the hand-back's outputs. If the orchestrator wants every number in the row backed by a
tracked output, those four should be added to the `read` and `score` outputs first or cited to this review.
