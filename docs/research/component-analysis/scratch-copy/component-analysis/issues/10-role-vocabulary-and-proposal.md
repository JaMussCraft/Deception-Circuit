# 10 — Role vocabulary, proposal step, and family knockout

**What to build:** A docs file defines the Component Role vocabulary (binder, selector, mover, suppressor, unknown; pressure reader reserved) and the criteria for each in terms of head-table columns. An agent step reads a finished head table, writes a proposed role and a one-line justification per Component, and the researcher's confirmed role lives in its own column. Knockout by role family reruns the interchange knockout grouped by confirmed (or, absent that, proposed) role.

**Blocked by:** 06 — Paired honest-instruction columns; 07 — Per-Component knockout; 09 — Path patching extensions.

**Status:** resolved

- [x] Criteria doc written before any role is assigned; each role names the attention, DLA and path-patching conditions it requires, following the conjunction rule in the glossary.
- [x] A CLI subcommand applies the criteria mechanically to write `role_proposed` and `role_notes`; an agent may refine the notes but the mechanical pass runs first and its output is kept.
- [x] `role_confirmed` is read from the head table if present and never overwritten by the tool.
- [x] Family knockout: interchange knockout of all Components sharing a role, written beside the single-Component results with a PNG.
- [x] Test: criteria applied to a hand-built head table yield the expected roles, including `unknown` when views disagree.
- [x] Verified on the SDR head table from the preceding tickets; family knockout run within the short-job budget.
- [x] Subagent code review against the spec completed and findings addressed. Both axes ran as independent sub-agents and both reports arrived; every finding's disposition is in `reports/10-role-vocabulary-and-proposal-review.md` and summarized under Comments.

## Comments

### What was built

