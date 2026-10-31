# 05 — Phase 3: path patching on the candidate sets, the A′ adjudication, selector vs mover, where the pressure enters

**What to do:** run the path-patching grids of spec §4 phase 3 on the candidate circuits `C_t` (never the union),
under the item-swap and neutral-twin counterfactuals. Add the position-specific pass and the neutral-twin path
completeness sweep. Adjudicate every A′ reading by the exhaustive categories of spec §2.3, read B-selector and B4,
and rerun the roles pass.

**Status:** resolved
**Type:** task
**Blocked by:** 04 (phase-2 reading posted per R9).
**GPU allocation:** 9.25 H100 GPU-h on Bridges-2 (3 jobs + 1 rerun). Delta fallback with the orchestrator's approval,
H200 only (R16). The full 32-MLP grid of R14 is outside this allocation.

## Facts to build on

- `component_analysis/path_patching.py` (grid definition `:1-60`; cost `:426-435`; counterfactuals `:128-139`; K and
  V receivers per KV group `:41`). Path patching freezes every Component of the model, not only the grid (`:463`,
  `:593`). Thresholds and floors: `docs/component-roles.md` (path floor 0.01; `--path-position-threshold` default
  0.05). Cross-card noise is about 0.005 (A40 vs A100), so read nothing inside 0.01.
- `C_t` (spec §4): core | excl_t | ((D_t - H_t) - core) | the heads of the deciding `S_k` | at most 10 MLP blocks.
  Sizes and `--dry-run` cost from `reports/04-phase2-reading.md`. Budget a grid only after its dry-run estimate is in
  the ledger entry.
- The routing shares (a)-(c) per task from `reports/03-phase1-reading.md`. R14: the full 32-MLP grid runs only for a
  task whose share (c) exceeds 0.25, and only after the user approves the cap raise (about +2.75 reserve per task).
- 02b's receiver-category function and the amended criteria.
- v1 precedent: the SDR D&H-core grids were deferred at about 40 min for both on an H200 (memory
  `dh-core-component-analysis`). v1's selector call hinged on one cell at 0.0068 (`docs/component-roles.md`,
  2026-09-20 amendment). L17H24-27 share one KV group (spec §7).

## Acceptance criteria

- [x] Per task: both grids, the position-specific pass, and the neutral-twin path completeness sweep, completed and
      fetched to Delta under `outputs/_analyses/mechanism-analysis-p3/`, run into the phase-2 D cell or a copy of it
      (builder; carry-forward rules in `analyze_components.py`).
- [x] **A′ adjudication** for every task read A′: per head of the deciding set, the category (Q / K-V clause span /
      K-V post-clause / none above the floor) with effect and SE; MLP members listed and counted; the weighted
      majority call and the sub-reading (A′-selector, A′-clause-reader, A′-mover, A′-unresolved, A′-mixed). A′-mover
      and A′-unresolved only if routing share (c) <= 0.25; otherwise "A′, route outside `C_t`", handed back for R14.
- [x] B-selector: the category of L17H24-27 and of the core's L24 heads per task (K/V for the L17 heads counted as
      one test). Per-receiver totals (Q vs K+V sum) as a descriptive column; the strongest single receiver is not
      dominance (roles doc).
- [x] Where the pressure enters: the senders whose neutral-twin paths into the candidates clear the floor, with their
      Segment-resolved positions (clause span or post-clause). Compared across the three tasks.
- [x] Completeness: the share of the neutral-twin gap carried by non-candidate direct paths, per task.
- [x] Roles rerun on every phase-3 cell; role counts per task; a cross-task role comparison table (C3).
- [x] `reports/05-phase3-results.md` (+ `.json`) and `reports/05-phase3-reading.md`.
- [x] Curated copies (R6) under `docs/research/mechanism-analysis/phase3/`: head tables as CSV, `roles.json`,
      readings JSON. Handed to the orchestrator for commit.
- [x] Ledger reconciled under the lock; results fetched; review in `reports/05-review.md`; progress in
      `reports/05-handback.md`.

## Hand-back

The phase-3 reading and the A′ sub-readings. The orchestrator posts the reading to the user before synthesis.

**Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if
the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user is
always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.

## Comments

**2026-10-26, impl-05 (resolved, pending commit).**

- Ran: Bridges-2 jobs 49896838 / 49896843 / 49896848 (far / sdr / ser; 02:19 / 01:51 / 02:38, exit 0), fetched to
  `outputs/_analyses/mechanism-analysis-p3/`. Ledger: 8.5 GPU-h reserved, 7.25 charged of 9.25, no rerun; bridges2 0
  in flight.
- Box 1 wording: the grids ran into fresh C_t cells (`d` for the neutral twin with the Segment pass at 0.01, the
  receiver categories and the completeness sweep; `d_is` for the item swap), not into the phase-2 D cell. The reasons:
  `carry_forward` replaces a whole analysis namespace, so two path-patching counterfactuals need two cells, and C_t
  is not U'. The phase-2 D views and phase-1 knockout columns reach the roles pass through restricted merge tables
  (`p3_merge.py`), which add no row.
- Readings (`reports/05-phase3-reading.md`): far and ser **A′-clause-reader** (0.74, 0.83). sdr is read B, so it gets
  no sub-reading; its shape is Q-dominated (0.64, mixed at a 0.02 floor). B-selector: clause 1 holds on all tasks,
  clause 2 fails on all, so it is refuted. B4: K/V weight is mostly on the clause span on far and ser and 44 %
  post-clause on sdr. Completeness: 0.80 / 0.81 / 0.77 of the twin gap on direct paths from outside C_t (late writers
  at the Readout; a different position set from 1C's routing (c)). Roles: pressure readers 16 / 4 / 5, all
  kv_clause; L17H24 a selector on all three tasks.
- For the researcher: sdr qualifies formally under R14 ((c) 0.297); the recommendation is not to run the 32-MLP grid.
- Review: `reports/05-review.md`. Spec findings 1-10 all fixed. Standards findings fixed except 7 (`receiver_category`
  sample count vs coverage when the gap excludes instances; 0 excluded in phase 3, so no delivered number is
  affected; follow-up for 02b's module) and 13 (helper duplication across launch modules), both deferred.
- Tests: `tests/test_mechanism_analysis_p3.py` + `tests/test_receiver_category.py` 60 passed in mgnp and base. The
  full suites ran on the a8a9b63 code: base 8 failed / 2173 passed, mgnp 8 failed / 2370 passed, the 8 baseline names
  in both. The post-review edits touch only the p3 launch modules and their test file, which were rerun green in both
  environments.
- Files to commit are listed in `reports/05-handback.md` (Progress 6).
