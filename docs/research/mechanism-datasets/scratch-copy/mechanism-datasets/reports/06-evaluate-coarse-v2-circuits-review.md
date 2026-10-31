# Ticket 06 Phase A review (two axes, mattpocock-skills:code-review)

Scope: the new, uncommitted ticket-06 files under `outputs/_launch_mechanism_v2/evals/` and
`tests/test_mechanism_v2_evals.py`, against branch base bd67758. Two sub-agents ran in parallel, one for
Standards and one for Spec. The orchestrator then ruled on the spec findings. The dispositions below are
the state after the fixes.

## Standards

The standards were these:

- the agent brief's design and shell rules;
- CONTEXT.md vocabulary;
- line length 120;
- the Fowler smell baseline.

No hard violations were found, and the code is py3.9-clean.

| finding | disposition |
| --- | --- |
| `gen_cells.py` hard-coded `PASSTHROUGH = ("DC_DELTA_REPO_ROOT",)`, which is Delta knowledge in the generator | fixed (orchestrator follow-up): no caller variable reaches the profile shell (only PATH, HOME), so every value comes from the profile file. `test_generator_hard_codes_no_cluster_setting` forbids `DC_DELTA` in the source. `test_generated_argv_carries_no_value_the_profile_did_not_give` checks that no real-profile value, no `/projects/beto` path and no caller `DC_*` variable appears in any generated sbatch argv |
| CONTEXT.md avoids "control" for the Honest Condition / Format Circuit; blocks were named `control_H_on_D`, `control_nopressure` | fixed: renamed `H_on_D_test_set`, `D_on_nopressure` in mv2_cells, README and suite_v2.json (the stage name `control` means drift control and stays, as in the ticket) |
| drift cell built by hand, duplicating `add()`'s schema | fixed: drift cells go through `add()` |
| `MAIN_CHECKOUT` defined three times | fixed: `mv2_cells.MAIN_CHECKOUT`, imported by build_operands / build_suite (the test keeps its own literal as an independent reference) |
| `drift.py` opened suite_v2.json itself | fixed: `mc.load_suite()` |
| mid-file `import sys`, no-op comprehension, dict-copy comprehension | fixed |
| test `PROFILE_VARS` unused; `_stage` re-implemented `select` | fixed |
| test computed the expected `--time` with the functions under test | fixed: literal times (`01:00:00` at the default floor; `00:45:00` / `00:30:00` at `--walltime-floor 30`) |
| checker test asserted only that "nopressure" appeared | fixed: asserts the "test-set condition nopressure" finding |
| copies of fc_cells' `COMMON_ARGS` / `job_args` / `walltime` | kept: the v2 suite is a side build, and fc_cells is format-control's file; the walltime floor now matches fc (60) |
| Data Clumps (`add()` parameters, dt/ht/npt dicts), Primitive Obsession (dict cells), Repeated Switches on `kind`, Shotgun Surgery for a new GPU class, `_active` Middle Man | accepted as judgement calls: cells are JSON records by design (suite_v2.json is the definition), and the kind switch has two values |

## Spec

The spec sources were ticket 06, spec 14.G14, the recon and the Phase A brief. The cell counts check out:

- 24 / 33 / +6 cells;
- every expression, test set and operand;
- head counts equal to recon A3.

