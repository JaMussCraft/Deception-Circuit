# 12 — First SDR run and result write-up

**What to build:** The full pipeline run on the SDR nls0.3 deceptive circuit with its honest twin as reference circuit and the Honest-Instruction Counterfactual enabled, followed by a result summary in the style of the existing evaluation summaries: the head table with proposed roles, the composition structure, what the pre-registered hypothesis got right and wrong, and what to run next.

**Blocked by:** 10 — Role vocabulary and proposal step; 11 — Parameterized review notebook.

**Status:** resolved

- [x] All analyses run via Slurm within the short-job budget, split across jobs if needed; every output file present and schema-valid.
- [x] Role proposal step run; the researcher's confirmation column left empty for them to fill.
- [x] `result_summary.md` in the cell directory: executive summary, head table excerpt, composition diagram or table, hypothesis check, caveats, next steps (including the FAR rerun after polarity rebalancing).
- [x] Notes on runtime per analysis recorded so later runs can be budgeted.
- [x] Subagent review of the write-up for claims not supported by the outputs.

## Comments

### What was run

Five Slurm jobs, all `gpuA40x4`, one A40 each, every one rehearsed with
`--dry-run` on the login node first and submitted from the ca-12 worktree root
with `--time` on the `sbatch` command line. No job exceeded an hour and none
was an H200.

| job | what it ran | node | elapsed |
|---|---|---|---|
| 22240028 | `attention_patterns,dla,knockout`, `--dla-split designation`, both paired conditions | gpub100 | 10:32 |
| 22240066 | `path_patching --path-counterfactual item_swap --path-position-threshold 0.01` | gpub048 | 19:03 |
| 22240067 | `path_patching --path-counterfactual honest_instruction --path-position-threshold 0.01` | gpub100 | 14:16 |
| 22240068 | `path_patching --path-completeness-sweep`, `--n-causal 64`, `--path-sweep-threshold 0.05` | gpub042 | 41:44 |
| 22281702 | `knockout --knockout-families --knockout-roles-from <cell>` | gpub058 | 2:16 |

Two jobs were cancelled before they ran and resubmitted at shorter `--time`,
because the scheduler estimated the longer requests for the following day: one
`--path-counterfactual both` job at 55 minutes became 22240066 and 22240067 at
25 minutes each, and a 20-minute family job became 22281702 at 10 minutes. The
partition was backlogged throughout (over 2000 pending jobs on each of
`gpuA40x4` and `gpuA100x4`), and queue time dominated: the four analysis jobs
waited between 12 minutes and 13 hours. **Shorter `--time` requests backfill
sooner, and this is the single most useful scheduling fact from the ticket.**

Every job's `--dry-run` was clean, no log contains an error or a CUDA
out-of-memory, and no `core.*` dump appeared.

### Cell paths, for the orchestrator to copy

- **The cell of record:**
  `Deception-Circuit/.claude/worktrees/ca-12/outputs/_analyses/sdr-first-run/delta__head/sdr/`
  — head table with every analysis's columns plus `roles.*` and the two
  `knockout.role_family*` columns, `result_summary.md`, and the `attention/`,
  `dla/`, `knockout/`, `path_patching/` and `roles/` directories.
- **The completeness sweep:** `.../outputs/_analyses/sdr-first-run-sweep/delta__head/sdr/`
  — kept separate on purpose (see the open questions).
- **The staging cells**, one per job, are `sdr-first-run-desc`,
  `sdr-first-run-paths`, `sdr-first-run-paths-hi` and `sdr-first-run-family`
  under the same `outputs/_analyses/`. They are what the cell of record was
  assembled from and what section 8's per-analysis timings were read from.

### The result, in four lines

- **Roles: 0 binder, 0 selector, 1 mover (L31 MLP), 0 suppressor, 17 unknown**,
  which is ticket 10's roles of record re-derived from this run's own analyses.
- **Every head-table value shared with the outputs of record is byte-identical**
  — 315 of 315 attention and DLA against `ca06-paired2`, 72 of 72 knockout
  against `ca07-knockout`, 216 of 216 path patching against
  `ca09-path-patching` — and the family job's eighteen single-Component drops
  are bit-identical to job 22240028's.
- **Family knockout:** the seventeen `unknown` Components together drop the
  logit difference by **+0.9500** and accuracy to **0.63**; the one-member
  `mover` family drops it by +0.3065 at accuracy 0.98.
- **The pre-registered hypothesis**: binding in layers 7 to 9 not supported
  (no established read at the Readout query); selection in 12 to 15 with the
  lie signal at the queries **not supported** — indeterminate on size, and
  against Q on the sign reading, since every above-noise Q cell into a mid head
  is positive; late movers partly supported (17 and 24, no layer-22 head in the
  circuit, and the largest mover is an MLP block); the honest-twin clause
  untestable from a delta that shares 0 of 18 Components with the honest
  circuit.

### The roles table

