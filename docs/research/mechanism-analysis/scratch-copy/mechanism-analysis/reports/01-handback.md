# Ticket 01 hand-back (impl-01): progress log

Worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis`, branch
`mechanism-analysis` (HEAD c24b5d9). No git, no GPU.

## Progress

- 2026-10-25: ticket claimed. Baseline suites started in both envs on the untouched tree (before any edit).
- Verified (derived, from `data/datasets/<t>_v2{,_nopressure}/test`, mgnp, clause surgery): for far, sdr and ser,
  the `no_pressure` variant rows of D's test split (clause removed from both streams by
  `dataset/clause_surgery.remove_clause`) equal `<t>_v2_nopressure`'s test split row for row, clean and corrupt
  prompts, 1000/1000, same instance ids in the same order. So a bank collected over the variant rows is the bank
  over `<t>_v2_nopressure`'s test split (R13). A test pins this identity.
- Design (advisor-checked): opt-in evaluator flag (absent from the CLI namespace unless given, so every existing
  cell's `cli` record is unchanged); per-task `variant:no_pressure` bank keyed by task label; chain wrapper
  `scripts/evaluate_chain.sbatch` running one `evaluate_circuit.sbatch` per scheme (one cold load, two warm);
  `delta.env` keeps a hard-coded worktree default with `DC_DELTA_REPO_ROOT` as override; filtered fetch of
  `outputs/_analyses/mechanism-analysis-*`.
- Seams under test (the ticket's): b2.sh `--dry` output; the profile and wrapper behaviour at job run time
  (bash sandbox with stubs); `Session.mean_bank` and the knockout variant section on the tiny model; the real CLI
  end to end on the tiny model; the launcher's plan, sbatch lines, `--test-only`, ledger-locked `--submit` and
  checker.
- Before-snapshot taken on the untouched tree, both envs: real `evaluate_circuit.py --evals knockout` cells on the
  tiny model under interchange, zero and mean, with a tiny task that serves both prompt variants, so the variant
  rows run (`/u/swong2/.claude/jobs/1c836bb8/tmp/impl01/snap_before/`). Re-run after the edits and diffed byte for
  byte.
- Note: the job tmp dir is shared with other agents; my first baseline output files were deleted mid-run (I use
  `tmp/impl01/` now) and the mgnp baseline was re-run on the untouched existing files (only my new test files
  ignored).
- New files written (TDD, green): `scripts/evaluate_chain.sbatch`, launcher `ma_cells.py`, `ma_build_suite.py`,
  `suite_ma.json`, `ma_gen_cells.py`, `ma_check_cells.py`, `README.md`.
- Finding: on ser, `D_ser - H_ser` (19 heads) holds no core head, so set 6 = set 5 there. The ser set-6 cells under
  mean and zero duplicate set 5, and the ser set-6 interchange cell duplicates ticket 06's `D_ser_minus_H_ser_hko`.
  Kept, as the spec lists them (about 20 H100-min); open question for the orchestrator.

## impl-01r (resumed 2026-10-25 14:10, after impl-01 stalled on a spend limit)

Verified impl-01's uncommitted work against the worktree and applied the two reviews' findings and R21
(details and the review itself: `reports/01-review.md`). Scratch files: `/u/swong2/.claude/jobs/1c836bb8/tmp/impl01r/`.

- Blocking fix (R19(2), R21): with `--variant-mean-bank no_pressure`, knockout.json has `variants.<v>` (task bank,
  exactly the no-flag run) and `variants_matched_bank.no_pressure` (the same rows under their own bank), plus
  `mean_banks` naming the bank per section that ran. Ticket 03 reads both no-pressure results from there.
- Byte-identity pin without the flag: a suite test runs real `evaluate_circuit.py` knockout cells on the tiny
  model under interchange, zero and mean and compares knockout.json with branch-base fixtures
  (`tests/fixtures/mechanism_analysis_v1_knockout/`, `seconds` masked). Finding: impl-01's mgnp before-snapshot
  does not reproduce on dt-login04 (one fp32 ulp everywhere, deterministic; env unchanged); the branch-base code
  from the main checkout (= c24b5d9) reproduces today's output exactly, so it is host-side. mgnp fixtures rebuilt
  from the main checkout's code on this host; the test skips on another CPU model (`cpu.txt`).
- Refactors: `_load_module` in `ma_cells.py`; bank-name helpers and the single flag reader in
  `evaluation/ablation.py`; comment fix; `edit_ledger` no longer masks the owner-write error.
- b2.sh: forced refspec; explicit branch-exists check; after a failed fast-forward (force-push) the clone's branch
  moves with `reset --keep` (never `--hard`), printing old and new heads; literal usage text. Tested against real
  local git repos (track a new branch, fast-forward, force-push, a local edit blocking checkout).
- R21: phase 1A is 33 cells; ser's set-6 cells are dropped by a data rule (set 6 == set 5) and recorded in
  `suite_ma.json` `dropped_cells` with the identity and ticket 06's interchange cell of record.
- Cost model: the mean group now also pays the matched no-pressure run (4.0 A40-min per mean cell, derived).
- Deviation (R21, accepted): `scripts/analyze_components.sbatch` exports `OMP/MKL/OPENBLAS_NUM_THREADS=1` through
  the Delta profile, so its unset-`DC_CLUSTER` behaviour is the pre-profile wrapper plus that thread pin.
- `tests/test_knockout.py`, `tests/test_knockout_model.py`, `tests/test_knockout_families_model.py`: impl-02ar's
  hand-back claims them as 02a's edits (they test `component_analysis.knockout`'s mean and zero schemes and fail
  without 02a's code). Left untouched and NOT on ticket 01's commit list.

### impl-01r hand-back 2026-10-25 (ticket resolved)

**Built and run.** impl-01's uncommitted work was verified, and the review findings and R21 were applied. Details
are in `reports/01-review.md` (both axes, done by impl-01r itself, no sub-agents). Under `--variant-mean-bank
no_pressure` the no-pressure rows now run under both banks. knockout.json gets `variants.<v>` (task bank, identical
to the no-flag run), `variants_matched_bank.no_pressure` (the rows' own bank) and `mean_banks` (the bank per section
that ran). Without the flag, knockout.json is byte-identical to the branch base for interchange, zero and mean
(suite test against fixtures). Phase 1A has 33 cells (R21).

**Files to commit** (absolute; exclude `__pycache__`, `logs/`, `eval_jobs.txt`):

- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/evaluate_circuit.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/evaluation/ablation.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/evaluation/context.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/evaluation/knockout.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/scripts/remote/b2.sh
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/scripts/cluster/delta.env
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/scripts/analyze_components.sbatch
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/scripts/evaluate_chain.sbatch
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/docs/bridges2.md
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/outputs/_launch_mechanism_analysis/README.md
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/outputs/_launch_mechanism_analysis/ma_cells.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/outputs/_launch_mechanism_analysis/ma_build_suite.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/outputs/_launch_mechanism_analysis/ma_gen_cells.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/outputs/_launch_mechanism_analysis/ma_check_cells.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/outputs/_launch_mechanism_analysis/suite_ma.json
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_mechanism_analysis_infra.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_mechanism_analysis_launcher.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/test_mechanism_analysis_mean_bank.py
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/fixtures/mechanism_analysis_v1_knockout/cpu.txt
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/fixtures/mechanism_analysis_v1_knockout/py39-torch2.8.0/{interchange,zero,mean}.json
- /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-analysis/tests/fixtures/mechanism_analysis_v1_knockout/py312-torch2.11.0/{interchange,zero,mean}.json

Not on this list: `tests/test_knockout.py`, `tests/test_knockout_model.py` and `tests/test_knockout_families_model.py`.
impl-02ar's hand-back claims them as 02a's edits. They test `component_analysis.knockout` and fail without 02a's
code, so they belong on 02a's commit. Nothing under `docs/research/mechanism-analysis/` is ticket 01's.

**Tests** (full suite, BLAS threads pinned to 1, `-rfE -p no:cacheprovider`; outputs in
`/u/swong2/.claude/jobs/1c836bb8/tmp/impl01r/full_{base,mgnp}.txt`):

| env | failed | passed | skipped | time |
| --- | --- | --- | --- | --- |
| login base (py3.9) | 8 | 1973 | 60 | 488 s |
| mgnp (py3.12) | 8 | 2152 | 19 | 1357 s |

In both envs the 8 failures are exactly the 8 names in `reports/00-baseline-failures.md`. There are no new failures,
and no red test from 02a's or 08's new files. The byte-identity tests run (not skip) in both envs on dt-login04.

**Phase 1A job table** (Bridges-2, one h100-80 per job, from `ma_gen_cells.py --profile bridges2 --stage 1a --via
scripts/remote/b2.sh --dry`):

| job | cells (mean + zero + interchange) | H100 estimate | walltime | reserved GPU-h |
| --- | --- | --- | --- | --- |
| p1a_far | 7 + 4 + 1 | 97.8 min | 02:30:00 | 2.5 |
| p1a_sdr | 7 + 4 + 1 | 97.8 min | 02:30:00 | 2.5 |
| p1a_ser | 6 + 3 + 0 | 76.9 min | 02:00:00 | 2.0 |
| total | 33 | 4.54 GPU-h (derived) | | 7.0 GPU-h (14 SU) |

The spec says about 7.5 for 36 cells. Dropping ser's 3 cells saves 0.5 GPU-h reserved. The matched no-pressure run
adds about 6.5 min to each far/sdr job. The bank and matched-run rates are derived, not measured; the first job
recalibrates them.

**Jobs (test-only, nothing queued):**

- **Delta, default profile (beto, gpuA40x4).** `sbatch --test-only` accepted all three jobs (23199480-23199482),
  with --time 09:00:00, 09:00:00 and 07:00:00.
- **Delta, bjhz-delta-gpu on gpuH200x8.** Accepted all three (23199483-23199485), with --time 02:00:00, 02:00:00
  and 01:30:00.
- **Bridges-2, chain script.** `b2.sh submit --dry --test-only --script scripts/evaluate_chain.sbatch` printed
  the exact remote sbatch line. It is dry only because the chain script is not on the clone until the branch is
  pushed and synced (R3).
- **Bridges-2, same options with the evaluate wrapper.** A live `--test-only` with
  `scripts/evaluate_circuit.sbatch` and p1a_far's mean group was accepted (49824094, GPU-shared, w008). SSH
  masters were open on dt-login04.
- **Chain dry-run.** The real chain wrapper with `--dry-run` per group ran on the login node for p1a_ser: both
  groups exited 0, and the estimate lists the matched bank and the matched run.

**Ledger delta:** none (0 GPU-h, no reservation).

**Deviations, logged:**

1. **Thread pin (R21, accepted).** `analyze_components.sbatch` with unset `DC_CLUSTER` is the pre-profile wrapper
   plus the BLAS thread pin from `delta.env`.
2. **Force-push sync.** b2.sh `sync-code` fast-forwards. After a force-push it moves the clone's branch with
   `git reset --keep`, never `--hard`, and prints the old and new heads. The ticket said "clone or fast-forward".
   The review asked that a force-pushed branch sync, and `+` on the refspec alone cannot do that.
3. **1A total.** It is 7.0 GPU-h reserved, against the spec's 7.5 (R21's drop, plus the matched-run cost).
4. **mgnp fixtures.** impl-01's mgnp before-snapshot did not reproduce on dt-login04. It is off by about one fp32
   ulp everywhere, deterministically, with the env unchanged. Branch-base code run from the main checkout gives
   exactly today's bytes, so the cause is the host. The mgnp fixtures come from that run, and the identity test
   skips on another CPU model.

**For ticket 03:** read the no-pressure column under mean from both `variants.no_pressure` (task bank) and
`variants_matched_bank.no_pressure` (the rows' own bank), as R19(2) requires. The mean-bank provenance is in each
section's `mean_bank`.

**Open questions for the researcher:** none.

**Review outcome:** no open blocking or standards finding. Three accepted residuals are listed in
`reports/01-review.md`.
