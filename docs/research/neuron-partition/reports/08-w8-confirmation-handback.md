# Hand-back 08: W8, the pre-registered confirmation test of the size-500 lead (R14)

Agent: implementation worker W8 (Claude, Opus). Ticket: the team lead's W8 brief of Tue 3 Nov 2026 ("Confirmation test
of the size-500 lead"), under ruling R14 of `docs/research/neuron-partition/spec.md`. Status: resolved. Every R14 bar is
met on the fresh sample, and an independent recomputation matches the verdict exactly.

## What changed

Committed by the orchestrator from the worktree:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/scripts/neuron_partition_data.py`.
  The `sample` subcommand gains three options.
  - **`--exclude-ids JSON`.** It is repeatable. It reads a per-condition `ids` dict, a flat `ids` list or a flat list.
    The union of the file's ids is removed from every pool before the balanced draw. The file's path, sha256, id
    count and per-condition counts go into the sample's `excluded.exclude_ids_<k>` block.
  - **`--count-only`.** It prints the eligible ids, the strata and the largest n for each pool. It draws and writes
    nothing.
  - **`--no-rank-ids`.** It writes only the test sample.
  - **File names.** The sample is now written to `far_test_sample_seed{seed}.json`. A seed other than 2 writes its
    rank ids to `far_rank_ids_seed{seed}.json`, so `far_rank_ids.json` cannot be overwritten. Seed 2 writes the same
    files as before.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/tests/test_neuron_partition_data.py`
  adds three tests, for 23 in total.
  - The first covers the exclusion file loader on all three file shapes and refuses a malformed one.
  - The second runs `sample` end to end on synthetic pools with the file readers stubbed. It draws seed 2, then
    seed 3 with the seed-2 file excluded, and checks four things. No excluded id appears in any condition. The
    sha256 is recorded. The eight strata stay within one of each other. Each pool shrinks by exactly the prior
    sample's ids that it held.
  - The third covers `--count-only`.
- This file.

The run manifest names commit `d3d842b886971e196d0f7df139e2d32a1dc22a97` with `git_dirty` false, so the two code files
above were already in that commit when the job ran. Their current sha256 values start `83a45e7e` for the script and
`631dd1c0` for the tests, so you can check that d3d842b holds exactly these versions. If it does not, the files to
commit are the two above and this hand-back.

These outputs are git-ignored and stay under
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/outputs/_analyses/neuron-partition/`:

| file | sha256 |
| --- | --- |
| `data/far_test_sample_seed3.json` | `bdd94ce25aa7d029d20f6a17909c8c8b583beef52426d641aa7e04e0ed4f87d6` |
| `ablation/confirm_k500-d3d842b/summary.json` | `eb7c1bc2dd0d0832690907c86e310a9c2adc1890e63ca66226e347d4b0944d4a` |
| `ablation/confirm_k500-d3d842b/rows.jsonl` | `6b134e7211860cc2bda04b5f5b47e4998bb32e532ed4eb407040fe3fd6e7315f` |
| `ablation/confirm_k500-d3d842b/run_manifest.json` | `c67edb0e85829f190eb14c744d504874058a17d454503b80e83941ffbeeb1b8f` |
| `verdict/confirm_k500-d3d842b/verdict.json` | `87d32cdf0299fb075f005a5fd62d3a747c32721ad051c2f4798e45d5c3a5f8f7` |
| `verdict/confirm_k500-d3d842b/verdict.md` | `66371cb464117862520f58cc9ad2bed17638cee6b45e3b57d2be363cf648548e` |
| `ablation/confirm_h_only_k2000_sets.json`, prepared for the optional cell and not run | `0f00cfd9d6837727b04f2549f05c0414ff3c09ce385f89c00e7f31b004c26f2f` |

The scratch scripts are in `w8_tmp/`: the IOI overlap check, the seed-3 checks, the adapted recompute copies and the
half check. Nothing is staged for the apply tool.

## How verified

### Tests

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_neuron_partition_data.py -p no:cacheprovider -q -rf --basetemp=/projects/beto/swong2/.w8-5201d56c-tmp/bt1
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_neuron_partition_data.py -p no:cacheprovider -q -rf --basetemp=/projects/beto/swong2/.w8-5201d56c-tmp/bt2
```

