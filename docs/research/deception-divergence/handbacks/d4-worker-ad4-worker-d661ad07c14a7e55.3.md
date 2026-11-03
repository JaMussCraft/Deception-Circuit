# Last message of d4-worker ad4-worker-d661ad07c14a7e55 (2026-11-02T14:03:28-05:00)

All three D4 riders finished cleanly and are read. The results are appended to hand-back 02, which lints clean, and the orchestrator has the verdicts.

| rider | job | elapsed | result |
|---|---|---|---|
| (a) quartet attention, D against the twin | Delta 23443932 | 134 s | the attention moves on both tasks |
| (b) after-cue arm of the sycophancy test | Delta 23443933 | 1,048 s | the effect is mostly after the cue window |
| (c) SDR key against query | Bridges-2 50132625 | 1,868 s | query-side, like far and ser |

- **(a)** L17H26 has the second-largest attention shift among the circuit's heads on both tasks. On far, the four heads look less at the designating sentence and more at the item options. On ser, they look less at the designation suffix and more at the pressure clause.
- **(b)** J4's numbers reproduce exactly (0.724 and 0.498). Patching only after the cue keeps 0.662 of the effect. The MLPs' extra contribution falls from 0.226 to 0.080, so they act mostly at the cue tokens themselves. No null draw reaches 0.5 on the after-cue span. That is only a reading: F-rte-008's pre-registered measurement is the full post-tag span.
- **(c)** Query restoration moves 0.524 of the effect and key restoration moves about zero. On the same code as B1, SDR therefore matches far and ser, and the key-side account of F-sdr-012 does not hold up. Beside the rule, the loop closes through the quartet on SDR (0.546, interval 0.511 to 0.577), unlike the bypass on far and ser.

Job (c) was first submitted on Delta, but its projected start slipped to Wed 4 Nov. It was cancelled there and rerun on Bridges-2. I fetched its output into the worktree with the new glob, which was the path you asked me to prepare.

The `b2.sh` edit adds the `deception-divergence*` glob and keeps the two existing ones. All 142 tests that touch `b2.sh` pass on both interpreters. The sync-code dry run exits 0, and both SSH masters were open. A real fetch for this direction needs `DC_DELTA_REPO_ROOT` set to this worktree, because the default writes into the mechanism-analysis worktree.

Files for the orchestrator to commit, all under the worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`:
- `docs/research/deception-divergence/reports/02-handback.md`
- `docs/research/deception-divergence/results/d4c/b1_readings.json` and `b1_readings.md`
- `scripts/remote/b2.sh`
- `tests/test_d4_jobs.py`
