# 14 — Path patching: sign agrees with knockout, completeness sweep on the grid's sample

**What to build:** The path-patching cell is reported so that positive means the path helps deception, matching knockout's drop; the JSON meta states the convention and a version marker so an old cell of record is told apart; `roles.direct_support` becomes the native column; and the completeness sweep runs on the same instances as the grid by default.

**Blocked by:** 13 — Paired column names, per-column coverage meta, multi-job cells, lifted job budget.

**Status:** resolved

- [x] The path-patching metric is reported as `(clean - patched) / (clean - corrupt)` (positive = the path carries the deceptive signal), in every JSON, PNG and head-table column `path_patching.*`; `metric.sign` in each JSON says so in words and a `metric.convention` marker distinguishes new cells from legacy ones.
- [x] `roles.py` reads the convention marker: on a new cell `roles.direct_support` equals the native column; on a legacy cell it is negated as today; ADR-0002 and docs/component-roles.md are updated to say path patching is now read natively.
- [x] `review.py` and the notebook render legacy and new cells correctly, stating the convention in the figure subtitle.
- [x] `--path-completeness-sweep` uses the grid's sample (the global `--n-causal`/`--seed` draw, 100 instances by default) rather than a separate draw; the sweep's head-table columns and the grid's then cover the same instance set and the per-column coverage meta says so.
- [x] Tests: the sign test on the tiny model (a last-layer MLP patched with its corrupt output gives a positive cell when its direct effect helps the Target); a legacy JSON fixture read by roles gives the same `direct_support` as before; the sweep's instance ids equal the grid's.
- [x] Verified by a Slurm run on SDR nls0.3 at head-granularity delta with both counterfactuals, the Segment pass and the sweep on 100 instances (one job is fine even if it takes two or three hours; rehearse with `--dry-run`, put `--time` on the command line, A40/A100/H200 as the queue allows); the strongest cells reproduce `sdr-first-run` with the sign flipped.
- [x] Subagent code review against the spec completed and findings addressed.

## Comments

### What was built

Nine commits on `ca/14-path-patching-sign-and-full-sample-sweep`, base `4ba2877`
(not rebased onto ticket 16's `4fb2c66`; that is the orchestrator's):

    5fc7a96  Report path patching as (clean - patched) / gap, so positive helps deception as in knockout
    b2e1689  Give the sign-flipped path-patching columns new names, never a legacy translation
    a667709  Read path patching natively in the roles pass, and negate only a legacy cell
    f243463  State each path figure's sign in its subtitle, and flag a cell mixing both
    57aa349  Run the completeness sweep on the grid's own sample, and say so in its coverage
    9451969  Record in ADR-0002 and the criteria doc that path patching is now read natively
    a03b2e7  Say in the head-table view when a cell's path columns are in the legacy sign
    2a2ba5c  Take both independent reviews: one marker vocabulary, a marker check, one read table
    1d2bff6  Give the measured sweep time, and document the marker agreement check

**The sign.** `normalized_effect` is now `(clean - patched) / (clean - counterfactual)`.
A positive cell is a path that helps the deceptive answer, the sign of knockout's
drop. Every JSON's `metric` block carries `sign` in words, and two markers:
`convention: "positive_helps_deception"` and `convention_version: 2`. A file
without `convention` is legacy (`path_patching.convention_of`). Every PNG title
states the convention too.

**Marker plus new names, as the brief preferred.** The JSONs carry the marker.
In the head table, each column whose sign changed got a new name; nothing else
was renamed. A column name travels with its values through merges,
carry-forward and the CSV, which has no meta at all. A marker kept only in the
head table's meta could be lost while the numbers survived. `LEGACY_COLUMNS`
maps neither generation into the other, and a test pins that.

### Renamed columns

Old cells keep the left column, in the old sign. New runs write the right
column, in the new sign. Neither is translated into the other.

