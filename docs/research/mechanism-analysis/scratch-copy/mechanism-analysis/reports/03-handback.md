# Ticket 03 hand-back (impl-03): progress log

Worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis`, branch
`mechanism-analysis` (HEAD 7f8dc01). No git. Scratch: `/u/swong2/.claude/jobs/1c836bb8/tmp/impl03/`.

## Block 1A

### Pre-submission checks (2026-10-25, dt-login04)

- SSH masters `bridges2` and `b2dtn` running. Bridges-2 clone at 7f8dc01.
- `ma_check_cells.py`: 3 jobs, 8 groups, 33 cells, 0 problems.
- `ma_gen_cells.py --profile bridges2 --stage 1a --via scripts/remote/b2.sh --dry`: estimate 4.54 GPU-h, reservation
  7.00 GPU-h (p1a_far 02:30:00, p1a_sdr 02:30:00, p1a_ser 02:00:00).
- Data on Bridges-2: the six run dirs' `active_nodes*.json`, the all-MLP operand `allmlp_nomb_v2`, and the
  `<t>_v2` test arrows are md5-identical to Delta. The wikitext cache is present under `/ocean/.../hf/datasets`.
  No `sync-data` was needed.
- `--first 1 --test-only` (p1a_far): accepted, test job 49824656, projected start 17:01 on w010.
- The real chain wrapper with `--dry-run` per group for p1a_far on the login node: all three groups exit 0;
  nothing written.

### Deviation (logged)

The ticket says the first job of each block is the calibration, compared with the estimate before the rest of the
block goes in. The orchestrator's 1A instruction says to submit all three jobs. I followed the orchestrator: 1A's
cell rate is measured (ticket 06), not extrapolated, and the walltimes carry the x1.5 buffer. The calibration is
recorded post hoc from the far job's per-group `=== evaluate_chain` timestamps against the 97.8-min estimate.

### Submitted (2026-10-25 15:08 CDT)

| job | Bridges-2 id | --time | reserved GPU-h | output |
| --- | --- | --- | --- | --- |
| p1a_far | 49824695 | 02:30:00 | 2.5 | `outputs/_suites/mechanism-analysis/phase1a/p1a_far__{mean,zero,interchange}` |
| p1a_sdr | 49824696 | 02:30:00 | 2.5 | `outputs/_suites/mechanism-analysis/phase1a/p1a_sdr__{mean,zero,interchange}` |
| p1a_ser | 49824697 | 02:00:00 | 2.0 | `outputs/_suites/mechanism-analysis/phase1a/p1a_ser__{mean,zero}` |

Ledger `bridges2`: three reservations under ticket `03-phase1-ablation-replication-and-sweeps`, written by
`ma_gen_cells.py --submit` under the lock, 7.0 GPU-h of the ticket's 19.5. Section in flight after submit: 7.5 GPU-h
(with impl-08's 0.5). All three PENDING in sacct at 15:09.

All three started at 15:09:55 CDT (Bridges-2 log stamps are Eastern, 16:09:55). Cold model load took about 6 min,
under the 10.5-min estimate.

### Results builder (written while the jobs run)

- `outputs/_launch_mechanism_analysis/p1a_results.py` (new): reads the fetched 1A cells from `suite_ma.json`,
  ticket 06's interchange cells of record from mechanism-datasets `reports/06-stage{1,2}-results.json` (same label,
  dataset `<t>_v2`), the flip audits per group, and the chain logs. It writes `reports/03-1a-results.{md,json}` and
  the curated `docs/research/mechanism-analysis/phase1a/{p1a_cells.csv,p1a_sets.csv,p1a_readings.json}`.
- Separation count reuses ticket 06's `drift.py` rule (percentile <= 5 and z <= -2, of 4 metrics).
- R-A1 per set 3-6: mean D-test KO accuracy with zero no-pressure KO deceptive rate. The same bands applied with
  the mean no-pressure column (task bank, matched bank) are reported as robustness only.
- `tests/test_mechanism_analysis_p1a_results.py` (new, TDD): 17 tests over the reading's bands and edges, cell
  extraction under both banks, the per-set rows (calibration sets, ser set 6 = set 5), and the chain-log
  timing parser. Green in mgnp and base.
- Smoke run with no cells fetched: the ticket-06 lookup finds all 18 interchange cells of record (sets 1-5, 7 per
  task), matching the published 06 tables.

### Clone moved during 1A (logged)

While 1A ran, the Bridges-2 clone moved from 7f8dc01 to 45e3340 (ticket 08's sync). The 1A zero and interchange
groups start new processes after that. The diff touches only `dataset/build_inversion_v2.py`, the inversion pools,
data and `tests/test_inversion_v2.py`. `evaluate_circuit.py` and `evaluation/` are unchanged, so the 1A cells are not
affected.

## Block 1B (released 2026-10-25 by the orchestrator: 02a drift control PASSED)

- `outputs/_launch_mechanism_analysis/p1b_jobs.py` (new) writes `docs/research/mechanism-analysis/jobs/
  03-p1b-{far,sdr,ser}.batch`: S1, S2, S2p, S3, S4, S5, S6, L (D: pressure + neutral twin; F: pressure), U bound
  at leaf with the six atomic runs as references (02a's smoke binding), selection sample (n = 100, seed 0, CLI
  defaults). One output dir per cell: `outputs/_analyses/mechanism-analysis-p1/<cell>/U__leaf/<test set>/`.
  Timings: `outputs/_analyses/mechanism-analysis-p1/timings/<t>.json`.
- Tests for the generator added to `tests/test_mechanism_analysis_p1a_results.py` (21 green, mgnp).
- Walltime per the orchestrator: 02:00:00 per task job (02a's measured basis, about 74 min a job).
- Login dry-run on Delta (redirected to tmp): 27 of 27 lines ok; sample 100 of 100 at seed 0 on every line; twin
  paired 100 of 100 on every D line; S5 notes "this test set is the twin itself", S6 "no clause".
- The orchestrator committed the job files as 701e0b3 and pushed. `sync-code` moved the clone to 701e0b3, and the
  batch files and wrapper are md5-identical to Delta. H, F and the F stand-ins were already identical, so no
  `sync-data` was needed. `submit --test-only` was accepted (49825304). No B2-side dry-run was run, so the real
  output dirs are not pre-written.

### Submitted (2026-10-25 15:49 CDT)

| job | Bridges-2 id | --time | reserved GPU-h |
| --- | --- | --- | --- |
| 1B far | 49825315 | 02:00:00 | 2.0 |
| 1B sdr | 49825317 | 02:00:00 | 2.0 |
| 1B ser | 49825318 | 02:00:00 | 2.0 |

Ledger: reserved under the lock with `tmp/impl03/ledger_tool.py`, which reuses `ma_gen_cells.edit_ledger` and the
budget check. Ticket 03 now holds 13.0 of 19.5 GPU-h (1A 7.0 + 1B 6.0) before reconciliation.

### 1B reading tools (written while the jobs run)

- `outputs/_launch_mechanism_analysis/p1_readings.py` (new, TDD): R-cls (spec 2.2 as amended by R16, checked in
  order, with the sub-reason for "none"), the significance rule, the C-own sign test with Holm, and the bootstrap
  clustered by `pressure_id` (R12). Tests: `tests/test_mechanism_analysis_p1_readings.py`, 18 green on mgnp.
- `outputs/_launch_mechanism_analysis/p1b_results.py` (new): reads the seven sweeps and the lens cells per task.
  It writes `reports/03-1b-results.{md,json}` and the curated `docs/research/mechanism-analysis/phase1/`
  (`rcls.csv`, `c1_matrix.csv` + `.png`, `top20.csv`, `c_own.csv`, `p1b_readings.json`). Shape-tested end to end
  on a fake root built from 02a's smoke cells (`tmp/impl03/p1b_fake/`). Set sizes are right: core 31,
  exclusives 8/14/10, D-H 26/21/19, (D-H)-core 15/15/19, and 933 outside every circuit.
- Rankings use `signed_rank`, with the layer-0 MLP excluded from S2p, S3 and S2 (02a's open note).
- Path finding: analyze_components files every cell under the task label `<t>_v2`, including H, F and I. The 1B
  cells do not collide (one output dir per cell). The builder's path rule was fixed to `<t>_v2`.

## Block 1C (I datasets committed c2d47da; released by the orchestrator)

- `sync-code` to c2d47da failed harmlessly. The clone holds untracked copies of impl-08's
  `outputs/_build_inversion_v2/directive/*`, which are md5-identical to the commit, and the checkout refused. The
  clone stayed clean at 701e0b3. This was reported to the orchestrator, and the files were left untouched (another
  ticket's).
- 1C needs 1B: both selectors rank from 1B's S2p sweep, and the held-out exclusion uses S1's sample. Two waves:
  1C-a (S7 + greedy, per task, one job, --time 01:30:00), then 1C-b (held-out groups, after 1C-a's greedy sets are
  fetched, --time 00:45:00).
- `outputs/_launch_mechanism_analysis/p1c_jobs.py` (new) writes `docs/research/mechanism-analysis/jobs/03-p1c-a.batch`
  and the config-only I stand-ins `outputs/_launch_mechanism_analysis/standins/<t>_v2_inversion/config.json`
  (ticket 06's nopressure stand-in with `deception_condition: inversion`). Login dry-run: 6 of 6 ok.

### I-sample comparability (selection sample, seed 0, n = 100; I split 210 / 788 / 249)

| task | sample | designation polarity inv/id | item polarity 1/2 | template lab/audit | clause form act/pred/other |
| --- | --- | --- | --- | --- | --- |
| far | D | 48 / 52 | 50 / 50 | 50 / 50 | 100 / 0 / 0 |
| far | I | 81 / 19 | 55 / 45 | 56 / 44 | 100 / 0 / 0 |
| sdr | D | 48 / 52 | 50 / 50 | 50 / 50 | 27 / 54 / 19 |
| sdr | I | 48 / 52 | 50 / 50 | 50 / 50 | 13 / 65 / 22 |
| ser | D | 48 / 52 | 50 / 50 | 50 / 50 | 11 / 58 / 31 |
| ser | I | 48 / 52 | 50 / 50 | 50 / 50 | 0 / 60 / 40 |

- `outputs/_launch_mechanism_analysis/p1c_groups.py` (new, TDD; `tests/test_mechanism_analysis_p1c_groups.py`, 6
  green) builds wave b from the fetched S2p sweep and greedy.json. It writes groups files per task under
  `docs/research/mechanism-analysis/phase1/groups/`, the paired R-inv id lists, a meta file (null seed base
  20261025, per candidate seed = base + 1000 x index) and `jobs/03-p1c-b.batch`.
  - Held-out D: 14 candidates, 20 layer-matched nulls each, routing (b) and (c) per candidate, (a) once, and 3
    named groups: 326 groups.
  - H and F: 12 candidates with k <= 20, plus the 3 named groups.
  - R-inv: D and I on the paired ids, 12 candidates.
  - Preliminary `C_t`: core | excl_t | ((D_t - H_t) - core) | the heads of `S_k` | 10 MLPs (S_k's first, then by
    S2p rank; the layer-0 MLP never).

FAR's I sample is not comparable on Designation Polarity: only 19 identity rows survive I's filter. SDR and SER
match on all three sampler strata. Their clause-form mix differs, and SER's I has no act-naming clause. Derived
from the dry-run `sample.json` files with `tmp/impl03/strata_mix.py`.

### Clone synced to 8bf0109 (2026-10-25 16:10 CDT, orchestrator-approved)

- On the clone, `outputs/_build_inversion_v2/directive` was moved to `directive.b2local-261025`, then `sync-code`
  reached 8bf0109. No evaluator code changed between 701e0b3 and 8bf0109, so the running 1B jobs are unaffected.
- The clone now holds two `b2local-261025` directories (`outputs/_suites/mechanism-v2-coarse.b2local-261025`,
  `outputs/_build_inversion_v2/directive.b2local-261025`) plus the untracked round-1 dirs
  `outputs/_build_inversion_v2/<t>_v2/`.
- FAR R-inv (orchestrator, with 8bf0109): besides the pooled paired bootstrap, report a within-stratum comparison
  (I inversion-polarity rows against D inversion-polarity rows) and mark the FAR result polarity-confounded.
- `p1c_groups.paired_strata` (new, tested; 7 green in mgnp and base) records each task's paired R-inv id count, its
  sampler-strata mix and its inversion-polarity subset in `phase1/groups/meta.json`. The R-inv reading filters the
  per-instance sidecars to that subset for the FAR within-stratum comparison.

## Block 1A results (2026-10-25 17:30 CDT)

- All three jobs COMPLETED with every chain group exiting 0 (far 01:17:30, sdr 01:17:44, ser 01:00:27). 33 of 33
  cells fetched to `outputs/_suites/mechanism-analysis/phase1a/`. The only error-like log line is the benign
  wikitext tokenizer length warning.
- Ledger reconciled under the lock (reserved lowered to actual, rounded up to 0.25 h): far 1.5, sdr 1.5, ser 1.25
  GPU-h, 4.25 of the 7.0 reserved.
- Flip audits for the six mean and zero groups under `outputs/_suites/mechanism-analysis/phase1a/flip_audit/`.
- Results: `reports/03-1a-results.md` + `.json` (reading under the title), curated
  `docs/research/mechanism-analysis/phase1a/{p1a_cells.csv,p1a_sets.csv,p1a_readings.json}`. Ticket 1A boxes ticked.
- Reading: no set is deception-specific or an item carrier on any task. The core reads answer machinery everywhere
  but is a positional collapse on far and ser. far D-H misses deception-specific (0.331 mean / 0.116 zero).

## Block 1B results and 1C-a submission (2026-10-25 ~17:45 CDT)

- 1C-a submitted as Bridges-2 job 49828172 (`--time 01:30:00`, test-only passed). Ledger row
  `03-1c-a-2026-10-25T17:21:45` holds 1.5 GPU-h. The clone was at 8bf0109 with all three S2p sweeps present.
- 1B jobs COMPLETED with 9 of 9 batch lines ok each (far 01:12:34, sdr 00:59:49, ser 01:13:53). 21 sweeps and
  6 lens files fetched to `outputs/_analyses/mechanism-analysis-p1/`. Ledger reconciled: 1.25 + 1.0 + 1.25 = 3.5 GPU-h
  of the 6.0 reserved. Ticket 03 is at 4.25 + 3.5 reconciled + 1.5 in flight = 9.25 of 19.5 GPU-h.
- `p1b_results.py` gained a C1 section (mean d per composition group and test set, from `c1_summary`), rows in
  the figure ordered numerically by layer, and a note that the twin's honest-first rate is 0 by construction.
- Results: `reports/03-1b-results.md` + `.json` (reading under the title); curated
  `docs/research/mechanism-analysis/phase1/{rcls.csv,c1_matrix.csv,c1_matrix.png,top20.csv,c_own.csv,p1b_readings.json}`.
  1B, C1/C-own and R-lens ticket boxes ticked. Tests: 46 green (p1a, p1 readings, p1c groups) in mgnp.

### 1C-b preparation (while 1C-a runs)

- Held-out D samples come from a login dry-run of the 1C-b held-out D lines with placeholder groups
  (`tmp/impl03/p1cb_heldout_dry.py`): 100 ids per task, seed 1, the S1 ids excluded.
- R19(3) pairs R-inv on D's held-out ids that survive I's filter. That gives only 14 (far), 73 (sdr) and 26 (ser)
  ids. The orchestrator was asked to choose. Option A runs as is. Option B draws I's own held-out sample (seed 1,
  selection ids excluded, as spec section 2 line 53, section 2.4 and the ticket say) and runs D on the same ids:
  100 paired ids per task, all in D, none in the selection sample. `p1c_groups.py --rinv-sample-root` switches to
  option B and records the rule in meta.json.
- `outputs/_launch_mechanism_analysis/p1c_results.py` (new, TDD; `tests/test_mechanism_analysis_p1c_results.py`, 10
  green) builds R-AB (tests (i) and (ii), nulls, bootstrap CIs, curves, reading, deciding set and members), named
  groups, routing shares, paired R-inv (pooled and inversion-polarity only, FAR flagged polarity-confounded),
  S7 vs S2p, B's shared share and C-confound. Writes `reports/03-1c-results.{md,json}` and curated
  `phase1/{rab_curves.csv,rinv.csv,routing.csv,s7_vs_s2p.csv,p1c_readings.json}`. An end-to-end fake-root run
  (`tmp/impl03/p1c_fake_root.py`: real groups names, random margins) builds every section.
- Ticket tests: 56 green in mgnp (py3.12) and base (py3.9).

### R23 (orchestrator ruling: option B plus the R19(3) robustness row)

- `p1c_groups.py`: `--rinv-sample-root` (I's held-out sample) is now required. Per task it writes
  `<t>_rinv_ids_optionB.txt` (100), `<t>_rinv_ids_r19.txt` (14 / 73 / 26) and their union `<t>_rinv_ids.txt`
  (106 / 162 / 110), which the paired lines run on with `--n-causal 1000` (the sample is then exactly those ids).
  It also copies the seed-1 samples to `<t>_heldout_{D,I}_sample.json` and records the rule, seed and strata in
  meta.json.
- `p1c_results.py`: three R-inv rows per task (option B, its inversion-polarity subset, the R19(3) subset), a strata
  table and the survivorship and FAR polarity-confound statement. Ticket tests: 58 green in both envs.
- Outside-U question answered: the selectors already rank all 1,056 components. A U-only top-k arm was costed
  (about 0.15 GPU-h, no new lines) for the orchestrator's decision.

### R24 (orchestrator ruling: U-only top-k arm folded into 1C-b, descriptive; walltime 00:55:00)

- `p1c_groups.u_only_sets` (tested) takes the S2p signed top k among U's 123 heads on the single k grid. Each
  candidate `uonly_kK` gets 20 layer-matched nulls on held-out D, and k <= 20 also goes on H and F. There is no
  routing and no R-inv. Null seeds for the pre-registered candidates are unchanged, because U-only candidates are
  indexed after them. Groups per task: held-out D 326 to 494, H/F 15 to 21.
- `p1c_results.reading` ignores the U-only arm (tested). It has its own section beside the unrestricted single
  selector at the same k. Ticket tests: 60 green.

### 1C-a results and 1C-b build (2026-10-25 ~19:30 CDT)

- 1C-a 49828172 COMPLETED with 6 of 6 lines ok (00:58:04). S7 and greedy were fetched for all tasks. Ledger
  reconciled at 1.0 of 1.5 GPU-h, so ticket 03 has used 8.75 reconciled GPU-h with nothing in flight.
- `p1c_groups.py` built the real 1C-b files under `docs/research/mechanism-analysis/phase1/groups/` (25 files, 2.0 MB)
  and `jobs/03-p1c-b.batch` (15 lines). Per task: held-out D 494 groups, H/F 21, R-inv 12; R-inv ids option B 100,
  R19(3) 14 / 73 / 26, union 106 / 162 / 110.
- Login dry-run (`tmp/impl03/p1cb_batch_dry.py`): 15 of 15 ok. Each R-inv sample equals its union id file, and each
  held-out D sample equals the committed copy. Estimate about 6 GPU-min per task plus model load, against
  `--time 00:55:00`.

## Block 1C results (2026-10-25 ~20:20 CDT)

- 1C-b 49830654 COMPLETED with 15 of 15 lines ok (00:30:35). Ledger reconciled at 0.75 of 0.9167 GPU-h. Ticket 03 total:
  9.5 reconciled GPU-h of 19.5, nothing in flight.
- `p1c_results.py` fix: numpy booleans in the JSON dump and the (i)/(ii) flags are now plain Python values.
- Results: `reports/03-1c-results.md` + `.json`; curated `phase1/{rab_curves,rinv,routing,s7_vs_s2p}.csv` and
  `p1c_readings.json`; reading in `reports/03-phase1-reading.md`. Ticket boxes ticked except the single combined
  `03-phase1-results.md` (the tables are split by block into 1a, 1b and 1c) and the review (`03-review.md`), both
  deferred under the orchestrator's essentials-only usage note.

## Close-out (2026-10-25)

- Combined `reports/03-phase1-results.md` + `.json` from `outputs/_launch_mechanism_analysis/p1_results.py` (links the
  1a/1b/1c tables). Self-review in `reports/03-review.md`. Ticket status set to resolved.
