# 08 hand-back: the Instructed-Inversion Condition (I) (impl-08)

**Status (R22 round): DONE, with a limitation for FAR and SER.** The primary `<t>_v2_inversion` (directive pool,
job 49825105) keeps FAR 210, SDR 788 and SER 249 of 1,000 ids. **FAR and SER are below the 300 minimum**, which R22
says to state as a limitation for those tasks. The secondary `<t>_v2_inversion_reported` (round 1) keeps 0 / 618
/ 7. The ledger is reconciled: 0.25 GPU-h for each job, and the 0.0833 borrowed from the holdback is returned. The
commit list is in "R22 commit list" below.

### R22 retention, primary condition `inversion` (source: `data/datasets/<t>_v2_inversion/filter_report.json`)

| task | kept (argmax + margin) | margin-only | median target margin clean / corrupt | meets 300 |
| --- | --- | --- | --- | --- |
| far_v2 | 210 / 1000 | 210 | -0.00 / 0.12 | **no** |
| sdr_v2 | 788 / 1000 | 788 | 3.62 / 3.50 | yes |
| ser_v2 | 249 / 1000 | 249 | 0.50 / 0.62 | **no** |

| task | act | Predicate | other |
| --- | --- | --- | --- |
| far_v2 | 210/1000 | - | - |
| sdr_v2 | 114/216 | 509/603 | 165/181 |
| ser_v2 | 1/72 | 148/695 | 100/233 |

- **FAR is skewed by Designation Polarity.** 191 of its 210 kept rows are Designation Polarity `inversion`; the
  `identity` strata keep 19 of 500. A stratified FAR sample from I is unbalanced on that factor.
- **SER act-naming almost never takes** (1 of 72).
- **Directive vs reported.** The directive frame raises retention in every task: FAR 0 to 210, SDR 618 to 788, SER
  7 to 249.
- **Full tables.** Retention per `pressure_id` and per sampler stratum is in
  `docs/research/mechanism-analysis/inversion-control.md` ("Result: primary condition").

### R22 commit list (absolute paths)

