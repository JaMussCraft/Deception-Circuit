# Resume: neuron-partition

Last rewritten: Tue 3 Nov 2026, 12:50 pm EST by claude-5201d56c.

## Status

N1 is active: the attribution-patching scorer is committed and reviewed-in-progress, and the full FAR ranking
(job 23476096, 400 D/H and 354 I/N rows, forward and reverse) is done under
`outputs/_analyses/neuron-partition/attribution/far_v2_{dh,in}_train+validation_7386fd3{,_rev}/`. Rulings R2 to R6
in `spec.md` fix the effect measure (ladder margin effect primary), the mean-bank splits, the IOI adapter, the
assessment-id file and the partition rule. N2 and N3 wait on N1's classes. No finding has been recorded. First
look, descriptive: the D/H and I/N maps correlate at 0.78 and most strong D neurons are strong I neurons. The first report is due Wed 4 Nov 2026,
12:00 pm EST, with whatever N1 has produced.

## Branch, worktree and commit

- Branch: `neuron-partition`.
- Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition`.
- Last commit on the branch: see `git log -1`; the branch starts from main at `7a020a9` (claim rendered).
- Tool-owned records (state, worklog, ledger, hook-saved hand-backs) live in the main checkout at
  `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/neuron-partition/`; everything else is on the branch.
- Uncommitted work, if any: none.

## In-flight jobs

None. Reservations r-001 (pilot, 89 s) and r-002 (full ranking, 252 s) are reconciled; 1.25 of 20 GPU-hours reserved.

## Next action

1. Collect the hand-backs of W2 (neuron ablation under twin, mean and zero; `scripts/neuron_set_ablation.py`),
   W3 (seed-2 test sample at `outputs/_analyses/neuron-partition/data/`, nulls, Bridges-2 sync), W4 (partition
   sets per R6 at `outputs/_analyses/neuron-partition/partition/`) and the scorer review (`reviews/01`); commit by
   file list.
2. Submit the ablation cells (every class at k 500, 1,000, 2,000 with 20 matched nulls, three references, conditions
   D/H/F/I/N and IOI) as one job: Bridges-2 H100 charged to cis260372p if `--test-only` starts sooner, else a Delta
   interactive partition in 55-minute chunks.
3. W1's split-half ranking job for N3; then the N1 verdict against item 10, the N2 cell on the H-only set, and the
   first report by Wed noon EST.

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
