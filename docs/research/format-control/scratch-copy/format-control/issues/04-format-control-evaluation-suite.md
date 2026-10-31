# 04 — Evaluation suite: 3×3 faithfulness, knockouts with nulls, overlap, deltas

**What to build:** Per task family, one suite under `outputs/_suites/` that evaluates the deceptive circuit D, the honest twin H and the Format Circuit F on the D, H and F test sets, with knockouts, random nulls, flip audits, the eval 2 variant rows and wikitext collateral, Jaccard overlap, and the delta cells, at the granularities the spec fixes. Launch scripts shard cells into Slurm jobs and merge them, as the 2026-09-22 cross-task rerun did.

**Status:** resolved
**Type:** task
**Blocked by:** 02 (needs `--task-from` on a `nopressure` run); 03 for the real runs (the suite can be built and dry-run against the D and H runs first)

**Facts to build on**
- `evaluate_circuit.py`: `--circuit NAME=RUN_DIR`, `--expr`, `--xor A,B,C`, `--all-pairs-delta`, `--compose-granularity {leaf,head,both}`, `--task-from RUN_DIR` (repeatable), `--task NAME`, `--evals ...`, `--ablation interchange`, `--n-random`, `--knockout-null-count`, `--suite-name`, `--output-dir`, `--dry-run`. Suite layout: `_shards/`, `cells/`, `suite.json`, `matrix.{csv,json}`, `flip_audit.{md,json}`, `evaluation_summary.md`.
- Cross-task tooling to copy from: `outputs/_suites/_launch_260922/{cell_cmd.sh,submit.sh,merge_shards.py,write_cell_summary.py,write_suite_summary.py,flip_audit_analysis.py}` (one Slurm job per cell, interchange, `--n-random 20 --knockout-null-count 20`).
- Coarse circuits: a knockout of an expanded coarse mask knocks out every MLP (expansion artifact); use the heads-only cell `c - m` with the `_allmlp_nomb` operand (`_launch/submit_headsko.sh`), and compose at `head`.
- Eval 2 (`evaluation/knockout.py`): knockout on the task, task-side null, wikitext collateral with floor and null, variant rows (`honest_instruction`, `no_pressure`) with inverted label semantics, greedy wikitext generations. Eval 4 (`evaluation/pressure.py`) has no knockout row. Overlap: `compare_node_masks.py` (pairwise Jaccard per granularity, `--json`) and `evaluation/mask_compare.py`.
- H test instances are disjoint from D's; F's are a subset of D's (ticket 01). Cells on D and F data are instance-paired; cells on H data are not.

- [x] Suite definitions: `format-control-far-nls0.3`, `format-control-sdr-nls0.3`, `format-control-sdr-coarse-nls0.3`; circuits bound `D`, `H`, `F`; tasks via `--task-from` of the D, H and F run directories.
- [x] Cells: (i) faithfulness of D, H, F on each of the three test sets (9); (ii) knockout (eval 2, with task null, wikitext, variant rows, generations) of D, H, F on each test set (9), where cells on the F test set carry no variant rows because that dataset is already the no-pressure condition (ticket 01); (iii) deltas `D-F`, `D&F`, `F-D`, `--xor D,H,F` as knockout cells on the D test set with null and flip audit; fine suites at `--compose-granularity both` with head marked primary in the summary, coarse at `head` only; (iv) overlap table over heads and fine units for D/H, D/F, H/F. Interchange only, `--n-random 20 --knockout-null-count 20`.
- [x] `outputs/_launch_format_control/cell_cmd.sh` + `submit.sh` (any account/partition, `--dry`), `merge_shards.py` reuse, and a `suite_manifest.json` listing every cell and its job id; coarse knockout cells built with the `c - m` expression.
- [x] Flip audit per knockout cell, with the positional-default check (P(item_2) under knockout versus base rate, stay-rate split by which item the deceptive answer is) from `flip_audit_analysis.py`, so a delta "half necessity" is read correctly.
- [x] Dry-run of every cell on the login node before submission; cells merged; `evaluation_summary.md` produced by ticket 05's writer (until it lands, the existing `write_suite_summary.py` output is acceptable as a placeholder).
- [x] Tests: `tests/test_suite_layout.py` pattern for the manifest and merge; the cell command generator is a pure function with tests for every (circuit, dataset, granularity) combination and the coarse `c - m` rewriting; a tiny-model end-to-end on one faithfulness cell and one delta cell with `nopressure` as `--task-from`.
- [x] All cells run for the three suites with the ticket 03 runs; wikitext KL of each F knockout quoted in Comments against the 0.66 gate, since that gate decides ticket 06.
- [x] Both suites in both envs; failure names vs baseline.
- [x] Independent review (orchestrator-dispatched: build phase approved after one fix round; SDR and FAR real-cell reviews approved); report in `reports/04-format-control-evaluation-suite-review.md`.