| finding | disposition |
| --- | --- |
| one all-MLP operand (from far_v2 D) serves all tasks; recon suggested one per task dir | orchestrator ruling (a): accepted, task-agnostic. README states its source run and that the evaluator takes test sets only from `--task-from`; test `test_test_set_comes_from_task_from_never_from_the_operand_config`; the checker requires exactly one `--task-from` |
| drift reference: fc 22895982 primary, the named evaluations_headsko cell 22316469 secondary | ruling (b): run both. Two drift cells, each with its reference's own argv; a test compares each against the reference job's recorded `suite.json` argv |
| 30-min walltime floor risked a timeout on the job that measures H100 speed | ruling (c): floor 60 (`01:00:00`) for the drift control and the first stage-1 wave; `--walltime-floor` tightens later |
| sanity requested on composed sufficiency cells where the orchestrator wrote `null pressure` | documented in the README (skipped with a recorded reason; eval 1 runs on exactly the six home-test-set atomic cells) |
| `--submit` did not enforce the 12 GPU-h allocation | fixed: `--submit --ledger` budget-checks reconciled + in-flight + new against the ticket allocation (and any cap), refuses with how many leading jobs fit, writes reservations and job ids to the ledger, updates totals; tests for refusal, reservation and the remote dispatcher |
| `--submit` ran only on the profile's cluster, away from the ledger | fixed: `--submit` runs on Delta; a remote profile submits through `--via scripts/remote/b2.sh` (ticket 07's `submit -- ARGS` interface) |
| GPU flag mix in the wrapper header; BLAS thread pinning | ticket 07 (orchestrator ruling); DC_GPU_SPEC is taken from bridges2.env as-is (it is now several flags, so `gpu_count` reads every spec form; parametrized test) |
| a Bridges-2 job needs DC_CLUSTER=bridges2 and DC_B2_ALLOC in its submit environment (ticket 07 follow-up) | fixed: a remote profile can only submit through `--via scripts/remote/b2.sh` (refused otherwise). `test_bridges2_submission_through_b2sh_sets_the_jobs_submit_environment` runs the real `b2.sh submit --dry` on the generator's argv and checks the remote command token by token: the `cd`, the `--export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=<alloc>` option right after sbatch (updated after impl-07 moved off the env prefix: Bridges-2 sets SBATCH_EXPORT=NONE), the account, partition, GPU spec, time and job name, and the unchanged evaluate_circuit.py arguments. Delta submissions are unchanged |
| scope additions (gates, `--only`, `--no-pack`, `--profile-file`, `--time`, drift.py, extra GPU classes) | kept; harmless, and drift.py is the Phase B comparison |

## Outcome

Two smells were accepted as judgement calls at the orchestrator's ruling: the duplication with
`fc_cells.py` and the parameter count of `add()`. There are no open findings. Tests are in
`tests/test_mechanism_v2_evals.py` (36 tests). The full-suite
results per env are in the ticket's Comments section.

## Phase B addendum: results scripts and runs (self-review, both axes)

The scope is `stage1_results.py`, `stage2_results.py`, the drift and launcher fixes made during Phase B,
and the report files. The review was done in-agent; no sub-agents were spawned for this addendum.

**Spec.** Every ticket item is covered:

- Drift control run first and compared per metric to both Delta references, then accepted (G15).
- Stage 1 (24 cells) and stage 2 (33 + 6 conditional, all 6 per G16) evaluated on one GPU type
  (H100, GPU-shared).
- Results fetched to the Delta worktree under `outputs/_suites/mechanism-v2-coarse/{control,stage1,stage2}/`.
- Ledger `bridges2` reconciled from sacct after every wave.
- `06-stage1-results.md/.json` give per cell:
  - faithfulness accuracy, EM, LD and KL;
  - the knockout against its random-circuit null, with the separation count and the 4/4 flag;
  - the pressure, interchange, honest-instruction and no-pressure rows;
  - the D-H call with a recommendation.
- `06-stage2-results.md/.json` cover cross-task transfer, the core, exclusives and XOR, H on D's test set,
  D on nopressure, and D-H cross-task.
- `06-evaluation-reading.md` gives the combined verdict.
- No EVAL 5, no training, no component analysis. One resubmission per job was never needed: no job failed.

**Standards.**

- The scripts reuse `drift.metrics_of` and the stage-1 parsers rather than re-parsing, which avoids
  duplication.
- Paths come from `suite_v2.json` results, with nothing hard-coded except the `.scratch` reports default,
  which is a CLI flag.
- The D-H "strong" rule is written once, in `dh_call`, and stated in the report: 4/4 separation, the
  written gate. No new threshold was invented.
- The sanity column says "tolerance flag" rather than "FAIL" because the deltas are cross-GPU drift, and
  the reading says so.
- Judgement calls:
  - `markdown()` in both scripts is long, table-building code (Long Function); acceptable for report
    writers.
  - The hand-written readings live in `.scratch` and are included verbatim, so a regenerated table can
    drift from a stale reading. The reading must be re-checked whenever the numbers change.
- Phase B fixes:
  - a dispatcher without the execute bit now runs through bash;
  - a launch error zeroes its reservation;
  - reservation ids are unique per process;
  - `gpu_count` parses multi-flag GPU specs;
  - the cost model is recalibrated from measured H100 times.

  Each has a test.

**Open.** There are no code findings. One interpretive caveat is carried into the reading: the knockout
evidence is interchange-only. A mean/zero-ablation replication is suggested and was not run.
