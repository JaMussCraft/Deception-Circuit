# Code review — ticket 10, role vocabulary, proposal step and family knockout

Fixed point: `19f1fb1` (the `component-analysis` tip). Branch
`ca/10-role-vocabulary-and-proposal`, worktree
`Deception-Circuit/.claude/worktrees/ca-10`.

## How the review was run, and how independent it is

Two independent sub-agents were spawned against the fixed point, one per axis
(Standards, Spec), with the ticket, the spec, the brief and the sibling
tickets' `## Comments` named for them, and with instructions to report findings
only and edit nothing. **Both ended without delivering a report through
`SubagentHandback`** — the failure mode the brief and tickets 02, 02b, 04, 06,
07 and 09 all record. Both were then asked by `SendMessage` to deliver their
findings, and were given more than the brief's ten minutes.

**Both reports then arrived**, forwarded through the orchestrator, and they are
appended verbatim in sections 3 and 4 below with the disposition of every
finding and the orchestrator's ruling where it gave one. **The review is
independent of the author.** The author's own pass, written while waiting, is
kept below it as sections 1 and 2: it found six things the independent pass did
not name, and the independent pass found thirteen the author's did not. Read
the independent ones first.

**Sections 1 and 2 are a snapshot.** They were written before the independent
reports arrived and before the criteria amendment in section 5, so where they
quote a role, a test count or a family number they quote the branch as it stood
then: one selector and one mover, sixteen unknowns. Sections 3 to 5 and the
ticket carry the current numbers.

## 1. Standards axis (author's own pass, written before the reports arrived)

Reviewed against `CONTEXT.md` (the glossary and its avoided terms), ADR-0001
(nnsight confined to `hooks.py`, fp32 readout, no second hook path), the
brief's "Design rules that apply to every ticket", and the conventions of
`knockout.py`, `dla.py` and `path_patching.py` as they stood at `19f1fb1`.

**No hard violation of a documented standard found.**

- **nnsight confinement holds.** `roles.py` imports no model machinery at all;
  the fresh-interpreter probe in `tests/test_roles.py` asserts it, and the
  module was added to the shared probe in `tests/test_component_analysis.py`.
  The family knockout reaches the model only through `hooks.capture_forward`
  and `hooks.readout_logits`, inside `knockout.py`'s existing loop; no new hook
  path exists and `hooks.py` is untouched.
- **fp32 readout holds.** The family pass reads its metric through the same
  `logit_difference` closure as the single pass, which is the fp32 readout over
  the captured residual.
- **Glossary vocabulary.** "Component", "Component Role", "Readout", "Segment",
  "Designation Positions", "Item Mention", "Matched Honest Instruction",
  "Honest Twin", "Corruption" are used as the glossary defines them. The
  reserved word "baseline" appears nowhere in the new code, JSON keys or docs.
  `clean_run` is reused rather than renamed.
- **PNG plus JSON twin.** The one new figure, `knockout_families.png`, has
  `knockout_families.json`, and the JSON carries every number the chart draws
  (role, n_components, members, mean drop, standard error, accuracy, rank).
- **Tests assert at caller-visible seams.** The criteria are asserted on
  returned `Decision`s and on written files; the family knockout is asserted on
  written JSON and on numbers, never on hook wiring.

Findings, by severity, all **fixed before this report** except where marked:

1. **A family knockout could reach past the circuit under study.**
   `families_for` read every role in the source cell, and the completeness
   sweep appends non-circuit Components to a head table, all of which the roles
   pass labels `unknown`. `--knockout-roles-from` pointed at a sweep cell would
   have ablated a family wider than the circuit, silently. Refused by name with
   the strays listed (`21b02cd`), with a test and a mutation check.
2. **`merge_cells` let the last cell on the command line win.** Two merged
   cells that both carried `path_patching.direct_effect` would have silently
   taken the later one, so a role's provenance would have been an argument
   order. Now refused by name (`a72205b`), with two tests.
3. **`Effects.keys` was typed and documented as Component keys** and now also
   holds role names. Docstring and annotation corrected (`a72205b`).
4. **`--dry-run` into the roles cell destroys the roles columns.**
   `dry_run()` writes the head table before printing estimates, so the natural
   rehearsal (`--dry-run --knockout-families --suite-name <the roles suite>`)
   overwrites the table it is about to read and then fails saying no Component
   carries a role. Documented in the criteria doc and in
   `--knockout-roles-from`'s help; **not fixed in code**, because a guard
   belongs in `write_cell`, a shared function, and that is an orchestrator
   decision (open question 3 in the ticket).
