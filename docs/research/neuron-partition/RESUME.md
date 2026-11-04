# Resume: neuron-partition

Last rewritten: Tue 3 Nov 2026, 9:45 pm EST by claude-5201d56c, after the confirmation test.

## Status

Two decisions stand side by side. R13: on the original ladder, N1 FAILED at every set size under the frozen bars
(the size-500 class missed only the IOI bar on 100 rows) and N2 is UNDETERMINED. R14: a pre-registered
confirmation test of that fixed size-500 all-position deception-only class (338 neurons, layers 0 to 9) on fresh
ids (208 D, 166 I) and 1,000 fresh IOI rows met every N1 bar under twin and mean on the whole sample and both
halves: 0.82 and 0.75 of the deception effect removed, 0.14 to 0.15 of inversion, H and F at zero shift, IOI minus
2.7 points, 35 times the null 95th percentile. Findings F1 to F6 are in `WORKLOG.md`; F3, F4 and F6 are reviewed
(reviews 03 and 04). The report is `reports/05-first-report.md` (final, both decisions and the confirmation
section). Every GPU job is reconciled: 15.83 of 20 GPU-hours reserved, about 10.3 used. The optional N2 fresh-data
cell (honest-only at size 2,000) was not run (no H200 available); its sets file is
`outputs/_analyses/neuron-partition/ablation/confirm_h_only_k2000_sets.json`.

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

1. The user decides: release the direction as done, or pause it for a follow-up (candidates: the N2 fresh-data
   cell above, about 40 min on an A40; SER; the one-neuron interchange check of review 01; a finer size ladder
   around 500 with a 1,000-row IOI bar, each needing its own pre-registration).
2. After the Wed 4 Nov 2026 8:00 am EST reset, the user reverts `CAP_PERCENT` to 80 in
   `/projects/beto/swong2/Alignment/.agents/research_session/usage.py`.
3. Before Bridges-2 goes offline (about Sun 9 Nov 2026): copy the clone's `logs/` entries for jobs 50182995,
   50183187 and 50183194 under the primary checkout on Delta, so the evidence blocks stay traceable.
4. Wrap-up when the user says so: merge the branch into main, delete branch and worktree, keep the worktree's
   untracked outputs under the primary checkout, copy the Bridges-2 outputs and logs to Delta.

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
