# Component Roles: the vocabulary and the assignment criteria

Status: pre-registered 2026-09-20, before any role was assigned to any
Component of any circuit. Stated plainly, because it is what makes the
thresholds auditable:

- the author had read the block C and D outputs of record (the SDR nls0.3 head
  tables) during orientation, so these numbers were not written blind;
- the criteria and every threshold were committed **before** any pass was run;
- **one threshold has since been amended** — the path floor, on 2026-09-20,
  for a reason external to any result — and **one flavour of `unknown` has
  been added** — `unknown/knockout-only`, on 2026-10-13, by the researcher's
  decision. Both changes, their reasons and the results they changed are
  logged under "Changing these criteria" at the end of this file. Nothing else
  has moved. Read that section before quoting a role.
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

**What that clause does and does not test.** It reads the *strongest single
incoming receiver*, which is not the same as the query dominating the
Component's input. Ticket 09's Slurm read-back is explicit that the two differ
where it matters: layer 9 is V-dominated through `head.8.15 -> v.9.3` in the
Pressure Clause, layers 13 and 14 are level between Q and K/V, and at layer 17
Q wins the single strongest cell while K and V are larger *in sum*. So a head
can satisfy this clause while most of the honest instruction reaches it
somewhere other than its query. The clause is the mechanical form of the
pre-registered hypothesis, not evidence for it, and a selector proposed by it
is a candidate for the Q-versus-V test the spec describes rather than the
result of one. A Q-dominance clause would need a per-receiver total the head
table does not carry; that is a column for a later ticket, not a criterion
here.

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

**unknown** — everything else, in three flavours that the notes name apart:

- `unknown/disagree` — two support views are significant in opposite
  directions. The Component does something, and the views do not agree on what.
- `unknown/knockout-only` — knockout is the only view that speaks: its
  knockout clears the bar, and it has no established read, writes nothing at
  the Readout and passes nothing on above the path floor. It matters causally
  and does nothing the four roles describe, and it is held here **until there
  is reads evidence** rather than given a fifth role (the researcher's
  2026-10-13 decision; the criterion is rule 6 below).
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
`attention_patterns.honest_instruction_paired_top_segment` is not) and **never
assigns the reserved name**. The note is appended whatever role the Component
gets, an assigned one included: a mover may also read the pressure, and that is
worth seeing.

## The columns the criteria read

Every column named here is written by an earlier analysis and read, never
written, by the roles pass. The roles pass writes only `roles.*` columns.

| view | column | sign |
|---|---|---|
| reads | `attention_patterns.pressure_top_segment` / `_top_mass` | mass, no direction |
| reads (paired) | `attention_patterns.pressure_paired_top_segment`, `attention_patterns.honest_instruction_paired_top_segment` | names, no direction |
| writes | `dla.pressure`, `dla.pressure_se` | native: positive supports deception |
| writes (paired) | `dla.honest_instruction_paired`, `dla.differential_paired`, `dla.differential_paired_se` | native |
| writes | `dla.suppression` | boolean, true means it favours the Distractor |
| depends (whether) | `knockout.logit_diff_drop`, `knockout.standard_error` | native: positive supports deception |
| depends (how, direct) | `roles.direct_support` = `-path_patching.direct_effect`, se from `path_patching.direct_effect_se` | **derived**, ADR-0002 |
| depends (how, indirect) | `path_patching.strongest_outgoing`, `..._effect` | magnitude and receiver name |
| depends (query side) | `path_patching.strongest_incoming_honest_instruction_paired`, `..._effect_honest_instruction_paired` | magnitude and receiver name |

`role_confirmed` is read if the table has it and **never written** by anything
in the package; `head_table.PROTECTED_COLUMNS` enforces that.

**Every paired column says `paired` in its name** (the researcher's 2026-10-13
decision): a column computed over the same instance ids on both sides of a
contrast is `..._paired...`, and one computed over the unpaired Honest Twin is
`..._descriptive...`. Cells written before that decision carry the older names
(`dla.differential`, `path_patching.*_honest_instruction`, ...). The pass reads
them under the current names — `head_table.LEGACY_COLUMNS` is the one map —
writes the table back under the current names, and records the translation
in `roles.json`'s `renamed_columns`.

### Two columns do not cover the same instances

