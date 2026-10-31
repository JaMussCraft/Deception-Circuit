# Ticket 06 review: EVAL 5 suite preparation (gated), build phase

Reviewer: independent review agent, 2026-10-13. Read-only.
Scope: base f20341a, head db72d03 (one commit, 12 new files), worktree
`Deception-Circuit/.claude/worktrees/format-control`.
**This is the build-phase review.** The real-F `--dry-run`s and the gate run on real
ticket 04 KL numbers are out of scope, because F is null for all three families in
`suites.json` and ticket 04's cells do not exist yet. The stand-in (F := H) dry-runs
are in scope.

What I checked directly:
- the diff in full;
- the six stand-in logs;
- `eval5_args.sh` in the main checkout;
- the old coarse launcher `outputs/llama-8b-instruct_sdr_coarse/_launch/submit_eval5.sh`;
- `scripts/evaluate_circuit.sbatch`;
- `evaluation/screen_cache.py`, the key and the dry-run `[cached]` logic;
- `evaluation/format_control_summary.py`, `load_eval5`;
- the worktree's `suite_manifest.json` and `suites.json`;
- a real `knockout.json` and a real coarse `benchmarks.json`;
- the eval5-grader-fixes spec and issues.

I re-ran `tests/test_format_control_eval5.py` in the base env and got 47 passed.

## Spec compliance

| requirement | verdict | evidence |
| --- | --- | --- |
| One `evaluate_circuit.py` invocation binds D, H and F | ✅ | `eval5_cmd.py:132-158`. Every log shows "CELL GRID (3 circuits x 1 tasks)". `--task-from <D run>` is needed and correct: without it the evaluator builds a 3 x 3 grid. |
| Coarse uses three `c - m` heads-only expressions against `_allmlp_nomb` | ✅ | `eval5_cmd.py:146-153` matches the old coarse recipe: `--compose-granularity leaf`, with `--expr` cells only. `sdr_coarse_sm.log` shows `D_hko__leaf` at 8,832 fine units, `H_hko__leaf` and `F_hko__leaf` at 7,168, and `m=…/_allmlp_nomb`. |
| Settings are exactly those of `eval5_args.sh` | ✅ | `eval5_cmd.py:95-97`, checked against `outputs/_eval5_launch/eval5_args.sh`: interchange, `--benchmarks <group>`, n 50, 6 randoms, budget 600. The groups and the `eval5_format_<family>{,_lb}` outputs match. |
| Two added flags | ✅ | The screen cache path is not in the key. `--benchmark-repo-root` equals the main checkout's default root, and the key hashes rubric bytes, not the path (`screen_cache.py` "NOT keyed"). |
| `--dry` prints the command and runs `--dry-run` | ✅ | `submit_eval5.sh:66-79`. |
| Stand-in dry-runs pass for all six combinations | ✅ | Each log has the full argv header, real evaluator banners, "Nothing was written" and no Traceback. F's unit count equals H's in every log, as F := H requires. Six of six. |
| Real-F dry-runs | out of scope | Box 1 stays open. |
| Nothing is submitted, and no build-phase path reaches `sbatch` | ✅ | Details below this table. |
| Pre-flight gate reads F's knockout wikitext KL, refuses above 0.66 naming the number, and refuses a missing cell | ✅ (⚠️ see I2) | `eval5_cmd.py:172-232`. NaN and inf refuse through `not kl <= threshold` (`:224`). A suite absent from the manifest gives `{}`, so both conditions refuse. The delta labels `F_minus_D__leaf` and `F_minus_D_hko__leaf` map to no role. Coarse correctly picks `F_hko__leaf` (`roles: ["knockout"]`), not atomic `F` (`roles: ["faithfulness"]`). Tests cover pass, fail, missing, no-KL, both fields and coarse. The gate does not check that the cell belongs to the configured F (I2). |
| `result_summary.md` writer for three circuits | ✅ (⚠️ see I1) | `eval5_format_summary.py:230-364`. Per dataset it gives full and D/H/F knockout and random-mean rows, dec/hon/unp, `ref_nll`, `distinct_n`, Δ and null percentile. It also prints the random-rows note and the caveat counters. Tested on a three-circuit fixture, fine and coarse. |
| The three grader caveats, verbatim | ⚠️ | They are accurate paraphrases, not verbatim, and caveat 3 has no ticket (I1). |
| Ticket 05 consumes the directory through `--eval5-dir` with no reader change | ✅ | See the ticket 05 paragraph below. |
| "One spec": one screen, one judge cache, identical settings | ✅ (⚠️ see I3) | Within a suite this holds by construction: one process, the `Session.screen_for` memo, and one `judge_cache.jsonl` in the output dir. Reuse of the main checkout's A40 screens is read-only on a hit. A hit requires every key field except the device to match, and the dry-run's `[cached]` lines show that held at db72d03. Nothing enforces it at submit time (I3). |
| Cost estimate per suite, labelled stand-in, in Comments | ✅ | 4,671 / 4,050 judge calls and 24.3-29.6 / 9.2-12.5 GPU h. The 1,557 × 3 = 4,671 cross-check against the one-cell coarse suite holds: 9 configs × 173 items per cell. The cost lines go to stdout only, not into the logs. |
| Tests | ✅ | The command generator is a pure function, the gate refusal is covered, and the summary writer runs on a three-circuit fixture. 47 tests, each with real assertions. The script tests shadow `sbatch` with a stub and assert the shadowing. |
| Both suites in both envs, failure names against baseline | ✅ (reported) | The implementer reports the 8 baseline names in both envs. The orchestrator ran 147 passed on the four files. I confirmed 47 passed in base. |

