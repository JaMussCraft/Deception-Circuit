# v2 coarse evaluation suite (ticket 06, spec 14.G14)

This suite runs evaluations 1-4 of the six coarse heads-only v2 circuits. They are D and H for far_v2,
sdr_v2 and ser_v2, with run dirs in `mv2_cells.RUNS` and listed in `reports/05-training-summary.md`.
There is no EVAL 5, no training and no component analysis.

Every path below and in every generated command is relative to the repository root, `DC_REPO_ROOT`. So the
same suite runs on Delta and on Bridges-2.

## Files

| file | what |
| --- | --- |
| `mv2_cells.py` | the cell plan (`plan_cells`), packing into jobs (`jobs_for`), `job_args`, cost model and walltime rule |
| `suite_v2.json` | the suite definition (see below) |
| `build_operands.py` | builds `operands/allmlp_nomb_v2/`, `standins/<t>_v2_nopressure/` and `drift_control/sdr_coarse_D_260922-092742/` |
| `build_suite.py` | writes `suite_v2.json`, reading the reference knockout.json files from the main checkout (read-only) |
| `gen_cells.py` | sbatch lines from a cluster profile: `--dry` prints a bash script; `--submit` budgets, checks, reserves in the ledger, submits and records |
| `check_cells.py` | the login-node checker of every generated `evaluate_circuit.py` command: argparse, paths, mask composition, test sets |
| `drift.py` | per-metric deltas of the drift-control cells against their Delta references |
| `eval_jobs.txt` | one tab-separated row per submitted job: submitted_at, profile, stage, job, job_id, time, output_dir. `--submit` creates it |

`suite_v2.json` holds these things:

- every cell;
- the packed jobs per stage, with their output and result dirs and estimates;
- the drift-control block, with the Delta reference values.

`build_suite.py` writes it, and a test fails when it is stale. The tests are in
`tests/test_mechanism_v2_evals.py`.

## Cell design

The suite uses the coarse SDR wave's two-cell design (`llama-8b-instruct_sdr_coarse/_launch/submit_headsko.sh`,
`submit_composed.sh`) and the format-control coarse suite's (`../_launch_format_control/README_suites.md`).

- **Sufficiency** is the atomic circuit, or `(E) | m` for a composition, with evals `sanity null pressure`.
- **Knockout** is `(E) - m`, the heads-only knockout that keeps every MLP, with evals `knockout`.
- All compositions are at `--compose-granularity leaf`. Head granularity would OR every MLP unit back in,
  because these runs have no `mlp_blocks` gate. On these masks every live head has all its neurons open,
  so leaf set operations are head set operations.
- Every job also passes `--ablation interchange --n-random 20 --knockout-null-count 20`. The one exception
  is the secondary drift cell, which keeps its reference's argv.
- **Sanity is skipped** with a recorded reason (`summary.json` `skipped.sanity`) wherever there is no in-run
  number to reproduce. That covers every composed sufficiency cell `(E) | m` and every cell on another
  run's test set: cross-task D, H on D's test set, and D on nopressure. So eval 1 runs exactly on the six
  atomic circuits on their own test sets. The orchestrator's text said `null pressure` for sufficiency;
  `sanity` is the only addition and costs nothing where it is skipped.
- **Eval 4 (pressure)** is skipped the same way on a nopressure test set.

| stage | block | cells |
| --- | --- | --- |
| control | drift_control | v1 coarse SDR D heads-only KO on `sdr`, once per Delta reference, each with its argv (2) |
| 1 | pair | per circuit X of the 6: X suff + `(X) - m` KO on its own test set (`<t>_v2` for D, `<t>_v2_honest` for H) (12) |
| 1 | composition | per task, on D's test set: `(D&H) \| m` suff, `(D&H) - m`, `(D-H) - m`, `(H-D) - m` KO (12) |
| 2 | cross_task | each D on the other two D test sets, suff + KO (12) |
| 2 | core | `D_far & D_sdr & D_ser` (31 heads), suff + KO on all three D test sets (6) |
| 2 | exclusive | `D_t - D_u - D_v` = `D_t - (D_u \| D_v)` (the `--xor` family), KO on its own test set (3; 8 / 14 / 10 heads) |
| 2 | H_on_D_test_set | H on D's test set, suff + KO (6) |
| 2 | D_on_nopressure | D on `<t>_v2_nopressure`, suff + KO (6) |
| 2, conditional | conditional_D_minus_H_cross_task | `(D_t - H_t) - m` KO on the other two D test sets (6; with `--include-conditional`, only if stage 1 shows a strong home-task D-H knockout) |