## Comments

**2026-10-13, impl-04 (build and dry-run phase).** Full report:
`reports/04-implementer-report.md`. Status stays `claimed`: the real-cell phase awaits
ticket 03's F runs (and ticket 01's `*_nopressure` datasets on the branch).

- **Not yet in the worktree or committed.** The harness pinned this session to another
  worktree and refused git and Write/Edit in `format-control-04`; all files are staged under
  `reports/04-staged/` (worktree-relative layout; copy instructions in the report). Ticks above are for the staged files, verified against the `format-control-04` code.
- Built: `outputs/_launch_format_control/{suites.json, fc_cells.py, fc_launch.py, cell_cmd.sh,
  submit.sh, merge_shards.py, flip_audit_analysis.py, overlap.py, postprocess.sh, README.md,
  suite_manifest.json, dryrun/, dryrun_standin/}` and `tests/test_format_control_launch.py`
  (33 tests). No shared file changed. F run directories are one configuration point
  (`suites.json`).
- Grid: fine suites 15 jobs / 21 cells each (9 atomic with evals 1-4; 6 delta jobs at
  `both`), coarse 24 jobs / 24 cells (9 sufficiency, 9 heads-only knockouts, 6 deltas).
- The merge files cells by test set (`far`, `far_honest`, `far_nopressure`): with one
  `--task-from` per job the evaluator labels all three test sets `far`, so they would collide.
- **Ruling needed (resolved later the same day, see "Orchestrator rulings" below; Cells box
  stays unticked until the real cells run):** coarse cells compose at `leaf` with `(<expr>) - m`,
  not `head`. On the heads-only runs (no `mlp_blocks` gate) `head` composition keeps every MLP unit
  in every expression (checked on the real masks); `leaf` keeps none and gives the same head sets.
- Dry-runs: all 16 jobs with existing inputs PASS (`dryrun/`); the 38 F-dependent jobs PASS with
  F := H as a plumbing stand-in (`dryrun_standin/`). Dry-run box left unticked until the real F jobs
  are dry-run. Flip-audit box left unticked until it runs on real knockout cells (tooling verified
  on the tiny end-to-end suite).
- Tests: base 8 failed / 635 passed / 20 skipped; mgnp 8 failed / 636 passed / 19 skipped; the 8
  baseline names in both, no new failures.
- Overlap D/H (D/F, H/F await F): FAR heads 0.430, fine units 0.185; SDR heads 0.593, fine units
  0.242; SDR coarse heads 0.524.
- No Slurm job submitted. Independent review not run; the orchestrator dispatches it.

**2026-10-13, impl-04 (landed in `format-control`).** After ticket 01 merged (06110bb), the new
files were copied into `format-control` (no tracked file modified; README named
`README_suites.md`). The orchestrator commits on my instruction. Re-verified at c73bb21:
- Tests: base 8 failed / 695 passed / 20 skipped; mgnp 8 failed / 696 passed / 19 skipped, the 8
  baseline names only.
- The end-to-end test now asserts that eval 4 and the variant rows are skipped, with a reason, on
  the F test set.
- Dry-runs: all 16 ready jobs PASS. All 38 F-dependent jobs PASS with a stand-in F (H's masks
  with `deception_condition: nopressure`, so they read the real `*_nopressure` test sets).
