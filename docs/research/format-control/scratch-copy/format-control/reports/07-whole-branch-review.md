# 07 — Whole-branch review: format-control (5b61031..e47daf3, 33 commits)

Reviewer: review-final (Opus 5.5), 2026-10-15. Read-only; suites not re-run (orchestrator's
e47daf3 runs: base 8 failed / 850 passed / 20 skipped, mgnp 8 / 851 / 19, baseline names only).

Read in three passes: (1) spec, tickets 01-06, ledger, per-ticket reviews; (2) the package's
code/test/doc diff, with the launchers and shared files read in full at e47daf3; (3) the three
`evaluation_summary.md` / `decision.json` outputs, the real EVAL 5 dry-run logs, and the data.
Extra evidence gathered: `find -newermt 2026-10-13` on all six main-checkout D/H run dirs and
`outputs/_screens` (empty); instance-id overlap of `<task>_nopressure` test sets with the
`<task>` and `<task>_honest` test sets (FAR F∩H 492/500, F∩D 8; SDR F∩D 520, F∩H 0).

## Strengths

- **Every ticket's deliverable is present.** Clause-surgery helper shared by the builder and
  `evaluation/variants.py`; `nopressure` registered in `tasks/deception.py`, `train.py`,
  `run_io.py` slugs and the evaluator's `--task-from`; three F runs with `size_check.json`; three
  merged suites (21/21/24 cells, 0 missing); the writer with `decision.json`; the gated EVAL 5
  launcher with six real dry-runs. Ticket 06's one open box (writer consumes `--eval5-dir`) can
  only close after EVAL 5 runs.
- **Safety invariant 1 holds and is test-pinned at the script level.** `submit_eval5.sh` reaches
  `sbatch` only after `check` (F set, gate incl. F identity, coarse mask signature,
  `FORMAT_CONTROL_EVAL5_GO=1`), a passing dry-run (exit 5 otherwise), the `sbatch` builder's own
  dry-run check, and `cache-check` (A40 hits or a recorded `--allow-rescreen`). Path overrides
  are refused outside `--dry` unless `EVAL5_ALLOW_PATH_OVERRIDES=1`. The harness in
  `tests/test_format_control_eval5.py:671-830` shadows `sbatch` with a recording stub and asserts
  zero calls for every refusal and exactly one call when all clear. The bar is written
  `not kl <= threshold`, so a NaN KL refuses.
- **Invariant 2 holds.** The only main-checkout paths are read-only inputs (D/H run dirs, the
  screen source, anchor suites); the screen cache is a file copy into a git-ignored worktree
  directory. No file in the six D/H run dirs or `outputs/_screens` changed since 2026-10-13.
- **Invariant 3 holds.** `submit_train.sh:45-68` is an allowlist (`gpuA40x4 gpuH200x8`) checked
  per comma token before any submission; `--only` is validated before the loop.
- **Invariant 4 holds.** `deception_records` (`evaluation/variants.py:125-171`) derives both
  variants by `remove_clause` / `replace_clause` on the stored strings; the only remaining
  `rebuild_prompt` is the STD path. Mixed nopressure/pressured test sets are refused.
- **Invariant 5 holds.** `decide` (`evaluation/format_control_summary.py:440-565`): F drop
  `>= 0.8 x D` (1e-9 tolerance, boundary tested both sides), outside null strictly `ko < p5`,
  (c) at `kl > 0.66`. The (c)-before-(a) order and the 0.5 distinct-2 fraction carry the
  "not pre-registered; ... researcher to confirm" label in the rule order, the gate line and
  `decisions_taken`.
- **Backward compatibility is good.** The `deceptive`/`honest` paths of `dataset_dir`, the run
  slug and the CLI are unchanged; the modified tests in `tests/test_deception_tasks.py` were
  widened (parametrised over three conditions, exact slug prefixes), not weakened, and an unknown
  condition now raises instead of loading an unbuilt directory.
- **Honest reporting.** Saturation, non-discriminating rows (1 binomial SE, not loosened after
  seeing the coarse result), the FAR retune failure, the both-fail and oversized-F remedy
  sentences (physically correct: higher NLS gives the smaller circuit) and the null sampling unit
  are all printed from data. No test asserts nothing (AST scan of the nine changed test files).

## Declined to judge

