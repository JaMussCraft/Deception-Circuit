# Last message of d4-worker ad4-worker-d661ad07c14a7e55 (2026-11-02T14:05:41-05:00)

All three D4 riders are complete, and I've written up D4(c) in hand-back 02 and reported it to team-lead. Your notice about the move to Bridges-2 crossed with my earlier report, so I sent a short follow-up with the same result.

**D4(c) on SDR, Bridges-2 job 50132625:** the job completed in 1,868 seconds, of which 394 seconds was model load.

| Test | Reading | Interval | Rule | Verdict |
|---|---|---|---|---|
| Query-vs-key test (T2) | query share 0.524, key share -0.002 | 0.488 to 0.556 for the query share | lead must exceed 0.15 | query-side, lead 0.526 |
| Loop-closure test (T1) | M_q 0.546 | 0.511 to 0.577 | must reach 0.50 | closes, route-specific |

In B1, FAR and SER did not close the loop, at 0.360 and 0.462. SDR is the first of the three that does.

**Files to commit since c6752c0**, all under the worktree:
- `scripts/remote/b2.sh`, which now fetches the deception-divergence outputs.
- `tests/test_d4_jobs.py`, which tests that change.
- `docs/research/deception-divergence/reports/02-handback.md`, where the "Addendum: GPU riders" section holds the evidence for all three jobs.
- `docs/research/deception-divergence/results/d4c/b1_readings.json` and `b1_readings.md`.

I stopped my leftover background check that was waiting for a Delta resubmission. I did not add the worklog entry the compaction hook asked for, because your brief forbids touching WORKLOG.md. You may want to add it.
