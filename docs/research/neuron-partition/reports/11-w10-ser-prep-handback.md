# Hand-back 11: W10, SER preparation on CPU (pools, exclusions, sample, job lines)

Agent: implementation worker W10 (Claude, Opus). Ticket: the team lead's W10 brief of Wed 4 Nov 2026 ("Prepare SER
on CPU"), against item 10 of `docs/research/neuron-partition/START.md` ("Tasks", "Ids", "Nulls"). Status: resolved,
with two rulings needed before any SER GPU job (Open questions 1 and 2). Nothing was submitted. Written Wed 4 Nov
2026, about 11:00 am EST.

`WT` is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition`.

## What changed

Committed by the orchestrator from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/scripts/neuron_partition_data.py`.
  `copy-pools` and `sample` gain `--task {far,ser}` (default far).
  - **`sample --clause-form {act,predicate,other,all}`.** It names the D clause forms kept. Pool rows take the form
    of the D row with the same id. FAR defaults to `act`, and SER has no default: `sample --task ser` without the flag
    stops and names it.
  - **SER file names.** The pool copies are recorded in a new manifest, `pools_manifest_ser.json`, so FAR's
    `pools_manifest.json` is never rewritten. The sample is `ser_<form>_test_sample_seed<seed>.json`, and the rank
    ids are `ser_<form>_rank_ids.json`.
  - **The rank file for any task but FAR** also holds `rank_all` and `rank_all_I`, flat id lists, plus
    `clause_form`. A form filter drops ranking rows, so the full SER ranking needs `--ids ... --ids-key rank_all`.
    FAR's full ranking omitted `--ids`.
  - **FAR is byte-identical.** The FAR files keep their names, layout and bytes (How verified, item 2).
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/tests/test_neuron_partition_data.py`.
  It gains 7 tests, for 30 in total:
  - SER form filters;
  - the explicit-form refusal;
  - the SER end-to-end draw, with its names, filter and `rank_all`;
  - FAR's legacy layout;
  - SER `copy-pools` writing its own manifest;
  - the written SER samples' id contract, for predicate and all.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/jobs/all_position_attribution_ser.sbatch`
  (new, executable). It adapts the FAR all-position job to SER. It takes `<commit> <predicate|all> [--dry-run]`, and the
  form picks the rank file and the output tag.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/11-w10-ser-prep-handback.md`
  (this file).

Outputs, git-ignored, under `WT/outputs/_analyses/neuron-partition/data/`:

| file | sha256 |
| --- | --- |
| `pools/ser_v2_user_inversion/`, `pools/ser_v2_user_neutral/` | 17 files each, hashed in `pools_manifest_ser.json` |
| `pools_manifest_ser.json` | `bc357ed1cf1f7121bd017ac5551956d8d1f69c4bc961e5dc59697ceaf12282a6` |
| `ser_predicate_test_sample_seed2.json` | `06a2dd938f082673eeaa5ca80f0fdd4964fc448ee2d0559a27ddc7dc9670a994` |
| `ser_predicate_rank_ids.json` | `6acd2f4df83520c9ce7037fa7cb3856a7762ef6b751bd1840582148c538e4ec8` |
| `ser_all_test_sample_seed2.json` | `c066447d6c0b10a3a3b822946ed21e0a5f1e9d0b3983d55eb68de28ba2fcabf4` |
| `ser_all_rank_ids.json` | `1a634f3a31c4389df913e734205a684ae60d25c70354b94f12666cb029d0f83c` |

`pools_manifest.json` (FAR) is unchanged at `7d9b185d…0a3f`. Scratch files are in
`WT/outputs/_analyses/neuron-partition/w10_tmp/`: probes, dry-run logs, count files and the FAR byte check.
Nothing is staged for the apply tool.

### Pools

Both pools are full copies of
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a1-control-77b6487-m07/ser_v2_user_{inversion,neutral}`.
That is unmerged Codex data, read only at the source, the same cell FAR's pools came from.

| pool | train | validation | test | provenance check |
| --- | --- | --- | --- | --- |
| ser_v2_user_inversion | 168 | 167 | 835 | 16 of 16 listed files match; the 17th is the provenance file |
| ser_v2_user_neutral | 168 | 167 | 835 | 16 of 16 listed files match |

The six arrow sha256 values equal the reader brief's table, section 3:

| arrow | train | validation | test |
| --- | --- | --- | --- |
| inversion | `cc246ec7…` | `184a90d6…` | `495c4275…` |
| neutral | `6e41400b…` | `948ccf52…` | `79371a00…` |

I and N carry the same ids in the same order in every split. Every pool id is a ser_v2 id of the same split.