`dla.pressure` and `attention_patterns.pressure_*` are computed over the whole
test split; `dla.honest_instruction_paired`, `dla.differential_paired`, the
paired attention columns and every `*_honest_instruction_paired` path column
are computed over the instances with a Matched Honest survivor (71 of the
100-instance causal sample on SDR nls0.3), and `knockout.*` and
`path_patching.direct_effect` over all 100. **The head table's meta says so
per column**: `meta.coverage[<column>]` gives `n` and an instance-set id, and
`meta.instance_sets[<id>]` lists the ids (`head_table.coverage_of` reads both).
The criteria never subtract one from the other across that boundary: each
column is thresholded on its own, and the comparisons that must be paired
(`dla.differential_paired`) are computed per instance by the analysis that
owns them. The derived `roles.direct_support*` columns take the coverage of the
path-patching column each negates.

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
| `--roles-path-floor` | 0.01 | one percent of the clean-minus-corrupt gap, which the patching metric normalizes to 1, and **twice ticket 09's measured cross-card noise floor** of about 0.005 on a path-patching cell (A40 against A100). A criterion resting on a cell inside that noise is one that changes with the card the job landed on. Amended from 0.005 on 2026-09-20; see "Changing these criteria" |
| `--roles-attention-floor` | 0.20 | a Segment must carry a fifth of the head's mass at the query position before the pass calls it what the head reads |

The defaults are flags so a different task or circuit can be read at a
different scale, and the values actually used are written into `roles.json`
beside every decision.

**The position-threshold question is recorded here, not decided.** Ticket 09's
`--path-position-threshold` defaults to 0.05, which selects exactly one cell on
this circuit, and its verification ran at 0.0035, which selects cells that
change between cards. That default is the researcher's call and these criteria
do not make it; the roles path floor above is a separate number answering a
separate question, and it is set where it is for the cross-card reason given.

Three flags of the subcommand are not criteria. `--dry-run` proposes and prints
without writing, so the pass can be rehearsed on the login node like every
other part of the CLI. `--roles-merge-from CELL_DIR` (repeatable) copies
another cell's analysis columns onto the matching rows before the criteria
run, because the block C and D analyses of record were run one suite per
analysis and the conjunction needs all three views in one table (since ticket
13 every job runs into one cell and carries the others' columns forward, so a
new cell needs no merge); it reads a merged cell under the current column
names before comparing, brings its coverage with it, never copies a key column,
an intake column or `role_confirmed`, and it refuses to overwrite a column that
already holds a different value. `--roles-allow-missing-views` proposes anyway
when a whole view's columns are absent from the table, which is otherwise
refused: a table with no DLA columns proposes `unknown` for every Component,
and that reads like a finding. The views that were missing are recorded in
`roles.json`.

## Segment groups: what counts as a read

The reads view is the **top Segment** at the query position and its mass. The
Segment names come from the task's segmentation (`segmentation.json`); the
groups are fixed here, from `CONTEXT.md`'s prompt anatomy, and a Segment name
the table does not list is `unestablished` — including a `--segment` override
such as ticket 03's `bos`, which has not been shown to be anything.

| group | Segments |
|---|---|
| `designation` | `designating_sentence`, `designation_site`, `predicate_token`, `other_token`, `inverse_predicate_token`, `designation_suffix` |
| `item_mention` | `item_1_intro`, `item_2_intro`, `item_1_question_pair`, `item_1_question_option`, `item_2_question_pair`, `item_2_question_option` |
| `pressure` | `pressure_clause` |
| `frame` | `intro`, `question`, `stem` |
| `unestablished` | `readout`, `unsegmented`, and any Segment not named above |

**These are the mechanism tasks' Segments (FAR, SDR, SER).** STD has its own
segmentation — `stipulation_token` and `statement` in place of the Designating
Sentence's anatomy — and neither is in the table, so on an STD cell every head
would read as unestablished. That is presently harmless, because STD is out of
the causal analyses by the researcher's 2026-09-16 decision and its depends
views would be null anyway, but a full table of `unknown` reads like a finding.
Give STD its groups before running the pass on an STD cell.

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

**Say the carve-out out loud, because it is the one place the conjunction is
weaker than the glossary's sentence.** Every other role needs all three of the
glossary's views. A suppressor can be assigned on `dla.suppression` alone plus
a negative knockout — that is one glossary view (DLA) and knockout, which is
not one of the three. It is written this way on purpose: a suppressor is
defined by what it produces, its reads view is as likely to be the attention
sink as anything else, and a circuit discovered against a deceptive Corruption
has no reason to make its suppressors legible. **It is also a researcher
decision to bless or tighten**, and it is in ticket 10's open questions. No
suppressor has been assigned on any circuit so far, so no output of record
depends on it.

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
  `dla.differential_paired` significant and above the DLA floor — the
  contribution is pressure-dependent;
- depends (whether): `knockout.logit_diff_drop` or `roles.direct_support`
  significantly positive and above its floor;
