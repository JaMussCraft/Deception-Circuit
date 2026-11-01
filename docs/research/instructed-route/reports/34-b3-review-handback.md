# Hand-back 34: independent review of the B3 premise result (review 06)

Agent: independent review agent (Claude Opus 5.5), session claude-230e4716, direction instructed-route. Brief: the
team lead's request to review the B3 alignment-faking premise verdict and hand-back 33, and to propose the FINDINGS
row. Status: resolved. CPU only: no Slurm job, no paid call, no git, no research-session command, no frozen file
touched.

## What changed

- The review is
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reviews/06-b3-premise-review.md`.
  It has the four requested headings and the proposed row F-rte-007.
- The recompute scripts and their logs are in
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/outputs/_studies/b3/premise/analysis/review06/`.
  The files are `review_recompute.py`, `review_recompute.log`, `review_extra.py` and `review_extra.log`.
- This hand-back. Nothing else under `docs/research/` changed, and FINDINGS.md was not edited.

**Verdict of the review.** I agree with the verdict, and it is a clean negative at the frozen bar. The judged gap is
7.0 points (3.9 to 10.2) against the bar of 10, on 100 queries, with P2 agreement 0.959. Every rule number and
secondary number recomputes exactly.

**Problems.** None blocks the verdict.

1. **Tier disclosure.** 435 of 2,000 sampled responses name the tier, RLHF or the contractors themselves, so the
   judge could infer the tier from them. Those rows are nearly all compliant in both tiers. This is a caveat for the
   row, and hand-back 33 omits it.
2. **Spend.** The ledgers settle at $2.22, not the $2.38 the label files sum to.
3. **Re-judge size.** The re-judge is 213 independent calls, not 220.
4. **J2 token file.** J2 ran under the seed token file. It is identical to G2, so nothing changes.
5. **One unchecked link.** I could not check whether `spec.md` held R6 and G2 at commit 476c187. Two git commands
   for the orchestrator are in the review.

## How verified

- **Own recompute.** I wrote it from the plan text, without importing `spontaneous.premise`, `proxy` or `rows`. It
  covers the gap, both bootstraps, P1 and P2 labels from my own token encoding, the calibration rule, the P2 margins
  from the stored stem log-probs, the C1 and C2 Δ values, the cap counts and the judge comparisons.
- **What the judge saw.** For all 3,080 judged main and calibration rows, I rebuilt the judge request from the query
  and response alone. Every key is in the main cache, and every cached text parses to the stored label.
- **Single runs.** The settled attempts in the ledgers equal the unique requests: 813, 1,839 and 213 on the main
  ledger, and 191 plus 3 errors on the cross-check ledger.
- **Frozen hashes.** G1 reproduces with `--print-hash`, and G2 with `sha256sum`. The manifests' own `created`
  fields put the G2 calibration run at 15:06:24 and J2's start at 15:21:35.

## Execution evidence

```
HF_HUB_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python outputs/_studies/b3/premise/analysis/review06/review_recompute.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python outputs/_studies/b3/premise/analysis/review06/review_extra.py
HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m spontaneous.judge --print-hash
sha256sum spontaneous/grader/proxy_tokens_g2.json
```

Observed: both scripts exited 0, and their full output is in the two logs. The hash printed is
`2e819a465b22504996c3421dc55e83f80903c016a550813c0f2f88cdc17bbf00`, and the G2 file hashes to
`2e4fd784092eedd16e9483ae985d68b2200a40a34c39f96e416ad53d1b673934`. Both match `spec.md`.

## What is NOT done

- **No git.** The `spec.md` content at 476c187 is unchecked; the commands are in review problem 5.
- **No lint.** I did not run `research-session lint` on the review or on this file, because the brief forbids
  research-session commands.
- **No FINDINGS edit.** The row is proposed text only.
- **No regeneration.** No row was regenerated, and no seed was re-derived.

## Open questions

1. **Spend note.** Should RESUME and the budget notes use the ledger total of $2.22? Default: yes.
2. **Adopting the row.** Should F-rte-007 be added as written, with the tier-disclosure caveat? Default: yes.