| legacy name (negative helps deception) | new name (positive helps deception) |
|---|---|
| `path_patching.direct_effect` | `path_patching.direct_support` |
| `path_patching.direct_effect_se` | `path_patching.direct_support_se` |
| `path_patching.strongest_incoming_effect` | `path_patching.strongest_incoming_support` |
| `path_patching.strongest_outgoing_effect` | `path_patching.strongest_outgoing_support` |
| `path_patching.direct_effect_honest_instruction_paired` | `path_patching.direct_support_honest_instruction_paired` |
| `path_patching.direct_effect_se_honest_instruction_paired` | `path_patching.direct_support_honest_instruction_paired_se` |
| `path_patching.strongest_incoming_effect_honest_instruction_paired` | `path_patching.strongest_incoming_support_honest_instruction_paired` |
| `path_patching.strongest_outgoing_effect_honest_instruction_paired` | `path_patching.strongest_outgoing_support_honest_instruction_paired` |
| `path_patching.sweep_direct_effect` | `path_patching.sweep_direct_support` |
| `path_patching.sweep_direct_effect_se` | `path_patching.sweep_direct_support_se` |
| (sweep on the honest pair only) `sweep_direct_effect[_se]_honest_instruction_paired` | `sweep_direct_support_honest_instruction_paired[_se]` |

**Unchanged:** `strongest_incoming` and `strongest_outgoing` (the cell names,
chosen by absolute effect), and `sweep_rank`, `sweep_in_circuit` and
`sweep_flagged`, with their honest twins. Filenames and JSON keys are also
unchanged; each file's marker says which sign it holds. The honest-instruction
standard errors now use the `<name>_paired_se` order.

### Readers

- **roles.py tells the generations apart by column name, not by reading the
  marker.** This differs from the ticket's wording, "roles.py reads the
  convention marker", and is deliberate: a CSV has no meta, and a name travels
  with its values. Every path-patching number is read through one table,
  `roles.PATH_READS`, which lists native and legacy pairs. `path_value` copies
  the native column and negates the legacy one; a standard error is copied.
- **Roles also checks the marker, on the reviews' call.** Where a cell holds
  `agnostic*.json`, `check_markers` requires that file's `metric.convention`
  to agree with the generation of that counterfactual's direct column. It
  checks the cell and every `--roles-merge-from` cell, and refuses by file
  name on a mismatch with `roles.MixedConventions`.
- **A row carrying both generations is refused by name.** That happens when a
  legacy cell is merged into a new one, which the merge's own conflict check
  cannot see because the names differ.
- **roles.json records the reading.** `path_conventions` lists the markers
  the table was read in, using `path_patching`'s own strings, and
  `sign_convention` gives a sentence. The view keys `outgoing_support` and
  `incoming_honest_instruction_support` are in the support sign; no criterion
  reads their sign.
- **review.py, and so the notebook,** puts `path_patching.convention_sentence`
  in the subtitle of every path heatmap, direct-effect bar chart, Segment
  heatmap and sweep chart. Values are shown as the file holds them: a legacy
  cell is labelled, never re-signed. The head-table view adds a "legacy
  sign" note when a cell holds `*_effect` columns. The notebook's prose in
  sections 4 and 5 was updated; the notebook was not executed.
- **check_cell.py** prints `path-patching sign: ...` from the view's
  `check_lines`, with no special case for path patching. It prints `MIXED`
  with the file names when a later run left a directory half in each sign,
  because a run rewrites only the files of the passes it ran. The skipped
  file of a counterfactual with no instance also carries the `metric` block.

### The sweep's sample

The code never had a separate draw: the sweep already walked
`ctx.causal_batches()`. The 64 instances of `sdr-first-run-sweep` came from a
separate job run with `--n-causal 64`. Two things did differ and are fixed:

- the sweep never excluded a gap-excluded instance;
- it declared coverage over every instance it saw, while the grid declared the
  measured ones.