Eleven commits, **rebased by the orchestrator onto `7e31237` (ticket 11's tip)
while this ticket was finishing and merged into `component-analysis`**, so the
hashes below are the merged ones and the originals no longer resolve. They sit
on top of `d4c3186`, the orchestrator's own commit teaching ticket 11's
notebook to read the role family under either column name.

    e58f643  Refuse a --dla-conditions typo before the model loads, not after
    e0d3b75  Pre-register the Component Role criteria before assigning any role
    be769eb  Propose a Component Role mechanically, from the finished head table
    c9b9b11  Ask whether a family of small effects is a large one together
    03c979c  Refuse a merge that would overwrite a measured column, and say what a rerun costs
    b57681e  Pin the roles columns the module declares, and drop an unused import
    82d1944  Say which of the notes survives an agent rewriting them
    46cda9b  Refuse a role that names a Component outside this circuit
    23a4963  Take both independent reviews, and raise the path floor off the noise
    d323ae2  Say what the selector clause does not test, and stop overclaiming the pre-registration
    5bafa53  Keep the researcher's confirmed role across a rerun of the analyses

**`docs/component-roles.md`** is the pre-registered criteria doc, and
**`docs/adr/0002-one-sign-convention-for-reading-across-component-analyses.md`**
is the sign convention it reads by. `CONTEXT.md`'s Component Role entry gains a
two-line pointer to both. **`component_analysis/roles.py`** applies the
criteria; **`component_analysis/knockout.py`** gains the family pass;
`analyze_components.py` gains a four-line subcommand dispatch.

### The one sign convention, and how it is applied

**Positive supports the deceptive answer.** `knockout.logit_diff_drop` and
every `dla.*` column already read that way and are read natively, with the sign
stated where each is read. `path_patching` is the opposite, so the criteria
read a **new derived column**, `roles.direct_support = -path_patching.direct_effect`
(and its `_honest_instruction` twin), exactly as the 2026-09-20 decision
requires: **no existing column, JSON key or figure was renamed, re-signed or
rewritten.** `path_patching.strongest_outgoing_effect` and its incoming twin
are read as magnitudes plus a receiver name, because "which Component feeds
which" is a question about the size of a path, not its direction.

ADR-0002 also records the thing that is easy to get wrong: under the
Honest-Instruction Counterfactual the counterfactual is the *honest* prompt, so
a negative cell there means the path carries the honest instruction, not the
Corruption.

### Why a subcommand and not `--analyses roles`

A registered analysis runs inside one CLI invocation, over `base_rows` freshly
built from the intake, with a model loaded; the head table is written once at
the end. The roles pass needs the opposite of all three: the **finished** table
off disk (including columns written by earlier runs, in other suites), no
model, no circuit binding and no task. Putting it in `ANALYSES` would have
meant either loading an 8B model to read a CSV or teaching the run loop to read
its own previous output. So it is `python analyze_components.py roles <cell>`,
dispatched in four additive lines at the top of `main()`, and
`registry.ANALYSES` is untouched — which also keeps the five-name rule intact.

`--roles-merge-from CELL_DIR` (repeatable) merges another cell's analysis
columns first, because the analyses of record are one suite per analysis and
the conjunction needs all three views in one table. It refuses to overwrite a
column that already holds a different value.

### The criteria amendment that changed the answer, and why it is not a fit

**Read this before the table.** The criteria were pre-registered with a
path-patching floor of 0.005. After both reviews, the orchestrator relayed
ticket 09's Slurm read-back: the **cross-card noise floor on a path-patching
cell is about 0.005** (the same cell on an A40 and on an A100). The floor sat
exactly on the noise, so a criterion it admitted at the margin was one that
could turn on which card the job landed on. The floor is now **0.01**, twice
the measured noise, logged in `docs/component-roles.md` under "Changing these
criteria" with its reason and both outcomes.

It costs the circuit its only selector. **L17H25's selector label rested on its
honest-instruction query cell at 0.0068** — above the old floor, below the new
one, and inside the cross-card noise. That is the amendment doing its job
rather than a threshold tuned to a result: the change came from a fact about
the measurement, was made before the pass was rerun, and the pass was rerun
whole. A test pins the real case so it cannot be quietly undone.

| pass | binder | selector | mover | suppressor | unknown |
|---|---|---|---|---|---|
| path floor 0.005, first run | 0 | 1 (L17H25) | 1 (L31 MLP) | 0 | 16 |
| **path floor 0.01, of record** | 0 | **0** | 1 (L31 MLP) | 0 | **17** |

### The proposed roles for all 18 Components

Merged from the outputs of record (`ca06-paired2` for attention and DLA,
`ca07-knockout`, `ca09-path-patching`), run on the login node in about a
second. Thresholds: z 2.0, DLA floor 0.01, knockout floor 0.01, path floor
0.01, attention floor 0.20.

| Component | role | reads group | dla.pressure | knockout drop | direct support |
|---|---|---|---|---|---|
| L5H5 | unknown/insufficient | frame | −0.0007 | +0.0330 | −0.0001 |
| L5H6 | unknown/insufficient | frame | −0.0004 | +0.0277 | −0.0001 |
| L5H8 | unknown/insufficient | unestablished | −0.0000 | +0.0572 | −0.0001 |
| L5H9 | unknown/insufficient | unestablished | −0.0005 | +0.0415 | −0.0001 |
| L5H11 | unknown/insufficient | item_mention | −0.0003 | +0.1503 | −0.0001 |
| L8H12 | unknown/insufficient | unestablished | −0.0001 | +0.0332 | −0.0001 |
| L8H14 | unknown/insufficient | unestablished | −0.0001 | +0.0679 | +0.0001 |
| L8H15 | unknown/insufficient | unestablished | −0.0001 | +0.0320 | +0.0000 |
| L9H12 | unknown/insufficient | unestablished | +0.0006 | +0.0682 | −0.0004 |
| L13H17 | unknown/insufficient | frame | +0.0003 | −0.0053 | −0.0007 |
| L14H7 | unknown/insufficient | frame | −0.0005 | **−0.0936** | −0.0004 |
| L14H21 | unknown/insufficient | unestablished | −0.0011 | +0.0203 | −0.0009 |
| L14H22 | unknown/insufficient | frame | −0.0011 | +0.1122 | −0.0005 |
| L17H25 | unknown/insufficient (**selector lean, query not met**) | frame | +0.0310 | +0.4465 | +0.0192 |
| L24H18 | unknown/insufficient (mover lean) | unestablished | +0.0444 | +0.0230 | +0.0159 |
| L24H25 | unknown/insufficient (mover lean) | unestablished | +0.0405 | +0.0021 | +0.0193 |
| L27H4 | unknown/insufficient | unestablished | −0.0045 | −0.0008 | −0.0005 |
| **L31 MLP** | **mover** | not applicable | +0.1795 | +0.3065 | +0.0951 |

**binder 0, selector 0, mover 1, suppressor 0, unknown 17.** Every decision,
every view's input and every criterion's verdict is in
`outputs/_analyses/ca10-roles/delta__head/sdr/roles/roles.json`, and the
one-line `roles.role_notes` carries the lean and the numbers for each row.

**Seventeen unknowns is the honest answer, not a bug, and it is worth reading
before deciding what to do about it.**

1. **The attention view is the binding constraint for most of the circuit.**
   The reads view is established on only 6 of 17 heads at the Readout query
   position, and on five of those it is `question`, the frame rather than an
   Item Mention. Nine heads top out on `unsegmented`, which ticket 03 showed is
   the `<|begin_of_text|>` attention sink. A sink head is not idle, but the
   Readout query says nothing about what it reads, and the criteria refuse to
   promote "we could not see" into a role. **L24H18 and L24H25 are movers on
   every other view** and are held at unknown by this alone.
2. **L17H25 is held at unknown by one cell inside the cross-card noise**, and
   it is the Component the researcher should look at first. Three of the four
   views agree loudly: it reads (the question frame, 0.27), it writes (+0.031,
   z = 22), it is by far the most causal single Component (+0.4465, 14% of the
   clean-corrupt gap), and its direct path to the Readout is significant. Only
   the selector's query clause fails, and it fails by 0.0032 of a normalized
   patching cell. Either a rerun of the honest-instruction pass with more
   instances settles it, or the researcher confirms `selector` by hand in
   `role_confirmed`, which the tool reads and never overwrites.
3. **L14H7 leans suppressor and is held at unknown by the conjunction.** Its
   knockout raises the deceptive margin by 0.094 (z = 3.3), but its DLA and its
   direct effect are both inside their own error, so exactly one view speaks.
4. **The layer-31 MLP is the only assigned role**, and it is the only Component
   with no reads view to fail, which is worth saying out loud: an MLP block
   gets to a role on two views because it has only two, by definition.

### Family knockout: Slurm job 22238754

`gpuA40x4`, **2:17** elapsed, `COMPLETED`, `--time=00:20:00` on the command
line, rehearsed with `--dry-run` on the login node first. Submitted from the
worktree root:

    sbatch --time=00:20:00 --partition=gpuA40x4 scripts/analyze_components.sbatch \
      --circuit sdr=<nls0.3 run> --circuit honest_c=<honest twin run> \
      --reference honest=<honest twin run> --expr "delta=sdr \ honest_c" \
      --compose-granularity head --task-from <nls0.3 run> \
      --analyses knockout --knockout-families \
      --knockout-roles-from outputs/_analyses/ca10-roles/delta__head/sdr \
      --suite-name ca10-family2 --output-dir outputs/_analyses/ca10-family2

(Job **22237473**, 2:18, ran the same command against the roles of the 0.005
pass and is superseded. Its numbers are in the family table below for the
comparison; every single-Component number is identical between the two jobs.)

**Why a second job at all, when the ticket 09 relay said not to rerun
anything.** That instruction was about ticket 09's own passes, and none were
rerun. This is ticket 10's family knockout, whose grouping is the roles column:
the amendment changed the families from three to two, so job 22237473's
families no longer matched any roles table on disk. Rerunning was the only way
the figure and the head table could describe the same grouping. **22238754 is
the job of record**; 22237473 is kept only for the comparison.

The clean run over the same 100 instances reproduces ticket 07 exactly:
**+1.6132**, standard error 0.0886, accuracy **1.00**.

| rank | family | Components | mean drop | SE | accuracy | sum of its singles |
|---|---|---|---|---|---|---|
| 1 | unknown | 17 | **+0.9500** | 0.1290 | **0.63** | +1.0153 |
| 2 | mover | 1 | +0.3065 | 0.0649 | 0.98 | +0.3065 |

**Four things in that table.**

1. **It answers ticket 07's point 4.** Accuracy discriminated nothing at the
   single-Component level (every knockout between 0.98 and 1.00). Knocking out
   the seventeen unknowns together drops the deception rate to **0.63**, so 37
   of 100 instances flip to the honest answer. The family pass is what makes
   the accuracy column mean something, exactly as ticket 07 predicted.
2. **Read the `unknown` family as a necessity check, not as a role effect.**
   The independent spec reviewer's point, and it is right: a family that is
   seventeen of eighteen Components answers "is this circuit necessary" rather
   than "is this role a large effect". The number belongs beside the
   circuit-level knockouts, not beside the mover's +0.31. The figure labels
   every family with its size for the same reason.
3. **The joint effect is slightly sub-additive** (+0.9500 against +1.0153
   summed), where the sixteen-member family of the earlier pass was slightly
   super-additive. Neither gap is large: at this circuit's size the Components
   are close to independent, and the sign of the gap is not stable to which
   Components are in the group.
4. **The single-member family is bit-identical to its single knockout**
   (`==`, not `approx`: +0.3064858818054199), and all **18 single-Component
   drops in this job are bit-identical to ticket 07's job 22110635** (max
   absolute difference 0.0). That is the evidence that the family pass is
   ticket 07's code path and that the loop refactor changed no number.