- The `FORMAT_CONTROL_EVAL5_GO` variable as a trust boundary: it is a speed bump, not proof of
  consent (review-06 M9); the consent itself is a process matter outside the code.
- `EVAL5_ALLOW_PATH_OVERRIDES=1` as a test affordance: an explicit second switch; acceptable.
- SER deferral, the three grader caveats, mean/zero ablation: out of scope by the spec.
- The FAR designation-following / polarity finding and the "FAR F is a second honest circuit"
  reading: data findings, not code; recorded in the ledger for the researcher.
- Carrying the NLS 0.3 FAR F after the 0.4 retune failed the in-run gate: a recorded ruling with
  its cost; the summary states it.
- The 1 SE non-discriminating criterion and the `--honest-rows variants` default: recorded
  rulings, labelled in the output, reversible by a flag.
- On FAR both D-data honest-answer drops are negative (knockouts make the model more honest), so
  "F <= D" compares honesty gains and fails by 0.002; (c) pre-empts it and the SE caveat covers
  it. The rule is the spec's; no change proposed.
- Walltime sizing (`--time` 44:30:00 vs an anchored ~10-12 h): a scheduling preference with an
  override; jobs are not capped.
- The coarse leaf-composition deviation and "delta cells eval 2 only": recorded rulings,
  documented in `suites.json`, the README and the summary.

## Issues

### Critical

None.

### Important

**I1. With EVAL 5 present the rule still reads the saturated eval 2 deception drop and nulls,
while the summary says eval 5 is the discriminating comparison; the choice is not recorded in the
output.**
- *Where:* `evaluation/format_control_summary.py:744-748` (sides take `deception_drop`,
  `knockout_acc`, `null_p5`, `outside_null` from the eval 2 knockout regardless of
  `eval5_dirs`), `:103-128` (`DECISIONS_TAKEN` records the eval 5 switch for collateral and
  distinct-2 only), `:969-973` (caveat: "eval 5 is the discriminating comparison").
- *What:* `load_eval5` reads per-dataset benchmark deception rates and null p5, but they are only
  rendered; no rule condition uses them. On `format-control-sdr-coarse-nls0.3`, the only family
  cleared for EVAL 5, the eval 2 deception-drop condition is trivially satisfied (D 0.998, F
  1.000, both saturated) and will stay so after `--eval5-dir` is added. The verdict line meanwhile
  prints the spec sentence "The benchmark effect is format or answer machinery" on eval 2 alone.
- *Why:* the spec's Further Notes make eval 2's knockout rows the rule's rows, so keeping them is
  defensible. But a researcher who launches EVAL 5 because the summary says it discriminates will
  get a verdict whose deception condition ignores it, and `decision.json` does not say so. Ticket
  05 Comments item 5 records the choice; the output does not.
- *Fix:* (1) add a `decisions_taken["deception_drop"]` entry: "deception drop and nulls are eval
  2's even with eval 5 [not pre-registered; researcher to confirm]"; (2) reword the saturation
  caveat to say what EVAL 5 changes in the rule (collateral and distinct-2) and what it does not;
  (3) when `--eval5-dir` is given, print an informational "eval 5 deception drop" row in the
  decision block: per shared dataset and mean, full minus knockout deception rate for D and F,
  with each knockout's null p5 or percentile. Whether that row becomes rule-bearing is the
  researcher's call. One test for the new row.

**I2. The F run directories are worktree-absolute, and the EVAL 5 gate matches F by path, so the
pending EVAL 5 launch breaks after merge and worktree removal.**
- *Where:* `outputs/_launch_format_control/suites.json:23,32,41` (F), `allmlp`, `_side_jobs`;
  the committed suite cells' `summary.json` operands;
  `outputs/_launch_format_control/eval5_cmd.py:155-159` (`_same_path`), `:353`, `:388`.
