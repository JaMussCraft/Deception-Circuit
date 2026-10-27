# Mechanism analysis: synthesis, claims and limitations (ticket 06)

Written by impl-06 on 2026-10-26 from the phase readings of tickets 03, 04 and 05, the curated tables in this
directory and the instructed-inversion record (`inversion-control.md`). Model: Llama-3.1-8B-Instruct. Inputs: the six
coarse heads-only v2 circuits (NLS 0.3, seed 42) and the v2 datasets far_v2, sdr_v2 and ser_v2 with their Neutral-Clause
Twin (H), no-pressure (F) and instructed-inversion (I) conditions. Spec: `.scratch/mechanism-analysis/spec.md`
(sections 2, 4, 7 and rulings R0-R29).

**How to read the sources.** A path such as `phase1/rinv.csv` is relative to this directory
(`docs/research/mechanism-analysis/`). `reports/...` is the working record in
`/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports/`, outside the repository. `figures/...` are the
CSVs this ticket extracted; `figures/figures_meta.json` names every CSV's own sources. A number marked "derived" is
computed from the named file and is not printed there.

**Verdicts.** Only the pre-registered rules of spec section 2 decide (R0). "confirmed" and "refuted" apply to
pre-registered predictions and rules. "Exploratory" and "descriptive" readings never decide and are kept in their own
table. This document compiles the verdicts the phase readings made and overturns none of them. Two predictions no
reading graded (A3, H11) are graded here from their rules, and say so.

## 1. Headline

**R-AB reads A′ overall: far A′, ser A′, sdr B** (`phase1/p1c_readings.json`, `reports/03-phase1-reading.md`). On far
and ser a set of 20 Components, chosen greedily on the selection sample, removes most of the pressure effect on the
held-out sample (f_D 0.893 and 0.904). Each set also carries the item, so test (ii) fails. On sdr no set of 20 or fewer
Components mediates the pressure.

**The A′ sub-reading on both A′ tasks is A′-clause-reader** (`phase3/a_prime.csv`, `reports/05-phase3-reading.md`).
On the selection sample, the deciding set's head weight sits mostly on heads whose strongest neutral-twin input arrives
through their keys or values from the Pressure Clause span: far 0.74, ser 0.83.

**R-inv labels both deciding sets (far, ser) "instructed inversion machinery"** on the primary paired sample
(`phase1/rinv.csv`): f_I is above half of f_D with the clustered CI clear of zero. By spec 2.4 the paper therefore does
not call these sets deception-specific, which is all the label licenses. Both readings are below the 300-id minimum; FAR polarity-confounded, inversion-polarity subset agrees
(FAR's and SER's I pools keep 210 and 249 ids; R30 keeps the readings as run under R23; section 5, L6). sdr has no
deciding set and so no R-inv verdict; its descriptive S_20 contrast is reported in H9 as description only.

In one sentence: on far and ser a small set, mostly clause-reading heads in layers 7-14 fed by early MLPs, mediates
the pressure on held-out instances, but the set also carries the item and meets R-inv's bar for transparent instructed
inversion (below the 300-id minimum; FAR polarity-confounded, inversion-polarity subset agrees), so the paper does not call it deception-specific.

## 2. Claims table: pre-registered predictions and rules