**The roles the run grouped by are still in the table it wrote**, and so is
anything the researcher confirmed. Every analysis run rebuilds the head table
from the intake's rows, so the CLI now copies an existing cell's
`role_confirmed` and `roles.*` columns onto those rows before the analyses run
and before the table is written; `ca10-family2`'s head table holds them beside
`knockout.role_family` and `knockout.role_family_logit_diff_drop`. That was the
independent Standards review's highest-severity finding, widened by the
orchestrator to cover `role_confirmed`, which made it a defect against
checkbox 3 rather than a nuisance. Two CLI-seam tests assert it, one of them a
dry run, and a mutation check confirms they bite.

### How the family knockout reuses ticket 07's path

`knockout_effects` now calls a new `knock_out_groups(model, batches, groups)`
with one group per Component, and `family_effects` calls the same function with
one group per role. One loop, one `capture_forward` per group with the corrupt
stream's values written over **every** member at once, so a family number is a
joint ablation rather than a sum. Per batch the family pass costs
`len(families) + 2` forwards. `Effects`, `summarize`, `columns` and `payload`
are untouched for the single case, so ticket 03's `knockout.rank` still reads.

The seam test that proves the claim is arithmetic, not reading: a family of one
reproduces that Component's single knockout exactly, and a family of three is
asserted against `replace_forward` with all three replaced — a route through
the model's own head inside the trace, independent of the analysis's fp32
readout. An earlier, weaker version of that test let a mutation (ablate only
the first member) pass; the mutation is caught now.