| Component | reads (mass) | writes | differential | knockout | direct support | role |
|---|---|---|---|---|---|---|
| L5H5 | question (0.51) | −0.0007 | +0.0003 | +0.0330 | −0.0001 | unknown |
| L5H6 | question (0.60) | −0.0004 | −0.0003 | +0.0277 | −0.0001 | unknown |
| L5H8 | unsegmented (0.42) | −0.0000 | +0.0001 | +0.0572 | −0.0001 | unknown |
| L5H9 | unsegmented (0.52) | −0.0005 | −0.0006 | +0.0415 | −0.0001 | unknown |
| L5H11 | item_1_question_option (0.35) | −0.0003 | −0.0002 | +0.1503 | −0.0001 | unknown |
| L8H12 | unsegmented (0.62) | −0.0001 | +0.0004 | +0.0332 | −0.0001 | unknown |
| L8H14 | unsegmented (0.53) | −0.0001 | +0.0004 | +0.0679 | +0.0001 | unknown |
| L8H15 | unsegmented (0.44) | −0.0001 | −0.0004 | +0.0320 | +0.0000 | unknown |
| L9H12 | unsegmented (0.54) | +0.0006 | +0.0005 | +0.0682 | −0.0004 | unknown |
| L13H17 | question (0.25) | +0.0003 | −0.0003 | −0.0053 | −0.0007 | unknown |
| L14H7 | question (0.32) | −0.0005 | +0.0008 | **−0.0936** | −0.0004 | unknown |
| L14H21 | unsegmented (0.44) | −0.0011 | −0.0022 | +0.0203 | −0.0009 | unknown |
| L14H22 | question (0.29) | −0.0011 | −0.0038 | +0.1122 | −0.0005 | unknown |
| L17H25 | question (0.27) | **+0.0310** | +0.0347 | **+0.4465** | +0.0192 | unknown (selector lean, query not met) |
| L24H18 | unsegmented (0.64) | +0.0444 | +0.0703 | +0.0230 | +0.0159 | unknown (mover lean, reads not met) |
| L24H25 | unsegmented (0.56) | +0.0405 | +0.0849 | +0.0021 | +0.0193 | unknown (mover lean, reads not met) |
| L27H4 | unsegmented (0.78) | −0.0045 | −0.0032 | −0.0008 | −0.0005 | unknown |
| **L31 MLP** | not applicable | **+0.1795** | **+0.3253** | **+0.3065** | **+0.0951** | **mover** |

### Runtime, for budgeting

| analysis | card | forwards | wall |
|---|---|---|---|
| model load + `attention_patterns` | A40 | 2208 eager (derived) | 8 min 18 s |
| `dla` | A40 | not recorded | 1 min 14 s |
| `knockout` | A40 | 260 (derived) | 50 s |
| path patching, item-swap, position-agnostic | A40 | 5382 | 1038 s |
| path patching, honest-instruction, position-agnostic | A40 | 5382 | 763 s |
| Segment pass at 0.01, 5 and 4 cells | A40 | 156 / 364 | 30 s / 52 s |
| completeness sweep, 64 instances | A40 | 8472 | 1760 s |
| family knockout, 2 families | A40 | 312 (derived) | inside a 2:16 job |

The descriptive trio is about 11 minutes; each position-agnostic grid is 13 to
18 minutes at 100 instances; the sweep is about 30 minutes at 64. Ticket 02b's
A40 constant of 0.1848 s per forward **under**-predicts the item-swap grid by 4
percent and over-predicts the honest one by 30 percent, since the honest pass
spends all 5382 forwards at 71-of-100 occupancy. Neither
`attention/patterns.json` nor `knockout/knockout.json` records a cost block, so
those two forward counts are derived rather than read.

### Files touched

- **New, committed:** `scripts/check_cell.py` (`bfdbe19`) — walks
  `component_analysis.review`'s own view functions over a cell and prints one
  line per analysis, so a missing or malformed output is named without
  executing the notebook. It is what checkbox 1's "schema-valid" was verified
  with.
- **Committed under an ignored path:** the write-up,
  `outputs/_analyses/sdr-first-run/delta__head/sdr/result_summary.md`
  (`3c66f4c`), force-added because `outputs/_analyses/` is in `.gitignore` and
  the ticket asks for the write-up in the cell directory.
- **No shared file was changed.** Not `analyze_components.py`, not
  `component_analysis/`, not `tests/`, not the sbatch, not `README.md`, not
  `CONTEXT.md`, not the docs. The rebase should be clean.
- **No package code changed, so no test suite was run.** The one new file is a
  standalone script that imports `component_analysis.review`; it was exercised
  on three real cells (`ca10-roles`, `sdr-first-run`, `sdr-first-run-sweep`) in
  the login-node base environment with the BLAS thread pins. No `core.*` dump
  appeared and none was committed.

### The checkboxes, and what verifies each

1. **All analyses run, every output present and schema-valid.**
   `scripts/check_cell.py` over the cell of record reports every view present:
   head table, attention patterns, top heads, DLA, DLA heatmap, paired scatter,
   logit lens, knockout, family knockout, path patching, segmentation, sample.
   The only `Missing` is the completeness sweep, which is present in its own
   cell for the reason in the open questions. Every PNG in the cell has a JSON
   twin.
