# Ticket 06 implementer report: EVAL 5 preparation, build phase

Date 2026-10-13. Worktree `Deception-Circuit/.claude/worktrees/format-control`, branch `format-control` (base a365e65).
**Nothing was submitted to Slurm.** Commits are made by the orchestrator on the implementer's instruction; the implementer ran no git command. Build phase committed as db72d03.

## Status

Build phase done. Ticket stays `claimed`. Open boxes: real-F `--dry-run`s for all six combinations (F is null in `suites.json`), the gate run on real ticket 04 cells (none exist yet), ticket 05's writer run on real EVAL 5 suites, and the independent review (not run in this dispatch by instruction).

## What was built

| file | what |
| --- | --- |
| `outputs/_launch_format_control/eval5_cmd.py` | pure command generator (`eval5_args`), gate (`gate`, `f_knockout_cells`, `read_wikitext_kl`), `refusals`, `sbatch_cmd`, dry-run parser and cost (`parse_dryrun`, `known_item_counts`, `cost_estimate`); CLI `args / check / gate / sbatch / cost` |
| `outputs/_launch_format_control/submit_eval5.sh` | `<far|sdr|sdr_coarse> <sm|lb> [--dry] [--standin] [--account] [--partition] [--time]` |
| `evaluation/eval5_format_summary.py` | `load_suite`, `tabulate`, `caveat_hits`, `render`, `write` (`result_summary.md` + `eval5_format.json`) |
| `outputs/_launch_format_control/write_eval5_format_summary.py` | thin CLI over the library |
| `outputs/_launch_format_control/README_eval5.md` | settings, gate, refusals, cost, the ticket 05 interface |
| `tests/test_format_control_eval5.py` | 47 tests |
| `outputs/_launch_format_control/dryrun_eval5_standin/*.log` | six stand-in dry-run logs |

### Design points worth knowing

- **`--task-from <D run>` is mandatory.** Without a task flag `resolve_tasks` defaults to every bound circuit's own task; D, H, F have three conditions, so the evaluator would run a 3 x 3 grid of benchmark cells. With it: "CELL GRID (3 circuits x 1 tasks)" in every dry-run.
- **Coarse.** `--circuit m=<_allmlp_nomb>`, `--expr D_hko=D - m` (and H, F), `--compose-granularity leaf`, same as the coarse recipe and ticket 04's ruling. Operands are not cells when `--expr` is used, so the suite has exactly `D_hko__leaf`, `H_hko__leaf`, `F_hko__leaf`. D's heads-only knockout is 8,832 fine units, matching `eval5_sdr_coarse_nls0.3_nomb`.
- **Two added flags, no number changed.** `--benchmark-screen-cache /projects/beto/swong2/Alignment/Deception-Circuit/outputs/_screens` puts D, H, F on the existing suites' items (the worktree has no cache). `--benchmark-repo-root /projects/beto/swong2/Alignment` locates MASK and Liars' Bench (the first probe failed: the default resolves to `.claude/worktrees/mask/mask`). Neither path is part of the screen-cache key.
- **Partition.** The screens were made on NVIDIA A40 and the GPU is in the key, so `--partition` defaults to `gpuA40x4`.
- **Gate.** Reads F's knockout cells on the D (`deceptive`) and F (`nopressure`) test sets from `suite_manifest.json`; KL from `knockout.json` `headline.wikitext_kl`, else `wikitext.discovered.kl_per_token` (field names checked on a real cell of `cross-task-faithfulness-nls0.3-rerun260922`). Refuses on a missing cell, missing KL, or KL > 0.66, naming cell and number. The "or fluent generations" route is the researcher's: the refusal points at `generation.examples`.
- **Refusal order** (no `--dry`, exit 3): F null, gate, `FORMAT_CONTROL_EVAL5_GO=1` absent; then the script runs its own `--dry-run` and refuses (exit 5) if it fails. `--dry` needs no go-ahead and prints the sbatch line only when F is set and the gate passes. `--standin` never gets one.
- **Walltime.** Dry-run ceiling x 1.5 in quarter hours via ticket 04's `fc_cells.walltime`: 44:30:00 (sm), 19:00:00 (lb).

