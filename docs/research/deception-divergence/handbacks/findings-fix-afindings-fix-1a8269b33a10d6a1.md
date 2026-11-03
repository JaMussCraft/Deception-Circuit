# Last message of findings-fix afindings-fix-1a8269b33a10d6a1 (2026-11-02T11:30:50-05:00)

I corrected the F-rte-008 row, and all four points from the evidence review checked out against the raw files. Two of those points could not be fixed in this row, and the findings checker still fails on an older row.

**What changed in the F-rte-008 row.** The id, the status and the single table line stay as they were.
- **Commits.** A new provenance sentence says which run each number comes from. The main sycophancy run (S_all, the quartet, Gupta's six) ran at 21bc397. The supplement (heads-only, FAR set, SER set) ran at c32627e, and the parity check at a6ae1a6. All three manifests are clean and have identical code hashes. The commit column stays 21bc397, because the checker only accepts one short SHA there.
- **Interval.** The 0.669 to 0.770 subject-clustered interval now names its method: 2,000 resamples at seed 1. It says no run file stores the interval, points to the new reproduction file, and gives the seed 0 and seed 20261101 intervals.
- **Two caveat errors.** The review also listed these for this row, so I fixed them; you can revert them. The flip-coverage claim now depends on position, because S_all at the readout misses 2 and 1 of the readout reversals. The near-zero range now reads "f between -0.05 and 0.05 reverse 0.30 to 0.43", replacing "0.34 to 0.43".
- **Evidence.** The cell now also lists the parity manifest, the item file and the two reproduction files.

**Reproduction.** The script needs no GPU and exited 0 with the mgnp Python. It recomputes the stored S_all score and its item interval exactly, and the seed 1 clustered interval matches the row.

| Check | Recomputed | In the row or stored |
|---|---|---|
| S_all score | 0.7241 | 0.7241 |
| Item interval | 0.7017 to 0.7463 | 0.7017 to 0.7463 |
| Subject-clustered, seed 1 | 0.669 to 0.770 | 0.669 to 0.770 |

**Left for you to decide:**
- **Layer range and logits wording.** Neither phrase is in F-rte-008. "Layers 18 to 31" is in F-rte-005, and the key-arm dispersion is in F-rte-006. Both checked out: the senders sit in layers 22 to 31, and 0.21 and 0.17 are raw logits. I left both rows alone because your brief limits edits to F-rte-008.
- **The checker still fails.** It fails only on F-mech-009, whose claim does not end with "(superseded by F-rte-001)". The unmodified FINDINGS.md on main fails the same way, and my diff touches only the F-rte-008 line. I did not change F-mech-009. The lint check on FINDINGS.md passes.

I sent you both questions by message. I did not run git, so the claim that no script changed between 21bc397 and c32627e rests on the matching code hashes.

Files are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/`:
- `docs/research/FINDINGS.md`
- `docs/research/deception-divergence/reports/f-rte-008-interval-repro.py`
- `docs/research/deception-divergence/reports/f-rte-008-interval-repro.json`
- `docs/research/deception-divergence/reports/03-handback.md` (lint passes)
