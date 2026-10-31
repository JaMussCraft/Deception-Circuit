# 13 — Paired column names, per-column coverage meta, multi-job cells, lifted job budget

**What to build:** Every paired column carries "paired" in its name; the head table meta records, per column, the instance count and instance set it was computed over; a rerun of any analysis into a cell carries every other analysis's existing columns forward, so a cell is assembled by running jobs into it rather than by copy-then-merge; the roles vocabulary gains the `unknown/knockout-only` flavour; and the one-hour job budget is lifted from the sbatch defaults and the docs.

**Blocked by:** 12 — First SDR run and result write-up.

**Status:** resolved

- [x] Every column computed over the same instance ids on both sides carries `paired` in its bare name, in `attention_patterns`, `dla` and `path_patching` (for example `dla.honest_instruction` becomes `dla.honest_instruction_paired`, `dla.differential` becomes `dla.differential_paired`, `path_patching.direct_effect_honest_instruction` becomes `path_patching.direct_effect_honest_instruction_paired`; `pressure_paired` already complies). Readers (`roles.py`, `review.py`, the notebook, `check_cell.py`, docs/component-roles.md, ADR-0002, README) use the new names; `review.py` renders a legacy-name cell of record with a note rather than an error.
- [x] `head_table.json` meta carries, per column, `n` and a reference to the instance set (the sample's instance-set id plus the list of ids, or the paired subset's ids) so 71-versus-100 coverage is readable from the table without being in the name; `write_head_table` / `merge_columns` gain the seam for an analysis to declare it; every analysis declares it.
- [x] `analyze_components.py` carries every existing column of a cell's head table forward onto the fresh intake rows on any run into that cell (`--dry-run` included), overwriting only the namespaces of the analyses that run in that invocation; `role_confirmed` and `roles.*` keep today's behaviour as a special case of the general rule. Test at the CLI seam: two sequential runs with different `--analyses` into one cell produce a table with both namespaces; a third run over one namespace replaces only that namespace.
- [x] `roles.py` writes `unknown/knockout-only` when a Component's only significant view is knockout (no established read, no DLA, no path above the floor); documented in docs/component-roles.md with its criterion; test on a hand-built table.
- [x] `scripts/analyze_components.sbatch` and the docs no longer presume a one-hour budget: the default partition/time are documented as a starting point, `--dry-run` still prints the estimate, and the README and agent-facing docs say multi-hour jobs and A100/H200 partitions are allowed.
- [x] Both suites at the 8-name baseline; the mechanical roles pass rerun on the login node over the `sdr-first-run` cell of record copied into the worktree, confirming the renamed columns are read and the `knockout-only` flavour appears for the early heads the write-up names.
- [x] Subagent code review against the spec completed and findings addressed.

## Comments

### What was built

Ten commits on `ca/13-column-conventions-and-multi-job-cells`, base `3c66f4c`:

    060ab9d  Record per-column coverage and translate legacy paired names in the head table
    a103a18  Carry every column forward on a run into a cell, so jobs assemble one table
    d18b964  Say paired in the paired attention column, and declare each column's instances
    2bb0a5d  Say paired in the paired DLA columns, and declare each column's instances
    62015e4  Say paired in the honest-instruction path columns, and declare their instances
    eab121e  Declare the causal sample every knockout column was measured over
    2b39f0d  Hold knockout-only Components at unknown/knockout-only, and read legacy cells
    9fbd93d  Render a cell of record written before the paired names, with a note
    ed05fa8  Print the head table's legacy-name and coverage notes in check_cell
    68c672d  Lift the one-hour job budget, and document multi-job cells and paired names

plus three review-fix commits listed under "The code review" below
(`24862dd`, `fb12bd7`, `4ba2877`); the tip is `4ba2877`.

### Old-to-new column names (for tickets 14, 15 and 16)

Names only: no value and no sign changed. The one map is
`component_analysis/head_table.LEGACY_COLUMNS`; `head_table.modernize_columns`
applies it, and every reader (the CLI's carry-forward, `roles.py`, `review.py`,
so the notebook and `check_cell.py`) goes through it.