2. **Role proposal run, confirmation column left empty.** `roles/roles.json`
   holds every decision, every threshold and every criterion's verdict, and
   records `role_confirmed: null` for all eighteen Components. **There is no
   `role_confirmed` column in the head table, and that is the package's
   behaviour, not an omission**: `head_table.PROTECTED_COLUMNS` is exactly that
   one name and nothing in the package writes it, so the researcher creates the
   column and every later run carries it forward through `carry_roles`. The
   write-up says this in section 3. Whether the roles pass should instead write
   an empty column is an open question below.
3. **`result_summary.md` in the cell directory** with all six required parts.
4. **Runtime per analysis recorded** — the table above and section 8 of the
   write-up.
5. **Subagent review** — below.

### The review

Two independent sub-agents, on an unsupported-claims axis and a spec axis, as
the ticket's last checkbox asks in place of a code review. **Both handbacks
failed** — the failure tickets 02, 02b, 04, 06, 07, 09 and 10 all record — and
both reports arrived afterwards by `SendMessage`, the claims axis also relayed
by the orchestrator, so **the review is independent of the author**. Report,
with both reviews and the disposition of every finding:
`Alignment/.scratch/component-analysis/reports/12-first-sdr-run-and-writeup-review.md`.

Claims axis: 11 findings. Spec axis: **ship with changes**, 9 findings, none
needing a rerun. **Every finding was addressed**, along with the orchestrator's
seven further requirements. Neither reviewer found a measurement error; every
finding was about prose over the measurements. The five that changed what the
document says:

1. **The dry-run error direction was backwards** — the estimate under-predicts
   the item-swap grid, it does not over-predict it. An earlier self-correction
   of that same sentence had silently failed to apply, and the reviewer caught
   the live text.
2. **"Everything else in the grid is below 0.005" was false for the
   honest-instruction grid**, where four more cells clear it. Two of those four
   are the mid-band Q cells the hypothesis check needs.
3. **The Q-versus-V verdict rested on a cell outside the band the spec names.**
   `head.8.15 -> v.9.3` is layer 9, the binding band. The verdict is now argued
   from the mid band: indeterminate on size, against Q on the sign reading,
   with the layer-9 cell moved to the binding clause, and with the KV-group
   asymmetry (a Q receiver is one head, a K or V receiver is four, some outside
   the circuit) applied wherever sizes are compared.
4. **`role_confirmed` was described as an empty column** when no such column
   exists.
5. **A knockout drop was expressed as a fraction of the patching gap** without
   saying that the knockout analysis's own clean run is the other candidate
   denominator; both are now given.

### Open questions for the researcher

1. **Separate Slurm jobs cannot accumulate into one cell.** Every analysis run
   rebuilds the head table from the circuit intake and carries forward only
   `role_confirmed` and `roles.*` (`analyze_components.py`, `carry_roles`), so
   three jobs pointed at one cell leave only the last job's columns. With a
   one-hour job budget, multi-job cells are the normal case, and the workaround
   here was copy-the-directories-then-merge-the-columns through the roles pass.
   Either the CLI should carry every analysis's columns forward, or the docs
   should say plainly that a cell is one job's output and that assembly is
   manual. **This is the one thing from this ticket that most wants a decision.**
2. **Should the roles pass write an empty `role_confirmed` column?**
   `head_table.merge_columns` refuses that name outright, which is the
   protection that keeps a confirmed role from being overwritten, so writing an
   empty column needs a deliberate exception rather than a flag.
3. **The completeness sweep cannot share a cell with the grid.** It ran over 64
   instances and the grid over 100, so its `path_patching.direct_effect` column
   contradicts the grid's and `merge_cells` refuses the merge by design. Either
   the sweep's columns should be namespaced apart from the grid's, or the sweep
   should be run at the grid's instance count — which on an A40 is about 46
   minutes for the sweep alone, so it would need its own job either way.
4. **`--path-position-threshold` is still 0.05 in code.** This run used 0.01,
   the roles path floor, and said so; at 0.01 the Segment pass swept one K or V
   cell, where ticket 09's 0.0035 pass swept nine — on exactly the Q-versus-V
   question the spec calls the direct test. The default is still yours to set.
5. **Everything ticket 06, 09 and 10 left open** is unchanged and is collected
   at the end of the write-up, including L17H25's one missing cell, the
   suppressor carve-out, the ten heads with no established read, whether
   `question` is a frame, and whether the vocabulary is missing a fifth role
   for the five Components that matter causally and do nothing the four roles
   describe.
6. **A finding worth a decision of its own**: the sweep says seven non-circuit
   Components clear a 0.05 direct effect and that non-circuit direct paths carry
   most of the gap, while the delta shares 0 of 18 Components with the honest
   circuit. Whether the head-granularity delta is the right object to analyse,
   as against the union or the intersection, is a question this run raises and
   cannot answer.