Operand names are task-qualified (`D_far`, `H_sdr`, `m`), so a label means the same thing in every job.

Each cell records `expected_heads`. `mv2_cells.live_heads` computes it from the masks with plain set
operations, and the values match the recon's table A3. For example, far D&H / D-H / H-D are 32 / 26 / 28
heads, and sdr is 39 / 21 / 19.

**Packing.** A job is one `evaluate_circuit.py` process, so it loads the model once. Cells that share a
stage, test set and evals run in one job:

- stage 1: 12 jobs;
- stage 2: 12 jobs, with the conditional cells joining the D-test-set KO jobs.

`--no-pack` gives one cell per job. A job writes `outputs/_suites/mechanism-v2-coarse/<control|stage1|stage2>/<job>/`,
and each cell lands in `cells/<cell_dir>/<test task>/interchange/`. The per-cell result path is in
`suite_v2.json` (`stages.<s>.jobs_packed[].results`). `matrix.json` appears only at the end of a job,
while a cell's `summary.json` and `knockout.json` are written as it finishes.

## Operands (`build_operands.py`)

### `operands/allmlp_nomb_v2/`

This is the `m` operand, shared by all three tasks.
`../_launch_format_control/build_allmlp.py` (the `submit_headsko.sh` recipe) builds it from the **far_v2 D
run** (`built_from` in its `active_nodes.json`). It has no head, no attention block, no attention neuron,
and every MLP unit open.

- **Masks.** They are identical to `../_launch_format_control/allmlp_nomb`, which is tested. The v2 mask
  keys and shapes equal v1's.
- **The operand is task-agnostic.** One copy serves far, sdr and ser.
- **Config.** Its `config.json` is that run's config. So it names `far_v2` and deceptive, plus an inert
  `operand` key.

The evaluator never takes a test set from an operand's config. Tasks come only from `--task-from`, which
reads that run's `task`, `deception_condition` and `data_dir`. Every job passes exactly one `--task-from`,
which the checker and a test enforce. Without `--task-from`, the evaluator's default would be every bound
circuit's own task, and that is the one way m's config could matter.

A test confirms the rule on a real job: an H knockout job on `sdr_v2_honest`, with `m` bound, resolves to
exactly one test set, `sdr_v2` / honest.

### `standins/<t>_v2_nopressure/config.json`

This is a config-only task source, as format-control's `standin-dryrun --f-run` did. It holds the `<t>_v2`
D run's config with `deception_condition: nopressure`, so `--task-from` binds
`data/datasets/<t>_v2_nopressure`. There are no v2 Format Circuits. A stand-in is never bound as a circuit,
and the checker refuses that.

### `drift_control/sdr_coarse_D_260922-092742/`

This holds byte copies of `active_nodes.json` and `config.json` of the v1 coarse SDR D run. That run lives
only in the main checkout and is not on this branch. `provenance.json` records their sha256.

The run's test set `data/datasets/sdr` is byte-identical between this worktree and the main checkout, and
unchanged since 2026-08-18. Both drift cells bind `m` to the on-branch `../_launch_format_control/allmlp_nomb`.
Its masks equal the SDR wave's `llama-8b-instruct_sdr_coarse/_allmlp_nomb`.

## Drift control (2 cells; ran 2026-10-24, 0.41 H100 GPU-h actual)

Each drift cell reproduces one Delta reference with that job's own argv, apart from paths, the output dir
and the suite name. A test compares each against the reference job's recorded `suite.json` argv.

| drift job | reference | date | argv | role |
| --- | --- | --- | --- | --- |
| `drift_sdr_coarse_D_hko` | fc coarse suite `D_hko__sdr`, job 22895982 | 2026-10-15 | `D_hko=(D) - m`, `--ablation interchange --n-random 20 --knockout-null-count 20` | primary |
| `drift_sdr_coarse_D_headsko` | SDR wave `evaluations_headsko`, job 22316469 | 2026-09-22 | `headsko=c - m`, `--n-random 20` | secondary |

Both references ran on A40s.

- **Task and wikitext rows.** The two references agree exactly here. On one GPU type the cell is bit-stable.
- **Pressure-variant rows.** These differ between the references. For example, no_pressure full accuracy is
  0.169 vs 0.228, because of an evaluator change between the two dates, not the dataset. The primary is the
  yardstick for those rows.
- **Cross-GPU.** A cross-GPU run is not expected to be bit-exact.
- **Acceptance.** No threshold is pre-registered, and the orchestrator decides.