Under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/`:

- `data/datasets/far_v2_inversion/`, `data/datasets/sdr_v2_inversion/`, `data/datasets/ser_v2_inversion/`. Each
  holds dataset_config.json, dataset_dict.json, filter_report.json and test/{data-00000-of-00001.arrow,
  dataset_info.json, state.json}.
- `outputs/_build_inversion_v2/directive/{far_v2,sdr_v2,ser_v2}/{scores.jsonl, meta.json}`.
- `docs/research/mechanism-analysis/inversion-control.md`, rewritten with both conditions, retention and pools.
- `docs/research/mechanism-analysis/inversion-dry-run-directive.txt`, new.
- `docs/research/mechanism-analysis/inversion-dry-run-reported.txt`: the old `inversion-dry-run.txt`, renamed with
  a note line added. **Delete `inversion-dry-run.txt` from the index.**
- `CONTEXT.md`: the entry names the directive form as primary and the reported form as secondary.

Already committed in 45e3340, not changed since: the builder, both pools, the tests, the reported datasets and
`outputs/_build_inversion_v2/reported/`.

Under R22 the first round is kept as the secondary condition `<t>_v2_inversion_reported`. It retained 0 (FAR), 618
(SDR) and 7 (SER) rows; see "Result: retention" below and the curated note.

## R22 round (2026-10-25)

- **Builder.** `--condition {inversion, inversion_reported}`; each condition has its own pool, style, work
  subdirectory (`outputs/_build_inversion_v2/{directive,reported}/`) and dataset suffix. A task that keeps no row
  gets only `dataset_config.json` and `filter_report.json`. Directive rules are checked mechanically: a game or
  intent marker, an instruction verb to the assistant, no reported-wish verb, no motive word.
- **Pools.** The new primary `dataset/deception_pools/v2/inversion_v2.json` (style directive, 112 clauses, ids
  `invd_*`). The old pool is renamed to `inversion_v2_reported.json` with its bytes unchanged, so it still matches
  the sha256 recorded by job 49824662. Its "_reported" marker is therefore the file name, not the clause ids.
- **Dry run.** The directive pool derives 3,000 of 3,000 rows with 0 drops.
- **Tests.** `tests/test_inversion_v2.py`: 71 pass in mgnp. Full suites in both envs are running:
  `reports/08-suite-{base,mgnp}-r22.txt`.
- **Reported outputs rebuilt.** The old `outputs/_build_inversion_v2/<t>/` moved to `.../reported/<t>/`. The
  reported datasets were re-assembled as `data/datasets/<t>_v2_inversion_reported/` (`reports/08-assemble-reported.log`,
  retention unchanged). The uncommitted `data/datasets/<t>_v2_inversion/` of round 1 were moved aside to
  `/u/swong2/.claude/jobs/1c836bb8/tmp/impl08/old_datasets/`.
- **CONTEXT.md.** The entry now names the directive form as primary and the reported form as secondary.
- **Planned job.** `--time 00:20:00` (0.3333 GPU-h; round 1 took 745 s). The ticket has 0.25 left, so 0.0833
  comes from `orchestrator-holdback`, recorded in the ledger's `allocation_changes`. Reconciled savings go back to
  the holdback.
- **Job.** 45e3340 pushed and synced; the Bridges-2 hashes of the builder, pool and wrapper match Delta's.
  `--test-only` was accepted (49825104). The ledger reservation `08-score-inversion-directive-1` was 0.3333 GPU-h,
  with 0.0833 from the holdback. Job **49825105** COMPLETED on w004 in 775 s; log in `reports/08-job-49825105.log`.
  Reconciled to 0.25 GPU-h; the 0.0833 went back to the holdback, so the ticket allocation is 0.5 again and the
  holdback is 0.75.
- **Fetch and assemble.** Fetched only `outputs/_build_inversion_v2/directive`. `b2.sh fetch` was dry-run first
  in round 1; the meta records job 49825105, the H100 and the directive pool sha256. Assembled on Delta
  (`reports/08-assemble-directive.log`, exit 3 for FAR and SER below 300).
- **Bridges-2 leftovers.** The clone still holds the untracked round-1 dirs `outputs/_build_inversion_v2/{far,sdr,ser}_v2/`.
  They duplicate the committed `reported/` copies. They are harmless, and a bare `b2.sh fetch
  outputs/_build_inversion_v2` would bring them back, so fetch the subdirectories by name.
- **Suites (R22 code).** Base env: 8 failed, 2009 passed, 60 skipped, the same 8 baseline names
  (`reports/08-suite-base-r22.txt`). mgnp: 8 failed, 2188 passed, 19 skipped, exactly the 8 baseline names
  (`reports/08-suite-mgnp-r22.txt`). impl-02a's two DLA failures from the earlier run are gone.
  `tests/test_inversion_v2.py`: 71 pass.

## Progress log

- 2026-10-25: read the brief, ticket, spec (§2.4, R6, R9, R12, R15, R19), plan-review Pile-3 #7 and review-2
  Fix 4, CONTEXT (v2), the pinned builders, the far_v2 config and provenance, and the D and H test rows. Ticket
  claimed.
- Baseline before any edit, in both envs: `reports/00-baseline-failures-08.md` has the same 8 names as impl-01's
  `reports/00-baseline-failures.md`.
- Pool, builder and tests written test-first. The pool was checked against 02a's `clause-forms.csv` (fc9e614)
  before use: 49 of 49 D clauses agree, and the builder refuses to run on any disagreement.
- Two-axis review (`reports/08-review.md`). Then the orchestrator's rulings were applied: R20 and the standards
  rulings. Summary:
  - Every pool clause carries a knowledge or intent/game marker, checked mechanically. The pool is now 94 clauses.
  - "Other" D clauses get "other" I clauses. The filter is argmax + margin, and both counts are reported.
  - Retention is reported per full sampler stratum.
  - D's clause and margins are in `i_source_*` columns. All other D columns are kept.
  - Row fields are `instructed_inversion_*` and the slot kind is `transparent`. The condition id stays `inversion`.
  - CONTEXT.md gains the entry "Instructed-Inversion Condition (I)". "Control condition" no longer appears.
  - Helpers are imported from the pinned builder. There is one length limit, raised errors replace asserts, test
    files are closed, and the git check has a 20 s test timeout.
- Final CPU dry run on the real test splits with the Llama tokenizer: **3,000 of 3,000 rows derived, 0 dropped**.
  The log is `docs/research/mechanism-analysis/inversion-dry-run.txt`. Every I row is clause-aligned with D and with
  the Neutral-Clause Twin in both streams.
- Tests: `tests/test_inversion_v2.py`, 52 tests. Full suites in both envs on the final files: baseline names only,
  plus 2 mgnp failures in impl-02a's DLA tests (see "Tests" below).

- 2026-10-25: the orchestrator committed the CPU work as d0a30c8 (7 files; wrapper placed at
  `scripts/build_inversion_v2.sbatch`). No "## Answer" or map.md pointer needed. Idle until the orchestrator says
  ticket 01 is committed and the branch is pushed; then the scoring job per the plan below.
- 2026-10-25 GO received (7f8dc01 pushed). The Bridges-2 clone first showed e1ad804 on mechanism-datasets, so I
  re-ran `b2.sh sync-code --branch mechanism-analysis`; remote_head = local_head = 7f8dc01. On Bridges-2 the
  builder and pool sha256 match the dry-run log. The wrapper's dry path on Delta derived 3,000 of 3,000 rows. The
  `submit --dry` output was as planned, and `--test-only` was accepted (test 49824657). The ledger reservation
  `08-score-inversion-1` (0.5 GPU-h) was written under the lock. Submitted **job 49824662** at
  2026-10-25T15:05:47-05:00 with `--time 00:30:00`.
- Job 49824662 COMPLETED on w008 (H100 80GB HBM3): start 16:08:25, end 16:20:50 EDT, elapsed 745 s (sacct).
  Scoring took 39.6 s (far), 8.5 s (sdr) and 8.5 s (ser); the rest was the model load. Log copied to
  `reports/08-job-49824662.log`. Ledger reconciled under the lock: status completed, actual 0.2069 GPU-h,
  reserved lowered to 0.25 GPU-h (0.5 SU).
- Fetched `outputs/_build_inversion_v2/` with `b2.sh fetch` (meta: job 49824662, pool and builder sha256 as in the
  dry-run log). Assembled on Delta (`reports/08-assemble.log`): exit 3, the below-minimum hand-back.

## Ticket checklist

- [x] Pool `dataset/deception_pools/v2/inversion_v2.json`: 94 transparent clauses over 7 (task, form) cells, with
      several length variants per wording. It is listed in `docs/research/mechanism-analysis/inversion-control.md`
      for a human read.
- [x] Builder: clause surgery in both streams, token- and form-matched, aligned-pair assertion re-run. It records
      `condition: "inversion"`, the clause id (`instructed_inversion_id`), D's `pressure_id` and labels. Drops are
      counted per `pressure_id`; there are none.
- [x] CPU pairing check: every derived row is clause-aligned with `<task>_honest` by `instance_id`, in the builder
      on all 3,000 rows and in tests.
- [x] Scoring job on Bridges-2 (49824662), with retention per task, `pressure_id` and stratum (below). FAR and
      SER are below 300: hand-back.
- [x] `data/datasets/<task>_inversion/` written with `dataset_config.json` (`bridges2_delivery: branch`).
      `far_v2_inversion` has an empty test split that `datasets.load_from_disk` cannot load.
- [x] Tests (CPU, both envs): the fixture builder makes aligned pairs and refuses a mismatched length. The v2
      reproducibility test passes. Base-env failures match the baseline by name; mgnp adds 2 failures in
      impl-02a's DLA tests, unrelated to ticket 08.
- [x] Curated note with pool, coverage, examples and retention. Ledger reconciled. Review in
      `reports/08-review.md`.

## Result: retention (hand-back)

Source: `data/datasets/<task>_inversion/filter_report.json` (counts derived from those files). Under the
transparent clause the model names the honest item in FAR and SER: the median target margin is about -3.6 (FAR)
and -2.75 (SER) in both streams, and 999 of 1,000 FAR rows and 890 of 1,000 SER rows choose the honest item in
both streams. The scoring direction is right: SDR, through the same code, keeps 618, and its Predicate-naming and
other clauses mostly elicit the requested item. Act-naming clauses ("wants the wrong result") almost never do, in
any task (SDR 28 of 216). The argmax + margin rule and the margin-only rule keep the same rows in every task.

Likely reading, for the orchestrator: a reported, descriptive request ("In this quiz the reviewer wants the wrong
result.") does not move Llama off the true answer, while D's directive clauses do. That is open question 2 below
(descriptive vs directive wording), now measured. A directive but transparent pool ("For this quiz, answer with
the wrong result.") would be the obvious next variant, but the screens currently allow imperatives only because
D clauses carry them; that is a design decision, not something I have started.

#### Per task

| task | kept (argmax + margin) | margin-only | median target margin clean / corrupt | choice both streams target / honest | meets 300 |
| --- | --- | --- | --- | --- | --- |
| far_v2 | 0/1000 (0%) | 0 | -3.62 / -3.75 | 0 / 999 | **no** |
| sdr_v2 | 618/1000 (62%) | 618 | 2.12 / 2.12 | 740 / 79 | yes |
| ser_v2 | 7/1000 (1%) | 7 | -2.75 / -2.75 | 25 / 890 | **no** |

#### Per form

| task | act | Predicate | other |
| --- | --- | --- | --- |
| far_v2 | 0/1000 (0%) | - | - |
| sdr_v2 | 28/216 (13%) | 425/603 (70%) | 165/181 (91%) |
| ser_v2 | 0/72 (0%) | 2/695 (0%) | 5/233 (2%) |

#### Per sampler stratum (Designation Polarity / Item Polarity / Template Variant)

| stratum | far_v2 | sdr_v2 | ser_v2 |
| --- | --- | --- | --- |
| identity/1/audit | 0/125 (0%) | 75/125 (60%) | 0/125 (0%) |
| identity/1/lab | 0/125 (0%) | 89/125 (71%) | 0/125 (0%) |
| identity/2/audit | 0/125 (0%) | 73/125 (58%) | 1/125 (1%) |
| identity/2/lab | 0/125 (0%) | 86/125 (69%) | 0/125 (0%) |
| inversion/1/audit | 0/125 (0%) | 80/125 (64%) | 2/125 (2%) |
| inversion/1/lab | 0/125 (0%) | 76/125 (61%) | 0/125 (0%) |
| inversion/2/audit | 0/125 (0%) | 78/125 (62%) | 2/125 (2%) |
| inversion/2/lab | 0/125 (0%) | 61/125 (49%) | 2/125 (2%) |

#### Per pressure_id (D clause, form, kept/n)


far_v2:

| pressure_id | form | kept |
| --- | --- | --- |
| 00 | act | 0/116 (0%) |
| 01 | act | 0/96 (0%) |
| 03 | act | 0/150 (0%) |
| 05 | act | 0/110 (0%) |
| 06 | act | 0/44 (0%) |
| 07 | act | 0/7 (0%) |
| 08 | act | 0/150 (0%) |
| 09 | act | 0/9 (0%) |
| 10 | act | 0/88 (0%) |
| 11 | act | 0/91 (0%) |
| 12 | act | 0/72 (0%) |
| 15 | act | 0/67 (0%) |

sdr_v2:

| pressure_id | form | kept |
| --- | --- | --- |
| 00 | predicate | 56/70 (80%) |
| 01 | act | 4/49 (8%) |
| 02 | act | 9/46 (20%) |
| 03 | act | 1/33 (3%) |
| 04 | other | 53/56 (95%) |
| 05 | other | 23/25 (92%) |
| 06 | act | 5/28 (18%) |
| 07 | act | 2/33 (6%) |
| 08 | act | 6/19 (32%) |
| 09 | act | 1/8 (12%) |
| 10 | predicate | 42/44 (95%) |
| 11 | predicate | 17/43 (40%) |
| 12 | predicate | 72/100 (72%) |
| 13 | other | 89/100 (89%) |
| 14 | predicate | 38/45 (84%) |
| 15 | predicate | 49/61 (80%) |
| 16 | predicate | 50/66 (76%) |
| 17 | predicate | 30/44 (68%) |
| 18 | predicate | 39/77 (51%) |
| 19 | predicate | 32/53 (60%) |

ser_v2:

| pressure_id | form | kept |
| --- | --- | --- |
| 00 | predicate | 0/150 (0%) |
| 01 | other | 3/36 (8%) |
| 02 | other | 2/49 (4%) |
| 03 | act | 0/46 (0%) |
| 04 | act | 0/23 (0%) |
| 05 | act | 0/1 (0%) |
| 06 | act | 0/2 (0%) |
| 10 | predicate | 0/101 (0%) |
| 11 | predicate | 0/64 (0%) |
| 12 | predicate | 0/82 (0%) |
| 13 | other | 0/49 (0%) |
| 14 | predicate | 0/26 (0%) |
| 15 | predicate | 2/150 (1%) |
| 16 | predicate | 0/46 (0%) |
| 17 | other | 0/54 (0%) |
| 18 | predicate | 0/76 (0%) |
| 19 | other | 0/45 (0%) |


## Design (what the builder does)

- **Form match (R19(4), R20).** The D clause's form comes from the text rule `clause_form`. Act-naming means it says
  wrong, incorrect, false or not true, checked first. Predicate-naming means it has one of the task's two Predicate
  words. Anything else is other. The builder refuses to run unless every D test clause is in `clause-forms.csv` with
  the same text and form. I clauses are drawn only from pool entries of the same task and form.
- **Transparency (R20).** Each clause needs a knowledge marker (knows, knowingly, already knows, already has) or an
  intent or game marker (on purpose, drill, quiz, quizzing, game, testing). `pool_violations` checks this, and the
  pool loader refuses violations.
- **Token match.** A pool clause fits a row only if three things hold in both streams. The full prompt keeps D's
  token count. I is clause-aligned with D over D's clause. I is clause-aligned with the twin `<task>_honest` over
  I's own clause, which is the assertion 02a's `neutral_twin` pairing runs with I as the pressure stream. The pick
  is `sha1("inversion:" + instance_id) mod k` over the fitting clauses in pool order.
- **One length limit.** The D config's `max_seq_length` must equal `v2.MAX_SEQ_LENGTH`, which the scorer uses.
- **Columns.** Every D column is kept, and the clause is swapped in `clean_prompt`, `corrupt_prompt` and
  `neutral_prompt`.
  - `condition` is `inversion` and `slot_kind` is `transparent`. `honest_twin_kind` is None.
  - `pressure` holds the I clause, because segmentation finds the clause by `rfind(pressure)`.
  - Added: `instructed_inversion_id`, `instructed_inversion_form`, `instructed_inversion_wording`.
  - D's clause and margins: `i_source_pressure`, `i_source_clause_form`, `i_source_clean_margin`,
    `i_source_corrupt_margin`.
  - After scoring: `h_instructed_inversion_clean` and `_corrupt`, and the I target margins in `clean_margin` and
    `corrupt_margin`.
  - D's `h_*`, `honest_instruction_*`, `prior_margin` and `neutral_id` stay as D's values.
  - Each `dataset_config.json` records these notes under `field_notes`.
- **Filter (R20).** D's pressure rule, `contingency._deceptive` at margin 0.7: the target must be the argmax with a
  margin of at least 0.7 in both streams. The margin-only count is reported beside it, as `n_margin_only_kept` in
  the config and `margin_only_kept` in the filter report. Retention is reported per `pressure_id`, form, Template
  Variant, Designation x Item Polarity, and the full sampler stratum (`retention_by_sampler_stratum`).
- **Outputs.** The score stage writes `outputs/_build_inversion_v2/<task>/{scores.jsonl, meta.json}`. The assemble
  stage runs on Delta and writes `data/datasets/<task>_inversion/` (test split only) with `dataset_config.json`
  and `filter_report.json`. The config holds the pool, table and builder sha256, the salt, the thresholds, the
  scoring job id, cluster, GPU and seconds, and `bridges2_delivery`. Assemble exits 3 when a task keeps fewer than
  300 ids, which is a hand-back before 1C.
- **Safety.** The pinned alignment checks are assert statements, so the builder refuses to run under `python -O`.

## For 02a (the `neutral_twin` kind and loaders)

- `<task>_inversion` is a DatasetDict with a **test split only**. Kept rows keep D's row order as a subset. `tasks/`
  is untouched, and "inversion" is not in `tasks.DECEPTION_CONDITIONS`.
- Join it to `<task>_honest` by `instance_id`. The `pressure_id` values are equal, so the pairing assertion holds
  as written: `assert_clause_aligned_pair(I_prompt, H_prompt, I_row["pressure"])` with I as the pressure stream.
- I's labels are D's. `target` is the deceptive item, and `clean_margin` / `corrupt_margin` point in the target's
  direction. R-inv reads `d` on I in the deceptive direction, as on D.
- The I rows carry D's `honest_instruction_*` prompts unchanged. Those prompts do not contain D's clause.

## Tests

- `tests/test_inversion_v2.py`: 52 passed in mgnp with HF offline, including the real-tokenizer tests, and with
  `-W error::ResourceWarning`.
- Full suites on the final files (2026-10-25, after every edit), compared by name with
  `reports/00-baseline-failures.md`. Logs: `reports/08-suite-base.txt` and `reports/08-suite-mgnp.txt`.
- `tests/test_inversion_v2.py` on its own: 52 passed, 0 skipped in the base env with BLAS threads 1. In mgnp with
  HF offline it is also 52 passed.

| env | failed | passed | skipped | failure names vs baseline |
| --- | --- | --- | --- | --- |
| base (py3.9, BLAS threads 1) | 8 | 1956 | 60 | the same 8 names |
| mgnp (py3.12, HF offline) | 10 | 2130 | 19 | the same 8 names, plus 2 not in the baseline |

- **The 2 extra mgnp failures are not ticket 08's.** Both are in impl-02a's in-progress
  `tests/test_component_analysis_v2_cli_model.py`:
  - `test_dla_measures_the_neutral_twin_pair_and_the_lens_crossing`
  - `test_dla_on_a_nopressure_cell_reads_the_crossing_in_the_deception_direction`

  Both fail on `n_instances` 1000 where the test expects the 40-instance sample, inside the DLA path of
  `component_analysis/`. Nothing in `component_analysis/`, `analyze_components.py` or that test imports or reads
  `build_inversion_v2.py`, the pool or the CONTEXT.md entry; CONTEXT.md appears there only in docstrings. impl-02a
  should look at them. The v2 reproducibility test and `tests/test_inversion_v2.py` pass in both envs.

## GPU job plan (not submitted; waiting at the gate)

- **Wrapper.** `scripts/` belongs to ticket 01, so I did not write there. The proposed profile-aware wrapper is
  `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports/08-build_inversion_v2.sbatch`. It copies the
  cluster-profile block of `evaluate_circuit.sbatch`, because `build_v2.sbatch` sources `~/.bashrc`, which does not
  exist on Bridges-2. Proposed path: `scripts/build_inversion_v2.sbatch`. The orchestrator places it, or tells me to.
- **Prerequisites.** Ticket 01 has landed. The branch is pushed with the builder, the pool, `clause-forms.csv` and
  the wrapper. The D and H test datasets are tracked, so the Bridges-2 clone already has them.
- **Commands**, from the worktree root on the Delta login node that holds the SSH masters:

```
/u/swong2/.conda/envs/mgnp/bin/python -I dataset/build_inversion_v2.py --stage score --no-model
DC_CLUSTER=delta bash scripts/build_inversion_v2.sbatch --no-model     # the wrapper's own command line, dry
scripts/remote/b2.sh sync-code --dry
scripts/remote/b2.sh sync-code
scripts/remote/b2.sh submit --dry --time 00:30:00 --script scripts/build_inversion_v2.sbatch --job-name build-inv-v2
scripts/remote/b2.sh submit --test-only --time 00:30:00 --script scripts/build_inversion_v2.sbatch --job-name build-inv-v2
# ledger reservation (lock), then:
scripts/remote/b2.sh submit --time 00:30:00 --script scripts/build_inversion_v2.sbatch --job-name build-inv-v2
scripts/remote/b2.sh status <jobid>
scripts/remote/b2.sh fetch outputs/_build_inversion_v2
/u/swong2/.conda/envs/mgnp/bin/python -I dataset/build_inversion_v2.py --stage assemble
```

- **Walltime.** Cold model load takes about 460 s on Bridges-2. Scoring is 6,000 forwards (3 tasks x 1,000 rows x
  2 streams) at batch 32 with prompts of 120 tokens or fewer, so about 1 to 2 min. That estimate is derived from the
  per-forward costs of the v2 build and has not been measured on an H100. The total is about 10 to 13 min; x1.5
  rounded up to a quarter hour gives `--time 00:30:00`.
- **Reservation.** One h100-80 on GPU-shared, account cis260361p, 0.5 GPU-h. That is exactly ticket 08's
  allocation. `source_sha256` will cover `dataset/build_inversion_v2.py`, the pool and the wrapper.
- **After the job.** Reconcile sacct elapsed, rounded up to 0.25 h, under the lock. Run assemble on Delta. Report
  retention per task, `pressure_id`, sampler stratum and form, and both filter counts. Fill the curated note's
  retention section. A task with fewer than 300 kept ids is a hand-back before 1C.

## Open questions for the orchestrator

1. **Wrapper placement** in `scripts/`, as above.
2. **Descriptive vs directive wording.** D clauses are directives to the assistant ("Your job is to ..."). I clauses
   report the asker's request ("The buyer already knows ... and wants ..."). That frame is what makes them
   transparent, but it is a wording difference beyond the deceptive / transparent contrast. The curated note states
   it as a limitation (spec §7.5). No action needed unless you want a directive-framed variant.
3. **CONTEXT.md edit.** The ruling asked for the glossary entry, so I made it. CONTEXT.md is shared, so the commit
   should include it; it is listed below.

## Comments

### Files to commit (absolute paths)

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/dataset/build_inversion_v2.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/dataset/deception_pools/v2/inversion_v2.json`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_inversion_v2.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/docs/research/mechanism-analysis/inversion-control.md`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/docs/research/mechanism-analysis/inversion-dry-run.txt`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/CONTEXT.md` (the
  "Instructed-Inversion Condition (I)" entry only)
- To place, then commit: the wrapper
  `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports/08-build_inversion_v2.sbatch`, proposed as
  `scripts/build_inversion_v2.sbatch`.
- After the job (written 2026-10-25):
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/data/datasets/sdr_v2_inversion/`
    (dataset_dict.json, test/{data-00000-of-00001.arrow, dataset_info.json, state.json}, dataset_config.json,
    filter_report.json)
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/data/datasets/ser_v2_inversion/`
    (same files; 7 rows)
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/data/datasets/far_v2_inversion/`
    (dataset_config.json, filter_report.json, dataset_dict.json, test/{dataset_info.json, state.json}; no arrow
    file, 0 rows; it does not load, so commit only dataset_config.json and filter_report.json, or all of it as a
    record, the orchestrator's call)
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/outputs/_build_inversion_v2/`
    ({far,sdr,ser}_v2/{scores.jsonl, meta.json})
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/docs/research/mechanism-analysis/inversion-control.md`
    (retention section filled)

### Per-clause form match and the pool

The full per-clause form match and the pool listing (94 clauses, with the rows each clause drew) are in
`docs/research/mechanism-analysis/inversion-control.md`, sections "Per-clause form match (derived)" and "The pool".
They were regenerated on the final pool. All 49 D clauses have table form = rule form.
