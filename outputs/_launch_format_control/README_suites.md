# Format-control evaluation suites (ticket 04)

Three suites under `outputs/_suites/`, one per task family, over the deceptive
circuit **D**, its Honest Twin **H** and the Format Circuit **F** (pruned on the
`nopressure` condition):

| suite | family | D / H | F |
| --- | --- | --- | --- |
| `format-control-far-nls0.3` | fine | FAR nls0.3 deceptive / honest | ticket 03 |
| `format-control-sdr-nls0.3` | fine | SDR nls0.3 deceptive / honest | ticket 03 |
| `format-control-sdr-coarse-nls0.3` | coarse heads-only | SDR coarse nls0.3 deceptive / honest | ticket 03 |

Settings everywhere: interchange ablation, `--n-random 20 --knockout-null-count 20`,
everything else at the evaluator's defaults (wikitext collateral, 3 greedy
generations, eval 2 variant rows).

## Files

| file | what |
| --- | --- |
| `suites.json` | the one configuration point: D, H, F run directories per suite (F is `null` until ticket 03), and the coarse `m` operand |
| `fc_cells.py` | the pure cell-command generator (`plan_suite`, `job_args`), walltime rule, dry-run log parser |
| `fc_launch.py` | `plan`, `args`, `dryrun`, `standin-dryrun`, `submit`, `merge`, `overlap` |
| `suite_manifest.json` | every job and cell, its arguments, dry-run verdict and estimate, Slurm job id |
| `cell_cmd.sh` / `submit.sh` | thin wrappers over `fc_launch.py args` / `fc_launch.py submit` |
| `merge_shards.py` | the cross-task rerun's merge, filing cells by test set (see below) |
| `flip_audit_analysis.py` | the cross-task rerun's flip audit with the positional-default check; `is_delta` reads operands |
| `overlap.py` | Jaccard over heads and pooled fine units for D/H, D/F, H/F |
| `postprocess.sh` | merge, flip audit, overlap, then `write_format_control_summary.py` (ticket 05: summary and verdict) for one suite |
| `README_suites.md` | this file (named apart from ticket 03's launcher files in the same directory) |
| `dryrun/<suite>/<job>.log` | login-node `--dry-run` logs of the real jobs |
| `dryrun_standin/<suite>/<job>.log` | plumbing-only dry-runs with F := H, before the Format Circuits exist |
| `logs/<suite>/` | Slurm output (git-ignored) |

## Cells

**Fine suites** (15 jobs, 21 cells each):

- 9 atomic jobs `X__<dataset>` for X in D, H, F and the D, H, F test sets
  (`<task>`, `<task>_honest`, `<task>_nopressure`, bound with `--task-from` on
  the D, H, F run directories). Evals 1-4 in one model load, so each job is
  both the faithfulness cell and the knockout cell (eval 2 with task null,
  wikitext, variant rows and generations). On the F test set, which already
  is the no-pressure condition, the evaluator skips the eval 2 variant rows
  and eval 4 with a recorded reason (`knockout.json` `variants.<v>.skipped`,
  `summary.json` `skipped.pressure`); the jobs request the same evals anyway.
- 6 delta jobs on the D test set, eval 2 only, `--compose-granularity both`
  (cells `<label>__leaf` and `<label>__head`; head is primary): `D_minus_F`,
  `D_and_F`, `F_minus_D`, and the `--xor D,H,F` family expanded to explicit
  expressions with the evaluator's own labels (`D_minus_H_minus_F`,
  `H_minus_D_minus_F`, `F_minus_D_minus_H`), one job each. Eval 3 (the
  composed circuit's own sufficiency null) is deliberately not run on delta
  cells: the ticket defines them as knockout cells, and the decision rule reads
  eval 2 with its task-side null. The 2026-09-22 delta suite ran evals 1-4;
  pass `null` in the delta jobs' evals in `fc_cells.py` if delta sufficiency
  is wanted.

**Coarse suite** (26 jobs, 30 cells: 24 planned for every coarse suite, plus 6 extra deltas packed into 2 jobs):

- 9 sufficiency jobs `X__<dataset>`: the atomic (expanded) circuit, evals
  sanity, null, pressure. No knockout: an expanded coarse mask contains every
  MLP unit, so its knockout removes all 32 MLPs.
- 9 heads-only knockout jobs `X_hko__<dataset>`: `--expr X_hko=(X) - m`.
- 6 delta jobs on the D test set: `--expr <label>_hko=(<expr>) - m`.
- Every coarse knockout composes at **leaf**, not head: the heads-only runs
  have no `mlp_blocks` gate, so `head` composition ORs the operands' MLP units
  and keeps all 589,824 of them in every expression (checked on the real D, H
  and `m` masks: `D - m`, `(D & H) - m`, `D - H` all keep every MLP unit at
  `head`, none at `leaf`, with identical head counts 69, 43, 26). Every live
  head of these masks has all its neurons open, so leaf set operations are
  head set operations. Same recipe as `llama-8b-instruct_sdr_coarse/_launch/
  submit_headsko.sh` and `submit_composed.sh`. This is a deliberate deviation
  from the spec's literal "coarse at head" (orchestrator ruling 2026-10-13);
  summaries report these cells at head level.

**Extra deltas** (researcher request 2026-10-16). A suite's `suites.json` entry
may list `"extra_deltas": [[label, expr], ...]`; `fc_cells.plan_suite` plans
them after the xor family exactly like the built-in deltas (fine: one job,
`--compose-granularity both`, cells `<label>__leaf` / `<label>__head`; coarse:
`--expr <label>_hko=(<expr>) - m` at leaf, cell `<label>_hko__leaf`), all
knockout cells with role `delta` on the D test set. Only
`format-control-sdr-coarse-nls0.3` lists any: `H_and_F` (`H & F`), `H_minus_F`
(`H - F`), `D_and_H_minus_F` (`(D & H) - F`), `D_and_F_minus_H` (`(D & F) - H`),
`H_and_F_minus_D` (`(H & F) - D`), `D_and_H_and_F` (`D & H & F`). A row's
optional third element is a job group: rows sharing it run as ONE job
`<group>__<D dataset>` with one `--expr` per row and one ordinary delta cell
per row, so merge, flip audit and summary see ordinary delta cells. The coarse
suite packs them as `xdeltas_a__sdr` (H_and_F, H_minus_F, D_and_H_and_F) and
`xdeltas_b__sdr` (D_and_H_minus_F, D_and_F_minus_H, H_and_F_minus_D), because
the H200 interactive partition allows one job per user at a time (scope
refinement 2026-10-16). The evaluator writes each cell's `knockout.json` and
`summary.json` as the cell finishes, but `matrix.json` only at the end of the
job, and the merge takes a shard only once `matrix.json` exists. They are not
in the global `DELTAS`, so the FAR and SDR-fine suites keep exactly their jobs
and cells. The summary writer and the flip audit pick the new cells up from
the manifest's cells index (role `delta`) and from the cells' operands, with
no hardcoded labels.

`suite_manifest.json` has a per-suite `cells` index (circuit, dataset,
condition, roles, job, path) so a reader finds a cell by (circuit, test-set
condition).

## Task labels and the merge

With one `--task-from` per job the evaluator labels every test set by the bare
task name (`far`), so the D, H and F test sets of one circuit would collide in
`cells/<circuit>/far/`. `merge_shards.py` files each cell under its test set's
directory name, read from the shard's own task provenance
(`dataset.deception_condition`): `cells/<circuit>/{far,far_honest,far_nopressure}/interchange/`.
That is also the directory `flip_audit_analysis.py --data-dir data/datasets`
loads, and its prompt-excerpt alignment check confirms it per cell. With
`--manifest` (as `fc_launch.py merge` passes it) each shard must produce
exactly the cells the manifest planned.

## Workflow

Run everything from the worktree root.

```
# 1. set F in suites.json to the ticket 03 run directories, then
python outputs/_launch_format_control/fc_launch.py plan
# 2. login-node dry-runs (1-8 min each under load), logs under dryrun/
python outputs/_launch_format_control/fc_launch.py dryrun --parallel 4
# 3. check the sbatch lines, then submit (job ids land in suite_manifest.json)
bash outputs/_launch_format_control/submit.sh --dry --accounts bgrb-delta-gpu bimc-delta-gpu
bash outputs/_launch_format_control/submit.sh --accounts bgrb-delta-gpu bimc-delta-gpu
# 4. per suite, after its jobs finish
bash outputs/_launch_format_control/postprocess.sh format-control-far-nls0.3
```

Until the Format Circuit runs exist, `fc_launch.py standin-dryrun` dry-runs
every F-dependent job with a stand-in F (plumbing only; logs under
`dryrun_standin/`): by default the H run, or with `--f-run SUITE=DIR` a copy of
the H run whose `config.json` says `deception_condition: nopressure`, so the F
test set really is `<task>_nopressure`.