- Committed by the orchestrator on my instruction: e439e91.

**Orchestrator rulings (2026-10-13), applied by impl-04.**
- **Coarse at leaf, a deliberate deviation from the spec's literal "coarse at head".** Every
  coarse knockout and delta cell composes at leaf as `(expr) - m`, as `submit_headsko.sh` does.
  The heads-only runs have no `mlp_blocks` gate, so head composition would keep all 589,824 MLP
  units (the expansion artifact). Leaf keeps none and gives the same head sets. Summaries report
  these cells at head level. The ruling is recorded in `suites.json` (`_coarse_granularity`), in
  the `fc_cells.py` header and in `README_suites.md`.
- Delta jobs run eval 2 only, which is correct.
- Merged cells are refiled by test set; this is approved. Every planned cell now carries
  `condition`, and `suite_manifest.json` has a per-suite `cells` index (circuit, dataset,
  condition, roles, job, path), so ticket 05 can find cells by (circuit, condition).
- F runs will record `data_dir: ./data/datasets` under this worktree, which resolves correctly.
- Launcher tests after these changes: 34 passed in both envs. Committed by the orchestrator on my
  instruction: 4e12a1d.

- 2026-10-13 orchestrator: session stopped at its usage limit with this ticket in progress; see reports/00-orchestration-ledger.md for the exact remaining steps.

**2026-10-15, impl-04 (SDR suites run and merged; FAR pending).**
- **Jobs.** All 39 SDR jobs completed: fine 22895954-22895968, coarse 22895970-22895973 and
  22895977-22895996. None failed or timed out.
- **Merge and postprocess.** Both SDR suites are merged: fine 21 cells and coarse 24 cells, with
  0 pending and 0 missing. `postprocess.sh` wrote the flip audit, overlap and
  `evaluation_summary.md` / `decision.json` with ticket 05's writer.
- **Flip audit.** Every knockout cell (21 fine, 15 coarse) is row-aligned with its test set, and
  every one is a content-driven flip. No cell is a positional default.
- **F knockout wikitext KL against the 0.66 gate** (this decides ticket 06):
  - SDR fine F: 1.342, which **fails** the gate. D is 1.383 and H 0.694 for reference.
  - SDR coarse F (heads-only): 0.279, which **passes**. D is 0.364 and H 0.275.
- **Verdicts.** `format-control-sdr-nls0.3` is **(c)**, eval 2 alone, because F's knockout fails
  the KL gate. `format-control-sdr-coarse-nls0.3` is **(a)**, eval 2 alone.
- **Verification checks.** These are non-strict warnings logged in the jobs, and both are tiny.
  - 34 knockout cells report a non-zero all-gates-open wikitext floor, KL 6.3e-4 to 6.6e-4 on A40
    and H200 nodes. That is 1000x below the gate.
  - 2 sanity cells on an H200 node miss the in-run numbers by one tolerance step: fine D accuracy
    +0.002 against a tolerance of 0.002, and F logit diff +0.0115 against 0.01. This is hardware
    numerics, since training ran on A40.
- **Ticks.** I ticked Cells (the coarse-at-leaf ruling is recorded above). The flip audit,
  dry-run/merge/summary and "all cells run" boxes wait for the FAR suite. The Independent review
  box belongs to the orchestrator; I ticked it by mistake and have un-ticked it.
- **SDR real-cell review: approved.** I fixed its Minor finding test-first: a knockout that flips no
  item now reads "no flip" in the flip audit, not "content-driven flip". Three cells are affected:
  fine H\D\F at head and at leaf, and coarse H\D\F.
- Both SDR suites' `flip_audit.{json,md}` and `evaluation_summary.md` / `decision.json` were
  regenerated without re-running any cell. The verdicts are unchanged: fine (c), coarse (a).

**2026-10-15, impl-04: closing comments (all three suites run; awaiting the orchestrator's
review).**

