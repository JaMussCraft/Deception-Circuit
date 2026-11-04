# Hand-back 10: W9, the finer-ladder sets and the one-neuron interchange sets (R15 inputs)

Agent: implementation worker W9 (Claude, Opus). Ticket: the team lead's W9 brief of Wed 4 Nov 2026 ("Build ladder and
one-neuron sets"). Status: resolved for W9's part. The inputs are built and dry-run. R15 was committed at 92fc6fb,
and the job lines went to r1-runner with that commit on Wed 4 Nov 2026 at about 11:00 am EST. Both cells are not
yet verified, because neither has run.

## What changed

No tracked code changed. The only file to commit is this hand-back:

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/10-w9-ladder-handback.md`.

Nothing is staged for the apply tool. The outputs below are git-ignored. `NP` stands for
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition`.

| file | sha256 |
| --- | --- |
| `NP/ablation/ladder_sets.json`, 84 groups | `361b12a7c39ffb97bb768f619503684a5626b39a0fd059afb86ae910e77b2ce0` |
| `NP/ablation/one_neuron_sets.json`, 40 groups | `873afbce27fbb70e1162e7a19af701875861e7c5f9f64b622c38127cdd7465f3` |
| `NP/ablation/one_neuron_scores.json`, scores and provenance | `a499f68cc24161cd0b1cc33a46c4dc63a84e285c0abeb675e85ed56bd89c8a8e` |
| `NP/sets/far_atp_all_c3d7763_ladder/partition_summary_all.json` | `2952109d1043a2775507ad9b88b87dcf10d3ecf250fe9db62040b9cc77b24200` |
| `NP/w9_tmp/one_neuron_report.py`, the CPU report | `a27330482b955865b397fad96c59eec4ab0a192be1f66a11f5adf5bd94b8d1c0` |
| `NP/data/far_test_sample_seed3.json`, unchanged input | `bdd94ce25aa7d029d20f6a17909c8c8b583beef52426d641aa7e04e0ed4f87d6` |
| `NP/data/far_test_sample_seed2.json`, unchanged input | `cdbfca851a004069c31c1390eebcda03fc4845ce73fb6d8f2fbb50bbff48a845` |

- **Ladder sets.** `NP/sets/far_atp_all_c3d7763_ladder/` holds `far_all_sets_k{250,375,625,750}.json`, the
  matching `_with_nulls.json` files with 84 groups each, `nulls/` and the summary. The console log is
  `NP/sets/far_atp_all_c3d7763_ladder.log`.
- **Scratch.** Everything else is in `NP/w9_tmp/`:
  - the builders `build_ladder.py`, `split_ladder.py` and `build_one_neuron.py`;
  - the non-nesting check `nesting_cause.py`;
  - the report test `test_one_neuron_report.py`;
  - the dry-run logs `dry_*.log`;
  - the two 42-group half files, which are not meant for submission;
  - the k = 500 reproduction `repro_k500/`.

**One departure from the brief.** The ladder's tested sets are named `D_only_<k>`, for example `D_only_250`. The
brief asked for `D_only_k<k>`. The verdict script finds a set's nulls through the `<class>_<k>` suffix. I fed it the
names from `ladder_sets.json` through its own `tested_sets`:

| name form | class | k | nulls paired |
| --- | --- | --- | --- |
| `D_only_k250`, the brief's form | `D_only_k250` | none | 0 |
| `D_only_250`, the form used | `D_only` | 250 | 20 |

With the brief's names, the verdict step would have reported no class and no null. The nulls keep the brief's names,
`null_D_only_<k>_<i>`.

## How verified

### Inputs and reproduction

The ranking inputs are the same as those of `sets/far_atp_all_c3d7763`. The `--dh` and `--dh-reverse` inputs are
`far_v2_dh_train+validation_c3d7763_rev`. The `--in` input is the plain `far_v2_in_train+validation_c3d7763`. The
brief names the I run's `_rev` directory, so I compared the two I directories first.

```
/u/swong2/.conda/envs/mgnp/bin/python -c "... torch.load both I scores.pt ... (a['atp_all_mean']-b['atp_all_mean']).abs().max()"
```

Observed: `max diff atp_all_mean 0.0 torch.Size([32, 14336])`. The two I directories give the same s_I.