## TDD evidence

Vertical slices, each red then green, run with the mgnp interpreter:

1. Command generator: 8 tests red (module missing), green after `eval5_args`.
2. Gate: 7 tests red (`gate` missing), green.
3. Config, refusals, sbatch line: 10 red, green.
4. Dry-run parser and cost: 4 red, green; then checked against the real probe log.
5. `submit_eval5.sh`: 8 red (script missing), green after the script; one test fixed (it looked for the evaluator's echo on stdout, which goes to the log).
6. Summary writer: 9 red, green after one test fix (a row prefix matched detail rows too). A further caveat-rule test went red, then green once the Liars' Bench guard counter replicated `_verdict` exactly (case-sensitive, REJECTED only).

Two test-side bugs were mine: a helper name clash (`_config` defined twice) that broke earlier tests, fixed by renaming the second helper `_bconfig`.

## Dry-run output (stand-in, F := H; login node, mgnp)

All six pass. Excerpt for `far sm`:

```
STAND-IN: F := H (plumbing only; never submitted)
  TOTAL     1460.5 - 1774.3 min (3 cell(s))
  cost: 3 cell(s); judge calls (ablated configs, upper bound, items from known post-screen counts): 4,671
        judge calls for uncached screens (at most): 0  (cached screens: 7 of 7)
        GPU hours (dry-run estimate, 1 GPU, very rough): 24.3 - 29.6
dry run OK; no submit line:
  REFUSED: a stand-in suite (F := H) is plumbing only and is never submitted
  REFUSED: the F run directory is not configured (suites.json format-control-far-nls0.3 runs.F is null: the Format Circuit has not landed)
```

| suite | dry-run | judge calls | GPU h (floor - ceiling) | --time |
| --- | --- | ---: | --- | --- |
| far sm | pass | 4,671 | 24.3 - 29.6 | 44:30:00 |
| far lb | pass | 4,050 | 9.2 - 12.5 | 19:00:00 |
| sdr sm | pass | 4,671 | 24.3 - 29.6 | 44:30:00 |
| sdr lb | pass | 4,050 | 9.2 - 12.5 | 19:00:00 |
| sdr_coarse sm | pass | 4,671 | 24.3 - 29.6 | 44:30:00 |
| sdr_coarse lb | pass | 4,050 | 9.2 - 12.5 | 19:00:00 |
| **all six** | | **26,163** | **100.5 - 126.3** | |

The cost is labelled stand-in. F's size changes the random draws, not the counts. Judge calls are an upper bound over knockout, circuit_only, empty and 6 randoms per cell, using the existing suites' post-screen item counts; the judge cache dedups repeats. Validation: the one-cell coarse sm suite logged 1,376 writes + 181 hits = 1,557 judge calls, exactly a third of 4,671. The dry-run's runtime is pessimistic: that suite is rated near 10 h and ran in 3 h 51 min, so a three-cell sm suite is plausibly 10 to 12 h on an A40.

## Tests

| env | ticket file | full suite | failing names |
| --- | --- | --- | --- |
| login base (py3.9) | 47 passed | 8 failed, 786 passed, 20 skipped | the 8 baseline names |
| mgnp (py3.12) | 47 passed | 8 failed, 787 passed, 19 skipped | the 8 baseline names |

The failing sets are identical to `00-baseline-failures.md` in both envs. No new failure; no failure in another ticket's files. The full suites ran before a lint-only refactor (semicolons, an unused import); the ticket file was re-run in both envs after it (47 passed). `ruff check --line-length 120` is clean on the four Python files; `bash -n` passes on the script. No `core.*` dumps.

## Files changed

New: `outputs/_launch_format_control/eval5_cmd.py`, `submit_eval5.sh`, `write_eval5_format_summary.py`, `README_eval5.md`, `dryrun_eval5_standin/{far,sdr,sdr_coarse}_{sm,lb}.log`; `evaluation/eval5_format_summary.py`; `tests/test_format_control_eval5.py`. Edited: the ticket file. No shared or other-ticket file changed.

## Interface for ticket 05

No change needed in ticket 05. Its `load_eval5` reads `<dir>/cells/<label>/<task>/<ablation>/benchmarks.json` and strips `__leaf|__head` then `_hko`, which maps both `D`/`H`/`F` and `D_hko__leaf`/... to the roles. Checked on a symlinked stand-in suite of real cells (D = `eval5_sdr`, H = `eval5_sdr_h03`, F = the coarse `hko__leaf` cell): D, H, F found with 7 datasets each, and `eval5_aggregate` returns numbers. Call it with both groups:

```
--eval5-dir outputs/eval5_format_<family> --eval5-dir outputs/eval5_format_<family>_lb
```

Optional single-file reader: `eval5_format.json` per suite (schema in `README_eval5.md`), or `evaluation.eval5_format_summary.tabulate(load_suite(dir))`.

## Summary writer, checked on real data

On the symlinked smoke suite the coarse cell's numbers match the hand-written `eval5_sdr_coarse_nls0.3_nomb/result_summary.md` (for example KO dec 0.000 on sandbagging with Δ +0.020, mean Δ +0.100; the fine pair's mean Δ +0.320 and +0.296). The full row is identical across three real suites, so no mismatch is flagged. Two caveat counters reproduce rows recorded in earlier summaries: 2 empty generations on `eval5_sdr_lb`'s knockout and 1 guard row on the coarse LB knockout. The MASK verdict-D counter reports 2 rows on the fine honest knockout; I did not check that count against a recorded one.

