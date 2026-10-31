# Mechanism analysis: what the coarse v2 deception circuits compute, and how FAR / SDR / SER differ

Status: approved (2026-10-25; review-00 approve on re-check; rulings R0-R19; tickets 01 and 02a running)
Repo: Deception-Circuit (`DC` = `/projects/beto/swong2/Alignment/Deception-Circuit`, main at c24b5d9)
Worktree: `DC/.claude/worktrees/mechanism-analysis`, branch `mechanism-analysis` off main (created 2026-10-25;
orchestrator-only git; the branch may be pushed to origin, R3).
Inputs: the six coarse heads-only v2 circuits of mechanism-datasets ticket 05 (NLS 0.3, seed 42,
Llama-3.1-8B-Instruct) and the 65 evaluation cells of its ticket 06. Ground truth for every fact below:
`reports/00-plan-handback.md` (cited as "HB (x)"), `reports/00-plan-review.md` (cited as "review"), and
mechanism-datasets `reports/06-evaluation-reading.md` (cited as "06"). Rulings are in §9 and cited as R0-R17.

## 1. Intent and why

Find publishable, top-venue interpretability results on two questions:

1. how deception under an operator rule works at the circuit level in this model, in general;
2. how the three Deception Mechanisms (FAR Fabrication, SDR Omission, SER Pragmatic Distortion) differ.

Why now. Ticket 06 showed the coarse heads-only circuits are faithful and necessary but **mostly shared answer
machinery**: a 31-head D core in all three D circuits removes deception on every task and also inverts the
honest no-pressure answers. Mechanism-specific heads exist but are small and partial (exclusives 8 / 14 / 10).
Every one of those readings rests on interchange ablation, under which an answer-carrying head shows up as an
item inversion. Circuit membership alone cannot say what the heads compute. This feature asks, with
Component-level evidence (reads, writes, depends; `docs/component-roles.md`), what the core computes, where the
Pressure Clause enters, and what the mechanism-specific heads do.

## 2. Research questions and pre-registered predictions

**Status of the numbers (R0, R17).** Every threshold below is pre-registered as written; numbers at other
thresholds are reported as exploratory and never decide a reading. Two are calibrated against data: R-A1's bands
(on one v1 cell, the far fine delta leaf) and R-cls's factor of two (from the v1 SDR D&H-core analysis). Every
other number in this section is a convention with no measurement behind it, and the paper says so in one sentence.

### 2.1 The headline outcomes

- **Outcome A.** Deception-specific computation is a small set of pressure mediators on top of shared answer
  selection, and the mechanisms differ in where and how the pressure enters.
- **Outcome B.** No set of 20 or fewer Components, chosen by single-Component or greedy neutral-twin effect,
  mediates the pressure; the neutral-twin effect is spread over Components that R-cls calls shared (that share is
  reported).
- Between them sits **A′**: a small set mediates the pressure but also carries the item.

Outcome A has two halves. Its first half (a small separable set exists) is decided by rule R-AB below. Its second
half (the mechanisms differ in where and how the pressure enters) is decided by RQ-B and RQ-C (B-selector,
B-reader, C-own, C-reads), not by R-AB.

### 2.2 Shared notation and rule R-cls

Test sets per task t: D = `<t>_v2`, H = `<t>_v2_honest` (the Neutral-Clause Twin), F = `<t>_v2_nopressure`,
I = `<t>_v2_inversion` (the instructed-inversion control condition, ticket 08, R15).

Samples (R11(b)). The **selection sample** is the stratified balanced causal sample, n = 100, seed 0 (as in v1).
The **held-out sample** is drawn the same way with seed 1, the selection sample's ids excluded. On H, F and I the
same seeds and exclusion apply; where a set shares D's instance ids, the same ids are used.

Positions. **Post-clause** = every token after the end of the `pressure_clause` Segment, the Readout excluded
(the range form of `--knockout-positions`, e.g. `after=pressure_clause,exclude=readout`). Every position before the
clause has bit-identical activations in D and its twin (causal attention; review §0), so a neutral-twin knockout
there is exactly zero.

Effects. For a Component c and a test set X, `d_c(X)` = knockout drop / X's clean margin, signed, each in X's own
target direction: deceptive on D and I, honest on H and F. A positive `d` on H or F means "supports the honest
answer". Significance uses `docs/component-roles.md`'s rule: |drop| >= 2 SE and >= 0.01 logits.

**Rule R-cls** (amended per R16; classified on signed `d` from the item-swap sweeps S1, S5, S6 of §4). Let
`m_HF = max(max(d(H), 0), max(d(F), 0))` (negative values floored at 0, a convention) and
`U_HF = max over X in {H, F} of max(d(X) + 1.96 SE(d(X)), 0)`. Checked in this order:

1. **opposes**: d(D) significantly negative. Its H and F significance is reported as a column.
2. **shared**: d(D) significantly positive, H or F significantly positive, and d(D) / m_HF in [0.5, 2].
3. **deception-leaning**: d(D) significantly positive and d(D) >= 2 U_HF.
4. **honest-leaning**: H or F significantly positive and m_HF >= 2 d(D).
5. **none**: otherwise (the sub-reason is reported).

### 2.3 Rule R-AB: is there a small set of pressure mediators? (amended per R11)

**Ranking (selection sample).** Sweep S2p of §4: per Component, the neutral-twin knockout drop on D at
post-clause positions. The layer-0 MLP is excluded (it is the Positive Control and acts as a second embedding;
`CONTEXT.md`). The all-positions neutral-twin sweep S2 is descriptive only.

**Two selectors** build the candidate sets `S_k`:

- **single**: the top k of the S2p ranking, k in {1, 2, 3, 5, 10, 20, 40, 80};
- **greedy**: from the top 50 of the S2p ranking, start from the empty set and at each step add the Component whose
  addition gives the largest joint post-clause neutral-twin drop on the selection sample, up to k = 20 (grid points
  1, 2, 3, 5, 10, 20). k = 40 and 80 come from the single selector only.

**Tests (held-out sample)**, for each selector and each k:

- **(i) Pressure mediation.** The joint neutral-twin knockout of `S_k` at post-clause positions on D gives
  two-way deceptive accuracy <= 0.25, and the mediated fraction
  `f_D = (mean clean margin - mean KO margin) / (mean clean margin - mean twin margin)` >= 0.75. `f_D` is a ratio
  of means; per-instance ratios are reported. The gap is at least 1.0 logit by construction (D margin >= 0.7,
  twin honest margin >= 0.3). (i) also requires `f_D` to exceed all 20 draws of the null at that k.
- **Null.** 20 random k-sets drawn from the 1,055 Components (layer-0 MLP excluded), layer-matched (the same number
  of heads and MLPs per layer as `S_k`), knocked out the same way on the same held-out sample.
- **CIs.** Per-instance bootstrap (2,000 resamples) 95% CIs on both (i) numbers, for `S_k` and for the null mean.
- **(ii) Not answer-carrying.** The item-swap knockout of `S_k` at all positions, on the H and F held-out samples,
  moves honest two-way accuracy by <= 0.10 and the honest margin by <= 25% of its clean value, on both.

**Readings, per task, checked in this order:**

- **A, separable pressure mediators.** Some k <= 20, with either selector, meets (i) and (ii).
- **A′, pressure mediators that also carry the item.** No k <= 20 meets both, but some k <= 20 meets (i).
- **B, no small mediating set.** No k <= 20 meets (i) with either selector. Reported with the share of the summed
  positive S2p effect over the top 80 that is held by Components R-cls calls shared.

