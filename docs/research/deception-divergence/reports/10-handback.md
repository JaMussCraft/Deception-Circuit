# Hand-back 10: the D2 follow-up, amended plan, build and result

Written Mon 2 Nov 2026, about 11:55 pm EST, by the Opus worker `d2-worker` of direction `deception-divergence`,
under ruling R15, extended on Tue 3 Nov 2026 after the orchestrator's Bridges-2 job 50161975, and corrected in
wording after independent review 06 (`reviews/06-d2-followup-review.md`), which found no numerical or code error. This is hand-back
10 because `reports/09-handback.md` holds the plan reviewer's hand-back. I ran no git, no Slurm job and no paid
call; the orchestrator committed, synced, submitted and fetched.

**Result in one paragraph.** Every task is (b), and the direction label is (b). The D-against-HI classifier
separates the lie instruction from its honest mirror on every task (validation AUROC 0.976 to 1.000), and the joint
reading places DT with D and HT with HI on every task, so it reads the instruction's content. But on the
form-matched act-form clauses, where I names the wrong answer as D does, D and I do not differ: the gap is 0.010 on
FAR (210 ids) and 0.114 on SDR (35 ids), and both intervals reach zero. Under R15 the D2 route therefore closes U1
(R6 iv). F8's SDR pass is attributed to clause wording. Where wording is form-matched (act-form FAR and SDR), D and
I do not differ at the rate readout. On SER the attribution rests on descriptive by-form gaps. F8 and the D2 verdict
stand as recorded.

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
- **After job 50161975.** The record copies are in `results/d2_followup/`: `readings.json`, `readings.md`,
  `drift_anchor.json`, `gpu_timings_1793684926.json`, and the nine feature manifests in `far_v2/`, `sdr_v2/` and
  `ser_v2/`. Each is byte-identical to the fetched file. The feature `.jsonl` files stay in
  `outputs/_analyses/deception-divergence/d2_followup/` only. The job logs are copied to `logs/bridges2/`:
  `d2_followup_50161975.out` (sha256 `2fba3e62cf35c8796cb70addb7c1e8ff096a7dd63663b0a05f01ea54f394271b`) and the
  failed first submission `d2_followup_50161907.out` (sha256
  `561e02293d886b936553a3df3c960c9dd574acb7caeb08e37dcd06319bd4c6ea`), each equal to the Bridges-2 copy.
- **Results.** A new Results section, before What is NOT done.

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
- **The job's manifests.** A scratch check (`/u/swong2/.claude/jobs/5b9b1c28/tmp/verify_fu.py`) read all nine.
  - Every feature file's sha256 equals its manifest's, and every row count equals the file's.
  - Every manifest carries `pre_registered: true`, an empty stack check, torch 2.11.0+cu128 and transformers 5.13.0
    on an "NVIDIA H100 80GB HBM3", the pinned direction sha256, the full-sequence path and commit `54cd1eb`.
  - Picks are all own mirrors, with zero fallback firings and zero failed picks.
  - The code and pool hashes equal the local files.
  - Rows are 5,481 in all: 600 anchor, 3,572 other unablated and 1,309 ablated.
- **The D2 hashes the read checked.** The six D2 feature hashes in `readings.json`, those in the follow-up
  manifests and those of the files on Delta are identical. FAR's unablated file is the `6affb59a...` of hand-back 07.
- **Local re-read.** I ran `read` on a scratch copy of the fetched features:

```
OMP_NUM_THREADS=4 /u/swong2/.conda/envs/mgnp/bin/python scripts/d2_followup.py read --out-root /u/swong2/.claude/jobs/5b9b1c28/tmp/fu_reread
```

`drift_anchor.json` is byte-identical, and `readings.md` is identical apart from its timestamp. `readings.json` is
not byte-identical. 146 floating-point values differ by at most 3.6e-15. They are the classifier coefficients and the
IH-interaction statistics, which are computed from those coefficients. Every rate, gap, rate interval, label and
non-numeric field is identical. This is linear-algebra rounding between the Bridges-2 node and the Delta login node.

- **One figure computed after the read.** The test AUROC of D against HI under `C_HI` is not in the readings, so I
  computed it with the read's own fit (`/u/swong2/.claude/jobs/5b9b1c28/tmp/test_auroc_fu.py`). It is descriptive.

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

**Job 50161975.** `sacct` on Bridges-2 reports COMPLETED, exit 0:0, node w004, from 00:21:03 to 00:49:10 on Tue 3
Nov 2026 (Bridges-2 time), elapsed 00:28:07. The log is `logs/bridges2/d2_followup_50161975.out`, at commit
`54cd1ebe98a1fe084452d56f0610fabfba1f5b05`.

