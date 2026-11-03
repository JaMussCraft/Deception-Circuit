# Last message of d2-worker ad2-worker-f58bfa5283c22b81 (2026-11-02T20:45:59-05:00)

I sent you the resubmit command, the no-cache estimate and a ruling to append. Nothing was submitted.

**Code change.** The old guard also compared the two paths in a no-cache run, so a plain `--no-prefix-cache` resubmit would have stopped on the same 0.251. The guard now stops only cached runs. Under `--no-prefix-cache` the full-sequence path is the path of record, and the 8-row comparison is recorded in each features manifest without stopping anything. The 0.25 bar is unchanged.

**Command.** The wrapper passes every argument after the script name to all stages:
```
sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p -A cis260361p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 01:15:00 --job-name=d2-premise scripts/jobs/run_d2_premise.sh --no-prefix-cache
```

**Estimate without the cache**, from the wrapper dry run, which exited cleanly:

| Item | Without cache | With cache |
|---|---|---|
| Feature forwards | 7,854 | 15,708 |
| Feature tokens | 54.9M | 10.8M |
| Estimated total | 3,696 s (1.03 GPU-hours) | 1,835 s (0.51 GPU-hours) |

- **Likely faster than estimated:** the failed job loaded the model in about 30 s, not the 460 s assumed. Its cached FAR pass also ran about 30 percent faster than predicted, so I expect 0.5 to 0.8 hours.
- **Reservation:** `-t 01:15:00` covers the worst case plus about 20 percent. That is 0.25 GPU-hours over START's 1 GPU-hour premise allowance but inside D2's phase-1 allowance. That is your call.

**Validity.** No features exist for any task to doubt. The guard fires before the file is written, FAR ran first, and SDR and SER never started.
- **The drift looks like rounding:** 0.251 is the largest of 384 values, about two bf16 rounding steps at logit sizes of 16 to 32. That fits a different attention path rather than a cache bug: on the float32 tiny model the two paths agree within 1e-4.
- **Path of record:** I recommend dropping the cached path from it. The ruling R14 text in my message to you records this, and the reservation of 01:15:00.

**Changed files**, in the worktree:
- `scripts/d2_premise.py`: the guard change, plus the dry-run estimate now reports both paths.
- `tests/test_d2_premise.py`: one new test for the no-cache path; 33 tests pass on mgnp.
- `docs/research/deception-divergence/plans/D2-plan.md` and `docs/research/deception-divergence/reports/07-handback.md`: a note on the failed job, both lint-clean.

I did not rerun the tests on the base interpreter for this change. None of the three judge files changed, so the judge hash is still `1e41b6b9…0215`.
