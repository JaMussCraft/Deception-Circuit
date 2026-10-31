# 02a hand-back (impl-02a)

Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis` (branch
`mechanism-analysis`, base c24b5d9). No git run by this agent. Status: CPU work, login dry-runs and the job plan done;
**waiting at the Bridges-2 gate** (ticket 01 landed + branch pushed) for the smoke + drift job. Nothing submitted, no
ledger entry written.

## Progress log

- Ticket claimed; read brief, ticket (with the orchestrator's R19 addition), spec, HB, review, CONTEXT, ADRs, code.
- `reports/00-baseline-failures.md` did not exist, so the branch-base baseline was recorded before any edit:
  `reports/00-baseline-failures-02a.md` (the same 8 names in both envs).
- Clause-form table written and hand-checked; sent to the orchestrator for an early commit.
- Sampling, segmentation, loaders, I binding, knockout, DLA, batch runner, drift comparator: built test-first.
- 48 login dry-runs of phase 1B and 1C: all exit 0 (`reports/02a-dryrun-tables.md`).
- Drift argv reconstructed and dry-run on Delta: its sample.json equals the cell of record's, field for field.
- Smoke + drift job file login-checked on Delta: 8 of 8 lines ok.

(Final sections are appended below when the suites and the review are done.)

## impl-02ar (resumed 2026-10-25 14:10)

- Read the brief, ticket and R19 comments, spec §2 / §9, review B1-B3 and Pile 2, the three 02a reports.
- Diffed every 02a file against the main checkout (the branch base for these files).
- Independent checks with the UNMODIFIED main-checkout code (`tmp/impl02ar/verify_*.py`): the v1 segmentation
  snapshot reproduces on far/sdr/ser (1000 rows each, digests equal); the sample golden file reproduces on all 8
  task/seed keys.
- `tests/test_knockout.py`, `tests/test_knockout_model.py`, `tests/test_knockout_families_model.py` are 02a's edits,
  not ticket 01's: they test `component_analysis.knockout` and only flip "mean and zero refused as future work" to
  "mean and zero built". They go on 02a's commit list.
- Fixes: (1) v1 `knockout.json` / `sweep.json` / `knockout_families.json` gained four keys under the default plan;
  now written only for a v2 cell or a non-default plan (`record_plan`), with a hand-written v1-keys test.
  (2) R19(1): the Neutral-Clause Twin's own margin is now recorded per instance under EVERY plan on a cell whose
  batches carry a twin (one extra forward per batch on non-twin plans), `neutral_twin_logit_difference` in every
  sidecar. (3) The family pass writes its per-instance sidecar. (4) Unused imports in new tests.
- Not done here, by design: `response_line` -> `frame` in `roles.SEGMENT_GROUPS` is part of 02b's criteria
  amendment (R7, R10: user veto until applied). The Segment exists; the group mapping is handed to 02b.
- Two of impl-02a's DLA CLI tests were red on mgnp. They expected the fixture's 40 rows, but DLA reads the whole
  1,000-row split, as on v1. The tests are fixed; the code was right.
- `batch --timings` now creates its parent directory. Before, a timings path under a new suite directory would have
  crashed the GPU job after its first line. This was test-first: red, then green.
- Re-ran the job file's Delta login dry-run with impl-02a's redirect script, copied to `tmp/impl02ar/`: 8 of 8 lines
  ok, and the timings file was written into a new directory.

## Smoke + drift job plan (Bridges-2, ticket 02a; nothing submitted)

Gate: ticket 01 committed, 02a committed, branch `mechanism-analysis` pushed (R3). Ledger: no 02a entry yet. The
`bridges2` section is empty, and 02a's allocation is 1.0 GPU-h.

Steps, each run first with `--dry`, from the worktree root on the Delta login node that holds the SSH masters:

```
scripts/remote/b2.sh sync-code --branch mechanism-analysis
DC_DELTA_REPO_ROOT=/projects/beto/swong2/Alignment/Deception-Circuit DC_B2_MANIFEST=/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports/02a-drift-manifest.txt scripts/remote/b2.sh sync-data --what runs
ssh bridges2 '/ocean/projects/cis260361p/swong2/envs/mgnp/bin/python -c "import nnsight; print(nnsight.__version__)"'    # expect 0.7.0
ssh bridges2 'cd /ocean/projects/cis260361p/swong2/Deception-Circuit && HF_HOME=/ocean/projects/cis260361p/swong2/hf HF_HUB_OFFLINE=1 OMP_NUM_THREADS=1 /ocean/projects/cis260361p/swong2/envs/mgnp/bin/python analyze_components.py batch docs/research/mechanism-analysis/jobs/02a-smoke-drift.batch --dry-run'
scripts/remote/b2.sh submit --test-only --time 01:00:00 --script scripts/analyze_components.sbatch --job-name ma-02a-smoke -- batch docs/research/mechanism-analysis/jobs/02a-smoke-drift.batch --timings outputs/_analyses/mechanism-analysis-02a-smoke-timings/timings.json
# ledger reservation (lock), then the same submit without --test-only
scripts/remote/b2.sh status <jobid>
scripts/remote/b2.sh fetch
/u/swong2/.conda/envs/mgnp/bin/python -m component_analysis.sweep_drift /projects/beto/swong2/Alignment/Deception-Circuit/outputs/_analyses/sdr-dh-core-kosweep/dh_core__leaf/sdr/knockout/sweep.json /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/outputs/_analyses/mechanism-analysis-02a-drift-kosweep/dh_core__leaf/sdr/knockout/sweep.json --out /projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports/02a-drift.json
```

The drift manifest lists the five untracked v1 runs from the main checkout, the H run among them (R16, Pile 2
item 6). The v1 `sdr` data and the v1 fine run are tracked, so `sync-code` brings them. The v2 runs are already in
`scripts/remote/b2_manifest.txt`.

Cost, derived from the dry-run forward counts and the extrapolated H100 rate of 0.0497 s per forward:

| line | forwards | estimate |
| --- | --- | --- |
| 1 drift sweep, v1, n = 100 | 13,754 | 11.4 min |
| 2 S2p shape, n = 8 | 1,058 | 0.9 min |
| 3-6 mean (incl. bank), zero, Readout, clause; n = 8 | 754 | 0.6 min |
| 7 groups + greedy k = 3, n = 100 | 2,080 | 1.7 min |
| 8 DLA, pressure + twin pair, 1,000 rows | 375 | 0.3 min (more per forward: every Component captured) |
| model load (cold) + 8 x segmentation | - | 10.5 + about 1.5 min |
| total expected | about 18,000 | about 27-30 min |

Walltime `--time 01:00:00`, one h100-80 on GPU-shared: reservation 1.0 GPU-h = 2 SU, the ticket's allocation.
Estimate x 1.5 is about 0.75 h. The extra quarter covers the forward rate, which is extrapolated from H200 and not
yet measured; this job measures it. Fits: reconciled 0 + in flight 0 + 1.0 <= 02a's 1.0 and the 35 h cap.

Source sha256 (at hand-back; recompute at submit): job file `a5b4d7f3...2927`, groups file `d453e240...85c3`,
`scripts/analyze_components.sbatch` `2e504b7a...364c`, `component_analysis/batch.py` `6502da67...9073`.

Cost basis to record after the job: `timings.json` gives seconds per line. `sweep.json` `cost` gives seconds per
forward for lines 1 and 2. `groups.json` gives `seconds_per_group`. `greedy.json` gives `seconds_per_forward` and
`group_knockouts`.

## Status

**resolved-pending-gpu.** The CPU scope is done, tested in both envs and reviewed (`reports/02a-review.md`, no open
hard finding). The open boxes are the Bridges-2 smoke, the drift control, the cost basis and the ledger, which wait
for the gate above. A further box stays open on purpose: the `frame` mapping of `response_line`, which is 02b's.

## Files to commit (02a)

Excluded: the clause-form files already committed at fc9e614 (`component_analysis/clause_forms.py`,
`docs/research/mechanism-analysis/clause-forms.csv`, `tests/test_component_analysis_v2_clause_forms.py`) and every
`__pycache__`.

```
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/analyze_components.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/component_analysis/batch.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/component_analysis/dataloaders.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/component_analysis/dla.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/component_analysis/head_table.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/component_analysis/instances.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/component_analysis/knockout.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/component_analysis/registry.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/component_analysis/sampling.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/component_analysis/segmentation.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/component_analysis/sweep_drift.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/docs/research/mechanism-analysis/jobs/02a-smoke-drift.batch
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/docs/research/mechanism-analysis/jobs/02a-smoke-groups.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/fixtures/component_analysis_v2/sample_snapshot.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/fixtures/component_analysis_v2/v1_segmentation_snapshot.json
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_component_analysis_v2_batch.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_component_analysis_v2_cli.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_component_analysis_v2_cli_model.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_component_analysis_v2_dataloaders.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_component_analysis_v2_dla.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_component_analysis_v2_knockout.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_component_analysis_v2_knockout_model.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_component_analysis_v2_sampling.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_component_analysis_v2_segmentation.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_component_analysis_v2_sweep_drift.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_knockout.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_knockout_model.py
/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_knockout_families_model.py
```

The last three test files are 02a's, not ticket 01's. They test `component_analysis.knockout`, and their only change
flips "mean and zero refused as future work" to "built". Committing 02a without them turns them red.

## Tests (full suites, worktree root, 2026-10-25, after every edit)

| env | result | failures vs `00-baseline-failures.md` |
| --- | --- | --- |
| mgnp (py3.12, nnsight 0.7.0) | 8 failed, 2152 passed, 19 skipped (1354 s) | exactly the 8 baseline names |
| base (py3.9, BLAS threads 1) | 11 failed, 1966 passed, 60 skipped (502 s) | the 8 baseline names plus 3 in ticket 01's `tests/test_mechanism_analysis_infra.py`, listed below |

The three ticket-01 tests are `test_b2_sync_code_defaults_to_the_mechanism_datasets_branch`,
`test_b2_sync_code_takes_the_branch_from_dc_b2_branch` and `test_b2_branch_flag_overrides_the_environment`. Each
expects `fetch origin mechanism-datasets` in the sync-code command. They passed in the later mgnp run, which points
to ticket 01 editing `b2.sh` while the base run was going. Confirmed: re-run on base afterwards,
`tests/test_mechanism_analysis_infra.py` gives 22 passed. None of these files is 02a's.

The drift comparator was self-checked on the real reference `sweep.json`, compared with itself. It passed with
0 deltas and Spearman 1.0, and its `flagged` entries are label strings, as the comparator assumes.

The base run was collected before the `batch.py` fix and the new knockout tests. Those files were re-run on base
afterwards (`..._v2_batch.py`, `..._v2_knockout.py`, `tests/test_knockout.py`): 61 passed. The nnsight tests skip on
base and run on mgnp. No `core.*` dump was left.

Logs: `/u/swong2/.claude/jobs/1c836bb8/tmp/impl02ar/full_{base,mgnp}.txt`.

## Jobs, ledger

No job submitted. No ledger entry written. 02a's 1.0 GPU-h is untouched.

## Open questions for the orchestrator / researcher

1. **Which order feeds the selectors (ticket 03).** Greedy draws its pool by SIGNED `mean_drop` (layer-0 MLP out),
   because a mediator removes the deceptive margin. `sweep.json`'s `rank` is by |drop| (v1). Its `signed_rank` is
   the signed order. Recommendation: ticket 03 builds the single selector's `S_k` from `signed_rank` too, so both
   selectors rank alike, and states it.
2. **`response_line` -> `frame`.** This is for 02b, with the amendment: one line in `roles.SEGMENT_GROUPS`.
3. **I condition.** It is fixture-tested only. The first real I dry-run follows ticket 08's build.

## Gate (2026-10-25)

- The orchestrator committed the 28 files as 2ab5a29 and accepted the `tests/test_knockout*.py` attribution.
- Holding at the Bridges-2 gate until the orchestrator says "go" (ticket 01 committed and the branch pushed).
- On "go": run the plan above, dry first. Then take the ledger reservation under the lock, submit, fetch, write `reports/02a-drift.json`, reconcile the ledger and hand back the drift verdict.

## Smoke + drift run (2026-10-25)

- The clone was on `mechanism-datasets` at e1ad804. It had no running jobs and a clean tree, so I re-ran sync-code, which moved it to `mechanism-analysis` at 7f8dc01.
- sync-data (drift manifest): the 5 untracked v1 sdr_coarse runs were copied, the H run among them.
- Login checks: nnsight 0.7.0, torch 2.11.0+cu128, transformers 5.13.0. The batch `--dry-run` passed 8 of 8 on the Bridges-2 login node (log `tmp/impl02ar/b2_dryrun.log`).
- `submit --test-only`: accepted, with an expected start at 16:10 on w003.
- Ledger: `b2-02a-smoke-drift-1` reserved at 1.0 GPU-h under the lock.
- Submitted Bridges-2 job **49824729** (GPU-shared, h100-80:1, `-t 01:00:00`).

## Results (job 49824729: COMPLETED, 00:23:51 = 1,431 s, exit 0:0)

All 8 batch lines were ok. Fetched to the worktree: the 9 `outputs/_analyses/mechanism-analysis-02a-*` directories
(71 files) and the job log, copied to `tmp/impl02ar/analyze_components_49824729.out`.

### Drift control: PASSED (`reports/02a-drift.json`)

| check (pre-registered) | tolerance | measured |
| --- | --- | --- |
| Components compared | 1,056, none missing | 1,056, none missing |
| max abs delta mean_drop | <= 0.05 logits | 0.0 |
| 99th percentile abs delta | <= 0.02 | 0.0 |
| Spearman of mean_drop | >= 0.99 | 1.0 |
| flagged set at 0.4 | same, except within 0.02 of the cut | identical (8 Components) |

The H100 rerun is bit-identical to the Delta H200 cell of record, and it is a distinct measurement. Its file hash
differs, and its wall time is 535 s against the reference's 506 s. The clean run, the 100 sampled ids and every
mean_drop are equal. This fits H100 and H200 sharing one architecture, sm_90, with the same bf16 kernels.

### Phase-1 cost basis (measured, H100, Bridges-2 GPU-shared)

| item | measured | source |
| --- | --- | --- |
| model load, cold | 476 s (7.9 min) | `timings.json` line 1 `model_load_seconds` |
| 1,056-Component sweep, n = 100 (13,754 forwards) | 535 s (8.9 min), 0.0389 s per forward | drift `sweep.json` `cost` |
| same sweep shape, n = 8 (S2p plan, 1,058 forwards) | 39.5 s, 0.0374 s per forward | smoke-s2p `sweep.json` `cost` |
| named group knockout, n = 100 | 0.78 s per group (incl. the clean and twin passes) | `groups.json` `seconds_per_group` |
| greedy group knockout, n = 100 | 72.0 s for 147 = 0.49 s each, 0.0362 s per forward | `greedy.json` `cost` |
| mean bank, 1,000 rows, both streams, every Component | 18.0 s | smoke-mean `mean_bank.wall_seconds` |
| DLA, 1,000 rows, pressure + twin pair, 123 Components | 49.5 s line total | `timings.json` line 8 |

Derived:
- Per sweep, 535 s is 0.69x the spec's ~13 min and 0.78x the extrapolated 0.0497 s per forward. A greedy group
  knockout costs 0.49 s, against the spec's ~0.75 s.
- A phase-1B task-job (7 sweeps + bank + L + load) projects to about 7 x 535 + 18 + 50 + 476 s = 74 min,
  against the spec's 110 min. At x1.5 that is about 1.85 h, so 2.0 h rounded per task-job, against the 3.0
  reserved.
- 1C greedy (810 group knockouts per task) is about 6.6 min per task.

### Smoke outputs (shape checks only, not readings)

- S2p plan recorded (`after=pressure_clause,exclude=readout`, deceptive, `mlp.0.0` excluded). The twin's margin
  equals the counterfactual run in the sidecar.
- Mean bank over 1,000 rows. The twin's margin is recorded on all 8 rows under the mean plan.
- Groups and greedy: k = 3 steps written with per-step joint drops. DLA: the twin pair is over 1,000 rows, the
  crossing summary covers 3 conditions, and the neutral-twin figures are written.

### Ledger (`b2-02a-smoke-drift-1`, under the lock)

Reserved 1.0 GPU-h, then reconciled from sacct: 1,431 s = 0.3975 GPU-h actual, lowered to 0.5 GPU-h (1.0 SU).
0.5 GPU-h of 02a's allocation is returned. After my write the `bridges2` totals read: in flight 7.0, reconciled
0.75 (another ticket's 0.25 included), committed 7.75 GPU-h = 15.5 SU.

Status: **resolved**. The only open box is the `frame` mapping of `response_line`, which is 02b's.