## Self-review

- **Standards.** Uses the CONTEXT.md vocabulary (Format Circuit, Honest Twin, `nopressure`); never "control circuit". Pure functions at the seams; I/O only in the CLI and the script. Tests hit public seams (generator output, gate result, script exit code and output, rendered markdown and JSON); `caveat_hits` was made public because its rule is a seam of its own.
- **Spec.** One invocation, one screen, one judge cache, random rows per circuit: yes. Interchange only, n 50, 6 randoms, budget 600, both groups: yes. Gate KL <= 0.66 with the number named, missing cell refused: yes. Explicit go-ahead: yes, via the environment variable. Grader caveats printed in every summary: yes, verbatim constants with sources. Nothing submitted: yes; every script test shadows `sbatch` with a stub and asserts the shadowing.
- **Safety of the submit path.** The only `sbatch` call is the last line of `submit_eval5.sh`, reached only after `check` (F, gate, go-ahead) and a passing dry-run. It was exercised only with the stub.

## Concerns and decisions for the researcher

1. **Partition vs "any partition".** The launcher defaults to `gpuA40x4` because the cached screens are A40-only. Another GPU re-screens, writes new screens into the main checkout's `outputs/_screens`, and breaks item-for-item comparability with the existing suites.
2. **The screen cache lives in the main checkout.** On an A40 hit nothing is written there; on a miss the job writes a new screen into it. The alternative is copying the 21 MB cache into the worktree.
3. **"Or fluent generations."** The gate refuses on KL alone; a fluency override is the researcher's ruling and has no switch here.
4. **Gate on both F cells.** Wikitext KL depends only on the circuit, so the two cells should agree; the gate requires both present and both under the bar.
5. **Pre-existing quirk (evaluate_circuit.py, not fixed):** the dry-run's "Screen cache:" listing says "nothing cached" because it builds the key without the model; the runtime lines, which include it, say `[cached]`.
6. **Real defaults checked (no flags, real `suites.json` and `suite_manifest.json`):** `submit_eval5.sh far sm` exits 3 naming the null F and the missing go-ahead, before any dry-run; `eval5_cmd.py gate sdr_coarse` finds the manifest's `F_hko__leaf` cells on `sdr` and `sdr_nopressure` and refuses both as missing (ticket 04's suite has not run).
7. **Resume steps:** set F in `suites.json` (ticket 03), run ticket 04's suites, then `python outputs/_launch_format_control/eval5_cmd.py gate <family>` and `bash outputs/_launch_format_control/submit_eval5.sh <family> <sm|lb> --dry` for all six, tick boxes 1 and 2, and wait for the researcher's go-ahead.

