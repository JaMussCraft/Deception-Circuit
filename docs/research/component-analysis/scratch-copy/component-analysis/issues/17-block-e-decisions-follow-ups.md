# 17 — Block E decision follow-ups: thresholds, positive control, knockout-only notes, legacy caveat

**What to build:** The researcher's decisions on block E's open items, applied: the knockout sweep flags at 0.4 by default and treats the layer 0 MLP as a labelled positive control outside the outsider count; the path-patching sweep threshold defaults to 0.05 on its own; the roles pass notes heads that have both a knockout effect and an established read; and the legacy cells of record carry a caveat about the old path-patching sign and the pre-13 column names.

**Blocked by:** 14 — Path patching sign; 15 — Knockout completeness sweep.

**Status:** resolved

- [x] `--knockout-sweep-threshold` defaults to 0.4; the default and its reason (hand-tuned on SDR nls0.3; the full ranked list is always written so nothing is hidden) are stated in `--help`, `sweep.json` meta and docs/component-roles.md; the threshold ladder stays.
- [x] The layer 0 MLP stays in the knockout sweep's ranked list and figures, marked `positive_control: true` in `sweep.json` and labelled so on the bar chart, and is excluded from the outside-the-circuit count and the flagged list the way the embedding is excluded; the meta says so.
- [x] `--path-sweep-threshold` defaults to 0.05 and no longer follows `--path-position-threshold`; `--help`, the sweep JSON meta and the README say so.
- [x] `roles.py` applies `unknown/knockout-only` literally (unchanged) and adds a note to `roles.role_notes` for a Component whose knockout is significant and whose read is established but whose DLA and path views are silent ("knockout effect with an established read"); docs/component-roles.md names this case beside rule 6; test on a hand-built table; the mechanical pass on a copy of `sdr-first-run` names L5H11, L14H7 and L14H22.
- [x] A short caveat is added at the top of `outputs/_analyses/sdr-first-run/delta__head/sdr/result_summary.md` (committed) and a `LEGACY.md` note beside each pre-2026-10-13 cell of record in the `component-analysis` worktree's outputs (not committed; list them in the ticket) saying the path-patching columns are in the legacy sign and the column names predate ticket 13, with pointers to ADR-0002 and `head_table.LEGACY_COLUMNS`.
- [x] Both suites at the 8-name baseline; no Slurm job unless a default changes a written number (a default change alone does not). *(Orchestrator's own runs on fa02314: base 8 failed / 1024 passed, mgnp 8 failed / 1177 passed, the same 8 names in both.)*
- [x] Subagent code review against the spec completed and findings addressed.

## Comments

### What was built

Four commits on `ca/17-block-e-decisions-follow-ups`, base `4086e12`:

    cd9abe8  Flag the knockout sweep at 0.4 and set the layer 0 MLP aside as a positive control
    28f9a53  Give the path-patching sweep its own 0.05 threshold, apart from the Segment pass
    75f2cf6  Note a knockout effect with an established read, and keep rule 6 literal
    a391977  Say at the top of the SDR first-run write-up that it is in the legacy conventions

plus one review-fix commit, `4aa41a0  Take the independent reviews: units in
the default names, one outsider test, reversed margin`. The tip is `4aa41a0`.
Names below are as of the tip.

**1. Knockout sweep threshold 0.4.** `knockout.DEFAULT_SWEEP_THRESHOLD_LOGITS = 0.4`.
The reason is in `--help`, in `sweep.json`'s `threshold_justification`, in the
constant's comment and in docs/component-roles.md: hand-tuned on SDR nls0.3,
tune by hand per run, and the full ranked list is always written. The code
text interpolates the default. The SDR observation (20 strongest outsiders at
0.4, 90 at 0.1) is dated in the docs only. The ladder stays and, on the
orchestrator's call after the standards review, gained a 0.4 rung:
`(0.02, 0.05, 0.1, 0.2, 0.4)`. Counts on the sweep of record
(`ca15-knockout-sweep`, job 22874364), recomputed from its `components`:

| cut (logits) | outside the circuit | of which the layer 0 MLP | in the circuit |
|---|---|---|---|
| 0.2 | 51 | 1 | 2 (L17H25, L31 MLP) |
| 0.3 | 34 | 1 | 2 |
| **0.4** | **21** | 1 | **1 (L17H25, +0.454)** |
| 0.5 | 13 | 1 | 0 |

**2. The layer 0 MLP is a positive control.** `knockout.POSITIVE_CONTROLS =
(("mlp", 0, 0),)`. On SDR nls0.3 its knockout reverses the margin (drop +3.12
against a clean 1.66, accuracy 0.01). Every sweep row carries
`positive_control`; the layer 0 MLP stays in `components`, ranked (rank 1 on
SDR) and drawn. Through one test, `counts_as_outsider`, it is left out of
`flagged`, `strongest_outside_circuit` and `threshold_counts[*].outside_circuit`;
the `in_circuit` counts are untouched. `sweep.json` gains a
`positive_controls` block (`components`, `why`, `treatment`), and
`flagged_means` and `figure.shows` say so. On `sweep.png` the bar is hatched,
its tick reads `mlp.0.0 (positive control)`, and the legend has a third entry;
the hatch keeps the mark readable under a blue-light filter and in greyscale,
as the circuit highlight is. The notebook view's hover says "positive
control" (one line in `review.py`). The run's print line says "positive
controls aside".

**3. `--path-sweep-threshold` defaults to 0.05.** `path_patching.DEFAULT_SWEEP_THRESHOLD_GAP_FRACTION
= 0.05`; `sweep_threshold` never falls back to `--path-position-threshold`.
`--help` (both flags; the position flag's stale sentence about flagging sweep
Components is removed), the sweep JSON's `threshold_flag`
(`SWEEP_THRESHOLD_FLAG`) and the README say so. Three existing CLI tests that
steered the sweep through `--path-position-threshold` now pass
`--path-sweep-threshold` too, and a new CLI-seam test checks the written JSON
uses 0.05 when only the position threshold is set. The path-patching output of
record (`ca14-path-patching-2`, job 22874991) was run with
`--path-sweep-threshold 0.05`, so the new default reproduces it exactly.

**4. Knockout effect with an established read.** `roles.knockout_only` is
unchanged in behaviour. The clauses it shares are now one helper,
`knockout_alone_of_the_support_views` (knockout significant; DLA, differential,
suppression, direct, onward and own-query honest paths measured and silent),
and `knockout_with_established_read` is that helper plus an established read.
`propose` appends "; knockout effect with an established read (knockout
supports|opposes deception, reads <Segment>; DLA and path views silent)" to the
notes in `decide`, beside the pressure-reader note, so the role, the flavour
and the note's `unknown/insufficient:` prefix do not change. docs/component-roles.md
names the case right after rule 6 and logs a 2026-10-14 line under "Changing
these criteria" (no criterion changed, so rule 2 asks for no rerun).