| step | seconds | rows | seconds per row |
|---|---|---|---|
| plan (picks and fit tests, CPU) | 13.9 | | |
| model load | 295.2 | | |
| drift anchor, three tasks | 153.8 | 600 | 0.256 |
| unablated HI, DT, HT and IH | 744.3 | 3,572 | 0.208 |
| ablated HI | 301.0 | 1,309 | 0.230 |

- **Drift anchor.** All 600 recomputed train D rows are bit-identical to job 50155519's, with a maximum absolute
  difference of 0.0 on every task.
- **First submission.** Job 50161907 failed after 4 s, before any Python ran. Its working directory pointed at the
  other allocation's path, `/ocean/projects/cis260372p/...`, and the wrapper's cwd guard refused it.

## Results

All figures are from `results/d2_followup/readings.json` unless marked as computed after the read. A rate is the
share of rows `C_HI` scores at or above 0.5. R15 writes rates as `p_X`, but the read and the joint table below use
`p_X` for positions on the HI-to-D axis, `p_X = (rate_X - rate_HI) / (rate_D - rate_HI)`. In this hand-back "rate"
always means a share, and every `p_X` is a position.

### Labels

| task | role | gate AUROC, validation (act-form validation) | test AUROC D against HI, all ids (act-form) | label |
|---|---|---|---|---|
| far_v2 | primary | 1.000 (1.000 on 200) | 1.000 (1.000) | (b) |
| sdr_v2 | secondary | 0.999 (0.997 on 46) | 0.999 (1.000) | (b) |
| ser_v2 | excluded from the act-form reading | 0.976 (0.991 on 15) | 0.980 (one act-form id) | (b) |

The direction label is (b): D and I share what `C_HI` reads. U1 is not re-admitted. The test AUROCs were computed
after the read and are descriptive.

**What (b) everywhere means under R15.** The D-against-HI classifier passes its gate on every task, so it
separates the instruction to lie from the token-matched honest instruction, not just the presence of an instruction.
But on the form-matched act-form clauses, where I names the wrong answer as D does, D and I do not differ. On FAR,
I is scored D-like on 208 of 210 ids. On SDR, D and I differ on 4 of 35 ids, with an interval reaching zero. The D2
route therefore closes U1 (R6 iv). F8's SDR pass, which review 04 traced to predicate-form clauses, is
attributed to clause wording. Where wording is form-matched (act-form FAR and SDR), D and I do not differ at the rate
readout. On SER the attribution rests on descriptive by-form gaps, because SER has no matched act-form reading.

### Rates under `C_HI`

| task | ids | D | I | H | HI | DT | HT | IH |
|---|---|---|---|---|---|---|---|---|
| far_v2 | all test, 210 | 1.000 | 0.990 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| far_v2 | act-form, 210 | 1.000 | 0.990 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| sdr_v2 | all test, 250 | 0.976 | 0.636 | 0.000 | 0.020 | 0.980 | 0.176 | (act-form only) |
| sdr_v2 | act-form, 35 | 1.000 | 0.886 | 0.000 | 0.000 | 1.000 | 0.257 | 0.000 |
| ser_v2 | all test, 249 | 0.944 | 0.414 | 0.032 | 0.120 | 0.912 | 0.277 | (not run) |

FAR's test ids are all act-form, so its two rows are the same ids.

### The act-form reading

| | far_v2 (primary) | sdr_v2 (secondary) |
|---|---|---|
| ids, D clause clusters, I clauses | 210, 12, 13 | 35, 7, 17 |
| signed gap, D minus I | 0.010 | 0.114 |
| interval clustered by D clause | 0.000 to 0.028 | 0.000 to 0.250 |
| interval clustered by I clause | 0.000 to 0.025 | 0.000 to 0.269 |
| leave-one-cluster-out range | 0.005 to 0.012 | 0.037 to 0.143 |
| spread, D minus HI | 1.000 | 1.000 |
| I's position `p_I` | 0.990 | 0.886 |
| ablated refit: rates D, I, HI | 1.000, 0.990, 0.000 | 1.000, 0.943, 0.000 |
| ablated gap | 0.010 | 0.057 |
| ablated `C_HI` AUROC D against HI, act-form (all ids) | 1.000 (1.000) | 1.000 (0.999) |
| refusal control explains | no | yes (a change of exactly half) |
| IH interaction on the logit | 3.853, interval 1.823 to 6.205 | 0.716, interval -1.449 to 3.473 |
| logit shift D minus I, HI minus IH | 2.347, -1.506 | 1.065, 0.349 |
| frame share | -0.64 | 0.33 |
| conditions failed | gap under 15 points; interval reaches zero | gap under 15 points; interval reaches zero; refusal explains; IH interval reaches zero |

