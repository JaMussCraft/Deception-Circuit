# Phase-2 reading (ticket 04): Component cells on U' (D, H, F, I), what the heads read and write, roles, and the proposed C_t

Rewritten by impl-04o on 2026-10-26 from the rebuilt `reports/04-phase2-results.{md,json}` (builder
`outputs/_launch_mechanism_analysis/p2_results.py`), after both reviewers' findings were applied (`reports/04-review.md`).
Curated copies: `docs/research/mechanism-analysis/phase2/` (R6). Cells: `outputs/_analyses/mechanism-analysis-p2/<cell>/
Up__leaf/<t>_*/` on Delta, fetched from Bridges-2 jobs 49876003 / 49876005 / 49876008 (35-38 min each, exit 0;
1.83 GPU-h actual, booked 0.75 per job = 2.25 GPU-h of the 3.5 allocated). U' per task = the 123-head union U | the deciding S_k's heads | the proposed C_t MLP
blocks, at leaf (R26): far 146, sdr 136, ser 144 Components. No single-Component knockout ran here (R16).

**Sign conventions.** Every drop and DLA is read in its cell's own target direction, `target_direction` in the
cell's `knockout/groups.json`: `deceptive` on D and I (I's target slot holds the inverted answer) and `honest` on H
and F. Positive supports that target. The DLA reads the same target and distractor fields with `direction_sign` 1, so
its fixed metric text ("logit(deceptive answer) - logit(honest answer)") is honest-positive on H and F; the H cell's
whole-model margin is +7.2 (far, `dla/dla.json` totals). Every test below is head level, not clustered by pressure id.

