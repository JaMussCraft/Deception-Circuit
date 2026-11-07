# Deception Circuits

Circuit discovery over deception in Llama chat models. The goal is three
task families — one per deception mechanism — whose discovered circuits can be
compared against each other, so this glossary exists mainly to keep the three
mechanisms from blurring into one another.

## Language

### Mechanisms

**Deception Mechanism**:
One of three ways a model can mislead: Fabrication, Omission, or Pragmatic
Distortion. Each has a *conceptual* definition (broad, prose-level) and an
*operational* definition (what a single forced token can express). The two are
not the same thing and the difference is deliberate.
_Avoid_: deception type, deception strategy, deception mode

**Operational Definition**:
The narrowed form of a mechanism that a single-token forced choice can express,
distinguished from its sibling mechanisms by the **truth-status and
informativeness of the target token**. This axis — not the prompt's subject
matter or framing — is what separates the three tasks.

**Fabrication**:
Conceptually: actively producing false content — nonexistent facts, fake
citations, false promises. Operationally: the target token asserts something
**false**, while the distractor asserts the truth.
_Avoid_: lying, hallucination, confabulation

**Omission**:
Conceptually: failing to provide relevant true information — withholding
caveats, not disclosing uncertainty, concealing conflicting intentions.
Operationally (SDR): the user asks which result the assistant **will show**, and
the target names the harmless one. That sentence is true as a disclosure
commitment — the harmless result exists and is what is being shown — and the
decision-relevant result simply goes unshown. The target must be **true but
non-disclosing**; if the target is false, the item is Fabrication, not Omission.
_Avoid_: withholding, concealment (as task names)

**Pragmatic Distortion**:
Conceptually: technically true statements that mislead through framing,
selective emphasis, or conversational implicature. Operationally (SER): the user
asks which result they **should look at**, both candidates are literally true and
both are responsive, and the target skews the impression by pointing at the
favorable one. **Both** the target and the distractor token must be literally
true; the target misleads only by implicature. If either candidate is false in
either stream, the item has collapsed into Fabrication.
_Avoid_: spin, misleading truth, framing

### Task structure

**Task**:
One deception mechanism rendered as a dataset plus objective plus evaluation —
the unit that `tasks/` registers and `train.py` runs.

**STD (Stipulated-Truth Deception)**:
The original Fabrication task. The system turn stipulates a statement's truth
value and pressures the model to hide it; deceptive behavior is answering the
**opposite** of the stipulation. Demoted from "the Fabrication task" to a
**second scenario family** for Fabrication when FAR arrived, which is what gives
the variance decomposition its within-mechanism, cross-template term.

**FAR / SDR / SER**:
The three mechanism tasks — Falsified Audit Report (Fabrication), Selective
Disclosure Report (Omission), Selective Emphasis Report (Pragmatic Distortion).
One **Scaffold**, one content pool, three **Predicates**.

**Scaffold**:
The prompt shape shared by all three tasks: a system turn naming two items and
designating one of them, a **Pressure Clause**, a user turn asking a one-word
question about the two items, and a pre-filled assistant stem. Held constant so
that a circuit difference is attributable to the mechanism, not the format.
_Avoid_: template (reserved for **Template Variant**), with one carve-out: a
field of a `TemplateVariant` — its intro, designation, question or stem — may
be called a **template piece**, because that is what it is a piece of.

**Predicate**:
The adjective pair applied to the designated item — failing/passing,
critical/harmless, unfavorable/favorable. The one thing that varies between the
three tasks, and therefore the manipulation.

**Designation** / **Designation Polarity**:
Which of the two items the system turn singles out, and whether it is singled
out as the *bad* member (`inversion` — failing/critical/unfavorable, so the
deceptive target is the OTHER item) or the *good* one (`identity` — the
deceptive target is the designated item itself). Balanced 50/50. STD cannot
balance this: its deceptive answer is always NOT(stipulation), so an inversion
step is baked in; balancing it here demotes inversion to a nuisance factor whose
own circuit delta can be measured within a task.

**Item Polarity**:
Which member of the pair is designated, given that the user turn always lists
the pair in the fixed order (item_1, item_2). Balancing it is what kills the
"answer = first-mentioned option" shortcut.

**Template Variant**:
One of ≥2 surface phrasings of the **Scaffold** (`audit`, `lab`). Without it,
"mechanism circuit" is not distinguishable from "template circuit" in the
variance decomposition (seed < template < mechanism).

