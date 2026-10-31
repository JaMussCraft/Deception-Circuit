# 02b — Neutral twin in attention patterns and path patching, the A′ receiver category, and the v2 criteria amendment

**What to do:** add the paired Neutral-Clause Twin to attention patterns and path patching, so phase 2 can read the
pressure-reader signature (B2) and phase 3 can adjudicate A′ (spec §2.3, R11(g)). Write and apply the v2 amendment of
`docs/component-roles.md` (R1, R7, R10) before any v2 roles pass. Blocks phase 2, not phase 1.

**Status:** resolved
**Type:** task
**Blocked by:** 02a (the `neutral_twin` paired kind and v2 segmentation). The amendment is applied only after the
orchestrator confirms it has reported the text to the user (R10).
**GPU allocation:** 0.5 H100 GPU-h on Bridges-2 (one smoke job). Delta: 0 without the orchestrator's approval.

## Facts to build on

- 02a's `neutral_twin` paired kind (D or I as the pressure stream, `<t>_v2_honest` as the twin, D's labels).
- Counterfactual plumbing to mirror: `path_patching.py:128-139,191,504` (`COUNTERFACTUALS`, `COLUMN_SUFFIX`,
  `INSTANCE_SETS`, `counterfactual_pair`), `attention_patterns.py:154-164`, `head_table.py:70-72`. K and V receivers
  are per KV group (`path_patching.py:41`).
- Path patching freezes every Component of the model, not only the grid (`path_patching.py:463`, `:593`; review
  §0). Every position before the clause is identical in D and its twin, so no neutral-twin path can originate
  there.
- `docs/component-roles.md`: the roles (binder, selector, mover, suppressor, unknown), the reserved "pressure
  reader", the path floor 0.01, `--path-position-threshold` default 0.05, and the "Changing these criteria" section
  with its dated change log. Every amendment so far is "the researcher's decision"; this one is an orchestrator
  ruling under the user's standing go, reported to the user first (R10).
- Rulings: R1 (twin is the v2 counterfactual; pressure reader un-reserved for v2 cells only, v1 keeps it reserved),
  R7 (neutral-twin columns in rule 4; `response_line` in the `frame` group), R10.

## Acceptance criteria

- [x] Attention patterns: the `neutral_twin` paired condition, with `_neutral_twin_paired` columns and coverage meta,
      and the B2 signature per head: Readout-query mass on `pressure_clause` under D minus under the twin, with its
      paired SE.
- [x] Path patching: `neutral_twin` as a counterfactual (`--path-counterfactual neutral_twin` and `both`), with
      `_neutral_twin_paired` columns, and the position-specific pass reporting sender positions by Segment.
- [x] Receiver category per head (spec §2.3): from the neutral-twin path outputs, the strongest incoming path above
      0.01 classified as Q / K-V from the clause span / K-V from post-clause positions / none above the floor, with
      its effect and SE. Unit-tested on synthetic path tables, including a K-V tie inside one KV group.
- [x] v1 cells are byte-identical before and after (snapshot test of a v1 attention and path-patching head table).
- [x] Login `--dry-run` of the phase-2 cells (spec §4) and of the phase-3 path grids for the provisional `C_t`
      (core | excl_t | ((D_t - H_t) - core), plus 10 placeholder MLPs) prints grid sizes and cost; recorded in the
      hand-back.
- [x] **Criteria amendment.** `reports/02b-criteria-amendment.md` holds the exact text: the neutral-twin columns in
      rule 4 (the v2 query-side clause reads `path_patching.strongest_incoming_neutral_twin_paired`), the
      `response_line` Segment in `frame`, and the pressure-reader criteria for v2 cells. Starting proposal, to adapt to
      the doc's metric names and precedence:
  - the B2 signature (mass on `pressure_clause` falls under the twin by >= 0.05 and >= 2 SE, paired);
  - a significant post-clause neutral-twin knockout drop in the deceptive direction (the 1B sweep S2p);
  - where path patching exists for the cell, the strongest neutral-twin incoming path is K or V from the clause span;
    without path data the role is marked "attention and knockout only".
  After the orchestrator's go, the same text goes into `docs/component-roles.md` as a dated amendment with its change
  log entry, before any v2 roles pass.
- [x] Bridges-2 smoke: one GPU job runs a tiny v2 cell (`--n-causal 8`) with attention patterns and path patching
      under the twin on a small grid. Elapsed time per path forward recorded as the phase-3 cost basis.
- [x] Both envs: full suites, failures compared by name with `reports/00-baseline-failures.md`.
- [x] Ledger `bridges2` reconciled. Review in `reports/02b-review.md`; progress in `reports/02b-handback.md`.

## Hand-back

The file list to commit (with `docs/component-roles.md` once amended), tests per env, the smoke numbers, the dry-run
grid sizes, and the amendment text for the orchestrator to report to the user.

**Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if
the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user is
always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.

## Comments

- 2026-10-25 (impl-02b) — Code complete in the worktree (branch mechanism-analysis, base ddd1da4): attention
  `neutral_twin` paired condition + B2 column `attention_patterns.clause_mass_drop_neutral_twin_paired` (+ `_se`);
  path patching `neutral_twin` (`--path-counterfactual neutral_twin|both`, `both` = item_swap + neutral_twin on v2
  tasks and unchanged on v1) with the Segment-resolved pass; `component_analysis/receiver_category.py`
  (q / kv_clause / kv_post_clause / kv_unresolved / none, floor 0.01, `analyze_components.py receiver-category`),
  written by the twin pass as `path_patching.receiver_category_neutral_twin*`; roles v2 variant (rule 4 and rule 6
  read the twin's columns on a v2 cell; rule 4b pressure reader, `--roles-b2-floor` 0.05; `response_line` -> frame);
  v1 snapshot test `tests/test_v1_snapshot_02b.py` byte-identical. Dry-run tables in
  `reports/02b-dryrun-tables.md` and the hand-back. Amendment text in `reports/02b-criteria-amendment.md`
  (= `02b-amendment-draft.md`), sent to the orchestrator; `docs/component-roles.md` untouched until the R10 go.
  Base-env full suite: the 8 baseline names only (2115 passed). Smoke, mgnp suite, ledger and review follow.
- 2026-10-26 (impl-02b) — Resolved. Amendment applied to `docs/component-roles.md` and CONTEXT.md under R25 (d134ea48),
  with the review fixes (twin-only `--path-twin-position-threshold`, `TwinPassSkipped`, tie-break aligned with
  `strongest_incoming`, `--path-category-floor`, v2 console tally, rerun hint, vocabulary); R27 (83599b5): v2 writes
  and differential clauses read `dla.differential_neutral_twin_paired`. Smoke job 49841165 PASS (twin attention,
  twin path and receiver-category columns present on all 15 heads; 2.6 % of cells selected at 0.01; steady-state
  path forward 0.036 s, Segment forward 0.039 s, model load 585 s on the H100); ledger reconciled (0.3536 GPU-h
  actual, 0.5 booked). Both-env full suites = the 8 baseline names only. Review in `reports/02b-review.md`,
  record in `reports/02b-handback.md`, cost table in `reports/02b-dryrun-tables.md`.
