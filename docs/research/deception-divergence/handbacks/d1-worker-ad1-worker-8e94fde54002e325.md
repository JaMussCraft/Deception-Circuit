# Last message of d1-worker ad1-worker-8e94fde54002e325 (2026-11-02T14:01:43-05:00)

The D1 scoring pipeline is built, tested on both interpreters, and dry-run through its wrapper. No GPU job was submitted. The hand-back passes the research-session lint and is at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research/deception-divergence/reports/01-handback.md`.

**Anchor byte identity:** for each task's 1,000 selected test ids, the regenerated D clean, D corrupt and prior prompts match the stored dataset rows exactly. This holds on both interpreters.

| task | D clean | D corrupt | prior prompt |
| --- | --- | --- | --- |
| far_v2 | 1000/1000 | 1000/1000 | 1000/1000 |
| sdr_v2 | 1000/1000 | 1000/1000 | 1000/1000 |
| ser_v2 | 1000/1000 | 1000/1000 | 1000/1000 |

**Runtime estimate:** the job needs about 622,000 forward passes across the three tasks. That is about 1.05 GPU-hours on an H100 or about 2.2 on an A100.

Bridges-2 is the preferred cluster. Push the branch and run `scripts/remote/b2.sh sync-code --branch deception-divergence` first. The submit command, then the sbatch it runs on Bridges-2:
```
scripts/remote/b2.sh submit --time 01:45:00 --script scripts/jobs/run_d1_visibility.sh --job-name d1-visibility
sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p -A cis260361p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 01:45:00 --job-name=d1-visibility scripts/jobs/run_d1_visibility.sh
```
The Delta fallback, from the worktree root:
```
sbatch --time=03:00:00 --partition=gpuA100x4 --account=bgrb-delta-gpu scripts/jobs/run_d1_visibility.sh
```

**Things to know before reading results:**
- **Candidate pool:** the original build scored only 140,000 of the 162,500 planned FAR test entries and 40,000 of 54,168 for SDR. I sample only from what was actually scored.
- **Prompt length:** every arm fits in the builder's 120 tokens, so no row is dropped and D is scored exactly as the builder scored it.
- **I clause:** following your clarification, the I clause is picked without the token-count match. It agrees with the stored inversion datasets' pick on only 19 to 29 percent of anchors. With the token match added back, the pick reproduces the stored one on all 1,000.
- **FAR coverage:** the inversion pool has no FAR clause matching 7 of FAR's 25 pressure clauses, so those ids get no I arm.
- **Full test suite:** the full mgnp run shows 19 failures and 101 setup errors. The errors are missing files from other directions that this worktree doesn't hold. The 19 failures are the same when my test file is left out, and I edited no existing file. I did not compare against main's baseline list or run the full suite on py3.9.

Files for you to commit, all in the worktree:
- `scripts/d1_visibility.py`
- `tests/test_d1_visibility.py` (24 tests, all passing on both interpreters)
- `scripts/jobs/run_d1_visibility.sh`
- `docs/research/deception-divergence/reports/01-handback.md`