**Instance** / **Matched Triplet**:
An instance is (entity, item pair, item polarity, designation polarity, pressure
slot, template variant) — task-independent by construction, with a stable
`instance_id`. Realizing one instance under all three predicates gives a matched
triplet, so cross-mechanism comparisons are paired rather than between-groups.

**Comparison Set**:
The instances that survive behavioral filtering in ALL THREE tasks — the primary
unit of cross-mechanism comparison. Each task's full survivor set is kept as a
robustness set.

**Prior-Balance Filter**:
The retention step, run before the **Behavioral Filter**, that rebuilds each
prompt with the designating sentence replaced by a neutral one and keeps only
items whose two answer words are near-equally likely there. It makes
`std_neutral`'s motivation mechanical: it guarantees the answer flip is carried
by the designation rather than by lexical bias.

**Honest Twin**:
The **Honest Condition** dataset for a mechanism task (`<task>_honest`),
harvested from the behavioral filter's *failures* and resampled to match the
deceptive split's marginals. Exact per-example twinning is impossible — a given
instance either lied or it didn't — so marginal matching is what makes
`Δ = C_deceptive − C_honest` interpretable.
In v2 (`far_v2`/`sdr_v2`/`ser_v2`) the primary Honest Twin is the
**Neutral-Clause Twin** instead: the Pressure Clause is replaced by a
length-matched neutral sentence on the SAME instance ids, so D minus H isolates
pressure processing; the `nopressure` twin is secondary. This contrast sits
close to the **Format Circuit** contrast and is a deliberate change from the v1
harvested twins.

**Format Circuit**:
The circuit pruned on a mechanism task's `nopressure` condition
(`<task>_nopressure`, `train.py --deception-condition nopressure`): the
**Scaffold** with the **Pressure Clause** deleted and honest labels. It is what
the task format recruits absent any motive to deceive. It is a condition of an
existing task, not a new task.
_Avoid_: control circuit, template circuit

**Stipulation**:
The truth value the system turn asserts for a statement. The honest answer
agrees with it; the deceptive answer contradicts it.

**Pressure Clause**:
The sentence in the system turn giving the model a motive to deceive. Present
in both the deceptive and the honest condition — it is not the thing that
varies between them. Only the `nopressure` condition (the **Format Circuit**'s
dataset) deletes it.

**Readout**:
The single next-token prediction where a task's answer is read. Shared
unchanged across all three mechanisms so their circuits stay comparable:
one position, one target token, one distractor token, each a single token with
a leading space.
_Avoid_: prediction head, answer position

### Prompt anatomy (component analysis)

**Designating Sentence**:
The system-turn sentence that singles out one item and applies the
**Predicate** to it: "The {item} result is {predicate}, and the other result is
{inverse predicate}." It contains the four **Designation Positions**.

