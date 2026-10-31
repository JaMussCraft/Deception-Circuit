# 02b — criteria amendment DRAFT for `docs/component-roles.md` (R1, R7, R10)

**Status: DRAFT. Not applied.** Per R10 the text below goes into `docs/component-roles.md` only after the
orchestrator confirms it has reported it to the user. This file is the exact text, in the doc's own vocabulary and
metric names. The code columns it names are the ones ticket 02b writes (`component_analysis/attention_patterns.py`,
`component_analysis/path_patching.py`, `component_analysis/receiver_category.py`).

The orchestrator's ruling (R1) under the user's standing go, reported to the user first. Every earlier amendment in
the doc's change log is "the researcher's decision"; this one is recorded as "orchestrator ruling R1/R7, reported
to the user on <date>" and is the first that changes an assignable role on any cell.

---

## A. Change-log entry (goes at the end of "Changing these criteria", before "The rest of this section")

**2026-10-25 — v2 cells: the Neutral-Clause Twin as the paired counterfactual, `pressure reader` un-reserved for
v2 cells, `response_line` in `frame`.** Reason: mechanism-analysis spec rulings R1 and R7 (orchestrator ruling under
the user's standing go, reported to the user before this text was applied, R10). The v2 tasks (`far_v2`, `sdr_v2`,
`ser_v2`) have no Matched Honest Instruction pool and will not get one (R1). Their paired honest counterfactual is
the **Neutral-Clause Twin**: the same instance with the Pressure Clause replaced by a token-matched neutral
sentence, paired by instance id, read with the pressure prompt's Target and Distractor. Every column computed over
it says `neutral_twin_paired` in its name (the researcher's 2026-10-13 rule). Four things change, **for v2 cells
only**; a cell is a v2 cell when `head_table.json` records `meta.task.task` in (`far_v2`, `sdr_v2`, `ser_v2`). v1
cells read exactly as before, which the byte-identity snapshot `tests/test_v1_snapshot_02b.py` enforces.

1. **Rule 4 (selector), depends (query side).** On a v2 cell the clause reads
   `path_patching.strongest_incoming_neutral_twin_paired` and
   `path_patching.strongest_incoming_support_neutral_twin_paired` in place of the honest-instruction pair. Rule 6's
   last clause ("no honest-instruction path at the Component's own query") reads the same two columns on a v2
   cell. The number compared, the floor (`--roles-path-floor` 0.01) and the receiver test (a `q.` receiver on this
   Component) are unchanged; only the counterfactual the path is measured against changes.
2. **Rule 4b (pressure reader), v2 cells only.** New assignable role, checked after rule 4 (selector) and before
   rule 5 (mover). Text in section B.
3. **Segment groups.** `response_line` (the v2 frame line "Only respond with ...", carved out of `question` by
   02a) joins the `frame` group: `frame` = `intro`, `question`, `response_line`, `stem`. On a v1 cell no
   `response_line` Segment exists, so no v1 read can change.
4. **The pressure-reader note.** On a v2 cell the note "pressure-reader signature" is written from the B2 columns
   (section B) instead of the honest-instruction top-Segment pair, and reads "pressure-reader signature (B2)". On a
   v1 cell the note and the reserved status are unchanged.

Thresholds added: `--roles-b2-floor` 0.05 (spec §2 B2, the spec-writer's proposal per R0, not a calibration);
the same `z` = 2 as every other criterion. No existing threshold moves.

Per rule 2 of this section, every v2 cell with a role column is rerun under the amended criteria; there is none
yet (no v2 roles pass has run, which is what R1 requires). v1 cells of record are not rerun: no v1 criterion
changed.

## B. Rule 4b — pressure reader (v2 cells only), inserted between rules 4 and 5 under "The criteria"

**4b. pressure reader (v2 cells only).** On a v1 cell this rule is skipped and the name stays reserved. On a v2
cell, all of:

- reads (paired, the **B2 signature**): `attention_patterns.clause_mass_drop_neutral_twin_paired` — the head's
  Readout-query attention mass on `pressure_clause` under the pressure prompt minus under its Neutral-Clause Twin,
  paired per instance over the whole test split — is at or above the B2 floor (0.05) and at least `z` = 2 of its
  paired standard error `attention_patterns.clause_mass_drop_neutral_twin_paired_se`. (`pressure_neutral_twin_paired_top_segment`
  is `pressure_clause` in the textbook case, but the criterion is the paired drop, not the top-Segment pair: a head
  can read the clause under pressure and still read it under the twin, and that is not a pressure reader.)
- depends (whether, post-clause): the neutral-twin knockout drop at post-clause positions
  (`knockout.logit_diff_drop_neutral_twin_paired_after_pressure_clause_excl_readout`, the 1B sweep S2p; standard
  error `knockout.standard_error_neutral_twin_paired_after_pressure_clause_excl_readout`) is significantly
  positive and at or above the knockout floor — the Component carries the pressure, in the deceptive direction,
  somewhere after the clause. The column may be merged in from the phase-1 sweep cell with `--roles-merge-from`.
- depends (how), **where path patching under the twin exists for the cell**:
  `path_patching.strongest_incoming_neutral_twin_paired` names a `k.` or `v.` receiver of **this head's KV
  group** with `|support|` at or above the path floor, and the receiver category
  (`path_patching.receiver_category_neutral_twin`, section C) is `kv_clause`: the pressure arrives at the head's
  keys or values from the clause span. A `q.` arrival is rule 4 (selector), which is checked first. **Without
  path data** (the column absent or unmeasured) the role is assigned on the two clauses above and the flavour
  `pressure reader/attention and knockout only` is written, so a reader sees that the where-clause was never
  tested rather than passed.
- writes: not a clause. A pressure reader may or may not write the answer; the DLA columns go in the notes.

A head that meets the B2 signature but not the knockout clause gets the note "pressure-reader signature (B2),
knockout silent post-clause" whatever role it receives; a head whose strongest neutral-twin path is K or V from
post-clause positions (`kv_post_clause`) is not a pressure reader (it reads items the pressure already changed:
spec §2.3's mover reading) and is noted as such.

The reserved-role paragraph under "The vocabulary" gains one sentence: "**On v2 cells (mechanism-analysis spec
R1) the role is assignable, by rule 4b**; v1 cells keep it reserved because they have no Neutral-Clause Twin."

## C. Columns added to "The columns the criteria read"

| view | columns | sign |
|---|---|---|
| reads (paired, v2) | `attention_patterns.pressure_neutral_twin_paired_top_segment` / `_top_mass`, `attention_patterns.neutral_twin_paired_top_segment` / `_top_mass` | names and mass, no direction |
| reads (B2, v2) | `attention_patterns.clause_mass_drop_neutral_twin_paired`, `..._se` | positive: less mass on the clause under the twin |
| depends (query side, v2) | `path_patching.strongest_incoming_neutral_twin_paired`, `path_patching.strongest_incoming_support_neutral_twin_paired` | magnitude and receiver name |
| depends (direct, v2) | `path_patching.direct_support_neutral_twin_paired`, `..._se` | native: positive helps deception, against the twin |
| depends (where, v2) | `path_patching.receiver_category_neutral_twin` in {`q`, `kv_clause`, `kv_post_clause`, `kv_unresolved`, `none`}, with `..._path`, `..._support`, `..._se`, `..._segment` | category; support signed as above |
| depends (whether, post-clause, v2) | `knockout.logit_diff_drop_neutral_twin_paired_after_pressure_clause_excl_readout`, `knockout.standard_error_...` | native: positive supports deception |

**Receiver category (spec §2.3, R11(g)).** Per head, from the neutral-twin path-patching outputs: the strongest
incoming cell by `|mean|` at or above the path floor (0.01) among the cells into this head's own `q.` receiver and
into its KV group's `k.` and `v.` receivers.

- `q`: the receiver is the head's query (selector).
- `kv_clause`: K or V, and the position-specific split of that cell has its top Segment (by `|mean|`) at
  `pressure_clause`.
- `kv_post_clause`: K or V, top Segment after the clause (`question`, `response_line`, the four `item_*_question_*`
  mentions, `stem`, `readout`).
- `kv_unresolved`: K or V, but no position-specific split exists for the cell (its `|mean|` is below
  `--path-position-threshold`), or the split's top Segment is `unsegmented`. Counted separately and never folded
  into clause or post-clause. A top Segment **before** the clause is impossible by construction (every pre-clause
  position is identical in D and its twin) and is reported as `kv_unresolved` with a `!!` note: it is a bug.
- `none`: no incoming cell at or above the floor.

Ties: the strongest cell is chosen by `|mean|`; on an exact tie the tied cells are listed and the choice goes to
the first in receiver order (`q`, `k`, `v`). Two tied K and V cells of one KV group agree on the category when
their top Segments fall in the same class; when they do not, the category is `kv_unresolved` and the tie is
recorded. K and V receivers are per KV group, so this category is a claim about the group's heads together, not
about one head (the four L17H24-27 heads are one test, spec §7).

**Phase-3 setting that the category needs.** The position-specific pass runs only on cells whose
position-agnostic `|mean|` clears `--path-position-threshold` (default 0.05), while the category's floor is 0.01.
A phase-3 grid therefore runs with `--path-position-threshold 0.01` under the neutral-twin counterfactual, so
every K/V path above the category floor has its Segment split; otherwise paths between 0.01 and 0.05 read
`kv_unresolved`. The cost of the lower threshold is in the 02b dry-run tables.

## D. Operational decisions carried with the amendment (for the orchestrator, not for the doc)

- `--path-counterfactual both` means `item_swap` + `honest_instruction` on a v1 task (unchanged, byte-identical)
  and `item_swap` + `neutral_twin` on a v2 task (there is no Matched Honest pool for v2, R1).
  `--path-counterfactual neutral_twin` alone is also accepted; on a v1 cell, or on a v2 H/F cell (no twin), the
  pass writes the skipped file with the loader's reason, as the honest pass does.
- Attention patterns on a v2 cell profile `neutral_twin` by default (the paired condition brings its left term
  `pressure_neutral_twin_paired` with it, as `honest_instruction` brings `pressure_paired`); the v1 default
  condition list is unchanged. `--attention-conditions` accepts `neutral_twin`.
- `roles.SEGMENT_GROUPS["response_line"] = "frame"` is a code change with the amendment; on a v1 table the
  Segment never occurs, so the snapshot stays byte-identical.


---

Applied 2026-10-25 (R25, orchestrator ruling). Decision A is implemented as a separate flag, `--path-twin-position-threshold 0.01`, that lowers the neutral-twin pass's position threshold alone; the item-swap pass keeps `--path-position-threshold 0.05`. The text above says `--path-position-threshold 0.01` because the flag did not yet exist when it was written; `docs/component-roles.md` carries the applied wording.
