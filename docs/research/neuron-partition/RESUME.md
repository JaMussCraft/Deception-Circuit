# Resume: neuron-partition

Last rewritten: Tue 3 Nov 2026, 8:40 pm EST by claude-5201d56c, after the ablation cells.

## Status

Item 10 is decided (ruling R13): N1 FAILED at every set size under the frozen bars and N2 is UNDETERMINED. Findings
F1 to F5 are in `WORKLOG.md` (F3 and F4 confirmed by review 03). The near miss: the all-position deception-only
class at size 500 (338 neurons, layers 0 to 9) removes 0.81 of the deception margin under the twin interchange
and 0.72 under mean, 0.15 of the inversion margin, leaves H and F unmoved, and failed only the IOI bar (minus 6.0 on
100 rows); an exploratory 1,000-row IOI measurement (F5) puts that cost at 3.7 points, under the bar and outside
the null band. It is a descriptive lead, not a pass. The first report is `reports/05-first-report.md` (review 03
folded in; the 1,000-row IOI result being folded in at 8:40 pm EST), due Wed 4 Nov 2026, 12:00 pm EST. Every
GPU job is reconciled: 14.83 of 20 GPU-hours reserved, about 9.5 used.

## Branch, worktree and commit

- Branch: `neuron-partition`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition`.
- Last commit on the branch: see `git log -1`; the branch starts from main at `7a020a9` (claim rendered).
- Tool-owned records (state, worklog, ledger, hook-saved hand-backs) live in the main checkout at
  `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition/`; everything else is on the branch.
- Uncommitted work, if any: none.

## In-flight jobs

Reservations r-001 to r-003 (ranking pilot, full ranking, split halves; 89, 252 and 259 s) are reconciled r-004 (ablation pilot, 679 s) and r-005 (all-position ranking, 482 s) are reconciled; r-006 is job C (2 h). 4.75 of 20 GPU-hours reserved before jobs A and B (8 h more).

## Next action

1. Morning of Wed 4 Nov: confirm hand-back 02's IOI addendum and the report's IOI fold-in are committed (if not,
   write them from `outputs/_analyses/neuron-partition/ablation/ioi_resolution-delta-e8dd8a8/summary.json` and
   finding F5); run `research-session lint` and `scripts/check_report_numbers.py` on the report; push.
2. Ask the user to revert `CAP_PERCENT` to 80 in `/projects/beto/swong2/Alignment/.agents/research_session/usage.py`
   after the 8:00 am EST reset, and to note the cadence (26) for the record.
3. Hand the report to the user; the advisor meeting decides whether the size-500 lead gets a pre-registered
   follow-up (a 1,000-row IOI bar, SER, the one-neuron interchange check of review 01). No further GPU work is
   planned in this session.

## Do not

- Do not redo the head-level D/H partition (F-comp-001), the head-level cross-task tests (F-mech-005, F-mech-008),
  the layer-17 residual probe (F-rte-004), or any residual-stream direction.
- Do not use the item-swap corrupt prompt as the neuron ablation reference (near no-op by construction).
- Do not use SAE or transcoder features, top-activating lists without ablation, raw Jaccard without ceiling and floor,
  or thresholds tuned on the evaluation ids.
- Do not read or import code from `.claude/worktrees/specificity-ladder/`, write there, or touch its Slurm jobs
  (23472894, 23474289 and later). Read its user-turn pools only, by path, and record sha256.
- Do not record a verdict in the Codex A3 cell (down-projection-input neurons at MLP layers 5 to 8 and 11, readout
  position only, D-minus-I gap over H standard deviation, top 1 percent per layer, A1's 100 assessment ids).
- Do not use A1's 100 assessment ids or the mechanism-analysis held-out samples for ranking or ablation.
- Paused directions (sdr-mechanism, selective-deception, mechanism-datasets, deception-divergence) stay paused.

## Open decisions for the user

- Cadence: START says 24 points; only the user can set it with the research-session cadence command; the default
  16 is in force until then.
