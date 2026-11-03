# Hand-back 08: independent review of the D1 follow-up (pointer)

Agent: Opus reviewer (claude-opus-5-5), direction deception-divergence. Ticket: the lead's brief of Mon 2 Nov 2026,
an independent review of the D1 follow-up under ruling R6. Status: resolved. The review itself is
`docs/research/deception-divergence/reviews/03-d1-followup-review.md`, and this file only points to it.

## What changed

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reviews/03-d1-followup-review.md`
  is new.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/08-handback.md`
  is this file.

No code, output, state or worklog file was touched. My scratch scripts are outside the repository, in
`/u/swong2/.claude/jobs/5b9b1c28/tmp/d1furev/`.

## How verified

```
/u/swong2/.local/bin/research-session lint docs/research/deception-divergence/reviews/03-d1-followup-review.md
```

Observed: no output, exit 0.

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_d1_followup.py
```

Observed: `15 passed in 22.85s`.

My recompute imports no project code, apart from the per-id token-length count. Every reported count and point
estimate reproduced. Across 54 comparisons, the intervals agree within 0.3 points.

## Results

- **R6 (i) and (ii).** Phrasing 4 is null on every task, on both the full pool and the content pool. Supported.
- **R6 (iii).** The flip pools for phrasings 1 and 4 are empty on every task. Supported with caveats. R6 (iv) applies.
- **Cross-job control.** The control is bit for bit on 1,000 anchors per task.
- **Recommendation.** Mark F6 and F7 reviewed, with the wording corrections of issues 1, 3 and 5 in the review.
  - **Issue 1.** F7's "does not exist at the first token" overclaims.
  - **Issue 3.** The visible arm complies more, which is the wrong sign for listener-conditioned deception.
  - **Issue 5.** F6's "not a change of answer" is too broad, and F6 mixes denominators.

## Execution evidence

No job ran. The review read the outputs of Bridges-2 jobs 50145353 and 50152632. Their hashes match the manifests.

## What is NOT done

- **Base interpreter.** I did not run the base-interpreter tests.
- **Slurm accounting.** I did not query Slurm for job 50152632's wall time or state.
- **Read stage.** I did not rerun the `read` stage, because it would overwrite the outputs under review.

## Open questions

- **Finding wording.** Should the F6 and F7 register entries take the suggested wording before they are marked
  reviewed? Default: yes, as the review's Recommendation gives it.