After the jobs, run:

```
python outputs/_launch_mechanism_v2/evals/drift.py      # each drift cell against its reference
```

It compares these metrics:

- the knockout and circuit-alone accuracy, logit diff, KL and exact match;
- the task-side KO null's mean, percentile and z per metric, with the 4/4 separation count
  (percentile <= 5 and z <= -2);
- flips to honest;
- wikitext KL/token and ppl ratio, and their null;
- the pressure-variant headlines.

## Generating and submitting (`gen_cells.py`)

A cluster profile is `scripts/cluster/<name>.env`, from ticket 07, or any file given with `--profile-file`.
It is sourced in a clean bash. Only `PATH` and `HOME` reach that shell, so every value, including any
cross-cluster root mapping, comes from the profile file and never from the caller's environment. A test
checks that no real-profile value, `/projects/beto` path or caller variable leaks into a generated argv.
The profile must export these variables:

- `DC_ACCOUNT`, `DC_PARTITION`, `DC_GPU_SPEC`
- `DC_ACTIVATE`, `DC_HF_HOME`, `DC_HF_OFFLINE`
- `DC_REPO_ROOT`, `DC_TIME_DEFAULT`

A missing file or variable is a clear error. Every sbatch line uses those variables only:

```
cd $DC_REPO_ROOT && mkdir -p logs
sbatch --export=ALL,DC_CLUSTER=<profile> --account=$DC_ACCOUNT --partition=$DC_PARTITION $DC_GPU_SPEC \
  --time=<T> --job-name=mv2-<stage>-<job> scripts/evaluate_circuit.sbatch <repo-relative evaluate_circuit.py args>
```

`DC_CLUSTER` makes the wrapper source the same profile inside the job, where `DC_ACTIVATE`, `DC_HF_HOME` and
`DC_HF_OFFLINE` act. BLAS thread pinning also belongs in the profile, per ticket 07.

**Walltime `<T>`.** It is the cost model's estimate for the profile's GPU class x 1.5, rounded up to 15 min,
at least `--walltime-floor` minutes. The GPU class is read from `DC_GPU_SPEC` and `DC_PARTITION`.

- **Default floor (60).** Per the orchestrator's ruling, the drift control and the first stage-1 wave run
  with a 01:00:00 limit. Bridges-2 GPU-shared charges actual use.
- **Tightening.** Once the drift jobs have measured the H100 time, lower the floor (e.g. `--walltime-floor
  30`). Also update `SPEEDUP["H100"]` in `mv2_cells.py` and rerun `build_suite.py` if the estimate is far
  off.
- **Fallbacks.** An unknown GPU class falls back to `DC_TIME_DEFAULT`, and `--time` overrides everything.

```
# from the repository root (Delta worktree)
python outputs/_launch_mechanism_v2/evals/check_cells.py                       # all stages, ~1 min
python outputs/_launch_mechanism_v2/evals/gen_cells.py --profile bridges2 --stage control --via scripts/remote/b2.sh --dry
python outputs/_launch_mechanism_v2/evals/gen_cells.py --profile bridges2 --stage control --via scripts/remote/b2.sh \
    --submit --ledger /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/compute-ledger.json
```

`--submit` runs on Delta, the canonical checkout where the ledger lives. It works in this order:

1. **Stage gates.** It refuses stage 1 without `--drift-ok` (the orchestrator accepted the drift control)
   and stage 2 without `--user-go` (the user has seen stage 1).
2. **Placeholders.** It refuses any profile value still shaped `__NAME__`.
3. **Budget.** It enforces the ticket allocation in the ledger section. The section defaults to the one
   named after the profile (`bridges2`), else the top level; `--ledger-section` overrides it.
   - The ticket's reserved GPU-h, reconciled plus in flight, plus the new `--time x GPUs`, must stay within
     `allocations_gpu_hours["06-evaluate-coarse-v2-circuits"]`. That is 12 H100 GPU-h in `bridges2`.
   - The total must also stay within `reserved_gpu_hour_cap` when the section has one.
   - If it does not fit, nothing is submitted. The message says how many leading jobs would fit; use
     `--first N` or `--only`.
4. **Checker.** It runs the checker on this checkout, and any problem aborts.
5. **Per job, in order:**
   - It writes the reservation to the ledger (fields as in the brief, `status: submitting`; read-modify-write
     with an atomic replace) and re-checks the budget on that fresh read.
   - It submits, and records the job id (`status: submitted`) or zeroes a failed reservation.
   - It appends the row to `eval_jobs.txt`.
   - It updates the section's totals.