Both now use the same rule. `stream_batches` records the exclusion for every
pass, and the grid and the sweep both declare `measured_ids(tally)`, so a grid
column and a sweep column get the same instance-set id. `sweep.json` records
`excluded_by_gap`, `drawn_by` and `same_as_grid`. The dry-run line, the flag
help, the README and the sbatch comment say the sweep runs on the grid's
instances, with the measured times: 23 minutes on an A100 over 100 instances,
and 29 on an A40 over 64 (ticket 12).

### Tests

New or changed tests, at the seams the ticket names:

- **The sign test on the tiny model.** `test_a_path_that_helps_the_target_gives_a_positive_cell`
  uses a last-layer MLP whose clean output favours the Target, with a positive
  gap. Its cell is positive and equals the knockout-style drop over the gap.
  The whole-model invariant now gives +1.
- **The legacy fixture read by roles.** `test_a_legacy_cell_of_record_reads_the_direct_support_it_always_had`
  holds two literal rows of `sdr-first-run`. The new-cell twin test gives the
  same roles and the same `roles.direct_support` from native columns. Two
  more tests cover the mixed-row refusal and coverage taken from the native
  column.
- **The sweep's instance ids equal the grid's.** `test_the_sweep_runs_on_the_grids_own_sample_and_its_coverage_says_so`
  checks this at the CLI seam: the ids, `same_as_grid`, one instance-set id,
  and sweep values equal to `direct_support` on circuit rows.
  `test_an_instance_the_gap_excludes_is_excluded_from_the_sweep_as_from_the_grid`
  checks the exclusion at the library seam.
- Column-name tests, review subtitles for legacy and new cells, and
  check_cell's legacy and MIXED output.

| env | baseline on `4ba2877` | tip `9451969` | final tip `1d2bff6` | new failures |
|---|---|---|---|---|
| login-node base (py3.9, BLAS pins) | 8 failed, 964 passed, 44 skipped | 8 / 978 / 44 | 8 failed, 983 passed, 44 skipped | none, the same 8 names |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 1092 passed, 19 skipped | 8 / 1109 / 19 | 8 failed, 1114 passed, 19 skipped | none, the same 8 names |

The 8 are the known names in `test_benchmarks.py`, `test_deception_common.py`
and `test_deception_tasks.py`. The review fixes added tests for the marker
agreement (agree, and disagree in both directions), the skipped file's
marker, and the sweep's tally. No `core.*` dump appeared.

**Bookkeeping caveat.** The job tmp directory is shared with tickets 15 and 16,
and a sibling overwrote my suite script mid-ticket. The tip runs were redone
from a private subdirectory. The baseline logs are in the shared directory, and
their counts and failure names match the orchestrator's baseline for `4ba2877`.

### Slurm

Both jobs were rehearsed with `--dry-run` on the login node and submitted from
the worktree root, with `--time`, `--partition` and `--account` on the command
line. The partition and account were picked by `sbatch --test-only`: every A40
choice was estimated for the next night, and A100 under bgrb or bimc for the
same afternoon.

| job | partition / account | node | elapsed | limit | what |
|---|---|---|---|---|---|
| 22874568 | gpuA100x4 / bgrb-delta-gpu | gpua063 | 40:30 | 1:30:00 | `--path-counterfactual both --path-position-threshold 0.01 --path-completeness-sweep`, 100 instances, suite `ca14-path-patching` |
| 22874991 | gpuA100x4 / bimc-delta-gpu | gpua063 | 39:58 | 1:15:00 | the same plus `--path-sweep-threshold 0.05`, suite `ca14-path-patching-2`, **the output of record** |

**Why two jobs.** The first omitted `--path-sweep-threshold`, so the sweep
flagged at the 0.01 Segment threshold: 55 non-circuit Components and a
73-row head table. `sdr-first-run-sweep` flagged at 0.05. The second job
reran with 0.05.

**Results.**

