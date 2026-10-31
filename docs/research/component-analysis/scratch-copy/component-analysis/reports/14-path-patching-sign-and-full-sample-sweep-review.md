# Ticket 14 code review — path patching sign and full-sample sweep

Fixed point: `4ba2877`. Branch `ca/14-path-patching-sign-and-full-sample-sweep`.
Both axes were reviewed at `a03b2e7`. The fixes are in `2a2ba5c` and `1d2bff6`.

**The review is independent of the author.** Both axes ran as parallel
sub-agents (`a28d50adcd3fe3971` Standards, `aa3c319a20a0b4899` Spec). Their
handbacks failed, the failure mode the brief records. Both reports then
reached the orchestrator and the implementer by message, and the orchestrator
forwarded them with its calls. The reports are reproduced verbatim below.

## Standards (verbatim)

> Diff 4ba2877...HEAD, six commits. No hard violations found.
>
> Compliant with the documented standards:
> - No nnsight import outside hooks.py.
> - LEGACY_COLUMNS gains no entries, and test_no_legacy_translation_reaches_a_column_whose_sign_flipped pins that.
> - The flipped columns get new `*_support` names, which ticket 13's "new names or a marker" rule allows.
> - column_name() gives the `_paired_se` order.
> - `strongest_*` and `sweep_rank`/`sweep_flagged` keep their names, correctly: both rank and flag use abs(mean) (path_patching.py:1264-1273).
> - No new figures or flags. The head_table.py and sbatch edits are comment-only. The review.py and check_cell.py additions are additive.
> - Tests assert on files and returned numbers.
>
> Judgement calls (baseline smells):
> 1. Mysterious Name, roles.py:398-439. `outgoing_effect = support_of(...)` and `incoming_effect` now hold support-signed values under the legacy "effect" name. That is exactly the confusion ADR-0002's amendment exists to prevent. Rename them `outgoing_support` / `incoming_support`.
> 2. Primitive Obsession, two vocabularies for one concept. path_patching uses the markers `CONVENTION`/`LEGACY_CONVENTION`. roles.conventions_of uses the bare strings "native"/"legacy". roles.json writes only a sentence, so tests parse it (`"native" in ...["sign_convention"]`, `"negat" in ...`). That goes against path_patching's own stated rule: "a marker a reader tests rather than a sentence it parses". Emit a list of markers in roles.json. `sorted(found, reverse=True)` also relies on alphabetical order.
> 3. Speculative Generality: roles.SE_PAIRS is defined and never read. SIGNED_PAIRS and DERIVED_FROM repeat the same native/legacy pairs (a Data Clump). Call sites pass the pairs by hand again (`support_of(row, DIRECT_SUPPORT, DIRECT_EFFECT)`).
> 4. Duplicated Code, path_patching.py:1041 and 1247: the same `tally.excluded.extend(... if not usable)` appears in both places. `sweep_measured_ids` re-derives `measured_ids` from the payload instead of from the sweep's tally.
> 5. Middle Man:
>    - review._convention is a one-line delegate.
>    - tests/test_review.py `path_figures(group)` returns just `list(group.items)`.
> 6. Message Chain plus a special case, check_cell.py: `review.path_patching.LEGACY_CONVENTION`, and `if view_of is review.path_patching_views` (an identity switch inside a generic loop).
> 7. Error handling, roles.main: a bare `except ValueError` around decide_rows turns any ValueError into a "mixed generations" exit tagged with the cell. A dedicated exception type would scope it.
> 8. Vocabulary (CONTEXT.md):
>    - The metric `sign` sentence says "the pressure prompt's signal", which is not a glossary term. "the clean stream" or "the prompt under its Pressure Clause" would be.
>    - The heatmap title and normalized_effect docstring still say "(clean - corrupt)", while metric_meta now says "(clean - counterfactual)". The honest-instruction pass has no Corruption, so the honest heatmap's title misnames its denominator.
> 9. Minor: `grid_ids: Sequence[str] = None` should be `Optional[...]`. `roles.standard_error` has no docstring.
>
> Spec-axis pointer only: the ticket says "roles.py reads the convention marker", but roles tells the generations apart by column names. That is permitted by the ticket-13 standard and argued in ADR-0002's amendment, but it is worth the Spec reviewer's eye.