**No submission path in the build phase.** The `sbatch` string is built only at `eval5_cmd.py:303`, and it is executed only at `submit_eval5.sh:99`. That line is reached only after three things:
- `check` passes without `--dry` (`:62`, `|| exit 3`), which needs F configured, the gate passed and `FORMAT_CONTROL_EVAL5_GO=1`;
- the dry-run passes (`:74-76`);
- `eval5_cmd.py sbatch` re-parses the log as passing (`:82-83`).

`--standin` always refuses, dry or not. All three `runs.F` are null today, so even with GO=1 the script exits 3 at line 62. No new Python file uses `subprocess`, `os.system` or `Popen`. No `eval5_jobs.txt` exists, and no `outputs/eval5_format*` directory exists.

**Ticket 05's reader.** `evaluation/format_control_summary.py:280-308`, `_role_of` plus `load_eval5`, globs `cells/*/*/*/benchmarks.json`. It strips `__(leaf|head)` and then `_hko`, so `D`/`H`/`F` and `D_hko__leaf`/… map to roles, and the coarse operand `m` is never a cell. It reads `configs.{full,knockout}.rates.deceptive`, `null.deceptive.p5/p50` and `coherence.ref_nll/distinct_n`. All of these are present in the real `eval5_sdr_coarse_nls0.3_nomb_lb/cells/hko__leaf/.../benchmarks.json`. The sm and lb dataset names are disjoint, so merging two `--eval5-dir`s by `setdefault` is safe. `write_format_control_summary.py:40` takes `--eval5-dir` with `action="append"`. The claim holds.

## Strengths

- The refusals are ordered sensibly, every one names its reason, and the gate fails closed. A malformed cell can only produce a refusal or a crash, never a pass.
- The script tests run the real `submit_eval5.sh` end to end, using a stub `sbatch` and a stub evaluator. The happy path is asserted to call `sbatch` exactly once, and each refusal is asserted to call it zero times.
- `--task-from` was found and documented. Without it the run silently becomes nine cells.
- The cost estimate is anchored on a real suite's post-screen counts and cross-checked against that suite's real judge count.
- The caveat counters reproduce `_verdict`'s exact case-sensitive rule, and they were checked against rows recorded in earlier summaries.
- The summary reports missing cells, failed datasets and full rows that differ between cells, rather than raising on them.