- depends (query side):
  `path_patching.strongest_incoming_honest_instruction_paired` names a `q.`
  receiver **on this Component**, with `|effect|` at or above the path floor. This clause is what separates selector from mover, and it is the
  one the researcher should argue with first.

**5. mover.** All of:
- reads: top Segment in `item_mention` with mass at or above the attention
  floor; not applicable, and so satisfied, for an MLP block;
- writes: `dla.pressure` significantly positive and above the DLA floor;
- depends: `roles.direct_support` significantly positive and above the path
  floor, **and** `path_patching.strongest_outgoing` names the Readout — its
  effect reaches the Readout directly;
- and not a selector by rule 4.

**6. unknown/knockout-only.** No role above holds, and all of:
- depends (whether): `knockout.logit_diff_drop` significant and above the
  knockout floor, **in either direction** — the notes say which ("knockout
  supports deception" or "opposes deception");
- reads: **not established** — the top Segment is unestablished, below the
  attention floor or unmeasured; an MLP block, whose reads view is not
  applicable, has no reads evidence to wait for and qualifies;
- writes: `dla.pressure` and `dla.differential_paired` not significant or below
  the DLA floor, and `dla.suppression` false;
- depends (how): `roles.direct_support` not significant or below the path
  floor, `|path_patching.strongest_outgoing_effect|` below the path floor, and
  no honest-instruction path at the Component's own query at or above it.

The DLA and path-patching columns must have been **measured** for this
Component: a table missing either view (allowed with
`--roles-allow-missing-views`) leaves it unmeasured rather than silent, and
the Component stays `unknown/insufficient`. An unmeasured read is no reads
evidence, which is the flavour's premise, so it does not block.

An established read is reads evidence, so a Component that reads an Item
Mention and matters on knockout alone is `unknown/insufficient`, not
`knockout-only`; that is the line between "we cannot see what it reads" and
"we can see what it reads but not what it does with it". Incoming paths other
than the query-side one do not count against the flavour: they say what feeds
the Component, not what it does.

**7. unknown/insufficient.** Everything else. The notes say which views were
established, which were silent, and which role the established ones lean
towards, so that a researcher reading the table sees the evidence rather than
the word "unknown".

A Component that satisfies no role but whose views are all established and
agree is still `unknown/insufficient`; the notes say so, and that is a signal
that the vocabulary is missing a role rather than that the Component is dull.

## A Component the completeness sweep flagged, but the circuit does not contain

Ticket 09's completeness sweep appends rows for Components outside the circuit
— on SDR nls0.3, seven of them cleared its 0.05 direct-effect threshold, one
(`mlp.30.0`, +0.1275) larger in magnitude than the circuit's own layer-31 MLP,
and non-circuit direct paths carried about three quarters of the gap on that
draw. Those rows carry `path_patching.sweep_*` columns and **nothing else**: no
attention, no DLA, no knockout, because no analysis ran over them.

The criteria treat them as the conjunction requires and no better: every view
is silent, so the role is `unknown/insufficient` and the note says "no analysis
scored this Component". **A sweep flag is not a view and never becomes one**,
because a large direct effect says what a Component writes into the Readout,
not where it reads or what it depends on, and a role assigned from it would be
a role assigned from one view.

Two consequences, both deliberate. Merging a sweep cell into a roles table adds
those rows as `unknown`, inflating the `unknown` count with Components that
were never candidates; and the family knockout **drops** them rather than
ablating them, because a family knockout is a statement about the circuit under
study, with the dropped count recorded in `knockout_families.json`'s `grouping`
block. If the researcher wants those Components analysed, the answer is to put
them in a circuit and run the analyses over them, not to give the sweep a role.

## What the pass writes

Into the head table, namespaced `roles.`, next to the columns it read:

    roles.role_proposed     one of binder, selector, mover, suppressor, unknown
    roles.role_notes        one line: the flavour, the lean and the numbers
    roles.direct_support    the derived column of ADR-0002
    roles.direct_support_se
    roles.direct_support_honest_instruction_paired
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
records the three views' inputs, each criterion's pass or fail, the role, its
flavour and the notes, so that a disputed label is settled by reading the file
rather than by rerunning the pass. It also counts the flavours of `unknown`
(`flavour_counts`) and names any legacy column it read under a current name
(`renamed_columns`).

**The mechanical pass runs first and its output is kept.** An agent may rewrite
`roles.role_notes` in the head table to say something a one-line template
cannot, and a researcher may write `role_confirmed`. Neither touches
`roles.json`, which holds the mechanical note and the mechanical role as the
pass produced them; a rerun of the pass rewrites the table's notes from the
criteria again, so a hand-written note belongs in the ticket or in
`role_confirmed`, not only in a cell that the next run regenerates.

## Knockout by role family

**A cell is assembled by running jobs into it** (ticket 13). A run of
`analyze_components.py` into a cell that already has a head table rewrites the
namespaces of the analyses it runs and carries every other column forward —
the other analyses' columns, `role_confirmed` and the `roles.*` columns alike —
and a `--dry-run` rewrites nothing. So the family knockout can run into the
very cell the roles pass wrote, and reads its roles from that cell by default.
`--knockout-roles-from` still reads them from another cell. Rerun the roles
pass on a cell whose analyses were rerun: the carried `roles.*` columns were
proposed from the old numbers.

The family pass adds two columns of its own, `knockout.role_family` and
`knockout.role_family_logit_diff_drop`, beside the `roles.*` columns it
grouped by, so the grouping a figure was built from is still in the table
beside it.

Once roles exist, `--knockout-families` groups the Components by
`role_confirmed` where the researcher has set it and by `roles.role_proposed`
everywhere else, and interchange-ablates each group **together**, through the
same code path as the single-Component knockout. It answers the question a
per-Component ranking cannot: whether a family of small effects is a large one
together. Its sign convention is the single knockout's, unchanged — positive
means the family helps deception.

## Changing these criteria

**2026-09-20 — `--roles-path-floor` raised from 0.005 to 0.01.** Reason:
ticket 09's Slurm read-back measured the **cross-card noise floor on a
path-patching cell at about 0.005** (the same cell computed on an A40 and on an
A100). The original floor sat exactly on that number, so any criterion it
admitted at the margin was one that could change with the card the job landed
on. The new floor is twice it.

This is a change made from a fact about the measurement, not from the result,
and the result it changes is stated here rather than buried: **at 0.005 the SDR
nls0.3 delta had one selector (L17H25) and one mover (the layer-31 MLP); at
0.01 it has the mover alone and seventeen unknowns.** L17H25's selector label
rested on its honest-instruction query cell at **0.0068** — above the old
floor, below the new one, and inside the cross-card noise. Both passes are
reported in ticket 10; the 0.01 pass is the one of record.

**Nothing else about the criteria changed.** This one threshold did move after
a pass had run, which is exactly why it is logged here with its cause rather
than quietly re-defaulted: the cause is ticket 09's cross-card measurement,
which arrived after the first pass and would have set the floor here had it
arrived before. The test of whether that is a fit rather than a fact is whether
the reason survives without the result, and it does: a criterion inside the
noise of its own measurement is not a criterion, whichever way this circuit had
come out.

**2026-10-13 — `unknown/knockout-only` added as a flavour of `unknown`.**
Reason: the researcher's decision on the SDR first run. Five Components of the
SDR nls0.3 head-granularity delta (ticket 10 named L5H8, L5H9, L5H11, L8H14 and
L9H12; the write-up's section 5 named the binding band's L8H12, L8H14, L8H15
and L9H12) have a knockout effect several standard errors from zero, no DLA,
no direct effect and no onward path above the floor. Ticket 10 asked whether
the vocabulary was missing a fifth role for them. **The answer is no fifth
role**: they get the `unknown` flavour `unknown/knockout-only` until there is
reads evidence, because without a read there is nothing to say what they do
beyond that they matter. The criterion is rule 6 above. It changes **no role**,
only the flavour of some `unknown`s, so no count of binder, selector, mover,
suppressor or unknown can move.

Its result, on a copy of the cell of record `sdr-first-run` (ticket 13's
comments carry the full table): **0 binder, 0 selector, 1 mover, 0 suppressor,
17 unknown, as before**, of which six are now `unknown/knockout-only` — L5H8,
L5H9, L8H12, L8H14, L8H15 and L9H12 — and eleven stay `unknown/insufficient`.
**L5H11 is not knockout-only**, although ticket 10 listed it: its top Segment
at the Readout is `item_1_question_option` at 0.35, an established read, so it
has reads evidence and the flavour's premise does not hold. L14H7 and L14H22
are excluded the same way (an established `question` read). Rule 2 below asks
for every cell with a role column to be rerun; the cells of record are the
researcher's, and the rerun on them is theirs to make.

The rest of this section is the rule for any future change. A threshold or a
clause may be changed, and then:

1. say so here, with the date and the reason;
2. rerun the mechanical pass over every cell that has a role column, because a
   role proposed under old criteria and one proposed under new criteria must
   not sit in the same table;
3. leave `role_confirmed` alone — it is the researcher's, and a criteria change
   is a reason to ask them, not to overwrite them.