Observed: "23 passed" on mgnp and "23 passed, 1 warning" on base, against a baseline of 20 on each.

- **Temp directory.** A run with `--basetemp` under `outputs/_analyses/` fails
  `test_b2_fetch_brings_back_neuron_partition`. That test looks for exactly one fetch line containing
  "outputs/_analyses/", and a temp path there matches every line. The failure comes from where the temp directory is,
  not from the code.

### Count, before any draw

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_data.py sample --count-only --exclude-ids <WT>/outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json
```

Observed, with the 356 ids also excluded and every seed-2 id removed from every pool:

| pool | eligible | largest n of the balanced draw | largest n with an equal share per stratum |
| --- | --- | --- | --- |
| D | 208 | 208 | 128 |
| I | 166 | 166 | 72 |

Excluding seed-2 ids only within their own condition would have left 344 D and 266 I. R14 chose the union, so every
instance is new.

### The seed-3 draw

The draw ran at 8:47 pm EST, after R14 was in `spec.md` stamped 8:30 pm EST. It used the brief's 20-minute fallback,
because no "committed at" reply had arrived.

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_data.py sample --n 208 --seed 3 --no-rank-ids --exclude-ids <WT>/outputs/_analyses/neuron-partition/data/far_test_sample_seed2.json
```

Observed: "warning: I drew 166 of 208". The per-condition counts are below.

| condition | rows | ids shared with the seed-2 file, any condition |
| --- | --- | --- |
| D | 208 | 0 |
| H | 208 | 0 |
| F | 208 | 0 |
| I | 166 | 0 |
| N | 166 | 0 |

- **Twins.** H and F carry D's ids, and N carries I's.
- **Overlap.** All 166 I ids are also D ids.
- **Exclusions.** `exclude_ids_0` records the seed-2 file (sha256 `cdbfca85…`, 436 distinct ids). None of the six
  excluded lists touches the sample.
- **Strata.** D's strata hold 31, 30, 32, 35, 22, 16, 20 and 22 rows. I's hold 25, 30, 32, 34, 11, 10, 9 and 15. The
  draw takes every eligible id.

### IOI overlap

```
PYTHONHASHSEED=0 HF_HOME=/work/nvme/beto/swong2 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python outputs/_analyses/neuron-partition/w8_tmp/ioi_overlap.py
```

The script calls the ablation CLI's own `ioi_rows`. Observed:

- **Seed 1.** It gives 1,000 rows with sha256 `fec3aa49…`, which matches W7's cell.
- **Seed 2.** At the default pool of 1,000, it gives 1,000 rows with sha256 `906a93ed…`.
- **Overlap.** 0 sentences are shared, so nothing was dropped and no exclusion flag was needed.

The job's summary records the same seed-2 sha256.

### Verdict

```
/u/swong2/.conda/envs/mgnp/bin/python scripts/neuron_partition_verdict.py --cell outputs/_analyses/neuron-partition/ablation/confirm_k500-d3d842b --sample outputs/_analyses/neuron-partition/data/far_test_sample_seed3.json --output-dir outputs/_analyses/neuron-partition/verdict/confirm_k500-d3d842b
```

Observed: "N1 pass at any k: True".

- **Schema.** The script accepts the seed-3 file as it stands.
- **Halves.** They come from the rule, not the fallback: `split_halves` stratified by pressure_id with seed 2, over
  the union of the D and I ids. D, H and F split 104 and 104; I and N split 78 and 88. IOI enters both halves.
- **Bootstrap.** It uses 1,000 resamples with seed 2.

