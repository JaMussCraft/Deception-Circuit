# Ticket 06 hand-back (impl-06, Opus, 2026-10-26)

Status: resolved. The R22 vs R23 decision was ruled by the orchestrator as R30 and is applied. Progress is
appended below as it happened; the final sections are at the end.

## Plan

1. Figures first: `docs/research/mechanism-analysis/figures/figures.py` (extract stage writes one CSV per figure from
   the curated tables and named reports; render stage draws each PNG from its CSV only), tests in
   `tests/test_mechanism_analysis_figures.py` (data layer, both envs).
2. `docs/research/mechanism-analysis/synthesis.md`: headline, claims table, narrative, limitations, follow-ups, records.
3. Two Opus reviewers (numbers; rules and exploratory labels), dispositions in `reports/06-review.md`.
4. Full suites in both envs (background), then this hand-back's final section and the ticket's Comments.

## Progress

- 2026-10-26: orientation done (brief, spec §2/§4/§7/§9 R0-R29, ticket, phase readings and results, reviews,
  inversion-control note, RESUME tail, ledger). Usage 5% (5-hour) / 9% (weekly).
- Seams tested (no user to confirm them with; chosen from the ticket and the lead's brief): each figure's extract
  function against values printed in the phase readings, the committed CSVs against a fresh extraction, the meta
  file, and render-from-CSV. 14 tests, green in mgnp and base.
- Figures built: 9 PNG + 9 CSV + figures_meta.json under docs/research/mechanism-analysis/figures/. Palette: Okabe-Ito
  picks, checked with the dataviz validator (CVD and normal-vision separation pass; grey reserved for nulls / "none").
- Cross-env determinism: Python 3.12's sum() is compensated, so float sums differed by one ulp from py3.9; the builder
  uses math.fsum, and both envs now write byte-identical CSVs.
- Lens CIs: the fetched lens cells keep only per-row mean and SE, no per-instance trajectories, so Figure 9's band is
  per-instance SE, not clustered by pressure_id (stated in the caption, synthesis L7, and as a follow-up).
- synthesis.md written. Ungraded predictions now graded from the rule: R-A1's exclusives no-pressure prediction
  (refuted: sdr 0.215, ser 0.184 under zero) and the roll-up of outcome A's second half.
- Full suites launched in the background (both envs); two Opus reviewers spawned (numbers; spec rules / labels).
- Reviews in (`06-review.md`): numbers 1 mismatch + 11 citation / wording fixes; spec 1 blocker (R22 vs R23), 10
  should-fix, 4 nits. All fixed in synthesis.md except the blocker, which is qualified in the text and raised below.
  H11 (outcome A's second half) moved from "not supported" to "inconclusive" (C-MLP's refutation is a sign of a
  difference). Per-instance f ratios (spec 2.3, R11(i)) added to the Figure 1 CSV and quoted in H2-H4.
- mgnp full suite restarted with a longer timeout: another agent's mgnp suite was running on the same login node and
  mine would have hit its 50-minute limit at about 20 %.
- Lead relayed both reviews with ruling R30 (R23 supersedes R22's last sentence). Applied: the headline, the
  one-sentence summary, H8, H10, the narrative, L6 and Figure 2's caption and title carry "below the 300-id minimum;
  FAR polarity-confounded, inversion-polarity subset agrees"; H9 reads "no R-inv verdict"; Figure 2 labels sdr's rows
  "descriptive"; the reconciliation follow-up row removed. Every other finding re-checked as applied. Figures rebuilt;
  figure tests 14 passed in both envs.

## Decision for the orchestrator (resolved by R30)

**R22 vs R23 (spec reviewer's blocker).** R22: "The 300-id minimum still applies per task; a task that still fails it
has no I contrast and says so in §7." I keeps FAR 210 and SER 249 ids. R23 then drew the paired R-inv sample from those
pools ("the FAR and SER pools are 210 and 249 rows") without amending R22, and phase 1 reported the far and ser labels.
synthesis.md keeps the labels as run under R23 and flags them everywhere (headline, H8, H10, L6, section 6). Options:

- (a) a dated ruling that R23 supersedes R22's sentence for R-inv (then cite it in synthesis.md);
- (b) far and ser have no I contrast; R-inv is reported for sdr only (descriptive, since sdr is B), and the headline
  loses its R-inv label;
- (c) the costed follow-up: rebuild I for FAR and SER above 300 ids and rerun R-inv (about 1 H100 GPU-h, before
  Bridges-2 goes offline).

Recommendation: (a), plus (c) if time allows. R23 was a dated ruling that named the pool sizes, so the contrast was
meant to run on them. **Outcome:** the orchestrator ruled (a) as R30 on 2026-10-26; (c) stays in synthesis section 6.

## Comments (final)

**Built and run.** CPU only, 0 GPU-h. `figures/figures.py` (extract and render stages, 9 figures), 9 CSV + 9 PNG +
`figures_meta.json`, `synthesis.md` (headline, claims table, descriptive / exploratory table, narrative, limitations
L1-L25, costed follow-ups, records), 14 tests, two Opus reviews with dispositions.

**Commit file list** (relative to the worktree):

```
docs/research/mechanism-analysis/synthesis.md
docs/research/mechanism-analysis/figures/figures.py
docs/research/mechanism-analysis/figures/figures_meta.json
docs/research/mechanism-analysis/figures/fig1_mediation.csv
docs/research/mechanism-analysis/figures/fig1_mediation.png
docs/research/mechanism-analysis/figures/fig2_rinv.csv
docs/research/mechanism-analysis/figures/fig2_rinv.png
docs/research/mechanism-analysis/figures/fig3_b2_by_layer.csv
docs/research/mechanism-analysis/figures/fig3_b2_by_layer.png
docs/research/mechanism-analysis/figures/fig4_a_prime.csv
docs/research/mechanism-analysis/figures/fig4_a_prime.png
docs/research/mechanism-analysis/figures/fig5_entry_paths.csv
docs/research/mechanism-analysis/figures/fig5_entry_paths.png
docs/research/mechanism-analysis/figures/fig6_route.csv
docs/research/mechanism-analysis/figures/fig6_route.png
docs/research/mechanism-analysis/figures/fig7_c1_matrix.csv
docs/research/mechanism-analysis/figures/fig7_c1_matrix.png
docs/research/mechanism-analysis/figures/fig8_exclusives.csv
docs/research/mechanism-analysis/figures/fig8_exclusives.png
docs/research/mechanism-analysis/figures/fig9_lens.csv
docs/research/mechanism-analysis/figures/fig9_lens.png
tests/test_mechanism_analysis_figures.py
```

Working record (not in the repo): `reports/06-handback.md`, `reports/06-review.md`, and the ticket file.

**Cells to move before the worktree is removed** (git-ignored, under the worktree's `outputs/_analyses/`):
`mechanism-analysis-02a-drift-kosweep`, `-02a-smoke-clause`, `-02a-smoke-dla`, `-02a-smoke-groups`,
`-02a-smoke-mean`, `-02a-smoke-readout`, `-02a-smoke-s2p`, `-02a-smoke-timings`, `-02a-smoke-zero`,
`-02b-smoke-timings`, `-02b-smoke-twin`, `-p1` (227 MB), `-p2` (345 MB), `-p3` (40 MB). Also untracked but NOT ignored,
so they are lost with the worktree unless moved or committed: `outputs/_suites/mechanism-analysis/` (62 MB; the
phase-1A evaluator cells named by `phase1a/p1a_cells.csv`), `outputs/_suites/mechanism-v2-coarse.b2local-261025/`
(66 MB) and `outputs/_launch_mechanism_analysis/eval_jobs.txt`.

**Tests.** `tests/test_mechanism_analysis_figures.py`: 14 passed in mgnp and in base. Full suite, base: 8 failed = the
8 baseline names of `00-baseline-failures.md`, 2203 passed, 66 skipped (1871 s). Full suite, mgnp: 8 failed = the 8 names of `00-baseline-failures.md`; 2400 passed, 19 skipped (1647 s). The run started before the R30 caption edits to figures.py; the figure tests were rerun after the last figures.py write, 14 passed in both envs.

**Jobs, ledger.** None; ledger unchanged (Bridges-2 20.5 booked of 35; Delta 0).

**Not done, and why.**
- Ticket box "Figures": all built, but the lens CIs are not clustered by pressure_id. The fetched lens cells hold only
  per-row means and SEs, no per-instance trajectories. Left unticked; costed in synthesis section 6.
- `claims.md`: the lead's brief put the claims table in `synthesis.md`; one copy is kept there to avoid drift.
- Related-work positioning: the ticket requires a paper-reading agent to confirm each paper first; the lead's
  deliverables omit it. Listed as a follow-up.
- `/code-review` skill: replaced by the two Opus reviews of the synthesis and a by-hand two-axis review of the builder,
  to keep usage down (`06-review.md`).

**Open questions for the researcher.** Whether to spend part of the remaining 14.5 H100
GPU-h on held-out path patching of the A′ sets or on an I rebuild before Bridges-2 goes offline (synthesis section 6).

**Review outcome.** No unresolved finding; the one blocker (R22 vs R23) was resolved by R30 and applied.