### The carried `--dla-conditions` fix

`925518f`, its own commit, first. `--dla-conditions` is now refused by
`argparse` at parse time through a `type=parse_conditions` hook and an
`UnknownCondition(ValueError, argparse.ArgumentTypeError)`, the same shape
`--attention-conditions` has had since ticket 06. Two lines of real change in
`dla.py` plus the class, and the one assertion in `tests/test_dla_model.py`
moves from `ValueError` inside `run()` to `SystemExit` at parse time. Ticket
06's open question 4 is closed.

### Files touched, for the rebase

- **New, nobody else's:** `component_analysis/roles.py`, `docs/component-roles.md`,
  `docs/adr/0002-one-sign-convention-for-reading-across-component-analyses.md`,
  `tests/test_roles.py` (57 tests), `tests/test_knockout_families.py` (11),
  `tests/test_knockout_families_model.py` (14, nnsight 0.7.0 only), plus two
  added to `tests/test_dla.py`.
- **Shared, and minimal:**
  - `analyze_components.py` — two additive pieces. The `SUBCOMMANDS` dict and
    the dispatch at the top of `main()` (plus one clause in the parser
    description and a paragraph in the module docstring, so `--help` finds the
    subcommand); and **`carry_roles`**, which puts an existing cell's
    `role_confirmed` and `roles.*` columns back onto the fresh intake rows,
    called once in `dry_run()` and once in `run()`. The second is the
    orchestrator's ruling on the head-table rewrite: a rerun into a cell was
    dropping the researcher's confirmed role, which is a defect against
    checkbox 3. `registry.py` and the five-name analysis protocol are
    untouched; the earlier `extra_columns` seam this superseded is removed.
  - `CONTEXT.md` — three lines added to the Component Role entry, pointing at
    the criteria doc and ADR-0002.
  - `tests/test_component_analysis.py` — one module name added to the shared
    fresh-interpreter nnsight probe, as tickets 03, 04, 07 and 08 each did.