Rerunning the existing rule at k = 500 into scratch reproduces the existing files byte for byte:

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_sets.py partition --position all -k 500 --dh ".../far_v2_dh_train+validation_c3d7763_rev" --in ".../far_v2_in_train+validation_c3d7763" --dh-reverse ".../far_v2_dh_train+validation_c3d7763_rev" --out-dir NP/w9_tmp/repro_k500
cmp NP/w9_tmp/repro_k500/far_all_sets_k500.json NP/sets/far_atp_all_c3d7763/far_all_sets_k500.json
cmp NP/w9_tmp/repro_k500/far_all_sets_k500_with_nulls.json NP/sets/far_atp_all_c3d7763/far_all_sets_k500_with_nulls.json
```

Observed: exit 0, and both comparisons are `identical`. So the ladder rungs are cut from the fixed ranking with the
same rule, the same null seed (2) and 20 nulls per class.

### Task A: the finer ladder

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_sets.py partition --position all -k 250 375 625 750 --dh ".../far_v2_dh_train+validation_c3d7763_rev" --in ".../far_v2_in_train+validation_c3d7763" --dh-reverse ".../far_v2_dh_train+validation_c3d7763_rev" --label "FAR finer ladder k 250/375/625/750, AtP all positions (R11 ranking, R15 follow-up)" --out-dir NP/sets/far_atp_all_c3d7763_ladder
```

Observed: exit 0. No ranking was truncated. The k = 500 row comes from the existing partition.

| k | D_only | DI_shared | H_only | all_shared | threshold T_D | densest D_only layers |
| --- | --- | --- | --- | --- | --- | --- |
| 250 | 152 | 49 | 183 | 40 | 0.05024 | L7 22, L12 19, L5 15 |
| 375 | 243 | 65 | 291 | 54 | 0.04032 | L8 33, L12 28, L7 27 |
| 500 | 338 | 79 | 390 | 62 | 0.03515 | L8 44, L7 39, L12 37 |
| 625 | 424 | 99 | 492 | 72 | 0.03156 | L8 51, L7 46, L10 43 |
| 750 | 524 | 114 | 595 | 79 | 0.02884 | L7 63, L8 62, L6 53 |

```
/u/swong2/.conda/envs/mgnp/bin/python NP/w9_tmp/build_ladder.py --force
```

The builder asserts that each null has its class's size and 32-layer histogram, shares no neuron with the class, and
differs from the other 19 nulls. Observed: `groups 84 sha256 361b12a7…2ce0`.

**The D-only classes are not nested.** T_D is nested at every step, but D_only is not. D_only_500 is not a subset of
D_only_625, and it is not a superset of D_only_375. The rule causes this: T_I and T_H also grow with k, so a D_only
member can enter T_I or T_H at the larger k and leave the class.

```
/u/swong2/.conda/envs/mgnp/bin/python NP/w9_tmp/nesting_cause.py
```

| step | T_D nested | members dropped | entered T_I | entered T_H | unexplained | new members |
| --- | --- | --- | --- | --- | --- | --- |
| 250 to 375 | yes | 8 of 152 | 3 | 5 | 0 | 99 |
| 375 to 500 | yes | 6 of 243 | 2 | 4 | 0 | 101 |
| 500 to 625 | yes | 13 of 338 | 7 | 6 | 0 | 99 |
| 625 to 750 | yes | 9 of 424 | 6 | 3 | 0 | 109 |

So 237 of D_only_375's 243 neurons are in D_only_500, and 325 of D_only_500's 338 are in D_only_625.

```
/u/swong2/.conda/envs/mgnp/bin/python -c "... neuron_partition_verdict.tested_sets(...) ... knockout.load_groups(...)"
```

Observed: the verdict script pairs `D_only_250`, `D_only_375`, `D_only_625` and `D_only_750` each with class
`D_only`, the right k and 20 nulls. `load_groups` reads 84 groups from the ladder file and 40 from the one-neuron
file. The verdict script reads k from the names and hard-codes no ladder, apart from the 2,000-neuron size bar.

### The ladder dry run, seed-3 sample

```
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 HF_HOME=/work/nvme/beto/swong2 HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_set_ablation.py --task far --sets outputs/_analyses/neuron-partition/ablation/ladder_sets.json --ids outputs/_analyses/neuron-partition/data/far_test_sample_seed3.json --i-dir outputs/_analyses/neuron-partition/data/pools/far_v2_user_inversion --n-dir outputs/_analyses/neuron-partition/data/pools/far_v2_user_neutral --output-dir outputs/_analyses/neuron-partition/w9_tmp/dry_ladder_final --max-length 128 --references twin,mean --ioi-rows 1000 --ioi-seed 2 --dry-run
```

Observed, exit 0:

- **Size.** 84 sets in 3 chunks. **49,339 forwards**, with a forward-time estimate of 1,999.5 s at the H100
  constant.