Tests on the hand-built table: the three heads' numbers (L5H11
`item_1_question_option` 0.35, knockout +0.150; L14H7 `question` 0.32, -0.094;
L14H22 `question` 0.29, +0.112) get the note and stay `insufficient`; a
knockout-only row does not; L5H5's case (a `question` read, knockout z = 1.8)
does not; an established read with DLA or an onward path speaking does not.

**Mechanical pass on a copy of `sdr-first-run`** (`outputs/_analyses/ca17-sdr-first-run`
in this worktree, not committed; base env): **0 binder, 0 selector, 1 mover,
0 suppressor, 17 unknown**, flavours 11 insufficient and 6 knockout-only, no
role changed against the record, and the note lands on exactly **L5H11, L14H7
and L14H22** and no other row.

**5. Legacy caveat.** A block quote at the top of the committed
`outputs/_analyses/sdr-first-run/delta__head/sdr/result_summary.md`. A
`LEGACY.md` beside the head table of each pre-2026-10-13 cell of record in the
`component-analysis` worktree (ignored by git there; that worktree's
`git status` stays clean). Each note is tailored from the cell's own files: the
sign caveat lists the cell's legacy-sign `*_effect` columns and says its
path-patching JSONs carry no `metric.convention` marker, or says the cell has
no path-patching output; the name caveat tabulates the cell's pre-13 names with
their current names from `LEGACY_COLUMNS`, or says it holds none. Where a
translated name is still a legacy-sign `*_effect*` column, the note says the
map renames only. Pointers: ADR-0002, `head_table.LEGACY_COLUMNS`, tickets 13
and 14.