| old | new |
|---|---|
| `attention_patterns.honest_instruction_top_segment` | `attention_patterns.honest_instruction_paired_top_segment` |
| `attention_patterns.honest_instruction_top_mass` | `attention_patterns.honest_instruction_paired_top_mass` |
| `dla.honest_instruction` | `dla.honest_instruction_paired` |
| `dla.differential` | `dla.differential_paired` |
| `dla.differential_se` | `dla.differential_paired_se` |
| `path_patching.strongest_incoming_honest_instruction` | `path_patching.strongest_incoming_honest_instruction_paired` |
| `path_patching.strongest_incoming_effect_honest_instruction` | `path_patching.strongest_incoming_effect_honest_instruction_paired` |
| `path_patching.strongest_outgoing_honest_instruction` | `path_patching.strongest_outgoing_honest_instruction_paired` |
| `path_patching.strongest_outgoing_effect_honest_instruction` | `path_patching.strongest_outgoing_effect_honest_instruction_paired` |
| `path_patching.direct_effect_honest_instruction` | `path_patching.direct_effect_honest_instruction_paired` |
| `path_patching.direct_effect_se_honest_instruction` | `path_patching.direct_effect_se_honest_instruction_paired` |
| `path_patching.sweep_*_honest_instruction` (5, only if the sweep ran on that pair) | `path_patching.sweep_*_honest_instruction_paired` |
| `roles.direct_support_honest_instruction` | `roles.direct_support_honest_instruction_paired` |
| `knockout.family`, `knockout.family_logit_diff_drop` (ticket 10's rename) | `knockout.role_family`, `knockout.role_family_logit_diff_drop` |

**Note for ticket 14:** the `_se` order differs between modules
(`dla.differential_paired_se`, but
`path_patching.direct_effect_se_honest_instruction_paired`). The orchestrator's
ruling: ticket 14 applies `<name>_paired_se` (here
`direct_effect_honest_instruction_paired_se`) when it renames the flipped
path-patching columns, and adds the old spelling to `LEGACY_COLUMNS` only if
the meaning is unchanged.

**"Paired" means the honest-instruction pairing only.** Item-swap path-patching
and knockout columns are not renamed.

**Unchanged, deliberately:** `attention_patterns.pressure_paired_*` and
`dla.pressure_paired` (already comply); `*_descriptive` (the twin); the
full-split `attention_patterns.pressure_*`, `dla.pressure*`, `dla.suppression`;
every item-swap `path_patching.*` column and every `knockout.*` column. Reading:
"paired" names the honest-instruction contrast over the same instance ids on
both sides, which is what the ticket's three examples and spec user story 27
mean. The item-swap pair is also clean-versus-corrupt of one instance, but
every causal column is that, and renaming them would carry no information.

Code-side constants for the next tickets: `attention_patterns.COLUMN_PREFIXES`,
`dla.COLUMN_SOURCES`, `path_patching.COLUMN_SUFFIX` / `COLUMN_NAMES` /
`SWEEP_COLUMN_NAMES`, `roles.COLUMNS` and the `roles` column constants.
**Ticket 14 (sign flip):** `LEGACY_COLUMNS` must never map a column whose
meaning changes. If the flipped path-patching columns keep their names, the
legacy translation would make an old-sign cell read like a new-sign one, so
ticket 14 should either give the flipped columns new names or make the readers
check the sign in the meta (`roles.derived_columns` negates
`path_patching.direct_effect` today). ADR-0002's amendment leaves that to it.

### Per-column coverage

`head_table.json`'s `meta` now carries

    coverage       {column: {"n": int, "instance_set": set id or null}}
    instance_sets  {set id: {"name", "n", "dataset", "instance_ids"}}

Each set is written once and every column over it points at it; a set id is
its name plus a digest of its sorted ids (and dataset), so two columns over the
same instances share an id and the 71 and the 100 never do. The seam:
`head_table.add_coverage` (namespaced like `merge_columns`), `coverage_of`,
`load_head_table_meta`; `write_head_table` drops coverage for columns the table
no longer holds; `load_head_table` is unchanged and a table without coverage
loads and reads as "not recorded". Analyses declare through
`AnalysisContext.declare_coverage(columns, instance_ids=..., instance_set=...,
dataset=...)`, which the CLI namespaces and merges after each `module.run`
(the five-name registry protocol is unchanged). Every analysis declares:

| analysis | columns | instance set |
|---|---|---|
| attention_patterns | `pressure_*` / `pressure_paired_*` and `honest_instruction_paired_*` / `honest_twin_descriptive_*` | `test_split` / `paired_honest_instruction` / `honest_twin_split` (with its dataset) |
| dla | `pressure`, `pressure_se`, `suppression` / the four paired ones / the two twin ones | the same three |
| knockout | all four, and the two `role_family*` | `causal_sample` |
| path_patching | item-swap / `_honest_instruction_paired` / the sweep's | `causal_sample` less gap-excluded / `paired_honest_instruction` / whichever pair the sweep ran on |
| roles (subcommand) | `direct_support*` | copied from the path-patching column each negates |

`attention_patterns.query_position` is a setting and declares nothing. A
condition that did not run declares its columns with n = 0 and no set.

### Multi-job cells

`analyze_components.carry_forward(cell, rows, replaced=...)` replaces
`carry_roles`: on any run into a cell, every existing column is carried onto
the fresh intake rows except the intake's own (`BASE_COLUMNS`, `reference.*`)
and the namespaces of the analyses that run in that invocation. A dry run
replaces nothing. `role_confirmed` and `roles.*` are the special case (nothing
the CLI runs owns them). Also carried: the coverage of every carried column,
and every meta key that is not the intake's (`roles`, `renamed_columns`).
Rows an analysis appended outside the circuit (the sweep's) travel with their
namespace; an old intake row the new circuit lacks is dropped. Legacy names are
translated on the way and recorded in the meta. This closes ticket 10's open
question 5 and ticket 12's open question 1; `docs/component-roles.md`'s "Knockout
by role family" paragraph that warned a dry run would wipe the table is rewritten.

### unknown/knockout-only

Criterion (`roles.knockout_only`, rule 6 in `docs/component-roles.md`, amendment
logged 2026-10-13): knockout significant and above its floor in either direction;
no established read (an MLP block qualifies); DLA and paired differential not
significant and no suppression flag; no direct, onward or own-query honest
path above the path floor. It changes no role, only flavours; `roles.json`
gains `flavour_counts` and `renamed_columns`.

### Verification on the login node (copy of the cell of record)

`sdr-first-run` copied to `outputs/_analyses/ca13-sdr-first-run` in this
worktree (not committed). `check_cell.py` before: 12 views present, the sweep
missing, as ticket 12 recorded. Then:

1. `analyze_components.py roles <copy>`: all twelve legacy names read under the
   new ones, **0 binder, 0 selector, 1 mover, 0 suppressor, 17 unknown**,
   unchanged, every role the same as the record, and all 864 non-notes values
   identical to the record under their new names. Flavours: **6 knockout-only
   (L5H8, L5H9, L8H12, L8H14, L8H15, L9H12), 11 insufficient.**
2. A real `--dry-run` with the SDR delta bindings into the same copy: "carried
   forward ... 42 column(s) under attention_patterns, dla, knockout,
   path_patching, roles"; afterwards all 864 values identical again, the
   `roles.*` columns present, sample ids identical to the record's.
3. The roles pass again: same counts and flavours; `check_cell.py`: same 12.

**One divergence from the orchestrator's list, for the researcher:** L5H11 is
**not** knockout-only. Its top Segment at the Readout is
`item_1_question_option` at 0.35, an established read, and the ticket's
criterion (and the researcher's "until there is reads evidence") excludes it.
The four binding-band heads the write-up's section 5 names (L8H12, L8H14,
L8H15, L9H12) all get the flavour, and so do L5H8 and L5H9. L14H7 and L14H22
(knockout significant, nothing else) are excluded by their `question` reads.
If the researcher wants the flavour to mean "knockout is the only *support*
view" regardless of reads, it is one clause in `roles.knockout_only` and would
add L5H11, L14H7 and L14H22.

### Tests

| env | baseline on `3c66f4c` | `68c672d` (before review) | final on `fb12bd7` | new failures |
|---|---|---|---|---|
| login-node base (py3.9, BLAS pins) | 8 failed, 919 passed, 44 skipped | 8 / 960 / 44 | 8 failed, 963 passed, 44 skipped | none, the same 8 names |
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 1045 passed, 19 skipped | 8 / 1088 / 19 | 8 failed, 1091 passed, 19 skipped | none, the same 8 names |

Failure lists were diffed by name. New test files: `tests/test_column_conventions.py`
(head-table seam), `tests/test_multi_job_cells.py` (the CLI seam the ticket
names: two runs with different `--analyses` keep both namespaces, a third over
one namespace replaces only it, a dry run carries everything, roles survive a
full run, appended rows travel with their namespace, coverage survives later
runs; two stub analyses, both envs), `tests/test_check_cell.py`. A mutation
(ignoring `replaced`) fails two of the CLI tests. No Slurm job: no computed
number changed. No `core.*` dump appeared.

### Shared files changed (for the merge)

`analyze_components.py` (carry_forward, coverage collection, write_cell meta),
`component_analysis/head_table.py` (meta keys are `COVERAGE_KEY`,
`INSTANCE_SETS_KEY`, `RENAMED_KEY`; set names `TEST_SPLIT`, `CAUSAL_SAMPLE`,
`PAIRED_HONEST_INSTRUCTION`, `HONEST_TWIN_SPLIT`; helpers `current_name`,
`modernize_meta`, `is_appended_row`), `component_analysis/registry.py`
(`declare_coverage`/`take_coverage` on the context), `README.md`,
`scripts/analyze_components.sbatch`, `docs/component-roles.md`, ADR-0002. Each
analysis module changed only its column names and one declaration call; tickets
14, 15 and 16 own `path_patching.py`, `knockout.py` and `attention_patterns.py`
and start from this tip.

### Open questions for the researcher

1. **The knockout-only reading.** The literal criterion gives six heads on
   SDR nls0.3: L5H8, L5H9, L8H12, L8H14, L8H15 and L9H12 (0/0/1/0/17
   unchanged). It excludes every head with an established read: L5H11
   (item-mention read at 0.35, and the largest knockout of the early heads at
   +0.150) and L14H7 and L14H22 (`question` reads, knockout z = 3.3 and 3.6).
   L5H5 and L5H6 also read `question`, but their knockouts (z = 1.8 and 1.9)
   do not clear the z = 2 bar, so no reading would give them the flavour.
   Should "matters on knockout alone" ignore frame reads, or all reads?
   Ignoring frame reads would add L14H7 and L14H22; ignoring all reads would
   add L5H11 as well. Either is one clause in `roles.knockout_only`.
2. **Rerunning the cells of record.** `docs/component-roles.md` asks for every
   cell with a role column to be rerun after a criteria change; only the copy
   was rerun here. A run into a cell of record also rewrites its table under
   the new names (values unchanged, translation recorded in the meta).
3. **"Paired" was read as the honest-instruction pairing only**; item-swap and
   knockout columns keep their names.

### The code review

`mattpocock-skills:code-review` against `3c66f4c`, both axes as independent
parallel sub-agents. Both handbacks failed as the brief predicts; both reports
were then delivered by message to me and to the orchestrator. **The review is
independent of the author.** Report, with both reviews verbatim and every
disposition: `Alignment/.scratch/component-analysis/reports/13-column-conventions-and-multi-job-cells-review.md`.

- **Spec: nothing blocking.** One real defect, **fixed** in `24862dd`: under
  `--roles-allow-missing-views` a table with knockout alone would have made
  every significant head `unknown/knockout-only`; the flavour now needs the
  DLA and path views to have been measured (two tests, doc rule 6). Also fixed
  in `fb12bd7`: ADR-0002's amendment overstated that a legacy cell is never
  rewritten (a run into one writes it back under the new names, recorded in
  the meta), and the README now warns that a rerun replaces its analysis's
  whole namespace. The agent-facing budget docs it flagged had already been
  updated by the orchestrator. L5H11 and the "paired" reading are for the
  researcher.
- **Standards: no hard violation.** Fixed in `fb12bd7`: one legacy-name path
  (`head_table.current_name` / `modernize_meta`) instead of three hand-written
  copies, the meta-key constants renamed so they do not clash with the
  analyses' maps, shared instance-set name constants, `check_cell.py` reading
  the view's fields instead of note text, `roles.FLAVOURS` used by a doc test.
  Kept with reasons: the declaration-level coverage tests (the written-meta
  assertions exist but run only in mgnp), `_PATH_COLUMNS` restated in
  `head_table` (a circular import otherwise; test-pinned), `carry_forward`
  staying in the CLI, and the two modules' differing `_se` placement.

After the fixes the roles pass on the copy was rerun: same 0/0/1/0/17 and the
same six knockout-only heads.

**Rulings applied (2026-10-13).** The orchestrator's three messages are
recorded with their outcomes in the review file. Fixed in `4ba2877`: the
base-env coverage tests now assert on a written head table (no spy); a
Component whose DLA or path view was never measured is
`unknown/insufficient` with "not measured: ..." in its notes; the README
puts "rerun the roles pass" beside the whole-namespace warning; the criteria
doc says `meta.roles` is carried until the pass reruns. Kept by ruling:
`_PATH_COLUMNS` restated (pin test), `carry_forward` in the CLI, the `_se`
order (ticket 14), `knockout.family` in the map, `meta.roles` carried.
After `4ba2877` (a test-only and roles-note change) the touched files were
rerun as ruled, not the full suites: `tests/test_dla.py`,
`test_paired_honest.py`, `test_roles.py`, `test_multi_job_cells.py`,
`test_column_conventions.py` and `test_paired_honest_cli.py` give 152 passed
in `mgnp` and 137 passed, 1 skipped (the CLI file, at module level) in the
base env. The last full runs, on `fb12bd7`, are in the Tests table above.
