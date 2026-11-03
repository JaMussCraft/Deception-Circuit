# Last message of d1-reviewer ad1-reviewer-f2da8a3ae8570bc4 (2026-11-02T16:41:58-05:00)

Both D1 verdicts are null on all three tasks, and the nulls hold under the frozen rules. D1 can be marked reviewed.

Every number in the readings file and hand-back 01 reproduces from the raw scores and the stored datasets. That covers the pools, all 48 per-arm compliance counts, every comparison and both reproduction anchors. My intervals use a different bootstrap seed and agree within half a point.

The code applies the compliance gate, the listener sentences, the I pick rule, the prior gate and the clustered bootstrap exactly as the spec freezes them. The 31 D1 tests pass on mgnp. The job log is clean, and no row was dropped for length. The visible and hidden sentences of phrasing 1 have identical token lengths.

| task | listener knowledge | review | honesty override | review |
| --- | --- | --- | --- | --- |
| FAR | null, +2.5 | supported with caveats | null, -5.9 | supported |
| SDR | null, -5.2 | supported | null, +8.2 | supported with caveats |
| SER | null, -2.4 | supported | null, +1.9 | supported |

The null is a result, not a code artefact. Two qualifiers should go with the finding:

- **Issue 1, medium.** Each task has five shared clauses that are stakes sentences and never tell the model to give the wrong item. Their I substitute is an explicit "give the wrong result" instruction. They produce all of SDR's +8.2 override and its -5.2 listener effect. On the 20 content clauses, SDR drops to -4.1 and -0.9. I minus D is negative on content clauses in every task, so the override null gets stronger.
- **Issue 3, medium, interpretive.** FAR's 10-point bar sits on a 13 percent D compliance rate. On the ids that comply under D, phrasing 1 shows +14.7 points, with an interval of +8.6 to +22.3. Phrasings 2 and 3 show nothing. This cut depends on the model's own D outcome, so it is not a result. A finding should still say "null under the pooled rule" for FAR, not that the model ignores listener knowledge.

The low issues are these:
- **Clause-form labels.** Two stakes clauses are labelled act-form only because a regex matches "goes wrong". The clause-form table never covered the shared clauses.
- **Fallback lengths.** The hidden sentences of phrasings 2 and 3 are one or two tokens longer than the visible ones.
- **Hardware drift.** The D arm passes the compliance gate on 969, 994 and 948 of the 1,000 anchors. Drift across hardware moves 3 to 5 percent of ids across the 0.7 margin.
- **Hand-back wording.** Hand-back 01 has three small inaccuracies about prior drift and the length-120 controls.
- **Test baseline.** The full-suite failures in hand-back 01 were not compared with the known baseline names.

I did not run the D1 tests on the base Python 3.9 interpreter. The summary went to team-lead, and no git was run.

Files are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/`:
- reviews/02-d1-review.md
- reports/05-handback.md
