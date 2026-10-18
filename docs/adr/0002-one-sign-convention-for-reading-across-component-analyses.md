# ADR-0002: One sign convention for reading across the component analyses, applied by derived columns rather than by rewriting an output

Date: 2026-09-20
Status: accepted

## Context

Four analyses write per-Component numbers into one head table, and two of them
disagree about what a positive number means.

- **Knockout** (`knockout.logit_diff_drop`) is
  `clean logit difference - knocked-out logit difference`. **Positive means the
  Component helps deception**: removing it moves the model away from the
  deceptive answer.
- **DLA** (`dla.pressure` and its siblings) is the Component's contribution to
  `logit(deceptive answer) - logit(honest answer)` at the Readout, with the
  Honest Twin condition negated into that same direction. **Positive means the
  Component writes towards deception.**
- **Path patching** (`path_patching.direct_effect` and every `*_effect` cell)
  is `(patched - clean) / (clean - counterfactual)`. **Negative means the path
  carries the counterfactual** — for the item-swap pair, that the path carries
  the Corruption, which is the same physical claim knockout states with a
  positive number.
- **Attention masses** are non-negative and carry no direction at all.

So a reader scanning one row of the head table meets `+0.4465` and `-0.0207`
for the same head and has to remember which column reverses. The researcher's
block D decision was that each analysis keeps its native sign, each JSON states
its own convention in its `meta`, and the roles vocabulary settles one
convention for reading across them.

Each of those columns is an output of record with GPU runs behind it
(`outputs/_analyses/ca03-attention`, `dla-verify3`, `ca07-knockout`,
`ca08-path-patching`, `ca06-paired2`, `ca09-path-patching`, `ca09-sweep`), and
tickets 03 and 09 both note that a sibling analysis reads a column by name.

## Decision

**The deception-support convention: a number is positive when the Component
supports the deceptive answer.** It is the convention every cross-analysis
reading uses — the role criteria in `docs/component-roles.md`, the roles JSON,
and any figure or notebook panel that puts two analyses on one axis.

It is applied in one of two ways, never a third:

1. **A column whose native sign already matches is read natively**, and the
   criteria say so where they read it. `knockout.logit_diff_drop` and every
   `dla.*` column are read natively.
2. **A column whose native sign is opposite gets a new derived column** in the
   reader's own namespace, never a change to the original. The roles pass adds
   `roles.direct_support = -path_patching.direct_effect` and
   `roles.direct_support_honest_instruction_paired =
   -path_patching.direct_effect_honest_instruction_paired`, with the standard
   errors copied across unchanged (a standard error has no sign). (Both
   honest-instruction names gained `_paired` on 2026-10-13; see the
   amendment below.)

**No existing column, JSON key or figure is renamed, re-signed or rewritten.**
`path_patching.direct_effect` keeps its native sign and its meaning in every
file already written, and `path_patching.json`'s `metric` block keeps saying
what it says.

Magnitudes that carry no direction are read as magnitudes, and the criteria say
so: `attention_patterns.*_top_mass` is a probability mass, and
`path_patching.strongest_incoming_effect` and `strongest_outgoing_effect` are
read as `|effect|` with the receiver's name, because "which Component feeds
which" is a question about the size of a path, not its direction.

**Under the Honest-Instruction Counterfactual the counterfactual is the honest
prompt**, so a negative `path_patching.*_honest_instruction_paired` cell means
the path carries the *honest instruction*, not the Corruption. The derived
`roles.direct_support_honest_instruction_paired` is therefore positive when the
Component supports the deceptive answer *against* the honest instruction, which
is the same convention. **No criterion reads that column today**; it is
written for the notebook and for a reader comparing the two
counterfactuals, and it carries ticket 09's caveat that it covers 71
instances where its item-swap partner covers 100.

## Alternatives

- **Flip `path_patching`'s sign at the source.** Rejected: it rewrites outputs
  of record, silently changes the meaning of every `path_patching.json` already
  written, and would make the tables in tickets 08 and 09 wrong without
  marking them.
- **Let the roles criteria read each column in its native sign and simply say
  which is which.** Rejected for the columns that flip: a criterion reading
  `direct_effect <= -0.005` beside `logit_diff_drop >= +0.01`, both meaning
  "supports deception", is exactly the trap this ADR exists to close. The
  derived column makes the convention checkable in the table rather than only
  in prose.
- **A single global "support" table replacing the per-analysis columns.**
  Rejected: analyses are implemented and reviewed one module at a time, and a
  derived column that a later analysis may ignore is additive where a
  replacement table is not.

## Consequences