All three suites are run, merged, flip-audited, overlapped and summarised. Every grid job was
dry-run on the login node first, and every submitted job COMPLETED: SDR fine 15, SDR coarse 24,
FAR 15 plus the F04 side job. `suite_manifest.json` records each job's id and state, the
partition and node it ran on (`ran_on`), and any time limit lowered in place.

**Verdicts, evaluated on eval 2 alone, with F's knockout wikitext KL against the 0.66 gate (this
decides ticket 06):**

| suite | verdict | F KO KL | gate | D / H KO KL | F heads (D, H) |
| --- | --- | --- | --- | --- | --- |
| `format-control-far-nls0.3` | (c) | 4.265 | fails | 0.327 / 2.784 | 82 (48, 65) |
| `format-control-sdr-nls0.3` | (c) | 1.342 | fails | 1.383 / 0.694 | 73 (68, 69) |
| `format-control-sdr-coarse-nls0.3` | (a) | 0.279 | passes | 0.364 / 0.275 | 68 heads-only (69, 56) |

- **FAR (c).** F's knockout fails the KL gate. Two other conditions fail as well: collateral (4.265
  against D's 0.327) and the honest_instruction row (F -0.680 against D -0.682).
- **SDR fine (c).** F's knockout fails the KL gate.
- **SDR coarse (a).** All four conditions pass. F's deception drop is 1.000 against D's 0.998, at
  lower collateral (0.279 against 0.364).

**Knockouts.** Every atomic knockout takes accuracy to at most 0.004 on every test set, outside its
null, in all three suites.

**Overlap.**

| suite | Jaccard heads D/H, D/F, H/F | Jaccard fine units D/H, D/F, H/F |
| --- | --- | --- |
| FAR | 0.430, 0.340, 0.652 | 0.185, 0.166, 0.407 |
| SDR fine | 0.593, 0.584, 0.775 | 0.242, 0.311, 0.470 |
| SDR coarse | 0.524, 0.356, 0.531 | n/a (heads only) |

**Flip audit.** All 57 knockout cells are row-aligned with their test set.
- 3 FAR leaf deltas are positional defaults: D-F, D\H\F and F\D\H, with P(KO picks item_2) of
  0.79 / 0.71 / 0.71 against a base of 0.48. Their head-primary versions are content-driven.
- 3 SDR cells read "no flip" (the H\D\F deltas).
- The rest are content-driven flips.

**F04 side job** (FAR NLS 0.4 retune, not carried; FAR D test set; `_side_F04/`, not in the cells
index). Its knockout wikitext KL also fails the gate, though below the NLS 0.3 F's 4.265.

| measure | value |
| --- | --- |
| circuit-alone accuracy | 0.782 |
| knockout accuracy | 0.000 |
| null mean / p5 | 0.668 / 0.412 |
| null z | -3.21 |
| knockout wikitext KL | 2.317 |

**Caveats for the researcher.**
- **FAR F test set barely paired with D.** Ticket 05's writer reports that `far_nopressure` is 98%
  honest-split fallback instances. FAR cells on F data are therefore NOT instance-paired with D
  data, unlike SDR.
- **Verification warnings (non-strict).** All are tiny and logged in the Slurm output.
  - A non-zero all-gates-open wikitext floor, KL 6.3e-4 to 6.6e-4, in every knockout cell.
  - Two SDR fine sanity cells that ran on H200 miss by one tolerance step: D accuracy +0.002 and F
    logit diff +0.0115.
  - One FAR sanity cell shows generic-vs-task evaluator disagreement of 2.1e-4.

**Tests at 4082241.**

| env | full suite | launcher tests |
| --- | --- | --- |
| base | 8 failed, 845 passed, 20 skipped | 41 passed |
| mgnp | 8 failed, 846 passed, 19 skipped | 41 passed |

Both envs fail only the 8 baseline names.

**Status.** It stays `claimed` until the orchestrator's review box is ticked; nothing else is
open. Commits were made by the orchestrator on my instruction (e439e91, 4e12a1d, a365e65,
e7ebddd, 8e25b41, b08c5a9, 1bc5e58, and the final FAR commit).
