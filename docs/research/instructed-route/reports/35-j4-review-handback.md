# Hand-back 35: independent review of J4, the B3 transfer test on sycophancy alone

Agent: the J4 reviewer (Opus), session claude-230e4716, direction instructed-route. Brief: the team lead's request to
review Slurm job 23415595 and propose the F-rte-008 row, then to fold in the supplement, job 23416459. Status:
resolved, with both runs reviewed. CPU only. I ran no Slurm job, no git, no research-session command, and touched no
frozen file.

The verdict is confirmed: shared, non-specific under R5 as R11 applies it. f_syc(S_all) at post_tag is 0.724 (0.702
to 0.746), and the largest null draw is 0.505.

The supplement shows that both the qualifier and the band rest on mlp.5 to mlp.7:

- S_all's 32 heads alone give 0.498 (0.470 to 0.526) against a heads-only null maximum of 0.271.
- S_far gives 0.393 against a null maximum of 0.276.
- S_ser gives 0.197, and 3 of its 20 null draws exceed it (maximum 0.586).

## What changed

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reviews/07-j4-review.md`
  is the review. Its headings are Verdict, Checks, Problems found and Proposed finding text. Check 6 now covers the
  supplement, and the finding text includes its numbers.
- This hand-back.

The scripts and logs below are in the job tmp directory. They are outside the repository and are not for committing:

- `/u/swong2/.claude/jobs/230e4716/tmp/j4rev_recompute.py`, `j4rev_span.py`, `j4rev_supp.py` and `j4rev_supp2.py`,
  each with its `.log`
- `j4rev_tail.md` and `j4rev_splice.py`, the helpers that rewrote the finding section

Nothing else under `docs/research/` changed.

## How verified

Every script was run like this:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -I <script>
```

- **Recompute.** It imports no project code. In both runs it reproduces every f, CI, reversal share and null maximum
  to four decimals.
- **Null draws.** The 320 recorded draws (200 in J4, 120 in the supplement) match my own port of the draw loop
  exactly. No draw holds a head member of its own set, and every draw keeps its set's MLP members, as R10a requires.
- **Identity across runs.** Pass 1 and the pass-2 clean and uncued margins are identical across J3, J4 and the
  supplement.
- **Span.** The span check rebuilds the 800 twins with the cached tokenizer. The differing window is 7 tokens, the
  post_tag span is 30 positions and one neutral sentence is used throughout.
- **Hashes.** `sha256sum` equals every code and dataset hash in both manifests. The commits are 21bc397 and c32627e,
  both clean.
- **Line length.** No line in the review is over 120 characters.

## Execution evidence

Not applicable: this hand-back covers a review. The runs under review are jobs 23415595 and 23416459. The parity check
(job 23415522) agreed exactly, with a difference of 0.0 on both arms.

## What is NOT done

- **No arm patches only the positions after the cue window.** Problem 2 of the review proposes one as a follow-up, at
  about 0.2 A100 hours. The supplement makes it more pressing, because the shared band rests on early MLPs at the cue
  tokens. R11 does not require it, and the patching code does not exist yet.
- **No MLP-only arm exists.** The MLP contribution (0.226) is inferred as S_all minus its heads.

## Open questions

1. **Should the R11 verdict be written into a readings file?** `syc_results` does not compute one. My default is that
   the finding row states it, as the proposed text does.
2. **Is the post-cue-window arm wanted before B3 closes?** It would decide whether the early MLPs that carry the band
   act as token substitution.