6. **Where it submits.** It uses local sbatch when `DC_REPO_ROOT` is this checkout, which is the Delta
   case, unchanged. Otherwise `--via SCRIPT` is required, and without it `--submit` refuses. The script is
   called as `SCRIPT submit --time T --job-name N -- <args>`.
   - For Bridges-2 the script is `scripts/remote/b2.sh`. It runs `cd $DC_REPO_ROOT && mkdir -p logs &&
     sbatch --export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=<alloc> -A ... -p ... $DC_GPU_SPEC -t T
     --job-name=N scripts/evaluate_circuit.sbatch <args>` on the login node.
   - That exported environment is what makes the wrapper source the Bridges-2 profile rather than Delta's.
     Bridges-2 login nodes set `SBATCH_EXPORT=NONE`, so variables placed in front of sbatch never reach the
     job. A plain sbatch line would also lack `DC_B2_ALLOC`.
   - A test runs the real `b2.sh submit --dry` on the generator's argv. It checks that prefix token by
     token and that the evaluate_circuit.py arguments arrive unchanged.

After a job ends, reconcile its reservation with sacct as the brief says, via `b2.sh status`.

Before a remote submission, the code and data must be synced (ticket 07). The checker checks the Delta
copy only.

## The checker (`check_cells.py`)

For every job it checks these things:

- `evaluate_circuit.build_parser().parse_args(...)` accepts the exact argument list.
- Every `--evals` name is known, and none is `benchmarks`.
- Exactly one `--task-from` is given.
- Every bound circuit and task source exists under the repo root, with `config.json`, plus
  `active_nodes.json` for circuits.
- `evaluation.circuits.resolve_circuits` composes every expression from the real masks. Each cell has its
  `expected_heads`. Knockout cells keep zero MLP units, and sufficiency cells keep all of them. This is
  the old dry-run's "complement verified" check.
- `resolve_tasks` binds one test set with the cells' task and condition, and the derived
  `data/datasets/<dataset>/test` exists with at least `test_samples` rows.
- Atomic home-test-set cells are bound to their own run, so sanity really runs.
- No two jobs share an output dir.

It never calls `build_session`, `main()` or `--dry-run`, loads no model and touches no GPU. Current
result: 26 jobs, 65 cells, 0 problems.

## Cost per stage (GPU-h, one GPU per job, packed)

Here is how the cost model works:

- Cell minutes on an A40 come from sacct of past coarse cells (recon A1/A3). KO is 26 min, suff 27 min,
  nopressure suff 8 min and nopressure KO 11.5 min, plus a 3.5 min load per job.
- The A100 speed-up is 2.26x and H200 is 5.4x, both measured.
- **H100, measured by the drift control** (2026-10-24, node w010):
  - one coarse KO cell took 401 s and 367 s, so the speed-up is 26 / 6.4 = 4.0x an A40;
  - start-up from job start to suite creation, covering env, imports and model load from /ocean, took
    10.4 min cold and 21 s when the node's page cache was warm (the second job ran on the same node right
    after the first);
  - the estimates use the cold 10.5 min;
  - H100 sufficiency cells are not measured yet and are assumed to scale like KO.

Reserved means `--time` x GPUs.

| stage | cells | jobs | A40 elapsed | A40 reserved | H100 elapsed (cold loads) | H100 reserved (floor 60) | H100 reserved (floor 30) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control | 2 | 2 | 0.98 | 2.00 | 0.57 (actual 0.41) | 2.00 | 1.00 |
| 1 | 24 | 12 | 11.25 | 18.75 | 4.74 | 12.00 | 8.25 |
| 2 | 33 | 12 | 13.57 | 25.50 | 5.32 | 12.75 | 9.75 |
| 2 + conditional | 39 | 12 | 16.18 | 29.25 | 5.97 | 13.50 | 10.50 |

**Elapsed.** With cold loads everywhere the suite is about 11.3 H100 GPU-h. The drift control took 0.75
reconciled, stage 1 about 4.7 and stage 2 with the conditional cells about 6.0. That leaves almost no
room in the 12 h allocation. Loads are 12 x 10.5 min, about 2.1 h per stage, and warm loads, with jobs
sharing a node's page cache, remove most of that.

**Reservations.** Use `--walltime-floor 30` from stage 1 on, now that the timing is measured. Stage 1 then
reserves 8.25 h in one wave, within the 11.25 h left after the drift control. Stage 2 has to wait for
stage 1 to reconcile.
