# 03 — Phase 1: mean/zero replication of the circuit knockouts, mask-independent sweeps, and the R-AB / R-inv tests

**What to do:** run phase 1 of spec §4 (blocks 1A, 1B, 1C), then read it against the pre-registered rules R-A1,
R-cls, R-AB, R-inv, C-own, C-v1, C-MLP and C-confound, and report R-lens as exploratory (spec §2). Build the cross-task
knockout matrix (C1) from the sweeps.

**Status:** resolved
**Type:** task
**Blocked by:** 01 for block 1A; 02a (smoke + drift control passed) for 1B; 1B and 08 for 1C.
**GPU allocation:** 19.5 H100 GPU-h on Bridges-2 (1A 7.5, 1B 9.0, 1C 3.0). Delta only as a fallback with the
orchestrator's approval (A40 or H200, bjhz-delta-gpu first).

## Facts to build on

- Spec §2 (rules and predictions) and §4 (cell lists, costs). HB (a), (g). Review §0-§1 for why R-AB is built this
  way.
- Circuits: the six run dirs in mechanism-datasets `reports/05-training-summary.md`. The all-MLP operand and the
  nopressure stand-ins are in `outputs/_launch_mechanism_v2/evals/{operands,standins}/`. U for 1B = the 123-head union
  of the six circuits minus m, composed at leaf (head granularity leaks every MLP; memory
  `dh-core-component-analysis`); this ticket writes its operand.
- Ticket-06 numbers, interchange, to compare against: mechanism-datasets `reports/06-stage1-results.md` and
  `06-stage2-results.md`.
- Flip audit tooling (R16): `evaluation/knockout.py` `_flip_audit`, plus `flip_audit_analysis.py` as listed in
  mechanism-datasets `reports/06-recon-evals-and-bridges2.md:39`; the precedent is
  `outputs/_suites/mechanism-v2-coarse/dh_home_flip_audit/flip_audit.md` in the mechanism-datasets worktree.
- Groups files: JSON `{name: [[kind, layer, index], ...]}` in `head_table.row_key` order, written by a script under
  `outputs/_launch_mechanism_analysis/` that reads `sweep.json` (R16).
- Cost anchors: KO cell 6.5 H100-min; load 10.5 min cold, 0.4 warm. The sweep and group-knockout times measured in
  02a's smoke replace the extrapolated ones. **The first job of each block is the calibration**: compare its elapsed
  time with the estimate before the rest of the block goes in.
- Walltimes: observed runtime + buffer (x1.5, quarter hours), never worst case (memory `slurm-job-policy`).
- If 1A and 1B/1C compete for the same day, 1B and 1C go first (R17).

## Acceptance criteria

- [x] **1A.** 36 KO cells (33 run; ser set 6 = set 5 per R21) (spec §4) completed and fetched to Delta under `outputs/_suites/mechanism-analysis/phase1a/`.
      Table per task, set and scheme: D-test KO accuracy, no_pressure and honest_instruction KO deceptive rates
      (mean rows: task bank and variant-matched bank both stated), separation against the 20-set KO null, wikitext
      KL/token. Interchange values for sets 1-5 and 7 come from ticket 06. R-A1 reading for sets 3-6 (no-pressure
      column under zero); sets 1, 2 and 7 as calibration rows.
- [x] Flip audit (positional default) on every mean/zero cell with D-test KO accuracy in 0.25-0.75.
- [x] **1B.** Per task: the seven sweeps S1, S2, S2p, S3, S4, S5, S6 and the L cell on the selection sample with U bound, fetched to Delta under
      `outputs/_analyses/mechanism-analysis-p1/`. Then:
  - [x] R-cls class of every Component (signed, five classes, spec §2.2);
  - [x] class counts for core, exclusives, D-H, (D-H)-core, H-D, and outside every circuit;
  - [x] the positive control (layer-0 MLP) behaving as in v1;
  - [x] the S2p ranking (layer-0 MLP excluded) and the S3 ranking per task: top 20 with circuit membership, and the
        overlap of the three tasks' top-20 lists; S2 as descriptive.
