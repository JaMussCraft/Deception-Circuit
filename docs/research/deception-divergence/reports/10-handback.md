# Hand-back 10: the D2 follow-up, amended plan and build

Written Mon 2 Nov 2026, about 11:55 pm EST, by the Opus worker `d2-worker` of direction `deception-divergence`,
under ruling R15. The lead asked for hand-back 09, but `reports/09-handback.md` already holds the plan reviewer's
hand-back, so this one is 10. No git, no Slurm job and no paid call.

## What changed

- **Plan amended to R15.** `plans/D2-followup-plan.md` now carries review 05's recommendations 1 to 14:
  - the SDR 15 and SDR 18 rewrites, SDR 02 no longer borderline, and the SER 13, 17 and 19 caveats;
  - the IH arm and its 30 clause pairs (new section 3.5);
  - per-task labels, then a direction label, with the signed 15-point rule;
  - the spread condition on the same ids with I's position beside it, and the leave-one-cluster-out condition;
  - the secondary interval clustered by I clause;
  - the refusal control on the same ids, with the validity bar on the ablated classifier;
  - the IH interaction condition, and SDR-alone (c) reported as suggestive;
  - the joint statistic `p_DT - p_HT` with relabelled cells;
  - the descriptive frame-family split and the B1 to B4 sensitivity refit;
  - the drift anchor, the pinned stack and the direction hash check;
  - fallback firing blocks submission, and the reservation is 00:45:00;
  - a statement that F8 and the D2 verdict stand whatever the result.
  The token-match tables in sections 3.3 to 3.5 are now rendered from the CPU dry run, not the scratch check.
- **Pool file.** New `data/d2/d2_followup_clauses.json` holds the 50 HI pairs and the 30 IH pairs. Each pair
  carries its forms, words changed, borderline reasons and caveats. The IH mirrors are rule-built, with "wrong" or
  "incorrect" becoming "correct" and "an incorrect" becoming "a correct", and the code checks that rule.
- **Code.** New `scripts/d2_followup.py` has three stages, `build --dry-run`, `features` and `read`. It imports
  `d2_premise.py` and `d2_rows.py` unchanged and reuses D2's feature, ablation, logistic regression, AUROC and
  bootstrap code. No D2 file changed.
- **Wrapper.** New `scripts/jobs/run_d2_followup.sh` runs `features` then `read`, or `build --dry-run` with
  `--dry-run`. Its header gives the Bridges-2 command.
- **Tests.** New `tests/test_d2_followup.py` has 43 tests.
- **Dry-run report.** New `results/d2_followup/build_report.json`.

| file | sha256 |
|---|---|
| `scripts/d2_followup.py` | `0b277047f5a50f49b3f071c87e66e50c970ed83ee6dfbff3a01fb8616e67f373` |
| `scripts/jobs/run_d2_followup.sh` | `b35f2d29d30b7f3ab62f94ac2df48ad2228e8090476c88c612a6c1c6395e24c4` |
| `tests/test_d2_followup.py` | `89fe9a30f1e0636386f7e09317ae43c874379560372ba8a28554e993f014438e` |
| `data/d2/d2_followup_clauses.json` | `9b8244d9aab323a9575242516566ab88262ea4c46d6fd060d346ee7f25be332a` |
| `results/d2_followup/build_report.json` | `56a55855517b9e3f9dd0d02453795b6d2b73e9718fd49dbe961cc7b98e0976ba` |

## How verified

- **The new tests.** On mgnp, all 43 pass. On the base interpreter, 79 pass across the three D2 files (43 new, 28
  premise, 8 rows), with BLAS threads pinned and no skips:

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_d2_followup.py
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 /sw/external/python/anaconda3/bin/python3.9 -m pytest \
    -p no:cacheprovider -q tests/test_d2_followup.py tests/test_d2_premise.py tests/test_d2_rows.py
```

- **What the tests cover.**
  - The pool rules and the R15 amendments, including a mirror that is dishonest, misformed, item-naming or a token
    longer.
  - The mirror pick and the salted fallback. A forced fallback makes the dry run exit 1 with
    `submission_blocked: true`.
  - Every condition's row text, and the anchor row equal byte for byte to D2's own row.
  - Fit, alignment and token checks on real FAR rows, and the pre-registered row counts.
  - The per-task label for every condition, SER as (a) or (b) only, and the direction label including SDR alone.
  - The joint cells.
  - Synthetic reads giving (c), (a), a negative gap as (b), the IH interaction blocking (c), and the refusal
    validity bar blocking (c).
  - The drift anchor stopping the read above 0.25. A D2 file that no longer matches its manifest also stops it.
  - The features stage on the tiny model. A wrong direction hash stops it before any feature. With D2's own
    features computed on the same model, the anchor reproduces them exactly (maximum difference 0.0).
  - The wrapper.
- **Full suite on mgnp.** See Execution evidence.
- **Full-scale read.** A scratch read on stand-in follow-up files exercised the read stage on the real ids. The
  stand-ins were built from D2's own rows, with HI taken from H, DT from D, HT from H and IH from I. It ran in
  1.3 s. With HI equal to H, `C_HI` is D2's `C_H`, and the act-form gaps reproduce D2's: FAR 0.005 and SDR 0.000.
  These files are scratch and are not a result.
- **Lint.** `research-session lint` passes on the plan and this hand-back.

## Execution evidence

The CPU dry run through the wrapper, on the Delta login node:

```
D2_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python DC_CLUSTER=delta bash scripts/jobs/run_d2_followup.sh --dry-run \
    --out-root /u/swong2/.claude/jobs/5b9b1c28/tmp/fu_dry \
    --report docs/research/deception-divergence/results/d2_followup/build_report.json