- *What:* after the branch merges, the F runs exist in the main checkout at
  `outputs/llama-8b-instruct_*/...nopressure...`, but every config and cell names
  `.claude/worktrees/format-control/...`. If the worktree is removed, the launcher refuses
  (fail-safe): for `sdr_coarse` at the mask-signature check ("cannot read
  .../active_nodes.json", exit 3), for the fine families at the dry-run (exit 5). If someone repoints `suites.json` to the merged copies, the gate refuses
  every F cell as "a stale cell: re-run ticket 04's suite", though the masks are byte-identical;
  that advice costs 24 coarse jobs. Nothing in `README_eval5.md` or ticket 06 says to keep the
  worktree.
- *Why:* the researcher's next decision is the `sdr_coarse` launch, and the branch is up for
  merge now. Ticket 03 review Minor 1 flagged the same paths in `size_check.json`.
- *Fix (either):* (a) state in `README_eval5.md` and ticket 06 that EVAL 5 must be launched and
  summarised from this worktree, which is kept until then; or (b) let `_same_path` also accept
  two run dirs whose `active_nodes.json` (and `config.json` `deception_condition`) hash
  identically, and make the refusal say "different masks" rather than "stale". (a) is one
  paragraph; (b) is a few lines plus a test.

### Minor

1. **Review-06 M5, still open: the CLI docstring names directories that never exist.**
   `write_format_control_summary.py:19-20` shows `outputs/_suites/eval5-format-control-far-{sm,lb}`;
   the launcher writes `outputs/eval5_format_far` and `outputs/eval5_format_far_lb`
   (`eval5_cmd.py:173-175`, `README_eval5.md:209`). This is the command the researcher copies
   after EVAL 5. Fix the two lines. **Promoted to must-fix.**
2. **FAR's F-data column is instance-paired with the H column, and the summary says otherwise.**
   `evaluation/format_control_summary.py:1016-1025` labels H data "unpaired (disjoint
   instances)" unconditionally. For FAR, 492 of 500 F test instances are `far_honest` test
   instances, so the H and F columns are paired. `source_counts` gives only how many records are
   honest-split, not whether they are the same ids, so either count ids against
   `<task>_honest/test` in the writer or have the builder record which honest split each fallback
   came from, then say "paired with F data" where it holds. Informational rows
   only; the rule is unaffected.
3. **The KL gate and null boundaries are correct but unpinned.** No test puts F's KL at exactly
   0.66 (must pass) or a knockout accuracy exactly at p5 (must be inside the null). Two tests in
   `tests/test_format_control_summary.py`, mirroring the 80 percent boundary tests at :490-516.
4. **Ticket text lags the state.** Ticket 03:97 and ticket 04:184 still say "Status stays
   `claimed`" under a `resolved` header; ticket 06 is `resolved` with one box open (fine, but say
   it closes after EVAL 5).
5. **Untracked leftovers in the worktree.** `outputs/llama-8b-instruct_sdr/nls0.3_nopressure_noedge_261013-203424/`
   and its `sdr_coarse` twin (the OOM runs), three `_shards/` trees and `eval5_record.json.lock`.
   Delete the OOM dirs and ignore `_shards/` and `*.lock` before merge so no `git add -A` picks
   them up.
6. **The (a) verdict line carries the benchmark sentence with no eval 5 data.** Covered by the I1
   fix; at minimum print the saturation caveat directly under the verdict, not in the Caveats
   section at line 100 of the summary.

## Deferred-minor triage

**Must fix before merge**
- Ticket 06 M5 / ledger line 94: wrong `--eval5-dir` paths in `write_format_control_summary.py:19-20`
  (Minor 1 above).
- Ticket 03 review Minor 1 (absolute worktree paths): resolved together with I2, by either fix.

**Already resolved on the branch (verified)**
- Ticket 03: `--only` validated mid-loop (now `submit_train.sh:69-74`).
- Ticket 06: cost lines not saved (now `tee -a` into the log); path overrides on the submit path
  (now refused without `--dry` or the test switch); coarse F mask signature unchecked (now
  `coarse_signature_reasons`); no script test of a failing dry-run (now
  `test_submit_refuses_a_failing_dry_run`); `eval5_record` fixed `.tmp` name (now pid-suffixed
  under `flock`).
- Ticket 04 real-cell review: zero-flip delta cells read "no flip" (7d62b7c).
- Ticket 05 review Minor 4: eval 5 collateral restricted to shared datasets (441e8fc).

**Stay deferred** (none changes a number a reader acts on)
- Ticket 02: `train.py` help "so both are trained"; condition-default idiom in three places;
  plumbing-only nopressure fixture; "template circuit" in two senses in CONTEXT.md.
- Ticket 01: stale `train_samples`/`test_samples` keys in `dataset_config.json` (no reader);
  duplicated unexpected-token counting; `filter_report.json` describes the deceptive split only
  (the FAR caveat already states 99 percent honest-split); `_is_nopressure` on a missing key.
