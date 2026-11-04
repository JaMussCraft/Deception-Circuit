# Review 08: independent recomputation of the one-neuron interchange check (FAR, R15 c, R21)

**Verdict: CONFIRMED WITH CORRECTIONS.** Every number that ruling R21 and `one_neuron_report.md` state for the cell
`one_neuron-92fc6fb` was recomputed from `rows.jsonl` and the attribution tensors without W9's report script. All 400
per-group quantities match `one_neuron_report.json` with a difference of exactly 0.0, and the summary statistics
match to within 4.4e-16. The 40 neurons are exactly the top 20 by s_D and the top 20 by s_H of the all-position
ranking. The correction is to R21's layer sentence. The top 20 by s_D span layers 0 to 19, not 8 to 19. The three
largest measured single-neuron effects sit in layers 8, 0 and 9, and all three are members of the size-500 D-only
class. A qualification also applies to "faithful predictor": the signs are faithful, but within the s_D list alone
the rank correlation is 0.65, not 0.93.

Reviewer: R8 (Claude Opus, independent). Written Wed 4 Nov 2026, 12:50 pm EST. `WT` below means
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition`, and `NP` means
`WT/outputs/_analyses/neuron-partition`.

- **Read before my numbers were saved.** Spec item 10 and rulings R2, R6, R11, R15 and R21; hand-back 10 (W9's set
  construction and report definitions); hand-back 09's one-neuron addendum; review 01 major 2; review 06 as the
  model; and `one_neuron_report.md`, which the brief names as the claim. The R21 numbers and the claimed per-group
  table were therefore known to me before I computed mine.
- **Not read.** `NP/w9_tmp/one_neuron_report.py` was never opened, imported or run. Its definitions came from
  hand-back 10's prose. The row schema came from the rows themselves and the `definitions` block of `summary.json`.
  `one_neuron_report.json` was opened only after `NP/r8_tmp/recompute.json` was saved.
- **Read to confirm the aggregation.** `WT/component_analysis/neuron_attribution.py` lines 464 and 537 only.
- **Not used.** No GPU, Slurm or version control. Everything ran on the Delta login node with the mgnp interpreter.
  Spearman uses my own average-rank implementation, because scipy is not installed in mgnp.

## Definitions used

- **Scores.** s_D is `atp_all_mean` and s_H is minus `rev_atp_all_mean`, both from
  `NP/attribution/far_v2_dh_train+validation_c3d7763_rev/scores.pt`. s_I is `atp_all_mean` from
  `NP/attribution/far_v2_in_train+validation_c3d7763/scores.pt`. The plain dh directory
  `far_v2_dh_train+validation_c3d7763` gives the same `atp_all_mean`, with a maximum difference of 0.0.
- **Aggregation.** Per ranking row, the attribution (a_clean minus a_twin) times the gradient is summed over every
  valid position of the prompt. That sum is then averaged over the 400 train and validation rows of the run
  (`rows.json`, `n_rows` 400). This is R11's all-position key.
- **Selection.** Top 20 by each signed score, positive scores only, ties to the lower flat index. There are no ties
  at either cut. The 20th and 21st s_D are 0.18207 and 0.18195. The 20th and 21st s_H are 0.15584 and 0.15292.
- **Margins.** m is the row's `m_intact` or `m_ablated` per stream, in D's orientation. For "both streams", the
  clean and corrupt values are averaged within an id, then ids are averaged. The clean-stream variant uses the clean
  stream only.
- **Shifts.** dD is the mean of m_ablated minus m_intact on the 300 D rows (D patched with H's value at the one
  neuron, every position). dH is the same on the 300 H rows (the reverse patch, H given D's value). First-order
  attribution predicts dD = minus s_D and dH = plus s_H.
- **D removed (R2).** G is the mean over ids of the intact D margin minus the intact H margin of the same id. D
  removed is minus dD divided by G. G is 9.836 for every group, from the H rows and from the D rows'
  `twin_m_intact` alike.
- **Sign agreement.** sign(dD) equals sign(minus s_D), and sign(dH) equals sign(s_H).
- **Distinct neurons.** For the 4 neurons in both lists the s_D group is kept, giving 36.

## Recomputed numbers beside the claims

| quantity | R21 / report claim | mine | match |
|---|---|---|---|
| rows in `rows.jsonl` | 24,000 | 24,000 (twin D 12,000, twin H 12,000, no other rows) | yes |
| rows per group | 300 D and 300 H | 300 and 300 for all 40, ids equal to the seed-2 sample's D and H lists | yes |
| sign agreement on D, 40 groups | 40/40 | 40/40 | yes |
| sign agreement on H, 40 groups | 39/40 | 39/40, the miss is sD_17 L1 n3349 | yes |
| sign agreement, 36 distinct | 36/36 and 35/36 | 36/36 and 35/36 | yes |
| Spearman ρ(s_D, minus dD), 40 groups | 0.93 (report 0.929) | 0.92943 | yes |
| Spearman ρ(s_H, dH), 40 groups | 0.998 | 0.99756 | yes |
| Spearman, 36 distinct, D and H | 0.938 and 0.997 | 0.93848 and 0.99665 | yes |
| clean stream, 40 groups, D and H | 0.931 and 0.997, signs 40/40 and 39/40 | 0.93149 and 0.99662, signs 40/40 and 39/40 | yes |
| clean stream, 36 distinct, D and H | 0.940 and 0.995 | 0.94003 and 0.99537 | yes |
| Pearson, 40 groups, D and H (report only) | 0.950 and 0.998 | 0.94970 and 0.99849 | yes |
| duplicate groups give identical measurements | 4 pairs, max difference 0 | 4 pairs, every ablated margin and argmax identical row by row | yes |
| maximum single-neuron D removed | at most 0.05 | 0.0524, sD_01 L8 n11594 | yes, to rounding |
| minimum single-neuron D removed | not stated | minus 0.0196, sH_05 L16 n9215 | not applicable |
| 36 distinct, 4 in both lists | L13 n4212, L13 n10624, L14 n7120, L19 n11138 | the same four | yes |
| neurons are the top 20 by s_D and by s_H, all positions | yes | yes, both lists in rank order | yes |
| top single neurons in layers 8 to 19 | stated | s_D list layers 0, 1, 5, 8, 9, 12 to 16, 18, 19; s_H list layers 12 to 19 and 21 | **no, see correction 1** |

Per group, all ten columns (s_D, s_H, s_I, dD, dH, D removed, G, and the three clean-stream columns) match
`one_neuron_report.json` with a worst absolute difference of 0.0. The four summary blocks agree on every sign count,
and every correlation agrees to within 4.4e-16.

## Corrections

1. **The layer sentence of R21 is wrong.** R21 says the top single neurons "sit in layers 8 to 19, not in the layers
   0 to 9 where the size-500 class is dense". The top 20 by s_D include L0 n2935, L1 n3349, L5 n171, L8 n11594 and
   L9 n520. Ranked by measured D removed, the three largest single neurons are L8 n11594 (0.0524), L0 n2935
   (0.0485) and L9 n520 (0.0442). Six of the top 20 by s_D are members of the size-500 D-only class: the five above
   and L18 n10857. The other 14 are excluded from the class because they are in T_I, apart from L12 n10833, which
   is in T_H only. The top s_H neurons are in layers 12 to 21, and none is in the class.

   The conclusion of the sentence survives only in a weaker form. On the same seed-2 sample, the six members alone
   remove 0.213 of the D margin when summed one at a time. The whole 338-neuron class removes 0.813 under the twin
   interchange (`NP/verdict/far_atp_all_c3d7763/verdict.md`, line 11). About 0.6 is therefore carried by the other
   332 members or by interactions. The class is also not confined to layers 0 to 9: 211 of its 338 neurons are
   there, and layers 10 to 12 hold another 102.

   Suggested wording: "The top 20 neurons by s_D span layers 0 to 19, and the top 20 by s_H span layers 12 to 21.
   The 14 top s_D neurons in layers 12 to 19 that are not in the D-only class are excluded because 13 of them are
   also in the inversion top 500 and one is in the honest top 500.
   The six that are in the class include the three largest single-neuron effects (layers 8, 0 and 9, 0.044 to
   0.052 each). Together the six remove 0.21 of the D margin one at a time, against 0.81 for the whole class, so
   most of the class effect is carried by its other 332 members."

2. **"Faithful predictor at the top of the ranking" needs a qualification.** The sign claim holds in full. The
   rank correlation of 0.93 pools two lists. The s_H list stretches s_D down to minus 0.18, and 8 of its 20 neurons
   have negative s_D, while the s_D list starts at plus 0.18. That wider range inflates the pooled rank correlation.
   Within each list:

   | list | n | ρ(s_D, minus dD) | ρ(s_H, dH) |
   |---|---|---|---|
   | top 20 by s_D | 20 | 0.648 | 0.992 |
   | top 20 by s_H | 20 | 0.997 | 0.988 |

   The weak spot is the early layers, which attribution under-predicts. The measured D shift divided by s_D is
   2.45 for L0 n2935, 1.71 for L9 n520, 1.32 for L5 n171, 1.23 for L12 n10833 and 1.20 for L1 n3349. For the
   neurons in layers 13 to 19 the ratio lies between 0.90 and 1.09. Suggested wording: "faithful in sign for every
   neuron and in size for the layer 13 to 19 neurons; it under-predicts the early-layer neurons by up to a factor
   of 2.5, so the top of the s_D ranking is ordered less well (ρ 0.65 within that list)."

3. **The one H sign miss is a zero prediction.** sD_17 L1 n3349 has s_H minus 0.0004 and a measured dH of plus
   0.0033. Both are noise-sized, so 39 of 40 is not a substantive disagreement. R21 could say so.

## Sanity checks

- **Intact forwards.** `m_intact` on D and H, and `twin_m_intact` on D, are identical across all 40 groups for every
  id and stream (maximum deviation 0.0). The D rows' `twin_m_intact` equals the H rows' own `m_intact` with a
  difference of 0.0.
- **Self-replay.** `summary.json` gives a self-replay error of 0.0 on D. It records no unpaired ids, no missing ids
  and no ids dropped by tokenization.
- **Sets file.** It has 40 groups of one `mlp_hidden` neuron each, and each name's layer and index match its member.
  The sets do not match the readout-position top 20, so the all-position ranking of R11 was used, as R15 (c)
  requires.
- **Manifest.** `run_manifest.json` lists the argv of hand-back 10's one-neuron line, Slurm job 23520193 on
  gpub059, and `git_dirty` false. Its `dataset_files` hashes for the sets file (`873afbce…65f3`) and the seed-2
  sample (`cdbfca85…a845`) match the files on disk. Its five `code_sha256` values match the worktree's current
  files. The manifest names commit `800c9037c22c54256a049a4615b4f06f00493f46`, not the 92fc6fb of the directory
  name. Hand-back 09 already flags this. The code hashes match W9's pre-run list, so the scored code is the code W9
  dry-ran.
- **Attribution provenance.** The c3d7763 reverse run's manifest records commit 8363d3f with `git_dirty` true and
  `--commit c3d7763`. That is the ranking every other cell of this session uses. It is noted here, not re-litigated.

## Commands

Run from `WT` on the Delta login node.

```
OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python outputs/_analyses/neuron-partition/r8_tmp/recompute.py
```

Observed: `n_lines 24000`, counts `twin/D 12000` and `twin/H 12000`, `sets_sD_match_top20_all true`,
`sets_sH_match_top20_all true`, `max_intact_dev_across_sets 0.0`, `both/all40` agreeD 40, agreeH 39, rhoD
0.92943, rhoH 0.99756, duplicates all 0.0, `max_D_removed` sD_01_L8_n11594 0.05241. The output is saved to
`NP/r8_tmp/recompute.json`.

```
/u/swong2/.conda/envs/mgnp/bin/python outputs/_analyses/neuron-partition/r8_tmp/compare2.py
```

Observed: the worst per-group difference is 0.0 in all ten columns. The summary differences are at most 4.4e-16.
The size-500 D-only class has 338 members, 211 of them in layers 0 to 9. Six of the 40 groups are class members.

```
sha256sum scripts/neuron_set_ablation.py component_analysis/knockout.py component_analysis/hooks.py component_analysis/dataloaders.py dataset/ioi_llama.py
```

Observed: `b4efbd59…972a`, `e39cbbed…3914`, `bcd0dc72…b062`, `89e0c613…c4b3` and `624dde94…5c33`, equal to the
manifest's values.

## Discrepancies

- **Numbers.** None in R21 or the report. Every numeric claim holds. One small slip is in hand-back 10, which says
  9 of the top 20 by s_H have negative s_D. The count is 8: L15 n10429, L16 n9215, L18 n3352, L15 n1283, L15 n211,
  L13 n1424, L14 n9545 and L17 n1672. Nothing downstream uses that count.
- **Interpretation.** R21's layer sentence is wrong (correction 1), and its "faithful predictor" sentence overstates
  the magnitude agreement at the top of the s_D list (correction 2).
- **Not checked.** The 1,447 s of 2,700 reserved. `summary.json` gives 1,426 s of script wall time and 44.8 s of
  model load, which is consistent.