## Issues

### Critical

None.

### Important

**I1. The grader caveats are not verbatim, the third has no ticket, and the test cannot detect drift.**
- **Where:** `evaluation/eval5_format_summary.py:41-70`, `README_eval5.md:127`, `tests/test_format_control_eval5.py:586-593`.
- **What:** `GRADER_CAVEATS` condenses issues 01 and 02. For example, the source says "Δ dec is unchanged; `dec/parsed` and the honest fraction are slightly inflated for the knockout", and the constant says "the deception rate is unchanged; dec/parsed and the honest fraction are slightly inflated". Yet the docstring (`:41`) and the README (`:127`) call them "verbatim". Caveat 3, the Liars' Bench "correct" guard, cites a result summary with "no ticket yet". The folder's own `spec.md` still says "Two grader behaviours", while the format-control spec says "three known issues" live there. The test asserts that each constant appears in the rendered output, which is true by construction; it never reads the ticket files.
- **Why it matters:** the binding constraint is verbatim caveats from the tickets. A reader of a result summary cannot tell the printed text was edited, and nothing will flag drift if a ticket changes.
- **Fix:** quote each ticket's Observed and Impact sentences exactly, or drop the "verbatim" claim and say "summarised from". Open `eval5-grader-fixes/issues/03-lb-correct-guard.md` from the 2026-09-23 coarse-wave summary text (`eval5_sdr_coarse_nls0.3_nomb_lb/result_summary.md:58`) and point caveat 3 at it. Optionally, add a test that reads the three issue files and checks the quoted sentences appear in the summary.

**I2. The gate does not check that the knockout cell it reads belongs to the F now configured.**
- **Where:** `outputs/_launch_format_control/eval5_cmd.py:192-232` and `:278-284`.
- **What:** `refusals` takes F from `suites.json` but gates on whatever `knockout.json` sits at the manifest's `path` under `outputs/_suites/<suite>`. Neither the manifest suite's `runs.F` nor the cell's recorded operand is compared with the configured `runs.F`.
- **Why it matters:** this situation is realistic. Two SDR `nopressure` runs already sit untracked in the worktree (`nls0.3_nopressure_noedge_261013-203424` and `-204850`). If ticket 04's suite ran with one F and `suites.json` later names the other, the gate passes or fails on the wrong circuit's KL. The submit line would then carry an F that was never gated.
- **Fix:** refuse unless `manifest_suite["runs"]["F"] == config runs.F`. Better still, also check the F operand recorded in the suite's `suite.json` `circuits[].operands`, or in the cell's shard `suite.json`, against `runs.F`. Name both paths in the refusal and add a stale-cell test.

**I3. The cached-screen and A40 condition behind "same items as the existing suites" is documented but not enforced.**
- **Where:** `submit_eval5.sh:34` and `:42`, `eval5_cmd.py:106`, `render_cost`.
- **What:** `--partition` is a free override. `cost` prints "cached screens: N of M", but nothing refuses a submit line when N < M or when the partition is not an A40 queue.
- **Why it matters:** a miss silently re-screens. A miss can come from another GPU, from a later edit to `evaluation/benchmarks/*.py` or `base.py` on this branch (the key hashes adapter source), or from a different torch or transformers version in `mgnp`. The re-screen then writes pickles into the main checkout's `outputs/_screens` from a worktree job, and the items stop matching `eval5_far`, `eval5_sdr`, `eval5_sdr_h03` and `eval5_sdr_coarse_*`. D, H and F would still share one screen with each other, because the in-process memo guarantees that, so the ticket's "one spec" survives. What breaks is the prior-wave comparability the README promises, plus the cross-tree write. The spec allows "any partition", so whether to narrow it is the researcher's call. If a re-screen is allowed, it should be a deliberate choice rather than a fall-through.
- **Fix:**
  - Refuse to print or submit when the dry-run log shows any dataset without `[cached]` or the partition is not an A40 partition.
  - Add an `--allow-rescreen` flag that overrides this and points `--benchmark-screen-cache` at a worktree-local directory.
  - Record the decision in the ticket.

