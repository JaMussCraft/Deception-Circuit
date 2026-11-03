# Last message of d2-worker ad2-worker-f58bfa5283c22b81 (2026-11-03T00:07:18-05:00)

The D2 follow-up is built to R15, and its CPU dry run passes with nothing blocking submission. The summary has gone to the lead. No GPU job has run yet, so the anchor and the readings are tested only on the tiny model and on synthetic or stand-in features. I ran no git, no Slurm job and no paid call. The hand-back is number 10, because the plan reviewer already wrote hand-back 09.

**What I built**
- **Plan.** `plans/D2-followup-plan.md` now carries all 14 of review 05's amendments. Its token-match tables come from the dry run, and a new section lists the 30 honest mirrors of the inversion clauses (the IH arm).
- **Clause pool.** `data/d2/d2_followup_clauses.json` holds the 50 honest mirrors of the D clauses and the 30 IH mirrors. Its sha256 is `9b8244d9aab323a9575242516566ab88262ea4c46d6fd060d346ee7f25be332a`, which R15 records.
- **Code.** `scripts/d2_followup.py` has three stages: a CPU dry run, the GPU features and the read. It uses D2's code unchanged and changes no existing file. The Bridges-2 wrapper is `scripts/jobs/run_d2_followup.sh`, and the 43 tests are in `tests/test_d2_followup.py`.
- **Dry-run report.** `results/d2_followup/build_report.json`.

**Tests**
- All 43 new tests pass on mgnp. On the base interpreter, 79 pass across the three D2 test files, with none skipped.
- The full suite on mgnp gave 22 failures and 101 errors. All 8 known baseline failures are among them.
- The other 115 are in other directions' test files. 112 of them fail because artifacts from other sessions are not in this worktree, and 3 are `IndexError`s in `test_end_to_end`. None of those tests imports the new files. I did not rerun them at the parent commit to prove they failed before.

**Dry run**

| Item | Value |
|---|---|
| Rows in total | 5,481 (R15's 4,881 plus the 600-row drift anchor) |
| Fallback firings, form mismatches, token differences | 0 |
| Estimate at D2's measured rates | 0.46 GPU-hours |
| Estimate by the D2 plan's model constant | 0.68 GPU-hours |
| Reservation | 45 minutes on one Bridges-2 H100 |

A full-scale read on stand-in files made from D2's own rows reproduces D2's act-form gaps, as it should when the honest arm is replaced by H.

**Waiting on the lead**
- Two readings in the code need confirmation. The refusal-validity bar is computed on the same act-form ids as the gap. The IH condition holds when its clustered interval lies above zero.
- After that, the lead commits, syncs and submits. The commands are in hand-back 10, starting with a dry run on the Bridges-2 login node:

```
cd /ocean/projects/cis260361p/swong2/Deception-Circuit
DC_CLUSTER=bridges2 bash scripts/jobs/run_d2_followup.sh --dry-run --out-root /tmp/d2fu_dry --report /tmp/d2fu_dry/build_report.json
sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p -A cis260361p -p GPU-shared \
    --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 00:45:00 --job-name=d2-followup \
    scripts/jobs/run_d2_followup.sh
```

Files are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`:
- `docs/research/deception-divergence/reports/10-handback.md`
- `docs/research/deception-divergence/plans/D2-followup-plan.md`
- `data/d2/d2_followup_clauses.json`
- `scripts/d2_followup.py`
- `scripts/jobs/run_d2_followup.sh`
- `tests/test_d2_followup.py`
- `docs/research/deception-divergence/results/d2_followup/build_report.json`