- [x] **C1 and C-own** from the sweeps: the Components x 9 test sets matrix (item-swap; neutral twin and mean on D) as
      CSV and figure, rows grouped by composition set, R-cls class per Component per task. C-own sign tests with
      Holm and the per-head table. C-MLP reading.
- [x] **R-lens (exploratory, R12)**: honest-first rate per task on D and on the twin, FAR vs the act-naming subsets of
      SDR and SER per `docs/research/mechanism-analysis/clause-forms.csv`, CIs from a bootstrap clustered by
      `pressure_id`. Labelled exploratory everywhere it appears.
- [x] **1C.** Per task, on the selection sample: S7 on I and greedy selection over the S2p top 50 to k = 20. Groups
      files for both selectors over the k grid, each with 20 layer-matched null draws (fixed RNG seed recorded). On
      the held-out sample (seed 1, selection ids excluded): every candidate `S_k` and its nulls on D (neutral twin,
      post-clause); every `S_k` with k <= 20 on H and F (item-swap, all positions) and on I (neutral twin,
      post-clause); the routing groups (a), (b), (c) for each candidate's preliminary `C_t`; core, excl_t and
      (D_t - H_t) - core as named groups. Computing R-inv and routing for every candidate avoids a second pass once
      the deciding set is known.
- [x] R-AB per task: (i) and (ii) with their numbers and bootstrap CIs, the null distribution per k, the mediation
      curves of both selectors, the reading (A, A′ or B, checked in that order), the deciding set and its members with
      circuit membership. For B, the shared-class share of the top-80 S2p effect. The overall reading (shared by >= 2
      tasks, else mixed). An A′ reading lists the deciding set's heads for phase 3; it is settled only by the
      adjudication of spec §2.3.
- [x] R-inv per task (`f_I` vs `f_D`, CIs, the label), the S7 vs S2p comparison, and the routing shares (a)-(c).
- [x] C-v1 and C-confound readings.
- [x] Whether any headline claim rests on exclusive-head identities (R-own, C-reads, C-v1), stated for R5's decision
      on ticket 07.
- [x] `reports/03-phase1-results.md` (+ `.json`) with every table, generated by a script under
      `outputs/_launch_mechanism_analysis/` (name: builder). `reports/03-phase1-reading.md`: plain-language verdict,
      each prediction marked confirmed, refuted or inconclusive, the proposed MLP blocks for U (at most 10) and the
      deciding sets for `C_t`.
- [x] Curated copies (R6) under `docs/research/mechanism-analysis/phase1/`: the head tables as CSV, the readings JSON,
      the groups files. Handed to the orchestrator for commit.
- [x] Ledger `bridges2` reconciled with sacct after every wave, under the ledger lock. Results fetched after every
      wave.
- [x] No EVAL 5, no training, no path patching. Tests in both envs if code changed.
- [x] Review in `reports/03-review.md`; progress in `reports/03-handback.md`.

## Hand-back

The phase-1 reading, the R-AB and R-inv verdicts per task, and the R5 statement. The orchestrator posts the reading
to the user before phase 2's first GPU submission.

**Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if
the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user is
always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.

## Comments

### Orchestrator addition 2026-10-25 (R19(2), R19(3))
- Mean cells on the no-pressure side report BOTH banks (task bank, no-pressure bank); zero decides (R13).
- R-inv reading is PAIRED on D's held-out ids that survived I's filter: "instructed inversion machinery" when the
  paired bootstrap (clustered by pressure_id) 95% CI of f_I - 0.5 f_D lies above 0; "deception-specific" when the CI
  of 0.5 f_D - f_I lies above 0; otherwise "undecided". Replaces "CIs do not overlap".