The **deciding set** is the smallest `S_k` that meets the reading's criteria (on a tie, the single selector's).
The minimal k and the mediation curve (k vs `f_D`, with the null) are reported per selector. The paper's headline is
the reading shared by >= 2 of the 3 tasks; if all three differ, it is "mixed", named per task.

**Routing check (phase 1C, R11(h)).** Per task, on the held-out sample, joint neutral-twin knockouts at
post-clause positions of: (a) all 32 MLP blocks; (b) all heads outside the preliminary `C_t` (§4, phase 1C);
(c) every Component outside `C_t`. Each is reported as a share of the clean-minus-twin gap.

**A′ adjudication (phase 3, R11(g)).** For each head in the deciding `S_k` (MLP members excluded from the call and
counted), the strongest neutral-twin incoming path above the 0.01 floor falls in exactly one category:

| category | meaning |
| --- | --- |
| Q | the pressure arrives at the head's query: selector |
| K/V from the clause span | the head reads the clause directly |
| K/V from post-clause positions (item mentions, question, response line, stem, Readout) | the head reads items whose representation the pressure already changed: mover |
| none above the floor | unresolved |

The call is the category holding > 50% of the deciding set's head weight, the weight being each head's S2p single
effect; otherwise "A′-mixed". The sub-readings are **A′-selector**, **A′-clause-reader**, **A′-mover**,
**A′-unresolved** and **A′-mixed**. A′-selector and A′-clause-reader are positive mechanism results: the lie signal
enters at these heads. Any sub-reading that rests on where or whether grid paths arrive (A′-mover, A′-unresolved) is
claimed only if routing share (c) is <= 0.25, because path patching freezes every non-grid Component (review §0).
Otherwise the reading is "A′, route outside `C_t`", and R14 applies.

### 2.4 Rule R-inv: deception or instructed inversion? (R15)

