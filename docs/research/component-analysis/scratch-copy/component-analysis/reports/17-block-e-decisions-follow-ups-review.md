# Ticket 17 review: block E decision follow-ups

Fixed point `4086e12` (the `component-analysis` tip). Reviewed commits:

    cd9abe8  Flag the knockout sweep at 0.4 and set the layer 0 MLP aside as a positive control
    28f9a53  Give the path-patching sweep its own 0.05 threshold, apart from the Segment pass
    75f2cf6  Note a knockout effect with an established read, and keep rule 6 literal
    a391977  Say at the top of the SDR first-run write-up that it is in the legacy conventions

Process: `mattpocock-skills:code-review`, both axes as independent parallel
sub-agents with no shared context. Both handbacks failed, as the brief
predicts. Both reports then arrived by message, to the implementer and to the
orchestrator, and the orchestrator forwarded each with calls. **The review is
independent of the author.** Fixes are in `4aa41a0` (code, tests and docs),
`fa02314` (one nnsight-gated test the suite run exposed) and
in the ignored `LEGACY.md` files of the `component-analysis` worktree.

## Standards

ca-17 Standards review (4086e12...HEAD): no hard violations of a documented standard; six judgement calls.

HARD VIOLATIONS: none found. No new flags (the prefix rule holds). sweep.png's JSON twin is updated (`positive_controls`, `figure.shows`). Shared-file edits are additive (review.py +1 line, README +2). The component-roles.md "Changing these criteria" entry has a date and a reason, and correctly says rule 2 asks for no rerun. The legacy caveat cites ADR-0002 and LEGACY_COLUMNS. Glossary vocabulary (Component, Segment, Readout) is used correctly.

JUDGEMENT CALLS
1. Duplicated Code, knockout.py: the outsider test appears three times. `row["flagged"] = (... not row["in_circuit"] and not row["positive_control"])`, in threshold_counts (`not row["in_circuit"] and not row.get("positive_control")`) and in strongest_outside_circuit. Extract `counts_as_outsider(row)`. The same file reads the key two ways, `row["positive_control"]` and `row.get(...)`, on rows it just built.
2. Shotgun Surgery / stale text: the 0.4 rationale is written four times (the comment, THRESHOLD_JUSTIFICATION, the --help text, component-roles.md). THRESHOLD_JUSTIFICATION and the help's "(the 20 strongest outsiders there)" hard-code their numbers, while the default itself is interpolated. Change DEFAULT_SWEEP_THRESHOLD and the text goes stale. Pre-existing pattern.
3. THRESHOLD_LADDER = (0.02, 0.05, 0.1, 0.2) now tops out below the 0.4 default. The doc's "the cut hides nothing / can be moved without a rerun" is weaker above 0.2. Consider adding 0.4.
4. Mysterious Name: knockout.DEFAULT_SWEEP_THRESHOLD (0.4, logits) and path_patching.DEFAULT_SWEEP_THRESHOLD (0.05, fraction of the gap) share a name across modules that already import each other. A unit in the name (e.g. `_LOGITS`, `_GAP_FRACTION`) would remove the trap. Also, path_patching repeats "it does not follow --path-position-threshold" in SWEEP_THRESHOLD_FLAG and in the help string. That goes against the module's own "spelled once" convention (comment on DEFAULT_POSITION_THRESHOLD).
5. Tests, spec Testing Decisions ("not tautological"): test_the_png_draws_a_positive_control only checks the PNG magic bytes, so it passes without the hatch or label. Either drop it or assert on something the feature changes. test_the_sweep_flags_at_its_own_default... recomputes `flagged` with the implementation's own filter. If no tiny-model sender clears 0.05, both sides are [] and it proves nothing; add a non-empty or count assertion.
6. Vocabulary: CONTEXT.md lists "control" as ambiguous (under Honest Condition). "Positive control" is the researcher's own term for a different concept, so it is not a breach. But it is now a JSON key (`positive_control`, `positive_controls`) with no glossary entry. Consider a one-line CONTEXT.md term.

Minor: the new component-roles.md 2026-10-14 entry gives no result check on a copy of sdr-first-run, unlike its precedents. That is not required by rules 1-3.

### Orchestrator's calls and outcomes

The call was to fix all six and add the copy-check result. All done in `4aa41a0`:

1. **Fixed.** `knockout.counts_as_outsider(row)` is used by flagging, `threshold_counts` and `strongest_outside_circuit`. Every read of the key in `knockout.py` is now `row["positive_control"]`. `review.py` keeps `.get`, because it reads JSON written before the field existed.
2. **Fixed.** `THRESHOLD_JUSTIFICATION` and the `--help` text interpolate the default and carry no SDR counts. The "20 strongest outsiders" sentence is now only in docs/component-roles.md, as an observation dated 2026-10-14 (job 22874364).
3. **Fixed.** The ladder is `(0.02, 0.05, 0.1, 0.2, 0.4)`. A test asserts the 0.4 rung, and the docs list it.
4. **Fixed.** The defaults are now `knockout.DEFAULT_SWEEP_THRESHOLD_LOGITS` and `path_patching.DEFAULT_SWEEP_THRESHOLD_GAP_FRACTION`. The sentence "it does not follow --path-position-threshold" is `path_patching.SWEEP_THRESHOLD_INDEPENDENT`, used by both `--help` and `SWEEP_THRESHOLD_FLAG`.
5. **Fixed.** `test_the_png_marks_a_positive_control` draws the same rows with and without the mark and asserts the PNGs differ. A mutation that turns the mark off fails it; this was checked, then reverted. The flagging test now asserts a non-empty `flagged` with the position threshold at 1e9: following the position threshold would flag nothing, and the tiny model flags six at 0.05. It also checks that every flagged sender clears 0.05 and lies outside the circuit.
6. **Fixed.** CONTEXT.md has a **Positive Control** entry: the layer 0 MLP in the knockout sweep, and why it is not "control" in the Honest Condition sense. The two test files that read CONTEXT.md pass.
- **Minor, fixed.** The 2026-10-14 entry in the criteria doc records the copy check: 0/0/1/0/17, the same six knockout-only heads, and the note on L5H11, L14H7 and L14H22 only.

