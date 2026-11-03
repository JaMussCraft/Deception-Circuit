# Resume: neuron-partition

Last rewritten: Tue 3 Nov 2026, 3:05 pm EST by claude-5201d56c, after a login-node reboot.

## Status

N1 is active. Done: the attribution scorer (reviewed, PASS WITH FIXES), the full and split-half FAR rankings at the
readout position, the partition under R6 (sets under `outputs/_analyses/neuron-partition/sets/far_atp_66741d7/`),
the N3 stability report (preliminary finding F1: every class stable), the neuron set-ablation machinery (reviewed,
PASS WITH FIXES; two majors being fixed), the seed-2 test sample (300 per condition), the verdict script, and the
first report draft with placeholders (`reports/05-first-report.md`). In progress after the reboot of about 2:30 pm EST (which killed the workers, not the Slurm jobs): the all-position ranking (Delta job 23478550, 482 s) is done and reconciled; job C (contrast k 1,000, Bridges-2 job 50182995, 2 h) is submitted; worker w5-sets builds the all-position and readout sets at c3d7763, syncs them to the clone and submits jobs A and B (4 h each); worker w6-babysit waits on all three, fetches the cells, runs the verdict script and writes the addenda to hand-back 02. Rulings R1 to R12 are in `spec.md`. The first report is due Wed 4
Nov 2026, 12:00 pm EST.

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

1. Read w5-sets' reply: commit its files (hand-backs 01 and 04 addenda) and confirm jobs A and B are in the
   ledger and job list; read w6-babysit's timing message and its per-job completion messages.
2. If a worker died (login-node reboot), find the live jobs with `squeue -u swong2` on bridges2 and the
   ledger, and respawn one Opus worker with the dead worker's brief; the outputs on the clone survive.
3. Fetch the cells, run `scripts/neuron_partition_verdict.py`, log the N1 and N2 decisions, fill the placeholders of
   `reports/05-first-report.md`, run `scripts/check_report_numbers.py`, hand back by Wed noon EST.

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