Removed fractions are on the margin effect (R2). The rate columns are at margin 0.7 (R8). Collateral is in points
under the mean reference (R7).

| reference | subset | D removed, margin | D removed, rate | I removed, margin | I removed, rate | H shift | F shift | IOI shift | null p95 of D removed | all bars |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| twin | whole | 0.822 [0.81, 0.83] | 1.000 | 0.141 [0.14, 0.15] | 0.175 | 0.0 | 0.0 | -2.7 | 0.013 | pass |
| twin | half 1 | 0.824 | 1.000 | 0.145 | 0.167 | 0.0 | 0.0 | -2.7 | 0.015 | pass |
| twin | half 2 | 0.820 | 1.000 | 0.137 | 0.182 | 0.0 | 0.0 | -2.7 | 0.012 | pass |
| mean | whole | 0.748 [0.73, 0.77] | 1.000 | 0.154 [0.15, 0.16] | 0.127 | 0.0 | 0.0 | -2.7 | 0.021 | pass |
| mean | half 1 | 0.751 | 1.000 | 0.160 | 0.109 | 0.0 | 0.0 | -2.7 | 0.023 | pass |
| mean | half 2 | 0.744 | 1.000 | 0.148 | 0.142 | 0.0 | 0.0 | -2.7 | 0.020 | pass |

- **Intact effects.** The deception margin effect is 9.30 and the inversion margin effect is 14.13. The intact D rate
  effect is 0.986, and it falls to 0.0 under both references.
- **Nulls.** The largest null D removed is 0.019 under twin and 0.023 under mean. The nulls' p95 of I removed is 0.012
  and 0.015. Under mean, the nulls moved IOI from -1.3 to +2.2 points, with a p95 of |shift| of 1.8. Their H and F
  shifts were all 0.0.

Each R14 bar, on the point estimate, is met under twin and mean on the whole sample and both halves:

| bar | needed | worst value over the six cells | met |
| --- | --- | --- | --- |
| size | at most 2,000 | 338 | yes |
| D removed, margin | at least 0.50 | 0.744 (mean, half 2) | yes |
| I removed, margin | under 0.25 | 0.160 (mean, half 1) | yes |
| H shift | under 5 points | 0.0 | yes |
| F shift | under 5 points | 0.0 | yes |
| IOI shift, 1,000 fresh rows | under 5 points | -2.7 | yes |
| D removed above the null p95 | more than the null p95 | 0.744 against 0.020 | yes |

**The IOI drop is real but under the bar.** Paired over the 1,000 rows under mean, 38 rows went from correct to wrong
and 11 from wrong to correct.

| measure | value |
| --- | --- |
| exact McNemar p | 0.00014 |
| bootstrap 95% interval of the shift | -4.1 to -1.4 points |
| null range of the IOI shift | -1.3 to +2.2 points |

So the class costs a small amount of IOI accuracy, outside the null range, and the whole interval lies under the
5-point bar.

### Independence check

The review-03 scripts were copied to `w8_tmp/` and changed only as follows:

- the cell and verdict paths come from the command line;
- the zero reference is dropped, because it was not run;
- only k 500 is read;
- the cross-cell intact-equality block is removed, because there is one cell.

The originals in `review3_tmp/` are untouched.

```
cd <WT>/outputs/_analyses/neuron-partition/w8_tmp
/u/swong2/.conda/envs/mgnp/bin/python recompute_confirm.py recompute_confirm.json <WT>/outputs/_analyses/neuron-partition/ablation/confirm_k500-d3d842b
/u/swong2/.conda/envs/mgnp/bin/python compare_confirm.py recompute_confirm.json <WT>/outputs/_analyses/neuron-partition/verdict/confirm_k500-d3d842b/verdict.json
HF_DATASETS_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python halves_check.py
```

Observed:

- **Whole sample.** All 40 compared quantities are "ok", and the worst difference is 0.0 for fractions and 0.0 for
  points.
