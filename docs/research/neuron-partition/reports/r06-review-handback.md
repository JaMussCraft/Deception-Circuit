# Hand-back r06: independent recomputation of the finer size ladder (review 06)

Agent: independent reviewer R6 (Claude Opus). Ticket: the team lead's R6 brief of Wed 4 Nov 2026 ("Review 06:
recompute ladder"), which checks ruling R19 of
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/spec.md`.
Status: resolved. Verdict: CONFIRMED WITH CORRECTIONS. Every number of R19 and `verdict.md` matches. The N1 pass holds
at sizes 250, 375, 625 and 750 under twin and mean, on the whole sample and both halves. One sentence of R19 needs a
fix. Written Wed 4 Nov 2026, about 12:21 pm EST.

## What changed

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reviews/06-ladder-recompute.md`,
  the review.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/r06-review-handback.md`,
  this file.
- Untracked scratch, not for commit:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r6_tmp/`.
  It holds the scripts `schema.py`, `summ.py`, `probe.py`, `recompute.py`, `sets_check.py`, `provenance.py`,
  `abs_paths.py` and `compare.py`, and the outputs `recompute.json` and `sets_check.json`.
- Nothing is staged for the apply tool. No code, spec or ruling was edited.

## How verified

The review lists every command with its observed lines. The key ones follow.

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r6_tmp/recompute.py
```

Observed: "rows 227136", halves D 104 and 104, I 78 and 88, 24 cells each "pass True", and "N1 verdict per k {250:
True, 375: True, 625: True, 750: True}".

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r6_tmp/compare.py
```

Observed: "compared 1128 worst fraction diff 1.1102230246251565e-16 worst point diff 0.0", "flags [] 0". This ran
after `recompute.json` was saved.

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r6_tmp/sets_check.py
```

Observed: the R6 rebuild gives D-only classes of 152, 243, 424 and 524 neurons, equal to `ladder_sets.json` and the
sets directory. At 500 it gives 338, equal to F6's class. The 20 nulls at each size match size and layer histogram,
are disjoint from the class and are distinct.

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r6_tmp/provenance.py
```

Observed: the sample and IOI ids equal the R14 cell's. The intact margins are identical across all 84 sets. The IOI
shift at 250 is 33 lost and 6 gained, and the R14 class at 500 is 38 lost and 11 gained. Both nets are -2.7.

```
/u/swong2/.local/bin/research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reviews/06-ladder-recompute.md
```

Observed: no output, exit 0.

## Execution evidence

- Job id and cluster: no Slurm job. These were local CPU scripts on the Delta login node, run with
  `/u/swong2/.conda/envs/mgnp/bin/python`. The commands are above.
- Exit code or Slurm state: 0 for every script.
- Row counts: 227,136 rows in `ladder-92fc6fb/rows.jsonl`, against 227,136 expected. That is 84 sets of 2,704 rows,
  with no duplicate key.
- Baseline reproduces: the intact IOI accuracy is 0.511, against 0.511 in `summary.json` and 0.510 in the ladder
  reference. My D removed at size 250 under twin is 0.8126458, against 0.8126458 in `verdict.json`.
- Provenance file:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/ablation/ladder-92fc6fb/run_manifest.json`,
  commit `d5f6b1750e5b5a770d48b5c44cd4cb2c688236c6`.

## What is NOT done

- The bootstrap intervals of `verdict.md` were not reproduced.
- The Slurm elapsed time of 3,041 s was not checked, because the job ran on Bridges-2. `summary.json` gives 2,786 s
  of script wall time.
- The self-replay error and the twin cross-check were read from `summary.json`. They cannot be recomputed from the
  rows.
- R19 was not edited. The correction is for the orchestrator to apply.

## Open questions

1. **R19's trend sentence.** "The deception effect flat and the inversion cost rising with size" holds under twin
   only. Under mean, D removed rises from 0.69 to 0.78 and I removed is not monotone. Default: amend R19 or note it
   in F8 with the wording suggested in review 06, correction 1.
2. **The bar that fails first.** No bar fails between 250 and 750. The closest is I removed under twin, 0.217 of 0.25
   at 750, or 0.223 on half 1. On the secondary rate measure it is 0.256, already over 0.25. Default: F8 names the
   inversion cost as the first bar to fail as the size grows, and says the ladder does not bound the specific size
   above 750.
3. **The class's own IOI cost.** At sizes 250, 375 and 625 the class's IOI shift lies below every one of its 20
   nulls, though it stays under the 5-point bar. Default: report it descriptively in F8.
