# Hand-back r04: independent recomputation of the R14 confirmation cell

Agent: reviewer rev4, Claude Opus, read-only. Ticket: the team lead's review brief of Tue 3 Nov 2026 ("Independent
recompute of the confirmation cell"), under ruling R14 of
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/spec.md`.
Status: resolved. Review verdict: CONFIRMED WITH NOTES.

## What changed

For the orchestrator to commit from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reviews/04-confirmation-review.md`,
  the review: verdict line, recomputed table beside the verdict, bar checks, sanity checks, notes and commands.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/r04-confirmation-review-handback.md`,
  this file.

Scratch, git-ignored, not for commit:
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review4_tmp/`.
It holds `recompute.py`, `sanity.py`, `ioi_check.py`, `sets_check.py`, `ioi_paired.py`, `inside_effect.py`,
`compare.py` and `diff.py`, with outputs `recompute.json`, `ioi_check.json` and `ioi_conditions.json`. Nothing is
staged for the apply tool.

## How verified

My numbers were computed and saved before any verdict file or hand-back 08 was opened. The verdict script was never
read.

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review4_tmp/recompute.py
```

Observed: "rows 56784 dups 0" and "ALL BARS PASS True". The whole-sample values are below.

| reference | D removed | I removed | null p95 of D removed | H / F / IOI shift, points |
|---|---|---|---|---|
| twin | 0.822 | 0.141 | 0.013 | (R7: read under mean) |
| mean | 0.748 | 0.154 | 0.021 | 0.0 / 0.0 / -2.7 |

Both halves pass every bar under both references. D removed is at least 0.744 and I removed at most 0.160.

```
PYTHONHASHSEED=0 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review4_tmp/ioi_check.py
```

Observed: seed 2 regenerates sha256 `906a93ed…` and seed 1 regenerates `fec3aa49…`, each with 1,000 rows. There
are 0 shared sentences.

```
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/review4_tmp/diff.py
```

Observed: "compared 188 worst fraction diff 0.0 worst point diff 0.0", and the pass flags agree in all six cells.

```
sha256sum <WT>/scripts/neuron_partition_data.py <WT>/tests/test_neuron_partition_data.py <WT>/scripts/neuron_set_ablation.py
```

Observed: `83a45e7e…` and `631dd1c0…`, which are the prefixes hand-back 08 names. The ablation script gives
`b4efbd59…`, the same as the manifest's `code_sha256`.

`sanity.py` and `sets_check.py` gave 0 overlap with seed 2 and with the 792 excluded ids. They found no unpaired
rows. All 71 manifest dataset hashes re-verified. All 21 sets equal the k500 source and the nulls are layer-matched.
The full commands and outputs are in the review.

## Execution evidence

- **Job id and cluster.** Local CPU commands on the Delta login node, listed above and in the review. The cell
  itself is Delta job 23494260, which W8 ran.
- **Exit code.** 0 for every script.
- **Row counts.** `rows.jsonl` has 56,784 lines against 56,784 expected. The 1,000 IOI rows match a fresh
  regeneration.
- **Baseline reproduces.** Intact IOI argmax accuracy is 0.513 against the ladder's 0.51. Intact D, H, F, I and N
  accuracy is 1.0.
- **Provenance file.**
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/ablation/confirm_k500-d3d842b/run_manifest.json`,
  commit `d3d842b886971e196d0f7df139e2d32a1dc22a97`, `git_dirty` false.

## What is NOT done

- **The optional H_only cell.** It was not run, so it was not reviewed.
- **The bootstrap intervals.** The verdict's bootstrap intervals were not recomputed. R14 reads the point estimate.
- **The script hashes against the commit.** The worktree files were hashed, but it was not shown that commit d3d842b
  holds exactly these versions. That needs version control, which this review may not run. The session-start status
  showed only hand-back 08 as untracked, which is consistent with a match.

## Open questions

1. **I removed under the inside-the-model reading.** Under mean, I removed is 0.230 by that reading, close to the
   0.25 bar. Should the finding report this beside R2's 0.154? Default: yes, as a descriptive line. R2 decides, so
   the verdict does not change.
2. **The IOI cost.** It is -2.7 points, McNemar p 0.00014, outside the null range. Should the finding headline it
   beside the pass? Default: yes, as a measured, small collateral cost under the bar, as hand-back 08 proposes.