5. **The pre-registration claim was stated more strongly than it could be
   checked.** The author had read the block C and D outputs of record during
   orientation. The doc's Status line now says so, and says what is checkable:
   the criteria and every threshold were committed before the pass ran and
   nothing was changed after seeing the result.
6. **Unused import and a dead conditional** in `roles.py` and
   `tests/test_knockout_families_model.py`. Removed, and `roles.COLUMNS` is now
   asserted against the written table rather than merely declared.
7. **Judgement call, kept:** `roles.py` re-declares the column-name constants
   it reads (`DLA`, `KNOCKOUT`, ...) rather than importing them from the
   analyses. Importing would couple the roles pass to four modules that are
   rebased separately, which is `registry.py`'s own stated rationale. The cost
   is that a renamed column upstream fails here as a null rather than an
   ImportError; the mitigation is that a null now reads as "unestablished" in
   the notes rather than as a silent zero.
8. **Judgement call, kept:** the family figure uses one flat colour rather than
   the single-knockout chart's layer ramp, because a family has no layer.

## 2. Spec axis (author's own pass, written before the reports arrived)

Reviewed against the ticket's six checkboxes, spec user stories 16, 17, 30, 35,
36 and 43, the "Roles" and "Knockout" Implementation Decisions, and the
binding researcher decisions of 2026-09-16 and 2026-09-20.

**Verdict: ship.** Every checkbox is met; the deviations are declared below and
in the ticket.

- **"Criteria doc written before any role is assigned"** — `docs/component-roles.md`
  and ADR-0002 are commit `78425b2`; the pass that assigns roles is `4353de3`,
  and the first role on real data was assigned after both. Each role names the
  attention, DLA and path-patching conditions it requires, per the glossary's
  conjunction rule, with knockout folded into "depends" explicitly rather than
  made a fourth view.
- **"A CLI subcommand applies the criteria mechanically"** — `analyze_components.py roles <cell>`.
  Not a registry analysis, and the reason is in the code comment and the ticket:
  a registered analysis runs inside one invocation from the intake's fresh rows
  and never sees a previous run's columns, while the roles pass needs the
  finished table and no model.
- **"`role_confirmed` read and never overwritten"** — read into the decision
  and the JSON; `merge_columns` refuses the name outright, so the protection is
  mechanical. A test writes a confirmed role and asserts it survives while the
  proposal lands beside it.
- **"Family knockout ... beside the single-Component results with a PNG"** —
  `knockout/knockout_families.{json,png}` beside `knockout/knockout.{json,png}`,
  same sign convention, grouped by `role_confirmed` else `roles.role_proposed`.
  Routed through ticket 07's loop: `knockout_effects` now calls
  `knock_out_groups` with singleton groups, and on the real SDR run the two
  single-member families are **bit-identical** to their single knockouts.
- **"Test: ... expected roles, including `unknown` when views disagree"** —
  `tests/test_roles.py`, 48 tests, including the disagree flavour, the
  insufficient flavour, the MLP's not-applicable reads view, and the one column
  that separates selector from mover.
- **"Verified on the SDR head table; family knockout within the short-job
  budget"** — the mechanical pass over the merged outputs of record, and Slurm
  job 22237473 (A40, 2:18, `--time=00:20:00`), both in the ticket's Comments.

Declared deviations, all additive:

1. **Namespaced `roles.role_proposed` / `roles.role_notes` with a bare
   `role_confirmed`**, where `spec.md` writes a bare triple. The orchestrator's
   block C namespacing rule and `head_table.PROTECTED_COLUMNS` (keyed on the
   bare name) force this; recorded in the criteria doc so ticket 11 reads the
   right names.
