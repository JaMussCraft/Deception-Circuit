# Ticket 06 hand-back: Phase A (login node, no GPU, no submission)

Status: Phase A is done, with the orchestrator's review rulings (a), (b) and (c) applied. Phase B, the drift
control on Bridges-2, waits for the orchestrator's go. No job was submitted, no `evaluate_circuit.py` ran
in any form, and the ledger is unchanged.

## What was built

All of it lives under `outputs/_launch_mechanism_v2/evals/`. The README documents everything.

- **`suite_v2.json`** holds 65 cells:
  - control 2: drift cells, one per Delta reference;
  - stage 1 with 24 cells;
  - stage 2 with 33 cells plus 6 `conditional: true` D-H cross-task cells.

  Each cell records expression, operands, test task, condition and dataset, evals, block,
  `expected_heads`, argv extras and result dir. The file also lists the packed jobs (12 for stage 1, 12
  for stage 2), estimates and the Delta reference metrics.
- **Two-cell design.** Sufficiency is the atomic circuit or `(E) | m` with evals `sanity null pressure`.
  Sanity is skipped, with a recorded reason, on composed and non-home cells, which the README documents.
  A knockout is `(E) - m` with evals `knockout`. Compositions are at leaf, with interchange ablation,
  `--n-random 20` and `--knockout-null-count 20`.
- **The `m` operand** is `operands/allmlp_nomb_v2`.
  - It is built from the far_v2 D run by fc `build_allmlp.py`, and its masks equal fc `allmlp_nomb`.
  - It serves all three tasks. Ruling (a) accepted that, because the operand is task-agnostic.
  - Test sets come only from `--task-from`. A test proves this on a real job, and the checker requires
    exactly one `--task-from`.
- **Stand-ins.** `standins/{far,sdr,ser}_v2_nopressure/config.json` are config-only.
- **Drift control, ruling (b).** There are two jobs, about 0.45 H100 GPU-h estimated in total, with the measured 7.7-minute /ocean model load. Each
  reproduces one Delta A40 reference with that job's own argv, and a test checks this against the
  references' recorded `suite.json`:
  - `drift_sdr_coarse_D_hko` reproduces fc job 22895982 and is the primary;
  - `drift_sdr_coarse_D_headsko` reproduces SDR-wave job 22316469.

  The two references agree exactly on the task and wikitext rows. Their pressure-variant rows differ (for
  example 0.169 vs 0.228), because of an evaluator change, since the dataset is unchanged since Aug 18.
  The v1 D run is byte-copied into `drift_control/`, with sha256 recorded.
- **`gen_cells.py`.**
  - `--dry` prints sbatch lines built from the `DC_*` profile variables only, with paths relative to the
    repo root.
  - Walltime is the estimate x 1.5 with a 60-minute floor, per ruling (c). `--walltime-floor` tightens it
    later.
  - `--submit` runs on Delta, in this order:
    1. stage gates (`--drift-ok`, `--user-go`) and the placeholder refusal;
    2. a budget check against the ledger's `bridges2` section, ticket allocation 12, counting reconciled
       plus in-flight plus new; it refuses beyond the allocation and says how many leading jobs fit;
    3. the checker;
    4. per job, a ledger reservation (read-modify-write, atomic), then the submission, through
       `--via scripts/remote/b2.sh` for Bridges-2, then the job id recorded in the ledger and in
       `eval_jobs.txt`, and the totals updated.
- **Profile isolation and the Bridges-2 route** (orchestrator follow-ups).
  - Only PATH and HOME reach the profile shell, so no caller variable can change a value. A test checks
    that no real-profile value, `/projects/beto` path or caller `DC_*` variable appears in any generated
    argv.
  - A remote profile can submit only through `--via scripts/remote/b2.sh`. That script supplies
    `--export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=<alloc>`, the job environment the wrapper needs (Bridges-2 sets SBATCH_EXPORT=NONE).
  - A test runs the real `b2.sh submit --dry` on the generator's argv. It checks the remote command token
    by token.
  - Delta submissions are unchanged.
- **`check_cells.py`.** Its current result is 26 jobs, 65 cells, 0 problems. It never calls
  `build_session`, `main()` or `--dry-run`.
