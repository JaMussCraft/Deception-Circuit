# Mechanism-analysis evaluator suite (ticket 01 builds it, ticket 03 runs it)

This launcher runs the `evaluate_circuit.py` cells of the mechanism-analysis feature. Today that is phase 1A
of the spec (section 4): circuit-level mean and zero knockouts of the six coarse heads-only v2 circuits, read
by rule R-A1 (spec section 2.5). It is a copy-and-adapt of ticket 06's launcher
(`../_launch_mechanism_v2/evals/`), which stays untouched. The circuits, the all-MLP operand `m` and the
measured cost rates are imported from there.

Every path below and in every generated command is relative to the repository root (`DC_REPO_ROOT`), so the
same suite runs on Delta and on Bridges-2.

## Files

| file | what |
| --- | --- |
| `ma_cells.py` | the cell plan (`plan_cells`), scheme groups and chained jobs (`jobs_for`), `group_args`, `chain_args`, cost model, walltime rule |
| `suite_ma.json` | the suite definition, written by `ma_build_suite.py`; a test fails when it is stale |
| `ma_build_suite.py` | writes `suite_ma.json` |
| `ma_gen_cells.py` | sbatch lines from a cluster profile: `--dry`, `--test-only`, `--submit` (ledger under its lock) |
| `ma_check_cells.py` | the login-node checker of every generated `evaluate_circuit.py` command |
| `eval_jobs.txt` | one row per submitted job; `--submit` creates it |

Tests: `tests/test_mechanism_analysis_launcher.py`. The chain wrapper and the variant-matched mean bank are
tested in `tests/test_mechanism_analysis_infra.py` and `tests/test_mechanism_analysis_mean_bank.py`.

## Phase 1A cells (33)

Per task t, heads-only knockout cells `(E) - m` at leaf on D_t's own test set (`<t>_v2`), `--evals knockout`,
`--n-random 20 --knockout-null-count 20`, over the seven sets of RQ-A:

| set | E | label (`<label>_hko`) |
| --- | --- | --- |
| 1 | D_t | `D_t` |
| 2 | H_t | `H_t` |
| 3 | core = D_far & D_sdr & D_ser | `D_core` |
| 4 | excl_t = D_t - D_u - D_v | `D_t_minus_D_u_minus_D_v` |
| 5 | D_t - H_t | `D_t_minus_H_t` |
| 6 | (D_t - H_t) - core | `D_t_minus_H_t_minus_D_core` |
| 7 | D_t & H_t | `D_t_and_H_t` |

| scheme | sets | extra arguments |
| --- | --- | --- |
| mean | 1-7 | `--ablation mean --variant-mean-bank no_pressure` |
| zero | 3-6 | `--ablation zero` |
| interchange | 6 | `--ablation interchange` |

The labels of sets 1-5 and 7 are ticket 06's, so a phase-1A cell and the interchange cell of record share a
name.

Head counts (from the masks; the checker recomposes them with the evaluator):

| task | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| far | 58 | 60 | 31 | 8 | 26 | 15 | 32 |
| sdr | 60 | 58 | 31 | 14 | 21 | 15 | 39 |
| ser | 55 | 69 | 31 | 10 | 19 | 19 | 36 |

The spec lists 36 cells. On ser, `D_ser - H_ser` holds no core head, so set 6 is set 5: the ser set-6 cells
under mean and zero would repeat the set-5 cells, and the ser set-6 interchange cell would repeat ticket 06's
`D_ser_minus_H_ser_hko` (its stage-1 cell on `ser_v2`). R21 drops the three, so phase 1A has 33 cells.
`ma_cells.dropped_cells()` finds them from the masks (set 6 equal to set 5) and `suite_ma.json` records them under
`dropped_cells`, with the identity and the interchange cell of record.

### The variant-matched mean bank (R13)

Under `--ablation mean` the task rows are ablated with the bank over D's test split, as before. With
`--variant-mean-bank no_pressure` the `no_pressure` variant rows run twice (R19(2), R21):

- **Task bank.** Under `variants.no_pressure`, exactly as without the flag.
- **Their own bank.** Under `variants_matched_bank.no_pressure`, with a bank collected over those very rows:
  D's test prompts with the Pressure Clause removed from both streams, through the evaluator's own variant
  loader. For the v2 tasks those rows are `<t>_v2_nopressure`'s test split, row for row and in both streams. A
  test pins that identity on the real datasets.

The `honest_instruction` rows keep the task bank. `knockout.json` records the bank per section that ran
(`mean_banks`), and every variant section names its own (`mean_bank`, with row and token counts for the matched
bank). Without the flag nothing new is written and `knockout.json` is byte-identical to the branch base (tested).
The mean is still position-pooled and broadcast to every position; that caveat goes in spec section 7.