```

The run exited 0 with an empty `blocked` list. It reproduces plan section 3.4 and every row count:

| arm | far_v2 | sdr_v2 | ser_v2 | total |
|---|---|---|---|---|
| D anchor (train) | 200 | 200 | 200 | 600 |
| HI unablated | 610 | 650 | 649 | 1,909 |
| DT | 210 | 250 | 249 | 709 |
| HT | 210 | 250 | 249 | 709 |
| IH | 210 | 35 | 0 | 245 |
| HI ablated | 410 | 450 | 449 | 1,309 |
| total | 1,850 | 1,835 | 1,796 | 5,481 |

- **Picks.** Every HI row took its own mirror, with zero fallback firings on every task and split. Every IH row
  took its mirror. The pool has no violations.
- **Checks.** Every HI row is aligned with D (1,909) and every IH row with I (245). Every HT row is aligned with DT
  (709). DT minus D and HT minus D tokens are 0 on all 709 test ids. There are no form mismatches and no multi-token
  true items.
- **Forms.** The D forms per split match the scratch check exactly. For example, SDR test has 35 act, 166 predicate
  and 49 other.
- **Estimate.** At the measured D2 rates it is 1,655 s, or 0.46 GPU-hours. By the model constant it is 2,447 s, or
  0.68 GPU-hours. Both equal review 05's figures. The reservation is 00:45:00.
- **Refusal direction.** The local `refusal_direction.pt` hashes to the pinned
  `3e03edcd4b0458be2ce4a8a73468fcbf7ad33047b9c52bb018c1ff81f0bf7cf0`.
- **CPU time.** 12.4 s FAR, 14.1 s SDR and 11.6 s SER. The job's features stage repeats the picks and fit tests
  before the model loads, so the first half-minute or so of the job is CPU work inside the reservation.

**Full suite on mgnp.** A serial run projected about 5 hours, so I stopped it at 3 percent. The suite then ran as
six parallel shards split by file, each with its own basetemp and two BLAS threads
(`/u/swong2/.claude/jobs/5b9b1c28/tmp/shard_suite.py`). It took 781 s over 152 files.

| outcome | count |
|---|---|
| passed | 3,833 |
| failed | 22 |
| errors | 101 |
| skipped | 23 |

- **The 8 worktree baseline names all fail as known.** They are the MASK repo-root test, the three
  `test_deception_common` word-reuse cases, its length-matching and `test_pressure_pools_are_well_formed[ser]` and
  `test_three_specs_registered` tests, and `test_deception_tasks::test_hyperparameters_are_identical_across_the_three_mechanisms`.
- **The other 14 failures and 101 errors sit in other directions' tests.** These are `test_sdr_completion_diagnostic`,
  `test_sdr_cue_circuits`, `test_sdr_cue_positions`, `test_sdr_cue_probe`, `test_sdr_routing_validation`,
  `test_sdr_shared_composition`, `test_selective_v6_manifest`, `test_selective_v7` and `test_end_to_end`. 112 of
  these 115 stop on a `FileNotFoundError` for an artifact absent from this worktree, under `.superpowers/sdd/`,
  `outputs/_analyses/sdr-*` or `.claude/worktrees/.scratch/selective-deception/`. The other three are
  `test_end_to_end` cases that stop on `IndexError: index out of range in self`.
- **None of them involves this build.** No existing test imports `d2_followup` or the new pool file, and no existing
  file changed in this round. I did not rerun them at the parent commit, so "pre-existing" rests on that argument,
  not on a measured baseline for the newer files.

**Job command.** Run it from the Bridges-2 clone after the branch is pushed and synced
(`scripts/remote/b2.sh sync-code --branch deception-divergence`). A dry run on the Bridges-2 login node first checks
the clone, its data and the stored direction there:

```
cd /ocean/projects/cis260361p/swong2/Deception-Circuit
DC_CLUSTER=bridges2 bash scripts/jobs/run_d2_followup.sh --dry-run --out-root /tmp/d2fu_dry --report /tmp/d2fu_dry/build_report.json
sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p -A cis260361p -p GPU-shared \
    --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 00:45:00 --job-name=d2-followup \
    scripts/jobs/run_d2_followup.sh
```

Then, from Delta:

```
DC_DELTA_REPO_ROOT=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence \
    scripts/remote/b2.sh fetch outputs/_analyses/deception-divergence/d2_followup
```

The job needs D2's `outputs/_analyses/deception-divergence/d2/` in the Bridges-2 clone. That covers the six
feature files with their manifests and `refusal_direction.pt`. Job 50155519 wrote them there, and the wrapper
refuses to start if the direction is missing.

## What is NOT done

- **No job.** Nothing was submitted, synced, fetched or committed, and no GPU feature exists yet.
- **The anchor on the real stack is untested.** It is tested only on the tiny model. The pinned-stack refusal can
  only fire on the cluster; on Delta's login node there is no GPU.
- **Readings are untested on real follow-up features.** The read has run only on synthetic records and on the
  scratch stand-in files.
- **The Bridges-2 dry run** has not been run.

## Open questions

1. **Validity bar ids.** The ablated AUROC that gates (c) is computed on the same act-form test ids as the gap,
   following R15's "on the same ids". The all-ids AUROC is reported beside it. Please confirm.
2. **IH interaction.** "Holds" is coded as the clustered interval of
   `(z_D - z_I) - (z_HI - z_IH)` lying above zero. This equals R15's I minus IH read beside D minus HI. The frame
   share is reported, not thresholded. Please confirm.
3. **Hand-back number.** This is 10 because 09 was taken. Any reference to "hand-back 09" for the build should
   point here.