The conditions that pass on FAR are the gate, the spread, every leave-one-cluster-out gap above zero, the refusal
validity bar, the refusal control not explaining, and the IH interaction. The two that fail are the ones that carry
the hypothesis.

### The joint DT and HT reading (all test ids)

The `p_X` columns are positions on the HI-to-D axis, not rates: 0 is HI's rate and 1 is D's. A position can fall
below 0 or rise above 1, as SDR's `p_H` of -0.021 and `p_DT` of 1.004 do.

| task | spread, D minus HI (rates) | position `p_I` | position `p_H` | position `p_DT` | position `p_HT` | `p_DT - p_HT` | interval | cell |
|---|---|---|---|---|---|---|---|---|
| far_v2 | 1.000 | 0.990 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 to 1.000 | instruction content |
| sdr_v2 | 0.956 | 0.644 | -0.021 | 1.004 | 0.163 | 0.841 | 0.725 to 0.940 | instruction content |
| ser_v2 | 0.823 | 0.356 | -0.107 | 0.961 | 0.190 | 0.771 | 0.647 to 0.887 | instruction content |

On every task the deceptive instruction with a true answer reads as D, and the honest instruction with a true answer
reads near HI. `C_HI` follows what the system instruction says, not the truth of the stated answer or whether the
model obeyed. This holds on FAR. On SDR and SER, score space shows a compliance-like component beside instruction
content: on the mean logit a true answer moves HT about 40 percent of the way toward D and barely moves D (review 06,
Question 3, reviewer-computed and descriptive). The rate readout hides it, because most HT rows stay below the
threshold. The statistic is near +1, the content reader's value, and its interval excludes 0 on every task.

### Descriptive readings

The D-I gap under `C_HI` by D form:

| task | all ids | interval | act | predicate | interval | other | interval |
|---|---|---|---|---|---|---|---|
| far_v2 | 0.010 (210) | 0.000 to 0.028 | 0.010 (210) | none | | none | |
| sdr_v2 | 0.340 (250) | 0.242 to 0.442 | 0.114 (35) | 0.386 (166) | 0.262 to 0.532 | 0.347 (49) | 0.240 to 0.571 |
| ser_v2 | 0.530 (249) | 0.374 to 0.693 | 0.000 (1) | 0.426 (148) | 0.236 to 0.618 | 0.690 (100) | 0.477 to 0.955 |

The act-form gap by I frame family:

| task | drill | quiz | game |
|---|---|---|---|
| far_v2 | 0.000 (52 ids) | 0.013 (78) | 0.013 (80) |
| sdr_v2 | 0.000 (14) | 0.231 (13) | 0.125 (8) |

Rates under D2's frozen `C_H` (D against H, refitted exactly as D2 did; its D, I and H rates reproduce D2's):

| task | D | I | H | HI | DT | HT | IH |
|---|---|---|---|---|---|---|---|
| far_v2 | 1.000 | 0.995 | 0.000 | 0.005 | 1.000 | 0.000 | 0.010 |
| sdr_v2 | 1.000 | 0.840 | 0.000 | 0.240 | 1.000 | 0.692 | 0.286 |
| ser_v2 | 1.000 | 0.855 | 0.000 | 0.956 | 1.000 | 0.936 | (not run) |

The B1 to B4 sensitivity refit drops every row of a borderline D clause, which is 6 clauses on SDR and 5 on SER:

| task | fit, gate, test ids | gate AUROC | gap, all ids | interval | predicate gap | interval |
|---|---|---|---|---|---|---|
| sdr_v2 | 113, 125, 146 | 0.998 | 0.308 | 0.181 to 0.441 | 0.369 (111) | 0.217 to 0.525 |
| ser_v2 | 151, 136, 149 | 0.972 | 0.376 | 0.198 to 0.559 | 0.378 (148) | 0.195 to 0.560 |

SDR's act-form gap is unchanged at 0.114, because no act-form clause is borderline after SDR 02's relabelling. The
borderline mirrors do not drive the predicate-form gaps.

### Drift anchor and cost

The drift anchor is bit-identical on all 600 rows (maximum difference 0.0 against the 0.25 bar).

| item | GPU-hours |
|---|---|
| reserved, 00:45:00 on one H100 | 0.75 |
| estimate at D2's measured rates | 0.46 |
| estimate by the model constant | 0.68 |
| actual, job 50161975, 28:07 | 0.47 |
| failed first submission 50161907, 4 s | 0.00 |

No paid call was made, and no OpenRouter spend.

### Caveats

