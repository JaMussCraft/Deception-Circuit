# Hand-back r03: independent recomputation of the neuron-partition verdict (rev3)

Agent: independent reviewer, Opus. Ticket: the team lead's review request for session claude-5201d56c. Status:
resolved. Verdict CONFIRMED WITH NOTES. The review is
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reviews/03-verdict-review.md`.

## What changed

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reviews/03-verdict-review.md`,
  the review.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/r03-verdict-review-handback.md`,
  this hand-back.
- Scratch, not for commit:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review3_tmp/`
  holds `recompute.py`, `recompute.json`, `show.py`, `compare.py`, `explore.py`, `sumkeys.py`, `sum2.py` and
  `vkeys.py`.
- Nothing was staged for the apply tool. No repository code changed. Git, sbatch and GPUs were not used.

## How verified

The recomputation read only `rows.jsonl` and `summary.json` of the three cells. The verdict script was never
opened, and the verdict files were opened only after `recompute.json` existed.

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review3_tmp/recompute.py /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review3_tmp/recompute.json
```

Observed: `done 500`, `done 1000`, `done 2000`, exit 0. At size 500, D_only removes 0.8126 of the D margin effect
under twin and 0.7237 under mean. It removes 0.1452 and 0.1612 of the I effect. The IOI shift under mean is -6.0
points.

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review3_tmp/compare.py
```

Observed: every compared quantity is flagged `ok`. The worst differences are
`{'frac': 1.1102230246251565e-16, 'points': 0.0}`. The 20 null values per reference match exactly.

## Execution evidence

- Job id and cluster: local CPU commands on the Delta login node, the two shown above. No Slurm job.
- Exit code or Slurm state: 0 for both.
- Row counts: `rows.jsonl` has 369,600 lines in each of the three cells against 369,600 expected (84 sets x 4,400).
  Every reference, set and condition has 300 ids, and IOI has 100. There are no duplicates and no unpaired ids.
- Baseline reproduces: intact IOI accuracy is 0.51 against the ladder's 0.51. The intact margins are identical
  across the three cells on all 3,100 condition-id-stream keys, maximum difference 0.0.
- Provenance file: the `run_manifest.json` of each of the three cells, which all name commit
  `fe2db9e0d4736469aa180c6d89a18b5736710c20`. The IOI `sentences_sha256`
  `61ebeea317ac4932c0b859cc62b88ed0c45a7d6602d4866a9cf2373ee2cc5e59` is equal in all three `summary.json` files.

## What is NOT done

- The split halves (R10) were not recomputed. The half assignment lives in `scripts/neuron_partition_data.py`, and
  the half bar values were read from `verdict.json`.
- The self-replay error was not recomputed, because `rows.jsonl` holds no self-replay set. The 0.0 is
  `summary.json`'s claim. The twin pairing identity was recomputed instead.
- N2 (H_only) and the classes other than D_only were not recomputed. They were outside the request.
- The readout-position comparison cell and the job C contrast cell were not checked.

## Open questions

- Should the finding quote the zero reference's own collateral beside the mean-reference collateral? The
  verdict.md zero table shows only the mean collateral, and item 10 asks for disagreement among the references.
  Default: quote both in the finding.
- Should the IOI fail at 500 be written as a one-row fail that the 100-row sample cannot resolve? Default: yes, with
  the bar unchanged and N1 recorded as failed.