(Concerns 1 to 3 above are superseded by the fix round below.)

---

# Fix round 1 (2026-10-13): review findings I1-I3 and the orchestrator's rulings (committed by the orchestrator as 1c06455)

Source: `reports/06-eval5-suite-preparation-gated-review.md` (base db72d03) and the orchestrator's rulings: no writes into the main checkout (worktree-local cache copy); the A40 default stands; an explicit, recorded gate override. Nothing was submitted to Slurm. The work was test-first: the test file was rewritten first (47 red), then the code (75 green).

## What changed

| finding | change | covering tests |
| --- | --- | --- |
| **I1** caveats not verbatim | `GRADER_CAVEATS` now holds exact quotes, each with its source path: issue 01's title, its `_claim` mechanism sentence and its impact sentence; issue 02's title, its "GPT-4o codes it `D`" sentence and its "direction is conservative" sentence. Caveat 3 has `ticket: False` and is labelled "NO TICKET". It quotes item 3 of the project memory note `eval5-grader-fixes-pending.md` and the coarse-wave `eval5_sdr_coarse_nls0.3_nomb_lb/result_summary.md` sentence. The summary prints each as a blockquote followed by its source path, under "Quoted word for word (line breaks re-flowed)". | `test_grader_caveats_are_quoted_verbatim_from_their_sources` reads every source file and asserts each quote is in it (whitespace-normalised; it did not skip). `test_summary_prints_the_three_grader_caveats_and_the_random_row_note` checks each quote and source appears in the summary. |
| **I2** stale F cell | `gate(..., f_run=)` refuses when the manifest's planned `runs.F` is not the configured F, or is absent. It also refuses when a cell's `summary.json` `circuit_spec.operands.F` is not the configured F, naming both paths, or is unreadable ("cannot verify"). | `test_gate_refuses_a_cell_from_a_different_F_than_the_configured_one`, `test_gate_refuses_when_the_suite_was_planned_with_another_F`, `test_gate_refuses_a_cell_whose_F_cannot_be_verified` |
| **I3** plus ruling 1: cache and A40 not enforced, writes into main | `--benchmark-screen-cache` is now `<worktree>/outputs/_eval5_format_cache/screens`. `seed-cache` copies the group's A40 screens there before every dry run: real files, a symlinked source followed, never overwriting, temp file then rename, sidecar last. The directory carries its own `.gitignore`. After the dry-run, `cache-check` refuses when any group dataset is not `[cached]`, when the copy holds a non-A40 screen, or when the partition is not `gpuA40x4`. Only `--allow-rescreen "<reason>"` clears it, and the reason is printed and recorded. | `test_screens_come_from_the_worktree_local_copy`; `test_no_path_in_the_command_is_writable_under_the_main_checkout` (6 suites, sbatch argv included: only run directories may sit under the main checkout's outputs/); `test_seeding_copies_only_A40_screens_as_real_files`; `test_seeding_follows_a_symlinked_source_and_never_overwrites`; `test_group_datasets_match_what_the_evaluator_expands`; the four `test_cache_check_*` / `test_allow_rescreen_*` tests; the script tests `test_dry_prints_no_submit_line_when_a_screen_is_not_cached` and `test_submit_refuses_an_uncached_screen_unless_a_rescreen_is_allowed` |
| ruling 2: A40 default | Kept. The README and the script say "keep the screened items item-for-item comparable with the existing eval5_* suites; other partitions re-screen", and that the brief's "any partition" is for speed only. | `test_cache_check_refuses_a_non_A40_partition_or_copy` |
| ruling 3: explicit gate override | `--gate-override "<reason>"` clears only the KL bar. A missing cell, a missing KL, a stale F or a mismatched manifest are never overridable, and an empty reason is an error. The override and the gate numbers it overrode are printed and written to `eval5_record.json`. The README says how the researcher uses it. | `test_gate_override_clears_only_the_KL_bar_and_is_reported`, `test_refusal_when_the_gate_fails_names_the_number` (override part), `test_a_gate_override_is_recorded_with_its_reason` |
| record | The new `eval5_record.json` takes one event per dry run and submission, with arguments, cost, gate KLs and reasons, overrides and their reasons, cache reasons and job id. It replaces `eval5_jobs.txt`. | `test_dry_seeds_the_local_cache_and_prints_the_submit_line`, `test_submit_with_every_refusal_cleared_reaches_sbatch_once` |