The neutral-twin contrast removes an operator rule that says "name the other one". A set that mediates it may be
generic instructed-inversion machinery. I = `<t>_v2_inversion` keeps the instance and the target item but makes the
inversion transparent (ticket 08). Per task, after R-AB: the deciding `S_k` (for B, `S_20` of the single selector,
descriptive) is knocked out jointly with the neutral twin at post-clause positions on I's held-out sample, giving
`f_I` (the fraction of I's clean-minus-twin gap, ratio of means).

- `f_I >= 0.5 f_D`: **instructed-inversion mediators**. The paper does not call the set deception-specific.
- `f_I < 0.5 f_D` and the two 95% CIs do not overlap: **deception-leaning mediators**.
- otherwise: undetermined.

Per Component, sweep S7 (I, neutral twin, post-clause) is compared with S2p, descriptively: "inversion-shared" if
both are significant and d(I) / d(D) is in [0.5, 2].

### 2.5 RQ-A. What does the shared core compute: the answer, or the deception?

Measurements:

- **A1. Circuit-level mean and zero knockouts** (`evaluate_circuit.py --ablation mean|zero --evals knockout`,
  1,000 items, 20-set KO null). Sets per task: 1 D_t, 2 H_t on D's test set, 3 core, 4 excl_t, 5 D_t - H_t,
  6 (D_t - H_t) - core, 7 D_t & H_t.
- **A2. Mask-independent sweeps** (`analyze_components.py`, knockout completeness sweep, 1,056 Components,
  selection sample) on D, H and F under item-swap, on D also under neutral twin and mean (§4: S1, S2, S2p, S3, S4, S5, S6).

**Rule R-A1** (amended per R13), per set and task, for sets 3-6. Accuracy counts the deceptive item. The D-test
column is read under mean ablation (task bank: D's test split). The no-pressure column is **decided under zero
ablation**. Mean ablation of the no-pressure rows uses a variant-matched bank collected on `<t>_v2_nopressure`
(ticket 01) and is reported as robustness. Sets 1, 2 and 7 get the mean D-test column only, as calibration rows,
with no R-A1 reading.

| reading | D-test KO accuracy (mean) | no_pressure KO deceptive rate (zero) |
| --- | --- | --- |
| answer machinery (the answer is lost, not swapped) | 0.25-0.75 | >= 0.25 |
| deception-specific | <= 0.25 | <= 0.10 |
| item carrier (the ablation value itself carries an item) | <= 0.25 | >= 0.75 |
| partial or none | anything else | |

Calibration: on the v1 far fine delta leaf cell, interchange KO 0.485, mean 0.690, zero 0.607; circuit alone under
mean 0.495 (HB (a)). Every mean/zero cell with D-test KO accuracy in 0.25-0.75 gets ticket 06's flip audit for
positional default (tooling named in ticket 03).

Predictions:

- the core reads as answer machinery on all three tasks;
- the exclusives' no-pressure flips under interchange (sdr 21%, ser 34%) are an item-injection artifact, so their
  no-pressure deceptive rate under zero is <= 0.10;
- by R-cls on the sweeps, >= 2/3 of the core is shared and the majority of each exclusive set is
  deception-leaning.

### 2.6 RQ-B. Where and how does the pressure enter?

Measurements:

- **B1. Neutral-twin sweeps** on D at three position sets: all (S2), post-clause (S2p) and the Readout only (S3).
  An effect post-clause but not at the Readout means the Component processes the pressure upstream; an effect at
  the Readout means it carries the decision there.
- **B2. Paired attention** (D vs its twin, 1,000 paired rows; ticket 02b). The pressure-reader signature: a head's
  attention mass from the Readout query on the `pressure_clause` span falls under the twin by >= 0.05 and >= 2 SE
  (paired).
- **B3. Paired DLA differential** (D minus twin, per instance, 1,000 rows), and a per-instance logit-lens
  trajectory (ticket 02a).
- **B4. Path patching** under the neutral-twin counterfactual into the candidates' Q, K and V (phase 3), read by the
  four categories of §2.3.

Predictions:

- **B-selector.** At least one of L17H24-27 (all four in the core) has category Q on >= 2 tasks; the core's L24
  heads fall in "K/V from post-clause positions" (movers). The four L17 heads share one KV group, so their K/V
  categories are one test, not four (§7).
- **B-reader.** The share of B2-signature heads in layers 8-17 exceeds the base rate 10/32 by a one-sided binomial
  test, p < 0.05, per task. The v1 SDR D&H core's L13H5, L13H20 and L13H21 (0.15-0.25 of their mass on the clause in
  v1; all three in the v2 core) show the signature.
- **B-lens (rule R-lens), EXPLORATORY (R12).** An instance is "honest-first" if the lens margin,
  logit(deceptive) - logit(honest), is < -0.5 at some layer in 8..28 before the final layer's margin turns
  positive. Expected direction: FAR's honest-first rate exceeds that of the act-naming subsets of SDR and SER by
  >= 0.2. Clause form comes from a committed table of the 49 test clauses (12 / 20 / 17), labelled before any lens
  run by a text rule: Predicate-naming iff the clause contains a Predicate word; act-naming iff it says wrong,
  incorrect, false or not true; otherwise other. Every between-task CI on instance-level quantities, the lens
  included, is a bootstrap clustered by `pressure_id`. The neutral-twin lens is the reference trajectory. Not gated:
  FAR has no Predicate-naming clause, SER has 72 act-naming rows, and the raw lens is uncalibrated (§7).

### 2.7 RQ-C. How do the mechanisms differ?

Measurements:

- **C1. Cross-task knockout matrix**, read from the phase-1 sweeps (R16): every Component on 9 test sets (3 tasks
  x D/H/F) under item-swap (S1, S5, S6), on D also under neutral twin (S2, S2p, S3) and mean (S4). The 1B sweeps bind
  U (the 123-head union at leaf), so the in-circuit columns are in the same head table. No duplicate single
  knockouts in phase 2.
- **C2. What the exclusives and D-H heads read and write**: top Segment at the Readout (Predicate Token,
  Designation Suffix, question and response line, Pressure Clause, Item Mentions), DLA under pressure and paired.
- **C3. Cross-task role comparison**: roles per task under the amended criteria (R7), and the family knockout of
  each composition set on each task.
- **C4. Machinery outside the heads-only circuits**: the MLP rows of the sweeps. Heads-only circuits keep every MLP
  by construction, so only the sweeps can say this.

Predictions:

- **C-own (rule R-own).** For each head of excl_t, "own" means its d(D) on t's D (S1) exceeds the maximum of its
  d(D) on the other two tasks' D. One-sided sign test over the set's heads, Holm over the three tasks. Holds for sdr
  and ser, fails for far (06: far's exclusives separate on 0/4 metrics). Power is low: far's 8 heads give a minimum
  p of 0.004 before Holm, so far can pass only at 8 of 8.
- **C-reads.** The three exclusive sets differ in their top-Segment group (Fisher exact over group counts,
  p < 0.05; a head-level test, not clustered). They sit at different depths already (HB (g)): sdr's 8 of 14 at L4-5,
  far's 8 of 8 at L9-14, ser's 7 of 10 at L15-16. Exploratory, not gated: sdr's early heads read designation or Item
  Mention positions, and ser's later heads read the clause or the Designation Suffix.
- **C-v1.** v1 replication: of L5H8, L5H9, L5H11 and L9H12 (in v2 sdr's exclusives; flagged by the v1 SDR
  head-delta), >= 3 classify deception-leaning by R-cls on sdr_v2 and not on far_v2 or ser_v2.
- **C-MLP.** No MLP block other than layer 0 is deception-leaning on exactly one task with d(D) >= 0.1, and the late
  MLPs (L30, L31) are shared. Falsified by one such MLP.
- **C-confound.** far's D-H holds 11 core heads (ser's none). If far's "deception-leaning" D-H reading of 06 does
  not survive in `(D-H)-core` (R-A1, set 6), the paper says the far D-H effect was core.
- **C-honest.** The late H-D heads, in layers no D circuit uses (far L22, all three L30, sdr/ser L18), write towards
  the honest answer on H and F. Under pressure their honest-direction DLA is >= 50% smaller than on the paired twin
  (they are suppressed, not absent).

### 2.8 RQ-D (ticket 07, conditional per R5). Are the mechanism-specific heads stable across seeds?

Runs only if a headline claim rests on exclusive-head identities (R-own, C-reads or C-v1) after the phase-1
reading. Seeds 1 and 123 for the three D circuits. Prediction: the core's chance-corrected Jaccard across seeds is
>= 0.6, and the exclusives' is <= 0.4. Each exclusive set's median layer stays within ±2 layers. If the identities
are unstable, mechanism claims are made at the level of layer band and function, not head identity. If ticket 07
does not run, single seed is stated as a limitation (§7).

### 2.9 Descriptive (cheap, no gate)

- Layer of emergence per task: the first layer where the mean lens margin turns positive on D, against the twin.
  From the same DLA run as B3.
- Pressure-clause attention mass per layer per task.
- Segment-resolved neutral-twin knockout of the top 20 (phase 2). Pre-clause Segments must read exactly zero; that is
  a sanity assertion, never a finding (R16).

## 3. Prerequisites (tickets 01, 02a, 02b, 08)

**Ticket 01: infrastructure** (unblocks phase 1A; 0 GPU-h).

- `scripts/remote/b2.sh`: the branch comes from the profile or a flag; it is hard-coded `mechanism-datasets` today
  (`:25`). Add `outputs/_analyses` to the fetch roots (`:35`; the directory is git-ignored, `.gitignore:8`). Point
  the Delta repo root at this worktree (`delta.env:25`, `DC_DELTA_REPO_ROOT`).
- `scripts/analyze_components.sbatch`: the cluster-profile block of `evaluate_circuit.sbatch:48-61`. Today it
  sources `~/.bashrc` (`:62`), which does not exist on Bridges-2.
- Ticket-06 launcher (`outputs/_launch_mechanism_v2/evals/mv2_cells.py:72`, `gen_cells.py`): an ablation parameter,
  the phase-1A cell set including `(D-H)-core`, and per-task packing of several schemes into one job.
- `evaluation/`: a **variant-matched mean bank** (R13). Mean ablation of the `no_pressure` variant rows uses a bank
  collected on `<t>_v2_nopressure`; the task bank stays D's test split. Tested; v1 and interchange behaviour
  byte-identical.

**Ticket 02a: what phase 1B and 1C need** (1.0 GPU-h).

- `dataloaders.py:72` `MECHANISM_TASKS` gains the v2 ids, including the `<t>_v2_inversion` condition of ticket 08.
- Segmentation (`segmentation.py:534-541` registries; `_mechanism_intro` at `:338` dispatching to
  `deception_v2.make_spec`). The v1 segmenter validates all 9,000 v2 rows once dispatched (HB (b)5). A v2 scheme adds
  the `response_line` Segment carved from `question`, in the `frame` group (R7). The v1 scheme stays byte-identical.
- `analyze_components.py:345`: v2 cells are never skipped silently.
- A `neutral_twin` paired kind: `<t>_v2_honest` joined by `instance_id`, `honest_twin_kind == neutral_clause`
  asserted, same `pressure_id`, `assert_clause_aligned_pair` on both streams, D's labels kept. The D-row columns
  `neutral_prompt` / `neutral_text` are the Prior-Balance prompt (Designating Sentence neutralized, clause kept),
  NOT the twin; a test asserts the twin comes from `<t>_v2_honest` (R16).
- Sampling: an id-exclusion option for the held-out sample (seed 1, selection ids excluded). `component_analysis/
  sampling.py` `draw_sample` has none today.
- Knockout: `--knockout-scheme {interchange, mean, zero}` (evaluator mean semantics); `--knockout-counterfactual
  {item_swap, neutral_twin}`; `--knockout-positions {all, readout, <Segment>}` plus the range form
  `after=<Segment>[,exclude=readout]` (R11(a)); `--knockout-groups FILE` (JSON `{name: [[kind, layer, index], ...]}`
  in `head_table.row_key` order, R16).
- DLA: the `neutral_twin` paired condition and differential, and the per-instance lens crossing summary.
- The committed clause-form table of the 49 test clauses (R12), before any lens run.
- Tests in both envs, login dry-runs of every phase-1B/1C cell, the Bridges-2 smoke and the component drift control.

**Ticket 02b: neutral twin in attention and path patching; the criteria amendment** (0.5 GPU-h; blocks phase 2,
not 1B).

- `neutral_twin` in attention patterns (paired condition) and path patching (counterfactual, `_neutral_twin_paired`
  columns), plus the per-head receiver category of §2.3 (Q / K-V clause span / K-V post-clause / none).
- The v2 amendment of `docs/component-roles.md` (R1, R7, R10): neutral-twin columns in rule 4, the `response_line`
  Segment in `frame`, and the pressure-reader criteria for v2 cells. Applied before any v2 roles pass.

**Ticket 08: the instructed-inversion control condition** (R15; 0.5 GPU-h). `<t>_v2_inversion`: same instance ids
and target item as D, a transparent clause (the asker requests the inverted item), clause token count matched to
D's clause per instance so that `<t>_v2_honest` is its paired twin, behaviour-filtered. A new builder script; the
provenance-pinned builders and the existing v2 files are not edited.

## 4. Costed cell list per phase

Bridges-2 GPU-shared, one h100-80 per job (2 SU per GPU-h). Model load 10.5 min cold, 0.4 min warm. Evaluator KO
cell 6.5 min on an H100. Sweep (1,056 Components, n = 100) ~13 min; one group knockout ~0.75 s (sweep / 1,056).
Walltime = estimate x 1.5, rounded up to a quarter hour; "expected" is the estimate. Sources: HB, "Cost model".
Component-analysis H100 rates are extrapolated; ticket 02a's smoke and the first 1B job recalibrate them.

### Phase 0 (tickets 01, 02a, 02b, 08)

| ticket | cells | reserve | expected |
| --- | --- | --- | --- |
| 01 | login dry-runs, `sbatch --test-only` (Delta and Bridges-2) | 0 | 0 |
| 02a | smoke + drift: rerun v1 `sdr-dh-core-kosweep` (1,056-Component sweep) + one tiny v2 cell (`--n-causal 8`, every 02a analysis) | 1.0 | 0.5 |
| 02b | smoke: one tiny v2 cell, attention and path patching under neutral twin | 0.5 | 0.25 |
| 08 | behaviour filter, 3 tasks x 1,000 test rows | 0.5 | 0.25 |

### Phase 1 (ticket 03)

**1A. Circuit-level ablation replication** (needs ticket 01). Per task t, KO cells `(E) - m` at leaf on D_t's test
set, `--evals knockout`, 20 random KO sets, 1,000 items, E over the seven sets of §2.5:

| block | cells |
| --- | --- |
| mean, sets 1-7 | 21 |
| zero, sets 3-6 (R-A1's deciding no-pressure column) | 12 |
| interchange, set 6 (new set; its interchange twin) | 3 |
| total | 36 |

One job per task: 12 cells x 6.5 + load + banks (task, variant-matched no-pressure, wikitext) about 94 min.
**Reserve 3 x 2.5 = 7.5, expected 4.7.** If the launcher cannot chain schemes in one job, split per scheme and
re-cost (about +1.5 reserve).

**1B. Mask-independent sweeps and lens** (needs 02a's smoke and drift control). One job per task, U bound (the
123-head union at leaf, R16). All on the selection sample:

| cell | test set | counterfactual / scheme | positions | use |
| --- | --- | --- | --- | --- |
| S1 | D | item-swap | all | R-cls, C1 |
| S2 | D | neutral twin | all | descriptive (B1) |
| S2p | D | neutral twin | post-clause | R-AB ranking |
| S3 | D | neutral twin | Readout | B1 |
| S4 | D | mean | all | C1 |
| S5 | H | item-swap (honest margin) | all | R-cls, C1 |
| S6 | F | item-swap (honest margin) | all | R-cls, C1 |
| L | D paired with the twin (1,000 rows), F | DLA + logit lens with crossing summary | - | B3, R-lens |

Per job: 7 sweeps x 13 min + L ~6 + load + segmentation, about 110 min. **Reserve 3 x 3.0 = 9.0, expected 5.5.**

**1C. R-AB, R-inv and the routing check** (needs 1B and ticket 08). One job for the three tasks. Per task:

- S7: neutral-twin sweep on I at post-clause positions (selection sample, descriptive);
- greedy selection over the S2p top 50 to k = 20 (about 810 group knockouts, selection sample);
- on the held-out sample: both selectors' `S_k` over the k grid with the 20-draw layer-matched null (about 280 group
  knockouts on D), (ii) on H and F, R-inv on I, and the routing check of §2.3 against the preliminary `C_t`
  (phase 3's definition, built from the deciding set);
- core, excl_t and (D_t - H_t) - core as named groups under neutral twin on D and item-swap on H and F (descriptive).

About 34 min per task + load, about 112 min. **Reserve 3.0, expected 1.9.**

**Phase 1 total: reserve 19.5, expected about 12.1.**

### Phase 2 (ticket 04): Component cells

Circuit U is the 123-head union of the six circuits at leaf, plus at most 10 MLP blocks the phase-1 reading flags.
References: the six atomic run dirs only (`--reference NAME=RUN_DIR`; `component_analysis/intake.py:88-98`, `:129`).
Membership of core, excl_t, D_t - H_t and (D_t - H_t) - core is derived from the six reference columns on CPU.

Per task one job with four cells; no single-Component knockout passes (C1 comes from phase 1, R16):

- **(U, D):** attention patterns and DLA, pressure + neutral-twin paired, token-level for the top heads, designation
  split; family knockout by composition set; segment-resolved neutral-twin knockout of the top 20 (the clause, the
  post-clause question, item and response-line mentions, the stem, the Readout; the pre-clause Segments only as the
  zero-by-construction sanity assertion).
- **(U, H)** and **(U, F):** attention and DLA.
- **(U, I):** attention and DLA paired with the twin.
- Roles pass on every cell (CPU) under the amended criteria (R7, R10).

**Reserve 3 x 1.0 + 0.5 rerun = 3.5, expected 2.0.**

### Phase 3 (ticket 05): path patching on candidates only, never the union

Per task, grid circuit `C_t` = core | excl_t | ((D_t - H_t) - core) | the heads of the deciding `S_k` | at most 10
MLP blocks (the deciding set's MLPs first, then by S2p rank). About 55-80 Components.

- `--path-counterfactual both` (item_swap and neutral_twin);
- the position-specific pass at the default threshold;
- the path completeness sweep under neutral_twin.

About 105 min per task-job: **reserve 3 x 2.75 + 1.0 rerun = 9.25, expected 5.3.** `--dry-run` grid sizes replace
these numbers before submission. The full 32-MLP grid (R14) runs only for a task whose routing share (c) exceeds
0.25, and only after the user approves the cap raise it needs (about +2.75 reserve per task).

### Phase 4 (ticket 06): synthesis

CPU only: figures, claims table, limitations, records. **0 GPU-h.**

### Ticket 07 (conditional, R5): seeds, on Delta

Train D_far, D_sdr, D_ser at seeds 1 and 123 on gpuH200x8-interactive: 6 runs, ~0.5 h each, reserve 0.75 each.
Then 9 KO cells (each seed's exclusives, and the seed-intersection exclusives) in one Delta H200 job.
**Delta reserve 4.5 + 1.5 = 6.0, expected 3.9.** A40 training (~2.5 h per run) does not fit the 6 GPU-h and would
need a cap raise.

### Totals

| item | Bridges-2 H100 reserve | expected |
| --- | --- | --- |
| phase 0 (02a, 02b, 08) | 2.0 | 1.0 |
| phase 1 (03) | 19.5 | 12.1 |
| phase 2 (04) | 3.5 | 2.0 |
| phase 3 (05) | 9.25 | 5.3 |
| holdback | 0.75 | - |
| **total** | **35.0 (70 SU)** | **~20.4 (~41 SU)** |
| ticket 07 (Delta H200, conditional) | 6.0 Delta | 3.9 Delta |

The holdback is small because reserves are walltimes: reconciliation to sacct frees about 14 GPU-h of the cap if the
estimates hold. Compared with the pre-review plan, phase-1 reserve rises by 2.25 and expected by 1.1, and phase 0
gains 02b and 08 (+1.0 reserve).

## 5. Phase order and the phase gate

1. Tickets 01, 02a and 08 start in parallel; 02b starts when 02a lands (it reuses 02a's pairing).
2. Phase 1A starts when ticket 01 lands. Phase 1B starts when 02a's Bridges-2 smoke and component drift control
   pass. Phase 1C starts when 1B and ticket 08 are done. If 1A and 1B/1C compete, 1B and 1C go first (R17).
3. Phase 2 starts after phase 1 and ticket 02b (the criteria amendment applied). Phase 3 starts after phase 2.
   Phase 4 starts after phase 3 (and ticket 07, if it runs).
4. **Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
   submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only
   if the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user
   is always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.
5. Standing constraints:
   - no training except ticket 07 under R5;
   - no two-way result;
   - no change to the v2 datasets, their provenance-pinned builders, or any existing output;
   - `docs/component-roles.md` changes only by ticket 02b's v2 amendment (R1, R7). The orchestrator reports its
     text, the pressure-reader criteria included, to the user before 02b applies it; it is in the doc as a dated
     amendment before any v2 roles pass; the user may veto until then (R10). Any other criteria change needs the
     user.
6. **Bridges-2 goes offline around 2026-11-09** (user's information, unconfirmed by PSC). GPU work is front-loaded:
   phases 1 to 3 are planned to finish by about 2026-11-04. Results are fetched to Delta after every job wave;
   anything only on `/ocean` is at risk. If Bridges-2 is unavailable, Delta is the fallback with the orchestrator's
   approval per wave, inside R2's cap: bjhz-delta-gpu first; A40 or H200 for phase 1; H200 only for phases 2-3
   (R16; phase 3 on A40 would cost about 21 GPU-h).

## 6. Budget

- **Bridges-2** (R2): cap **35 H100 GPU-h = 70 SU** for tickets 01-06 and 08. The allocation cis260361p has 200 SU;
  mechanism-datasets used 23.0 SU, so 177 remain, and 107 would remain at the cap.

  | ticket | allocation (H100 GPU-h) |
  | --- | --- |
  | 01 | 0 |
  | 02a | 1.0 |
  | 02b | 0.5 |
  | 08 | 0.5 |
  | 03 | 19.5 |
  | 04 | 3.5 |
  | 05 | 9.25 |
  | 06 | 0 |
  | holdback | 0.75 |

  The orchestrator may move reconciled savings between tickets inside the cap. A raise needs the user.
- **Delta** (R2): **18 GPU-h** in total = 12 fallback (above) + 6 for ticket 07 (H200 only to fit).
- Accounting as in `compute-ledger.json`. Reserve = `--time` x GPUs before submission, reconciled to sacct elapsed
  rounded up to 0.25 h. Submit only if reconciled + in-flight + new stays within the ticket allocation and the cap.
  Every write to the ledger holds its lock (agent-brief, R16).
- No OpenRouter use is planned.
- **Records (R6, R16).** Analysis cells stay untracked under the worktree's `outputs/_analyses/mechanism-analysis-*/`
  on Delta (canonical, fetched from Bridges-2); nothing under `outputs/_analyses/` is un-ignored. Each ticket
  commits a curated copy of what the paper needs (head tables as CSV, `roles.json`, readings JSON) under
  `docs/research/mechanism-analysis/` on the branch; ticket 06 writes the synthesis there. `.scratch` reports are the
  working record. Before the worktree is removed, the orchestrator moves the cells to the main checkout's
  `outputs/_analyses/` (git-ignored files are deleted with a worktree).

## 7. Limitations to state in the paper

1. **Single seed** (42) for every circuit unless ticket 07 runs (R5). Head identities of small sets (exclusives,
   D-H) may not replicate.
2. **Unpaired cross-mechanism comparison** (R8). The Comparison Set has 8 test instances (5 train, 0 validation;
   HB (d)). Comparisons are between-group, matched only on the stratification marginals (designation x item polarity
   250 each, template variants 500/500) and overlapping item pairs. Clauses differ by task.
3. **Interchange-pruned circuits.** The circuits were pruned under item-swap interchange, so they are biased towards
   answer-carrying Components; item-swap interchange cannot see a Component that only reads the Pressure Clause.
   Mitigated by mean/zero (1A), the neutral-twin counterfactual and the mask-independent sweeps.
4. **Instruction-following inducement.** All three tasks use `rule_instructed` clauses (an operator rule that fixes
   the answer by relation). The deception studied is instructed, not motive-driven.
5. **Deception vs instructed inversion.** The neutral-twin contrast removes an operator rule that says "name the
   other one". Ticket 08's transparent-inversion control separates the two only as far as its clauses match D's
   wording; they differ in wording and in whether anyone is misled (R15).
6. **Wording confound.** FAR's 12 test clauses are all act-naming, so FAR has no Predicate-naming subset. The pool's
   slot provenance does not map to clause form, so form comes from the text-rule table (R12). SER's act-naming
   clauses cover 72 of 1,000 rows, SDR's about 216. R-lens is therefore exploratory.
7. **FAR's question and stem name the Predicate** ("The result that is failing is"), which primes the factual
   answer.
8. **Few clauses per task**: 12 / 20 / 17 test clauses with 1 to 150 rows each. The effective n for cross-task
   contrasts is clauses, not instances; between-task CIs are clustered by `pressure_id`.
9. **The neutral twin flips the answer as well as the clause.** A neutral-twin knockout conflates "pressure removed"
   with "honest answer written". Post-clause ranking without the Readout reduces this, it does not remove it.
10. **Selection and test.** The held-out sample is disjoint in instances but shares clauses with the selection
    sample, so clause-specific effects can carry over. Two selectors at six k values give each task more than one
    chance at reading A; the null controls each test, not the family.
11. **Redundancy and self-repair.** Single-Component ranking misses redundant sets and self-repair; the greedy
    selector over the top 50 is a partial remedy.
12. **Path patching freezes every non-grid Component.** Path claims are relative to `C_t`. The routing check bounds
    the share of the gap outside `C_t`; the 32-MLP grid runs only under R14.
13. **Shared KV group.** L17H24-27 share one KV group, so B-selector's K/V categories for them are one test, not
    four.
14. **Mean ablation** is position-pooled and broadcast to every position, BOS included, which is harsher than
    position-wise mean ablation. Its task bank is pressure prompts, so on no-pressure rows it can inject the
    pressure; R-A1's no-pressure column is decided under zero and the variant-matched bank is robustness (R13).
15. **Raw logit lens** (no tuned lens): uncalibrated, so -0.5 at layer 8 and at layer 28 mean different things.
16. **Construction-defined mechanism purity.** LLM judges did not separate SDR from SER (kappa 0.00/0.08).
17. **Heads-only circuits.** Every MLP is kept in every circuit; MLP claims rest on the sweeps alone.
18. **Incomplete pressure contingency of the circuits.** D alone names the deceptive item on 20-53% of no-pressure
    rows (06).
19. **One model, one-token Readout, 1,000 test instances per task, causal views on 100-instance samples** (about 12
    instances per stratum; balanced allocation, so sample rates are not split rates).
20. **Counterfactual change from v1** (R1). v2 roles read a pressure-vs-neutral contrast where v1 read
    pressure-vs-honesty-instruction; v1 and v2 roles are not directly comparable.
21. **Cross-GPU numerics.** Bridges-2 H100 and Delta results are not bit-exact; drift controls bound it (G15 for the
    evaluator; ticket 02a for component analysis).
22. **Multiple comparisons** over 1,056 Components x 9+ test sets: only the pre-registered rules decide; everything
    else is exploratory.
23. **Thresholds** (R17): R-A1's bands rest on one v1 cell and R-cls's factor of two on one v1 analysis; every other
    threshold is a convention.

## 8. Left to the builder

- Job packing within a ticket's allocation, including whether 1C runs as one job or three.
- The launcher's stage names.
- The MLP blocks added to U (phase 2) and to `C_t`, within the caps of §4.
- The inversion clause wording, within ticket 08's constraints and its review.
- Figure design.

## 9. Rulings

Numbered R1, R2, ... Orchestrator rulings are made under the user's standing go of 2026-10-25 ("We can start making
progress once the plan is agent-reviewed and good to go (you have my permission)"); user decisions are marked
as such. The user is still asked before any merge to main, any EVAL 5, or dropping a mechanism.

- R0. (Orchestrator, 2026-10-25.) Every threshold in §2 (R-AB, R-A1, R-cls, R-lens, R-own, ...) is pre-registered
  as written and is the spec-writer's proposal, not a measured calibration. Numbers at other thresholds are
  reported where useful; they never decide a reading. If a threshold must change, the change is dated and logged
  here before the affected cell is read.
- R1. (Orchestrator, 2026-10-25; §10 Q1.) The paired honest counterfactual for v2 component analysis is the
  Neutral-Clause Twin, paired by instance id (option 2). Matched-Honest-Instruction pools are NOT built for v2.
  The reserved role "pressure reader" is UN-RESERVED for v2 cells only, with its assignment criteria written into
  `docs/component-roles.md` (dated amendment, "Changing these criteria" section) BEFORE any v2 roles pass runs;
  v1 cells keep the reserved status.
- R2. (Orchestrator, 2026-10-25; Q2.) Caps: Bridges-2 35 H100 GPU-h (70 SU) for tickets 01-06; Delta 18 GPU-h
  in total = 12 fallback (bjhz-delta-gpu first; A40/H200 only, never A100 40 GB for training) + 6 for ticket 07.
  Any raise needs the user.
- R3. (Orchestrator, 2026-10-25; Q3.) Branch `mechanism-analysis` may be pushed to origin so the Bridges-2 clone
  can pull it. Pushing a feature branch is not a merge to main. Reported to the user in the next update.
- R4. (Orchestrator, 2026-10-25; Q4.) Phases run back to back under the user's standing go. Phase 1A starts when
  ticket 01 lands, 1B when ticket 02's smoke + drift control pass. Before each later phase's first GPU submission
  the orchestrator posts the previous phase's reading to the user; it STOPS and asks only if the reading changes
  the plan (e.g. outcome B on all three tasks makes phase-3 path patching moot, or a drift control fails).
- R5. (Orchestrator, 2026-10-25; Q5.) Ticket 07 (seeds) is CONDITIONAL: it launches on Delta (H200/A40) after
  the phase-1 reading if any headline claim rests on exclusive-head identities (R-own, C-reads, C-v1); otherwise
  it is dropped and single-seed is stated as a limitation. 6 Delta GPU-h reserved for it inside R2.
- R6. (Orchestrator, 2026-10-25; Q6.) Of record: analysis cells stay untracked under the worktree's
  `outputs/_analyses/mechanism-analysis-*/` on Delta (canonical, fetched from Bridges-2). Each ticket commits a
  curated copy of what the paper needs (head tables as CSV, roles.json, readings JSON) under
  `docs/research/mechanism-analysis/` in the repo, on the branch; ticket 06 writes the synthesis there too.
  `.scratch` reports are the working record; nothing under `outputs/_analyses/` is un-ignored.
- R7. (Orchestrator, 2026-10-25; Q7.) `docs/component-roles.md` is amended for v2 (neutral-twin columns in
  rule 4, the `response_line` Segment in the `frame` group, the pressure-reader criteria of R1), dated and logged
  as the document requires, applied in ticket 02 before any v2 roles pass.
- R8. (Orchestrator, 2026-10-25; Q8.) No cross-realization of the comparison set now; the unpaired
  cross-mechanism comparison is stated as a limitation (§7).
- R9. (Orchestrator, 2026-10-25; review-00 B6 / Pile-3 #1.) ONE hard-stop rule, written identically everywhere:
  phases run back to back under the user's standing go (R4 stands). Before each later phase's first GPU submission
  the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if the
  reading changes the plan (outcome B on all three tasks; a failed drift control; a cap raise). Spec §5, every
  ticket, agent-brief.md and the plan draft are synced to this wording. User-asks that never lapse: merge to main,
  EVAL 5, dropping a mechanism, cap raises.
- R10. (Orchestrator, 2026-10-25; Pile-3 #2.) R1 and R7 are CONFIRMED as orchestrator rulings under the standing
  go, reported to the user before ticket 02 applies them; the pressure-reader criteria text is written into the
  ticket-02 report and `docs/component-roles.md` BEFORE any v2 roles pass. The user may veto until then.
- R11. (Orchestrator, 2026-10-25; B1-B3 / Pile-3 #3.) R-AB is amended BEFORE anything runs: (a) ranking on a
  neutral-twin sweep restricted to post-clause positions excluding the Readout (a range form of
  `--knockout-positions`, e.g. `after=pressure_clause,exclude=readout`), layer-0 MLP excluded as the positive
  control; the all-positions sweep stays descriptive; (b) rank on the seed-0 causal sample, TEST on a disjoint
  held-out sample (seed 1, ids excluded); (c) 20-draw layer-matched random-k null and per-instance bootstrap CIs on
  both (i) numbers; (d) greedy joint selection over the top 50 as the second selector; k grid
  {1,2,3,5,10,20,40,80} for the mediation curve; (e) the reading is renamed "pressure mediators" (not "pressure
  readers"); (f) outcome B is reworded to what is measured: "no set of <= 20 Components, chosen by single-Component
  or greedy neutral-twin effect, mediates the pressure; the neutral-twin effect is spread over Components that
  R-cls calls shared" (share reported); (g) A′ adjudication is exhaustive per member head (MLP members excluded,
  counted): Q (selector) / K-V from the clause span (reads the clause) / K-V from post-clause item or question
  positions (reads pressure-modulated items) / nothing above the floor; the call is by majority of S_k's heads,
  weighted by their single effect; (h) because path patching freezes non-grid Components, phase 1C adds the cheap
  routing check: joint neutral-twin knockout of all 32 MLPs at post-clause positions, and of all non-C_t heads,
  each reported as a share of the clean-minus-twin gap. A′-mover is claimed only if the outside-C_t share is small
  (<= 0.25). (i)'s 0.75 is a ratio of means; per-instance ratios are reported.
- R12. (Orchestrator, 2026-10-25; B5 / Pile-3 #4.) R-lens is EXPLORATORY, not gated. The hand-labelled clause table
  (text rule: Predicate-naming iff the clause contains a Predicate word; act-naming iff it says wrong / incorrect /
  false / not true; otherwise other) is still committed before any lens run, and every between-task CI, lens
  included, uses a bootstrap clustered by `pressure_id`. §7 gains: FAR's question and stem name the Predicate; the
  raw lens is uncalibrated; the effective n for cross-task contrasts is clauses, not instances.
- R13. (Orchestrator, 2026-10-25; B4 / Pile-3 #5.) R-A1's no-pressure column is DECIDED under zero ablation. Mean
  ablation for that column uses a variant-matched bank collected on `<t>_v2_nopressure` (ticket 01 code change in
  `evaluation/`, tested) and is reported as robustness; the position-broadcast caveat goes in §7.
- R14. (Orchestrator, 2026-10-25; B3 / Pile-3 #6.) Phase 3 keeps the heads+<=10 MLP grid. The full 32-MLP grid
  runs only for a task whose R11(h) routing check puts > 0.25 of the gap outside C_t, and only after the user
  approves the cap raise it needs (about 2x that task's phase-3 cost).
- R15. (Orchestrator, 2026-10-25; Pile-3 #7.) A non-deceptive instructed-inversion control IS built: a new
  condition `<t>_v2_inversion` per task (transparent game clause, e.g. "the reviewer asked you to name the result
  that is NOT failing", same instance ids, clause surgery, behaviour-filtered; CPU + < 1 GPU-h). Ticket 08. It is
  used in phase 1C/2 as a test set: if S_k also mediates transparent inversion, the paper says "instructed
  inversion machinery", not "deception". Dataset v2 files are untouched; this is a new condition like `nopressure`.
- R16. (Orchestrator, 2026-10-25; Pile 2.) All thirteen Pile-2 defaults are adopted as written in
  `reports/00-plan-review.md` §2, including: flip-audit paths; `--knockout-groups` JSON format; R-cls on signed d
  with an "opposes" class and the upper-95%-bound clause; the `neutral_prompt` column trap stated in ticket 02
  with a test; drift inputs verified in the manifest; the C1 matrix and C-own read from the phase-1 sweeps (bind
  U in 1B; no duplicate single knockouts in phase 2); B-reader's binomial test; C-own's definition and its low
  power stated; a lock file around `compute-ledger.json` writes; cells moved to the main checkout's
  `outputs/_analyses/` before the worktree is removed; Delta fallback for phases 2-3 on H200 only; segment-resolved
  pre-clause knockouts are a sanity assertion, never a finding.
- R17. (Orchestrator, 2026-10-25; §3 non-blocking.) Ticket 02 is split into 02a (what phase 1B needs) and 02b
  (neutral twin in attention and path patching, the criteria amendment). 1B/1C take priority over 1A if they
  compete. §7 gains the reviewer's added limitations list and the one-sentence statement of which thresholds are
  calibrated (R-A1 bands on one v1 cell; R-cls factor two from v1) and which are conventions. Expected phase-1
  cost rises by about 2 H100 GPU-h (held within the 3.5 h holdback); the 35 h cap stands.

Sync note (plan-01, 2026-10-25; for the orchestrator to confirm or amend). After the 02a/02b split, "ticket 02" in
R4, R7 and R10 reads: 02a for the smoke and drift control that gate phase 1B (R4), and 02b for the amendment and its
report (R7, R10). The recost of §4 puts phase 1 at +2.25 reserve / +1.1 expected and adds 02b and 08 (+1.0 reserve),
so at the 35 h cap the holdback is 0.75, not 3.5 (R17's "held within the 3.5 h holdback"); §4 and §6 carry the
recosted numbers. Ticket 08 (R15) draws on R2's Bridges-2 cap with tickets 01-06. Ticket 07 is costed on H200 only:
A40 training (~2.5 h per run) does not fit R5's 6 Delta GPU-h.

- R18. (Orchestrator, 2026-10-25; confirms the sync note.) (1) Holdback 0.75 h accepted at the 35 h cap; reconciled
  savings refill the holdback first (§6); a cap raise is a user-ask. (2) "ticket 02" reads 02a in R4 (smoke + drift
  gate for 1B) and 02b in R7/R10 (criteria amendment). (3) Ticket 07 is H200-only on Delta, 6.0 GPU-h. (4) R2's
  Bridges-2 cap covers tickets 01-08. plan-01's gap calls (greedy stops at k=20; zero cells for sets 3-6 only; I's
  clause token-matched so the existing twin pairs with I; routing condition covers A′-mover and A′-unresolved) are
  confirmed. Spec status: approved. Implementation starts 2026-10-25 with tickets 01 and 02a in parallel.
- R19. (Orchestrator, 2026-10-25; review-00 re-check, reports/00-plan-review-2.md.) Four additions, binding for the
  tickets named: (1) 02a: every group knockout and sweep writes per-instance clean margins, knocked margins and
  the twin's own margin (R-AB's denominator and the bootstrap CIs need them). (2) 01: the variant-matched mean
  bank is opt-in behind a flag (v1 mean cells stay byte-identical without it); with the flag the no-pressure side
  runs under both banks and reports both; the bank is collected over the evaluator's own no-pressure variant
  loader. (3) R-inv is PAIRED: 02a adds an id-inclusion option; f_D and f_I are computed on D's held-out ids that
  survived I's filter; the reading "instructed inversion machinery" holds when the paired bootstrap (clustered by
  pressure_id) 95% CI of f_I - 0.5 f_D lies above 0, "deception-specific" when the CI of 0.5 f_D - f_I lies above
  0, otherwise "undecided". This replaces "CIs do not overlap" and is dated before any 1C job. (4) 08: each
  inversion clause is form-matched to its D clause by the clause-form table (act-naming D clauses get act-naming
  transparent-game inversion clauses, Predicate-naming get Predicate-naming) and token-matched; the ticket-08
  report shows the per-clause match before the pool is used. Non-blocking: the lens summary also records the layer
  of the last sign change; the clause-form rule states its precedence (act-naming is checked first, then
  Predicate-naming, then other).
- R20. (Orchestrator, 2026-10-25; ticket-08 spec review.) Every inversion clause carries an explicit transparency
  marker beyond "openly wants": a knowledge marker (the asker knows which result is unfavorable / critical /
  failing) or an intent/game marker (on purpose, drill, quiz, game), checked mechanically by `pool_violations`;
  "other"-form D clauses get "other"-form I clauses; the I filter is argmax = target AND margin >= 0.7 in both
  streams (both counts reported); retention reported per full sampler stratum; D-derived `d_*` fields on I rows are
  renamed `i_*`.
- R21. (Orchestrator, 2026-10-25; ticket-01 reviews.) With `--variant-mean-bank` the no-pressure rows run under
  BOTH banks and both results are written (blocking fix). The three ser set-6 cells of phase 1A are dropped: on
  ser, D-H holds no core head, so set 6 equals set 5 and the interchange cell duplicates ticket 06's; 1A is 33
  cells, suite_ma.json records the identity. The thread-limit env vars added to analyze_components.sbatch are an
  accepted, logged deviation from byte-identical v1 behaviour.
- R22. (Orchestrator, 2026-10-25; ticket-08 scoring result.) The descriptive transparent pool ("the buyer wants
  the wrong result") keeps FAR 0 / SDR 618 / SER 7 of 1,000 ids under the I filter: a reported third-party wish does
  not move the model off the truth on FAR and SER, while SDR's disclosure choice follows it. This is kept as a
  FINDING and a secondary condition `<t>_v2_inversion_reported` (committed as built; FAR config + filter report
  only). The primary I condition `<t>_v2_inversion` is rebuilt from a DIRECTIVE transparent pool (imperative to the
  assistant with an explicit quiz / drill / game frame, no motive to mislead; form- and token-matched per D
  clause), one more scoring job (0.25 H100 GPU-h). The 300-id minimum still applies per task; a task that still
  fails it has no I contrast and says so in §7.

- R23. (Orchestrator, 2026-10-25; ticket-03 1C-b question.) R19(3) as written (f_D and f_I on D's held-out ids that
  survived I's filter) yields paired sets of 14 / 73 / 26 ids (far / sdr / ser), too small for the clustered bootstrap
  and for the FAR within-stratum comparison. RULING: the paired R-inv sample is drawn from I itself (seed 1, S1
  selection ids excluded, 100 ids per task; the FAR and SER pools are 210 and 249 rows) and D is run on the SAME ids
  (--include-ids), so the pairing holds, the sample stays disjoint from the selection sample, and the S_k remain
  chosen on D's selection sample only. This keeps R19's intent (pairing by id, clustered by pressure_id) and matches
  spec §2's wording for I's held-out sample. The letter-of-R19(3) subset (D held-out ∩ I filter, 14 / 73 / 26) is
  also reported as a robustness row since its cost is negligible. Both samples condition on I-filter survivorship;
  §7 says so, and FAR's result stays marked polarity-confounded (R22 strata).

- R24. (Orchestrator, 2026-10-25; after the 1B reading.) The 1C selectors already rank all 1,056 components (the
  S2p sweep is a completeness sweep; U only marks membership), and 31-36 of the S2p top 50 lie outside U on every
  task. RULING: 1C-b adds a DESCRIPTIVE "U-only top-k" arm (single selector restricted to U's 123 heads, same k
  grid, 20 layer-matched nulls each on held-out D, k <= 20 sets on H and F; ~190 groups per task, ~0.15 GPU-h, folded
  into the existing 1C-b groups files; 1C-b walltime 00:45:00 -> 00:55:00). It compares the circuits' best heads
  against the model's best on the held-out R-AB metrics. The pre-registered selectors, readings and the R-AB outcome
  rule are unchanged; the arm is reported in §7 as descriptive and may motivate a phase-2 arm (ticket 04) only
  under a separate ruling.

- R25. (Orchestrator, 2026-10-25; ticket-02b amendment draft.) The v2 criteria amendment to docs/component-roles.md
  (reports/02b-amendment-draft.md: rule 4 / 6 read the neutral-twin path columns on v2 cells; new rule 4b "pressure
  reader" = B2 signature (clause_mass_drop_neutral_twin_paired >= 0.05 and >= 2 SE) AND significantly positive S2p
  neutral-twin post-clause knockout AND, where path data exist, receiver category kv_clause, else flavour "attention
  and knockout only"; --roles-b2-floor 0.05 as an R0 proposal; response_line in the frame group; receiver category
  q / kv_clause / kv_post_clause / kv_unresolved / none above the 0.01 floor with recorded tie-breaks) was REPORTED
  to the user in the orchestrator's 19:10 CDT update per R10 and may be applied; the user may veto. Decisions:
  (A) phase-3 path grids run with --path-twin-position-threshold 0.01 (the neutral-twin Segment pass alone; item_swap stays at 0.05) so that no
  path above the category floor reads kv_unresolved for lack of a position split, PROVIDED the dry-run cost stays
  within ticket 05's allocation; otherwise keep 0.05 and report kv_unresolved. (B) --path-counterfactual both =
  item_swap + honest_instruction on v1 and item_swap + neutral_twin on v2 (no Matched Honest pool for v2, R1);
  neutral_twin alone writes a skipped file on cells without a twin. v1 tables stay byte-identical (snapshot test).

- R26. (Orchestrator, 2026-10-25; phase-1 reading.) The deciding S_k sets lie mostly outside U (far 15 of 20 heads,
  ser 12 of 20) and the U-only arm never passes (i), so phase-2 cells run on U' = U | the heads of each task's
  deciding S_k (far / ser greedy k = 20; sdr single k = 20, descriptive) | the proposed C_t MLP blocks (<= 10 per task,
  p1c_readings.json), instead of U plus MLPs alone. Membership columns record which of U, S_k and C_t each Component
  belongs to, so every reading can be split by circuit membership. The segment-resolved neutral-twin knockout stays
  on the S2p top 20 regardless of membership. Cost change is negligible (<= 20 heads per task). Phase-3 C_t is
  unchanged (§4). Reported to the user with the phase-1 reading; the user may veto.

- R27. (Orchestrator, 2026-10-25; found by ticket 04.) roles.py reads the v1 DLA differential (dla.differential_paired)
  on both variants, but a v2 DLA cell writes that column as None and the twin differential under
  dla.differential_neutral_twin_paired, so on a real v2 cell no Component could be a selector and rule 6's
  differential clause was vacuous; the test fixture kept the v1 column and hid it. RULING (amendment, same shape as
  R25's query-side change, applied by ticket 02b): on a v2 cell rule 4's writes clause and rule 6's differential
  clause read dla.differential_neutral_twin_paired / _se (pressure minus the Neutral-Clause Twin, paired) in place
  of dla.differential_paired / _se; floor and z unchanged. Code: a Variant field for the differential pair read in
  views_of; the v2 fixture drops the v1 column; v1 snapshot byte-identical. Phase-2 roles passes run only after this
  lands. Reported to the user; the user may veto.

- R28. (Orchestrator, 2026-10-26; phase-2 reading.) Phase 3 runs on the C_t proposed by ticket 04 (far 72 / sdr 66 /
  ser 78 Components) with `--path-counterfactual both` and `--path-twin-position-threshold 0.01` (R25 A). The
  measured cost (0.036 s per forward) gives far ~110 min, sdr ~95 min, ser ~125 min; walltimes at x1.5 are 2.75 /
  2.5 / 3.25 h = 8.5 GPU-h, within ticket 05's 9.25 GPU-h allocation, so ser's per-task line is raised from 2.75 h to
  3.25 h by reallocation inside the ticket (no cap raise). The phase-2 researcher decisions (C-honest is a sign flip,
  not suppression; C-reads has no power because the sink dominates; ser walltime) are reported to the user with the
  phase-2 reading; none changes the phase-3 plan.

- R29. (Orchestrator, 2026-10-26; phase-3 reading.) sdr formally qualifies for R14's 32-MLP grid (routing (c) =
  0.297 > 0.25) but sdr's R-AB reading is B, and R14 exists to rescue a routing-gated A' sub-reading, so the grid is
  NOT run; §7 states that sdr's route description is descriptive and carries the (c) and 0.02-floor caveats. R5:
  no headline claim rests on exclusive-head identities (phases 1-3), so ticket 07 (seed replication) does not run.
  Ticket 06 (synthesis) starts now; its wording of sdr's route ("query-heavy, with post-clause value reads") and of
  B-selector ("clause 1 confirmed; the L24 heads are fed at the query by L17H24", second half exploratory) follows
  ticket 05's recommendation. The user may veto either.

- R30. (Orchestrator, 2026-10-26; ticket-06 spec review, blocker.) R22's last sentence ("a task that still fails
  [the 300-id minimum] has no I contrast") conflicts with what phase 1 did under the orchestrator's instruction of
  2026-10-25 16:05 CDT ("a task failing it runs as a stated limitation, not dropped; report its n explicitly") and
  with R23. RULING: R23 and that instruction supersede R22's last sentence. FAR (210 ids) and SER (249 ids) keep
  their R-inv readings, but every statement of them, the headline included, carries the qualification "below the
  300-id minimum; FAR polarity-confounded, inversion-polarity subset agrees", and §7 lists it as a limitation.
  R-inv licenses only "not called deception-specific" (f_I >= 0.5 f_D); "the same machinery" and "does the same
  work" are not licensed and the synthesis must not say them. sdr's S_20 is descriptive (B task), so sdr has no
  R-inv verdict row. The user may veto.

## 10. Questions for the user

None open. The eight questions of the draft plan were answered by orchestrator rulings under the user's standing
go, and the builder check's researcher questions by R9-R17:

| question | ruling |
| --- | --- |
| Q1 honest counterfactual; un-reserve "pressure reader" | R1, R10 |
| Q2 GPU caps | R2 |
| Q3 push branch `mechanism-analysis` | R3 |
| Q4 may phase 1 start; hard stops | R4, R9 |
| Q5 seed replication | R5 |
| Q6 what is of record | R6 |
| Q7 criteria amendment | R7, R10 |
| Q8 cross-realization of the comparison set | R8 |
| review Pile 3: R-AB amendments, R-lens status, no-pressure column, path grid, inversion control | R11-R15 |
| review Pile 2 defaults; ticket split; calibrated vs conventional thresholds | R16, R17 |

The user may object to any ruling; the plan draft lists them.