- **Halves.** The review-03 scripts are whole-sample only, so I added a half check. It rebuilds the halves from
  `split_halves` and the test-split pressure ids without the verdict script, then recomputes D removed, I removed and
  the null p95 per half. The worst difference from the verdict is 0.0.
- **Sanity fields.**
  - Intact margins agree across all sets and references, with a maximum difference of 0.0.
  - The twin pairing matches on 31,416 pairs, with a maximum difference of 0.0.
  - No D and H opposite-token pair mismatches.
  - There are 20 nulls and no duplicate rows.

No discrepancy exceeds 0.005 or 0.5 points.

## Execution evidence

- **Job and cluster.** Delta job 23494260, account beto-delta-gpu, on A40 node gpub075 in `gpuA40x4-interactive`.
  - **Partition.** The `--test-only` call on `gpuH200x8-interactive` alone failed with "Requested node configuration
    is not available": all eight H200 nodes, gpue01 to gpue08, were draining. The brief's fallback list
    `gpuH200x8-interactive,gpuA40x4-interactive` projected a start within two minutes.
  - **Time.** The job started at 8:48:45 pm EST and ended at 9:27:21 pm EST.
  - **Records.** It is ledger r-012, reconciled at 2,316 s, with job status COMPLETED.
- **Slurm state.** COMPLETED, ElapsedRaw 2316. The log `logs/np_ablate_23494260.out` ends with "wrote …summary.json,
  rows.jsonl, run_manifest.json in 2295 s".
- **Row counts.** `rows.jsonl` has 56,784 lines, against 56,784 expected. That is 21 sets × (twin over D, H, I and N
  at 748 ids, plus mean over D, H, F, I and N at 956 ids, plus 1,000 IOI rows). `unpaired` is empty.
- **Baseline reproduces.**
  - Intact IOI argmax accuracy on the 1,000 fresh rows is 0.513, against the ladder's 0.51.
  - The self-replay error is 0.0 for D and I.
  - The twin cross-check maximum difference is 0.0 on 416 D rows and 332 I rows.
- **Provenance.** `outputs/_analyses/neuron-partition/ablation/confirm_k500-d3d842b/run_manifest.json`, commit
  `d3d842b886971e196d0f7df139e2d32a1dc22a97`, `git_dirty` false.

Under R14, every bar is met. The size-500 lead is confirmed on fresh data. N1 passes for the all-position D-only class
at size 500 on the confirmation sample. The review-03 recompute scripts and my half check both match the verdict to
0.0. I ran both myself, so whether this meets R14's independent-recomputation clause is the team lead's call.

## What is NOT done

- **The optional H_only cell.** The N2 cell at size 2,000 was not run. R14 runs it only if the first job is on an
  H200, and the first job ran on an A40 because every H200 node was draining. Its sets file is built:
  `ablation/confirm_h_only_k2000_sets.json`, with 21 sets of 1,623 neurons, extracted unchanged from
  `far_all_sets_k2000_with_nulls.json`.
- **The zero reference.** It was not run, as R14 specifies.
- **Bridges-2.** Nothing was synced, because the job ran on Delta.
- **Commit message.** No "R14 committed at" message reached me. I took the sha from the worktree's branch ref,
  d3d842b, and the run manifest confirms it.

## Open questions

1. **The IOI cost.** Should the finding report it? The class lowers IOI accuracy by 2.7 points, outside the nulls'
   range, though under the bar. Default: report it beside the pass as a measured, small, non-zero collateral cost.
2. **The H_only cell.** Should it run later, once the H200 nodes return? It would need 1 to 2 GPU-hours on an A40.
   Default: no, unless you rule that it should. R14 tied it to the first job running on an H200.
3. **Sample size.** The I sample has 166 rows, under item 10's floor of 300 rows. R14 accepts this because it takes
   every eligible id. Default: the finding states the sample sizes beside the result.