Minor findings also fixed:
- **M1:** any exception reading a cell becomes a named "unreadable" refusal. Covered by `test_gate_refuses_a_malformed_cell_with_a_reason`.
- **M2:** script tests now cover a failing dry-run in submit mode (exit 5, no sbatch) and `--standin` without `--dry`.
- **M3:** an unreadable `benchmarks.json` or a second cell for a role is reported. Covered by `test_summary_reports_an_unreadable_or_duplicate_cell`.
- **M4:** the mean row averages only datasets every circuit has, and names the ones left out. Covered by `test_summary_reports_a_failed_dataset`.
- **M6:** `--standin` with F configured is refused. Covered by `test_a_stand_in_is_refused_once_F_is_configured`.
- **M8:** path overrides outside `--dry` exit 2 unless `EVAL5_ALLOW_PATH_OVERRIDES=1`. Covered by `test_submit_refuses_path_overrides_without_the_test_switch`.
- **M10:** a coarse run whose mask signature does not match the all-MLP operand is refused. Covered by `test_coarse_runs_must_match_the_all_mlp_operands_mask_signature`.
- **M12:** the cost is appended to the dry-run log and recorded.
- **M9 and M11:** documented in `README_eval5.md`.
- **M7:** documented; the ceiling-based default is kept.
- **M5:** not fixed, because it is ticket 05's file. Its docstring example should read `--eval5-dir outputs/eval5_format_far --eval5-dir outputs/eval5_format_far_lb`.

## Commands and output

Stand-in dry-runs, all six re-run through the new flow (mgnp, login node):

```
PYTHON=/u/swong2/.conda/envs/mgnp/bin/python bash outputs/_launch_format_control/submit_eval5.sh far sm --dry --standin
...
screen cache .../format-control/outputs/_eval5_format_cache/screens: copied 15, kept 0, skipped (not A40 or no .pt) 2 from .../Deception-Circuit/outputs/_screens
  TOTAL     1460.5 - 1774.3 min (3 cell(s))
  cost: 3 cell(s); judge calls (...): 4,671
        judge calls for uncached screens (at most): 0  (cached screens: 7 of 7)
dry run OK; no submit line:
  REFUSED: a stand-in suite (F := H) is plumbing only and is never submitted
  REFUSED: the F run directory is not configured (... runs.F is null: the Format Circuit has not landed)
  cleared: every screen is an NVIDIA A40 cache hit on gpuA40x4
recorded dry in .../outputs/_launch_format_control/eval5_record.json
```

All six pass with "cleared: every screen is an NVIDIA A40 cache hit on gpuA40x4": sm 7 of 7 cached, lb 3 of 3. The lb seed copied 9 screens; the later runs kept the copies. The two skipped sandbagging sidecars are the H200 screens. Cost and walltime are unchanged from the build phase.

**No write into the main checkout.** A listing of the main checkout's `outputs/_screens` (path, size, mtime; 52 files) taken before the six runs is identical after them. The only main-checkout paths in the six logs are the seven circuit run directories and the six read-only anchor suites the cost line cites.