- **Another ticket's modules, changed deliberately:**
  - `component_analysis/knockout.py` (ticket 07) — the loop takes groups, plus
    the family functions and flags. The single-Component path is unchanged and
    its numbers are bit-identical.
  - `component_analysis/dla.py` and `tests/test_dla_model.py` (ticket 04) — the
    carried parse-time fix, in its own commit so it can be rebased or dropped
    separately.
- `hooks.py`, `dataloaders.py`, `registry.py`, `segmentation.py`,
  `sampling.py`, `head_table.py`, `attention_patterns.py`,
  `path_patching.py` and `scripts/analyze_components.sbatch` are **untouched**.

### Tests

Both suites were run on the branch tip as it stood before the orchestrator's
rebase (`c95a193`, now `5bafa53`). After the rebase onto `7e31237` the five
affected test files were rerun in both environments — 100 passed in `mgnp`,
87 passed and 1 skipped in the base env — but **the two full suites were not
rerun on the rebased tip**, because the worktree was removed before that could
happen. The rebase replays the same changes onto ticket 11's tip and ticket 11
touched none of this ticket's files, so no result is expected to differ; it is
recorded as not verified rather than as verified.

| env | this branch | new failures |
|---|---|---|
| `mgnp` (py3.12, nnsight 0.7.0) | 8 failed, 995 passed, 19 skipped | none, the same 8 names |
| login-node base (py3.9, nnsight 0.5.12) | 8 failed, 869 passed, 44 skipped | none, the same 8 names |

**One earlier `mgnp` run reported a transient error, and it is worth recording.**
`tests/test_path_patching_passes.py::test_a_strong_component_outside_the_circuit_gets_a_row_of_its_own`
errored in fixture setup because `dataset/deception_common.load_entities()`
read an empty string from a tracked, read-only JSON data file this branch does
not touch. The module passed on rerun (26 passed) and the final run above is
clean. It is the hang-and-empty-read behaviour the brief warns about, not a
failure of this branch.

The two environments' failure lists are **identical by name**, and all eight
are in `tests/test_benchmarks.py`, `tests/test_deception_common.py` and
`tests/test_deception_tasks.py` — files this branch does not touch, and the
list the orchestrator recorded for `19f1fb1`. **Stated plainly: the baseline
was not re-derived by checking out `19f1fb1` and running both suites there.**
The comparison is against the orchestrator's 8-name list for this exact base
commit, and every failure name on the branch is in it. 85 tests are added;
`tests/test_knockout_families_model.py` is the extra module-level skip in the
base environment.

**No rerun of the roles pass or the family job was needed after the last two
commits**, and the reason is worth stating rather than assuming: neither commit
touches a criterion. `c95a193` changes when columns are copied between tables,
not how any number is computed or thresholded, and `8dd94b9` changes prose and
one docstring. The roles of record and job 22238754's numbers stand. The last
change that *did* move a number was the path-floor amendment in `27b3b4e`, and
both the roles pass and the family job were rerun whole after it.

