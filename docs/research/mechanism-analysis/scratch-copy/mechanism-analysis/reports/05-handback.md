# 05 hand-back (impl-05): running record

Agent impl-05 (Opus). Worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis`,
branch `mechanism-analysis` (HEAD b3553b0 at start). No git beyond read-only status. Scratch:
`/u/swong2/.claude/jobs/1c836bb8/tmp/impl05/`.

## Status

**claimed** (2026-10-26 ~15:45 CDT). Orientation done: brief, spec (§2.3, §4 phase 3, §9 R1-R28), ticket, phase-1 and
phase-2 readings, 02b hand-back / review / dry-run tables, 04 hand-back, RESUME tail, `path_patching.py`,
`receiver_category.py`, `roles.py` merge rules, `analyze_components.py` carry-forward, `p2_jobs.py`, impl-04's C_t
cost probe.

## Design (before any code; advisor-checked)

- **Grid circuit C_t** per task = ticket 04's proposal (R28), bound at leaf as
  `Ct=(((Df&Ds&De)|(D_t-D_o1-D_o2)|((D_t-H_t)-(Df&Ds&De)))-m)|X` with X = `operands/skct_<t>` (S_k heads + 10 MLPs),
  the six atomic runs and `x_<t>` as references (membership columns). Sizes far 72 (31 core / 8 excl / 15 (D-H)-core /
  18 S_k heads / 10 MLPs, overlaps once), sdr 66, ser 78. `outputs/_launch_mechanism_analysis/p3_jobs.py` writes the
  job files and `docs/research/mechanism-analysis/phase3/ct.json`.
- **Routing check against C_t: verified, not rerun.** The operand-backed C_t equals, Component for Component, the
  complement of phase 1C's `route_c_<candidate>` group on all three tasks (`ct.json` `routing_identity.identical`,
  checked by `p3_jobs.py`, which refuses otherwise). So phase 1C's shares are the routing check of §2.3 for this
  grid: (c) far 0.163, sdr 0.297, ser 0.006 (`p1c_readings.json`).
- **Sample: the default causal sample, n = 100, seed 0** (the selection sample). The ticket runs phase 3 into the
  phase-2 D cell (seed 0), and the A′ weights are the S2p single effects (seed 0). R11(b)'s held-out rule is for
  R-AB's tests (i)/(ii). Consequence stated in the reading: the S_k heads were chosen for large twin effects on this
  sample, so their path magnitudes carry selection pressure; the category is less exposed than the magnitude.
- **Two lines per job, twin first** (one model load). `both` runs the item swap first and the head table is written
  only when an invocation ends; a wall-clock kill in the twin's Segment pass (the one cost unknown) would lose the
  twin split, the categories, the twin sweep and every head-table column. Line 1: `--path-counterfactual neutral_twin
  --path-twin-position-threshold 0.01 --path-completeness-sweep` into cell `d` (a twin-only line sweeps under the
  twin, so no code change to `path_patching.py` is needed; a `--path-sweep-counterfactual` flag was written test-first
  and then reverted as unnecessary). Line 2: `--path-counterfactual item_swap` (Segment pass at the default 0.05) into
  cell `d_is`. Two cells because a second path-patching run into one cell replaces the whole `path_patching.`
  namespace (`carry_forward`). Same forwards as `both` (R25 B, R28): a packing choice under spec §8.
- **Roles merge source.** `--roles-merge-from` appends rows it does not find (`merge_columns`), so the 146-row p2 D
  cell or the `_merge` tables would add 74 U' rows. A CPU builder makes a copy of the Delta p2 D cell (attention,
  DLA, the phase-1 knockout merge) restricted to the phase-3 cell's rows, `roles.*` stripped, with knockout for the
  sweep-appended rows from the phase-1 sweeps (as `p2_merge.py`); the roles pass merges it and `d_is`.
- **02b leftovers.** S4 fixed (the `receiver-category` CLI declares coverage over measured ids, test first). S5 (B2
  without `readout`) deferred: phase 3 runs no attention pass, and every v2 job file passes `readout`.
- **Results**: `p3_results.py` (A′ adjudication, B-selector, B4 / where the pressure enters, completeness share, roles
  counts and the C3 table, curated copies), tests in `tests/test_mechanism_analysis_p3.py`.

## Progress 1 (2026-10-26 15:50 CDT): job files, login dry-runs, commit list

Login `batch --dry-run` (mgnp, `tmp/impl05/login_dry/`): 2 of 2 invocations ok per task; the twin line prints
"completeness sweep ... on neutral_twin only"; stubs removed from the output root afterwards.

| task | C_t (heads + MLPs) | senders x receivers | cells | Q / K / V / MLP-in / Readout | forwards per counterfactual |
|---|---|---|---|---|---|
| far | 62 + 10 = 72 | 73 x 151 | 5,020 | 2,090 / 1,257 / 1,257 / 343 / 73 | 66,235 |
| sdr | 56 + 10 = 66 | 67 x 133 | 4,067 | 1,737 / 955 / 955 / 353 / 67 | 53,768 |
| ser | 68 + 10 = 78 | 79 x 161 | 5,984 | 2,531 / 1,502 / 1,502 / 370 / 79 | 78,845 |

Cost on 02b's measured H100 rates (path 0.0364 s, Segment 0.0392 s per forward, load 585 s + 20 s warm-up; derived,
`tmp/impl05/grid_cost.json`): fixed part (load, two agnostic passes, the twin sweep) far 98.8 / sdr 83.7 / ser
114.1 min. Each 1 % of all cells selected for a Segment split costs far 4.9 / sdr 3.8 / ser 5.9 min. At 3 % (item
swap at 0.05) + 3 % (twin at 0.01): far 128 / sdr 106 / ser 149 min against R28's walltimes 165 / 150 / 195 min.
**Break-even selected share, both Segment passes summed: far 13.5 %, sdr 17.6 %, ser 13.8 %** (smoke: 2.6 % at 0.01).

Commit list sent to the orchestrator 15:52 CDT (receiver_category.py + its test, p3_jobs.py, the p3 test file, the
three batch files, phase3/ct.json). Waiting for the push before sync-code, the Bridges-2 login dry-run,
`submit --test-only`, the ledger reservations and the three submissions (`tmp/impl05/b2_dry.sh`,
`tmp/impl05/submit_p3.sh`, ledger tool `tmp/impl05/ledger_tool.py`, ticket id 05-phase3-path-patching-on-candidates).

## Progress 2 (2026-10-26 16:05 CDT): CPU builders while the jobs wait

Written and tested (no data yet; a fabricated task with the 02b smoke cell's file shapes runs end to end):
- `outputs/_launch_mechanism_analysis/p3_logic.py`: the pre-registered readings as pure functions (weighted call
  over the deciding set's heads, the routing gate of R11(h)/R14, B-selector's two clauses with the literal reading
  deciding clause 1 and the loose reading reported, per-receiver totals, entry points by position class, the
  completeness sums). Conventions recorded in the code and the results: a negative S2p weight counts 0; a
  `kv_unresolved` majority has no pre-registered sub-reading and goes to the researcher.
- `p3_merge.py`: the roles merge tables restricted to the phase-3 cell's rows (`_merge/<t>_p2d` attention + DLA
  from the phase-2 D cell; `_merge/<t>_ko` the phase-1 s1 + s2p sweeps), because `merge_columns` appends absent rows.
- `p3_roles.py`: roles on cell d merging p2d, ko and the item-swap cell d_is; first without
  `--roles-allow-missing-views`, then with it only if the CLI refuses.
- `p3_results.py`: results md/json and the curated copies under `docs/research/mechanism-analysis/phase3/`.
- Tests: `tests/test_mechanism_analysis_p3.py` 20 passed in mgnp; with test_receiver_category 44 passed in base.
  (The p3_logic/p3_results tests were written alongside the modules, not strictly before them.)
- Full suites started in the background (both envs, `tmp/impl05/suite_{base,mgnp}.txt`).

## Progress 3 (2026-10-26 ~16:10 CDT): pushed; BLOCKED on closed Bridges-2 SSH masters

- Orchestrator committed the eight files as a8a9b63 and pushed; both design choices accepted (selection sample for
  path patching, with the reading stating that the A′ adjudication runs on the sample the S_k were chosen on and
  that R-AB's held-out verdict is the generalisation claim; twin line first). Routing reuse from 1C accepted.
- `b2.sh sync-code` refused: no SSH master for `bridges2` on dt-login02. `ssh -O check` for bridges2 and b2dtn gives
  "Connection refused" on dt-login01-04 (stale sockets of Oct 24-25). Handed back to the orchestrator to reopen;
  nothing reserved or submitted.

## Progress 4 (2026-10-26 ~16:15 CDT): jobs submitted on Bridges-2
- Orchestrator reopened the masters on dt-login02. `b2.sh sync-code --branch mechanism-analysis`: remote_head = local_head = a8a9b63.
- Bridges-2 login dry-run: 2/2 invocations ok per task, same grid as the login node (far 5,020 / sdr 4,067 / ser 5,984 cells; 66,235 / 53,768 / 78,845 forwards per counterfactual; completeness sweep 13,767 forwards on neutral_twin only). Dry-run stubs under `outputs/_analyses/mechanism-analysis-p3` on /ocean removed (the p3 root is ticket 05's own and did not exist before).
- `--test-only` accepted all three (estimated start 17:20-17:30 on w002, GPU-shared, h100-80:1).
- Reserved under the ledger lock and submitted:

| task | job | walltime | ledger reservation |
|---|---|---|---|
| far | 49896838 | 02:45:00 | 05-p3-far-2026-10-26T16:14:55 |
| sdr | 49896843 | 02:30:00 | 05-p3-sdr-2026-10-26T16:14:58 |
| ser | 49896848 | 03:15:00 | 05-p3-ser-2026-10-26T16:15:01 |

  Bridges-2 ledger after submission: 8.5 GPU-h in flight, 13.25 reconciled, 21.75 committed. Remaining ticket allowance: 0.75 GPU-h (one rerun).
- Full suite, login base env: 8 failed / 2173 passed / 66 skipped; the 8 failure names equal `00-baseline-failures.md`. mgnp suite pending.
- Next: on completion fetch, check `sweep_neutral_twin.json` exists in each `d` cell, reconcile the ledger, `check_cell.py`, then p3_merge / p3_roles / p3_results and the reading.

## Progress 5 (2026-10-26 evening): fetched, reconciled, built, read
- Jobs exit 0: far 49896838 02:19:20, sdr 49896843 01:51:03, ser 49896848 02:37:42. Twin invocations 5,506 / 4,294 / 6,209 s (model load 767 / 908 / 704 s), item swap 2,495 / 2,020 / 2,901 s.
- `b2.sh fetch outputs/_analyses/mechanism-analysis-p3`: cells d and d_is for all three tasks plus timings. `sweep_neutral_twin.json` present on every task.
- Ledger reconciled under the lock: 2.5 / 2.0 / 2.75 = 7.25 GPU-h of 9.25; bridges2 now 0 in flight, 20.5 reconciled. No rerun used.
- `check_cell.py`: path patching present on all six cells. Its completeness-sweep view looks only for `sweep_bars.json`, so it misses the twin's `sweep_bars_neutral_twin.json` (review-view gap, recorded in the reading; not fixed here).
- The completeness sweep appends flagged outside Components to the head table (far 2, sdr 4, ser 4 rows; mlp.30/31, L31H0, L27H7 or L22H28). Kept under `outside_C_t` everywhere.
- p3_merge, p3_roles (no `--roles-allow-missing-views` fallback needed), p3_results built.
- Added test-first: `p3_logic.robustness` (exploratory re-readings of the call) and `p3_results.cross_task_roles` (C3 table, curated `roles_cross_task.csv`). 46 passed in mgnp and base.
- Full suites (run before these additions, on the a8a9b63 code): base 8 failed / 2173 passed / 66 skipped; mgnp 8 failed / 2370 passed / 19 skipped; both failure lists equal `00-baseline-failures.md`.
- Reading written: `reports/05-phase3-reading.md`. far and ser A′-clause-reader; sdr descriptive Q; B-selector refuted on clause 2; completeness ~0.8 outside C_t at the Readout (different positions from 1C's (c)); sdr R14 surfaced with a do-not-run recommendation.
- Reviews spawned (spec + standards, opus).

## Progress 6 (2026-10-26): reviews, fixes, final state
- Reviews: `reports/05-review.md` (spec: 3 should-fix, 7 nits, no blocker; standards: 9 should-fix, 5 nits, no blocker). All fixed except standards 7 (`receiver_category` sample count vs coverage when the gap excludes instances; 0 excluded in phase 3) and 13 (helper duplication), deferred with reasons.
- Main change from review: K/V arrivals whose top Segment is `unsegmented` are post-clause by construction. B4 now places them (post-clause share of K/V 0.17 / 0.44 / 0.21). The pre-registered category and every call are unchanged.
- Code after review: required twin segments file, convention check, B-selector and adjudication refuse missing categories, sweep unmeasured senders reported, dropped the direct-sum ratio, B task labelled descriptive, C_t-only role counts, narrowed roles retry, subset refusal. 60 tests pass in mgnp and base.
- Results, curated tables and reading rebuilt. Ticket boxes ticked; status resolved pending commit.
- **Commit list (worktree-relative, Deception-Circuit):**
  - outputs/_launch_mechanism_analysis/p3_logic.py
  - outputs/_launch_mechanism_analysis/p3_merge.py
  - outputs/_launch_mechanism_analysis/p3_results.py
  - outputs/_launch_mechanism_analysis/p3_roles.py
  - tests/test_mechanism_analysis_p3.py
  - docs/research/mechanism-analysis/phase3/a_prime.csv
  - docs/research/mechanism-analysis/phase3/b_selector.csv
  - docs/research/mechanism-analysis/phase3/categories.csv
  - docs/research/mechanism-analysis/phase3/completeness.csv
  - docs/research/mechanism-analysis/phase3/entry_paths.csv
  - docs/research/mechanism-analysis/phase3/far_head_table.csv
  - docs/research/mechanism-analysis/phase3/sdr_head_table.csv
  - docs/research/mechanism-analysis/phase3/ser_head_table.csv
  - docs/research/mechanism-analysis/phase3/p3_readings.json
  - docs/research/mechanism-analysis/phase3/roles/far.json
  - docs/research/mechanism-analysis/phase3/roles/sdr.json
  - docs/research/mechanism-analysis/phase3/roles/ser.json
  - docs/research/mechanism-analysis/phase3/roles_by_part.csv
  - docs/research/mechanism-analysis/phase3/roles_cross_task.csv
  - Not mine; leave out: outputs/_launch_mechanism_analysis/eval_jobs.txt, outputs/_suites/.
  - Scratch files (outside the repo): issues/05, reports/05-handback.md, 05-phase3-reading.md, 05-phase3-results.{md,json}, 05-review.md.

- Final full suites on the post-review code: base 8 failed / 2189 passed / 66 skipped; mgnp 8 failed / 2396 passed / 19 skipped; both failure lists equal the 8 baseline names. Status set to resolved.