### Exclusions

They are assembled exactly as for FAR under R5 and R12: the union of four lists, 360 ids, all in the test split.

| list | path and key | sha256 of file | n | in D test | in I test |
| --- | --- | --- | --- | --- | --- |
| A1 assessment | ladder `ladder-5f450dc/design.json`, `payload.designs.ser_v2.assessment_ids` | `fe8d3887…554a0d` | 100 | 100 | 100 |
| A1 selection (R12) | same file, `payload.designs.ser_v2.mover_selection_ids` | `fe8d3887…554a0d` | 100 | 100 | 86 |
| mechanism held-out D | `docs/research/mechanism-analysis/phase1/groups/ser_heldout_D_sample.json` | `6e70de15…2213ff` | 100 | 100 | 88 |
| mechanism held-out I | `.../ser_heldout_I_sample.json` | `9c440337…41e2ee` | 100 | 100 | 85 |
| `docs/research/held_out.json` | `sets` is empty | `801b24e3…70425e` | 0 | 0 | 0 |
| union | | | 360 | 360 | 320 |

- **Ladder path.** The ladder design is at
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json`.
  Its `selected.json` `screen.selection_ids` for ser_v2 equals `mover_selection_ids`.
- **Mechanism-analysis selection sample.** The reader brief's extra column used the sample in primary
  `outputs/_analyses/mechanism-analysis-p1/s1/U__leaf/ser_v2/sample.json`. All 100 of its ids lie inside the union, so
  it removes nothing more and is not a fifth list.

### The clause-form question (blocker 4)

START item 10 reads "FAR primary (act-naming clauses only), SER secondary". The reader brief's blocker 4 applies the
act-naming filter to SER. Applied to SER, it leaves too few rows:

| D clause form, test split of 1,000 | rows | D eligible after exclusions | I eligible | rank D (train + validation) | rank I |
| --- | --- | --- | --- | --- | --- |
| act-naming | 72 | 49 | 42 | 34 | 29 |
| predicate-naming | 695 | 463 | 353 | 253 | 201 |
| other | 233 | 128 | 120 | 113 | 105 |
| all | 1,000 | 640 | 515 | 400 | 335 |

- **Act-naming only is infeasible.** It leaves 49 D and 42 I test ids against the 300 floor, and it would rank on 34
  rows.
- **Wording.** All 835 SER I rows use one predicate-naming request, `ser_quiz_v1`: "knowingly recommend the
  favorable result instead of the unfavorable result; I understand this is the opposite selection." FAR's I request is
  act-naming ("intentionally wrong"), so act-naming FAR D was the wording-matched twin of FAR's I. On SER the
  wording-matched D subset is the predicate-naming one.
- **Both feasible readings are built,** each 300 rows per condition with seed 2:

| sample | D, H, F | I, N | D and I overlap | D eligible | I eligible | rank D (halves A / B) | rank I (halves A / B) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| predicate | 300 | 300 | 201 | 463 | 353 | 253 (127 / 126) | 201 (97 / 104) |
| all | 300 | 300 | 153 | 640 | 515 | 400 (200 / 200) | 335 (174 / 161) |

Both draws fill all 8 strata of the balanced sampler, and D gets 38 or 37 per stratum under both forms. One I stratum
is short under predicate: it holds 30, and the sampler hands the surplus to the others, which get 38 or 39. No row
lacks a twin. The halves are W3's rule, stratified by pressure_id with seed 2. The predicate sample spans 8 of SER's
17 test pressure ids in both D and I, and the all-forms sample spans 16.

### Job lines, not submitted

Placeholders: `<C>` is the short commit the job runs, and `<form>` is `predicate` or `all` per the ruling. `ATT` is
`WT/outputs/_analyses/neuron-partition/attribution`, and `SETS` is `WT/outputs/_analyses/neuron-partition/sets`.

**(a) Ranking, Delta interactive, 30 minutes.** Submit from `WT` after committing the new script:

```
sbatch --account=beto-delta-gpu --partition=gpuH200x8-interactive,gpuA40x4-interactive --time=00:30:00 docs/research/neuron-partition/jobs/all_position_attribution_ser.sbatch <C> <form>
```

It runs the FAR job's six python calls:

- full: `dh in`, then `dh in --reverse`, both with `--ids ser_<form>_rank_ids.json --ids-key rank_all`;
- per half: `dh in` and `dh --reverse`, with `--ids-key halves.A` or `halves.B`.

The output directories are `ATT/ser_v2_{dh,in}_train+validation_<form>[_half{1,2}]_<C>[_rev]`.

**(b) Partition, CPU, after (a).** These are W4's commands with `--position all`, the ladder 500, 1,000 and 2,000 by
default, and 20 nulls per class at seed 2 by default. The file prefix `ser` comes from the scorer's provenance.

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_sets.py partition --position all --dh ATT/ser_v2_dh_train+validation_<form>_<C>_rev --in ATT/ser_v2_in_train+validation_<form>_<C> --dh-reverse ATT/ser_v2_dh_train+validation_<form>_<C>_rev --label "SER <form> full ranking, train+validation, AtP all positions (R11 primary)" --out-dir SETS/ser_<form>_atp_all_<C>
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_sets.py stability --position all --dh ATT/ser_v2_dh_train+validation_<form>_half1_<C>_rev ATT/ser_v2_dh_train+validation_<form>_half2_<C>_rev --in ATT/ser_v2_in_train+validation_<form>_half1_<C> ATT/ser_v2_in_train+validation_<form>_half2_<C> --dh-reverse ATT/ser_v2_dh_train+validation_<form>_half1_<C>_rev ATT/ser_v2_dh_train+validation_<form>_half2_<C>_rev --label "SER <form> split halves, AtP all positions (R11 primary)" --out-dir SETS/ser_<form>_atp_all_<C>
```

