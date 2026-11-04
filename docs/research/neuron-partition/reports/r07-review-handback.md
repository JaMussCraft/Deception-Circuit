# Hand-back r07: review 07, independent recomputation of the SER k-500 cell

Agent: independent reviewer R7 (Claude Opus). Ticket: the team lead's review-07 brief of Wed 4 Nov 2026 ("recompute
SER cell"), against ruling R20 and finding F9 in `docs/research/neuron-partition/spec.md`. Status: resolved. Written
Wed 4 Nov 2026, about 12:46 pm EST.

## What changed

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reviews/07-ser-recompute.md`,
  the review. Its verdict is CONFIRMED WITH CORRECTIONS.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/r07-review-handback.md`,
  this file.
- Staged: nothing.
- Scratch, git-ignored, under
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r7_tmp/`.
  It holds the scripts `recompute.py`, `sets_check.py`, `provenance.py`, `excl.py`, `compare.py`, `collateral.py`,
  `polarity.py` and `strict_argmax.py`, the peeks, and the output `recompute.json`.

## How verified

Each command is listed with its observed output in the review's Commands section. The key ones:

```
HF_DATASETS_OFFLINE=1 OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r7_tmp/recompute.py
```

Observed: "rows 310800 dups 0", halves D 146 and 154 and I 144 and 156, D_only failing H and F only in all six cells,
N2 "suppression or shared" on all six, "IOI intact acc 0.511".

```
HF_DATASETS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/r7_tmp/compare.py
```

Observed: "compared 2640 worst fraction diff 2.220446049250313e-16 worst point diff 1.4210854715202004e-14", "flags
[] 0", "D_only N1 bar flags equal 36 of 36".

```
/u/swong2/.local/bin/research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reviews/07-ser-recompute.md
```

Observed: no output, exit 0.

## Execution evidence

- Job id and cluster: none. Local CPU commands on the Delta login node with the mgnp interpreter, listed above and in
  the review.
- Exit code or Slurm state: every script exited 0.
- Row counts: `rows.jsonl` holds 310,800 rows against the 310,800 derived from the schema, 84 × (4 × 300 twin + 5 ×
  300 mean + 1,000 IOI).
- Baseline reproduces: intact IOI argmax accuracy is 0.511 from the rows, against 0.511 in `summary.json` and the
  ladder's 0.51.
- Provenance file:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/ablation/ser_predicate_k500-d5f6b17/run_manifest.json`,
  commit `d5f6b1750e5b5a770d48b5c44cd4cb2c688236c6`.

## What is NOT done

- **Bootstrap intervals** in `verdict.md` were not reproduced.
- **The Slurm elapsed time** of 3,572 s was not checked, because the job ran on Bridges-2.
- **The polarity reading is descriptive.** The H and F loss of the deception-only class sits in "identity" rows. The
  reading that the class partly carries "pick the item named as favorable" is untested.
- **R20 and F9 were not edited.** The correction is proposed in the review for the team lead to apply.
- **F9 was checked through its restatements.** It was checked against `RESUME.md` and follow-up C of report 13. The
  `worklog.json` entry itself is readable only through the research-session tool. Every F9 number in those two
  places matches.

## Open questions

1. **R20's "rate 1.0".** It should read 0.998 under twin and 1.05 under mean, the latter above 1 because the
   ablated H rows turn deceptive. Default: the team lead amends R20 with the review's suggested wording.
2. **The polarity concentration.** Should F9 mention it? 94 of 95 lost H pairs and all 38 lost F pairs are identity
   rows. Default: one descriptive sentence in F9, with no new bar.
3. **The brief's row formula.** It is not a finding about the cell: twin has four conditions and IOI runs under mean
   only, which gives 310,800. Default: no action.