Scope abbreviations: sel = selection sample (n = 100, seed 0); held = held-out sample (n = 100, seed 1, selection
ids excluded); paired-I = R-inv option B (I's own held-out ids, D on the same ids, R23); test = D's 1,000-row test
split. Limitations (L1-L25) are listed in section 5.

| # | claim (spec section) | rule | evidence (number; file) | verdict | scope | limitation |
|---|---|---|---|---|---|---|
| H1 | **Headline outcome** (2.1) | R-AB, shared by >= 2 tasks | far A′, ser A′, sdr B; `phase1/p1c_readings.json` (`overall` "A'") | **A′** | held, neutral twin, post-clause | L3, L8, L9 |
| H2 | R-AB far (2.3) | (i) and (ii) at k <= 20 | greedy k = 20: f_D 0.893 [0.860, 0.927], KO acc 0.000, null max 0.309, (ii) H/F acc move 0.31 / 0.33; per-instance f median 0.902, quartiles [0.764, 1.034]; `phase1/rab_curves.csv`, `figures/fig1_mediation.csv` (`f_pi_*`) | **A′** (i) yes, (ii) no | held | L8, L9, L10 |
| H3 | R-AB ser (2.3) | same | greedy k = 20: f_D 0.904 [0.859, 0.951], KO acc 0.050, null max 0.369, (ii) 0.25 / 0.18; per-instance f median 0.907, quartiles [0.742, 1.086]; `phase1/rab_curves.csv`, `figures/fig1_mediation.csv` | **A′** | held | L8, L9, L10 |
| H4 | R-AB sdr (2.3) | same | no k <= 20 passes (i); best greedy k = 20 f_D 0.664, KO acc 0.36; single k = 20 f_D 0.485 [0.440, 0.533] (per-instance median 0.494, `figures/fig1_mediation.csv`), null max 0.434; shared share of the top-80 S2p effect 0.554 (`reports/03-1c-results.md`); curves in `phase1/rab_curves.csv` | **B** | held | L8, L9 |
| H5 | A′ adjudication far (2.3, R11(g)) | category with > 50 % of head weight | kv_clause 0.74 (13 of 18 heads; 10 KV groups); `phase3/a_prime.csv` (shares derived from it), printed as 0.738 in `figures/fig4_a_prime.csv` | **A′-clause-reader** | sel, C_t paths | L11, L12, L13 |
| H6 | A′ adjudication ser (2.3) | same | kv_clause 0.83 (14 of 19 heads; 10 KV groups); same files, printed as 0.835 in `figures/fig4_a_prime.csv` | **A′-clause-reader** | sel, C_t paths | L11, L12, L13 |
| H7 | Routing gate for mover / unresolved (2.3, R11(h)) | share (c) <= 0.25 | (c) far 0.163, sdr 0.297, ser 0.006; `phase1/routing.csv` | far, ser pass; sdr exceeds, but sdr is B, so R14's grid was not run (R29) | held | L12 |
| H8 | R-inv far (2.4, R19(3), R23) | paired CI of f_I - 0.5 f_D above 0 | option B: f_D 0.866, f_I 0.798, diff 0.365 [0.332, 0.393]; inversion-polarity rows (n 83): 0.352 [0.320, 0.385]; R19(3) subset (n 14): 0.414 [0.353, 0.471]; `phase1/rinv.csv` | **instructed inversion machinery**: not called deception-specific (below the 300-id minimum; FAR polarity-confounded, inversion-polarity subset agrees; I pool 210 ids; R30) | paired-I, 10 clusters | L5, L6 |
| H9 | R-inv sdr | same | option B: f_D 0.425, f_I 0.309, diff 0.097 [0.024, 0.155]; inversion-polarity 0.078 [0.002, 0.143]; R19(3) subset 0.049 [-0.018, 0.122]; `phase1/rinv.csv` | no R-inv verdict (sdr is B, so S_20 of the single selector is not a deciding set; spec 2.4, R30); descriptively the option-B CI clears zero and the R19(3) subset's does not | paired-I | L5 |
| H10 | R-inv ser | same | option B: f_D 0.925, f_I 0.679, diff 0.217 [0.165, 0.268]; inversion-polarity 0.221 [0.142, 0.295]; R19(3) 0.236 [0.161, 0.322]; `phase1/rinv.csv` | **instructed inversion machinery**: not called deception-specific (below the 300-id minimum; FAR polarity-confounded, inversion-polarity subset agrees; I pool 249 ids; R30) | paired-I, 13 clusters | L5, L6 |
| H11 | Outcome A, second half: the mechanisms differ in where and how the pressure enters (2.1, decided by RQ-B and RQ-C) | RQ-B and RQ-C predictions | the head-level tests of a difference fail (C-own C1, C-reads C2, C-v1 C3); B-reader holds on all three tasks alike (B2); C-MLP's refutation (C4) is the one pre-registered sign of a difference: mlp.11, mlp.13 and mlp.16 are deception-leaning on ser alone (selection sample, single seed); B-selector predicted a shared route and says nothing about differences; the R-AB first half is not A on any task | **inconclusive** (graded here; no reading graded the roll-up) | all | L1, L2, L14 |
| A1 | Rule R-A1: some set 3-6 is deception-specific or an item carrier (2.5) | R-A1 bands | none on any task; core "answer machinery" on all three; ser D-H (sets 5 = 6) "answer machinery"; the rest "partial or none"; `phase1a/p1a_sets.csv` | no deception-specific set | test, mean / zero | L15 |
| A2 | The core reads as answer machinery on all three tasks (2.5) | R-A1 | D-test KO acc (mean) 0.492 / 0.443 / 0.478, no-pressure rate (zero) 0.495 / 0.440 / 0.487; `phase1a/p1a_sets.csv` | **confirmed** (on far and ser it is a positional collapse: P(KO item_2) 0.80 / 0.72 under mean; `reports/03-1a-results.md`) | test | L15 |
| A3 | The exclusives' no-pressure flips under interchange are an item-injection artifact: zero-ablation no-pressure deceptive rate <= 0.10 (2.5; sdr and ser) | R-A1 no-pressure column | zero: sdr 0.215, ser 0.184 (far 0.001, not in the prediction); `phase1a/p1a_sets.csv` (`np_zero`, set 4) | **refuted** (not graded by the phase-1 reading; graded here from the rule) | test | L15 |
| A4 | >= 2/3 of the core is shared by R-cls (2.5) | R-cls | shared 16/31 far, 25/31 sdr, 18/31 ser; `phase1/p1b_readings.json` (`rqa`) | per task: **confirmed on sdr, refuted on far and ser** (read as applying to every task: refuted) | sel | L21 |
| A5 | The majority of each exclusive set is deception-leaning (2.5) | R-cls | 3/8 far, 0/14 sdr, 1/10 ser; `phase1/p1b_readings.json` | **refuted** | sel | L1, L21 |
| B1 | B-selector (2.6): some L17H24-27 head is Q on >= 2 tasks, AND the core's L24 heads are K/V post-clause movers | path categories | clause 1: all four L17 heads Q on all three tasks; clause 2: core L24 heads are Q or none on every task, no K/V cell into an L24 group above 0.003; `phase3/b_selector.csv`, `phase3/p3_readings.json` | **refuted on its second clause** (R29 wording: "clause 1 confirmed; the L24 heads are fed at the query by L17H24", the second half exploratory and true of the Q-category L24 heads only: L24H26 and L24H27 on every task, plus L24H17 on sdr and L24H20 on ser) | sel, C_t | L11, L13 |
| B2 | B-reader (i): B2-signature heads concentrate in layers 8-17 above 10/32 (2.6) | one-sided binomial, p < 0.05 per task | 32 of 36 (far), 34 of 36 (sdr), 27 of 28 (ser); p 9.5e-13 / 2.0e-15 / 4.5e-13; `phase2/p2_readings.json`, `figures/fig3_b2_by_layer.csv` | **confirmed** on all three | U' heads, 1,000 paired rows | L21 |
| B3 | B-reader (ii): L13H5, L13H20, L13H21 show the signature (2.6) | B2 >= 0.05 and >= 2 SE | L13H20 and L13H21 on all three; L13H5 0.021 (far), 0.063 (sdr), 0.037 (ser); `phase2/p2_readings.json` | **holds on sdr; refuted on far and ser** (L13H5 under the 0.05 floor) | U' heads | L21 |
| B4 | B-lens (2.6), EXPLORATORY (R12) | R-lens | far minus act-naming: -0.022 [-0.053, 0.009] (sdr), 0.001 [-0.089, 0.055] (ser); expected >= 0.2; `phase1/p1b_readings.json` (`lens`) | expected direction not seen (exploratory, decides nothing) | test, 1,000 rows | L7 |
| C1 | C-own (2.7): holds for sdr and ser, fails for far | sign test, Holm | own heads 7/8 far (p 0.035, Holm 0.105), 5/14 sdr, 5/10 ser; `phase1/c_own.csv`, `phase1/p1b_readings.json` | **refuted** (fails on all three; the far half of the prediction held) | sel | L1 |
| C2 | C-reads (2.7): the exclusive sets differ in top-Segment group | Fisher exact, p < 0.05 | p 0.58 on 12 heads with an established read; 20 of 32 exclusive heads read the BOS sink; `phase2/p2_readings.json` (`c_reads`), `figures/fig8_exclusives.csv` | **refuted as tested** (the test has almost no power) | U' heads, D cell | L14 |
| C3 | C-v1 (2.7): >= 3 of L5H8, L5H9, L5H11, L9H12 deception-leaning on sdr_v2 only | R-cls | 0 of 4; `phase1/p1b_readings.json` (`c_v1`) | **refuted** | sel | L19 |
| C4 | C-MLP (2.7): no MLP other than layer 0 is deception-leaning on exactly one task with d(D) >= 0.1; L30, L31 shared | R-cls | mlp.11, mlp.13, mlp.16 deception-leaning on ser alone (d 0.239, 0.203, 0.175); mlp.30 opposes on all three; mlp.31 shared; `phase1/rcls.csv`, `reports/03-1b-results.md` | **refuted** | sel | L16 |
| C5 | C-confound (2.7): does far's deception-leaning D-H reading survive in (D-H)-core? | R-A1 set 6 | deciding (R-A1's columns): set 6 reads "partial or none", D-test KO acc under mean 0.506 (set 5: 0.331). Supporting: interchange 0.191 (set 5) vs 0.476 (set 6); held-out neutral-twin f_D of (D-H)-core 0.105. Counter-evidence: under zero set 6 moves little (0.320 to 0.363) and its no-pressure rate is lower (0.028 vs 0.116); interchange set 6 still separates from its null on 4 of 4 metrics; jointly (D-H)-core costs D by d 0.99 and H/F by about 0. `phase1a/p1a_sets.csv`, `reports/03-1a-results.md`, `phase1/p1c_readings.json` (`named`), `phase2/families.csv` | **does not survive** (phase 1's verdict; fragile): the paper says far's D-H effect was core | test, held | L15 |
| C6 | C-honest (2.7): the late H-D heads write honest on H and F, and under pressure their honest-direction DLA is >= 50 % smaller | DLA, per head | both clauses on 9/12 (far), 5/7 (sdr), 7/8 (ser) heads; 0 heads suppressed, every reduction is a sign flip; `phase2/p2_readings.json` (`c_honest`) | per head: **holds on 9/12, 5/7, 7/8 heads**; every reduction is a **sign flip toward the pressured answer, none a suppression** (R28); 3 heads have no honest-signed twin DLA, so no reduction is defined; the spec's gloss "suppressed, not absent" is refuted | 1,000 paired rows, direct path | L23 |
| D1 | RQ-D seeds (2.8): core Jaccard >= 0.6, exclusives <= 0.4 | ticket 07 | not run: no headline claim rests on exclusive-head identities (R5, R29) | **not tested** | - | L1 |
| P1 | Positive control: the layer-0 MLP is rank 1 as in v1 (2.2, 3) | S1 sweep | d 1.86 / 1.88 / 1.97, KO acc 0.05 / 0.00 / 0.02 (v1 1.89, 0.01); `phase1/p1b_readings.json`, `reports/03-1b-results.md` | **confirmed** | sel | - |
| P2 | Pre-clause Segments read exactly zero (2.9, R16; a sanity assertion) | assertion | max abs drop 0.0 on all three tasks; `phase2/segments.csv` (`pre_clause` = 1 rows) | **pass** | sel | - |
| P3 | Component drift control, H100 vs Delta H200 (ticket 02a) | max abs delta <= 0.05, Spearman >= 0.99 | max abs delta 0.0, Spearman 1.0, flagged set identical; `reports/02a-drift.json` | **pass** (bit-identical) | v1 sweep, n = 100 | L20 |

## 3. Descriptive and exploratory readings

None of these decides anything. Each names the reading that made it.

| # | reading | evidence (file) | status |
|---|---|---|---|
| E1 | Deciding-set members outside the six circuits' head union U: far 15 of 20, ser 12 of 20, sdr 9 of 20, counting MLPs as outside. Every MLP is kept in every heads-only circuit, so counting heads only: far 13 of 18, ser 11 of 19, sdr 3 of 14 (derived from the member tables). The far and ser mediators lie mostly outside the circuits; sdr's S_20 does not | `reports/03-phase1-reading.md` (far, ser), the deciding-set member tables of `reports/03-1c-results.md` (sdr) | descriptive |
| E2 | U-only arm (R24): the circuits' best heads never pass (i); k = 20 f_D 0.405 / 0.407 / 0.520 against the unrestricted single 0.545 / 0.485 / 0.663 | `reports/03-1c-results.md` | descriptive |
| E3 | Named groups on held-out D under the neutral twin: core f_D 0.165 / 0.322 / 0.257; excl 0.028 / -0.036 / 0.057; (D-H)-core 0.105 / 0.014 / 0.046 | `phase1/p1c_readings.json` (`named`) | descriptive |
| E4 | S7 (I) vs S2p (D): inversion-shared Components among the S2p top 20: 20 (far), 18 (sdr), 16 (ser) | `phase1/s7_vs_s2p.csv`, `phase1/p1c_readings.json` (`s7`) | descriptive |
| E5 | C1: the core and the MLPs act alike on all nine item-swap sets (core mean d 0.15-0.18); the MLPs dominate the neutral twin on D (far 0.71) | `phase1/c1_matrix.csv`, `figures/fig7_c1_matrix.csv` | descriptive |
| E6 | Family knockouts (item swap, joint): the core costs H and F about as much as D (d 1.82-2.04 on all nine cells); far's exclusives help the honest answer on H and F (d -0.25); far's (D-H)-core costs D only (0.99) | `phase2/families.csv` | descriptive; the family R-cls bands are exploratory (phase 2; not the rule of record) |
| E7 | Segment-resolved twin knockout of the S2p top 20: on far and ser the clause-position effect sits in MLPs 5-8 (and 11) and L7-11 heads, carried to the Readout by mlp.13, L14H4, L14H5; on sdr the Readout carries most of it (joint Readout 6.5 vs clause 3.2) | `phase2/segments.csv`, `reports/04-phase2-reading.md` section 2 | descriptive |
| E8 | Clause attention mass at the Readout peaks at layer 13 on every task (0.155-0.160 over U' heads) | `reports/04-phase2-results.json` (`clause_mass_by_layer`) | descriptive (spec 2.9) |
| E9 | I cells: the deciding-set heads read the same top Segment on I as on D (17/18, 13/14, 19/19) and, of the heads with the B2 signature on D, almost all keep it on I (15/16, 8/9, 6/6) | `reports/04-phase2-reading.md` section 4 | descriptive Segment overlap; the B2-on-I overlap is exploratory (phase 2); consistent with R-inv, which is the claim of record |
| E10 | B4, where the pressure arrives on C_t: post-clause share of K/V weight 0.17 (far), 0.44 (sdr), 0.21 (ser); the placement of template-token arrivals as post-clause is exploratory | `phase3/entry_paths.csv`, `figures/fig5_entry_paths.csv` | descriptive / exploratory |
| E11 | Shared downstream route: L14H4 (far, sdr) or L15H8 (ser) gives L17H24 its strongest query input; L17H24 feeds the L24 queries (B-selector's second half as worded in R29) | `phase3/b_selector.csv`, `figures/fig6_route.csv` | **exploratory** |
| E12 | sdr's route is "query-heavy, with post-clause value reads": Q-dominated 0.64 at the 0.01 floor, mixed (q 0.38) at 0.02; routing (c) 0.297 | `phase3/a_prime.csv`, `reports/05-phase3-reading.md` | **exploratory** (sdr is B) |
| E13 | Robustness re-readings of the A′ call: far kv_clause 0.70 (positive paths only), 0.58 (floor 0.02); ser 0.69, 0.77 | `reports/05-phase3-results.md` | exploratory |
| E14 | Completeness: about four fifths of the twin gap reaches the Readout on direct writes from outside C_t (signed 0.80 / 0.81 / 0.77; mlp.31, mlp.30, L31H0); that C_t acts through them is an inference | `phase3/completeness.csv` | exploratory |
| E15 | Roles over C_t (R25 rule 4b with path data): pressure readers 16 / 4 / 5, all kv_clause; L17H24 a selector on all three tasks; L13H21 and L13H23 pressure readers on all three | `phase3/roles_by_part.csv`, `phase3/roles_cross_task.csv` | role counts descriptive; the cross-task role comparison is exploratory (phase 3 section 5) |
| E16 | Layer of emergence (spec 2.9): the mean lens margin on D keeps its final, positive sign from layer 15 (far), 13 (sdr), 7 (ser; the margin stays near 0 until layer 16); D minus twin from 13 / 10 / 14. The D mean first exceeds +0.5, and the twin's first falls below -0.5, at layer 17 on all three (derived) | `figures/fig9_lens.csv` (`sign_flip_layer`, `mean`) | descriptive, raw lens |
| E17 | Honest-first rates 0.93 / 0.91 / 0.85: almost every pressured instance passes through a lens margin below -0.5 before turning deceptive. There is no null for this rate: the twin rate is 0 by construction, and the mean D margin sits near 0 at layers 8-16, so per-instance lens noise could produce much of it | `phase1/p1b_readings.json` (`lens`) | exploratory (R12) |
| E18 | R22 finding: a reported third-party wish ("the buyer wants the wrong result") keeps FAR 0 / SDR 618 / SER 7 of 1,000 ids; only SDR's disclosure choice follows it | `inversion-control.md` | finding of ticket 08, not a section-2 prediction |
| E19 | C-reads' exploratory expectation (spec 2.7: sdr's early exclusives read designation or Item Mentions, ser's later ones the clause or the Designation Suffix) is not seen: with the sink left out, every exclusive set reads the frame most (far 6/8, sdr 11/14, ser 7/10; Fisher p 0.15) | `reports/04-phase2-reading.md` section 5 | exploratory |

## 4. Results narrative (for the paper)

**Setting.** Llama-3.1-8B-Instruct answers a two-item question after an operator rule (the Pressure Clause) tells it
to name the item that is not supported by the record. Three Deception Mechanisms share the scaffold: Fabrication (far),
Omission (sdr) and Pragmatic Distortion (ser). Each pressured prompt D has a Neutral-Clause Twin H that keeps every
token except the clause, so a knockout that patches D's activations with H's at the positions after the clause isolates
what the clause changes. A third condition I keeps D's instance and target item but makes the inversion transparent:
the assistant is told, inside an explicit quiz or game frame, to name the other item, and nobody is misled.

**What the six coarse circuits capture, and what they miss.** The coarse heads-only circuits were pruned under
item-swap interchange. Their shared 31-head core is answer machinery: knocking it out leaves deceptive accuracy near
0.5 on every task (A2), and on far and ser the flips are a collapse to one answer position, not a swap of content. Its
joint knockout costs the honest answer on H and F about as much as the deceptive one on D (E6, descriptive). Some core
heads do read or route the pressure: L13H20 and L13H21 carry the B2 pressure-reader signature on every task (B3), and
L17H24-27 take the pressure at their queries on every task (B1). The exclusive heads of each circuit (8 / 14 / 10) are
mostly not deception-leaning (A5) and not significantly owned by their task (C1); the test of what they read (C2) is
uninformative, because most of them attend to the BOS sink. On far and ser the strongest pressure mediators lie mostly
outside the circuits (E1, descriptive; on sdr the S_20 heads are mostly inside), and the circuits' own best heads never
reach the mediation bar (E2, descriptive). The pruned circuits' core behaves as answer machinery, and on far and ser
the strongest pressure mediators sit mostly elsewhere.

**A small clause-reading set mediates the pressure on far and ser.** Ranked by their post-clause neutral-twin effect
and grown greedily, 20 Components remove about 90 % of the clean-minus-twin gap on a held-out sample (far 0.893, ser
0.904) and drive deceptive accuracy to 0.00 and 0.05; 20 random layer-matched sets reach at most 0.309 and 0.369
(H2, H3; Figure 1). The per-instance ratios agree with the ratio of means (medians 0.902 and 0.907). On the selection
sample, path patching places the strongest neutral-twin input of most of these heads in their keys and values over the
clause span (H5, H6; Figure 4). The senders are early MLPs (far mlp.6, 8, 9; ser mlp.5, 6, 7, 11), so the heads at
layers 7-14 read a clause representation the MLPs wrote. That is where the pressure signal enters on these two tasks
(A′-clause-reader). Across the analysed heads, those with the B2 attention signature (under pressure the Readout query
attends to the clause, under the twin it does not) concentrate in layers 8-17 on every task (B2; Figure 3). Within the
deciding sets, 16 of 18 far heads carry the signature, but only 6 of 19 ser heads; 9 of 14 heads of sdr's descriptive S_20 do (`reports/04-phase2-reading.md`
section 4).

**But the set also carries the item, and it is not called deception-specific.** Knocking the far and ser sets out
with item swaps also flips 18-33 % of the honest answers on H and F (test (ii) fails), so the reading is A′, not A.
Test (ii) and R-inv apply to the whole set, its MLPs included, so which members carry the item is not tested. On the
transparent inversion condition the same sets mediate f_I 0.798 (far) and 0.679 (ser) of I's gap, against f_D 0.866
and 0.925 on the same ids. f_I clears half of f_D with clustered CIs above zero (H8, H10; Figure 2), which is R-inv's
bar for "instructed inversion machinery"; on ser f_I is still clearly below f_D. Descriptively, 20, 18 and 16 of the
S2p top 20 are inversion-shared, with d(I) / d(D) in [0.5, 2] (E4). By spec 2.4 the paper therefore does not call
these sets deception-specific. Two caveats bound this: R-inv speaks only for instances whose transparent inversion the
model follows (L5), and both readings are below the 300-id minimum; FAR polarity-confounded, inversion-polarity subset agrees (L6).

**sdr reads B; its route contrast is descriptive.** On Omission no set of 20 or fewer Components mediates the pressure
(H4, reading B): the best reaches f_D 0.664, and more than half of the summed post-clause effect sits in Components
R-cls calls shared. On the path grid sdr's single-selector set is query-heavy, with post-clause value reads (E12):
L14H4, L14H5, L14H20 and L17H24 take the pressure at their queries, sdr's clause-span K/V weight is about 0.28 of
far's, and 44 % of what sdr carries through keys and values arrives after the clause (E10; Figure 5). Because sdr is
read B, because the shape becomes mixed at a 0.02 floor, and because 0.297 of sdr's post-clause pressure routes outside
the grid, this contrast is exploratory. Of the pre-registered tests for a difference between mechanisms, the head-level
ones fail (C-own, C-v1) or are uninformative (C-reads). The one pre-registered sign of a difference is C-MLP's
refutation: mlp.11, mlp.13 and mlp.16 are deception-leaning on ser alone (selection sample, single seed). Outcome A's
second half is therefore inconclusive (H11).

**A shared downstream route.** On every task L17H24-27 take the pressure at their queries (B-selector, clause 1).
B-selector's second clause fails: the core's L24 heads are not post-clause movers. The Q-category ones (L24H26 and
L24H27 on every task) are fed at the query by L17H24, which in turn takes its strongest query input from L14H4 (far,
sdr) or L15H8 (ser) (E11; Figure 6; exploratory). Most of the
final write at the Readout comes from late Components outside the grid (mlp.31, mlp.30, L31H0; E14).

**Honest writers flip.** Most late H-D heads (far L22 and L30, sdr and ser L18 and L30) write toward the honest
answer on H and F. Under pressure their direct effect does not merely shrink: on every head where it is reduced, it
flips sign and writes toward the pressured answer (C6; honest writes of at most 0.26 logits, flipped writes of at most 0.18).

**The lens.** On D the raw lens margin stays near zero through the middle layers and first passes +0.5 at layer 17 on
all three tasks, the layer at which the twin's margin first passes -0.5 (derived from `figures/fig9_lens.csv`; Figure
9). Most pressured instances dip below -0.5 at some mid layer before turning deceptive (E17), but that rate has no null
and may be lens noise around a near-zero mean; FAR shows no more of it than the act-naming subsets of SDR and SER (B4).
The raw lens is uncalibrated, so all of this is exploratory.

## 5. Limitations

**Thresholds (R17).** Only R-A1's bands (calibrated on one v1 cell, the far fine delta leaf) and R-cls's factor of two
(from the v1 SDR D&H-core analysis) are calibrated against data, and every other threshold (R-AB's 0.75, 0.25, 0.10
and 25 %, R-inv's 0.5, the B2 floor 0.05, the 0.01 path floor, R-lens's -0.5, R-own's sign test, R14's 0.25) is a
convention with no measurement behind it.

Spec section 7 item numbers are given as §7.n.

- **L1. Single seed** (§7.1). Ticket 07 did not run (R5, R29). The head identities of small sets (exclusives, D-H,
  the deciding sets) are unreplicated. No headline claim rests on them.
- **L2. Unpaired cross-mechanism comparison; few clauses** (§7.2, §7.8, R8). The Comparison Set has 8 test
  instances, so the three tasks are compared between groups, matched only on the stratification marginals and on
  overlapping item pairs; their clauses differ. 12 / 20 / 17 test clauses with 1 to 150 rows each; the effective n
  for between-task contrasts is clauses, not instances.
- **L3. Interchange-pruned circuits** (§7.3). The circuits are biased toward answer-carrying heads, and on far and ser
  the strongest pressure mediators lie mostly outside them (E1, E2, descriptive). Statements about "the circuits" do not
  transfer to the model's mediators.
- **L4. Instructed deception; the twin flips the answer too** (§7.4, §7.9). Every clause is a rule-instructed operator
  rule. The neutral-twin knockout conflates "pressure removed" with "honest answer written"; post-clause ranking
  without the Readout reduces this, it does not remove it.
- **L5. R-inv survivorship and wording** (§7.5, R22, R23). Both R-inv samples condition on survival of I's behaviour
  filter (target argmax and margin >= 0.7 in both streams), so R-inv speaks for the instances whose transparent
  inversion the model follows. I's clauses carry a game frame where D's carry a motive or rule, so the pair differs
  in frame as well as in whether anyone is misled.
- **L6. FAR and SER I below the 300-id minimum; FAR polarity confound** (R22, R23). I keeps 210 FAR and 249 SER ids
  (SDR 788; `inversion-control.md`). R22 said a task below the 300-id minimum "has no I contrast"; R23 drew the paired
  R-inv sample from those same pools, and R30 rules that R23 and the phase-1 instruction ("a task failing it runs as a
  stated limitation, not dropped") supersede that sentence of R22. The far and ser R-inv readings therefore stand, each
  qualified as below the 300-id minimum; FAR polarity-confounded, inversion-polarity subset agrees. 191 of FAR's 210 kept rows have Designation Polarity inversion, so FAR's option-B sample is
  polarity-confounded (83 inversion, 17 identity); its inversion-polarity row compares like with like and agrees. FAR's
  bootstrap has 10 pressure_id clusters.
- **L7. Wording confound and the raw lens** (§7.6, §7.7, §7.15). FAR's clauses are all act-naming, so FAR has no
  Predicate-naming subset, and its question and stem name the Predicate. Act-naming clauses cover 72 of SER's 1,000
  rows and 216 of SDR's (`phase1/p1b_readings.json`, `lens`). The lens is raw and uncalibrated. The lens figure's band is the per-instance SE, not clustered by
  pressure_id: the fetched cells keep no per-instance trajectory.
- **L8. Selection, test and multiplicity** (§7.10). The held-out sample shares clauses with the selection
  sample. Two selectors at six k values give each task several chances at A; the null controls each test, not the
  family. Greedy passes (i) only at k = 20 on far and ser (greedy k = 10: far f_D 0.676, ser 0.746; `phase1/rab_curves.csv`).
- **L9. Degenerate MLP nulls** (`reports/03-review.md`). An MLP's layer-matched null is the MLP itself (one block per
  layer), so an all-MLP candidate (sdr k = 1, 2) equals its own null and cannot pass (i); mixed sets get a partly fixed
  null. No reading depends on those k.
- **L10. Test (ii) uses absolute moves.** A margin rise above 25 % also fails (ii). k = 40 and 80 have no (ii) by design.
- **L11. Path patching ran on the selection sample.** The A′ adjudication and B-selector describe the deciding sets on
  the sample that chose them. The generalisation claim is R-AB's held-out verdict.
- **L12. Path patching freezes every non-grid Component** (§7.12). Path claims are relative to C_t. Routing share (c)
  is 0.163 (far), 0.006 (ser) and 0.297 (sdr); sdr exceeds R14's 0.25, and the 32-MLP grid was not run because sdr is B
  (R29), so every sdr route statement is descriptive. At the Readout itself about 0.8 of the twin gap arrives on direct
  writes from outside C_t (E14).
- **L13. Floor and KV-group dependence** (§7.13). sdr's Q shape becomes mixed at a 0.02 floor. Heads of one KV group
  share K/V cells: far's 13 and ser's 14 clause-reading heads are 10 independent groups each, and L17H24-27's K/V
  category is one test.
- **L14. C-reads is dominated by the attention sink.** 20 of 32 exclusive heads put their top mass on BOS; the Fisher
  test runs on 12 heads, all but one "frame". Its failure says little either way.
- **L15. Mean ablation and positional collapse** (§7.14). Mean ablation is position-pooled and broadcast to every
  position, BOS included. Its task bank is built from pressure prompts, so on no-pressure rows it can inject the
  pressure; that is why R13 decides R-A1's no-pressure column under zero ablation. The core's "answer machinery"
  reading is a collapse to one answer position on far and ser.
- **L16. Heads-only circuits** (§7.17). MLP claims rest on the sweeps; C_t holds at most 10 MLP blocks.
- **L17. Construction-defined purity; incomplete contingency** (§7.16, §7.18). LLM judges did not separate SDR from
  SER; D alone names the deceptive item on 20-53 % of no-pressure rows.
- **L18. Scale** (§7.19). One model, a one-token Readout, 1,000 test instances per task, causal views on
  100-instance samples: about 12 instances per stratum, with balanced allocation, so sample rates are not split rates.
- **L19. v1 to v2 counterfactual change** (§7.20, R1). v2 reads pressure against the Neutral-Clause Twin; v1 read it
  against an honesty instruction, so v1 and v2 roles are not directly comparable. C-v1's failure may partly reflect
  this change.
- **L20. Cross-GPU numerics** (§7.21). Every mechanism-analysis job ran on Bridges-2 H100. The component drift control
  against the Delta H200 cell of record is bit-identical (P3). The evaluator drift control (Bridges-2 H100 against Delta
  A40, commit c8021ea, mechanism-datasets) was accepted.
- **L21. Multiple comparisons; head-level tests** (§7.22). Only the pre-registered rules decide. B-reader, C-reads and
  R-cls are head-level tests, not clustered by pressure_id.
- **L22. I stand-ins are smaller than D** (`reports/04-phase2-reading.md`): far 210, sdr 788, ser 249 rows.
- **L23. Roles and direct effects.** Phase 2 could assign only "pressure reader"; after phase 3 most C_t Components are
  still "unknown". C-honest is a direct-path DLA reading: honest writes of at most 0.26 logits, flipped writes of at most 0.18.
- **L24. Redundancy and self-repair** (§7.11). Single-Component ranking misses redundant sets and self-repair; the
  greedy selector over the S2p top 50 is a partial remedy. The steep greedy curves (far f_D 0.676 at k = 10, 0.893 at
  k = 20) are consistent with redundancy among the mediators.
- **L25. Per-instance spread.** The deciding sets' per-instance f varies widely around the ratio of means (far quartiles
  0.764-1.034, ser 0.742-1.086; `figures/fig1_mediation.csv`); test (i) is a ratio of means as pre-registered.