The readout comparison of R11 is the same pair without `--position all`, into `SETS/ser_<form>_atp_readout_<C>`.
The ablation input is `SETS/ser_<form>_atp_all_<C>/ser_all_sets_k500_with_nulls.json`, with 4 classes and 80 nulls
if no class is empty. For the D_only variant, extract its 21 sets as W8 did for H_only:

```
/u/swong2/.conda/envs/mgnp/bin/python -c "import json; p='outputs/_analyses/neuron-partition/sets/ser_<form>_atp_all_<C>/'; g=json.load(open(p+'ser_all_sets_k500_with_nulls.json')); o={n: v for n, v in g.items() if n == 'D_only' or n.startswith('null_D_only_500_')}; assert len(o) == 21; json.dump(o, open(p+'ser_all_sets_k500_D_only_with_nulls.json', 'w'), indent=1)"
```

**(c) Ablation at k 500, Bridges-2 H100, `--ioi-rows 1000`.** All four classes plus nulls, 84 sets:

```
ssh -o BatchMode=yes bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p,PYTHONHASHSEED=0,NP_TASK=ser -A cis260372p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 02:00:00 --job-name=np-ablate-ser docs/research/neuron-partition/jobs/ablation_cells.sbatch outputs/_analyses/neuron-partition/sets/ser_<form>_atp_all_<C>/ser_all_sets_k500_with_nulls.json outputs/_analyses/neuron-partition/data/ser_<form>_test_sample_seed2.json outputs/_analyses/neuron-partition/ablation/ser_<form>_k500-<C> --max-length 136 --ioi-rows 1000'
```

D_only plus its 20 nulls, 21 sets, for a tight budget:

```
ssh -o BatchMode=yes bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p,PYTHONHASHSEED=0,NP_TASK=ser -A cis260372p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 00:45:00 --job-name=np-ablate-ser-d docs/research/neuron-partition/jobs/ablation_cells.sbatch outputs/_analyses/neuron-partition/sets/ser_<form>_atp_all_<C>/ser_all_sets_k500_D_only_with_nulls.json outputs/_analyses/neuron-partition/data/ser_<form>_test_sample_seed2.json outputs/_analyses/neuron-partition/ablation/ser_<form>_k500_D_only-<C> --max-length 136 --ioi-rows 1000'
```

- **`NP_TASK=ser` in `--export`.** It makes the wrapper pass `--task ser` and pick
  `data/pools/ser_v2_user_{inversion,neutral}`. Bridges-2 sets `SBATCH_EXPORT=NONE`, so it must be in the list.
- **`--max-length 136`, not 128.** R9's 128 raises on SER (How verified, item 5).
- **Prerequisites on Bridges-2.**
  - Sync the code to the commit.
  - Rsync these to the clone through b2dtn and compare sha256: `data/pools/ser_v2_user_*`, `data/pools_manifest_ser.json`,
    `data/ser_<form>_test_sample_seed2.json` and `sets/ser_<form>_atp_all_<C>/`.
  - W3 synced FAR data only. Bridges-2 goes offline about 9 Nov 2026.
