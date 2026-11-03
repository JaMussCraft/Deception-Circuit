# Last message of d1-worker ad1-worker-8e94fde54002e325 (2026-11-02T16:26:28-05:00)

D1 finished, and neither verdict passes on any task. The listener-knowledge and honesty-override verdicts are null on FAR, SDR and SER under both the primary and the secondary definitions. Both reproduction anchors pass, so the readings can be trusted.

**Run:** Bridges-2 job 50145353 completed with exit code 0 in 1:08:27, which is 1.14 GPU-hours on one H100. It ran at commit 4bdf6bb. The scores files have exactly as many rows as the build reports. Rerunning the read stage on mgnp gave the same readings as the job.

**Listener knowledge** (phrasing 1, visible minus hidden, primary rule, in points):

| task | difference | 95% interval |
|---|---|---|
| FAR | +2.5 | +1.1 to +4.1 |
| SDR | -5.2 | -9.1 to -1.7 |
| SER | -2.4 | -3.9 to -0.8 |

All three intervals exclude zero, but none reaches the 10-point bar. Phrasings 2 and 3 also stay under 10 on every task. SDR drops under every phrasing and both definitions, by 9.6 to 9.9 points under the secondary one.

**Honesty override** (I minus D, primary rule, in points):

| task | difference | 95% interval |
|---|---|---|
| FAR | -5.9 | -15.0 to +2.8 |
| SDR | +8.2 | -2.3 to +20.2 |
| SER | +1.9 | -8.1 to +10.8 |

**Matched pools:**

| task | listener n | override n |
|---|---|---|
| FAR | 9,954 | 6,933 |
| SDR | 9,563 | 9,563 |
| SER | 9,846 | 9,846 |

Four SER cells fall under the floor of 100. They are clause 06 at 81 and 90 and clause 07 at 55 and 60.

**Anchors:**
- **First anchor.** D reproduced the stored margins with no sign flips in 1,000 on any task or stream.
- **Prior window.** 941 to 952 of the 1,000 anchors stay inside it on the rescore. Each exit moved one bf16 step from 0.375 to exactly 0.5 against the strict cut, so it is precision drift, not a failure.
- **Second anchor.** Token-matched I compliance is 210, 788 and 249, exactly the stored counts. All 1,000 picks and kept flags agree on every task.

**Outside the pre-registered rules:**
- **SER sentence effect.** Adding the listener sentence at all raises SER compliance by +9.6 points, with an interval of +5.7 to +13.7.
- **Post hoc cut.** On FAR ids that comply under D, phrasing 1 reads +14.7 points. It is listed only as an open question and changes no verdict.

I sent the team lead these numbers. The only file I changed is the hand-back, which now has a Results section and passes lint. No code changed after 4bdf6bb. The outputs are git-ignored, so the team lead decides whether to track the readings. I did not write the worklog entry the compaction hook asked for, because workers never touch the worklog.

Files are in the worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`:
- docs/research/deception-divergence/reports/01-handback.md
- outputs/_analyses/deception-divergence/d1/readings.md
- outputs/_analyses/deception-divergence/d1/readings.json
- logs/bridges2/d1_visibility_50145353.out