1. **The sign flip changes nothing else, bit for bit.** Both jobs ran on an
   A100, as ticket 08's job 22111541 did, and the item-swap grid is the exact
   negation of `ca08-path-patching`. All 393 cells have `new == -old` and
   identical standard errors, with the same 100 ids and the same gap of
   3.3391.
2. **The cross-card comparison with `sdr-first-run` (A40) holds.** The same
   ids are used, and every one of the 393 cells per counterfactual agrees
   with the record's negation within 0.0050. The median difference is 0.0007
   for the item swap and 0.0010 for the honest instruction.

   | cell | new (A100) | `sdr-first-run` (A40, legacy sign) |
   |---|---|---|
   | item swap `mlp.31.0->readout` | +0.0944 | -0.0951 |
   | item swap `head.24.25->readout` | +0.0194 | -0.0193 |
   | item swap `head.17.25->readout` | +0.0191 | -0.0192 |
   | item swap `head.17.25->mlp_in.31.0` | +0.0166 | -0.0161 |
   | item swap `head.24.18->readout` | +0.0156 | -0.0159 |
   | item swap `head.14.22->q.17.25` | +0.0070 | -0.0066 |
   | honest `mlp.31.0->readout` | +0.0763 | -0.0770 |
   | honest `head.24.25->readout` | +0.0208 | -0.0209 |
   | honest `head.24.18->readout` | +0.0171 | -0.0167 |
   | honest `head.8.15->v.9.3` | -0.0130 | +0.0155 |
   | honest `head.17.25->readout` | +0.0090 | -0.0088 |

3. **Same-card reproducibility.** The two jobs are bit-identical on both
   agnostic grids, both Segment passes and all 1057 sweep means.
4. **The sweep is on the grid's 100.** `same_as_grid` is true and no instance
   was gap-excluded. `path_patching.direct_support` and
   `path_patching.sweep_direct_support` share the instance set
   `causal_sample:fe8c26e841`, n = 100. The honest columns are
   `paired_honest_instruction:6e75c2d861`, n = 71. On circuit rows the sweep
   value equals `direct_support` exactly; `mlp.31.0` is +0.0944 in both.
5. **The sweep at 100 instances, threshold 0.05:**

   | sweep fact | value |
   |---|---|
   | non-circuit Components flagged | 6 |
   | sum of all 1057 direct supports | +0.999 of the gap |
   | the circuit's share of that sum | +0.146 |

   The six flagged Components are `mlp.30.0` (-0.1317), `head.31.0`,
   `head.30.24`, `head.30.12`, `head.27.7` and `head.17.24`. On the
   64-instance draw `mlp.29.0` was a seventh; here it is -0.0494, just under
   the threshold. Circuit ranks are `mlp.31.0` 2, `head.24.25` 28,
   `head.17.25` 29 and `head.24.18` 35. On the earlier 64-instance draw the
   sum was 0.90.
6. **The Segment pass at 0.01** selected 5 item-swap cells, all Readout or
   `mlp_in`, and 4 honest cells. One honest cell is a K or V cell:
   `head.8.15->v.9.3`, -0.0130, top Segment `pressure_clause`, union check
   exactly 0.

Outputs, in the ca-14 worktree and not committed:
`outputs/_analyses/ca14-path-patching-2/delta__head/sdr/` (of record) and
`ca14-path-patching/` (superseded, kept for the reproducibility check).

**Real-cell checks on the login node.**

- The roles pass on a copy of `sdr-first-run` (`ca14-sdr-first-run`) gives
  0/0/1/0/17 with 6 knockout-only. All 18 rows have the record's role,
  `direct_support`, se and honest support: zero differences, read by negating
  the legacy columns.
- The roles pass on a copy of the new cell, merged with that copy stripped of
  its path and roles columns (`ca14-roles-check`), gives the record's role on
  all 18 circuit rows. `roles.direct_support` equals the native column on
  every row.
- `check_cell.py` prints `positive_helps_deception` for the new cell and
  `legacy, negative_helps_deception` for the copy of the record.