## 6. Follow-ups (costed, not started)

Bridges-2 is expected offline about 2026-11-09; 14.5 of the 35 H100 GPU-h cap remain (`compute-ledger.json`).

| follow-up | why | cost |
|---|---|---|
| Path patching of the far and ser deciding sets on the held-out sample (twin line only) | turns the A′-clause-reader call (L11) into a held-out result | at most about 5.25 H100 GPU-h (phase 3 charged 2.5 far and 2.75 ser with both counterfactuals); a twin-only line costs less |
| Rebuild I for FAR and SER above 300 ids (more directive clauses per D clause) and rerun the paired R-inv lines | closes L6 | about 0.25-0.5 GPU-h scoring (ticket 08 ran 0.21 per pool) + about 0.5 GPU-h for the R-inv lines |
| Per-instance lens trajectories in the DLA cells | clustered CIs for Figure 9 and R-lens (L7) | a code change in `component_analysis/dla.py` + about 0.25 GPU-h per task (estimate: spec section 4 costs the 1B lens cell at about 6 min, plus about 8-10 min of model load) |
| Ticket 07, seed replication (Delta H200) | L1; exclusive identities | 6.0 Delta GPU-h reserve, 3.9 expected (spec section 4) |
| sdr 32-MLP path grid (R14) | sdr's route outside C_t (L12) | about +2.75 H100 GPU-h reserve; needs the user's cap approval |
| `receiver_category` coverage-id fix (02b S4, 05 review standards #7) | the CLI's instance list can disagree with the head table when the gap excludes instances (0 affected so far) | CPU |
| Related-work positioning (Campbell et al. 2023; Halawi et al. 2023/2024; the 2025 "Universal Motif" paper) by a paper-reading agent | the ticket asks for it; not done here because each claim needs a confirmed reading first | CPU, no GPU |

## 7. Records

### Figures

`figures/figures.py` extracts one CSV per figure from the sources named in `figures/figures_meta.json` and draws each PNG
from its CSV alone (`python figures.py --render`). Tests: `tests/test_mechanism_analysis_figures.py`.

| figure | shows | status |
|---|---|---|
| `fig1_mediation.png` | R-AB mediation curves, both selectors, 20-draw null band, bootstrap CIs, f_I of the deciding set | pre-registered |
| `fig2_rinv.png` | R-inv paired contrast, three id sets per task | pre-registered |
| `fig3_b2_by_layer.png` | B2 pressure-reader signature by layer per task | pre-registered (B-reader) |
| `fig4_a_prime.png` | A′ receiver-category shares | pre-registered (far, ser); descriptive (sdr) |
| `fig5_entry_paths.png` | where the neutral-twin pressure arrives on C_t | descriptive |
| `fig6_route.png` | the 25 strongest neutral-twin paths per task | exploratory |
| `fig7_c1_matrix.png` | cross-task knockout matrix by composition group (rebuilt here from `phase1/c1_matrix.csv`; the per-Component `phase1/c1_matrix.png` of ticket 03 stays) | descriptive |
| `fig8_exclusives.png` | the exclusives' layer bands and reads | C-reads (refuted); bands descriptive |
| `fig9_lens.png` | raw logit lens, D vs its paired twin | exploratory |

### Jobs and GPU-hours

All on Bridges-2 GPU-shared, one H100-80 per job; no Delta GPU use. Booked = reservations reconciled to sacct elapsed,
rounded up to 0.25 h; actual = sacct (`compute-ledger.json`, section `bridges2`).

| ticket | job ids | booked GPU-h | actual GPU-h |
|---|---|---|---|
| 01 | none (login dry-runs only) | 0 | 0 |
| 02a | 49824729 | 0.5 | 0.398 |
| 02b | 49841165 | 0.5 | 0.354 |
| 08 | 49824662, 49825105 | 0.5 | 0.422 |
| 03 (phase 1) | 49824695, 49824696, 49824697 (1A); 49825315, 49825317, 49825318 (1B); 49828172 (1C-a); 49830654 (1C-b) | 9.5 | 8.510 |
| 04 (phase 2) | 49876003, 49876005, 49876008 | 2.25 | 1.830 |
| 05 (phase 3) | 49896838, 49896843, 49896848 | 7.25 | 6.801 |
| 06 | none | 0 | 0 |
| **total** | 18 jobs | **20.5 (41 SU of the 70 SU cap)** | 18.31 (derived) |

### Commits by phase (branch `mechanism-analysis`, base c24b5d9 = main)

| phase | commits |
|---|---|
| phase 0 (tickets 01, 02a, 08) | fc9e614, d0a30c8, 2ab5a29, 7f8dc01, 45e3340, c2d47da |
| phase 0 (ticket 02b, R25, R27) | 925417c, d134ea4, 83599b5 |
| phase 1 (ticket 03) | 701e0b3, 8bf0109, a4dd35f, 57a43aa, ddd1da4, a13c6bd, 5e266a7 |
| phase 2 (ticket 04) | a9545ed, a0fae76, b3553b0 |
| phase 3 (ticket 05) | a8a9b63, 21f6e76 |
| synthesis (ticket 06) | this ticket's commit |

### Analysis cells to move before the worktree is removed (R6, R16)

Git-ignored under `outputs/_analyses/` in the worktree; move each to the main checkout's `outputs/_analyses/`:
`mechanism-analysis-02a-drift-kosweep`, `-02a-smoke-clause`, `-02a-smoke-dla`, `-02a-smoke-groups`, `-02a-smoke-mean`,
`-02a-smoke-readout`, `-02a-smoke-s2p`, `-02a-smoke-timings`, `-02a-smoke-zero`, `-02b-smoke-timings`,
`-02b-smoke-twin`, `-p1` (227 MB), `-p2` (345 MB), `-p3` (40 MB).

Also untracked and not ignored, so lost with the worktree unless moved or committed: `outputs/_suites/mechanism-analysis/`
(62 MB, the phase-1A evaluator cells that `phase1a/p1a_cells.csv` names), `outputs/_suites/mechanism-v2-coarse.b2local-261025/`
(66 MB) and `outputs/_launch_mechanism_analysis/eval_jobs.txt`.
