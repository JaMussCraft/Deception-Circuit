# 06 — Evaluate the six coarse v2 circuits (stage 1, then stage 2 on the user's go)

**What to do:** define and run the two-cell evaluation suite of spec §14.G14 for the six coarse heads-only circuits
of ticket 05, stage 1 first; hand back a results table after stage 1 (HARD STOP before stage 2).

**Status:** resolved
**Type:** task
**Blocked by:** 05 (done); 07 for remote execution (suite definitions and operands can be built before 07 lands)
**GPU allocation:** 12 H100 GPU-h on Bridges-2 (separate ledger section `bridges2`); Delta only as a fallback with
the orchestrator's approval.

## Facts to build on

- Recon: `reports/06-recon-evals-and-bridges2.md` (cell design, costs, head-set sizes, prerequisites).
- Run dirs: `reports/05-training-summary.md`. Reference wave: main checkout
  `outputs/llama-8b-instruct_sdr_coarse/_launch/` (`submit_headsko.sh`) and the format-control suite
  `outputs/_launch_format_control/{README_suites.md,suites.json,fc_cells.py,fc_launch.py}` in the worktree.
- `evaluate_circuit.py` accepts the v2 task ids. Do not edit `component_analysis/dataloaders.py` (not in scope).
- The cluster profile interface is owned by ticket 07: `scripts/cluster/<name>.env` exporting `DC_ACCOUNT`,
  `DC_PARTITION`, `DC_GPU_SPEC` (e.g. `--gpus=h100-80:1`), `DC_ACTIVATE` (shell snippet to activate the env),
  `DC_HF_HOME`, `DC_HF_OFFLINE` (0/1), `DC_REPO_ROOT`, `DC_TIME_DEFAULT`. Generate sbatch lines that only use
  these variables; never hard-code Delta or Bridges-2 settings in the suite generator.

## Acceptance criteria

- [x] `outputs/_launch_mechanism_v2/evals/suite_v2.json`: every cell of stage 1 (24) and stage 2 (33 + the
      conditional D-H cross-task cells, flagged `conditional: true`) with expression, operand, test task/condition,
      evals list, output dir; plus one drift-control cell reproducing an already-evaluated Delta cell (the coarse
      SDR D heads-only KO cell), with the Delta reference values recorded next to it.
- [x] All-MLP operand rebuilt from a v2 run with a correct config; nopressure config-only stand-in dirs for the
      three tasks; both documented in the suite README.
- [x] `outputs/_launch_mechanism_v2/evals/gen_cells.py --profile <name> --stage {control,1,2} --dry` prints
      sbatch lines using only the profile variables; `--submit` writes job ids to `eval_jobs.txt`. A login-node
      checker parses every generated `evaluate_circuit.py` command with its argparse and resolves every path.
- [x] Drift control run first and compared to the Delta reference (report the per-metric deltas); stage 1 only
      after the orchestrator confirms the drift is acceptable.
- [x] Stage-1 results table in `reports/06-stage1-results.md` (+ `.json`): per cell faithfulness KL / accuracy /
      exact match, knockout effect vs the random-circuit null (4/4 separation or not), interchange/pressure
      metrics; per task the D-H home-task KO effect called out explicitly with a recommendation on the
      conditional stage-2 cells.
- [x] Results rsynced back to the worktree (Delta canonical) under each run dir's `evaluations_*/` or the suite
      output dir; ledger `bridges2` section reconciled with sacct from Bridges-2.
- [x] No EVAL 5, no training, no component analysis. Tests in both envs: only the baseline failures.
- [x] Review in `reports/06-evaluate-coarse-v2-circuits-review.md`; progress in `reports/06-handback.md`.

## Hand-back (HARD STOP after stage 1)

Report the stage-1 table and the D-H recommendation to the orchestrator. Stage 2 needs the user's go.

## Comments

### Phase A (impl-06, 2026-10-24)

- Built: `outputs/_launch_mechanism_v2/evals/` holds the suite definition `suite_v2.json` and the cell
  planner, operands, launcher, checker and drift comparison. The orchestrator committed them in ad067ff.
  The README documents all of it, and `reports/06-handback.md` has the detail and the file list.
- Rulings applied:
  - (a) one task-agnostic `m`; test sets come only from `--task-from`;
  - (b) two drift cells, one per Delta reference, each with that job's own argv;
  - (c) a 01:00:00 walltime floor first, plus ledger enforcement in `--submit`;
  - the follow-ups: no environment passthrough, CONTEXT.md block names, tighter tests, and a Bridges-2
    route only through `scripts/remote/b2.sh` with `--export=ALL,DC_CLUSTER=bridges2,DC_B2_ALLOC=...`.
