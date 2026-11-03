# Last message of d1-worker ad1-worker-8e94fde54002e325 (2026-11-02T15:01:24-05:00)

R2a is in: the I arm now uses the builder's own token-matched pick, and on every task its pick matches the stored inversion dataset on all 1,000 anchors. The sample did not change and nothing was submitted. Tests pass 31 of 31 on both interpreters.

**Pick kinds** (all ids, with sampled ids only in brackets):

| task | token-matched | form-only | no twin |
| --- | --- | --- | --- |
| far_v2 | 16,264 (15,264) | 1,908 (1,908) | 0 |
| sdr_v2 | 33,300 (32,300) | 0 | 0 |
| ser_v2 | 31,000 (30,000) | 1,250 (1,250) | 0 |

- **Form-only rows:** they fall on whole clauses: FAR shared_01 and shared_04, and SER clause 07.
- **FAR coverage:** FAR still has no I arm for 7 of its 25 clauses, leaving the 18 act-form clauses R2a names.
- **Second anchor:** the stored kept counts it compares against, recomputed from the stored filter reports, are 210, 788 and 249.

**Forwards and GPU-hours:** the expected forward count is unchanged at 621,959. The job now spends about 20 extra minutes of CPU time rebuilding twins and picking I clauses for prior-kept rows and anchors. That brings the estimate to about 1.2 GPU-hours on an H100 or about 2.4 on an A100.

Submit commands:
```
scripts/remote/b2.sh submit --time 02:00:00 --script scripts/jobs/run_d1_visibility.sh --job-name d1-visibility
sbatch --time=03:30:00 --partition=gpuA100x4 --account=bgrb-delta-gpu scripts/jobs/run_d1_visibility.sh
```
The first is for Bridges-2, which is preferred. The second is the Delta fallback.

**Gap:** I did not rerun the py3.9 build dry run on the R2a code. The py3.9 tests check the R2a pick on 25 stored anchors per task.

The hand-back is updated and passes lint. I messaged you the file list. These files changed, all in the worktree:
- `scripts/d1_visibility.py`
- `tests/test_d1_visibility.py`
- `docs/research/deception-divergence/reports/01-handback.md`
