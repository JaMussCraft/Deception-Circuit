# Ticket 13 review: column conventions and multi-job cells

Fixed point: `3c66f4c` (the `component-analysis` tip). Branch
`ca/13-column-conventions-and-multi-job-cells`, reviewed at `24862dd`'s parent
(`68c672d`, ten commits). `mattpocock-skills:code-review`, both axes as
independent parallel sub-agents. Both handbacks failed in the way the brief
describes, and both reports were then delivered by message, to the author and
to the orchestrator. **The review is independent of the author.**

Fixes are in `24862dd` (the spec axis's defect), `fb12bd7` (everything else
taken by the author) and `4ba2877` (the orchestrator's rulings, at the end).

## Standards

Verbatim:

> Standards review of ca/13 (3c66f4c..HEAD): no hard violations; two soft
> breaches of documented rules and eight smells, all judgement calls.
>
> Checked and clean: only hooks.py imports nnsight; no new CLI flags;
> role_confirmed stays protected; paired columns say `paired`, twin columns
> keep `descriptive`; docs use no avoid-list glossary terms; ADR-0002 records
> the rename as a deliberate exception. Shared-file changes exceed "minimal and
> additive", but ticket 13 is the serial ticket, so low concern.
>
> Soft breaches of documented standards:
> 1. tests/test_dla.py (`_Ctx` spy) and tests/test_paired_honest.py
>    (`ctx.take_coverage()`) assert on `declare_coverage` calls, not the
>    written head table/JSON (spec.md "Testing Decisions");
>    test_multi_job_cells.py already checks the written meta.
> 2. head_table.py and the ADR-0002 amendment call
>    `modernize_columns`/LEGACY_COLUMNS "the one place" old names are
>    translated, yet `{LEGACY_COLUMNS.get(c, c): ...}` is hand-written again in
>    `analyze_components.carry_forward`, `roles.read_table` and
>    `review.head_table_view`.
>
> Smells:
> - Mysterious Name: `head_table.INSTANCE_SETS` is a meta-key string;
>   `attention_patterns`, `dla`, `path_patching` each define `INSTANCE_SETS` as
>   a condition-to-set-name dict.
> - Primitive Obsession / Duplicated Code: "test_split", "causal_sample",
>   "paired_honest_instruction", "honest_twin_split" repeated as literals in
>   four modules and tests; likewise "renamed_columns", whose merge is written
>   in both analyze_components.py and roles.main.
> - Duplicated Code: `head_table._PATH_COLUMNS`/`_SWEEP_COLUMNS` restate
>   path_patching's names (test-pinned); `dla.declare_coverage` and
>   `attention_patterns.declare_coverage` share a shape.
> - Data Clumps: (columns, instance_ids, instance_set, dataset) travel as a
>   loose dict through declare_coverage, take_coverage, add_coverage.
> - Feature Envy: `carry_forward`/`print_carried` in the CLI work on head-table
>   meta internals and hard-code `row.get("active_neuron_count")`; belong in
>   head_table.py.
> - Primitive Obsession: scripts/check_cell.py filters notes by
>   `"paired" in note or "coverage" in note` though
>   `Table.renamed_columns`/`Table.coverage` hold the facts.
> - Speculative Generality: `roles.FLAVOURS` unused.
> - Naming inconsistency: `differential_paired_se` (DLA) vs
>   `direct_effect_se_honest_instruction_paired` (path patching).

### Dispositions

| finding | outcome |
|---|---|
| Soft 1: coverage tests assert on declarations | **Kept**, as a judgement call. The written-meta assertion for attention and DLA exists at the CLI seam (`tests/test_paired_honest_cli.py::test_the_head_table_meta_says_how_many_instances_each_column_covers`), and for knockout and path patching in their model tests, but those need nnsight 0.7.0 and run only in `mgnp`. The declaration tests are the base-env coverage of the same rule, built from a hand-made payload; `declare_coverage(ctx, payload)` is each module's own function, so they test it rather than hook wiring. |
| Soft 2: legacy translation hand-written three times | **Fixed** (`fb12bd7`): `head_table.current_name` and `head_table.modernize_meta` (coverage keys plus the `renamed_columns` record) are the one path; the CLI, `roles.read_table`, `roles.main` and `review.head_table_view` use them. |
| `INSTANCE_SETS` name clash | **Fixed**: the meta keys are `head_table.COVERAGE_KEY`, `INSTANCE_SETS_KEY`, `RENAMED_KEY`. |
| Set-name and `renamed_columns` literals | **Fixed**: `head_table.TEST_SPLIT`, `CAUSAL_SAMPLE`, `PAIRED_HONEST_INSTRUCTION`, `HONEST_TWIN_SPLIT` and `RENAMED_KEY` are used by every module (tests keep literals, as expected values from an independent source). |
| `_PATH_COLUMNS` / `_SWEEP_COLUMNS` restated | **Kept**: `path_patching` imports `head_table`, so the reverse import would be circular; `tests/test_path_patching.py::test_the_legacy_names_cover_every_column_this_module_writes` pins the two equal. The two `declare_coverage` functions read different payload shapes; kept. |
| Data clump in declarations | **Kept**: one keyword-argument call in, one dict per declaration out; a type would add a class for a two-function seam. |
| Feature envy in `carry_forward` | **Partly fixed**: the intake-row test is `head_table.is_appended_row`, and the meta handling goes through `modernize_meta`. `carry_forward` stays in the CLI, where the orchestrator placed the generalized `carry_roles`; it is about which namespaces a run replaces, which is the CLI's knowledge. |
| `check_cell.py` matching note text | **Fixed**: it prints from `Table.renamed_columns` and `Table.coverage`. |
| `roles.FLAVOURS` unused | **Fixed by use**: `tests/test_roles.py::test_every_flavour_of_unknown_is_named_in_the_criteria_doc` iterates it, as `ROLES` is the vocabulary's declaration. |
| `differential_paired_se` vs `direct_effect_se_honest_instruction_paired` | **Kept**: each follows its module's existing rule (DLA puts `_se` last; path patching appends a per-counterfactual suffix to every bare name, as ticket 09 did for `_honest_instruction`). Recorded for the researcher. |

## Spec

Verbatim:

> ca-13 spec review (3c66f4c...HEAD): nothing blocks the merge; one real gap,
> the agent-facing docs, and a few smaller points.
>
> (a) Missing or partial
> 1. Ticket: "the README and agent-facing docs say multi-hour jobs and A100/H200
>    partitions are allowed." The README and scripts/analyze_components.sbatch
>    now say so. The agent-facing docs still say the opposite, and none is on
>    the branch: .scratch/component-analysis/spec.md:101 and :121 ("about an
>    hour on A100/A40 ... never a multi-hour H200 job"); agent-brief.md:93
>    ("never an H200 job and never a multi-hour job"); the memory file
>    slurm-job-policy.md. The orchestrator must update these.
> 2. Ticket: "Readers ... use the new names." The head_table.py:5 module
>    docstring still gives `dla.differential` as its example. Nit.
>
> (b) Not asked for (all small and defensible)
> - LEGACY_COLUMNS also maps ticket 10's knockout.family to knockout.role_family.
> - carry_forward now keeps old meta keys such as meta.roles, which used to be
>   dropped. After an analysis reruns, meta.roles.counts survives next to stale
>   roles.* columns.
> - New outputs: flavour_counts and renamed_columns in roles.json,
>   derived-column coverage for roles.direct_support*, print_carried, runtime
>   figures in the docs.
>
> (c) Implemented, but check
> 1. Ticket: "no established read, no DLA, no path above the floor."
>    knockout_only() treats a missing column as silent (direction(None...)
>    returns 0). Under --roles-allow-missing-views, a knockout-only table marks
>    every significant head unknown/knockout-only, and the note "no other view
>    speaks" is wrong: those views were never measured.
> 2. Interpretation (3) is literal and defensible, but the researcher should
>    see the consequence. L5H11 has by far the largest knockout effect (+0.150)
>    and ticket 10 named it; it is excluded because its item_1_question_option
>    read at 0.35 counts as established. L5H5 and L5H6 (question reads) are
>    excluded the same way. The brief says "early heads that matter on knockout
>    alone." The six-head result on the copy checks out: 0/0/1/0/17,
>    flavour_counts {insufficient 11, knockout-only 6}.
> 3. Interpretation (2) is overstated. The ADR amendment says "no output of
>    record is rewritten." In fact any later roles pass, or any CLI run (dry
>    runs included), into a legacy cell writes it back under the new names; the
>    translation is recorded in meta.renamed_columns.
> 4. Ticket: "overwriting only the namespaces of the analyses that run." A
>    whole namespace is replaced, so a later path_patching run with only
>    --path-counterfactual item_swap and no --path-completeness-sweep drops the
>    earlier *_honest_instruction_paired and sweep columns. That follows the
>    spec but deserves a README warning.
> 5. Interpretation (1) fits the ticket's examples and "Paired columns stay on
>    the causal sample." Item-swap and knockout columns are not renamed. If
>    "paired" was meant to cover clean/item-swap pairs too, those columns are
>    missing the word.
>
> Verified as matching the ticket: coverage (n, an instance-set id, the id
> list; all four analyses declare it); CLI tests cover two runs, a third run
> over one namespace, a dry run, and an appended row; review.py and
> check_cell.py show a note for legacy cells; the notebook reads through
> review.head_table_view; the sbatch documents the default partition and time
> as a starting point.

### Dispositions

| finding | outcome |
|---|---|
| (a)1 agent-facing docs | **Already resolved by the orchestrator** before the report was read: `spec.md` lines 101 and 121 and `agent-brief.md` line 94 now say the cap is lifted, and the memory file and its index line say so too. Nothing on the branch to change. |
| (a)2 `head_table.py` docstring example | **Fixed** (`fb12bd7`). |
| (b) `knockout.family` in the map | **Kept**: one legacy map is the point of the seam, and it let `review.py` read ticket 10's old spelling the same way; the two review tests for it now expect the current names. |
| (b) `meta.roles` carried beside rerun analyses | **Kept**, documented: the `roles.*` columns are carried too, and `docs/component-roles.md` says to rerun the roles pass on a cell whose analyses were rerun. Dropping `meta.roles` while keeping the columns would leave columns with no record of the criteria they were proposed under. |
| (b) other additions | **Kept**; each is a reader-facing record of something this ticket changed. |
| (c)1 unmeasured view read as silent | **Fixed** (`24862dd`): `knockout_only` requires the DLA and path-patching views to have been measured; two parametrized tests; the doc's rule 6 says so. The real cell is unaffected (re-verified: still the same six heads). |
| (c)2 L5H11 | **For the researcher**; in the ticket's open questions. |
| (c)3 ADR overstated | **Fixed** (`fb12bd7`): the amendment says a run into a legacy cell writes it back under the current names and records the translation. |
| (c)4 whole-namespace replacement | **Fixed** (`fb12bd7`): README warning with the exact case. |
| (c)5 "paired" reading | **Kept**, recorded in the ticket for the researcher. |

## Orchestrator's rulings

Three messages from the orchestrator, after it received both reports directly.
The first two forwarded each axis with calls; the third ruled on the six
findings the author had kept, and where it differs from the first two it is
the one applied (it keeps `carry_forward` in the CLI and leaves the `_se`
order to ticket 14).

| finding | ruling | outcome |
|---|---|---|
| Standards soft 1: coverage tests assert on declarations | **Fix** | `4ba2877`: the `_Ctx` spy and the declaration assertions are gone. `tests/test_dla.py` and `tests/test_paired_honest.py` now write the analysis's columns and its declared coverage into a head table through `head_table.add_declarations` (the helper the CLI now calls after each analysis) and assert on the written file's `meta.coverage` and `meta.instance_sets`. Base env, no model. |
| Standards soft 2: legacy translation in three places | Fix | Done in `fb12bd7` (`current_name`, `modernize_meta`). |
| `INSTANCE_SETS` meta-key clash; set-name and `renamed_columns` literals; `check_cell.py` note matching; `roles.FLAVOURS` | Fix the cheap smells | Done in `fb12bd7`. |
| `_PATH_COLUMNS` / `_SWEEP_COLUMNS` restated | Keep; the pin test is enough | Kept. |
| Coverage data clump; the two `declare_coverage` twins | Record as judgement calls | Recorded; no change. |
| `carry_forward` in the CLI | Keep | Kept; the intake-row predicate is `head_table.is_appended_row`. |
| `differential_paired_se` vs `direct_effect_se_honest_instruction_paired` | Keep for now; ticket 14 applies `<name>_paired_se` when it renames the flipped columns | Kept; the note is in the ticket's name table. |
| Spec (c1) unmeasured view read as silent | Fix, test both cases, note the unmeasured views | `24862dd` made the flavour need measured views; `4ba2877` adds the "not measured: ..." note and a test that a measured-and-insignificant view still gives `knockout-only`. |
| Spec (c3) ADR overstated | Reword | Done in `fb12bd7`. |
| Spec (c4) whole-namespace replacement | README warning with the rerun-the-roles-pass note | Warning in `fb12bd7`; the roles-pass note beside it in `4ba2877`. |
| Spec (a2) docstring example | Fix | Done in `fb12bd7`. |
| Spec (c2) L5H11, L5H5, L5H6 excluded by established reads | Record for the researcher | In the ticket's open questions, with the six-head result. One correction to the finding: L5H5 and L5H6 also fail the knockout bar (z = 1.8 and 1.9), so only L5H11, L14H7 and L14H22 are excluded by their reads alone. |
| Spec (c5) "paired" is the honest-instruction pairing only | Record once in the name table | In the ticket's name table. |
| Spec (b) extra outputs; `meta.roles` carried beside stale `roles.*` | Fine; note it | `docs/component-roles.md` says `meta.roles` is carried until the pass reruns (`4ba2877`). |
| `knockout.family` in the legacy map | Keep | Kept. |

The roles pass on the copy of `sdr-first-run` after every fix: still 0/0/1/0/17
and the same six `knockout-only` heads; no note says "not measured" there,
because every Component of that cell has DLA and path-patching values.
