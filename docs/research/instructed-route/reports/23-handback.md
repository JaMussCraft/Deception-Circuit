# Hand-back 23: B1 ticket 7, the loop-closure batch files, the fetch glob and the dry runs

Agent: ticket implementer (Claude Opus 5.5), session claude-230e4716. Ticket: `docs/research/instructed-route/plans/B1-plan.md` section 5, ticket 7 (with sections 0, 3 and 4). Status: resolved. Nothing was submitted for real.

## What changed

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/jobs/B1-smoke.batch`, new. It has two lines, far then ser, each with `--route-max-batches 1`, and output dirs `outputs/_analyses/instructed-route-b1/smoke/far` and `.../smoke/ser`.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/jobs/B1-far.batch`, new. It has one line, all 100 held-out ids, and output dir `outputs/_analyses/instructed-route-b1/far`.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/jobs/B1-ser.batch`, new. It is the same for ser, with output dir `outputs/_analyses/instructed-route-b1/ser`.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/scripts/remote/b2.sh`. `FETCH_ANALYSIS_GLOBS` now holds `"mechanism-analysis-*" "instructed-route-b1*"`, plus one comment line.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/tests/test_instructed_route_b1_jobs.py`, new, with 24 tests.
- Committed by the orchestrator from the worktree: this file.

How each line is built:

- **Composition.** Every argument up to and including `--task-from VALUE` is copied verbatim from the first line of `docs/research/mechanism-analysis/jobs/05-p3-<task>.batch`. That covers the seven `--circuit` bindings, `--expr Ct=...`, `--compose-granularity leaf`, the seven `--reference` flags and `--task-from`. A test asserts the copy is exact.
- **Sample.** Each line adds `--include-ids docs/research/mechanism-analysis/phase1/groups/<task>_heldout_D_sample.json --n-causal 100`.
- **Analysis.** Each line adds `--analyses route_closure --route-tests both --route-direction both --route-sweep both`.
- **Grid and deciding set.** Each line adds `--route-ct docs/research/mechanism-analysis/phase3/ct.json` and `--route-deciding-set docs/research/mechanism-analysis/phase1/groups/<task>_heldout_D.json:greedy_k20`. The name `greedy_k20` exists in both files and holds 20 Components each.
- **Defaults kept.** Path patching stays on and the seed stays at 0, as in 05-p3. With all 100 ids included, the seed only orders the draw.
- **Timings.** `--timings` is a flag of the `batch` subcommand, so it appears only in each header's run command, never on a line.

The files were written by a one-off script outside the repository. No generator was added, and the headers say so.

## How verified

Dry runs. Each command was run from the worktree on the login node, with the mgnp interpreter and BLAS pinned to one thread. The full logs are `/u/swong2/.claude/jobs/230e4716/tmp/dry_{smoke,far,ser}.log`, which are deleted with the job, so the key lines are quoted here.

```
python analyze_components.py batch docs/research/instructed-route/jobs/B1-smoke.batch --dry-run
python analyze_components.py batch docs/research/instructed-route/jobs/B1-far.batch --dry-run
python analyze_components.py batch docs/research/instructed-route/jobs/B1-ser.batch --dry-run
```

Observed: all three exited 0. The batch summaries were "2 of 2 invocation(s) ok", "1 of 1" and "1 of 1". Key lines per cell:

- **far cell.** `Ct__leaf x far_v2`: "62 head(s) and 10 MLP block(s) over 14 layer(s)", which is 72 Components.
- **ser cell.** `Ct__leaf x ser_v2`: "68 head(s) and 10 MLP block(s) over 16 layer(s)", which is 78 Components.
- **Sample.** "sample: 100 of 100 requested, seed 0" and "id inclusion: 100 id(s) from .../<task>_heldout_D_sample.json; 100 in the split, 0 not".
- **Segments.** The segmentation has 19 Segments. They include `pressure_clause`, `readout`, `item_1_intro`, `item_2_intro`, `designation_site` and all four option Segments.
- **Causal loader.** "100 instance(s) of 100 requested, 13 batch(es) of 8" and "neutral-clause twin on 100 of 100, from .../data/datasets/<task>_v2_honest; 0 without".
- **route_closure.** "quartet layer 17 heads [24, 25, 26, 27]; 35 arm(s)" and "grid docs/research/mechanism-analysis/phase3/ct.json (72 Component(s))", or 78 for ser.

Forward counts and estimates from the route_closure line. The minutes are the module's A40-rate price.

| line | batches | arms and captures | T1 sweep and controls (outside senders) | path patching | total forwards | estimate |
|---|---|---|---|---|---|---|
| smoke far | 1 | 37 | 1,982 (984) | 134 | 2,153 | 6.6 min |
| smoke ser | 1 | 37 | 1,970 (978) | 134 | 2,141 | 6.6 min |
| far | 13 | 481 | 25,766 (984) | 1,742 | 27,989 | 86.2 min |
| ser | 13 | 481 | 25,610 (978) | 1,742 | 27,833 | 85.7 min |

My own extrapolation, not a measurement, uses the plan's H100 rate of 0.047 s per forward at batch 8. On it the far job is about 22 minutes of forwards plus a 10 to 13 minute model load, inside the 1:15 reservation. The smoke is about 16 minutes inside 0:30. The module notes that capture-all forwards are heavier, so the smoke's timings decide.

```
scripts/remote/b2.sh sync-code --dry --branch instructed-route
```

Observed: exit 0. It printed one `ssh -o BatchMode=yes bridges2 '...'` command that fetches `+instructed-route:refs/remotes/origin/instructed-route` into `/ocean/projects/cis260361p/swong2/Deception-Circuit`, checks it out or tracks it, and fast-forwards. Nothing ran.

```
DC_B2_BRANCH=instructed-route scripts/remote/b2.sh submit --dry --test-only --time 00:30:00 --script scripts/analyze_components.sbatch -- batch docs/research/instructed-route/jobs/B1-smoke.batch --timings outputs/_analyses/instructed-route-b1/timings/smoke.json
```

Observed: exit 0. It printed `cd /ocean/projects/cis260361p/swong2/Deception-Circuit && mkdir -p logs && sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=cis260361p -A cis260361p -p GPU-shared --gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G -t 00:30:00 --test-only scripts/analyze_components.sbatch batch docs/research/instructed-route/jobs/B1-smoke.batch --timings outputs/_analyses/instructed-route-b1/timings/smoke.json`. The far and ser variants with `--time 01:15:00` printed the same command with `-t 01:15:00` and their own file names, and both exited 0. `--dry` runs nothing, so these are prints, not scheduler answers.

The SSH master to `bridges2` was open, so I also ran the same three commands without `--dry`. That ran `sbatch --test-only` on Bridges-2, which submits nothing.

```
DC_B2_BRANCH=instructed-route scripts/remote/b2.sh submit --test-only --time 00:30:00 --script scripts/analyze_components.sbatch -- batch docs/research/instructed-route/jobs/B1-smoke.batch --timings outputs/_analyses/instructed-route-b1/timings/smoke.json
```

Observed: "sbatch: Job 50105493 to start at 2026-11-01T17:47:58 using 12 processors on nodes w001 in partition GPU-shared", exit 0. For far, with `--time 01:15:00`, it answered "Job 50105503 to start at 2026-11-01T17:47:58 ... w001 in partition GPU-shared", exit 0. For ser it answered "Job 50105505", the same start time, exit 0. Delta's clock read 15:17 CST when these ran. Afterwards `squeue -u $USER` on Bridges-2 listed no jobs.

The test-only did not need the branch on Bridges-2, because sbatch checks only the script, which the clone already has. The clone is on branch `mechanism-analysis`, though. It has no `docs/research/instructed-route/jobs/`, and it does not have the `route_closure` module. A real submit therefore needs the branch pushed and `sync-code --branch instructed-route` first.

Every input the lines read exists on Bridges-2 under the repo root. I checked with `ssh -o BatchMode=yes bridges2 '... [ -e $p ] ...'`. The list covered the six v2 run dirs, `allmlp_nomb_v2`, `skct_far`, `skct_ser`, `data/datasets/{far,ser}_v2{,_honest}`, `ct.json` and the held-out group files.

Delta fallback, as the brief gave it:

```
sbatch --test-only --time=00:30:00 --partition=gpuH200x8-interactive --account=bimc-delta-gpu scripts/analyze_components.sbatch batch docs/research/instructed-route/jobs/B1-smoke.batch --timings outputs/_analyses/instructed-route-b1/timings/smoke.json
```

Observed: refused, exit 1, with this error:

```
sbatch: error: QOSMaxSubmitJobPerUserLimit
allocation failure: Job violates accounting/QOS policy (job submit limit, user's size and/or time limits)
```

The cause is that `squeue` shows job 23412454 (`b2-p1-capture`, bimc-delta-gpu) already pending on `gpuH200x8-interactive`. The interactive partitions allow one job per user. I then asked the regular H200 partition, which plan section 4 names as the Delta fallback:

```
sbatch --test-only --time=00:30:00 --partition=gpuH200x8 --account=bimc-delta-gpu scripts/analyze_components.sbatch batch docs/research/instructed-route/jobs/B1-smoke.batch --timings outputs/_analyses/instructed-route-b1/timings/smoke.json
```

Observed: "Job 23412892 to start at 2026-11-20T21:46:16 ... gpue04 in partition gpuH200x8". The far file with `--time=01:15:00` got "Job 23412893", with the same start time. The smoke under `--account=bgrb-delta-gpu` got "Job 23412895 to start at 2026-11-03T11:12:16".

Fetch glob:

```
DC_DELTA_REPO_ROOT=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route scripts/remote/b2.sh fetch --dry
```

Observed: the `outputs/_analyses` rsync line carries `--include=/mechanism-analysis-*/*** --include=/instructed-route-b1*/*** --exclude=*` and targets `.../worktrees/instructed-route/outputs/_analyses/`. Without the override, the target is `.../worktrees/mechanism-analysis/outputs/_analyses/`, a worktree that no longer exists. See Open questions.

Tests:

```
/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q -p no:cacheprovider tests/test_instructed_route_b1_jobs.py
```

Observed: 24 passed in 18.60s.

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -q -p no:cacheprovider tests/test_instructed_route_b1_jobs.py
```

Observed: 24 passed, 3 warnings in 19.35s. There were no skips: the run dirs are present, so the C_t test ran on base too.

The tests assert the following:

- each file parses with the CLI parser, as route_closure with both tests, both directions, both estimators and path patching on, with no `--timings` on a line;
- each header names its own timings file;
- each line's composition equals the 05-p3 line's verbatim;
- each cell's Component set equals `ct.json`'s C_t, with far at 72 and ser at 78. This uses `intake.resolve_intake` and `head_table_for` with `num_kv_heads=8`, the resolver `--dry-run` uses, with no model;
- every line has `--route-ct ct.json`, the task's held-out id file with 100 unique ids, `--n-causal 100`, and the task's `greedy_k20` deciding set of 20;
- the four output dirs are distinct, under `outputs/_analyses/instructed-route-b1/`, and none is nested in another;
- smoke lines carry `--route-max-batches 1` and task lines do not, and the two otherwise match;
- `FETCH_ANALYSIS_GLOBS` holds both globs, and a `fetch --dry` against a temporary repo root prints the new include and creates nothing.

Because I edited `b2.sh`, I also ran its existing tests. These were `tests/test_cluster_profiles.py`, `tests/test_mechanism_v2_evals.py`, `tests/test_mechanism_analysis_launcher.py` and `tests/test_mechanism_analysis_infra.py`. Observed: 108 passed on mgnp in 110.97s, and 108 passed with 3 warnings on base 3.9 in 159.67s.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- **No real submission.** That was by instruction. The branch is not pushed and `sync-code` has not run, so the Bridges-2 clone cannot run these files yet.
- **Smoke gates G1 to G5 are not measured.** They need the smoke job.
- **The full test suite was not run.** Only the new file and the four `b2.sh` test files ran. The orchestrator compares the full suite by name.
- **The dry runs wrote files into Delta's git-ignored outputs.** Each of the four cells under `outputs/_analyses/instructed-route-b1/{smoke/far,smoke/ser,far,ser}/Ct__leaf/<task>_v2/` got a head table, `segmentation.json` and `sample.json`. Nothing else was written outside the files listed above.

## Open questions

1. **The Delta repo root for `fetch`.** `scripts/cluster/delta.env` defaults `DC_REPO_ROOT` to the removed `mechanism-analysis` worktree. A plain `b2.sh fetch` would recreate that path and land the results there. Default: run the fetch with `DC_DELTA_REPO_ROOT=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route`. I did not edit `delta.env`, which other directions share.
2. **The Delta fallback partition.** `gpuH200x8-interactive` is blocked while job 23412454 is queued there. The regular `gpuH200x8` under bimc forecasts 2026-11-20, and under bgrb it forecasts 2026-11-03 11:12. Default: use Bridges-2, which forecasts a start today. If it is lost, use `gpuH200x8` under `bgrb-delta-gpu`, or the interactive partition once the capture job has left it.
3. **The dry-run cells on Delta.** The fetch runs with `--update --checksum --backup`, so a differing dry-run file is replaced and left beside the new one as `<name>.pre-b2fetch`. Default: delete `outputs/_analyses/instructed-route-b1/` on Delta just before the first fetch.
4. **Smoke output dirs.** I gave each smoke line its own dir, `smoke/far` and `smoke/ser`, so every line in the three files has a distinct `--output-dir`. One `smoke` root would also work, since cells separate by task. Default: keep them separate.
5. **Reservations.** I kept 0:30 for the smoke and 1:15 per task, as in plan section 4. My extrapolation fits inside both, but the capture-all forwards are not timed. Default: reset the task reservations from the smoke's `--timings` at observed plus about 50%, as the plan says.