Real defaults (no flags):
- `submit_eval5.sh far sm` exits 3, naming the null F and the missing go-ahead.
- `eval5_cmd.py gate sdr_coarse` exits 3 with "runs.F is null".
- `submit_eval5.sh far sm --config /tmp/x.json` exits 2: "--config may only be overridden with --dry".

## Tests

| env | ticket file | full suite | failing names |
| --- | --- | --- | --- |
| login base (py3.9) | 75 passed | 8 failed, 817 passed, 20 skipped | identical to the 8 baseline names |
| mgnp (py3.12) | 75 passed | 8 failed, 818 passed, 19 skipped | identical to the 8 baseline names |

`ruff check --line-length 120` is clean on the four Python files and `bash -n` passes on the script. No `core.*` dumps.

## Files changed in this round

`outputs/_launch_format_control/{eval5_cmd.py, submit_eval5.sh, README_eval5.md}`, the six regenerated `dryrun_eval5_standin/*.log`, the new `outputs/_launch_format_control/eval5_record.json`, `evaluation/eval5_format_summary.py`, `tests/test_format_control_eval5.py`. The local cache `outputs/_eval5_format_cache/` is git-ignored by its own `.gitignore` and must not be staged.

## Remaining limits

- Caveat 3 still has no ticket in `.scratch/eval5-grader-fixes/`. It is labelled so and cites the memory note; opening `issues/03-...` was outside this ticket's write area.
- The A40 check trusts the sidecars' `device` field and the evaluator's `[cached]` line, which matches every key field except the device. Since the copy holds A40 screens only, a `[cached]` line on it means an A40 hit.

---

# SDR resume (2026-10-15): real gate and real dry-runs

Nothing was submitted; `FORMAT_CONTROL_EVAL5_GO` was unset throughout. Inputs: commit 1bc5e58 with the merged `outputs/_suites/format-control-sdr{,-coarse}-nls0.3` and F set in `suites.json`.

## Gate

```
$ python outputs/_launch_format_control/eval5_cmd.py gate sdr
  cells/F/sdr/interchange: wikitext KL 1.342
  cells/F/sdr_nopressure/interchange: wikitext KL 1.342
REFUSED: F knockout wikitext KL 1.342 > 0.66 in cells/F/sdr/interchange (deceptive test set): fails the eval 2 gate. ...
REFUSED: F knockout wikitext KL 1.342 > 0.66 in cells/F/sdr_nopressure/interchange (nopressure test set): fails the eval 2 gate. ...
gate FAILED (.../outputs/_suites/format-control-sdr-nls0.3)          exit 3
$ python outputs/_launch_format_control/eval5_cmd.py gate sdr_coarse
  cells/F_hko__leaf/sdr/interchange: wikitext KL 0.279
  cells/F_hko__leaf/sdr_nopressure/interchange: wikitext KL 0.279
gate PASSED (.../outputs/_suites/format-control-sdr-coarse-nls0.3)   exit 0
```

Both match the orchestrator's expected numbers. Every cell's `summary.json` operand is the configured F, so the F-identity check passed.

For the fluency ruling, the SDR fine F knockout shows:
- wikitext KL 1.342, against a null median of 0.55;
- a perplexity ratio of 3.80;
- 2 of 3 knockout generations that degenerate into runs of `" ...`.

## Dry-runs (mgnp, login node)

| suite | result | judge calls | GPU h | --time |
| --- | --- | ---: | --- | --- |
| sdr_coarse sm | pass; submit line printed, not run | 4,671 | 24.3 - 29.6 | 44:30:00 |
| sdr_coarse lb | pass; submit line printed, not run | 4,050 | 9.2 - 12.5 | 19:00:00 |
| sdr sm | pass; **no submit line** (gate, KL 1.342) | 4,671 | 24.3 - 29.6 | |
| sdr lb | pass; **no submit line** (gate, KL 1.342) | 4,050 | 9.2 - 12.5 | |

All four logs show "cached screens: 7 of 7" (sm) or "3 of 3" (lb) and "cleared: every screen is an NVIDIA A40 cache hit on gpuA40x4". The main checkout's `_screens` listing is unchanged. Unit counts: coarse D_hko 8,832, H_hko 7,168, F_hko 8,704; fine D 11,251, H 8,732, F 11,882.