Mutation checks: flipping the sign of the derived `direct_support` column,
removing the floor from the significance test, removing the disagreement check
and forcing the selector's query clause true each fail between 2 and 12 tests;
ablating only the first member of a family fails the definitional family test;
skipping the out-of-circuit check fails its own test; and dropping the
role carry from either of its two call sites fails the rerun test. No `core.claude*` or other `core.*` dump
was produced or committed; `outputs/` and `logs/` stay ignored.

### Outputs of record

- `outputs/_analyses/ca10-roles/delta__head/sdr/` — the merged head table with
  the `roles.*` columns and `roles/roles.json`, at the amended path floor of
  0.01. Built by copying `ca07-knockout`'s cell and merging `ca06-paired2` and
  `ca09-path-patching` into it; **nothing was written into the
  `component-analysis` worktree.** The command that reproduces it:

      python analyze_components.py roles outputs/_analyses/ca10-roles/delta__head/sdr \
        --roles-merge-from outputs/_analyses/ca06-paired2/delta__head/sdr \
        --roles-merge-from outputs/_analyses/ca09-path-patching/delta__head/sdr
- `outputs/_analyses/ca10-family2/delta__head/sdr/knockout/` — job 22238754's
  `knockout_families.json`, `knockout_families.png` and the single-Component
  pair beside them, plus a head table carrying both the `knockout.role_family`
  columns and the `roles.*` columns the run grouped by.
- `outputs/_analyses/ca10-family/delta__head/sdr/` — job 22237473, the same
  command against the roles of the superseded 0.005 pass. Kept only for the
  comparison in the family table above; `ca10-family2` is the one of record.

Both live in the `ca-10` worktree and are not committed.

### The code review

**Both independent sub-agents delivered, and the review is independent of the
author.** They ended without delivering through `SubagentHandback` — the
failure mode the brief and tickets 02, 02b, 04, 06, 07 and 09 all record — and
both reports arrived afterwards by `SendMessage`, with the orchestrator's
rulings on each. Both reports are reproduced verbatim, with the disposition of
every finding, in
`reports/10-role-vocabulary-and-proposal-review.md`. The author's own pass,
written while waiting, is kept in the same file beneath them.

**Spec axis: ship with changes.** Six findings. All seven checkboxes met, no
scope creep, and the reviewer independently verified the thing this ticket most
needed checking: all 18 rows of the family job's single-Component table match
`ca07-knockout` exactly on drop, standard error, rank and accuracy, so the
knockout refactor is behaviour-preserving on the real model. Four findings
fixed (the zero standard error, the pressure-reader wording, the ADR's claim
about `direct_support_honest_instruction`, the weakened DLA test assertion);
two kept on the orchestrator's ruling and written into the doc (the namespaced
column names, and the suppressor carve-out, which is open question 2 below).

**Standards axis: one hard violation, seven caller-visible errors, ten
judgement calls.** Sixteen fixed, three kept with reasons recorded, one noted
in the doc. The three that mattered:

1. **The hard violation was in a doc, not the code.** ADR-0002 said nothing
   reads `roles.*`; the family knockout does. Corrected.
2. **`--knockout-families`' default roles source erased the columns it had just
   read.** Every run rebuilds the head table from the intake's rows, so a
   family run against its own cell read a role, ablated by it, and wrote a
   table with no role column left. Fixed better than the reviewer's two
   options: an optional `extra_columns(ctx)` in the run loop lets the analysis
   carry those columns back, so the in-place case now works instead of being
   forbidden.
3. **The family columns were `knockout.family`**, and CONTEXT.md already uses
   "family" for task families and STD scenario families. Renamed to
   `knockout.role_family` and `knockout.role_family_logit_diff_drop`. **The
   JSON keys are unchanged**, because ticket 11's notebook reads them.

Kept with reasons: the duplicated clean and corrupt forwards (two passes per
batch, about five seconds, against splitting ticket 07's `Effects` contract);
STD's Segments having no groups (noted in the doc instead, since STD is out of
the causal analyses); and the `--dla-conditions` fix being larger than the
brief's "two lines" estimate.

