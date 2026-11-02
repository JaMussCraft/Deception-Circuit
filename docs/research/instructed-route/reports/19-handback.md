# Hand-back 19: B2 ticket T8, the P2 and P3 job files, the P1 capture wrapper and the login checks

Agent: Opus implementer (claude-opus-5-5), team member of the instructed-route session. Ticket:
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B2-plan.md`,
section 6, T8. Status: resolved. No job was submitted.

## What changed

All files are new and are committed by the orchestrator from the worktree. Nothing is staged for the apply tool.

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/jobs/B2-p2.batch`
  holds the six P2 lines, for two conditions and three position sets.
  - Every line carries the U binding of the mechanism-analysis 1C-b file, byte for byte: seven `--circuit`, the
    expression `U=(Df|Hf|Ds|Hs|De|He)-m`, leaf granularity and six `--reference`.
  - Every line uses `--seed 0`, the 618-id file with `--n-causal 1000`, knockout only and `--knockout-singles off`.
    It also sets scheme `interchange`, counterfactual `neutral_twin` and the groups file `p2_groups.json`.
  - The `wish_*` lines run the reported-wish stand-in. The `sdrd_*` lines run SDR D, the coarse sdr_v2 D run, on the
    same ids.
  - Position sets are `all`, `readout` and `after=pressure_clause,exclude=readout`, each written explicitly.
  - Each of the six (condition, positions) pairs has its own root under `outputs/_analyses/instructed-route-b2/p2/`,
    named `wish_all`, `wish_readout`, `wish_after`, `sdrd_all`, `sdrd_readout` and `sdrd_after`. Both conditions
    write the cell `U__leaf/sdr_v2`, which is why the roots must differ.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/jobs/B2-p3.batch`
  holds 21 P3 lines.
  - Seed 0 runs on SER only, as the reproduction. Seeds 1 and 2 each run on far, sdr and ser, and every task gets
    D, H and F.
  - Each line passes `--seed N` and `--include-ids` of `groups/<task>_seed<N>_ids.txt` with `--n-causal 1000`.
    It uses the groups file `p3_groups.json` and singles off.
  - Each line is an item-swap interchange at all positions, with both flags written explicitly.
  - D uses the coarse D run, H the `nls0.3_honest_` run and F the `<task>_v2_nopressure` stand-in, as in the
    mechanism-analysis held-out file.
  - The roots are `outputs/_analyses/instructed-route-b2/p3/seed<N>_<d|h|f>`. D, H and F share the cell name
    `U__leaf/<task>_v2`, so each (seed, role) pair has its own root.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/jobs/B2-p3-layout.json`
  is the layout for `scripts/instructed_route_b2_read.py p3`. It sets `baseline_run` to `seed0` and
  `replication_runs` to `["seed1", "seed2"]`. Each cell is `<root>/U__leaf/<task>_v2` and is relative to the
  repository root, so the reader must run from there. Two extra keys, `groups` and `ids`, name the input files. The
  reader ignores them and the test checks them.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/jobs/run_b2_capture.sbatch`
  wraps the P1 capture.
  - The header has no `--time`, so the walltime goes on the command line. It defaults to `bimc-delta-gpu`, to
    `gpuA100x4` and to one GPU, all of which the command line can override.
  - The script runs under `set -euo pipefail` and changes to `SLURM_SUBMIT_DIR`. Its cwd guard needs both
    `scripts/falsity_probe_capture.py` and a `pwd -P` equal to the literal worktree path.
  - It sources the cluster profile, activates mgnp, forces the Hugging Face offline variables and pins BLAS threads
    to 1.
  - With no arguments it runs the real plan into `outputs/_analyses/instructed-route-b2/p1`. With arguments it
    passes them through, so the smoke job can name its own plan and directory.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_instructed_route_b2_jobs.py`
  holds 28 tests.
  - They parse every line with the real CLI parser and check that every `--include-ids` line sets `--n-causal 1000`.
    They also check one shared U binding, that the referenced runs, groups and id files exist, and distinct output
    roots.
  - For P2 they check the two-by-three design, that the wish and D reference roots are disjoint and not nested, and
    the neutral-twin flags.
  - For P3 they check seeds {0, 1, 2} with seed 0 on SER only, and that D, H and F share one id file and use three
    roots. They also check that the seed id files hold 100 ids each with no overlap between seeds.
  - For the layout they check that its cells equal the batch output cells, that run directories are distinct and
    that the named group and id files exist. They also check that the real reader reads it as "not yet verified"
    when no cell exists.
  - For the wrapper they check `bash -n`, the header without `--time`, the guard, offline mode and threads, and that
    it refuses another cwd.
- The `logs/` directory was created in the worktree for the `#SBATCH --output` path. It is not a tracked file.

A throwaway generator wrote both batch files and the layout. It is at `/u/swong2/.claude/jobs/230e4716/tmp/gen_b2_jobs.py`,
is not part of the commit, and the batch file headers say how each line is built.

## How verified