### Minor

- **M1. Some malformed cells refuse without a reason.** `eval5_cmd.py:211-217` catches only `OSError` and `ValueError`. A `knockout.json` that parses to a non-dict, or whose KL is a list, raises `AttributeError` or `TypeError`, which `main()` does not catch (`:505`). The script still refuses: exit 1 becomes `|| exit 3`, and in `--dry` the result is "no submit line". But the `--dry` refusal list is empty and the traceback goes to stderr. Catch `Exception` in the read path and name the cell.
- **M2. Script paths without a test.** No script-level test covers a failing dry-run in submit mode (exit 5, no `sbatch`). None covers `--standin` without `--dry` with GO=1 either; that case is covered only at the `refusals()` unit level.
- **M3. Silent ambiguity in `load_suite`.** At `eval5_format_summary.py:108-111`, a corrupt or unreadable `benchmarks.json` becomes a present cell with no datasets, so it is not in `missing`. A second label mapping to the same role is dropped silently. Report both.
- **M4. The headline mean row can average different datasets.** At `eval5_format_summary.py:288-295`, the `full` mean covers every dataset, but a role's mean skips its failed datasets. With a failure the means are not comparable; restrict them to the common datasets or mark them.
- **M5. Ticket 05's docstring names the wrong directories.** `write_format_control_summary.py:19-20` uses `--eval5-dir outputs/_suites/eval5-format-control-far-sm`, but ticket 06 writes `outputs/eval5_format_far{,_lb}`. Fix the example; this is ticket 05's file.
- **M6. `--standin` with a configured F is mislabelled.** It keeps the real F but still prints "STAND-IN: F := H" and logs under `dryrun_eval5_standin/` (`eval5_cmd.py:258`, `submit_eval5.sh:68`).
- **M7. The walltime is far above the anchored runtime.** The default `--time` of 44:30:00 for sm is about four times the implementer's own anchored estimate of 10-12 h, which hurts backfill. Consider the anchor × 1.5 when submitting. The `--time` override exists.
- **M8. Overrides work on the real submit path.** `--config`, `--manifest` and `--suite-root` are accepted without `--dry`, so a fixture manifest can clear the gate. The tests need them, but consider allowing them only with `--dry` or behind a test env var.
- **M9. The go-ahead variable is a speed bump, not proof of consent.** Any agent can export `FORMAT_CONTROL_EVAL5_GO=1`. The researcher's go-ahead still has to be obtained in the session and recorded in the ticket before anyone sets it.
- **M10. The coarse F's mask signature is not checked.** The old coarse launcher derived `_allmlp_{mb,nomb}` from the run's `active_nodes.json`, but the new one trusts `suites.json allmlp`. When F lands, confirm it is a `nomb` run, or derive and check the signature as the old launcher did.
- **M11. The gate reads two cells where one would do.** It reads F's knockout on the deceptive and `nopressure` sets. Wikitext KL depends only on the circuit: the real `ser/ser` and `ser/far` cells have the identical 0.98936. Requiring both is redundant but harmless.
- **M12. The cost lines are not saved.** They print to stdout only. Appending the `cost` output to the dry-run log would keep the estimate next to the evidence.

## Assessment

**Needs fixes.**
- **Spec:** compliant for the build phase, except the caveat form (I1). Boxes 1, 2 and 4 stay open by scope, pending real F, ticket 04's cells and real suites.
- **Quality:** good. The submit path is safe and fails closed, and the tests are meaningful.
- **Before the gated run:** fix I1, I2 and I3. I2 and I3 decide whether the gate and the comparability claim hold when the real F lands.

## Re-review of fix round 1 (db72d03..1c06455)

Read-only review of the fix diff, the worktree code at 1c06455, the evaluator's screen-cache and provenance code, the regenerated stand-in logs and the local cache copy. I ran `tests/test_format_control_eval5.py` in the login base env: 75 passed, none skipped. Nothing was submitted and nothing in the worktree was modified.

