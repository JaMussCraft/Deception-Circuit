# Full ablation cells on Bridges-2: jobs A, B and C

Written Tue 3 Nov 2026, 1:40 pm EST by W2 for the orchestrator. Nothing here has been submitted. The `--test-only`
variants were run once at 1:26 pm EST with placeholder arguments; they create no job.

## Before submitting

1. Commit the review 02 fixes and sync the clone `/ocean/projects/cis260361p/swong2/Deception-Circuit` to that
   commit. The clone's `ablation_cells.sbatch` must be the version that accepts a comma-separated list of sets files.
   The e5962fe version takes one file only and would fail on jobs A and B.
2. Replace the placeholders in every line with the real names once W4's sets exist and W3 has synced them:
   - `ALLSHA` is the suffix of `sets/far_atp_all_<sha>/`.
   - `READSHA` is the suffix of `sets/far_atp_readout_<sha>/`.
   - `CONSHA` is the suffix of `sets/far_contrast_<sha>/`.
   - `COMMIT` is the short commit the clone runs.
3. Check the file names inside each sets directory. These lines assume W4 keeps the names of
   `sets/far_atp_66741d7/` (`far_sets_k<k>_with_nulls.json`) and `sets/far_contrast_66741d7/`
   (`far_contrast_sets_k<k>_with_nulls.json`).
4. Every line runs from Delta over the open SSH master. Check it first with `ssh -O check bridges2`.

The wrapper exports `PYTHONHASHSEED=0` itself. The `--export` list repeats it, and `SBATCH_EXPORT=NONE` on Bridges-2
means only that list reaches the job. `DC_B2_ALLOC=cis260361p` names where the clone lives, and `-A cis260372p`
names the allocation charged. Each sets file of a list writes into its own subdirectory of the output dir, named
after the file. A walltime kill during the second file leaves the first file's `summary.json` complete.

## Job A: all-position sets, k 500 and 1,000

```
ssh -o BatchMode=yes bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p,PYTHONHASHSEED=0,NP_I_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_inversion,NP_N_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_neutral -A cis260372p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 03:30:00 --job-name=np-ablate-A docs/research/neuron-partition/jobs/ablation_cells.sbatch outputs/_analyses/neuron-partition/sets/far_atp_all_ALLSHA/far_sets_k500_with_nulls.json,outputs/_analyses/neuron-partition/sets/far_atp_all_ALLSHA/far_sets_k1000_with_nulls.json outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json outputs/_analyses/neuron-partition/ablation/jobA-COMMIT --max-length 128'
```

Test-only variant:

```
ssh -o BatchMode=yes bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && sbatch --test-only --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p,PYTHONHASHSEED=0,NP_I_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_inversion,NP_N_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_neutral -A cis260372p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 03:30:00 --job-name=np-ablate-A docs/research/neuron-partition/jobs/ablation_cells.sbatch outputs/_analyses/neuron-partition/sets/far_atp_all_ALLSHA/far_sets_k500_with_nulls.json,outputs/_analyses/neuron-partition/sets/far_atp_all_ALLSHA/far_sets_k1000_with_nulls.json outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json outputs/_analyses/neuron-partition/ablation/jobA-COMMIT --max-length 128'
```

## Job B: all-position k 2,000, then the readout-position comparison at k 1,000

```
ssh -o BatchMode=yes bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p,PYTHONHASHSEED=0,NP_I_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_inversion,NP_N_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_neutral -A cis260372p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 03:30:00 --job-name=np-ablate-B docs/research/neuron-partition/jobs/ablation_cells.sbatch outputs/_analyses/neuron-partition/sets/far_atp_all_ALLSHA/far_sets_k2000_with_nulls.json,outputs/_analyses/neuron-partition/sets/far_atp_readout_READSHA/far_sets_k1000_with_nulls.json outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json outputs/_analyses/neuron-partition/ablation/jobB-COMMIT --max-length 128'
```

Test-only variant:

```
ssh -o BatchMode=yes bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && sbatch --test-only --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p,PYTHONHASHSEED=0,NP_I_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_inversion,NP_N_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_neutral -A cis260372p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 03:30:00 --job-name=np-ablate-B docs/research/neuron-partition/jobs/ablation_cells.sbatch outputs/_analyses/neuron-partition/sets/far_atp_all_ALLSHA/far_sets_k2000_with_nulls.json,outputs/_analyses/neuron-partition/sets/far_atp_readout_READSHA/far_sets_k1000_with_nulls.json outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json outputs/_analyses/neuron-partition/ablation/jobB-COMMIT --max-length 128'
```

## Job C: contrast-key sets at k 1,000