Red first. Before any job file existed, the new tests failed.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_instructed_route_b2_jobs.py
```

Observed before the files: `12 failed, 4 passed, 12 errors`. Observed after: `28 passed`.

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_instructed_route_b2_jobs.py tests/test_instructed_route_b2_read.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_instructed_route_b2_jobs.py tests/test_instructed_route_b2_read.py
```

Observed: `58 passed` on mgnp, and `58 passed, 3 warnings` on base 3.9. The warnings are library deprecation notices.

P2 dry run, from the worktree, took 58 s:

```
/u/swong2/.conda/envs/mgnp/bin/python analyze_components.py batch docs/research/instructed-route/jobs/B2-p2.batch --dry-run
```

Observed on each of the six lines:

```
    sample: 618 of 1000 requested, seed 0
      id inclusion: 618 id(s) from docs/research/instructed-route/groups/sdr_wish_ids.txt; 618 in the split, 0 not
    causal loader: 618 instance(s) of 618 requested, 78 batch(es) of 8
    causal loader: neutral-clause twin on 618 of 618, from .../data/datasets/sdr_v2_honest; 0 without
    knockout: per-Component pass off (--knockout-singles off); plus 29 named group(s) from docs/research/instructed-route/groups/p2_groups.json (sizes 1-4) = 2418 more forward pass(es)
```

The plans were `{'scheme': 'interchange', 'counterfactual': 'neutral_twin', 'positions': P}`, with P equal to `all`,
`readout` and `after=pressure_clause,exclude=readout` for each condition in turn. The U binding resolved to 123
heads and 0 MLP blocks over 17 layers. The run ended with `batch: 6 of 6 invocation(s) ok`. Wish lines segment the
618-row stand-in. The SDR D lines segment 1,000 rows and sample the same 618.

P3 dry run, from the worktree, took 121 s:

```
/u/swong2/.conda/envs/mgnp/bin/python analyze_components.py batch docs/research/instructed-route/jobs/B2-p3.batch --dry-run
```

Observed on each of the 21 lines: `sample: 100 of 1000 requested, seed N` and `id inclusion: 100 id(s) from
<task>_seed<N>_ids.txt; 100 in the split, 0 not`. Each line then showed 13 batches of 8 and `6 named group(s) from
p3_groups.json (sizes 1-1) = 104 more forward pass(es)`, with the item-swap plan. The run ended with
`batch: 21 of 21 invocation(s) ok`.

The dry runs wrote `sample.json` into every cell. A CPU script then compared them:

```
/u/swong2/.conda/envs/mgnp/bin/python /u/swong2/.claude/jobs/230e4716/tmp/cmp_samples.py
```

Observed:

```
seed0 ser {'D': 100, 'H': 100, 'F': 100} D=H=F set: True same order: True == id file set: True
seed1 far / sdr / ser, seed2 far / sdr / ser: the same line, all True
seed0 ser D vs S1 sample.json: same list True
P2 cells: {'sdrd_after': 618, 'sdrd_all': 618, 'sdrd_readout': 618, 'wish_after': 618, 'wish_all': 618, 'wish_readout': 618} all equal the 618-id set: True
```

The seed-0 SER sample is identical, ids and order, to the mechanism-analysis S1 sample behind `rcls.csv`. Samples are
kept in dataset order whether drawn or included. These dry-run cells existed only in the dry runs, so the whole new
`outputs/_analyses/instructed-route-b2` tree was removed afterwards. It held 27 cells of `head_table`, `sample.json`
and `segmentation.json` files. The real runs start clean.

```
bash -n scripts/jobs/run_b2_capture.sbatch && echo "capture bash -n ok"
bash -n scripts/analyze_components.sbatch && echo "analyze_components bash -n ok"
```

Observed: both lines printed. A test also ran the capture wrapper from a temporary directory. It exited non-zero with
the worktree message before activating anything.

For P1, the per-cell counts come from T6's dry run of the same plan in `reports/15-handback.md`. It had 18 cells with
9,972 rows in total, and the encoding check passed on every row. I did not repeat it here. See "What is NOT done".

Fair-share at submit time:

```
sshare -u swong2 -A beto-delta-gpu,bimc-delta-gpu,bgrb-delta-gpu,bjhz-delta-gpu -o Account,User,FairShare
```

Observed: bgrb 0.2527, beto 0.2503, bjhz 0.2249, bimc 0.2151.

Test-only submissions from the worktree after `mkdir -p logs`. Each named `--account=bimc-delta-gpu` and
`--time=00:45:00`. The sbatch time on the login node was 14:26 CST on 2026-11-01. The seven commands were:

