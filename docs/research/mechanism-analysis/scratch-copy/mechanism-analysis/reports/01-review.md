# Ticket 01 review (impl-01r, 2026-10-25)

Done by impl-01r itself on both axes (Standards, Spec). The two earlier reviews of impl-01's work (spec review and
standards review, ruled on in R21) are the input; this file records how each finding was applied and what a final
read of the resulting diff found. Sub-agents were not spawned for this pass.

## Earlier findings and how they were applied

| finding | where | resolution |
| --- | --- | --- |
| BLOCKING: with `--variant-mean-bank` the no-pressure rows must run under both banks, both written (R19(2), R21) | `evaluation/knockout.py` | `_variant_sections`: `variants.<v>` is the task-bank run, unchanged; `variants_matched_bank.no_pressure` is the same rows under the bank over those rows. Tests: spy (`ctx.asked == [task, task, variant:no_pressure]`), real CLI on the tiny model (task-bank sections equal the no-flag run key for key, the matched run's full row equals it, its knockout row differs). |
| A suite test pins knockout.json byte-identical without the flag | `tests/test_mechanism_analysis_mean_bank.py`, `tests/fixtures/mechanism_analysis_v1_knockout/` | Three schemes (interchange, zero, mean), real `evaluate_circuit.py` on the tiny model, compared byte for byte with branch-base output (`seconds` masked). See "Fixture provenance" below. |
| One `_load_module(name, relpath)` for the three importlib loaders | `ma_cells.py` | Done; `ma_gen_cells.py` and `ma_check_cells.py` use it; a test asserts no other launcher file imports importlib. |
| `VARIANT_BANK_PREFIX` everywhere; one place for the `variant_mean_bank` getattr | `evaluation/ablation.py` | `VARIANT_BANK_PREFIX`, `variant_bank_name`, `is_variant_bank`, `matched_variants(cli)` live in `evaluation/ablation.py` (a leaf both `context.py` and `knockout.py` import; no cycle). Used in `context.py`, `knockout.py`, `evaluate_circuit.py`, `ma_check_cells.py`. No hand-built `variant:` string is left in code (`ma_cells.MEAN_BANKS` became the count `MEAN_BANKS_PER_GROUP`). |
| `mean_banks.variants` names a bank only for sections that ran | `knockout.section_banks` | Built from the payload: skipped sections are left out, `wikitext` only when it ran; a skipped variant gets no matched run and no bank collection (test). |
| b2.sh `sync-code` hides a real checkout error behind "already exists" | `scripts/remote/b2.sh` | `show-ref --verify --quiet refs/heads/<b>` decides between `checkout` and `checkout -b --track`; no `2>/dev/null`. Tested for real against local git repos: a local edit in the way stops sync with git's message naming the file. |
| Forced refspec so a force-pushed branch syncs | `scripts/remote/b2.sh` | `fetch origin +<b>:refs/remotes/origin/<b>`. With `+` alone `merge --ff-only` would still refuse a rewritten branch, so after a failed fast-forward the branch moves with `git reset --keep origin/<b>` (keeps uncommitted edits, refuses if they are in the way; never `--hard`), printing old and new heads. Tested for real: force-push, then sync lands on the new head and stderr names the old one. |
| Line-number `usage()` | `scripts/remote/b2.sh` | Literal heredoc text in the file; test checks it has no `#` lines and names `DC_B2_BRANCH`. |
| Misleading comment "mean first (it builds the banks)" | `ma_cells.py` | Rewritten: each scheme is its own process, nothing carries over; mean runs first only so the longest group starts after the cold load. |
| `edit_ledger`'s `finally` masks the original error when the owner write fails | `ma_gen_cells.py` | `contextlib.suppress(FileNotFoundError)` around the owner removal, `rmdir` always. Test: a failing owner write raises its own `PermissionError`, the lock dir is gone, the ledger is untouched. |
| Drop the location-coupled delta.env test | `tests/test_mechanism_analysis_infra.py` | Removed with the `WORKTREE` constant; the `DC_DELTA_REPO_ROOT` override test stays. |
| R21: drop ser's three set-6 cells; 1A is 33 cells; suite_ma.json records the identity | `ma_cells.py`, `ma_build_suite.py`, `suite_ma.json` | Data-driven: set 6 is dropped for a task when its head set equals set 5's (`D_t - H_t` holds no core head); only ser qualifies. `suite_ma.json` `dropped_cells` records each dropped cell, the identity (19 = 19 heads, 0 core heads in set 5) and, for interchange, ticket 06's cell of record (`outputs/_suites/mechanism-v2-coarse/stage1/s1_ser__D_ko/cells/D_ser_minus_H_ser_hko__leaf/ser_v2/interchange`, present on Delta, test). |
| Thread-limit env vars in `analyze_components.sbatch` | `scripts/cluster/delta.env` via the profile | Kept (R21: accepted deviation, logged in the hand-back). |

## Standards (final read of the diff)

- Additive and opt-in: without the flag the CLI namespace has no new entry (argparse SUPPRESS), knockout.json is
  byte-identical (pinned), the log adds nothing (the matched section is absent). v1 code paths are untouched.
- One reader of the flag (`matched_variants`), one bank-name constructor (`variant_bank_name`).
- Tests sit at the seams the ticket names: argparse, `Session.mean_bank`, the knockout variant sections, the real
  CLI end to end, the b2.sh remote command against real git, the launcher's plan/lines/ledger, the checker
  against the real masks and datasets.
- Cost model: the pass, bank and matched-run rates are labelled derived in code, README and suite_ma.json.
- Accepted residuals (not fixed):
  1. The matched no-pressure run re-evaluates the all-gates-open `full` row, which no bank affects (one extra
     pass and live reference per mean cell, about 0.3 H100-min). Kept for an identical section layout; the CLI
     test asserts the two `full` rows are equal, a free check that only the hook varies.
  2. The byte-identity fixtures hold only on the CPU model recorded in `cpu.txt` (AMD EPYC 7763); the test skips
     elsewhere. See below.
  3. `ma_cells.V2_INTERCHANGE_CELL` hard-codes ticket 06's stage-1 path pattern. It is checked by a test that
     the file exists on this checkout.

## Spec (ticket 01 acceptance criteria, R13, R19(2), R21)

- b2.sh branch from `--branch` / `DC_B2_BRANCH` / default, sync-code clone or fast-forward, `--dry` tests: met;
  plus the force-push behaviour above (documented in docs/bridges2.md).
- fetch brings back `outputs/_analyses/mechanism-analysis-*` with the same safety rules: met (impl-01, tested).
- delta.env repo root override: met (tested by the override test only, per the review).
- analyze_components.sbatch profile block: met (impl-01, tested; thread pin is the R21 deviation).
- Variant-matched mean bank: met and now matches R19(2): opt-in, both banks, both written, bank collected over the
  evaluator's own no-pressure variant loader; recorded per section with row and token counts; the hand-computed
  mean test and the per-task keying test pass; interchange, zero and mean without the flag are byte-identical.
- Launcher: ablation scheme per group, 1A stage, no sanity, one job per task chaining its schemes, distinct ids and
  output dirs under `outputs/_suites/mechanism-analysis/phase1a/`: met, 33 cells per R21.
- Checker parses every command and resolves every path: met (3 jobs, 8 groups, 33 cells, 0 problems). Dry output
  prints the jobs with walltimes: 7.0 H100 GPU-h reserved (spec: about 7.5 for 36 cells; see the hand-back).
- Test-only on Delta and Bridges-2: Delta accepted all three jobs (default A40 profile and bjhz H200). Bridges-2:
  the chain line was checked with `--dry` only (the chain script is not on the Bridges-2 clone until the branch
  is pushed, R3); a live `--test-only` of the same options with `scripts/evaluate_circuit.sbatch` was accepted.
- No GPU job submitted: met.

## Fixture provenance (byte-identity test)

impl-01's before-snapshots: the base-env set reproduces on this host byte for byte and is used as is. The mgnp set
does not: on dt-login04 (AMD EPYC 7763) every float differs from impl-01's mgnp snapshot by about one fp32 ulp,
deterministically, while the mgnp env is unchanged since before 10:00. Running impl-01's snapshot procedure
against the main checkout's untouched code (main = c24b5d9 = the branch base) on this host gives output identical
to the current branch's code, so the difference is host-side, not code. The mgnp fixtures were rebuilt from that
main-checkout run (`tmp/impl01r/snap_main.py`, `make_fixtures.py`), and the test skips on another CPU model.

## Verdict

No open blocking or standards finding on ticket 01's files. Residuals 1-3 above are accepted and recorded.
