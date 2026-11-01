# Hand-back 35: independent review of J4, the B3 transfer test on sycophancy alone

Agent: the J4 reviewer (Opus), session claude-230e4716, direction instructed-route. Brief: the team lead's request to
review Slurm job 23415595 and propose the F-rte-008 row. Status: resolved for the deciding arm. The supplement (job
23416459: heads_only, S_far, S_ser) had not finished when this was written, so its section of the review is pending.
CPU only. I ran no Slurm job, no git, no research-session command, and touched no frozen file.

## What changed

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reviews/07-j4-review.md`
  is the review. Its headings are Verdict, Checks, Problems found and Proposed finding text.
- This hand-back.

The scripts and logs below are in the job tmp directory. They are outside the repository and are not for committing:

- `/u/swong2/.claude/jobs/230e4716/tmp/j4rev_recompute.py` and its `.log`
- `/u/swong2/.claude/jobs/230e4716/tmp/j4rev_span.py` and its `.log`
- `/u/swong2/.claude/jobs/230e4716/tmp/j4rev_supp.py`, prepared for the supplement but not yet run

Nothing else under `docs/research/` changed.

## How verified

The recompute was run like this:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -I \
  /u/swong2/.claude/jobs/230e4716/tmp/j4rev_recompute.py
```

It imports no project code. It reproduces every f, CI, f over flips, reversal share and null maximum to four
decimals. It re-draws all 200 null draws with its own port of the draw loop, and they match exactly. It confirms there
are 0 head-member overlaps and that MLP members are kept for S_all. It also confirms that pass 1, the pass-2 clean
and uncued margins, and every shared readout arm are bit-identical to J3.

The span check (`j4rev_span.py`) rebuilds the 800 twins with the cached tokenizer:

- the differing window is 7 tokens;
- the post_tag span is 30 positions on every item;
- all items use one neutral sentence.

`sha256sum` on the seven code files and two data files equals every manifest entry.

## Execution evidence

Not applicable: this hand-back covers a review, and the run under review is job 23415595. The parity check (job
23415522) agreed exactly, with a difference of 0.0 on both arms.

## What is NOT done

- **The supplement is not reviewed.** It was still running. `j4rev_supp.py` reads it, checks the draws and pass-1
  identity, and prints f, CI, reversal, non-flip damage and null statistics for heads_only, S_far and S_ser. Section 6
  of the review says how to read each outcome.
- **No arm patches only the positions after the cue window.** Problem 2 of the review proposes one as a follow-up. It
  is not required by R11.

## Open questions

1. **Should the R11 verdict be written into a readings file?** `syc_results` does not compute a transfer verdict, so
   the "shared, non-specific" label exists only in the orchestrator's reading. My default is that the finding row
   states it explicitly.
2. **Is a post-cue-window arm wanted?** It would separate carrying the cue forward from reading the cue tokens, at
   about 0.2 A100 hours. Patching code for that span does not exist yet.