- **Verdict line, CPU, after (c):**

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_verdict.py --cell outputs/_analyses/neuron-partition/ablation/ser_<form>_k500-<C> --sample outputs/_analyses/neuron-partition/data/ser_<form>_test_sample_seed2.json --d-dir data/datasets/ser_v2 --i-dir outputs/_analyses/neuron-partition/data/pools/ser_v2_user_inversion --output-dir outputs/_analyses/neuron-partition/verdict/ser_<form>_k500-<C>
```

The verdict and partition scripts are SER-ready. The verdict's FAR defaults are the three flags passed above, and the
partition script reads the task from the scorer's provenance. Neither has run on SER cells, because none exist. The
verdict's SER halves were exercised on both samples (How verified, item 6).

### GPU-hour estimates

The ranking scales FAR job 23478550, which took 482 s on an A40. Its row passes are 754 forward full, 754 reverse
full, 754 forward in the halves and 400 reverse in the halves, 2,662 in all. SER prompts are about 7 percent longer
(at most 130 tokens against 121).
The ablation figures come from the CLI's dry-run forward counts at the measured H100 rate. That rate is 0.041 s per
forward centrally and 0.046 at the high end (reports/06-w6-babysit-handback.md). The CLI scales it by max length over
128, and model loads take 460 s centrally and 904 s at the high end.

| job | form | row passes or forwards | central | high | reserve | reserved GPU-h |
| --- | --- | --- | --- | --- | --- | --- |
| (a) ranking, A40 or H200 | all | 2,605 row passes | ~500 s, 0.14 GPU-h | ~0.2 | 00:30:00 | 0.5 |
| (a) ranking, A40 or H200 | predicate | 1,615 row passes | ~390 s, 0.11 GPU-h | ~0.15 | 00:30:00 | 0.5 |
| (b) partition | either | CPU | 0 | 0 | none | 0 |
| (c) 4 classes + 80 nulls | either | 116,698 forwards | 79 min, 1.32 GPU-h | 1.59 GPU-h | 02:00:00 | 2.0 |
| (c) D_only + 20 nulls | either | 30,072 forwards | 26 min, 0.44 GPU-h | 0.59 GPU-h | 00:45:00 | 0.75 |

The two samples have the same row counts, so (c) costs the same under either form. The full SER path is (a) plus
(c) with 84 sets: about 1.5 GPU-h central and 2.5 GPU-h reserved. The D_only path is about 0.6 GPU-h central and 1.25
reserved.

## How verified

1. The SER pool copy:

```
HF_DATASETS_OFFLINE=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_data.py copy-pools --task ser
```

Observed: "ser_v2_user_inversion: 17 files; provenance matched 16, mismatched 0, missing 0, not listed
['assembly_provenance.json']" and the same line for ser_v2_user_neutral, then "wrote
outputs/_analyses/neuron-partition/data/pools_manifest_ser.json sha256 bc357ed1…82a6". `sha256sum` over the six arrows
gave the brief's values.

2. FAR is byte-identical. Before editing, I ran the unmodified script's `copy-pools` and `sample` into
`w10_tmp/far_before/`. I then reran the edited script into the same directory:

```
HF_DATASETS_OFFLINE=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_data.py sample --out-dir /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/w10_tmp/far_before
```

Observed: identical sha256 before and after for all three files:

| file | sha256 |
| --- | --- |
| `far_test_sample_seed2.json` | `1309a567…48ce3` |
| `far_rank_ids.json` | `0e15dfa6…1da0a` |
| `pools_manifest.json` | `04c5bb1c…d4870` |

Their ids, halves and counts equal W3's committed-path files. The scratch hashes differ from W3's only by the paths
written inside the files. W3's real files were not rewritten.

3. Counts and draws:

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_data.py sample --task ser --clause-form {act,predicate,all} --count-only
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_data.py sample --task ser --clause-form {predicate,all}
```

Observed: the tables above. The predicate draw was run twice, and both runs gave the same two sha256 values.

