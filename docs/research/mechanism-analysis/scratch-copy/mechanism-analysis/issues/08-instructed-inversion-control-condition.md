# 08 — The instructed-inversion control condition `<t>_v2_inversion`

**What to do:** build a non-deceptive instructed-inversion condition per task (R15), so phase 1C and phase 2 can test
whether the pressure mediators are deception-specific or generic instructed-inversion machinery (spec §2.4, R-inv).
Each row is a D test instance whose Pressure Clause is replaced by a transparent clause that asks for the same item
openly (for example, "The reviewer asked you to name the result that is NOT failing."). Same instance ids, same
target item, behaviour-filtered. CPU work plus one short GPU scoring job.

**Status:** resolved
**Type:** task
**Blocked by:** nothing for the CPU build. The scoring job needs ticket 01 (b2.sh branch) and the branch pushed (R3),
or the orchestrator's approval for a Delta interactive H200 job.
**GPU allocation:** 0.5 H100 GPU-h on Bridges-2 (one scoring job, 3 tasks x 1,000 test rows x 2 streams).

## Facts to build on

- The v2 conditions live in `data/datasets/<t>_v2{,_honest,_nopressure}/` (DatasetDict with `dataset_config.json`).
  I is a new sibling, `data/datasets/<t>_v2_inversion/`, test split only. Existing v2 files are not touched.
- Provenance-pinned, never edited (agent-brief): `dataset/build_deception_v2.py`, `dataset/deception_v2.py`,
  `dataset/clause_surgery.py`, `dataset/contingency.py`; `tests/test_v2_reproducibility.py` fails by design if they
  change. Import them as libraries from a new builder script (name: builder, e.g. `dataset/build_inversion_v2.py`).
- Clause surgery: `clause_surgery.replace_clause(prompt, clause, replacement)` edits the stored prompt strings in
  place and refuses anything ambiguous; callers re-run the aligned-pair assertion.
- Length matching, the neutral twin's precedent: `deception_v2.neutral_candidates` / `select_neutral` (`:596`,
  `:614`) choose, from a pool ordered by token count (`NEUTRAL_POOL_PATH`), a sentence that keeps the prompt's token
  count unchanged in both streams. I's clause must match D's clause token count per instance the same way, so that
  `<t>_v2_honest` is I's paired twin by instance id (02a's `neutral_twin` kind with I as the pressure stream).
- The behaviour filter thresholds: `contingency.MARGIN = 0.7` (pressure: the target item's margin >= 0.7 in both
  streams). The scoring step to mirror: `dataset/build_nopressure_dataset.py` (it scores a derived condition and
  records `margin_thresh` in `dataset_config.json`).
- Target item: the item D's response names (D's labels). Under I the asker requests that item openly, so naming it
  misleads no one.

## Acceptance criteria

- [x] A transparent-inversion clause pool per task in a new file under `dataset/` (the v2 pools are not edited):
      each clause names the requested item by relation, says openly that it is the inverse of what would otherwise be
      asked for, and contains no instruction to mislead. Several length variants per wording so every D clause token
      count can be matched. The pool is listed in the review for a human read.
- [x] The builder replaces each D test row's clause in both streams with a token-count-matched pool clause, re-runs
      the aligned-pair assertion, and records `condition: "inversion"`, the chosen clause id, D's `pressure_id` and
      labels. Rows with no matching clause are dropped and counted per `pressure_id`.
- [x] Pairing check on CPU: for every kept row, `<t>_v2_honest` with the same id is clause-aligned with the I row
      (identical tokens outside the clause span, equal clause token count).
- [x] Scoring job (Bridges-2, one job): margins in both streams; kept = target margin >= 0.7 in both streams.
      Retention per task, per `pressure_id` and per stratum reported. If fewer than 300 of 1,000 test ids are kept for
      a task, hand back before 1C.
- [x] `data/datasets/<t>_v2_inversion/` written with `dataset_config.json` (pool file hash, thresholds, the scoring
      job id); reaches Bridges-2 through the branch or `b2.sh sync-data` (builder checks which applies).
- [x] Tests (CPU, both envs): the builder on a fixture produces aligned pairs and refuses a mismatched length; the v2
      reproducibility test still passes; failures compared by name with `reports/00-baseline-failures.md`.
- [x] Curated copy (R6): `docs/research/mechanism-analysis/inversion-control.md` with the pool, retention and
      examples. Ledger `bridges2` reconciled under the lock. Review in `reports/08-review.md`; progress in
      `reports/08-handback.md`.

## Hand-back

The file list to commit (builder, pool, datasets, tests, curated note), the retention table, and the scoring job's
numbers. Phase 1C waits for this ticket.

**Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if
the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user is
always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.

## Comments