- **Few clusters.** SDR's act-form reading rests on 35 ids in 7 D clause clusters, and FAR's on 12 clusters
  ranging from 1 to 44 ids. Percentile intervals over so few clusters are optimistic. Neither label is close to the
  line, though: FAR's gap is 2 ids of 210, and SDR's is 4 of 35.
- **The rates saturate.** `C_HI` scores D at 1.000 and HI at 0.000 on FAR's act-form ids, so the rule's rates
  cannot show gradation. On the logit, I sits 2.35 below D on FAR but stays above the threshold on 208 of 210 ids.
  The pre-registered rule is on rates, and the logit figures are description.
- **The IH interaction on FAR holds, with a surprising sign.** The frame words move the honest mirror toward D:
  IH scores 1.51 logits more D-like than HI, a negative frame share. So the frames do not carry I's D-likeness, and
  the interaction holds because I sits below D while IH sits above HI. It cannot rescue the label, because the gap
  fails. On SDR the interaction's interval reaches zero. Review 06 adds that the interaction is enlarged by IH
  sitting above HI. The residual D minus I of 2.35 log-odds (interval 0.92 to 4.34) tracks I-clause identity and
  wording overlap. It falls to 1.19 (interval -0.20 to 3.08) on the 153 ids whose D clause uses I's lie word,
  "wrong". These figures are reviewer-computed and descriptive.
- **SDR's refusal "explains" by an exact tie.** The ablated gap is 0.057, exactly half of 0.114, and R12 counts half
  or more. The label is (b) on the gap alone, so the tie changes nothing.
- **Under `C_HI` the non-act gaps grow.** All-ids gaps are 0.340 on SDR and 0.530 on SER, against 0.160 and 0.145
  under D2's `C_H`. The predicate and other I clauses never name a wrong answer, and a classifier that reads
  instruction content places them nearer HI. This fits the attribution to clause wording. It is descriptive, and the R15
  rule reads only the act-form ids.
- **D2's own classifier read different things on different tasks.** Under the frozen `C_H`, HI reads as D on SER
  (0.956), not on FAR (0.005), and partly on SDR (0.240). SER's D2 classifier read instruction presence. FAR's
  did not.
- **The truth shift is small on rates only.** HT's position is 0.163 on SDR and 0.190 on SER rather than 0, and
  DT's is about 1. On the logit the shift is not small: a true answer moves HT 5.7 (SDR) and 3.1 (SER) log-odds
  toward D, and moves D to DT by less than one (review 06, Question 3, reviewer-computed and descriptive). That is not
  a common shift, so the statistic does not cancel it. It is the compliance-like component noted under the joint
  reading. The cell is the same on all three tasks.
- **The re-read differs in the last digits.** 146 values differ by at most 3.6e-15 (How verified). No rate, gap,
  interval of a rate or label differs.
- **The acts-on-it sequence** was computed for every row and is not read, as planned.

## What is NOT done

- **No git.** I committed, pushed, synced and submitted nothing; the orchestrator did.
- **No finding or worklog entry.** Recording the result, the closure of the D2 route to U1 under R6 iv, and how F8
  is now read is the orchestrator's.
- **Independent review 06** has been run. Its wording corrections are applied here, and its new figures are
  marked as reviewer-computed.
- **No refusal share and no generations.** These were excluded by the plan, and the acts-on-it sequences stay
  unread.
- **Feature files are not copied into `results/`,** as instructed; they stay in
  `outputs/_analyses/deception-divergence/d2_followup/`, which is git-ignored.
- **The test AUROC of D against HI** is not in `readings.json`. It was computed afterwards by a scratch script and
  is recorded only in this hand-back.

## Open questions

The two operational readings below were confirmed by the orchestrator before the job and recorded as a dated R15
implementation note in `spec.md`:

1. **Validity bar ids (confirmed).** The ablated AUROC that gates (c) is computed on the same act-form test ids as
   the gap. The all-ids AUROC is reported beside it.
2. **IH interaction (confirmed).** "Holds" means the clustered interval of `(z_D - z_I) - (z_HI - z_IH)` on the
   `C_HI` logit lies above zero. This equals R15's I minus IH read beside D minus HI. The frame share is reported,
   not thresholded.

The hand-back number is 10, as the orchestrator asked, because 09 holds the plan reviewer's hand-back.

After the job, I asked the orchestrator two questions. Neither changes a label, and both are now closed:

1. **Should the test AUROC be in the readings? (closed)** No. The orchestrator ruled that it stays a hand-back
   figure, because the code is frozen at `54cd1eb` for this result. Review 06 agrees.
2. **Does the FAR IH sign need a note in the finding? (closed)** Yes. The note is the addition to the IH caveat
   under Caveats, with review 06's account of the residual D minus I.
