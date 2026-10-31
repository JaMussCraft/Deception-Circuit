# Ticket 04 implementer report: format-control evaluation suite (build and dry-run phase)

Date: 2026-10-13. Implementer: impl-04. Landed in `Deception-Circuit/.claude/worktrees/format-control`
(branch `format-control`, after ticket 01's merge 06110bb; tested at c73bb21).

## Status: DONE_WITH_CONCERNS (real-cell phase awaits ticket 03; the coarse-at-leaf ruling was made 2026-10-13, see the ticket Comments)

**History.** I started in the sibling worktree `format-control-04` (base e194874). The harness
pinned the session elsewhere and refused git and Write/Edit there; I did not work around it and
staged everything (durable copy: `reports/04-staged/`, pre-landing version). The orchestrator
then ruled that sibling worktrees are abandoned and that it is the only git actor. After ticket
01 merged, I copied the new files into `format-control` (all new; no tracked file modified),
renamed my README to `README_suites.md` to stay apart from ticket 03's launcher files, re-ran
the tests and every dry-run there, and sent the orchestrator an explicit commit request.
**Commits are made by the orchestrator on my instruction** (SHA in the ticket Comments once
made).

**Changes made after landing on the ticket-01 tip.**
- The end-to-end test failed once on `pressure.json` missing. With ticket 01, the evaluator
  correctly skips eval 4 and the eval 2 variant rows on the `nopressure` test set, recording a
  reason. The test now asserts exactly that: no `pressure.json`, `summary.json`
  `skipped.pressure` set, and every `knockout.json` variant `skipped`. This is the ticket's
  "F-data cells carry no variant rows", verified.
- `standin-dryrun` gained `--f-run SUITE=DIR`. Each stand-in F is a copy of the H run with
  `deception_condition: nopressure`, kept in job tmp only. The stand-in dry-runs therefore read
  the real `far_nopressure` / `sdr_nopressure` test sets.

## What was built

Files (all new; no shared file changed):

| path | what |
| --- | --- |
| `outputs/_launch_format_control/suites.json` | the single configuration point: D, H, F run dirs per suite (F `null`), coarse `m` operand |
| `outputs/_launch_format_control/fc_cells.py` | pure generator: `plan_suite(suite, cfg)`, `job_args(job)`, `dataset_label`, `walltime`, `parse_dryrun_log` |
| `outputs/_launch_format_control/fc_launch.py` | CLI: `plan`, `args`, `dryrun`, `standin-dryrun`, `submit [--dry]`, `merge`, `overlap` |
| `outputs/_launch_format_control/suite_manifest.json` | 54 jobs / 66 cells, args, dry-run verdicts and estimates, `slurm.job_id` (all null) |
| `outputs/_launch_format_control/cell_cmd.sh`, `submit.sh` | thin wrappers over `args` / `submit` |
| `outputs/_launch_format_control/merge_shards.py` | the 260922 merge, now filing cells by test set and checking shards against the manifest |
| `outputs/_launch_format_control/flip_audit_analysis.py` | copy of the 260922 flip audit (positional-default check unchanged); `is_delta` reads operands |
| `outputs/_launch_format_control/overlap.py` | Jaccard heads + pooled fine units, D/H, D/F, H/F -> `<suite>/overlap.{json,md}` |
| `outputs/_launch_format_control/postprocess.sh` | merge, flip audit, overlap, placeholder `write_suite_summary.py` |
| `outputs/_launch_format_control/README_suites.md` | layout, cells, coarse ruling, workflow |
| `outputs/_launch_format_control/dryrun/<suite>/<job>.log` | 16 real login-node dry-runs |
| `outputs/_launch_format_control/dryrun_standin/<suite>/<job>.log` | 38 plumbing dry-runs with F := H |
| `tests/test_format_control_launch.py` | 33 tests |

### Cells

- **Fine suites** (`format-control-far-nls0.3`, `format-control-sdr-nls0.3`): 15 jobs, 21 cells each.
  9 atomic jobs `X__<dataset>` (X in D, H, F; datasets `<task>`, `<task>_honest`,
  `<task>_nopressure` via `--task-from` on the D, H, F runs) with evals 1-4, so each is both the
  faithfulness cell and the knockout cell (eval 2 with task null, wikitext, variant rows,
  generations). 6 delta jobs on the D test set, `--evals knockout`, `--compose-granularity both`
  (cells `<label>__leaf`, `<label>__head`): `D_minus_F`, `D_and_F`, `F_minus_D`, and the xor family
  expanded with `algebra.expand_xor` into explicit `--expr` (labels identical to what `--xor D,H,F`
  produces: `D_minus_H_minus_F`, `H_minus_D_minus_F`, `F_minus_D_minus_H`; `\` written as ` - `).
- **Coarse suite** (`format-control-sdr-coarse-nls0.3`): 24 jobs, 24 cells. 9 sufficiency jobs
  (atomic, evals sanity null pressure), 9 heads-only knockouts `X_hko=(X) - m`, 6 deltas
  `<label>_hko=(<expr>) - m`, all knockouts at `--compose-granularity leaf` (see concern 1).
- All jobs: `--ablation interchange --n-random 20 --knockout-null-count 20`, one shard per job
  under `outputs/_suites/<suite>/_shards/<job>`.

### Task labels (a bug the merge fixes)

With one `--task-from` per invocation, `resolve_tasks` labels every test set by its bare task
name (`far`), so the D, H and F test sets of one circuit would all merge into
`cells/<circuit>/far/`. `merge_shards.py` relabels each cell to its test set's directory name from
the shard's own `suite.json` task provenance (`dataset.deception_condition`, through
`get_task(..).dataset_dir`), keeps the evaluator label as `task_name`, adds `dataset_condition` and
`shard`, refuses two shards for one cell, and with the manifest refuses a shard whose cells differ
from the plan and lists planned jobs with no shard. The flip audit then loads
`data/datasets/<label>/test`, and its excerpt-alignment check confirms the pairing per cell.

## TDD evidence

Test command (staging; nothing written to the worktree):

```
bash /u/swong2/.claude/jobs/fcfa1a47/tmp/runtests.sh <python> .../stage04/tests/test_format_control_launch.py
```

| slice | RED | GREEN |
| --- | --- | --- |
| generator (22 tests incl. every (circuit, dataset, granularity) and the coarse `c - m` rewrite) | `ModuleNotFoundError: No module named 'fc_cells'` (1 error, -x) | `22 passed in 0.17s` |
| merge (4) | `22 passed, 4 errors` (no `merge_shards`) | `26 passed` |
| manifest + submit `--dry` (4) | `26 passed, 4 errors` (no `fc_launch`) | `30 passed` |
| overlap (2) | `2 failed` (no `overlap`) | `2 passed` |
| tiny end to end (1) | written after the units it exercises; passed on first run | `1 passed in 19.37s` |

The end-to-end test trains a tiny deceptive run D and a tiny `nopressure` run F, runs the
generator's own argument lists for `D__far_nopressure` (faithfulness cell, `--task-from` the
nopressure run) and `D_minus_F__far` (delta, both granularities) through `evaluate_circuit.main`,
merges with the manifest's expected cells, asserts the cells land at
`cells/D/far_nopressure/` (n = 4, the nopressure test set) and `cells/D_minus_F__{leaf,head}/far/`
(n = 6), with task-side nulls, then runs the flip audit and asserts every knockout cell is
row-aligned and carries a positional verdict, and that `is_delta` marks the delta and not D.
I also ran the placeholder `write_suite_summary.py` on that merged tiny suite: it read all three
cells under the new labels.

## Test results (full suite, both envs)

On `format-control` at c73bb21, with ticket 01 merged and the files landed (the final run):

| env | result | failures vs baseline |
| --- | --- | --- |
| login base (py3.9, transformers 4.57.3) | 8 failed, 695 passed, 20 skipped | the 8 baseline names, no new |
| mgnp (py3.12, transformers 5.13) | 8 failed, 696 passed, 19 skipped | the 8 baseline names, no new |

Earlier, in staging against `format-control-04` (e194874), the counts were: base 8 failed,
635 passed, 20 skipped; mgnp 8 failed, 636 passed, 19 skipped. Both runs had the same 8 baseline
names.

## Dry-runs (login node, mgnp interpreter)

Real configuration, every job whose inputs exist (16): all PASS.

| suite | job | estimate (min) | --time |
| --- | --- | --- | --- |
| far | D__far, H__far_honest | 81.2 | 02:15:00 |
| far | D__far_honest, H__far | 76.6 | 02:00:00 |
| sdr | D__sdr, H__sdr_honest | 81.2 | 02:15:00 |
| sdr | D__sdr_honest, H__sdr | 76.6 | 02:00:00 |
| sdr-coarse | D__sdr, H__sdr_honest | 42.8 | 01:15:00 |
| sdr-coarse | D__sdr_honest, H__sdr | 38.2 | 01:00:00 |
| sdr-coarse | D_hko__sdr, D_hko__sdr_honest, H_hko__sdr, H_hko__sdr_honest | 41.8 | 01:15:00 |

The dry-run TASKS block confirms each test set's condition (e.g. `D__far_honest`:
`task=far condition=honest n=1000` from the FAR H run). Coarse heads-only knockouts ablate
8,832 fine units for D (69 heads x 128) and 7,168 for H (56 heads), with every MLP unit live.

The table above was re-run in `format-control` after landing: 16 of 16 PASS, same estimates.

Awaiting F (38 jobs): every job that binds F or reads the F test set. In `format-control`, they
were dry-run with a stand-in F: H's masks and H's config, with `deception_condition: nopressure`.
That makes `--task-from F` resolve to the real `far_nopressure` / `sdr_nopressure` test sets, for
example `F__far_nopressure: task=far condition=nopressure`. All 38 PASS (`dryrun_standin/`). The
check is plumbing only, since the F circuit is H's. Fine delta jobs (`both`, two cells) estimate 80.2 min; coarse delta jobs 41.8 min; the
stand-in `D_and_F_hko` (= D & H) ablates 5,504 units (43 heads), MLPs all live.

`submit.sh --dry --accounts bgrb-delta-gpu bimc-delta-gpu` prints 16 sbatch lines and a skip line
per F job; no job was submitted.

## Overlap (D/H now; D/F and H/F await F)

| suite | D/H Jaccard heads | heads D / H / both | D/H Jaccard fine units | fine D / H / both |
| --- | --- | --- | --- | --- |
| FAR fine | 0.430 | 48 / 65 / 34 | 0.185 | 5,436 / 10,935 / 2,556 |
| SDR fine | 0.593 | 68 / 69 / 51 | 0.242 | 11,251 / 8,732 / 3,894 |
| SDR coarse (heads, un-expanded masks) | 0.524 | 69 / 56 / 43 | n/a | n/a |

These match the spec's sizes (FAR D 48 heads / 5,436 units, SDR D 68 / 11,251) and the earlier
"51 shared heads" and "3,894-leaf shared core" findings.

## What the orchestrator must give me to launch the real cells

1. The three Format Circuit run directories from ticket 03 (absolute paths), set as `F` in
   `suites.json`; nothing else in the launcher changes.
2. (Done: ticket 01 is merged; `far_nopressure` / `sdr_nopressure` are in the worktree.)
3. Coarse F run post-processed like the D/H runs (`*.coarse.json` copies, then
   `expand_coarse_masks.py`), with the same mask keys as D (no `mlp_blocks`), so `m` composes with it.
4. A ruling on concern 1 (coarse at leaf). Commits go through the orchestrator.
5. I will read each F run's `config.json["data_dir"]` first. D and H record `./data/datasets`, which
   resolves against the submit directory; if ticket 03 recorded an absolute path into its own
   worktree, the F-data cells need `--data-dir` (or the config) pointed at the suite's worktree.

Then: `fc_launch.py plan`, `fc_launch.py dryrun --parallel 4`, `submit.sh --dry`, `submit.sh`,
and per suite `postprocess.sh <suite>`.

## Self-review findings and concerns

1. **Coarse composition is at `leaf`, not the spec's `head` (needs a ruling).** The heads-only coarse
   runs have no `mlp_blocks` key, so `_compose_head` never applies the expression to MLP units and ORs
   them across operands. Checked on the real D, H and `_allmlp_nomb` masks: at `head`, `D - m`,
   `(D & H) - m`, `D - H` and `(D - H) - m` all keep all 458,752 + 131,072 MLP units (a knockout would
   remove every MLP); at `leaf` they keep none, with identical head counts (69, 43, 26, 26). Every live
   head of these masks has all 128 neurons open (verified on D), so leaf set operations are head set
   operations. This is the existing `submit_headsko.sh` / `submit_composed.sh` recipe. Cell labels
   therefore end in `__leaf`; the summary should say "head membership, composed at leaf".
2. Fine delta cells use one job per expression at `--compose-granularity both`; the xor family is
   expanded to explicit `--expr` (same labels as `--xor`), one job per member, so each shard is small
   and the coarse `- m` wrapper applies uniformly. Delta jobs run eval 2 only: eval 3 (the composed
  circuit's own sufficiency null) is deliberately omitted because the ticket defines deltas as
  knockout cells and the decision rule reads eval 2's task-side null. The 2026-09-22 delta suite ran
  evals 1-4; adding `null` to the delta jobs is a one-line change in `fc_cells.py` if wanted.
3. On cross-dataset cells the evaluator skips eval 1 (sanity) by design; faithfulness there is read
   from eval 3's `null.json` (`discovered`, `anchors.full`) and eval 2's `task.circuit`.
4. The `m` operand's `config.json` was copied from the coarse D run, so plans print
   `m:deceptive` as its condition. Cosmetic; `m` is not a circuit of the suite.
5. Walltime is the dry-run estimate (calibrated on 1x A100, "very rough") x 1.5 in quarter hours,
   floor 1 h; the default partition list includes A40. If A40 jobs time out, pass `--time 03:00:00`.
6. `postprocess.sh` calls the placeholder `write_suite_summary.py` from the main checkout's untracked
   `_launch_260922/` until ticket 05's writer lands.
7. Flip audit on H-data and F-data cells: the evaluator's `stayed_deceptive` means "stayed on the
   target", and the target there is the honest answer; the docstring of the copied script says so.
8. On the F test set the evaluator (ticket 01) skips eval 4 and the eval 2 variant rows with a
   recorded reason; the F-data jobs still request evals 1-4 (fine) or sanity/null/pressure (coarse)
   so every job's eval list is uniform, and the end-to-end test asserts the skips.
9. Not run: the code-review skill and the independent review (the orchestrator dispatches it).

## Fix round 1 (review of c73bb21..4e12a1d, two Important findings)

Review: `reports/04-format-control-evaluation-suite-review.md`. Both findings were fixed test-first.

**I1. Job ids were saved only after the whole submit loop.**
- `fc_launch.submit` now takes `save` and calls it after every successful sbatch. A failure later
  in the loop (QOS limit, bad account, Ctrl-C) therefore cannot lose an id that Slurm already holds.
- `main` passes `save_manifest` for real submissions and saves nothing on `--dry`.
- A job that already has an id is skipped unless `--resubmit`, which now also accepts `--force`.
- Test: `test_a_failed_sbatch_mid_loop_keeps_the_ids_already_queued`. The fake `sbatch` raises on
  the third job. The saved manifest then holds the first two ids, and a re-run sends only the
  remaining two jobs.

**I2. Any existing dry-run log counted as a pass.**
- `read_dryruns` now compares the argument string in the log's header with `shlex.join(job_args(job))`.
- On a mismatch the verdict is `passed: None, stale: True`.
- `submit` skips such a job with "dry-run log is for other arguments; dry-run it again".
- Test: `test_a_dry_run_log_counts_only_for_the_arguments_it_ran`. A matching log passes. A log
  written for a different F path is stale, and submit skips that job.

**RED**, base env, before the code change: the two new tests failed, with 34 passing.
- The first failed with `TypeError: submit() got an unexpected keyword argument 'save'`.
- The second failed with `assert True is None` on the stale F log.

**GREEN.** Command:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 <python> -m pytest -p no:cacheprovider -q tests/test_format_control_launch.py
```

| env | result |
| --- | --- |
| base | 36 passed |
| mgnp | 36 passed |

**Real logs still count.** After the change, `fc_launch.py plan` re-read the 16 real dry-run logs:
16 passed and 0 stale. `submit --dry` prints 16 sbatch lines, so the existing logs match their
jobs' current arguments.

**Minor finding 1** is also addressed: the ticket Comments and this report's Status line no longer
say the ruling is open. The other Minor findings (A40 walltime margin, re-merge `--force`, the
head-uniformity check, empty composed circuits, the `m` config label, wider arg-list
parametrisation) are not changed in this round.

## Real-cell phase, SDR suites (2026-10-14)

**Configuration.** F is set in `suites.json` for both SDR suites. FAR F stays null until the
NLS 0.4 retune.
- Fine SDR F: `outputs/llama-8b-instruct_sdr/nls0.3_nopressure_noedge_261013-204850`.
- Coarse SDR F: `outputs/llama-8b-instruct_sdr_coarse/nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_261013-204850`.

**The `m` operand.** It was rebuilt from the coarse F run's expanded mask by the new
`build_allmlp.py` (submit_headsko.sh recipe; one new test) into `outputs/_launch_format_control/allmlp_nomb/`.
Its keys are the same as those of D, H and F: attention blocks, heads and neurons, MLP hidden and
MLP output, with no `mlp_blocks`. Its config is the F run's, so plans print `m:nopressure`.

**Test-set gate.** `evaluate_circuit.py --dry-run` prints only the configured cap (`n=1000`) and
the relative data dir. Each dry-run log therefore now ends with `fc_launch.py testset`: the test
set that `--task-from` resolves to, by the evaluator's own `resolve_train_args` and
`dataset_dir`, with its absolute directory and loaded size. It is covered by the end-to-end test,
including the CLI path.
- The first pass of the dry-runs exposed an argparse bug: subparser REMAINDER rejects `--circuit`.
  The test now covers that path, and the fix dispatches `testset` before argparse.
- All 39 SDR dry-runs were re-run and PASS.
- The 9 F-data cells all show `condition=nopressure n_test=520 dir=<format-control>/data/datasets/sdr_nopressure`:
  D, H and F on the fine suite, D, H and F on the coarse suite, and D_hko, H_hko and F_hko.
- Every D-data cell shows `n_test=1000` from `data/datasets/sdr`. Every H-data cell shows
  `n_test=1000` from `data/datasets/sdr_honest`.

**Coarse knockout gate.** Each of the 15 coarse knockout and delta cells has exactly one
"fine units ablated" line, and no log has a key-mismatch error or traceback. Every count is a
multiple of 128 (head-uniform), with mlp_hidden at 458,752 live (100%).

| cell | fine units ablated | heads |
| --- | --- | --- |
| D_hko | 8,832 | 69 |
| H_hko | 7,168 | 56 |
| F_hko | 8,704 | 68 |
| D_minus_F_hko | 4,224 | 33 |
| D_and_F_hko | 4,608 | 36 |
| F_minus_D_hko | 4,096 | 32 |
| D_minus_H_minus_F_hko | 2,816 | 22 |
| H_minus_D_minus_F_hko | 256 | 2 |
| F_minus_D_minus_H_hko | 2,688 | 21 |

No fine delta circuit is empty.

| fine delta | leaf units | head units |
| --- | --- | --- |
| D-F | 5,769 | 739 |
| D&F | 5,482 | 15,494 |
| F-D | 6,400 | 1,418 |
| D\H\F | 5,263 | 704 |
| H\D\F | 1,636 | 328 |
| F\D\H | 3,198 | 523 |

**Submission.** 39 jobs on `gpuA40x4,gpuH200x8`, alternating beto-delta-gpu and bgrb-delta-gpu.
Each job id was saved in `suite_manifest.json` as it was queued.

| suite | jobs | Slurm ids | beto / bgrb | --time |
| --- | --- | --- | --- | --- |
| SDR fine | 15 | 22895954-22895968 | 8 / 7 | 04:00:00 |
| SDR coarse | 24 | 22895970-22895973 and 22895977-22895996 | 12 / 12 | 02:30:00 |

Both walltimes are generous by choice, given the A40 margin noted in the review.
`sbatch --test-only` estimated a start of Oct 17 for beto and bgrb and Oct 19 for bimc.

**Tests at 71e4c7e:**

| env | full suite | launcher tests |
| --- | --- | --- |
| base | 8 failed, 818 passed, 20 skipped | 37 passed |
| mgnp | 8 failed, 819 passed, 19 skipped | 37 passed |

Both envs fail only the 8 baseline names.

## Real-cell phase, FAR suite (2026-10-14)

**F run.** The orchestrator ruled that FAR F is the NLS 0.3 run,
`outputs/llama-8b-instruct_far/nls0.3_nopressure_noedge_261013-203424`. The size rule's NLS 0.4
retune, `nls0.4_nopressure_noedge_261014-081312`, failed the in-run gate (KL 0.214) and is not
carried.

**Side job.** The NLS 0.4 retune is evaluated as a side job outside the grid. It is declared in
`suites.json` `_side_jobs`, with arguments from `fc_cells.side_job_args`, and was added test-first
with two new tests.
- It runs evals sanity and knockout on the FAR D test set, writing to
  `outputs/_suites/format-control-far-nls0.3/_side_F04/`.
- It is recorded under the manifest's `side_jobs` key, never in the `cells` index.
- Eval 1 skips by design here, because the circuit is not on its own run's test set. Its
  sufficiency on D data is therefore the knockout eval's circuit-alone row (`task.circuit`).

**Dry-runs.** All 16 FAR jobs pass (15 grid jobs and the side job). The 3 F-data cells show
`condition=nopressure n_test=500 dir=<format-control>/data/datasets/far_nopressure`. No fine delta
circuit is empty; the smallest is H\D\F, with 225 head-granularity units (3,477 at leaf).

**Submission.** 16 jobs, ids 22906787-22906802, 8 on beto and 8 on bgrb, partitions
gpuA40x4 and gpuH200x8, `--time 04:00:00`. The side job is 22906802.

**Tests.** Launcher tests: 39 passed in the base env and in mgnp.

## SDR results (2026-10-15)

All 39 SDR jobs completed. `postprocess.sh` merged both suites: fine 21 cells and coarse 24, with
0 pending and 0 missing. It also wrote the flip audit, the overlap table, and ticket 05's
`evaluation_summary.md` / `decision.json`, all evaluated on eval 2 alone.

**Verdicts.**

| suite | verdict | why |
| --- | --- | --- |
| SDR fine | (c) | F's knockout wikitext KL fails the 0.66 gate |
| SDR coarse heads-only | (a) | all four conditions pass |

**SDR fine.** Every atomic knockout takes accuracy to at most 0.002 on every test set, and all
are outside their nulls. The deltas on D data, head-primary, have these knockout accuracies:

| delta | knockout accuracy |
| --- | --- |
| D-F | 0.942 |
| D&F | 0.000 |
| F-D | 0.807 |
| D\H\F | 0.939 |
| H\D\F | 1.000 (not outside its null) |
| F\D\H | 0.996 |

**SDR coarse heads-only.** Every heads-only knockout takes accuracy to at most 0.002, and all are
outside their nulls.

| delta | knockout accuracy |
| --- | --- |
| D-F | 0.119 |
| D&F | 0.002 |
| F-D | 0.598 |
| D\H\F | 0.782 (not outside its null) |
| H\D\F | 1.000 |
| F\D\H | 0.965 |

**Collateral and overlap.**

| suite | knockout wikitext KL D / H / F | Jaccard heads D/H, D/F, H/F | Jaccard fine units D/H, D/F, H/F |
| --- | --- | --- | --- |
| SDR fine | 1.383 / 0.694 / 1.342 | 0.593, 0.584, 0.775 | 0.242, 0.311, 0.470 |
| SDR coarse | 0.364 / 0.275 / 0.279 | 0.524, 0.356, 0.531 | n/a (heads only) |

**Flip audit.** All 36 knockout cells are row-aligned with their test set, and every one is a
content-driven flip. No cell is a positional default.

**Verification warnings.** These are non-strict, logged in the jobs, and tiny.
- A non-zero all-gates-open wikitext floor, KL 6.3e-4 to 6.6e-4, in 34 knockout cells.
- 2 sanity cells on H200 miss the in-run numbers by one tolerance step: fine D accuracy +0.002
  against a tolerance of 0.002, and F on F data logit diff +0.0115 against 0.01.

**Manifest.** It now records `time_limit_actual` and `time_limit_note` for the 52 jobs whose limits
the orchestrator lowered in place. The commit request excludes `_shards/` (55 MB, a duplicate of
`cells/`) and `logs/` (gitignored).

## Review fixes after the SDR real-cell review (approved; one Minor)

**"no flip".** A knockout that flips no item now reads "no flip" in the flip audit, not
"content-driven flip". This was fixed test-first, with one new test; the end-to-end test now accepts
"no flip". Both SDR audits and summaries were regenerated without re-running any cell, and the
verdicts are unchanged. Three cells read "no flip": the H\D\F delta in the fine suite at head and
at leaf, and in the coarse suite.

**record-slurm.** At the orchestrator's request, `fc_launch.py record-slurm` (test-first) records each
job's sacct state, the partition and node it ran on (`ran_on`), and any time limit lowered in
place. SDR fine ran 12 jobs on H200 and 3 on A40. SDR coarse and FAR ran entirely on A40.

## FAR results (2026-10-15)

All 16 FAR jobs completed on A40. The suite is merged (21 cells, 0 pending, 0 missing), with
flip audit, overlap and summary.

**Verdict: (c)** on eval 2 alone, because F's knockout fails the gate. Two other conditions fail
as well: collateral (F 4.265 against D 0.327) and the honest_instruction row (F -0.680 against
D -0.682).

| circuit | knockout wikitext KL | gate 0.66 |
| --- | --- | --- |
| D | 0.327 | passes |
| H | 2.784 | fails |
| F | 4.265 | fails |

**Knockouts.** Every atomic knockout takes accuracy to at most 0.004 on every test set, outside its
null. The deltas, head-primary, have these knockout accuracies, all outside their nulls:

| delta | knockout accuracy |
| --- | --- |
| D-F | 0.504 |
| D&F | 0.000 |
| F-D | 0.155 |
| D\H\F | 0.775 |
| H\D\F | 0.988 |
| F\D\H | 0.588 |

**Flip audit.** 3 leaf deltas are positional defaults: D-F, D\H\F and F\D\H, with P(KO picks
item_2) of 0.79 / 0.71 / 0.71 against a base of 0.48. Their head-primary versions are content-driven.

**Overlap.**

| pair | Jaccard heads | Jaccard fine units |
| --- | --- | --- |
| D/H | 0.430 | 0.185 |
| D/F | 0.340 | 0.166 |
| H/F | 0.652 | 0.407 |

**Pairing caveat.** The writer reports `far_nopressure` is 98% honest-split fallback instances. FAR
F-data cells are therefore not instance-paired with D data.

**F04 side job** (22906802; the NLS 0.4 retune, not carried; on the D test set). Its knockout KL
also fails the gate.

| measure | value |
| --- | --- |
| circuit-alone accuracy | 0.782 |
| knockout accuracy | 0.000 |
| null mean / p5 | 0.668 / 0.412 |
| null z | -3.21 |
| knockout wikitext KL | 2.317 |

**Tests at 4082241.** Both envs fail only the 8 baseline names. The closing Comments are in the
ticket, and Status stays `claimed` until the orchestrator's review.

| env | full suite | launcher tests |
| --- | --- | --- |
| base | 8 failed, 845 passed, 20 skipped | 41 passed |
| mgnp | 8 failed, 846 passed, 19 skipped | 41 passed |