- Ticket 03: raw `--nls` in the slug; stray comma in `--partition`; `postprocess_coarse.sh`
  untested.
- Ticket 04: malformed dry-run header reported as "stale"; re-merge keeps stale cells (`--force`
  exists); head uniformity now checked by `null_sampling_of` (coarse F 8,704 = 68 x 128 in the
  real dry-run); empty composed circuits and walltime calibration (cells finished); `m` config
  cosmetic (documented in `suites.json`); arg-list test covers 4 of 15 coarse jobs.
- Ticket 05: eval 5 role collision (not live: the real coarse EVAL 5 dry-run has only the three
  `X_hko__leaf` cells); non-positive D drop (guarded by the null condition); dead full-accuracy
  fallback; condition mismatch filed under "missing"; manifest parsed twice; a test confounded by
  F's KL cell; no default-mode "failed plus missing" test; ruling text always in `decision.json`.
- Ticket 06: quote test can skip one missing source; caveat 3 cites a machine-local memory path;
  an A40 cache miss inside a running job re-screens without refusing (dry-run-time check only).

## Verdict

**Needs fixes.** The code meets the spec, the five safety invariants hold, and the three verdicts
follow the pre-registered arithmetic. Two Important issues change what the researcher does next:
the summary promises that EVAL 5 discriminates while the rule will not read EVAL 5's deception
numbers (I1, a labelling and reporting fix), and the pending EVAL 5 launch silently depends on
this worktree's absolute paths surviving the merge (I2, one README paragraph or a content-hash
comparison). Both are cheap; with them and the promoted minor fixed, the branch is ready to merge.

## Re-review of the fix wave (e47daf3..6b8d2d6)

Reviewed the diff (commits 2985407, 6b8d2d6) and ran `tests/test_format_control_summary.py` plus `tests/test_format_control_eval5.py` (140 passed, base env).

### Finding Verdicts
- **I1: ADDRESSED.** `format_control_summary.py` adds a `decisions_taken["eval2_conditions"]` entry (labels the choice "not pre-registered; orchestrator choice 2026-10-15, researcher to confirm"). The saturation caveat in `diagnostic_caveats` no longer says eval 5 is the discriminating comparison. `eval5_aggregate` gains `deception_drop`. `summarize` emits `eval5_deception_drop` with `in_rule: False`, computed over the datasets D and F share. `render` prints an informational row after the rule's deception-drop row (`| 0.900 | 0.600 |`), and `decision_record` stores it. `decide()` is untouched. The new test gives F eval 5 drop 0.600 against D 0.900 (F < 0.8 x D) and the verdict stays (a). No eval 5 row appears without `--eval5-dir`. The three regenerated suite summaries and decisions only add the new text.
- **I2: ADDRESSED.** `eval5_cmd.py` adds `same_run` (same path, else identical `active_nodes.json` masks and identical `config.json` `deception_condition`). `gate()` uses it for the manifest-planned F (line 391) and for each cell's recorded F (line 426). Refusals name the reason: "different masks", "identical masks but a different deception condition", or "cannot compare masks/conditions". An unreadable recorded run gets the "keep the format-control worktree" advice. `README_eval5.md` has a "Keep this worktree until EVAL 5 has run" section. `suites.json` is unchanged. Four new tests cover the relocated copy accepted, different masks refused (3 reasons), different condition refused, and the removed worktree giving the keep-worktree message.
- **M5: ADDRESSED.** The usage text in `write_format_control_summary.py` now gives `outputs/eval5_format_far` and `_lb`, and the sdr and sdr_coarse equivalents.

### New Breakage
None Critical or Important.
- Minor: when the masks key is absent in both runs, `same_run` reports "different masks" (conservative refusal, wording slightly off).
- Minor: the "same path" shortcut skips the condition check; harmless because the path is then the same run.

### Out-of-Scope Observations
- After a merge the gate matches by mask content only while the worktree run directories exist (documented in the README). It is not a defect, but the worktree must not be removed before EVAL 5 runs.
- The informational row reports "-" in the result column. If the shared dataset set is empty it will show "n/a" values; not exercised.

### Verdict
Fix wave ACCEPTED. All three findings addressed, verdict logic unchanged, no new submit path (no sbatch/subprocess/write additions in the diff), no writes to the main checkout.
