# 06 — Synthesis: claims table, figures, limitations, records

**What to do:** turn phases 1-3 (and 07 if it ran) into a claims table and paper-ready figures. Mark every
pre-registered prediction of spec §2 as confirmed, refuted or inconclusive, with its numbers, and every exploratory
reading as exploratory. Write the synthesis under `docs/research/mechanism-analysis/` (R6). CPU only.

**Status:** resolved
**Type:** task
**Blocked by:** 05 (phase-3 reading posted per R9), and 07 if it runs (R5).
**GPU allocation:** 0. Figure reruns, if any, come from reconciled savings or the holdback with the orchestrator's
approval.

## Facts to build on

- `reports/03-*`, `04-*`, `05-*` (and `07-*`) readings and `.json` results; the curated copies under
  `docs/research/mechanism-analysis/phase{1,2,3}/`; spec §2 (rules), §7 (limitations), §9 (rulings).
- Headline rule (spec §2.1): R-AB decides outcome A's first half; RQ-B and RQ-C decide its second half. R-inv decides
  whether a mediating set is called deception-leaning or instructed-inversion machinery.
- Related work to position against, to be confirmed by a paper-reading agent before use:
  - "Interpretability of LLM Deception: Universal Motif" (2025), in `project_context/related_papers.md`;
  - Campbell et al. 2023, "Localizing Lying in Llama", instructed lying, heads and layers;
  - Halawi et al. 2023/2024, "Overthinking the Truth", honest-then-overridden lens trajectories.
  The latter two are not yet in `related_papers.md`.

## Acceptance criteria

- [x] `docs/research/mechanism-analysis/claims.md`: one row per claim, with: (kept in `synthesis.md` sections 2-3, as the lead's brief named it; one copy only)
  - the evidence (file and number);
  - the rule that decides it, or "exploratory";
  - the verdict;
  - the scope (task, seed, ablation, sample);
  - the limitation that qualifies it (spec §7 item).
  The headline (outcome A, A′ with its sub-reading, B, or mixed) is stated first, with R-inv's label.
- [ ] Figures (PNG + the JSON that draws them), under `docs/research/mechanism-analysis/figures/`:
  - the cross-task knockout matrix;
  - the **mediation curve**: k in {1, 2, 3, 5, 10, 20, 40, 80} vs `f_D` and deceptive accuracy, both selectors, with
    the 20-draw null band and bootstrap CIs, per task, and `f_I` for the deciding set;
  - lens trajectories per task (exploratory, clustered CIs);
  - the exclusives' layer bands and reads;
  - the A′ adjudication / selector-mover diagram per task.
- [x] Limitations section from spec §7, updated with anything phases 1-3 found, including the one-sentence
      statement of which thresholds are calibrated and which are conventions (R17).
- [x] A list of follow-ups the user may want, each costed. Not started.
- [x] A file list for the orchestrator: everything under `docs/research/mechanism-analysis/` to commit, and the
      `outputs/_analyses/mechanism-analysis-*` cells to move to the main checkout's `outputs/_analyses/` before the
      worktree is removed (R16).
- [x] Review in `reports/06-review.md`, by an independent reader given the code and outputs, not this reading.

## Hand-back

The claims table and figures, for the user. Merging the branch to main is the user's call.

**Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if
the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user is
always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.

## Comments

**impl-06, 2026-10-26: resolved.** Full hand-back in `reports/06-handback.md`; reviews and dispositions in
`reports/06-review.md`.

- Commit (paths relative to the worktree): `docs/research/mechanism-analysis/synthesis.md`;
  `docs/research/mechanism-analysis/figures/figures.py`, `figures_meta.json`, `fig1_mediation` ... `fig9_lens` (9 CSV +
  9 PNG); `tests/test_mechanism_analysis_figures.py`.
- The claims table lives in synthesis.md section 2 (no separate claims.md, per the lead's brief).
- The Figures box stays unticked: the lens figure's band is the per-instance SE, not clustered by pressure_id, because
  the lens cells hold no per-instance trajectories (synthesis L7, section 6). Figures ship as PNG + CSV, not JSON.
- R30 applied: every far / ser R-inv statement carries "below the 300-id minimum; FAR polarity-confounded,
  inversion-polarity subset agrees"; sdr has no R-inv verdict.
- Tests: figure tests 14 passed in mgnp and base. Full suite, base: the 8 baseline failures, 2203 passed, 66 skipped.
  Full suite, mgnp: 8 failed = the 8 names of `00-baseline-failures.md`; 2400 passed, 19 skipped (1647 s). The run started before the R30 caption edits to figures.py; the figure tests were rerun after the last figures.py write, 14 passed in both envs.
- No GPU jobs; `compute-ledger.json` unchanged.
