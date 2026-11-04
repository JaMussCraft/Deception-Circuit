# Hand-back r08: independent recomputation of the one-neuron interchange check (review 08)

Agent: independent reviewer R8 (Claude Opus). Ticket: the team lead's R8 brief of Wed 4 Nov 2026 ("Review 08:
recompute one-neuron check"). Status: resolved. Verdict CONFIRMED WITH CORRECTIONS. Written Wed 4 Nov 2026, 12:50
pm EST.

## What changed

Nothing is staged for the apply tool. No tracked code changed.

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reviews/08-one-neuron-recompute.md`,
  the review with its verdict line, the comparison table, three corrections and the commands.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/r08-review-handback.md`,
  this hand-back.
- Git-ignored scratch, not to commit:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r8_tmp/`
  holds `recompute.py`, `compare2.py`, `compare.py` (an unused first draft) and the output `recompute.json`.

## How verified

```
OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python outputs/_analyses/neuron-partition/r8_tmp/recompute.py
```

Observed: 24,000 rows (twin D 12,000, twin H 12,000). All 40 groups have 300 D and 300 H rows whose ids equal the
seed-2 sample's lists. The sets equal the top 20 by s_D and by s_H of the all-position ranking. Sign agreement is
40 of 40 on D and 39 of 40 on H. Spearman is 0.92943 on D and 0.99756 on H over 40 groups, and 0.93848 and 0.99665
over the 36 distinct neurons. The 4 duplicate pairs are identical row by row. The largest D removed is 0.0524.

```
/u/swong2/.conda/envs/mgnp/bin/python outputs/_analyses/neuron-partition/r8_tmp/compare2.py
```

Observed: the worst per-group difference from `one_neuron_report.json` is 0.0 in all ten columns, and the summary
differences are at most 4.4e-16. Six of the 40 neurons are in the size-500 D-only class, including the three largest
measured effects (L8, L0 and L9).

```
/u/swong2/.local/bin/research-session lint docs/research/neuron-partition/reviews/08-one-neuron-recompute.md
```

Observed: exit 0, no output.

## Execution evidence

Not applicable: no runs. All checks were CPU recomputations on the Delta login node from the existing cell
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/ablation/one_neuron-92fc6fb/`.
That cell's manifest names Slurm job 23520193 and commit `800c9037c22c54256a049a4615b4f06f00493f46`. The
recomputation matches the claimed numbers, as the review records.

## What is NOT done

- The reserved time of 1,447 s of 2,700 was not checked against Slurm accounting. `summary.json` gives 1,426 s of
  script wall time, which is consistent.
- W9's report script was neither read nor run, by design. Its definitions were taken from hand-back 10.
- R21 was not edited. The corrected wording is in the review for the orchestrator to apply.

## Open questions

1. **Amend R21?** The layer sentence is wrong, and the "faithful predictor" sentence needs the within-list
   qualification. Default: amend R21 with the review's suggested wording, as R18 and R19 were amended after
   reviews 05 and 06.
2. **Hand-back 10's count.** It says 9 of the top 20 by s_H have negative s_D, and the count is 8. Default: leave
   the hand-back as written, since review 08 records the correct count and nothing downstream uses it.