```
sbatch --test-only --time=00:45:00 --partition=gpuH200x8 --account=bimc-delta-gpu scripts/analyze_components.sbatch batch docs/research/instructed-route/jobs/B2-p2.batch --timings outputs/_analyses/instructed-route-b2/timings/p2.json
sbatch --test-only --time=00:45:00 --partition=gpuH200x8 --account=bimc-delta-gpu scripts/analyze_components.sbatch batch docs/research/instructed-route/jobs/B2-p3.batch --timings outputs/_analyses/instructed-route-b2/timings/p3.json
sbatch --test-only --time=00:45:00 --partition=gpuA100x4 --account=bimc-delta-gpu scripts/analyze_components.sbatch batch docs/research/instructed-route/jobs/B2-p2.batch --timings outputs/_analyses/instructed-route-b2/timings/p2.json
sbatch --test-only --time=00:45:00 --partition=gpuA100x4 --account=bimc-delta-gpu scripts/analyze_components.sbatch batch docs/research/instructed-route/jobs/B2-p3.batch --timings outputs/_analyses/instructed-route-b2/timings/p3.json
sbatch --test-only --time=00:45:00 --partition=gpuH200x8-interactive --account=bimc-delta-gpu scripts/analyze_components.sbatch batch docs/research/instructed-route/jobs/B2-p2.batch --timings outputs/_analyses/instructed-route-b2/timings/p2.json
sbatch --test-only --time=00:45:00 --partition=gpuA100x4-interactive --account=bimc-delta-gpu scripts/analyze_components.sbatch batch docs/research/instructed-route/jobs/B2-p3.batch --timings outputs/_analyses/instructed-route-b2/timings/p3.json
sbatch --test-only --time=00:45:00 --partition=gpuH200x8 --account=bimc-delta-gpu scripts/jobs/run_b2_capture.sbatch
```

| submission | partition | scheduler reply |
| --- | --- | --- |
| P2 | gpuH200x8 | `to start at 2026-11-04T03:48:16 ... nodes gpue07` |
| P3 | gpuH200x8 | `to start at 2026-11-04T03:48:16 ... nodes gpue07` |
| P2 | gpuA100x4 | `to start at 2026-11-01T14:32:05 ... nodes gpua055` |
| P3 | gpuA100x4 | `to start at 2026-11-01T14:32:05 ... nodes gpua055` |
| P2 | gpuH200x8-interactive | `to start at 2026-11-01T15:06:16 ... nodes gpue07` |
| P3 | gpuA100x4-interactive | `to start at 2026-11-01T14:26:06 ... nodes gpua055` |
| P1 capture | gpuH200x8 | `to start at 2026-11-04T03:48:16 ... nodes gpue07` |

`squeue -u swong2` was empty afterwards, so no test-only call queued a job.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **No job was submitted or run.** Every P2 and P3 number in section 7 is still not yet verified. That includes the
  clean I margin of 3.15, the twin margin of -2.92, the seed-0 reproduction and the 40-hex manifests.
- **The capture wrapper was not executed on the login node.** This session's worktree-isolation hook refuses any
  `bash <script>` command, and setting `DC_RUN_MANIFEST_GIT=0` on the command line also trips it. Only `bash -n` and
  the test-driven cwd refusal ran. The P1 dry run was not repeated, and T6's dry run of the same plan stands as the
  evidence. Before the P1 smoke job, the orchestrator should run the wrapper's dry run from the worktree:
  `bash scripts/jobs/run_b2_capture.sbatch --plan docs/research/instructed-route/jobs/B2-p1-plan.json --output-dir <scratch> --dry-run`.
- **The P1 capture plan has no test-only check on gpuA100x4.** T6's hand-back notes that batch size 8 on 8B has not
  been checked for memory. The smoke job should settle the partition.
- **The 57 held-out ids are not given their own drop row in the batch.** The sensitivity row that drops them is a
  reader option (`p2 --exclude-ids`) and needs no extra GPU line.
- **The ledger was not updated.** No GPU time was reserved or spent.

## Open questions

1. **Partition.** gpuH200x8 is days away. gpuH200x8-interactive was about 40 minutes out, and gpuA100x4-interactive
   and gpuA100x4 start within minutes. P3's seed-0 line must reproduce `rcls.csv` within 0.01, and that file came
   from an H100 job. Shared memory records bf16 drift on A100 evaluations, which would add a cause of a miss that the
   plan does not name. P2 checks only dataset margins at a 0.05 tolerance, so an A100 is fine for it. Default: P3 on
   gpuH200x8-interactive and P2 on gpuA100x4-interactive, one job per interactive partition. Pick the account with
   the best fair-share at submit time, which is bgrb now, ahead of bimc.
2. **`--time` for P2.** The brief's 45 minutes leaves a thin margin on an A100 for 6 x 2,418 group forwards over
   618 rows plus the model load. The plan's 20-minute estimate is based on H100 timings. Default: request 00:55:00
   on an A100 partition, which still fits the interactive 1-hour cap.
3. **The literal worktree path in the capture wrapper's guard.** The wrapper refuses to run from the primary
   checkout after a merge. Default: keep the literal path while the direction lives in this worktree, as
   `run_sdr_cue_probe.sh` does, and change it at merge.
4. **The output root name `outputs/_analyses/instructed-route-b2`.** The plan names none. Default: keep it, since
   the P2 reader, the layout and the capture wrapper all point there.
