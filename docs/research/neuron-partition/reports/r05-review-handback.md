# Hand-back r05: independent recomputation of the N2 fresh-data cell

Agent: reviewer R5, Claude Opus, read-only. Ticket: the team lead's review brief of Wed 4 Nov 2026 ("Review 05:
recompute N2 cell"), under rulings R14, R15 (a) and R18 of
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/spec.md`.
Status: resolved. Review verdict: CONFIRMED.

## What changed

For the orchestrator to commit from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reviews/05-n2-fresh-data-recompute.md`,
  the review: verdict line, recomputed numbers beside the claims, the N2 rule table, sanity checks, notes and
  commands.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/r05-review-handback.md`,
  this file.

Scratch, not for commit:
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/`.
It holds `schema.py`, `peek_files.py`, `sets_peek.py`, `recompute.py`, `details.py`, `null_rate.py`,
`numeric_order.py`, `d_argmax.py`, `sanity.py`, `sets_check.py` and `compare.py`, with the output `recompute.json`.
Nothing is staged for the apply tool.

## How verified

My numbers were saved before `verdict.json` was opened. The verdict script was never read. I had read `verdict.md`
and R18 first, because the brief names them as the claim.

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/recompute.py
```

Observed: "rows 56784 dups 0" and halves of 104 and 104 for D and 78 and 88 for I. The N2 label is "suppression or
shared" in all six reference and subset cells. The mean reference gives the values below.

| subset | H shift, points | D deceptive-rate change, points | null p95 of absolute H shift |
|---|---|---|---|
| whole | -21.9 | -12.7 | 0.0 |
| half 1 | -21.6 | -10.6 | 0.0 |
| half 2 | -22.1 | -14.9 | 0.0 |

D removed by margin is -0.639 under mean and -0.528 under twin. F shifts -19.2 and IOI -2.4 points.

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/compare.py
```

Observed: 420 quantities compared, a worst fraction difference of 5.6e-17 and a worst point difference of 7.1e-15,
and an empty flag list.

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r5_tmp/null_rate.py
```

Observed: "mean|whole H_only D rate change -12.74 | null p5 -25.43 median -9.74 p95 -1.85 | nulls <= -10: 10/20 |
nulls <= H_only: 9/20".

`sanity.py` and `sets_check.py` gave 0 overlap with the seed-2 sample, the ranking ids and the 792 excluded ids.
Intact IOI accuracy is 0.513. The H_only set has 1,623 neurons, equals the k 2,000 file of `far_atp_all_c3d7763`,
and rebuilds from rule R6. All 20 nulls are layer-matched. All 71 manifest dataset hashes re-verify. The review
lists every command.

```
/u/swong2/.local/bin/research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reviews/05-n2-fresh-data-recompute.md
```

Observed: no output, exit 0.

## Execution evidence

- **Job id and cluster.** Local CPU commands on the Delta login node, listed above and in the review. The cell
  itself is Delta job 23519165, which runner R1 ran.
- **Exit code.** 0 for every script. `sacct` shows the cell's job COMPLETED in 2,480 s on gpub007.
- **Row counts.** `rows.jsonl` has 56,784 lines against 56,784 expected, with no duplicate key.
- **Baseline reproduces.** Intact IOI argmax accuracy is 0.513 against the ladder's 0.51. Intact D, H, F, I and N
  accuracy is 1.0.
- **Provenance file.**
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/ablation/confirm_h_only_k2000-3486f1a/run_manifest.json`,
  commit `d5f6b1750e5b5a770d48b5c44cd4cb2c688236c6`, `git_dirty` false.

## What is NOT done

- **Bootstrap intervals.** The verdict's bootstrap intervals were not recomputed. N2 reads the point estimate.
- **Self-replay error.** It was read from `summary.json` (0.0), not recomputed. It needs a GPU forward pass.
- **The commit label.** It was not shown that `3486f1a` and `d5f6b17` hold the same five code files, because that
  needs version control. The files hash identically to the R14 cell's manifest and to the worktree now.
- **IOI regeneration.** The IOI sentences were not regenerated. The rows equal those of the R14 cell, which review 04
  regenerated and checked against the seed-1 draw.

## Open questions

1. **The D-rate clause and the null.** Under mean, 9 of 20 matched random sets lower D's deceptive rate at least as
   much as the class. Should F7 say so beside the label? Default: yes, as "suppression or shared by the item 10 rule;
   the D-rate fall is not distinguishable from the matched null, the H fall is".
2. **The R16 to R18 timestamps.** They are about an hour later than the clock. Default: the orchestrator corrects them
   in a dated note, since the frozen text is not edited.
3. **The preliminary tag.** Default: lift it from the N2 outcome now that this recomputation matches, with question 1
   attached.
