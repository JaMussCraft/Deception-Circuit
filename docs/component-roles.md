# Component Roles: the vocabulary and the assignment criteria

Status: pre-registered 2026-09-20, before any role was assigned to any
Component of any circuit.
Owner of the final labels: the researcher, in `role_confirmed`.
Applied by: `python analyze_components.py roles <cell dir>`.
Sign convention: ADR-0002.
Glossary: `CONTEXT.md`, "Prompt anatomy (component analysis)".

This file is the whole of the role vocabulary. A role is assigned by the
criteria written here or it is not assigned at all; the mechanical pass in
`component_analysis/roles.py` implements exactly these rules and writes what it
decided, and an agent may rewrite the *notes* afterwards but not the role.

## The rule the glossary imposes

> **Component Role**: a label for what a Component does in the task, assigned
> only from the conjunction of where it reads (attention pattern), what it
> writes (direct logit attribution) and what it depends on (path patching). No
> single view assigns a role.

Three views, and a role needs all three of them to agree on one story. The
consequence, stated here so it is not read later as a bug: **a Component whose
views are silent or partial gets `unknown`, not the role its loudest column
suggests.** On a real circuit that is the common outcome, and the criteria are
not softened to avoid it. What the pass can still say goes in `role_notes`,
which carries the lean and the numbers behind it.

### Where knockout enters

Knockout is not one of the glossary's three views, and it is not made into a
fourth. It joins **depends**, which the criteria split in two:

- **whether** the Component matters causally at the Readout, and in which
  direction: `knockout.logit_diff_drop`, read natively (ADR-0002).
- **how** its effect reaches the Readout: directly, as a path into the Readout
  receiver (`roles.direct_support`), or indirectly, through another
  Component's Q, K, V or MLP input
  (`path_patching.strongest_outgoing`, read as a magnitude).

### MLP blocks have no reads view

An MLP block has no attention pattern, so `attention_patterns.*` is null on its
row. That is not a missing measurement, it is the Component definition: an MLP
block is a single unit with no query position to read from. For an MLP the
reads view is **not applicable** and the conjunction is over the remaining two
views. For a head, a null attention column is a *missing* measurement and the
reads view is **unestablished**, which is not the same thing.

## The vocabulary

Five assignable roles and one reserved name.

**binder** — reads the designation and hands it on. It attends to the
Designating Sentence's Designation Positions (or its Suffix) at the query
position, writes nothing measurable at the Readout, and its causal effect
reaches the Readout only through another Component. The pre-registered
hypothesis places binders in layers 7 to 9; **layer is not a criterion** and
never becomes one, so that the hypothesis can be wrong.

**selector** — chooses which item the Readout will name, and the choice depends
on the pressure. It writes a measurable, pressure-dependent contribution at the
Readout, and the Honest-Instruction Counterfactual reaches it at **its own
query**: the honest-instruction path patching says its strongest incoming path
is a `q.` receiver on this Component. That is the spec's "the lie signal enters
at their queries", made mechanical.

**mover** — writes the selected item to the Readout. It writes a measurable
contribution towards the deceptive answer, its effect reaches the Readout
directly rather than through another Component, and the honest instruction does
*not* arrive at its query. A mover's DLA may still flip when the honest
instruction flips what was selected upstream: a mover that does not know it is
lying is still a mover, which is why the flip alone does not separate mover from
selector and the query-side path does.

**suppressor** — opposes the deceptive answer. It writes towards the honest
answer at the Readout and its knockout *raises* the deceptive margin. Because a
suppressor is defined by what it produces rather than by what it reads, the
reads view constrains it only by not contradicting it; the read is recorded in
the notes.

**unknown** — everything else, in two flavours that the notes name apart:

- `unknown/disagree` — two support views are significant in opposite
  directions. The Component does something, and the views do not agree on what.