`LEGACY.md` written (all under
`Deception-Circuit/.claude/worktrees/component-analysis/outputs/_analyses/`,
each at `<suite>/delta__head/sdr/LEGACY.md`):

| suite | path-patching sign caveat | pre-13 names |
|---|---|---|
| ca03-attention | n/a | none |
| ca03-attention-sink | n/a | none |
| dla-verify3 | n/a | 3 |
| ca07-knockout | n/a | none |
| ca08-path-patching | yes (4 columns, 3 JSONs) | none |
| ca06-paired2 | n/a | 5 |
| ca09-path-patching | yes (8 columns, 10 JSONs) | 6 |
| ca09-sweep | yes (6 columns, 7 JSONs) | none |
| ca10-roles | yes (8 columns, no JSON) | 12 |
| ca10-family | n/a | 2 (`knockout.family*`) |
| ca10-family2 | n/a | none |
| sdr-first-run | yes (8 columns, 10 JSONs) | 12 |
| sdr-first-run-desc | n/a | 5 |
| sdr-first-run-paths | yes (4 columns, 5 JSONs) | none |
| sdr-first-run-paths-hi | yes (4 columns, 5 JSONs) | 6 |
| sdr-first-run-family | n/a | none |
| sdr-first-run-sweep | yes (6 columns, 7 JSONs) | none |

`ca10-family`'s note attributes its `knockout.family*` names to ticket 10's
rename of 2026-09-20, not ticket 13's (spec review). On the spec review's
optional suggestion, a block E cell got a note too:
`ca15-knockout-sweep/delta__head/sdr/LEGACY.md`. It says the cell's `flagged`
list and `knockout.sweep_clears_threshold` were written at 0.1 with `mlp.0.0`
flagged and no `positive_control` field, and how to read it at 0.4.
That makes 18 files in all.

`dla-verify` and `dla-verify2` are on disk there but are not cells of record
(superseded by `dla-verify3`), so they got no note.

CONTEXT.md gained a **Positive Control** glossary entry (standards review).

### No Slurm job

None was run. A default or a note changes no number already written. The
knockout sweep of record `ca15-knockout-sweep` predates this ticket: its
`sweep.json` has `threshold` 0.1, its `flagged` list is the 90 at 0.1 (with
`mlp.0.0` among them), and its rows have no `positive_control` field, the same
way ticket 15 recorded its missing meta fields. Every number in it stands; a
reader can read it at 0.4 from `components` (20 outsiders, `mlp.0.0` aside).
A rerun only to refresh those fields was not asked for.

### Files touched (for the merge)

- **Owned by this ticket's decisions:** `component_analysis/knockout.py`,
  `component_analysis/path_patching.py`, `component_analysis/roles.py`.
- **Shared, additive:** `component_analysis/review.py` (one hover line),
  `README.md` (one sentence on the path sweep threshold),
  `docs/component-roles.md` (sweep paragraph, the note beside rule 6, a dated
  log entry), `CONTEXT.md` (one glossary entry, Positive Control).
- **Committed write-up:** `outputs/_analyses/sdr-first-run/delta__head/sdr/result_summary.md`
  (caveat block at the top).
- **Tests:** `tests/test_knockout_sweep.py`, `tests/test_knockout_model.py`,
  `tests/test_path_patching.py`, `tests/test_path_patching_passes.py`,
  `tests/test_roles.py`.
- **Not touched:** `analyze_components.py`, `registry.py`, `hooks.py`,
  `head_table.py`, `dataloaders.py`, the sbatch, the notebook, the shared
  nnsight probe.
- **Outside git:** 18 `LEGACY.md` files in the `component-analysis` worktree
  (listed above), and the roles-pass copy `outputs/_analyses/ca17-sdr-first-run`
  in this worktree.

### Open questions for the researcher