### Orchestrator addition 2026-10-25 (R19(4), from review-00's re-check)
- Form-match every inversion clause to its D clause using `docs/research/mechanism-analysis/clause-forms.csv`
  (ticket 02a): act-naming D clauses ("answer with the wrong result") get act-naming transparent-game inversion
  clauses; Predicate-naming D clauses get Predicate-naming ones ("the result that is NOT failing"). Token-match each
  pair so the existing neutral twin pairs with I. The report shows the per-clause form match BEFORE the pool is used;
  FAR's 12 D clauses are all act-naming, so FAR's inversion pool is all act-naming.

### impl-08 hand-back 2026-10-25 (CPU part done; waiting at the GPU gate)
- Full record: `reports/08-handback.md`; review: `reports/08-review.md`; the R20 and standards rulings are applied.
- I is stored as `data/datasets/<task>_inversion/`, for example `far_v2_inversion`. The condition id is
  `inversion`, the slot kind is `transparent`, and the added columns are `instructed_inversion_*` and `i_source_*`.
  All other D columns are kept.
- CPU dry run with the Llama tokenizer: 3,000 of 3,000 D test rows derived, 0 dropped. The log is
  `docs/research/mechanism-analysis/inversion-dry-run.txt`.
- Tests on the final files, compared by name with `reports/00-baseline-failures.md`:
  - **base env:** 8 failed, 1956 passed, 60 skipped. These are the same 8 baseline names.
  - **mgnp env:** 10 failed, 2130 passed, 19 skipped. These are the 8 baseline names plus 2 failures in impl-02a's
    `tests/test_component_analysis_v2_cli_model.py`. Both DLA tests get `n_instances` 1000 where they expect 40. They
    are unrelated to ticket 08's files.
  - `tests/test_inversion_v2.py` passes in both envs, 52 of 52 with none skipped. `tests/test_v2_reproducibility.py` passes.
  - Logs: `reports/08-suite-base.txt` and `reports/08-suite-mgnp.txt`.
- Files to commit (absolute):
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/dataset/build_inversion_v2.py`
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/dataset/deception_pools/v2/inversion_v2.json`
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_inversion_v2.py`
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/docs/research/mechanism-analysis/inversion-control.md`
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/docs/research/mechanism-analysis/inversion-dry-run.txt`
  - `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/CONTEXT.md`
    (only the "Instructed-Inversion Condition (I)" entry)
  - The wrapper `/projects/beto/swong2/Alignment/.scratch/mechanism-analysis/reports/08-build_inversion_v2.sbatch`,
    to be placed as `scripts/build_inversion_v2.sbatch`.
- Still open: the scoring job (0.5 H100 GPU-h, `--time 00:30:00`), the assembly, retention, and the ledger
  reconciliation. They need ticket 01 to land and the branch to be pushed.

### impl-08 scoring result 2026-10-25: HAND-BACK before phase 1C
- Bridges-2 job 49824662 COMPLETED in 745 s. The ledger is reconciled to 0.25 GPU-h (0.5 SU).
- Kept ids, filter argmax + margin >= 0.7 in both streams. The margin-only rule keeps the same rows.
  - far_v2: **0 of 1000**.
  - sdr_v2: 618 of 1000.
  - ser_v2: **7 of 1000**.
- FAR and SER are below the 300 minimum. Under the transparent, descriptive clause the model names the honest item.
  The median target margin is about -3.6 for FAR and -2.75 for SER.
- Retention tables are in `reports/08-handback.md` and `docs/research/mechanism-analysis/inversion-control.md`.
- `far_v2_inversion` has an empty test split that does not load.

### impl-08 R22 result 2026-10-25: primary I built; FAR and SER below 300 (stated limitation)
- The primary `<t>_v2_inversion` uses the directive pool and Bridges-2 job 49825105 (775 s). Kept ids:
  - far_v2: **210 of 1000**.
  - sdr_v2: 788 of 1000.
  - ser_v2: **249 of 1000**.
- FAR and SER are below the 300 minimum; R22 states that as a limitation for those tasks. 191 of FAR's 210 kept
  rows have Designation Polarity `inversion`.
- The secondary `<t>_v2_inversion_reported` (job 49824662) keeps 0 / 618 / 7. It is recorded as the R22 finding.
- Ledger: both jobs are reconciled to 0.25 GPU-h each, and the holdback loan of 0.0833 has been returned.
- Suites on the R22 code show only the baseline names. Base env: 8 failed, 2009 passed. mgnp: 8 failed, 2188
  passed. `tests/test_inversion_v2.py` 71 pass.
- The commit list is in `reports/08-handback.md`, "R22 commit list". The curated note is
  `docs/research/mechanism-analysis/inversion-control.md`.

### impl-08 closed 2026-10-25
- The orchestrator committed the R22 file list as c2d47da (28 files) and pushed it. `inversion-dry-run.txt` left the index in the same commit.
- The round-1 note above about an unloadable `far_v2_inversion` test split is superseded. Round 1 is now `far_v2_inversion_reported`, which holds only its config and filter report. The primary `far_v2_inversion` loads with 210 rows.
- Nothing is open on the ticket-08 side.