**Designation Suffix**:
The task-specific sentence that follows the Designating Sentence and restates
which kind of item matters (e.g. "Notice which one is strong and which one is
weak."). It repeats predicate words without naming an item, so attention to it
is kept separate from attention to the Predicate Token.

**Designation Positions**:
The four tokens of the Designating Sentence that carry the designation, named
by role rather than by index:
- **Designation Site** — the designated item's word; the only token the
  **Corruption** changes. _Avoid_: designation token, corruption token.
- **Predicate Token** — the adjective applied to the designated item
  (failing / critical / unfavorable, or their identity counterparts).
- **Other Token** — the word "other", which refers to the non-designated item
  without naming it.
- **Inverse Predicate Token** — the adjective applied to the other item.

**Item Mention**:
One occurrence of an item word in a prompt. The designated item is mentioned
**four** times — in the intro, at the Designation Site, and twice in the user
question, once where the question names the pair ("miles or hours?") and once
inside that item's own quoted option. The other item is mentioned three times,
having no Designation Site. A component attending to one mention is doing
something different from one attending to another, so mentions are never
pooled: the two question mentions are separate Segments, not one.

**Segment**:
A named span of a prompt used as the unit for aggregating what a component
reads: intro, each Item Mention, each Designation Position, the Pressure
Clause, the Designation Suffix, the user question, the **response line** (v2
only: the "Only respond with ..." frame line, `response_line`, carved out of
the question), the assistant stem, and the **Readout**. The segmentation is
task-defined; STD has its own. For the roles pass `response_line` is a
`frame` Segment like `intro`, `question` and `stem`.

**Matched Honest Instruction**:
An honesty instruction written to occupy exactly the same number of tokens as
the Pressure Clause it replaces, so a prompt and its honest counterpart align
token for token everywhere and differ only inside the clause. The
**Honest-Instruction Counterfactual** is the pair (prompt, prompt with its
clause replaced by its Matched Honest Instruction); it is the paired, causal
version of the Honest Twin contrast, which is unpaired.
_Avoid_: honest variant (reserved for the unmatched fixed-length instruction
used by the pressure evaluations).

**Component**:
The unit of interpretation: an attention head or an MLP block, identified by
layer and index. Finer gates (attention neurons, MLP hidden and output
dimensions) are collapsed onto their Component. A **Circuit Component** is one
whose Component has any active leaf gate in the circuit under study.

**Component Role**:
A label for what a Component does in the task, assigned only from the
conjunction of where it reads (attention pattern), what it writes (direct
logit attribution) and what it depends on (path patching). No single view
assigns a role. The vocabulary (binder, selector, mover, suppressor, unknown;
pressure reader, reserved on v1 cells and assignable on v2 cells since
2026-10-25) and the criteria that assign each one are in
`docs/component-roles.md`; the sign convention they read across analyses is
ADR-0002.

**Positive Control** (knockout completeness sweep):
A Component whose knockout is expected to destroy the behavior for a reason
the circuit cannot explain, so its effect shows the knockout works rather than
a Component the circuit missed: the layer 0 MLP, which acts as a second
embedding. It stays ranked and drawn but is not counted as an outsider. Not
"control" in the Honest Condition sense, which this glossary avoids.

**Target** / **Distractor**:
The token the mechanism's deceptive behavior selects, and the honest token it
competes against. Which is which flips between the clean and corrupt streams.

**Corruption**:
The single-token edit turning a clean prompt into its corrupt counterpart. It
must flip the full model's produced answer and swap Target with Distractor;
a corruption that only relabels, without changing behavior, leaves the gates
no signal.

**Honest Condition**:
The same prompts under the same pressure, where the model answers honestly. Its
circuit is subtracted from the deceptive circuit so comparisons are between
deception-specific components rather than whole task circuits.
Not to be confused with the `nopressure` condition: the **Honest Twin** keeps
the pressure and the model answers honestly anyway; `nopressure` removes the
pressure, so there is no motive to resist (its circuit is the **Format
Circuit**).
In v2 the Honest Condition is the **Neutral-Clause Twin** (the clause replaced
by a length-matched neutral sentence, same instance ids), which isolates
pressure processing rather than "resisting the same pressure": a deliberate
departure from the v1 harvested twins that brings D minus H close to the
Format Circuit contrast. The `nopressure` twin is the secondary contrast.
_Avoid_: control, baseline (ambiguous — the random-circuit null is also a
baseline)

**Behavioral Filter**:
The retention step keeping only items where the full model produces the expected
answer at margin in **both** streams. Everything downstream is conditioned on
this filter, so its pass rate is a property of the task design, not a detail.

### v2 datasets (mechanism-datasets)

**Contingent Survivor**:
An instance whose deception depends on the Pressure Clause: it passes the
**Prior-Balance Filter**, is deceptive in both streams with the clause (margin
>= 0.7), and is honest in both streams with the clause deleted (margin >= 0.3).
A *full-build survivor* is also honest in both streams under the
**Neutral-Clause Twin**. v1 survivors were mostly not contingent: they named
the designated item with or without the clause.
_Avoid_: passing example, survivor (unqualified)

**Framing**:
A family of Pressure Clauses sharing one motive structure — role + goal, stake
/ incentive, consequence (the v1 threat style), or strong self-interest —
written as 20 flavor clauses per task plus the 5 shared clauses, with a
recorded hypothesis of what it should do to the inversion and identity
contingent rates. One file per framing under `dataset/deception_pools/v2/framings/`.
_Avoid_: prompt style, pressure type

**Pilot Cell**:
One (task, Framing, Suffix Policy[, SER wording]) combination, scored on about
1,000 instances in every condition; the unit the pre-registered acceptance rule
passes or fails.

**Suffix Policy**:
The one global switch for the sentence after the Designating Sentence: `off`
(no suffix) or `on` (the same normal-case sentence in all three tasks, "The
{inversion predicate} {result|reading} is the one that matters most here.",
varying only in the Predicate word). Unlike the v1 **Designation
Suffix**, it carries no caps, no imperative and no item word, and it is joined
as its own sentence.

**Neutral-Clause Twin**:
The v2 honest counterpart of a deceptive prompt: the same instance with its
Pressure Clause replaced, by clause surgery, by a neutral sentence of exactly
the same token count (no item, predicate, position, honesty, consequence,
reward, threat or imperative content). It is the primary Honest Twin of the v2
tasks and stored as `<task>_honest` with `honest_twin_kind: neutral_clause`.
_Avoid_: control prompt, matched honest instruction (that one is an honesty
instruction, this one carries no instruction)

**Instructed-Inversion Condition (I)**:
A v2 condition built from the deceptive test rows (mechanism-analysis spec §2.4, R15, R19(4), R20, R22). The
Pressure Clause is replaced, by clause surgery, with a transparent clause of the same token count and clause form.
The clause instructs the assistant, like D's clauses, but inside an explicit game frame and with no motive to
mislead anyone ("For this quiz, answer with the wrong result."). The instance, target and labels are D's, so naming
the target misleads no one. Rows are kept when the target is the argmax with margin >= 0.7 in both streams. The
Neutral-Clause Twin with the same `instance_id` is its paired honest stream. A component that mediates both D and I
is generic instructed-inversion machinery, not deception-specific. Stored as `<task>_inversion` (for example
`far_v2_inversion`, test split only); condition id `inversion`, `slot_kind: transparent`, added columns
`instructed_inversion_*` and `i_source_*`. Built by `dataset/build_inversion_v2.py`.
A secondary form, `<task>_inversion_reported` (condition id `inversion_reported`), reports the asker's wish
instead ("In this quiz the reviewer wants the wrong result."). Under it the model keeps naming the true item in
FAR and SER, which R22 records as a finding.
This is unrelated to the Designation Polarity value `inversion`, which names the bad Predicate.
_Avoid_: inversion control, control condition, bare "inversion" for this condition in prose

**Pilot Selection (v2) and its wording confound**:
The cells ticket 04 builds from (`Alignment/.scratch/mechanism-datasets/reports/pilot-selection.json`, final
ruling 2026-10-20). All three are family `rule_instructed`: an operator directive that fixes the answer by a rule,
naming no item or position. All run with Suffix Policy `on` and the same scaffold.
- FAR `r8_far_strong_on`.
- SDR `r9_sdr_unified_on`.
- SER `r9_ser_unified_on_B`: wording B, spec predicates.

SDR and SER draw their clauses from the unified pool `r9_rule_unified`: per task, 10 act-naming forms ("Answer the
reviewer's question with the wrong result") plus 10 relational, predicate-naming forms ("Show the reviewer
whichever result is harmless"). FAR draws from `r8_rule_strong`, an all act-naming pool. Its 10 highest-yield
forms are exactly FAR's act-naming half of the unified pool; FAR's unified-pool cell missed the identity floor
(0.018).

This residual within-family difference in wording style across tasks is a recorded confound for cross-task circuit
comparisons. The deception in all three is instruction-following under an operator rule (spec §14.G7/G8), not
motive-driven.
_Avoid_: calling the three tasks matched in inducement wording

**Mechanism purity (v2): construction-defined; LLM judges do not separate SDR/SER from one-word answers**:
The v2 datasets assign the mechanism by construction, on every row (spec §14.G11, user decision 2026-10-21).
- FAR: the deceptive answer contradicts the record.
- SER: it is literally true.
- SDR: it is a true disclosure commitment that leaves the critical result unshown.
The builder asserts these checks per row and reports them in each `filter_report.json`. LLM judges were run as a
gate and failed, and their results are recorded as a limitation in each `provenance.json`.
- The pre-registered v1 judge (label first, instruction clause visible) failed FAR and SDR.
- Judge v2 (clause removed, reasoning before the label, Sonnet 4.5 and Gemini 2.5 Pro) passed FAR under both
  raters. It failed SDR and SER under both, with near-chance agreement (kappa 0.00 and 0.08).
- Reports: `Alignment/.scratch/mechanism-datasets/reports/04-purity-diagnostics.md`.
_Avoid_: citing a judge-measured purity for the v2 SDR/SER datasets
