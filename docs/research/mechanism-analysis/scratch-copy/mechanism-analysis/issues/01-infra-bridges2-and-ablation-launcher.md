# 01 — Bridges-2 dispatch for a new branch, profile-aware component analysis, ablation-aware launcher, variant-matched mean bank

**What to do:** make the dispatch and launch tooling serve this feature. b2.sh needs a configurable branch and must
fetch analysis cells. `analyze_components.sbatch` must honour the cluster profile. The ticket-06 cell launcher needs
an ablation parameter, the phase-1A cell set and per-task packing (spec §4). The evaluator needs a variant-matched
mean bank for the no-pressure rows (R13). Small, test-first, and done first, because it unblocks phase 1A.

**Status:** resolved
**Type:** task
**Blocked by:** nothing (the worktree and branch exist since 2026-10-25). This ticket records the baseline failures
first (agent-brief).
**GPU allocation:** 0. Only `sbatch --test-only`, on Delta and on Bridges-2 through `b2.sh submit --test-only`.

## Facts to build on

- `scripts/remote/b2.sh:25` `BRANCH="mechanism-datasets"` is hard-coded. `:35` `FETCH_SUITE_ROOTS` lacks
  `outputs/_analyses`, and `.gitignore:8` ignores that directory.
- `scripts/cluster/delta.env:25`: `DC_REPO_ROOT` defaults to the mechanism-datasets worktree; `DC_DELTA_REPO_ROOT`
  overrides it.
- `scripts/analyze_components.sbatch:62` sources `~/.bashrc`, with no profile block. The block to mirror is in
  `scripts/evaluate_circuit.sbatch:48-61`.
- `outputs/_launch_mechanism_v2/evals/mv2_cells.py:72` hard-codes `--ablation interchange`. `:69-70`: KO cells run
  `--evals knockout` only. Packing rule today: one job per stage, test set, evals and common args (`jobs_for`,
  `:251`).
- Mean ablation today (review §0 and B4): `evaluation/ablation.py` `MeanCollector` / `MeanHook`, per site,
  position-pooled and broadcast to every position. The bank is collected over the bound task's test loader
  (`evaluation/context.py:351-372`), which is all pressure prompts. The variant rows use the task bank
  (`evaluation/knockout.py:325`, `ctx.hook_for("task")`).
- Bridges-2 rules: `docs/bridges2.md`; memory `bridges2-dispatch`; HB (e).
- Phase-1A cell set (spec §4): per task, `(E) - m` at leaf on D_t's test set. Sets 1-7 under mean; sets 3-6 under
  zero; set 6 under interchange; 36 cells. Set 6 is `(D_t - H_t) - (D_far & D_sdr & D_ser)`.

## Acceptance criteria

- [x] b2.sh: the branch comes from `DC_B2_BRANCH`, defaulting to the current behaviour, or a `--branch` flag.
      `sync-code` on `mechanism-analysis` clones or fast-forwards that branch. Tests cover the default, the
      override and `--dry` output.
- [x] b2.sh `fetch` with no paths also brings back `outputs/_analyses/<suite>` for the suites this feature names
      (`mechanism-analysis-*`). Cells are immutable, so a list file or `--ignore-existing` is fine. No `--delete`,
      same backup rule. Tested with `--dry`.
- [x] `delta.env`: the Delta repo root can point at this worktree (`DC_DELTA_REPO_ROOT`), tested.
- [x] `scripts/analyze_components.sbatch` sources `scripts/cluster/${DC_CLUSTER:-delta}.env` and runs
      `DC_ACTIVATE`, `HF_HOME` and the offline flags exactly as `evaluate_circuit.sbatch` does. Unset `DC_CLUSTER`
      reproduces today's Delta behaviour. A test like the evaluate wrapper's profile tests covers it.
- [x] **Variant-matched mean bank (R13).** Under `--ablation mean`, the `no_pressure` variant rows are ablated with a
      bank collected on `<t>_v2_nopressure`'s test split; the task rows keep the bank collected on D's test split.
      The bank used per row group is recorded in the cell's output. CPU tests on the tiny model: the variant bank
      equals a hand-computed mean over the variant rows; interchange and zero cells, and v1 mean cells, are
      byte-identical before and after.
- [x] Launcher: `gen_cells.py` / `mv2_cells.py` take an ablation scheme, and a phase-1A stage (name: builder) emits
      the 36 cells. Mean/zero cells never include `sanity`. One job per task chains the three schemes (warm loads).
      Cell ids and output dirs are distinct per scheme, so nothing in
      `outputs/_suites/mechanism-v2-coarse/{control,stage1,stage2}` is overwritten. New suite root:
      `outputs/_suites/mechanism-analysis/phase1a/`.
- [x] `check_cells.py` parses every generated command with `evaluate_circuit.py`'s argparse and resolves every path.
      The launcher's `--profile bridges2 --dry` output for the 1A stage prints the jobs with walltimes from the cost
      model, about 7.5 H100 GPU-h in total (spec §4). If chaining schemes in one job is not possible, report the
      split cost instead.
- [x] `b2.sh submit --test-only` accepts one 1A job on Bridges-2. Delta `sbatch --test-only` accepts the same job
      under the delta profile.
- [x] Tests in both envs, failures compared by name with `reports/00-baseline-failures.md`, which this ticket writes
      first (agent-brief). No GPU job submitted.
- [x] Review in `reports/01-review.md`; progress in `reports/01-handback.md`.

## Hand-back

The file list to commit, test results per env, and the dry-run job table for 1A. The orchestrator commits and pushes
the branch (R3).

**Phase gate (R9).** Phases run back to back under the user's standing go. Before each later phase's first GPU
submission the orchestrator posts the previous phase's reading to the user and continues; it stops and asks only if
the reading changes the plan (outcome B on all three tasks, a failed drift control, or a cap raise). The user is
always asked before a merge to main, an EVAL 5, dropping a mechanism, or a cap raise.

## Comments

### Orchestrator addition 2026-10-25 (R19(2), from review-00's re-check)
- The variant-matched mean bank is OPT-IN behind a flag. Without the flag, every existing mean cell (v1 and ticket
  06) stays byte-identical. With the flag, the no-pressure variant rows run under BOTH banks (task bank and the
  no-pressure bank) and both results are written; ticket 03 reports both. Collect the no-pressure bank over the
  evaluator's own no-pressure variant loader (the same rows the variant evaluation uses), not a new loader.

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
