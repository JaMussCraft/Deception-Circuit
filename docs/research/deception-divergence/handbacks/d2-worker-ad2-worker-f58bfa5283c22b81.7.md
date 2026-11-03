# Last message of d2-worker ad2-worker-f58bfa5283c22b81 (2026-11-02T22:04:49-05:00)

The D2 premise job (Bridges-2 job 50155519) finished cleanly in 42 minutes, about 0.7 GPU-hours. On the classifier arm, only SDR passes the pre-registered rule. No task has a final verdict until the paid judge runs, which is the lead's to run.

**Run checks.**
- All 24 files the job wrote match between Bridges-2 and here by checksum. Every row count equals the dry-run table.
- Rerunning the read stage on the login node reproduces the job's numbers.
- The cached path was compared with the full path on 8 rows per task, for the record only. The largest differences were FAR 0.25, SDR 0.37 and SER 0.38 logits. On SDR, 2 of the 8 rows changed their first reply token, which supports making the full path the path of record.
- The refusal-direction control is valid: ablating it takes the harmful refusal share from 1.0 to 0.0.

**Classifier arm.** The gap is between the D and I rates. A task separates when the gap is at least 0.15 and its interval excludes zero, and the refusal control must not explain it.

| task | rate D | rate I | rate H | gap | 95% interval | gap with refusal ablated | result |
|---|---|---|---|---|---|---|---|
| FAR | 1.000 | 0.995 | 0.000 | 0.005 | 0.000 to 0.018 | 0.000 | no gap |
| SDR | 1.000 | 0.840 | 0.000 | 0.160 | 0.086 to 0.227 | 0.136 | passes |
| SER | 1.000 | 0.855 | 0.000 | 0.145 | 0.076 to 0.215 | 0.032 | misses |

- **SDR passes narrowly.** The gap is one point over the bar, and its interval spans the bar.
- **SER misses by half a point.** Ablating the refusal direction would explain its gap anyway.
- **The I condition reads like D on all three tasks.** The classifier separates D from H perfectly in every task, and only H lacks an operator instruction. It may be detecting the instruction rather than a lie.

**Judge plan, sent to the lead.** It covers five stages, about 4,345 paid requests and roughly $3.40 estimated, with exact commands. The per-stage spending caps matter more than the spend. The Sonnet cross-check needs a cap of at least about $6.50, so B3's $10/$3/$7 split will not carry over.

**Two fixes to the read stage, beyond the ask.**
- A read with only the calibration labels reported the verdict as final. It now stays partial until every test row has a judge label.
- Cross-check and re-judge labels could overwrite the main judge labels when passed to the read stage. They are now kept separate, and the read stage reports their agreement as ruling R11 requires.

No GPU-stage code or judge file changed, and 35 tests pass on both interpreters. The lead can accept or revert either fix.

One slip: a combined command ran a read-only `git status` once, which the brief forbids. It produced no output and is noted in the hand-back.

Files, all in the worktree for the lead to commit:
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/07-handback.md` has the results, the evidence block and the judge commands.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/results/d2/job50155519/` holds the job's readings and manifests.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/logs/bridges2/d2_premise_50155519.out` is the job log.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/scripts/d2_premise.py` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/tests/test_d2_premise.py` carry the two fixes and their tests.