2. **Four extra `roles.*` columns** beyond the ticket's two:
   `direct_support`, `direct_support_se`, `direct_support_honest_instruction`
   (ADR-0002's sign flip, which the brief requires be a new column) and
   `reads_group` (the reads view in one cell, which the notebook can filter on).
3. **Two extra `knockout.*` columns**, `family` and `family_logit_diff_drop`,
   so a reader of the head table sees a Component's family effect without
   opening the JSON. Additive; ticket 03's `knockout.rank` is untouched.
4. **The suppressor criterion does not require the reads view.** A suppressor
   is defined by what it produces; the reads view is recorded in the notes and
   constrains it only by not contradicting it. Argued in the criteria doc.
5. **`--roles-merge-from`**, which the ticket does not name. It exists because
   the analyses of record are one suite per analysis and the conjunction needs
   all three views in one table; without it the verification would have been a
   hand-rolled uncommitted script.

Nothing in the diff contradicts ADR-0001. ADR-0002 is new and additive.

## What this review did not cover

The criteria's *scientific* content — whether the selector clause is the right
test for "the lie signal enters at the queries", whether `question` should
count as a frame, and whether 12 of 17 heads reading the attention sink at the
Readout means the query position is wrong — is the researcher's call, not a
review finding. Those are open questions 1, 2 and 4 in the ticket.

## 3. Standards axis — the independent sub-agent's report, verbatim

> Standards review of ca/10-role-vocabulary-and-proposal (19f1fb1..0526f9d): 1 hard violation (ADR-0002's "nothing else reads roles.*" is false — knockout.py:405 reads roles.role_proposed), 7 caller-visible errors (worst: --knockout-families' default roles source erases the roles columns it just read), 10 judgement calls.
>
> Sources checked: full diff, CONTEXT.md, ADR-0001, ADR-0002, the agent brief's "Design rules that apply to every ticket", and knockout.py / dla.py / path_patching.py / head_table.py / registry.py / segmentation.py as they stood at 19f1fb1. Also ran tests/test_roles.py and tests/test_knockout_families.py in the base env (56 passed) — context only, not a correctness claim.
>
> **1. HARD VIOLATIONS**
>
> 1.1 [HIGH] docs/adr/0002, final Consequences bullet — the ADR contradicts code in its own commit range. The standard, quoted: "`roles.*` columns exist only after the roles pass has run. Nothing else reads them, so a cell that never runs the pass is unaffected." The code: knockout.py:405 ROLE_COLUMNS = ("role_confirmed", "roles.role_proposed"), read by role_of and families_from_rows, and --knockout-families raises SystemExit by name when the column is missing. So a second thing does read them, in the same branch that asserts nothing does. Fix is one sentence in the ADR.
>
> Nothing else rises to a hard violation, and I want that stated rather than padded: ADR-0001 holds (no nnsight at module scope anywhere new; knock_out_groups keeps torch and hooks function-local; no second hook path; the prunable wrapper is never mentioned; the shared no-nnsight probe is correctly extended). Brief design rules hold (figure + JSON twin; every new flag carries its analysis prefix; shared-file changes minimal and additive; tests assert at written-file and returned-number seams; --dry-run writes nothing). CONTEXT.md vocabulary holds ("baseline" and "control" appear nowhere new; roles.SEGMENT_GROUPS matches segmentation.MECHANISM_SEGMENTS name-for-name, all 18, so the reads view is not silently dead).
>
> **2. CALLER-VISIBLE ERRORS (ranked)**
>
> 2.1 [HIGH] knockout.py:625-629 — the default roles source erases the roles columns the run just consumed, and the help string recommends exactly that case. run() begins each invocation with fresh intake rows and ends with write_cell, which rewrites the table. So the default path reads roles.role_proposed, runs the family pass, then overwrites the table without any roles.* column. docs/component-roles.md already documents the hazard and tells the reader to use a separate suite; the flag default and its help say the opposite. Either make the flag required or say in the help that the run erases them.
>
> 2.2 [MEDIUM-HIGH] roles.py payload() — roles.json's "circuit" and "task" are provenance dicts; every sibling analysis JSON has label strings. Ticket 11's notebook reading "circuit" across the analysis JSONs meets two types. One-line fix: (meta.get("circuit") or {}).get("label").
>
> 2.3 [MEDIUM] roles.py:100-101 — docstring promises loud failure, code fails silently. Nothing validates the column names against the table, so a renamed upstream column produces unknown/insufficient for every Component with no diagnostic. The names are currently all correct — verified against attention_patterns.py:1013-1015, dla.py:1257-1264 and path_patching.py:125-140. Either drop the claim or assert the columns are present.
>
> 2.4 [MEDIUM] analyze_components.py:451-462 — the roles subcommand is undiscoverable from --help. The dispatch happens before build_parser() runs, and neither the parser description nor the module Usage block mentions roles.
>
> 2.5 [LOW-MEDIUM] roles.py:80-82 and the criteria doc — the `other` group is documented but unreachable; segment_group returns the literal "unestablished", never "other". The doc contradicts itself on the same point.
>
> 2.6 [LOW-MEDIUM] tests/test_dla_model.py:399-409 — the assertion is weaker than the one it replaced. Old: pytest.raises(ValueError, match="nosuch"). New: a bare pytest.raises(SystemExit), which any argparse error satisfies. The message this ticket exists to produce is now untested.
>
> 2.7 [LOW] knockout.py:60-64 — stale module docstring: it still describes only the per-Component ranking, while the module now writes four files and carries two new flags.
>
> **3. JUDGEMENT CALLS / SMELLS**
>
> 3.1 [MEDIUM] knockout.py:427-440 and 670-711 — nothing constrains family members to this cell's circuit. Point --knockout-roles-from at a different circuit's cell and the family JSON reports a joint effect over Components the single pass never scored, the figure is titled with THIS circuit's label, and family_columns appends rows carrying only key columns. Cheap fix: drop non-members and record the dropped count in the JSON's grouping block.
>
> 3.2 [MEDIUM] knockout.py:414 — FAMILY_COLUMNS = ("family", "family_logit_diff_drop") collides with established vocabulary. CONTEXT.md uses "family" for task families and "scenario family"; the criteria doc says "Component Role family". role_family is free now and a breaking rename later.
>
> 3.3 [LOW-MEDIUM] knockout.py:670-711 — the clean and corrupt forwards run twice, 2 x len(batches) wasted forwards, which undercuts the refactor's own stated rationale.
>
> 3.4 [LOW-MEDIUM] tests/test_knockout_families_model.py:267-269 — a test that hedges its own assertion; family_payload has no "counts" key, so the first branch is dead and the test adapts to whichever schema it meets.
>
> 3.5 [LOW-MEDIUM] roles.py views_of — bool(row.get(DLA_SUPPRESSION)) against the module's own stated input contract; with CSV rows bool("0") is True and every Component becomes a suppressor candidate, and suppressor is checked first.
>
> 3.6 [LOW] roles.py + the criteria doc — STD's Segments (stipulation_token, statement) are absent from SEGMENT_GROUPS, so on an STD cell every head's read is unestablished with no note saying why.
>
> 3.7 [LOW] knockout.py:105-125 — Effects carries two kinds of key under one annotation; summarize() would raise on a family Effects.
>
> 3.8 [LOW] dla.py:688-704 — parse_conditions silently drops what its docstring says it refuses (the non-str path), and --dla-conditions "" changed meaning from ALL conditions to none.
>
> 3.9 [LOW] Scope drift versus the brief: the carry-over was scoped as "two lines in dla.py, one in the test"; the diff is ~40 lines with a new public exception class and a new public function.
>
> 3.10 [VERY LOW] Cosmetic: unused imports; CONFIRMED = PROTECTED_COLUMNS[0] indexes a tuple documented as extensible.

### Disposition, Standards axis

The orchestrator ruled on every finding; all rulings were followed.

| # | disposition |
|---|---|
| 1.1 | **Fixed.** The ADR's Consequences bullet now names the family knockout as the one reader of `roles.*`. |
| 2.1 | **Fixed twice; the second fix is the one that ships, on the orchestrator's ruling.** The first attempt gave the run loop an optional `extra_columns(ctx)` so the family pass could carry its own `roles.*` columns back. The orchestrator then ruled the defect wider than the reviewer had scoped it: a rerun into a cell drops **`role_confirmed`** too, which is a defect against the ticket's third checkbox, because the column was safe from being *overwritten* and not from being *dropped*. So the carry moved into `analyze_components.py` itself (`carry_roles`), covers `role_confirmed` and every `roles.*` column, runs before the analyses and before `write_cell`, and applies to the dry run and to every analysis rather than to one. `extra_columns` is removed — one mechanism, not two. `merge_columns` is deliberately not the mechanism: it refuses `role_confirmed` outright, which is the protection that made the carry necessary. Two CLI-seam tests, one of them a dry run, plus a mutation check. **One behaviour is lost and is worth naming:** when the roles come from *another* cell via `--knockout-roles-from`, they are no longer copied into the family cell's table. They remain in the cell they were computed in, and `knockout_families.json` records `grouping.read_from` and every family's members. |
| 2.2 | **Fixed.** `_label` unwraps the provenance dict; a test pins `circuit == "delta__head"` and `task == "sdr"`. |
| 2.3 | **Fixed, the preferred way.** `require_columns` refuses a table missing a whole view and names the columns; `--roles-allow-missing-views` proposes anyway and records which views were missing in `roles.json`. |
| 2.4 | **Fixed.** The subcommand is in the module Usage block and in the parser description. |
| 2.5 | **Fixed.** `other` is gone from the code comment, the prose and the group table; an unlisted name is `unestablished`, and a test pins `bos`. |
| 2.6 | **Fixed.** A capsys assertion checks the refusal names the offending condition. |
| 2.7 | **Fixed.** The module docstring names all four files and both flags. |
| 3.1 | **Fixed as ruled.** Members outside `ctx.components` are dropped, not refused (an earlier commit on this branch refused them); the count and the keys are in `grouping.n_outside_this_circuit` and `grouping.outside_this_circuit`, and a test asserts both. |
| 3.2 | **Fixed.** `knockout.role_family` and `knockout.role_family_logit_diff_drop`. The **JSON keys are unchanged**, because ticket 11's notebook reads them. |
| 3.3 | **Kept, with the reason recorded.** Folding the singles and the families into one group list would save two forwards per batch, about five seconds of a two-minute job. It would also mean the single-Component `Effects` and the family `Effects` come out of one call and have to be split apart again, and ticket 07's `knockout_effects` signature is what its own tests and ticket 03's `knockout.rank` consumer depend on. The reviewer is right about the waste and right that the docstring oversold it; `knock_out_groups`' docstring now says the two callers make two calls, what that costs and why the alternative costs more. |
| 3.4 | **Fixed.** The hedged branch is gone. |
| 3.5 | **Fixed.** `_flag` normalizes true/"true"/1/"0", with a test. |
| 3.6 | **Noted in the doc, not fixed in code.** (This paragraph, and four others in the criteria doc, were lost when an editing script aborted part-way and were restored in `c95a193`; the dispositions below describe the doc as it now stands.) |
| 3.6b | **Noted in the doc, not fixed in code.** The group table now says it covers the mechanism tasks and that STD needs its groups before the pass runs on an STD cell. STD is out of the causal analyses by the researcher's 2026-09-16 decision, so adding groups now would be untested vocabulary. |
| 3.7 | **Fixed** (docstring and annotation) in an earlier commit on this branch. |
| 3.8 | **Fixed.** An unknown name is refused from a list as well as a string, and an empty selection still means every condition, both with tests. |
| 3.9 | **Accepted as stated.** The fix is larger than the brief's estimate because matching `--attention-conditions`' shape needs the exception class and the `type=` hook; `dla.py` is not a shared file and the commit is separate, so the orchestrator can drop it alone. |
| 3.10 | **Fixed.** Unused imports gone; `CONFIRMED` is now the literal name with an assertion that `head_table` still protects it. |

## 4. Spec axis — the independent sub-agent's report, verbatim

> Spec review of ticket 10 — VERDICT: SHIP WITH CHANGES. Six findings (2 medium, 4 low); all seven ticket checkboxes met by the code, no scope creep, family knockout genuinely routed through ticket 07's path.
>
> **Checkbox-by-checkbox evidence.** (1) Criteria doc before any role — MET; the doc and ADR land in 78425b2 (10:57:08), roles.py in 4353de3 (11:03:20), roles.json created 11:03:45. (2) CLI subcommand — MET; dispatch before the intake parser, columns and audit JSON written. (3) role_confirmed read, never overwritten — MET by mechanism: merge_columns raises on PROTECTED_COLUMNS, NOT_MERGED keeps the merge from copying it. (4) Family knockout — MET, and VERIFIED NOT A REIMPLEMENTATION: all 18 rows of ca10-family match ca07-knockout exactly on logit_diff_drop, standard_error, rank and accuracy (0 mismatches), so the refactor is behaviour-preserving on the real model, not only on the tiny one. (5) Tests — MET; ran the two pure files in the base env, 56 passed. (6) Verified on SDR — MET on disk. (7) Subagent review — this is it.
>
> **Column names and signs — verified against the outputs of record.** Every constant in roles.py exists in the real tables. knockout.json meta says positive drop = helps deception (read natively, correct); dla.json meta says positive = writes towards deception with the Honest Twin already negated (correct); path_patching meta says negative = the path carries the counterfactual, so roles.direct_support = -direct_effect is the correct flip. Receiver parsing checks out against real data; restricting is_query_receiver_on to `q.` is right because K/V are per KV group and cannot name one head. All 18 real Segment names are in SEGMENT_GROUPS.
>
> **Findings.** 1. MEDIUM — columns are namespaced roles.role_proposed / roles.role_notes where spec story 30 says bare. The deviation is deliberate and argued, and knockout already reads the namespaced name; the risk is ticket 11 reading the bare name. Relay before either branch merges. 2. MEDIUM — a suppressor can be assigned with zero attention input and zero path-patching input: dla.suppression alone satisfies the writes clause and knockout_sign<0 alone the depends clause, and knockout is not one of the glossary's three views. Every other role is a real three-view conjunction and no single view assigns any role anywhere. The carve-out is pre-registered and zero suppressors were assigned, so no current output depends on it — but it is a researcher decision. 3. LOW — direction() skips the z-gate when the standard error is exactly 0.0. 4. LOW — the pressure-reader note is appended to assigned roles too, but the doc reads "assigns unknown all the same"; the code's behaviour is the sensible one, change the sentence. 5. LOW — roles.direct_support_honest_instruction is written but read by no criterion, while the ADR says the criteria doc uses it. 6. LOW — the test_dla_model.py assertion was weakened to a bare SystemExit.
>
> **Scope.** Nothing is creep and nothing the ticket asked for is missing. ADR-0002 obeys the binding rule: the flip is a NEW roles.* column, no output of record is rewritten (verified — path_patching.direct_effect is untouched everywhere). --roles-merge-from is not named in the ticket but is necessary.
>
> **For the comments.** The 16-member unknown family has the largest drop (0.599 +/- 0.130, accuracy 0.72) versus selector 0.447 and mover 0.306. A family that is most of the circuit answers "is the circuit necessary", not "is this role a large effect". Worth a caveat wherever that number is quoted. The criteria doc carries a cross-ticket proposal in prose (ticket 09's threshold default); correctly left as a proposal, it needs the researcher's call.

### Disposition, Spec axis

| # | disposition |
|---|---|
| 1 | **Kept, as the orchestrator ruled**: namespaced `roles.role_proposed` and `roles.role_notes`, bare `role_confirmed` because the protection is keyed on that name. Recorded as a deviation from spec story 30 in the ticket; the orchestrator has told ticket 11 the names, and ticket 11 is merged reading them. |
| 2 | **Kept and stated plainly**, as ruled. The criteria doc's suppressor clause now says the carve-out out loud, names it as the one place the conjunction is weaker than the glossary's sentence, and says it is the researcher's to bless or tighten. It is open question 2 in the ticket. |
| 3 | **Fixed.** `direction()` fails on `se <= 0`, with a test. |
| 4 | **Fixed.** "notes the signature and never assigns the reserved name", and the doc now says the note is appended whatever role the Component gets. |
| 5 | **Fixed.** ADR-0002 says no criterion reads the column today, that it is for downstream readers, and that it carries ticket 09's 71-versus-100 caveat. |
| 6 | **Fixed.** Same capsys assertion as Standards 2.6. |

Both reviewers' closing notes are taken up in the ticket: the unknown-family caveat is written beside the number wherever it is quoted, and the position-threshold default is recorded as the researcher's call rather than decided.

## 5. The one criteria amendment, which neither review asked for

Ticket 09's Slurm read-back, relayed by the orchestrator after both reviews,
measured the **cross-card noise floor on a path-patching cell at about 0.005**
(A40 against A100). The roles path floor was 0.005 — sitting exactly on the
noise — so a criterion could turn on which card a job landed on. It is now
0.01, logged in the criteria doc with its reason and both outcomes.

It costs the circuit its only selector: **L17H25's selector label rested on an
honest-instruction query cell of 0.0068**, above the old floor and inside the
cross-card noise. The SDR nls0.3 delta of record is now one mover and
seventeen unknowns. Both passes are reported in the ticket, and a test pins the
real case so the amendment cannot be quietly undone.
