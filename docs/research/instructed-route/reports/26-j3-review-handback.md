# Hand-back 26: independent review of the B3 sycophancy positive control J3

Agent: review-J3 (Opus), session claude-230e4716. Brief: the orchestrator's review request for Slurm job 23412270.
Status: resolved. The verdict is pass with caveats.

## What changed

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reviews/03-j3-review.md`
  is new. It has the four headings the brief asked for: Verdict, Checks, Problems found and Proposed finding text.
- This hand-back is also new. I wrote it because the session's stop hook requires one. The orchestrator's brief asked
  for the review file only.

No other file changed. Nothing is staged, and I ran no git command.

## How verified

I ran the CPU checks with `/u/swong2/.conda/envs/mgnp/bin/python` and the BLAS threads set to 1. The scripts were
in the job tmp directory, and their essential lines are quoted in the review.

- I recomputed kept items, flips, reversal shares, f, the bootstrap CI and the null maxima from `margins.json`
  without importing `spontaneous`. Each value equals the stored one: 800, 530 and 154 items; 73 of 154 reversed
  (0.474); a null maximum of 0.084; and f 0.3399 with CI 0.3242 to 0.3553.
- I ran `sha256sum` on the data and code files. Every value equals its manifest entry, including
  `data/b3/syc_items.json` at `4a9e5e5a…`.
- I checked all 100 null draws for layer matching and for overlap with their set.
- I measured near ties, drift between the two passes, collateral effects on kept items that did not flip, and the
  uncued twin's accuracy and pull toward the cue letter.

## Execution evidence

Not applicable. I submitted no job, and the CPU reads changed no file under `outputs/`.

## What is NOT done

- I did not redo the 800-item selection from the MMLU parquet, because the download is not committed.
- I verified the Gupta head list against the project's deep read, not the arXiv text itself.
- I did not run the `knockout.py` parity check. It needs a GPU, and the brief excluded Slurm.
- I did not recompute the f over flips. Its stored value is 0.4546.

## Open questions

- **Should the null draws exclude the set's own members before J4?** The review's problem 1 explains why this
  matters. Default: the pre-registered procedure stays unchanged, and the orchestrator decides.
- **Should the parity check run before J4?** Default: recommended, at about 0.13 h.
- **Is the review's proposed row text acceptable for FINDINGS?** It changes "neutral twin" to "uncued twin" and
  gives the null maximum. Default: use the review's text.