- `unknown/insufficient` — some view is silent, unestablished, or below its
  floor. The notes carry the lean ("mover lean: writes and direct effect
  support deception, read unestablished").

**pressure reader** — **reserved and never assigned.** A pressure reader would
attend to the Pressure Clause under pressure and leave it under the Matched
Honest Instruction. Finding them is out of scope (spec, Out of Scope): it needs
a dataset variant with an honest-instruction Corruption and a mask trained on
it, so a circuit discovered against the item-swap Corruption has no reason to
contain them. The name is held so that nothing else takes it. The mechanical
pass **notes** a pressure-reader signature when it sees one
(`attention_patterns.pressure_paired_top_segment` is `pressure_clause` and
`attention_patterns.honest_instruction_top_segment` is not) and assigns
`unknown` all the same.

## The columns the criteria read

Every column named here is written by an earlier analysis and read, never
written, by the roles pass. The roles pass writes only `roles.*` columns.

| view | column | sign |
|---|---|---|
| reads | `attention_patterns.pressure_top_segment` / `_top_mass` | mass, no direction |
| reads (paired) | `attention_patterns.pressure_paired_top_segment`, `attention_patterns.honest_instruction_top_segment` | names, no direction |
| writes | `dla.pressure`, `dla.pressure_se` | native: positive supports deception |
| writes (paired) | `dla.honest_instruction`, `dla.differential`, `dla.differential_se` | native |
| writes | `dla.suppression` | boolean, true means it favours the Distractor |
| depends (whether) | `knockout.logit_diff_drop`, `knockout.standard_error` | native: positive supports deception |
| depends (how, direct) | `roles.direct_support` = `-path_patching.direct_effect`, se from `path_patching.direct_effect_se` | **derived**, ADR-0002 |
| depends (how, indirect) | `path_patching.strongest_outgoing`, `..._effect` | magnitude and receiver name |
| depends (query side) | `path_patching.strongest_incoming_honest_instruction`, `..._effect_honest_instruction` | magnitude and receiver name |

`role_confirmed` is read if the table has it and **never written** by anything
in the package; `head_table.PROTECTED_COLUMNS` enforces that.

### Two columns do not cover the same instances

`dla.pressure` and `attention_patterns.pressure_*` are computed over the whole
test split; `dla.honest_instruction`, `dla.differential`, the paired attention
columns and every `*_honest_instruction` path column are computed over the
instances with a Matched Honest survivor (71 of the 100-instance causal sample
on SDR nls0.3), and `knockout.*` and `path_patching.direct_effect` over all 100.
The criteria never subtract one from the other across that boundary: each
column is thresholded on its own, and the comparisons that must be paired
(`dla.differential`) are computed per instance by the analysis that owns them.

## Significance: a z-score and a floor, both

Every numeric criterion asks two questions, and a column must clear both.

1. **Is it distinguishable from zero?** `|value| / standard error >= 2.0`
   (`--roles-z`). Two standard errors, the same bar tickets 04, 06 and 07 used
   in prose. A column with no standard error (or a null one) fails the test:
   a number whose spread was never measured is not significant.
2. **Is it big enough to matter?** `|value| >= floor`, per view. A floor exists
   because several path-patching cells are four standard errors from zero at
   0.0005, which is noise measured precisely.

| flag | default | why this number |
|---|---|---|
| `--roles-z` | 2.0 | two standard errors |
| `--roles-dla-floor` | 0.01 logits | the SDR clean margin is about 1.6 logits, so this is under one percent of what the Readout has to explain |
| `--roles-knockout-floor` | 0.01 logits | the same scale on the same metric; it excludes the three Components ticket 07 called indistinguishable from zero |
| `--roles-path-floor` | 0.005 | half of one percent of the clean-minus-corrupt gap, which the patching metric normalizes to 1. Ticket 09's `--path-position-threshold` default of 0.05 admits exactly one cell on this circuit and ticket 09 asked for a weigh-in: **0.005 is the number these criteria use, and the recommendation is that the position threshold default move to it** |
| `--roles-attention-floor` | 0.20 | a Segment must carry a fifth of the head's mass at the query position before the pass calls it what the head reads |

The defaults are flags so a different task or circuit can be read at a
different scale, and the values actually used are written into `roles.json`
beside every decision.

## Segment groups: what counts as a read

The reads view is the **top Segment** at the query position and its mass. The
Segment names come from the task's segmentation (`segmentation.json`); the
groups are fixed here, from `CONTEXT.md`'s prompt anatomy, and an unrecognized
Segment name falls in `other`.

| group | Segments |
|---|---|
| `designation` | `designating_sentence`, `designation_site`, `predicate_token`, `other_token`, `inverse_predicate_token`, `designation_suffix` |
| `item_mention` | `item_1_intro`, `item_2_intro`, `item_1_question_pair`, `item_1_question_option`, `item_2_question_pair`, `item_2_question_option` |
| `pressure` | `pressure_clause` |
| `frame` | `intro`, `question`, `stem` |
| `unestablished` | `readout`, `unsegmented`, `other`, and any Segment not named above |

Three judgement calls, made here and not revisited:

- **`designation_site` is a Designation Position, not an Item Mention**, though
  it is anatomically both. It is the one token the Corruption edits, and a head
  reading it is reading the designation.
- **`question` is a frame, not an item-bearing read.** The Item Mentions inside
  the user question are carved out into their own Segments, so the mass left on
  `question` is the mass on the question's *other* words. A head topping out
  there has an established read of the question frame and has not been shown to
  read an item.
- **`unsegmented` is unestablished, not "no read".** On Llama it is mostly the
  `<|begin_of_text|>` attention sink, and ticket 03 showed nine of seventeen
  SDR heads topping out there at the Readout query. A sink head is not idle;
  the Readout query simply says nothing about it. Carving the sink out with
  `--segment 'bos=^<\|begin_of_text\|>'` moves the name but not the fact, so
  `bos` is unestablished too, by falling in `other`. The way to establish those
  reads is a different query position (ticket 03's `--query-positions`), not a
  lower bar.

## The criteria

Checked in this order, first match wins, so exactly one role comes out.

**0. No Component at all.** If every one of the three views is null — no
attention, no DLA, no knockout and no path patching — the role is
`unknown/insufficient` with the note "no analysis scored this Component".

**1. disagree.** If two of the three support numbers
(`dla.pressure`, `knockout.logit_diff_drop`, `roles.direct_support`) are
significant by the rule above and have opposite signs, the role is
`unknown/disagree`. This is checked before every assignable role, so no role is
ever assigned over a contradiction.

**2. suppressor.** All of:
- writes: `dla.pressure` significantly negative, **or** `dla.suppression` true;
- depends: `knockout.logit_diff_drop` significantly negative, **or**
  `roles.direct_support` significantly negative;
- reads: not contradicted (the reads view never blocks a suppressor; the top
  Segment and its mass go in the notes).

**3. binder.** All of:
- reads: top Segment in the `designation` group with mass at or above the
  attention floor;
- writes: `dla.pressure` **not** significant, or below the DLA floor — a binder
  does not write the answer;
- depends: `roles.direct_support` not significant or below the path floor
  (no direct path to the Readout), **and** `path_patching.strongest_outgoing`
  names a receiver that is not the Readout with `|effect|` at or above the path
  floor (it feeds another Component).

**4. selector.** All of:
- reads: established — top Segment in `designation`, `item_mention`, `pressure`
  or `frame`, with mass at or above the attention floor. Not applicable, and so
  satisfied, for an MLP block;
- writes: `dla.pressure` significant and above the DLA floor, **and**
  `dla.differential` significant and above the DLA floor — the contribution is
  pressure-dependent;
- depends (whether): `knockout.logit_diff_drop` or `roles.direct_support`
  significantly positive and above its floor;
- depends (query side): `path_patching.strongest_incoming_honest_instruction`
  names a `q.` receiver **on this Component**, with `|effect|` at or above the
  path floor. This clause is what separates selector from mover, and it is the
  one the researcher should argue with first.

**5. mover.** All of:
- reads: top Segment in `item_mention` with mass at or above the attention
  floor; not applicable, and so satisfied, for an MLP block;
- writes: `dla.pressure` significantly positive and above the DLA floor;
- depends: `roles.direct_support` significantly positive and above the path
  floor, **and** `path_patching.strongest_outgoing` names the Readout — its
  effect reaches the Readout directly;
- and not a selector by rule 4.

**6. unknown/insufficient.** Everything else. The notes say which views were
established, which were silent, and which role the established ones lean
towards, so that a researcher reading the table sees the evidence rather than
the word "unknown".

A Component that satisfies no role but whose views are all established and
agree is still `unknown/insufficient`; the notes say so, and that is a signal
that the vocabulary is missing a role rather than that the Component is dull.

## What the pass writes

Into the head table, namespaced `roles.`, next to the columns it read:

    roles.role_proposed     one of binder, selector, mover, suppressor, unknown
    roles.role_notes        one line: the flavour, the lean and the numbers
    roles.direct_support    the derived column of ADR-0002
    roles.direct_support_se
    roles.direct_support_honest_instruction
    roles.reads_group       designation / item_mention / pressure / frame /
                            unestablished / not_applicable

`role_confirmed` is left exactly as it was found, present or absent.

**A naming discrepancy, recorded so the notebook reads the right names.**
`spec.md` calls for a bare `role_proposed`, `role_confirmed`, `role_notes`
triple. The orchestrator's block C rule namespaces every column an analysis
writes, and `head_table.PROTECTED_COLUMNS` protects the bare `role_confirmed`.
The resolution in force: **`roles.role_proposed` and `roles.role_notes` are
namespaced, `role_confirmed` stays bare** because it is the human's column and
the protection is keyed on that exact name.

And into the cell, under `roles/`:

    roles/roles.json    every decision, every threshold, every criterion's
                        evaluated value and verdict, per Component

`roles.json` is the audit trail the spec asks for: for each Component it
records the three views' inputs, each criterion's pass or fail, the role and
the notes, so that a disputed label is settled by reading the file rather than
by rerunning the pass.

## Knockout by role family

Once roles exist, `--knockout-families` groups the Components by
`role_confirmed` where the researcher has set it and by `roles.role_proposed`
everywhere else, and interchange-ablates each group **together**, through the
same code path as the single-Component knockout. It answers the question a
per-Component ranking cannot: whether a family of small effects is a large one
together. Its sign convention is the single knockout's, unchanged — positive
means the family helps deception.

## Changing these criteria

The point of writing them down before running them is that the numbers cannot
argue them into a different shape. A threshold or a clause may be changed, and
then:

1. say so here, with the date and the reason;
2. rerun the mechanical pass over every cell that has a role column, because a
   role proposed under old criteria and one proposed under new criteria must
   not sit in the same table;
3. leave `role_confirmed` alone — it is the researcher's, and a criteria change
   is a reason to ask them, not to overwrite them.