### Open questions for the researcher

1. **L17H25 is one cell away from `selector`, and that cell is inside the
   cross-card noise.** Three views agree loudly and only the selector's query
   clause fails, at 0.0068 against a floor of 0.01 set from ticket 09's
   measured 0.005 noise. The options are a longer honest-instruction pass so
   the cell has a standard error worth trusting, a different clause for the
   selector's query evidence, or confirming `selector` by hand in
   `role_confirmed`. Doing nothing is also defensible and leaves the SDR delta
   with one assigned role.
2. **The suppressor carve-out.** Both the independent spec review and I flag
   it: every other role is a conjunction of all three of the glossary's views,
   but a suppressor can be assigned on `dla.suppression` plus a negative
   knockout, which is one glossary view plus knockout. It is pre-registered and
   argued in the criteria doc (a suppressor is defined by what it produces, and
   its read is as likely to be the attention sink as anything else), and no
   suppressor has been assigned on any circuit, so nothing of record depends on
   it. Bless it or tighten it.
3. **Twelve of seventeen heads have no established read at the Readout query,
   and that is what holds most of the circuit at `unknown`.** The criteria will
   not lower the bar for it. The fix, if you want one, is to rerun the roles
   pass against an attention run at a different query position (ticket 03's
   `--query-positions`) — the designation Segments, or the Pressure Clause —
   and see whether the reads view establishes there. The pass costs a second on
   the login node, so this is cheap to try; it needs one more GPU attention run
   per query position.
4. **Is `question` a frame rather than an item-bearing read?** The criteria say
   yes, because the Item Mentions inside the user question are carved into
   their own Segments, so the mass left on `question` is on the question's
   other words. It is the call that keeps L17H25's read *established* at all;
   reverse it and L17H25 loses the selector lean as well as the label, and the
   five heads reading `question` join the nine reading the sink.
5. **A rerun into a cell still strips the analysis columns that were merged
   into it, though the role columns now survive.** The orchestrator's ruling is
   implemented and verified on the real cell: a `--dry-run` knockout into
   `ca10-roles` leaves `role_confirmed`, `roles.role_proposed` and
   `roles.reads_group` exactly as they were. **What it does not carry is any
   column that belongs to an analysis that did not run in that invocation** —
   which, for a cell assembled with `--roles-merge-from`, is every view the
   roles were derived from. I hit this by accident while verifying the fix: the
   dry run left the roles intact and took `knockout.logit_diff_drop` with it,
   and the next roles pass refused the table by name for having no knockout
   view. The refusal is the guard working, the cell was rebuilt in one command,
   and nothing of record was lost. It is worth deciding whether a merged cell
   should be rebuildable at all, or whether `--roles-merge-from` should write a
   provenance note the rerun can honour. Not urgent: the workaround is to give
   every analysis run its own `--suite-name`, which the criteria doc says.
6. **`--path-position-threshold`'s default is recorded here, not decided.**
   Ticket 09 asked for a weigh-in and the orchestrator ruled it is yours. The
   facts, for the record: 0.05 selects exactly one cell on this circuit,
   ticket 09's verification ran at 0.0035, and ticket 09 measured the
   cross-card noise on a cell at about 0.005, so a threshold below that
   selects cells that change between cards. The roles path floor of 0.01 is a
   separate number answering a separate question and does not constrain this
   one.
7. **The `_honest_instruction` columns cover 71 instances and their partners
   cover 100**, which ticket 09 flagged and the column names still do not say.
   The criteria threshold each column on its own and never subtract across that
   boundary, and the criteria doc says so, but a reader putting two columns
   side by side is still unwarned.
8. **The vocabulary may be missing a role.** Five Components (L5H8, L5H9,
   L5H11, L8H14, L9H12) have a knockout effect four to eight standard errors
   from zero, no DLA, no direct effect and a strongest outgoing path below the
   path floor. They matter causally and do nothing the four roles describe. If
   a later run establishes their reads, they are the population a fifth role
   would be for.