### Dispositions (orchestrator's calls)

| # | outcome |
|---|---|
| 1 | **Fixed** (`2a2ba5c`). The locals are `outgoing_support` and `incoming_support`, and the `roles.json` view keys are `outgoing_support` and `incoming_honest_instruction_support`. |
| 2 | **Fixed.** `roles.generations_of` returns `path_patching.CONVENTION` and/or `LEGACY_CONVENTION`, current first, by explicit order rather than sorting. `roles.json` gains `path_conventions`, the list of markers, which the tests check. The `sign_convention` sentence stays for humans. |
| 3 | **Fixed.** `SE_PAIRS`, `SIGNED_PAIRS`, `DERIVED_FROM`, `support_of` and `standard_error` are gone. One table, `roles.PATH_READS` (`{name: (native, legacy)}`), is read by `path_value(row, name)`, `derived_coverage` and `generations_of`. `DERIVED` names the three roles columns read through it. |
| 4 | **Fixed.** `stream_batches` records the gap exclusion once for every pass. `completeness_sweep` returns `(payload, tally)` as `agnostic_pass` does, and `run()` declares the sweep's coverage with `measured_ids(sweep_tally)`; `sweep_measured_ids` is deleted. |
| 5 | **Kept as a judgement call**, per the call: `review._convention` and the test helper `path_figures`. |
| 6 | **Fixed.** `review.Group` gains `check_lines`. `path_patching_views` fills it with `review.convention_summary(results_dir)`, and `check_cell.check` prints any view's `check_lines`, with no special case and no message chain. |
| 7 | **Fixed.** `roles.MixedConventions(ValueError)` is raised for a row holding both generations and for a marker disagreement. `main` catches only it. |
| 8 | **Fixed.** The `sign` sentence now says "the clean stream (the prompt under its Pressure Clause)". The heatmap title, the `normalized_effect` docstring and the module docstring say `(clean - counterfactual)`. |
| 9 | **Fixed.** `grid_ids: Optional[Sequence[str]]`. `roles.standard_error` no longer exists; its job is `path_value`, which has a docstring. |
| pointer | **Fixed by the orchestrator's call.** Roles still tells the generations apart by column name, and `roles.check_markers` now also requires each cell's `agnostic*.json` marker to agree with the generation of that counterfactual's direct column, for the cell and for every `--roles-merge-from` cell. It refuses by file name on a mismatch. Three tests cover agreement and both directions of disagreement. On the real cells, the copy of `sdr-first-run` (legacy, no marker) and the new cell (marker) both pass. |

## Spec (verbatim)