1. **`ca15-knockout-sweep` is not rerun.** Its `sweep.json` and
   `knockout.sweep_clears_threshold` stay at 0.1, with `mlp.0.0` flagged; a
   `LEGACY.md` says so. A rerun would refresh only those fields (23 min on an
   A100).
2. **`POSITIVE_CONTROLS` is the layer 0 MLP of any model**, by key. The
   decision was made on Llama-3.1-8B SDR; whether it holds for other tasks or
   models is unmeasured.
3. **docs/component-roles.md still says the `--path-position-threshold`
   question is "recorded here, not decided".** The researcher decided on
   2026-10-13 to keep its default and tune it by hand. Updating that paragraph
   was outside this ticket's checkboxes, so it is left as it is.

### Tests

| env | `4aa41a0` | final tip `fa02314` | new failures on `fa02314` |
|---|---|---|---|
| login-node base (py3.9, BLAS pins) | 8 failed, 1024 passed, 58 skipped | 8 failed, 1024 passed, 58 skipped | none: the same 8 names |
| `mgnp` (py3.12, nnsight 0.7.0) | 9 failed, 1176 passed, 19 skipped | 8 failed, 1177 passed, 19 skipped | none: the same 8 names |

Failure lists were compared by name. The 8 are the known ones in
`test_benchmarks.py`, `test_deception_common.py` and `test_deception_tasks.py`.
The ninth on `4aa41a0` was
`test_knockout_model.py::test_the_sweep_columns_land_on_circuit_rows_only_with_their_coverage`,
which is nnsight-gated and so ran only in `mgnp`. It expected a threshold-0
sweep to flag every outsider. The tiny circuit lacks `mlp.0.0`, which is now a
positive control, so it is correctly unflagged. `fa02314` updates the
expectation and asserts the control is named.
That failure came from this ticket's own change, not a regression elsewhere. I
missed it before the full run because I had run only the base-env files and the
two path files in `mgnp`. Checkbox 6 is left for the orchestrator, who is
rerunning both suites on `fa02314`. A mutation check bit as intended: turning
off the figure's mark fails the PNG test. No `core.*` dump appeared.

### The code review

`mattpocock-skills:code-review` against `4086e12`, both axes as independent
parallel sub-agents. Both handbacks failed. Both reports came by message to
me and to the orchestrator, who forwarded each with calls. **The review is
independent of the author.** Report, with both reviews verbatim and every
outcome: `Alignment/.scratch/component-analysis/reports/17-block-e-decisions-follow-ups-review.md`.

- **Standards: no hard violation; six judgement calls, all fixed in
  `4aa41a0` per the calls.**
  - One `counts_as_outsider`, with the key read one way.
  - The default interpolated into its justification and help.
  - 0.4 added to the ladder.
  - Unit-named defaults, and the "does not follow" sentence spelled once.
  - A PNG test that fails without the mark, and a flagging test that fails if
    the sweep follows the position threshold.
  - A Positive Control glossary entry.
  - Also the copy-check result added to the criteria-doc entry.
- **Spec: two partials and two wording errors, all fixed.**
  - The LEGACY.md list is above.
  - The suites are above.
  - The layer 0 MLP knockout "reverses" the margin, not "almost removes" it
    (`4aa41a0`).
  - `ca10-family`'s note attributes its rename to ticket 10.
  - The optional `ca15-knockout-sweep` note was written.
  - The review.py hover is kept by the call.


### Orchestrator's close-out (2026-10-14)

Fast-forwarded into `component-analysis` (tip fa02314; the base was the tip,
so no rebase). Suites rerun by the orchestrator on fa02314: base 8 failed /
1024 passed / 58 skipped, mgnp 8 failed / 1177 passed / 19 skipped, the same
8 pre-existing names. Worktree `ca-17` removed. The co-author trailer naming
Fable 5.1 on commits an Opus 5.5 session wrote is left as is (the researcher
accepted model-naming trailers; rewriting history is not worth it). The three
researcher items (rerun ca15-knockout-sweep at 0.4; positive control keyed to
any model's layer 0 MLP; the stale "not decided" paragraph on
`--path-position-threshold`) go to the block E close-out.