R-A1 decides the no-pressure column under zero ablation. The mean no-pressure column is robustness.

## Jobs: one per task, its schemes chained

`evaluate_circuit.py` takes one `--ablation` per process, so a scheme is one process (a "group"). Each group
has its own output dir and suite name:

```
outputs/_suites/mechanism-analysis/phase1a/p1a_<t>__<scheme>/
    cells/<label>__leaf/<t>_v2/<scheme>/knockout.json
```

Nothing lands under ticket 06's `outputs/_suites/mechanism-v2-coarse/`. `scripts/evaluate_chain.sbatch` runs
the groups of a task in one Slurm job. The groups are separated by `:::` and run in the order mean, zero,
interchange (ser has no interchange group). Each group goes through `scripts/evaluate_circuit.sbatch`, so the
cluster profile acts as for a single run. Every group runs even if an earlier one fails, and the job exits with
the first failure's status. The job pays one cold model load and a warm one per later group. Nothing carries over
between groups: each process builds its own banks.

## Cost (one H100 per job)

The cost model per job is the cold load, plus the warm loads, plus the cells, plus the mean groups' extras:

- **Cold load:** 10.5 min (measured by ticket 06).
- **Warm loads:** 0.4 min per later group (measured by ticket 06).
- **Cells:** 26 A40-min / 4.0 each, which is 6.5 min a cell on an H100 (measured by ticket 06).
- **Mean banks:** 3 x 2.0 A40-min / 4.0 per mean group. Derived, not measured.
- **Matched no_pressure run:** 4.0 A40-min / 4.0 per mean cell (six passes at about 0.65 A40-min). Derived,
  not measured.

Walltime is the estimate x 1.5, rounded up to a quarter hour.

| job | cells (mean + zero + interchange) | H100 estimate | walltime | reserved GPU-h |
| --- | --- | --- | --- | --- |
| p1a_far | 7 + 4 + 1 | 97.8 min | 02:30:00 | 2.5 |
| p1a_sdr | 7 + 4 + 1 | 97.8 min | 02:30:00 | 2.5 |
| p1a_ser | 6 + 3 + 0 | 76.9 min | 02:00:00 | 2.0 |
| total | 33 | 4.54 GPU-h (derived) | | **7.0 GPU-h (14 SU)** |

The spec's numbers are about 94 min per job, 7.5 reserved and 4.7 expected. The first job recalibrates the
bank and matched-run rates. The evaluator log prints a time stamp per group (`=== evaluate_chain: group i of n
...`).

## Generating, testing and submitting

```
# from the repository root (Delta worktree)
python outputs/_launch_mechanism_analysis/ma_check_cells.py
python outputs/_launch_mechanism_analysis/ma_gen_cells.py --profile bridges2 --stage 1a --via scripts/remote/b2.sh --dry
python outputs/_launch_mechanism_analysis/ma_gen_cells.py --profile bridges2 --stage 1a --via scripts/remote/b2.sh --first 1 --test-only
python outputs/_launch_mechanism_analysis/ma_gen_cells.py --profile bridges2 --stage 1a --via scripts/remote/b2.sh \
    --submit --ledger /projects/beto/swong2/Alignment/.scratch/mechanism-analysis/compute-ledger.json
```

Run `b2.sh` and the generator on the Delta login node that holds the SSH masters. Bridges-2 sees only pushed
code (R3). Before the first wave, push the branch, then run
`DC_B2_BRANCH=mechanism-analysis scripts/remote/b2.sh sync-code`. Phase 1A needs no new data on Bridges-2: the
six run dirs, `m` and the `<t>_v2` test sets are already there from ticket 06, and the variant rows are built
from `<t>_v2` at run time.

- **Ledger.** `--submit` writes reservations to the `bridges2` section under ticket
  `03-phase1-ablation-replication-and-sweeps`.
- **Lock.** Every read-modify-write holds `compute-ledger.lock/`, made with mkdir, with the writer in `owner`.
  A held lock is an error and is never broken.
- **Budget.** The ticket's reconciled plus in-flight hours, plus the new reservations, must stay within its
  allocation and within the section cap. If they do not, nothing is submitted.
- **Delta fallback.** It needs the orchestrator's approval per wave. Use `--profile delta --account <bjhz
  account> --partition <A40 or H200 partition> --ledger-ticket "<the delta section's fallback key>"`. On an
  A40 the far and sdr jobs estimate about 5.9 h (ser 4.5 h). On an H200 they estimate about 1.2 h (ser 0.9 h).
- **Reconcile.** After a job ends, reconcile its reservation with `b2.sh status <id>`, as the agent-brief
  says.
- **Fetch.** Fetch with `scripts/remote/b2.sh fetch`. With no paths it brings back `outputs/_suites`, which
  includes `mechanism-analysis/`, and `outputs/_analyses/mechanism-analysis-*`.