- **Rows.** The rows are D 208, H 208, F 208, I 166, N 166 and IOI 1,000. No id is missing or dropped by
  tokenization. Every D id has an H twin, and every I id has an N twin.
- **IOI.** The IOI sentences sha256 is `906a93ed…86e0`, the same seed-2 draw as the confirmation cell (hand-back
  08). The ladder cell therefore reads the same 1,000 fresh IOI rows.

**Calibration.** I re-dry-ran the confirmation cell's exact inputs (`ioi_resolution_sets.json`, seed 3, twin and
mean, IOI 1,000 with seed 2). It gives 12,830 forwards, which matches the brief, and an estimate of 523.2 s. The real
job 23494260 timed 2,163.2 s of forwards on an A40, so the A40 runs at 4.13 times the dry-run estimate. The measured
H100 rates of Bridges-2 jobs A, B and C are 0.039 to 0.042 s per forward at 128 tokens, against the dry run's
0.0497. Model loads there took 475 to 904 s.

| cell | forwards | A40 (calibrated) | H100 (measured rate) | load and overhead |
| --- | --- | --- | --- | --- |
| ladder, all 84 sets | 49,339 | about 138 min | about 27 to 29 min | up to 15 min on Bridges-2 |
| ladder, one half (42 sets) | 25,278 | about 71 min (84 min at 0.20 s per forward) | not applicable | about 1 min on Delta |
| one-neuron, 40 sets | 6,916 | about 24 min | not applicable | about 1 min on Delta |

### Task B: the one-neuron sets

```
OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python NP/w9_tmp/build_one_neuron.py
```

- **Scores.** s_D is `atp_all_mean` and s_H is minus `rev_atp_all_mean` of the dh `_rev` run. s_I comes from the
  I run and is recorded beside them.
- **Rule.** The top 20 of each score, positive scores only, with ties going to the lower flat index. This is the
  partition script's rule.
- **Names.** Groups are named `sD_<rank>_L<layer>_n<index>` and `sH_<rank>_L<layer>_n<index>`, with the rank
  zero-padded to two digits.

Observed: 40 groups. **The two lists share 4 neurons**: L13 n4212, L13 n10624, L14 n7120 and L19 n11138. They hold
36 distinct neurons. I kept both groups for each shared neuron. That costs 4 groups of forwards and gives a
determinism check, because the two groups must give identical changes.

What the scores predict, descriptively:

- **Top s_D neurons.** 8 of the 20 have s_H below minus 0.05. Examples: L15 n11788 with s_D +0.358 and s_H −1.054,
  L15 n2808 with s_H −0.620, and L16 n8935 with s_H −0.522. These are review 01's cases.
- **Top s_H neurons.** 9 of the 20 have a negative s_D.

```
PYTHONHASHSEED=0 OMP_NUM_THREADS=1 HF_HOME=/work/nvme/beto/swong2 HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_set_ablation.py --task far --sets outputs/_analyses/neuron-partition/ablation/one_neuron_sets.json --ids outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json --i-dir outputs/_analyses/neuron-partition/data/pools/far_v2_user_inversion --n-dir outputs/_analyses/neuron-partition/data/pools/far_v2_user_neutral --output-dir outputs/_analyses/neuron-partition/w9_tmp/dry_one_neuron --max-length 128 --conditions D,H --references twin --no-ioi --dry-run
```

Observed, exit 0: 40 sets, rows D 300 and H 300, 38 batches each. That is **6,916 forwards**, of which 228 are
self-replay, with an estimate of 343.6 s.

### The report script

`NP/w9_tmp/one_neuron_report.py` uses only the standard library. It reads the cell's `rows.jsonl` and
`one_neuron_scores.json`. Every margin in `rows.jsonl` is in D orientation. For each neuron it reports:

- **The D change.** The mean of m_ablated − m_intact on D under the twin patch. First-order AtP predicts −s_D.
- **The H change.** The same mean on H under the reverse patch. It predicts +s_H.
- **Further columns.** The fraction of the D margin effect removed, s_I, and the clean-stream-only changes. The
  ranking scored only the clean stream.