## Spec

Ticket 17 spec review (4086e12...HEAD): substantially done, two partials, two wording errors.

Verified OK: knockout default 0.4, with its reason in --help, THRESHOLD_JUSTIFICATION and docs, and the ladder kept. ca15 sweep.json at 0.4: 21 outsiders clear, including mlp.0.0, so 20 once it is set aside; L17H25 is the only circuit member to clear; 90 flagged at 0.1. Positive control: marked, ranked, hatched and labelled; left out of flagged, strongest_outside_circuit and the ladder's outside count; positive_controls meta present. Path sweep: defaults to 0.05 and no longer follows the position threshold (help, threshold_flag, README). Roles: knockout_only is unchanged in behaviour, the note is added, the doc names the case beside rule 6, tests exist. On the ca17-sdr-first-run copy: 0/0/1/0/17, 6 knockout-only, and the note on exactly L5H11, L14H7, L14H22. LEGACY.md: all 17 present. Listed legacy and *_effect columns match each head_table.json, no missing or extra. The "no path-patching" claims match the empty path_patching/ dirs, and no JSON carries metric.convention. No rerun is consistent with "a default change alone does not".

(a) Missing or partial
1. "not committed; list them in the ticket": issue 17 does not list the 17 LEGACY.md cells yet.
2. "Both suites at the 8-name baseline" and "Subagent code review ... findings addressed": not checked here (read-only). Still open.

(b) Scope creep
- review.py hover adds " · positive control". It is small and arguably covered by "labelled so", so fine. Nothing else.

(c) Implemented but wrong
1. Positive-control wording. knockout.py POSITIVE_CONTROLS comment and docs/component-roles.md: "removes almost the whole margin on SDR nls0.3 (+3.12 of 1.66, accuracy 0.01)". In ca15 sweep.json the clean margin is about 1.66, the drop 3.12, and the knocked logit difference -1.46. The knockout reverses the margin (about 1.9 times it), it does not "almost" remove it. Reword, e.g. "reverses the margin (drop +3.12 against a clean 1.66; accuracy 0.01)".
2. ca10-family/LEGACY.md: under "These column names predate ticket 13" it lists knockout.family -> knockout.role_family. LEGACY_COLUMNS dates that rename to "2026-09-20, ticket 10", not ticket 13. Attribute it to ticket 10 (spec: "the column names predate ticket 13").

Not a defect: ca15-knockout-sweep's sweep.json and knockout.sweep_clears_threshold were written at 0.1 with mlp.0.0 flagged. Spec allows no rerun. Optionally give that cell a one-line LEGACY-style note so readers do not take its flagged list as the 0.4 list.

### Orchestrator's calls and outcomes

The call was to fix all of these, keep the hover text, then run both suites, fold both reviews in here, tick the boxes and resolve.

- **(a1) Fixed.** The ticket's Comments list all 17 `LEGACY.md` paths, with what each note covers.
- **(a2) Done.** The first full `mgnp` run on `4aa41a0` found a ninth failure, `tests/test_knockout_model.py::test_the_sweep_columns_land_on_circuit_rows_only_with_their_coverage`. That nnsight-gated test expected a threshold-0 sweep to flag every outsider. The tiny circuit lacks `mlp.0.0`, which is now a positive control and is correctly left unflagged. The test's expectation was updated in `fa02314`, with assertions that `mlp.0.0` is unflagged and named in `positive_controls`. Both suites were then rerun on `fa02314`; the counts are in the ticket. The review findings are addressed as listed here.
- **(b) Kept** by the call: the hover text.
- **(c1) Fixed** in `4aa41a0`. The `POSITIVE_CONTROLS` comment and docs/component-roles.md now say the knockout reverses the margin (drop +3.12 against a clean 1.66, knocked logit difference about -1.46, accuracy 0.01). `POSITIVE_CONTROL_WHY` makes no size claim and is unchanged.
- **(c2) Fixed.** `ca10-family/LEGACY.md` attributes the `knockout.family*` rename to ticket 10 on 2026-09-20 and quotes `LEGACY_COLUMNS`' reason.
- **Optional note, done.** `ca15-knockout-sweep/delta__head/sdr/LEGACY.md` says its `flagged` list and `knockout.sweep_clears_threshold` were written at 0.1 with `mlp.0.0` flagged and no `positive_control` field. It also says how to read the cell at 0.4: 20 outsiders with `mlp.0.0` aside, and L17H25 the only circuit Component.

## Summary

Standards: 0 hard violations and 6 judgement calls, all fixed. The worst was the two same-named defaults in different units. Spec: 2 partials and 2 wording errors, all fixed. The worst was the claim that the layer 0 MLP knockout "removes almost the whole margin", when in fact it reverses it.