**What decides.** The pre-registered rules decide (R0). Family-level R-cls, the sink-free C-reads, the binomial against
U''s own layer share, the B2 signature on I, and the twin-condition family knockouts (d_twinko, I) are exploratory and
labelled so. Where phase 1 already graded a prediction (RQ-A's per-head R-cls, C-confound, R-inv), phase 1's verdict
stands and phase 2 only adds description.

## Verdicts

| prediction (spec section) | phase-2 outcome |
|---|---|
| Pre-clause zero (2.9, R16; sanity, not a finding) | PASS on all three tasks: max abs drop 0.0, 0 non-zero entries |
| B-reader (i): L8-17 share of B2-signature heads above 10/32, one-sided binomial p < 0.05 (2.6) | **holds on all three** (p 9.5e-13 / 2.0e-15 / 4.5e-13) |
| B-reader (ii): L13H5, L13H20, L13H21 show the signature (2.6) | **holds on sdr only.** L13H20 and L13H21 carry it on all three tasks; L13H5 falls below the 0.05 floor on far (0.021) and ser (0.037) |
| C-honest: late H-D heads write honest on H and F, and their honest-direction DLA is >= 50 % smaller under pressure (2.7) | **holds on most heads**: both clauses on 9 of 12 (far), 5 of 7 (sdr), 7 of 8 (ser). No head is merely suppressed: every reduction is a sign flip |
| C-reads: the exclusive sets differ in top-Segment group, Fisher p < 0.05 (2.7) | **fails** (p 0.58). Only 12 of 32 exclusive heads have an established read; the other 20 read the attention sink |
| RQ-A per-head R-cls (2.5) | phase 1's verdict stands: core >= 2/3 shared holds on sdr only; exclusives' majority deception-leaning fails everywhere |
| C-confound (2.7) | phase 1's verdict stands: refuted, far's D-H effect was core |

## 1. RQ-A, component part (C3): family knockouts, descriptive

Phase 1 graded RQ-A on per-head R-cls from the sweeps S1, S5, S6 (`reports/03-phase1-results.json`, rqa). Core shared:
far 16/31, sdr 25/31, ser 18/31. Exclusives deception-leaning: far 3/8, sdr 0/14, ser 1/10. Those are the
pre-registered verdicts. The family knockouts here (item swap, all positions, one group per composition set) describe
the same sets jointly. Values are d = drop / clean margin, signed in each cell's direction (`families.csv`):

| task | family (n) | d on D | d on H | d on F | R-cls bands on the joint drop (descriptive) |
|---|---|---|---|---|---|
| far | core (31) | 1.96 | 1.95 | 1.95 | shared |
| far | excl (8) | 0.53 | -0.25 | -0.25 | deception-leaning |
| far | D-H (26) | 1.56 | 0.60 | 0.62 | deception-leaning |
| far | (D-H)-core (15) | 0.99 | -0.01 | 0.03 | deception-leaning |
| far | late H-D (12) | 0.45 | 0.53 | 0.54 | shared |
| sdr | core (31) | 1.93 | 1.82 | 1.88 | shared |
| sdr | excl (14) | 0.49 | 0.55 | 0.49 | shared |
| sdr | (D-H)-core (15) | 0.52 | 0.55 | 0.51 | shared |
| sdr | late H-D (7) | 0.55 | 0.53 | 0.55 | shared |
| ser | core (31) | 2.04 | 1.96 | 1.97 | shared |
| ser | excl (10) | 1.05 | 0.72 | 0.86 | shared |
| ser | D-H = (D-H)-core (19) | 1.38 | 1.23 | 1.31 | shared |
| ser | late H-D (8) | 0.61 | 0.58 | 0.58 | shared |

What the family numbers add to phase 1:

- Jointly, the core costs the honest margin on H and F as much as the deceptive margin on D, on every task. Per head
  the core is mixed on far and ser (phase 1), so "the core is answer machinery" is a set-level statement only.
- far's exclusives are the one family whose knockout helps the honest answer on H and F (d -0.25, 14-18 SE from zero)
  while costing D. They push towards the pressured answer and against the honest one as a set. Per head only 3 of 8 are
  deception-leaning (phase 1), so the effect is a set property.
- far's (D-H)-core costs D (d 0.99) and nothing on H or F. Phase 1's C-confound verdict (refuted) rests on R-A1 set 6:
  removing the core from D-H drops the interchange KO accuracy effect (set 5 0.191 vs set 6 0.476), and the held-out
  twin f_D of (D-H)-core is 0.105. The two are compatible. Removing the core from D-H keeps two thirds of the D drop
  (3.98 to 2.54 logits) and loses the whole H/F cost, yet that remainder neither flips the answer nor mediates the
  pressure. The verdict stays phase 1's.
- sdr's and ser's exclusives and (D-H)-core cost H and F as much as D, which agrees with phase 1's per-head classes.
- Exploratory (d_twinko, I): under the neutral twin post-clause each family's drop is at most 0.43 of its item-swap
  drop on D (about 0 for sdr's exclusives and D-H), and the I cell's twin drops sit at the same size. The late H-D
  heads give about 0 there (d 0.01), so they do not process the clause.

## 2. RQ-B: where the pressure enters

**B-reader.** B2 signature = Readout-query mass on the Pressure Clause falls under the twin by >= 0.05 and >= 2 SE,
paired over the whole split (D cell).

| task | signature heads / measured | in layers 8-17 | binomial p vs 10/32 (pre-registered) | L13H5 | L13H20 | L13H21 | exploratory p vs U''s own L8-17 share |
|---|---|---|---|---|---|---|---|
| far | 36 / 136 | 32 | 9.5e-13 | no (0.021) | yes (0.072) | yes (0.275) | 0.007 (share 0.70) |
| sdr | 36 / 126 | 34 | 2.0e-15 | yes (0.063) | yes (0.135) | yes (0.402) | 0.0002 (0.68) |
| ser | 28 / 134 | 27 | 4.5e-13 | no (0.037) | yes (0.156) | yes (0.266) | 0.0005 (0.69) |

Clause (i) holds on every task. Clause (ii) holds on sdr and fails on far and ser on L13H5 alone. U' sits mostly in
layers 8-17 anyway, so the exploratory second p tests against that share; the concentration survives it. The
strongest readers are L13H23 (far 0.69), L13H22 (0.35-0.40), L13H21, L10H22 (far 0.28) and L9H3 / L9H16 (far
0.22-0.25). The mean clause mass at the Readout peaks at layer 13 on every task (0.155-0.160 over U' heads); far also
reads the clause at layers 9-11 (0.07-0.10), sdr and ser much less (0.02-0.07). Exploratory: the I cell shows the same
band concentration (36 / 48 / 31 signature heads, binomial p <= 5e-14).

**Segment-resolved neutral-twin knockout of the S2p top 20** (descriptive, spec 2.9; replacing one Component's output
with its twin value at one Segment):

- far: at the clause, MLPs 6 (3.30), 8 (3.20), 7 (2.28), 11 (1.64) and heads 9.19 (0.83), 9.16 (0.81); at the
  Readout, 14.4 (1.81), mlp.13 (1.77), 14.5 (1.67), mlp.14 (0.64), 11.0 (0.53). Joint set: clause 8.3, Readout 2.8,
  question 1.0.
- sdr: Readout first, 17.24 (2.52), 15.8 (2.35), 14.4 (1.66), 14.5 (1.09), 15.11 (0.99), mlp.13 (0.62); at the clause
  only MLPs 8 (0.94), 7 (0.68), 12 (0.63) and head 12.4 (0.35). Joint: Readout 6.5, clause 3.2.
- ser: at the clause, MLPs 5 (2.80), 6 (2.13), 7 (2.12) and heads 9.19 (0.31), 11.0 (0.27); at the Readout 14.4
  (0.66), 14.5 (0.59), mlp.13 (0.53), 13.22 (0.52); 13.23 and mlp.14 at the item-1 question option (0.30, 0.19).
  Joint: clause 4.5, Readout 2.2, response line 1.2.

On far and ser the pressure is processed at the clause by MLP blocks 5-8 (and 11) and layer-9-11 heads, then carried
to the Readout by mlp.13, 14.4 and 14.5. On sdr the clause-position effect is smaller and the Readout carries most of
it through L14-L17 heads. Item Mentions and the stem carry about 0.3 or less jointly, except ser's item-1 option
(0.54). Which of these are movers or selectors is phase 3's question (path patching, B-selector).

## 3. C-honest: the late H-D heads

DLA on H and F is honest-positive. On D the honest-direction DLA is the negated deceptive-positive DLA, read over the
paired instances on both sides (pressure: `dla.pressure_neutral_twin_paired`; twin: `dla.neutral_twin_paired`).

| task | late H-D heads | write honest on H and F (> 0, >= 2 SE) | suppressed (>= 50 % smaller, same sign) | flipped (negative under pressure) | both clauses |
|---|---|---|---|---|---|
| far | 12 (L22 x7, L30 x5) | 10 | 0 | 10 | 9 |
| sdr | 7 (L18 x3, L30 x4) | 5 | 0 | 6 | 5 |
| ser | 8 (L18 x4, L30 x4) | 7 | 0 | 7 | 7 |

Both clauses hold on most heads of every task. The spec's gloss "suppressed, not absent" does not describe what
happens: no head keeps an honest-signed DLA under pressure. Each reduction is a sign flip, so these heads write
towards the pressured answer under pressure (far 30.24: twin +0.26, pressure -0.11; sdr 30.12: +0.08 vs -0.18; ser
30.12: +0.16 vs -0.11). The exceptions:

- far 22.16, sdr 30.15 and ser 30.15 have a twin DLA that is not honest-signed, so no reduction is defined. They are
  near zero or write against the honest answer on H and F as well.
- far 30.15 writes honest and falls by 49 %, just under the bar.
- far 30.30 and sdr 30.30 flip under pressure but miss the 2-SE bar on H or F.

The DLA values are small (largest 0.26 logits), and the ratio is large where the twin DLA is tiny (sdr 18.20: 0.006).

## 4. The I cells: the deciding sets under transparent inversion (descriptive, input to R-inv)

| task | deciding-set heads | B2 signature on D | on I | on both | top Segment the same on I and D |
|---|---|---|---|---|---|
| far | 18 | 16 | 15 | 15 | 17 |
| sdr | 14 | 9 | 10 | 8 | 13 |
| ser | 19 | 6 | 7 | 6 | 19 |

The deciding-set heads read the same Segment on I as on D and mostly keep the B2 signature on both. Their twin-paired
DLA differentials are about zero on both (|diff| <= 0.02), except sdr 17.24, which writes 0.21 on both. The I cell's
roles pass gives pressure reader to 30 / 19 / 19 Components against 32 / 16 / 16 on D. This is descriptive overlap,
the same kind of evidence as phase 1's S7-vs-S2p match. The claim that S_k is instructed-inversion machinery rather
than deception-specific is phase 1's R-inv reading (far and ser; sdr on option B, undecided on the R19(3) subset).
Phase 2 is consistent with it and does not test it.

## 5. C-reads and C2: what the exclusives and the D-H heads read

**C-reads (pre-registered): fails.** Top Segment at the Readout under pressure, mapped to the read groups of
`docs/component-roles.md`. `unestablished` is the absence of a group, so those heads stay out of the test:

| task | item_mention | frame | unestablished (left out) |
|---|---|---|---|
| far | 1 | 3 | 4 |
| sdr | 0 | 5 | 9 |
| ser | 0 | 3 | 7 |

Fisher exact p = 0.58. Twenty of the 32 exclusive heads put their top mass on the attention sink (`unsegmented`,
the BOS position). The 12 that remain all read the frame but one, so this table has almost no power to separate the
sets. The verdict is the faithful table's: the exclusive sets do not differ in what they read.

Exploratory, sink left out (top prompt Segment): p = 0.15. Every set reads the frame most (response line and stem:
far 6/8, sdr 11/14, ser 7/10). sdr's two L24 exclusives read the inverse predicate token, ser's L15-16 exclusives read
Item Mentions (3/10) and far's L14H27 reads the designation suffix. The depth difference of HB (g) stands, but the sets
do not separate by what they read.

**C2.** The results file lists the exclusives and every D-H head (core members flagged) with top Segment, top prompt
Segment, DLA under pressure and on the paired twin, and the B2 drop. The exclusives write almost nothing directly
(|DLA| <= 0.02 on far and ser; sdr's L24H18 / L24H25 0.04 / 0.09). The D-H heads mostly read the response line or
the stem, like the exclusives. The largest D-H direct writers are sdr L24H25 and ser L24H22 (0.09 each).

## 6. Roles under the amended criteria (R7, R10, R27)

No phase-2 cell has path patching, which is what a Component depends on (CONTEXT.md, Component Role). The roles pass
therefore ran with `--roles-allow-missing-views`, and its knockout view was merged from the phase-1 sweeps over the
U' rows (`p2_merge.py`, R16). Rule 4b, pressure reader (B2 signature plus the post-clause twin knockout), is the only
rule that can fire:

| task | D | I | H | F |
|---|---|---|---|---|
| far | 32 | 30 | 0 | 0 |
| sdr | 16 | 19 | 0 | 0 |
| ser | 16 | 19 | 0 | 0 |

Every other Component is `unknown` with flavour `insufficient`, except one `disagree` on sdr D. H and F have no twin,
so rule 4b cannot fire there. The I cell has no plain knockout view because phase 1 ran no I item-swap sweep; its
roles are rule 4b only. roles.json records the missing views per cell.

## 7. Proposed C_t for phase 3, sizes and cost

C_t = core | excl_t | ((D_t - H_t) - core) | S_k heads | 10 MLP blocks (the deciding set's MLPs first, then by S2p
rank, never the layer-0 MLP), per spec section 4 phase 3. The MLP sets equal the phase-2 operands' C_t sets, so
`outputs/_launch_mechanism_analysis/operands/skct_<t>` serves phase 3 unchanged.

| task | heads (core / excl / (D-H)-core / S_k; overlaps counted once) | MLP blocks | Components |
|---|---|---|---|
| far | 62 (31 / 8 / 15 / 18) | 6, 7, 13, 14, 11, 8, 4, 15, 16, 9 | 72 |
| sdr | 56 (31 / 14 / 15 / 14) | 14, 13, 12, 6, 7, 8, 19, 16, 4, 15 | 66 |
| ser | 68 (31 / 10 / 19 / 19) | 5, 13, 14, 6, 7, 11, 15, 1, 19, 16 | 78 |

All three sit in the spec's 55-80 range.

**Phase-3 cost, from the login `--dry-run`** of path patching on the operand-backed C_t (impl-04's probe,
`/u/swong2/.claude/jobs/1c836bb8/tmp/impl04/ct_probe/<t>.txt`): `--path-counterfactual both`, the completeness sweep,
and the twin Segment pass at `--path-twin-position-threshold 0.01`. Derived at 02b's measured H100 rate of 0.036 s
per forward, with 02b's 9-13 min twin Segment pass and 10 min model load:

| task | grid (senders x receivers) | forwards per counterfactual | two counterfactuals | sweep | estimate |
|---|---|---|---|---|---|
| far | 73 x 151 = 5,020 cells | 66,235 | 79 min | 13,767 fwd, 8 min | about 110 min |
| sdr | 67 x 133 = 4,067 cells | 53,768 | 65 min | 8 min | about 95 min |
| ser | 79 x 161 = 5,984 cells | 78,845 | 95 min | 8 min | about 125 min |

At x1.5 the walltimes are about 2.75 h (far), 2.5 h (sdr) and 3.25 h (ser). ser's exceeds the spec's 2.75 h per-task
reserve, and the total of 8.5 h fits the 9.25 GPU-h allocation with 0.75 h of rerun left. Expected total about 5.5
GPU-h. The phase-2 evidence for each member: the S_k heads carry the B2 signature and the post-clause twin effect,
far's exclusives and (D-H)-core are the one D-specific family, and the MLP lists hold the clause-position carriers
(far 6/7/8/11, sdr 7/8/12, ser 5/6/7) plus the Readout carriers (13, 14). A smaller grid for sdr and ser would drop
their shared exclusives (14 and 10 heads), but the spec's definition is kept so the four categories of section 2.3
are read on the same grid per task.

## 8. Limitations to carry into the paper

- Every test is head level. The clustered-by-pressure-id CI is for instance-level quantities only.
- C-reads is dominated by the attention sink, and the faithful table has 12 heads. The sink-free read is exploratory.
- Family-level R-cls describes a set's joint drop. Phase 1's per-head classes are the record.
- C-honest is a DLA reading of direct effects of at most 0.26 logits. The sign flip is a direct-path statement.
- The I cells use the stand-in datasets (far 210, sdr 788, ser 249 rows), smaller than D's 1,000.
- Roles here lack path patching. Nothing but pressure reader can be assigned before phase 3.
