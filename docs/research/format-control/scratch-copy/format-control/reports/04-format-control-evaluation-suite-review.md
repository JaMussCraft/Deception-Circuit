# Ticket 04 review: format-control evaluation suite (build and dry-run phase)

Reviewer: review-04, 2026-10-13. Range: c73bb21..4e12a1d (e439e91, the launcher, plus 4e12a1d,
the per-cell condition index and the coarse-leaf ruling note, which the orchestration ledger
added to this review's scope). Read-only review of the diff, plus focused reads outside it
(named below).

**This is the build-phase review.** The real Slurm cells have not run (the Format Circuit runs
are still training), so "All cells run", the wikitext KL quotes against the 0.66 gate, and the
flip audit on real knockout cells are out of scope here. A second, short review follows after
the real cells run.

## Checks made outside the diff

- `evaluation/circuits.py:304-340` `resolve_tasks`: with a single `--task-from`, the spec gets
  `label=args.task` (bare `far`/`sdr`). The `@<run-slug>` suffix only applies when two specs
  share a task in one invocation. So the D, H and F test sets of one circuit would all land in
  `cells/<circuit>/far/`, and the refiling in `merge_shards.py` is needed.
- `evaluation/algebra.py:262-274` `_operand_keys` raises `ExprError` when operands' mask keys
  differ. A coarse F whose keys do not match the shared `_allmlp_nomb` operand fails its
  dry-run loudly, not silently.
- `scripts/evaluate_circuit.sbatch`: `cd "${SLURM_SUBMIT_DIR}"` and `python evaluate_circuit.py "$@"`.
  The relative `--output-dir` and `./data/datasets` of the D/H configs resolve against the
  worktree. The worktree's `data/datasets/` has `far`, `far_honest`, `far_nopressure`, `sdr`,
  `sdr_honest` and `sdr_nopressure`.
- The committed manifest (parsed): 54 jobs and 66 cells. Fine suites have 15 jobs and 21 cells
  each, and the coarse suite has 24 jobs and 24 cells. 16 jobs are ready, and all 16 have a
  passing real dry-run. Every job has a `slurm.job_id` slot.
- Dry-run logs read: `dryrun/format-control-sdr-coarse-nls0.3/D_hko__sdr_honest.log` (69 heads,
  8,832 attention neurons, 0 MLP units, condition=honest), and
  `dryrun_standin/.../F_hko__sdr_nopressure.log` and `.../H_minus_D_minus_F__far.log`. These are
  real `evaluate_circuit.py --dry-run` output. The stand-in H - D - F is empty (0 units), which
  is expected with F := H and is flagged by the evaluator's WARNING.
- Focused test run at 4e12a1d (base env): `tests/test_format_control_launch.py` passed 34 tests
  in 22.6 s. That is 33 tests plus the new manifest-index test.

## Spec Compliance

| requirement | verdict | evidence |
| --- | --- | --- |
| Three suites under `outputs/_suites/`, D/H/F bound, tasks via `--task-from` of the D, H, F runs | ✅ | `suites.json`; `fc_cells.py:119-178`; `fc_cells.job_args` emits `--task-from <run of the data role>` |
| 9 faithfulness cells (3 circuits x 3 test sets) | ✅ | `fc_cells.py:141-153`. Fine: evals 1-4 per job. Coarse: sanity/null/pressure on the atomic expanded circuit |
| 9 knockout cells (eval 2 with task null, wikitext, variant rows, generations) | ✅ | Fine: the same 9 jobs run `knockout`. Coarse: 9 `X_hko=(X) - m` jobs, `fc_cells.py:154-162` |
| F-test-set cells carry no variant rows, by design | ✅ | The skip is dataset-driven in the evaluator (ticket 01), not a launcher omission. The launcher requests uniform evals. It is documented in `README_suites.md` and asserted by the end-to-end test (`tests/test_format_control_launch.py:559`: every variant `skipped`; no `pressure.json`; `skipped.pressure` set) |
| Deltas D-F, D&F, F-D, `--xor D,H,F` as knockout cells on the D test set | ✅ | `fc_cells.py:60, 165-177`. The xor family is expanded via `algebra.expand_xor` with the evaluator's own labels. All six run on the D test set with `--evals knockout` |
| Fine deltas at `--compose-granularity both` | ✅ | `fc_cells.py:168`. Manifest: every fine delta job is `both` with `__leaf` and `__head` cells. The end-to-end test checks both delta cells exist with nulls |
| Coarse at head with `c - m` against `_allmlp_nomb` | ✅ (per ruling) | Compose at leaf as `(expr) - m` (`fc_cells.py:160, 172`). Ruling recorded in `00-orchestration-ledger.md:61`, `suites.json` `_coarse_granularity`, the `fc_cells.py` header and `README_suites.md:65-75` (4e12a1d) |
| Delta cells run eval 2 only | ✅ (per ruling) | `KNOCKOUT_EVALS`, ledger line 62, README |
| Merged cells refiled under `<task>`, `<task>_honest`, `<task>_nopressure`, mapping in the manifest | ✅ | `merge_shards.py:48-131` reads the condition from each shard's own `suite.json`. In 4e12a1d the manifest gained a per-suite `cells` index (circuit, dataset, condition, roles, job, path) at `fc_launch.py:86-92` |
| Interchange only, `--n-random 20 --knockout-null-count 20` | ✅ | `fc_cells.py:68` `COMMON_ARGS` on every job |
| Overlap table (Jaccard heads and fine units) for D/H, D/F, H/F | ✅ | `overlap.py`. Coarse uses the un-expanded `active_nodes.coarse.json`, heads only. D/H numbers match the spec's sizes. D/F and H/F render as `awaits F` |
| `cell_cmd.sh` + `submit.sh`, any account/partition, `--dry` prints exact sbatch lines | ✅ | `submit.sh`, `fc_launch.py:150-190`. `tests/...:381-404` asserts the exact line |
| `merge_shards.py` reuse | ✅ | An adaptation of the 260922 merge (diffed against `_launch_260922/merge_shards.py`): refiling, a two-shards-one-cell refusal, a manifest cross-check, and missing-job reporting |
| `suite_manifest.json` lists every cell and its job id | ✅ | The id slot is per job (`slurm.job_id`). Each cell reaches it through its job, and the 4e12a1d `cells` index adds `job` per cell |
| Flip audit per knockout cell with the positional-default check | ⚠️ tooling only | `flip_audit_analysis.py` is the 260922 script with only `suite_exprs`/`is_delta` changed (diffed). `postprocess.sh` runs it on every `knockout.json`. The end-to-end test asserts `rows_aligned` and a positional verdict per cell. Real cells are pending |
| Dry-run of every cell whose inputs exist | ✅ | 16 of 16 ready jobs PASS (`dryrun/`). The 38 F-dependent jobs PASS with a stand-in F (`dryrun_standin/`, plumbing only) |
| Generator is a pure function, tested for every (circuit, dataset, granularity) and the coarse `c - m` rewrite | ✅ | `tests/...:158` (every combination, no duplicates, exact counts 21/21/24); `:135` (the `c - m` arg lists for 4 representative jobs) |
| Merge/manifest tests in the `test_suite_layout.py` pattern | ✅ | Merge: 4 tests. Manifest/submit: 4 tests plus the 4e12a1d index test |
| Tiny-model end-to-end: one faithfulness cell and one delta cell with `nopressure` as `--task-from` | ✅ | `tests/...:519`. It uses the generator's own args, merges with the manifest's cells, then runs the flip audit |
| Both suites in both envs, names vs baseline | ⚠️ not re-run here | Per instructions. The implementer and ledger report base and mgnp with the 8 baseline names only. That list matches `00-baseline-failures.md` (8 names) |
| All cells run; wikitext KL quotes; summary | out of scope | Real phase. The summary is ticket 05 (placeholder `write_suite_summary.py` meanwhile) |

## Strengths

- The cell grid is data. `plan_suite`/`job_args` are filesystem-free except for the task-registry
  lookup. F is one configuration point, and jobs that need F carry `awaits` instead of
  half-formed arguments.
- Spotting the bare-label collision before any real run, and fixing it with provenance read
  from each shard's `suite.json` rather than from the job name, is the right seam. The merge
  refuses two shards for one cell and refuses shards that disagree with the manifest.
- The `is_delta` fix is substantive. The 260922 rule (a `-` in the expression) would have missed
  `D & F` and counted every coarse `(X) - m` as a delta.
- The coarse leaf-versus-head problem was checked on the real masks (MLP units kept at head
  versus leaf, identical head counts). It was escalated rather than silently deviating, and it
  is now recorded in four places.
- `submit` refuses jobs without a passing dry-run, alternates accounts, passes argv as a list
  (no shell quoting of `D & F`), and preserves job ids across manifest rebuilds.
- The tests assert behaviour at the seams. No test asserts nothing. The end-to-end test checks
  n per test set (4 against 6), which proves the right dataset was loaded.

## Issues

### Critical

None.

### Important

1. **`submit` saves job ids only after the whole loop** (`fc_launch.py:181` and `:315`).
   `_default_run` uses `check=True`. If one sbatch fails mid-loop (a QOS limit, a bad account,
   a transient Slurm error) or the user interrupts, `submit` raises and `main` never reaches
   `save_manifest`. The ids of jobs already queued are lost. A re-run of `submit.sh` then
   double-submits them: same shard dir, two jobs writing it concurrently. With 54 jobs across
   accounts this is a realistic failure.
   *Fix:* call `save_manifest` after each successful submission (pass the path into `submit`,
   or wrap the loop in `try/finally` in `main`). Add a test where `run` raises on the third job
   and the first two ids are persisted.

2. **A dry-run log is trusted regardless of the arguments it ran** (`fc_launch.py:97-107`, used at
   `:75`). `read_dryruns` marks a job passed whenever `dryrun/<suite>/<job>.log` exists and parsed.
   `build_manifest` prefers that verdict over the args-equality check it applies to `previous`.
   If `suites.json` changes after a dry-run, `submit` sends the job on a stale PASS. This
   happens with a size-rule retune of F (pre-registered in ticket 03), a corrected F path, or a
   change to `COMMON_ARGS`. That breaks the spec's "`--dry-run` on the login node before every
   submission".
   *Fix:* the log's first line already records `shlex.join(args)`. Compare it with the job's
   current args in `read_dryruns`, treat a mismatch as `passed: None`, and add a test.

### Minor

1. **Ticket Comments and the implementer report still say the ruling is open**
   (`issues/04-...md:44` "Ruling needed"; `reports/04-implementer-report.md:6` "coarse ruling
   open"). The rulings live in the ledger, `suites.json`, the `fc_cells.py` header and the
   README. Add one Comments line to the ticket so the ticket itself is current.
2. **The walltime margin is calibrated on 1x A100 but the default partition list starts with A40**
   (`fc_cells.py:217-221`, `fc_launch.py:274`). An 81-minute A100 estimate x 1.5 gives 2:15. An
   A40 can plausibly exceed that on the knockout-null-heavy fine jobs. Use a larger factor
   when A40 is in the partition list, or default to A100/H200 partitions. Job length is no
   longer capped.
3. **The re-merge after a re-run keeps stale cell directories** (`merge_shards.py`, the "keep
   existing" branch; `postprocess.sh` calls merge without `--force`). If a finished job is
   resubmitted and post-processing runs again, the matrix row comes from the new shard while
   `cells/...` keeps the old files. This is inherited from the 260922 merge. Overwrite when the
   shard's `matrix.json` is newer than the destination, or document `--force` in the workflow.
4. **The head-uniformity assumption behind coarse leaf composition is checked by hand, not by
   code.** "Every live head has all 128 neurons open" was verified on D. The H and D&H dry-run
   counts (7,168 = 56 x 128; 5,504 = 43 x 128) imply it for H. The real coarse F needs the same
   check. A one-line assertion in the plan or a dry-run log check (attention_neurons equals heads
   x 128 for every coarse cell) would make it automatic.
5. **Empty composed circuits pass the dry-run** (`fc_cells.py:209-214`). The evaluator only
   WARNs. With the real F, a delta such as `F - D - H` may be empty. It would then spend about
   80 minutes on a no-op knockout. Surface the empty-circuit warning in `fc_launch.py dryrun`
   output and the manifest so it is a decision, not a surprise.
6. **The `m` operand's `config.json` was copied from coarse D**, so plans print `m:deceptive`.
   This is cosmetic. A one-line note in `suites.json` would avoid confusion when reading
   dry-run logs.
7. **`test_every_coarse_knockout_is_rewritten_as_c_minus_m` covers 4 of the 15 coarse
   knockout/delta jobs.** The combination test covers the cell labels of all 15, not their
   argument lists. Parametrising the arg-list assertion over all 15 would cost nothing.

## Assessment

**Spec: compliant** for the build phase, with the two orchestrator rulings applied and recorded.
**Quality: Needs fixes.** Fix the two submit-path issues (persist job ids per submission; reject
dry-run logs whose arguments differ from the job's) before the first real `submit.sh`. Neither
affects the cells' scientific content.

## Re-review of fix round 1 (4e12a1d..a365e65)

### Finding Verdicts
- **Job ids saved only after the loop: ADDRESSED.** `fc_launch.py:~211-213` calls `save(manifest)` right after each successful sbatch records its id; `main` (`~:334`) passes `save_manifest` for real runs and `None` for `--dry`, and the trailing post-loop save is gone. `save_manifest` writes via tmp + `os.replace` (`:136`), so a crash mid-save cannot corrupt the file. Covered by `test_a_failed_sbatch_mid_loop_keeps_the_ids_already_queued` (third sbatch raises; saved file holds ids 2001/2002, H is None; the re-run sends only the two unsent jobs).
- **Any dry-run log counted as PASS: ADDRESSED.** `read_dryruns` (`:106-125`) parses the log header (`_LOG_HEADER`, `:97`), which matches the exact line `_dryrun_one` writes (`:229`), and compares it with `shlex.join(job_args(job))`. A mismatch yields `passed: None, stale: True`; `submit` (`:192-195`) skips it with an explicit message. `build_manifest` keeps the stale record (it is non-None, so it overrides the carried-forward old verdict). Covered by `test_a_dry_run_log_counts_only_for_the_arguments_it_ran` (matching D passes with estimate 76.6; F log written for a different path is stale and skipped in submit). Report states the 16 real logs still match (16 passed, 0 stale).

Tests: the fix report names both tests, shows RED (TypeError on `save`; `True is None`) and GREEN (36 passed in base and mgnp). I did not re-run.

### New Breakage in the Fix Diff
None Critical or Important.
- Minor: `read_dryruns` now skips jobs with `awaits` (`:115`), so a pre-existing log for an awaiting job is ignored. Correct (no args to compare), and such jobs are never submitted anyway.
- Minor: a log whose first line is not the header (hand-made or truncated) is reported `stale`, with the message "for other arguments" rather than "unreadable header". Message slightly misleading only.
- Minor: `suite_manifest.json` was regenerated (timestamp only) in the fix commit; harmless churn.

### Out-of-Scope Observations (non-blocking)
- `build_manifest` carries a previous `dryrun` verdict forward when the log file is deleted and args are unchanged (`:74-75`); pre-existing and consistent with the args-match rule.
- `plan` output does not print the `stale` flag distinctly; a stale job just shows as not dry-run.

### Verdict
All findings addressed, no new Critical/Important breakage.


## Real-cell review: SDR suites (8e25b41, 1bc5e58)

Reviewer: review-04 (real-cell phase), 2026-10-15. Read-only: JSON reads of the merged suites, the manifest, `sacct`, and the September reference cells. No re-run and no pytest (no specific doubt arose). The FAR suite is out of scope.

### Named checks

1. **PASS. Refiling and manifest index.** `suite_manifest.json` `suites.<suite>.cells` has 21 (fine) and 24 (coarse) entries with 21 and 24 unique paths. Every path exists under `cells/`, and there is no extra cell directory on disk. Dataset directories are `sdr` / `sdr_honest` / `sdr_nopressure` with 15/3/3 (fine) and 12/6/6 (coarse). Each cell's `summary.json:task_spec.dataset.deception_condition` matches its directory (deceptive / honest / nopressure), and `circuit_spec.label` equals the circuit directory name. Every merged `*.json` is byte-identical to its copy under `_shards/<job>/cells/` (filecmp, 0 differences).
2. **PASS.** Six of the nine nopressure cells have a knockout: fine D, H, F and coarse D_hko, H_hko, F_hko. Each carries `knockout.json:variants.honest_instruction.skipped`, `variants.no_pressure.skipped` and `honest.skipped`, with n=520. The text is "sdr 'honest_instruction' variant skipped: the dataset's condition is 'nopressure' (empty pressure), so it already is the no_pressure variant (the Pressure Clause was deleted at build time) and has no clause to replace with an honest instruction". The other three nopressure cells are the coarse D, H, F faithfulness cells, which have no knockout.json; they record the same reason for eval 4 in `summary.json:skipped.pressure`. The writer renders the six as "n/a (condition is nopressure)" (`evaluation/format_control_summary.py:418`; both `evaluation_summary.md` variant tables).
3. **PASS.** `allmlp_nomb/active_nodes.json:built_from` is the coarse F run `.../nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_261013-204850`. Its keys are attention_blocks, attention_heads, attention_neurons, mlp_hidden and mlp_output, with no mlp_blocks. These are the same keys, with the same per-layer lengths, as F's expanded mask and as D's and H's. It holds 0 heads and 0 attention neurons, and all 458,752 mlp_hidden and 131,072 mlp_output units. It is identical to the September `_allmlp_nomb` mask. All 15 coarse knockout cells show the following. `knockout.json:counts.ablated_fine_units` is a multiple of 128 and equals heads x 128 (8,832 / 7,168 / 8,704 / 4,224 / 4,608 / 4,096 / 2,816 / 256 / 2,688). The circuit has 0 MLP units, and `summary.json:knockout.counts.mlp_hidden` and `mlp_output` are fully live (458,752/458,752 and 131,072/131,072). The expression is `(X) - m` with `compose_granularity: leaf`.
4. **PASS.** `flip_audit.json:cells` has 21 (fine) plus 15 (coarse), so 36 entries. Each has `flip_audit: true`, `rows_aligned: true` and a `positional` block. That block holds p_target_item_2, p_ko_item_2, binom_p_vs_base, stay_rate_target_1 and _2, and verdict. All 36 verdicts are "content-driven flip". See Minor 2 for how the no-flip cells are labelled.
5. **PASS.** Hardware explains the fine differences.
   - **Coarse.** D_hko on `sdr` matches the September `evaluations_headsko/cells/headsko__leaf/sdr` cell exactly. Knockout accuracy is 0.002, wikitext KL 0.364369, floor 6.64e-4, null accuracy p5/p50/p95 0.04085/0.4145/0.7736, and wikitext-null KL p5/mean/p95 0.2596/0.3973/0.5788. Every difference is 0.0, and both cells ran on A40.
   - **Fine.** D on `sdr` against the rerun's `cells/sdr/sdr`: knockout accuracy is 0.000 in both, and ablated units are 11,251 in both. Wikitext KL is 1.38315 against 1.38252, null accuracy p5/p50/p95 0.3966/0.7045/0.8774 against 0.3954/0.6995/0.8719, and circuit-alone accuracy 0.950 against 0.953.
   - **Fine hardware.** The new cell ran on gpue07 (H200), and the September job 22317661 ran on gpub086 (A40). The exact coarse match shows the pipeline is unchanged.
6. **⚠️ The null samples whole heads, but the summary does not yet say so.** `evaluation/masks.py:sample_random_masks` draws the circuit's number of heads per layer. `_draw_neurons_uniform` places the circuit's attention-neuron count inside the drawn heads, and MLP units are drawn per layer. Attention blocks are copied verbatim. For every heads-only cell, attention_neurons = heads x 128 and MLP = 0 (`summary.json:circuit.counts`, with `null_alloc: uniform` and `knockout_granularity: finest`). So each drawn head is filled completely and no MLP unit is drawn. The coarse null is therefore whole heads, matched per layer, with no MLP units. The fine atomic cells instead sample fine units: heads per layer, neurons inside the drawn heads, and MLP units per layer. The committed `evaluation_summary.md` of both suites does not state this. The "Null: ..." line exists only in the uncommitted working-tree change to `evaluation/format_control_summary.py` (ticket 05). Once that lands, re-running the writer is enough. No cell needs a re-run.
7. **PASS. Settings and hardware.** All 45 cells have `cli.ablation: interchange`, `n_random: 20`, `knockout_null_count: 20`, `null_alloc: uniform` and `knockout_granularity: finest`.
   - **Fine composition.** The 9 atomic cells ran evals sanity, knockout, null and pressure. The 6 delta jobs ran `--compose-granularity both` with knockout only, which gives 12 cells, `__head` and `__leaf`.
   - **Coarse composition.** The 9 faithfulness cells ran sanity, null and pressure. The 15 knockout and delta cells ran knockout only, as `(expr) - m` at `leaf`.
   - **Partitions.** `sacct` agrees with the manifest's `slurm.ran_on`, which is still uncommitted in the working tree. All 39 jobs COMPLETED with exit 0, and none ran outside A40 or H200.

   | suite | A40 jobs | H200 jobs |
   | --- | --- | --- |
   | fine | 22895955 D on sdr_honest, 22895957 H on sdr, 22895967 H-D-F delta | the other 12, all on gpue07 |
   | coarse | all 24 | none |

   - **Decision inputs.** Every fine decision-rule input came from H200: the D and F cells on `sdr`, including their variant rows. The H row on D data came from A40.
   - **Sanity misses.** Both tolerance misses are in H200 cells, recorded in `summary.json:failures`: `cells/D/sdr` (job 22895954) and `cells/F/sdr_nopressure` (job 22895962).
8. **PASS.** `overlap.json` has D/H, D/F and H/F. The fine suite has heads and fine units, pooling attention_neurons, mlp_hidden and mlp_output. The coarse suite has heads only, from `active_nodes.coarse.json`, and `fine_units: null`. A recomputation from the raw masks matches:
   - Fine D/F heads are 52/89 = 0.5843.
   - Fine D/F fine units are 5,482/17,651 = 0.3106.
   - Coarse D/F heads are 36/101 = 0.3564.
   - All three equal the `overlap.json` values. The coarse counts agree with the delta cells: D&F has 36 heads, D-F has 33 and F-D has 32. The coarse expanded and un-expanded masks have identical head sets.

### Issues

**Critical:** none.

**Important:** none.

**Minor:**
1. **The null's sampling unit is not printed yet** (check 6). This is tracked by ticket 05. After that change lands, regenerate both suites' `evaluation_summary.md` and `decision.json`.
2. **Zero-flip delta cells are labelled as flips.** The H-D-F delta cells (fine head, fine leaf and coarse) stay deceptive on 1000 of 1000 items. Their positional verdict and the summary's delta table still read "content-driven flip". The audit or the writer should say "no flip" when the stay rate is about 1.
3. **Actual partitions are not committed yet.** The manifest records them only in the uncommitted `slurm.ran_on` and `state` fields. Commit them with the FAR suite so the hardware split stays on record.
4. **Observation for the researcher, not a ticket 04 defect.** Under interchange ablation every atomic knockout swaps the answer on every test set: knockout accuracy is at most 0.002 on D, H and F data in both suites. On the D-data variant rows, D, H and F give nearly the same honest-answer drop (fine 0.522 for both D and F; coarse 0.530 against 0.519 and 0.560 against 0.535). The honest-answer condition therefore separates the circuits only weakly here. The coarse (a) verdict passes that condition by margins of 0.011 and 0.025.

### Verdict
**Approved.** The merged SDR suites match the ticket, the spec and the orchestrator rulings. The one ⚠️ (check 6) waits on ticket 05's summary line and needs no re-run.


## Real-cell review: FAR suite (b08c5a9, 7d62b7c)

Reviewer: review-04-real (FAR phase), 2026-10-15. Read-only: JSON reads of the merged suite, its shards, the manifest, the Slurm logs, live `sacct`, the raw `active_nodes.json` masks and the September reference cell. No pytest: no doubt arose that a focused test would settle. The `record-slurm` code and its test were read, and the manifest was cross-checked against live `sacct`. PASS lines on the summary refer to the committed `evaluation_summary.md` at 7d62b7c. The working tree has small uncommitted edits to the FAR and SDR `evaluation_summary.md` / `decision.json` (FAR: 4 and 7 lines, verdict wording). Those are ticket 05's, not a FAR defect.

### Named checks

1. **PASS. Merge and index.** `suite_manifest.json` `suites.format-control-far-nls0.3.cells` has 21 entries and 21 unique paths. They equal the 21 `summary.json` directories on disk, with nothing missing or extra. Dataset directories are `far` 15, `far_honest` 3, `far_nopressure` 3. Each cell's `task_spec.dataset.deception_condition` matches the manifest condition, and `circuit_spec.label` equals the circuit directory. All 69 merged JSON files are byte-identical to their `_shards/<job>/cells/<circuit>/far/interchange` source. F04 is absent from the cells index and from `matrix.json`, `matrix.csv`, `overlap.json`, `decision.json` and `flip_audit.{json,md}`. It sits under `side_jobs.format-control-far-nls0.3[0]` with `slurm.job_id` 22906802, state COMPLETED, and `output_dir` `_side_F04`.
2. **PASS.** The knockout cells for D, H and F on `far_nopressure` all carry `knockout.json:variants.honest_instruction.skipped`, `variants.no_pressure.skipped` and `honest.skipped`. The text is "far '…' variant skipped: the dataset's condition is 'nopressure' (empty pressure), so it already is the no_pressure variant …". `summary.json:skipped.pressure` records the same reason. The committed summary's variant table renders both F-data columns as "n/a (condition is nopressure)" for D, H and F (lines 75-77).
3. **PASS.**
   - **F-data n.** All three F-data cells have `task.circuit.n` = `task.knockout.n` = 500. The Slurm logs read "Attempting to load dataset from: ./data/datasets/far_nopressure … Successfully loaded test split with 500 samples" (`D__far_nopressure_22906789.out:30-38`, `F__far_nopressure_22906795.out:183`).
   - **D reproduction.** D on `far` matches the September rerun's `cells/far/far/interchange/knockout.json` exactly. Circuit-alone accuracy is 0.969, knockout accuracy 0.000 (n 1000), ablated units 5,436, wikitext KL 0.3265542514855042 and floor 6.639e-4. Null accuracy p5/p50/p95/mean is 0.4403 / 0.872 / 0.99905 / 0.816, and wikitext-null KL p5/mean/p95 is 0.1215 / 0.1432 / 0.1594. Every difference is 0.0.
   - **Summary note.** The summary marks F data "NOT paired: 98% honest-split instances" in the header, the section title, every F-data row and the caveats.
4. **PASS.**
   - **FAR audit.** `flip_audit.json:cells` has 21 entries, each with `flip_audit: true`, `rows_aligned: true` and a `positional` block.
   - **Positional defaults.** Exactly three verdicts are "positional default", the leaf cells D−F, D−H−F and F−D−H. Their P(KO item_2) is 0.790 / 0.708 / 0.715 against a base of 0.482, with binom p ≤ 2e-47. Their head versions are content-driven (0.646 / 0.561 / 0.612).
   - **Surfaced.** The committed summary's delta table shows the three leaf rows as "positional default; separable" (lines 92, 98, 102), and the ticket Comments repeat them.
   - **No flip.** No FAR knockout flips zero items, so no FAR cell reads "no flip". The regenerated SDR audits read "no flip" on exactly the zero-flip cells: fine H−D−F head and leaf, and coarse H−D−F, each with stay rate 1.0/1.0. Both SDR summaries show "no flip; not separable" for them. The rule is `flip_audit_analysis.py:464-466` (`n_flipped == 0`), covered by `tests/test_format_control_launch.py:607-621`.
5. **PASS. `record-slurm`.** All 55 jobs carry `job_id`, `state`, `ran_on.partition` and `ran_on.node`: FAR 15 + side 1, SDR fine 15 and coarse 24. Fifty-two also carry `time_limit_actual`. Live `sacct` agrees with the manifest on partition, node, state, effective time limit and account for all 55 jobs, with 0 mismatches.
   - **FAR.** All 16 FAR jobs ran on gpuA40x4 with limit 01:30:00, lowered from 04:00:00. Accounts alternate between beto and bgrb.
   - **SDR exceptions.** The three SDR fine jobs without `time_limit_actual` (22895955, 22895957 and H on `sdr_nopressure`) still have their submission limit in `sacct`, so omitting the field is correct.
   - **Test.** `test_sacct_actuals_record_where_each_job_ran` covers the actual partition and node, the final state, a changed versus unchanged limit, a PENDING job without `ran_on`, and survival through `build_manifest(previous=…)`.
6. **PASS.** `overlap.json` has D/H, D/F and H/F with heads and fine units (pooling attention_neurons, mlp_hidden and mlp_output). The raw `masks` in the three `active_nodes.json` files give D 48, H 65 and F 82 heads, all inside live blocks, and 5,436 / 10,935 / 12,986 fine units. Recomputed values match `overlap.json` in every count:
   - D/H: heads 34/79 = 0.4304, units 2,556/13,815 = 0.1850.
   - D/F: heads 33/97 = 0.3402, units 2,621/15,801 = 0.1659.
   - H/F: heads 58/89 = 0.6517, units 6,917/17,004 = 0.4068.
   - The D&F cells agree: head-composed 33 heads, leaf-composed 2,621 units.
7. **PASS. Side job.** `_side_F04/cells/F04/far/interchange/` holds `knockout.json`, `summary.json` and `plots/`.
   - **Numbers.** Circuit-alone accuracy is 0.782, knockout accuracy 0.000 (n 1000), null p5 0.4121 (p50 0.6475, p95 0.9664, n 20), wikitext KL 2.3167 and ablated units 10,729.
   - **Settings.** `cli.evals` is sanity and knockout, with interchange, 20 and 20. Eval 1 is skipped by design with the recorded reason "circuit 'F04' was trained in …nls0.4_nopressure… but this cell evaluates task 'far', so there is no in-run number to reproduce".
8. **PASS.** All 21 cells have `cli.ablation: interchange`, `n_random: 20`, `knockout_null_count: 20`, `knockout_granularity: finest` and `null_alloc: uniform`.
   - **Atomic cells.** The 9 atomic cells ran sanity, knockout, null and pressure.
   - **Delta cells.** The 6 delta jobs ran knockout only with `compose_granularity: both`, giving 12 cells: `__head` and `__leaf` for D−F, D&F, F−D, D−H−F, H−D−F and F−D−H.
   - **Logs.** The Slurm log command lines carry the same arguments (e.g. `D__far_nopressure_22906789.out:8`).

### Issues

**Critical:** none.

**Important:** none.

**Minor:**
1. **`summary.json:task_spec.dataset.test_samples` reads 1000 on the three F-data cells**, but they evaluated 500 records. The field is inherited from the run config, while `knockout.json` n and the log are correct. A reader of `summary.json` alone gets the wrong n. Record the loaded count, or rename the field to say it is the requested count.
2. **Near-zero-flip cells read "content-driven flip".** The verdict is binary on `n_flipped == 0`. FAR H−D−F head flips about 0.6% of items (stay 0.996/0.992, knockout accuracy 0.988), and SDR fine F−D−H head about 0.3%. Both read "content-driven flip". This follows the ruling ("zero-flip knockouts read 'no flip'") and is not a defect. The researcher should read the label next to the stay rate.
3. **`apply_sacct` writes a fixed `time_limit_note`.** It says "lowered in place by the orchestrator … on 2026-10-14" whenever the `sacct` limit differs from the submitted one, whatever the direction or date (`fc_launch.py:291-293`). It is correct for the current 52 records. A later raise or a different-day change would be mislabelled. An account moved with `scontrol` is also not re-recorded, since `SACCT_FIELDS` omits Account. All 55 accounts match today.
4. **Expected warning, noted for the record.** Every FAR knockout cell, F04 included, carries the non-strict failure "all-gates-open wikitext floor is not zero (KL 6.639e-04)". The ticket already caveats it.

### Verdict
**Approved.** The merged FAR suite, the side job, the "no flip" fix and `record-slurm` match the ticket, the spec and the four orchestrator rulings. The Minor items need no re-run.
