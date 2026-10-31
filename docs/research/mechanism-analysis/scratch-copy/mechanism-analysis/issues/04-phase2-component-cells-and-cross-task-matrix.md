# 04 — Phase 2: Component cells on the union circuit (D, H, F, I), what the heads read and write, and roles

**What to do:** run phase 2 of spec §4. Per task, four cells (D, H, F, I) on the union circuit U with attention
patterns and DLA under pressure and paired with the twin, the family knockouts, and the segment-resolved neutral-twin
knockout of the top 20. Run the roles pass. Read the result against C-reads, C-honest, B-reader and RQ-A's component
part. The cross-task knockout matrix and C-own come from phase 1 (ticket 03, R16); no single-Component knockout pass
runs here.

**Status:** resolved
**Type:** task
**Blocked by:** 03 (phase-1 reading posted per R9) and 02b (the criteria amendment applied, R10).
**GPU allocation:** 3.5 H100 GPU-h on Bridges-2 (3 jobs + 0.5 rerun). Delta fallback with the orchestrator's approval,
H200 only (R16).

## Facts to build on

- Spec §2 and §4 (phase 2). Phase-1 reading (`reports/03-phase1-reading.md`) for the MLP blocks to add to U (at most
  10), the S2p top-20 lists and the R-cls classes.
- Cell of record to mirror for shape, write-up and checks: `outputs/_analyses/sdr-dh-core/dh_core__leaf/sdr/`
  `result_summary.md` (main checkout).
- Composition at **leaf** granularity: U = `(D_far | D_sdr | D_ser | H_far | H_sdr | H_ser) - m`, plus the flagged MLP
  blocks (operand: builder; ticket 03 wrote the heads-only U operand).
- `--reference NAME=RUN_DIR` binds atomic run dirs only (`component_analysis/intake.py:88-98`, `:129`). Bind the six
  atomic circuits as references. Derive the membership columns for core, excl_t, D_t - H_t and (D_t - H_t) - core
  from them on CPU.
- On H and F cells the knockout sign means "supports the honest answer". The DLA metric text is fixed and says
  "deceptive", so the write-up states the sign per cell, as the v1 honest cell did.
- Knockout groups for the family pass (JSON format of 02a): core, excl_t, D_t - H_t, (D_t - H_t) - core, H_t - D_t,
  and the late H-D heads (layers 18, 22, 30).
- Segment-resolved neutral-twin knockout (R16): every Segment before the clause reads exactly zero by construction.
  It is a sanity assertion, never a finding. The informative Segments are the clause, the post-clause question, the
  item and response-line mentions, the stem and the Readout.
- Pressure-reader role and B2 signature: the amended `docs/component-roles.md` (02b).

## Acceptance criteria

- [x] 12 cells per spec §4 completed, fetched to Delta under `outputs/_analyses/mechanism-analysis-p2/`.
      `scripts/check_cell.py` shows no BROKEN view.
- [x] Segment-resolved neutral-twin knockout of the S2p top 20 on D: the informative Segments as results, the
      pre-clause Segments asserted zero (a non-zero value is a bug, handed back).
- [x] C-reads: top-Segment group counts per exclusive set; Fisher test; per-head reads with masses.
- [x] B-reader: B2-signature heads per task with layers, the L8-17 share against 10/32 by a one-sided binomial test,
      and L13H5, L13H20, L13H21.
- [x] C-honest: the late H-D heads' DLA under pressure vs the paired twin.
- [x] The I cells: the B2 signature and the paired DLA on I vs on D, per head of the R-AB deciding sets
      (descriptive, feeds R-inv's discussion).
- [x] Roles pass on every cell under the amended criteria (ruling recorded). Role counts per task, with flavours of
      `unknown`. Family knockouts per set and task.
- [x] `reports/04-phase2-results.md` (+ `.json`) and `reports/04-phase2-reading.md`. The reading proposes `C_t` per
      task (spec §4 phase 3) with sizes and `--dry-run` cost.
- [x] Curated copies (R6) under `docs/research/mechanism-analysis/phase2/`: head tables as CSV, `roles.json`, readings
      JSON. Handed to the orchestrator for commit.
- [x] Ledger reconciled under the lock; results fetched; review in `reports/04-review.md`; progress in
      `reports/04-handback.md`.

## Hand-back

The phase-2 reading and the proposed `C_t`. The orchestrator posts the reading to the user before phase 3's first
GPU submission.

**Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if
the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user is
always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.

## Comments

**2026-10-26, impl-04 then impl-04o (resolved).**

- Built and run: U' operands per task (R26), family and top-20 groups, three job files (23 lines each), Bridges-2
  jobs 49876003 / 49876005 / 49876008 (far / sdr / ser, 35-38 min, exit 0), fetched to
  `outputs/_analyses/mechanism-analysis-p2/`; sweep-built merge tables and 12 roles passes (R27 criteria,
  `--roles-allow-missing-views`); `p2_results.py` -> `reports/04-phase2-results.{md,json}`; reading
  `reports/04-phase2-reading.md` with the C_t proposal (72 / 66 / 78 Components) and the phase-3 dry-run cost.
- Files to commit (worktree-relative): `outputs/_launch_mechanism_analysis/p2_{jobs,merge,results,roles}.py`,
  `tests/test_mechanism_analysis_p2.py`, `docs/research/mechanism-analysis/phase2/{families.csv,segments.csv,
  p2_readings.json}`, `docs/research/mechanism-analysis/phase2/{far,sdr,ser}_{d,h,f,i}_head_table.csv`,
  `docs/research/mechanism-analysis/phase2/roles/{far,sdr,ser}_{d,h,f,i}.json`. (Operands, groups, job files and the
  first builders were committed in a9545ed / a0fae76.)
- Tests: ticket file 27 passed in mgnp and base. Full suites: base (impl-04) 8 failed = the 8 baseline names, 2147
  passed; mgnp (impl-04o) 8 failed = the 8 baseline names (compared by name), 2347 passed, 19 skipped (1420 s); started before the last p2_results edits, after which the ticket file was rerun green in both envs.
- Jobs: Bridges-2 49876003, 49876005, 49876008, all COMPLETED. Ledger: 2.25 GPU-h booked (1.83 actual) of 3.5;
  bridges2 reconciled 13.25 GPU-h / 26.5 SU, 0 in flight.
- Review: both reviewers' findings (a)-(l) fixed; impl-04o's own review fixed a re-adjudication of phase-1 verdicts
  in the first reading, a stale reading, a redundant exploratory table and a relative-path bug
  (`reports/04-review.md`). Nothing unresolved.
- For the researcher: (1) C-honest's "suppressed, not absent" gloss does not hold: every reduced late H-D head flips
  sign under pressure. (2) C-reads has almost no power on the faithful table (20 of 32 exclusive heads read the
  attention sink). (3) ser's phase-3 walltime at x1.5 (about 3.25 h) exceeds the spec's 2.75 h per-task reserve;
  the three tasks together fit the 9.25 GPU-h allocation.