- Both roles checks were rerun after the review fixes, with the marker check
  live, and gave the same results. `path_conventions` is
  `["negative_helps_deception"]` on the copy and
  `["positive_helps_deception"]` on the new cell.
- **Against the spec reviewer's checklist,** for job 22874991:
  - The Segment pass selects exactly the record's cells: 5 item-swap and 4
    honest.
  - `direct_support` is within 0.0007 of minus the record's `direct_effect`
    on all 18 Components, for both counterfactuals.
  - The `strongest_*` cell names match the A40 record on only 5 to 10 of 18
    rows. Every row that differs has a strongest cell of 0.0045 or less on
    the record, inside the cross-card floor.
  - Against ticket 08's same-card A100 cell, the names match on 18 of 18,
    and `direct_support` and `strongest_*_support` are exact negations.

### Shared files touched (for the merge)

- `component_analysis/head_table.py`: a comment on `_PATH_COLUMNS`, which now
  names the legacy bare names; `LEGACY_COLUMNS` is unchanged.
- `component_analysis/roles.py`, `component_analysis/review.py`, `scripts/check_cell.py`
- `review_components.ipynb`: markdown in sections 4 and 5 only.
- `README.md`, `scripts/analyze_components.sbatch` (a comment only),
  ADR-0002 (an amendment) and `docs/component-roles.md`.
- `tests/test_roles.py`, `tests/test_review.py`, `tests/test_check_cell.py`
- Not touched: `analyze_components.py`, `registry.py`, `hooks.py`,
  `dataloaders.py`, `knockout.py`, `attention_patterns.py` and the shared
  nnsight probe.

The branch is not rebased onto ticket 16's `4fb2c66`; that is left to the
orchestrator.

### Open questions for the researcher

1. **Should `--path-sweep-threshold` default to 0.05 rather than to
   `--path-position-threshold`?** With the Segment pass now run at 0.01 by
   hand, the inherited default flags 55 Components and appends 55 rows to the
   head table, which job 22874568 did.
2. **Do the cells of record get rerun?** They stay in the legacy sign, labelled
   in every reader. A rerun of path patching into `sdr-first-run` would
   rewrite only the files of the passes run; `check_cell` flags that as
   `MIXED`.
3. **The sweep's direct supports sum to +0.999 of the gap** over the grid's
   100 instances, against 0.90 on the earlier 64-instance draw; the circuit's
   share is +0.146. Recorded, not interpreted.

### The code review

`mattpocock-skills:code-review` against `4ba2877`, with both axes as
independent parallel sub-agents. Both handbacks failed. Both reports reached
the orchestrator and the implementer by message, and the orchestrator
forwarded them with its calls. **The review is independent of the author.**
The report, with both reviews verbatim and every disposition, is
`reports/14-path-patching-sign-and-full-sample-sweep-review.md`.

- **Standards: no hard violation.** Of nine judgement calls, eight were fixed
  in `2a2ba5c`, per the calls:
  - the `*_support` locals;
  - one marker vocabulary in `roles.json`;
  - one `PATH_READS` table;
  - the gap exclusion recorded once, with the sweep's coverage taken from its
    tally;
  - `check_lines` in place of check_cell's identity switch;
  - `MixedConventions`;
  - glossary wording and `(clean - counterfactual)`;
  - `Optional`.

  The two one-line delegates (`review._convention`, the test helper
  `path_figures`) are kept as judgement calls. The reviewer's pointer about
  the marker became the marker agreement check.
- **Spec: nothing blocking, nothing implemented wrong.**
  - The skipped file's `metric` block was fixed in `2a2ba5c`.
  - The Comments notes on name-based detection, the copy check and the sweep
    coverage are above.
  - The measured sweep time was fixed in `1d2bff6`.
  - The reviewer's Slurm checklist is answered above, with one honest
    partial: `strongest_*` names match the A40 record only where the cell
    clears the cross-card floor, and match ticket 08's A100 cell exactly.