> Verdict: nothing blocking in the code. Two small partials, and the Slurm run is still open.
>
> (a) Missing or partial
> 1. "...in every JSON...; `metric.sign` in each JSON says so in words and a `metric.convention` marker distinguishes new cells". `_skipped_payload` (path_patching.py ~1085, the file written when a counterfactual finds no instance) has no `metric` block. `review.path_patching_conventions` skips it without a word. One-line fix: add `"metric": metric_meta(counterfactual)`.
> 2. "`roles.py` reads the convention marker". It does not read the marker. It tells new cells from old ones by column name (`*_support` vs `*_effect`) and never opens a JSON. The orchestrator's ruling (marker plus a name change) allows this, and the ADR-0002 amendment explains why (a CSV has no meta). It is acceptable, but the code does something different from the ticket's wording. Note that in Comments.
> 3. docs/component-roles.md says "Checked on a copy of `sdr-first-run`... (ticket 14's comments)", but the ticket has no Comments yet. Record that check, or the doc of record cites evidence that does not exist.
> 4. Sweep: "uses the grid's sample... rather than a separate draw". The old code already walked the grid's `batches`; the earlier draw was separate only because it ran as its own 64-instance job. The real fix here is that coverage is now declared over `sweep_measured_ids`, which drops gap-excluded instances as the grid does, so the two instance-set digests match. That part is correct. Say this in Comments so nobody goes looking for sampling code.
>
> (b) Scope creep
> Small only. The README and sbatch give "about 45 minutes" for the sweep, which is scaled up from the 64-instance run, not measured. The new "+0.1275 in the legacy sign, so pushes against" note on mlp.30.0 is new interpretation: correct, but an addition. Refusing a row that holds both generations, the `check_cell` MIXED flag, the `same_as_grid` and `excluded_by_gap` fields, and the bar-colour flip are all within the guidance.
>
> (c) Implemented but wrong
> None found. The flipped `normalized_effect` is right; `column_name` puts `_paired` before `_se`; `LEGACY_COLUMNS` maps no flipped column; the ranks and Segment selection use |mean|, so the flip does not move them. A new cell's `metric` reads native and an old one's reads legacy. Mixing across rows is reported, not refused; only a row holding both is refused.
>
> What the Slurm run must show:
> - It writes into a new suite, and the `sdr-first-run` files stay untouched.
> - Every `path_patching/*.json` has `convention == "positive_helps_deception"`, and `check_cell` prints no MIXED.
> - `direct_support ≈ -(record direct_effect)` per Component, within tolerance on a different GPU. `strongest_*` cell names are identical with their `_support` values negated, and the Segment pass selects the same cells.
> - Sweep: `n_instances == 100`, `same_as_grid == true`, `excluded_by_gap` equals the grid's, and `direct_support` and `sweep_direct_support` share one `instance_set` id. The sweep numbers will not match `sdr-first-run-sweep` (that was a different 64-instance draw). Only the flagged set and mlp.30.0 now being negative can be checked.
> - The roles pass on the new cell gives 0/0/1/0/17 with the same `roles.direct_support`, and `sign_convention` says "native".
> - Both suites pass in both envs against the 8-name failure baseline.

### Dispositions (orchestrator's calls)

| # | outcome |
|---|---|
| a1 | **Fixed** (`2a2ba5c`). `_skipped_payload` carries `metric_meta(counterfactual)`, and the skipped-file test asserts the marker. |
| a2 | **Fixed.** Recorded in the ticket's Comments: generation by column name, plus the JSON-marker agreement check (see Standards "pointer"). |
| a3 | **Fixed.** The copy check and its numbers are in the ticket's Comments: 0/0/1/0/17, 6 knockout-only, zero differences on 18 rows. It was rerun after the review fixes with the same result. |
| a4 | **Fixed.** The ticket's Comments say the sweep always walked the grid's batches, and that the change is the coverage declaration, now via `measured_ids(sweep_tally)`. |
| b, sweep time | **Fixed** (`1d2bff6`). The README and sbatch give measured times: 29 min over 64 instances on an A40 (ticket 12), 23 min over 100 on an A100, and 40 min for the whole job (ticket 14). |
| b, rest | **Kept**, per the call. |
| c | Nothing found. |

**The Slurm checklist, against job 22874991** (A100, cell `ca14-path-patching-2`):

- **A new suite**, with `sdr-first-run` read only through copies.
- **Every path-patching JSON** carries `positive_helps_deception`, and `check_cell` prints no MIXED.
- **`direct_support`** is within 0.0007 of minus the record's `direct_effect` on all 18 Components, for both counterfactuals.
- **`strongest_*`, against the A40 record:** the cell names match on 5 to 10 of 18 rows. Every row that differs has a strongest cell of 0.0045 or less on the record, inside the cross-card floor.
- **`strongest_*`, against ticket 08's A100 cell (same card):** names match on 18 of 18, with exactly negated values.
- **Segment pass:** it selects exactly the record's cells for both pairs (5 item-swap, 4 honest).
- **Sweep:** `n_instances` is 100, `same_as_grid` is true, no instance is gap-excluded (the grid has none either), and one `instance_set` id is shared with the grid. Six non-circuit Components are flagged at 0.05, and `mlp.30.0` is now negative at -0.1317.
- **Roles:** on the new cell merged with the record's other views, the record's role on all 18 circuit rows, 1 mover and 6 knockout-only, with `path_conventions` `["positive_helps_deception"]`.
- **Both suites:** see the ticket.