- Checker: 26 jobs, 65 cells, 0 problems. All head counts equal recon A3.
- Tests on the final Phase A code. `tests/test_mechanism_v2_evals.py` has 37 tests and passes in both envs.

  | env | result |
  | --- | --- |
  | base py3.9 | 8 failed, 1721 passed, 58 skipped |
  | mgnp py3.12 | 8 failed, 1874 passed, 19 skipped |

  The failures are exactly the 8 baseline names in both envs, none new.
- Review: two axes, in `reports/06-evaluate-coarse-v2-circuits-review.md`. No open findings.

### Phase B (in progress)

- **Pre-checks.** The Bridges-2 clone is at e1ad804 and clean. Its drift inputs, `evaluate_circuit.py` and
  the wrapper have the same sha256 as on Delta. `sbatch --test-only` through b2.sh accepted both drift jobs.
- **First attempt failed before sbatch.** `scripts/remote/b2.sh` has no execute bit in the checkout (mode
  660). The submission raised PermissionError before sbatch, so nothing was submitted.
  - That reservation was set to `submit-failed` and 0 h.
  - `gen_cells.py` now runs a non-executable dispatcher through bash, and frees the reservation on any
    launch error. Both are tested.
- **Drift control submitted.** 49774554 (`drift_sdr_coarse_D_hko`, primary) and 49774563
  (`drift_sdr_coarse_D_headsko`, secondary) went in 2026-10-24 13:04, at 2 x 1.0 H100 GPU-h reserved in
  ledger `bridges2`.
- **Drift control done.** Both jobs completed on w010: 18:18 and 06:32, with a KO cell of 401 s / 367 s and
  a cold start-up of 10.4 min. The deltas against the primary A40 reference are at most 1e-3 on rates and
  under 1% on logit diff and KL. The verdict quantities are identical, and the two H100 runs match each
  other exactly. The tables are in `reports/06-handback.md`, and the recommendation is to accept.
- **Ledger reconciled.** `bridges2` shows 0.5 + 0.25 h, so ticket 06 has used 0.75 of 12.
- **Cost model updated.** H100 is now 4.0x an A40, with a 10.5 min cold load (mv2_cells, suite_v2.json,
  README).
- Stage 1 waits for the orchestrator.
- **Stage 1 done (2026-10-24).** All 12 packed jobs completed, exit 0:0: 49787284-49787309 on w002, w004
  and w010, 6-37 min each. The results are fetched to `outputs/_suites/mechanism-v2-coarse/stage1/`, with
  sacct in `sacct.json`.
- **Ledger.** Ticket 06 stands at 5.25 of 20 H100 GPU-h reconciled, 3.40 actual.
- **Report.** The results are in `reports/06-stage1-results.md` and `.json`, built by
  `outputs/_launch_mechanism_v2/evals/stage1_results.py` with the reading in `reports/06-stage1-reading.md`.
  - The D and D&H knockouts remove the deceptive answer, but invert the no-pressure answers too: they are
    answer machinery.
  - D-H is strong on far (0.191, 4/4) and ser (0.228, 4/4), and weak on sdr (0.513, 1/4).
  - The recommendation is to run the conditional cells for D_far-H_far and D_ser-H_ser (4 of 6).
- **Tests.** `tests/test_mechanism_v2_evals.py` passes all 40 tests in both envs. The full suites were last
  run before `stage1_results.py` was added; that module only adds tests and does not touch shared code.
- **HARD STOP.** Stage 2 waits for the user's go.
- **Stage 2 done (2026-10-24, user go G16, all 6 conditional cells).** All 12 packed jobs completed, exit
  0:0: 49790833-49790847, 4-51 min each. They are fetched to `outputs/_suites/mechanism-v2-coarse/stage2/`
  with `sacct.json`.
- **Ledger.** Ticket 06 bridges2 stands at 11.0 of 20 H100 GPU-h reconciled (7.39 actual); stage 2 reserved
  10.5 and reconciled to 5.75.
- **Reports.**
  - `reports/06-stage2-results.md/.json`, built by `stage2_results.py`, with its reading in
    `06-stage2-reading.md`.
  - `reports/06-evaluation-reading.md`, the combined verdict.
  - The verdict: shared answer machinery (the 31-head D core, in H too), with small partial
    mechanism-specific exclusives. The most mechanism-like task is far.
- **Review.** The Phase B addendum is in `reports/06-evaluate-coarse-v2-circuits-review.md`.

**Status:** resolved (pending the orchestrator's commit; no further GPU jobs).