### Finding Verdicts

**I1: ADDRESSED.**
- `evaluation/eval5_format_summary.py:53-100`: each caveat is now a list of quotes, and each quote names its source file. Issues 01 and 02 supply the title, the mechanism sentence and the impact sentence. The earlier paraphrase, which said "deception rate is unchanged", now reads "Δ dec is unchanged ... for the knockout".
- `:87-99`: caveat 3 carries `ticket: False` and the label "NO TICKET: recorded only in the project memory note (item 3) and in the coarse-wave summary". It quotes both sources.
- `tests/test_format_control_eval5.py:930-945`: the test opens every source file and asserts that each whitespace-normalised quote is a substring. All three source files exist on this machine, so every quote is checked. The run shows no skip.
- README `:177` now says "quoted word for word (line breaks re-flowed)". The claim and the code agree.
- No ticket 03 was opened in `.scratch/eval5-grader-fixes/`. The ruling asked only that its source be labelled, so this does not block.

**I2: ADDRESSED.**
- `outputs/_launch_format_control/eval5_cmd.py:349-356`: the gate refuses when the manifest's planned `runs.F` is absent or differs from the configured F.
- `:379-391`: it also refuses when the cell's own `summary.json` `circuit_spec.operands.F` differs from the configured F or cannot be read. The refusal names both paths.
- I checked that the operand really exists. `evaluation/suite.py:214` writes `spec.provenance()`, and for an atomic spec `evaluation/circuits.py:219` sets `operands={name: bindings[name]}`. Ticket 04 binds the role names (`fc_cells.py:189-190`; the manifest cells are labelled `F`), so an atomic cell records `operands.F`. The coarse `F_hko__leaf` records `{F, m}` (`circuits.py:233`).
- A stale cell cannot pass. Re-planning the manifest alone fails the cell-operand check. A stale manifest alone fails the planned-F check.
- The gate fails closed when it cannot verify the operand. Only the KL bar yields to `--gate-override` (`:393-397`).
- Covered by three tests: a stale cell, the manifest planned with another F, and an F that cannot be verified.

**I3: ADDRESSED.**
- `eval5_cmd.py:93-94, 205`: `--benchmark-screen-cache` points at `<worktree>/outputs/_eval5_format_cache/screens`. The flag name matches `evaluate_circuit.py:243`, and `evaluate_circuit.py:649` and `evaluation/screen_cache.py:357` read it.
- The stand-in log `sdr_coarse_sm.log:139` prints this worktree path as the screen cache, and all seven datasets show `[cached]`.
- `seed_screen_cache` (`:220-262`) uses `shutil.copyfile`, which follows a symlinked source and writes a regular file. It writes to a temp file and renames it, and it never overwrites. `find outputs/_eval5_format_cache -type l` returns 0. The directory's `.gitignore` holds `*`, and `git check-ignore` confirms it.
- `cache_check` (`:265-293`) refuses three cases: any group dataset not `[cached]`, any non-A40 sidecar in the copy, and any partition outside `gpuA40x4`. Only `--allow-rescreen "<reason>"` clears it, and the reason is printed and recorded.
- `submit_eval5.sh:131` runs `cache-check` before `sbatch` at `:134`. In `--dry` mode it gates the printed submit line at `:114-116`.
- `test_no_path_in_the_command_is_writable_under_the_main_checkout` (`tests/...:115-129`) builds the real `sbatch_cmd` argv for all six suites. It resolves every token and every `=` piece against the worktree, and allows only the circuit run directories under the main checkout's `outputs/`. It inspects the generated command.
- I also checked writes the command does not name. The invocation binds several circuits with `--output-dir`, so it is not legacy (`evaluation/suite.py:76-77`). Cells and `judge_cache.jsonl` (`benchmark_eval.py:1417-1430`) therefore go under the worktree output dir. `scripts/evaluate_circuit.sbatch` runs from `SLURM_SUBMIT_DIR`, which is the worktree because the script cds there at `:38`.