## Fixes found by the real runs (test-first)

1. **Operand signature from content, not name.** ticket 04's operand is now `outputs/_launch_format_control/allmlp_nomb`, and the name parser refused it. The first two coarse dry runs printed "cannot tell the all-MLP operand's signature from its name". `coarse_signature_reasons` now reads the operand's masks. Those masks are identical to the main checkout's `_allmlp_nomb`; only a `built_from` field is added. The test was updated red first, then turned green.
2. **Record race.** The coarse and fine runs appended to `eval5_record.json` at once, and the first coarse sm event was lost. The new test `test_concurrent_launchers_never_lose_a_record_event` (four processes, 25 events each) went red; `record_event` now flocks `<record>.lock`, and the test is green. Lustre `/projects` is mounted with `flock`, checked. The lost event is not reconstructed.

Tests: 76 in the ticket file pass in both envs. `ruff` is clean.

Process slip: I ran one read-only `git log -- suites.json` against the no-git rule. Nothing was modified.

**Full suite after these fixes:** base 8 failed, 844 passed, 20 skipped; mgnp 8 failed, 845 passed, 19 skipped. Both sets of failures are exactly the 8 baseline names. A first mgnp run also failed 47 tests in ticket 05's `tests/test_format_control_summary.py`. Ticket 05's `evaluation/format_control_summary.py` was rewritten at 07:17:32, during that run, which ended at 07:17:43. Re-run alone, that file passes 52 of 52, and the clean full mgnp run above followed.

---

# FAR resume and closing

### 2026-10-15, FAR resume and closing (nothing submitted; FORMAT_CONTROL_EVAL5_GO unset)

**FAR gate** (`eval5_cmd.py gate far`, exit 3): REFUSED, "F knockout wikitext KL 4.265 > 0.66" on `cells/F/far` and `cells/F/far_nopressure`. Both cells are the configured F's (`nls0.3_nopressure_noedge_261013-203424`). The NLS 0.4 side job under `_side_F04/` (KL 2.317) is outside the manifest's cells index and was not read. **FAR real dry-runs:** sm and lb both pass on the evaluator side, with every screen an A40 cache hit on the local copy, and neither prints a submit line. Fine units: D 5,436, H 10,935, F 12,986; grid 3 x 1. The main checkout's `_screens` listing is unchanged.

**Box 1 ticked:** all six real `--dry-run`s pass on the login node: far, sdr and sdr_coarse, each sm and lb.

#### Per-family gate (eval 2 wikitext KL of each knockout; the gate reads F)

| family | D KO KL | H KO KL | **F KO KL** | F ppl ratio | gate | eval 2 verdict (ticket 05) | EVAL 5 submit line |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| FAR fine | 0.327 | 2.784 | **4.265** | x69.7 | **refused** | (c) | none |
| SDR fine | 1.383 | 0.694 | **1.342** | x3.80 | **refused** | (c) | none |
| SDR coarse (heads-only `X - m`) | 0.364 | 0.275 | **0.279** | x1.31 | **passes** | (a) | printed for sm and lb, not run |

The F knockout generations differ sharply. FAR's are token salad (`riverHeaderCodeHeaderCode_Tis ... _marshall_marshall`). SDR fine's degenerate in 2 of 3 cases (`" ...  " ...`). Neither reads as fluent.

#### Cost of the one family that passed (sdr_coarse; real dry-runs; upper bounds)

| suite | judge calls | GPU h (dry-run floor - ceiling) | default --time | anchored wall time |
| --- | ---: | --- | --- | --- |
| `eval5_format_sdr_coarse` (sm) | 4,671 | 24.3 - 29.6 | 44:30:00 | about 10-12 h on an A40 (the one-cell coarse suite ran 3 h 51 min) |
| `eval5_format_sdr_coarse_lb` | 4,050 | 9.2 - 12.5 | 19:00:00 | a few hours |
| both | 8,721 | 33.5 - 42.1 | | |