- Any later analysis whose native sign is opposite adds its own derived
  `<namespace>.*_support` column rather than negotiating with the original.
- The head table now carries two columns for the same measurement
  (`path_patching.direct_effect` and `roles.direct_support`). They are exact
  negations of each other, and the roles JSON records that relation so a reader
  who finds only one of them can reconstruct the other.
- `roles.*` columns exist only after the roles pass has run, so a cell that
  never runs the pass is unaffected. One thing does read them back: the
  family knockout groups by `role_confirmed` else `roles.role_proposed`
  (`component_analysis/knockout.py`), and every run into a cell carries them
  forward with the cell's other columns (ticket 13). Any other reader should
  expect them to be absent.

## Amendment, 2026-10-13: names change, signs do not

The researcher decided that **every paired column carries `paired` in its
name**. That renames, without re-signing or rewriting, the honest-instruction
columns of three analyses (`dla.honest_instruction` to
`dla.honest_instruction_paired`, `dla.differential` to
`dla.differential_paired`, `path_patching.*_honest_instruction` to
`path_patching.*_honest_instruction_paired`, the paired attention column, and
the derived `roles.direct_support_honest_instruction`). It is a departure from
"no existing column is renamed" above, made deliberately and limited to names:

- no value and no sign changes, and nothing rewrites a cell of record for the
  rename — the cells of record keep the names they were written with until
  something is run into them: a later roles pass or `analyze_components.py`
  run into a legacy cell (a dry run included) writes its head table back
  under the current names, with the same values, and records each
  translation in the meta's `renamed_columns`;
- every reader translates an old name through one map,
  `head_table.LEGACY_COLUMNS`, so an old cell reads under the new names (the
  roles pass, the notebook seam and `analyze_components.py`'s carry-forward
  all do), and records the translation it made;
- a column whose **meaning** changes — a sign flip included — never goes in
  that map. The same day the researcher also decided that path patching's sign
  flips to agree with knockout (positive helps deception), with old cells told
  apart by their JSON meta; that change, and how this ADR's derived-column rule
  meets it, is recorded in the next amendment.

## Amendment, 2026-10-13 (ticket 14): path patching now writes the support sign, under new names

The researcher decided that path patching's sign agrees with knockout. **For
every run from this date, a path-patching cell is `(clean - patched) / (clean -
counterfactual)`: positive means the path helps the deceptive answer**, the
same claim knockout's positive drop makes. This revisits the first rejected
alternative above ("flip `path_patching`'s sign at the source"), and keeps the
reason it was rejected: no output of record is rewritten.

- **New sign, new names.** The columns whose sign changed are new columns:
  `path_patching.direct_support`, `direct_support_se`,
  `strongest_incoming_support`, `strongest_outgoing_support` and
  `sweep_direct_support`, `sweep_direct_support_se`, with honest-instruction
  twins that end `_honest_instruction_paired` and put a standard error last
  (`direct_support_honest_instruction_paired_se`). The names of the strongest
  cells, the sweep's rank and flags, and the files themselves keep their names,
  because selection by absolute effect did not change.
- **Old cells keep their old sign under their old names**
  (`path_patching.direct_effect`, `*_effect`). `head_table.LEGACY_COLUMNS`
  maps neither generation into the other, because a sign is meaning; a reader
  tells them apart by which names a row carries.
- **Every path-patching JSON carries the marker** `metric.convention =
  "positive_helps_deception"` (with `convention_version: 2`) beside the `sign`
  sentence. A file without it is legacy (`path_patching.convention_of`). The
  review seam puts the convention in every path figure's subtitle and shows
  values as written; `scripts/check_cell.py` prints it, and calls out a cell
  whose directory holds both (a new run into a legacy cell rewrites only the
  files of the passes it ran).
- **The derived-column rule now applies to legacy cells only.** On a new cell
  `roles.direct_support` is `path_patching.direct_support` read natively (rule
  1 above); on a legacy cell it is `-path_patching.direct_effect`, as before
  (rule 2). The two give the same number for the same measurement, so no
  criterion and no role moves; a row carrying both generations is refused by
  name rather than read either way. The roles pass tells the generations
  apart by column name, and where the cell holds the path-patching JSON the
  columns came from, it also requires that file's `metric.convention` marker
  to agree, and refuses the cell by name when it does not. `roles.json`
  records the markers it read in (`path_conventions`).

Why names and a JSON marker, rather than a marker alone in the head table's
meta: a column name travels with its values through every merge, carry-forward
and CSV export, and the CSV has no meta at all, so a marker kept only in the
meta could be lost on the way while the numbers survived; with distinct names,
an old number can never be read as a new one.