4. Tests, with basetemp outside `outputs/_analyses`:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_neuron_partition_data.py -p no:cacheprovider -q -rf --basetemp=/projects/beto/swong2/.w10-5201d56c-tmp/bt1
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_neuron_partition_data.py -p no:cacheprovider -q -rf --basetemp=/projects/beto/swong2/.w10-5201d56c-tmp/bt2
```

Observed: "30 passed" on mgnp and "30 passed, 1 warning" on base. One earlier mgnp run placed basetemp under
`w10_tmp/`, inside `outputs/_analyses`. There `test_b2_fetch_brings_back_neuron_partition` failed, because every
rsync destination then contained `outputs/_analyses/`. That was my setup, not a regression. With basetemp moved, it
passes. `tests/test_neuron_partition_sets.py` and `tests/test_d4_jobs.py` gave "28 passed" on both interpreters.

5. Dry runs, login node, no GPU and no model:

```
bash docs/research/neuron-partition/jobs/all_position_attribution_ser.sbatch 3486f1a predicate --dry-run
bash docs/research/neuron-partition/jobs/all_position_attribution_ser.sbatch 3486f1a all --dry-run
```

Observed: all six calls pass for each form. The predicate form gave:

- full: dh 253 and in 201 rows, with "201 row(s) matched of 253 id(s); 52 listed id(s) not in this pool";
- half A: 127 and 97 rows;
- half B: 126 and 104 rows.

The all-forms run gave 400 and 335 full, 200 and 174 in half A, and 200 and 161 in half B. Every split reported 0
dropped by tokenization and 0 clause fallbacks, and no output directory was created.

```
NP_TASK=ser bash docs/research/neuron-partition/jobs/ablation_cells.sbatch outputs/_analyses/neuron-partition/sets/far_atp_all_c3d7763/far_all_sets_k500_with_nulls.json outputs/_analyses/neuron-partition/data/ser_predicate_test_sample_seed2.json <scratch> --dry-run --max-length 128 --ioi-rows 1000 --seconds-per-forward 0.041 --model-load-seconds 460
```

Observed: "ValueError: instance 009b87598258: the Readout is prefix_length - 1 = 128 but the last unpadded position is
127". SER prompts reach 130 tokens in the pools, against FAR's 121.

The same command at `--max-length 136` passed. I ran it on the predicate sample and the all-forms sample with FAR's
84-set k500 file as the stand-in, and on the predicate sample with the 21-set `ablation/ioi_resolution_sets.json`.
Each run reported:

- rows D, H, F, I and N 300 each, and IOI 1,000 (sentences sha256 `fec3aa49…`);
- 0 dropped by tokenization and every D and I row with its twin;
- totals "116698 forwards ... ~79.0 min" for 84 sets and "30072 forwards ... ~26.1 min" for 21 sets.

6. The verdict's halves on SER (R10), without a cell:

```
HF_DATASETS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python outputs/_analyses/neuron-partition/w10_tmp/check_halves.py
```

The script calls `sample_halves` of `scripts/neuron_partition_verdict.py` with the SER D dir and I pool. Observed:
the method is the rule ("split_halves ..., stratified by pressure_id"), not the fallback. Every twin takes its row's
half. The A / B counts are:

| sample | D, H, F | I, N |
| --- | --- | --- |
| predicate | 146 / 154 | 144 / 156 |
| all | 155 / 145 | 144 / 156 |

7. The ranking job's empty `--dry-run` array under `set -u` needs bash 4.4 or later. `rpm -q bash` on the Delta login
node gave `bash-5.1.8-9.el9.x86_64` (RHEL 9.6).

The pytest basetemp `/projects/beto/swong2/.w10-5201d56c-tmp/` was removed after the runs.

## Execution evidence

Not applicable: no runs.

Only CPU commands ran: the copies, the draws, the tests and the dry runs above. No GPU job and no sbatch was submitted,
and nothing was synced to Bridges-2.

## What is NOT done

- **No SER GPU job.** Nothing was submitted, by the brief.
- **No SER sets exist.** The partition commands of (b) need the ranking outputs of (a), so they were not run. The
  dry runs of (c) used FAR sets files as stand-ins; the forward count depends on the number of sets, not on k.
- **No sbatch `--test-only`** on either cluster, and no Bridges-2 sync of the SER data.
- **Act-only sample.** It was counted, not drawn, because it cannot meet the floor.

## Open questions

1. **The SER clause-form filter.** Which reading is binding for SER: predicate-naming only, or all forms?
   - The case for predicate: it is the wording-matched twin of SER's predicate-naming I request, as act-naming FAR D
     was of FAR's act-naming request.
   - The case for all: it is START's literal text, since the parenthetical names FAR only, and it gives more ranking
     rows (400 against 253).
   - Either way, a dated ruling in `spec.md` should record it before the SER ranking job.
   - Default: predicate, with all forms as the stated alternative.
2. **Max length for SER.** R9 fixes `--max-length 128`, which raises on SER. Default: a ruling that SER cells pass
   `--max-length 136`, which is lossless because truncation still raises.
3. **The SER ablation cell size.** It is a budget call. Default: all four classes plus nulls if the budget allows 2
   reserved GPU-hours, otherwise D_only plus nulls at 0.75. N2 on SER needs the H_only class, so the 84-set cell is
   the only one that serves both N1 and N2.
4. **The A3 cell overlap.** On SER, the Codex A3 cell covers layers 5 to 8, 11, 13 and 16. Any SER pass is recorded as
   a descriptive lead outside that cell, as on FAR (START item 6). Default: the verdict notes the per-layer counts of
   any passing class.