- **`drift.py`**, run with no arguments after the drift jobs, gives per-metric deltas for both cells
  against their references.

## Files to commit

Worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets`:

- outputs/_launch_mechanism_v2/evals/README.md
- outputs/_launch_mechanism_v2/evals/mv2_cells.py
- outputs/_launch_mechanism_v2/evals/build_operands.py
- outputs/_launch_mechanism_v2/evals/build_suite.py
- outputs/_launch_mechanism_v2/evals/gen_cells.py
- outputs/_launch_mechanism_v2/evals/check_cells.py
- outputs/_launch_mechanism_v2/evals/drift.py
- outputs/_launch_mechanism_v2/evals/suite_v2.json
- outputs/_launch_mechanism_v2/evals/operands/allmlp_nomb_v2/active_nodes.json
- outputs/_launch_mechanism_v2/evals/operands/allmlp_nomb_v2/config.json
- outputs/_launch_mechanism_v2/evals/standins/far_v2_nopressure/config.json
- outputs/_launch_mechanism_v2/evals/standins/sdr_v2_nopressure/config.json
- outputs/_launch_mechanism_v2/evals/standins/ser_v2_nopressure/config.json
- outputs/_launch_mechanism_v2/evals/drift_control/sdr_coarse_D_260922-092742/active_nodes.json
- outputs/_launch_mechanism_v2/evals/drift_control/sdr_coarse_D_260922-092742/config.json
- outputs/_launch_mechanism_v2/evals/drift_control/sdr_coarse_D_260922-092742/provenance.json
- tests/test_mechanism_v2_evals.py

Do not commit `outputs/_launch_mechanism_v2/evals/__pycache__/`. Ticket 07's files are not in this list.
The branch must be pushed after this commit so Bridges-2 can `git pull` it. The drift run copy and the
operands travel with the code.

## Tests

| env | result |
| --- | --- |
| base (py3.9) | see the ticket's Comments section (final run) |
| mgnp (py3.12) | see the ticket's Comments section (final run) |

`tests/test_mechanism_v2_evals.py` has 36 tests, all passing in mgnp.

## Phase B: what it needs, and the commands

1. **Ticket 07 ready.** That means:
   - `bridges2.env` holds the real allocation (it now reads `cis260361p`);
   - the code is pulled on Bridges-2 at the commit with these files;
   - the six v2 run dirs, the datasets including v1 `data/datasets/sdr`, and the HF caches are present;
   - the wrapper sources `scripts/cluster/${DC_CLUSTER}.env` and pins BLAS threads.
2. **Drift control.** Run this from the Delta worktree root:

   ```
   /u/swong2/.conda/envs/mgnp/bin/python -I outputs/_launch_mechanism_v2/evals/gen_cells.py --profile bridges2 \
     --stage control --via scripts/remote/b2.sh --submit \
     --ledger /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/compute-ledger.json
   ```

   It reserves 2 x 1.0 H100 GPU-h. Then `scripts/remote/b2.sh status <ids>`, then
   `scripts/remote/b2.sh fetch outputs/_suites/mechanism-v2-coarse/control`, then `drift.py`, then
   reconcile the ledger from sacct.
3. **Stage 1, after the orchestrator accepts the drift.** Run the same command with `--stage 1 --drift-ok`.
   At the 60-minute floor stage 1 needs 12.0 h, so `--submit` limits the first wave to the jobs that fit
   (`--first N`). After the drift jobs measure the H100 time, update `SPEEDUP["H100"]` if needed, rerun
   `build_suite.py`, and use `--walltime-floor 30` for later waves.

## Open questions for the researcher

- Packing (several cells per process, about 20% less GPU time, identical cells) is the default.
  `--no-pack` runs one cell per job if isolation is preferred.

## Phase B: drift-control result (2026-10-24)

Jobs 49774554 and 49774563 ran on Bridges-2 node w010 (H100, GPU-shared) and completed with exit 0. The
results are fetched to `outputs/_suites/mechanism-v2-coarse/control/` on Delta.

| job | cell | elapsed | knockout cell | start-up to suite | ledger |
| --- | --- | --- | --- | --- | --- |
| 49774554 | drift_sdr_coarse_D_hko vs fc 22895982 | 18:18 | 401 s | 10.4 min (cold) | 0.5 h |
| 49774563 | drift_sdr_coarse_D_headsko vs SDR wave 22316469 | 06:32 | 367 s | 21 s (warm page cache) | 0.25 h |

Ticket 06 has used 0.75 of its 12 H100 GPU-h on Bridges-2, reconciled from sacct, so 11.25 remain.

The two Bridges-2 cells agree with each other exactly on every metric. The run is deterministic on an H100.

Deltas, H100 minus A40 (`drift.py`):

| metric | A40 (primary) | H100 | delta |
| --- | --- | --- | --- |
| KO accuracy / exact match | 0.002 / 0.002 | 0.003 / 0.003 | +0.001 (1 of 1000 items) |
| KO logit diff | -1.7319 | -1.7256 | +0.0063 (0.4%) |
| KO KL | 1.2111 | 1.2032 | -0.0079 (0.7%) |
| circuit-alone acc / LD / KL | 0.0 / -1.7316 / 1.1964 | 0.0 / -1.7250 / 1.1890 | 0 / +0.0066 / -0.0074 |
| KO null mean acc / LD / KL / EM | 0.3897 / -0.2459 / 0.4838 / 0.4130 | 0.3912 / -0.2456 / 0.4808 / 0.4135 | <= 0.003 |
| KO null percentiles (all 4) | 0, 0, 0, 0 | 0, 0, 0, 0 | 0 |
| KO null z acc / LD / KL / EM | -1.533 / -2.168 / -2.769 / -1.579 | -1.521 / -2.160 / -2.760 / -1.571 | <= +0.012 |
| 4/4 separation count | 2 | 2 | 0 |
| flipped to honest | 998 | 997 | -1 |
| wikitext KL/token / ppl ratio | 0.36437 / 1.43063 | 0.36409 / 1.43005 | -0.0003 / -0.0006 |
| wikitext null mean KL, percentile | 0.39726, 45 | 0.39726, 45 | 0.000002, 0 |
| honest_instruction full / KO acc | 0.234 / 0.764 | 0.232 / 0.760 | -0.002 / -0.004 |
| no_pressure full / KO acc | 0.228 / 0.788 | 0.224 / 0.781 | -0.004 / -0.007 |

The secondary reference (22316469) gives the same task and wikitext deltas. Its pressure-variant rows
differ more: no_pressure full is +0.055 and KO -0.074, and honest_instruction KO is -0.005. That gap is
the known evaluator change between Sep 22 and Oct 15, of the same size as between the two Delta
references, and not GPU drift.

**Recommendation: accept.**

- The cross-GPU drift is about 1e-3 on rates (one item in 1000) and under 1% on logit diff and KL.
- No verdict-bearing quantity changes: separation counts, null percentiles and signs are all the same.
- The H100 runs are bit-reproducible with each other.
- The A40/H100 gap is far below the effect sizes the suite reads. Heads-KO accuracy is 0.003 vs a random
  mean of 0.39.
- Stage-1 numbers should still be compared only within the Bridges-2 suite (one GPU type per suite).

## Stage-1 wave plan (awaiting the orchestrator's go)

- **One wave, packed.** All 12 stage-1 jobs (24 cells) go in one wave, 4 per task:
  - D_suff, 2 cells, `--time 00:45:00`;
  - D_ko, 4 cells, `01:00:00`;
  - H_suff, 1 cell, `00:30:00`;
  - H_ko, 1 cell, `00:30:00`.

  That is `--walltime-floor 30` with the measured cost model.
- **Cost.**
  - Reservation: 8.25 H100 GPU-h, within the 11.25 left.
  - Estimated elapsed with cold loads: 4.74 GPU-h. It will be less if jobs share a node's warm page cache.
- **Command:**

  ```
  /u/swong2/.conda/envs/mgnp/bin/python -I outputs/_launch_mechanism_v2/evals/gen_cells.py --profile bridges2 \
    --stage 1 --drift-ok --walltime-floor 30 --via scripts/remote/b2.sh --submit \
    --ledger /projects/beto/swong2/Alignment/.scratch/mechanism-datasets/compute-ledger.json
  ```

- **Budget risk for stage 2.**
  - Stage 2 with the conditional cells is estimated at 5.97 GPU-h with cold loads, 10.50 h reserved at
    the 30-min floor.
  - After a cold-load stage 1, about 6 h would remain, which covers stage 2's elapsed time only barely and
    its reservation only in waves.
  - Two ways out: an extra Bridges-2 allocation of about 2-3 H100 GPU-h for stage 2, or a ticket-07 step
    that stages the model to node-local storage, which would cut the 10.4-min cold start.

## Stage 1 complete (2026-10-24), HARD STOP before stage 2

- **Jobs.** All 12 packed jobs (24 cells) completed on Bridges-2 with exit 0:0: 49787284-49787309, 6-37 min
  each. They are fetched to `outputs/_suites/mechanism-v2-coarse/stage1/`, with sacct saved in
  `sacct.json` there.
- **Ledger.** Reconciled from sacct, ticket 06 has used 5.25 of 20 H100 GPU-h (3.40 actual), so 14.75
  remain.
- **Report.** The results are in `reports/06-stage1-results.md` (tables and reading) and
  `reports/06-stage1-results.json`. `outputs/_launch_mechanism_v2/evals/stage1_results.py` regenerates
  them, and the reading text is in `reports/06-stage1-reading.md`.
- **Headline.**
  - The D and D&H heads-only knockouts remove the deceptive answer: KO accuracy 0.000-0.001, with 998-1000
    of 1000 flipped. They also turn the no-pressure honest answers deceptive (0.99-1.00), so they carry
    the answer choice itself.
  - far's D-H heads are the only deception-leaning part: KO 0.191, 4/4 separation, and only 18% of
    no-pressure answers inverted.
  - The D-H call is far strong, ser strong (0.228, 4/4, but answer-like), and sdr weak (0.513, 1/4).
- **Recommendation.** Run the conditional cells for D_far-H_far and D_ser-H_ser, 4 of the 6.
  `--include-conditional` adds all 6, and choosing the 4 needs a small selector.
- **Files to commit.**
  - `outputs/_launch_mechanism_v2/evals/stage1_results.py`
  - `tests/test_mechanism_v2_evals.py`
  - `outputs/_launch_mechanism_v2/evals/eval_jobs.txt` (12 new rows)
  - `outputs/_suites/mechanism-v2-coarse/stage1/` (fetched results plus `sacct.json`)

  The reports live in `.scratch` and are not in the repo.

## Stage 2 complete (2026-10-24); ticket 06 resolved

- **Jobs.** All 12 packed jobs (39 cells, all 6 conditional ones included per G16) completed on Bridges-2
  with exit 0:0: 49790833-49790847. They are fetched to `outputs/_suites/mechanism-v2-coarse/stage2/`,
  with sacct in `sacct.json`.
- **Ledger.** Ticket 06 used 11.0 of 20 H100 GPU-h reconciled (7.39 actual) in total, with no Delta GPU.
- **Reports.**
  - `reports/06-stage2-results.md` and `.json`, from `stage2_results.py` with the reading in
    `06-stage2-reading.md`;
  - `reports/06-evaluation-reading.md`, the combined stage 1+2 verdict;
  - the review addendum in `reports/06-evaluate-coarse-v2-circuits-review.md`.
- **Verdict.** The circuits are mostly shared answer machinery.
  - The 31-head D core is common to all three tasks and also in H. Its knockout removes deception on every
    task but inverts honest answers too.
  - The mechanism-specific exclusives (8 / 14 / 10 heads) give small, partial, more specific effects:
    24-48% of deceptive answers removed, 0-34% of honest answers inverted.
  - far's D-H is the most deception-leaning set.
- **Files to commit.**
  - `outputs/_launch_mechanism_v2/evals/stage2_results.py`
  - `tests/test_mechanism_v2_evals.py`
  - `outputs/_launch_mechanism_v2/evals/eval_jobs.txt`
  - `outputs/_suites/mechanism-v2-coarse/stage2/`