```
ssh -o BatchMode=yes bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p,PYTHONHASHSEED=0,NP_I_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_inversion,NP_N_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_neutral -A cis260372p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 02:00:00 --job-name=np-ablate-C docs/research/neuron-partition/jobs/ablation_cells.sbatch outputs/_analyses/neuron-partition/sets/far_contrast_CONSHA/far_contrast_sets_k1000_with_nulls.json outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json outputs/_analyses/neuron-partition/ablation/jobC-COMMIT --max-length 128'
```

Test-only variant:

```
ssh -o BatchMode=yes bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && sbatch --test-only --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p,PYTHONHASHSEED=0,NP_I_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_inversion,NP_N_DIR=outputs/_analyses/neuron-partition/data/pools/far_v2_user_neutral -A cis260372p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 02:00:00 --job-name=np-ablate-C docs/research/neuron-partition/jobs/ablation_cells.sbatch outputs/_analyses/neuron-partition/sets/far_contrast_CONSHA/far_contrast_sets_k1000_with_nulls.json outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json outputs/_analyses/neuron-partition/ablation/jobC-COMMIT --max-length 128'
```

Job C writes straight into `ablation/jobC-COMMIT/`, because it has one sets file. Jobs A and B write
`ablation/jobA-COMMIT/far_sets_k500_with_nulls/` and the like.

## Estimate

The dry runs used the fixed code, W3's sample file as `--ids` (300 ids per condition) and `--max-length 128`. The
stand-in sets were the 66741d7 files, because the all-position sets do not exist yet. The forward count depends on
the number of sets and not on k. An all-position file with 4 classes and 20 nulls each holds 84 sets. A contrast file
with 3 classes holds 63.

| Sets file | Sets | Forwards |
|---|---|---|
| far_sets_k500_with_nulls (stand-in for each all-position or readout file) | 84 | 97,210 |
| far_contrast_sets_k1000_with_nulls | 63 | 72,622 |

The rate is the pilot's. Job 23477197 measured 0.201 s per forward on an A40, 1.06 times the A40 constant of 0.19.
The H100 constant of 0.0497 s is extrapolated from an H200 sweep and has never been measured on an H100. Scaled by the
same 1.06 it gives 0.0526 s per forward. Each file adds one model load, about 460 s from /ocean, and a few minutes of
batch building and mean bank.

| Job | Files | Forwards | Estimate at 0.0526 s | Reserved | Fits if the H100 rate is under |
|---|---|---|---|---|---|
| A | 2 x 84 sets | 194,420 | about 3.2 h | 03:30:00 | 0.058 s per forward |
| B | 2 x 84 sets | 194,420 | about 3.2 h | 03:30:00 | 0.058 s per forward |
| C | 63 sets | 72,622 | about 1.2 h | 02:00:00 | 0.090 s per forward |

The three jobs are about 7.6 GPU-hours at the central rate and reserve 9.0.

**Walltime risk.** The 03:30 reservations of A and B leave about 10 percent headroom. They hold only if the H100 runs
at least 3.5 times an A40. If it runs only 3 times an A40, the second file of A and of B is killed near 80 percent;
the first file of each still completes. A projected start at 1:26 pm EST was about 1:57 pm for any reservation up to
03:30 and 3:10 pm for 03:45 or 04:00, so a longer reservation costs over an hour of queue time.

**Recommendation.** Submit at 03:30 as planned. Read the per-cell `seconds` in job C's
`cells_partial.jsonl` about 15 minutes after the jobs start. If the measured rate is above 0.058 s per forward, cancel
A and B and resubmit each file as its own job at 02:00:00. Do the same if a second file is killed. Each finished cell
is in `cells_partial.jsonl`, but no code resumes from it, so a killed file reruns in full.

## Pilot numbers (job 23477197, before the review 02 fixes)

| Quantity | Value |
|---|---|
| State and runtime | COMPLETED, 679 s on a Delta A40, 30 of 30 cells |
| Measured rate | 0.201 s per forward |
| Self-replay error and twin cross-check | 0 and 0 |
| Intact G, D against its twin | 10.508 (ladder audit 10.087) |
| Intact G, I against user-neutral | 14.564 (ladder audit 14.979) |
| Intact rate at margin 0.7, D and I | 0.9375 and 1.0 |
| Intact IOI accuracy | 0.48 (brief 0.51) |

The pilot's IOI rows came from the old hash-seed-dependent draw. The fixed draw gives 100 rows with sentences sha256
`61ebeea317ac4932c0b859cc62b88ed0c45a7d6602d4866a9cf2373ee2cc5e59` under every hash seed. No model has run on those
rows yet. The R4 check against 0.51 therefore comes from the first full job, at
`sets.<any>.references.mean.conditions.IOI.accuracy_argmax_intact` in `summary.json`.
