# SDR nls0.3 coarse heads-only D&H core: component analysis of the 43 shared heads

Cell: `outputs/_analyses/sdr-dh-core/dh_core__leaf/sdr/` in the `component-analysis` worktree,
current conventions (no `LEGACY.md`). Circuit: `dh_core__leaf = (D&H)-m` at leaf granularity, **43
attention heads, 0 MLP blocks, 10 layers** (`head_table.json`, `meta.circuit`, `meta.components`).
D is the heads-only coarse SDR nls0.3 deceptive circuit (seed 42), H its honest twin, m the all-MLP
operand `_allmlp_nomb` (run directories in `meta.circuit.operands`). References: `reference.fine`,
`reference.seed1`, `reference.seed123` (`meta.intake.references`). Task: SDR, deceptive condition,
1000-instance test split (`meta.task`). Model: `llama-8b-instruct` (`attention/patterns.json`), in
`torch.bfloat16` under SDPA per the job logs. Companion cells, kept separate by design:
`sdr-dh-core-honest/dh_core__leaf/sdr/` (the 43 heads on H's task) and
`sdr-dh-core-kosweep/dh_core__leaf/sdr/` (knockout sweep over all 1056 Components), both under
`outputs/_analyses/`. Every number names its file; numbers computed from those files are **derived**.

**Sign conventions, stated once** (ADR-0002). In this cell and the sweep cell, positive supports the
deceptive answer: `knockout.logit_diff_drop` and every `dla.*` column are read natively, and
`dla.honest_twin_descriptive` is negated into that direction by the DLA analysis. **The honest-task
cell is different.** Its task is H's dataset (`sdr_honest`, `deception_condition: honest`), whose
Target is the honest answer, so there **positive means the head supports the honest answer** (clean
logit difference +2.1464, `knockout/knockout.json` there). That file's `metric.sign` sentence
("helps deception") and its `dla/dla.json` `metric` sentence ("logit(deceptive answer) −
logit(honest answer)") are the analyses' fixed text and both misread on this cell. The honest cell's
`dla.pressure` runs over exactly the same 1000 instances as this cell's `honest_twin` condition
(instance ids identical, derived check), so it is the same measurement with the opposite sign
convention, on an A100 instead of an A40: L17H24 reads +0.0757 there and −0.0761 here. **The honest
cell's only new measurement is its knockout.**

## 1. Executive summary

1. **About half the core is shared task machinery; the rest leans one way or does little.** Each
   head is placed by one rule (section 5), comparing its knockout on D's deceptive task with its
   knockout on H's honest task after scaling each by its task's clean margin. 22 heads are
   significant on both and within a factor of two; 15 lean deceptive; 3 lean honest; 3 are
   significant on neither (derived). The six heads in both top tens (L17H24, L10H1, L14H4, L24H27,
   L13H18, L11H12) are all in the shared 22. Spearman 0.586, Pearson 0.754 between the two knockout
   columns (derived).
2. **The necessity is joint, and the joint knockout saturates.** Knocking out all 43 heads at once
   drops the logit difference by **+3.2183** (se 0.1167), from +1.6132 to −1.6051, accuracy **0.01**
   (`knockout/knockout_families.json`). That is the mirror of the clean margin, near the metric's
   floor, so the singles' sum of +10.84 (derived) could not have been reached whatever the overlap:
   the sub-additivity says nothing about redundancy. Directly, the 43 write +0.2533 (se 0.0773) of
   the model's +1.7454 under pressure (`dla/dla.json`, `conditions.pressure.totals.all`).
3. **The largest paired differentials do not settle format against deception.** In order: L17H24
   +0.1670, L24H16 +0.1224 (not interpretable) and L24H27 +0.1106. L17H24 and L24H27 flip from the
   deceptive answer under pressure to the honest one under the instruction. That flip fits a mover
   or a selector (`docs/component-roles.md`); the roles pass leans selector and only the path grid
   can decide. Both are also necessary on both tasks, so they meet the brief's two tests at once.
4. **The 15 deception-leaning heads span layers 7 to 17; the strongest are in layers 12 to 17.** By
   margin-scaled difference the top six are L13H5, L13H20, L12H6, L13H21, L14H24 and L17H26
   (derived). The three layer-13 heads attend to the Pressure Clause more than any other head
   (0.245, 0.153 and 0.230 of their mass under pressure for L13H5, L13H20 and L13H21), and that mass
   roughly halves under the honest instruction (derived, `attention/patterns.json`). The same
   halving occurs in shared heads (L14H4, L10H1, L12H28), so it does not mark deception-leaning.
5. **Three heads lean honest**, mattering only on H's task: L14H23, L9H28 and L8H9 (section 5).
6. **The roles pass proposes 43 `unknown/insufficient`** (`roles/roles.json`, `counts`), because
   path patching is deferred. No head carries a pressure-reader signature.
7. **The knockout sweep flags 8 outsiders at 0.4 logits, against 11 circuit heads** (`sweep.json`).
   Five of the eight oppose deception; the two flagged heads that support it, L15H8 (+0.865) and
   L17H25 (+0.450), are in the deceptive-only remainder D − H (derived from the run masks).

## 2. How it was run

| job | cell | partition, node | what | elapsed |
|---|---|---|---|---|
| 22899541 | `sdr-dh-core` | gpuA40x4-interactive, gpub076 | attention_patterns (with token-level PNGs), dla (designation split), single knockouts | 15:08 |
| 22899542 | `sdr-dh-core-honest` | gpuA100x4-interactive, gpua023 | the same three analyses on H's task, pressure condition only | 4:36 |
| 22899543 | `sdr-dh-core-kosweep` | gpuH200x8-interactive, gpue02 | knockout completeness sweep, 1056 Components | 9:33 |
| 22899733 | `sdr-dh-core` | gpuA40x4-interactive, gpub058 | family knockout, grouped by this cell's roles | 3:16 |

All four are `COMPLETED` in `sacct`. The roles pass ran between the trio and the family job
(`roles/roles.json`, `created` 12:43:29), with `missing_views: ["depends, how (path_patching)"]`.

**Samples.** This cell and the sweep cell use the same 100-instance causal sample, seed 0, over 8
strata: identity 52 / inversion 48, item polarity 50/50, audit 50 / lab 50 (`sample.json`,
`marginals`). It is the same 100 ids as the legacy `sdr-first-run` cell (derived check), and the
clean run reproduces that cell's +1.6132 exactly. 71 of the 100 have an Honest-Instruction
Counterfactual; 29 are listed in `dla/dla.json` (`unpaired_instance_ids`). The honest cell's sample
is a different 100 from H's dataset, over **7** strata, because identity / item 2 / audit has no
instances and identity / item 1 / audit has one: identity 35 / inversion 65, audit 34 / lab 66
(`sdr-dh-core-honest/.../sample.json`).

**check_cell.py**, run after the family job. Every missing view is one not run in that cell by design;
no view is `BROKEN`:

| cell | present | missing |
|---|---|---|
| `sdr-dh-core` | head table, attention patterns, top heads, dla, dla heatmap, dla paired scatter, logit lens, knockout, family knockout, segmentation, sample | knockout sweep (lives in its own cell), path patching (deferred), completeness sweep (deferred) |
| `sdr-dh-core-honest` | head table, attention patterns, top heads, dla, dla heatmap, logit lens, knockout, segmentation, sample | dla paired scatter (no paired condition exists for H's task), family knockout, knockout sweep, path patching, completeness sweep |
| `sdr-dh-core-kosweep` | head table, knockout, knockout sweep, segmentation, sample | every attention and DLA view, family knockout, path patching, completeness sweep (none were run there) |

**Checks passed.** Every attention profile sums to one within 2.9e-3 (tolerance 0.02), with no NaN
and `max_outside` 0.0, in all four conditions here and the honest cell's one
(`attention/patterns.json`, `checks`). The DLA sum check over 1057 senders is within 0.0163 of the
model's logit difference (mean magnitude 1.5434) on 8 instances (`dla/dla.json`, `sum_check`); the
honest cell's is 0.0110 against 0.9615. The family job rewrote `knockout/knockout.json`; its 43
singles are bit-identical to a copy of the trio's taken before it ran, which is not kept in the cell
(derived check).

## 3. The 43 heads, with the proposed roles

From `head_table.json`, `roles/roles.json`, the honest cell's `head_table.json` and the sweep cell's
`knockout/sweep.json`. Sorted by the deceptive-task knockout rank.

**ref** is `reference.fine`, `reference.seed1`, `reference.seed123` (y = member; every head is in
seed 42, which is D). **reads** is the top Segment at the Readout and its mass over the 71 paired
instances (`attention_patterns.{pressure,honest_instruction}_paired_*`); the full-split pressure top
Segment matches the paired one for all 43 (derived). **dla P** is `dla.pressure` (1000), **diff**
`dla.differential_paired` (71). **KO** is `knockout.logit_diff_drop` (se) [rank among the 43]: this
cell for deceptive, the honest cell for honest (positive = supports the honest answer). **sweep** is
the rank by absolute drop among all 1056 Components (`sweep.json`, H200).

`item_1` and `item_2` are **positional** (first and second item as the user question lists them),
not designated and undesignated (`component_analysis/segmentation.py`; `CONTEXT.md`, Item Polarity).
Item polarity is 50/50, so a head that tracks the designated item splits its mass across the two,
and the top Segment's name says nothing about which item.

| head | ref F s1 s123 | reads, pressure | reads, honest instr. | dla P | diff | KO deceptive | KO honest | sweep | role proposed |
|---|---|---|---|---|---|---|---|---|---|
| L17H24 | y y y | item_1_q_option (0.23) | item_2_q_pair (0.19) | +0.1000 | +0.1670 | +1.292 (0.053) [1] | +1.398 (0.068) [1] | 2 | unknown, selector lean |
| L10H1 | y y y | question (0.71) | question (0.71) | +0.0019 | -0.0011 | +0.862 (0.078) [2] | +0.869 (0.155) [5] | 4 | unknown |
| L14H4 | y y y | desig_suffix (0.20) | unsegmented (0.26) | +0.0040 | +0.0089 | +0.669 (0.053) [3] | +1.011 (0.082) [4] | 7 | unknown |
| L24H27 | y y y | item_1_q_option (0.28) | unsegmented (0.22) | +0.0467 | +0.1106 | +0.615 (0.024) [4] | +0.790 (0.032) [6] | 8 | unknown, selector lean |
| L13H20 | y y y | unsegmented (0.36) | unsegmented (0.34) | +0.0004 | -0.0006 | +0.599 (0.046) [5] | +0.192 (0.076) [16] | 10 | unknown |
| L13H18 | y y y | question (0.31) | desig_suffix (0.33) | +0.0015 | +0.0005 | +0.598 (0.075) [6] | +1.228 (0.116) [2] | 9 | unknown |
| L11H12 | y y y | question (0.55) | question (0.50) | -0.0001 | +0.0000 | +0.594 (0.054) [7] | +0.503 (0.117) [8] | 11 | unknown |
| L12H6 | y y y | unsegmented (0.49) | unsegmented (0.50) | -0.0001 | +0.0008 | +0.527 (0.050) [8] | +0.236 (0.080) [14] | 13 | unknown |
| L13H21 | y y y | desig_suffix (0.40) | desig_suffix (0.54) | -0.0003 | -0.0007 | +0.470 (0.041) [9] | +0.214 (0.052) [15] | 16 | unknown, binder lean |
| L13H5 | y y y | unsegmented (0.28) | unsegmented (0.28) | +0.0018 | +0.0018 | +0.459 (0.036) [10] | -0.133 (0.070) [43] | 19 | unknown |
| L14H5 | y y y | question (0.20) | desig_suffix (0.28) | +0.0025 | +0.0054 | +0.452 (0.055) [11] | +1.166 (0.072) [3] | 18 | unknown |
| L17H26 | y y y | item_1_q_option (0.31) | desig_sentence (0.28) | +0.0092 | +0.0134 | +0.388 (0.015) [12] | +0.157 (0.016) [18] | 24 | unknown |
| L11H13 | y y y | unsegmented (0.41) | unsegmented (0.38) | +0.0004 | +0.0004 | +0.333 (0.034) [13] | +0.429 (0.075) [9] | 30 | unknown |
| L10H2 | y y y | question (0.74) | question (0.75) | +0.0029 | -0.0008 | +0.278 (0.040) [14] | +0.136 (0.057) [20] | 39 | unknown |
| L12H4 | y y y | question (0.39) | question (0.32) | -0.0009 | -0.0023 | +0.250 (0.044) [15] | +0.394 (0.063) [10] | 43 | unknown |
| L14H24 | y y y | question (0.40) | question (0.29) | +0.0002 | -0.0005 | +0.239 (0.038) [16] | -0.043 (0.066) [42] | 45 | unknown |
| L10H28 | y y y | question (0.42) | question (0.37) | -0.0013 | +0.0005 | +0.218 (0.035) [17] | +0.127 (0.057) [21] | 51 | unknown |
| L12H13 | y y y | unsegmented (0.47) | unsegmented (0.46) | -0.0003 | +0.0006 | +0.198 (0.029) [18] | +0.283 (0.051) [11] | 54 | unknown |
| L9H31 | y y y | question (0.68) | question (0.66) | -0.0005 | -0.0004 | +0.184 (0.025) [19] | +0.013 (0.040) [38] | 58 | unknown |
| L11H8 | y y y | unsegmented (0.46) | unsegmented (0.42) | -0.0011 | -0.0003 | +0.179 (0.027) [20] | +0.070 (0.036) [26] | 60 | unknown |
| L7H1 | · · y | unsegmented (0.53) | unsegmented (0.53) | +0.0006 | -0.0005 | +0.168 (0.023) [21] | +0.150 (0.045) [19] | 61 | unknown |
| L11H14 | y y y | question (0.45) | question (0.45) | -0.0007 | -0.0002 | +0.151 (0.027) [22] | +0.177 (0.054) [17] | 68 | unknown |
| L8H1 | y y y | question (0.70) | question (0.64) | +0.0002 | +0.0016 | +0.131 (0.017) [23] | +0.126 (0.033) [22] | 80 | unknown |
| L8H0 | y y y | question (0.75) | question (0.73) | -0.0001 | -0.0008 | +0.130 (0.018) [24] | +0.044 (0.026) [33] | 81 | unknown |
| L12H28 | y y y | unsegmented (0.50) | unsegmented (0.53) | -0.0000 | +0.0002 | +0.119 (0.016) [25] | +0.244 (0.029) [13] | 84 | unknown |
| L24H26 | y y y | unsegmented (0.48) | unsegmented (0.50) | +0.0185 | +0.0399 | +0.106 (0.008) [26] | +0.079 (0.008) [25] | 91 | unknown |
| L8H11 | y y y | question (0.98) | question (0.98) | -0.0006 | -0.0014 | +0.093 (0.028) [27] | +0.111 (0.042) [24] | 96 | unknown |
| L9H26 | y y y | unsegmented (0.59) | unsegmented (0.56) | +0.0002 | -0.0001 | +0.088 (0.021) [28] | +0.015 (0.027) [37] | 99 | unknown |
| L9H20 | y y y | unsegmented (0.63) | unsegmented (0.61) | -0.0004 | -0.0013 | +0.087 (0.014) [29] | +0.121 (0.027) [23] | 112 | unknown |
| L7H29 | · · y | unsegmented (0.59) | unsegmented (0.56) | -0.0003 | +0.0003 | +0.070 (0.017) [30] | -0.027 (0.014) [41] | 125 | unknown |
| L8H14 | y · y | unsegmented (0.52) | unsegmented (0.46) | -0.0001 | +0.0004 | +0.068 (0.015) [31] | +0.049 (0.020) [30] | 131 | unknown |
| L8H6 | y y y | unsegmented (0.64) | unsegmented (0.63) | -0.0004 | +0.0004 | +0.054 (0.011) [32] | +0.055 (0.019) [28] | 139 | unknown |
| L8H8 | y · · | question (0.67) | question (0.68) | -0.0001 | +0.0001 | +0.047 (0.015) [33] | -0.014 (0.039) [39] | 152 | unknown |
| L12H7 | · y y | unsegmented (0.59) | unsegmented (0.58) | +0.0001 | -0.0004 | +0.037 (0.017) [34] | +0.051 (0.029) [29] | 170 | unknown |
| L24H17 | y y y | unsegmented (0.62) | unsegmented (0.56) | +0.0473 | +0.0626 | +0.033 (0.007) [35] | +0.049 (0.011) [31] | 186 | unknown |
| L24H16 | y · y | unsegmented (0.69) | unsegmented (0.68) | -0.0228 | +0.1224 | +0.028 (0.009) [36] | +0.047 (0.014) [32] | 179 | unknown |
| L24H18 | y y y | unsegmented (0.64) | unsegmented (0.63) | +0.0444 | +0.0703 | +0.023 (0.004) [37] | +0.026 (0.009) [34] | 260 | unknown |
| L7H23 | · · y | question (0.74) | question (0.74) | +0.0006 | -0.0000 | +0.018 (0.015) [38] | -0.016 (0.018) [40] | 424 | unknown |
| L7H2 | · · · | unsegmented (0.59) | unsegmented (0.60) | -0.0000 | +0.0006 | +0.012 (0.008) [39] | +0.018 (0.009) [36] | 476 | unknown |
| L14H23 | y y y | question (0.47) | question (0.43) | +0.0023 | +0.0020 | +0.011 (0.032) [40] | +0.658 (0.040) [7] | 342 | unknown |
| L9H28 | · y y | question (0.31) | question (0.32) | +0.0003 | -0.0001 | +0.007 (0.054) [41] | +0.265 (0.076) [12] | 747 | unknown |
| L8H9 | · · y | question (0.50) | question (0.49) | +0.0003 | +0.0008 | +0.002 (0.015) [42] | +0.058 (0.022) [27] | 455 | unknown |
| L10H3 | · y y | question (0.36) | question (0.38) | -0.0028 | +0.0011 | -0.044 (0.032) [43] | +0.020 (0.038) [35] | 150 | unknown |

Every `unknown` is `unknown/insufficient`. Thresholds, from `roles/roles.json`: z ≥ 2.0, DLA floor
0.01, knockout floor 0.01, path floor 0.01, attention floor 0.20. `role_confirmed` is absent from
the head table, so no role is confirmed.

## 4. The roles pass

Rules 3 to 6 (binder, selector, mover and `unknown/knockout-only`) need the path-patching view
(`docs/component-roles.md`). It was not measured, so the pass reports only leans: **selector lean,
query not met** for L17H24 and L24H27, **binder lean, depends not met** for L13H21
(`roles/roles.json`, `notes`). The selector query clause needs the honest-instruction path grid; the
DLA flip in section 6 is what a mover would also show. Rule 2 (suppressor) needs no path view, and
no head meets it: none has a significantly negative deceptive knockout or `dla.pressure`, and no
`dla.suppression` is true. `roles.reads_group` counts 21 `unestablished`, 18 `frame`, 3
`item_mention` and 1 `designation` (L13H21) (derived). No row carries a pressure-reader note: no
head's paired top Segment is `pressure_clause`.

## 5. Cut 1: knockout on the deceptive task against the honest task

The singles on each task (`knockout/knockout.json` in each cell):

| | deceptive task (this cell) | honest task (honest cell) |
|---|---|---|
| clean logit difference | +1.6132 (se 0.0886), accuracy 1.00 | +2.1464 (se 0.1220), accuracy 1.00 |
| heads with drop ≥ 0.01 and z ≥ 2 | 37 of 43 (derived) | 31 of 43 (derived) |
| strongest single | L17H24 +1.2918, accuracy 0.66 | L17H24 +1.3983, accuracy 0.84 |
| sum of the 43 singles | +10.84 (derived) | +11.35 (derived) |

**The rule.** The two samples differ in instances and prompt distribution, so sizes are compared only
after scaling. A head is significant on a task when its drop is at least 0.01 with z ≥ 2. Its
margin-scaled drop is the drop over its own task's clean margin (1.6132 deceptive, 2.1464 honest),
and its ratio is scaled deceptive over scaled honest. Every head falls in exactly one set (derived):

| set | rule | heads |
|---|---|---|
| shared | significant on both, ratio 0.5 to 2 | 22: L17H24, L10H1, L14H4, L24H27, L13H18, L11H12, L14H5, L11H13, L12H4, L12H13, L11H14, L8H1, L7H1, L12H28, L24H26, L8H11, L9H20, L8H14, L8H6, L24H17, L24H16, L24H18 |
| deception-leaning | significant on the deceptive task only, or on both with ratio above 2 | 15: L13H5, L13H20, L12H6, L13H21, L14H24, L17H26, L10H2, L9H31, L11H8, L10H28, L8H0, L7H29, L9H26, L8H8, L12H7 |
| honest-leaning | significant on the honest task only, or on both with ratio below 0.5 | 3: L14H23, L9H28, L8H9 |
| neither | significant on neither | 3: L7H23, L7H2, L10H3 |

**Shared.** The 22 include all six heads in both top tens: L17H24 (rank 1 on both), L10H1 (2 and 5),
L14H4 (3 and 4), L24H27 (4 and 6), L11H12 (7 and 8) and L13H18 (6 and 2). L14H5 (ratio 0.52) and
L13H18 and L12H28 (0.65) tilt honest but stay inside the factor of two. These heads help the model
produce whichever answer its task demands.

**Deception-leaning.** The 15 span layers 7 to 17. Ordered by scaled difference, deceptive minus
honest (derived), the first six are well separated from the rest:

| head | KO deceptive (z) [rank] | KO honest (z) [rank] | scaled | Pressure Clause mass, pressure → honest instr. |
|---|---|---|---|---|
| L13H5 | +0.459 (12.8) [10] | −0.133 (−1.9) [43] | 0.28 / −0.06 | 0.245 → 0.101 |
| L13H20 | +0.599 (13.0) [5] | +0.192 (2.5) [16] | 0.37 / 0.09 | 0.153 → 0.074 |
| L12H6 | +0.527 (10.5) [8] | +0.236 (2.9) [14] | 0.33 / 0.11 | 0.050 → 0.032 |
| L13H21 | +0.470 (11.5) [9] | +0.214 (4.1) [15] | 0.29 / 0.10 | 0.230 → 0.108 |
| L14H24 | +0.239 (6.3) [16] | −0.043 (−0.7) [42] | 0.15 / −0.02 | 0.070 → 0.056 |
| L17H26 | +0.388 (25.8) [12] | +0.157 (9.5) [18] | 0.24 / 0.07 | 0.031 → 0.021 |

The other nine have scaled differences of 0.11 or less: L10H2 0.109, L9H31 0.108, L11H8 0.079,
L10H28 0.076, L8H0 0.060, L7H29 0.056, L9H26 0.047, L8H8 0.035 and L12H7 −0.001. L12H7 qualifies
only because its honest drop (z 1.8) misses the bar; on size it is shared. Shared heads L17H24
(0.150), L11H12 (0.133) and L10H1 (0.130) have larger scaled differences than all nine, because the
ratio rule is relative. L13H5 and L14H24 are non-significantly negative on H's task (z −1.9 and
−0.7): "not needed there", not "opposes there". L7H29's honest drop, −0.027 at z −2.008, just clears
the bar in the opposite direction.

**Honest-leaning.** L14H23 +0.011 (z 0.4) against +0.658 (z 16.5, rank 7); L9H28 +0.007 (z 0.1)
against +0.265 (z 3.5); L8H9 +0.002 against +0.058 (z 2.7). D's own task barely uses them singly.

**Joint knockout** (`knockout/knockout_families.json`; one family, because every head is `unknown`):

| family | heads | mean drop | se | knocked logit difference | accuracy | sum of singles |
|---|---|---|---|---|---|---|
| unknown | 43 | **+3.2183** | 0.1167 | −1.6051 | **0.01** | +10.84 (derived) |

This is the circuit-level necessity check, not a role effect. It reproduces the evaluation wave's
result on this cell's own sample: there the 43-head knockout gave accuracy 0.000 and logit
difference −1.733 over 1000 items (`_launch/wave_status.md`, "Pair compositions"). Removing all 43
costs about twice the clean margin: the knocked value, −1.6051, mirrors the clean +1.6132, near the
metric's floor. The positive control `mlp.0.0`, which acts like re-embedding the corrupt prompt,
reaches −1.4308 (`sweep.json`); no corrupt-run value is stored. **So the joint drop cannot exceed
about 3.2, and the singles' +10.84 sum forces sub-additivity**: the ratio of about 30 percent
(derived) does not measure redundancy. Testing redundancy needs family knockouts of subsets that do
not saturate. No family knockout ran on H's task.

## 6. Cut 2: the paired differential and the reads

**What the 43 write** (`dla/dla.json`, `conditions.<name>.totals.all`; honest row from the honest
cell's `dla/dla.json`):

| condition | n | model logit difference | the 43 heads | outside the circuit |
|---|---|---|---|---|
| pressure | 1000 | +1.7454 | +0.2533 (se 0.0773) | +1.4920 |
| pressure (paired left term) | 71 | +1.5857 | −0.0164 (se 0.2714) | +1.6017 |
| honest instruction (paired) | 71 | −2.3468 | −0.6177 (se 0.2774) | −1.7292 |
| differential (paired) | 71 | +3.9325 | +0.6013 (se 0.0472) | +3.3309 |
| honest twin | 1000 | −2.1120 | −0.1747 | −1.9371 |
| H's task, honest cell (positive = honest answer) | 1000 | +2.0949 | +0.1724 | +1.9222 |

The circuit writes 14.5 percent of the Readout margin under pressure (derived). Only the paired
differential is precise. Its two terms have standard errors of about 0.27, and the full-split
+0.2533 is within one of them, so which side carries the +0.6013 is unresolved.

**36 of 43 heads have a near-zero paired differential**, which is uninformative for heads that write
nothing in any condition. Only five have a significant, above-floor `dla.pressure` (L17H24, L24H27,
L24H26, L24H17, L24H18). Seven differentials clear the 0.01 DLA floor at z ≥ 2, all in layers 17 and
24 (`head_table.csv`; terms from `dla.pressure_paired`, `dla.honest_instruction_paired`,
`dla.honest_twin_descriptive`, and the honest cell's `dla.pressure`):

| head | pressure (paired) | honest instr. (paired) | differential | twin | H's task (honest sign) |
|---|---|---|---|---|---|
| L17H24 | +0.0902 | −0.0768 | +0.1670 | −0.0761 | +0.0757 |
| L24H16 | −0.2345 | −0.3569 | +0.1224 | +0.0271 | −0.0271 |
| L24H27 | +0.0470 | −0.0637 | +0.1106 | −0.0680 | +0.0678 |
| L24H18 | +0.0616 | −0.0087 | +0.0703 | −0.0383 | +0.0379 |
| L24H17 | +0.0033 | −0.0593 | +0.0626 | −0.0008 | +0.0001 |
| L24H26 | +0.0270 | −0.0128 | +0.0399 | −0.0127 | +0.0125 |
| L17H26 | +0.0075 | −0.0059 | +0.0134 | −0.0047 | +0.0046 |

**Reading that table.** L17H24 and L24H27 write the deceptive answer under pressure and the honest
answer under the honest instruction and on the Twin (H's task's data), at similar size each way.
L24H26 and L17H26 flip the same way, less evenly (about 2:1 and 1.3:1). A flip is what a mover that
does not know it is lying would show, and it is also what a selector would show:
`docs/component-roles.md` says the flip does not separate them and the query-side path does. The
roles pass leans selector for L17H24 and L24H27, and only the honest-instruction path grid can
decide. On the 71 paired instances L24H17 writes only under the instruction (−0.0593), though its
full-split `dla.pressure` is +0.0473 (z 2.05). L24H18 writes mostly under pressure (+0.0616 against
−0.0087). Both have small knockouts (+0.033, +0.023). L24H16, with the second-largest differential,
writes against the deceptive answer under both instructions, has a full-split se of 0.069 and reads
`unsegmented`; it is not interpretable here.

**Read moves.** Six heads change top Segment between the paired pressure and honest-instruction
conditions (`head_table.csv`). None moves to or from `pressure_clause`:

| head | pressure (paired) | honest instr. (paired) | Twin and H's task |
|---|---|---|---|
| L17H24 | item_1_question_option 0.23 | item_2_question_pair 0.19 | item_2_question_pair 0.18 |
| L14H4 | designation_suffix 0.20 | unsegmented 0.26 | unsegmented 0.25 |
| L24H27 | item_1_question_option 0.28 | unsegmented 0.22 | item_1_question_option 0.25 |
| L13H18 | question 0.31 | designation_suffix 0.33 | designation_suffix 0.30 |
| L14H5 | question 0.20 | designation_suffix 0.28 | designation_suffix 0.24 |
| L17H26 | item_1_question_option 0.31 | designating_sentence 0.28 | designating_sentence 0.27 |

In five of the six the honest-instruction read equals the Twin read. Every mass in that table is
within 0.13 of the 0.20 floor and the item Segments are positional, so these are weak reads.
Grouping the Segments (derived, from the full profiles in `attention/patterns.json`) shows what
moves. L17H24 puts 0.72 of its mass on Item Mentions under pressure and 0.58 under the instruction,
while its designation mass rises from 0.09 to 0.21. L17H26 moves from 0.45 item / 0.17 designation
to 0.19 / 0.50. L14H5's designation mass rises from 0.34 to 0.52.

**The Pressure Clause is attended to, but is never a top Segment, so never a read.** The largest
`pressure_clause` masses, paired pressure → paired honest instruction (derived; under the
instruction those positions hold the Matched Honest Instruction, length-matched token for token):
L13H5 0.245 → 0.101, L13H21 0.230 → 0.108, L13H20 0.153 → 0.074, L14H4 0.125 → 0.031. L11H13 (0.120
→ 0.123) and L13H18 (0.108 → 0.094) do not move. The halving is not specific to the
deception-leaning heads: L14H4 drops furthest (ratio 0.25), and the shared heads L10H1 (0.41) and
L12H28 (0.47) halve as much as the layer-13 heads (0.41 to 0.48). No head is a pressure-reader
signature, which needs `pressure_clause` as the top Segment.

## 7. Cut 3: seed and fine stability

From the `reference.*` columns of `head_table.csv`: 35 heads are in the fine circuit, 35 in seed 1,
41 in seed 123, 35 in all three seeds and 32 in all three seeds and the fine circuit. The overlaps
with the other cuts are derived.

- **The eight heads that are not seed-stable are the low-necessity tail.** L7H1, L7H2, L7H23, L7H29,
  L8H8, L8H9, L8H14 and L24H16 rank 21, 39, 38, 30, 33, 42, 31 and 36 of 43 on the deceptive
  knockout. Four are layer-7 heads, as `wave_status.md`'s "Seed stability" section notes.
- **The three lowest-ranked heads on the deceptive knockout are outside the fine circuit.** L9H28
  (+0.007), L8H9 (+0.002) and L10H3 (−0.044) have `reference.fine` false. Six heads are
  non-significant there; L14H23 (+0.011) is one of them and is in the fine circuit.
- **By set** (section 5): of the 15 deception-leaning heads, 12 are seed-stable and in the fine
  circuit; L7H29 is neither, L8H8 is not seed-stable and L12H7 is not fine. The top six are all
  stable and fine. Of the 22 shared heads, 19 are; L7H1 is neither, and L8H14 and L24H16 are not
  seed-stable.

## 8. The knockout completeness sweep

Cell `sdr-dh-core-kosweep`, job 22899543, H200, the same 100 instances as this cell. It ran 13754
forwards in 505.7 s (`sweep.json`, `cost`). Its clean run is +1.6153 (se 0.0895) against this cell's
A40 +1.6132. Its 43 in-circuit drops differ from this cell's by at most 0.0132 (L8H14) and by 0.0045
on average (derived). That is cross-card drift, which is why the sweep stays in its own cell.

**Threshold ladder** (`threshold_counts`; the layer 0 MLP positive control is excluded from the
outside count):

| absolute drop at least | 0.02 | 0.05 | 0.1 | 0.2 | 0.4 |
|---|---|---|---|---|---|
| outside the circuit | 189 | 105 | 67 | 35 | 8 |
| in the circuit | 37 | 31 | 26 | 17 | 11 |

**The 8 flagged outsiders at 0.4 logits** (`flagged`, with values from `components`; D − H
membership derived from the D and H masks):

| sweep rank | Component | drop | se | accuracy | membership |
|---|---|---|---|---|---|
| 3 | head.20.14 | −0.9761 | 0.0528 | 1.00 | in neither D nor H |
| 5 | head.15.8 | +0.8651 | 0.0772 | 0.76 | D − H |
| 6 | head.18.22 | −0.7820 | 0.0371 | 1.00 | in neither |
| 12 | head.19.3 | −0.5795 | 0.0373 | 1.00 | in neither |
| 14 | mlp.11.0 | +0.4970 | 0.0515 | 0.93 | MLP, outside every heads-only circuit |
| 15 | mlp.30.0 | −0.4702 | 0.0685 | 1.00 | MLP, outside every heads-only circuit |
| 17 | head.26.15 | −0.4616 | 0.0206 | 1.00 | in neither |
| 20 | head.17.25 | +0.4502 | 0.0274 | 0.99 | D − H |

The positive control `mlp.0.0` ranks first at +3.0461, accuracy 0.01 (`positive_controls`).

- **Five of the eight oppose deception**: their knockout raises the deceptive margin, and neither D
  nor H contains the four heads among them.
- **Both flagged heads that support deception are in D − H.** head.17.25 is also the strongest head
  of the fine-circuit delta in `sdr-first-run`. D − H as a set leaves accuracy 0.384 when knocked
  out (`wave_status.md`).
- **The two MLPs are outside by construction**: heads-only circuits never gate MLPs.
- **The 11 circuit heads that clear 0.4** are L17H24, L10H1, L14H4, L24H27, L13H18, L13H20, L11H12,
  L12H6, L13H21, L14H5 and L13H5, at sweep ranks 2 to 19. The circuit holds 11 of the top 20, 15 of
  the top 43, 28 of the top 100 and 37 of the top 200 (derived). Its lowest is L9H28, rank 747.
- **Summed sweep drops by remainder** (derived; singles do not add): D & H +10.73, D − H +2.38, H −
  D +1.23. D − H heads rank 5 to 888, H − D heads 34 to 970.

## 9. Answering the question: format components or deception-relevant?

**What the brief defined.** A format component looks the same with and without the pressure:
near-zero paired differential, same read, comparable knockout on both tasks. A deception-relevant
component differs on one of those.

**Evidence for a format or task core.** 22 of 43 heads are significant on both tasks and within a
factor of two after margin scaling, including the six strongest (section 5). 37 of 43 keep their top
Segment between pressure and instruction (section 6). The 36 near-zero differentials are not
evidence either way, because most of those heads write nothing; the format reading rests on the
knockouts and the reads.

**Evidence against a pure format core.** 15 heads lean deceptive, six of them strongly: L13H5,
L13H20, L12H6, L13H21, L14H24 and L17H26. They write nothing measurable directly, so what they do
reaches the Readout through other heads. Three heads lean honest. Six heads change their weak top
read between pressure and instruction. L17H24 and L24H27 meet both the brief's tests: they are
necessary on both tasks, and they have large paired differentials. They carry 58 percent of the
circuit's full-split pressure write and 46 percent of its paired differential (derived).

**Verdict.** About half the core, 22 heads, is shared task machinery that serves the honest answer
as much as the deceptive one. The singles suggest the joint knockout would also destroy H's task,
but none ran there. A deception-leaning minority, strongest in L13H5, L13H20, L12H6 and L13H21, is
the best candidate inside the core for where pressure matters. The layer-13 heads attend to the
Pressure Clause, but so do shared heads, so that attention does not explain their leaning.

**What this cell cannot settle.** Whether the deception-leaning heads feed the queries, keys or
values of L17H24 and L24H27, and whether those two are movers or selectors, are direct-path
questions; nothing here measures direct paths. The joint knockout saturates, so "the intersection
carries the necessity" says the shared machinery is necessary, not that the deception computation
lives there. The D − H heads head.15.8 (+0.865) and head.17.25 (+0.450) are individually as
necessary as the core's second- and tenth-ranked heads, L10H1 and L13H5.

## 10. Caveats

1. **Path patching is deferred**: both counterfactual grids and the path completeness sweep. The
   43-head grid is 1,920 cells, about 80 A40-minutes per counterfactual by the orchestrator's
   estimate. Nothing in this document infers a direct path, and the roles pass cannot assign any
   role without that view.
2. **The honest-task sample differs**: a different 100 instances from a different dataset over 7
   strata, with an inversion-heavy marginal (65 of 100, against 48 here). Section 5 compares ranks,
   signs and margin-scaled drops, never raw differences. No family knockout ran on H's task.
3. **Different cards.** The honest cell's attention and DLA repeat this cell's Twin columns on the
   same 1000 instances, on an A100, so they are not independent evidence. The sweep ran on an H200
   and differs from this cell's A40 knockouts by up to 0.013 logits, so it is its own cell.
4. **No `role_confirmed`**; every role here is proposed, and all are `unknown/insufficient`.
5. **Columns cover different samples**: `dla.pressure` and the full-split attention columns cover
   1000 instances, every paired column 71, and knockout 100 (`meta.coverage`). No number here
   subtracts across those boundaries.
6. **Reads are weak and positional.** Every read move sits within 0.13 of the attention floor, the
   item Segments are positional, and everything is read at the Readout query only. Pressure Clause
   and grouped masses are derived from `attention/patterns.json`; no head-table column carries them.

## 11. Runtime

Per-analysis boundaries are output-file modification times against each job's `sacct` start
(12:27:39 for the first three). The model load is inside the first row of each job.

| job | analysis | card | wall | note |
|---|---|---|---|---|
| 22899541 | model load + attention_patterns, 4 conditions + token-level | A40 | 11:50 | to `attention/top_heads.json` at 12:39:29 |
| 22899541 | dla | A40 | 1:23 | to `dla/logit_lens_paired.json` at 12:40:52 |
| 22899541 | knockout, 43 singles | A40 | 1:51 | to `knockout/knockout.json` at 12:42:43 |
| 22899541 | whole job | A40 | **15:08** | |
| 22899542 | load + attention 3:13, dla 0:23, knockout 0:56 | A100 | **4:36** whole job | pressure condition only |
| 22899543 | completeness sweep, 1056 Components, 13754 forwards | H200 | 505.7 s; **9:33** whole job | 0.0368 s per forward (`sweep.json`, `cost`) |
| 22899733 | family knockout, 1 family of 43, plus singles | A40 | **3:16** whole job | 12:44:57 to 12:48:13 |

## 12. Next steps

1. **Run the path patching**, at about 80 A40-minutes per counterfactual for the 1,920-cell grid.
   The honest-instruction grid is the one that answers section 9: does L13H5, L13H20 or L13H21 feed
   the Q, K or V of L17H24 or L24H27?
2. **Family knockouts of the cuts**, on both tasks: the 22 shared heads, the 15 deception-leaning
   heads and the three honest-leaning heads, each jointly. The family pass groups by role, so this
   needs `role_confirmed` values or a grouping flag. The 43-head family job took 3:16.
3. **Split the reads by item polarity** from `attention/token_level/`, to turn positional item reads
   into designated-item reads, and read the layer-13 heads at the Pressure Clause query position.
4. **Analyse head.15.8 and head.17.25 with the core**, the deception-supporting Components it lacks.
5. **Evaluate the 35-head seed-stable subset**, which `wave_status.md` notes has not been evaluated.