**Ruling A: ADDRESSED.**
- The README (`README_eval5.md:65-69`) and the script header (`submit_eval5.sh:35-36`) document the `gpuA40x4` default as the item-for-item comparability reason. They say the brief's "any partition" is for speed only.
- `eval5_cmd.py:133-137` keeps the default.

**Ruling B: ADDRESSED.**
- `gate(..., override=)` moves only the KL-bar failures to `overridden` (`:393-397`).
- A missing cell, a missing KL, a stale F, an unverifiable F and a manifest mismatch stay refusals.
- An empty reason raises (`:149-152`), and `main` turns that into exit 3.
- The `check` command prints the override (`:726-731`). `record` writes `gate_override` and the `gate_overridden` messages to `eval5_record.json` (`:803-804`).
- The README documents usage at `:114, :133`.

**Ruling C: ADDRESSED, with one residual noted under Out-of-Scope.**
- No argument or derived path in the command writes under the main checkout.
- The seed reads from the main checkout's `_screens` and writes only to the copy. The implementer's before-and-after listing of the main `_screens` was identical.
- Path overrides outside `--dry` exit 2 unless `EVAL5_ALLOW_PATH_OVERRIDES=1` (`submit_eval5.sh:67-70`).

**Highest-stakes checks.**
1. No submit path skips a refusal. The submit order is: `check` (`:81`), then the `args` refusal of a null F (`:86`), the dry-run (`:95`, exit 5 on failure), the sbatch line (`:103`), and `cache-check` (`:131`), before `sbatch` (`:134`). `check` covers a null F, the gate including F identity, and `FORMAT_CONTROL_EVAL5_GO=1` (`eval5_cmd.py:465-480`). A stand-in is always refused, and a stand-in with F configured raises (`:417-420`).
2. A stale cell cannot satisfy the F-identity check, as shown under I2.
3. The cache is a real copy, and the evaluator is pointed at it, as shown under I3.
4. The main-checkout test inspects the generated sbatch argv, as shown under I3.

### New Breakage

Critical: none. Important: none.

Minor:
- **N1.** `tests/test_format_control_eval5.py:937-939` skips any single quote whose source file is missing, as long as another quote was checked. A renamed memory note or coarse summary would leave its caveat-3 quote silently unverified. Assert that each source exists, and skip only when the whole `.scratch` tree is absent.
- **N2.** `eval5_cmd.py:637` writes the record through a fixed `path + ".tmp"`. Two launchers recording at the same moment can clobber each other's event. `seed_screen_cache` already uses a per-PID temp name; reuse that here.
- **N3.** Caveat 3's first source is a file in the user's home `.claude` memory (`eval5_format_summary.py:41-42`). Every result summary will print that machine-local path as a source. This is acceptable as a label, but opening `eval5-grader-fixes/issues/03-...` would give the caveat a durable source.

### Out-of-Scope Observations (non-blocking)

- **The A40 check is enforced only at dry-run time.** A login-node `--dry-run` cannot include the device in its key. Its `[cached]` line therefore means a match on every field except the device (`screen_cache.cached_on_devices`), and the copy holds only A40 screens. The key also includes the torch and transformers versions, so a dry-run under another interpreter fails closed. If the job's runtime lookup still misses, for example because the mgnp env is upgraded between the dry-run and the job, nothing refuses. The job re-screens into the worktree copy: no main-checkout write, but the items silently diverge. A runtime guard would need an evaluator flag such as "require a screen-cache hit", which is outside this ticket. When the real suites land, the researcher can confirm hits from the job log's screen lines.
- M5 is still pending in ticket 05's file. The implementer notes it.

### Verdict

**Fix round passes.** I1, I2, I3 and rulings A, B and C are all addressed. The fix introduces no Critical or Important breakage. N1-N3 are Minor and optional. The ticket stays gated on the real F, ticket 04's suite and the researcher's go-ahead.