All screens are cached, so no screen judge calls. The judge-call counts are upper bounds; the cache dedups repeats.

#### Recommended next decision for the researcher

1. **SDR coarse: launch, if you want the benchmark test of verdict (a).** It is the only family whose Format Circuit knockout is coherent (KL 0.279, below D's 0.364). Eval 2 already reads it as (a), "format explains it". EVAL 5 would check whether F's knockout also matches D's deception drop on sandbagging, MASK and Liars' Bench at equal or lower NLL cost, on the same screened items as `eval5_sdr_coarse_nls0.3_{nomb,honest_nomb}`. To launch, give the go-ahead in the session, record it here, and run `FORMAT_CONTROL_EVAL5_GO=1 bash outputs/_launch_format_control/submit_eval5.sh sdr_coarse sm` (and `lb`) on gpuA40x4.
2. **FAR and SDR fine: no EVAL 5; follow outcome (c).** The pre-registered response is to retrain the Format Circuit at a lower NLS, never to reinterpret. Two facts bear on that:
   - **Direction of the retrain.** On FAR, the NLS 0.4 retune side job gave KL 2.317, lower than 4.265 at 0.3 but still failing. Check which NLS direction shrinks the knockout's collateral before retraining.
   - **SDR fine's own D is above the bar.** D's knockout is 1.383, so the bar refuses D as well as F, and F is no less coherent than D. The spec gates F only. Whether "matched incoherence" justifies `--gate-override` is a judgement this ticket does not make; the generations argue against "fluent".
3. **No override is recommended.** Neither failing family's generations read as fluent, and the override exists only for that case.

Open: box 4 (ticket 05 consuming real EVAL 5 suites) needs a launched suite. Box 8 is the orchestrator's (build-phase review plus scoped re-review). Status stays `claimed`, since EVAL 5 itself waits on the researcher.

---

# Whole-branch review I2 fix (2026-10-15)

Finding: the F paths are worktree-absolute and the gate matched F by path alone. After a merge, a repointed `suites.json` would be refused as "stale", with advice that costs 24 jobs. If the worktree were removed, the pending sdr_coarse launch would refuse.

**(a) Code, test-first.** I added `same_run(a, b)` to `eval5_cmd.py`. The same path counts as the same run. Otherwise two runs are the same when their parsed `active_nodes.json` masks and `config.json` `deception_condition` are identical. The gate uses it for both identity checks: the manifest's planned F, and each cell's `summary.json` operand. Each refusal now names its reason:
- "different masks": advice is to re-run ticket 04's suite;
- "identical masks but a different deception condition";
- "cannot compare masks (...)": advice is to keep the format-control worktree.

New tests, all red then green:
- `test_gate_accepts_a_relocated_copy_of_the_configured_F`
- `test_gate_refuses_a_run_with_different_masks` (manifest plus both cells: 3 reasons)
- `test_gate_refuses_identical_masks_under_another_condition`
- `test_gate_says_to_keep_the_worktree_when_the_recorded_run_is_gone`

On real data, the coarse F run compared with a copy of its `active_nodes.json` and `config.json` in another directory gives `(True, 'identical masks and condition')`. Against the fine SDR F it gives "different masks". Against the incomplete coarse `...-203424` run, which has no `active_nodes.json`, it gives "cannot compare masks".

**(b) Docs.** A new "Keep this worktree until EVAL 5 has run" section in `README_eval5.md`, and a line in the ticket Comments. Repointing `suites.json` to the merged copies works only while the worktree's run directories still exist. `suites.json`'s paths were not changed.

**Checks:**
- `tests/test_format_control_eval5.py`: 80 passed in base and in mgnp.
- `ruff`: clean.
- `eval5_cmd.py gate sdr_coarse`: still PASSED, KL 0.279 on both cells, exit 0.
- `gate sdr` and `gate far`: still FAILED.

Nothing submitted.