The summary gives sign agreement and Spearman ρ(s_D, −dD) and ρ(s_H, dH). Each is given over all 40 groups and over
the 36 distinct neurons, and also by list. It also gives the largest difference between duplicate groups.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q -rs --basetemp=/projects/beto/swong2/.w9-5201d56c-tmp/bt1 test_one_neuron_report.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q -rs --basetemp=/projects/beto/swong2/.w9-5201d56c-tmp/bt2 test_one_neuron_report.py
```

Both were run from `NP/w9_tmp/`. Observed: `7 passed in 0.18s` on mgnp and `7 passed in 0.20s` on base. The tests
use synthetic rows files:

- **Exact first order.** The changes equal −s_D and +s_H, the sign agreement is 5 of 5, Spearman is 1.0, the
  duplicate difference is 0, and a mean-reference row is ignored.
- **Flipped H.** H moves against the prediction, and D agrees on the clean stream only. Spearman for H is −1, and
  the clean-stream view is checked.
- **Ties.** Average ranks are used for ties.
- **Missing stream.** A row missing a stream is skipped and counted.
- **Refusals.** It refuses an unknown set, a group with no rows, and an overwrite.
- **Real names.** The real `one_neuron_scores.json` with synthetic rows gives 36 distinct neurons and 4 duplicate
  pairs.

## Execution evidence

Not applicable: no runs. The partition, builders, dry runs and tests above are login-node CPU checks. No Slurm job
was submitted.

## What is NOT done

- **Neither GPU cell has run.** Team-lead sent "R15 committed at 92fc6fb", and the lines below went to r1-runner
  with `<sha>` = 92fc6fb. The output directories are `ablation/ladder-92fc6fb/` and `ablation/one_neuron-92fc6fb/`.
  The order is team-lead's. The ladder goes first on Bridges-2, test-only and then submitted. The one-neuron job
  runs on Delta interactive only after r1-runner's N2 cell (its job 1) ends, because the interactive partition
  allows one job per user.
- **The budget.** The ladder reserves 1.5 GPU-hours and the one-neuron cell 0.75, 2.25 in all. Together with the
  N2 cell, they must stay within R15's 3.5 GPU-hours. I did not see the N2 cell's reservation.
- **Post-processing waits on the runs.** The verdict on the ladder and the one-neuron report have not run.
  r1-runner runs them as written below.
- **No Delta fallback for the ladder.** By the brief's rule, the ladder is Bridges-2 only. Each half is 25,278
  forwards. At 0.20 s per forward that is about 84 minutes. The calibrated A40 rate gives about 71 minutes. Both are
  well over the 50-minute bar for a one-hour interactive slot.
- **No change to the verdict script.** I renamed the sets instead.

**The ladder line, Bridges-2.** It runs from Delta over the open master, and `ssh -O check bridges2` comes first.

```
ssh -o BatchMode=yes bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p,PYTHONHASHSEED=0,NP_I_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_inversion,NP_N_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_neutral -A cis260372p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 01:30:00 --job-name=np-ladder docs/research/neuron-partition/jobs/ablation_cells.sbatch outputs/_analyses/neuron-partition/ablation/ladder_sets.json outputs/_analyses/neuron-partition/data/far_test_sample_seed3.json outputs/_analyses/neuron-partition/ablation/ladder-<sha>/ --max-length 128 --references twin,mean --ioi-rows 1000 --ioi-seed 2'
```

Reserve 90 minutes. The expected time is 45 to 50 minutes: about 29 minutes of forwards, up to 15 of model load,
and a few minutes of batch building and the mean bank.

**Before submitting the ladder.** Every step runs from the Delta worktree root.

1. **The clone's code must match the worktree.** The four sha256 values below must match on both sides. If they
   do not, the orchestrator syncs the clone first, because that step uses version control.
   - `scripts/neuron_set_ablation.py`: `b4efbd59…972a`.
   - `component_analysis/knockout.py`: `e39cbbed…3914`.
   - `docs/research/neuron-partition/jobs/ablation_cells.sbatch`: `6cedc093…d989`.
   - `models/llama_node.py`: `2c48ae2c…4644`.
2. **Push the two inputs.** The seed-3 file may already be on the clone. The checksum makes the copy a no-op if so.

   ```
   rsync -rl --checksum outputs/_analyses/neuron-partition/ablation/ladder_sets.json b2dtn:/ocean/projects/cis260361p/swong2/Deception-Circuit/outputs/_analyses/neuron-partition/ablation/
   rsync -rl --checksum outputs/_analyses/neuron-partition/data/far_test_sample_seed3.json b2dtn:/ocean/projects/cis260361p/swong2/Deception-Circuit/outputs/_analyses/neuron-partition/data/
   ```

3. **Check the hashes on Bridges-2.** Expect `361b12a7…2ce0` for the sets file and `bdd94ce2…87d6` for the sample.
   Also check that both pool directories exist.

   ```
   ssh -o BatchMode=yes bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && sha256sum outputs/_analyses/neuron-partition/ablation/ladder_sets.json outputs/_analyses/neuron-partition/data/far_test_sample_seed3.json scripts/neuron_set_ablation.py component_analysis/knockout.py docs/research/neuron-partition/jobs/ablation_cells.sbatch models/llama_node.py && ls -d outputs/_analyses/neuron-partition/data/pools/far_v2_user_inversion outputs/_analyses/neuron-partition/data/pools/far_v2_user_neutral'
   ```

4. **Test the submission.** Run the same sbatch line with `--test-only` first.

**After the ladder job.**

1. **Fetch the cell and log.** Use `rsync -rl` through b2dtn, without `-a`.

   ```
   rsync -rl b2dtn:/ocean/projects/cis260361p/swong2/Deception-Circuit/outputs/_analyses/neuron-partition/ablation/ladder-<sha>/ outputs/_analyses/neuron-partition/ablation/ladder-<sha>/
   rsync -rl b2dtn:/ocean/projects/cis260361p/swong2/Deception-Circuit/logs/np_ablate_<jobid>.out logs/
   ```

2. **Compare hashes.** Compare the sha256 of `summary.json`, `rows.jsonl`, `cells_partial.jsonl` and
   `run_manifest.json` on both sides.
3. **Run the verdict.**

   ```
   /u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_verdict.py --cell outputs/_analyses/neuron-partition/ablation/ladder-<sha> --sample outputs/_analyses/neuron-partition/data/far_test_sample_seed3.json --output-dir outputs/_analyses/neuron-partition/verdict/ladder-<sha>
   ```

**The one-neuron line, Delta.** It runs from the worktree root on the beto account, the account W8's interactive job
used. The I and N pool directories must exist for the wrapper's check, and they do on Delta.

```
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition && sbatch --account=beto-delta-gpu --partition=gpuH200x8-interactive,gpuA40x4-interactive --exclude=gpub001 --gpus-per-node=1 --cpus-per-task=1 --mem=64G -t 00:45:00 --job-name=np-one-neuron docs/research/neuron-partition/jobs/ablation_cells.sbatch outputs/_analyses/neuron-partition/ablation/one_neuron_sets.json outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json outputs/_analyses/neuron-partition/ablation/one_neuron-<sha>/ --max-length 128 --conditions D,H --references twin --no-ioi
```

Reserve 45 minutes. On an A40, expect about 24 minutes of forwards, 1 to 2 minutes of load and a few minutes of
batch building. On an H200 it takes a few minutes.

**After the one-neuron job.**

```
/u/swong2/.conda/envs/mgnp/bin/python outputs/_analyses/neuron-partition/w9_tmp/one_neuron_report.py --rows outputs/_analyses/neuron-partition/ablation/one_neuron-<sha>/rows.jsonl --scores outputs/_analyses/neuron-partition/ablation/one_neuron_scores.json --out-dir outputs/_analyses/neuron-partition/verdict/one_neuron-<sha>
```

It prints the per-neuron table and the summary table, and it writes `one_neuron_report.{json,md}`.

## Open questions

1. **A Delta route for the ladder.** Is one wanted, if Bridges-2 stalls? Four single-size jobs of 21 sets each
   would mirror the confirmation cell, which ran 38 minutes of wall time on an A40. Each would fit a one-hour
   interactive slot. Default: Bridges-2 only, as the brief says.
2. **The names.** Should the finding cite the ladder classes as `D_only_<k>`? Default: yes. The verdict tables
   print class `D_only` with k, so the names never reach the finding.
3. **Duplicate neurons.** Should the four neurons in both top-20 lists be ablated twice? Default: yes. It costs
   about 10 percent of a short cell and checks determinism. The Spearman values are read on the 36 distinct
   neurons.
4. **Which neurons the one-neuron check takes.** The brief takes the top 20 by signed s_D and by signed s_H.
   Review 01 proposed the top 20 by absolute value. Default: the brief's signed lists. The two choices differ. I
   checked this on the same scores:

   | score | top 20 by absolute value that are negative | shared with the signed top 20 |
   | --- | --- | --- |
   | s_D | 5 | 15 |
   | s_H | 9 | 11 |

   For example, s_H's most negative neuron, L15 n11788 at −1.054, is in the absolute-value list. It is not in the
   signed s_H list, but it enters the cell through the s_D list. If the lead wants the negative tails tested too,
   at most 14 more groups would cover them. That adds at most about 2,400 forwards, about 32 minutes of forwards
   on an A40 in all, so it still fits the 45-minute slot.
